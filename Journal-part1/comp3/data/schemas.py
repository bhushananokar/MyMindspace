from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from datetime import datetime
import numpy as np

@dataclass
class PersonEntity:
    """Detected person in text"""
    name: str
    relationship_type: Optional[str] = None  # family, friend, colleague, etc.
    context_clues: List[str] = None
    confidence: float = 0.0
    mentions: int = 1

@dataclass
class LocationEntity:
    """Detected location in text"""
    name: str
    location_type: str  # city, country, building, etc.
    context: str = ""
    confidence: float = 0.0

@dataclass
class OrganizationEntity:
    """Detected organization in text"""
    name: str
    org_type: str  # company, school, hospital, etc.
    context: str = ""
    confidence: float = 0.0

@dataclass
class ExtractedEvent:
    """Future event detected in text (Component 8 integration)"""
    event_id: str
    event_text: str
    event_type: str  # professional, medical, social, personal, travel
    event_subtype: Optional[str] = None  # interview, appointment, meeting, etc.
    parsed_date: Optional[datetime] = None
    original_date_text: str = ""
    participants: List[str] = None
    location: Optional[str] = None
    importance_score: float = 0.0
    confidence: float = 0.0
    emotional_context: Dict[str, float] = None

@dataclass
class FollowupQuestion:
    """Generated follow-up question for events"""
    event_id: str
    question_text: str
    question_type: str  # before_event, after_event, during_prep
    optimal_timing: datetime
    context_needed: Dict[str, Any] = None

@dataclass
class TemporalFeatures:
    """Time-based patterns and cycles"""
    writing_time: datetime
    hour_of_day: int
    day_of_week: int
    is_weekend: bool
    days_since_last_entry: int
    writing_frequency_score: float = 0.0
    cyclical_patterns: Dict[str, float] = None
    anomaly_score: float = 0.0

@dataclass
class SemanticEmbedding:
    """Sentence embeddings with metadata"""
    primary_embedding: np.ndarray  # 768-dim from all-mpnet-base-v2
    lightweight_embedding: np.ndarray  # 384-dim from all-MiniLM-L6-v2
    text_length: int
    processing_time_ms: float
    model_version: str

@dataclass
class SemanticAnalysis:
    """Complete output from Component 3"""
    # Entity extraction
    people: List[PersonEntity]
    locations: List[LocationEntity]
    organizations: List[OrganizationEntity]
    
    # Event extraction (Component 8)
    future_events: List[ExtractedEvent]
    followup_questions: List[FollowupQuestion]
    
    # Embeddings
    embeddings: SemanticEmbedding
    
    # Temporal analysis
    temporal_features: TemporalFeatures
    
    # Relationships
    entity_relationships: Dict[str, List[str]]
    
    # Topics and patterns
    detected_topics: List[str]
    novelty_score: float = 0.0
    complexity_score: float = 0.0
    
    # Processing metadata
    processing_time_ms: float = 0.0
    component_version: str = "3.0"