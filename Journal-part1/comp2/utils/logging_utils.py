"""
Logging utilities for Component 2: RL Emotion Model
Provides structured logging, performance monitoring, and privacy-safe logging
"""

import logging
import logging.handlers
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Union
import json
import traceback
from functools import wraps
import time
import threading
from contextlib import contextmanager

from .config import LoggingConfig


class PrivacyFilter(logging.Filter):
    """Filter to remove potentially sensitive information from logs"""
    
    SENSITIVE_PATTERNS = [
        # Email addresses
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        # Phone numbers (various formats)
        r'\b(?:\+?1[-.\s]?)?(?:\([0-9]{3}\)|[0-9]{3})[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b',
        # Social Security Numbers
        r'\b\d{3}-\d{2}-\d{4}\b',
        # Credit card numbers (basic pattern)
        r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
        # User IDs that might be sensitive
        r'user_id["\s]*[:=]["\s]*([a-zA-Z0-9]+)',
        # API keys and tokens
        r'(?:api_key|token|secret)["\s]*[:=]["\s]*([a-zA-Z0-9+/=]+)'
    ]
    
    def __init__(self):
        super().__init__()
        import re
        self.patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.SENSITIVE_PATTERNS]
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Filter out sensitive information from log records"""
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            filtered_msg = record.msg
            
            # Replace sensitive patterns with placeholders
            for i, pattern in enumerate(self.patterns):
                if i == 4:  # user_id pattern
                    filtered_msg = pattern.sub(r'user_id: [REDACTED]', filtered_msg)
                elif i == 5:  # API key pattern
                    filtered_msg = pattern.sub(r'\1: [REDACTED]', filtered_msg)
                else:
                    filtered_msg = pattern.sub('[REDACTED]', filtered_msg)
            
            record.msg = filtered_msg
        
        return True


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging with JSON output option"""
    
    def __init__(self, json_format: bool = False, include_extra: bool = True):
        self.json_format = json_format
        self.include_extra = include_extra
        
        if json_format:
            super().__init__()
        else:
            super().__init__(
                fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
    
    def format(self, record: logging.LogRecord) -> str:
        if not self.json_format:
            return super().format(record)
        
        # Create structured log entry
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add thread information
        if hasattr(record, 'thread'):
            log_entry['thread_id'] = record.thread
            log_entry['thread_name'] = getattr(record, 'threadName', 'Unknown')
        
        # Add exception information
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # Add custom fields
        if self.include_extra:
            extra_fields = {}
            for key, value in record.__dict__.items():
                if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                              'filename', 'module', 'lineno', 'funcName', 'created', 
                              'msecs', 'relativeCreated', 'thread', 'threadName', 
                              'processName', 'process', 'exc_info', 'exc_text', 'stack_info']:
                    extra_fields[key] = value
            
            if extra_fields:
                log_entry['extra'] = extra_fields
        
        return json.dumps(log_entry, default=str)


