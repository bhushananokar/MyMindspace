"""
Shared utilities for Gemini Engine Components 6 & 7.
Production-ready utility functions for common operations.
"""

import asyncio
import logging
import time
import uuid
import re
from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
from functools import wraps
import json
import hashlib
import tiktoken
from dataclasses import asdict
import yaml
from pathlib import Path


# ============================================================================
# LOGGING AND MONITORING UTILITIES
# ============================================================================

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name"""
    return logging.getLogger(f"gemini_engine.{name}")


def log_execution_time(func):
    """Decorator to log function execution time"""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            execution_time = (time.time() - start_time) * 1000
            logger = get_logger(func.__module__)
            logger.info(f"{func.__name__} executed in {execution_time:.2f}ms")
            return result
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger = get_logger(func.__module__)
            logger.error(f"{func.__name__} failed after {execution_time:.2f}ms: {e}")
            raise
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = (time.time() - start_time) * 1000
            logger = get_logger(func.__module__)
            logger.info(f"{func.__name__} executed in {execution_time:.2f}ms")
            return result
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger = get_logger(func.__module__)
            logger.error(f"{func.__name__} failed after {execution_time:.2f}ms: {e}")
            raise
    
    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper


def generate_correlation_id() -> str:
    """Generate a unique correlation ID for request tracking"""
    return str(uuid.uuid4())


def log_with_correlation_id(correlation_id: str, level: str, message: str, **kwargs):
    """Log message with correlation ID for request tracking"""
    logger = get_logger("correlation")
    log_data = {
        "correlation_id": correlation_id,
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
        **kwargs
    }
    
    if level.upper() == "DEBUG":
        logger.debug(json.dumps(log_data))
    elif level.upper() == "INFO":
        logger.info(json.dumps(log_data))
    elif level.upper() == "WARNING":
        logger.warning(json.dumps(log_data))
    elif level.upper() == "ERROR":
        logger.error(json.dumps(log_data))
    elif level.upper() == "CRITICAL":
        logger.critical(json.dumps(log_data))


# ============================================================================
# TOKEN COUNTING AND TEXT PROCESSING
# ============================================================================

class TokenCounter:
    """Efficient token counting for various text formats"""
    
    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        """Initialize token counter with specified model"""
        try:
            self.encoding = tiktoken.encoding_for_model(model_name)
        except KeyError:
            # Fallback to cl100k_base encoding
            self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text string"""
        if not text:
            return 0
        return len(self.encoding.encode(text))
    
    def count_tokens_list(self, texts: List[str]) -> int:
        """Count total tokens in list of texts"""
        return sum(self.count_tokens(text) for text in texts)
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate tokens using character count (faster approximation)"""
        if not text:
            return 0
        # Rough approximation: 1 token ≈ 4 characters for English text
        return len(text) // 4
    
    def truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        """Truncate text to fit within token limit"""
        if self.count_tokens(text) <= max_tokens:
            return text
        
        # Binary search for optimal truncation
        left, right = 0, len(text)
        while left < right:
            mid = (left + right + 1) // 2
            truncated = text[:mid]
            if self.count_tokens(truncated) <= max_tokens:
                left = mid
            else:
                right = mid - 1
        
        return text[:left]


# ============================================================================
# TEXT PROCESSING UTILITIES
# ============================================================================

def clean_text(text: str) -> str:
    """Clean and normalize text for processing"""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove control characters
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    
    # Normalize quotes and dashes
    text = text.replace('"', '"').replace('"', '"')
    text = text.replace(''', "'").replace(''', "'")
    text = text.replace('–', '-').replace('—', '-')
    
    return text


def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """Extract key terms from text for context matching"""
    if not text:
        return []
    
    # Remove common stop words
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those'
    }
    
    # Clean and tokenize
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    
    # Filter and count
    word_counts = {}
    for word in words:
        if word not in stop_words and len(word) > 2:
            word_counts[word] = word_counts.get(word, 0) + 1
    
    # Return top keywords
    sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
    return [word for word, count in sorted_words[:max_keywords]]


def summarize_text(text: str, max_length: int = 200) -> str:
    """Create a concise summary of text"""
    if not text or len(text) <= max_length:
        return text
    
    # Simple sentence-based summarization
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    summary = ""
    for sentence in sentences:
        if len(summary + sentence) <= max_length:
            summary += sentence + ". "
        else:
            break
    
    return summary.strip()


def detect_language(text: str) -> str:
    """Detect the primary language of text (simplified)"""
    if not text:
        return "unknown"
    
    # Simple language detection based on character patterns
    text_lower = text.lower()
    
    # Check for common language indicators
    if re.search(r'[а-яё]', text):
        return "russian"
    elif re.search(r'[一-龯]', text):
        return "chinese"
    elif re.search(r'[あ-ん]', text):
        return "japanese"
    elif re.search(r'[가-힣]', text):
        return "korean"
    elif re.search(r'[à-ÿ]', text):
        return "french"
    elif re.search(r'[äöüß]', text):
        return "german"
    elif re.search(r'[ñáéíóúü]', text):
        return "spanish"
    else:
        return "english"


# ============================================================================
# MEMORY AND CONTEXT UTILITIES
# ============================================================================

def calculate_memory_relevance(
    memory_content: str,
    current_context: str,
    memory_metadata: Dict[str, Any]
) -> float:
    """Calculate relevance score for memory in current context"""
    if not memory_content or not current_context:
        return 0.0
    
    # Extract keywords from both texts
    memory_keywords = set(extract_keywords(memory_content))
    context_keywords = set(extract_keywords(current_context))
    
    if not memory_keywords or not context_keywords:
        return 0.0
    
    # Calculate Jaccard similarity
    intersection = len(memory_keywords & context_keywords)
    union = len(memory_keywords | context_keywords)
    
    if union == 0:
        return 0.0
    
    base_relevance = intersection / union
    
    # Apply metadata adjustments
    relevance = base_relevance
    
    # Time decay (older memories less relevant)
    if 'created_at' in memory_metadata:
        age_days = (datetime.utcnow() - memory_metadata['created_at']).days
        time_decay = max(0.1, 1.0 - (age_days / 365.0) * 0.5)
        relevance *= time_decay
    
    # Importance boost
    if 'importance_score' in memory_metadata:
        importance_boost = 1.0 + (memory_metadata['importance_score'] - 0.5) * 0.5
        relevance *= importance_boost
    
    # Emotional significance
    if 'emotional_significance' in memory_metadata:
        emotional_boost = 1.0 + memory_metadata['emotional_significance'] * 0.3
        relevance *= emotional_boost
    
    return min(1.0, max(0.0, relevance))


def compress_memories(
    memories: List[Dict[str, Any]],
    max_tokens: int,
    token_counter: TokenCounter
) -> Tuple[List[Dict[str, Any]], int]:
    """Compress memories to fit within token budget"""
    if not memories:
        return [], 0
    
    # Sort by relevance and importance
    sorted_memories = sorted(
        memories,
        key=lambda m: (
            m.get('relevance_score', 0),
            m.get('importance_score', 0),
            m.get('emotional_significance', 0)
        ),
        reverse=True
    )
    
    compressed_memories = []
    total_tokens = 0
    
    for memory in sorted_memories:
        # Try to add full memory
        memory_text = format_memory_for_context(memory)
        memory_tokens = token_counter.count_tokens(memory_text)
        
        if total_tokens + memory_tokens <= max_tokens:
            compressed_memories.append(memory)
            total_tokens += memory_tokens
        else:
            # Try compressed version
            compressed_memory = compress_single_memory(memory, token_counter)
            compressed_tokens = token_counter.count_tokens(compressed_memory)
            
            if total_tokens + compressed_tokens <= max_tokens:
                compressed_memories.append({
                    **memory,
                    'content_summary': compressed_memory,
                    'compressed': True
                })
                total_tokens += compressed_tokens
            else:
                break
    
    return compressed_memories, total_tokens


def format_memory_for_context(memory: Dict[str, Any]) -> str:
    """Format memory for inclusion in context"""
    template = """Memory: {type} - {summary}
