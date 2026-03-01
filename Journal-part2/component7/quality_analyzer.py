"""
Quality Analyzer Module for Component 7.
Assesses response quality, coherence, and relevance for AI responses.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import re
import json

from shared.schemas import (
    EnhancedResponse, QualityMetrics, ResponseAnalysis
)
from shared.utils import (
    get_logger, log_execution_time, generate_correlation_id,
    extract_keywords, clean_text
)


class QualityAnalyzer:
    """Analyzes response quality and generates improvement suggestions"""
    
    def __init__(self):
        """Initialize quality analyzer"""
        self.logger = get_logger("quality_analyzer")
        
        # Quality assessment models (simplified for production)
        self.coherence_patterns = self._load_coherence_patterns()
        self.safety_patterns = self._load_safety_patterns()
        self.engagement_patterns = self._load_engagement_patterns()
        
        # Performance tracking
        self.analysis_times = []
        self.quality_scores = []
        
        self.logger.info("Quality Analyzer initialized")
    
    def _load_coherence_patterns(self) -> List[str]:
        """Load coherence patterns for analysis"""
        return [
            r'\b(however|moreover|furthermore|additionally|consequently)\b',
            r'\b(because|since|therefore|thus|hence)\b',
            r'\b(first|second|third|finally|in conclusion)\b'
        ]
    
    def _load_safety_patterns(self) -> List[str]:
        """Load safety patterns for analysis"""
        return [
            r'\b(dangerous|harmful|unsafe|risky)\b',
            r'\b(illegal|unlawful|forbidden)\b'
        ]
    
    def _load_engagement_patterns(self) -> List[str]:
        """Load engagement patterns for analysis"""
        return [
            r'\?',  # Questions
            r'\b(what do you think|how do you feel|would you like)\b',
            r'\b(interesting|exciting|amazing)\b'
        ]
    
    def _get_quality_score(self, response) -> float:
        """Safely extract quality score from response object"""
        try:
            # Try different attribute names used in EnhancedResponse
            if hasattr(response, 'quality_score'):
                return float(response.quality_score)
            elif hasattr(response, 'quality_metrics'):
                metrics = response.quality_metrics
                if isinstance(metrics, dict):
                    return float(metrics.get('overall_score', metrics.get('overall_quality', 0.5)))
            elif hasattr(response, 'enhancement_metadata'):
                metadata = response.enhancement_metadata
                if isinstance(metadata, dict):
                    return float(metadata.get('quality_score', 0.5))
        except (AttributeError, TypeError, ValueError):
            pass
        
        # Default fallback
        return 0.5
    
    @log_execution_time
    async def analyze_response(
        self,
        response: EnhancedResponse,
        context_used: Dict[str, Any],
        user_satisfaction: Optional[float] = None
    ) -> ResponseAnalysis:
        """Analyze response quality and generate comprehensive assessment"""
        correlation_id = generate_correlation_id()
        
        # Get response text safely
        response_text = ""
        if hasattr(response, 'enhanced_response') and response.enhanced_response:
            response_text = str(response.enhanced_response)
        elif hasattr(response, 'original_response') and response.original_response:
            response_text = str(response.original_response)
        else:
            response_text = str(response)
        
        self.logger.info(f"Analyzing response quality for {getattr(response, 'response_id', 'unknown')}", extra={
            "correlation_id": correlation_id,
            "response_length": len(response_text)
        })
        
        start_time = datetime.utcnow()
        
        try:
            # Calculate quality metrics
            quality_metrics = await self._calculate_quality_metrics(
                response, context_used
            )
            
            # Analyze context usage
            context_usage = await self._analyze_context_usage(
                response, context_used
            )
            
            # Generate improvement suggestions
            improvement_suggestions = await self._generate_improvement_suggestions(
                response, quality_metrics, context_usage
            )
            
            # Create response analysis
            analysis = ResponseAnalysis(
                analysis_id=correlation_id,
                response_id=getattr(response, 'response_id', 'unknown'),
                conversation_id=getattr(response, 'conversation_id', 'unknown'),
                user_id=getattr(response, 'user_id', 'unknown'),
                quality_scores=quality_metrics,
                context_usage=context_usage,
                user_satisfaction=user_satisfaction or 0.5,
                improvement_suggestions=improvement_suggestions,
                analysis_timestamp=datetime.utcnow()
            )
            
            # Update performance tracking
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            self.analysis_times.append(processing_time)
            self.quality_scores.append(quality_metrics.get('overall_quality', 0.5))
            
            self.logger.info(f"Quality analysis completed", extra={
                "correlation_id": correlation_id,
                "processing_time_ms": processing_time,
                "overall_quality": quality_metrics.get('overall_quality', 0.5)
            })
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Failed to analyze response quality: {e}", extra={
                "correlation_id": correlation_id,
                "error": str(e)
            })
            raise
    
    async def _calculate_quality_metrics(
        self,
        response: EnhancedResponse,
        context_used: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate comprehensive quality metrics"""
        
        # Get response text
        response_text = getattr(response, 'enhanced_response', '') or getattr(response, 'original_response', '') or str(response)
        
        metrics = {}
        
        # Coherence score
        metrics['coherence_score'] = self._calculate_coherence_score(response_text)
        
        # Relevance score
        metrics['relevance_score'] = self._calculate_relevance_score(response_text, context_used)
        
        # Context usage score
        metrics['context_usage_score'] = self._calculate_context_usage_score(response, context_used)
        
        # Safety score
        metrics['safety_score'] = self._calculate_safety_score(response_text)
        
        # Overall quality score (weighted average)
        metrics['overall_quality'] = (
            metrics['coherence_score'] * 0.3 +
            metrics['relevance_score'] * 0.3 +
            metrics['context_usage_score'] * 0.2 +
            metrics['safety_score'] * 0.2
        )
        
        return metrics
    
    def _calculate_coherence_score(self, response_text: str) -> float:
        """Calculate coherence score based on text structure"""
        if not response_text:
            return 0.0
        
        score = 0.5  # Base score
        
        # Check for transition words
        coherence_matches = sum(1 for pattern in self.coherence_patterns 
                               if re.search(pattern, response_text.lower()))
        
        # Normalize by response length
        sentence_count = len(re.split(r'[.!?]+', response_text))
        if sentence_count > 0:
            transition_ratio = coherence_matches / sentence_count
            score += min(0.3, transition_ratio)
        
        # Check for logical flow (simplified)
        if len(response_text.split()) > 20:  # Longer responses
            score += 0.2
        
        return min(1.0, max(0.0, score))
    
    def _calculate_relevance_score(self, response_text: str, context_used: Dict[str, Any]) -> float:
        """Calculate relevance score based on context"""
        if not response_text or not context_used:
            return 0.5
        
        score = 0.5  # Base score
        
        # Check for context keyword usage
        context_keywords = []
        if 'memories' in context_used:
            for memory in context_used.get('memories', []):
                if isinstance(memory, dict) and 'content_summary' in memory:
                    context_keywords.extend(memory['content_summary'].lower().split()[:5])
        
        if context_keywords:
            response_words = set(response_text.lower().split())
            context_word_set = set(context_keywords)
            overlap = len(response_words.intersection(context_word_set))
            
            if context_keywords:
                relevance_ratio = overlap / len(context_word_set)
                score += min(0.4, relevance_ratio)
        
        return min(1.0, max(0.0, score))
    
    def _calculate_context_usage_score(self, response: EnhancedResponse, context_used: Dict[str, Any]) -> float:
        """Calculate how well the response uses provided context"""
        if not context_used:
            return 0.5
        
        # Use existing quality score from response if available
        existing_score = self._get_quality_score(response)
        if existing_score != 0.5:  # If we got a real score
            return existing_score
        
        # Basic heuristic scoring
        score = 0.5
        
        # Check if memories were provided and potentially used
        if 'memories' in context_used and context_used['memories']:
            score += 0.3
        
        return min(1.0, max(0.0, score))
    
    def _calculate_safety_score(self, response_text: str) -> float:
        """Calculate safety score"""
        if not response_text:
            return 1.0  # Safe by default
        
        # Check for potentially unsafe patterns
        safety_violations = sum(1 for pattern in self.safety_patterns 
                               if re.search(pattern, response_text.lower()))
        
        if safety_violations == 0:
            return 1.0
        else:
            # Reduce score based on violations
            return max(0.0, 1.0 - (safety_violations * 0.2))
    
    async def _analyze_context_usage(
        self,
        response: EnhancedResponse,
        context_used: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze how well the response utilizes provided context"""
        
        context_analysis = {
            "memories_referenced": 0,
            "context_integration_score": 0.5,
            "missing_context_opportunities": [],
            "effective_usage": []
        }
        
        # Check memory usage
        if 'memories' in context_used:
            memories = context_used.get('memories', [])
            context_analysis["memories_referenced"] = len(memories)
            
            if memories:
                context_analysis["context_integration_score"] = 0.7
                context_analysis["effective_usage"].append("Used provided memories")
        
        return context_analysis
    
    async def _generate_improvement_suggestions(
        self,
        response: EnhancedResponse,
        quality_metrics: Dict[str, float],
        context_usage: Dict[str, Any]
    ) -> List[str]:
        """Generate specific improvement suggestions"""
        
        suggestions = []
        
        # Quality-based suggestions
        if quality_metrics.get('coherence_score', 0.5) < 0.6:
            suggestions.append("Improve response coherence with better transitions")
        
        if quality_metrics.get('relevance_score', 0.5) < 0.6:
            suggestions.append("Better incorporate context keywords and themes")
        
        if quality_metrics.get('context_usage_score', 0.5) < 0.6:
            suggestions.append("Make better use of provided memory context")
        
        # Context-based suggestions
        if context_usage.get('memories_referenced', 0) == 0:
            suggestions.append("Reference relevant memories when available")
        
        # Default suggestion if none generated
        if not suggestions:
            suggestions.append("Continue maintaining response quality")
        
        return suggestions
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get analyzer performance metrics"""
        if not self.analysis_times:
            return {
                "total_analyses": 0,
                "avg_processing_time_ms": 0,
                "avg_quality_score": 0
            }
        
        return {
            "total_analyses": len(self.analysis_times),
            "avg_processing_time_ms": sum(self.analysis_times) / len(self.analysis_times),
            "avg_quality_score": sum(self.quality_scores) / len(self.quality_scores),
            "min_quality_score": min(self.quality_scores),
            "max_quality_score": max(self.quality_scores)
        }