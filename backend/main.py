from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import os
import re
import uuid
import threading
import yt_dlp


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")

os.makedirs(DOWNLOAD_DIR, exist_ok=True)


# BgUtils servisinin Render-dəki public URL-i
# Render-də environment variable kimi əlavə edəcəyik.
POT_PROVIDER_URL = os.getenv("POT_PROVIDER_URL", "").rstrip("/")


def clean_filename(name: str) -> str:
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name[:180] or "YouTube_Media"


def build_ydl_options(format_type: str, output_template: str):
    options = {
        "outtmpl": output_template,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": False,
        "retries": 3,
        "fragment_retries": 3,
        "concurrent_fragment_downloads": 4,
    }

    # PO Token Provider
    if POT_PROVIDER_URL:
        options["extractor_args"] = {
            "youtubepot-bgutilhttp": {
                "base_url": POT_PROVIDER_URL
            }
        }

    if format_type == "mp3":
        options.update({
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
        })

    elif format_type == "mp4":
        options.update({
            "format": "bv*+ba/b",
            "merge_output_format": "mp4",
        })

    else:
        raise ValueError("Invalid format")

    return options


@app.get("/")
def index():
    return FileResponse(
        os.path.join(BASE_DIR, "frontend", "index.html")
    )


@app.get("/convert")
def convert_video(url: str, format: str = "mp3"):

    if not url:
        raise HTTPException(
            status_code=400,
            detail="YouTube URL daxil edin."
        )

    if format not in ("mp3", "mp4"):
        raise HTTPException(
            status_code=400,
            detail="Format yalnız mp3 və ya mp4 ola bilər."
        )

    unique_id = str(uuid.uuid4())[:12]

    try:
        # Əvvəl videonun məlumatını alırıq
        info_options = {
            "quiet": True,
            "no_warnings": False,
            "noplaylist": True,
        }

        if POT_PROVIDER_URL:
            info_options["extractor_args"] = {
                "youtubepot-bgutilhttp": {
                    "base_url": POT_PROVIDER_URL
                }
            }

        with yt_dlp.YoutubeDL(info_options) as ydl:
            info = ydl.extract_info(url, download=False)

        title = info.get("title") or "YouTube_Media"
        clean_title = clean_filename(title)

        extension = "mp3" if format == "mp3" else "mp4"

        output_template = os.path.join(
            DOWNLOAD_DIR,
            f"{unique_id}.%(ext)s"
        )

        options = build_ydl_options(
            format,
            output_template
        )

        # Faylı yüklə
        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.download([url])

        # Yaranmış faylı tap
        possible_files = []

        for filename in os.listdir(DOWNLOAD_DIR):
            if filename.startswith(unique_id):
                possible_files.append(filename)

        if not possible_files:
            raise Exception(
                "Yükləmə tamamlandı, amma fayl tapılmadı."
            )

        # MP3/MP4 faylını seç
        selected_file = None

        for filename in possible_files:
            if filename.lower().endswith(f".{extension}"):
                selected_file = filename
                break

        if not selected_file:
            selected_file = possible_files[0]

        return {
            "status": "success",
            "title": title,
            "clean_title": clean_title,
            "file_key": selected_file,
            "format": format,
        }

    except Exception as e:

        error_text = str(e)

        # istifadəçiyə çox uzun yt-dlp logu göstərməyək
        if len(error_text) > 1200:
            error_text = error_text[-1200:]

        raise HTTPException(
            status_code=500,
            detail=f"YouTube yükləmə xətası: {error_text}"
        )


@app.get("/get-file/{file_key}")
def get_file(file_key: str):

    # Path traversal qoruması
    if "/" in file_key or "\\" in file_key or ".." in file_key:
        raise HTTPException(
            status_code=400,
            detail="Yanlış fayl adı."
        )

    file_path = os.path.join(
        DOWNLOAD_DIR,
        file_key
    )

    if not os.path.isfile(file_path):
        raise HTTPException(
            status_code=404,
            detail="Fayl tapılmadı."
        )

    extension = os.path.splitext(file_key)[1].lower()

    if extension == ".mp3":
        media_type = "audio/mpeg"
    elif extension == ".mp4":
        media_type = "video/mp4"
    else:
        media_type = "application/octet-stream"

    # Download zamanı faylı sil
    def delete_later():
        import time

        time.sleep(120)

        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass

    threading.Thread(
        target=delete_later,
        daemon=True
    ).start()

    download_name = file_key

    return FileResponse(
        file_path,
        media_type=media_type,
        filename=download_name,
        headers={
            "Content-Disposition":
                f'attachment; filename="{download_name}"'
        }
    )


# Frontend static faylları
STATIC_DIR = os.path.join(BASE_DIR, "frontend")

if os.path.isdir(STATIC_DIR):
    app.mount(
        "/static",
        StaticFiles(directory=STATIC_DIR),
        name="static"
    )
