"""
Feature Quality Controller for Component 4
Validates feature quality, detects outliers, and ensures consistency
"""

import numpy as np
from typing import Dict, List, Optional, Any, Tuple
import logging

from comp4.data.schemas import (
    EngineeredFeatures, TemporalFeatures, EmotionalFeatures,
    SemanticFeatures, UserFeatures
)

logger = logging.getLogger(__name__)

class FeatureQualityController:
    """
    Controls and validates feature quality for Component 4
    Ensures completeness, consistency, and reliability of feature vectors
    """
    
    def __init__(self):
        """Initialize quality controller"""
        self.name = "FeatureQualityController"
        self.version = "4.0"
        
        # Quality thresholds
        self.min_completeness = 0.8  # Minimum feature completeness
        self.max_outlier_ratio = 0.1  # Maximum outlier ratio
        self.consistency_threshold = 0.95  # Feature consistency threshold
        
        # Feature value ranges for validation
        self.feature_ranges = {
            'temporal': {'min': 0.0, 'max': 1.0, 'special_values': [-1.0]},  # Allow -1 for missing
            'emotional': {'min': 0.0, 'max': 1.0, 'special_values': []},
            'semantic': {'min': 0.0, 'max': 1.0, 'special_values': []},
            'user': {'min': 0.0, 'max': 1.0, 'special_values': []}
        }
        
        # Quality metrics tracking
        self.quality_history = []
        self.outlier_counts = {'temporal': 0, 'emotional': 0, 'semantic': 0, 'user': 0}
    
    def validate_features(self, features: EngineeredFeatures) -> Dict[str, Any]:
        """
        Comprehensive feature validation
        
        Args:
            features: EngineeredFeatures object to validate
            
        Returns:
            Dictionary with validation results and quality metrics
        """
        try:
            validation_results = {
                'is_valid': True,
                'completeness_score': 0.0,
                'consistency_score': 0.0,
                'outlier_ratio': 0.0,
                'dimension_check': False,
                'range_check': False,
                'quality_issues': [],
                'recommendations': []
            }
            
            # 1. Dimension validation
            dim_check = self._validate_dimensions(features)
            validation_results['dimension_check'] = dim_check['valid']
            if not dim_check['valid']:
                validation_results['is_valid'] = False
                validation_results['quality_issues'].extend(dim_check['issues'])
            
            # 2. Range validation
            range_check = self._validate_ranges(features)
            validation_results['range_check'] = range_check['valid']
            if not range_check['valid']:
                validation_results['quality_issues'].extend(range_check['issues'])
            
            # 3. Completeness check
            completeness = self._calculate_completeness(features)
            validation_results['completeness_score'] = completeness
            if completeness < self.min_completeness:
                validation_results['is_valid'] = False
                validation_results['quality_issues'].append(
                    f"Low completeness: {completeness:.2f} < {self.min_completeness}"
                )
            
            # 4. Outlier detection
            outlier_results = self._detect_outliers(features)
            validation_results['outlier_ratio'] = outlier_results['ratio']
            if outlier_results['ratio'] > self.max_outlier_ratio:
                validation_results['quality_issues'].append(
                    f"High outlier ratio: {outlier_results['ratio']:.2f} > {self.max_outlier_ratio}"
                )
                validation_results['recommendations'].extend(outlier_results['recommendations'])
            
            # 5. Consistency check
            consistency = self._check_consistency(features)
            validation_results['consistency_score'] = consistency
            if consistency < self.consistency_threshold:
                validation_results['quality_issues'].append(
                    f"Low consistency: {consistency:.2f} < {self.consistency_threshold}"
                )
            
            # 6. Generate overall quality score
            quality_score = self._calculate_quality_score(validation_results)
            validation_results['quality_score'] = quality_score
            
            # Update quality history
            self.quality_history.append({
                'timestamp': features.timestamp,
                'quality_score': quality_score,
                'completeness': completeness,
                'consistency': consistency,
                'outlier_ratio': outlier_results['ratio']
            })
            
            # Keep last 100 quality records
            if len(self.quality_history) > 100:
                self.quality_history = self.quality_history[-100:]
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Error validating features: {e}")
            return {
                'is_valid': False,
                'quality_issues': [f"Validation error: {str(e)}"],
                'quality_score': 0.0
            }
    
    def _validate_dimensions(self, features: EngineeredFeatures) -> Dict[str, Any]:
        """Validate feature vector dimensions"""
        try:
            issues = []
            
            # Check main feature vector
            if features.feature_vector.shape != (90,):
                issues.append(f"Main feature vector has shape {features.feature_vector.shape}, expected (90,)")
            
            # Check component vectors
            expected_shapes = {
                'temporal_features': (25,),
                'emotional_features': (20,),
                'semantic_features': (30,),
                'user_features': (15,)
            }
            
            for feature_name, expected_shape in expected_shapes.items():
                actual_shape = getattr(features, feature_name).shape
                if actual_shape != expected_shape:
                    issues.append(f"{feature_name} has shape {actual_shape}, expected {expected_shape}")
            
            # Check if main vector is concatenation of components
            if len(issues) == 0:  # Only check if individual vectors are correct
                reconstructed = np.concatenate([
                    features.temporal_features,
                    features.emotional_features,
                    features.semantic_features,
                    features.user_features
                ])
                
                if not np.allclose(features.feature_vector, reconstructed, rtol=1e-6):
                    issues.append("Main feature vector doesn't match concatenated components")
            
            return {
                'valid': len(issues) == 0,
                'issues': issues
            }
            
        except Exception as e:
            return {
                'valid': False,
                'issues': [f"Dimension validation error: {str(e)}"]
            }
    
    def _validate_ranges(self, features: EngineeredFeatures) -> Dict[str, Any]:
        """Validate feature value ranges"""
        try:
            issues = []
            
            # Check each feature type
            feature_types = {
                'temporal': features.temporal_features,
                'emotional': features.emotional_features,
                'semantic': features.semantic_features,
                'user': features.user_features
            }
            
            for feature_type, feature_vector in feature_types.items():
                range_info = self.feature_ranges[feature_type]
                min_val, max_val = range_info['min'], range_info['max']
                special_values = range_info['special_values']
                
                # Check for values outside range (excluding special values)
                for i, value in enumerate(feature_vector):
                    if not np.isfinite(value):
                        issues.append(f"{feature_type}[{i}] is not finite: {value}")
                    elif value not in special_values and (value < min_val or value > max_val):
                        issues.append(f"{feature_type}[{i}] = {value:.3f} outside range [{min_val}, {max_val}]")
            
            return {
                'valid': len(issues) == 0,
                'issues': issues
            }
            
        except Exception as e:
            return {
                'valid': False,
                'issues': [f"Range validation error: {str(e)}"]
            }
    
    def _calculate_completeness(self, features: EngineeredFeatures) -> float:
        """Calculate feature completeness score"""
        try:
            total_features = 90
            complete_features = 0
            
            # Count non-zero, finite features
            for value in features.feature_vector:
                if np.isfinite(value) and value != 0.0:
                    complete_features += 1
            
            completeness = complete_features / total_features
            
            # Update in features object
            features.feature_completeness = completeness
            
            return completeness
            
        except Exception as e:
            logger.error(f"Error calculating completeness: {e}")
            return 0.0
    
    def _detect_outliers(self, features: EngineeredFeatures) -> Dict[str, Any]:
        """Detect outlier features using statistical methods"""
        try:
            outlier_count = 0
            total_features = 90
            recommendations = []
            
            # Use IQR method for outlier detection within each feature type
            feature_types = {
                'temporal': features.temporal_features,
                'emotional': features.emotional_features,
                'semantic': features.semantic_features,
                'user': features.user_features
            }
            
            for feature_type, feature_vector in feature_types.items():
                if len(feature_vector) < 4:  # Skip if too few features
                    continue
                
                # Calculate IQR
                q1 = np.percentile(feature_vector, 25)
                q3 = np.percentile(feature_vector, 75)
                iqr = q3 - q1
                
                if iqr > 0:  # Avoid division by zero
                    lower_bound = q1 - 1.5 * iqr
                    upper_bound = q3 + 1.5 * iqr
                    
                    # Count outliers
                    type_outliers = np.sum((feature_vector < lower_bound) | (feature_vector > upper_bound))
                    outlier_count += type_outliers
                    
                    # Update outlier tracking
                    self.outlier_counts[feature_type] += type_outliers
                    
                    if type_outliers > len(feature_vector) * 0.2:  # >20% outliers
                        recommendations.append(f"High outlier rate in {feature_type} features")
            
            outlier_ratio = outlier_count / total_features
            
            return {
                'ratio': outlier_ratio,
                'count': outlier_count,
                'recommendations': recommendations
            }
            
        except Exception as e:
            logger.error(f"Error detecting outliers: {e}")
            return {'ratio': 0.0, 'count': 0, 'recommendations': []}
    
    def _check_consistency(self, features: EngineeredFeatures) -> float:
        """Check feature consistency and logical relationships"""
        try:
            consistency_score = 1.0
            
            # 1. Check temporal feature consistency
            temporal_issues = self._check_temporal_consistency(features.temporal_features)
            consistency_score -= temporal_issues * 0.2
            
            # 2. Check emotional feature consistency
            emotional_issues = self._check_emotional_consistency(features.emotional_features)
            consistency_score -= emotional_issues * 0.2
            
            # 3. Check cross-feature relationships
            cross_issues = self._check_cross_feature_consistency(features)
            consistency_score -= cross_issues * 0.3
            
            # 4. Check for impossible combinations
            impossible_issues = self._check_impossible_combinations(features)
            consistency_score -= impossible_issues * 0.3
            
            return max(consistency_score, 0.0)
            
        except Exception as e:
            logger.error(f"Error checking consistency: {e}")
            return 0.5
    
    def _check_temporal_consistency(self, temporal_features: np.ndarray) -> float:
        """Check temporal feature logical consistency"""
        issues = 0.0
        
        try:
            # Extract specific temporal features (based on TemporalFeatures.to_vector structure)
            if len(temporal_features) >= 25:
                # Check cyclical encodings are valid
                sin_hour, cos_hour = temporal_features[0], temporal_features[1]
                sin_day, cos_day = temporal_features[2], temporal_features[3]
                sin_month, cos_month = temporal_features[4], temporal_features[5]
                
                # Check if sin^2 + cos^2 ≈ 1 for cyclical features
                cyclical_checks = [
                    abs((sin_hour**2 + cos_hour**2) - 1.0),
                    abs((sin_day**2 + cos_day**2) - 1.0),
                    abs((sin_month**2 + cos_month**2) - 1.0)
                ]
                
                for check in cyclical_checks:
                    if check > 0.1:  # Tolerance for floating point errors
                        issues += 0.3
                
                # Check logical relationships
                days_since_last = temporal_features[6] if len(temporal_features) > 6 else 0
                frequency_score = temporal_features[7] if len(temporal_features) > 7 else 0
                
                # Frequency and days_since_last should be inversely related
                if days_since_last > 7 and frequency_score > 0.8:  # High frequency despite long gap
                    issues += 0.2
                
        except Exception as e:
            logger.error(f"Error checking temporal consistency: {e}")
            issues += 0.5
        
        return min(issues, 1.0)
    
    def _check_emotional_consistency(self, emotional_features: np.ndarray) -> float:
        """Check emotional feature logical consistency"""
        issues = 0.0
        
        try:
            if len(emotional_features) >= 20:
                # Extract emotion metrics (based on EmotionalFeatures.to_vector structure)
                intensity = emotional_features[0]
                confidence = emotional_features[1]
                valence = emotional_features[2]
                arousal = emotional_features[3]
                
                # Check for logical inconsistencies
                # High intensity should generally correlate with high arousal
                if intensity > 0.8 and arousal < 0.3:
                    issues += 0.2
                
                # Very low confidence with extreme valence is suspicious
                if confidence < 0.3 and abs(valence) > 0.8:
                    issues += 0.3
                
                # Dominant emotion one-hot should sum to 1
                dominant_onehot = emotional_features[12:20] if len(emotional_features) >= 20 else []
                if len(dominant_onehot) == 8:
                    onehot_sum = np.sum(dominant_onehot)
                    if abs(onehot_sum - 1.0) > 0.1:
                        issues += 0.4
                
        except Exception as e:
            logger.error(f"Error checking emotional consistency: {e}")
            issues += 0.5
        
        return min(issues, 1.0)
    
    def _check_cross_feature_consistency(self, features: EngineeredFeatures) -> float:
        """Check consistency across different feature types"""
        issues = 0.0
        
        try:
            # Check if user consistency features align with temporal patterns
            if (len(features.user_features) >= 15 and 
                len(features.temporal_features) >= 25):
                
                user_consistency = features.user_features[0]  # writing_consistency
                temporal_consistency = features.temporal_features[8]  # consistency_score
                
                # These should be somewhat correlated
                consistency_diff = abs(user_consistency - temporal_consistency)
                if consistency_diff > 0.5:
                    issues += 0.2
            
            # Check if high emotional intensity aligns with high engagement
            if (len(features.emotional_features) >= 4 and 
                len(features.user_features) >= 15):
                
                emotional_intensity = features.emotional_features[0]
                engagement_level = features.user_features[5]
                
                # High intensity should generally indicate some engagement
                if emotional_intensity > 0.8 and engagement_level < 0.3:
                    issues += 0.1
            
            # Check semantic-user alignment
            if (len(features.semantic_features) >= 30 and 
                len(features.user_features) >= 15):
                
                social_language = features.semantic_features[18]  # social_language
                relationship_focus = features.user_features[7]    # relationship_focus
                
                # These should be somewhat aligned
                social_diff = abs(social_language - relationship_focus)
                if social_diff > 0.6:
                    issues += 0.1
                
        except Exception as e:
            logger.error(f"Error checking cross-feature consistency: {e}")
            issues += 0.3
        
        return min(issues, 1.0)
    
    def _check_impossible_combinations(self, features: EngineeredFeatures) -> float:
        """Check for impossible or highly unlikely feature combinations"""
        issues = 0.0
        
        try:
            # Check for all-zero vectors (usually indicates missing data)
            feature_vectors = [
                features.temporal_features,
                features.emotional_features,
                features.semantic_features,
                features.user_features
            ]
            
            for i, vector in enumerate(feature_vectors):
                if np.allclose(vector, 0.0, atol=1e-6):
                    issues += 0.25  # Each zero vector is 25% issue
            
            # Check for all-same values (usually indicates default filling)
            for vector in feature_vectors:
                if len(set(vector)) == 1 and vector[0] != 0.0:  # All same non-zero value
                    issues += 0.2
            
            # Check for extreme combinations
            if len(features.feature_vector) == 90:
                # Very high values across all features is suspicious
                high_value_ratio = np.sum(features.feature_vector > 0.9) / 90
                if high_value_ratio > 0.8:
                    issues += 0.3
                
                # Very low values across all features is also suspicious
                low_value_ratio = np.sum(features.feature_vector < 0.1) / 90
                if low_value_ratio > 0.8:
                    issues += 0.3
                
        except Exception as e:
            logger.error(f"Error checking impossible combinations: {e}")
            issues += 0.5
        
        return min(issues, 1.0)
    
    def _calculate_quality_score(self, validation_results: Dict[str, Any]) -> float:
        """Calculate overall quality score from validation results"""
        try:
            score = 1.0
            
            # Dimension and range checks are critical
            if not validation_results.get('dimension_check', False):
                score -= 0.4
            if not validation_results.get('range_check', False):
                score -= 0.3
            
            # Weight other factors
            completeness = validation_results.get('completeness_score', 0.0)
            consistency = validation_results.get('consistency_score', 0.0)
            outlier_ratio = validation_results.get('outlier_ratio', 1.0)
            
            score *= completeness  # Multiply by completeness
            score *= consistency   # Multiply by consistency
            score *= (1.0 - outlier_ratio)  # Reduce by outlier ratio
            
            return max(score, 0.0)
            
        except Exception as e:
            logger.error(f"Error calculating quality score: {e}")
            return 0.0
    
    def get_quality_statistics(self) -> Dict[str, Any]:
        """Get quality statistics from recent processing"""
        try:
            if not self.quality_history:
                return {'message': 'No quality history available'}
            
            recent_scores = [entry['quality_score'] for entry in self.quality_history[-20:]]
            recent_completeness = [entry['completeness'] for entry in self.quality_history[-20:]]
            recent_consistency = [entry['consistency'] for entry in self.quality_history[-20:]]
            
            return {
                'total_processed': len(self.quality_history),
                'avg_quality_score': np.mean(recent_scores),
                'min_quality_score': np.min(recent_scores),
                'max_quality_score': np.max(recent_scores),
                'avg_completeness': np.mean(recent_completeness),
                'avg_consistency': np.mean(recent_consistency),
                'outlier_counts': self.outlier_counts.copy(),
                'quality_trend': 'improving' if len(recent_scores) > 10 and recent_scores[-5:] > recent_scores[:5] else 'stable'
            }
            
        except Exception as e:
            logger.error(f"Error getting quality statistics: {e}")
            return {'error': str(e)}
    
    def repair_features(self, features: EngineeredFeatures) -> Tuple[EngineeredFeatures, List[str]]:
        """
        Attempt to repair common feature issues
        
        Args:
            features: EngineeredFeatures with potential issues
            
        Returns:
            Tuple of (repaired_features, list_of_repairs_made)
        """
        try:
            repairs_made = []
            
            # 1. Fix NaN and infinite values
            for attr_name in ['temporal_features', 'emotional_features', 'semantic_features', 'user_features']:
                vector = getattr(features, attr_name)
                
                # Replace NaN with 0
                nan_mask = ~np.isfinite(vector)
                if np.any(nan_mask):
                    vector[nan_mask] = 0.0
                    repairs_made.append(f"Replaced {np.sum(nan_mask)} NaN/inf values in {attr_name}")
            
            # 2. Clip values to valid ranges
            for attr_name in ['temporal_features', 'emotional_features', 'semantic_features', 'user_features']:
                vector = getattr(features, attr_name)
                
                # Clip to [0, 1] range (except special values)
                clipped_vector = np.clip(vector, 0.0, 1.0)
                if not np.allclose(vector, clipped_vector):
                    setattr(features, attr_name, clipped_vector)
                    repairs_made.append(f"Clipped out-of-range values in {attr_name}")
            
            # 3. Reconstruct main feature vector
            features.feature_vector = np.concatenate([
                features.temporal_features,
                features.emotional_features,
                features.semantic_features,
                features.user_features
            ])
            repairs_made.append("Reconstructed main feature vector")
            
            # 4. Recalculate completeness
            features.feature_completeness = self._calculate_completeness(features)
            repairs_made.append("Recalculated feature completeness")
            
            return features, repairs_made
            
        except Exception as e:
            logger.error(f"Error repairing features: {e}")
            return features, [f"Repair failed: {str(e)}"]
