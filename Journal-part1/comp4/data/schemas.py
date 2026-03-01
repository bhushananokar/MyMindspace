"""
Data schemas for Component 4: Feature Engineering Pipeline
Dataclass models for input, output, and internal processing
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import uuid

# Import dependencies from Components 2 & 3
# These will be passed in from the integration layer
from comp2.data.schemas import EmotionAnalysis
from comp3.data.schemas import SemanticAnalysis

@dataclass
class Component4Input:
    """Combined input from Components 2 and 3 for feature engineering"""
    
    # Core Analysis Results
    emotion_analysis: EmotionAnalysis      # From Component 2
    semantic_analysis: SemanticAnalysis    # From Component 3
    
    # Entry Context
    user_id: str
    entry_id: str
    session_id: str
    entry_timestamp: datetime
    raw_text: str
    
    # User Context (for personalized features)
    user_history: Optional['UserHistoryContext'] = None
    previous_entries: Optional[List[Dict]] = None  # Recent entries for pattern analysis

@dataclass 
class UserHistoryContext:
    """User's historical context for personalized feature engineering"""
    writing_frequency_baseline: float
    emotional_baseline: Dict[str, float]  # User's normal emotional state
    topic_preferences: List[str]
    behavioral_patterns: Dict[str, Any]
    last_entry_timestamp: Optional[datetime] = None
    
    # Extended context for Component 4
    total_entries: int = 0
    avg_session_duration: float = 0.0
    preferred_writing_times: List[int] = field(default_factory=list)  # Hours 0-23
    emotional_volatility: float = 0.0
    topic_consistency: float = 0.0
    social_connectivity: float = 0.0

@dataclass
class TemporalFeatures:
    """Temporal feature extraction results"""
    cyclical_hour: float           # sin/cos encoded hour
    cyclical_day: float            # sin/cos encoded day of week
    cyclical_month: float          # sin/cos encoded month
    days_since_last: float         # Days since last entry
    writing_frequency_score: float # Frequency relative to baseline
    consistency_score: float       # Timing consistency
    spontaneity_score: float       # How spontaneous this entry is
    future_orientation: float      # Focus on future events
    time_pressure: float           # Deadline proximity indicators
    anomaly_score: float           # Unusual timing pattern
    
    def to_vector(self) -> np.ndarray:
        """Convert to 25D vector with cyclical encodings"""
        hour_rad = 2 * np.pi * self.cyclical_hour / 24
        day_rad = 2 * np.pi * self.cyclical_day / 7
        month_rad = 2 * np.pi * self.cyclical_month / 12
        
        return np.array([
            # Cyclical time features (6D)
            np.sin(hour_rad), np.cos(hour_rad),
            np.sin(day_rad), np.cos(day_rad), 
            np.sin(month_rad), np.cos(month_rad),
            
            # Relative time features (4D)
            self.days_since_last,
            self.writing_frequency_score,
            self.consistency_score,
            self.spontaneity_score,
            
            # Content time features (3D)
            self.future_orientation,
            self.time_pressure,
            self.anomaly_score,
            
            # Extended temporal patterns (12D)
            self.cyclical_hour / 24,  # Normalized hour
            self.cyclical_day / 7,    # Normalized day
            float(self.cyclical_hour < 6 or self.cyclical_hour > 22),  # Late night
            float(self.cyclical_day >= 5),  # Weekend
            float(6 <= self.cyclical_hour <= 9),   # Morning
            float(9 <= self.cyclical_hour <= 17),  # Work hours
            float(17 <= self.cyclical_hour <= 22), # Evening
            min(self.days_since_last / 7, 1.0),    # Weeks since last (capped)
            min(self.writing_frequency_score, 2.0), # Frequency (capped)
            self.consistency_score,
            self.spontaneity_score,
            self.anomaly_score
        ], dtype=np.float32)

