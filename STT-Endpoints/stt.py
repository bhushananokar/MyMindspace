from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import websocket
import json
import threading
import time
import wave
import io
import asyncio
from urllib.parse import urlencode
from datetime import datetime
from typing import Optional
import logging
import os
from dotenv import load_dotenv
load_dotenv()
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Speech-to-Text API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
API_KEY = os.getenv("PLAY_API_KEY")
CONNECTION_PARAMS = {
    "sample_rate": 16000,
    "format_turns": True
}
API_ENDPOINT_BASE_URL = "wss://streaming.assemblyai.com/v3/ws"
API_ENDPOINT = f"{API_ENDPOINT_BASE_URL}?{urlencode(CONNECTION_PARAMS)}"

class SpeechToTextProcessor:
    def __init__(self):
        self.ws = None
        self.transcript_parts = []
        self.final_transcript = ""
        self.is_connected = False
        self.processing_complete = False
        self.error_message = None
        self.lock = threading.Lock()
        
    def on_open(self, ws):
        """Called when the WebSocket connection is established."""
        logger.info("WebSocket connection opened")
        self.is_connected = True
        
    def on_message(self, ws, message):
        try:
            data = json.loads(message)
            msg_type = data.get('type')
            
            with self.lock:
                if msg_type == "Begin":
                    session_id = data.get('id')
                    logger.info(f"Session began: ID={session_id}")
                    
                elif msg_type == "Turn":
                    transcript = data.get('transcript', '')
                    formatted = data.get('turn_is_formatted', False)
                    
                    if formatted and transcript:
                        self.transcript_parts.append(transcript)
                        logger.info(f"Received transcript: {transcript}")
                        
                elif msg_type == "Termination":
                    self.final_transcript = " ".join(self.transcript_parts)
                    self.processing_complete = True
                    logger.info("Session terminated")
                    
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding message: {e}")
            with self.lock:
                self.error_message = f"JSON decode error: {e}"
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            with self.lock:
                self.error_message = f"Message handling error: {e}"
    
    def on_error(self, ws, error):
        """Called when a WebSocket error occurs."""
        logger.error(f"WebSocket Error: {error}")
        with self.lock:
            self.error_message = str(error)
            self.processing_complete = True
    
    def on_close(self, ws, close_status_code, close_msg):
        """Called when the WebSocket connection is closed."""
        logger.info(f"WebSocket closed: Status={close_status_code}, Msg={close_msg}")
        with self.lock:
            self.is_connected = False
            self.processing_complete = True
    
    async def process_audio_data(self, audio_data: bytes, sample_rate: int = 16000) -> dict:
        """Process audio data and return transcript."""
        self.transcript_parts = []
        self.final_transcript = ""
        self.processing_complete = False
        self.error_message = None
        self.is_connected = False
        
        # Create WebSocket connection
        self.ws = websocket.WebSocketApp(
            API_ENDPOINT,
            header={"Authorization": API_KEY},
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
        )
        
        # Run WebSocket in a separate thread
        ws_thread = threading.Thread(target=self.ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()
        
        # Wait for connection
        max_wait_time = 10  # seconds
        start_time = time.time()
        while not self.is_connected and time.time() - start_time < max_wait_time:
            await asyncio.sleep(0.1)
        
        if not self.is_connected:
            return {"success": False, "error": "Failed to connect to speech service"}
        
        try:
            # Send audio data in chunks
            chunk_size = 1600  # 100ms of 16kHz audio (0.1s * 16000Hz * 2 bytes)
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i + chunk_size]
                if self.ws and self.ws.sock and self.ws.sock.connected:
                    self.ws.send(chunk, websocket.ABNF.OPCODE_BINARY)
                    await asyncio.sleep(0.01)  # Small delay between chunks
                else:
                    break
            
            # Send termination message
            if self.ws and self.ws.sock and self.ws.sock.connected:
                terminate_message = {"type": "Terminate"}
                self.ws.send(json.dumps(terminate_message))
            
            # Wait for processing to complete
            max_processing_time = 30  # seconds
            start_time = time.time()
            while not self.processing_complete and time.time() - start_time < max_processing_time:
                await asyncio.sleep(0.1)
            
            # Close WebSocket
            if self.ws:
                self.ws.close()
            
            # Return results
            with self.lock:
                if self.error_message:
                    return {"success": False, "error": self.error_message}
                else:
                    return {
                        "success": True, 
                        "transcript": self.final_transcript or " ".join(self.transcript_parts),
                        
                    }
                    
        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            if self.ws:
                self.ws.close()
            return {"success": False, "error": f"Processing error: {e}"}

