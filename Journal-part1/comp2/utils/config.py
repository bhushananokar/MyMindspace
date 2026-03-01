"""
Configuration management for Component 2: RL Emotion Model
Handles loading, validation, and defaults for all system parameters
"""

import yaml
import json
from pathlib import Path
from typing import Dict, Any, Union, Optional
import logging
from dataclasses import dataclass, asdict
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


@dataclass
class BaseEmotionConfig:
    """Configuration for base emotion detection"""
    model_name: str = "cardiffnlp/twitter-roberta-base-emotion"
    max_sequence_length: int = 512
    emotion_threshold: float = 0.1
    confidence_threshold: float = 0.3
    cache_dir: str = "./models/saved_models"
    device: str = "auto"  # "cpu", "cuda", or "auto"


@dataclass  
class RLConfig:
    """Configuration for RL training"""
    # Algorithm parameters
    algorithm: str = "SAC"
    learning_rate: float = 3e-4
    batch_size: int = 64
    buffer_size: int = 10000
    update_frequency: int = 100
    target_update_interval: int = 1000
    
    # SAC specific
    gamma: float = 0.99  # Discount factor
    tau: float = 0.005   # Soft update coefficient  
    alpha: float = 0.2   # Entropy regularization
    
    # Network architecture
    policy_hidden_dims: list = None
    value_hidden_dims: list = None
    
    # Experience replay
    prioritized_replay: bool = True
    priority_alpha: float = 0.6
    priority_beta: float = 0.4
    priority_beta_increment: float = 0.001
    
    # Training control
    min_experiences_before_training: int = 200
    training_frequency: int = 4
    max_gradient_norm: float = 10.0
    
    def __post_init__(self):
        """Set default network architectures"""
        if self.policy_hidden_dims is None:
            self.policy_hidden_dims = [128, 64]
        if self.value_hidden_dims is None:
            self.value_hidden_dims = [256, 128]


@dataclass
class RewardConfig:
    """Configuration for reward calculation"""
    explicit_weight: float = 0.6
    engagement_weight: float = 0.3
    behavioral_weight: float = 0.1
    
    correction_penalty: float = 0.8
    confirmation_bonus: float = 1.2
    time_decay_hours: float = 24.0
    
    # Reward scaling
    max_reward: float = 10.0
    min_reward: float = -10.0
    reward_normalization: bool = True


@dataclass
class StorageConfig:
    """Configuration for data storage"""
    models_dir: str = "./models/saved_models"
    user_data_dir: str = "./data/user_data"
    experience_buffers_dir: str = "./data/user_data/experience_buffers"
    
    # Auto-save settings
    auto_save_interval: int = 100  # Experiences between saves
    model_save_frequency: int = 1000  # Training steps between model saves
    backup_frequency_hours: int = 24  # Hours between backups
    
    # Retention policy
    max_user_experiences: int = 10000
    experience_retention_days: int = 90
    model_retention_days: int = 365


