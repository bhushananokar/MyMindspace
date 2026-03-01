"""
Satisfaction Tracker Module for Component 7.
Monitors user engagement and satisfaction signals in real-time.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
import json
import statistics

from shared.schemas import (
    ResponseAnalysis, ConversationMetrics, ContextEffectiveness,
    UserProfile, QualityMetrics
)
from shared.utils import (
    get_logger, log_execution_time, generate_correlation_id
)
from configu.settings import settings


class SatisfactionTracker:
    """Tracks user satisfaction and engagement signals"""
    
    def __init__(self):
        """Initialize satisfaction tracker"""
        self.logger = get_logger("satisfaction_tracker")
        
        # User satisfaction tracking
        self.user_satisfaction = {}
        self.engagement_signals = {}
        self.conversation_satisfaction = {}
        
        # Signal processing
        self.signal_weights = {
            "response_quality": 0.3,
            "context_relevance": 0.25,
            "personality_match": 0.2,
            "response_time": 0.15,
            "proactive_engagement": 0.1
        }
        
        # Performance tracking
        self.satisfaction_calculation_times = []
        self.signal_processing_times = []
        
        self.logger.info("Satisfaction Tracker initialized")
    
    @log_execution_time
    async def track_user_satisfaction(
        self,
        user_id: str,
        response_analysis: ResponseAnalysis,
        conversation_metrics: Optional[ConversationMetrics] = None,
        user_profile: Optional[UserProfile] = None
    ) -> Dict[str, Any]:
        """Track user satisfaction based on response analysis and metrics"""
        correlation_id = generate_correlation_id()
        self.logger.info(f"Tracking satisfaction for user {user_id}", extra={
            "correlation_id": correlation_id,
            "user_id": user_id
        })
        
        start_time = datetime.utcnow()
        
        try:
            # Process engagement signals
            engagement_score = await self._process_engagement_signals(
                response_analysis, conversation_metrics
            )
            
            # Calculate satisfaction score
            satisfaction_score = await self._calculate_satisfaction_score(
                response_analysis, engagement_score, user_profile
            )
            
            # Update user satisfaction tracking
            await self._update_user_satisfaction(user_id, satisfaction_score, engagement_score)
            
            # Update conversation satisfaction
            if conversation_metrics and hasattr(conversation_metrics, 'conversation_id'):
                await self._update_conversation_satisfaction(
                    conversation_metrics.conversation_id, satisfaction_score
                )
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            self.satisfaction_calculation_times.append(processing_time)
            
            # Keep only last 100 measurements
            if len(self.satisfaction_calculation_times) > 100:
                self.satisfaction_calculation_times = self.satisfaction_calculation_times[-100:]
            
            result = {
                "user_id": user_id,
                "satisfaction_score": satisfaction_score,
                "engagement_score": engagement_score,
                "timestamp": datetime.utcnow(),
                "processing_time_ms": processing_time,
                "correlation_id": correlation_id
            }
            
            self.logger.info(f"Satisfaction tracked for user {user_id}: {satisfaction_score:.3f}", extra={
                "correlation_id": correlation_id,
                "user_id": user_id,
                "satisfaction_score": satisfaction_score,
                "engagement_score": engagement_score
            })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to track user satisfaction: {e}", extra={
                "correlation_id": correlation_id,
                "user_id": user_id,
                "error": str(e)
            })
            raise
    
    async def _process_engagement_signals(
        self,
        response_analysis: ResponseAnalysis,
        conversation_metrics: Optional[ConversationMetrics]
    ) -> float:
        """Process various engagement signals to calculate engagement score"""
        start_time = datetime.utcnow()
        
        signals = {}
        
        # Extract quality scores from response analysis
        if hasattr(response_analysis, 'quality_scores') and response_analysis.quality_scores:
            quality_scores = response_analysis.quality_scores
            
            # Response quality signal
            if 'overall_quality' in quality_scores:
                signals['response_quality'] = quality_scores['overall_quality']
            
            # Context relevance signal
            if 'context_usage_score' in quality_scores:
                signals['context_relevance'] = quality_scores['context_usage_score']
            
            # Personality match signal
            if 'personality_consistency_score' in quality_scores:
                signals['personality_match'] = quality_scores['personality_consistency_score']
            
            # Safety and engagement signals
            if 'safety_score' in quality_scores:
                signals['safety'] = quality_scores['safety_score']
            
            if 'engagement_potential' in quality_scores:
                signals['engagement_potential'] = quality_scores['engagement_potential']
        
        # Extract conversation metrics if available
        if conversation_metrics:
            # Response time signal
            if hasattr(conversation_metrics, 'avg_response_time_ms'):
                response_time_score = self._calculate_response_time_score(
                    conversation_metrics.avg_response_time_ms
                )
                signals['response_time'] = response_time_score
            
            # Proactive engagement signal
            if hasattr(conversation_metrics, 'proactive_success_rate'):
                signals['proactive_engagement'] = conversation_metrics.proactive_success_rate
            
            # Conversation flow signal
            if hasattr(conversation_metrics, 'conversation_flow_score'):
                signals['conversation_flow'] = conversation_metrics.conversation_flow_score
        
        # Calculate weighted engagement score
        engagement_score = self._calculate_weighted_score(signals)
        
        # Update processing time tracking
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        self.signal_processing_times.append(processing_time)
        
        if len(self.signal_processing_times) > 100:
            self.signal_processing_times = self.signal_processing_times[-100:]
        
        return engagement_score
    
    def _calculate_response_time_score(self, response_time_ms: float) -> float:
        """Calculate satisfaction score based on response time"""
        # Target: <3 seconds (3000ms)
        # Excellent: <1s, Good: <2s, Average: <3s, Poor: >3s
        
        if response_time_ms < 1000:
            return 1.0
        elif response_time_ms < 2000:
            return 0.8
        elif response_time_ms < 3000:
            return 0.6
        elif response_time_ms < 5000:
            return 0.4
        else:
            return 0.2
    
    def _calculate_weighted_score(self, signals: Dict[str, float]) -> float:
        """Calculate weighted score based on available signals"""
        if not signals:
            return 0.5  # Default neutral score
        
        total_weight = 0.0
        weighted_sum = 0.0
        
        for signal_name, score in signals.items():
            if signal_name in self.signal_weights:
                weight = self.signal_weights[signal_name]
                weighted_sum += score * weight
                total_weight += weight
            else:
                # For signals without predefined weights, use default weight
                default_weight = 0.1
                weighted_sum += score * default_weight
                total_weight += default_weight
        
        if total_weight == 0:
            return 0.5
        
        return weighted_sum / total_weight
    
    async def _calculate_satisfaction_score(
        self,
        response_analysis: ResponseAnalysis,
        engagement_score: float,
        user_profile: Optional[UserProfile]
    ) -> float:
        """Calculate overall user satisfaction score"""
        # Base satisfaction from engagement
        satisfaction_score = engagement_score
        
        # Adjust based on user profile preferences if available
        if user_profile and hasattr(user_profile, 'communication_preferences'):
            preferences = user_profile.communication_preferences
            
            # Adjust for communication style preference
            if hasattr(response_analysis, 'quality_scores') and response_analysis.quality_scores:
                quality_scores = response_analysis.quality_scores
                
                # Personality consistency adjustment
                if 'personality_consistency_score' in quality_scores:
                    personality_score = quality_scores['personality_consistency_score']
                    if personality_score > 0.8:
                        satisfaction_score += 0.1
                    elif personality_score < 0.6:
                        satisfaction_score -= 0.1
                
                # Context usage adjustment
                if 'context_usage_score' in quality_scores:
                    context_score = quality_scores['context_usage_score']
                    if context_score > 0.8:
                        satisfaction_score += 0.05
                    elif context_score < 0.5:
                        satisfaction_score -= 0.05
        
        # Ensure score is within [0, 1] range
        satisfaction_score = max(0.0, min(1.0, satisfaction_score))
        
        return satisfaction_score
    
    async def _update_user_satisfaction(
        self,
        user_id: str,
        satisfaction_score: float,
        engagement_score: float
    ) -> None:
        """Update user satisfaction tracking"""
        timestamp = datetime.utcnow()
        
        if user_id not in self.user_satisfaction:
            self.user_satisfaction[user_id] = {
                "scores": [],
                "engagement": [],
                "last_updated": timestamp,
                "avg_satisfaction": 0.0,
                "avg_engagement": 0.0,
                "trend": "stable"
            }
        
        user_data = self.user_satisfaction[user_id]
        
        # Add new scores
        user_data["scores"].append({
            "score": satisfaction_score,
            "timestamp": timestamp
        })
        user_data["engagement"].append({
            "score": engagement_score,
            "timestamp": timestamp
        })
        
        # Keep only last 50 scores per user
        if len(user_data["scores"]) > 50:
            user_data["scores"] = user_data["scores"][-50:]
        if len(user_data["engagement"]) > 50:
            user_data["engagement"] = user_data["engagement"][-50:]
        
        # Update averages
        user_data["avg_satisfaction"] = sum(s["score"] for s in user_data["scores"]) / len(user_data["scores"])
        user_data["avg_engagement"] = sum(e["score"] for e in user_data["engagement"]) / len(user_data["engagement"])
        
        # Calculate trend (last 10 scores vs previous 10)
        if len(user_data["scores"]) >= 20:
            recent_scores = [s["score"] for s in user_data["scores"][-10:]]
            previous_scores = [s["score"] for s in user_data["scores"][-20:-10]]
            
            recent_avg = sum(recent_scores) / len(recent_scores)
            previous_avg = sum(previous_scores) / len(previous_scores)
            
            if recent_avg > previous_avg + 0.1:
                user_data["trend"] = "improving"
            elif recent_avg < previous_avg - 0.1:
                user_data["trend"] = "declining"
            else:
                user_data["trend"] = "stable"
        
        user_data["last_updated"] = timestamp
    
    async def _update_conversation_satisfaction(
        self,
        conversation_id: str,
        satisfaction_score: float
    ) -> None:
        """Update conversation-level satisfaction tracking"""
        timestamp = datetime.utcnow()
        
        if conversation_id not in self.conversation_satisfaction:
            self.conversation_satisfaction[conversation_id] = {
                "scores": [],
                "avg_satisfaction": 0.0,
                "start_time": timestamp,
                "last_updated": timestamp
            }
        
        conv_data = self.conversation_satisfaction[conversation_id]
        
        # Add new score
        conv_data["scores"].append({
            "score": satisfaction_score,
            "timestamp": timestamp
        })
        
        # Keep only last 20 scores per conversation
        if len(conv_data["scores"]) > 20:
            conv_data["scores"] = conv_data["scores"][-20:]
        
        # Update average
        conv_data["avg_satisfaction"] = sum(s["score"] for s in conv_data["scores"]) / len(conv_data["scores"])
        conv_data["last_updated"] = timestamp
    
    async def get_user_satisfaction_summary(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get satisfaction summary for a specific user"""
        if user_id not in self.user_satisfaction:
            return {"error": "No satisfaction data for user"}
        
        user_data = self.user_satisfaction[user_id]
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Filter recent scores
        recent_scores = [
            s for s in user_data["scores"]
            if s["timestamp"] > cutoff_date
        ]
        
        recent_engagement = [
            e for e in user_data["engagement"]
            if e["timestamp"] > cutoff_date
        ]
        
        if not recent_scores:
            return {"message": f"No satisfaction data in last {days} days"}
        
        # Calculate statistics
        satisfaction_scores = [s["score"] for s in recent_scores]
        engagement_scores = [e["score"] for e in recent_engagement]
        
        return {
            "user_id": user_id,
            "period_days": days,
            "current_satisfaction": user_data["avg_satisfaction"],
            "current_engagement": user_data["avg_engagement"],
            "trend": user_data["trend"],
            "recent_scores": {
                "count": len(recent_scores),
                "average": sum(satisfaction_scores) / len(satisfaction_scores),
                "min": min(satisfaction_scores),
                "max": max(satisfaction_scores),
                "std_dev": statistics.stdev(satisfaction_scores) if len(satisfaction_scores) > 1 else 0.0
            },
            "recent_engagement": {
                "count": len(recent_engagement),
                "average": sum(engagement_scores) / len(engagement_scores) if engagement_scores else 0.0
            },
            "last_updated": user_data["last_updated"]
        }
    
    async def get_conversation_satisfaction_summary(
        self,
        conversation_id: str
    ) -> Dict[str, Any]:
        """Get satisfaction summary for a specific conversation"""
        if conversation_id not in self.conversation_satisfaction:
            return {"error": "No satisfaction data for conversation"}
        
        conv_data = self.conversation_satisfaction[conversation_id]
        
        return {
            "conversation_id": conversation_id,
            "average_satisfaction": conv_data["avg_satisfaction"],
            "total_interactions": len(conv_data["scores"]),
            "start_time": conv_data["start_time"],
            "last_updated": conv_data["last_updated"],
            "satisfaction_trend": self._calculate_conversation_trend(conv_data["scores"])
        }
    
    def _calculate_conversation_trend(self, scores: List[Dict[str, Any]]) -> str:
        """Calculate trend for a conversation based on score progression"""
        if len(scores) < 3:
            return "insufficient_data"
        
        # Split scores into halves
        mid_point = len(scores) // 2
        first_half = [s["score"] for s in scores[:mid_point]]
        second_half = [s["score"] for s in scores[mid_point:]]
        
        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)
        
        if second_avg > first_avg + 0.1:
            return "improving"
        elif second_avg < first_avg - 0.1:
            return "declining"
        else:
            return "stable"
    
    async def get_system_satisfaction_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get system-wide satisfaction summary"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Collect recent data from all users
        all_recent_scores = []
        all_recent_engagement = []
        active_users = 0
        
        for user_id, user_data in self.user_satisfaction.items():
            recent_scores = [
                s for s in user_data["scores"]
                if s["timestamp"] > cutoff_date
            ]
            
            if recent_scores:
                active_users += 1
                all_recent_scores.extend([s["score"] for s in recent_scores])
                
                recent_engagement = [
                    e for e in user_data["engagement"]
                    if e["timestamp"] > cutoff_date
                ]
                all_recent_engagement.extend([e["score"] for e in recent_engagement])
        
        if not all_recent_scores:
            return {"message": f"No satisfaction data in last {days} days"}
        
        # Calculate system-wide statistics
        satisfaction_scores = all_recent_scores
        engagement_scores = all_recent_engagement
        
        return {
            "period_days": days,
            "active_users": active_users,
            "total_interactions": len(satisfaction_scores),
            "system_satisfaction": {
                "average": sum(satisfaction_scores) / len(satisfaction_scores),
                "min": min(satisfaction_scores),
                "max": max(satisfaction_scores),
                "std_dev": statistics.stdev(satisfaction_scores) if len(satisfaction_scores) > 1 else 0.0
            },
            "system_engagement": {
                "average": sum(engagement_scores) / len(engagement_scores) if engagement_scores else 0.0
            },
            "user_trends": self._get_user_trends_summary()
        }
    
    def _get_user_trends_summary(self) -> Dict[str, int]:
        """Get summary of user satisfaction trends"""
        trends = {"improving": 0, "stable": 0, "declining": 0}
        
        for user_data in self.user_satisfaction.values():
            trend = user_data.get("trend", "stable")
            trends[trend] += 1
        
        return trends
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for monitoring"""
        if not self.satisfaction_calculation_times:
            return {
                "avg_satisfaction_calculation_ms": 0.0,
                "avg_signal_processing_ms": 0.0,
                "total_satisfaction_tracked": 0
            }
        
        return {
            "avg_satisfaction_calculation_ms": sum(self.satisfaction_calculation_times) / len(self.satisfaction_calculation_times),
            "min_satisfaction_calculation_ms": min(self.satisfaction_calculation_times),
            "max_satisfaction_calculation_ms": max(self.satisfaction_calculation_times),
            "avg_signal_processing_ms": sum(self.signal_processing_times) / len(self.signal_processing_times) if self.signal_processing_times else 0.0,
            "total_satisfaction_tracked": len(self.satisfaction_calculation_times),
            "active_users_tracked": len(self.user_satisfaction),
            "active_conversations_tracked": len(self.conversation_satisfaction)
        }
    
    async def cleanup_old_data(self, max_age_days: int = 90) -> Dict[str, int]:
        """Clean up old satisfaction and engagement data"""
        cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)
        cleanup_stats = {
            "users_cleaned": 0,
            "conversations_cleaned": 0,
            "total_entries_removed": 0
        }
        
        # Clean up user data
        for user_id in list(self.user_satisfaction.keys()):
            user_data = self.user_satisfaction[user_id]
            
            # Clean old scores
            original_score_count = len(user_data["scores"])
            user_data["scores"] = [
                s for s in user_data["scores"]
                if s["timestamp"] > cutoff_date
            ]
            score_removed = original_score_count - len(user_data["scores"])
            
            # Clean old engagement data
            original_engagement_count = len(user_data["engagement"])
            user_data["engagement"] = [
                e for e in user_data["engagement"]
                if e["timestamp"] > cutoff_date
            ]
            engagement_removed = original_engagement_count - len(user_data["engagement"])
            
            total_removed = score_removed + engagement_removed
            if total_removed > 0:
                cleanup_stats["total_entries_removed"] += total_removed
                cleanup_stats["users_cleaned"] += 1
            
            # Remove user if no recent data
            if not user_data["scores"] and not user_data["engagement"]:
                del self.user_satisfaction[user_id]
        
        # Clean up conversation data
        for conv_id in list(self.conversation_satisfaction.keys()):
            conv_data = self.conversation_satisfaction[conv_id]
            
            original_count = len(conv_data["scores"])
            conv_data["scores"] = [
                s for s in conv_data["scores"]
                if s["timestamp"] > cutoff_date
            ]
            
            removed = original_count - len(conv_data["scores"])
            if removed > 0:
                cleanup_stats["total_entries_removed"] += removed
                cleanup_stats["conversations_cleaned"] += 1
            
            # Remove conversation if no recent data
            if not conv_data["scores"]:
                del self.conversation_satisfaction[conv_id]
        
        if any(cleanup_stats.values()):
            self.logger.info(f"Cleaned up old satisfaction data: {cleanup_stats}")
        
        return cleanup_stats
