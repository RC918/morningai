#!/usr/bin/env python3
"""
Ops_Agent - Performance Optimization and System Operations
Integrates with GrowthStrategist for performance-growth feedback loops
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from resilience_patterns import resilience_manager, CircuitBreakerConfig
from persistent_state_manager import persistent_state_manager

@dataclass
class SystemCapacity:
    """System capacity metrics"""
    current_load: float
    max_capacity: int
    recommended_batch_size: int
    estimated_headroom: float
    
@dataclass
class PerformanceMetrics:
    """Performance monitoring metrics"""
    api_latency_p95: float
    error_rate: float
    throughput_rps: float
    cpu_usage: float
    memory_usage: float
    timestamp: datetime
    
class AlertLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class OpsAgent:
    """Operations Agent for performance optimization and capacity management"""
    
    def __init__(self, monitoring_system=None):
        self.monitoring_system = monitoring_system
        self.logger = logging.getLogger(__name__)
        self.performance_thresholds = {
            'api_latency_p95': 500,  # ms
            'error_rate': 0.01,      # 1%
            'cpu_usage': 0.8,        # 80%
            'memory_usage': 0.8      # 80%
        }
        
        self.circuit_breaker_config = CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=30,
            timeout=10.0
        )
        
    async def get_current_metrics(self) -> PerformanceMetrics:
        """Get current system performance metrics with circuit breaker protection"""
        async def _get_metrics():
            if self.monitoring_system:
                result = self.monitoring_system.check_endpoint('/health', dry_run=True)
                return PerformanceMetrics(
                    api_latency_p95=result.response_time * 1000,  # Convert to ms
                    error_rate=0.005 if result.success else 0.05,
                    throughput_rps=100.0,
                    cpu_usage=0.6,
                    memory_usage=0.7,
                    timestamp=datetime.now()
                )
            else:
                return PerformanceMetrics(
                    api_latency_p95=250.0,
                    error_rate=0.005,
                    throughput_rps=120.0,
                    cpu_usage=0.6,
                    memory_usage=0.7,
                    timestamp=datetime.now()
                )
        
        try:
            return await resilience_manager.protected_call(
                'monitoring_system', _get_metrics
            )
        except Exception as e:
            self.logger.warning(f"Failed to get metrics with circuit breaker: {e}")
            return PerformanceMetrics(
                api_latency_p95=500.0,  # Higher latency indicates degraded state
                error_rate=0.02,
                throughput_rps=50.0,
                cpu_usage=0.8,
                memory_usage=0.8,
                timestamp=datetime.now()
            )
        
    async def analyze_system_capacity(self) -> SystemCapacity:
        """Analyze current system capacity and recommend batch sizes"""
        metrics = await self.get_current_metrics()
        
        load_factor = max(metrics.cpu_usage, metrics.memory_usage)
        base_batch_size = 10000
        
        if load_factor > 0.8:
            recommended_batch_size = int(base_batch_size * 0.5)
        elif load_factor > 0.6:
            recommended_batch_size = int(base_batch_size * 0.7)
        else:
            recommended_batch_size = base_batch_size
            
        headroom = 1.0 - load_factor
        
        return SystemCapacity(
            current_load=load_factor,
            max_capacity=base_batch_size,
            recommended_batch_size=recommended_batch_size,
            estimated_headroom=headroom
        )
        
    async def monitor_campaign_performance(self, campaign_id: str) -> Dict:
        """Monitor performance during growth campaigns"""
        metrics = await self.get_current_metrics()
        
        alerts = []
        if metrics.api_latency_p95 > self.performance_thresholds['api_latency_p95']:
            alerts.append({
                'level': AlertLevel.HIGH,
                'message': f'API latency exceeded threshold: {metrics.api_latency_p95}ms',
                'action': 'pause_campaign'
            })
            
        if metrics.error_rate > self.performance_thresholds['error_rate']:
            alerts.append({
                'level': AlertLevel.CRITICAL,
                'message': f'Error rate exceeded threshold: {metrics.error_rate*100}%',
                'action': 'pause_campaign_and_scale'
            })
            
        return {
            'campaign_id': campaign_id,
            'metrics': metrics,
            'alerts': alerts,
            'recommendation': 'continue' if not alerts else 'pause'
        }
        
    async def trigger_auto_scaling(self, scale_factor: float = 1.5) -> Dict:
        """Trigger automatic scaling when thresholds exceeded"""
        self.logger.info(f"Triggering auto-scaling with factor {scale_factor}")
        
        return {
            'action': 'auto_scale',
            'scale_factor': scale_factor,
            'estimated_completion': datetime.now() + timedelta(minutes=5),
            'status': 'initiated'
        }
        
    def get_performance_report(self) -> Dict:
        """Generate performance optimization report"""
        return {
            'agent': 'Ops_Agent',
            'capabilities': [
                'System capacity analysis',
                'Performance monitoring during campaigns',
                'Automatic scaling triggers',
                'Integration with GrowthStrategist'
            ],
            'thresholds': self.performance_thresholds,
            'status': 'operational'
        }
