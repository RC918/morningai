#!/usr/bin/env python3
"""
Monitoring Tool - System and Application Monitoring
"""
import logging
import asyncio
import psutil
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class MetricType(Enum):
    """Metric types"""
    GAUGE = "gauge"
    COUNTER = "counter"
    HISTOGRAM = "histogram"


@dataclass
class SystemMetrics:
    """System metrics data"""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_sent: int
    network_recv: int
    timestamp: datetime


@dataclass
class CustomMetric:
    """Custom metric definition"""
    name: str
    value: float
    type: MetricType
    labels: Dict[str, str]
    timestamp: datetime


class MonitoringTool:
    """Tool for system and application monitoring"""
    
    def __init__(self):
        """Initialize Monitoring Tool"""
        self.custom_metrics: Dict[str, CustomMetric] = {}
        self.health_checks: Dict[str, callable] = {}
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """
        Get current system metrics
        
        Returns:
            Dict with system metrics
        """
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            disk = psutil.disk_usage('/')
            
            network = psutil.net_io_counters()
            
            return {
                'success': True,
                'metrics': {
                    'cpu': {
                        'percent': cpu_percent,
                        'count': cpu_count,
                        'frequency': cpu_freq.current if cpu_freq else None
                    },
                    'memory': {
                        'total': memory.total,
                        'available': memory.available,
                        'percent': memory.percent,
                        'used': memory.used,
                        'free': memory.free
                    },
                    'swap': {
                        'total': swap.total,
                        'used': swap.used,
                        'percent': swap.percent
                    },
                    'disk': {
                        'total': disk.total,
                        'used': disk.used,
                        'free': disk.free,
                        'percent': disk.percent
                    },
                    'network': {
                        'bytes_sent': network.bytes_sent,
                        'bytes_recv': network.bytes_recv,
                        'packets_sent': network.packets_sent,
                        'packets_recv': network.packets_recv
                    },
                    'timestamp': datetime.utcnow().isoformat()
                }
            }
        
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def check_service_health(self, service: str, url: Optional[str] = None) -> Dict[str, Any]:
        """
        Check health of a service
        
        Args:
            service: Service name
            url: Optional health check URL
        
        Returns:
            Dict with health status
        """
        try:
            if service in self.health_checks:
                is_healthy = await self.health_checks[service]()
            else:
                is_healthy = True
            
            return {
                'success': True,
                'service': service,
                'status': HealthStatus.HEALTHY.value if is_healthy else HealthStatus.UNHEALTHY.value,
                'timestamp': datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Health check failed for {service}: {e}")
            return {
                'success': False,
                'service': service,
                'status': HealthStatus.UNHEALTHY.value,
                'error': str(e)
            }
    
    async def add_custom_metric(
        self,
        name: str,
        value: float,
        metric_type: str = "gauge",
        labels: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Add a custom metric
        
        Args:
            name: Metric name
            value: Metric value
            metric_type: Type of metric (gauge, counter, histogram)
            labels: Optional labels
        
        Returns:
            Dict with result
        """
        try:
            metric = CustomMetric(
                name=name,
                value=value,
                type=MetricType(metric_type),
                labels=labels or {},
                timestamp=datetime.utcnow()
            )
            
            self.custom_metrics[name] = metric
            
            return {
                'success': True,
                'metric': {
                    'name': name,
                    'value': value,
                    'type': metric_type,
                    'labels': labels
                }
            }
        
        except Exception as e:
            logger.error(f"Failed to add custom metric: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Get summary of all metrics
        
        Returns:
            Dict with metrics summary
        """
        try:
            system_metrics = await self.get_system_metrics()
            
            return {
                'success': True,
                'summary': {
                    'system_metrics': system_metrics.get('metrics', {}),
                    'custom_metrics': {
                        name: {
                            'value': metric.value,
                            'type': metric.type.value,
                            'labels': metric.labels,
                            'timestamp': metric.timestamp.isoformat()
                        }
                        for name, metric in self.custom_metrics.items()
                    },
                    'total_custom_metrics': len(self.custom_metrics)
                }
            }
        
        except Exception as e:
            logger.error(f"Failed to get metrics summary: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def register_health_check(self, service: str, check_func: callable):
        """
        Register a custom health check function
        
        Args:
            service: Service name
            check_func: Async function that returns bool
        """
        self.health_checks[service] = check_func


def create_monitoring_tool() -> MonitoringTool:
    """Factory function to create MonitoringTool instance"""
    return MonitoringTool()
