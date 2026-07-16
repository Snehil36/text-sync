// ===== Element references =====
const dropZone = document.getElementById("dropZone");
const fileInput = document.getElementById("fileInput");

const errorModal = document.getElementById("errorModal");
const errorOkBtn = document.getElementById("errorOkBtn");

const confirmModal = document.getElementById("confirmModal");
const confirmText = document.getElementById("confirmText");
const confirmYesBtn = document.getElementById("confirmYesBtn");
const confirmNoBtn = document.getElementById("confirmNoBtn");

const progressContainer = document.getElementById("progressContainer");
const progressTrack = document.getElementById("progressTrack");
const progressFill = document.getElementById("progressFill");
const progressSize = document.getElementById("progressSize");

let pendingFile = null;

// Progress bar width scaling config (in pixels)
const MIN_BAR_WIDTH = 120;
const MAX_BAR_WIDTH = 320;
const SCALE_REFERENCE_MB = 50;

// ===== 1. Upload trigger: click anywhere in the drop zone =====
dropZone.addEventListener("click", () => {
    fileInput.click();
});

fileInput.addEventListener("change", () => {
    if (fileInput.files.length > 0) {
        handleFile(fileInput.files[0]);
    }
});

// ===== 1. Upload trigger: drag and drop =====
dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("drag-over");
});

dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("drag-over");
});

dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("drag-over");
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
});

// ===== 2. File validation =====
function handleFile(file) {
    const isPdf = file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf");

    if (!isPdf) {
        showErrorModal();
        fileInput.value = "";
        return;
    }

    pendingFile = file;
    showConfirmModal(file.name);
}

function showErrorModal() {
    errorModal.classList.remove("hidden");
}

function hideErrorModal() {
    errorModal.classList.add("hidden");
}

errorOkBtn.addEventListener("click", hideErrorModal);

function showConfirmModal(fileName) {
    confirmText.textContent = `Do you want to upload ${fileName}?`;
    confirmModal.classList.remove("hidden");
}

function hideConfirmModal() {
    confirmModal.classList.add("hidden");
}

confirmNoBtn.addEventListener("click", () => {
    pendingFile = null;
    fileInput.value = "";
    hideConfirmModal();
});

confirmYesBtn.addEventListener("click", () => {
    hideConfirmModal();
    if (pendingFile) {
        startUpload(pendingFile);
    }
});

// ===== 3. Upload progress indicator + real upload =====
function startUpload(file) {
    const fileSizeMB = file.size / (1024 * 1024);

    const scaleRatio = Math.min(fileSizeMB / SCALE_REFERENCE_MB, 1);
    const barWidth = MIN_BAR_WIDTH + scaleRatio * (MAX_BAR_WIDTH - MIN_BAR_WIDTH);

    progressTrack.style.width = `${barWidth}px`;
    progressFill.style.width = "0%";
    progressSize.textContent = `${fileSizeMB.toFixed(2)} MB`;
    progressContainer.classList.remove("hidden");

    // Animate the bar while the real upload + processing happens.
    // We pulse it to ~85% quickly then hold there until the server responds,
    // since we can't get real byte-level progress from a fetch() call easily.
    animateToPercent(85, 1500, () => {
        sendToServer(file);
    });
}

function animateToPercent(targetPercent, durationMs, onComplete) {
    const startTime = performance.now();
    let current = 0;

    function step(now) {
        const elapsed = now - startTime;
        const progress = Math.min(elapsed / durationMs, 1);
        current = progress * targetPercent;
        progressFill.style.width = `${current}%`;

        if (progress < 1) {
            requestAnimationFrame(step);
        } else {
            if (onComplete) onComplete();
        }
    }

    requestAnimationFrame(step);
}

// ===== 4. Send file to Flask server and trigger download =====
async function sendToServer(file) {
    const formData = new FormData();
    formData.append("file", file);

    try {
        const response = await fetch("/upload", {
            method: "POST",
            body: formData,
        });

        if (!response.ok) {
            // Try to parse an error message from the server's JSON response
            let errorMsg = "Something went wrong. Please try again.";
            try {
                const errData = await response.json();
                if (errData.error) errorMsg = errData.error;
            } catch (_) {}

            progressFill.style.width = "0%";
            progressContainer.classList.add("hidden");
            showServerError(errorMsg);
            return;
        }

        // Server returned the corrected PDF — complete the bar then download it
        progressFill.style.width = "100%";

        // Small delay so the user sees the bar finish before the download starts
        setTimeout(async () => {
            const blob = await response.blob();
            const url = URL.createObjectURL(blob);

            // Pull the filename from the Content-Disposition header if present
            const disposition = response.headers.get("Content-Disposition");
            let downloadName = "corrected_output.pdf";
            if (disposition) {
                const match = disposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
                if (match && match[1]) {
                    downloadName = match[1].replace(/['"]/g, "");
                }
            }

            // Trigger the browser's native download dialog
            const a = document.createElement("a");
            a.href = url;
            a.download = downloadName;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            // Reset the UI back to the initial state
            setTimeout(() => {
                progressContainer.classList.add("hidden");
                progressFill.style.width = "0%";
                fileInput.value = "";
                pendingFile = null;
            }, 800);

        }, 400);

    } catch (networkError) {
        // Network-level failure (server not running, connection refused, etc.)
        progressFill.style.width = "0%";
        progressContainer.classList.add("hidden");
        showServerError("Could not reach the server. Make sure server.py is running.");
    }
}

// ===== 5. Server error modal =====
// Reuses the existing errorModal element but sets a custom message.
function showServerError(message) {
    document.querySelector("#errorModal .modal-box p").textContent = message;
    errorModal.classList.remove("hidden");
}