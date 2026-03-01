# config/settings.py (REPLACE EXISTING - SIMPLIFIED VERSION)
"""
Simplified Configuration for Gemini Engine Components 5, 6 & 7
No PostgreSQL or Redis dependencies - focuses on core functionality
"""

import os
from dataclasses import dataclass
from typing import Dict, Any, Optional
import logging

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
@dataclass
class GeminiAPIConfig:
    """Gemini API configuration"""
    api_key: str
    model_name: str = "gemini-1.5-pro"
    base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    max_tokens: int = 2048
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    timeout_seconds: int = 30
    max_retries: int = 3
    # ADD THESE MISSING ATTRIBUTES:
    rate_limit_requests_per_minute: int = 60
    rate_limit_tokens_per_minute: int = 15000
    supports_system_prompt: bool = True
    safety_settings: Dict[str, str] = None  # This is the missing one!

    def __post_init__(self):
        """Set default safety settings if none provided"""
        if self.safety_settings is None:
            self.safety_settings = {
                "HARM_CATEGORY_HARASSMENT": "BLOCK_MEDIUM_AND_ABOVE",
                "HARM_CATEGORY_HATE_SPEECH": "BLOCK_MEDIUM_AND_ABOVE", 
                "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_MEDIUM_AND_ABOVE",
                "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_MEDIUM_AND_ABOVE"
            }


@dataclass  
class Component5LSTMConfig:
    """Component 5 LSTM Memory Gates configuration"""
    # Astra DB settings (only database we need)
    astra_endpoint: str
    astra_token: str
    astra_keyspace: str = "default_keyspace"
    
    # LSTM Gate settings
    gate_input_size: int = 90
    gate_hidden_size: int = 128
    gate_dropout_rate: float = 0.1
    
    # Memory thresholds
    forget_threshold: float = 0.3
    input_threshold: float = 0.4
    output_threshold: float = 0.4
    
    # Context settings
    max_context_tokens: int = 2000
    max_memories_per_context: int = 20


@dataclass
class PerformanceConfig:
    """Performance configuration"""
    # Timeouts (in milliseconds)
    total_response_timeout_ms: int = 30000
    context_assembly_timeout_ms: int = 5000
    memory_retrieval_timeout_ms: int = 3000
    gemini_api_timeout_ms: int = 20000
    
    # Limits
    max_memories_per_context: int = 20
    max_context_tokens: int = 2000
    max_conversation_history: int = 50


@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_handler: bool = True
    console_handler: bool = True
    log_file_path: str = "logs/gemini_engine.log"


@dataclass
class PersonalityConfig:
    """Personality configuration"""
    default_communication_style: str = "friendly"
    default_response_length: str = "moderate"
    default_emotional_matching: bool = True
    default_humor_preference: float = 0.7
    default_formality_level: float = 0.3
    default_conversation_depth: float = 0.8


