let currentFormat = "mp3";

const videoUrl = document.getElementById("videoUrl");
const actionBtn = document.getElementById("actionBtn");
const toggleBtn = document.getElementById("toggleFormatBtn");
const downloadArea = document.getElementById("downloadArea");

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

actionBtn.addEventListener("click", convert);

videoUrl.addEventListener("keydown", function (e) {
    if (e.key === "Enter") {
        convert();
    }
});

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
            Please wait. Fetching video details...
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
                <button 
                    id="directDownloadBtn" 
                    class="download-button"
                >
                    Download ${currentFormat.toUpperCase()}
                </button>
            </div>
        `;

        document.getElementById("directDownloadBtn").addEventListener("click", async function() {
            const btn = this;
            btn.disabled = true;
            btn.textContent = "Downloading file...";

            try {
                const mediaRes = await fetch(data.download_url);
                const blob = await mediaRes.blob();
                
                const blobUrl = window.URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.style.display = "none";
                a.href = blobUrl;
                a.download = `${data.title}.${data.format}`;
                
                document.body.appendChild(a);
                a.click();
                
                window.URL.revokeObjectURL(blobUrl);
                a.remove();
                
                btn.textContent = `Download ${currentFormat.toUpperCase()}`;
                btn.disabled = false;
            } catch (err) {
                window.location.href = data.download_url;
            }
        });

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
