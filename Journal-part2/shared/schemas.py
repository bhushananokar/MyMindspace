"""
Shared data models and schemas for Gemini Engine Components 6 & 7.
Implements all required interfaces and data structures for production use.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional, Union, Literal
from enum import Enum
import uuid
from pydantic import BaseModel, Field, validator


# ============================================================================
# COMPONENT 5 INTERFACE (INPUT FOR COMPONENT 6)
# ============================================================================

@dataclass
class MemoryContext:
    """Output from Component 5 LSTM Memory Gates - Primary input for Component 6"""
    selected_memories: List[Dict[str, Any]]
    relevance_scores: List[float]
    token_usage: int
    assembly_metadata: Dict[str, Any]


@dataclass
class MemoryItem:
    """Individual memory structure from Component 5"""
    id: str
    user_id: str
    memory_type: Literal["conversation", "event", "emotion", "insight"]
    content_summary: str
    original_entry_id: str
    importance_score: float
    emotional_significance: float
    temporal_relevance: float
    gate_scores: Dict[str, float]
    feature_vector: List[float]
    relationships: List[str]
    context_needed: Dict[str, Any]
    retrieval_triggers: List[str]
    access_frequency: int
    last_accessed: datetime
    created_at: datetime


# ============================================================================
# COMPONENT 6 DATA MODELS
# ============================================================================

class CommunicationStyle(str, Enum):
    """User communication style preferences"""
    FORMAL = "formal"
    CASUAL = "casual"
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    HUMOROUS = "humorous"
    DIRECT = "direct"
    ELABORATE = "elaborate"


@dataclass
class CommunicationStyleDetails:
    """Detailed communication style information"""
    style_id: str
    name: str
    characteristics: Dict[str, str]
    language_patterns: Dict[str, List[str]]


class EmotionalTone(str, Enum):
    """Emotional tone for AI responses"""
    NEUTRAL = "neutral"
    SUPPORTIVE = "supportive"
    ENCOURAGING = "encouraging"
    EMPATHETIC = "empathetic"
    EXCITED = "excited"
    CALM = "calm"
    PLAYFUL = "playful"


@dataclass
class PersonalityProfile:
    """AI personality profile for communication"""
    profile_id: str
    name: str
    description: str
    traits: Dict[str, float]
    communication_patterns: Dict[str, str]


@dataclass
class UserProfile:
    """User personality and communication preferences"""
    user_id: str
    communication_style: CommunicationStyle
    preferred_response_length: Literal["brief", "moderate", "detailed"] = "moderate"
    emotional_matching: bool = True
    cultural_context: Optional[str] = None
    humor_preference: float = 0.5  # 0-1 scale
    formality_level: float = 0.5   # 0-1 scale
    conversation_depth: float = 0.7  # 0-1 scale
    proactive_engagement: bool = True
    personality_traits: Dict[str, float] = field(default_factory=dict)
    preferences: Dict[str, Any] = field(default_factory=dict)
    interaction_history: List[Dict[str, Any]] = field(default_factory=list)
    last_interaction: Optional[datetime] = None
    last_updated: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ConversationContext:
    """Complete conversation state for Gemini integration"""
    user_id: str
    conversation_id: str
    user_input: Optional[str] = None
    conversation_topic: Optional[str] = None
    conversation_tone: Optional[str] = None
    conversation_goals: List[str] = field(default_factory=list)
    emotional_state: Optional[Dict[str, Any]] = None
    external_context: Optional[Dict[str, Any]] = None
    memories: List[MemoryItem] = field(default_factory=list)
    personality_profile: Optional[UserProfile] = None
    recent_history: List[Dict[str, Any]] = field(default_factory=list)
    context_metadata: Dict[str, Any] = field(default_factory=dict)
    message_history: List[Dict[str, Any]] = field(default_factory=list)
    context_window_size: int = 2000
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)


@dataclass
class GeminiRequest:
    """Structured request to Gemini API"""
    conversation_id: str
    user_id: str
    system_prompt: str
    user_prompt: Optional[str] = None
    context_section: Optional[str] = None
    conversation_history: Optional[str] = None
    current_message: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 500
    safety_settings: Dict[str, str] = field(default_factory=dict)
    response_guidelines: Dict[str, Any] = field(default_factory=dict)
    api_parameters: Dict[str, Any] = field(default_factory=dict)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    token_budget: int = 2000
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ConversationRequest:
    """Request object for conversation processing"""
    conversation_context: ConversationContext
    processing_options: Dict[str, bool] = field(default_factory=dict)
    response_preferences: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

# ALSO UPDATE YOUR EnhancedResponse SCHEMA in shared/schemas.py:
# Replace your existing EnhancedResponse with this:

@dataclass
class EnhancedResponse:
    """Processed Gemini response with quality metrics"""
    response_id: str
    conversation_id: str
    user_id: str
    original_response: str
    enhanced_response: str
    enhancement_metadata: Dict[str, Any] = field(default_factory=dict)
    processing_timestamp: datetime = field(default_factory=datetime.utcnow)
    quality_metrics: Dict[str, Any] = field(default_factory=dict)
    safety_checks: Dict[str, Any] = field(default_factory=dict)
    context_usage: Dict[str, Any] = field(default_factory=dict)
    response_metadata: Dict[str, Any] = field(default_factory=dict)
    follow_up_suggestions: List[str] = field(default_factory=list)
    proactive_suggestions: List[str] = field(default_factory=list)
    memory_context_metadata: Dict[str, Any] = field(default_factory=dict)
    response_analysis: Optional['ResponseAnalysis'] = None

@dataclass
class ProactiveMessage:
    """AI-initiated conversation message"""
    message_id: str
    user_id: str
    trigger_event: str
    message_content: str
    optimal_timing: datetime
    expected_response: str
    priority_level: Literal["low", "medium", "high"] = "medium"
    delivery_status: Literal["pending", "sent", "delivered", "responded"] = "pending"
    created_at: datetime = field(default_factory=datetime.utcnow)


# ============================================================================
# COMPONENT 7 DATA MODELS
# ============================================================================

@dataclass
class ResponseAnalysis:
    """Component 7 analysis results for response quality"""
    analysis_id: str
    response_id: str
    conversation_id: str
    user_id: str
    quality_scores: Dict[str, float]
    context_usage: Dict[str, Any]
    user_satisfaction: float
    improvement_suggestions: List[str]
    analysis_timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ConversationMetrics:
    """Session-level conversation analysis"""
    conversation_id: str
    user_id: str
    flow_score: float
    engagement_level: float
    goal_achievement: float
    relationship_progress: float
    topic_development_score: float
    memory_integration_score: float
    proactive_success_rate: float
    session_duration_minutes: float
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ContextEffectiveness:
    """Memory context effectiveness evaluation"""
    conversation_id: str
    user_id: str
    memory_relevance: float
    information_gaps: List[str]
    optimization_opportunities: List[str]
    redundant_information: List[str]
    context_compression_ratio: float
    token_efficiency: float
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class FeedbackReport:
    """Feedback for upstream components (5 & 6)"""
    feedback_id: str
    component_target: Literal["component5", "component6"]
    recommendation_type: Literal["memory_selection", "context_assembly", "personality", "proactive_timing"]
    priority_level: Literal["low", "medium", "high", "critical"]
    expected_impact: float
    recommendation_details: str
    supporting_metrics: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class QualityMetrics:
    """Comprehensive response quality assessment"""
    coherence_score: float
    relevance_score: float
    context_usage_score: float
    personality_consistency_score: float
    safety_score: float
    engagement_potential: float
    overall_quality: float
    confidence_level: float
    analysis_timestamp: datetime = field(default_factory=datetime.utcnow)


# ============================================================================
# INTEGRATION INTERFACES
# ============================================================================

@dataclass
class Component5Interface:
    """Interface for Component 5 LSTM Memory Gates"""
    get_memory_context: callable
    update_memory_access: callable
    get_user_profile: callable


@dataclass
class VectorDatabaseInterface:
    """Interface for vector database operations"""
    read_chat_embeddings: callable
    read_memory_embeddings: callable
    read_semantic_search: callable
    write_chat_embeddings: callable
    write_memory_embeddings: callable
    write_semantic_search: callable


@dataclass
class EmotionAnalysisInterface:
    """Interface for Component 2 Emotion Model"""
    analyze_emotion: callable
    get_emotional_state: callable
    track_emotion_changes: callable


@dataclass
class SemanticAnalysisInterface:
    """Interface for Component 3 NER & Embeddings"""
    generate_embeddings: callable
    extract_entities: callable
    semantic_similarity: callable


# ============================================================================
# UTILITY MODELS
# ============================================================================

@dataclass
class PerformanceMetrics:
    """System performance monitoring"""
    component_id: str
    operation_type: str
    execution_time_ms: float
    memory_usage_mb: float
    cpu_usage_percent: float
    success_rate: float
    error_count: int
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ErrorLog:
    """Error tracking and logging"""
    error_id: str
    component_id: str
    error_type: str
    error_message: str
    stack_trace: str
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    severity: Literal["low", "medium", "high", "critical"] = "medium"


@dataclass
class APIMetrics:
    """API usage and performance metrics"""
    api_name: str
    endpoint: str
    response_time_ms: float
    status_code: int
    token_usage: int
    cost_usd: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None


# ============================================================================
# PYDANTIC MODELS FOR API VALIDATION
# ============================================================================

class MemoryContextModel(BaseModel):
    """Pydantic model for Component 5 output validation"""
    selected_memories: List[Dict[str, Any]]
    relevance_scores: List[float]
    token_usage: int
    assembly_metadata: Dict[str, Any]

    @validator('token_usage')
    def validate_token_usage(cls, v):
        if v < 0 or v > 10000:
            raise ValueError('Token usage must be between 0 and 10000')
        return v

    @validator('relevance_scores')
    def validate_relevance_scores(cls, v):
        if not all(0 <= score <= 1 for score in v):
            raise ValueError('All relevance scores must be between 0 and 1')
        return v


class GeminiRequestModel(BaseModel):
    """Pydantic model for Gemini API request validation"""
    conversation_id: str
    user_id: str
    system_prompt: str
    context_section: str
    conversation_history: str
    current_message: str
    response_guidelines: Dict[str, Any]
    api_parameters: Dict[str, Any]
    user_preferences: Dict[str, Any]
    token_budget: int = Field(2000, ge=100, le=10000)

    class Config:
        extra = "forbid"


class ResponseAnalysisModel(BaseModel):
    """Pydantic model for response analysis validation"""
    response_id: str
    conversation_id: str
    user_id: str
    quality_scores: Dict[str, float]
    context_usage: Dict[str, Any]
    user_satisfaction: float = Field(ge=0.0, le=1.0)
    improvement_suggestions: List[str]

    class Config:
        extra = "forbid"
