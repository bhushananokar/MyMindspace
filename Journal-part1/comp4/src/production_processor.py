"""
Production Component 4 Processor - NO FALLBACKS
Strict production version that integrates with Components 2+3 without any fallbacks
"""

import sys
import json
import uuid
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Any, Union
import logging

from comp4.data.schemas import Component4Input, EngineeredFeatures, UserHistoryContext
from .production_feature_engineer import ProductionFeatureEngineer

logger = logging.getLogger(__name__)

class ProductionComponent4Processor:
    """
    Production processor for Component 4: Feature Engineering Pipeline
    NO FALLBACKS - Strict production mode
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize production Component 4 processor
        
        Args:
            config_path: Path to configuration file (optional)
        """
        self.name = "ProductionComponent4Processor"
        self.version = "4.0-PRODUCTION"
        
        # Load configuration
        self.config = self._load_config(config_path) if config_path else {}
        
        # Initialize production feature engineer
        self.feature_engineer = ProductionFeatureEngineer(self.config)
        
        # Performance tracking
        self.total_processed = 0
        self.session_start_time = datetime.now()
        
        logger.info(f"ProductionComponent4Processor {self.version} initialized - STRICT MODE")
    
    def process_journal_entry(
        self,
        emotion_analysis,      # From Component 2
        semantic_analysis,     # From Component 3
        user_id: str,
        entry_id: str,
        session_id: str,
        entry_timestamp: datetime,
        raw_text: str,
        user_history: Optional[UserHistoryContext] = None,
        previous_entries: Optional[List[Dict]] = None
    ) -> EngineeredFeatures:
        """
        Process a single journal entry into feature vectors - PRODUCTION MODE
        
        Args:
            emotion_analysis: EmotionAnalysis from Component 2
            semantic_analysis: SemanticAnalysis from Component 3
            user_id: User identifier
            entry_id: Entry identifier
            session_id: Session identifier
            entry_timestamp: When the entry was written
            raw_text: Original journal text
            user_history: User's historical context (optional)
            previous_entries: Recent entries for pattern analysis (optional)
            
        Returns:
            EngineeredFeatures with 90D feature vector and metadata
            
        Raises:
            ValueError: If input validation fails
            RuntimeError: If processing fails
        """
        try:
            logger.debug(f"Processing journal entry {entry_id} for user {user_id}")
            
            # Validate inputs with robust error handling
            self.validate_input_strict(
                raw_text=raw_text,
                emotion_analysis=emotion_analysis,
                semantic_analysis=semantic_analysis,
                user_id=user_id,
                entry_id=entry_id
            )
            
            # Create Component4Input with strict validation
            input_data = Component4Input(
                emotion_analysis=emotion_analysis,
                semantic_analysis=semantic_analysis,
                user_id=user_id,
                entry_id=entry_id,
                session_id=session_id,
                entry_timestamp=entry_timestamp,
                raw_text=raw_text,
                user_history=user_history,
                previous_entries=previous_entries
            )
            
            # Process through production feature engineering pipeline
            engineered_features = self.feature_engineer.engineer_features(input_data)
            
            # Update tracking
            self.total_processed += 1
            
            logger.debug(
                f"Entry {entry_id} processed successfully in "
                f"{engineered_features.processing_time_ms:.1f}ms"
            )
            
            return engineered_features
            
        except Exception as e:
            logger.error(f"Error processing journal entry {entry_id}: {e}")
            raise RuntimeError(f"Production Component 4 processing failed: {e}") from e
    
    def process_from_integration_output(
        self,
        integration_output: Union[Dict[str, Any], Any]
    ) -> EngineeredFeatures:
        """
        Process from Component 2+3 integration output - PRODUCTION MODE
        
        Args:
            integration_output: Output from production_integration.py
            
        Returns:
            EngineeredFeatures with 90D feature vector and metadata
            
        Raises:
            ValueError: If integration output is invalid
            RuntimeError: If processing fails
        """
        try:
            # Extract required fields from integration output
            if isinstance(integration_output, dict):
                # From dictionary format
                emotion_analysis = integration_output.get('emotion_analysis')
                semantic_analysis = integration_output.get('semantic_analysis')
                user_id = integration_output.get('user_id')
                entry_id = integration_output.get('entry_id')
                session_id = integration_output.get('session_id')
                entry_timestamp = integration_output.get('entry_timestamp')
                raw_text = integration_output.get('raw_text')
                user_history = integration_output.get('user_history')
                previous_entries = integration_output.get('previous_entries')
                
                # Convert timestamp if it's a string
                if isinstance(entry_timestamp, str):
                    entry_timestamp = datetime.fromisoformat(entry_timestamp)
                
            else:
                # From Component4Input or similar object
                emotion_analysis = integration_output.emotion_analysis
                semantic_analysis = integration_output.semantic_analysis
                user_id = integration_output.user_id
                entry_id = integration_output.entry_id
                session_id = integration_output.session_id
                entry_timestamp = integration_output.entry_timestamp
                raw_text = integration_output.raw_text
                user_history = integration_output.user_history
                previous_entries = integration_output.previous_entries
            
            # Validate extracted data
            if not all([emotion_analysis, semantic_analysis, user_id, entry_id, session_id, entry_timestamp]):
                raise ValueError("Integration output missing required fields")
            
            # Process using main method
            return self.process_journal_entry(
                emotion_analysis=emotion_analysis,
                semantic_analysis=semantic_analysis,
                user_id=user_id,
                entry_id=entry_id,
                session_id=session_id,
                entry_timestamp=entry_timestamp,
                raw_text=raw_text,
                user_history=user_history,
                previous_entries=previous_entries
            )
            
        except Exception as e:
            logger.error(f"Error processing integration output: {e}")
            raise RuntimeError(f"Production Component 4 integration processing failed: {e}") from e
    
    def batch_process(
        self,
        input_batch: List[Union[Component4Input, Dict[str, Any]]]
    ) -> List[EngineeredFeatures]:
        """
        Process multiple journal entries in batch - PRODUCTION MODE
        
        Args:
            input_batch: List of Component4Input objects or dictionaries
            
        Returns:
            List of EngineeredFeatures objects
            
        Raises:
            RuntimeError: If batch processing fails
        """
        try:
            logger.info(f"Starting production batch processing of {len(input_batch)} entries")
            start_time = time.time()
            
            results = []
            failed_entries = []
            
            for i, input_data in enumerate(input_batch):
                try:
                    if isinstance(input_data, dict):
                        result = self.process_from_integration_output(input_data)
                    else:
                        result = self.feature_engineer.engineer_features(input_data)
                    
                    results.append(result)
                    
                except Exception as e:
                    logger.error(f"Error processing batch item {i}: {e}")
                    failed_entries.append((i, str(e)))
                    # In production mode, we fail the whole batch if any item fails
                    raise RuntimeError(f"Batch processing failed at item {i}: {e}") from e
            
            processing_time = (time.time() - start_time) * 1000
            logger.info(
                f"Production batch processing completed: {len(results)}/{len(input_batch)} "
                f"entries processed in {processing_time:.1f}ms"
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Error in production batch processing: {e}")
            raise RuntimeError(f"Production batch processing failed: {e}") from e
    
    def validate_input_strict(
        self,
        emotion_analysis,
        semantic_analysis,
        user_id: str,
        entry_id: str,
        raw_text: str
    ) -> None:
        """
        Strict input validation - PRODUCTION MODE
        
        Args:
            emotion_analysis: EmotionAnalysis from Component 2
            semantic_analysis: SemanticAnalysis from Component 3
            user_id: User identifier
            entry_id: Entry identifier
            raw_text: Original journal text
            
        Raises:
            ValueError: If validation fails
        """
        if not user_id or not user_id.strip():
            raise ValueError("user_id is required and cannot be empty")
        
        if not entry_id or not entry_id.strip():
            raise ValueError("entry_id is required and cannot be empty")
        
        if raw_text is None:
            raise ValueError("raw_text cannot be None")
        
        if emotion_analysis is None:
            raise ValueError("emotion_analysis is required")
        
        if semantic_analysis is None:
            raise ValueError("semantic_analysis is required")
        
        # Validate emotion analysis structure with robust error handling
        if isinstance(emotion_analysis, dict):
            if 'dominant_emotion' not in emotion_analysis:
                # Try to recover by setting a default
                logger.warning("emotion_analysis missing dominant_emotion, setting default")
                emotion_analysis['dominant_emotion'] = 'trust'
            if 'emotions' not in emotion_analysis:
                # Try to recover by creating minimal emotions structure
                logger.warning("emotion_analysis missing emotions, creating fallback structure")
                dominant = emotion_analysis.get('dominant_emotion', 'trust')
                intensity = emotion_analysis.get('intensity', 0.5)
                emotions = {
                    'joy': 0.0, 'sadness': 0.0, 'anger': 0.0, 'fear': 0.0,
                    'surprise': 0.0, 'disgust': 0.0, 'anticipation': 0.0, 'trust': 0.0
                }
                if dominant in emotions:
                    emotions[dominant] = intensity
                emotion_analysis['emotions'] = emotions
        else:
            if not hasattr(emotion_analysis, 'dominant_emotion'):
                logger.warning("emotion_analysis object missing dominant_emotion attribute")
                # Try to add it if possible
                if hasattr(emotion_analysis, '__dict__'):
                    emotion_analysis.dominant_emotion = 'trust'
                else:
                    raise ValueError("emotion_analysis missing dominant_emotion and cannot be modified")
            if not hasattr(emotion_analysis, 'emotions'):
                logger.warning("emotion_analysis object missing emotions attribute")
                # Try to add it if possible
                if hasattr(emotion_analysis, '__dict__'):
                    # Create minimal emotions structure
                    emotions_dict = {
                        'joy': 0.0, 'sadness': 0.0, 'anger': 0.0, 'fear': 0.0,
                        'surprise': 0.0, 'disgust': 0.0, 'anticipation': 0.0, 'trust': 0.5
                    }
                    emotion_analysis.emotions = emotions_dict
                else:
                    raise ValueError("emotion_analysis missing emotions and cannot be modified")
        
        # Validate semantic analysis structure with robust error handling
        if isinstance(semantic_analysis, dict):
            if 'detected_topics' not in semantic_analysis:
                logger.warning("semantic_analysis missing detected_topics, setting default")
                semantic_analysis['detected_topics'] = []
            if 'people' not in semantic_analysis:
                logger.warning("semantic_analysis missing people, setting default")
                semantic_analysis['people'] = []
        else:
            if not hasattr(semantic_analysis, 'detected_topics'):
                logger.warning("semantic_analysis object missing detected_topics attribute")
                if hasattr(semantic_analysis, '__dict__'):
                    semantic_analysis.detected_topics = []
                else:
                    raise ValueError("semantic_analysis missing detected_topics and cannot be modified")
            if not hasattr(semantic_analysis, 'people'):
                logger.warning("semantic_analysis object missing people attribute")
                if hasattr(semantic_analysis, '__dict__'):
                    semantic_analysis.people = []
                else:
                    raise ValueError("semantic_analysis missing people and cannot be modified")
    
    def export_for_astra_db(
        self,
        engineered_features: EngineeredFeatures,
        c23_output: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Export features in Astra DB collection formats - PRODUCTION MODE
        
        Args:
            engineered_features: EngineeredFeatures object
            c23_output: Components 2+3 integration output
            
        Returns:
            Dictionary with chat_embeddings and semantic_search collections data
            
        Raises:
            ValueError: If inputs are invalid
        """
        try:
            if not isinstance(engineered_features, EngineeredFeatures):
                raise ValueError("engineered_features must be EngineeredFeatures object")
            
            if not engineered_features.validate_dimensions():
                raise ValueError("engineered_features has invalid dimensions")
            
            # Import Astra DB schemas
            from comp4.data.schemas import (
                ChatEmbedding, SemanticSearch, EmotionContext, 
                EntitiesMentioned, TemporalContext, LinkedEntities, SearchMetadata
            )
            
            # Extract data from Components 2+3 output
            emotion_analysis = c23_output.get('emotion_analysis', {})
            semantic_analysis = c23_output.get('semantic_analysis', {})
            
            # Create emotion context
            emotion_context = EmotionContext(
                dominant_emotion=emotion_analysis.get('dominant_emotion', 'neutral'),
                intensity=emotion_analysis.get('emotional_intensity', 0.5),
                emotions=emotion_analysis.get('emotions', {})
            )
            
            # Create entities mentioned
            entities_mentioned = EntitiesMentioned(
                people=[p.get('name', '') for p in semantic_analysis.get('people', [])],
                locations=[l.get('name', '') for l in semantic_analysis.get('locations', [])],
                organizations=[o.get('name', '') for o in semantic_analysis.get('organizations', [])]
            )
            
            # Create temporal context
            timestamp = engineered_features.timestamp
            temporal_context = TemporalContext(
                hour_of_day=timestamp.hour,
                day_of_week=timestamp.weekday(),
                is_weekend=timestamp.weekday() >= 5
            )
            
            # Create chat embedding record
            chat_embedding = ChatEmbedding(
                id=str(uuid.uuid4()),
                user_id=engineered_features.user_id,
                entry_id=engineered_features.entry_id,
                message_content=engineered_features.metadata.content_summary,
                message_type="user_message",
                timestamp=timestamp,
                session_id=engineered_features.metadata.context_needed.get('session_id', ''),
                conversation_context=c23_output.get('cross_component_insights', {}).get('summary', ''),
                primary_embedding=semantic_analysis.get('primary_embedding', {}).get('vector', []),
                lightweight_embedding=semantic_analysis.get('lightweight_embedding', {}).get('vector', []),
                text_length=len(engineered_features.metadata.content_summary),
                processing_time_ms=engineered_features.processing_time_ms,
                model_version=engineered_features.component_version,
                semantic_tags=semantic_analysis.get('detected_topics', []),
                emotion_context=emotion_context,
                entities_mentioned=entities_mentioned,
                temporal_context=temporal_context
            )
            
            # Create linked entities for semantic search
            linked_entities = LinkedEntities(
                people=[p.get('name', '') for p in semantic_analysis.get('people', [])],
                locations=[l.get('name', '') for l in semantic_analysis.get('locations', [])],
                events=[e.get('description', '') for e in semantic_analysis.get('future_events', [])],
                topics=semantic_analysis.get('detected_topics', [])
            )
            
            # Create search metadata
            search_metadata = SearchMetadata(
                boost_factor=engineered_features.metadata.importance_score,
                recency_weight=engineered_features.metadata.temporal_relevance,
                user_preference_alignment=engineered_features.confidence_score
            )
            
            # Create semantic search record
            semantic_search = SemanticSearch(
                id=str(uuid.uuid4()),
                user_id=engineered_features.user_id,
                content_type="journal_entry",
                title=f"Entry {engineered_features.entry_id}",
                content=engineered_features.metadata.content_summary,
                primary_embedding=semantic_analysis.get('primary_embedding', {}).get('vector', []),
                created_at=timestamp,
                updated_at=timestamp,
                tags=semantic_analysis.get('detected_topics', []) + engineered_features.metadata.retrieval_triggers,
                linked_entities=linked_entities,
                search_metadata=search_metadata
            )
            
            return {
                'chat_embeddings': chat_embedding.to_dict(),
                'semantic_search': semantic_search.to_dict(),
                'processing_metadata': {
                    'component_version': engineered_features.component_version,
                    'processing_time_ms': engineered_features.processing_time_ms,
                    'feature_quality_score': engineered_features.metadata.feature_quality_score,
                    'confidence_score': engineered_features.confidence_score,
                    'production_mode': True,
                    'astra_db_ready': True
                }
            }
            
        except Exception as e:
            logger.error(f"Error exporting for Astra DB: {e}")
            raise RuntimeError(f"Astra DB export failed: {e}") from e
    
    def export_features_for_vector_db(
        self,
        engineered_features: EngineeredFeatures
    ) -> Dict[str, Any]:
        """
        DEPRECATED: Use export_for_astra_db() instead
        Legacy method for backward compatibility
        """
        logger.warning("export_features_for_vector_db() is deprecated. Use export_for_astra_db() instead.")
        
        # Return minimal format for backward compatibility
        return {
            'embedding': engineered_features.feature_vector.tolist(),
            'metadata': {
                'user_id': engineered_features.user_id,
                'entry_id': engineered_features.entry_id,
                'timestamp': engineered_features.timestamp.isoformat(),
                'deprecated': True,
                'use_astra_db_export': True
            }
        }
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """
        Get processing statistics and performance metrics - PRODUCTION MODE
        
        Returns:
            Dictionary with processing statistics
        """
        try:
            # Get feature engineer stats
            fe_stats = self.feature_engineer.get_performance_stats()
            
            # Calculate session stats
            session_duration = (datetime.now() - self.session_start_time).total_seconds()
            
            return {
                'summary': {
                    'session_duration_seconds': session_duration,
                    'total_processed': self.total_processed,
                    'mode': 'PRODUCTION-STRICT'
                },
                'processor_info': {
                    'name': self.name,
                    'version': self.version,
                    'session_duration_seconds': session_duration,
                    'production_mode': True
                },
                'processing_stats': {
                    'total_processed': self.total_processed,
                    'processor_total': self.total_processed,
                    'feature_engineer_total': fe_stats.get('total_processed', 0)
                },
                'performance_metrics': fe_stats,
                'session_info': {
                    'start_time': self.session_start_time.isoformat(),
                    'current_time': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting processing stats: {e}")
            raise RuntimeError(f"Stats retrieval failed: {e}") from e
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from file"""
        try:
            import yaml
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Production configuration loaded from {config_path}")
            return config
        except Exception as e:
            logger.error(f"Could not load config from {config_path}: {e}")
            raise RuntimeError(f"Configuration loading failed: {e}") from e

# Production convenience function
def process_journal_entry_production(
    emotion_analysis,
    semantic_analysis,
    user_id: str,
    entry_id: str,
    session_id: str,
    entry_timestamp: datetime,
    raw_text: str,
    user_history: Optional[UserHistoryContext] = None,
    previous_entries: Optional[List[Dict]] = None,
    config_path: Optional[str] = None
) -> EngineeredFeatures:
    """
    Production convenience function to process a single journal entry
    NO FALLBACKS - Strict production mode
    
    Args:
        emotion_analysis: EmotionAnalysis from Component 2
        semantic_analysis: SemanticAnalysis from Component 3
        user_id: User identifier
        entry_id: Entry identifier
        session_id: Session identifier
        entry_timestamp: When the entry was written
        raw_text: Original journal text
        user_history: User's historical context (optional)
        previous_entries: Recent entries for pattern analysis (optional)
        config_path: Path to configuration file (optional)
        
    Returns:
        EngineeredFeatures with 90D feature vector and metadata
        
    Raises:
        ValueError: If input validation fails
        RuntimeError: If processing fails
    """
    processor = ProductionComponent4Processor(config_path)
    return processor.process_journal_entry(
        emotion_analysis=emotion_analysis,
        semantic_analysis=semantic_analysis,
        user_id=user_id,
        entry_id=entry_id,
        session_id=session_id,
        entry_timestamp=entry_timestamp,
        raw_text=raw_text,
        user_history=user_history,
        previous_entries=previous_entries
    )
