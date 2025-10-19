#!/usr/bin/env python3
"""
Ops Agent OODA Loop - Operations and Deployment Management Agent
Implements the Observe-Orient-Decide-Act decision-making cycle for operations tasks
"""
import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

from tools.deployment_tool import DeploymentTool
from tools.monitoring_tool import MonitoringTool
from tools.log_analysis_tool import LogAnalysisTool
from tools.alert_management_tool import AlertManagementTool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """Task priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class OpsAgentOODA:
    """Operations Agent with OODA Loop architecture"""
    
    def __init__(
        self,
        vercel_token: Optional[str] = None,
        team_id: Optional[str] = None,
        enable_monitoring: bool = True,
        enable_alerts: bool = True
    ):
        """
        Initialize Ops Agent
        
        Args:
            vercel_token: Vercel API token for deployments
            team_id: Vercel team ID
            enable_monitoring: Enable system monitoring
            enable_alerts: Enable alert management
        """
        self.deployment_tool = DeploymentTool(token=vercel_token, team_id=team_id)
        self.monitoring_tool = MonitoringTool() if enable_monitoring else None
        self.log_tool = LogAnalysisTool()
        self.alert_tool = AlertManagementTool() if enable_alerts else None
        
        self.context: Dict[str, Any] = {}
        self.task_history: List[Dict[str, Any]] = []
    
    async def execute_task(
        self,
        task: str,
        priority: str = "medium",
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute an operational task using OODA Loop
        
        Args:
            task: Task description
            priority: Task priority (critical, high, medium, low)
            context: Additional context
        
        Returns:
            Dict with execution result
        """
        try:
            task_id = len(self.task_history) + 1
            start_time = datetime.utcnow()
            
            logger.info(f"Task {task_id}: {task} (Priority: {priority})")
            
            observations = await self._observe()
            
            orientation = await self._orient(task, observations, context or {})
            
            decision = await self._decide(orientation)
            
            result = await self._act(decision)
            
            task_record = {
                'task_id': task_id,
                'task': task,
                'priority': priority,
                'start_time': start_time.isoformat(),
                'end_time': datetime.utcnow().isoformat(),
                'result': result
            }
            self.task_history.append(task_record)
            
            return {
                'success': True,
                'task_id': task_id,
                'result': result
            }
        
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _observe(self) -> Dict[str, Any]:
        """
        OBSERVE phase: Gather current operational state
        
        Returns:
            Dict with observations
        """
        observations = {}
        
        try:
            if self.monitoring_tool:
                metrics = await self.monitoring_tool.get_system_metrics()
                observations['system_metrics'] = metrics
            
            if self.alert_tool:
                alerts = await self.alert_tool.get_active_alerts()
                observations['active_alerts'] = alerts
            
            error_patterns = await self.log_tool.analyze_error_patterns(time_range="1h")
            observations['recent_errors'] = error_patterns
            
            anomalies = await self.log_tool.detect_anomalies()
            observations['anomalies'] = anomalies
            
            logger.info(f"Observations gathered: {len(observations)} categories")
            return observations
        
        except Exception as e:
            logger.error(f"Observation failed: {e}")
            return {}
    
    async def _orient(
        self,
        task: str,
        observations: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        ORIENT phase: Analyze and understand the situation
        
        Args:
            task: Task description
            observations: Gathered observations
            context: Additional context
        
        Returns:
            Dict with orientation analysis
        """
        try:
            orientation = {
                'task_type': self._classify_task(task),
                'observations': observations,
                'context': context,
                'recommendations': []
            }
            
            if observations.get('system_metrics'):
                health_analysis = self._analyze_system_health(
                    observations['system_metrics']
                )
                orientation['system_health'] = health_analysis
            
            if observations.get('recent_errors'):
                error_analysis = self._analyze_errors(
                    observations['recent_errors']
                )
                orientation['error_analysis'] = error_analysis
            
            logger.info(f"Orientation completed: task_type={orientation['task_type']}")
            return orientation
        
        except Exception as e:
            logger.error(f"Orientation failed: {e}")
            return {'task_type': 'unknown'}
    
    async def _decide(self, orientation: Dict[str, Any]) -> Dict[str, Any]:
        """
        DECIDE phase: Determine best course of action
        
        Args:
            orientation: Orientation analysis
        
        Returns:
            Dict with decision
        """
        try:
            task_type = orientation.get('task_type', 'unknown')
            
            decision = {
                'action': None,
                'parameters': {},
                'reason': ''
            }
            
            if task_type == 'deployment':
                decision['action'] = 'deploy'
                decision['reason'] = 'Deploy to Vercel platform'
            
            elif task_type == 'monitoring':
                decision['action'] = 'monitor'
                decision['reason'] = 'Monitor system metrics'
            
            elif task_type == 'log_analysis':
                decision['action'] = 'analyze_logs'
                decision['reason'] = 'Analyze logs for issues'
            
            elif task_type == 'alert_management':
                decision['action'] = 'manage_alerts'
                decision['reason'] = 'Manage alerts and notifications'
            
            elif task_type == 'troubleshooting':
                decision['action'] = 'troubleshoot'
                decision['reason'] = 'Investigate and resolve issues'
            
            else:
                decision['action'] = 'unknown'
                decision['reason'] = 'Task type not recognized'
            
            logger.info(f"Decision made: action={decision['action']}")
            return decision
        
        except Exception as e:
            logger.error(f"Decision failed: {e}")
            return {'action': 'error', 'reason': str(e)}
    
    async def _act(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """
        ACT phase: Execute the decision
        
        Args:
            decision: Decision to execute
        
        Returns:
            Dict with action result
        """
        try:
            action = decision.get('action')
            parameters = decision.get('parameters', {})
            
            if action == 'deploy':
                return await self._execute_deployment(parameters)
            
            elif action == 'monitor':
                return await self._execute_monitoring(parameters)
            
            elif action == 'analyze_logs':
                return await self._execute_log_analysis(parameters)
            
            elif action == 'manage_alerts':
                return await self._execute_alert_management(parameters)
            
            elif action == 'troubleshoot':
                return await self._execute_troubleshooting(parameters)
            
            else:
                return {
                    'success': False,
                    'error': f'Unknown action: {action}'
                }
        
        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _classify_task(self, task: str) -> str:
        """Classify task type based on description"""
        task_lower = task.lower()
        
        if any(keyword in task_lower for keyword in ['deploy', 'deployment', 'release']):
            return 'deployment'
        
        elif any(keyword in task_lower for keyword in ['monitor', 'metrics', 'performance']):
            return 'monitoring'
        
        elif any(keyword in task_lower for keyword in ['log', 'logs', 'error pattern']):
            return 'log_analysis'
        
        elif any(keyword in task_lower for keyword in ['alert', 'notification', 'alarm']):
            return 'alert_management'
        
        elif any(keyword in task_lower for keyword in ['troubleshoot', 'debug', 'investigate', 'fix']):
            return 'troubleshooting'
        
        return 'unknown'
    
    def _analyze_system_health(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze system health from metrics"""
        if not metrics.get('success'):
            return {'status': 'unknown', 'issues': []}
        
        issues = []
        data = metrics.get('metrics', {})
        
        cpu = data.get('cpu', {})
        if cpu.get('percent', 0) > 80:
            issues.append({
                'type': 'high_cpu',
                'severity': 'medium',
                'message': f"CPU usage at {cpu.get('percent')}%"
            })
        
        memory = data.get('memory', {})
        if memory.get('percent', 0) > 85:
            issues.append({
                'type': 'high_memory',
                'severity': 'medium',
                'message': f"Memory usage at {memory.get('percent')}%"
            })
        
        disk = data.get('disk', {})
        if disk.get('percent', 0) > 90:
            issues.append({
                'type': 'high_disk',
                'severity': 'high',
                'message': f"Disk usage at {disk.get('percent')}%"
            })
        
        status = 'healthy' if len(issues) == 0 else 'degraded'
        
        return {
            'status': status,
            'issues': issues
        }
    
    def _analyze_errors(self, error_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze error patterns"""
        if not error_data.get('success'):
            return {'critical_patterns': [], 'total_errors': 0}
        
        patterns = error_data.get('patterns', [])
        total_errors = error_data.get('total_errors', 0)
        
        critical_patterns = [
            p for p in patterns
            if p.get('count', 0) > 5
        ]
        
        return {
            'critical_patterns': critical_patterns,
            'total_errors': total_errors,
            'unique_patterns': len(patterns)
        }
    
    async def _execute_deployment(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute deployment action"""
        try:
            project = parameters.get('project', 'morningai')
            environment = parameters.get('environment', 'production')
            
            result = await self.deployment_tool.deploy(
                project=project,
                environment=environment
            )
            
            if result.get('success'):
                deployment_id = result.get('deployment_id')
                wait_result = await self.deployment_tool.wait_for_deployment(
                    deployment_id,
                    timeout=600
                )
                return wait_result
            
            return result
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _execute_monitoring(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute monitoring action"""
        if not self.monitoring_tool:
            return {'success': False, 'error': 'Monitoring not enabled'}
        
        return await self.monitoring_tool.get_metrics_summary()
    
    async def _execute_log_analysis(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute log analysis action"""
        time_range = parameters.get('time_range', '1h')
        return await self.log_tool.analyze_error_patterns(time_range=time_range)
    
    async def _execute_alert_management(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute alert management action"""
        if not self.alert_tool:
            return {'success': False, 'error': 'Alert management not enabled'}
        
        return await self.alert_tool.get_active_alerts()
    
    async def _execute_troubleshooting(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute troubleshooting action"""
        results = {}
        
        if self.monitoring_tool:
            results['metrics'] = await self.monitoring_tool.get_system_metrics()
        
        results['errors'] = await self.log_tool.analyze_error_patterns(time_range="1h")
        results['anomalies'] = await self.log_tool.detect_anomalies()
        
        if self.alert_tool:
            results['alerts'] = await self.alert_tool.get_active_alerts()
        
        return {
            'success': True,
            'diagnostics': results
        }


def create_ops_agent(
    vercel_token: Optional[str] = None,
    team_id: Optional[str] = None,
    enable_monitoring: bool = True,
    enable_alerts: bool = True
) -> OpsAgentOODA:
    """Factory function to create OpsAgentOODA instance"""
    return OpsAgentOODA(
        vercel_token=vercel_token,
        team_id=team_id,
        enable_monitoring=enable_monitoring,
        enable_alerts=enable_alerts
    )
