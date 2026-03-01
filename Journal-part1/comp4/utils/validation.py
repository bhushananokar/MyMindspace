"""
Validation utilities for Component 4
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging

from comp4.data.schemas import Component4Input, EngineeredFeatures

logger = logging.getLogger(__name__)

class FeatureValidator:
    """
    Comprehensive feature validation for Component 4
    """
    
    def __init__(self):
        self.name = "FeatureValidator"
        self.version = "4.0"
        
        # Validation rules
        self.dimension_requirements = {
            'temporal': 25,
            'emotional': 20,
            'semantic': 30,
            'user': 15,
            'total': 90
        }
        
        self.value_ranges = {
            'temporal': (0.0, 1.0),
            'emotional': (0.0, 1.0),
            'semantic': (0.0, 1.0),
            'user': (0.0, 1.0)
        }
        
        # Special validation rules
        self.special_validations = {
            'cyclical_features': self._validate_cyclical_features,
            'emotion_onehot': self._validate_emotion_onehot,
            'topic_distribution': self._validate_topic_distribution,
            'consistency_checks': self._validate_consistency
        }
    
    def validate_component4_input(self, input_data: Component4Input) -> Dict[str, Any]:
        """
        Validate Component4Input before processing
        
        Args:
            input_data: Component4Input object to validate
            
        Returns:
            Dictionary with validation results
        """
        try:
            validation_result = {
                'is_valid': True,
                'errors': [],
                'warnings': [],
                'input_quality_score': 0.0
            }
            
            # Check required fields
            required_fields = ['user_id', 'entry_id', 'session_id', 'entry_timestamp', 'raw_text']
            for field in required_fields:
                if not hasattr(input_data, field) or getattr(input_data, field) is None:
                    validation_result['errors'].append(f"Missing required field: {field}")
                    validation_result['is_valid'] = False
            
            # Validate user_id and entry_id
            if hasattr(input_data, 'user_id') and input_data.user_id:
                if not isinstance(input_data.user_id, str) or not input_data.user_id.strip():
                    validation_result['errors'].append("user_id must be a non-empty string")
                    validation_result['is_valid'] = False
            
            if hasattr(input_data, 'entry_id') and input_data.entry_id:
                if not isinstance(input_data.entry_id, str) or not input_data.entry_id.strip():
                    validation_result['errors'].append("entry_id must be a non-empty string")
                    validation_result['is_valid'] = False
            
            # Validate timestamp
            if hasattr(input_data, 'entry_timestamp') and input_data.entry_timestamp:
                if not isinstance(input_data.entry_timestamp, datetime):
                    validation_result['errors'].append("entry_timestamp must be a datetime object")
                    validation_result['is_valid'] = False
            
            # Validate text
            if hasattr(input_data, 'raw_text') and input_data.raw_text is not None:
                if not isinstance(input_data.raw_text, str):
                    validation_result['errors'].append("raw_text must be a string")
                    validation_result['is_valid'] = False
                elif len(input_data.raw_text.strip()) == 0:
                    validation_result['warnings'].append("raw_text is empty")
            
            # Validate emotion analysis
            emotion_validation = self._validate_emotion_analysis(input_data.emotion_analysis)
            if not emotion_validation['is_valid']:
                validation_result['errors'].extend(emotion_validation['errors'])
                validation_result['is_valid'] = False
            validation_result['warnings'].extend(emotion_validation['warnings'])
            
            # Validate semantic analysis
            semantic_validation = self._validate_semantic_analysis(input_data.semantic_analysis)
            if not semantic_validation['is_valid']:
                validation_result['errors'].extend(semantic_validation['errors'])
                validation_result['is_valid'] = False
            validation_result['warnings'].extend(semantic_validation['warnings'])
            
            # Calculate input quality score
            validation_result['input_quality_score'] = self._calculate_input_quality_score(
                input_data, emotion_validation, semantic_validation
            )
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating Component4Input: {e}")
            return {
                'is_valid': False,
                'errors': [f"Validation error: {str(e)}"],
                'warnings': [],
                'input_quality_score': 0.0
            }
    
    def validate_engineered_features(self, features: EngineeredFeatures) -> Dict[str, Any]:
        """
        Validate EngineeredFeatures output
        
        Args:
            features: EngineeredFeatures object to validate
            
        Returns:
            Dictionary with validation results
        """
        try:
            validation_result = {
                'is_valid': True,
                'errors': [],
                'warnings': [],
                'feature_quality_score': 0.0,
                'dimension_check': False,
                'range_check': False,
                'consistency_check': False,
                'special_checks': {}
            }
            
            # 1. Dimension validation
            dim_validation = self._validate_dimensions(features)
            validation_result['dimension_check'] = dim_validation['is_valid']
            if not dim_validation['is_valid']:
                validation_result['errors'].extend(dim_validation['errors'])
                validation_result['is_valid'] = False
            validation_result['warnings'].extend(dim_validation['warnings'])
            
            # 2. Range validation
            range_validation = self._validate_ranges(features)
            validation_result['range_check'] = range_validation['is_valid']
            if not range_validation['is_valid']:
                validation_result['errors'].extend(range_validation['errors'])
                validation_result['is_valid'] = False
            validation_result['warnings'].extend(range_validation['warnings'])
            
            # 3. Consistency validation
            consistency_validation = self._validate_feature_consistency(features)
            validation_result['consistency_check'] = consistency_validation['is_valid']
            if not consistency_validation['is_valid']:
                validation_result['errors'].extend(consistency_validation['errors'])
                validation_result['is_valid'] = False
            validation_result['warnings'].extend(consistency_validation['warnings'])
            
            # 4. Special validations
            for check_name, check_func in self.special_validations.items():
                try:
                    special_result = check_func(features)
                    validation_result['special_checks'][check_name] = special_result
                    if not special_result['is_valid']:
                        validation_result['warnings'].extend(special_result.get('warnings', []))
                except Exception as e:
                    validation_result['warnings'].append(f"Special check {check_name} failed: {e}")
            
            # 5. Calculate overall quality score
            validation_result['feature_quality_score'] = self._calculate_feature_quality_score(
                features, validation_result
            )
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating EngineeredFeatures: {e}")
            return {
                'is_valid': False,
                'errors': [f"Validation error: {str(e)}"],
                'warnings': [],
                'feature_quality_score': 0.0
            }
    
    def _validate_emotion_analysis(self, emotion_analysis) -> Dict[str, Any]:
        """Validate emotion analysis from Component 2"""
        result = {'is_valid': True, 'errors': [], 'warnings': []}
        
        if emotion_analysis is None:
            result['errors'].append("emotion_analysis is None")
            result['is_valid'] = False
            return result
        
        # Check for required attributes
        required_attrs = ['dominant_emotion', 'emotions']
        for attr in required_attrs:
            if not hasattr(emotion_analysis, attr):
                result['warnings'].append(f"emotion_analysis missing {attr}")
        
        # Validate emotions object
        if hasattr(emotion_analysis, 'emotions'):
            emotions = emotion_analysis.emotions
            emotion_names = ['joy', 'sadness', 'anger', 'fear', 'surprise', 'disgust', 'anticipation', 'trust']
            
            for emotion_name in emotion_names:
                if not hasattr(emotions, emotion_name):
                    result['warnings'].append(f"emotions missing {emotion_name}")
                else:
                    value = getattr(emotions, emotion_name)
                    if not isinstance(value, (int, float)) or not (0.0 <= value <= 1.0):
                        result['warnings'].append(f"Invalid emotion value for {emotion_name}: {value}")
        
        # Validate confidence if present
        if hasattr(emotion_analysis, 'confidence'):
            confidence = emotion_analysis.confidence
            if not isinstance(confidence, (int, float)) or not (0.0 <= confidence <= 1.0):
                result['warnings'].append(f"Invalid confidence value: {confidence}")
        
        return result
    
    def _validate_semantic_analysis(self, semantic_analysis) -> Dict[str, Any]:
        """Validate semantic analysis from Component 3"""
        result = {'is_valid': True, 'errors': [], 'warnings': []}
        
        if semantic_analysis is None:
            result['errors'].append("semantic_analysis is None")
            result['is_valid'] = False
            return result
        
        # Check for expected attributes
        expected_attrs = ['detected_topics', 'people', 'organizations', 'locations']
        for attr in expected_attrs:
            if not hasattr(semantic_analysis, attr):
                result['warnings'].append(f"semantic_analysis missing {attr}")
        
        # Validate people list
        if hasattr(semantic_analysis, 'people') and semantic_analysis.people:
            if not isinstance(semantic_analysis.people, list):
                result['warnings'].append("people should be a list")
            else:
                for i, person in enumerate(semantic_analysis.people):
                    if not hasattr(person, 'name'):
                        result['warnings'].append(f"person[{i}] missing name attribute")
        
        # Validate organizations list
        if hasattr(semantic_analysis, 'organizations') and semantic_analysis.organizations:
            if not isinstance(semantic_analysis.organizations, list):
                result['warnings'].append("organizations should be a list")
        
        # Validate topics
        if hasattr(semantic_analysis, 'detected_topics') and semantic_analysis.detected_topics:
            if not isinstance(semantic_analysis.detected_topics, list):
                result['warnings'].append("detected_topics should be a list")
        
        return result
    
    def _validate_dimensions(self, features: EngineeredFeatures) -> Dict[str, Any]:
        """Validate feature vector dimensions"""
        result = {'is_valid': True, 'errors': [], 'warnings': []}
        
        # Check main feature vector
        if features.feature_vector.shape != (90,):
            result['errors'].append(f"Main feature vector has shape {features.feature_vector.shape}, expected (90,)")
            result['is_valid'] = False
        
        # Check component vectors
        component_checks = [
            ('temporal_features', 25),
            ('emotional_features', 20),
            ('semantic_features', 30),
            ('user_features', 15)
        ]
        
        for attr_name, expected_dim in component_checks:
            vector = getattr(features, attr_name)
            if vector.shape != (expected_dim,):
                result['errors'].append(f"{attr_name} has shape {vector.shape}, expected ({expected_dim},)")
                result['is_valid'] = False
        
        # Check if main vector matches concatenated components
        if result['is_valid']:
            try:
                reconstructed = np.concatenate([
                    features.temporal_features,
                    features.emotional_features,
                    features.semantic_features,
                    features.user_features
                ])
                
                if not np.allclose(features.feature_vector, reconstructed, rtol=1e-6):
                    result['warnings'].append("Main feature vector doesn't match concatenated components")
            except Exception as e:
                result['warnings'].append(f"Error checking vector concatenation: {e}")
        
        return result
    
    def _validate_ranges(self, features: EngineeredFeatures) -> Dict[str, Any]:
        """Validate feature value ranges"""
        result = {'is_valid': True, 'errors': [], 'warnings': []}
        
        # Check each feature type
        feature_types = [
            ('temporal_features', 'temporal'),
            ('emotional_features', 'emotional'),
            ('semantic_features', 'semantic'),
            ('user_features', 'user')
        ]
        
        for attr_name, feature_type in feature_types:
            vector = getattr(features, attr_name)
            min_val, max_val = self.value_ranges[feature_type]
            
            # Check for NaN or infinite values
            if not np.all(np.isfinite(vector)):
                nan_count = np.sum(~np.isfinite(vector))
                result['errors'].append(f"{attr_name} has {nan_count} NaN/infinite values")
                result['is_valid'] = False
            
            # Check value ranges
            finite_mask = np.isfinite(vector)
            if np.any(finite_mask):
                finite_values = vector[finite_mask]
                
                if np.any(finite_values < min_val):
                    below_min = np.sum(finite_values < min_val)
                    result['warnings'].append(f"{attr_name} has {below_min} values below {min_val}")
                
                if np.any(finite_values > max_val):
                    above_max = np.sum(finite_values > max_val)
                    result['warnings'].append(f"{attr_name} has {above_max} values above {max_val}")
        
        return result
    
    def _validate_feature_consistency(self, features: EngineeredFeatures) -> Dict[str, Any]:
        """Validate logical consistency between features"""
        result = {'is_valid': True, 'errors': [], 'warnings': []}
        
        # Check metadata consistency
        if features.feature_completeness < 0 or features.feature_completeness > 1:
            result['warnings'].append(f"Invalid feature_completeness: {features.feature_completeness}")
        
        if features.confidence_score < 0 or features.confidence_score > 1:
            result['warnings'].append(f"Invalid confidence_score: {features.confidence_score}")
        
        if features.processing_time_ms < 0:
            result['warnings'].append(f"Negative processing_time_ms: {features.processing_time_ms}")
        
        # Check timestamp consistency
        if features.timestamp > datetime.now():
            result['warnings'].append("entry_timestamp is in the future")
        
        return result
    
    def _validate_cyclical_features(self, features: EngineeredFeatures) -> Dict[str, Any]:
        """Validate cyclical temporal features (sin/cos pairs)"""
        result = {'is_valid': True, 'warnings': []}
        
        try:
            temporal = features.temporal_features
            if len(temporal) >= 6:
                # Check sin/cos pairs for unit circle constraint
                pairs = [(0, 1), (2, 3), (4, 5)]  # (sin, cos) indices
                
                for sin_idx, cos_idx in pairs:
                    sin_val = temporal[sin_idx]
                    cos_val = temporal[cos_idx]
                    
                    # Check if sin^2 + cos^2 ≈ 1
                    magnitude_sq = sin_val**2 + cos_val**2
                    if abs(magnitude_sq - 1.0) > 0.1:  # Allow some tolerance
                        result['warnings'].append(
                            f"Cyclical feature pair ({sin_idx}, {cos_idx}) violates unit circle: "
                            f"sin^2 + cos^2 = {magnitude_sq:.3f}"
                        )
        except Exception as e:
            result['warnings'].append(f"Error validating cyclical features: {e}")
        
        return result
    
    def _validate_emotion_onehot(self, features: EngineeredFeatures) -> Dict[str, Any]:
        """Validate emotion one-hot encoding"""
        result = {'is_valid': True, 'warnings': []}
        
        try:
            emotional = features.emotional_features
            if len(emotional) >= 20:
                # Extract one-hot encoding (last 8 features)
                onehot = emotional[12:20]
                
                # Check if it sums to approximately 1
                onehot_sum = np.sum(onehot)
                if abs(onehot_sum - 1.0) > 0.1:
                    result['warnings'].append(
                        f"Emotion one-hot encoding sum = {onehot_sum:.3f}, expected ≈ 1.0"
                    )
                
                # Check if values are in [0, 1]
                if np.any(onehot < 0) or np.any(onehot > 1):
                    result['warnings'].append("Emotion one-hot values outside [0, 1] range")
        except Exception as e:
            result['warnings'].append(f"Error validating emotion one-hot: {e}")
        
        return result
    
    def _validate_topic_distribution(self, features: EngineeredFeatures) -> Dict[str, Any]:
        """Validate topic distribution normalization"""
        result = {'is_valid': True, 'warnings': []}
        
        try:
            semantic = features.semantic_features
            if len(semantic) >= 10:
                # Extract topic distribution (first 10 features)
                topics = semantic[:10]
                
                # Check if it sums to approximately 1
                topic_sum = np.sum(topics)
                if abs(topic_sum - 1.0) > 0.1:
                    result['warnings'].append(
                        f"Topic distribution sum = {topic_sum:.3f}, expected ≈ 1.0"
                    )
                
                # Check if all values are non-negative
                if np.any(topics < 0):
                    result['warnings'].append("Topic distribution has negative values")
        except Exception as e:
            result['warnings'].append(f"Error validating topic distribution: {e}")
        
        return result
    
    def _validate_consistency(self, features: EngineeredFeatures) -> Dict[str, Any]:
        """Validate cross-feature consistency"""
        result = {'is_valid': True, 'warnings': []}
        
        try:
            # Check if very high/low values across all features are suspicious
            all_values = features.feature_vector
            
            # Check for all zeros
            if np.allclose(all_values, 0.0):
                result['warnings'].append("All feature values are zero")
            
            # Check for all same values
            if len(set(all_values)) == 1:
                result['warnings'].append("All feature values are identical")
            
            # Check for extreme distributions
            high_values = np.sum(all_values > 0.9)
            low_values = np.sum(all_values < 0.1)
            
            if high_values > 80:  # >90% high values
                result['warnings'].append(f"Suspiciously high number of high values: {high_values}/90")
            
            if low_values > 80:  # >90% low values
                result['warnings'].append(f"Suspiciously high number of low values: {low_values}/90")
                
        except Exception as e:
            result['warnings'].append(f"Error validating consistency: {e}")
        
        return result
    
    def _calculate_input_quality_score(
        self, 
        input_data: Component4Input,
        emotion_validation: Dict[str, Any],
        semantic_validation: Dict[str, Any]
    ) -> float:
        """Calculate input quality score"""
        try:
            quality_score = 1.0
            
            # Penalize for missing required fields
            required_fields = ['user_id', 'entry_id', 'session_id', 'entry_timestamp', 'raw_text']
            missing_fields = sum(1 for field in required_fields 
                               if not hasattr(input_data, field) or getattr(input_data, field) is None)
            quality_score -= missing_fields * 0.2
            
            # Penalize for empty text
            if hasattr(input_data, 'raw_text') and input_data.raw_text:
                if len(input_data.raw_text.strip()) == 0:
                    quality_score -= 0.1
                elif len(input_data.raw_text.split()) < 5:  # Very short
                    quality_score -= 0.05
            
            # Factor in emotion analysis quality
            emotion_warnings = len(emotion_validation.get('warnings', []))
            quality_score -= emotion_warnings * 0.05
            
            # Factor in semantic analysis quality
            semantic_warnings = len(semantic_validation.get('warnings', []))
            quality_score -= semantic_warnings * 0.05
            
            return max(quality_score, 0.0)
            
        except Exception as e:
            logger.error(f"Error calculating input quality score: {e}")
            return 0.5
    
    def _calculate_feature_quality_score(
        self, 
        features: EngineeredFeatures,
        validation_result: Dict[str, Any]
    ) -> float:
        """Calculate feature quality score"""
        try:
            quality_score = 1.0
            
            # Major penalties for errors
            error_count = len(validation_result.get('errors', []))
            quality_score -= error_count * 0.3
            
            # Minor penalties for warnings
            warning_count = len(validation_result.get('warnings', []))
            quality_score -= warning_count * 0.05
            
            # Factor in dimension and range checks
            if not validation_result.get('dimension_check', False):
                quality_score -= 0.4
            if not validation_result.get('range_check', False):
                quality_score -= 0.3
            if not validation_result.get('consistency_check', False):
                quality_score -= 0.2
            
            # Factor in completeness and confidence
            if hasattr(features, 'feature_completeness'):
                quality_score *= features.feature_completeness
            
            if hasattr(features, 'confidence_score'):
                quality_score *= features.confidence_score
            
            return max(quality_score, 0.0)
            
        except Exception as e:
            logger.error(f"Error calculating feature quality score: {e}")
            return 0.5