@dataclass
class EmotionalFeatures:
    """Emotional feature extraction results"""
    emotion_vector: np.ndarray     # 8D emotion scores
    dominant_emotion_idx: int      # Index of dominant emotion
    emotional_intensity: float    # Overall intensity
    emotional_confidence: float   # Model confidence
    valence: float                 # Positive/negative sentiment
    arousal: float                 # High/low activation
    stability: float               # Emotional stability score
    volatility: float              # Recent emotional changes
    baseline_deviation: float     # Deviation from user baseline
    regulation_attempts: float    # Signs of emotional regulation
    
    def to_vector(self) -> np.ndarray:
        """Convert to 20D emotional feature vector"""
        # One-hot encode dominant emotion (8D)
        dominant_onehot = np.zeros(8, dtype=np.float32)
        if 0 <= self.dominant_emotion_idx < 8:
            dominant_onehot[self.dominant_emotion_idx] = 1.0
        
        return np.array([
            # Core emotional metrics (4D)
            self.emotional_intensity,
            self.emotional_confidence,
            self.valence,
            self.arousal,
            
            # Emotional dynamics (4D)
            self.stability,
            self.volatility,
            self.baseline_deviation,
            self.regulation_attempts,
            
            # Dominant emotion one-hot (8D)
            *dominant_onehot,
            
            # Additional emotional features to reach 20D (4D)
            min(self.emotional_intensity * self.arousal, 1.0),  # Emotional activation
            abs(self.valence),  # Valence magnitude
            self.emotional_confidence * self.stability,  # Confident stability
            (self.emotional_intensity + abs(self.valence) + self.arousal) / 3  # Overall emotional engagement
        ], dtype=np.float32)

@dataclass
class SemanticFeatures:
    """Semantic feature extraction results"""
    topic_distribution: np.ndarray    # Topic probabilities
    novelty_score: float              # Content novelty
    complexity_score: float          # Content complexity
    coherence_score: float           # Logical coherence
    entity_density: float            # People/places mentioned
    event_density: float             # Future events mentioned
    vocabulary_richness: float       # Unique word ratio
    sentence_complexity: float       # Avg sentence length/structure
    emotional_language: float        # Emotional word density
    social_language: float           # Social interaction words
    
    def to_vector(self) -> np.ndarray:
        """Convert to 30D semantic feature vector"""
        # Ensure topic distribution is 10D (pad or truncate)
        topic_features = np.zeros(10, dtype=np.float32)
        if self.topic_distribution is not None:
            min_len = min(len(self.topic_distribution), 10)
            topic_features[:min_len] = self.topic_distribution[:min_len]
        
        return np.array([
            # Topic modeling (10D)
            *topic_features,
            
            # Content analysis (10D)
            self.novelty_score,
            self.complexity_score,
            self.coherence_score,
            self.entity_density,
            self.event_density,
            self.vocabulary_richness,
            self.sentence_complexity,
            self.emotional_language,
            self.social_language,
            min(self.novelty_score + self.complexity_score, 1.0),  # Combined complexity
            
            # Extended semantic features (10D)
            float(self.entity_density > 0.5),     # High social content
            float(self.event_density > 0.3),      # Future-focused
            float(self.vocabulary_richness > 0.7), # Rich vocabulary
            float(self.emotional_language > 0.4), # Emotional content
            float(self.social_language > 0.3),    # Social content
            self.novelty_score * self.complexity_score,  # Novel complexity
            self.coherence_score * self.complexity_score, # Coherent complexity
            min(self.entity_density + self.event_density, 1.0), # Total mention density
            min(self.emotional_language + self.social_language, 1.0), # Expressive language
            (self.novelty_score + self.complexity_score + self.coherence_score) / 3  # Overall quality
        ], dtype=np.float32)

@dataclass
class UserFeatures:
    """User-specific behavioral and pattern features"""
    writing_consistency: float       # How consistent user's writing is
    session_patterns: float         # Session behavior patterns
    topic_preference_match: float   # Match to user's preferred topics
    emotional_baseline_match: float # Match to user's emotional baseline
    behavioral_anomaly: float       # How unusual this entry is for user
    engagement_level: float         # Estimated engagement with platform
    personal_growth: float          # Indicators of personal development
    relationship_focus: float       # Focus on relationships
    goal_orientation: float         # Focus on goals/achievements
    introspection_level: float      # Level of self-reflection
    
    def to_vector(self) -> np.ndarray:
        """Convert to 15D user feature vector"""
        return np.array([
            # Behavioral patterns (5D)
            self.writing_consistency,
            self.session_patterns,
            self.topic_preference_match,
            self.emotional_baseline_match,
            self.behavioral_anomaly,
            
            # Engagement and development (5D)
            self.engagement_level,
            self.personal_growth,
            self.relationship_focus,
            self.goal_orientation,
            self.introspection_level,
            
            # Combined user metrics (5D)
            (self.writing_consistency + self.session_patterns) / 2,  # Overall consistency
            (self.topic_preference_match + self.emotional_baseline_match) / 2,  # Baseline match
            (self.personal_growth + self.introspection_level) / 2,  # Growth indicators
            (self.relationship_focus + self.goal_orientation) / 2,  # Life focus
            1.0 - self.behavioral_anomaly  # Normality score
        ], dtype=np.float32)

