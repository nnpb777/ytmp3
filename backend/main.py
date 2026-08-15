from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import re
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
STATIC_DIR = os.path.join(BASE_DIR, "frontend")

@app.get("/")
def index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

@app.get("/convert")
def convert_video(url: str, format: str = "mp3"):
    if not url:
        raise HTTPException(status_code=400, detail="YouTube URL daxil edin.")

    # YouTube URL yoxlanışı
    if "youtube.com" not in url and "youtu.be" not in url:
        raise HTTPException(status_code=400, detail="Düzgün YouTube keçidi daxil edin.")

    # yt-dlp konfiqurasiyası
    ydl_opts = {
        'format': 'bestaudio/best' if format == "mp3" else 'best[ext=mp4]/best',
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            title = info.get('title', 'YouTube_Media')
            clean_title = re.sub(r'[\\/*?:"<>|]', "", title).strip() or "media"
            
            download_url = None
            
            # Formatdan asılı olaraq birbaşa yayım linkini tapırıq
            if 'url' in info:
                download_url = info['url']
            elif 'requested_formats' in info and len(info['requested_formats']) > 0:
                download_url = info['requested_formats'][0]['url']
            elif 'formats' in info and len(info['formats']) > 0:
                download_url = info['formats'][-1]['url']

            if download_url:
                return {
                    "status": "success",
                    "title": clean_title,
                    "download_url": download_url,
                    "format": format
                }
            else:
                raise HTTPException(status_code=400, detail="İndirmə linki yaradıla bilmədi.")

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Video məlumatı alına bilmədi: {str(e)}")

if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