Importance: {importance}/10
Emotional Significance: {emotional}/10
Last Accessed: {last_accessed}
Related Topics: {topics}
Context: {context}"""
    
    return template.format(
        type=memory.get('memory_type', 'unknown'),
        summary=memory.get('content_summary', ''),
        importance=int(memory.get('importance_score', 0) * 10),
        emotional=int(memory.get('emotional_significance', 0) * 10),
        last_accessed=memory.get('last_accessed', 'unknown'),
        topics=', '.join(memory.get('retrieval_triggers', [])),
        context=memory.get('context_needed', '')
    )


def compress_single_memory(memory: Dict[str, Any], token_counter: TokenCounter) -> str:
    """Compress a single memory to fit token constraints"""
    summary = memory.get('content_summary', '')
    if not summary:
        return ""
    
    # Try different compression levels
    compression_levels = [0.8, 0.6, 0.4, 0.2]
    
    for level in compression_levels:
        target_length = int(len(summary) * level)
        compressed = summarize_text(summary, target_length)
        
        if token_counter.count_tokens(compressed) <= 50:  # Target token limit
            return compressed
    
    # Fallback to minimal compression
    return summarize_text(summary, 100)


# ============================================================================
# CONFIGURATION AND YAML UTILITIES
# ============================================================================

def load_yaml_config(file_path: str) -> Dict[str, Any]:
    """Load YAML configuration file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found: {file_path}")
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in configuration file: {e}")


