"""
Performance metrics and monitoring.
"""
import psutil
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import deque
from dataclasses import dataclass, asdict

from app.config import get_config
from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class MemoryMetrics:
    """Memory metrics data class."""
    timestamp: datetime
    rss_mb: float  # Resident Set Size
    vms_mb: float  # Virtual Memory Size
    percent: float  # Memory usage percentage
    available_mb: float
    used_mb: float


@dataclass
class CPUMetrics:
    """CPU metrics data class."""
    timestamp: datetime
    percent: float
    cores: int
    load_avg: Optional[float] = None


@dataclass
class SystemMetrics:
    """System metrics data class."""
    timestamp: datetime
    memory: MemoryMetrics
    cpu: CPUMetrics


class MetricsCollector:
    """Collector for system performance metrics."""
    
    def __init__(self):
        """Initialize metrics collector."""
        self.config = get_config()
        self.enabled = self.config.metrics.enabled
        self.monitoring_interval = self.config.metrics.memory_monitoring_interval_seconds
        self.leak_detection = self.config.metrics.memory_leak_detection
        self.retention_days = self.config.metrics.historical_data_retention_days
        
        # Storage for historical data
        self.memory_history: deque = deque(maxlen=self._calculate_max_samples())
        self.cpu_history: deque = deque(maxlen=self._calculate_max_samples())
        
        # Leak detection
        self.baseline_memory: Optional[float] = None
        self.leak_threshold_percent = 20.0  # 20% increase indicates potential leak
        
        # Monitoring thread
        self.monitoring_thread: Optional[threading.Thread] = None
        self.stop_monitoring = threading.Event()
        
        if self.enabled:
            self.start_monitoring()
    
    def _calculate_max_samples(self) -> int:
        """Calculate maximum number of samples to keep."""
        # Keep samples for retention_days with monitoring_interval
        samples_per_day = (24 * 60 * 60) / self.monitoring_interval
        return int(samples_per_day * self.retention_days)
    
    def collect_memory_metrics(self) -> MemoryMetrics:
        """
        Collect current memory metrics.
        
        Returns:
            MemoryMetrics instance.
        """
        process = psutil.Process()
        memory_info = process.memory_info()
        system_memory = psutil.virtual_memory()
        
        return MemoryMetrics(
            timestamp=datetime.now(),
            rss_mb=memory_info.rss / (1024 * 1024),
            vms_mb=memory_info.vms / (1024 * 1024),
            percent=process.memory_percent(),
            available_mb=system_memory.available / (1024 * 1024),
            used_mb=system_memory.used / (1024 * 1024),
        )
    
    def collect_cpu_metrics(self) -> CPUMetrics:
        """
        Collect current CPU metrics.
        
        Returns:
            CPUMetrics instance.
        """
        process = psutil.Process()
        cpu_percent = process.cpu_percent(interval=0.1)
        cpu_count = psutil.cpu_count()
        
        # Get load average if available (Unix only)
        try:
            load_avg = psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else None
        except AttributeError:
            load_avg = None
        
        return CPUMetrics(
            timestamp=datetime.now(),
            percent=cpu_percent,
            cores=cpu_count,
            load_avg=load_avg,
        )
    
    def collect_metrics(self) -> SystemMetrics:
        """
        Collect all system metrics.
        
        Returns:
            SystemMetrics instance.
        """
        memory = self.collect_memory_metrics()
        cpu = self.collect_cpu_metrics()
        
        return SystemMetrics(
            timestamp=datetime.now(),
            memory=memory,
            cpu=cpu,
        )
    
    def _monitoring_loop(self):
        """Background monitoring loop."""
        logger.info("Metrics monitoring started")
        
        while not self.stop_monitoring.is_set():
            try:
                metrics = self.collect_metrics()
                
                # Store historical data
                self.memory_history.append(metrics.memory)
                self.cpu_history.append(metrics.cpu)
                
                # Check for memory leak
                if self.leak_detection:
                    self._check_memory_leak(metrics.memory)
                
                # Log metrics at DEBUG level
                logger.debug(
                    f"Metrics - Memory: {metrics.memory.rss_mb:.2f}MB RSS, "
                    f"{metrics.memory.percent:.1f}% | "
                    f"CPU: {metrics.cpu.percent:.1f}%"
                )
                
            except Exception as e:
                logger.error(f"Error collecting metrics: {e}", exc_info=True)
            
            # Wait for next interval
            self.stop_monitoring.wait(self.monitoring_interval)
        
        logger.info("Metrics monitoring stopped")
    
    def _check_memory_leak(self, memory: MemoryMetrics):
        """
        Check for potential memory leak.
        
        Args:
            memory: Current memory metrics.
        """
        if self.baseline_memory is None:
            # Set baseline after a few samples
            if len(self.memory_history) >= 5:
                self.baseline_memory = memory.rss_mb
            return
        
        # Check if memory increased significantly
        increase_percent = ((memory.rss_mb - self.baseline_memory) / self.baseline_memory) * 100
        
        if increase_percent > self.leak_threshold_percent:
            logger.warning(
                f"Potential memory leak detected: RSS increased by {increase_percent:.1f}% "
                f"({self.baseline_memory:.2f}MB -> {memory.rss_mb:.2f}MB)"
            )
            
            # Reset baseline to current value
            self.baseline_memory = memory.rss_mb
    
    def start_monitoring(self):
        """Start background monitoring thread."""
        if not self.enabled:
            return
        
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            logger.warning("Monitoring thread already running")
            return
        
        self.stop_monitoring.clear()
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True,
            name="MetricsCollector"
        )
        self.monitoring_thread.start()
        logger.info("Metrics monitoring thread started")
    
    def stop(self):
        """Stop monitoring."""
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.stop_monitoring.set()
            self.monitoring_thread.join(timeout=5)
            logger.info("Metrics monitoring stopped")
    
    def get_current_metrics(self) -> SystemMetrics:
        """
        Get current system metrics.
        
        Returns:
            SystemMetrics instance.
        """
        return self.collect_metrics()
    
    def get_memory_history(
        self,
        hours: Optional[int] = None
    ) -> List[MemoryMetrics]:
        """
        Get memory history.
        
        Args:
            hours: Number of hours to retrieve. If None, returns all.
            
        Returns:
            List of MemoryMetrics.
        """
        if hours is None:
            return list(self.memory_history)
        
        cutoff = datetime.now() - timedelta(hours=hours)
        return [
            m for m in self.memory_history
            if m.timestamp >= cutoff
        ]
    
    def get_cpu_history(
        self,
        hours: Optional[int] = None
    ) -> List[CPUMetrics]:
        """
        Get CPU history.
        
        Args:
            hours: Number of hours to retrieve. If None, returns all.
            
        Returns:
            List of CPUMetrics.
        """
        if hours is None:
            return list(self.cpu_history)
        
        cutoff = datetime.now() - timedelta(hours=hours)
        return [
            c for c in self.cpu_history
            if c.timestamp >= cutoff
        ]
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Get metrics summary.
        
        Returns:
            Dictionary with metrics summary.
        """
        if not self.memory_history or not self.cpu_history:
            return {
                "status": "no_data",
                "message": "No metrics collected yet"
            }
        
        latest_memory = self.memory_history[-1]
        latest_cpu = self.cpu_history[-1]
        
        # Calculate averages
        avg_memory = sum(m.rss_mb for m in self.memory_history) / len(self.memory_history)
        avg_cpu = sum(c.percent for c in self.cpu_history) / len(self.cpu_history)
        
        return {
            "status": "ok",
            "current": {
                "memory": {
                    "rss_mb": latest_memory.rss_mb,
                    "percent": latest_memory.percent,
                    "vms_mb": latest_memory.vms_mb,
                },
                "cpu": {
                    "percent": latest_cpu.percent,
                    "cores": latest_cpu.cores,
                },
            },
            "averages": {
                "memory_mb": avg_memory,
                "cpu_percent": avg_cpu,
            },
            "samples": {
                "memory": len(self.memory_history),
                "cpu": len(self.cpu_history),
            },
        }


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """
    Get global metrics collector instance.
    
    Returns:
        MetricsCollector instance.
    """
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector

