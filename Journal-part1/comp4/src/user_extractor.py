"""
User Feature Extractor for Component 4
Extracts user-specific behavioral patterns, preferences, and personal context
"""

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

from comp4.data.schemas import UserFeatures, UserHistoryContext

logger = logging.getLogger(__name__)

class UserFeatureExtractor:
    """
    Extracts user-specific features for personalized analysis
    Focuses on behavioral patterns, preferences, and personal context
    """
    
    def __init__(self):
        """Initialize user feature extractor"""
        self.name = "UserFeatureExtractor"
        self.version = "4.0"
        
        # Keywords for different life focuses
        self.relationship_keywords = {
            'family', 'friend', 'partner', 'relationship', 'love', 'together', 
            'social', 'connect', 'bond', 'support', 'care', 'trust'
        }
        
        self.goal_keywords = {
            'goal', 'achieve', 'success', 'accomplish', 'plan', 'target',
            'objective', 'ambition', 'progress', 'improve', 'grow', 'develop'
        }
        
        self.introspection_keywords = {
            'feel', 'think', 'realize', 'understand', 'reflect', 'consider',
            'aware', 'insight', 'learn', 'discover', 'notice', 'recognize'
        }
        
        self.growth_keywords = {
            'change', 'improve', 'better', 'growth', 'develop', 'progress',
            'evolve', 'transform', 'advance', 'mature', 'strengthen', 'overcome'
        }
    
    def extract(
        self,
        user_history: Optional[UserHistoryContext] = None,
        current_entry_data: Optional[Dict] = None,
        semantic_analysis = None,
        emotion_analysis = None,
        raw_text: str = "",
        entry_timestamp: Optional[datetime] = None
    ) -> UserFeatures:
        """
        Extract user-specific behavioral and pattern features
        
        Args:
            user_history: User's historical context and patterns
            current_entry_data: Current entry context
            semantic_analysis: Semantic analysis for content analysis
            emotion_analysis: Emotion analysis for emotional patterns
            raw_text: Original text for linguistic analysis
            entry_timestamp: When the entry was written
            
        Returns:
            UserFeatures object with 15-dimensional feature vector
        """
        try:
            # Calculate writing consistency
            writing_consistency = self._calculate_writing_consistency(user_history, entry_timestamp)
            
            # Calculate session patterns
            session_patterns = self._calculate_session_patterns(user_history, current_entry_data)
            
            # Calculate topic preference match
            topic_preference_match = self._calculate_topic_preference_match(
                user_history, semantic_analysis
            )
            
            # Calculate emotional baseline match
            emotional_baseline_match = self._calculate_emotional_baseline_match(
                user_history, emotion_analysis
            )
            
            # Calculate behavioral anomaly
            behavioral_anomaly = self._calculate_behavioral_anomaly(
                user_history, current_entry_data, entry_timestamp
            )
            
            # Calculate engagement level
            engagement_level = self._calculate_engagement_level(
                user_history, current_entry_data, raw_text
            )
            
            # Calculate personal growth indicators
            personal_growth = self._calculate_personal_growth(raw_text, user_history)
            
            # Calculate relationship focus
            relationship_focus = self._calculate_relationship_focus(raw_text, semantic_analysis)
            
            # Calculate goal orientation
            goal_orientation = self._calculate_goal_orientation(raw_text, semantic_analysis)
            
            # Calculate introspection level
            introspection_level = self._calculate_introspection_level(raw_text)
            
            return UserFeatures(
                writing_consistency=writing_consistency,
                session_patterns=session_patterns,
                topic_preference_match=topic_preference_match,
                emotional_baseline_match=emotional_baseline_match,
                behavioral_anomaly=behavioral_anomaly,
                engagement_level=engagement_level,
                personal_growth=personal_growth,
                relationship_focus=relationship_focus,
                goal_orientation=goal_orientation,
                introspection_level=introspection_level
            )
            
        except Exception as e:
            logger.error(f"Error extracting user features: {e}")
            return
    
    def _calculate_writing_consistency(
        self, 
        user_history: Optional[UserHistoryContext],
        entry_timestamp: Optional[datetime]
    ) -> float:
        """Calculate how consistent user's writing patterns are"""
        try:
            if not user_history or user_history.total_entries < 3:
                return 0.5  # Neutral for new users
            
            consistency_score = 0.5  # Base score
            
            # Time consistency
            if (user_history.preferred_writing_times and 
                entry_timestamp and 
                entry_timestamp.hour in user_history.preferred_writing_times):
                consistency_score += 0.2
            
            # Frequency consistency
            if hasattr(user_history, 'writing_frequency_baseline'):
                if user_history.writing_frequency_baseline > 0.1:  # Regular writer
                    consistency_score += 0.2
            
            # Topic consistency
            if hasattr(user_history, 'topic_consistency'):
                consistency_score += user_history.topic_consistency * 0.1
            
            return min(max(consistency_score, 0.0), 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating writing consistency: {e}")
            return 0.5
    
    def _calculate_session_patterns(
        self, 
        user_history: Optional[UserHistoryContext],
        current_entry_data: Optional[Dict]
    ) -> float:
        """Calculate session behavior patterns"""
        try:
            if not user_history:
                return 0.5
            
            pattern_score = 0.5  # Base score
            
            # Average session duration
            if user_history.avg_session_duration > 0:
                # Longer sessions indicate more thoughtful writing
                duration_score = min(user_history.avg_session_duration / 300, 1.0)  # 5 min max
                pattern_score += duration_score * 0.2
            
            # Entry length consistency
            if current_entry_data and 'text_length' in current_entry_data:
                current_length = current_entry_data['text_length']
                if hasattr(user_history, 'avg_entry_length'):
                    avg_length = user_history.avg_entry_length
                    if avg_length > 0:
                        length_consistency = 1.0 - abs(current_length - avg_length) / max(avg_length, current_length)
                        pattern_score += length_consistency * 0.3
            
            return min(max(pattern_score, 0.0), 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating session patterns: {e}")
            return 0.5
    
    def _calculate_topic_preference_match(
        self, 
        user_history: Optional[UserHistoryContext],
        semantic_analysis
    ) -> float:
        """Calculate match to user's preferred topics"""
        try:
            if not user_history or not user_history.topic_preferences:
                return 0.5  # Neutral for new users
            
            if not semantic_analysis or not hasattr(semantic_analysis, 'detected_topics'):
                return 0.3  # Low match if no topics detected
            
            current_topics = set(topic.lower() for topic in semantic_analysis.detected_topics)
            preferred_topics = set(topic.lower() for topic in user_history.topic_preferences)
            
            if not current_topics or not preferred_topics:
                return 0.3
            
            # Calculate overlap
            intersection = len(current_topics.intersection(preferred_topics))
            union = len(current_topics.union(preferred_topics))
            
            if union == 0:
                return 0.5
            
            # Jaccard similarity
            similarity = intersection / union
            return min(max(similarity, 0.0), 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating topic preference match: {e}")
            return 0.5
    
    def _calculate_emotional_baseline_match(
        self, 
        user_history: Optional[UserHistoryContext],
        emotion_analysis
    ) -> float:
        """Calculate match to user's emotional baseline"""
        try:
            if not user_history or not user_history.emotional_baseline:
                return 0.5  # Neutral for new users
            
            if not emotion_analysis or not hasattr(emotion_analysis, 'emotions'):
                return 0.5
            
            # Extract current emotions
            current_emotions = {
                'joy': emotion_analysis.emotions.joy,
                'sadness': emotion_analysis.emotions.sadness,
                'anger': emotion_analysis.emotions.anger,
                'fear': emotion_analysis.emotions.fear,
                'surprise': emotion_analysis.emotions.surprise,
                'disgust': emotion_analysis.emotions.disgust,
                'anticipation': emotion_analysis.emotions.anticipation,
                'trust': emotion_analysis.emotions.trust
            }
            
            # Calculate similarity to baseline
            similarities = []
            for emotion, baseline_value in user_history.emotional_baseline.items():
                if emotion in current_emotions:
                    current_value = current_emotions[emotion]
                    # Calculate absolute difference and convert to similarity
                    diff = abs(current_value - baseline_value)
                    similarity = max(0, 1.0 - diff)
                    similarities.append(similarity)
            
            if similarities:
                return np.mean(similarities)
            else:
                return 0.5
                
        except Exception as e:
            logger.error(f"Error calculating emotional baseline match: {e}")
            return 0.5
    
    def _calculate_behavioral_anomaly(
        self, 
        user_history: Optional[UserHistoryContext],
        current_entry_data: Optional[Dict],
        entry_timestamp: Optional[datetime]
    ) -> float:
        """Calculate how anomalous this entry is for the user"""
        try:
            if not user_history or user_history.total_entries < 5:
                return 0.0  # No anomaly detection for new users
            
            anomaly_score = 0.0
            
            # Time anomaly
            if entry_timestamp and user_history.preferred_writing_times:
                hour = entry_timestamp.hour
                if hour not in user_history.preferred_writing_times:
                    # Calculate distance to nearest preferred time
                    distances = [min(abs(hour - pref), 24 - abs(hour - pref)) 
                               for pref in user_history.preferred_writing_times]
                    min_distance = min(distances)
                    anomaly_score += min(min_distance / 12.0, 0.3)
            
            # Length anomaly
            if current_entry_data and 'text_length' in current_entry_data:
                current_length = current_entry_data['text_length']
                if hasattr(user_history, 'avg_entry_length') and user_history.avg_entry_length > 0:
                    length_ratio = current_length / user_history.avg_entry_length
                    if length_ratio > 3 or length_ratio < 0.3:  # Very long or short
                        anomaly_score += 0.2
            
            # Emotional volatility anomaly
            if hasattr(user_history, 'emotional_volatility'):
                if user_history.emotional_volatility < 0.2:  # Usually stable user
                    # Check if current entry shows high emotion
                    if current_entry_data and 'emotional_intensity' in current_entry_data:
                        if current_entry_data['emotional_intensity'] > 0.8:
                            anomaly_score += 0.3
            
            # Topic anomaly (covered in topic preference match, inverse relationship)
            
            return min(anomaly_score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating behavioral anomaly: {e}")
            return 0.0
    
    def _calculate_engagement_level(
        self, 
        user_history: Optional[UserHistoryContext],
        current_entry_data: Optional[Dict],
        raw_text: str
    ) -> float:
        """Calculate user's engagement level with the platform"""
        try:
            engagement_score = 0.5  # Base score
            
            # Text length indicates engagement
            text_length = len(raw_text.split()) if raw_text else 0
            if text_length > 100:
                engagement_score += 0.2
            elif text_length > 50:
                engagement_score += 0.1
            
            # Frequency indicates engagement
            if user_history and user_history.writing_frequency_baseline > 0.5:  # Regular writer
                engagement_score += 0.2
            
            # Detail and specificity indicate engagement
            if raw_text:
                # Check for specific details (names, numbers, dates)
                import re
                names = len(re.findall(r'\b[A-Z][a-z]+\b', raw_text))  # Capitalized words
                numbers = len(re.findall(r'\d+', raw_text))
                dates = len(re.findall(r'\b(today|tomorrow|yesterday|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b', raw_text.lower()))
                
                detail_score = min((names + numbers + dates) / 10.0, 0.2)
                engagement_score += detail_score
            
            # Session duration (if available)
            if user_history and user_history.avg_session_duration > 180:  # > 3 minutes
                engagement_score += 0.1
            
            return min(max(engagement_score, 0.0), 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating engagement level: {e}")
            return 0.5
    
    def _calculate_personal_growth(self, raw_text: str, user_history: Optional[UserHistoryContext]) -> float:
        """Calculate indicators of personal growth and development"""
        try:
            if not raw_text:
                return 0.0
            
            growth_score = 0.0
            text_lower = raw_text.lower()
            
            # Growth keywords
            growth_matches = sum(1 for keyword in self.growth_keywords if keyword in text_lower)
            growth_score += min(growth_matches * 0.1, 0.4)
            
            # Learning and insight language
            learning_patterns = [
                r'\blearned?\b', r'\brealized?\b', r'\bunderstood?\b', r'\bdiscovered?\b',
                r'\binsight\b', r'\bepiphany\b', r'\bbreakthrough\b'
            ]
            
            import re
            for pattern in learning_patterns:
                matches = len(re.findall(pattern, text_lower))
                growth_score += min(matches * 0.08, 0.2)
            
            # Past vs present comparisons (growth indicators)
            comparison_patterns = [
                r'\bused to\b', r'\bbefore.*now\b', r'\bno longer\b', r'\bchanged\b'
            ]
            
            for pattern in comparison_patterns:
                matches = len(re.findall(pattern, text_lower))
                growth_score += min(matches * 0.1, 0.2)
            
            # Self-awareness indicators
            awareness_patterns = [
                r'\bi am\b', r'\bi feel\b', r'\bi think\b', r'\bi believe\b',
                r'\bi realize\b', r'\bi understand\b'
            ]
            
            awareness_count = sum(len(re.findall(pattern, text_lower)) for pattern in awareness_patterns)
            growth_score += min(awareness_count * 0.02, 0.2)
            
            return min(growth_score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating personal growth: {e}")
            return 0.0
    
    def _calculate_relationship_focus(self, raw_text: str, semantic_analysis) -> float:
        """Calculate focus on relationships and social connections"""
        try:
            if not raw_text:
                return 0.0
            
            relationship_score = 0.0
            text_lower = raw_text.lower()
            
            # Relationship keywords
            relationship_matches = sum(1 for keyword in self.relationship_keywords if keyword in text_lower)
            relationship_score += min(relationship_matches * 0.08, 0.4)
            
            # People mentions from semantic analysis
            if semantic_analysis and hasattr(semantic_analysis, 'people'):
                people_count = len(semantic_analysis.people)
                relationship_score += min(people_count * 0.1, 0.3)
            
            # Pronouns indicating social interaction
            social_pronouns = ['we', 'us', 'they', 'them', 'he', 'she', 'him', 'her']
            pronoun_count = sum(1 for pronoun in social_pronouns if f' {pronoun} ' in f' {text_lower} ')
            relationship_score += min(pronoun_count * 0.05, 0.2)
            
            # Communication verbs
            communication_verbs = ['talk', 'speak', 'tell', 'share', 'discuss', 'call', 'text', 'meet']
            comm_count = sum(1 for verb in communication_verbs if verb in text_lower)
            relationship_score += min(comm_count * 0.06, 0.1)
            
            return min(relationship_score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating relationship focus: {e}")
            return 0.0
    
    def _calculate_goal_orientation(self, raw_text: str, semantic_analysis) -> float:
        """Calculate focus on goals, achievements, and future planning"""
        try:
            if not raw_text:
                return 0.0
            
            goal_score = 0.0
            text_lower = raw_text.lower()
            
            # Goal-oriented keywords
            goal_matches = sum(1 for keyword in self.goal_keywords if keyword in text_lower)
            goal_score += min(goal_matches * 0.1, 0.4)
            
            # Future events from semantic analysis
            if semantic_analysis and hasattr(semantic_analysis, 'future_events'):
                event_count = len(semantic_analysis.future_events)
                goal_score += min(event_count * 0.15, 0.3)
            
            # Planning language
            planning_words = ['plan', 'schedule', 'organize', 'prepare', 'arrange', 'setup']
            planning_count = sum(1 for word in planning_words if word in text_lower)
            goal_score += min(planning_count * 0.08, 0.2)
            
            # Achievement language
            achievement_words = ['accomplished', 'completed', 'finished', 'succeeded', 'achieved']
            achievement_count = sum(1 for word in achievement_words if word in text_lower)
            goal_score += min(achievement_count * 0.1, 0.1)
            
            return min(goal_score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating goal orientation: {e}")
            return 0.0
    
    def _calculate_introspection_level(self, raw_text: str) -> float:
        """Calculate level of self-reflection and introspection"""
        try:
            if not raw_text:
                return 0.0
            
            introspection_score = 0.0
            text_lower = raw_text.lower()
            
            # Introspective keywords
            introspection_matches = sum(1 for keyword in self.introspection_keywords if keyword in text_lower)
            introspection_score += min(introspection_matches * 0.08, 0.4)
            
            # Self-referential language
            self_references = text_lower.count(' i ') + text_lower.count('myself') + text_lower.count('my ')
            introspection_score += min(self_references * 0.02, 0.2)
            
            # Emotional awareness language
            emotion_awareness = ['feel', 'feeling', 'emotion', 'mood', 'state of mind']
            emotion_count = sum(1 for word in emotion_awareness if word in text_lower)
            introspection_score += min(emotion_count * 0.05, 0.2)
            
            # Questioning and wondering
            questions = text_lower.count('?') + text_lower.count('wonder') + text_lower.count('why')
            introspection_score += min(questions * 0.05, 0.2)
            
            return min(introspection_score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating introspection level: {e}")
            return 0.0
    
    # def _get_default_features(self) -> UserFeatures:
    #     """Return default user features for error cases"""
    #     return UserFeatures(
    #         writing_consistency=0.5,
    #         session_patterns=0.5,
    #         topic_preference_match=0.5,
    #         emotional_baseline_match=0.5,
    #         behavioral_anomaly=0.0,
    #         engagement_level=0.5,
    #         personal_growth=0.0,
    #         relationship_focus=0.0,
    #         goal_orientation=0.0,
    #         introspection_level=0.0
    #     )
    
    def get_feature_names(self) -> List[str]:
        """Get names of all user features for debugging"""
        return [
            'writing_consistency', 'session_patterns', 'topic_preference_match', 
            'emotional_baseline_match', 'behavioral_anomaly', 'engagement_level',
            'personal_growth', 'relationship_focus', 'goal_orientation', 'introspection_level',
            'overall_consistency', 'baseline_match', 'growth_indicators', 'life_focus', 'normality_score'
        ]
    
    def update_user_history(
        self, 
        user_history: UserHistoryContext,
        current_features: UserFeatures,
        entry_timestamp: datetime,
        raw_text: str
    ) -> UserHistoryContext:
        """
        Update user history with current entry information
        
        Args:
            user_history: Current user history
            current_features: Features extracted from current entry
            entry_timestamp: When the entry was written
            raw_text: Original text content
            
        Returns:
            Updated UserHistoryContext
        """
        try:
            # Update entry count
            user_history.total_entries += 1
            
            # Update writing times
            hour = entry_timestamp.hour
            if hour not in user_history.preferred_writing_times:
                user_history.preferred_writing_times.append(hour)
                # Keep only top 5 most common hours
                if len(user_history.preferred_writing_times) > 5:
                    user_history.preferred_writing_times = user_history.preferred_writing_times[-5:]
            
            # Update behavioral patterns
            if 'avg_entry_length' not in user_history.behavioral_patterns:
                user_history.behavioral_patterns['avg_entry_length'] = len(raw_text.split())
            else:
                # Moving average
                current_length = len(raw_text.split())
                old_avg = user_history.behavioral_patterns['avg_entry_length']
                new_avg = (old_avg * 0.9) + (current_length * 0.1)
                user_history.behavioral_patterns['avg_entry_length'] = new_avg
            
            # Update last entry timestamp
            user_history.last_entry_timestamp = entry_timestamp
            
            return user_history
            
        except Exception as e:
            logger.error(f"Error updating user history: {e}")
            return user_history
