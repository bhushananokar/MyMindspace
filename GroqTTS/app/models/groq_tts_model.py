"""
TTS model wrapper supporting both Groq API and local Orpheus model.
"""

import os
import asyncio
import logging
import base64
import tempfile
from typing import Optional, Dict, Any, List
from pathlib import Path

from ..config.settings import settings

logger = logging.getLogger(__name__)

# Groq integration
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    logger.warning("Groq library not available. Install with: pip install groq")
    
# Local model fallback imports
try:
    import torch
    import numpy as np
    from transformers import AutoTokenizer, AutoModelForCausalLM
    from snac import SNAC
    import soundfile as sf
    LOCAL_MODEL_AVAILABLE = True
except ImportError:
    LOCAL_MODEL_AVAILABLE = False
    logger.warning("Local model dependencies not available")


class GroqTTSModel:
    """Groq API-based TTS model with local fallback."""
    
    _instance: Optional['GroqTTSModel'] = None
    _initialized: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.groq_client: Optional[Groq] = None
        self.local_model = None
        self.local_snac = None
        self.local_tokenizer = None
        self.use_groq = settings.use_groq
        
        # Available Groq voices
        self.english_voices = [
            "Arista-PlayAI", "Atlas-PlayAI", "Basil-PlayAI", "Briggs-PlayAI",
            "Calum-PlayAI", "Celeste-PlayAI", "Cheyenne-PlayAI", "Chip-PlayAI",
            "Cillian-PlayAI", "Deedee-PlayAI", "Fritz-PlayAI", "Gail-PlayAI",
            "Indigo-PlayAI", "Mamaw-PlayAI", "Mason-PlayAI", "Mikail-PlayAI",
            "Mitch-PlayAI", "Quinn-PlayAI", "Thunder-PlayAI"
        ]
        
        self.arabic_voices = [
            "Ahmad-PlayAI", "Amira-PlayAI", "Khalid-PlayAI", "Nasser-PlayAI"
        ]
        
        self._initialized = True
    
    async def initialize(self):
        """Initialize the TTS model (Groq or local fallback)."""
        logger.info("Initializing TTS model...")
        logger.info(f"use_groq: {self.use_groq}, GROQ_AVAILABLE: {GROQ_AVAILABLE}")
        
        # Force re-initialization to ensure Groq client is set up
        self.groq_client = None
        self.local_model = None
        
        if self.use_groq and GROQ_AVAILABLE:
            await self._initialize_groq()
        else:
            logger.warning("Groq not available or disabled, falling back to local model")
            await self._initialize_local_model()
        
        logger.info("TTS model initialization completed")
    
    async def _initialize_groq(self):
        """Initialize Groq TTS client."""
        logger.info("Starting Groq TTS client initialization...")
        
        try:
            # Get API key from environment variables and settings
            api_key = os.getenv("GROQ_API_KEY") or settings.groq_api_key
            
            if not api_key:
                logger.error("❌ GROQ_API_KEY not found in environment variables or settings")
                logger.error("Please set GROQ_API_KEY in your .env file or environment")
                raise ValueError("Groq API key not found")
            
            logger.info("Creating Groq client...")
            self.groq_client = Groq(api_key=api_key)
            logger.info("Groq client object created successfully")
            
            # Test if client works with a simple call
            logger.info("Testing Groq client with test call...")
            test_response = self.groq_client.audio.speech.create(
                model=settings.groq_model,
                voice=settings.groq_voice,
                input="test",
                response_format="wav"
            )
            logger.info(f"Groq test call successful, response type: {type(test_response)}")
            logger.info("✅ Groq TTS client initialized and tested successfully!")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Groq client: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            self.groq_client = None
            # Don't raise here, let it fall back to local model
            logger.warning("Groq initialization failed, will attempt local model fallback")
    
    async def _test_groq_connection(self):
        """Test Groq API connection with a minimal request."""
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: self.groq_client.audio.speech.create(
                    model=settings.groq_model,
                    voice=settings.groq_voice,
                    input="Test",
                    response_format="wav"
                )
            )
            logger.info("Groq API connection test successful")
        except Exception as e:
            logger.error(f"Groq API connection test failed: {e}")
            raise
    
    async def _initialize_local_model(self):
        """Initialize local Orpheus model as fallback."""
        if not LOCAL_MODEL_AVAILABLE:
            logger.error("Local model dependencies not available")
            logger.error("Please install: pip install torch transformers snac soundfile")
            raise RuntimeError("Neither Groq nor local model dependencies are available")
        
        logger.warning("Groq not available - local model fallback is not fully implemented in this version")
        logger.warning("Please set GROQ_API_KEY to use the TTS service")
        logger.warning("Alternatively, implement local model fallback or disable use_groq in settings")
        
        # For now, raise an error instead of trying to load the complex local model
        raise RuntimeError("Local model fallback not implemented. Please configure Groq API key.")
    
    async def generate_audio(
        self, 
        text: str, 
        voice: Optional[str] = None,
        **kwargs
    ) -> bytes:
        """
        Generate audio from text using Groq API or local model.
        
        Args:
            text: Input text to convert to speech
            voice: Voice to use (Groq voice name or local voice)
            **kwargs: Additional parameters
            
        Returns:
            Audio data as bytes (WAV format)
        """
        logger.info(f"🎵 Generating audio for text: '{text[:50]}...'")
        logger.info(f"use_groq: {self.use_groq}, groq_client exists: {self.groq_client is not None}, local_model exists: {self.local_model is not None}")
        
        # Check if we need to initialize
        if self.use_groq and not self.groq_client:
            logger.warning("Groq client not initialized, attempting initialization...")
            await self.initialize()
        elif not self.use_groq and not self.local_model:
            logger.warning("Local model not initialized, attempting initialization...")
            await self.initialize()
        
        if self.use_groq and self.groq_client:
            logger.info("Using Groq TTS for generation")
            return await self._generate_with_groq(text, voice, **kwargs)
        elif self.local_model:
            logger.info("Using local model for generation")
            return await self._generate_with_local(text, voice, **kwargs)
        else:
            error_msg = f"No TTS model available. use_groq: {self.use_groq}, groq_client exists: {self.groq_client is not None}, local_model exists: {self.local_model is not None}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    async def _generate_with_groq(
        self, 
        text: str, 
        voice: Optional[str] = None,
        **kwargs
    ) -> bytes:
        """Generate audio using Groq API."""
        try:
            # Validate and set voice
            voice = voice or settings.groq_voice
            if voice not in self.english_voices + self.arabic_voices:
                logger.warning(f"Unknown voice {voice}, using default {settings.groq_voice}")
                voice = settings.groq_voice
            
            # Determine model based on voice
            model = settings.groq_model
            if voice in self.arabic_voices:
                model = "playai-tts-arabic"
            
            # Truncate text if too long (Groq has 10K character limit)
            if len(text) > 9000:  # Leave some buffer
                text = text[:9000] + "..."
                logger.warning("Text truncated to fit Groq limits")
            
            logger.info(f"Generating audio with Groq: model={model}, voice={voice}, text_length={len(text)}")
            
            # Run Groq API call in executor to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.groq_client.audio.speech.create(
                    model=model,
                    voice=voice,
                    input=text,
                    response_format="wav"
                )
            )
            
            # Get audio content from Groq response
            # The Groq API returns a binary response that we need to handle properly
            try:
                # For Groq API, we need to use .read() method to get the binary content
                if hasattr(response, 'read'):
                    audio_content = response.read()
                elif hasattr(response, 'content'):
                    audio_content = response.content
                else:
                    # Use write_to_file method and read back
                    import tempfile
                    import os
                    
                    # Create a temporary file
                    temp_fd, temp_path = tempfile.mkstemp(suffix='.wav')
                    try:
                        os.close(temp_fd)  # Close the file descriptor
                        
                        # Write to the temporary file
                        response.write_to_file(temp_path)
                        
                        # Read the file content
                        with open(temp_path, 'rb') as f:
                            audio_content = f.read()
                    finally:
                        # Clean up the temporary file
                        if os.path.exists(temp_path):
                            os.unlink(temp_path)
                        
                logger.info(f"Groq audio generation successful: {len(audio_content)} bytes")
                return audio_content
                
            except Exception as content_error:
                logger.error(f"Error extracting audio content: {content_error}")
                logger.info(f"Response type: {type(response)}")
                logger.info(f"Response attributes: {[attr for attr in dir(response) if not attr.startswith('_')]}")
                raise
            
        except Exception as e:
            logger.error(f"Groq audio generation failed: {e}")
            if self.local_model:
                logger.info("Falling back to local model...")
                return await self._generate_with_local(text, voice, **kwargs)
            else:
                raise RuntimeError(f"Audio generation failed: {e}")
    
    async def _generate_with_local(
        self, 
        text: str, 
        voice: Optional[str] = None,
        **kwargs
    ) -> bytes:
        """Generate audio using local Orpheus model."""
        if not self.local_model:
            raise RuntimeError("Local model not initialized")
        
        logger.info(f"Generating audio with local model: text_length={len(text)}")
        
        # Use the local model's generate method
        audio_data = await self.local_model.generate_audio(text, voice, **kwargs)
        
        return audio_data
    
    def get_supported_voices(self) -> List[str]:
        """Get list of supported voices."""
        if self.use_groq and self.groq_client:
            return self.english_voices + self.arabic_voices
        else:
            return ["tara"]  # Local model default
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        if self.use_groq and self.groq_client:
            return {
                "type": "groq",
                "model": settings.groq_model,
                "default_voice": settings.groq_voice,
                "supported_voices": self.get_supported_voices(),
                "max_characters": 10000
            }
        else:
            return {
                "type": "local",
                "model": settings.model_name,
                "default_voice": settings.default_voice,
                "supported_voices": self.get_supported_voices(),
                "max_characters": None
            }
    
    def cleanup(self):
        """Clean up resources."""
        if self.local_model and hasattr(self.local_model, 'cleanup'):
            self.local_model.cleanup()
        
        self.groq_client = None
        logger.info("TTS model cleanup completed")


# Global model instance
tts_model = GroqTTSModel()