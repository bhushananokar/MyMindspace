"""
Component 2: RL Emotion Model - Data Module
Exports all data models and schemas for easy imports
"""

from .schemas import (
    # Core emotion models
    EmotionScores,
    EmotionAnalysis,
    
    # RL training models
    RLState,
    RLAction,
    RLExperience,
    TrainingBatch,
    
    # User feedback and calibration
    UserFeedback,
    RewardComponents,
    UserCalibration,
    
    # Configuration
    ModelConfig,
    
    # Type aliases
    EmotionVector,
    StateVector,
    ActionVector,
)

# Version info
__version__ = "1.0.0"
__author__ = "AI Journal Platform Team"

# Export commonly used classes for convenience
__all__ = [
    # Main emotion output
    "EmotionScores",
    "EmotionAnalysis",
    
    # RL components
    "RLState",
    "RLAction", 
    "RLExperience",
    "TrainingBatch",
    
    # User interaction
    "UserFeedback",
    "RewardComponents",
    "UserCalibration",
    
    # Configuration
    "ModelConfig",
    
    # Type hints
    "EmotionVector",
    "StateVector", 
    "ActionVector",
]