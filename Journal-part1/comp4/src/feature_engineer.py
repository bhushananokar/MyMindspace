"""
Main Feature Engineer for Component 4
Orchestrates feature extraction, engineering, and quality control
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

class FeatureEngineer:
    """
    Main feature engineering orchestrator for Component 4
    Transforms semantic and emotion analysis into structured 90D feature vectors
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize feature engineer with all extractors
        
        Args:
            config: Configuration dictionary for feature engineering
        """
        self.name = "FeatureEngineer"
        self.version = "4.0"
        
        # Configuration
        self.config = config or self._get_default_config()
        
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
        
        logger.info(f"FeatureEngineer {self.version} initialized")
    
    def engineer_features(self, input_data: Component4Input) -> EngineeredFeatures:
        """
        Main feature engineering pipeline
        
        Args:
            input_data: Component4Input with emotion and semantic analysis
            
        Returns:
            EngineeredFeatures with 90D feature vector and metadata
        """
        start_time = time.time()
        
        try:
            logger.debug(f"Engineering features for entry {input_data.entry_id}")
            
            # 1. Extract and validate individual feature types
            temporal_features = self._extract_temporal_features(input_data)
            emotional_features = self._extract_emotional_features(input_data)
            semantic_features = self._extract_semantic_features(input_data)
            user_features = self._extract_user_features(input_data)
            
            if not all([temporal_features, emotional_features, semantic_features, user_features]):
                missing = []
                if not temporal_features: missing.append('temporal')
                if not emotional_features: missing.append('emotional')
                if not semantic_features: missing.append('semantic')
                if not user_features: missing.append('user')
                raise ValueError(f"Missing required feature sets: {', '.join(missing)}")
            
            # 2. Apply feature engineering transformations
            temporal_vector = self._engineer_temporal_features(temporal_features)
            emotional_vector = self._engineer_emotional_features(emotional_features)
            semantic_vector = self._engineer_semantic_features(semantic_features)
            user_vector = self._engineer_user_features(user_features)
            
            if not all([temporal_vector is not None, emotional_vector is not None, 
                       semantic_vector is not None, user_vector is not None]):
                missing = []
                if temporal_vector is None: missing.append('temporal')
                if emotional_vector is None: missing.append('emotional')
                if semantic_vector is None: missing.append('semantic')
                if user_vector is None: missing.append('user')
                raise ValueError(f"Failed to generate feature vectors for: {', '.join(missing)}")
            
            # 3. Combine into main feature vector
            try:
                feature_vector = np.concatenate([
                    temporal_vector, emotional_vector, semantic_vector, user_vector
                ])
            except Exception as e:
                raise ValueError(f"Failed to concatenate feature vectors: {str(e)}")
            
            # 4. Generate metadata
            metadata = self._generate_metadata(input_data, {
                'temporal': temporal_features,
                'emotional': emotional_features,
                'semantic': semantic_features,
                'user': user_features
            })
            
            # 5. Calculate confidence score
            confidence_score = self._calculate_confidence_score(
                temporal_features, emotional_features, semantic_features, user_features
            )
            
            # 6. Create engineered features object
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
            
            # 7. Quality control and validation
            if self.config.get('enable_quality_control', True):
                validation_results = self.quality_controller.validate_features(engineered_features)
                
                if not validation_results['is_valid'] and self.config.get('auto_repair', True):
                    engineered_features, repairs = self.quality_controller.repair_features(engineered_features)
                    logger.warning(f"Applied repairs to features: {repairs}")
                
                engineered_features.metadata.feature_quality_score = validation_results.get('quality_score', 0.0)
            
            # 8. Update performance tracking
            self.total_processed += 1
            self.total_processing_time += processing_time
            
            logger.debug(f"Feature engineering completed in {processing_time:.1f}ms")
            return engineered_features
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000  # Convert to ms
            self.error_count += 1
            error_msg = f"Error in feature engineering: {str(e)}"
            logger.error(error_msg, exc_info=True)
            # Don't create default features, let the error propagate up
            raise RuntimeError(error_msg) from e
    
    def _extract_temporal_features(self, input_data: Component4Input) -> TemporalFeatures:
        """Extract temporal features from input data"""
        try:
            return self.temporal_extractor.extract(
                entry_timestamp=input_data.entry_timestamp,
                user_history=input_data.user_history,
                semantic_analysis=input_data.semantic_analysis,
                raw_text=input_data.raw_text
            )
        except Exception as e:
            logger.error(f"Error extracting temporal features: {e}")
            return
    
    def _extract_emotional_features(self, input_data: Component4Input) -> EmotionalFeatures:
        """Extract emotional features from input data"""
        try:
            # Extract previous emotions from previous_entries for volatility calculation
            previous_emotions = []
            if input_data.previous_entries:
                for entry in input_data.previous_entries[-5:]:  # Last 5 entries
                    if 'emotion_analysis' in entry:
                        previous_emotions.append(entry['emotion_analysis'])
            
            return self.emotional_extractor.extract(
                emotion_analysis=input_data.emotion_analysis,
                user_history=input_data.user_history,
                previous_emotions=previous_emotions
            )
        except Exception as e:
            logger.error(f"Error extracting emotional features: {e}")
            return
    
    def _extract_semantic_features(self, input_data: Component4Input) -> SemanticFeatures:
        """Extract semantic features from input data"""
        try:
            # Extract user topic history
            user_topic_history = []
            if input_data.user_history and input_data.user_history.topic_preferences:
                user_topic_history = input_data.user_history.topic_preferences
            
            return self.semantic_extractor.extract(
                semantic_analysis=input_data.semantic_analysis,
                raw_text=input_data.raw_text,
                user_topic_history=user_topic_history
            )
        except Exception as e:
            logger.error(f"Error extracting semantic features: {e}")
            return
    
    def _extract_user_features(self, input_data: Component4Input) -> UserFeatures:
        """Extract user-specific features from input data"""
        try:
            # Prepare current entry data
            current_entry_data = {
                'text_length': len(input_data.raw_text.split()) if input_data.raw_text else 0,
                'session_id': input_data.session_id,
                'emotional_intensity': input_data.emotion_analysis.intensity if hasattr(input_data.emotion_analysis, 'intensity') else 0.5
            }
            
            return self.user_extractor.extract(
                user_history=input_data.user_history,
                current_entry_data=current_entry_data,
                semantic_analysis=input_data.semantic_analysis,
                emotion_analysis=input_data.emotion_analysis,
                raw_text=input_data.raw_text,
                entry_timestamp=input_data.entry_timestamp
            )
        except Exception as e:
            logger.error(f"Error extracting user features: {e}")
            return
    
    def _engineer_temporal_features(self, temporal_features: TemporalFeatures) -> np.ndarray:
        """Apply feature engineering to temporal features"""
        if temporal_features is None:
            raise ValueError("Temporal features cannot be None")
            
        # Get base vector from temporal features
        base_vector = temporal_features.to_vector()
        
        # Apply normalization and scaling
        if self.config.get('normalize_temporal', True):
            base_vector = self._normalize_features(base_vector, 'temporal')
        
        # Apply smoothing for cyclical features
        if self.config.get('smooth_cyclical', True):
            base_vector = self._smooth_cyclical_features(base_vector)
        
        return base_vector.astype(np.float32)
    
    def _engineer_emotional_features(self, emotional_features: EmotionalFeatures) -> np.ndarray:
        """Apply feature engineering to emotional features"""
        if emotional_features is None:
            raise ValueError("Emotional features cannot be None")
            
        # Get base vector from emotional features
        base_vector = emotional_features.to_vector()
        
        # Apply normalization
        if self.config.get('normalize_emotional', True):
            base_vector = self._normalize_features(base_vector, 'emotional')
        
        # Apply emotional balancing
        if self.config.get('balance_emotions', True):
            base_vector = self._balance_emotional_features(base_vector)
        
        return base_vector.astype(np.float32)
    
    def _engineer_semantic_features(self, semantic_features: SemanticFeatures) -> np.ndarray:
        """Apply feature engineering to semantic features"""
        if semantic_features is None:
            raise ValueError("Semantic features cannot be None")
            
        # Get base vector from semantic features
        base_vector = semantic_features.to_vector()
        
        # Apply normalization
        if self.config.get('normalize_semantic', True):
            base_vector = self._normalize_features(base_vector, 'semantic')
        
        # Apply semantic enhancement
        if self.config.get('enhance_semantic', True):
            base_vector = self._enhance_semantic_features(base_vector)
        
        return base_vector.astype(np.float32)
    
    def _engineer_user_features(self, user_features: UserFeatures) -> np.ndarray:
        """Apply feature engineering to user features"""
        if user_features is None:
            raise ValueError("User features cannot be None")
            
        # Get base vector from user features
        base_vector = user_features.to_vector()
        
        # Apply normalization
        if self.config.get('normalize_user', True):
            base_vector = self._normalize_features(base_vector, 'user')
        
        # Apply user-specific scaling
        if self.config.get('scale_user_patterns', True):
            base_vector = self._scale_user_patterns(base_vector)
        
        return base_vector.astype(np.float32)
    
    def _normalize_features(self, features: np.ndarray, feature_type: str) -> np.ndarray:
        """Apply normalization based on feature type"""
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
            
            elif normalization_method == 'robust':
                # Robust scaling using median and IQR
                median_val = np.median(features)
                q75, q25 = np.percentile(features, [75, 25])
                iqr = q75 - q25
                if iqr > 0:
                    features = (features - median_val) / iqr
                    features = np.clip(features, -2, 2)
                    features = (features + 2) / 4
            
            return np.clip(features, 0.0, 1.0)
            
        except Exception as e:
            logger.error(f"Error normalizing {feature_type} features: {e}")
            return features
    
    def _smooth_cyclical_features(self, temporal_vector: np.ndarray) -> np.ndarray:
        """Apply smoothing to cyclical temporal features"""
        try:
            if len(temporal_vector) >= 6:
                # Apply gentle smoothing to sin/cos pairs
                smoothing_factor = self.config.get('cyclical_smoothing', 0.1)
                
                # Smooth sin/cos pairs while preserving their relationship
                for i in range(0, 6, 2):  # Pairs: (sin, cos)
                    if i + 1 < len(temporal_vector):
                        sin_val, cos_val = temporal_vector[i], temporal_vector[i + 1]
                        # Ensure unit circle constraint
                        magnitude = np.sqrt(sin_val**2 + cos_val**2)
                        if magnitude > 0:
                            temporal_vector[i] = sin_val / magnitude
                            temporal_vector[i + 1] = cos_val / magnitude
            
            return temporal_vector
            
        except Exception as e:
            logger.error(f"Error smoothing cyclical features: {e}")
            return temporal_vector
    
    def _balance_emotional_features(self, emotional_vector: np.ndarray) -> np.ndarray:
        """Apply emotional balancing to prevent extreme values"""
        try:
            balancing_factor = self.config.get('emotional_balancing', 0.1)
            
            if len(emotional_vector) >= 12:
                # Extract dominant emotion one-hot (last 8 features)
                dominant_onehot = emotional_vector[12:20]
                
                # Apply soft balancing to prevent over-confidence
                if np.max(dominant_onehot) > 0.95:  # Very confident
                    # Reduce confidence slightly
                    max_idx = np.argmax(dominant_onehot)
                    dominant_onehot[max_idx] = 0.9
                    # Distribute remaining to other emotions
                    remaining = 0.1
                    other_indices = [i for i in range(8) if i != max_idx]
                    if other_indices:
                        dominant_onehot[other_indices] = remaining / len(other_indices)
                    
                    emotional_vector[12:20] = dominant_onehot
            
            return emotional_vector
            
        except Exception as e:
            logger.error(f"Error balancing emotional features: {e}")
            return emotional_vector
    
    def _enhance_semantic_features(self, semantic_vector: np.ndarray) -> np.ndarray:
        """Apply semantic enhancement for better representation"""
        try:
            if len(semantic_vector) >= 30:
                # Enhance topic distribution (first 10 features)
                topic_dist = semantic_vector[:10]
                
                # Apply topic smoothing
                if self.config.get('smooth_topics', True):
                    # Ensure topic distribution sums to 1
                    topic_sum = np.sum(topic_dist)
                    if topic_sum > 0:
                        topic_dist = topic_dist / topic_sum
                    else:
                        topic_dist[9] = 1.0  # Default to 'daily' category
                    
                    semantic_vector[:10] = topic_dist
                
                # Enhance complexity features
                if self.config.get('enhance_complexity', True):
                    # Apply non-linear scaling to complexity measures
                    complexity_features = [10, 11, 12]  # novelty, complexity, coherence
                    for idx in complexity_features:
                        if idx < len(semantic_vector):
                            # Apply square root to reduce extreme values
                            semantic_vector[idx] = np.sqrt(semantic_vector[idx])
            
            return semantic_vector
            
        except Exception as e:
            logger.error(f"Error enhancing semantic features: {e}")
            return semantic_vector
    
    def _scale_user_patterns(self, user_vector: np.ndarray) -> np.ndarray:
        """Apply user pattern scaling"""
        try:
            scaling_factor = self.config.get('user_scaling_factor', 1.0)
            
            if scaling_factor != 1.0:
                # Apply different scaling to different user features
                if len(user_vector) >= 15:
                    # Scale behavioral patterns more conservatively
                    user_vector[:5] *= scaling_factor * 0.8
                    
                    # Scale engagement and development features normally
                    user_vector[5:10] *= scaling_factor
                    
                    # Scale combined metrics more aggressively
                    user_vector[10:] *= scaling_factor * 1.2
            
            return np.clip(user_vector, 0.0, 1.0)
            
        except Exception as e:
            logger.error(f"Error scaling user patterns: {e}")
            return user_vector
    
    def _calculate_confidence_score(
        self, 
        temporal_features: TemporalFeatures,
        emotional_features: EmotionalFeatures,
        semantic_features: SemanticFeatures,
        user_features: UserFeatures
    ) -> float:
        """Calculate overall confidence score for the engineered features"""
        try:
            confidence_scores = []
            
            # Temporal confidence (based on data availability)
            if hasattr(temporal_features, 'consistency_score'):
                confidence_scores.append(temporal_features.consistency_score)
            else:
                confidence_scores.append(0.5)
            
            # Emotional confidence (from emotion analysis)
            if hasattr(emotional_features, 'emotional_confidence'):
                confidence_scores.append(emotional_features.emotional_confidence)
            else:
                confidence_scores.append(0.5)
            
            # Semantic confidence (based on content quality)
            if hasattr(semantic_features, 'coherence_score'):
                confidence_scores.append(semantic_features.coherence_score)
            else:
                confidence_scores.append(0.5)
            
            # User confidence (based on history availability)
            if hasattr(user_features, 'writing_consistency'):
                confidence_scores.append(user_features.writing_consistency)
            else:
                confidence_scores.append(0.5)
            
            # Calculate weighted average
            weights = [0.2, 0.3, 0.3, 0.2]  # Emphasize emotional and semantic
            overall_confidence = np.average(confidence_scores, weights=weights)
            
            return min(max(overall_confidence, 0.0), 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating confidence score: {e}")
            return 0.5
    
    def _generate_metadata(self, input_data: Component4Input, feature_data: Dict[str, Any]) -> FeatureMetadata:
        """Generate metadata for vector database storage"""
        try:
            # Generate content summary
            content_summary = self._generate_content_summary(input_data.raw_text)
            
            # Calculate importance score
            importance_score = self._calculate_importance_score(input_data, feature_data)
            
            # Calculate emotional significance
            emotional_significance = self._calculate_emotional_significance(feature_data['emotional'])
            
            # Calculate temporal relevance
            temporal_relevance = self._calculate_temporal_relevance(feature_data['temporal'])
            
            # Generate gate scores for LSTM memory gates
            gate_scores = self._calculate_gate_scores(feature_data)
            
            # Generate retrieval triggers
            retrieval_triggers = self._generate_retrieval_triggers(input_data)
            
            # Determine memory type
            memory_type = self._determine_memory_type(input_data, feature_data)
            
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
            logger.error(f"Error generating metadata: {e}")
            return FeatureMetadata(
                content_summary="Error generating summary",
                original_entry_id=input_data.entry_id
            )
    
    def _generate_content_summary(self, raw_text: str) -> str:
        """Generate a brief content summary"""
        try:
            if not raw_text:
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
            
            # Limit length
            return summary[:200] + "..." if len(summary) > 200 else summary
            
        except Exception as e:
            logger.error(f"Error generating content summary: {e}")
            return raw_text[:100] + "..." if len(raw_text) > 100 else raw_text
    
    def _calculate_importance_score(self, input_data: Component4Input, feature_data: Dict[str, Any]) -> float:
        """Calculate importance score for memory ranking"""
        try:
            importance = 0.0
            
            # Emotional intensity contributes to importance
            emotional_features = feature_data.get('emotional')
            if emotional_features and hasattr(emotional_features, 'emotional_intensity'):
                importance += emotional_features.emotional_intensity * 0.3
            
            # Novelty contributes to importance
            semantic_features = feature_data.get('semantic')
            if semantic_features and hasattr(semantic_features, 'novelty_score'):
                importance += semantic_features.novelty_score * 0.2
            
            # Complexity contributes to importance
            if semantic_features and hasattr(semantic_features, 'complexity_score'):
                importance += semantic_features.complexity_score * 0.2
            
            # Social content contributes to importance
            if semantic_features and hasattr(semantic_features, 'entity_density'):
                importance += semantic_features.entity_density * 0.1
            
            # Future events contribute to importance
            if semantic_features and hasattr(semantic_features, 'event_density'):
                importance += semantic_features.event_density * 0.1
            
            # Personal growth indicators contribute to importance
            user_features = feature_data.get('user')
            if user_features and hasattr(user_features, 'personal_growth'):
                importance += user_features.personal_growth * 0.1
            
            return min(max(importance, 0.0), 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating importance score: {e}")
            return 0.5
    
    def _calculate_emotional_significance(self, emotional_features: EmotionalFeatures) -> float:
        """Calculate emotional significance score"""
        try:
            if not emotional_features:
                return 0.0
            
            significance = 0.0
            
            # High intensity emotions are significant
            if hasattr(emotional_features, 'emotional_intensity'):
                significance += emotional_features.emotional_intensity * 0.4
            
            # Extreme valence (very positive or negative) is significant
            if hasattr(emotional_features, 'valence'):
                significance += abs(emotional_features.valence) * 0.3
            
            # High arousal is significant
            if hasattr(emotional_features, 'arousal'):
                significance += emotional_features.arousal * 0.2
            
            # Emotional volatility is significant
            if hasattr(emotional_features, 'volatility'):
                significance += emotional_features.volatility * 0.1
            
            return min(max(significance, 0.0), 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating emotional significance: {e}")
            return 0.0
    
    def _calculate_temporal_relevance(self, temporal_features: TemporalFeatures) -> float:
        """Calculate temporal relevance score"""
        try:
            if not temporal_features:
                return 0.5
            
            relevance = 0.5  # Base relevance
            
            # Recent entries are more relevant
            if hasattr(temporal_features, 'days_since_last'):
                days_ago = temporal_features.days_since_last
                if days_ago <= 1:
                    relevance += 0.3
                elif days_ago <= 7:
                    relevance += 0.2
                elif days_ago <= 30:
                    relevance += 0.1
            
            # Future-oriented content is relevant
            if hasattr(temporal_features, 'future_orientation'):
                relevance += temporal_features.future_orientation * 0.2
            
            return min(max(relevance, 0.0), 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating temporal relevance: {e}")
            return 0.5
    
    def _calculate_gate_scores(self, feature_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate LSTM memory gate scores"""
        try:
            # Forget gate: based on novelty and importance
            forget_score = 0.5
            semantic_features = feature_data.get('semantic')
            if semantic_features and hasattr(semantic_features, 'novelty_score'):
                forget_score = 1.0 - semantic_features.novelty_score  # High novelty = low forget
            
            # Input gate: based on emotional intensity and complexity
            input_score = 0.5
            emotional_features = feature_data.get('emotional')
            if emotional_features and hasattr(emotional_features, 'emotional_intensity'):
                input_score = emotional_features.emotional_intensity
            
            # Output gate: based on importance and relevance
            output_score = 0.5
            if semantic_features and hasattr(semantic_features, 'complexity_score'):
                output_score = semantic_features.complexity_score
            
            # Confidence: overall feature confidence
            confidence = 0.5
            if emotional_features and hasattr(emotional_features, 'emotional_confidence'):
                confidence = emotional_features.emotional_confidence
            
            return {
                'forget_score': min(max(forget_score, 0.0), 1.0),
                'input_score': min(max(input_score, 0.0), 1.0),
                'output_score': min(max(output_score, 0.0), 1.0),
                'confidence': min(max(confidence, 0.0), 1.0)
            }
            
        except Exception as e:
            logger.error(f"Error calculating gate scores: {e}")
            return {
                'forget_score': 0.5,
                'input_score': 0.5,
                'output_score': 0.5,
                'confidence': 0.5
            }
    
    def _generate_retrieval_triggers(self, input_data: Component4Input) -> List[str]:
        """Generate keywords for memory retrieval"""
        try:
            triggers = []
            
            # Add detected topics
            if (hasattr(input_data.semantic_analysis, 'detected_topics') and 
                input_data.semantic_analysis.detected_topics):
                triggers.extend(input_data.semantic_analysis.detected_topics[:5])  # Top 5 topics
            
            # Add people mentioned
            if (hasattr(input_data.semantic_analysis, 'people') and 
                input_data.semantic_analysis.people):
                for person in input_data.semantic_analysis.people:
                    if hasattr(person, 'name'):
                        triggers.append(person.name.lower())
            
            # Add organizations mentioned
            if (hasattr(input_data.semantic_analysis, 'organizations') and 
                input_data.semantic_analysis.organizations):
                for org in input_data.semantic_analysis.organizations:
                    if hasattr(org, 'name'):
                        triggers.append(org.name.lower())
            
            # Add dominant emotion
            if hasattr(input_data.emotion_analysis, 'dominant_emotion'):
                triggers.append(input_data.emotion_analysis.dominant_emotion)
            
            # Remove duplicates and limit
            triggers = list(set(triggers))[:10]
            
            return triggers
            
        except Exception as e:
            logger.error(f"Error generating retrieval triggers: {e}")
            return []
    
    def _determine_memory_type(self, input_data: Component4Input, feature_data: Dict[str, Any]) -> str:
        """Determine the type of memory for categorization"""
        try:
            # Check for future events
            if (hasattr(input_data.semantic_analysis, 'future_events') and 
                input_data.semantic_analysis.future_events):
                return "event"
            
            # Check for high emotional content
            emotional_features = feature_data.get('emotional')
            if (emotional_features and hasattr(emotional_features, 'emotional_intensity') and
                emotional_features.emotional_intensity > 0.7):
                return "emotion"
            
            # Check for insights or growth
            user_features = feature_data.get('user')
            if (user_features and hasattr(user_features, 'personal_growth') and
                user_features.personal_growth > 0.5):
                return "insight"
            
            # Default to conversation
            return "conversation"
            
        except Exception as e:
            logger.error(f"Error determining memory type: {e}")
            return "conversation"
    
    def _create_default_features(self, input_data: Component4Input, processing_time: float, error_msg: str) -> EngineeredFeatures:
        """Create default features when processing fails"""
        try:
            # Create default feature vectors
            temporal_vector = np.zeros(25, dtype=np.float32)
            emotional_vector = np.zeros(20, dtype=np.float32)
            semantic_vector = np.zeros(30, dtype=np.float32)
            user_vector = np.zeros(15, dtype=np.float32)
            
            # Set some reasonable defaults
            temporal_vector[6] = 1.0  # days_since_last
            emotional_vector[0] = 0.3  # neutral emotional intensity
            semantic_vector[9] = 1.0   # default topic category
            user_vector[0] = 0.5       # neutral writing consistency
            
            # Main feature vector
            feature_vector = np.concatenate([
                temporal_vector, emotional_vector, semantic_vector, user_vector
            ])
            
            # Default metadata
            metadata = FeatureMetadata(
                content_summary=f"Error processing entry: {error_msg[:100]}",
                original_entry_id=input_data.entry_id,
                processing_metadata={'error': error_msg}
            )
            
            return EngineeredFeatures(
                feature_vector=feature_vector,
                temporal_features=temporal_vector,
                emotional_features=emotional_vector,
                semantic_features=semantic_vector,
                user_features=user_vector,
                metadata=metadata,
                feature_completeness=0.0,
                confidence_score=0.0,
                processing_time_ms=processing_time,
                user_id=input_data.user_id,
                entry_id=input_data.entry_id,
                timestamp=input_data.entry_timestamp,
                component_version=self.version
            )
            
        except Exception as e:
            logger.error(f"Error creating default features: {e}")
            # Return absolute minimum
            return EngineeredFeatures(
                feature_vector=np.zeros(90, dtype=np.float32),
                temporal_features=np.zeros(25, dtype=np.float32),
                emotional_features=np.zeros(20, dtype=np.float32),
                semantic_features=np.zeros(30, dtype=np.float32),
                user_features=np.zeros(15, dtype=np.float32),
                metadata=FeatureMetadata(),
                feature_completeness=0.0,
                confidence_score=0.0,
                processing_time_ms=processing_time,
                user_id=input_data.user_id,
                entry_id=input_data.entry_id,
                timestamp=input_data.entry_timestamp
            )
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for feature engineering"""
        return {
            # Quality control
            'enable_quality_control': True,
            'auto_repair': True,
            
            # Normalization
            'normalization_method': 'minmax',  # 'minmax', 'zscore', 'robust'
            'normalize_temporal': True,
            'normalize_emotional': True,
            'normalize_semantic': True,
            'normalize_user': True,
            
            # Feature engineering
            'smooth_cyclical': True,
            'cyclical_smoothing': 0.1,
            'balance_emotions': True,
            'emotional_balancing': 0.1,
            'enhance_semantic': True,
            'smooth_topics': True,
            'enhance_complexity': True,
            'scale_user_patterns': True,
            'user_scaling_factor': 1.0,
            
            # Performance
            'max_processing_time_ms': 50,
            'batch_processing': False,
            'cache_features': False
        }
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        try:
            avg_processing_time = (
                self.total_processing_time / max(self.total_processed, 1)
            )
            
            error_rate = self.error_count / max(self.total_processed, 1)
            
            quality_stats = self.quality_controller.get_quality_statistics()
            
            return {
                'total_processed': self.total_processed,
                'total_processing_time_ms': self.total_processing_time,
                'avg_processing_time_ms': avg_processing_time,
                'error_count': self.error_count,
                'error_rate': error_rate,
                'quality_statistics': quality_stats,
                'component_version': self.version
            }
            
        except Exception as e:
            logger.error(f"Error getting performance stats: {e}")
            return {'error': str(e)}
    
    def batch_engineer_features(self, input_batch: List[Component4Input]) -> List[EngineeredFeatures]:
        """
        Process a batch of inputs for improved efficiency
        
        Args:
            input_batch: List of Component4Input objects
            
        Returns:
            List of EngineeredFeatures objects
        """
        try:
            logger.info(f"Processing batch of {len(input_batch)} entries")
            
            results = []
            for input_data in input_batch:
                result = self.engineer_features(input_data)
                results.append(result)
            
            logger.info(f"Batch processing completed: {len(results)} entries processed")
            return results
            
        except Exception as e:
            logger.error(f"Error in batch processing: {e}")
            # Return partial results if available
            return results if 'results' in locals() else []
