from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import re
import requests
from urllib.parse import quote

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "frontend")

RAPIDAPI_KEY = "f3afb72dc8msh14e3475506f7502p1355d6jsn988f8e0a8f2a"
RAPIDAPI_HOST = "youtube-media-downloader.p.rapidapi.com"

def extract_video_id(url: str) -> str:
    match = re.search(r'(?:v=|\/|embed\/|shorts\/)([\w-]{11})', url)
    if match:
        return match.group(1)
    return None

@app.get("/")
def index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

@app.get("/convert")
def convert_video(url: str, format: str = "mp3"):
    if not url:
        raise HTTPException(status_code=400, detail="YouTube URL daxil edin.")

    if format not in ("mp3", "mp4"):
        raise HTTPException(status_code=400, detail="Format yalnız mp3 və ya mp4 ola bilər.")

    video_id = extract_video_id(url)
    if not video_id:
        raise HTTPException(status_code=400, detail="Keçərsiz YouTube URL-i.")

    api_url = f"https://{RAPIDAPI_HOST}/v2/video/details"
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }
    params = {
        "videoId": video_id,
        "urlAccess": "normal"
    }

    try:
        response = requests.get(api_url, headers=headers, params=params, timeout=15)
        data = response.json()

        if data.get("errorId") != "Success":
            raise HTTPException(status_code=400, detail="API-dən video məlumatı alına bilmədi.")

        title = data.get("title", "YouTube_Media")
        download_url = None

        if format == "mp3":
            audios = data.get("audios", {}).get("items", [])
            if audios:
                download_url = audios[0].get("url")
        else:
            videos = data.get("videos", {}).get("items", [])
            if videos:
                download_url = videos[0].get("url")

        if not download_url:
            download_url = data.get("downloadUrl") or data.get("url")

        if download_url:
            return {
                "status": "success",
                "title": title,
                "download_url": download_url,
                "format": format
            }
        else:
            raise HTTPException(status_code=400, detail="İndirmə linki tapılmadı.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Xəta baş verdi: {str(e)}")

@app.get("/download-file")
def download_file(url: str, title: str = "media", format: str = "mp3"):
    try:
        req = requests.get(url, stream=True, timeout=30)
        
        clean_title = re.sub(r'[\\/*?:"<>|]', "", title).strip() or "download"
        ext = "mp3" if format == "mp3" else "mp4"
        filename = f"{clean_title}.{ext}"
        
        encoded_filename = quote(filename)
        media_type = "audio/mpeg" if format == "mp3" else "video/mp4"

        headers = {
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
            "Content-Type": media_type
        }

        return StreamingResponse(
            req.iter_content(chunk_size=1024 * 64),
            headers=headers,
            media_type=media_type
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fayl endirilərkən xəta baş verdi: {str(e)}")

if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
