"""
Reward calculation system for RL training based on user feedback
Converts various types of user interactions into training rewards
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime, timedelta
from enum import Enum

from comp2.data import UserFeedback, RewardComponents, EmotionAnalysis, EmotionScores

logger = logging.getLogger(__name__)


class FeedbackType(Enum):
    """Types of user feedback for reward calculation"""
    CORRECTION = "correction"      # User corrected emotion labels
    CONFIRMATION = "confirmation"  # User confirmed emotions were accurate
    ENGAGEMENT = "engagement"      # User continued conversation/asked follow-ups
    BEHAVIORAL = "behavioral"      # Session patterns, return visits, etc.


class RewardCalculator:
    """
    Calculates RL training rewards based on user feedback and behavior
    Combines explicit feedback with implicit engagement signals
    """
    
    def __init__(
        self,
        explicit_weight: float = 0.6,
        engagement_weight: float = 0.3, 
        behavioral_weight: float = 0.1,
        correction_penalty: float = 0.8,
        confirmation_bonus: float = 1.2,
        time_decay_hours: float = 24.0
    ):
        """
        Initialize reward calculator
        
        Args:
            explicit_weight: Weight for direct user corrections/confirmations
            engagement_weight: Weight for conversation engagement signals  
            behavioral_weight: Weight for session behavior patterns
            correction_penalty: Penalty multiplier for incorrect predictions
            confirmation_bonus: Bonus multiplier for correct predictions
            time_decay_hours: Hours over which feedback relevance decays
        """
        self.explicit_weight = explicit_weight
        self.engagement_weight = engagement_weight
        self.behavioral_weight = behavioral_weight
        self.correction_penalty = correction_penalty
        self.confirmation_bonus = confirmation_bonus
        self.time_decay_hours = time_decay_hours
        
        # Validate weights sum to 1.0
        total_weight = explicit_weight + engagement_weight + behavioral_weight
        if abs(total_weight - 1.0) > 0.01:
            logger.warning(f"Reward weights sum to {total_weight:.3f}, not 1.0")
    
    def calculate_reward(self, feedback: UserFeedback) -> RewardComponents:
        """
        Main reward calculation method
        
        Args:
            feedback: User feedback data
            
        Returns:
            Breakdown of reward components
        """
        try:
            # Calculate individual reward components
            explicit_reward = self._calculate_explicit_reward(feedback)
            engagement_reward = self._calculate_engagement_reward(feedback)  
            behavioral_reward = self._calculate_behavioral_reward(feedback)
            
            # Apply time decay
            time_factor = self._calculate_time_decay(feedback.timestamp)
            
            # Weight and combine rewards
            total_reward = (
                self.explicit_weight * explicit_reward * time_factor +
                self.engagement_weight * engagement_reward * time_factor +
                self.behavioral_weight * behavioral_reward * time_factor
            )
            
            # Calculate confidence in reward signal
            confidence = self._calculate_reward_confidence(feedback, explicit_reward)
            
            return RewardComponents(
                explicit_feedback=explicit_reward,
                engagement_signal=engagement_reward,
                behavioral_signal=behavioral_reward,
                total_reward=total_reward,
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"Error calculating reward: {e}")
            # Return neutral reward on error
            return RewardComponents(
                explicit_feedback=0.0,
                engagement_signal=0.0,
                behavioral_signal=0.0,
                total_reward=0.0,
                confidence=0.0
            )
    
    def _calculate_explicit_reward(self, feedback: UserFeedback) -> float:
        """
        Calculate reward from direct user corrections/confirmations
        
        Args:
            feedback: User feedback data
            
        Returns:
            Explicit feedback reward score
        """
        if feedback.feedback_type == FeedbackType.CORRECTION.value:
            return self._calculate_correction_reward(feedback)
        elif feedback.feedback_type == FeedbackType.CONFIRMATION.value:
            return self._calculate_confirmation_reward(feedback)
        else:
            return 0.0
    
    def _calculate_correction_reward(self, feedback: UserFeedback) -> float:
        """
        Calculate penalty for incorrect emotion predictions
        
        Args:
            feedback: Correction feedback data
            
        Returns:
            Negative reward for incorrect predictions
        """
        feedback_data = feedback.feedback_data
        
        if not feedback.emotion_context:
            return -5.0  # Default penalty for missing context
        
        # Get original predictions and user corrections
        original_emotions = feedback.emotion_context.emotions
        corrected_emotions = feedback_data.get('corrected_emotions', {})
        
        if not corrected_emotions:
            return -3.0  # Penalty for correction without specifics
        
        # Calculate prediction error
        total_error = 0.0
        emotion_count = 0
        
        for emotion, corrected_score in corrected_emotions.items():
            if hasattr(original_emotions, emotion):
                original_score = getattr(original_emotions, emotion)
                error = abs(original_score - corrected_score)
                total_error += error
                emotion_count += 1
        
        if emotion_count == 0:
            return -2.0
        
        # Convert error to penalty (higher error = more negative reward)
        avg_error = total_error / emotion_count
        penalty = -10.0 * avg_error * self.correction_penalty
        
        # Cap penalty to reasonable range
        return max(penalty, -10.0)
    
    def _calculate_confirmation_reward(self, feedback: UserFeedback) -> float:
        """
        Calculate bonus for accurate emotion predictions
        
        Args:
            feedback: Confirmation feedback data
            
        Returns:
            Positive reward for accurate predictions
        """
        feedback_data = feedback.feedback_data
        
        # Explicit confirmation
        if feedback_data.get('explicit_confirmation', False):
            confidence = feedback_data.get('confidence', 0.8)
            return 8.0 * confidence * self.confirmation_bonus
        
        # Implicit confirmation (no corrections provided)
        if feedback.emotion_context:
            # Bonus based on prediction confidence
            prediction_confidence = feedback.emotion_context.confidence
            return 5.0 * prediction_confidence * self.confirmation_bonus
        
        return 2.0  # Default small bonus
    
    def _calculate_engagement_reward(self, feedback: UserFeedback) -> float:
        """
        Calculate reward from conversation engagement signals
        
        Args:
            feedback: Engagement feedback data
            
        Returns:
            Engagement-based reward score
        """
        if feedback.feedback_type != FeedbackType.ENGAGEMENT.value:
            return 0.0
        
        feedback_data = feedback.feedback_data
        reward = 0.0
        
        # Continued conversation
        if feedback_data.get('continued_conversation', False):
            conversation_length = feedback_data.get('conversation_turns', 1)
            reward += min(3.0, 0.5 * conversation_length)
        
        # Follow-up questions  
        if feedback_data.get('asked_followup', False):
            followup_quality = feedback_data.get('followup_quality', 0.7)
            reward += 2.0 * followup_quality
        
        # Emotional response
        emotional_response = feedback_data.get('emotional_response', 'neutral')
        if emotional_response in ['positive', 'engaged', 'curious']:
            reward += 1.5
        elif emotional_response in ['negative', 'frustrated']:
            reward -= 2.0
        
        # Session duration
        session_duration_minutes = feedback_data.get('session_duration_minutes', 0)
        if session_duration_minutes > 0:
            # Reward for longer engagement, with diminishing returns
            duration_reward = min(2.0, np.log(1 + session_duration_minutes / 5.0))
            reward += duration_reward
        
        return reward
    
    def _calculate_behavioral_reward(self, feedback: UserFeedback) -> float:
        """
        Calculate reward from behavioral patterns and usage
        
        Args:
            feedback: Behavioral feedback data
            
        Returns:
            Behavior-based reward score
        """
        if feedback.feedback_type != FeedbackType.BEHAVIORAL.value:
            return 0.0
        
        feedback_data = feedback.feedback_data
        reward = 0.0
        
        # Return visits (user came back)
        if feedback_data.get('return_visit', False):
            days_since_last = feedback_data.get('days_since_last_visit', 1)
            # Reward return visits, higher reward for coming back sooner
            if days_since_last <= 1:
                reward += 2.0
            elif days_since_last <= 7:
                reward += 1.5
            else:
                reward += 1.0
        
        # Session completion
        session_completed = feedback_data.get('session_completed', False)
        if session_completed:
            reward += 1.0
        else:
            # Penalty for early exit
            completion_percentage = feedback_data.get('completion_percentage', 0.0)
            if completion_percentage < 0.3:
                reward -= 1.0
        
        # Usage frequency
        weekly_sessions = feedback_data.get('weekly_sessions', 0)
        if weekly_sessions >= 5:
            reward += 1.5  # High engagement
        elif weekly_sessions >= 3:
            reward += 1.0  # Good engagement
        elif weekly_sessions == 1:
            reward += 0.5  # Some engagement
        # No penalty for low usage - user choice
        
        # Feature usage
        features_used = feedback_data.get('features_used', [])
        if len(features_used) > 1:
            reward += 0.5 * len(features_used)  # Reward feature exploration
        
        return reward
    
    def _calculate_time_decay(self, feedback_timestamp: datetime) -> float:
        """
        Calculate time decay factor for feedback relevance
        
        Args:
            feedback_timestamp: When feedback was provided
            
        Returns:
            Decay factor between 0 and 1
        """
        try:
            # Calculate hours since feedback
            time_diff = datetime.now() - feedback_timestamp
            hours_elapsed = time_diff.total_seconds() / 3600.0
            
            # Exponential decay
            decay_factor = np.exp(-hours_elapsed / self.time_decay_hours)
            
            # Ensure minimum relevance
            return max(decay_factor, 0.1)
            
        except Exception:
            # Default to no decay if timestamp issues
            return 1.0
    
    def _calculate_reward_confidence(
        self, 
        feedback: UserFeedback, 
        explicit_reward: float
    ) -> float:
        """
        Calculate confidence in the reward signal
        
        Args:
            feedback: User feedback data
            explicit_reward: Explicit reward component
            
        Returns:
            Confidence score 0-1
        """
        confidence = 0.5  # Base confidence
        
        # Higher confidence for explicit feedback
        if feedback.feedback_type in [FeedbackType.CORRECTION.value, FeedbackType.CONFIRMATION.value]:
            confidence = 0.9
        
        # Adjust based on feedback quality
        feedback_data = feedback.feedback_data
        
        if 'confidence' in feedback_data:
            user_confidence = feedback_data['confidence']
            confidence = 0.7 * confidence + 0.3 * user_confidence
        
        # Lower confidence for ambiguous signals
        if abs(explicit_reward) < 0.5:
            confidence *= 0.8
        
        # Higher confidence for strong signals
        if abs(explicit_reward) > 5.0:
            confidence = min(1.0, confidence * 1.2)
        
        return np.clip(confidence, 0.0, 1.0)
    
    def batch_calculate_rewards(
        self, 
        feedback_list: List[UserFeedback]
    ) -> List[RewardComponents]:
        """
        Calculate rewards for batch of feedback
        
        Args:
            feedback_list: List of user feedback
            
        Returns:
            List of reward components
        """
        return [self.calculate_reward(fb) for fb in feedback_list]
    
    def get_reward_statistics(
        self, 
        reward_history: List[RewardComponents]
    ) -> Dict[str, float]:
        """
        Calculate statistics from reward history
        
        Args:
            reward_history: List of historical rewards
            
        Returns:
            Dictionary with reward statistics
        """
        if not reward_history:
            return {}
        
        total_rewards = [r.total_reward for r in reward_history]
        explicit_rewards = [r.explicit_feedback for r in reward_history]
        engagement_rewards = [r.engagement_signal for r in reward_history]
        behavioral_rewards = [r.behavioral_signal for r in reward_history]
        confidences = [r.confidence for r in reward_history]
        
        return {
            'mean_total_reward': np.mean(total_rewards),
            'std_total_reward': np.std(total_rewards),
            'mean_explicit_reward': np.mean(explicit_rewards),
            'mean_engagement_reward': np.mean(engagement_rewards),
            'mean_behavioral_reward': np.mean(behavioral_rewards),
            'mean_confidence': np.mean(confidences),
            'reward_trend': self._calculate_trend(total_rewards),
            'positive_feedback_ratio': sum(1 for r in total_rewards if r > 0) / len(total_rewards)
        }
    
    def _calculate_trend(self, values: List[float]) -> float:
        """
        Calculate trend in reward values (simple linear regression slope)
        
        Args:
            values: List of reward values over time
            
        Returns:
            Trend slope (positive = improving, negative = declining)
        """
        if len(values) < 2:
            return 0.0
        
        n = len(values)
        x = np.arange(n)
        y = np.array(values)
        
        # Simple linear regression
        slope = np.sum((x - x.mean()) * (y - y.mean())) / np.sum((x - x.mean()) ** 2)
        
        return slope
    
    def update_weights(
        self, 
        explicit_weight: float, 
        engagement_weight: float, 
        behavioral_weight: float
    ):
        """
        Update reward calculation weights
        
        Args:
            explicit_weight: New explicit feedback weight
            engagement_weight: New engagement signal weight  
            behavioral_weight: New behavioral signal weight
        """
        total = explicit_weight + engagement_weight + behavioral_weight
        
        if abs(total - 1.0) > 0.01:
            logger.warning(f"New weights sum to {total:.3f}, normalizing to 1.0")
            explicit_weight /= total
            engagement_weight /= total
            behavioral_weight /= total
        
        self.explicit_weight = explicit_weight
        self.engagement_weight = engagement_weight
        self.behavioral_weight = behavioral_weight
        
        logger.info(f"Updated reward weights: explicit={explicit_weight:.2f}, "
                   f"engagement={engagement_weight:.2f}, behavioral={behavioral_weight:.2f}")


class RewardSignalGenerator:
    """
    Utility class for generating synthetic reward signals for testing
    """
    
    def __init__(self, calculator: RewardCalculator):
        """
        Initialize reward signal generator
        
        Args:
            calculator: RewardCalculator instance to use
        """
        self.calculator = calculator
    
    def generate_correction_feedback(
        self, 
        user_id: str,
        original_emotions: EmotionScores,
        error_magnitude: float = 0.3
    ) -> UserFeedback:
        """
        Generate synthetic correction feedback for testing
        
        Args:
            user_id: User identifier
            original_emotions: Original emotion predictions
            error_magnitude: Size of corrections to generate
            
        Returns:
            Synthetic correction feedback
        """
        # Generate corrected emotions with some error
        original_dict = original_emotions.dict()
        corrected_dict = {}
        
        for emotion, score in original_dict.items():
            # Add random correction
            correction = np.random.normal(0, error_magnitude)
            corrected_score = np.clip(score + correction, 0.0, 1.0)
            corrected_dict[emotion] = corrected_score
        
        return UserFeedback(
            user_id=user_id,
            journal_entry_id=f"test_entry_{np.random.randint(1000)}",
            feedback_type=FeedbackType.CORRECTION.value,
            feedback_data={
                'corrected_emotions': corrected_dict,
                'confidence': 0.8
            },
            emotion_context=EmotionAnalysis(
                emotions=original_emotions,
                dominant_emotion=original_emotions.dominant_emotion(),
                intensity=0.6,
                confidence=0.7
            )
        )