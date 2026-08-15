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
            Məlumatlar alınır, zəhmət olmasa gözləyin...
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

        downloadArea.innerHTML = `
            <div class="download-box">
                <div class="success">✓ Hazırdır</div>
                <div class="title">${escapeHtml(data.title)}</div>
                <button 
                    id="startDownloadBtn" 
                    class="download-button"
                >
                    ${currentFormat.toUpperCase()} İndir
                </button>
                <div id="progressText" style="margin-top: 10px; font-size: 14px; color: #4caf50; font-weight: bold;"></div>
            </div>
        `;

        // Düyməyə basdıqda brauzeri başqa səhifəyə atmadan arxa fonda endiririk
        document.getElementById("startDownloadBtn").addEventListener("click", function() {
            startDirectDownload(data.download_url, data.title, data.format, this);
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

// BİRBAŞA ENDİRMƏ FUNKSİYASI (Pleyerə keçidin qarşısını alır)
async function startDirectDownload(fileUrl, title, format, btnElement) {
    btnElement.disabled = true;
    btnElement.textContent = "Yüklənir...";
    const progressText = document.getElementById("progressText");

    try {
        // referrerPolicy: 'no-referrer' Google CDN-in bloklamasını keçmək üçündür
        const response = await fetch(fileUrl, {
            method: "GET",
            referrerPolicy: "no-referrer"
        });

        if (!response.ok) {
            throw new Error("Fayl alına bilmədi.");
        }

        const contentLength = response.headers.get("content-length");
        const totalBytes = contentLength ? parseInt(contentLength, 10) : 0;
        
        const reader = response.body.getReader();
        let receivedBytes = 0;
        const chunks = [];

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            chunks.push(value);
            receivedBytes += value.length;

            if (totalBytes > 0 && progressText) {
                const percent = Math.round((receivedBytes / totalBytes) * 100);
                progressText.textContent = `Yüklənir: %${percent} (${(receivedBytes / (1024 * 1024)).toFixed(1)} MB)`;
            } else if (progressText) {
                progressText.textContent = `Yüklənir: ${(receivedBytes / (1024 * 1024)).toFixed(1)} MB`;
            }
        }

        const mimeType = format === "mp3" ? "audio/mpeg" : "video/mp4";
        const blob = new Blob(chunks, { type: mimeType });
        
        // Kompyuterə/Telefona fayl kimi saxlayırıq
        const blobUrl = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.style.display = "none";
        a.href = blobUrl;
        a.download = `${title}.${format}`;
        
        document.body.appendChild(a);
        a.click();
        
        setTimeout(() => {
            window.URL.revokeObjectURL(blobUrl);
            a.remove();
        }, 1000);

        btnElement.textContent = `${format.toUpperCase()} İndir`;
        btnElement.disabled = false;
        if (progressText) progressText.textContent = "✓ Yüklənmə tamamlandı!";

    } catch (err) {
        console.error("Download Error:", err);
        btnElement.disabled = false;
        btnElement.textContent = "Yenidən cəhd et";
        if (progressText) {
            progressText.style.color = "#ff4d4d";
            progressText.textContent = "Xəta baş verdi. Linki yenidən yerləşdirib cəhd edin.";
        }
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
