"""
Utility functions for the TTS microservice.
"""

import time
import functools
import logging
from typing import Callable, Any

logger = logging.getLogger(__name__)


def timing_decorator(func: Callable) -> Callable:
    """Decorator to measure function execution time."""
    @functools.wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"{func.__name__} executed in {execution_time:.2f} seconds")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.2f} seconds: {e}")
            raise
    
    @functools.wraps(func)
    def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"{func.__name__} executed in {execution_time:.2f} seconds")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.2f} seconds: {e}")
            raise
    
    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper


def format_audio_duration(seconds: float) -> str:
    """Format audio duration in a human-readable format."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.1f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours}h {minutes}m {secs:.1f}s"


def validate_text_input(text: str, max_length: int = 10000) -> tuple[bool, str]:
    """
    Validate text input for TTS processing.
    
    Args:
        text: Input text to validate
        max_length: Maximum allowed text length
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not text:
        return False, "Text cannot be empty"
    
    if not isinstance(text, str):
        return False, "Text must be a string"
    
    if len(text.strip()) == 0:
        return False, "Text cannot be only whitespace"
    
    if len(text) > max_length:
        return False, f"Text too long (max {max_length} characters)"
    
    # Check for potentially problematic characters
    if '\x00' in text:
        return False, "Text contains null characters"
    
    return True, ""


import asyncio