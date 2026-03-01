"""
Data schemas for Component 2: RL Emotion Model
Pydantic models for type safety and validation
"""

from datetime import datetime
from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator
import numpy as np


class EmotionScores(BaseModel):
    """Individual emotion scores from 0-1"""
    joy: float = Field(ge=0.0, le=1.0, default=0.0)
    sadness: float = Field(ge=0.0, le=1.0, default=0.0)
    anger: float = Field(ge=0.0, le=1.0, default=0.0)
    fear: float = Field(ge=0.0, le=1.0, default=0.0)
    surprise: float = Field(ge=0.0, le=1.0, default=0.0)
    disgust: float = Field(ge=0.0, le=1.0, default=0.0)
    anticipation: float = Field(ge=0.0, le=1.0, default=0.0)
    trust: float = Field(ge=0.0, le=1.0, default=0.0)

    def to_list(self) -> List[float]:
        """Convert to list for numpy operations"""
        return [self.joy, self.sadness, self.anger, self.fear, 
                self.surprise, self.disgust, self.anticipation, self.trust]
    
    def dominant_emotion(self) -> str:
        """Get the emotion with highest score"""
        emotions = self.dict()
        return max(emotions.items(), key=lambda x: x[1])[0]


class EmotionAnalysis(BaseModel):
    """Main emotion analysis output"""
    emotions: EmotionScores
    dominant_emotion: str
    intensity: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    calibration_applied: bool = False
    model_version: str = "v1.0"
    processing_time_ms: int = 0
    timestamp: datetime = Field(default_factory=datetime.now)

    @field_validator('dominant_emotion')
    @classmethod
    def validate_dominant_emotion(cls, v, info):
        valid_emotions = ['joy', 'sadness', 'anger', 'fear', 
                         'surprise', 'disgust', 'anticipation', 'trust']
        if v not in valid_emotions:
            raise ValueError(f"Invalid dominant emotion: {v}")
        return v


class RLState(BaseModel):
    """State representation for RL training"""
    text_features: List[float] = Field(min_items=1)
    base_emotions: EmotionScores
    user_history: List[float] = Field(default_factory=list, max_items=10)
    context_features: List[float] = Field(default_factory=list)
    
    def to_vector(self) -> List[float]:
        """Convert state to flat vector for neural network"""
        vector = []
        vector.extend(self.text_features)
        vector.extend(self.base_emotions.to_list())
        vector.extend(self.user_history)
        vector.extend(self.context_features)
        return vector


class RLAction(BaseModel):
    """Action representation for RL training"""
    emotion_adjustments: List[float] = Field(min_items=8, max_items=8)
    confidence_modifier: float = Field(ge=-0.5, le=0.5, default=0.0)
    
    @field_validator('emotion_adjustments')
    @classmethod
    def validate_adjustments(cls, v):
        if len(v) != 8:
            raise ValueError("Must have exactly 8 emotion adjustments")
        # Adjustments should be small (-0.3 to +0.3)
        for adj in v:
            if not -0.3 <= adj <= 0.3:
                raise ValueError("Adjustments must be between -0.3 and 0.3")
        return v


class RLExperience(BaseModel):
    """Single experience tuple for replay buffer"""
    user_id: str
    episode_id: int
    step_id: int
    state: RLState
    action: RLAction
    reward: float
    next_state: Optional[RLState] = None
    done: bool = False
    priority: float = 1.0  # For prioritized replay
    timestamp: datetime = Field(default_factory=datetime.now)
    
    class Config:
        # Allow numpy arrays to be serialized
        arbitrary_types_allowed = True


class UserFeedback(BaseModel):
    """User feedback for reward calculation"""
    user_id: str
    journal_entry_id: str
    feedback_type: str = Field(pattern="^(correction|confirmation|engagement|behavioral)$")
    feedback_data: Dict[str, Union[str, float, bool]]
    emotion_context: Optional[EmotionAnalysis] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # Feedback types:
    # - correction: User corrected emotion labels
    # - confirmation: User agreed with emotions  
    # - engagement: Continued conversation, follow-ups
    # - behavioral: Session time, return visits


