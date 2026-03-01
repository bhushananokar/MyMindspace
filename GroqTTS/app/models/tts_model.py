"""
TTS model wrapper - Updated to use Groq API with local fallback.
"""

# Import the new Groq-based model
from .groq_tts_model import tts_model

# Export for backward compatibility
__all__ = ['tts_model']