from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse, RedirectResponse
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
            clean_title = re.sub(r'[\\/*?:"<>|]', "", title).strip() or "media"
            return {
                "status": "success",
                "title": clean_title,
                "download_url": download_url,
                "format": format
            }
        else:
            raise HTTPException(status_code=400, detail="İndirmə linki tapılmadı.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Xəta baş verdi: {str(e)}")

# BİRBAŞA YÜKLƏMƏ ENDPOINT-i
@app.get("/download")
def proxy_download(url: str, title: str = "media", format: str = "mp3"):
    # Google Serverlərini "browser" olduğumuza inandırmaq üçün mükəmməl başlıqlar
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.youtube.com/",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    try:
        req = requests.get(url, headers=headers, stream=True, timeout=15)
        
        # Əgər uğurla cavab gələrsə, faylı məcburi yükləmə başlığı ilə yönləndirir
        if req.status_code == 200:
            clean_title = re.sub(r'[\\/*?:"<>|]', "", title).strip() or "download"
            filename = f"{clean_title}.{format}"
            encoded_filename = quote(filename)
            
            media_type = "audio/mpeg" if format == "mp3" else "video/mp4"
            
            res_headers = {
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
                "Content-Type": media_type
            }
            
            if "Content-Length" in req.headers:
                res_headers["Content-Length"] = req.headers["Content-Length"]

            return StreamingResponse(
                req.iter_content(chunk_size=1024 * 128),
                headers=res_headers,
                media_type=media_type
            )
        else:
            # IP bloku olarsa əlavə error vermədən linkin özünə atır
            return RedirectResponse(url=url)
    except Exception:
        return RedirectResponse(url=url)

if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