class RewardComponents(BaseModel):
    """Breakdown of reward calculation"""
    explicit_feedback: float = 0.0  # Direct corrections/confirmations
    engagement_signal: float = 0.0  # Conversation continuation
    behavioral_signal: float = 0.0  # Session patterns
    total_reward: float = 0.0
    confidence: float = 0.0  # How confident we are in this reward
    
    @field_validator('total_reward')
    @classmethod
    def calculate_total(cls, v, info):
        return (info.data.get('explicit_feedback', 0) + 
                info.data.get('engagement_signal', 0) + 
                info.data.get('behavioral_signal', 0))


class UserCalibration(BaseModel):
    """User's personal RL calibration data"""
    user_id: str
    policy_version: str = "v1.0"
    training_episodes: int = 0
    total_experiences: int = 0
    avg_reward: float = 0.0
    accuracy_improvement: float = 0.0
    last_updated: datetime = Field(default_factory=datetime.now)
    
    # Training metrics
    policy_loss_history: List[float] = Field(default_factory=list, max_items=100)
    value_loss_history: List[float] = Field(default_factory=list, max_items=100)
    reward_history: List[float] = Field(default_factory=list, max_items=1000)
    
    # Model performance
    baseline_accuracy: float = 0.0
    current_accuracy: float = 0.0
    feedback_count: int = 0
    
    def get_recent_performance(self, window: int = 50) -> float:
        """Get average reward over recent window"""
        if not self.reward_history:
            return 0.0
        recent = self.reward_history[-window:]
        return sum(recent) / len(recent)


class TrainingBatch(BaseModel):
    """Batch of experiences for training"""
    experiences: List[RLExperience]
    batch_size: int
    weights: Optional[List[float]] = None  # For prioritized replay
    
    @field_validator('batch_size')
    @classmethod
    def validate_batch_size(cls, v, info):
        experiences = info.data.get('experiences', [])
        if v != len(experiences):
            raise ValueError("Batch size must match number of experiences")
        return v
    
    def to_tensors(self):
        """Convert batch to format suitable for PyTorch training"""
        states = [exp.state.to_vector() for exp in self.experiences]
        actions = [[*exp.action.emotion_adjustments, exp.action.confidence_modifier] 
                  for exp in self.experiences]
        rewards = [exp.reward for exp in self.experiences]
        
        next_states = []
        dones = []
        for exp in self.experiences:
            if exp.next_state and not exp.done:
                next_states.append(exp.next_state.to_vector())
                dones.append(0.0)
            else:
                next_states.append([0.0] * len(states[0]))  # Dummy state
                dones.append(1.0)
        
        return {
            'states': states,
            'actions': actions, 
            'rewards': rewards,
            'next_states': next_states,
            'dones': dones,
            'weights': self.weights or [1.0] * len(self.experiences)
        }


class ModelConfig(BaseModel):
    """Configuration for emotion and RL models"""
    # Base emotion model
    base_model_name: str = "cardiffnlp/twitter-roberta-base-emotion"
    emotion_threshold: float = 0.1
    max_sequence_length: int = 512
    
    # RL configuration
    rl_algorithm: str = "SAC"
    learning_rate: float = 3e-4
    batch_size: int = 64
    buffer_size: int = 10000
    update_frequency: int = 100
    target_update_interval: int = 1000
    
    # Network architecture
    policy_hidden_dims: List[int] = [128, 64]
    value_hidden_dims: List[int] = [256, 128]
    
    # Training parameters
    gamma: float = 0.99  # Discount factor
    tau: float = 0.005   # Soft update coefficient
    alpha: float = 0.2   # Entropy regularization
    
    # Experience replay
    prioritized_replay: bool = True
    priority_alpha: float = 0.6
    priority_beta: float = 0.4
    
    class Config:
        # Allow extra fields for flexibility
        extra = "allow"


# Type aliases for convenience
EmotionVector = List[float]
StateVector = List[float] 
ActionVector = List[float]