# Global processor instance
processor = SpeechToTextProcessor()

def convert_audio_to_16khz_mono(audio_data: bytes, original_format: str = "wav") -> bytes:
    """Convert audio to 16kHz mono PCM format required by AssemblyAI."""
    try:
        # Read the uploaded audio file
        audio_io = io.BytesIO(audio_data)
        
        with wave.open(audio_io, 'rb') as wf:
            # Get original parameters
            channels = wf.getnchannels()
            sample_width = wf.getsampwidth()
            framerate = wf.getframerate()
            frames = wf.readframes(wf.getnframes())
            
            logger.info(f"Original audio: {channels} channels, {framerate}Hz, {sample_width} bytes per sample")
            
            # If already in the right format, return as is
            if channels == 1 and framerate == 16000 and sample_width == 2:
                return frames
            
            # For now, we'll assume the audio is in a compatible format
            # In a production environment, you'd want to use a library like pydub
            # to handle various audio formats and conversions
            
            # Simple conversion for common cases
            if sample_width == 2 and framerate == 16000:
                if channels == 2:
                    # Convert stereo to mono by taking every other sample
                    import struct
                    samples = struct.unpack('<' + 'h' * (len(frames) // 2), frames)
                    mono_samples = samples[::2]  # Take left channel
                    return struct.pack('<' + 'h' * len(mono_samples), *mono_samples)
                else:
                    return frames
            
            # For other cases, return original and let AssemblyAI handle it
            return frames
            
    except Exception as e:
        logger.error(f"Error converting audio: {e}")
        # Return original data if conversion fails
        return audio_data

@app.get("/")
async def root():
    return {"message": "Speech-to-Text API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Transcribe audio file to text.
    
    Supports common audio formats (WAV, MP3, etc.)
    Audio will be converted to 16kHz mono PCM as required by AssemblyAI.
    """
    try:
        # Validate file type
        allowed_types = ["audio/wav", "audio/mpeg", "audio/mp3", "audio/ogg", "audio/webm"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type: {file.content_type}. Supported types: {allowed_types}"
            )
        
        # Read uploaded file
        audio_data = await file.read()
        
        if len(audio_data) == 0:
            raise HTTPException(status_code=400, detail="Empty audio file")
        
        # Convert audio to required format
        processed_audio = convert_audio_to_16khz_mono(audio_data)
        
        # Process the audio
        result = await processor.process_audio_data(processed_audio)
        
        if result["success"]:
            return JSONResponse(
                status_code=200,
                content={
                    "transcript": result["transcript"],
                }
            )
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in transcribe_audio: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

@app.post("/transcribe-raw")
async def transcribe_raw_audio(file: UploadFile = File(...)):
    """
    Transcribe raw PCM audio data.
    Expected format: 16kHz, mono, 16-bit PCM
    """
    try:
        if file.content_type != "application/octet-stream":
            raise HTTPException(
                status_code=400, 
                detail="Raw audio endpoint expects application/octet-stream content type"
            )
        
        # Read the raw PCM data
        audio_data = await file.read()
        
        if len(audio_data) == 0:
            raise HTTPException(status_code=400, detail="Empty audio data")
        
        # Process the audio directly (assuming it's already in the right format)
        result = await processor.process_audio_data(audio_data)
        
        if result["success"]:
            return JSONResponse(
                status_code=200,
                content={
                    "transcript": result["transcript"],
                }
            )
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in transcribe_raw_audio: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)