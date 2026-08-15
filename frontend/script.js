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
        showError("YouTube linkini daxil edin.");
        return;
    }

    if (!url.includes("youtube.com") && !url.includes("youtu.be")) {
        showError("Düzgün YouTube linki daxil edin.");
        return;
    }

    actionBtn.disabled = true;
    toggleBtn.disabled = true;
    actionBtn.textContent = "Gözləyin...";

    downloadArea.classList.remove("hidden");
    downloadArea.innerHTML = `
        <div class="status">
            Məlumatlar emal olunur, zəhmət olmasa gözləyin...
        </div>
    `;

    try {
        const response = await fetch(`/convert?url=${encodeURIComponent(url)}&format=${currentFormat}`);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Xəta baş verdi.");
        }

        if (data.status !== "success") {
            throw new Error("Sorğu uğursuz oldu.");
        }

        // Qeyd: Yaratdığımız /download proxy-sinə müraciət edir, target="_blank"
        // səbəbi ilə brauzer arxa planda endirmə əmrini alır.
        downloadArea.innerHTML = `
            <div class="download-box">
                <div class="success">✓ Hazırdır</div>
                <div class="title">${escapeHtml(data.title)}</div>
                <a 
                    href="/download?url=${encodeURIComponent(data.download_url)}&title=${encodeURIComponent(data.title)}&format=${data.format}" 
                    class="download-button"
                    target="_blank"
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
