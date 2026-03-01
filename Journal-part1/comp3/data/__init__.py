"""
Data models and schemas for Component 3
"""

from .schemas import (
    PersonEntity,
    LocationEntity, 
    OrganizationEntity,
    ExtractedEvent,
    FollowupQuestion,
    TemporalFeatures,
    SemanticEmbedding,
    SemanticAnalysis
)

from .event_patterns import (
    EVENT_PATTERNS,
    IMPORTANCE_KEYWORDS,
    CONTEXT_PATTERNS,
    URGENT_EVENT_PATTERNS,
    classify_event_importance
)

__all__ = [
    # Schemas
    'PersonEntity',
    'LocationEntity',
    'OrganizationEntity', 
    'ExtractedEvent',
    'FollowupQuestion',
    'TemporalFeatures',
    'SemanticEmbedding',
    'SemanticAnalysis',
    
    # Event patterns
    'EVENT_PATTERNS',
    'IMPORTANCE_KEYWORDS',
    'CONTEXT_PATTERNS', 
    'URGENT_EVENT_PATTERNS',
    'classify_event_importance'
]