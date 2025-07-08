"""
Performance monitoring utilities for E2E tests.

This module provides tools to monitor and analyze performance metrics
during user story-based E2E tests.
"""

import asyncio
import time
import psutil
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Represents a single performance metric."""

    name: str
    value: float
    unit: str
    timestamp: datetime
    category: str = "general"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class APICallMetric:
    """Represents metrics for an API call."""

    endpoint: str
    method: str
    start_time: datetime
    end_time: Optional[datetime] = None
    response_time: Optional[float] = None
    status_code: Optional[int] = None
    response_size: Optional[int] = None
    error: Optional[str] = None


class PerformanceMonitor:
    """Monitor performance metrics during E2E tests."""

    def __init__(self, sample_interval: float = 1.0):
        self.sample_interval = sample_interval
        self.metrics: List[PerformanceMetric] = []
        self.api_calls: List[APICallMetric] = []
        self.monitoring = False
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self._monitoring_task: Optional[asyncio.Task] = None

    async def start_monitoring(self) -> None:
        """Start performance monitoring."""
        if self.monitoring:
            logger.warning("Performance monitoring is already running")
            return

        self.monitoring = True
        self.start_time = datetime.now()
        self.metrics.clear()
        self.api_calls.clear()

        # Start background monitoring task
        self._monitoring_task = asyncio.create_task(self._monitor_system_metrics())

        logger.info("Performance monitoring started")

    async def stop_monitoring(self) -> None:
        """Stop performance monitoring."""
        if not self.monitoring:
            logger.warning("Performance monitoring is not running")
            return

        self.monitoring = False
        self.end_time = datetime.now()

        # Stop background monitoring task
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass

        logger.info("Performance monitoring stopped")

    async def _monitor_system_metrics(self) -> None:
        """Monitor system metrics in the background."""
        try:
            while self.monitoring:
                await self._collect_system_metrics()
                await asyncio.sleep(self.sample_interval)
        except asyncio.CancelledError:
            logger.debug("System metrics monitoring cancelled")

    async def _collect_system_metrics(self) -> None:
        """Collect current system metrics."""
        try:
            timestamp = datetime.now()

            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=None)
            self._add_metric("cpu_usage", cpu_percent, "%", timestamp, "system")

            # Memory metrics
            memory = psutil.virtual_memory()
            self._add_metric("memory_usage", memory.percent, "%", timestamp, "system")
            self._add_metric(
                "memory_available",
                memory.available / 1024 / 1024,
                "MB",
                timestamp,
                "system",
            )

            # Disk I/O metrics
            disk_io = psutil.disk_io_counters()
            if disk_io:
                self._add_metric(
                    "disk_read_mb",
                    disk_io.read_bytes / 1024 / 1024,
                    "MB",
                    timestamp,
                    "system",
                )
                self._add_metric(
                    "disk_write_mb",
                    disk_io.write_bytes / 1024 / 1024,
                    "MB",
                    timestamp,
                    "system",
                )

            # Network I/O metrics
            network_io = psutil.net_io_counters()
            if network_io:
                self._add_metric(
                    "network_sent_mb",
                    network_io.bytes_sent / 1024 / 1024,
                    "MB",
                    timestamp,
                    "system",
                )
                self._add_metric(
                    "network_recv_mb",
                    network_io.bytes_recv / 1024 / 1024,
                    "MB",
                    timestamp,
                    "system",
                )

        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")

    def _add_metric(
        self,
        name: str,
        value: float,
        unit: str,
        timestamp: datetime,
        category: str = "general",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a performance metric."""
        metric = PerformanceMetric(
            name=name,
            value=value,
            unit=unit,
            timestamp=timestamp,
            category=category,
            metadata=metadata or {},
        )
        self.metrics.append(metric)

    def start_api_call(self, endpoint: str, method: str) -> str:
        """Start tracking an API call."""
        call_id = f"{method}_{endpoint}_{len(self.api_calls)}"
        api_call = APICallMetric(
            endpoint=endpoint,
            method=method,
            start_time=datetime.now(),
        )
        self.api_calls.append(api_call)
        return call_id

    def end_api_call(
        self,
        call_id: str,
        status_code: int,
        response_size: Optional[int] = None,
        error: Optional[str] = None,
    ) -> None:
        """End tracking an API call."""
        if not self.api_calls:
            logger.warning(f"No API calls to end for ID: {call_id}")
            return

        # Find the most recent API call (simple implementation)
        api_call = self.api_calls[-1]
        api_call.end_time = datetime.now()
        api_call.response_time = (
            api_call.end_time - api_call.start_time
        ).total_seconds()
        api_call.status_code = status_code
        api_call.response_size = response_size
        api_call.error = error

        # Add response time as a metric
        self._add_metric(
            name="api_response_time",
            value=api_call.response_time * 1000,  # Convert to milliseconds
            unit="ms",
            timestamp=api_call.end_time,
            category="api",
            metadata={
                "endpoint": api_call.endpoint,
                "method": api_call.method,
                "status_code": status_code,
            },
        )

    async def get_metrics(self) -> Dict[str, Any]:
        """Get all collected metrics."""
        if not self.start_time:
            return {}

        end_time = self.end_time or datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        # Organize metrics by category
        metrics_by_category = {}
        for metric in self.metrics:
            category = metric.category
            if category not in metrics_by_category:
                metrics_by_category[category] = []
            metrics_by_category[category].append(
                {
                    "name": metric.name,
                    "value": metric.value,
                    "unit": metric.unit,
                    "timestamp": metric.timestamp.isoformat(),
                    "metadata": metric.metadata,
                }
            )

        # Calculate API call statistics
        api_stats = self._calculate_api_stats()

        # Calculate system metrics statistics
        system_stats = self._calculate_system_stats()

        return {
            "duration": duration,
            "start_time": self.start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "metrics_by_category": metrics_by_category,
            "api_call_stats": api_stats,
            "system_stats": system_stats,
            "total_metrics": len(self.metrics),
            "total_api_calls": len(self.api_calls),
        }

    def _calculate_api_stats(self) -> Dict[str, Any]:
        """Calculate API call statistics."""
        if not self.api_calls:
            return {}

        completed_calls = [
            call for call in self.api_calls if call.response_time is not None
        ]

        if not completed_calls:
            return {"completed_calls": 0}

        response_times = [call.response_time for call in completed_calls]
        status_codes = [
            call.status_code for call in completed_calls if call.status_code
        ]

        stats = {
            "total_calls": len(self.api_calls),
            "completed_calls": len(completed_calls),
            "failed_calls": len([call for call in completed_calls if call.error]),
            "avg_response_time": sum(response_times) / len(response_times),
            "min_response_time": min(response_times),
            "max_response_time": max(response_times),
        }

        # Status code distribution
        if status_codes:
            status_distribution = {}
            for code in status_codes:
                status_distribution[str(code)] = (
                    status_distribution.get(str(code), 0) + 1
                )
            stats["status_distribution"] = status_distribution

        return stats

    def _calculate_system_stats(self) -> Dict[str, Any]:
        """Calculate system metrics statistics."""
        system_metrics = [m for m in self.metrics if m.category == "system"]

        if not system_metrics:
            return {}

        # Group by metric name
        metrics_by_name = {}
        for metric in system_metrics:
            name = metric.name
            if name not in metrics_by_name:
                metrics_by_name[name] = []
            metrics_by_name[name].append(metric.value)

        # Calculate statistics for each metric
        stats = {}
        for name, values in metrics_by_name.items():
            stats[name] = {
                "avg": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
                "samples": len(values),
            }

        return stats

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a summary of performance metrics."""
        if not self.metrics:
            return {"status": "no_data"}

        api_metrics = [m for m in self.metrics if m.category == "api"]
        system_metrics = [m for m in self.metrics if m.category == "system"]

        summary = {
            "monitoring_duration": (
                ((self.end_time or datetime.now()) - self.start_time).total_seconds()
                if self.start_time
                else 0
            ),
            "total_metrics": len(self.metrics),
            "api_metrics": len(api_metrics),
            "system_metrics": len(system_metrics),
            "api_calls": len(self.api_calls),
        }

        # Performance assessment
        if api_metrics:
            avg_response_time = sum(
                m.value for m in api_metrics if m.name == "api_response_time"
            ) / len([m for m in api_metrics if m.name == "api_response_time"])
            summary["avg_api_response_time_ms"] = avg_response_time

            # Simple performance assessment
            if avg_response_time < 100:
                summary["performance_rating"] = "excellent"
            elif avg_response_time < 500:
                summary["performance_rating"] = "good"
            elif avg_response_time < 1000:
                summary["performance_rating"] = "fair"
            else:
                summary["performance_rating"] = "poor"

        return summary

    def add_custom_metric(
        self,
        name: str,
        value: float,
        unit: str = "",
        category: str = "custom",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a custom performance metric."""
        self._add_metric(
            name=name,
            value=value,
            unit=unit,
            timestamp=datetime.now(),
            category=category,
            metadata=metadata,
        )

    def clear_metrics(self) -> None:
        """Clear all collected metrics."""
        self.metrics.clear()
        self.api_calls.clear()
        self.start_time = None
        self.end_time = None
        logger.info("Performance metrics cleared")