class PerformanceLogger:
    """Specialized logger for performance metrics and monitoring"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.metrics: Dict[str, list] = {}
        self.lock = threading.Lock()
    
    def log_timing(self, operation: str, duration_ms: float, **kwargs):
        """Log timing information for operations"""
        with self.lock:
            if operation not in self.metrics:
                self.metrics[operation] = []
            
            self.metrics[operation].append({
                'duration_ms': duration_ms,
                'timestamp': datetime.now().isoformat(),
                **kwargs
            })
            
            # Keep only recent metrics (last 1000 entries)
            if len(self.metrics[operation]) > 1000:
                self.metrics[operation] = self.metrics[operation][-1000:]
        
        self.logger.info(
            f"Performance: {operation} completed in {duration_ms:.2f}ms",
            extra={'operation': operation, 'duration_ms': duration_ms, **kwargs}
        )
    
    def log_memory_usage(self, operation: str, memory_mb: float, **kwargs):
        """Log memory usage information"""
        self.logger.info(
            f"Memory: {operation} using {memory_mb:.2f}MB",
            extra={'operation': operation, 'memory_mb': memory_mb, **kwargs}
        )
    
    def get_performance_stats(self, operation: str) -> Dict[str, float]:
        """Get performance statistics for an operation"""
        with self.lock:
            if operation not in self.metrics or not self.metrics[operation]:
                return {}
            
            durations = [m['duration_ms'] for m in self.metrics[operation]]
            
            return {
                'count': len(durations),
                'mean_ms': sum(durations) / len(durations),
                'min_ms': min(durations),
                'max_ms': max(durations),
                'p95_ms': sorted(durations)[int(0.95 * len(durations))] if len(durations) >= 20 else max(durations)
            }
    
    def clear_metrics(self, operation: Optional[str] = None):
        """Clear performance metrics"""
        with self.lock:
            if operation:
                self.metrics.pop(operation, None)
            else:
                self.metrics.clear()


class LoggingManager:
    """Main logging manager for Component 2"""
    
    def __init__(self, config: LoggingConfig):
        self.config = config
        self.loggers: Dict[str, logging.Logger] = {}
        self.performance_loggers: Dict[str, PerformanceLogger] = {}
        self.initialized = False
        
        self._setup_logging()
    
    def _setup_logging(self):
        """Initialize logging configuration"""
        if self.initialized:
            return
        
        # Create log directory
        log_dir = Path(self.config.log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.config.level.upper()))
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, self.config.level.upper()))
        console_formatter = StructuredFormatter(json_format=False)
        console_handler.setFormatter(console_formatter)
        console_handler.addFilter(PrivacyFilter())
        root_logger.addHandler(console_handler)
        
        # File handler (if enabled)
        if self.config.file_logging:
            file_handler = logging.handlers.RotatingFileHandler(
                filename=log_dir / "component2_rl_emotion.log",
                maxBytes=self.config.max_file_size_mb * 1024 * 1024,
                backupCount=self.config.backup_count
            )
            file_handler.setLevel(getattr(logging, self.config.level.upper()))
            file_formatter = StructuredFormatter(json_format=True, include_extra=True)
            file_handler.setFormatter(file_formatter)
            file_handler.addFilter(PrivacyFilter())
            root_logger.addHandler(file_handler)
        
        # Component-specific loggers
        self._setup_component_loggers()
        
        self.initialized = True
        logging.info("Logging manager initialized")
    
    def _setup_component_loggers(self):
        """Setup component-specific loggers with individual levels"""
        component_configs = {
            'emotion_detector': self.config.emotion_detector_level,
            'rl_trainer': self.config.rl_trainer_level,
            'experience_buffer': self.config.experience_buffer_level,
            'reward_calculator': self.config.reward_calculator_level
        }
        
        for component, level in component_configs.items():
            logger = logging.getLogger(f"component2.{component}")
            logger.setLevel(getattr(logging, level.upper()))
            self.loggers[component] = logger
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get logger for specific component or module"""
        if name in self.loggers:
            return self.loggers[name]
        
        # Create new logger
        logger = logging.getLogger(f"component2.{name}")
        logger.setLevel(getattr(logging, self.config.level.upper()))
        self.loggers[name] = logger
        
        return logger
    
    def get_performance_logger(self, name: str) -> PerformanceLogger:
        """Get performance logger for specific component"""
        if name not in self.performance_loggers:
            base_logger = self.get_logger(f"{name}_performance")
            self.performance_loggers[name] = PerformanceLogger(base_logger)
        
        return self.performance_loggers[name]
    
    def update_log_level(self, component: str, level: str):
        """Update log level for specific component"""
        if component in self.loggers:
            self.loggers[component].setLevel(getattr(logging, level.upper()))
            logging.info(f"Updated log level for {component} to {level}")
    
    def get_log_stats(self) -> Dict[str, Any]:
        """Get logging statistics"""
        stats = {
            'total_loggers': len(self.loggers),
            'performance_loggers': len(self.performance_loggers),
            'log_level': self.config.level,
            'file_logging_enabled': self.config.file_logging
        }
        
        # Add performance stats
        perf_stats = {}
        for name, perf_logger in self.performance_loggers.items():
            component_stats = {}
            for operation in perf_logger.metrics.keys():
                component_stats[operation] = perf_logger.get_performance_stats(operation)
            perf_stats[name] = component_stats
        
        stats['performance_metrics'] = perf_stats
        
        return stats


