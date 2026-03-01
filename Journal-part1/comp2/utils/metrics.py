"""
Performance metrics and monitoring utilities for Component 2: RL Emotion Model
Tracks system performance, model accuracy, and user satisfaction metrics
"""

import time
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from collections import defaultdict, deque
from dataclasses import dataclass, field
import numpy as np
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class TimingMetric:
    """Individual timing measurement"""
    operation: str
    duration_ms: float
    timestamp: datetime
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AccuracyMetric:
    """Model accuracy measurement"""
    metric_type: str  # 'emotion_accuracy', 'reward_prediction', etc.
    value: float
    baseline_value: float
    improvement: float
    timestamp: datetime
    user_id: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemMetric:
    """System resource measurement"""
    cpu_percent: float
    memory_mb: float
    gpu_memory_mb: Optional[float]
    disk_usage_mb: float
    timestamp: datetime


@dataclass
class UserSatisfactionMetric:
    """User satisfaction measurement"""
    user_id: str
    satisfaction_score: float  # 0-10 scale
    feedback_type: str  # 'explicit', 'implicit', 'behavioral'
    timestamp: datetime
    context: Dict[str, Any] = field(default_factory=dict)


class MetricsCollector:
    """
    Central metrics collection and aggregation system
    Thread-safe collection of various performance metrics
    """
    
    def __init__(self, max_history_size: int = 10000):
        """
        Initialize metrics collector
        
        Args:
            max_history_size: Maximum number of historical metrics to keep
        """
        self.max_history_size = max_history_size
        self.lock = threading.RLock()
        
        # Metric storage
        self.timing_metrics: deque = deque(maxlen=max_history_size)
        self.accuracy_metrics: deque = deque(maxlen=max_history_size)
        self.system_metrics: deque = deque(maxlen=max_history_size)
        self.satisfaction_metrics: deque = deque(maxlen=max_history_size)
        
        # Aggregated statistics
        self.timing_stats: Dict[str, Dict[str, float]] = defaultdict(lambda: {
            'count': 0, 'total_ms': 0.0, 'min_ms': float('inf'), 'max_ms': 0.0,
            'recent_avg_ms': 0.0, 'p95_ms': 0.0
        })
        
        self.accuracy_stats: Dict[str, Dict[str, float]] = defaultdict(lambda: {
            'current': 0.0, 'baseline': 0.0, 'improvement': 0.0, 'count': 0
        })
        
        # Background monitoring
        self.monitoring_active = False
        self.monitoring_thread: Optional[threading.Thread] = None
        self.monitoring_interval = 30  # seconds
    
    def record_timing(
        self, 
        operation: str, 
        duration_ms: float, 
        **context
    ):
        """
        Record timing metric
        
        Args:
            operation: Operation name
            duration_ms: Duration in milliseconds
            **context: Additional context
        """
        with self.lock:
            metric = TimingMetric(
                operation=operation,
                duration_ms=duration_ms,
                timestamp=datetime.now(),
                context=context
            )
            
            self.timing_metrics.append(metric)
            
            # Update aggregated stats
            stats = self.timing_stats[operation]
            stats['count'] += 1
            stats['total_ms'] += duration_ms
            stats['min_ms'] = min(stats['min_ms'], duration_ms)
            stats['max_ms'] = max(stats['max_ms'], duration_ms)
            
            # Calculate recent average (last 100 operations)
            recent_metrics = [m.duration_ms for m in self.timing_metrics 
                            if m.operation == operation][-100:]
            if recent_metrics:
                stats['recent_avg_ms'] = np.mean(recent_metrics)
                stats['p95_ms'] = np.percentile(recent_metrics, 95)
    
    def record_accuracy(
        self,
        metric_type: str,
        value: float,
        baseline_value: float,
        user_id: Optional[str] = None,
        **context
    ):
        """
        Record accuracy metric
        
        Args:
            metric_type: Type of accuracy metric
            value: Current accuracy value
            baseline_value: Baseline comparison value
            user_id: User identifier (optional)
            **context: Additional context
        """
        improvement = value - baseline_value
        
        with self.lock:
            metric = AccuracyMetric(
                metric_type=metric_type,
                value=value,
                baseline_value=baseline_value,
                improvement=improvement,
                timestamp=datetime.now(),
                user_id=user_id,
                context=context
            )
            
            self.accuracy_metrics.append(metric)
            
            # Update aggregated stats
            stats = self.accuracy_stats[metric_type]
            stats['current'] = value
            stats['baseline'] = baseline_value
            stats['improvement'] = improvement
            stats['count'] += 1
    
    def record_system_metrics(self):
        """Record current system resource usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            memory_mb = memory.used / (1024 * 1024)
            
            disk_usage = psutil.disk_usage('/')
            disk_mb = disk_usage.used / (1024 * 1024)
            
            # GPU memory (if available)
            gpu_memory_mb = None
            try:
                import torch
                if torch.cuda.is_available():
                    gpu_memory_mb = torch.cuda.memory_allocated() / (1024 * 1024)
            except ImportError:
                pass
            
            with self.lock:
                metric = SystemMetric(
                    cpu_percent=cpu_percent,
                    memory_mb=memory_mb,
                    gpu_memory_mb=gpu_memory_mb,
                    disk_usage_mb=disk_mb,
                    timestamp=datetime.now()
                )
                
                self.system_metrics.append(metric)
                
        except Exception as e:
            logger.warning(f"Failed to record system metrics: {e}")
    
    def record_user_satisfaction(
        self,
        user_id: str,
        satisfaction_score: float,
        feedback_type: str = 'explicit',
        **context
    ):
        """
        Record user satisfaction metric
        
        Args:
            user_id: User identifier
            satisfaction_score: Satisfaction score 0-10
            feedback_type: Type of feedback
            **context: Additional context
        """
        with self.lock:
            metric = UserSatisfactionMetric(
                user_id=user_id,
                satisfaction_score=satisfaction_score,
                feedback_type=feedback_type,
                timestamp=datetime.now(),
                context=context
            )
            
            self.satisfaction_metrics.append(metric)
    
    def get_timing_stats(self, operation: Optional[str] = None) -> Dict[str, Any]:
        """
        Get timing statistics
        
        Args:
            operation: Specific operation (None for all)
            
        Returns:
            Dictionary with timing statistics
        """
        with self.lock:
            if operation:
                if operation in self.timing_stats:
                    stats = self.timing_stats[operation].copy()
                    if stats['count'] > 0:
                        stats['avg_ms'] = stats['total_ms'] / stats['count']
                    return {operation: stats}
                else:
                    return {}
            else:
                result = {}
                for op, stats in self.timing_stats.items():
                    op_stats = stats.copy()
                    if op_stats['count'] > 0:
                        op_stats['avg_ms'] = op_stats['total_ms'] / op_stats['count']
                    result[op] = op_stats
                return result
    
    def get_accuracy_stats(self, metric_type: Optional[str] = None) -> Dict[str, Any]:
        """Get accuracy statistics"""
        with self.lock:
            if metric_type:
                return {metric_type: self.accuracy_stats.get(metric_type, {})}
            else:
                return dict(self.accuracy_stats)
    
    def get_system_stats(self, window_minutes: int = 60) -> Dict[str, float]:
        """
        Get system resource statistics
        
        Args:
            window_minutes: Time window for statistics
            
        Returns:
            Dictionary with system statistics
        """
        cutoff_time = datetime.now() - timedelta(minutes=window_minutes)
        
        with self.lock:
            recent_metrics = [m for m in self.system_metrics if m.timestamp >= cutoff_time]
            
            if not recent_metrics:
                return {}
            
            cpu_values = [m.cpu_percent for m in recent_metrics]
            memory_values = [m.memory_mb for m in recent_metrics]
            gpu_values = [m.gpu_memory_mb for m in recent_metrics if m.gpu_memory_mb is not None]
            
            stats = {
                'avg_cpu_percent': np.mean(cpu_values),
                'max_cpu_percent': np.max(cpu_values),
                'avg_memory_mb': np.mean(memory_values),
                'max_memory_mb': np.max(memory_values),
                'sample_count': len(recent_metrics)
            }
            
            if gpu_values:
                stats['avg_gpu_memory_mb'] = np.mean(gpu_values)
                stats['max_gpu_memory_mb'] = np.max(gpu_values)
            
            return stats
    
    def get_user_satisfaction_stats(
        self, 
        user_id: Optional[str] = None,
        window_days: int = 30
    ) -> Dict[str, float]:
        """
        Get user satisfaction statistics
        
        Args:
            user_id: Specific user (None for all users)
            window_days: Time window in days
            
        Returns:
            Dictionary with satisfaction statistics
        """
        cutoff_time = datetime.now() - timedelta(days=window_days)
        
        with self.lock:
            metrics = [m for m in self.satisfaction_metrics if m.timestamp >= cutoff_time]
            
            if user_id:
                metrics = [m for m in metrics if m.user_id == user_id]
            
            if not metrics:
                return {}
            
            scores = [m.satisfaction_score for m in metrics]
            
            return {
                'avg_satisfaction': np.mean(scores),
                'min_satisfaction': np.min(scores),
                'max_satisfaction': np.max(scores),
                'satisfaction_std': np.std(scores),
                'feedback_count': len(scores),
                'users_count': len(set(m.user_id for m in metrics)) if not user_id else 1
            }
    
    def start_monitoring(self):
        """Start background system monitoring"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        logger.info("Started background metrics monitoring")
    
    def stop_monitoring(self):
        """Stop background system monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("Stopped background metrics monitoring")
    
    def _monitoring_loop(self):
        """Background monitoring loop"""
        while self.monitoring_active:
            try:
                self.record_system_metrics()
                time.sleep(self.monitoring_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.monitoring_interval)
    
    def export_metrics(self, filepath: Union[str, Path], format: str = 'json'):
        """
        Export metrics to file
        
        Args:
            filepath: Output file path
            format: Export format ('json' or 'csv')
        """
        filepath = Path(filepath)
        
        with self.lock:
            data = {
                'timing_stats': dict(self.timing_stats),
                'accuracy_stats': dict(self.accuracy_stats),
                'export_timestamp': datetime.now().isoformat(),
                'metrics_count': {
                    'timing': len(self.timing_metrics),
                    'accuracy': len(self.accuracy_metrics),
                    'system': len(self.system_metrics),
                    'satisfaction': len(self.satisfaction_metrics)
                }
            }
            
            if format.lower() == 'json':
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
            else:
                raise ValueError(f"Unsupported export format: {format}")
        
        logger.info(f"Exported metrics to {filepath}")
    
    def clear_metrics(self, metric_type: Optional[str] = None):
        """
        Clear metrics history
        
        Args:
            metric_type: Type of metrics to clear (None for all)
        """
        with self.lock:
            if metric_type is None:
                self.timing_metrics.clear()
                self.accuracy_metrics.clear()
                self.system_metrics.clear()
                self.satisfaction_metrics.clear()
                self.timing_stats.clear()
                self.accuracy_stats.clear()
            elif metric_type == 'timing':
                self.timing_metrics.clear()
                self.timing_stats.clear()
            elif metric_type == 'accuracy':
                self.accuracy_metrics.clear()
                self.accuracy_stats.clear()
            elif metric_type == 'system':
                self.system_metrics.clear()
            elif metric_type == 'satisfaction':
                self.satisfaction_metrics.clear()
        
        logger.info(f"Cleared {metric_type or 'all'} metrics")


class PerformanceMonitor:
    """
    High-level performance monitoring interface
    Provides easy-to-use methods for common monitoring tasks
    """
    
    def __init__(self, collector: Optional[MetricsCollector] = None):
        """
        Initialize performance monitor
        
        Args:
            collector: MetricsCollector instance (creates new if None)
        """
        self.collector = collector or MetricsCollector()
        self.context_timers: Dict[str, float] = {}
    
    def start_timer(self, operation: str) -> str:
        """
        Start timing an operation
        
        Args:
            operation: Operation name
            
        Returns:
            Timer ID for stopping
        """
        timer_id = f"{operation}_{id(threading.current_thread())}"
        self.context_timers[timer_id] = time.time()
        return timer_id
    
    def stop_timer(self, timer_id: str, **context) -> float:
        """
        Stop timer and record metric
        
        Args:
            timer_id: Timer ID from start_timer
            **context: Additional context
            
        Returns:
            Duration in milliseconds
        """
        if timer_id not in self.context_timers:
            logger.warning(f"Timer {timer_id} not found")
            return 0.0
        
        start_time = self.context_timers.pop(timer_id)
        duration_ms = (time.time() - start_time) * 1000
        
        # Extract operation name from timer_id
        operation = timer_id.rsplit('_', 1)[0]
        self.collector.record_timing(operation, duration_ms, **context)
        
        return duration_ms
    
    def time_operation(self, operation: str):
        """
        Context manager for timing operations
        
        Args:
            operation: Operation name
        """
        from contextlib import contextmanager
        
        @contextmanager
        def timer_context(**context):
            timer_id = self.start_timer(operation)
            try:
                yield
            finally:
                self.stop_timer(timer_id, **context)
        
        return timer_context
    
    def record_model_accuracy(
        self,
        model_name: str,
        accuracy: float,
        baseline_accuracy: float,
        user_id: Optional[str] = None,
        **context
    ):
        """
        Record model accuracy metric
        
        Args:
            model_name: Name of the model
            accuracy: Current accuracy
            baseline_accuracy: Baseline accuracy for comparison
            user_id: User identifier (optional)
            **context: Additional context
        """
        self.collector.record_accuracy(
            metric_type=f"{model_name}_accuracy",
            value=accuracy,
            baseline_value=baseline_accuracy,
            user_id=user_id,
            **context
        )
    
    def record_user_feedback(
        self,
        user_id: str,
        feedback_quality: float,
        feedback_type: str = 'explicit'
    ):
        """
        Record user feedback as satisfaction metric
        
        Args:
            user_id: User identifier
            feedback_quality: Quality score 0-10
            feedback_type: Type of feedback
        """
        self.collector.record_user_satisfaction(
            user_id=user_id,
            satisfaction_score=feedback_quality,
            feedback_type=feedback_type
        )
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        return {
            'timing_stats': self.collector.get_timing_stats(),
            'accuracy_stats': self.collector.get_accuracy_stats(),
            'system_stats': self.collector.get_system_stats(window_minutes=60),
            'satisfaction_stats': self.collector.get_user_satisfaction_stats(window_days=7),
            'summary_timestamp': datetime.now().isoformat()
        }
    
    def start_monitoring(self):
        """Start background monitoring"""
        self.collector.start_monitoring()
    
    def stop_monitoring(self):
        """Stop background monitoring"""
        self.collector.stop_monitoring()


# Global performance monitor instance
_performance_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """
    Get global performance monitor instance
    
    Returns:
        PerformanceMonitor instance
    """
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


def timing_context(operation: str, **context):
    """
    Convenience function for timing context manager
    
    Args:
        operation: Operation name
        **context: Additional context
        
    Usage:
        with timing_context('model_training', batch_size=32):
            train_model()
    """
    monitor = get_performance_monitor()
    return monitor.time_operation(operation)(**context)


def record_timing(operation: str, duration_ms: float, **context):
    """
    Convenience function for recording timing
    
    Args:
        operation: Operation name
        duration_ms: Duration in milliseconds
        **context: Additional context
    """
    monitor = get_performance_monitor()
    monitor.collector.record_timing(operation, duration_ms, **context)


def record_accuracy(model_name: str, accuracy: float, baseline: float, **context):
    """
    Convenience function for recording accuracy
    
    Args:
        model_name: Model name
        accuracy: Current accuracy
        baseline: Baseline accuracy
        **context: Additional context
    """
    monitor = get_performance_monitor()
    monitor.record_model_accuracy(model_name, accuracy, baseline, **context)


def get_metrics_summary() -> Dict[str, Any]:
    """
    Get comprehensive metrics summary
    
    Returns:
        Dictionary with all metrics
    """
    monitor = get_performance_monitor()
    return monitor.get_performance_summary()