@dataclass
class FeatureMetadata:
    """Metadata that goes directly into vector DB memory_embeddings collection"""
    
    # Core Metadata (matches vector DB schema)
    memory_type: str = "conversation"      # conversation | event | emotion | insight
    content_summary: str = ""              # Generated from raw text
    original_entry_id: str = ""
    importance_score: float = 0.0          # 0-1
    emotional_significance: float = 0.0    # 0-1  
    temporal_relevance: float = 0.0        # 0-1
    
    # Gate Scores (for LSTM memory gates)
    gate_scores: Dict[str, float] = field(default_factory=lambda: {
        "forget_score": 0.0,
        "input_score": 0.0,
        "output_score": 0.0,
        "confidence": 0.0
    })
    
    # Relationships and Context
    relationships: List[str] = field(default_factory=list)  # Related memory IDs
    context_needed: Dict[str, Any] = field(default_factory=dict)
    retrieval_triggers: List[str] = field(default_factory=list)  # Keywords for retrieval
    
    # Access Tracking
    access_frequency: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    created_at: datetime = field(default_factory=datetime.now)
    
    # Extended metadata for feature engineering
    feature_quality_score: float = 0.0
    processing_metadata: Dict[str, Any] = field(default_factory=dict)
    version_info: Dict[str, str] = field(default_factory=dict)

@dataclass
class EngineeredFeatures:
    """Component 4 output optimized for vector database storage"""
    
    # Main Feature Vector (matches vector DB schema)
    feature_vector: np.ndarray             # Shape: (90,) - THE CORE OUTPUT
    
    # Feature Breakdown (for debugging/analysis)
    temporal_features: np.ndarray          # Shape: (25,)
    emotional_features: np.ndarray         # Shape: (20,)  
    semantic_features: np.ndarray          # Shape: (30,)
    user_features: np.ndarray              # Shape: (15,)
    
    # Metadata for Vector DB
    metadata: FeatureMetadata
    
    # Quality Metrics
    feature_completeness: float            # 0-1 score
    confidence_score: float                # Overall confidence
    processing_time_ms: float
    
    # Identifiers
    user_id: str
    entry_id: str
    timestamp: datetime
    component_version: str = "4.0"
    
    def validate_dimensions(self) -> bool:
        """Validate that all feature vectors have correct dimensions"""
        return (
            self.feature_vector.shape == (90,) and
            self.temporal_features.shape == (25,) and
            self.emotional_features.shape == (20,) and
            self.semantic_features.shape == (30,) and
            self.user_features.shape == (15,)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'feature_vector': self.feature_vector.tolist(),
            'temporal_features': self.temporal_features.tolist(),
            'emotional_features': self.emotional_features.tolist(),
            'semantic_features': self.semantic_features.tolist(),
            'user_features': self.user_features.tolist(),
            'metadata': {
                'memory_type': self.metadata.memory_type,
                'content_summary': self.metadata.content_summary,
                'original_entry_id': self.metadata.original_entry_id,
                'importance_score': self.metadata.importance_score,
                'emotional_significance': self.metadata.emotional_significance,
                'temporal_relevance': self.metadata.temporal_relevance,
                'gate_scores': self.metadata.gate_scores,
                'relationships': self.metadata.relationships,
                'context_needed': self.metadata.context_needed,
                'retrieval_triggers': self.metadata.retrieval_triggers,
                'access_frequency': self.metadata.access_frequency,
                'last_accessed': self.metadata.last_accessed.isoformat(),
                'created_at': self.metadata.created_at.isoformat(),
                'feature_quality_score': self.metadata.feature_quality_score,
                'processing_metadata': self.metadata.processing_metadata,
                'version_info': self.metadata.version_info
            },
            'feature_completeness': self.feature_completeness,
            'confidence_score': self.confidence_score,
            'processing_time_ms': self.processing_time_ms,
            'user_id': self.user_id,
            'entry_id': self.entry_id,
            'timestamp': self.timestamp.isoformat(),
            'component_version': self.component_version
        }

# Feature dimension validation
def validate_feature_dimensions():
    """Validate that all feature types sum to 90 dimensions"""
    temporal_dim = 25
    emotional_dim = 20
    semantic_dim = 30
    user_dim = 15
    
    total_dim = temporal_dim + emotional_dim + semantic_dim + user_dim
    assert total_dim == 90, f"Feature dimensions sum to {total_dim}, expected 90"
    
    return True

