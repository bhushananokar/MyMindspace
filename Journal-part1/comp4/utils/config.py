"""
Configuration management for Component 4
"""

import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)

@dataclass
class FeatureConfig:
    """Configuration for Component 4 feature engineering"""
    
    # Quality control settings
    enable_quality_control: bool = True
    auto_repair_features: bool = True
    min_completeness_threshold: float = 0.8
    max_outlier_ratio: float = 0.1
    
    # Normalization settings
    normalization_method: str = "minmax"  # "minmax", "zscore", "robust"
    normalize_temporal: bool = True
    normalize_emotional: bool = True
    normalize_semantic: bool = True
    normalize_user: bool = True
    
    # Feature engineering settings
    smooth_cyclical_features: bool = True
    cyclical_smoothing_factor: float = 0.1
    balance_emotions: bool = True
    emotional_balancing_factor: float = 0.1
    enhance_semantic_features: bool = True
    smooth_topic_distribution: bool = True
    enhance_complexity_measures: bool = True
    scale_user_patterns: bool = True
    user_scaling_factor: float = 1.0
    
    # Performance settings
    max_processing_time_ms: float = 50.0
    enable_batch_processing: bool = True
    cache_features: bool = False
    
    # Logging settings
    log_level: str = "INFO"
    log_feature_stats: bool = False
    log_processing_times: bool = True
    
    # Advanced settings
    feature_selection: Dict[str, bool] = field(default_factory=lambda: {
        'temporal': True,
        'emotional': True,
        'semantic': True,
        'user': True
    })
    
    custom_weights: Dict[str, float] = field(default_factory=lambda: {
        'temporal': 1.0,
        'emotional': 1.0,
        'semantic': 1.0,
        'user': 1.0
    })
    
    def validate(self) -> Dict[str, Any]:
        """Validate configuration settings"""
        issues = []
        warnings = []
        
        # Validate thresholds
        if not 0.0 <= self.min_completeness_threshold <= 1.0:
            issues.append("min_completeness_threshold must be between 0.0 and 1.0")
        
        if not 0.0 <= self.max_outlier_ratio <= 1.0:
            issues.append("max_outlier_ratio must be between 0.0 and 1.0")
        
        # Validate normalization method
        valid_methods = ["minmax", "zscore", "robust"]
        if self.normalization_method not in valid_methods:
            issues.append(f"normalization_method must be one of {valid_methods}")
        
        # Validate smoothing factors
        if not 0.0 <= self.cyclical_smoothing_factor <= 1.0:
            warnings.append("cyclical_smoothing_factor should be between 0.0 and 1.0")
        
        if not 0.0 <= self.emotional_balancing_factor <= 1.0:
            warnings.append("emotional_balancing_factor should be between 0.0 and 1.0")
        
        # Validate weights
        for feature_type, weight in self.custom_weights.items():
            if weight < 0:
                warnings.append(f"custom_weights[{feature_type}] is negative")
        
        return {
            'is_valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {}
        for field_name, field_value in self.__dict__.items():
            if isinstance(field_value, dict):
                result[field_name] = field_value.copy()
            else:
                result[field_name] = field_value
        return result
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'FeatureConfig':
        """Create from dictionary"""
        return cls(**{
            k: v for k, v in config_dict.items()
            if k in cls.__annotations__
        })

def load_config(config_path: str) -> FeatureConfig:
    """
    Load configuration from file
    
    Args:
        config_path: Path to configuration file (YAML or JSON)
        
    Returns:
        FeatureConfig object
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config file has invalid format
    """
    try:
        config_file = Path(config_path)
        
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        # Load based on file extension
        with open(config_file, 'r') as f:
            if config_file.suffix.lower() in ['.yml', '.yaml']:
                config_data = yaml.safe_load(f)
            elif config_file.suffix.lower() == '.json':
                config_data = json.load(f)
            else:
                raise ValueError(f"Unsupported config file format: {config_file.suffix}")
        
        # Extract Component 4 specific config if nested
        if 'component4' in config_data:
            config_data = config_data['component4']
        elif 'feature_engineering' in config_data:
            config_data = config_data['feature_engineering']
        
        # Create config object
        config = FeatureConfig.from_dict(config_data)
        
        # Validate configuration
        validation = config.validate()
        if not validation['is_valid']:
            raise ValueError(f"Invalid configuration: {validation['issues']}")
        
        if validation['warnings']:
            logger.warning(f"Configuration warnings: {validation['warnings']}")
        
        logger.info(f"Configuration loaded successfully from {config_path}")
        return config
        
    except Exception as e:
        logger.error(f"Error loading configuration from {config_path}: {e}")
        raise

def create_default_config(save_path: Optional[str] = None) -> FeatureConfig:
    """
    Create default configuration
    
    Args:
        save_path: Optional path to save the default config
        
    Returns:
        FeatureConfig with default settings
    """
    try:
        config = FeatureConfig()
        
        if save_path:
            save_config(config, save_path)
            logger.info(f"Default configuration saved to {save_path}")
        
        return config
        
    except Exception as e:
        logger.error(f"Error creating default configuration: {e}")
        raise

def save_config(config: FeatureConfig, save_path: str) -> None:
    """
    Save configuration to file
    
    Args:
        config: FeatureConfig object to save
        save_path: Path to save configuration
    """
    try:
        save_file = Path(save_path)
        save_file.parent.mkdir(parents=True, exist_ok=True)
        
        config_dict = config.to_dict()
        
        # Save based on file extension
        with open(save_file, 'w') as f:
            if save_file.suffix.lower() in ['.yml', '.yaml']:
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)
            elif save_file.suffix.lower() == '.json':
                json.dump(config_dict, f, indent=2)
            else:
                # Default to YAML
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)
        
        logger.info(f"Configuration saved to {save_path}")
        
    except Exception as e:
        logger.error(f"Error saving configuration to {save_path}: {e}")
        raise

