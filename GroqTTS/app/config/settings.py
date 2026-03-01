"""
Configuration management for TTS microservice.
"""

import os
from typing import Optional, Any


class Settings:
    """Application settings with environment variable support."""
    
    def __init__(self):
        # Load .env file if it exists
        self._load_env_file()
    
    def _load_env_file(self):
        """Load .env file if it exists."""
        env_file = '.env'
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        # Only set if not already in environment
                        if key.strip() not in os.environ:
                            os.environ[key.strip()] = value.strip()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get setting value from environment variables."""
        value = os.getenv(key, default)
        
        # Convert string boolean values
        if isinstance(value, str):
            if value.lower() in ('true', '1', 'yes', 'on'):
                return True
            elif value.lower() in ('false', '0', 'no', 'off'):
                return False
        
        return value
    
    # Server configuration
    @property
    def host(self) -> str:
        return self.get('TTS_HOST', '0.0.0.0')
    
    @property
    def port(self) -> int:
        return int(self.get('TTS_PORT', 8000))
    
    @property
    def debug(self) -> bool:
        return self.get('TTS_DEBUG', False)
    
    @property
    def log_level(self) -> str:
        return self.get('TTS_LOG_LEVEL', 'INFO')
    
    # TTS configuration
    @property
    def use_groq(self) -> bool:
        return self.get('TTS_USE_GROQ', True)
    
    @property
    def groq_api_key(self) -> Optional[str]:
        return self.get('GROQ_API_KEY')
    
    @property
    def groq_model(self) -> str:
        return self.get('TTS_GROQ_MODEL', 'playai-tts')
    
    @property
    def groq_voice(self) -> str:
        return self.get('TTS_GROQ_VOICE', 'Fritz-PlayAI')
    
    @property
    def max_concurrent_connections(self) -> int:
        return int(self.get('TTS_MAX_CONCURRENT_CONNECTIONS', 10))
    
    @property
    def max_text_length(self) -> int:
        return int(self.get('TTS_MAX_TEXT_LENGTH', 9000))
    
    @property
    def chunk_size(self) -> int:
        return int(self.get('TTS_CHUNK_SIZE', 200))
    
    @property
    def chunk_size_words(self) -> int:
        return int(self.get('TTS_CHUNK_SIZE_WORDS', 15))
    
    # Legacy properties for backward compatibility
    @property
    def model_name(self) -> str:
        return "canopylabs/orpheus-3b-0.1-ft"
    
    @property
    def snac_model_name(self) -> str:
        return "hubertsiuzdak/snac_24khz"
    
    @property
    def hf_token(self) -> Optional[str]:
        return self.get('HF_TOKEN') or self.get('TTS_HF_TOKEN')
    
    @property
    def default_voice(self) -> str:
        return "tara"
    
    @property
    def sample_rate(self) -> int:
        return 24000
    
    @property
    def websocket_timeout(self) -> int:
        return 60
    
    @property
    def chunk_timeout_seconds(self) -> int:
        return 10


# Global settings instance
settings = Settings()