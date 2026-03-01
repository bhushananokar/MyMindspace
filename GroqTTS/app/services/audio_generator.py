"""
Audio generation service that combines text processing and TTS model.
"""

import asyncio
import logging
import numpy as np
from typing import List, Dict, Any, AsyncGenerator, Optional
from ..models.tts_model import tts_model
from .text_processor import text_processor
from ..config.settings import settings

logger = logging.getLogger(__name__)


class AudioGenerator:
    """Handles audio generation with chunking and streaming."""
    
    def __init__(self):
        self.is_initialized = False
    
    async def initialize(self):
        """Initialize the audio generation service."""
        if not self.is_initialized:
            logger.info("Initializing audio generator...")
            await tts_model.initialize()
            self.is_initialized = True
            logger.info("Audio generator initialized successfully")
    
    async def generate_audio_stream(
        self,
        text: str,
        voice: str = None,
        parameters: Dict[str, Any] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generate audio stream with chunk-by-chunk processing.
        
        Args:
            text: Input text to convert to speech
            voice: Voice to use for generation
            parameters: Generation parameters (temperature, max_tokens, etc.)
            
        Yields:
            Dict containing chunk information and audio data
        """
        if not self.is_initialized:
            await self.initialize()
        
        voice = voice or (settings.groq_voice if settings.use_groq else settings.default_voice)
        parameters = parameters or {}
        
        try:
            # Process text into chunks
            logger.info(f"Processing text for TTS: {text[:100]}{'...' if len(text) > 100 else ''}")
            
            # Clean the text first
            cleaned_text = text_processor.clean_text(text)
            
            if not cleaned_text:
                logger.warning("No valid text after cleaning")
                yield {
                    "type": "error",
                    "message": "No valid text to process after cleaning",
                    "chunk_id": 0,
                    "total_chunks": 0
                }
                return
            
            # Use smaller chunks for Groq API to get faster responses
            if settings.use_groq:
                chunks = text_processor.create_micro_chunks(cleaned_text, settings.chunk_size_words)
            else:
                _, chunks = text_processor.prepare_for_tts(cleaned_text, voice)
            
            if not chunks:
                logger.warning("No valid chunks generated from text")
                yield {
                    "type": "error",
                    "message": "No valid text to process",
                    "chunk_id": 0,
                    "total_chunks": 0
                }
                return
            
            total_chunks = len(chunks)
            logger.info(f"Generated {total_chunks} chunks for processing")
            
            # Process each chunk
            for i, chunk in enumerate(chunks):
                chunk_id = i + 1
                
                try:
                    logger.info(f"Generating audio for chunk {chunk_id}/{total_chunks}: '{chunk[:30]}{'...' if len(chunk) > 30 else ''}'")
                    start_time = asyncio.get_event_loop().time()
                    
                    # Generate audio for this chunk using Groq or local model
                    audio_data = await tts_model.generate_audio(
                        text=chunk,
                        voice=voice,
                        **parameters  # Pass all parameters to the model
                    )
                    
                    generation_time = asyncio.get_event_loop().time() - start_time
                    logger.info(f"Chunk {chunk_id} generated in {generation_time:.2f} seconds")
                    
                    # Yield control to allow WebSocket keepalive
                    await asyncio.sleep(0.001)
                    
                    if len(audio_data) == 0:
                        logger.warning(f"No audio generated for chunk {chunk_id}")
                        yield {
                            "type": "error",
                            "message": f"Failed to generate audio for chunk {chunk_id}",
                            "chunk_id": chunk_id,
                            "total_chunks": total_chunks,
                            "text_chunk": chunk
                        }
                        continue
                    
                    # Convert audio bytes to base64 for transmission
                    import base64
                    audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                    
                    # Estimate audio length (rough approximation for Groq)
                    # Groq returns WAV files, so we estimate based on typical speech rates
                    estimated_length = len(chunk.split()) * 0.6  # ~0.6 seconds per word
                    # Yield chunk data
                    yield {
                        "type": "audio_chunk",
                        "data": {
                            "chunk_id": chunk_id,
                            "total_chunks": total_chunks,
                            "text_chunk": chunk,
                            "audio_data": audio_base64,
                            "sample_rate": settings.sample_rate,
                            "is_final": chunk_id == total_chunks,
                            "audio_length_seconds": estimated_length
                        }
                    }
                    
                    logger.info(f"Successfully generated chunk {chunk_id}/{total_chunks} "
                              f"({len(audio_data) / settings.sample_rate:.2f}s)")
                    
                except Exception as e:
                    logger.error(f"Error generating audio for chunk {chunk_id}: {e}")
                    yield {
                        "type": "error",
                        "message": f"Error generating audio for chunk {chunk_id}: {str(e)}",
                        "chunk_id": chunk_id,
                        "total_chunks": total_chunks,
                        "text_chunk": chunk
                    }
            
            # Send completion message
            yield {
                "type": "generation_complete",
                "data": {
                    "total_chunks_processed": total_chunks,
                    "original_text": cleaned_text,
                    "voice_used": voice
                }
            }
            
        except Exception as e:
            logger.error(f"Audio generation failed: {e}")
            yield {
                "type": "error",
                "message": f"Audio generation failed: {str(e)}",
                "chunk_id": 0,
                "total_chunks": 0
            }
        
        finally:
            # Clean up GPU memory
            tts_model.cleanup()
    
    async def generate_single_audio(
        self,
        text: str,
        voice: str = None,
        parameters: Dict[str, Any] = None
    ) -> Optional[np.ndarray]:
        """
        Generate audio for a single text input without chunking.
        
        Args:
            text: Input text
            voice: Voice to use
            parameters: Generation parameters
            
        Returns:
            Audio data as numpy array or None if failed
        """
        if not self.is_initialized:
            await self.initialize()
        
        voice = voice or settings.default_voice
        parameters = parameters or {}
        
        try:
            # Clean the text
            cleaned_text = text_processor.clean_text(text)
            
            if not cleaned_text:
                logger.warning("No valid text to process")
                return None
            
            # Generate audio
            audio_data = await tts_model.generate_audio(
                text=cleaned_text,
                voice=voice,
                max_tokens=parameters.get('max_tokens'),
                temperature=parameters.get('temperature'),
                top_p=parameters.get('top_p'),
                repetition_penalty=parameters.get('repetition_penalty')
            )
            
            return audio_data if len(audio_data) > 0 else None
            
        except Exception as e:
            logger.error(f"Single audio generation failed: {e}")
            return None
        
        finally:
            tts_model.cleanup()


# Global audio generator instance
audio_generator = AudioGenerator()