@dataclass
class LoggingConfig:
    """Configuration for logging"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_logging: bool = True
    log_dir: str = "./logs"
    max_file_size_mb: int = 100
    backup_count: int = 5
    
    # Component-specific logging levels
    emotion_detector_level: str = "INFO"
    rl_trainer_level: str = "INFO"
    experience_buffer_level: str = "WARNING"
    reward_calculator_level: str = "INFO"


@dataclass
class PerformanceConfig:
    """Configuration for performance optimization"""
    # Threading and concurrency
    max_concurrent_users: int = 10
    thread_pool_size: int = 4
    
    # Memory management
    max_memory_mb: int = 2048
    gc_frequency: int = 1000  # Steps between garbage collection
    
    # Caching
    enable_model_caching: bool = True
    cache_size_mb: int = 512
    cache_ttl_hours: int = 24
    
    # Batch processing
    max_batch_size: int = 128
    batch_timeout_ms: int = 100


class ComponentConfig:
    """Main configuration class combining all component configs"""
    
    def __init__(
        self,
        base_emotion: BaseEmotionConfig = None,
        rl: RLConfig = None,
        reward: RewardConfig = None,
        storage: StorageConfig = None,
        logging: LoggingConfig = None,
        performance: PerformanceConfig = None
    ):
        """
        Initialize component configuration
        
        Args:
            base_emotion: Base emotion detection config
            rl: RL training configuration
            reward: Reward calculation configuration  
            storage: Data storage configuration
            logging: Logging configuration
            performance: Performance optimization config
        """
        self.base_emotion = base_emotion or BaseEmotionConfig()
        self.rl = rl or RLConfig()
        self.reward = reward or RewardConfig()
        self.storage = storage or StorageConfig()
        self.logging = logging or LoggingConfig()
        self.performance = performance or PerformanceConfig()
        
        # Validate configuration
        self._validate_config()
    
    def _validate_config(self):
        """Validate configuration consistency"""
        # Check reward weights sum to 1.0
        total_weight = (self.reward.explicit_weight + 
                       self.reward.engagement_weight + 
                       self.reward.behavioral_weight)
        
        if abs(total_weight - 1.0) > 0.01:
            logger.warning(f"Reward weights sum to {total_weight:.3f}, normalizing...")
            self.reward.explicit_weight /= total_weight
            self.reward.engagement_weight /= total_weight
            self.reward.behavioral_weight /= total_weight
        
        # Validate RL parameters
        if self.rl.batch_size > self.rl.buffer_size:
            logger.warning("Batch size larger than buffer size, adjusting...")
            self.rl.batch_size = min(64, self.rl.buffer_size // 4)
        
        # Check directory paths
        for path_attr in ['models_dir', 'user_data_dir', 'experience_buffers_dir']:
            path_val = getattr(self.storage, path_attr)
            Path(path_val).mkdir(parents=True, exist_ok=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'base_emotion': asdict(self.base_emotion),
            'rl': asdict(self.rl),
            'reward': asdict(self.reward),
            'storage': asdict(self.storage),
            'logging': asdict(self.logging),
            'performance': asdict(self.performance)
        }
    
    def save(self, filepath: Union[str, Path]):
        """
        Save configuration to file
        
        Args:
            filepath: Path to save configuration (supports .yaml and .json)
        """
        filepath = Path(filepath)
        config_dict = self.to_dict()
        
        try:
            if filepath.suffix.lower() in ['.yaml', '.yml']:
                with open(filepath, 'w') as f:
                    yaml.dump(config_dict, f, default_flow_style=False, indent=2)
            elif filepath.suffix.lower() == '.json':
                with open(filepath, 'w') as f:
                    json.dump(config_dict, f, indent=2, default=str)
            else:
                raise ValueError(f"Unsupported file format: {filepath.suffix}")
            
            logger.info(f"Saved configuration to {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'ComponentConfig':
        """
        Create configuration from dictionary
        
        Args:
            config_dict: Configuration dictionary
            
        Returns:
            ComponentConfig instance
        """
        return cls(
            base_emotion=BaseEmotionConfig(**config_dict.get('base_emotion', {})),
            rl=RLConfig(**config_dict.get('rl', {})),
            reward=RewardConfig(**config_dict.get('reward', {})),
            storage=StorageConfig(**config_dict.get('storage', {})),
            logging=LoggingConfig(**config_dict.get('logging', {})),
            performance=PerformanceConfig(**config_dict.get('performance', {}))
        )
    
    @classmethod
    def load(cls, filepath: Union[str, Path]) -> 'ComponentConfig':
        """
        Load configuration from file
        
        Args:
            filepath: Path to configuration file
            
        Returns:
            ComponentConfig instance
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            logger.warning(f"Configuration file {filepath} not found, using defaults")
            return cls()
        
        try:
            if filepath.suffix.lower() in ['.yaml', '.yml']:
                with open(filepath, 'r') as f:
                    config_dict = yaml.safe_load(f)
            elif filepath.suffix.lower() == '.json':
                with open(filepath, 'r') as f:
                    config_dict = json.load(f)
            else:
                raise ValueError(f"Unsupported file format: {filepath.suffix}")
            
            logger.info(f"Loaded configuration from {filepath}")
            return cls.from_dict(config_dict or {})
            
        except Exception as e:
            logger.error(f"Failed to load configuration from {filepath}: {e}")
            logger.info("Using default configuration")
            return cls()
    
    def update_from_dict(self, updates: Dict[str, Any]):
        """
        Update configuration from dictionary (partial updates)
        
        Args:
            updates: Dictionary with configuration updates
        """
        for section, values in updates.items():
            if hasattr(self, section) and isinstance(values, dict):
                section_obj = getattr(self, section)
                for key, value in values.items():
                    if hasattr(section_obj, key):
                        setattr(section_obj, key, value)
                    else:
                        logger.warning(f"Unknown config key: {section}.{key}")
            else:
                logger.warning(f"Unknown config section: {section}")
        
        # Re-validate after updates
        self._validate_config()
    
    def get_device(self) -> str:
        """
        Get the appropriate device for computation
        
        Returns:
            Device string ('cpu' or 'cuda')
        """
        import torch
        
        device_config = self.base_emotion.device.lower()
        
        if device_config == "auto":
            return 'cuda' if torch.cuda.is_available() else 'cpu'
        elif device_config in ['cpu', 'cuda']:
            if device_config == 'cuda' and not torch.cuda.is_available():
                logger.warning("CUDA requested but not available, using CPU")
                return 'cpu'
            return device_config
        else:
            logger.warning(f"Unknown device config: {device_config}, using auto")
            return 'cuda' if torch.cuda.is_available() else 'cpu'


