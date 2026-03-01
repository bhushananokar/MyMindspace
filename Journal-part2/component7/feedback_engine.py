"""
Feedback Engine Module for Component 7.
Generates feedback reports for upstream components and manages feedback loops.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import json

from shared.schemas import (
    ResponseAnalysis, ConversationMetrics, ContextEffectiveness,
    FeedbackReport, QualityMetrics
)
from shared.utils import (
    get_logger, log_execution_time, generate_correlation_id
)
from configu.settings import settings


class FeedbackEngine:
    """Generates and manages feedback for upstream components"""
    
    def __init__(self):
        """Initialize feedback engine"""
        self.logger = get_logger("feedback_engine")
        
        # Feedback storage and tracking
        self.feedback_history = {}
        self.component_performance = {}
        self.feedback_patterns = {}
        
        # Performance tracking
        self.feedback_generation_times = []
        self.feedback_impact_scores = []
        
        self.logger.info("Feedback Engine initialized")
    
    @log_execution_time
    async def generate_component_feedback(
        self,
        component_target: str,
        analysis_results: List[ResponseAnalysis],
        conversation_metrics: Optional[ConversationMetrics] = None,
        context_effectiveness: Optional[ContextEffectiveness] = None
    ) -> List[FeedbackReport]:
        """Generate feedback reports for specified component"""
        correlation_id = generate_correlation_id()
        self.logger.info(f"Generating feedback for {component_target}", extra={
            "correlation_id": correlation_id,
            "analysis_count": len(analysis_results)
        })
        
        start_time = datetime.utcnow()
        
        try:
            feedback_reports = []
            
            # Analyze performance patterns
            performance_analysis = await self._analyze_component_performance(
                component_target, analysis_results
            )
            
            # Generate specific feedback based on component type
            if component_target == "component5":
                feedback_reports = await self._generate_memory_gate_feedback(
                    analysis_results, performance_analysis
                )
            elif component_target == "component6":
                feedback_reports = await self._generate_gemini_integration_feedback(
                    analysis_results, performance_analysis, conversation_metrics, context_effectiveness
                )
            else:
                # Generic feedback for other components
                feedback_reports = await self._generate_generic_feedback(
                    component_target, analysis_results, performance_analysis
                )
            
            # Store feedback history
            await self._store_feedback_history(component_target, feedback_reports)
            
            # Update performance tracking
            self._update_performance_metrics(start_time, len(feedback_reports))
            
            self.logger.info(f"Generated {len(feedback_reports)} feedback reports for {component_target}", extra={
                "correlation_id": correlation_id,
                "component_target": component_target
            })
            
            return feedback_reports
            
        except Exception as e:
            self.logger.error(f"Failed to generate component feedback: {e}", extra={
                "correlation_id": correlation_id,
                "component_target": component_target,
                "error": str(e)
            })
            raise
    
    async def _analyze_component_performance(
        self,
        component_target: str,
        analysis_results: List[ResponseAnalysis]
    ) -> Dict[str, Any]:
        """Analyze component performance based on analysis results"""
        if not analysis_results:
            return {"error": "No analysis results provided"}
        
        performance_data = {
            "total_responses": len(analysis_results),
            "avg_quality_score": 0.0,
            "quality_distribution": {},
            "context_usage_stats": {},
            "improvement_areas": [],
            "strength_areas": []
        }
        
        # Calculate quality statistics
        quality_scores = []
        context_usage_scores = []
        
        for analysis in analysis_results:
            # Extract quality scores
            if 'overall_quality' in analysis.quality_scores:
                quality_scores.append(analysis.quality_scores['overall_quality'])
            
            # Extract context usage scores
            if 'context_usage_score' in analysis.quality_scores:
                context_usage_scores.append(analysis.quality_scores['context_usage_score'])
        
        # Calculate averages
        if quality_scores:
            performance_data["avg_quality_score"] = sum(quality_scores) / len(quality_scores)
        
        if context_usage_scores:
            performance_data["avg_context_usage"] = sum(context_usage_scores) / len(context_usage_scores)
        
        # Analyze quality distribution
        quality_ranges = {
            "excellent": (0.9, 1.0),
            "good": (0.7, 0.9),
            "average": (0.5, 0.7),
            "poor": (0.0, 0.5)
        }
        
        for range_name, (min_val, max_val) in quality_ranges.items():
            count = sum(1 for score in quality_scores if min_val <= score < max_val)
            performance_data["quality_distribution"][range_name] = count
        
        # Identify improvement areas
        if quality_scores and performance_data["avg_quality_score"] < 0.7:
            performance_data["improvement_areas"].append("Overall response quality needs improvement")
        
        if context_usage_scores and performance_data.get("avg_context_usage", 0) < 0.6:
            performance_data["improvement_areas"].append("Context utilization could be improved")
        
        # Identify strength areas
        if quality_scores and performance_data["avg_quality_score"] > 0.8:
            performance_data["strength_areas"].append("Maintaining high response quality")
        
        return performance_data
    
    async def _generate_memory_gate_feedback(
        self,
        analysis_results: List[ResponseAnalysis],
        performance_analysis: Dict[str, Any]
    ) -> List[FeedbackReport]:
        """Generate feedback for Component 5 (Memory Gates)"""
        feedback_reports = []
        
        # Analyze memory selection effectiveness
        memory_effectiveness = await self._analyze_memory_selection_effectiveness(analysis_results)
        
        # Generate memory selection feedback
        if memory_effectiveness["needs_improvement"]:
            feedback_reports.append(FeedbackReport(
                feedback_id=generate_correlation_id(),
                component_target="component5",
                recommendation_type="memory_selection",
                priority_level="high" if memory_effectiveness["impact_score"] > 0.3 else "medium",
                expected_impact=memory_effectiveness["impact_score"],
                recommendation_details=memory_effectiveness["recommendation"],
                supporting_metrics=memory_effectiveness["metrics"]
            ))
        
        # Analyze context assembly effectiveness
        context_effectiveness = await self._analyze_context_assembly_effectiveness(analysis_results)
        
        if context_effectiveness["needs_improvement"]:
            feedback_reports.append(FeedbackReport(
                feedback_id=generate_correlation_id(),
                component_target="component5",
                recommendation_type="context_assembly",
                priority_level="medium",
                expected_impact=context_effectiveness["impact_score"],
                recommendation_details=context_effectiveness["recommendation"],
                supporting_metrics=context_effectiveness["metrics"]
            ))
        
        # Generate performance improvement feedback
        if performance_analysis.get("avg_quality_score", 0) < 0.7:
            feedback_reports.append(FeedbackReport(
                feedback_id=generate_correlation_id(),
                component_target="component5",
                recommendation_type="memory_selection",
                priority_level="high",
                expected_impact=0.25,
                recommendation_details="Optimize memory selection criteria to improve response relevance",
                supporting_metrics={"current_avg_quality": performance_analysis["avg_quality_score"]}
            ))
        
        return feedback_reports
    
    async def _generate_gemini_integration_feedback(
        self,
        analysis_results: List[ResponseAnalysis],
        performance_analysis: Dict[str, Any],
        conversation_metrics: Optional[ConversationMetrics],
        context_effectiveness: Optional[ContextEffectiveness]
    ) -> List[FeedbackReport]:
        """Generate feedback for Component 6 (Gemini Integration)"""
        feedback_reports = []
        
        # Analyze prompt engineering effectiveness
        prompt_effectiveness = await self._analyze_prompt_engineering_effectiveness(analysis_results)
        
        if prompt_effectiveness["needs_improvement"]:
            feedback_reports.append(FeedbackReport(
                feedback_id=generate_correlation_id(),
                component_target="component6",
                recommendation_type="context_assembly",
                priority_level="medium",
                expected_impact=prompt_effectiveness["impact_score"],
                recommendation_details=prompt_effectiveness["recommendation"],
                supporting_metrics=prompt_effectiveness["metrics"]
            ))
        
        # Analyze personality adaptation
        personality_analysis = await self._analyze_personality_adaptation(analysis_results)
        
        if personality_analysis["needs_improvement"]:
            feedback_reports.append(FeedbackReport(
                feedback_id=generate_correlation_id(),
                component_target="component6",
                recommendation_type="personality",
                priority_level="medium",
                expected_impact=personality_analysis["impact_score"],
                recommendation_details=personality_analysis["recommendation"],
                supporting_metrics=personality_analysis["metrics"]
            ))
        
        # Analyze proactive engagement if metrics available
        if conversation_metrics:
            proactive_analysis = await self._analyze_proactive_engagement(conversation_metrics)
            
            if proactive_analysis["needs_improvement"]:
                feedback_reports.append(FeedbackReport(
                    feedback_id=generate_correlation_id(),
                    component_target="component6",
                    recommendation_type="proactive_timing",
                    priority_level="low",
                    expected_impact=proactive_analysis["impact_score"],
                    recommendation_details=proactive_analysis["recommendation"],
                    supporting_metrics=proactive_analysis["metrics"]
                ))
        
        # Generate general performance feedback
        if performance_analysis.get("avg_quality_score", 0) < 0.7:
            feedback_reports.append(FeedbackReport(
                feedback_id=generate_correlation_id(),
                component_target="component6",
                recommendation_type="context_assembly",
                priority_level="high",
                expected_impact=0.3,
                recommendation_details="Review and optimize prompt engineering for better response quality",
                supporting_metrics={"current_avg_quality": performance_analysis["avg_quality_score"]}
            ))
        
        return feedback_reports
    
    async def _generate_generic_feedback(
        self,
        component_target: str,
        analysis_results: List[ResponseAnalysis],
        performance_analysis: Dict[str, Any]
    ) -> List[FeedbackReport]:
        """Generate generic feedback for other components"""
        feedback_reports = []
        
        # Generate performance-based feedback
        if performance_analysis.get("avg_quality_score", 0) < 0.7:
            feedback_reports.append(FeedbackReport(
                feedback_id=generate_correlation_id(),
                component_target=component_target,
                recommendation_type="memory_selection",  # Default type
                priority_level="medium",
                expected_impact=0.2,
                recommendation_details=f"Review {component_target} performance and identify improvement opportunities",
                supporting_metrics={"current_avg_quality": performance_analysis["avg_quality_score"]}
            ))
        
        return feedback_reports
    
    async def _analyze_memory_selection_effectiveness(
        self,
        analysis_results: List[ResponseAnalysis]
    ) -> Dict[str, Any]:
        """Analyze effectiveness of memory selection from Component 5"""
        analysis = {
            "needs_improvement": False,
            "impact_score": 0.0,
            "recommendation": "",
            "metrics": {}
        }
        
        # Calculate context usage effectiveness
        context_scores = []
        for result in analysis_results:
            if 'context_usage_score' in result.quality_scores:
                context_scores.append(result.quality_scores['context_usage_score'])
        
        if context_scores:
            avg_context_score = sum(context_scores) / len(context_scores)
            analysis["metrics"]["avg_context_usage"] = avg_context_score
            
            if avg_context_score < 0.6:
                analysis["needs_improvement"] = True
                analysis["impact_score"] = 0.3
                analysis["recommendation"] = "Improve memory selection relevance to increase context utilization"
        
        return analysis
    
    async def _analyze_context_assembly_effectiveness(
        self,
        analysis_results: List[ResponseAnalysis]
    ) -> Dict[str, Any]:
        """Analyze effectiveness of context assembly"""
        analysis = {
            "needs_improvement": False,
            "impact_score": 0.0,
            "recommendation": "",
            "metrics": {}
        }
        
        # Analyze token efficiency and context relevance
        relevance_scores = []
        for result in analysis_results:
            if 'relevance_score' in result.quality_scores:
                relevance_scores.append(result.quality_scores['relevance_score'])
        
        if relevance_scores:
            avg_relevance = sum(relevance_scores) / len(relevance_scores)
            analysis["metrics"]["avg_relevance"] = avg_relevance
            
            if avg_relevance < 0.7:
                analysis["needs_improvement"] = True
                analysis["impact_score"] = 0.25
                analysis["recommendation"] = "Optimize context assembly to improve response relevance"
        
        return analysis
    
    async def _analyze_prompt_engineering_effectiveness(
        self,
        analysis_results: List[ResponseAnalysis]
    ) -> Dict[str, Any]:
        """Analyze effectiveness of prompt engineering"""
        analysis = {
            "needs_improvement": False,
            "impact_score": 0.0,
            "recommendation": "",
            "metrics": {}
        }
        
        # Analyze coherence and personality consistency
        coherence_scores = []
        personality_scores = []
        
        for result in analysis_results:
            if 'coherence_score' in result.quality_scores:
                coherence_scores.append(result.quality_scores['coherence_score'])
            if 'personality_consistency_score' in result.quality_scores:
                personality_scores.append(result.quality_scores['personality_consistency_score'])
        
        if coherence_scores:
            avg_coherence = sum(coherence_scores) / len(coherence_scores)
            analysis["metrics"]["avg_coherence"] = avg_coherence
            
            if avg_coherence < 0.7:
                analysis["needs_improvement"] = True
                analysis["impact_score"] = 0.2
                analysis["recommendation"] = "Improve prompt engineering for better response coherence"
        
        if personality_scores:
            avg_personality = sum(personality_scores) / len(personality_scores)
            analysis["metrics"]["avg_personality_consistency"] = avg_personality
            
            if avg_personality < 0.8:
                analysis["needs_improvement"] = True
                analysis["impact_score"] = 0.15
                analysis["recommendation"] = "Enhance personality consistency in prompt engineering"
        
        return analysis
    
    async def _analyze_personality_adaptation(
        self,
        analysis_results: List[ResponseAnalysis]
    ) -> Dict[str, Any]:
        """Analyze personality adaptation effectiveness"""
        analysis = {
            "needs_improvement": False,
            "impact_score": 0.0,
            "recommendation": "",
            "metrics": {}
        }
        
        # Analyze personality consistency and engagement
        personality_scores = []
        engagement_scores = []
        
        for result in analysis_results:
            if 'personality_consistency_score' in result.quality_scores:
                personality_scores.append(result.quality_scores['personality_consistency_score'])
            if 'engagement_potential' in result.quality_scores:
                engagement_scores.append(result.quality_scores['engagement_potential'])
        
        if personality_scores:
            avg_personality = sum(personality_scores) / len(personality_scores)
            analysis["metrics"]["avg_personality_consistency"] = avg_personality
            
            if avg_personality < 0.8:
                analysis["needs_improvement"] = True
                analysis["impact_score"] = 0.2
                analysis["recommendation"] = "Improve personality adaptation algorithms for better consistency"
        
        if engagement_scores:
            avg_engagement = sum(engagement_scores) / len(engagement_scores)
            analysis["metrics"]["avg_engagement"] = avg_engagement
            
            if avg_engagement < 0.6:
                analysis["needs_improvement"] = True
                analysis["impact_score"] = 0.15
                analysis["recommendation"] = "Enhance engagement strategies in personality adaptation"
        
        return analysis
    
    async def _analyze_proactive_engagement(
        self,
        conversation_metrics: ConversationMetrics
    ) -> Dict[str, Any]:
        """Analyze proactive engagement effectiveness"""
        analysis = {
            "needs_improvement": False,
            "impact_score": 0.0,
            "recommendation": "",
            "metrics": {}
        }
        
        # Analyze proactive success rate
        if hasattr(conversation_metrics, 'proactive_success_rate'):
            success_rate = conversation_metrics.proactive_success_rate
            analysis["metrics"]["proactive_success_rate"] = success_rate
            
            if success_rate < 0.6:
                analysis["needs_improvement"] = True
                analysis["impact_score"] = 0.15
                analysis["recommendation"] = "Optimize proactive engagement timing and content"
        
        return analysis
    
    async def _store_feedback_history(
        self,
        component_target: str,
        feedback_reports: List[FeedbackReport]
    ) -> None:
        """Store feedback history for tracking and analysis"""
        timestamp = datetime.utcnow()
        
        if component_target not in self.feedback_history:
            self.feedback_history[component_target] = []
        
        for report in feedback_reports:
            history_entry = {
                "feedback_id": report.feedback_id,
                "timestamp": timestamp,
                "recommendation_type": report.recommendation_type,
                "priority_level": report.priority_level,
                "expected_impact": report.expected_impact,
                "recommendation_details": report.recommendation_details
            }
            
            self.feedback_history[component_target].append(history_entry)
        
        # Clean up old feedback (keep last 100 entries per component)
        if len(self.feedback_history[component_target]) > 100:
            self.feedback_history[component_target] = self.feedback_history[component_target][-100:]
    
    def _update_performance_metrics(self, start_time: datetime, feedback_count: int) -> None:
        """Update performance tracking metrics"""
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        self.feedback_generation_times.append(processing_time)
        
        # Estimate impact score (simplified)
        impact_score = min(0.5, feedback_count * 0.1)
        self.feedback_impact_scores.append(impact_score)
        
        # Keep only last 100 measurements
        if len(self.feedback_generation_times) > 100:
            self.feedback_generation_times = self.feedback_generation_times[-100:]
        if len(self.feedback_impact_scores) > 100:
            self.feedback_impact_scores = self.feedback_impact_scores[-100:]
    
    async def get_feedback_summary(
        self,
        component_target: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get feedback summary for a component over specified days"""
        if component_target not in self.feedback_history:
            return {"error": "No feedback history for component"}
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        recent_feedback = [
            entry for entry in self.feedback_history[component_target]
            if entry["timestamp"] > cutoff_date
        ]
        
        if not recent_feedback:
            return {"message": f"No feedback in last {days} days"}
        
        # Analyze feedback patterns
        priority_counts = {}
        type_counts = {}
        total_impact = 0.0
        
        for entry in recent_feedback:
            priority = entry["priority_level"]
            feedback_type = entry["recommendation_type"]
            impact = entry["expected_impact"]
            
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
            type_counts[feedback_type] = type_counts.get(feedback_type, 0) + 1
            total_impact += impact
        
        return {
            "component_target": component_target,
            "period_days": days,
            "total_feedback": len(recent_feedback),
            "priority_distribution": priority_counts,
            "type_distribution": type_counts,
            "average_expected_impact": total_impact / len(recent_feedback) if recent_feedback else 0.0,
            "recent_feedback": recent_feedback[-10:]  # Last 10 entries
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for monitoring"""
        if not self.feedback_generation_times:
            return {
                "avg_generation_time_ms": 0.0,
                "avg_impact_score": 0.0,
                "total_feedback_generated": 0
            }
        
        return {
            "avg_generation_time_ms": sum(self.feedback_generation_times) / len(self.feedback_generation_times),
            "min_generation_time_ms": min(self.feedback_generation_times),
            "max_generation_time_ms": max(self.feedback_generation_times),
            "avg_impact_score": sum(self.feedback_impact_scores) / len(self.feedback_impact_scores),
            "total_feedback_generated": len(self.feedback_generation_times)
        }
    
    async def cleanup_old_feedback(self, max_age_days: int = 90) -> int:
        """Clean up old feedback entries"""
        cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)
        total_removed = 0
        
        for component in list(self.feedback_history.keys()):
            original_count = len(self.feedback_history[component])
            self.feedback_history[component] = [
                entry for entry in self.feedback_history[component]
                if entry["timestamp"] > cutoff_date
            ]
            removed = original_count - len(self.feedback_history[component])
            total_removed += removed
        
        if total_removed > 0:
            self.logger.info(f"Cleaned up {total_removed} old feedback entries")
        
        return total_removed
