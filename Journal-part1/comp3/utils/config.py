import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
import sys

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

class Config:
    """Configuration management for Component 3"""
    
    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            # Look for config.yaml in the root directory
            config_path = Path(__file__).parent.parent / "config.yaml"
        
        self.config_path = Path(config_path)
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        if not self.config_path.exists():
            print(f"Config file not found at {self.config_path}, using defaults")
            return self._get_default_config()
        
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Merge with defaults to ensure all keys exist
            default_config = self._get_default_config()
            merged_config = self._deep_merge(default_config, config)
            return merged_config
            
        except Exception as e:
            print(f"Error loading config from {self.config_path}: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'models': {
                'spacy_model': 'en_core_web_lg',
                'primary_embedding_model': 'all-mpnet-base-v2',
                'lightweight_embedding_model': 'all-MiniLM-L6-v2'
            },
            'performance': {
                'max_processing_time_ms': 300,
                'embedding_cache_size': 10000,
                'batch_size': 32
            },
            'entity_extraction': {
                'person_confidence_threshold': 0.7,
                'location_confidence_threshold': 0.6,
                'organization_confidence_threshold': 0.6,
                'max_entities_per_type': 20
            },
            'event_extraction': {
                'confidence_threshold': 0.5,
                'max_future_days': 365,
                'event_importance_threshold': 0.3,
                'followup_generation': True
            },
            'embedding_settings': {
                'cache_enabled': True,
                'similarity_threshold': 0.8,
                'max_text_length': 5000
            },
            'temporal_analysis': {
                'anomaly_detection': True,
                'pattern_analysis': True,
                'cyclical_encoding': True
            },
            'database': {
                'event_storage_enabled': True,
                'retention_days': 730,
                'encryption_enabled': True
            }
        }
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation
        Example: config.get('models.spacy_model')
        """
        keys = key_path.split('.')
        value = self._config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any):
        """
        Set configuration value using dot notation
        Example: config.set('models.spacy_model', 'en_core_web_sm')
        """
        keys = key_path.split('.')
        target = self._config
        
        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in target:
                target[key] = {}
            target = target[key]
        
        # Set the final value
        target[keys[-1]] = value
    
    def update_from_env(self):
        """Update configuration from environment variables"""
        env_mappings = {
            'COMPONENT3_SPACY_MODEL': 'models.spacy_model',
            'COMPONENT3_EMBEDDING_MODEL': 'models.primary_embedding_model',
            'COMPONENT3_CACHE_SIZE': 'performance.embedding_cache_size',
            'COMPONENT3_BATCH_SIZE': 'performance.batch_size',
            'COMPONENT3_MAX_TEXT_LENGTH': 'embedding_settings.max_text_length'
        }
        
        for env_var, config_key in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                # Convert to appropriate type
                if config_key.endswith('_size') or config_key.endswith('_length'):
                    try:
                        env_value = int(env_value)
                    except ValueError:
                        continue
                
                self.set(config_key, env_value)
                print(f"Updated {config_key} from environment: {env_value}")
    
    def save_config(self, path: Optional[str] = None):
        """Save current configuration to file"""
        save_path = Path(path) if path else self.config_path
        
        try:
            with open(save_path, 'w') as f:
                yaml.dump(self._config, f, default_flow_style=False, indent=2)
            print(f"Configuration saved to {save_path}")
        except Exception as e:
            print(f"Error saving configuration: {e}")
    
    def validate(self) -> bool:
        """Validate configuration values"""
        issues = []
        
        # Check required model names
        required_models = [
            'models.spacy_model',
            'models.primary_embedding_model', 
            'models.lightweight_embedding_model'
        ]
        
        for model_key in required_models:
            if not self.get(model_key):
                issues.append(f"Missing required model: {model_key}")
        
        # Check numeric ranges
        numeric_checks = [
            ('performance.max_processing_time_ms', 50, 5000),
            ('performance.embedding_cache_size', 100, 50000),
            ('performance.batch_size', 1, 256),
            ('entity_extraction.person_confidence_threshold', 0.0, 1.0),
            ('event_extraction.max_future_days', 1, 3650),
            ('embedding_settings.max_text_length', 100, 50000)
        ]
        
        for key, min_val, max_val in numeric_checks:
            value = self.get(key)
            if value is not None and not (min_val <= value <= max_val):
                issues.append(f"{key} ({value}) should be between {min_val} and {max_val}")
        
        if issues:
            print("Configuration validation issues:")
            for issue in issues:
                print(f"  - {issue}")
            return False
        
        print("Configuration validation passed")
        return True
    
    def get_model_config(self) -> Dict[str, str]:
        """Get model configuration"""
        return {
            'spacy_model': self.get('models.spacy_model'),
            'primary_embedding_model': self.get('models.primary_embedding_model'),
            'lightweight_embedding_model': self.get('models.lightweight_embedding_model')
        }
    
    def get_performance_config(self) -> Dict[str, Any]:
        """Get performance configuration"""
        return {
            'max_processing_time_ms': self.get('performance.max_processing_time_ms'),
            'embedding_cache_size': self.get('performance.embedding_cache_size'),
            'batch_size': self.get('performance.batch_size')
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Get configuration as dictionary"""
        return self._config.copy()
    
    def __getitem__(self, key: str) -> Any:
        """Allow dictionary-style access"""
        return self._config[key]
    
    def __setitem__(self, key: str, value: Any):
        """Allow dictionary-style setting"""
        self._config[key] = value
    
    def __contains__(self, key: str) -> bool:
        """Check if key exists in configuration"""
        return key in self._config


# Global configuration instance
_global_config = None

def get_config(config_path: Optional[str] = None) -> Config:
    """Get global configuration instance"""
    global _global_config
    
    if _global_config is None:
        _global_config = Config(config_path)
        _global_config.update_from_env()  # Apply environment overrides
    
    return _global_config

def reload_config(config_path: Optional[str] = None):
    """Reload global configuration"""
    global _global_config
    _global_config = Config(config_path)
    _global_config.update_from_env()

# Convenience functions
def get_setting(key_path: str, default: Any = None) -> Any:
    """Get a configuration setting"""
    return get_config().get(key_path, default)

def set_setting(key_path: str, value: Any):
    """Set a configuration setting"""
    get_config().set(key_path, value)