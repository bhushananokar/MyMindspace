import math
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from collections import defaultdict, Counter
import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from data.schemas import TemporalFeatures

class TemporalAnalyzer:
    """Analyze temporal patterns and create time-based features"""
    
    def __init__(self):
        self.user_patterns = defaultdict(list)  # Store historical patterns per user
        self.pattern_window_days = 90  # Analyze patterns over last 90 days
    
    def analyze_temporal_features(self, 
                                current_time: datetime,
                                user_id: str,
                                last_entry_time: Optional[datetime] = None) -> TemporalFeatures:
        """Analyze temporal features for current entry"""
        
        # Basic time features
        hour_of_day = current_time.hour
        day_of_week = current_time.weekday()  # 0=Monday, 6=Sunday
        is_weekend = day_of_week >= 5
        
        # Days since last entry
        days_since_last = 0
        if last_entry_time:
            days_since_last = (current_time - last_entry_time).days
        
        # Calculate writing frequency score
        frequency_score = self._calculate_frequency_score(user_id, current_time)
        
        # Detect cyclical patterns
        cyclical_patterns = self._detect_cyclical_patterns(user_id, current_time)
        
        # Calculate anomaly score
        anomaly_score = self._calculate_anomaly_score(user_id, current_time)
        
        # Store this entry for future pattern analysis
        self._update_user_patterns(user_id, current_time)
        
        return TemporalFeatures(
            writing_time=current_time,
            hour_of_day=hour_of_day,
            day_of_week=day_of_week,
            is_weekend=is_weekend,
            days_since_last_entry=days_since_last,
            writing_frequency_score=frequency_score,
            cyclical_patterns=cyclical_patterns,
            anomaly_score=anomaly_score
        )
    
    def _calculate_frequency_score(self, user_id: str, current_time: datetime) -> float:
        """Calculate how frequently user writes (0-1 scale)"""
        user_entries = self.user_patterns.get(user_id, [])
        
        if len(user_entries) < 2:
            return 0.5  # Neutral score for new users
        
        # Look at entries in the last 30 days
        recent_cutoff = current_time - timedelta(days=30)
        recent_entries = [entry for entry in user_entries if entry >= recent_cutoff]
        
        if not recent_entries:
            return 0.1  # Low score if no recent activity
        
        # Calculate average days between entries
        if len(recent_entries) < 2:
            return 0.3
        
        intervals = []
        for i in range(1, len(recent_entries)):
            interval = (recent_entries[i] - recent_entries[i-1]).days
            intervals.append(max(interval, 1))  # At least 1 day
        
        avg_interval = sum(intervals) / len(intervals)
        
        # Convert to frequency score (daily=1.0, weekly=0.7, monthly=0.3)
        if avg_interval <= 1.5:
            return 1.0  # Daily
        elif avg_interval <= 7:
            return 0.8  # Weekly
        elif avg_interval <= 14:
            return 0.6  # Bi-weekly
        elif avg_interval <= 30:
            return 0.4  # Monthly
        else:
            return 0.2  # Infrequent
    
    def _detect_cyclical_patterns(self, user_id: str, current_time: datetime) -> Dict[str, float]:
        """Detect daily, weekly, and monthly writing patterns"""
        user_entries = self.user_patterns.get(user_id, [])
        
        if len(user_entries) < 7:  # Need at least a week of data
            return {}
        
        patterns = {}
        
        # Daily patterns (hour of day)
        hour_counts = Counter([entry.hour for entry in user_entries[-50:]])  # Last 50 entries
        if hour_counts:
            most_common_hour = hour_counts.most_common(1)[0][0]
            hour_consistency = hour_counts[most_common_hour] / len(user_entries[-50:])
            patterns['preferred_hour'] = most_common_hour
            patterns['hour_consistency'] = hour_consistency
            
            # Check if current time matches preferred pattern
            if abs(current_time.hour - most_common_hour) <= 1:
                patterns['matches_daily_pattern'] = 1.0
            else:
                patterns['matches_daily_pattern'] = 0.0
        
        # Weekly patterns (day of week)
        dow_counts = Counter([entry.weekday() for entry in user_entries[-30:]])  # Last 30 entries
        if dow_counts:
            most_common_dow = dow_counts.most_common(1)[0][0]
            dow_consistency = dow_counts[most_common_dow] / len(user_entries[-30:])
            patterns['preferred_day_of_week'] = most_common_dow
            patterns['dow_consistency'] = dow_consistency
            
            if current_time.weekday() == most_common_dow:
                patterns['matches_weekly_pattern'] = 1.0
            else:
                patterns['matches_weekly_pattern'] = 0.0
        
        # Weekend vs weekday preference
        weekend_entries = sum(1 for entry in user_entries[-30:] if entry.weekday() >= 5)
        weekday_entries = len(user_entries[-30:]) - weekend_entries
        
        if weekday_entries > 0 and weekend_entries > 0:
            weekend_ratio = weekend_entries / (weekday_entries + weekend_entries)
            patterns['weekend_preference'] = weekend_ratio
        
        return patterns
    
    def _calculate_anomaly_score(self, user_id: str, current_time: datetime) -> float:
        """Calculate how unusual this writing time is (0=normal, 1=very unusual)"""
        user_entries = self.user_patterns.get(user_id, [])
        
        if len(user_entries) < 10:  # Need sufficient history
            return 0.0  # No anomaly for new users
        
        anomaly_factors = []
        
        # Hour anomaly
        user_hours = [entry.hour for entry in user_entries[-50:]]
        hour_mean = sum(user_hours) / len(user_hours)
        hour_std = (sum((h - hour_mean) ** 2 for h in user_hours) / len(user_hours)) ** 0.5
        
        if hour_std > 0:
            hour_z_score = abs(current_time.hour - hour_mean) / hour_std
            hour_anomaly = min(hour_z_score / 3.0, 1.0)  # Normalize to 0-1
            anomaly_factors.append(hour_anomaly)
        
        # Day of week anomaly
        dow_counts = Counter([entry.weekday() for entry in user_entries[-30:]])
        current_dow_freq = dow_counts.get(current_time.weekday(), 0)
        max_dow_freq = max(dow_counts.values()) if dow_counts else 1
        dow_anomaly = 1.0 - (current_dow_freq / max_dow_freq)
        anomaly_factors.append(dow_anomaly)
        
        # Time gap anomaly
        if len(user_entries) > 1:
            recent_gaps = []
            for i in range(1, min(len(user_entries), 20)):
                gap = (user_entries[-i] - user_entries[-i-1]).total_seconds() / 3600  # Hours
                recent_gaps.append(gap)
            
            if recent_gaps:
                last_entry = user_entries[-1]
                current_gap = (current_time - last_entry).total_seconds() / 3600
                
                gap_mean = sum(recent_gaps) / len(recent_gaps)
                gap_std = (sum((g - gap_mean) ** 2 for g in recent_gaps) / len(recent_gaps)) ** 0.5
                
                if gap_std > 0:
                    gap_z_score = abs(current_gap - gap_mean) / gap_std
                    gap_anomaly = min(gap_z_score / 2.0, 1.0)
                    anomaly_factors.append(gap_anomaly)
        
        # Overall anomaly score
        if anomaly_factors:
            return sum(anomaly_factors) / len(anomaly_factors)
        else:
            return 0.0
    
    def _update_user_patterns(self, user_id: str, current_time: datetime):
        """Update stored user patterns with new entry"""
        if user_id not in self.user_patterns:
            self.user_patterns[user_id] = []
        
        self.user_patterns[user_id].append(current_time)
        
        # Keep only recent entries to manage memory
        cutoff_date = current_time - timedelta(days=self.pattern_window_days)
        self.user_patterns[user_id] = [
            entry for entry in self.user_patterns[user_id] 
            if entry >= cutoff_date
        ]
        
        # Keep sorted for easier analysis
        self.user_patterns[user_id].sort()
    
    def get_user_writing_insights(self, user_id: str) -> Dict[str, any]:
        """Get insights about user's writing patterns"""
        user_entries = self.user_patterns.get(user_id, [])
        
        if len(user_entries) < 5:
            return {"message": "Not enough data for insights"}
        
        insights = {}
        
        # Most active times
        hour_counts = Counter([entry.hour for entry in user_entries])
        most_active_hour = hour_counts.most_common(1)[0][0]
        
        if most_active_hour < 6:
            time_period = "very early morning"
        elif most_active_hour < 12:
            time_period = "morning" 
        elif most_active_hour < 17:
            time_period = "afternoon"
        elif most_active_hour < 21:
            time_period = "evening"
        else:
            time_period = "night"
        
        insights['most_active_time'] = f"{most_active_hour}:00 ({time_period})"
        
        # Weekly patterns
        dow_counts = Counter([entry.weekday() for entry in user_entries])
        days_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        most_active_day = days_names[dow_counts.most_common(1)[0][0]]
        insights['most_active_day'] = most_active_day
        
        # Frequency analysis
        if len(user_entries) >= 2:
            total_span = (user_entries[-1] - user_entries[0]).days
            avg_frequency = len(user_entries) / max(total_span, 1)
            
            if avg_frequency >= 0.8:
                frequency_desc = "daily"
            elif avg_frequency >= 0.3:
                frequency_desc = "several times per week"
            elif avg_frequency >= 0.14:
                frequency_desc = "weekly"
            else:
                frequency_desc = "occasionally"
            
            insights['writing_frequency'] = frequency_desc
        
        # Consistency score
        recent_entries = user_entries[-20:]  # Last 20 entries
        if len(recent_entries) >= 3:
            intervals = []
            for i in range(1, len(recent_entries)):
                interval = (recent_entries[i] - recent_entries[i-1]).total_seconds() / 3600
                intervals.append(interval)
            
            mean_interval = sum(intervals) / len(intervals)
            variance = sum((x - mean_interval) ** 2 for x in intervals) / len(intervals)
            std_dev = variance ** 0.5
            
            # Coefficient of variation (lower = more consistent)
            if mean_interval > 0:
                cv = std_dev / mean_interval
                consistency_score = max(0, 1 - cv)  # 1 = very consistent, 0 = very inconsistent
                insights['consistency_score'] = round(consistency_score, 2)
        
        return insights
    
    def predict_next_entry_time(self, user_id: str, current_time: datetime) -> Optional[datetime]:
        """Predict when user might write next based on patterns"""
        user_entries = self.user_patterns.get(user_id, [])
        
        if len(user_entries) < 5:
            return None
        
        # Calculate typical interval
        recent_entries = user_entries[-10:]
        intervals = []
        for i in range(1, len(recent_entries)):
            interval = (recent_entries[i] - recent_entries[i-1]).total_seconds()
            intervals.append(interval)
        
        if not intervals:
            return None
        
        # Use median interval to avoid outlier influence
        intervals.sort()
        median_interval = intervals[len(intervals) // 2]
        
        # Predict next entry time
        predicted_time = current_time + timedelta(seconds=median_interval)
        
        # Adjust to user's preferred time patterns if available
        hour_counts = Counter([entry.hour for entry in user_entries[-20:]])
        if hour_counts:
            preferred_hour = hour_counts.most_common(1)[0][0]
            predicted_time = predicted_time.replace(hour=preferred_hour, minute=0, second=0)
        
        return predicted_time
    
    def detect_writing_streaks(self, user_id: str) -> Dict[str, int]:
        """Detect current and longest writing streaks"""
        user_entries = self.user_patterns.get(user_id, [])
        
        if len(user_entries) < 2:
            return {"current_streak": 0, "longest_streak": 0}
        
        # Group entries by day
        daily_entries = defaultdict(int)
        for entry in user_entries:
            date_key = entry.date()
            daily_entries[date_key] += 1
        
        dates = sorted(daily_entries.keys())
        
        current_streak = 0
        longest_streak = 0
        temp_streak = 0
        
        # Calculate streaks
        for i, date in enumerate(dates):
            if i == 0:
                temp_streak = 1
            else:
                prev_date = dates[i-1]
                if (date - prev_date).days == 1:  # Consecutive days
                    temp_streak += 1
                else:
                    longest_streak = max(longest_streak, temp_streak)
                    temp_streak = 1
        
        longest_streak = max(longest_streak, temp_streak)
        
        # Calculate current streak (from today backwards)
        today = datetime.now().date()
        current_date = today
        
        while current_date in daily_entries:
            current_streak += 1
            current_date -= timedelta(days=1)
        
        return {
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "total_days": len(dates)
        }