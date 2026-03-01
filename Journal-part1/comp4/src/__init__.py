"""
Component 4: Feature Engineering Pipeline - Source Module
Exports all core processing classes
"""

from .feature_engineer import FeatureEngineer
from .processor import Component4Processor
from .temporal_extractor import TemporalFeatureExtractor
from .emotional_extractor import EmotionalFeatureExtractor
from .semantic_extractor import SemanticFeatureExtractor
from .user_extractor import UserFeatureExtractor
from .quality_controller import FeatureQualityController

__all__ = [
    'FeatureEngineer',
    'Component4Processor',
    'TemporalFeatureExtractor',
    'EmotionalFeatureExtractor', 
    'SemanticFeatureExtractor',
    'UserFeatureExtractor',
    'FeatureQualityController'
]
