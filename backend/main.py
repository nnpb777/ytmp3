from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os
import yt_dlp
import uuid
import re

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
DOWNLOAD_DIR = BASE_DIR / "backend" / "downloads"

DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)


def clean_filename(name):
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = re.sub(r"\s+", " ", name)
    return name.strip()


# =========================
# FRONTEND
# =========================

app.mount(
    "/static",
    StaticFiles(directory=str(FRONTEND_DIR)),
    name="static"
)


@app.get("/")
def home():
    return FileResponse(
        str(FRONTEND_DIR / "index.html")
    )


# =========================
# CONVERT
# =========================

@app.get("/convert")
def convert(url: str, format: str = "mp3"):

    if not url:
        raise HTTPException(
            status_code=400,
            detail="YouTube link daxil edilməyib."
        )

    if format not in ["mp3", "mp4"]:
        raise HTTPException(
            status_code=400,
            detail="Format səhvdir."
        )

    if "youtube.com" not in url and "youtu.be" not in url:
        raise HTTPException(
            status_code=400,
            detail="YouTube linki daxil edin."
        )

    job_id = uuid.uuid4().hex

    try:

        if format == "mp3":

            output = str(
                DOWNLOAD_DIR / f"{job_id}.%(ext)s"
            )

            options = {
                "format": "bestaudio/best",
                "outtmpl": output,
                "noplaylist": True,

                "quiet": False,
                "no_warnings": False,

                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ],

                "postprocessor_args": [
                    "-ar", "44100",
                    "-ac", "2"
                ],
            }

        else:

            output = str(
                DOWNLOAD_DIR / f"{job_id}.%(ext)s"
            )

            options = {
                "format":
                    "bestvideo[ext=mp4]+bestaudio[ext=m4a]/"
                    "best[ext=mp4]/best",

                "outtmpl": output,

                "merge_output_format": "mp4",

                "noplaylist": True,

                "quiet": False,
                "no_warnings": False,
            }


        print("\n==============================")
        print("DOWNLOAD STARTED")
        print("URL:", url)
        print("FORMAT:", format)
        print("==============================\n")


        with yt_dlp.YoutubeDL(options) as ydl:

            info = ydl.extract_info(
                url,
                download=True
            )

            title = info.get(
                "title",
                "YouTube Media"
            )


        # =========================
        # FIND RESULT FILE
        # =========================

        if format == "mp3":

            file_path = (
                DOWNLOAD_DIR /
                f"{job_id}.mp3"
            )

        else:

            file_path = (
                DOWNLOAD_DIR /
                f"{job_id}.mp4"
            )


        if not file_path.exists():

            files = list(
                DOWNLOAD_DIR.glob(
                    f"{job_id}.*"
                )
            )

            if not files:

                raise HTTPException(
                    status_code=500,
                    detail="Fayl yaradılmadı."
                )

            file_path = files[0]


        print("\nDOWNLOAD FINISHED:")
        print(file_path)
        print("==============================\n")


        return {
            "status": "success",

            "title": title,

            "filename":
                clean_filename(title),

            "file_key":
                file_path.name,

            "format":
                format
        }


    except Exception as e:

        print("\nDOWNLOAD ERROR:")
        print(str(e))
        print("==============================\n")

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# =========================
# DOWNLOAD FILE
# =========================

@app.get("/download/{filename}")
def download_file(filename: str):

    # təhlükəsizlik
    if (
        ".." in filename
        or "/" in filename
        or "\\" in filename
    ):
        raise HTTPException(
            status_code=400,
            detail="Yanlış fayl."
        )


    file_path = (
        DOWNLOAD_DIR / filename
    )


    if not file_path.exists():

        raise HTTPException(
            status_code=404,
            detail="Fayl tapılmadı."
        )


    if file_path.suffix.lower() not in [
        ".mp3",
        ".mp4"
    ]:

        raise HTTPException(
            status_code=400,
            detail="Fayl formatı dəstəklənmir."
        )


    return FileResponse(
        path=str(file_path),

        filename=file_path.name,

        media_type="application/octet-stream"
    )


# =========================
# HEALTH
# =========================

@app.get("/health")
def health():

    return {
        "status": "online"
    }

# Production entrypoint:
# The hosting provider supplies PORT; locally it defaults to 8000.
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8000"))
    )
