"""
Metrics Collector Module for Component 7.
Collects and aggregates performance metrics from all components.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
import json
import statistics
from collections import defaultdict, deque

from shared.schemas import (
    ResponseAnalysis, ConversationMetrics, ContextEffectiveness,
    QualityMetrics, FeedbackReport
)
from shared.utils import (
    get_logger, log_execution_time, generate_correlation_id
)
from configu.settings import settings


class MetricsCollector:
    """Collects and aggregates performance metrics from all components"""
    
    def __init__(self):
        """Initialize metrics collector"""
        self.logger = get_logger("metrics_collector")
        
        # Component metrics storage
        self.component_metrics = defaultdict(dict)
        self.performance_metrics = defaultdict(dict)
        self.quality_metrics = defaultdict(dict)
        self.error_metrics = defaultdict(dict)
        
        # Time-series data storage (rolling windows)
        self.response_time_history = deque(maxlen=1000)
        self.quality_score_history = deque(maxlen=1000)
        self.error_rate_history = deque(maxlen=1000)
        self.token_usage_history = deque(maxlen=1000)
        
        # Aggregation windows
        self.aggregation_windows = {
            "1min": 60,
            "5min": 300,
            "15min": 900,
            "1hour": 3600,
            "1day": 86400
        }
        
        # Performance tracking
        self.collection_times = []
        self.aggregation_times = []
        
        self.logger.info("Metrics Collector initialized")
    
    @log_execution_time
    async def collect_component_metrics(
        self,
        component_name: str,
        metrics_data: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ) -> bool:
        """Collect metrics from a specific component"""
        correlation_id = generate_correlation_id()
        start_time = datetime.utcnow()
        
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        try:
            self.logger.debug(f"Collecting metrics from {component_name}", extra={
                "correlation_id": correlation_id,
                "component_name": component_name,
                "metrics_count": len(metrics_data)
            })
            
            # Store component metrics
            self.component_metrics[component_name][timestamp] = metrics_data
            
            # Extract and store performance metrics
            await self._extract_performance_metrics(component_name, metrics_data, timestamp)
            
            # Extract and store quality metrics
            await self._extract_quality_metrics(component_name, metrics_data, timestamp)
            
            # Extract and store error metrics
            await self._extract_error_metrics(component_name, metrics_data, timestamp)
            
            # Update time-series data
            await self._update_time_series_data(component_name, metrics_data, timestamp)
            
            # Clean up old metrics (keep last 1000 per component)
            await self._cleanup_old_metrics(component_name)
            
            # Calculate collection time
            collection_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            self.collection_times.append(collection_time)
            
            if len(self.collection_times) > 100:
                self.collection_times = self.collection_times[-100:]
            
            self.logger.debug(f"Metrics collected from {component_name} in {collection_time:.2f}ms", extra={
                "correlation_id": correlation_id,
                "component_name": component_name
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to collect metrics from {component_name}: {e}", extra={
                "correlation_id": correlation_id,
                "component_name": component_name,
                "error": str(e)
            })
            return False
    
    async def _extract_performance_metrics(
        self,
        component_name: str,
        metrics_data: Dict[str, Any],
        timestamp: datetime
    ) -> None:
        """Extract performance-related metrics"""
        if component_name not in self.performance_metrics:
            self.performance_metrics[component_name] = defaultdict(list)
        
        perf_metrics = self.performance_metrics[component_name]
        
        # Response time metrics
        if "response_time_ms" in metrics_data:
            perf_metrics["response_times"].append({
                "value": metrics_data["response_time_ms"],
                "timestamp": timestamp
            })
        
        # Processing time metrics
        if "processing_time_ms" in metrics_data:
            perf_metrics["processing_times"].append({
                "value": metrics_data["processing_time_ms"],
                "timestamp": timestamp
            })
        
        # Token usage metrics
        if "token_usage" in metrics_data:
            perf_metrics["token_usage"].append({
                "value": metrics_data["token_usage"],
                "timestamp": timestamp
            })
        
        # Memory usage metrics
        if "memory_usage_mb" in metrics_data:
            perf_metrics["memory_usage"].append({
                "value": metrics_data["memory_usage_mb"],
                "timestamp": timestamp
            })
        
        # Throughput metrics
        if "requests_per_second" in metrics_data:
            perf_metrics["throughput"].append({
                "value": metrics_data["requests_per_second"],
                "timestamp": timestamp
            })
    
    async def _extract_quality_metrics(
        self,
        component_name: str,
        metrics_data: Dict[str, Any],
        timestamp: datetime
    ) -> None:
        """Extract quality-related metrics"""
        if component_name not in self.quality_metrics:
            self.quality_metrics[component_name] = defaultdict(list)
        
        quality_metrics = self.quality_metrics[component_name]
        
        # Quality scores
        if "quality_score" in metrics_data:
            quality_metrics["quality_scores"].append({
                "value": metrics_data["quality_score"],
                "timestamp": timestamp
            })
        
        # Context usage scores
        if "context_usage_score" in metrics_data:
            quality_metrics["context_usage"].append({
                "value": metrics_data["context_usage_score"],
                "timestamp": timestamp
            })
        
        # Relevance scores
        if "relevance_score" in metrics_data:
            quality_metrics["relevance"].append({
                "value": metrics_data["relevance_score"],
                "timestamp": timestamp
            })
        
        # Coherence scores
        if "coherence_score" in metrics_data:
            quality_metrics["coherence"].append({
                "value": metrics_data["coherence_score"],
                "timestamp": timestamp
            })
        
        # Safety scores
        if "safety_score" in metrics_data:
            quality_metrics["safety"].append({
                "value": metrics_data["safety_score"],
                "timestamp": timestamp
            })
    
    async def _extract_error_metrics(
        self,
        component_name: str,
        metrics_data: Dict[str, Any],
        timestamp: datetime
    ) -> None:
        """Extract error-related metrics"""
        if component_name not in self.error_metrics:
            self.error_metrics[component_name] = defaultdict(list)
        
        error_metrics = self.error_metrics[component_name]
        
        # Error counts
        if "error_count" in metrics_data:
            error_metrics["error_counts"].append({
                "value": metrics_data["error_count"],
                "timestamp": timestamp
            })
        
        # Error rates
        if "error_rate" in metrics_data:
            error_metrics["error_rates"].append({
                "value": metrics_data["error_rate"],
                "timestamp": timestamp
            })
        
        # Error types
        if "error_types" in metrics_data:
            error_metrics["error_types"].append({
                "value": metrics_data["error_types"],
                "timestamp": timestamp
            })
        
        # Retry counts
        if "retry_count" in metrics_data:
            error_metrics["retry_counts"].append({
                "value": metrics_data["retry_count"],
                "timestamp": timestamp
            })
    
    async def _update_time_series_data(
        self,
        component_name: str,
        metrics_data: Dict[str, Any],
        timestamp: datetime
    ) -> None:
        """Update time-series data for trending analysis"""
        # Response time
        if "response_time_ms" in metrics_data:
            self.response_time_history.append({
                "component": component_name,
                "value": metrics_data["response_time_ms"],
                "timestamp": timestamp
            })
        
        # Quality score
        if "quality_score" in metrics_data:
            self.quality_score_history.append({
                "component": component_name,
                "value": metrics_data["quality_score"],
                "timestamp": timestamp
            })
        
        # Error rate
        if "error_rate" in metrics_data:
            self.error_rate_history.append({
                "component": component_name,
                "value": metrics_data["error_rate"],
                "timestamp": timestamp
            })
        
        # Token usage
        if "token_usage" in metrics_data:
            self.token_usage_history.append({
                "component": component_name,
                "value": metrics_data["token_usage"],
                "timestamp": timestamp
            })
    
    async def _cleanup_old_metrics(self, component_name: str) -> None:
        """Clean up old metrics to prevent memory bloat"""
        cutoff_time = datetime.utcnow() - timedelta(hours=24)  # Keep 24 hours
        
        # Clean up component metrics
        if component_name in self.component_metrics:
            old_keys = [
                timestamp for timestamp in self.component_metrics[component_name].keys()
                if timestamp < cutoff_time
            ]
            for old_key in old_keys:
                del self.component_metrics[component_name][old_key]
        
        # Clean up performance metrics
        if component_name in self.performance_metrics:
            for metric_type in self.performance_metrics[component_name]:
                self.performance_metrics[component_name][metric_type] = [
                    entry for entry in self.performance_metrics[component_name][metric_type]
                    if entry["timestamp"] > cutoff_time
                ]
        
        # Clean up quality metrics
        if component_name in self.quality_metrics:
            for metric_type in self.quality_metrics[component_name]:
                self.quality_metrics[component_name][metric_type] = [
                    entry for entry in self.quality_metrics[component_name][metric_type]
                    if entry["timestamp"] > cutoff_time
                ]
        
        # Clean up error metrics
        if component_name in self.error_metrics:
            for metric_type in self.error_metrics[component_name]:
                self.error_metrics[component_name][metric_type] = [
                    entry for entry in self.error_metrics[component_name][metric_type]
                    if entry["timestamp"] > cutoff_time
                ]
    
    @log_execution_time
    async def get_component_performance_summary(
        self,
        component_name: str,
        time_window: str = "1hour"
    ) -> Dict[str, Any]:
        """Get performance summary for a specific component"""
        if component_name not in self.performance_metrics:
            return {"error": f"No performance metrics for {component_name}"}
        
        start_time = datetime.utcnow() - timedelta(seconds=self.aggregation_windows.get(time_window, 3600))
        
        # Aggregate performance metrics
        perf_summary = await self._aggregate_performance_metrics(component_name, start_time)
        
        # Aggregate quality metrics
        quality_summary = await self._aggregate_quality_metrics(component_name, start_time)
        
        # Aggregate error metrics
        error_summary = await self._aggregate_error_metrics(component_name, start_time)
        
        return {
            "component_name": component_name,
            "time_window": time_window,
            "timestamp": datetime.utcnow(),
            "performance": perf_summary,
            "quality": quality_summary,
            "errors": error_summary
        }
    
    async def _aggregate_performance_metrics(
        self,
        component_name: str,
        start_time: datetime
    ) -> Dict[str, Any]:
        """Aggregate performance metrics for a time period"""
        perf_metrics = self.performance_metrics[component_name]
        summary = {}
        
        for metric_type, entries in perf_metrics.items():
            recent_entries = [
                entry for entry in entries
                if entry["timestamp"] > start_time
            ]
            
            if recent_entries:
                values = [entry["value"] for entry in recent_entries]
                summary[metric_type] = {
                    "count": len(values),
                    "average": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "std_dev": statistics.stdev(values) if len(values) > 1 else 0.0,
                    "latest": values[-1] if values else 0.0
                }
        
        return summary
    
    async def _aggregate_quality_metrics(
        self,
        component_name: str,
        start_time: datetime
    ) -> Dict[str, Any]:
        """Aggregate quality metrics for a time period"""
        quality_metrics = self.quality_metrics[component_name]
        summary = {}
        
        for metric_type, entries in quality_metrics.items():
            recent_entries = [
                entry for entry in entries
                if entry["timestamp"] > start_time
            ]
            
            if recent_entries:
                values = [entry["value"] for entry in recent_entries]
                summary[metric_type] = {
                    "count": len(values),
                    "average": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "std_dev": statistics.stdev(values) if len(values) > 1 else 0.0,
                    "latest": values[-1] if values else 0.0
                }
        
        return summary
    
    async def _aggregate_error_metrics(
        self,
        component_name: str,
        start_time: datetime
    ) -> Dict[str, Any]:
        """Aggregate error metrics for a time period"""
        error_metrics = self.error_metrics[component_name]
        summary = {}
        
        for metric_type, entries in error_metrics.items():
            recent_entries = [
                entry for entry in entries
                if entry["timestamp"] > start_time
            ]
            
            if recent_entries:
                values = [entry["value"] for entry in recent_entries]
                summary[metric_type] = {
                    "count": len(values),
                    "average": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "std_dev": statistics.stdev(values) if len(values) > 1 else 0.0,
                    "latest": values[-1] if values else 0.0
                }
        
        return summary
    
    async def get_system_performance_summary(self, time_window: str = "1hour") -> Dict[str, Any]:
        """Get system-wide performance summary"""
        start_time = datetime.utcnow() - timedelta(seconds=self.aggregation_windows.get(time_window, 3600))
        
        system_summary = {
            "time_window": time_window,
            "timestamp": datetime.utcnow(),
            "components": {},
            "system_wide": {}
        }
        
        # Collect component summaries
        for component_name in self.performance_metrics.keys():
            component_summary = await self.get_component_performance_summary(component_name, time_window)
            if "error" not in component_summary:
                system_summary["components"][component_name] = component_summary
        
        # Calculate system-wide metrics
        system_summary["system_wide"] = await self._calculate_system_wide_metrics(start_time)
        
        return system_summary
    
    async def _calculate_system_wide_metrics(self, start_time: datetime) -> Dict[str, Any]:
        """Calculate system-wide aggregated metrics"""
        # Aggregate response times across all components
        recent_response_times = [
            entry for entry in self.response_time_history
            if entry["timestamp"] > start_time
        ]
        
        # Aggregate quality scores across all components
        recent_quality_scores = [
            entry for entry in self.quality_score_history
            if entry["timestamp"] > start_time
        ]
        
        # Aggregate error rates across all components
        recent_error_rates = [
            entry for entry in self.error_rate_history
            if entry["timestamp"] > start_time
        ]
        
        # Aggregate token usage across all components
        recent_token_usage = [
            entry for entry in self.token_usage_history
            if entry["timestamp"] > start_time
        ]
        
        system_metrics = {}
        
        # Response time metrics
        if recent_response_times:
            response_times = [entry["value"] for entry in recent_response_times]
            system_metrics["response_time"] = {
                "count": len(response_times),
                "average": sum(response_times) / len(response_times),
                "min": min(response_times),
                "max": max(response_times),
                "std_dev": statistics.stdev(response_times) if len(response_times) > 1 else 0.0
            }
        
        # Quality score metrics
        if recent_quality_scores:
            quality_scores = [entry["value"] for entry in recent_quality_scores]
            system_metrics["quality_score"] = {
                "count": len(quality_scores),
                "average": sum(quality_scores) / len(quality_scores),
                "min": min(quality_scores),
                "max": max(quality_scores),
                "std_dev": statistics.stdev(quality_scores) if len(quality_scores) > 1 else 0.0
            }
        
        # Error rate metrics
        if recent_error_rates:
            error_rates = [entry["value"] for entry in recent_error_rates]
            system_metrics["error_rate"] = {
                "count": len(error_rates),
                "average": sum(error_rates) / len(error_rates),
                "min": min(error_rates),
                "max": max(error_rates),
                "std_dev": statistics.stdev(error_rates) if len(error_rates) > 1 else 0.0
            }
        
        # Token usage metrics
        if recent_token_usage:
            token_usage = [entry["value"] for entry in recent_token_usage]
            system_metrics["token_usage"] = {
                "count": len(token_usage),
                "average": sum(token_usage) / len(token_usage),
                "min": min(token_usage),
                "max": max(token_usage),
                "std_dev": statistics.stdev(token_usage) if len(token_usage) > 1 else 0.0
            }
        
        return system_metrics
    
    async def get_trending_metrics(
        self,
        metric_type: str,
        component_name: Optional[str] = None,
        hours: int = 24
    ) -> Dict[str, Any]:
        """Get trending metrics for a specific type over time"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Select appropriate history based on metric type
        if metric_type == "response_time":
            history = self.response_time_history
        elif metric_type == "quality_score":
            history = self.quality_score_history
        elif metric_type == "error_rate":
            history = self.error_rate_history
        elif metric_type == "token_usage":
            history = self.token_usage_history
        else:
            return {"error": f"Unknown metric type: {metric_type}"}
        
        # Filter recent data
        recent_data = [
            entry for entry in history
            if entry["timestamp"] > start_time
        ]
        
        if component_name:
            recent_data = [
                entry for entry in recent_data
                if entry["component"] == component_name
            ]
        
        if not recent_data:
            return {"message": f"No {metric_type} data in last {hours} hours"}
        
        # Group by time intervals (hourly buckets)
        hourly_buckets = defaultdict(list)
        for entry in recent_data:
            hour_key = entry["timestamp"].replace(minute=0, second=0, microsecond=0)
            hourly_buckets[hour_key].append(entry["value"])
        
        # Calculate hourly averages
        hourly_trends = []
        for hour, values in sorted(hourly_buckets.items()):
            hourly_trends.append({
                "timestamp": hour,
                "average": sum(values) / len(values),
                "count": len(values),
                "min": min(values),
                "max": max(values)
            })
        
        return {
            "metric_type": metric_type,
            "component_name": component_name,
            "time_period_hours": hours,
            "hourly_trends": hourly_trends,
            "overall_stats": {
                "total_measurements": len(recent_data),
                "overall_average": sum(entry["value"] for entry in recent_data) / len(recent_data),
                "trend_direction": self._calculate_trend_direction(hourly_trends)
            }
        }
    
    def _calculate_trend_direction(self, hourly_trends: List[Dict[str, Any]]) -> str:
        """Calculate overall trend direction from hourly data"""
        if len(hourly_trends) < 2:
            return "insufficient_data"
        
        # Calculate slope between first and last hour
        first_avg = hourly_trends[0]["average"]
        last_avg = hourly_trends[-1]["average"]
        
        if last_avg > first_avg + 0.1:
            return "improving"
        elif last_avg < first_avg - 0.1:
            return "declining"
        else:
            return "stable"
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the metrics collector itself"""
        if not self.collection_times:
            return {
                "avg_collection_time_ms": 0.0,
                "avg_aggregation_time_ms": 0.0,
                "total_metrics_collected": 0
            }
        
        return {
            "avg_collection_time_ms": sum(self.collection_times) / len(self.collection_times),
            "min_collection_time_ms": min(self.collection_times),
            "max_collection_time_ms": max(self.collection_times),
            "avg_aggregation_time_ms": sum(self.aggregation_times) / len(self.aggregation_times) if self.aggregation_times else 0.0,
            "total_metrics_collected": len(self.collection_times),
            "active_components": len(self.component_metrics),
            "time_series_data_points": len(self.response_time_history)
        }
    
    async def cleanup_old_data(self, max_age_hours: int = 24) -> Dict[str, int]:
        """Clean up old metrics data"""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        cleanup_stats = {
            "components_cleaned": 0,
            "metrics_entries_removed": 0,
            "time_series_entries_removed": 0
        }
        
        # Clean up component metrics
        for component_name in list(self.component_metrics.keys()):
            old_keys = [
                timestamp for timestamp in self.component_metrics[component_name].keys()
                if timestamp < cutoff_time
            ]
            for old_key in old_keys:
                del self.component_metrics[component_name][old_key]
                cleanup_stats["metrics_entries_removed"] += 1
            
            if not self.component_metrics[component_name]:
                del self.component_metrics[component_name]
                cleanup_stats["components_cleaned"] += 1
        
        # Clean up time series data
        original_response_count = len(self.response_time_history)
        self.response_time_history = deque(
            [entry for entry in self.response_time_history if entry["timestamp"] > cutoff_time],
            maxlen=1000
        )
        cleanup_stats["time_series_entries_removed"] += original_response_count - len(self.response_time_history)
        
        original_quality_count = len(self.quality_score_history)
        self.quality_score_history = deque(
            [entry for entry in self.quality_score_history if entry["timestamp"] > cutoff_time],
            maxlen=1000
        )
        cleanup_stats["time_series_entries_removed"] += original_quality_count - len(self.quality_score_history)
        
        original_error_count = len(self.error_rate_history)
        self.error_rate_history = deque(
            [entry for entry in self.error_rate_history if entry["timestamp"] > cutoff_time],
            maxlen=1000
        )
        cleanup_stats["time_series_entries_removed"] += original_error_count - len(self.error_rate_history)
        
        original_token_count = len(self.token_usage_history)
        self.token_usage_history = deque(
            [entry for entry in self.token_usage_history if entry["timestamp"] > cutoff_time],
            maxlen=1000
        )
        cleanup_stats["time_series_entries_removed"] += original_token_count - len(self.token_usage_history)
        
        if any(cleanup_stats.values()):
            self.logger.info(f"Cleaned up old metrics data: {cleanup_stats}")
        
        return cleanup_stats