def load_config(filepath: Union[str, Path] = "config.yaml") -> ComponentConfig:
    """
    Convenience function to load configuration
    
    Args:
        filepath: Path to configuration file
        
    Returns:
        ComponentConfig instance
    """
    return ComponentConfig.load(filepath)


def create_default_config(filepath: Union[str, Path] = "config.yaml"):
    """
    Create a default configuration file
    
    Args:
        filepath: Where to save the default configuration
    """
    config = ComponentConfig()
    config.save(filepath)
    logger.info(f"Created default configuration at {filepath}")


def validate_config_file(filepath: Union[str, Path]) -> Dict[str, list]:
    """
    Validate configuration file and return any issues
    
    Args:
        filepath: Path to configuration file
        
    Returns:
        Dictionary with 'errors' and 'warnings' lists
    """
    issues = {'errors': [], 'warnings': []}
    
    try:
        config = ComponentConfig.load(filepath)
        
        # Check required directories exist or can be created
        for attr in ['models_dir', 'user_data_dir', 'experience_buffers_dir']:
            path = Path(getattr(config.storage, attr))
            try:
                path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                issues['errors'].append(f"Cannot create directory {path}: {e}")
        
        # Check RL parameter ranges
        if not 0 < config.rl.learning_rate < 1:
            issues['warnings'].append(f"Learning rate {config.rl.learning_rate} outside typical range")
        
        if not 0.9 < config.rl.gamma < 1.0:
            issues['warnings'].append(f"Gamma {config.rl.gamma} outside typical range")
        
        # Check memory limits
        if config.performance.max_memory_mb < 512:
            issues['warnings'].append("Memory limit very low, may cause performance issues")
        
        logger.info(f"Configuration validation completed: {len(issues['errors'])} errors, {len(issues['warnings'])} warnings")
        
    except Exception as e:
        issues['errors'].append(f"Failed to load configuration: {e}")
    
    return issues


# Configuration presets for different deployment scenarios
DEVELOPMENT_CONFIG = {
    'rl': {
        'buffer_size': 1000,
        'batch_size': 32,
        'learning_rate': 1e-3,
        'update_frequency': 50
    },
    'logging': {
        'level': 'DEBUG',
        'emotion_detector_level': 'DEBUG',
        'rl_trainer_level': 'DEBUG'
    },
    'performance': {
        'max_concurrent_users': 3,
        'max_memory_mb': 1024
    }
}

PRODUCTION_CONFIG = {
    'rl': {
        'buffer_size': 50000,
        'batch_size': 128,
        'learning_rate': 3e-4,
        'update_frequency': 200
    },
    'logging': {
        'level': 'INFO',
        'experience_buffer_level': 'ERROR'
    },
    'performance': {
        'max_concurrent_users': 50,
        'max_memory_mb': 8192,
        'enable_model_caching': True
    }
}

TESTING_CONFIG = {
    'rl': {
        'buffer_size': 100,
        'batch_size': 16,
        'min_experiences_before_training': 20
    },
    'storage': {
        'auto_save_interval': 10,
        'model_save_frequency': 50
    },
    'logging': {
        'level': 'WARNING'
    }
}