def merge_configs(base_config: FeatureConfig, override_config: Dict[str, Any]) -> FeatureConfig:
    """
    Merge configuration with overrides
    
    Args:
        base_config: Base FeatureConfig object
        override_config: Dictionary with override values
        
    Returns:
        New FeatureConfig with merged settings
    """
    try:
        # Convert base config to dict
        merged_dict = base_config.to_dict()
        
        # Apply overrides
        for key, value in override_config.items():
            if key in merged_dict:
                if isinstance(merged_dict[key], dict) and isinstance(value, dict):
                    # Merge nested dictionaries
                    merged_dict[key].update(value)
                else:
                    # Replace value
                    merged_dict[key] = value
            else:
                logger.warning(f"Unknown configuration key: {key}")
        
        # Create new config
        merged_config = FeatureConfig.from_dict(merged_dict)
        
        # Validate merged config
        validation = merged_config.validate()
        if not validation['is_valid']:
            raise ValueError(f"Invalid merged configuration: {validation['issues']}")
        
        return merged_config
        
    except Exception as e:
        logger.error(f"Error merging configurations: {e}")
        raise

def get_config_template() -> Dict[str, Any]:
    """
    Get configuration template for documentation
    
    Returns:
        Dictionary with configuration template and descriptions
    """
    return {
        "component4": {
            "description": "Component 4: Feature Engineering Pipeline Configuration",
            "quality_control": {
                "enable_quality_control": {
                    "type": "boolean",
                    "default": True,
                    "description": "Enable feature quality validation"
                },
                "auto_repair_features": {
                    "type": "boolean", 
                    "default": True,
                    "description": "Automatically repair invalid features"
                },
                "min_completeness_threshold": {
                    "type": "float",
                    "default": 0.8,
                    "range": [0.0, 1.0],
                    "description": "Minimum feature completeness required"
                }
            },
            "normalization": {
                "normalization_method": {
                    "type": "string",
                    "default": "minmax",
                    "options": ["minmax", "zscore", "robust"],
                    "description": "Feature normalization method"
                },
                "normalize_temporal": {
                    "type": "boolean",
                    "default": True,
                    "description": "Apply normalization to temporal features"
                }
            },
            "feature_engineering": {
                "smooth_cyclical_features": {
                    "type": "boolean",
                    "default": True,
                    "description": "Apply smoothing to cyclical time features"
                },
                "balance_emotions": {
                    "type": "boolean",
                    "default": True,
                    "description": "Apply balancing to prevent extreme emotion values"
                }
            },
            "performance": {
                "max_processing_time_ms": {
                    "type": "float",
                    "default": 50.0,
                    "description": "Maximum processing time per entry in milliseconds"
                },
                "enable_batch_processing": {
                    "type": "boolean",
                    "default": True,
                    "description": "Enable batch processing for multiple entries"
                }
            }
        }
    }
