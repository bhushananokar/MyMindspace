"""
Production Feature Engineer for Component 4 - NO FALLBACKS
Strict production version that fails fast and raises proper exceptions
"""

import numpy as np
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

from comp4.data.schemas import (
    Component4Input, EngineeredFeatures, FeatureMetadata,
    TemporalFeatures, EmotionalFeatures, SemanticFeatures, UserFeatures
)
from .temporal_extractor import TemporalFeatureExtractor
from .emotional_extractor import EmotionalFeatureExtractor
from .semantic_extractor import SemanticFeatureExtractor
from .user_extractor import UserFeatureExtractor
from .quality_controller import FeatureQualityController

logger = logging.getLogger(__name__)

class ProductionFeatureEngineer:
    """
    Production feature engineering orchestrator for Component 4
    NO FALLBACKS - Fails fast with proper error handling
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize production feature engineer
        
        Args:
            config: Configuration dictionary for feature engineering
        """
        self.name = "ProductionFeatureEngineer"
        self.version = "4.0-PRODUCTION"
        
        # Configuration - strict mode
        self.config = config or self._get_production_config()
        
        # Initialize feature extractors
        self.temporal_extractor = TemporalFeatureExtractor()
        self.emotional_extractor = EmotionalFeatureExtractor()
        self.semantic_extractor = SemanticFeatureExtractor()
        self.user_extractor = UserFeatureExtractor()
        
        # Quality controller
        self.quality_controller = FeatureQualityController()
        
        # Performance tracking
        self.total_processed = 0
        self.total_processing_time = 0.0
        self.error_count = 0
        
        logger.info(f"ProductionFeatureEngineer {self.version} initialized - STRICT MODE")
    
    def engineer_features(self, input_data: Component4Input) -> EngineeredFeatures:
        """
        Main feature engineering pipeline - PRODUCTION MODE
        Validates inputs strictly and fails fast on any issues
        
        Args:
            input_data: Component4Input with emotion and semantic analysis
            
        Returns:
            EngineeredFeatures with 90D feature vector and metadata
            
        Raises:
            ValueError: If input validation fails
            RuntimeError: If feature engineering fails
        """
        start_time = time.time()
        
        # 1. STRICT INPUT VALIDATION
        self._validate_input_strict(input_data)
        
        try:
            logger.debug(f"Engineering features for entry {input_data.entry_id}")
            
            # 2. Extract individual feature types - NO FALLBACKS
            temporal_features = self._extract_temporal_features_strict(input_data)
            emotional_features = self._extract_emotional_features_strict(input_data)
            semantic_features = self._extract_semantic_features_strict(input_data)
            user_features = self._extract_user_features_strict(input_data)
            
            # 3. Apply feature engineering transformations
            temporal_vector = self._engineer_temporal_features_strict(temporal_features)
            emotional_vector = self._engineer_emotional_features_strict(emotional_features)
            semantic_vector = self._engineer_semantic_features_strict(semantic_features)
            user_vector = self._engineer_user_features_strict(user_features)
            
            # 4. Validate dimensions strictly
            if temporal_vector.shape != (25,):
                raise RuntimeError(f"Temporal features dimension mismatch: {temporal_vector.shape} != (25,)")
            if emotional_vector.shape != (20,):
                raise RuntimeError(f"Emotional features dimension mismatch: {emotional_vector.shape} != (20,)")
            if semantic_vector.shape != (30,):
                raise RuntimeError(f"Semantic features dimension mismatch: {semantic_vector.shape} != (30,)")
            if user_vector.shape != (15,):
                raise RuntimeError(f"User features dimension mismatch: {user_vector.shape} != (15,)")
            
            # 5. Combine into main feature vector
            feature_vector = np.concatenate([
                temporal_vector, emotional_vector, semantic_vector, user_vector
            ])
            
            # 6. Final validation
            if feature_vector.shape != (90,):
                raise RuntimeError(f"Final feature vector dimension mismatch: {feature_vector.shape} != (90,)")
            
            if not np.all(np.isfinite(feature_vector)):
                raise RuntimeError("Feature vector contains non-finite values")
            
            # 7. Generate metadata
            metadata = self._generate_metadata_strict(input_data, {
                'temporal': temporal_features,
                'emotional': emotional_features,
                'semantic': semantic_features,
                'user': user_features
            })
            
            # 8. Calculate confidence score
            confidence_score = self._calculate_confidence_score_strict(
                temporal_features, emotional_features, semantic_features, user_features
            )
            
            # 9. Create engineered features object
            processing_time = (time.time() - start_time) * 1000
            
            engineered_features = EngineeredFeatures(
                feature_vector=feature_vector,
                temporal_features=temporal_vector,
                emotional_features=emotional_vector,
                semantic_features=semantic_vector,
                user_features=user_vector,
                metadata=metadata,
                feature_completeness=0.0,  # Will be calculated by quality controller
                confidence_score=confidence_score,
                processing_time_ms=processing_time,
                user_id=input_data.user_id,
                entry_id=input_data.entry_id,
                timestamp=input_data.entry_timestamp,
                component_version=self.version
            )
            
            # 10. Quality control and validation
            validation_results = self.quality_controller.validate_features(engineered_features)
            
            if not validation_results['is_valid']:
                raise RuntimeError(f"Feature validation failed: {validation_results['quality_issues']}")
            
            engineered_features.metadata.feature_quality_score = validation_results.get('quality_score', 0.0)
            
            # 11. Update performance tracking
            self.total_processed += 1
            self.total_processing_time += processing_time
            
            logger.debug(f"Feature engineering completed in {processing_time:.1f}ms")
            return engineered_features
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"Feature engineering failed for entry {input_data.entry_id}: {e}")
            raise RuntimeError(f"Component 4 feature engineering failed: {e}") from e
    
    def _validate_input_strict(self, input_data: Component4Input) -> None:
        """Strict input validation - NO FALLBACKS"""
        if not input_data.user_id or not input_data.user_id.strip():
            raise ValueError("user_id is required and cannot be empty")
        
        if not input_data.entry_id or not input_data.entry_id.strip():
            raise ValueError("entry_id is required and cannot be empty")
        
        if not input_data.session_id or not input_data.session_id.strip():
            raise ValueError("session_id is required and cannot be empty")
        
        if input_data.emotion_analysis is None:
            raise ValueError("emotion_analysis is required")
        
        if input_data.semantic_analysis is None:
            raise ValueError("semantic_analysis is required")
        
        if not isinstance(input_data.entry_timestamp, datetime):
            raise ValueError("entry_timestamp must be a datetime object")
        
        if input_data.raw_text is None:
            raise ValueError("raw_text cannot be None")
        
        # Validate emotion analysis structure
        if not hasattr(input_data.emotion_analysis, 'emotions'):
            raise ValueError("emotion_analysis missing emotions attribute")
        
        if not hasattr(input_data.emotion_analysis, 'dominant_emotion'):
            raise ValueError("emotion_analysis missing dominant_emotion attribute")
        
        # Validate semantic analysis structure
        if not hasattr(input_data.semantic_analysis, 'detected_topics'):
            raise ValueError("semantic_analysis missing detected_topics attribute")
    
    def _extract_temporal_features_strict(self, input_data: Component4Input) -> TemporalFeatures:
        """Extract temporal features - STRICT MODE"""
        try:
            features = self.temporal_extractor.extract(
                entry_timestamp=input_data.entry_timestamp,
                user_history=input_data.user_history,
                semantic_analysis=input_data.semantic_analysis,
                raw_text=input_data.raw_text
            )
            
            # Validate temporal features
            if not isinstance(features, TemporalFeatures):
                raise RuntimeError("Temporal extractor returned invalid type")
            
            return features
            
        except Exception as e:
            raise RuntimeError(f"Temporal feature extraction failed: {e}") from e
    
    def _extract_emotional_features_strict(self, input_data: Component4Input) -> EmotionalFeatures:
        """Extract emotional features - STRICT MODE"""
        try:
            # Extract previous emotions from previous_entries
            previous_emotions = []
            if input_data.previous_entries:
                for entry in input_data.previous_entries[-5:]:
                    if 'emotion_analysis' in entry:
                        previous_emotions.append(entry['emotion_analysis'])
            
            features = self.emotional_extractor.extract(
                emotion_analysis=input_data.emotion_analysis,
                user_history=input_data.user_history,
                previous_emotions=previous_emotions
            )
            
            # Validate emotional features
            if not isinstance(features, EmotionalFeatures):
                raise RuntimeError("Emotional extractor returned invalid type")
            
            return features
            
        except Exception as e:
            raise RuntimeError(f"Emotional feature extraction failed: {e}") from e
    
    def _extract_semantic_features_strict(self, input_data: Component4Input) -> SemanticFeatures:
        """Extract semantic features - STRICT MODE"""
        try:
            # Extract user topic history
            user_topic_history = []
            if input_data.user_history and input_data.user_history.topic_preferences:
                user_topic_history = input_data.user_history.topic_preferences
            
            features = self.semantic_extractor.extract(
                semantic_analysis=input_data.semantic_analysis,
                raw_text=input_data.raw_text,
                user_topic_history=user_topic_history
            )
            
            # Validate semantic features
            if not isinstance(features, SemanticFeatures):
                raise RuntimeError("Semantic extractor returned invalid type")
            
            return features
            
        except Exception as e:
            raise RuntimeError(f"Semantic feature extraction failed: {e}") from e
    
    def _extract_user_features_strict(self, input_data: Component4Input) -> UserFeatures:
        """Extract user-specific features - STRICT MODE"""
        try:
            # Prepare current entry data
            current_entry_data = {
                'text_length': len(input_data.raw_text.split()) if input_data.raw_text else 0,
                'session_id': input_data.session_id,
                'emotional_intensity': getattr(input_data.emotion_analysis, 'intensity', 0.5)
            }
            
            features = self.user_extractor.extract(
                user_history=input_data.user_history,
                current_entry_data=current_entry_data,
                semantic_analysis=input_data.semantic_analysis,
                emotion_analysis=input_data.emotion_analysis,
                raw_text=input_data.raw_text,
                entry_timestamp=input_data.entry_timestamp
            )
            
            # Validate user features
            if not isinstance(features, UserFeatures):
                raise RuntimeError("User extractor returned invalid type")
            
            return features
            
        except Exception as e:
            raise RuntimeError(f"User feature extraction failed: {e}") from e
    
    def _engineer_temporal_features_strict(self, temporal_features: TemporalFeatures) -> np.ndarray:
        """Apply feature engineering to temporal features - STRICT MODE"""
        try:
            # Get base vector from temporal features
            base_vector = temporal_features.to_vector()
            
            if base_vector.shape != (25,):
                raise RuntimeError(f"Temporal to_vector returned wrong shape: {base_vector.shape}")
            
            if not np.all(np.isfinite(base_vector)):
                raise RuntimeError("Temporal features contain non-finite values")
            
            # Apply normalization and scaling
            if self.config.get('normalize_temporal', True):
                base_vector = self._normalize_features_strict(base_vector, 'temporal')
            
            return base_vector.astype(np.float32)
            
        except Exception as e:
            raise RuntimeError(f"Temporal feature engineering failed: {e}") from e
    
    def _engineer_emotional_features_strict(self, emotional_features: EmotionalFeatures) -> np.ndarray:
        """Apply feature engineering to emotional features - STRICT MODE"""
        try:
            # Get base vector from emotional features
            base_vector = emotional_features.to_vector()
            
            if base_vector.shape != (20,):
                raise RuntimeError(f"Emotional to_vector returned wrong shape: {base_vector.shape}")
            
            if not np.all(np.isfinite(base_vector)):
                raise RuntimeError("Emotional features contain non-finite values")
            
            # Apply normalization
            if self.config.get('normalize_emotional', True):
                base_vector = self._normalize_features_strict(base_vector, 'emotional')
            
            return base_vector.astype(np.float32)
            
        except Exception as e:
            raise RuntimeError(f"Emotional feature engineering failed: {e}") from e
    
    def _engineer_semantic_features_strict(self, semantic_features: SemanticFeatures) -> np.ndarray:
        """Apply feature engineering to semantic features - STRICT MODE"""
        try:
            # Get base vector from semantic features
            base_vector = semantic_features.to_vector()
            
            if base_vector.shape != (30,):
                raise RuntimeError(f"Semantic to_vector returned wrong shape: {base_vector.shape}")
            
            if not np.all(np.isfinite(base_vector)):
                raise RuntimeError("Semantic features contain non-finite values")
            
            # Apply normalization
            if self.config.get('normalize_semantic', True):
                base_vector = self._normalize_features_strict(base_vector, 'semantic')
            
            return base_vector.astype(np.float32)
            
        except Exception as e:
            raise RuntimeError(f"Semantic feature engineering failed: {e}") from e
    
    def _engineer_user_features_strict(self, user_features: UserFeatures) -> np.ndarray:
        """Apply feature engineering to user features - STRICT MODE"""
        try:
            # Get base vector from user features
            base_vector = user_features.to_vector()
            
            if base_vector.shape != (15,):
                raise RuntimeError(f"User to_vector returned wrong shape: {base_vector.shape}")
            
            if not np.all(np.isfinite(base_vector)):
                raise RuntimeError("User features contain non-finite values")
            
            # Apply normalization
            if self.config.get('normalize_user', True):
                base_vector = self._normalize_features_strict(base_vector, 'user')
            
            return base_vector.astype(np.float32)
            
        except Exception as e:
            raise RuntimeError(f"User feature engineering failed: {e}") from e
    
    def _normalize_features_strict(self, features: np.ndarray, feature_type: str) -> np.ndarray:
        """Apply normalization - STRICT MODE"""
        try:
            normalization_method = self.config.get('normalization_method', 'minmax')
            
            if normalization_method == 'minmax':
                # Min-max scaling to [0, 1]
                min_val = np.min(features)
                max_val = np.max(features)
                if max_val > min_val:
                    features = (features - min_val) / (max_val - min_val)
            
            elif normalization_method == 'zscore':
                # Z-score normalization
                mean_val = np.mean(features)
                std_val = np.std(features)
                if std_val > 0:
                    features = (features - mean_val) / std_val
                    # Clip to reasonable range
                    features = np.clip(features, -3, 3)
                    # Rescale to [0, 1]
                    features = (features + 3) / 6
            
            # Ensure final values are in [0, 1] range
            features = np.clip(features, 0.0, 1.0)
            
            if not np.all(np.isfinite(features)):
                raise RuntimeError(f"Normalization produced non-finite values for {feature_type}")
            
            return features
            
        except Exception as e:
            raise RuntimeError(f"Feature normalization failed for {feature_type}: {e}") from e
    
    def _calculate_confidence_score_strict(
        self, 
        temporal_features: TemporalFeatures,
        emotional_features: EmotionalFeatures,
        semantic_features: SemanticFeatures,
        user_features: UserFeatures
    ) -> float:
        """Calculate overall confidence score - STRICT MODE"""
        try:
            confidence_scores = []
            
            # Temporal confidence
            confidence_scores.append(getattr(temporal_features, 'consistency_score', 0.5))
            
            # Emotional confidence
            confidence_scores.append(getattr(emotional_features, 'emotional_confidence', 0.5))
            
            # Semantic confidence
            confidence_scores.append(getattr(semantic_features, 'coherence_score', 0.5))
            
            # User confidence
            confidence_scores.append(getattr(user_features, 'writing_consistency', 0.5))
            
            # Calculate weighted average
            weights = [0.2, 0.3, 0.3, 0.2]
            overall_confidence = np.average(confidence_scores, weights=weights)
            
            if not np.isfinite(overall_confidence):
                raise RuntimeError("Confidence score calculation produced non-finite value")
            
            return float(np.clip(overall_confidence, 0.0, 1.0))
            
        except Exception as e:
            raise RuntimeError(f"Confidence score calculation failed: {e}") from e
    
    def _generate_metadata_strict(self, input_data: Component4Input, feature_data: Dict[str, Any]) -> FeatureMetadata:
        """Generate metadata - STRICT MODE"""
        try:
            # Generate content summary
            content_summary = self._generate_content_summary_strict(input_data.raw_text)
            
            # Calculate scores
            importance_score = self._calculate_importance_score_strict(input_data, feature_data)
            emotional_significance = self._calculate_emotional_significance_strict(feature_data['emotional'])
            temporal_relevance = self._calculate_temporal_relevance_strict(feature_data['temporal'])
            
            # Generate gate scores
            gate_scores = self._calculate_gate_scores_strict(feature_data)
            
            # Generate retrieval triggers
            retrieval_triggers = self._generate_retrieval_triggers_strict(input_data)
            
            # Determine memory type
            memory_type = self._determine_memory_type_strict(input_data, feature_data)
            
            return FeatureMetadata(
                memory_type=memory_type,
                content_summary=content_summary,
                original_entry_id=input_data.entry_id,
                importance_score=importance_score,
                emotional_significance=emotional_significance,
                temporal_relevance=temporal_relevance,
                gate_scores=gate_scores,
                retrieval_triggers=retrieval_triggers,
                context_needed={
                    'user_id': input_data.user_id,
                    'session_id': input_data.session_id,
                    'timestamp': input_data.entry_timestamp.isoformat()
                },
                version_info={
                    'component_version': self.version,
                    'temporal_extractor': self.temporal_extractor.version,
                    'emotional_extractor': self.emotional_extractor.version,
                    'semantic_extractor': self.semantic_extractor.version,
                    'user_extractor': self.user_extractor.version
                }
            )
            
        except Exception as e:
            raise RuntimeError(f"Metadata generation failed: {e}") from e
    
    def _generate_content_summary_strict(self, raw_text: str) -> str:
        """Generate content summary - STRICT MODE"""
        if not raw_text or not raw_text.strip():
            return "Empty entry"
        
        # Simple extractive summarization
        sentences = raw_text.split('.')
        if len(sentences) <= 2:
            return raw_text[:100] + "..." if len(raw_text) > 100 else raw_text
        
        # Take first sentence and longest sentence
        first_sentence = sentences[0].strip()
        longest_sentence = max(sentences, key=len).strip()
        
        if first_sentence == longest_sentence:
            summary = first_sentence
        else:
            summary = f"{first_sentence}. {longest_sentence}"
        
        return summary[:200] + "..." if len(summary) > 200 else summary
    
    def _calculate_importance_score_strict(self, input_data: Component4Input, feature_data: Dict[str, Any]) -> float:
        """Calculate importance score - STRICT MODE"""
        importance = 0.0
        
        # Emotional intensity
        emotional_features = feature_data.get('emotional')
        if emotional_features and hasattr(emotional_features, 'emotional_intensity'):
            importance += emotional_features.emotional_intensity * 0.3
        
        # Novelty
        semantic_features = feature_data.get('semantic')
        if semantic_features and hasattr(semantic_features, 'novelty_score'):
            importance += semantic_features.novelty_score * 0.3
        
        # Complexity
        if semantic_features and hasattr(semantic_features, 'complexity_score'):
            importance += semantic_features.complexity_score * 0.2
        
        # Social content
        if semantic_features and hasattr(semantic_features, 'entity_density'):
            importance += semantic_features.entity_density * 0.1
        
        # Personal growth
        user_features = feature_data.get('user')
        if user_features and hasattr(user_features, 'personal_growth'):
            importance += user_features.personal_growth * 0.1
        
        return min(max(importance, 0.0), 1.0)
    
    def _calculate_emotional_significance_strict(self, emotional_features: EmotionalFeatures) -> float:
        """Calculate emotional significance - STRICT MODE"""
        significance = 0.0
        
        if hasattr(emotional_features, 'emotional_intensity'):
            significance += emotional_features.emotional_intensity * 0.4
        
        if hasattr(emotional_features, 'valence'):
            significance += abs(emotional_features.valence) * 0.3
        
        if hasattr(emotional_features, 'arousal'):
            significance += emotional_features.arousal * 0.2
        
        if hasattr(emotional_features, 'volatility'):
            significance += emotional_features.volatility * 0.1
        
        return min(max(significance, 0.0), 1.0)
    
    def _calculate_temporal_relevance_strict(self, temporal_features: TemporalFeatures) -> float:
        """Calculate temporal relevance - STRICT MODE"""
        relevance = 0.5
        
        if hasattr(temporal_features, 'days_since_last'):
            days_ago = temporal_features.days_since_last
            if days_ago <= 1:
                relevance += 0.3
            elif days_ago <= 7:
                relevance += 0.2
        
        if hasattr(temporal_features, 'future_orientation'):
            relevance += temporal_features.future_orientation * 0.2
        
        return min(max(relevance, 0.0), 1.0)
    
    def _calculate_gate_scores_strict(self, feature_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate LSTM memory gate scores - STRICT MODE"""
        # Forget gate: based on novelty
        semantic_features = feature_data.get('semantic')
        forget_score = 1.0 - getattr(semantic_features, 'novelty_score', 0.5)
        
        # Input gate: based on emotional intensity
        emotional_features = feature_data.get('emotional')
        input_score = getattr(emotional_features, 'emotional_intensity', 0.5)
        
        # Output gate: based on complexity
        output_score = getattr(semantic_features, 'complexity_score', 0.5)
        
        # Confidence: overall confidence
        confidence = getattr(emotional_features, 'emotional_confidence', 0.5)
        
        return {
            'forget_score': min(max(forget_score, 0.0), 1.0),
            'input_score': min(max(input_score, 0.0), 1.0),
            'output_score': min(max(output_score, 0.0), 1.0),
            'confidence': min(max(confidence, 0.0), 1.0)
        }
    
    def _generate_retrieval_triggers_strict(self, input_data: Component4Input) -> List[str]:
        """Generate retrieval triggers - STRICT MODE"""
        triggers = []
        
        # Add detected topics
        if hasattr(input_data.semantic_analysis, 'detected_topics'):
            topics = input_data.semantic_analysis.detected_topics or []
            triggers.extend(topics[:5])
        
        # Add people mentioned
        if hasattr(input_data.semantic_analysis, 'people'):
            people = input_data.semantic_analysis.people or []
            for person in people:
                if hasattr(person, 'name'):
                    triggers.append(person.name.lower())
        
        # Add organizations
        if hasattr(input_data.semantic_analysis, 'organizations'):
            orgs = input_data.semantic_analysis.organizations or []
            for org in orgs:
                if hasattr(org, 'name'):
                    triggers.append(org.name.lower())
        
        # Add dominant emotion
        if hasattr(input_data.emotion_analysis, 'dominant_emotion'):
            triggers.append(input_data.emotion_analysis.dominant_emotion)
        
        return list(set(triggers))[:10]  # Remove duplicates and limit
    
    def _determine_memory_type_strict(self, input_data: Component4Input, feature_data: Dict[str, Any]) -> str:
        """Determine memory type - STRICT MODE"""
        # Check for future events
        if hasattr(input_data.semantic_analysis, 'future_events'):
            events = input_data.semantic_analysis.future_events or []
            if events:
                return "event"
        
        # Check for high emotional content
        emotional_features = feature_data.get('emotional')
        if emotional_features and hasattr(emotional_features, 'emotional_intensity'):
            if emotional_features.emotional_intensity > 0.7:
                return "emotion"
        
        # Check for insights or growth
        user_features = feature_data.get('user')
        if user_features and hasattr(user_features, 'personal_growth'):
            if user_features.personal_growth > 0.5:
                return "insight"
        
        return "conversation"
    
    def _get_production_config(self) -> Dict[str, Any]:
        """Get production configuration - NO DEFAULTS"""
        return {
            # Quality control - STRICT
            'enable_quality_control': True,
            'auto_repair': False,  # NO AUTO REPAIR IN PRODUCTION
            
            # Normalization
            'normalization_method': 'minmax',
            'normalize_temporal': True,
            'normalize_emotional': True,
            'normalize_semantic': True,
            'normalize_user': True,
            
            # Performance
            'max_processing_time_ms': 50,
            'strict_mode': True
        }
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return {
            'total_processed': self.total_processed,
            'total_processing_time_ms': self.total_processing_time,
            'avg_processing_time_ms': self.total_processing_time / max(self.total_processed, 1),
            'error_count': self.error_count,
            'error_rate': self.error_count / max(self.total_processed, 1),
            'component_version': self.version,
            'mode': 'PRODUCTION-STRICT'
        }
