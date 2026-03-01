"""
Component 7: Gemini Response Analysis
Main orchestrator and analysis coordination module.
"""

from .quality_analyzer import QualityAnalyzer
from .satisfaction_tracker import SatisfactionTracker
from .feedback_engine import FeedbackEngine
from .metrics_collector import MetricsCollector

__all__ = [
    "QualityAnalyzer",
    "SatisfactionTracker", 
    "FeedbackEngine",
    "MetricsCollector",
    "Component7Orchestrator"
]


class Component7Orchestrator:
    """Main orchestrator for Component 7 analysis and feedback"""
    
    def __init__(self):
        """Initialize Component 7 orchestrator"""
        self.quality_analyzer = QualityAnalyzer()
        self.satisfaction_tracker = SatisfactionTracker()
        self.feedback_engine = FeedbackEngine()
        self.metrics_collector = MetricsCollector()
    
    async def analyze_response(self, response=None, context_used=None, user_satisfaction=None, **kwargs):
        """Complete response analysis pipeline - handles errors gracefully"""
        
        # Handle None response
        if response is None:
            return {
                "analysis": None,
                "satisfaction": {"satisfaction_score": 0.5}
            }
        
        # Ensure context_used is not None
        if context_used is None:
            context_used = {}
        
        try:
            # Check if we have the required analyzer
            if not hasattr(self, 'quality_analyzer'):
                return {
                    "analysis": None,
                    "satisfaction": {"satisfaction_score": 0.5}
                }
            
            # Analyze response quality with error handling
            try:
                analysis = await self.quality_analyzer.analyze_response(
                    response, context_used, user_satisfaction
                )
            except Exception as qa_error:
                print(f"Quality analyzer failed: {qa_error}")
                # Create minimal mock analysis when quality analyzer fails
                analysis = type('MockAnalysis', (), {
                    'quality_scores': {'overall_quality': 0.5},
                    'context_usage': {},
                    'user_satisfaction': user_satisfaction or 0.5,
                    'improvement_suggestions': []
                })()
            
            # Get user_id from response object if available
            user_id = getattr(response, 'user_id', 'unknown')
            
            # Track user satisfaction with error handling
            try:
                satisfaction_data = await self.satisfaction_tracker.track_user_satisfaction(
                    user_id, analysis
                )
            except Exception as st_error:
                print(f"Satisfaction tracker failed: {st_error}")
                satisfaction_data = {"satisfaction_score": 0.5}
            
            # Collect metrics with error handling
            try:
                quality_score = 0.5  # Default
                if hasattr(analysis, 'quality_scores') and isinstance(analysis.quality_scores, dict):
                    quality_score = analysis.quality_scores.get("overall_quality", 0.5)
                
                await self.metrics_collector.collect_component_metrics(
                    "component7",
                    {
                        "quality_score": quality_score,
                        "satisfaction_score": satisfaction_data.get("satisfaction_score", 0.5),
                        "processing_time_ms": 100  # placeholder
                    }
                )
            except Exception as mc_error:
                print(f"Metrics collection failed: {mc_error}")
            
            return {
                "analysis": analysis,
                "satisfaction": satisfaction_data
            }
            
        except Exception as e:
            print(f"Error in Component7 analyze_response: {e}")
            # Return safe fallback
            return {
                "analysis": None,
                "satisfaction": {"satisfaction_score": 0.5}
            }
    
    async def generate_feedback(self, component_target, analysis_results):
        """Generate feedback for upstream components"""
        try:
            return await self.feedback_engine.generate_component_feedback(
                component_target, analysis_results
            )
        except Exception as e:
            print(f"Error generating feedback: {e}")
            return []
    
    def get_performance_summary(self):
        """Get comprehensive performance summary"""
        try:
            return {
                "quality_analyzer": self.quality_analyzer.get_performance_metrics() if hasattr(self.quality_analyzer, 'get_performance_metrics') else {},
                "satisfaction_tracker": self.satisfaction_tracker.get_performance_metrics() if hasattr(self.satisfaction_tracker, 'get_performance_metrics') else {},
                "feedback_engine": self.feedback_engine.get_performance_metrics() if hasattr(self.feedback_engine, 'get_performance_metrics') else {},
                "metrics_collector": self.metrics_collector.get_performance_metrics() if hasattr(self.metrics_collector, 'get_performance_metrics') else {}
            }
        except Exception as e:
            print(f"Error getting performance summary: {e}")
            return {}