"""
Temporal Feature Extractor for Component 4
Extracts time-based patterns, cycles, recency, and anomalies
"""

import numpy as np
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

from comp4.data.schemas import TemporalFeatures, UserHistoryContext

logger = logging.getLogger(__name__)

class TemporalFeatureExtractor:
    """
    Extracts temporal features from journal entries
    Focuses on time patterns, cycles, and behavioral timing
    """
    
    def __init__(self):
        """Initialize temporal feature extractor"""
        self.name = "TemporalFeatureExtractor"
        self.version = "4.0"
        
    def extract(
        self,
        entry_timestamp: datetime,
        user_history: Optional[UserHistoryContext] = None,
        semantic_analysis = None,
        raw_text: str = ""
    ) -> TemporalFeatures:
        """
        Extract temporal features from entry timestamp and context
        
        Args:
            entry_timestamp: When the entry was written
            user_history: User's historical context
            semantic_analysis: Semantic analysis for event detection
            raw_text: Original text for analysis
            
        Returns:
            TemporalFeatures object with 25-dimensional feature vector
        """
        try:
            # Basic cyclical features
            cyclical_hour = entry_timestamp.hour
            cyclical_day = entry_timestamp.weekday()  # 0=Monday, 6=Sunday
            cyclical_month = entry_timestamp.month
            
            # Calculate days since last entry
            days_since_last = self._calculate_days_since_last(entry_timestamp, user_history)
            
            # Writing frequency analysis
            writing_frequency_score = self._calculate_frequency_score(days_since_last, user_history)
            
            # Consistency scoring
            consistency_score = self._calculate_consistency_score(entry_timestamp, user_history)
            
            # Spontaneity analysis
            spontaneity_score = self._calculate_spontaneity_score(
                entry_timestamp, days_since_last, user_history
            )
            
            # Future orientation from semantic analysis
            future_orientation = self._calculate_future_orientation(semantic_analysis, raw_text)
            
            # Time pressure indicators
            time_pressure = self._calculate_time_pressure(semantic_analysis, raw_text)
            
            # Anomaly detection
            anomaly_score = self._calculate_anomaly_score(entry_timestamp, user_history)
            
            return TemporalFeatures(
                cyclical_hour=cyclical_hour,
                cyclical_day=cyclical_day,
                cyclical_month=cyclical_month,
                days_since_last=min(days_since_last, 30.0),  # Cap at 30 days
                writing_frequency_score=writing_frequency_score,
                consistency_score=consistency_score,
                spontaneity_score=spontaneity_score,
                future_orientation=future_orientation,
                time_pressure=time_pressure,
                anomaly_score=anomaly_score
            )
            
        except Exception as e:
            logger.error(f"Error extracting temporal features: {e}")
            # Return default features on error
            return
    
    def _calculate_days_since_last(
        self, 
        current_timestamp: datetime, 
        user_history: Optional[UserHistoryContext]
    ) -> float:
        """Calculate days since last entry"""
        if not user_history or not user_history.last_entry_timestamp:
            return 1.0  # Default to 1 day for new users
        
        time_diff = current_timestamp - user_history.last_entry_timestamp
        return max(time_diff.total_seconds() / (24 * 3600), 0.0)
    
    def _calculate_frequency_score(
        self, 
        days_since_last: float, 
        user_history: Optional[UserHistoryContext]
    ) -> float:
        """Calculate writing frequency relative to user baseline"""
        if not user_history:
            return 0.5  # Neutral score for new users
        
        baseline_frequency = user_history.writing_frequency_baseline
        if baseline_frequency <= 0:
            return 0.5
        
        # Expected days between entries based on baseline
        expected_gap = 1.0 / baseline_frequency
        
        # Score based on how close actual gap is to expected
        if expected_gap == 0:
            return 1.0
        
        frequency_ratio = expected_gap / max(days_since_last, 0.1)
        return min(frequency_ratio, 2.0) / 2.0  # Normalize to 0-1
    
    def _calculate_consistency_score(
        self, 
        entry_timestamp: datetime, 
        user_history: Optional[UserHistoryContext]
    ) -> float:
        """Calculate temporal consistency based on user patterns"""
        if not user_history or not user_history.preferred_writing_times:
            return 0.5  # Neutral for new users
        
        current_hour = entry_timestamp.hour
        preferred_hours = user_history.preferred_writing_times
        
        if not preferred_hours:
            return 0.5
        
        # Find closest preferred hour
        min_distance = min(
            min(abs(current_hour - pref), 24 - abs(current_hour - pref))
            for pref in preferred_hours
        )
        
        # Convert distance to consistency score (closer = higher score)
        consistency = max(0, 1.0 - (min_distance / 12.0))
        return consistency
    
    def _calculate_spontaneity_score(
        self, 
        entry_timestamp: datetime, 
        days_since_last: float,
        user_history: Optional[UserHistoryContext]
    ) -> float:
        """Calculate how spontaneous this entry is"""
        # Base spontaneity on time since last entry and typical patterns
        if days_since_last < 0.5:  # Same day
            spontaneity = 0.8
        elif days_since_last < 1.0:  # Next day
            spontaneity = 0.6
        elif days_since_last < 3.0:  # Within 3 days
            spontaneity = 0.4
        else:  # Longer gap
            spontaneity = min(days_since_last / 7.0, 1.0)  # Max at 1 week
        
        # Adjust based on time of day patterns
        hour = entry_timestamp.hour
        if hour < 6 or hour > 23:  # Very late/early
            spontaneity += 0.2
        elif 6 <= hour <= 9 or 17 <= hour <= 22:  # Normal times
            spontaneity -= 0.1
        
        return max(0, min(spontaneity, 1.0))
    
    def _calculate_future_orientation(self, semantic_analysis, raw_text: str) -> float:
        """Calculate focus on future events"""
        score = 0.0
        
        # From semantic analysis
        if semantic_analysis and hasattr(semantic_analysis, 'future_events'):
            event_count = len(semantic_analysis.future_events)
            score += min(event_count * 0.2, 0.6)  # Cap at 0.6 from events
        
        # Text analysis for future keywords
        future_keywords = [
            'tomorrow', 'next', 'will', 'going to', 'plan', 'schedule',
            'upcoming', 'future', 'later', 'soon', 'eventually', 'goal'
        ]
        
        text_lower = raw_text.lower()
        keyword_matches = sum(1 for keyword in future_keywords if keyword in text_lower)
        score += min(keyword_matches * 0.05, 0.4)  # Cap at 0.4 from keywords
        
        return min(score, 1.0)
    
    def _calculate_time_pressure(self, semantic_analysis, raw_text: str) -> float:
        """Calculate time pressure and deadline indicators"""
        score = 0.0
        
        # Pressure keywords
        pressure_keywords = [
            'deadline', 'urgent', 'rush', 'hurry', 'stress', 'pressure',
            'due', 'overdue', 'late', 'behind', 'catch up', 'running out'
        ]
        
        text_lower = raw_text.lower()
        pressure_matches = sum(1 for keyword in pressure_keywords if keyword in text_lower)
        score += min(pressure_matches * 0.15, 0.7)
        
        # Emotional pressure indicators
        if semantic_analysis and hasattr(semantic_analysis, 'detected_topics'):
            stress_topics = ['stress', 'anxiety', 'worry', 'deadline', 'work']
            topic_matches = sum(
                1 for topic in semantic_analysis.detected_topics 
                if any(stress_word in topic.lower() for stress_word in stress_topics)
            )
            score += min(topic_matches * 0.1, 0.3)
        
        return min(score, 1.0)
    
    def _calculate_anomaly_score(
        self, 
        entry_timestamp: datetime, 
        user_history: Optional[UserHistoryContext]
    ) -> float:
        """Calculate how anomalous this timing is for the user"""
        if not user_history:
            return 0.0  # No baseline for new users
        
        anomaly_score = 0.0
        
        # Time of day anomaly
        hour = entry_timestamp.hour
        if user_history.preferred_writing_times:
            avg_hour = sum(user_history.preferred_writing_times) / len(user_history.preferred_writing_times)
            hour_diff = min(abs(hour - avg_hour), 24 - abs(hour - avg_hour))
            anomaly_score += min(hour_diff / 12.0, 0.5)
        
        # Day of week anomaly (weekday vs weekend)
        is_weekend = entry_timestamp.weekday() >= 5
        if hasattr(user_history, 'weekend_writing_ratio'):
            expected_weekend = user_history.weekend_writing_ratio > 0.5
            if is_weekend != expected_weekend:
                anomaly_score += 0.3
        
        # Frequency anomaly
        if hasattr(user_history, 'avg_gap_days'):
            if user_history.last_entry_timestamp:
                actual_gap = (entry_timestamp - user_history.last_entry_timestamp).days
                expected_gap = getattr(user_history, 'avg_gap_days', 1.0)
                gap_ratio = abs(actual_gap - expected_gap) / max(expected_gap, 1.0)
                anomaly_score += min(gap_ratio / 2.0, 0.2)
        
        return min(anomaly_score, 1.0)
    
    # def _get_default_features(self, entry_timestamp: datetime) -> TemporalFeatures:
    #     """Return default temporal features for error cases"""
    #     return TemporalFeatures(
    #         cyclical_hour=entry_timestamp.hour,
    #         cyclical_day=entry_timestamp.weekday(),
    #         cyclical_month=entry_timestamp.month,
    #         days_since_last=1.0,
    #         writing_frequency_score=0.5,
    #         consistency_score=0.5,
    #         spontaneity_score=0.5,
    #         future_orientation=0.0,
    #         time_pressure=0.0,
    #         anomaly_score=0.0
    #     )
    
    def get_feature_names(self) -> List[str]:
        """Get names of all temporal features for debugging"""
        return [
            'sin_hour', 'cos_hour', 'sin_day', 'cos_day', 'sin_month', 'cos_month',
            'days_since_last', 'frequency_score', 'consistency_score', 'spontaneity_score',
            'future_orientation', 'time_pressure', 'anomaly_score',
            'norm_hour', 'norm_day', 'late_night', 'weekend', 'morning', 'work_hours', 'evening',
            'weeks_since_last', 'frequency_capped', 'consistency_repeat', 'spontaneity_repeat', 'anomaly_repeat'
        ]
