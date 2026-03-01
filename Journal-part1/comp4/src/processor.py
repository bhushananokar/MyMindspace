"""
Component 4 Main Processor
High-level interface for the Feature Engineering Pipeline
"""

import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import logging

from comp4.data.schemas import Component4Input, EngineeredFeatures, UserHistoryContext
from .feature_engineer import FeatureEngineer

logger = logging.getLogger(__name__)

class Component4Processor:
    """
    Main processor for Component 4: Feature Engineering Pipeline
    Provides high-level interface for transforming journal analysis into feature vectors
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize Component 4 processor
        
        Args:
            config_path: Path to configuration file (optional)
        """
        self.name = "Component4Processor"
        self.version = "4.0"
        
        # Load configuration
        self.config = self._load_config(config_path) if config_path else {}
        
        # Initialize feature engineer
        self.feature_engineer = FeatureEngineer(self.config)
        
        # Performance tracking
        self.total_processed = 0
        self.session_start_time = datetime.now()
        
        logger.info(f"Component4Processor {self.version} initialized")
    
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
        Process a single journal entry into feature vectors
        
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
        """
        try:
            logger.debug(f"Processing journal entry {entry_id} for user {user_id}")
            
            # Create Component4Input
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
            
            # Process through feature engineering pipeline
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
            raise RuntimeError(f"Component 4 processing failed: {e}")
    
    def process_from_integration_output(
        self,
        integration_output: Dict[str, Any]
    ) -> EngineeredFeatures:
        """
        Process from Component 2+3 integration output
        
        Args:
            integration_output: Output from production_integration.py
            
        Returns:
            EngineeredFeatures with 90D feature vector and metadata
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
            raise RuntimeError(f"Component 4 integration processing failed: {e}")
    
    def batch_process(
        self,
        input_batch: List[Union[Component4Input, Dict[str, Any]]]
    ) -> List[EngineeredFeatures]:
        """
        Process multiple journal entries in batch
        
        Args:
            input_batch: List of Component4Input objects or dictionaries
            
        Returns:
            List of EngineeredFeatures objects
        """
        try:
            logger.info(f"Starting batch processing of {len(input_batch)} entries")
            start_time = time.time()
            
            results = []
            for i, input_data in enumerate(input_batch):
                try:
                    if isinstance(input_data, dict):
                        result = self.process_from_integration_output(input_data)
                    else:
                        result = self.feature_engineer.engineer_features(input_data)
                    
                    results.append(result)
                    
                except Exception as e:
                    logger.error(f"Error processing batch item {i}: {e}")
                    # Continue with other items
                    continue
            
            processing_time = (time.time() - start_time) * 1000
            logger.info(
                f"Batch processing completed: {len(results)}/{len(input_batch)} "
                f"entries processed in {processing_time:.1f}ms"
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Error in batch processing: {e}")
            raise RuntimeError(f"Batch processing failed: {e}")
    
    def validate_input(
        self,
        emotion_analysis,
        semantic_analysis,
        user_id: str,
        entry_id: str,
        raw_text: str
    ) -> Dict[str, Any]:
        """
        Validate input data before processing
        
        Args:
            emotion_analysis: EmotionAnalysis from Component 2
            semantic_analysis: SemanticAnalysis from Component 3
            user_id: User identifier
            entry_id: Entry identifier
            raw_text: Original journal text
            
        Returns:
            Dictionary with validation results
        """
        try:
            validation_results = {
                'is_valid': True,
                'issues': [],
                'warnings': []
            }
            
            # Check required fields
            if not user_id or not user_id.strip():
                validation_results['is_valid'] = False
                validation_results['issues'].append("user_id is required")
            
            if not entry_id or not entry_id.strip():
                validation_results['is_valid'] = False
                validation_results['issues'].append("entry_id is required")
            
            if not raw_text or not raw_text.strip():
                validation_results['warnings'].append("raw_text is empty")
            
            # Check emotion analysis
            if emotion_analysis is None:
                validation_results['is_valid'] = False
                validation_results['issues'].append("emotion_analysis is required")
            else:
                if not hasattr(emotion_analysis, 'dominant_emotion'):
                    validation_results['warnings'].append("emotion_analysis missing dominant_emotion")
                if not hasattr(emotion_analysis, 'emotions'):
                    validation_results['warnings'].append("emotion_analysis missing emotions")
            
            # Check semantic analysis
            if semantic_analysis is None:
                validation_results['is_valid'] = False
                validation_results['issues'].append("semantic_analysis is required")
            else:
                if not hasattr(semantic_analysis, 'detected_topics'):
                    validation_results['warnings'].append("semantic_analysis missing detected_topics")
                if not hasattr(semantic_analysis, 'people'):
                    validation_results['warnings'].append("semantic_analysis missing people")
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Error validating input: {e}")
            return {
                'is_valid': False,
                'issues': [f"Validation error: {e}"],
                'warnings': []
            }
    
    def get_feature_vector_info(self) -> Dict[str, Any]:
        """
        Get information about the feature vector structure
        
        Returns:
            Dictionary with feature vector documentation
        """
        return {
            'total_dimensions': 90,
            'feature_breakdown': {
                'temporal_features': {
                    'dimensions': 25,
                    'description': 'Time-based patterns, cycles, recency, and anomalies',
                    'range': [0.0, 1.0],
                    'examples': ['cyclical_hour', 'days_since_last', 'consistency_score']
                },
                'emotional_features': {
                    'dimensions': 20,
                    'description': 'Emotion dynamics, intensity patterns, stability metrics',
                    'range': [0.0, 1.0],
                    'examples': ['emotional_intensity', 'valence', 'arousal', 'dominant_emotion_onehot']
                },
                'semantic_features': {
                    'dimensions': 30,
                    'description': 'Topic modeling, novelty detection, content complexity',
                    'range': [0.0, 1.0],
                    'examples': ['topic_distribution', 'novelty_score', 'complexity_score']
                },
                'user_features': {
                    'dimensions': 15,
                    'description': 'Personal patterns, preferences, behavioral signatures',
                    'range': [0.0, 1.0],
                    'examples': ['writing_consistency', 'engagement_level', 'personal_growth']
                }
            },
            'metadata': {
                'memory_type': 'conversation | event | emotion | insight',
                'importance_score': 'Importance for memory ranking (0-1)',
                'gate_scores': 'LSTM memory gate scores for forget/input/output',
                'retrieval_triggers': 'Keywords for memory retrieval'
            },
            'quality_metrics': {
                'feature_completeness': 'Ratio of non-zero features (0-1)',
                'confidence_score': 'Overall processing confidence (0-1)',
                'processing_time_ms': 'Feature engineering time in milliseconds'
            }
        }
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """
        Get processing statistics and performance metrics
        
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
                    'total_processed': self.total_processed
                },
                'processor_info': {
                    'name': self.name,
                    'version': self.version,
                    'session_duration_seconds': session_duration
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
            return {
                'error': str(e),
                'total_processed': self.total_processed,
                'summary': {
                    'session_duration_seconds': 0,
                    'total_processed': self.total_processed
                }
            }
    
    def export_features_for_vector_db(
        self,
        engineered_features: EngineeredFeatures
    ) -> Dict[str, Any]:
        """
        Export features in format suitable for vector database storage
        
        Args:
            engineered_features: EngineeredFeatures object
            
        Returns:
            Dictionary formatted for vector database insertion
        """
        try:
            return {
                # Vector data
                'embedding': engineered_features.feature_vector.tolist(),
                'metadata': {
                    # Core metadata
                    'memory_type': engineered_features.metadata.memory_type,
                    'content_summary': engineered_features.metadata.content_summary,
                    'original_entry_id': engineered_features.metadata.original_entry_id,
                    'user_id': engineered_features.user_id,
                    'entry_timestamp': engineered_features.timestamp.isoformat(),
                    
                    # Scoring
                    'importance_score': engineered_features.metadata.importance_score,
                    'emotional_significance': engineered_features.metadata.emotional_significance,
                    'temporal_relevance': engineered_features.metadata.temporal_relevance,
                    'confidence_score': engineered_features.confidence_score,
                    'feature_completeness': engineered_features.feature_completeness,
                    
                    # LSTM gate scores
                    'gate_scores': engineered_features.metadata.gate_scores,
                    
                    # Retrieval and relationships
                    'retrieval_triggers': engineered_features.metadata.retrieval_triggers,
                    'relationships': engineered_features.metadata.relationships,
                    'context_needed': engineered_features.metadata.context_needed,
                    
                    # Feature breakdown (for analysis)
                    'feature_breakdown': {
                        'temporal': engineered_features.temporal_features.tolist(),
                        'emotional': engineered_features.emotional_features.tolist(),
                        'semantic': engineered_features.semantic_features.tolist(),
                        'user': engineered_features.user_features.tolist()
                    },
                    
                    # Processing metadata
                    'processing_time_ms': engineered_features.processing_time_ms,
                    'component_version': engineered_features.component_version,
                    'created_at': engineered_features.metadata.created_at.isoformat(),
                    'access_frequency': engineered_features.metadata.access_frequency
                }
            }
            
        except Exception as e:
            logger.error(f"Error exporting features for vector DB: {e}")
            return {
                'error': str(e),
                'embedding': engineered_features.feature_vector.tolist() if engineered_features else []
            }
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from file"""
        try:
            import yaml
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Configuration loaded from {config_path}")
            return config
        except Exception as e:
            logger.warning(f"Could not load config from {config_path}: {e}")
            return {}
    
    def shutdown(self):
        """Clean shutdown of the processor"""
        try:
            logger.info(f"Shutting down Component4Processor")
            
            # Get final stats
            final_stats = self.get_processing_stats()
            logger.info(f"Final processing stats: {final_stats}")
            
            # Any cleanup needed
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

# Convenience function for direct usage
def process_journal_entry(
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
    Convenience function to process a single journal entry
    
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
    """
    processor = Component4Processor(config_path)
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