class Settings:
    """Simplified settings class without database dependencies"""
    
    def __init__(self):
        self.gemini_api = self._load_gemini_config()
        self.component5_lstm = self._load_component5_config()
        self.performance = self._load_performance_config()
        self.logging = self._load_logging_config()
        self.personality = self._load_personality_config()
        
        # Set up logging
        self._setup_logging()
    
    def _load_gemini_config(self) -> GeminiAPIConfig:
        """Load Gemini API configuration"""
        return GeminiAPIConfig(
            api_key=os.getenv("GEMINI_API_KEY", ""),
            model_name=os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-pro"),
            max_tokens=int(os.getenv("GEMINI_MAX_TOKENS", "2048")),
            temperature=float(os.getenv("GEMINI_TEMPERATURE", "0.7")),
            top_p=float(os.getenv("GEMINI_TOP_P", "0.9")),
            top_k=int(os.getenv("GEMINI_TOP_K", "40")),
            timeout_seconds=int(os.getenv("GEMINI_TIMEOUT", "30")),
            max_retries=int(os.getenv("GEMINI_MAX_RETRIES", "3")),
            # ADD THE MISSING ATTRIBUTES:
            rate_limit_requests_per_minute=int(os.getenv("GEMINI_RATE_LIMIT_RPM", "60")),
            rate_limit_tokens_per_minute=int(os.getenv("GEMINI_RATE_LIMIT_TPM", "15000")),
            supports_system_prompt=os.getenv("GEMINI_SUPPORTS_SYSTEM_PROMPT", "true").lower() == "true",
            safety_settings=None  # Will use defaults from __post_init__
        )
    
    def _load_component5_config(self) -> Component5LSTMConfig:
        """Load Component 5 configuration"""
        return Component5LSTMConfig(
            astra_endpoint=os.getenv("ASTRA_DB_API_ENDPOINT", ""),
            astra_token=os.getenv("ASTRA_DB_TOKEN", ""),
            astra_keyspace=os.getenv("KEYSPACE", "default_keyspace"),
            
            gate_input_size=int(os.getenv("LSTM_INPUT_SIZE", "90")),
            gate_hidden_size=int(os.getenv("LSTM_HIDDEN_SIZE", "128")),
            gate_dropout_rate=float(os.getenv("LSTM_DROPOUT", "0.1")),
            
            forget_threshold=float(os.getenv("FORGET_THRESHOLD", "0.3")),
            input_threshold=float(os.getenv("INPUT_THRESHOLD", "0.4")),
            output_threshold=float(os.getenv("OUTPUT_THRESHOLD", "0.4")),
            
            max_context_tokens=int(os.getenv("MAX_CONTEXT_TOKENS", "2000")),
            max_memories_per_context=int(os.getenv("MAX_MEMORIES_PER_CONTEXT", "20"))
        )
    
    def _load_performance_config(self) -> PerformanceConfig:
        """Load performance configuration"""
        return PerformanceConfig(
            total_response_timeout_ms=int(os.getenv("TOTAL_RESPONSE_TIMEOUT_MS", "30000")),
            context_assembly_timeout_ms=int(os.getenv("CONTEXT_ASSEMBLY_TIMEOUT_MS", "5000")),
            memory_retrieval_timeout_ms=int(os.getenv("MEMORY_RETRIEVAL_TIMEOUT_MS", "3000")),
            gemini_api_timeout_ms=int(os.getenv("GEMINI_API_TIMEOUT_MS", "20000")),
            
            max_memories_per_context=int(os.getenv("MAX_MEMORIES_PER_CONTEXT", "20")),
            max_context_tokens=int(os.getenv("MAX_CONTEXT_TOKENS", "2000")),
            max_conversation_history=int(os.getenv("MAX_CONVERSATION_HISTORY", "50"))
        )
    
    def _load_logging_config(self) -> LoggingConfig:
        """Load logging configuration"""
        return LoggingConfig(
            level=os.getenv("LOG_LEVEL", "INFO"),
            format=os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
            file_handler=bool(os.getenv("LOG_TO_FILE", "true").lower() == "true"),
            console_handler=bool(os.getenv("LOG_TO_CONSOLE", "true").lower() == "true"),
            log_file_path=os.getenv("LOG_FILE_PATH", "logs/gemini_engine.log")
        )
    
    def _load_personality_config(self) -> PersonalityConfig:
        """Load personality configuration"""
        return PersonalityConfig(
            default_communication_style=os.getenv("DEFAULT_COMMUNICATION_STYLE", "friendly"),
            default_response_length=os.getenv("DEFAULT_RESPONSE_LENGTH", "moderate"),
            default_emotional_matching=bool(os.getenv("DEFAULT_EMOTIONAL_MATCHING", "true").lower() == "true"),
            default_humor_preference=float(os.getenv("DEFAULT_HUMOR_PREFERENCE", "0.7")),
            default_formality_level=float(os.getenv("DEFAULT_FORMALITY_LEVEL", "0.3")),
            default_conversation_depth=float(os.getenv("DEFAULT_CONVERSATION_DEPTH", "0.8"))
        )
    
    def _setup_logging(self):
        """Configure logging"""
        # Create logs directory if it doesn't exist
        log_dir = os.path.dirname(self.logging.log_file_path)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Configure logging
        logging.basicConfig(
            level=getattr(logging, self.logging.level.upper()),
            format=self.logging.format
        )
    
    def validate_configuration(self) -> Dict[str, Any]:
        """Validate essential configuration"""
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Check required settings
        if not self.gemini_api.api_key:
            validation_results["errors"].append("GEMINI_API_KEY is required")
            validation_results["valid"] = False
        
        if not self.component5_lstm.astra_endpoint:
            validation_results["errors"].append("ASTRA_DB_API_ENDPOINT is required")
            validation_results["valid"] = False
        
        if not self.component5_lstm.astra_token:
            validation_results["errors"].append("ASTRA_DB_TOKEN is required")
            validation_results["valid"] = False
        
        return validation_results


# Global settings instance
settings = Settings()