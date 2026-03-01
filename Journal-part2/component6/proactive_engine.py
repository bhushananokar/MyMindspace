"""
Proactive Engine Module for Component 6.
Handles AI-initiated conversations and proactive engagement with advanced
pattern analysis and timing optimization as specified in documentation.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json

from shared.schemas import ProactiveMessage, UserProfile
from shared.utils import get_logger, generate_correlation_id
from configu.settings import settings


class ProactiveEngine:
    """Manages AI-initiated conversations and proactive engagement with advanced features"""
    
    def __init__(self):
        """Initialize proactive engine"""
        self.logger = get_logger("proactive_engine")
        self.message_queue = []
        self.scheduled_messages = {}
        self.user_patterns = {}
        self.engagement_success_rates = []
        self.trigger_templates = self._load_trigger_templates()
        self.timing_patterns = {}
        self.stress_pattern_thresholds = {
            "mild": 0.6,
            "moderate": 0.75,
            "high": 0.9
        }
        self.logger.info("Proactive Engine initialized")
    
    async def analyze_user_patterns(
        self,
        user_id: str,
        activity_data: Dict[str, Any],
        emotional_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze user activity and emotional patterns for proactive opportunities"""
        patterns = {
            "activity_patterns": self._analyze_activity_patterns(activity_data),
            "emotional_patterns": self._analyze_emotional_patterns(emotional_history),
            "stress_indicators": self._detect_stress_patterns(emotional_history),
            "engagement_windows": self._identify_engagement_windows(activity_data),
            "intervention_opportunities": []
        }
        
        # Store patterns for future use
        self.user_patterns[user_id] = {
            "patterns": patterns,
            "last_updated": datetime.utcnow(),
            "analysis_confidence": self._calculate_pattern_confidence(patterns)
        }
        
        # Identify intervention opportunities
        patterns["intervention_opportunities"] = self._identify_intervention_opportunities(patterns)
        
        return patterns
    
    async def generate_proactive_message(
        self,
        user_id: str,
        trigger_event: str,
        context: Dict[str, Any],
        user_profile: Optional[UserProfile] = None
    ) -> Optional[ProactiveMessage]:
        """Generate proactive message with advanced context awareness"""
        try:
            # Check if proactive messages are enabled
            if user_profile and not user_profile.proactive_engagement:
                return None
            
            # Check daily limits and timing appropriateness
            if not self._check_daily_limits(user_id) or not await self._is_appropriate_timing(user_id):
                return None
            
            # Generate contextual message content
            message_content = await self._generate_contextual_message(
                trigger_event, context, user_profile, user_id
            )
            
            if not message_content:
                return None
            
            # Calculate optimal timing using pattern analysis
            optimal_timing = await self._calculate_optimal_timing_advanced(user_id, trigger_event, context)
            
            # Determine priority level based on trigger
            priority_level = self._determine_priority_level(trigger_event, context)
            
            # Create proactive message
            proactive_message = ProactiveMessage(
                message_id=generate_correlation_id(),
                user_id=user_id,
                trigger_event=trigger_event,
                message_content=message_content,
                optimal_timing=optimal_timing,
                expected_response=self._predict_expected_response(trigger_event, context),
                priority_level=priority_level
            )
            
            # Schedule message with advanced queuing
            await self._schedule_message_advanced(proactive_message)
            
            return proactive_message
            
        except Exception as e:
            self.logger.error(f"Failed to generate proactive message: {e}")
            return None
    
    def _analyze_activity_patterns(self, activity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze user activity patterns for optimal engagement timing"""
        if not activity_data:
            return {"confidence": 0.0, "patterns": {}}
        
        patterns = {
            "peak_hours": [],
            "low_activity_periods": [],
            "preferred_days": [],
            "session_duration_avg": 0,
            "response_time_avg": 0
        }
        
        # Analyze hourly patterns
        hourly_activity = activity_data.get("hourly_activity", {})
        if hourly_activity:
            sorted_hours = sorted(hourly_activity.items(), key=lambda x: x[1], reverse=True)
            patterns["peak_hours"] = [int(hour) for hour, _ in sorted_hours[:3]]
            patterns["low_activity_periods"] = [int(hour) for hour, _ in sorted_hours[-3:]]
        
        # Analyze daily patterns
        daily_activity = activity_data.get("daily_activity", {})
        if daily_activity:
            sorted_days = sorted(daily_activity.items(), key=lambda x: x[1], reverse=True)
            patterns["preferred_days"] = [day for day, _ in sorted_days[:3]]
        
        # Calculate confidence based on data availability
        confidence = min(1.0, len(hourly_activity) / 24 * 0.5 + len(daily_activity) / 7 * 0.5)
        
        return {"confidence": confidence, "patterns": patterns}
    
    def _analyze_emotional_patterns(self, emotional_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze emotional patterns to identify intervention opportunities"""
        if not emotional_history:
            return {"confidence": 0.0, "patterns": {}}
        
        patterns = {
            "stress_trends": [],
            "emotional_volatility": 0.0,
            "positive_emotion_triggers": [],
            "negative_emotion_triggers": [],
            "recovery_patterns": []
        }
        
        # Analyze stress trends
        stress_levels = [entry.get("stress_level", 5) for entry in emotional_history[-14:]]  # Last 2 weeks
        if len(stress_levels) >= 3:
            patterns["stress_trends"] = self._calculate_trend(stress_levels)
            patterns["emotional_volatility"] = self._calculate_volatility(stress_levels)
        
        # Identify emotional triggers
        for i, entry in enumerate(emotional_history[1:], 1):
            prev_entry = emotional_history[i-1]
            current_emotion = entry.get("primary_emotion", "neutral")
            prev_emotion = prev_entry.get("primary_emotion", "neutral")
            
            # Look for significant emotional changes
            if current_emotion != prev_emotion:
                trigger_context = entry.get("context", {})
                if self._is_positive_emotion(current_emotion):
                    patterns["positive_emotion_triggers"].append(trigger_context)
                elif self._is_negative_emotion(current_emotion):
                    patterns["negative_emotion_triggers"].append(trigger_context)
        
        confidence = min(1.0, len(emotional_history) / 30)  # 30 days for good confidence
        
        return {"confidence": confidence, "patterns": patterns}
    
    def _detect_stress_patterns(self, emotional_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect stress patterns requiring intervention"""
        if not emotional_history:
            return {"stress_level": "unknown", "intervention_needed": False}
        
        recent_stress = [entry.get("stress_level", 5) for entry in emotional_history[-7:]]  # Last week
        
        if not recent_stress:
            return {"stress_level": "unknown", "intervention_needed": False}
        
        avg_stress = sum(recent_stress) / len(recent_stress)
        stress_trend = "stable"
        
        if len(recent_stress) >= 3:
            if recent_stress[-1] > recent_stress[0] + 1:
                stress_trend = "increasing"
            elif recent_stress[-1] < recent_stress[0] - 1:
                stress_trend = "decreasing"
        
        # Determine intervention need
        intervention_needed = (
            avg_stress >= self.stress_pattern_thresholds["moderate"] or
            (stress_trend == "increasing" and avg_stress >= self.stress_pattern_thresholds["mild"])
        )
        
        return {
            "average_stress": avg_stress,
            "stress_trend": stress_trend,
            "intervention_needed": intervention_needed,
            "urgency_level": self._calculate_stress_urgency(avg_stress, stress_trend)
        }
    
    def _identify_engagement_windows(self, activity_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify optimal windows for proactive engagement"""
        windows = []
        
        if not activity_data:
            # Default windows if no data
            return [
                {"hour": 9, "confidence": 0.3, "type": "morning_checkin"},
                {"hour": 15, "confidence": 0.3, "type": "afternoon_break"},
                {"hour": 20, "confidence": 0.3, "type": "evening_reflection"}
            ]
        
        hourly_activity = activity_data.get("hourly_activity", {})
        
        for hour, activity_level in hourly_activity.items():
            if activity_level > 0.3:  # Moderate activity threshold
                window_type = self._classify_engagement_window(int(hour))
                windows.append({
                    "hour": int(hour),
                    "confidence": min(1.0, activity_level),
                    "type": window_type,
                    "activity_level": activity_level
                })
        
        return sorted(windows, key=lambda x: x["confidence"], reverse=True)[:5]  # Top 5 windows
    
    async def _generate_contextual_message(
        self,
        trigger_event: str,
        context: Dict[str, Any],
        user_profile: Optional[UserProfile],
        user_id: str
    ) -> str:
        """Generate contextual message content based on user patterns and trigger"""
        template = self.trigger_templates.get(trigger_event, self.trigger_templates["default"])
        
        # Get user patterns for personalization
        user_pattern_data = self.user_patterns.get(user_id, {})
        
        # Personalize based on communication style
        if user_profile:
            if user_profile.communication_style.value == "formal":
                template = template.replace("Hi there!", "Good day,")
                template = template.replace("How are you feeling?", "I hope you are well.")
            elif user_profile.communication_style.value == "casual":
                template = template.replace("Good day,", "Hey!")
                template = template.replace("I hope you are well.", "How's it going?")
        
        # Add context-specific elements
        if "stress_level" in context and context["stress_level"] > 7:
            template += " I'm here to help you work through whatever is on your mind."
        
        # Incorporate recent patterns
        if user_pattern_data and "patterns" in user_pattern_data:
            emotional_patterns = user_pattern_data["patterns"].get("emotional_patterns", {})
            if emotional_patterns.get("patterns", {}).get("stress_trends") == "increasing":
                template += " I noticed you might be going through a challenging time."
        
        return template
    
    async def _calculate_optimal_timing_advanced(
        self,
        user_id: str,
        trigger_event: str,
        context: Dict[str, Any]
    ) -> datetime:
        """Calculate optimal timing using advanced pattern analysis"""
        base_time = datetime.utcnow()
        
        # Get user patterns
        user_pattern_data = self.user_patterns.get(user_id, {})
        
        if user_pattern_data and "patterns" in user_pattern_data:
            engagement_windows = user_pattern_data["patterns"].get("engagement_windows", [])
            
            if engagement_windows:
                # Find next optimal window
                current_hour = base_time.hour
                best_window = None
                
                # Look for windows in the next 24 hours
                for window in engagement_windows:
                    window_hour = window["hour"]
                    
                    # Calculate when this window occurs next
                    if window_hour > current_hour:
                        # Today
                        target_time = base_time.replace(hour=window_hour, minute=0, second=0, microsecond=0)
                    else:
                        # Tomorrow
                        target_time = (base_time + timedelta(days=1)).replace(hour=window_hour, minute=0, second=0, microsecond=0)
                    
                    if not best_window or window["confidence"] > best_window["confidence"]:
                        best_window = {"time": target_time, "confidence": window["confidence"]}
                
                if best_window:
                    base_time = best_window["time"]
        
        # Adjust for trigger urgency
        urgency_delays = {
            "stress_pattern": timedelta(minutes=30),
            "user_inactive": timedelta(hours=2),
            "follow_up_needed": timedelta(hours=1),
            "weekly_reflection": timedelta(hours=12),
            "goal_milestone": timedelta(minutes=15),
            "emotional_spike": timedelta(minutes=45)
        }
        
        if trigger_event in urgency_delays:
            adjustment = urgency_delays[trigger_event]
            # For urgent triggers, reduce delay if it's currently an optimal time
            if trigger_event in ["stress_pattern", "emotional_spike"]:
                current_hour = datetime.utcnow().hour
                if 9 <= current_hour <= 21:  # Daytime hours
                    adjustment = min(adjustment, timedelta(minutes=15))
            
            base_time = datetime.utcnow() + adjustment
        
        return base_time
    
    def _determine_priority_level(self, trigger_event: str, context: Dict[str, Any]) -> str:
        """Determine message priority based on trigger and context"""
        high_priority_triggers = ["stress_pattern", "emotional_spike", "crisis_indicator"]
        medium_priority_triggers = ["follow_up_needed", "goal_milestone", "pattern_concern"]
        
        if trigger_event in high_priority_triggers:
            return "high"
        elif trigger_event in medium_priority_triggers:
            return "medium"
        else:
            return "low"
    
    def _predict_expected_response(self, trigger_event: str, context: Dict[str, Any]) -> str:
        """Predict expected user response type"""
        response_predictions = {
            "stress_pattern": "emotional_sharing",
            "user_inactive": "general_update",
            "follow_up_needed": "specific_response",
            "goal_milestone": "celebration_acknowledgment",
            "weekly_reflection": "reflective_sharing",
            "emotional_spike": "emotional_processing"
        }
        
        return response_predictions.get(trigger_event, "general_response")
    
    async def _schedule_message_advanced(self, message: ProactiveMessage) -> None:
        """Schedule message with advanced queuing logic"""
        if message.user_id not in self.scheduled_messages:
            self.scheduled_messages[message.user_id] = []
        
        user_messages = self.scheduled_messages[message.user_id]
        
        # Check for conflicts with existing messages
        for existing_message in user_messages:
            time_diff = abs((message.optimal_timing - existing_message.optimal_timing).total_seconds())
            if time_diff < 3600:  # Less than 1 hour apart
                # Reschedule based on priority
                if message.priority_level == "high" and existing_message.priority_level != "high":
                    # Delay existing message
                    existing_message.optimal_timing += timedelta(hours=2)
                elif existing_message.priority_level == "high" and message.priority_level != "high":
                    # Delay new message
                    message.optimal_timing += timedelta(hours=2)
        
        user_messages.append(message)
        self.logger.debug(f"Message scheduled for {message.optimal_timing} with priority {message.priority_level}")
    
    async def _is_appropriate_timing(self, user_id: str) -> bool:
        """Check if current time is appropriate for proactive messaging"""
        current_hour = datetime.utcnow().hour
        
        # Basic hours check (not too late or too early)
        if current_hour < 7 or current_hour > 22:
            return False
        
        # Check user patterns if available
        user_pattern_data = self.user_patterns.get(user_id, {})
        if user_pattern_data and "patterns" in user_pattern_data:
            engagement_windows = user_pattern_data["patterns"].get("engagement_windows", [])
            
            # Check if current hour is in any engagement window
            for window in engagement_windows:
                if abs(window["hour"] - current_hour) <= 1:  # Within 1 hour
                    return True
            
            # If we have specific windows but current time isn't in them
            if engagement_windows:
                return False
        
        return True  # Default to appropriate if no specific patterns
    
    def _load_trigger_templates(self) -> Dict[str, str]:
        """Load message templates for different trigger events"""
        return {
            "user_inactive": "Hi there! I was thinking about you. How are you feeling today?",
            "goal_milestone": "Congratulations! I noticed you've made great progress on your goals. How does it feel?",
            "stress_pattern": "I've noticed some patterns that might be worth discussing. Would you like to talk about what's been on your mind?",
            "follow_up_needed": "I was thinking about our last conversation. How are things going with what we discussed?",
            "weekly_reflection": "It's been a while since we reflected together. What's been the highlight of your week?",
            "emotional_spike": "I noticed you might be experiencing some intense emotions. I'm here if you'd like to talk about it.",
            "pattern_concern": "I've noticed some changes in your patterns lately. How are you taking care of yourself?",
            "default": "Hello! I hope you're having a good day. How are things going for you?"
        }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from a series of values"""
        if len(values) < 3:
            return "insufficient_data"
        
        # Simple linear trend calculation
        x = list(range(len(values)))
        n = len(values)
        
        sum_x = sum(x)
        sum_y = sum(values)
        sum_xy = sum(x[i] * values[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))
        
        # Calculate slope
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        
        if slope > 0.1:
            return "increasing"
        elif slope < -0.1:
            return "decreasing"
        else:
            return "stable"
    
    def _calculate_volatility(self, values: List[float]) -> float:
        """Calculate emotional volatility from stress levels"""
        if len(values) < 2:
            return 0.0
        
        # Calculate standard deviation
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    def _is_positive_emotion(self, emotion: str) -> bool:
        """Check if emotion is generally positive"""
        positive_emotions = ["happy", "excited", "content", "grateful", "optimistic", "confident"]
        return emotion.lower() in positive_emotions
    
    def _is_negative_emotion(self, emotion: str) -> bool:
        """Check if emotion is generally negative"""
        negative_emotions = ["sad", "angry", "anxious", "stressed", "frustrated", "overwhelmed", "depressed"]
        return emotion.lower() in negative_emotions
    
    def _calculate_pattern_confidence(self, patterns: Dict[str, Any]) -> float:
        """Calculate confidence level in pattern analysis"""
        confidences = []
        
        for pattern_type, pattern_data in patterns.items():
            if isinstance(pattern_data, dict) and "confidence" in pattern_data:
                confidences.append(pattern_data["confidence"])
        
        if not confidences:
            return 0.0
        
        return sum(confidences) / len(confidences)
    
    def _identify_intervention_opportunities(self, patterns: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify specific intervention opportunities from patterns"""
        opportunities = []
        
        # Check stress patterns
        stress_indicators = patterns.get("stress_indicators", {})
        if stress_indicators.get("intervention_needed", False):
            opportunities.append({
                "type": "stress_intervention",
                "urgency": stress_indicators.get("urgency_level", "medium"),
                "trigger": "stress_pattern",
                "context": {"stress_level": stress_indicators.get("average_stress", 5)}
            })
        
        # Check emotional patterns
        emotional_patterns = patterns.get("emotional_patterns", {}).get("patterns", {})
        if emotional_patterns.get("emotional_volatility", 0) > 2.0:
            opportunities.append({
                "type": "emotional_stability",
                "urgency": "medium",
                "trigger": "emotional_spike",
                "context": {"volatility": emotional_patterns["emotional_volatility"]}
            })
        
        # Check activity patterns for disengagement
        activity_patterns = patterns.get("activity_patterns", {}).get("patterns", {})
        if activity_patterns.get("session_duration_avg", 0) < 5:  # Less than 5 minutes average
            opportunities.append({
                "type": "engagement_drop",
                "urgency": "low",
                "trigger": "user_inactive",
                "context": {"avg_session": activity_patterns["session_duration_avg"]}
            })
        
        return opportunities
    
    def _classify_engagement_window(self, hour: int) -> str:
        """Classify engagement window by time of day"""
        if 6 <= hour <= 10:
            return "morning_checkin"
        elif 11 <= hour <= 14:
            return "midday_break"
        elif 15 <= hour <= 18:
            return "afternoon_engagement"
        elif 19 <= hour <= 22:
            return "evening_reflection"
        else:
            return "off_hours"
    
    def _calculate_stress_urgency(self, avg_stress: float, trend: str) -> str:
        """Calculate urgency level for stress intervention"""
        if avg_stress >= self.stress_pattern_thresholds["high"]:
            return "high"
        elif avg_stress >= self.stress_pattern_thresholds["moderate"]:
            return "high" if trend == "increasing" else "medium"
        elif trend == "increasing" and avg_stress >= self.stress_pattern_thresholds["mild"]:
            return "medium"
        else:
            return "low"
    
    async def generate_proactive_message(
        self,
        user_id: str,
        trigger_event: str,
        context: Dict[str, Any],
        user_profile: Optional[UserProfile] = None
    ) -> Optional[ProactiveMessage]:
        """Generate proactive message based on trigger and context"""
        try:
            # Check if proactive messages are enabled
            if user_profile and not user_profile.proactive_engagement:
                return None
            
            # Check daily limits
            if not self._check_daily_limits(user_id):
                return None
            
            # Generate message content
            message_content = await self._generate_message_content(trigger_event, context, user_profile)
            
            if not message_content:
                return None
            
            # Calculate optimal timing
            optimal_timing = await self._calculate_optimal_timing(user_id, trigger_event)
            
            # Create proactive message
            proactive_message = ProactiveMessage(
                message_id=generate_correlation_id(),
                user_id=user_id,
                trigger_event=trigger_event,
                message_content=message_content,
                optimal_timing=optimal_timing,
                expected_response="general_response",
                priority_level="medium"
            )
            
            # Schedule message
            await self._schedule_message(proactive_message)
            
            return proactive_message
            
        except Exception as e:
            self.logger.error(f"Failed to generate proactive message: {e}")
            return None
    
    async def _generate_message_content(
        self,
        trigger_event: str,
        context: Dict[str, Any],
        user_profile: Optional[UserProfile]
    ) -> str:
        """Generate appropriate message content for trigger event"""
        templates = {
            "user_inactive": "Hi there! I was thinking about you. How are you feeling today?",
            "goal_milestone": "Congratulations! I noticed you've made great progress.",
            "stress_pattern": "I've noticed some patterns that might be worth discussing.",
            "follow_up_needed": "I was thinking about our last conversation. How are things going?",
            "weekly_reflection": "It's been a while since we reflected together. What's been on your mind?"
        }
        
        template = templates.get(trigger_event, templates["user_inactive"])
        
        # Basic personalization
        if "{user_name}" in template and "user_name" in context:
            template = template.replace("{user_name}", context["user_name"])
        
        return template
    
    async def _calculate_optimal_timing(self, user_id: str, trigger_event: str) -> datetime:
        """Calculate optimal timing for message delivery"""
        # Default to current time + small delay
        base_time = datetime.utcnow() + timedelta(minutes=30)
        
        # Adjust based on trigger urgency
        urgency_delays = {
            "stress_pattern": timedelta(minutes=30),
            "user_inactive": timedelta(hours=2),
            "follow_up_needed": timedelta(hours=1),
            "weekly_reflection": timedelta(hours=12)
        }
        
        if trigger_event in urgency_delays:
            base_time = datetime.utcnow() + urgency_delays[trigger_event]
        
        return base_time
    
    async def _schedule_message(self, message: ProactiveMessage) -> None:
        """Schedule message for delivery"""
        if message.user_id not in self.scheduled_messages:
            self.scheduled_messages[message.user_id] = []
        
        self.scheduled_messages[message.user_id].append(message)
        self.logger.debug(f"Message scheduled for {message.optimal_timing}")
    
    def _check_daily_limits(self, user_id: str) -> bool:
        """Check if user hasn't exceeded daily proactive message limits"""
        today = datetime.utcnow().date()
        today_messages = 0
        
        for message in self.scheduled_messages.get(user_id, []):
            if message.optimal_timing.date() == today:
                today_messages += 1
        
        max_daily = getattr(settings.personality, 'max_proactive_messages_per_day', 5)
        return today_messages < max_daily
    
    async def get_pending_messages(self, user_id: str) -> List[ProactiveMessage]:
        """Get pending proactive messages for user"""
        current_time = datetime.utcnow()
        pending_messages = []
        
        for message in self.scheduled_messages.get(user_id, []):
            if (message.optimal_timing <= current_time and 
                message.delivery_status == "pending"):
                pending_messages.append(message)
        
        return pending_messages
    
    async def mark_message_delivered(self, message_id: str, user_id: str) -> bool:
        """Mark message as delivered"""
        for message in self.scheduled_messages.get(user_id, []):
            if message.message_id == message_id:
                message.delivery_status = "delivered"
                return True
        return False
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for monitoring"""
        return {
            "avg_engagement_rate": sum(self.engagement_success_rates) / len(self.engagement_success_rates) if self.engagement_success_rates else 0.0,
            "total_messages_sent": len(self.engagement_success_rates),
            "pending_messages": sum(len(messages) for messages in self.scheduled_messages.values()),
            "active_users": len(self.user_patterns)
        }
