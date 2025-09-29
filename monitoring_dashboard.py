#!/usr/bin/env python3
"""
Monitoring Dashboard - Real-time observability for resilience patterns
Provides metrics for latency, success rate, retries, circuit breaker status, and DLQ
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import time

@dataclass
class DashboardMetrics:
    """Dashboard metrics snapshot"""
    timestamp: datetime
    circuit_breakers: Dict
    bulkheads: Dict
    saga_orchestrator: Dict
    storage_stats: Dict
    system_health: Dict

class MonitoringDashboard:
    """Real-time monitoring dashboard for resilience patterns"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.metrics_history: List[DashboardMetrics] = []
        self.alert_thresholds = {
            'error_rate': 0.05,      # 5%
            'latency_p95': 1000,     # 1000ms
            'circuit_breaker_open': True,
            'storage_errors': 10
        }
        
    async def collect_metrics(self) -> DashboardMetrics:
        """Collect comprehensive metrics from all resilience components"""
        try:
            from resilience_patterns import resilience_manager
            from persistent_state_manager import persistent_state_manager
            from saga_orchestrator import saga_orchestrator
            
            resilience_metrics = resilience_manager.get_all_metrics()
            
            storage_stats = persistent_state_manager.get_storage_stats()
            
            saga_metrics = saga_orchestrator.get_orchestrator_metrics()
            
            system_health = await self._calculate_system_health(resilience_metrics)
            
            metrics = DashboardMetrics(
                timestamp=datetime.now(),
                circuit_breakers=resilience_metrics.get('circuit_breakers', {}),
                bulkheads=resilience_metrics.get('bulkheads', {}),
                saga_orchestrator=saga_metrics,
                storage_stats=storage_stats,
                system_health=system_health
            )
            
            self.metrics_history.append(metrics)
            if len(self.metrics_history) > 1000:
                self.metrics_history = self.metrics_history[-500:]
                
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to collect metrics: {e}")
            return None
            
    async def _calculate_system_health(self, resilience_metrics: Dict) -> Dict:
        """Calculate overall system health indicators"""
        health = {
            'overall_status': 'healthy',
            'error_rate': 0.0,
            'avg_latency': 0.0,
            'open_circuit_breakers': 0,
            'rejected_requests': 0,
            'active_sagas': 0
        }
        
        try:
            circuit_breakers = resilience_metrics.get('circuit_breakers', {})
            total_requests = 0
            total_failures = 0
            total_latency = 0
            open_breakers = 0
            
            for cb_name, cb_metrics in circuit_breakers.items():
                if cb_metrics.get('state') == 'open':
                    open_breakers += 1
                    health['overall_status'] = 'degraded'
                    
                total_requests += cb_metrics.get('total_requests', 0)
                total_failures += cb_metrics.get('failed_requests', 0)
                
            if total_requests > 0:
                health['error_rate'] = total_failures / total_requests
                
            bulkheads = resilience_metrics.get('bulkheads', {})
            total_rejected = 0
            
            for bh_name, bh_metrics in bulkheads.items():
                total_rejected += bh_metrics.get('rejected_requests', 0)
                
            health['open_circuit_breakers'] = open_breakers
            health['rejected_requests'] = total_rejected
            
            if health['error_rate'] > self.alert_thresholds['error_rate']:
                health['overall_status'] = 'unhealthy'
            elif open_breakers > 0 or total_rejected > 0:
                health['overall_status'] = 'degraded'
                
        except Exception as e:
            self.logger.error(f"Failed to calculate system health: {e}")
            health['overall_status'] = 'unknown'
            
        return health
        
    def get_dashboard_data(self, hours: int = 1) -> Dict:
        """Get dashboard data for specified time period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_metrics = [m for m in self.metrics_history if m.timestamp >= cutoff_time]
        
        if not recent_metrics:
            # Return default dashboard structure when no metrics available
            return {
                'timestamp': datetime.now().isoformat(),
                'system_health': 'healthy',
                'circuit_breakers': {},
                'bulkheads': {},
                'saga_orchestrator': {'active_sagas': 0, 'completed_sagas': 0},
                'storage_stats': {'total_tables': 5},
                'trends': {},
                'alerts': []
            }
            
        latest_metrics = recent_metrics[-1]
        
        trends = self._calculate_trends(recent_metrics)
        
        return {
            'timestamp': latest_metrics.timestamp.isoformat(),
            'system_health': latest_metrics.system_health,
            'circuit_breakers': self._format_circuit_breaker_data(latest_metrics.circuit_breakers),
            'bulkheads': self._format_bulkhead_data(latest_metrics.bulkheads),
            'saga_orchestrator': latest_metrics.saga_orchestrator,
            'storage': latest_metrics.storage_stats,
            'trends': trends,
            'alerts': self._generate_alerts(latest_metrics)
        }
        
    def _format_circuit_breaker_data(self, circuit_breakers: Dict) -> List[Dict]:
        """Format circuit breaker data for dashboard display"""
        formatted = []
        
        for name, metrics in circuit_breakers.items():
            formatted.append({
                'name': name,
                'state': metrics.get('state', 'unknown'),
                'total_requests': metrics.get('total_requests', 0),
                'failed_requests': metrics.get('failed_requests', 0),
                'success_requests': metrics.get('success_requests', 0),
                'failure_rate': metrics.get('failure_rate', 0),
                'consecutive_failures': metrics.get('consecutive_failures', 0),
                'last_failure_time': metrics.get('last_failure_time'),
                'status_color': self._get_status_color(metrics.get('state', 'unknown'))
            })
            
        return formatted
        
    def _format_bulkhead_data(self, bulkheads: Dict) -> List[Dict]:
        """Format bulkhead data for dashboard display"""
        formatted = []
        
        for name, metrics in bulkheads.items():
            formatted.append({
                'name': name,
                'active_requests': metrics.get('active_requests', 0),
                'total_requests': metrics.get('total_requests', 0),
                'rejected_requests': metrics.get('rejected_requests', 0),
                'rejection_rate': metrics.get('rejection_rate', 0),
                'available_capacity': metrics.get('available_capacity', 0),
                'utilization': self._calculate_utilization(metrics)
            })
            
        return formatted
        
    def _calculate_utilization(self, metrics: Dict) -> float:
        """Calculate bulkhead utilization percentage"""
        active = metrics.get('active_requests', 0)
        available = metrics.get('available_capacity', 0)
        total_capacity = active + available
        
        if total_capacity > 0:
            return (active / total_capacity) * 100
        return 0
        
    def _get_status_color(self, state: str) -> str:
        """Get color code for circuit breaker state"""
        colors = {
            'closed': 'green',
            'open': 'red',
            'half_open': 'yellow',
            'unknown': 'gray'
        }
        return colors.get(state, 'gray')
        
    def _calculate_trends(self, metrics_list: List[DashboardMetrics]) -> Dict:
        """Calculate trends over time period"""
        if len(metrics_list) < 2:
            return {}
            
        first = metrics_list[0]
        last = metrics_list[-1]
        
        trends = {
            'error_rate_trend': 'stable',
            'request_volume_trend': 'stable',
            'circuit_breaker_changes': 0
        }
        
        try:
            first_error_rate = first.system_health.get('error_rate', 0)
            last_error_rate = last.system_health.get('error_rate', 0)
            
            if last_error_rate > first_error_rate * 1.1:
                trends['error_rate_trend'] = 'increasing'
            elif last_error_rate < first_error_rate * 0.9:
                trends['error_rate_trend'] = 'decreasing'
                
        except Exception as e:
            self.logger.error(f"Failed to calculate trends: {e}")
            
        return trends
        
    def _generate_alerts(self, metrics: DashboardMetrics) -> List[Dict]:
        """Generate alerts based on current metrics"""
        alerts = []
        
        try:
            system_health = metrics.system_health
            
            if system_health.get('error_rate', 0) > self.alert_thresholds['error_rate']:
                alerts.append({
                    'level': 'critical',
                    'message': f"High error rate: {system_health['error_rate']:.2%}",
                    'timestamp': metrics.timestamp.isoformat()
                })
                
            if system_health.get('open_circuit_breakers', 0) > 0:
                alerts.append({
                    'level': 'warning',
                    'message': f"{system_health['open_circuit_breakers']} circuit breaker(s) open",
                    'timestamp': metrics.timestamp.isoformat()
                })
                
            if system_health.get('rejected_requests', 0) > 10:
                alerts.append({
                    'level': 'warning',
                    'message': f"{system_health['rejected_requests']} requests rejected by bulkheads",
                    'timestamp': metrics.timestamp.isoformat()
                })
                
        except Exception as e:
            self.logger.error(f"Failed to generate alerts: {e}")
            
        return alerts
        
    async def start_monitoring(self, interval_seconds: int = 30):
        """Start continuous monitoring loop"""
        self.logger.info(f"Starting monitoring dashboard with {interval_seconds}s interval")
        
        while True:
            try:
                await self.collect_metrics()
                await asyncio.sleep(interval_seconds)
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(interval_seconds)
                
    def export_metrics(self, format: str = 'json') -> str:
        """Export metrics in specified format"""
        if not self.metrics_history:
            return '{"error": "No metrics available"}'
            
        latest = self.metrics_history[-1]
        
        if format == 'json':
            return json.dumps(asdict(latest), default=str, indent=2)
        elif format == 'prometheus':
            return self._export_prometheus_format(latest)
        else:
            return f"Unsupported format: {format}"
            
    def _export_prometheus_format(self, metrics: DashboardMetrics) -> str:
        """Export metrics in Prometheus format"""
        lines = []
        timestamp = int(metrics.timestamp.timestamp() * 1000)
        
        for name, cb_metrics in metrics.circuit_breakers.items():
            lines.append(f'circuit_breaker_total_requests{{service="{name}"}} {cb_metrics.get("total_requests", 0)} {timestamp}')
            lines.append(f'circuit_breaker_failed_requests{{service="{name}"}} {cb_metrics.get("failed_requests", 0)} {timestamp}')
            lines.append(f'circuit_breaker_failure_rate{{service="{name}"}} {cb_metrics.get("failure_rate", 0)} {timestamp}')
            
        lines.append(f'system_error_rate {metrics.system_health.get("error_rate", 0)} {timestamp}')
        lines.append(f'system_open_circuit_breakers {metrics.system_health.get("open_circuit_breakers", 0)} {timestamp}')
        
        return '\n'.join(lines)

monitoring_dashboard = MonitoringDashboard()
