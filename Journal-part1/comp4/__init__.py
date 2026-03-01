"""
Component 4: Feature Engineering Pipeline
Transforms semantic analysis and emotion data into structured feature vectors 
optimized for LSTM memory gates and downstream AI components.
"""

from .src.feature_engineer import FeatureEngineer
from .src.processor import Component4Processor
from .data.schemas import (
    Component4Input,
    UserHistoryContext,
    EngineeredFeatures,
    FeatureMetadata
)

__version__ = "4.0.0"
__author__ = "AI Journal Platform Team"

__all__ = [
    'FeatureEngineer',
    'Component4Processor',
    'Component4Input',
    'UserHistoryContext', 
    'EngineeredFeatures',
    'FeatureMetadata'
]
