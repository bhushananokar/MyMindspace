import os
from pathlib import Path

class Config:
    # API
    HOST = "0.0.0.0"
    PORT = 8000
    DEBUG = True
    
    # Paths
    BASE_DIR = Path(__file__).parent
    TEMP_DIR = BASE_DIR / "temp"
    LOGS_DIR = BASE_DIR / "logs"
    MEDITATION_CSV = BASE_DIR / "Core_engine" / "meditation.csv"
    
    # MeditationDB API Configuration
    MEDITATIONDB_API_URL = os.getenv("MEDITATIONDB_API_URL", "https://meditationdb-api-222233295505.asia-south1.run.app")
    MEDITATIONDB_API_TIMEOUT = int(os.getenv("MEDITATIONDB_API_TIMEOUT", "30"))
    
    # API Collections (for reference - handled by API client)
    USERS_COLLECTION = "users"
    SESSIONS_COLLECTION = "sessions" 
    VECTORS_COLLECTION = "vectors"
    FEEDBACK_COLLECTION = "feedback"
    HISTORY_COLLECTION = "history"
    
    # Vector similarity
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    VECTOR_DIMENSION = 384
    
    # Audio processing
    AUDIO_SAMPLE_RATE = 22050
    MAX_AUDIO_SIZE_MB = 10
    SUPPORTED_AUDIO_FORMATS = [".wav", ".mp3", ".m4a", ".flac"]
    
    # Session
    SESSION_TIMEOUT = 1800  # 30 minutes
    
    # Gemini API (optional)
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    
    @classmethod
    def setup_directories(cls):
        cls.TEMP_DIR.mkdir(exist_ok=True)
        cls.LOGS_DIR.mkdir(exist_ok=True)

config = Config()
