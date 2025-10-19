#!/usr/bin/env python3
"""
Alert Management Tool - Alert Rules and Notifications
"""
import logging
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AlertStatus(Enum):
    """Alert status"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class NotificationChannel(Enum):
    """Notification channels"""
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    SMS = "sms"


@dataclass
class AlertRule:
    """Alert rule definition"""
    id: str
    name: str
    condition: str
    severity: AlertSeverity
    channels: List[NotificationChannel]
    enabled: bool
    created_at: datetime
    threshold: Optional[float] = None
    check_func: Optional[Callable] = None


@dataclass
class Alert:
    """Alert instance"""
    id: str
    rule_id: str
    severity: AlertSeverity
    status: AlertStatus
    message: str
    triggered_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class AlertManagementTool:
    """Tool for managing alerts and notifications"""
    
    def __init__(self):
        """Initialize Alert Management Tool"""
        self.alert_rules: Dict[str, AlertRule] = {}
        self.alerts: Dict[str, Alert] = {}
        self.alert_counter = 0
        self.rule_counter = 0
    
    async def create_alert_rule(
        self,
        name: str,
        condition: str,
        severity: str = "medium",
        channels: Optional[List[str]] = None,
        threshold: Optional[float] = None,
        check_func: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Create an alert rule
        
        Args:
            name: Rule name
            condition: Condition description
            severity: Alert severity
            channels: Notification channels
            threshold: Threshold value
            check_func: Custom check function
        
        Returns:
            Dict with rule information
        """
        try:
            self.rule_counter += 1
            rule_id = f"rule_{self.rule_counter}"
            
            channel_list = [
                NotificationChannel(ch) for ch in (channels or ["email"])
            ]
            
            rule = AlertRule(
                id=rule_id,
                name=name,
                condition=condition,
                severity=AlertSeverity(severity),
                channels=channel_list,
                enabled=True,
                created_at=datetime.utcnow(),
                threshold=threshold,
                check_func=check_func
            )
            
            self.alert_rules[rule_id] = rule
            
            return {
                'success': True,
                'rule': {
                    'id': rule_id,
                    'name': name,
                    'condition': condition,
                    'severity': severity,
                    'channels': channels or ["email"],
                    'enabled': True
                }
            }
        
        except Exception as e:
            logger.error(f"Failed to create alert rule: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def trigger_alert(
        self,
        rule_id: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Trigger an alert
        
        Args:
            rule_id: Rule ID
            message: Alert message
            metadata: Additional metadata
        
        Returns:
            Dict with alert information
        """
        try:
            if rule_id not in self.alert_rules:
                return {
                    'success': False,
                    'error': f'Rule {rule_id} not found'
                }
            
            rule = self.alert_rules[rule_id]
            
            if not rule.enabled:
                return {
                    'success': False,
                    'error': f'Rule {rule_id} is disabled'
                }
            
            self.alert_counter += 1
            alert_id = f"alert_{self.alert_counter}"
            
            alert = Alert(
                id=alert_id,
                rule_id=rule_id,
                severity=rule.severity,
                status=AlertStatus.ACTIVE,
                message=message,
                triggered_at=datetime.utcnow(),
                metadata=metadata
            )
            
            self.alerts[alert_id] = alert
            
            await self._send_notifications(alert, rule)
            
            return {
                'success': True,
                'alert': {
                    'id': alert_id,
                    'rule_id': rule_id,
                    'severity': rule.severity.value,
                    'message': message,
                    'triggered_at': alert.triggered_at.isoformat()
                }
            }
        
        except Exception as e:
            logger.error(f"Failed to trigger alert: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_active_alerts(self, severity: Optional[str] = None) -> Dict[str, Any]:
        """
        Get active alerts
        
        Args:
            severity: Filter by severity
        
        Returns:
            Dict with active alerts
        """
        try:
            active_alerts = [
                alert for alert in self.alerts.values()
                if alert.status == AlertStatus.ACTIVE
            ]
            
            if severity:
                active_alerts = [
                    alert for alert in active_alerts
                    if alert.severity.value == severity
                ]
            
            return {
                'success': True,
                'alerts': [
                    {
                        'id': alert.id,
                        'rule_id': alert.rule_id,
                        'severity': alert.severity.value,
                        'status': alert.status.value,
                        'message': alert.message,
                        'triggered_at': alert.triggered_at.isoformat()
                    }
                    for alert in active_alerts
                ],
                'total': len(active_alerts)
            }
        
        except Exception as e:
            logger.error(f"Failed to get active alerts: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def acknowledge_alert(self, alert_id: str) -> Dict[str, Any]:
        """
        Acknowledge an alert
        
        Args:
            alert_id: Alert ID
        
        Returns:
            Dict with result
        """
        try:
            if alert_id not in self.alerts:
                return {
                    'success': False,
                    'error': f'Alert {alert_id} not found'
                }
            
            alert = self.alerts[alert_id]
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_at = datetime.utcnow()
            
            return {
                'success': True,
                'alert_id': alert_id,
                'status': alert.status.value,
                'acknowledged_at': alert.acknowledged_at.isoformat()
            }
        
        except Exception as e:
            logger.error(f"Failed to acknowledge alert: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def resolve_alert(self, alert_id: str) -> Dict[str, Any]:
        """
        Resolve an alert
        
        Args:
            alert_id: Alert ID
        
        Returns:
            Dict with result
        """
        try:
            if alert_id not in self.alerts:
                return {
                    'success': False,
                    'error': f'Alert {alert_id} not found'
                }
            
            alert = self.alerts[alert_id]
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.utcnow()
            
            return {
                'success': True,
                'alert_id': alert_id,
                'status': alert.status.value,
                'resolved_at': alert.resolved_at.isoformat()
            }
        
        except Exception as e:
            logger.error(f"Failed to resolve alert: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_alert_history(
        self,
        limit: int = 50,
        severity: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get alert history
        
        Args:
            limit: Maximum results
            severity: Filter by severity
        
        Returns:
            Dict with alert history
        """
        try:
            alerts = list(self.alerts.values())
            
            if severity:
                alerts = [a for a in alerts if a.severity.value == severity]
            
            alerts.sort(key=lambda a: a.triggered_at, reverse=True)
            alerts = alerts[:limit]
            
            return {
                'success': True,
                'alerts': [
                    {
                        'id': alert.id,
                        'rule_id': alert.rule_id,
                        'severity': alert.severity.value,
                        'status': alert.status.value,
                        'message': alert.message,
                        'triggered_at': alert.triggered_at.isoformat(),
                        'acknowledged_at': alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
                        'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None
                    }
                    for alert in alerts
                ],
                'total': len(alerts)
            }
        
        except Exception as e:
            logger.error(f"Failed to get alert history: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def update_alert_rule(
        self,
        rule_id: str,
        enabled: Optional[bool] = None,
        severity: Optional[str] = None,
        channels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Update an alert rule
        
        Args:
            rule_id: Rule ID
            enabled: Enable/disable rule
            severity: Update severity
            channels: Update channels
        
        Returns:
            Dict with updated rule
        """
        try:
            if rule_id not in self.alert_rules:
                return {
                    'success': False,
                    'error': f'Rule {rule_id} not found'
                }
            
            rule = self.alert_rules[rule_id]
            
            if enabled is not None:
                rule.enabled = enabled
            
            if severity:
                rule.severity = AlertSeverity(severity)
            
            if channels:
                rule.channels = [NotificationChannel(ch) for ch in channels]
            
            return {
                'success': True,
                'rule': {
                    'id': rule_id,
                    'name': rule.name,
                    'enabled': rule.enabled,
                    'severity': rule.severity.value,
                    'channels': [ch.value for ch in rule.channels]
                }
            }
        
        except Exception as e:
            logger.error(f"Failed to update alert rule: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def delete_alert_rule(self, rule_id: str) -> Dict[str, Any]:
        """
        Delete an alert rule
        
        Args:
            rule_id: Rule ID
        
        Returns:
            Dict with result
        """
        try:
            if rule_id not in self.alert_rules:
                return {
                    'success': False,
                    'error': f'Rule {rule_id} not found'
                }
            
            del self.alert_rules[rule_id]
            
            return {
                'success': True,
                'rule_id': rule_id,
                'deleted': True
            }
        
        except Exception as e:
            logger.error(f"Failed to delete alert rule: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _send_notifications(self, alert: Alert, rule: AlertRule):
        """Send notifications for an alert"""
        for channel in rule.channels:
            try:
                await self._send_notification(channel, alert, rule)
            except Exception as e:
                logger.error(f"Failed to send notification via {channel.value}: {e}")
    
    async def _send_notification(
        self,
        channel: NotificationChannel,
        alert: Alert,
        rule: AlertRule
    ):
        """Send notification via specific channel"""
        logger.info(f"Sending {alert.severity.value} alert via {channel.value}: {alert.message}")
        
        if channel == NotificationChannel.EMAIL:
            logger.info(f"Email notification: {alert.message}")
        elif channel == NotificationChannel.SLACK:
            logger.info(f"Slack notification: {alert.message}")
        elif channel == NotificationChannel.WEBHOOK:
            logger.info(f"Webhook notification: {alert.message}")
        elif channel == NotificationChannel.SMS:
            logger.info(f"SMS notification: {alert.message}")


def create_alert_management_tool() -> AlertManagementTool:
    """Factory function to create AlertManagementTool instance"""
    return AlertManagementTool()