def save_yaml_config(config: Dict[str, Any], file_path: str):
    """Save configuration to YAML file"""
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            yaml.dump(config, file, default_flow_style=False, indent=2)
    except Exception as e:
        raise RuntimeError(f"Failed to save configuration file: {e}")


# ============================================================================
# ERROR HANDLING AND VALIDATION
# ============================================================================

class GeminiEngineError(Exception):
    """Base exception for Gemini Engine errors"""
    pass


class ConfigurationError(GeminiEngineError):
    """Configuration-related errors"""
    pass


class TokenLimitError(GeminiEngineError):
    """Token limit exceeded errors"""
    pass


class MemoryRetrievalError(GeminiEngineError):
    """Memory retrieval and processing errors"""
    pass


class APIError(GeminiEngineError):
    """External API errors"""
    pass


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> bool:
    """Validate that required fields are present in data"""
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    
    if missing_fields:
        raise ValueError(f"Missing required fields: {missing_fields}")
    
    return True


def safe_get_nested(data: Dict[str, Any], path: List[str], default: Any = None) -> Any:
    """Safely get nested dictionary value"""
    current = data
    for key in path:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current


# ============================================================================
# PERFORMANCE AND CACHING UTILITIES
# ============================================================================

class SimpleCache:
    """Simple in-memory cache with TTL"""
    
    def __init__(self, default_ttl: int = 3600):
        self.cache = {}
        self.default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        if key in self.cache:
            value, expiry = self.cache[key]
            if datetime.utcnow() < expiry:
                return value
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache with TTL"""
        if ttl is None:
            ttl = self.default_ttl
        
        expiry = datetime.utcnow() + timedelta(seconds=ttl)
        self.cache[key] = (value, expiry)
    
    def delete(self, key: str):
        """Delete key from cache"""
        if key in self.cache:
            del self.cache[key]
    
    def clear(self):
        """Clear all cached items"""
        self.cache.clear()
    
    def size(self) -> int:
        """Get current cache size"""
        return len(self.cache)


def rate_limit_decorator(max_calls: int, time_window: int):
    """Decorator for rate limiting function calls"""
    def decorator(func):
        calls = []
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            
            # Remove expired calls
            calls[:] = [call_time for call_time in calls if now - call_time < time_window]
            
            if len(calls) >= max_calls:
                raise RuntimeError(f"Rate limit exceeded: {max_calls} calls per {time_window} seconds")
            
            calls.append(now)
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


# ============================================================================
# ASYNC UTILITIES
# ============================================================================

async def with_timeout(coro, timeout_seconds: float, default_value: Any = None):
    """Execute coroutine with timeout"""
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        return default_value


async def batch_process(items: List[Any], processor_func, batch_size: int = 10, max_concurrent: int = 5):
    """Process items in batches with concurrency control"""
    results = []
    
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        
        # Process batch with concurrency limit
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_item(item):
            async with semaphore:
                return await processor_func(item)
        
        batch_results = await asyncio.gather(*[process_item(item) for item in batch])
        results.extend(batch_results)
    
    return results


# ============================================================================
# HASHING AND IDENTIFICATION
# ============================================================================

def generate_content_hash(content: str) -> str:
    """Generate SHA-256 hash of content for deduplication"""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def generate_memory_id(user_id: str, content: str, timestamp: datetime) -> str:
    """Generate unique memory ID based on content and context"""
    content_hash = generate_content_hash(content)
    timestamp_str = timestamp.strftime('%Y%m%d_%H%M%S')
    return f"{user_id}_{content_hash[:8]}_{timestamp_str}"


# ============================================================================
# DATETIME UTILITIES
# ============================================================================

def format_timestamp(timestamp: datetime) -> str:
    """Format timestamp for human-readable display"""
    now = datetime.utcnow()
    diff = now - timestamp
    
    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    else:
        return "just now"


def is_recent(timestamp: datetime, hours: int = 24) -> bool:
    """Check if timestamp is within specified hours"""
    return datetime.utcnow() - timestamp < timedelta(hours=hours)


def get_time_bucket(timestamp: datetime, bucket_hours: int = 1) -> str:
    """Get time bucket identifier for grouping"""
    bucket_start = timestamp.replace(
        minute=0, second=0, microsecond=0
    )
    return bucket_start.strftime('%Y-%m-%d_%H')
