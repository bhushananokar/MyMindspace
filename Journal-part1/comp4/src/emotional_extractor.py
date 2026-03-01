"""
Emotional Feature Extractor for Component 4
Extracts emotion dynamics, intensity patterns, and stability metrics
"""

import numpy as np
from typing import Dict, List, Optional, Any
import logging

from comp4.data.schemas import EmotionalFeatures, UserHistoryContext

logger = logging.getLogger(__name__)

class EmotionalFeatureExtractor:
    """
    Extracts emotional features from Component 2's emotion analysis
    Focuses on emotion dynamics, patterns, and user-specific baselines
    """
    
    def __init__(self):
        """Initialize emotional feature extractor"""
        self.name = "EmotionalFeatureExtractor"
        self.version = "4.0"
        
        # Emotion mapping for consistent indexing
        self.emotion_names = [
            'joy', 'sadness', 'anger', 'fear', 
            'surprise', 'disgust', 'anticipation', 'trust'
        ]
        
        # Valence and arousal mappings based on emotion theory
        self.emotion_valence = {
            'joy': 0.8, 'trust': 0.6, 'anticipation': 0.4, 'surprise': 0.0,
            'fear': -0.6, 'anger': -0.4, 'disgust': -0.8, 'sadness': -0.9
        }
        
        self.emotion_arousal = {
            'anger': 0.9, 'fear': 0.8, 'joy': 0.7, 'surprise': 0.8,
            'anticipation': 0.6, 'disgust': 0.4, 'trust': 0.3, 'sadness': 0.2
        }
    
    def extract(
        self,
        emotion_analysis,  # From Component 2
        user_history: Optional[UserHistoryContext] = None,
        previous_emotions: Optional[List[Dict]] = None
    ) -> EmotionalFeatures:
        """
        Extract emotional features from emotion analysis
        
        Args:
            emotion_analysis: EmotionAnalysis from Component 2
            user_history: User's emotional baseline and patterns
            previous_emotions: Recent emotional states for volatility calculation
            
        Returns:
            EmotionalFeatures object with 20-dimensional feature vector
        """
        try:
            # Extract core emotion vector
            emotion_vector = self._extract_emotion_vector(emotion_analysis)
            
            # Find dominant emotion
            dominant_emotion_idx = self._get_dominant_emotion_idx(emotion_analysis)
            
            # Calculate emotional metrics
            emotional_intensity = self._calculate_intensity(emotion_analysis, emotion_vector)
            emotional_confidence = emotion_analysis.confidence
            
            # Calculate valence and arousal
            valence = self._calculate_valence(emotion_analysis, emotion_vector)
            arousal = self._calculate_arousal(emotion_analysis, emotion_vector)
            
            # Calculate stability and volatility
            stability = self._calculate_stability(emotion_vector, user_history)
            volatility = self._calculate_volatility(emotion_vector, previous_emotions)
            
            # Calculate baseline deviation
            baseline_deviation = self._calculate_baseline_deviation(emotion_vector, user_history)
            
            # Detect emotional regulation attempts
            regulation_attempts = self._detect_regulation_attempts(
                emotion_analysis, emotion_vector, user_history
            )
            
            return EmotionalFeatures(
                emotion_vector=emotion_vector,
                dominant_emotion_idx=dominant_emotion_idx,
                emotional_intensity=emotional_intensity,
                emotional_confidence=emotional_confidence,
                valence=valence,
                arousal=arousal,
                stability=stability,
                volatility=volatility,
                baseline_deviation=baseline_deviation,
                regulation_attempts=regulation_attempts
            )
            
        except Exception as e:
            logger.error(f"Error extracting emotional features: {e}")
            return
    
    def _extract_emotion_vector(self, emotion_analysis) -> np.ndarray:
        """Extract 8D emotion vector from emotion analysis"""
        try:
            if hasattr(emotion_analysis, 'emotions'):
                emotions = emotion_analysis.emotions
                return np.array([
                    emotions.joy,
                    emotions.sadness,
                    emotions.anger,
                    emotions.fear,
                    emotions.surprise,
                    emotions.disgust,
                    emotions.anticipation,
                    emotions.trust
                ], dtype=np.float32)
            else:
                logger.warning("Emotion analysis missing emotions attribute")
                return np.zeros(8, dtype=np.float32)
        except Exception as e:
            logger.error(f"Error extracting emotion vector: {e}")
            return np.zeros(8, dtype=np.float32)
    
    def _get_dominant_emotion_idx(self, emotion_analysis) -> int:
        """Get index of dominant emotion"""
        try:
            dominant_emotion = emotion_analysis.dominant_emotion
            if dominant_emotion in self.emotion_names:
                return self.emotion_names.index(dominant_emotion)
            else:
                return 0  # Default to joy
        except:
            return 0
    
    def _calculate_intensity(self, emotion_analysis, emotion_vector: np.ndarray) -> float:
        """Calculate overall emotional intensity"""

        # Use model's intensity if available, otherwise calculate from vector
        if hasattr(emotion_analysis, 'intensity'):
            return min(max(emotion_analysis.intensity, 0.0), 1.0)
        else:
        # Calculate as maximum emotion score
            return float(np.max(emotion_vector))
    
    def _calculate_valence(self, emotion_analysis, emotion_vector: np.ndarray) -> float:
        """Calculate emotional valence (positive/negative)"""

        weighted_valence = 0.0
        total_weight = 0.0
            
        for i, emotion_name in enumerate(self.emotion_names):
            emotion_score = emotion_vector[i]
            valence_value = self.emotion_valence[emotion_name]
            weighted_valence += emotion_score * valence_value
            total_weight += emotion_score
            
        if total_weight > 0:
            return weighted_valence / total_weight
    
    def _calculate_arousal(self, emotion_analysis, emotion_vector: np.ndarray) -> float:
        """Calculate emotional arousal (activation level)"""
        try:
            weighted_arousal = 0.0
            total_weight = 0.0
            
            for i, emotion_name in enumerate(self.emotion_names):
                emotion_score = emotion_vector[i]
                arousal_value = self.emotion_arousal[emotion_name]
                weighted_arousal += emotion_score * arousal_value
                total_weight += emotion_score
            
            if total_weight > 0:
                return weighted_arousal / total_weight
            else:
                return 0.5
        except:
            return
    
    def _calculate_stability(
        self, 
        emotion_vector: np.ndarray, 
        user_history: Optional[UserHistoryContext]
    ) -> float:
        """Calculate emotional stability based on user baseline"""
        try:
            if not user_history or not user_history.emotional_baseline:
                # For new users, calculate stability as inverse of emotion spread
                emotion_variance = np.var(emotion_vector)
                return max(0.0, 1.0 - emotion_variance * 2)
            
            # Calculate stability as consistency with emotional baseline
            baseline_vector = np.array([
                user_history.emotional_baseline.get(emotion, 0.3)
                for emotion in self.emotion_names
            ])
            
            # Cosine similarity between current and baseline emotions
            dot_product = np.dot(emotion_vector, baseline_vector)
            norm_current = np.linalg.norm(emotion_vector)
            norm_baseline = np.linalg.norm(baseline_vector)
            
            if norm_current > 0 and norm_baseline > 0:
                similarity = dot_product / (norm_current * norm_baseline)
                return max(0.0, min(similarity, 1.0))
            else:
                return
        except Exception as e:
            logger.error(f"Error: {e}")
            return
    
    def _calculate_volatility(
        self, 
        emotion_vector: np.ndarray, 
        previous_emotions: Optional[List[Dict]]
    ) -> float:
        """Calculate emotional volatility from recent history"""
        try:
            if not previous_emotions or len(previous_emotions) < 2:
                return 0.0  # No volatility without history
            
            # Calculate changes between recent emotion states
            recent_vectors = []
            for emotion_data in previous_emotions[-5:]:  # Last 5 entries max
                if 'emotion_vector' in emotion_data:
                    recent_vectors.append(np.array(emotion_data['emotion_vector']))
                elif 'emotions' in emotion_data:
                    # Reconstruct vector from emotion dict
                    emotions = emotion_data['emotions']
                    vector = np.array([
                        emotions.get(emotion, 0.0) for emotion in self.emotion_names
                    ])
                    recent_vectors.append(vector)
            
            if len(recent_vectors) < 2:
                return 0.0
            
            # Calculate average change between consecutive states
            changes = []
            for i in range(1, len(recent_vectors)):
                change = np.linalg.norm(recent_vectors[i] - recent_vectors[i-1])
                changes.append(change)
            
            avg_change = np.mean(changes)
            # Normalize to 0-1 range (typical changes are 0-2)
            return min(avg_change / 2.0, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating volatility: {e}")
            return 0.0
    
    def _calculate_baseline_deviation(
        self, 
        emotion_vector: np.ndarray, 
        user_history: Optional[UserHistoryContext]
    ) -> float:
        """Calculate deviation from user's emotional baseline"""
        try:
            if not user_history or not user_history.emotional_baseline:
                return 0.5  # Neutral for new users
            
            baseline_vector = np.array([
                user_history.emotional_baseline.get(emotion, 0.3)
                for emotion in self.emotion_names
            ])
            
            # Calculate Euclidean distance
            deviation = np.linalg.norm(emotion_vector - baseline_vector)
            # Normalize (max deviation between opposite corners is ~2.83)
            normalized_deviation = min(deviation / 2.83, 1.0)
            
            return normalized_deviation
            
        except:
            return 0.5
    
    def _detect_regulation_attempts(
        self, 
        emotion_analysis, 
        emotion_vector: np.ndarray,
        user_history: Optional[UserHistoryContext]
    ) -> float:
        """Detect signs of emotional regulation attempts"""
        try:
            regulation_score = 0.0
            
            # Check for mixed emotions (sign of regulation)
            emotion_spread = np.std(emotion_vector)
            if emotion_spread > 0.3:  # High spread indicates mixed emotions
                regulation_score += 0.3
            
            # Check for moderate intensity (sign of control)
            if hasattr(emotion_analysis, 'intensity'):
                intensity = emotion_analysis.intensity
                if 0.3 <= intensity <= 0.7:  # Moderate intensity
                    regulation_score += 0.2
            
            # Check for presence of "trust" emotion (often indicates coping)
            trust_score = emotion_vector[self.emotion_names.index('trust')]
            if trust_score > 0.4:
                regulation_score += 0.2
            
            # Check for balanced positive/negative emotions
            positive_emotions = emotion_vector[[0, 6, 7]]  # joy, anticipation, trust
            negative_emotions = emotion_vector[[1, 2, 3, 5]]  # sadness, anger, fear, disgust
            
            pos_total = np.sum(positive_emotions)
            neg_total = np.sum(negative_emotions)
            
            if pos_total > 0 and neg_total > 0:
                balance = min(pos_total, neg_total) / max(pos_total, neg_total)
                regulation_score += balance * 0.3
            
            return min(regulation_score, 1.0)
            
        except:
            return 0.0
    
    # def _get_default_features(self) -> EmotionalFeatures:
    #     """Return default emotional features for error cases"""
    #     return EmotionalFeatures(
    #         emotion_vector=np.array([0.3, 0.2, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1], dtype=np.float32),
    #         dominant_emotion_idx=0,
    #         emotional_intensity=0.3,
    #         emotional_confidence=0.5,
    #         valence=0.0,
    #         arousal=0.5,
    #         stability=0.5,
    #         volatility=0.0,
    #         baseline_deviation=0.5,
    #         regulation_attempts=0.0
    #     )
    
    def get_feature_names(self) -> List[str]:
        """Get names of all emotional features for debugging"""
        return [
            'emotional_intensity', 'emotional_confidence', 'valence', 'arousal',
            'stability', 'volatility', 'baseline_deviation', 'regulation_attempts',
            'dominant_joy', 'dominant_sadness', 'dominant_anger', 'dominant_fear',
            'dominant_surprise', 'dominant_disgust', 'dominant_anticipation', 'dominant_trust'
        ]
    
    def analyze_emotion_pattern(
        self, 
        emotion_analysis, 
        user_history: Optional[UserHistoryContext] = None
    ) -> Dict[str, Any]:
        """
        Analyze emotional patterns for insights
        
        Returns:
            Dictionary with pattern analysis results
        """
        try:
            features = self.extract(emotion_analysis, user_history)
            
            # Determine emotional state category
            if features.valence > 0.3 and features.arousal > 0.5:
                state_category = "energized_positive"
            elif features.valence > 0.3 and features.arousal <= 0.5:
                state_category = "calm_positive"
            elif features.valence <= -0.3 and features.arousal > 0.5:
                state_category = "energized_negative"
            elif features.valence <= -0.3 and features.arousal <= 0.5:
                state_category = "calm_negative"
            else:
                state_category = "neutral"
            
            # Assess emotional regulation
            if features.regulation_attempts > 0.6:
                regulation_status = "high_regulation"
            elif features.regulation_attempts > 0.3:
                regulation_status = "moderate_regulation"
            else:
                regulation_status = "natural_expression"
            
            return {
                'state_category': state_category,
                'regulation_status': regulation_status,
                'intensity_level': 'high' if features.emotional_intensity > 0.7 else 
                                 'moderate' if features.emotional_intensity > 0.4 else 'low',
                'stability_level': 'stable' if features.stability > 0.7 else
                                 'moderate' if features.stability > 0.4 else 'unstable',
                'volatility_level': 'high' if features.volatility > 0.6 else
                                  'moderate' if features.volatility > 0.3 else 'low',
                'baseline_match': 'close' if features.baseline_deviation < 0.3 else
                                'moderate' if features.baseline_deviation < 0.6 else 'distant'
            }
            
        except Exception as e:
            logger.error(f"Error analyzing emotion pattern: {e}")
            return {
                'state_category': 'neutral',
                'regulation_status': 'unknown',
                'intensity_level': 'moderate',
                'stability_level': 'moderate',
                'volatility_level': 'low',
                'baseline_match': 'moderate'
            }
