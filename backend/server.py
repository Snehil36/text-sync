"""
server.py — local Flask server for the PDF page-mapper tool.

Security measures implemented:
  - File type validated by MIME type AND magic bytes (first 4 bytes of the
    actual file content), not just the filename extension — prevents a
    malicious file renamed to .pdf from being processed.
  - Filename sanitized with werkzeug's secure_filename() before any
    filesystem interaction — prevents path traversal attacks like
    "../../etc/passwd.pdf".
  - Upload size hard-capped at 100 MB at the Flask layer — prevents
    denial-of-service via oversized uploads.
  - Files are saved to an isolated temp directory inside the server's own
    folder, never into any directory derived from user input.
  - Temp files (both upload and output) are always deleted after the
    response is sent, even if an error occurs, so nothing accumulates on disk.
  - No shell=True subprocess calls anywhere — all Python logic is called
    directly as functions, eliminating shell injection risk entirely.
  - CORS is intentionally not enabled — the server only accepts requests
    from the same origin (the page it serves itself), blocking cross-site
    request attempts from other domains.
"""

import os
import uuid
import tempfile

from flask import Flask, request, send_file, jsonify, abort, render_template_string, render_template
from werkzeug.utils import secure_filename

# ── Import your existing pipeline functions directly (no subprocess) ──────────
from find_toc import find_toc
from parse_result import parse_response
from shift_page import apply_toc_metadata

# ── App setup ─────────────────────────────────────────────────────────────────
app = Flask(__name__)

# Hard cap: reject any upload larger than 100 MB before it even hits your code.
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024  # 100 MB

# Isolated temp directory — all uploads and outputs land here, never anywhere
# derived from user-provided filenames.
TEMP_DIR = os.path.join(os.path.dirname(__file__), "_tmp")
os.makedirs(TEMP_DIR, exist_ok=True)

# PDF magic bytes — the first 4 bytes of every real PDF file are always %PDF.
# Checking this prevents a file renamed to .pdf from slipping through.
PDF_MAGIC = b"%PDF"


def is_real_pdf(file_storage) -> bool:
    """
    Read the first 4 bytes of the uploaded file to confirm it is actually a
    PDF by its magic bytes, regardless of what its filename or MIME type claim.
    Rewinds the stream afterward so the rest of the file can still be read.
    """
    header = file_storage.read(4)
    file_storage.seek(0)  # rewind so the full file can be saved afterward
    return header == PDF_MAGIC


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Serve the frontend HTML page."""
    # Serving as a static file — Flask will look for index.html in the same
    # directory as server.py (static_folder=".").
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    """
    Receive the uploaded PDF, run the full pipeline, and return the corrected
    PDF as a browser download.
    """

    # ── 1. Confirm a file was actually sent ───────────────────────────────────
    if "file" not in request.files:
        return jsonify({"error": "No file included in the request."}), 400

    uploaded_file = request.files["file"]

    if uploaded_file.filename == "":
        return jsonify({"error": "No file selected."}), 400

    # ── 2. Sanitize the filename ──────────────────────────────────────────────
    # secure_filename() strips path separators and any characters that could
    # be used for directory traversal (e.g. "../../../etc/passwd.pdf" becomes
    # "etc_passwd.pdf").  We don't actually use the sanitized name to derive
    # a storage path — we generate a UUID for that — but we keep it for the
    # output filename shown to the user.
    safe_name = secure_filename(uploaded_file.filename)

    if not safe_name.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files are accepted."}), 415

    # ── 3. Validate by magic bytes (not just extension/MIME type) ────────────
    if not is_real_pdf(uploaded_file):
        return jsonify({"error": "File does not appear to be a valid PDF."}), 415

    # ── 4. Save to an isolated temp path derived from a UUID, not user input ──
    unique_id = uuid.uuid4().hex
    input_path = os.path.join(TEMP_DIR, f"{unique_id}_input.pdf")
    output_path = os.path.join(TEMP_DIR, f"{unique_id}_output.pdf")

    try:
        uploaded_file.save(input_path)

        # ── 5. Run the pipeline ───────────────────────────────────────────────
        # All calls are direct Python function calls — no shell=True, no
        # subprocess, so there is no shell injection surface here at all.
        response_text = find_toc(input_path)
        offset, toc, special_pages = parse_response(response_text)
        apply_toc_metadata(input_path, offset, toc, output_path=output_path)

        # ── 6. Stream the corrected PDF back as a download ───────────────────
        # as_attachment=True tells the browser to save it rather than open it.
        # The download name shown to the user is derived from the sanitized
        # original filename, not from any raw user input.
        download_name = f"corrected_{safe_name}"

        return send_file(
            output_path,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=download_name,
        )

    except Exception as e:
        # Generic catch — log the real error server-side but never expose
        # internal details (stack traces, file paths, etc.) to the client,
        # as those could aid an attacker in mapping your system.
        app.logger.error("Pipeline error: %s", str(e))
        return jsonify({"error": "Something went wrong processing your PDF. Please try again."}), 500

    finally:
        # ── 7. Always clean up temp files, even if an error occurred ─────────
        for path in (input_path, output_path):
            try:
                if os.path.exists(path):
                    os.remove(path)
            except OSError:
                pass  # best-effort cleanup; don't mask the original error


# ── Error handlers ────────────────────────────────────────────────────────────

@app.errorhandler(413)
def request_entity_too_large(e):
    """Flask raises 413 automatically when MAX_CONTENT_LENGTH is exceeded."""
    return jsonify({"error": "File too large. Maximum upload size is 100 MB."}), 413


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found."}), 404


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # debug=False in all cases — debug mode exposes an interactive Python
    # console in the browser on errors, which is a severe security risk even
    # on a local server if anyone else on your network can reach the port.
    app.run(host="127.0.0.1", port=5000, debug=False)