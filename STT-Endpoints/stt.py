from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import os
import requests
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Speech-to-Text API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_WHISPER_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
WHISPER_MODEL = "whisper-large-v3-turbo"


@app.get("/")
def root():
    return {"message": "Speech-to-Text API is running"}


@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.post("/transcribe")
def transcribe_audio(file: UploadFile = File(...)):
    """Transcribe audio using Groq Whisper API. Accepts any format Groq supports (webm, mp4, wav, etc.)."""
    if not GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not configured")

    audio_data = file.file.read()
    if len(audio_data) == 0:
        raise HTTPException(status_code=400, detail="Empty audio file")

    filename = file.filename or "recording.webm"
    content_type = file.content_type or "audio/webm"

    try:
        response = requests.post(
            GROQ_WHISPER_URL,
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            files={"file": (filename, audio_data, content_type)},
            data={"model": WHISPER_MODEL},
            timeout=60,
        )
        if response.status_code != 200:
            logger.error(f"Groq Whisper error: {response.text}")
            raise HTTPException(status_code=500, detail=f"Groq API error: {response.text}")

        transcript = response.json().get("text", "").strip()
        logger.info(f"Transcript: {transcript}")
        return JSONResponse(status_code=200, content={"transcript": transcript})

    except requests.Timeout:
        raise HTTPException(status_code=504, detail="Transcription timed out")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