# Initialize validation on import
validate_feature_dimensions()

# ===== ASTRA DB COLLECTION SCHEMAS =====

@dataclass
class EmotionContext:
    """Emotion context for chat embeddings"""
    dominant_emotion: str
    intensity: float
    emotions: Dict[str, float]  # joy, sadness, anger, fear, surprise, disgust, anticipation, trust

@dataclass
class EntitiesMentioned:
    """Entities mentioned in content"""
    people: List[str] = field(default_factory=list)
    locations: List[str] = field(default_factory=list)
    organizations: List[str] = field(default_factory=list)

@dataclass
class TemporalContext:
    """Temporal context for embeddings"""
    hour_of_day: int
    day_of_week: int
    is_weekend: bool

@dataclass
class ChatEmbedding:
    """Schema for chat_embeddings collection in Astra DB"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    entry_id: str = ""
    message_content: str = ""
    message_type: str = "user_message"  # user_message | ai_response | system_message
    timestamp: datetime = field(default_factory=datetime.now)
    session_id: str = ""
    conversation_context: str = ""
    primary_embedding: List[float] = field(default_factory=list)  # 768 dimensions
    lightweight_embedding: List[float] = field(default_factory=list)  # 384 dimensions
    text_length: int = 0
    processing_time_ms: float = 0.0
    model_version: str = "4.0-PRODUCTION"
    semantic_tags: List[str] = field(default_factory=list)
    emotion_context: Optional[EmotionContext] = None
    entities_mentioned: Optional[EntitiesMentioned] = None
    temporal_context: Optional[TemporalContext] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Astra DB insertion"""
        result = {
            "id": self.id,
            "user_id": self.user_id,
            "entry_id": self.entry_id,
            "message_content": self.message_content,
            "message_type": self.message_type,
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
            "conversation_context": self.conversation_context,
            "primary_embedding": self.primary_embedding,
            "lightweight_embedding": self.lightweight_embedding,
            "text_length": self.text_length,
            "processing_time_ms": self.processing_time_ms,
            "model_version": self.model_version,
            "semantic_tags": self.semantic_tags
        }
        
        if self.emotion_context:
            result["emotion_context"] = {
                "dominant_emotion": self.emotion_context.dominant_emotion,
                "intensity": self.emotion_context.intensity,
                "emotions": self.emotion_context.emotions
            }
        
        if self.entities_mentioned:
            result["entities_mentioned"] = {
                "people": self.entities_mentioned.people,
                "locations": self.entities_mentioned.locations,
                "organizations": self.entities_mentioned.organizations
            }
        
        if self.temporal_context:
            result["temporal_context"] = {
                "hour_of_day": self.temporal_context.hour_of_day,
                "day_of_week": self.temporal_context.day_of_week,
                "is_weekend": self.temporal_context.is_weekend
            }
        
        return result

@dataclass
class LinkedEntities:
    """Linked entities for semantic search"""
    people: List[str] = field(default_factory=list)
    locations: List[str] = field(default_factory=list)
    events: List[str] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)

@dataclass
class SearchMetadata:
    """Search metadata for semantic search"""
    boost_factor: float = 1.0
    recency_weight: float = 1.0
    user_preference_alignment: float = 0.5

@dataclass
class SemanticSearch:
    """Schema for semantic_search collection in Astra DB"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    content_type: str = "journal_entry"  # journal_entry | event | person | location | topic
    title: str = ""
    content: str = ""
    primary_embedding: List[float] = field(default_factory=list)  # 768 dimensions
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    linked_entities: Optional[LinkedEntities] = None
    search_metadata: Optional[SearchMetadata] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Astra DB insertion"""
        result = {
            "id": self.id,
            "user_id": self.user_id,
            "content_type": self.content_type,
            "title": self.title,
            "content": self.content,
            "primary_embedding": self.primary_embedding,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "tags": self.tags
        }
        
        if self.linked_entities:
            result["linked_entities"] = {
                "people": self.linked_entities.people,
                "locations": self.linked_entities.locations,
                "events": self.linked_entities.events,
                "topics": self.linked_entities.topics
            }
        
        if self.search_metadata:
            result["search_metadata"] = {
                "boost_factor": self.search_metadata.boost_factor,
                "recency_weight": self.search_metadata.recency_weight,
                "user_preference_alignment": self.search_metadata.user_preference_alignment
            }
        
        return result
