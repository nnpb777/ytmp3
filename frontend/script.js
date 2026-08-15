let currentFormat = "mp3";

const videoUrl = document.getElementById("videoUrl");
const actionBtn = document.getElementById("actionBtn");
const toggleBtn = document.getElementById("toggleFormatBtn");
const downloadArea = document.getElementById("downloadArea");

// FORMAT SWITCH
toggleBtn.addEventListener("click", () => {
    if (currentFormat === "mp3") {
        currentFormat = "mp4";
        actionBtn.textContent = "Get MP4";
        toggleBtn.textContent = "download as MP3 (audio)";
    } else {
        currentFormat = "mp3";
        actionBtn.textContent = "Get MP3";
        toggleBtn.textContent = "download as MP4 (video)";
    }
});

// BUTTON CLICK
actionBtn.addEventListener("click", convert);

// ENTER KEY
videoUrl.addEventListener("keydown", function (e) {
    if (e.key === "Enter") {
        convert();
    }
});

// CONVERT FUNCTION
async function convert() {
    const url = videoUrl.value.trim();

    if (!url) {
        showError("Enter YouTube link.");
        return;
    }

    if (!url.includes("youtube.com") && !url.includes("youtu.be")) {
        showError("Enter the correct YouTube link.");
        return;
    }

    actionBtn.disabled = true;
    toggleBtn.disabled = true;
    actionBtn.textContent = "Processing...";

    downloadArea.classList.remove("hidden");
    downloadArea.innerHTML = `
        <div class="status">
            Please wait. Your query is being processed...
        </div>
    `;

    try {
        const response = await fetch(`/convert?url=${encodeURIComponent(url)}&format=${currentFormat}`);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "An error occurred during processing.");
        }

        if (data.status !== "success") {
            throw new Error("Failed query.");
        }

        downloadArea.innerHTML = `
            <div class="download-box">
                <div class="success">✓ Ready</div>
                <div class="title">${escapeHtml(data.title)}</div>
                <a 
                    class="download-button" 
                    href="${data.download_url}" 
                    target="_blank" 
                    rel="noopener noreferrer"
                >
                    Download ${currentFormat.toUpperCase()}
                </a>
            </div>
        `;

    } catch (error) {
        console.error(error);
        showError(error.message);
    } finally {
        actionBtn.disabled = false;
        toggleBtn.disabled = false;
        actionBtn.textContent = currentFormat === "mp3" ? "Get MP3" : "Get MP4";
    }
}

function showError(message) {
    downloadArea.classList.remove("hidden");
    downloadArea.innerHTML = `
        <div class="error">
            ${escapeHtml(message)}
        </div>
    `;
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text || "";
    return div.innerHTML;
}