# Global logging manager instance
_logging_manager: Optional[LoggingManager] = None


def setup_logging(config: LoggingConfig) -> LoggingManager:
    """
    Setup logging for the entire component
    
    Args:
        config: Logging configuration
        
    Returns:
        LoggingManager instance
    """
    global _logging_manager
    _logging_manager = LoggingManager(config)
    return _logging_manager


def get_logger(name: str) -> logging.Logger:
    """
    Get logger for component or module
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    if _logging_manager is None:
        # Use default logging config if not initialized
        setup_logging(LoggingConfig())
    
    return _logging_manager.get_logger(name)


def get_performance_logger(name: str) -> PerformanceLogger:
    """
    Get performance logger for component
    
    Args:
        name: Component name
        
    Returns:
        PerformanceLogger instance
    """
    if _logging_manager is None:
        setup_logging(LoggingConfig())
    
    return _logging_manager.get_performance_logger(name)


@contextmanager
def log_timing(logger: Union[logging.Logger, PerformanceLogger], operation: str, **kwargs):
    """
    Context manager for timing operations
    
    Args:
        logger: Logger instance
        operation: Operation name
        **kwargs: Additional context
    """
    start_time = time.time()
    try:
        yield
    finally:
        duration_ms = (time.time() - start_time) * 1000
        
        if isinstance(logger, PerformanceLogger):
            logger.log_timing(operation, duration_ms, **kwargs)
        else:
            logger.info(f"{operation} completed in {duration_ms:.2f}ms", 
                       extra={'operation': operation, 'duration_ms': duration_ms, **kwargs})


def log_exception(logger: logging.Logger, operation: str, exception: Exception, **kwargs):
    """
    Log exception with context
    
    Args:
        logger: Logger instance
        operation: Operation that failed
        exception: Exception that occurred
        **kwargs: Additional context
    """
    logger.error(
        f"{operation} failed: {type(exception).__name__}: {str(exception)}",
        exc_info=True,
        extra={'operation': operation, 'exception_type': type(exception).__name__, **kwargs}
    )


def timing_decorator(logger: Union[logging.Logger, PerformanceLogger], operation: str = None):
    """
    Decorator for timing function execution
    
    Args:
        logger: Logger instance
        operation: Operation name (defaults to function name)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            op_name = operation or f"{func.__module__}.{func.__name__}"
            
            with log_timing(logger, op_name):
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


class UserActivityLogger:
    """Specialized logger for user activity (privacy-conscious)"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def log_user_action(self, user_id: str, action: str, **context):
        """
        Log user action with privacy protection
        
        Args:
            user_id: User identifier (will be hashed)
            action: Action performed
            **context: Additional context (sensitive data filtered)
        """
        # Hash user ID for privacy
        import hashlib
        hashed_user_id = hashlib.sha256(user_id.encode()).hexdigest()[:8]
        
        # Filter sensitive context
        safe_context = {}
        for key, value in context.items():
            if key.lower() in ['email', 'phone', 'address', 'ssn']:
                safe_context[key] = '[REDACTED]'
            elif isinstance(value, str) and len(value) > 100:
                safe_context[key] = value[:50] + '...[TRUNCATED]'
            else:
                safe_context[key] = value
        
        self.logger.info(
            f"User action: {action}",
            extra={
                'user_hash': hashed_user_id,
                'action': action,
                'context': safe_context,
                'timestamp': datetime.now().isoformat()
            }
        )
    
    def log_training_event(self, user_id: str, event_type: str, metrics: Dict[str, float]):
        """
        Log training events with metrics
        
        Args:
            user_id: User identifier
            event_type: Type of training event
            metrics: Training metrics
        """
        import hashlib
        hashed_user_id = hashlib.sha256(user_id.encode()).hexdigest()[:8]
        
        self.logger.info(
            f"Training event: {event_type}",
            extra={
                'user_hash': hashed_user_id,
                'event_type': event_type,
                'metrics': metrics,
                'timestamp': datetime.now().isoformat()
            }
        )


def create_user_activity_logger() -> UserActivityLogger:
    """Create user activity logger with privacy protection"""
    logger = get_logger('user_activity')
    return UserActivityLogger(logger)