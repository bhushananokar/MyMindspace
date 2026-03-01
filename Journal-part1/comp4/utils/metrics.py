"""
Performance tracking and metrics for Component 4
"""

import time
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict, deque
import numpy as np
import logging

logger = logging.getLogger(__name__)

class PerformanceTracker:
    """
    Track performance metrics for Component 4 feature engineering
    """
    
    def __init__(self, window_size: int = 100):
        """
        Initialize performance tracker
        
        Args:
            window_size: Size of sliding window for metrics
        """
        self.window_size = window_size
        
        # Timing metrics
        self.processing_times = deque(maxlen=window_size)
        self.extraction_times = defaultdict(lambda: deque(maxlen=window_size))
        self.engineering_times = defaultdict(lambda: deque(maxlen=window_size))
        
        # Quality metrics
        self.quality_scores = deque(maxlen=window_size)
        self.completeness_scores = deque(maxlen=window_size)
        self.confidence_scores = deque(maxlen=window_size)
        
        # Error tracking
        self.error_counts = defaultdict(int)
        self.warning_counts = defaultdict(int)
        
        # System metrics
        self.memory_usage = deque(maxlen=window_size)
        self.cpu_usage = deque(maxlen=window_size)
        
        # Throughput metrics
        self.entries_processed = 0
        self.session_start_time = datetime.now()
        self.batch_sizes = deque(maxlen=window_size)
        
        # Feature-specific metrics
        self.feature_statistics = {
            'temporal': {'min': [], 'max': [], 'mean': [], 'std': []},
            'emotional': {'min': [], 'max': [], 'mean': [], 'std': []},
            'semantic': {'min': [], 'max': [], 'mean': [], 'std': []},
            'user': {'min': [], 'max': [], 'mean': [], 'std': []}
        }
    
    def record_processing_time(self, time_ms: float, component: str = 'total'):
        """Record processing time for a component"""
        if component == 'total':
            self.processing_times.append(time_ms)
        else:
            if 'extraction' in component:
                self.extraction_times[component].append(time_ms)
            elif 'engineering' in component:
                self.engineering_times[component].append(time_ms)
    
    def record_quality_metrics(
        self, 
        quality_score: float,
        completeness_score: float,
        confidence_score: float
    ):
        """Record quality metrics"""
        self.quality_scores.append(quality_score)
        self.completeness_scores.append(completeness_score)
        self.confidence_scores.append(confidence_score)
    
    def record_error(self, error_type: str, count: int = 1):
        """Record error occurrence"""
        self.error_counts[error_type] += count
    
    def record_warning(self, warning_type: str, count: int = 1):
        """Record warning occurrence"""
        self.warning_counts[warning_type] += count
    
    def record_system_metrics(self):
        """Record current system metrics"""
        try:
            # Memory usage
            memory_info = psutil.virtual_memory()
            self.memory_usage.append(memory_info.percent)
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=None)
            self.cpu_usage.append(cpu_percent)
            
        except Exception as e:
            logger.error(f"Error recording system metrics: {e}")
    
    def record_feature_statistics(self, features, feature_type: str):
        """Record feature vector statistics"""
        try:
            if hasattr(features, 'shape') and len(features) > 0:
                stats = self.feature_statistics[feature_type]
                stats['min'].append(float(np.min(features)))
                stats['max'].append(float(np.max(features)))
                stats['mean'].append(float(np.mean(features)))
                stats['std'].append(float(np.std(features)))
                
                # Keep only recent statistics
                for key in stats:
                    if len(stats[key]) > self.window_size:
                        stats[key] = stats[key][-self.window_size:]
                        
        except Exception as e:
            logger.error(f"Error recording feature statistics for {feature_type}: {e}")
    
    def record_batch_processing(self, batch_size: int, total_time_ms: float):
        """Record batch processing metrics"""
        self.batch_sizes.append(batch_size)
        self.entries_processed += batch_size
        
        # Calculate per-entry time
        if batch_size > 0:
            per_entry_time = total_time_ms / batch_size
            self.processing_times.append(per_entry_time)
    
    def get_timing_statistics(self) -> Dict[str, Any]:
        """Get timing performance statistics"""
        try:
            stats = {}
            
            # Overall processing times
            if self.processing_times:
                stats['total_processing'] = {
                    'count': len(self.processing_times),
                    'mean_ms': np.mean(self.processing_times),
                    'median_ms': np.median(self.processing_times),
                    'std_ms': np.std(self.processing_times),
                    'min_ms': np.min(self.processing_times),
                    'max_ms': np.max(self.processing_times),
                    'p95_ms': np.percentile(self.processing_times, 95),
                    'p99_ms': np.percentile(self.processing_times, 99)
                }
            
            # Extraction times by component
            stats['extraction_times'] = {}
            for component, times in self.extraction_times.items():
                if times:
                    stats['extraction_times'][component] = {
                        'count': len(times),
                        'mean_ms': np.mean(times),
                        'median_ms': np.median(times),
                        'std_ms': np.std(times)
                    }
            
            # Engineering times by component
            stats['engineering_times'] = {}
            for component, times in self.engineering_times.items():
                if times:
                    stats['engineering_times'][component] = {
                        'count': len(times),
                        'mean_ms': np.mean(times),
                        'median_ms': np.median(times),
                        'std_ms': np.std(times)
                    }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting timing statistics: {e}")
            return {'error': str(e)}
    
    def get_quality_statistics(self) -> Dict[str, Any]:
        """Get quality performance statistics"""
        try:
            stats = {}
            
            # Quality scores
            if self.quality_scores:
                stats['quality_scores'] = {
                    'count': len(self.quality_scores),
                    'mean': np.mean(self.quality_scores),
                    'median': np.median(self.quality_scores),
                    'std': np.std(self.quality_scores),
                    'min': np.min(self.quality_scores),
                    'max': np.max(self.quality_scores)
                }
            
            # Completeness scores
            if self.completeness_scores:
                stats['completeness_scores'] = {
                    'count': len(self.completeness_scores),
                    'mean': np.mean(self.completeness_scores),
                    'median': np.median(self.completeness_scores),
                    'std': np.std(self.completeness_scores)
                }
            
            # Confidence scores
            if self.confidence_scores:
                stats['confidence_scores'] = {
                    'count': len(self.confidence_scores),
                    'mean': np.mean(self.confidence_scores),
                    'median': np.median(self.confidence_scores),
                    'std': np.std(self.confidence_scores)
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting quality statistics: {e}")
            return {'error': str(e)}
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error and warning statistics"""
        try:
            total_processed = max(self.entries_processed, 1)
            
            stats = {
                'errors': dict(self.error_counts),
                'warnings': dict(self.warning_counts),
                'total_errors': sum(self.error_counts.values()),
                'total_warnings': sum(self.warning_counts.values()),
                'error_rate': sum(self.error_counts.values()) / total_processed,
                'warning_rate': sum(self.warning_counts.values()) / total_processed
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting error statistics: {e}")
            return {'error': str(e)}
    
    def get_throughput_statistics(self) -> Dict[str, Any]:
        """Get throughput performance statistics"""
        try:
            session_duration = (datetime.now() - self.session_start_time).total_seconds()
            
            stats = {
                'entries_processed': self.entries_processed,
                'session_duration_seconds': session_duration,
                'entries_per_second': self.entries_processed / max(session_duration, 1),
                'entries_per_minute': (self.entries_processed / max(session_duration, 1)) * 60,
                'entries_per_hour': (self.entries_processed / max(session_duration, 1)) * 3600
            }
            
            # Batch statistics
            if self.batch_sizes:
                stats['batch_statistics'] = {
                    'total_batches': len(self.batch_sizes),
                    'mean_batch_size': np.mean(self.batch_sizes),
                    'median_batch_size': np.median(self.batch_sizes),
                    'max_batch_size': np.max(self.batch_sizes),
                    'min_batch_size': np.min(self.batch_sizes)
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting throughput statistics: {e}")
            return {'error': str(e)}
    
    def get_system_statistics(self) -> Dict[str, Any]:
        """Get system resource statistics"""
        try:
            stats = {}
            
            # Memory usage
            if self.memory_usage:
                stats['memory_usage'] = {
                    'count': len(self.memory_usage),
                    'mean_percent': np.mean(self.memory_usage),
                    'max_percent': np.max(self.memory_usage),
                    'current_percent': self.memory_usage[-1] if self.memory_usage else 0
                }
            
            # CPU usage
            if self.cpu_usage:
                stats['cpu_usage'] = {
                    'count': len(self.cpu_usage),
                    'mean_percent': np.mean(self.cpu_usage),
                    'max_percent': np.max(self.cpu_usage),
                    'current_percent': self.cpu_usage[-1] if self.cpu_usage else 0
                }
            
            # Current system info
            try:
                memory_info = psutil.virtual_memory()
                stats['current_system'] = {
                    'total_memory_gb': memory_info.total / (1024**3),
                    'available_memory_gb': memory_info.available / (1024**3),
                    'memory_percent': memory_info.percent,
                    'cpu_count': psutil.cpu_count(),
                    'cpu_percent': psutil.cpu_percent(interval=None)
                }
            except Exception as e:
                stats['current_system'] = {'error': str(e)}
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting system statistics: {e}")
            return {'error': str(e)}
    
    def get_feature_statistics(self) -> Dict[str, Any]:
        """Get feature vector statistics"""
        try:
            stats = {}
            
            for feature_type, feature_stats in self.feature_statistics.items():
                if any(feature_stats.values()):
                    stats[feature_type] = {}
                    
                    for stat_name, values in feature_stats.items():
                        if values:
                            stats[feature_type][stat_name] = {
                                'count': len(values),
                                'mean': np.mean(values),
                                'std': np.std(values),
                                'min': np.min(values),
                                'max': np.max(values)
                            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting feature statistics: {e}")
            return {'error': str(e)}
    
    def get_comprehensive_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        try:
            report = {
                'summary': {
                    'entries_processed': self.entries_processed,
                    'session_duration_seconds': (datetime.now() - self.session_start_time).total_seconds(),
                    'total_errors': sum(self.error_counts.values()),
                    'total_warnings': sum(self.warning_counts.values()),
                    'window_size': self.window_size
                },
                'timing': self.get_timing_statistics(),
                'quality': self.get_quality_statistics(),
                'errors': self.get_error_statistics(),
                'throughput': self.get_throughput_statistics(),
                'system': self.get_system_statistics(),
                'features': self.get_feature_statistics(),
                'generated_at': datetime.now().isoformat()
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating comprehensive report: {e}")
            return {'error': str(e)}
    
    def reset_metrics(self):
        """Reset all metrics"""
        try:
            self.processing_times.clear()
            self.extraction_times.clear()
            self.engineering_times.clear()
            self.quality_scores.clear()
            self.completeness_scores.clear()
            self.confidence_scores.clear()
            self.error_counts.clear()
            self.warning_counts.clear()
            self.memory_usage.clear()
            self.cpu_usage.clear()
            self.batch_sizes.clear()
            
            self.entries_processed = 0
            self.session_start_time = datetime.now()
            
            for feature_type in self.feature_statistics:
                for stat_name in self.feature_statistics[feature_type]:
                    self.feature_statistics[feature_type][stat_name].clear()
            
            logger.info("Performance metrics reset")
            
        except Exception as e:
            logger.error(f"Error resetting metrics: {e}")
    
    def export_metrics(self, filepath: str, format: str = 'json'):
        """Export metrics to file"""
        try:
            report = self.get_comprehensive_report()
            
            if format.lower() == 'json':
                import json
                with open(filepath, 'w') as f:
                    json.dump(report, f, indent=2, default=str)
            elif format.lower() == 'yaml':
                import yaml
                with open(filepath, 'w') as f:
                    yaml.dump(report, f, default_flow_style=False, indent=2)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            logger.info(f"Metrics exported to {filepath}")
            
        except Exception as e:
            logger.error(f"Error exporting metrics to {filepath}: {e}")
            raise
