from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import requests

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

COBALT_API_URL = "https://api.cobalt.tools"

@app.get("/")
def index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

@app.get("/convert")
def convert_video(url: str, format: str = "mp3"):
    if not url:
        raise HTTPException(status_code=400, detail="YouTube URL daxil edin.")

    payload = {
        "url": url,
        "downloadMode": "audio" if format == "mp3" else "auto",
        "audioFormat": "mp3",
        "videoQuality": "720"
    }

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(COBALT_API_URL, json=payload, headers=headers, timeout=15)
        
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Video məlumatı alına bilmədi. Linki yoxlayın.")

        data = response.json()
        
        status = data.get("status")
        download_url = data.get("url")

        if status in ("tunnel", "redirect", "picker") and download_url:
            return {
                "status": "success",
                "title": data.get("filename", "YouTube_Media"),
                "download_url": download_url,
                "format": format
            }
        else:
            raise HTTPException(status_code=400, detail="İndirmə keçidi yaradıla bilmədi.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Xəta baş verdi: {str(e)}")

if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
