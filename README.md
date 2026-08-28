
---

## Running Locally

**Prerequisites:**
- Python 3.9+
- A Google Gemini API key (get one free at https://aistudio.google.com)

**Setup:**
```bash
# Clone the repo
git clone https://github.com/Snehil36/textsync.git
cd textsync

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set your Gemini API key as an environment variable
export PDF_OFFSETTER="your-gemini-api-key-here"

# Run the server
python3 server.py
```

Then open `http://127.0.0.1:5000` in any browser — Chrome, Firefox, Safari, Edge, etc.

---

## Security

- File type validated by magic bytes (`%PDF`), not just filename extension
- Filename sanitized with `werkzeug.secure_filename()` — prevents path traversal attacks
- Upload size capped at 100MB
- Temp files stored using UUIDs, never paths derived from user input
- All pipeline calls are direct Python functions — no subprocess, no shell injection surface
- Generic error responses — no internal details exposed to the client
- Temp files deleted immediately after each request, success or failure
- CORS disabled — same-origin requests only
- `debug=False` enforced — no interactive console exposed in the browser

---

## Future Plans

### Chrome Extension
Text Sync will also be available as a Chrome extension. Since the backend is already hosted on AWS, the extension frontend will simply point at the hosted URL — no backend changes required.

### Other Planned Improvements
- HTTPS support once a custom domain is acquired
- Async processing for large PDFs (currently synchronous, can take 30-60 seconds)
- Support for appendix pages with non-standard numbering (e.g. "A-1")
- Support for roman numeral front matter sections
- Browser extension versions for Firefox and Edge

---

## Known Limitations
- Gemini has a 1000 page PDF limit — handled by sending only the first 50 pages for TOC extraction
- Processing is synchronous — large PDFs may take up to 60 seconds
- Appendix pages with non-standard page numbers (e.g. "A-1") are detected but not currently mapped
- Requires a Google Gemini API key to run
- Currently running on HTTP — HTTPS will be enabled once a custom domain is configured

---

## Related Repository
The Python prototype used to develop and test the core logic before building the full web application:
**https://github.com/Snehil36/pdf_page_mapper**

---

## Author
Built by Snehil
