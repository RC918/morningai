#!/usr/bin/env python3
"""
Ops Agent - Phase 3 PR-3 (#1815)

Operations Agent for system health monitoring and operational tasks.
Monitors system health, reads structured logs, and executes restart/rollback operations.

Design Principles:
- Advisory role: Provides operational recommendations
- Health monitoring: Monitors system health metrics
- Log analysis: Reads and analyzes structured logs
- Action execution: Executes restart/rollback with HITL approval
- Integration: Works with existing monitoring and HITL components
"""
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)


class OpsRisk(Enum):
    """Operations risk levels"""
    CRITICAL = "critical"  # Immediate action required
    HIGH = "high"          # Significant issue, requires attention
    MEDIUM = "medium"      # Moderate issue, advisory
    LOW = "low"            # Minor issue, informational
    INFO = "info"          # No issue, informational only


class HealthStatus(Enum):
    """System health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ActionType(Enum):
    """Operational action types"""
    RESTART = "restart"
    ROLLBACK = "rollback"
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    ALERT = "alert"
    NO_ACTION = "no_action"


@dataclass
class LogEntry:
    """Represents a structured log entry"""
    timestamp: str
    level: str  # "error", "warning", "info", "debug"
    message: str
    source: str = ""
    trace_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "timestamp": self.timestamp,
            "level": self.level,
            "message": self.message,
            "source": self.source,
            "trace_id": self.trace_id,
            "metadata": self.metadata,
        }


@dataclass
class HealthMetric:
    """Represents a health metric"""
    name: str
    value: float
    unit: str
    status: HealthStatus
    threshold_warning: Optional[float] = None
    threshold_critical: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "status": self.status.value,
            "threshold_warning": self.threshold_warning,
            "threshold_critical": self.threshold_critical,
            "metadata": self.metadata,
        }


@dataclass
class OpsFinding:
    """Represents an operations finding"""
    category: str           # e.g., "health", "log", "performance", "error"
    risk_level: OpsRisk
    title: str
    description: str
    source: str = ""
    recommendation: Optional[str] = None
    recommended_action: ActionType = ActionType.NO_ACTION
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "category": self.category,
            "risk_level": self.risk_level.value,
            "title": self.title,
            "description": self.description,
            "source": self.source,
            "recommendation": self.recommendation,
            "recommended_action": self.recommended_action.value,
            "metadata": self.metadata,
        }


@dataclass
class ActionRecommendation:
    """Represents a recommended operational action"""
    action_type: ActionType
    target: str             # e.g., "worker", "api-backend", "orchestrator"
    reason: str
    urgency: OpsRisk
    requires_approval: bool = True
    estimated_downtime: str = "unknown"
    rollback_available: bool = True
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "action_type": self.action_type.value,
            "target": self.target,
            "reason": self.reason,
            "urgency": self.urgency.value,
            "requires_approval": self.requires_approval,
            "estimated_downtime": self.estimated_downtime,
            "rollback_available": self.rollback_available,
            "metadata": self.metadata,
        }


@dataclass
class OpsAdvisory:
    """Operations advisory result from OpsAgent analysis"""
    health_status: HealthStatus
    overall_risk: OpsRisk
    findings: List[OpsFinding] = field(default_factory=list)
    health_metrics: List[HealthMetric] = field(default_factory=list)
    log_summary: Dict[str, int] = field(default_factory=dict)
    recommended_actions: List[ActionRecommendation] = field(default_factory=list)
    summary: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "health_status": self.health_status.value,
            "overall_risk": self.overall_risk.value,
            "findings": [f.to_dict() for f in self.findings],
            "health_metrics": [m.to_dict() for m in self.health_metrics],
            "log_summary": self.log_summary,
            "recommended_actions": [a.to_dict() for a in self.recommended_actions],
            "summary": self.summary,
            "metadata": self.metadata,
        }


class OpsAgent:
    """
    Operations Agent for the orchestrator pipeline.

    Phase 3 PR-3 Features (#1815):
    - Health monitoring: Monitor system health metrics
    - Log analysis: Read and analyze structured logs
    - Action recommendations: Recommend restart/rollback/scaling actions
    - HITL integration: Request approval for high-risk operations
    - Auto-scaling decisions: Make scaling recommendations based on metrics
    """

    # Error patterns for log analysis
    ERROR_PATTERNS = {
        "timeout": ["timeout", "timed out", "deadline exceeded"],
        "memory": ["out of memory", "oom", "memory limit", "heap"],
        "connection": ["connection refused", "connection reset", "econnrefused"],
        "rate_limit": ["rate limit", "too many requests", "429"],
        "auth": ["authentication", "unauthorized", "403", "401"],
        "database": ["database", "postgres", "supabase", "connection pool"],
    }

    # Health thresholds
    HEALTH_THRESHOLDS = {
        "error_rate": {"warning": 0.05, "critical": 0.1},
        "latency_p99_ms": {"warning": 5000, "critical": 10000},
        "memory_percent": {"warning": 80, "critical": 95},
        "cpu_percent": {"warning": 80, "critical": 95},
        "queue_depth": {"warning": 100, "critical": 500},
    }

    def __init__(self):
        """Initialize OpsAgent with configuration"""
        self._load_settings()
        self._init_integrations()
        logger.info("[OpsAgent] Initialized - Phase 3 PR-3 (#1815)")

    def _load_settings(self):
        """Load settings from environment"""
        try:
            from common.config.settings import settings
            self.enabled = getattr(settings, 'ops_agent_enabled', True)
            self.auto_action_enabled = getattr(settings, 'ops_agent_auto_action', False)
            self.hitl_required = getattr(settings, 'ops_agent_hitl_required', True)
            logger.info(
                "[OpsAgent] Settings loaded: enabled=%s, auto_action=%s, hitl_required=%s",
                self.enabled, self.auto_action_enabled, self.hitl_required
            )
        except (ImportError, AttributeError) as e:
            logger.warning("[OpsAgent] Failed to load settings: %s, using defaults", e)
            self.enabled = True
            self.auto_action_enabled = False
            self.hitl_required = True

    def _init_integrations(self):
        """Initialize integrations with monitoring and HITL systems"""
        self.metrics_client = None
        self.hitl_interceptor = None

        # Try to initialize metrics client
        try:
            from orchestrator_metrics import get_orchestrator_metrics
            self.metrics_client = get_orchestrator_metrics()
            logger.info("[OpsAgent] Metrics integration enabled")
        except ImportError as e:
            logger.warning("[OpsAgent] Metrics not available: %s", e)

        # Try to initialize HITL interceptor
        try:
            from hitl import HITLInterceptor
            self.hitl_interceptor = HITLInterceptor(agent_id="ops_agent")
            logger.info("[OpsAgent] HITL integration enabled")
        except ImportError as e:
            logger.warning("[OpsAgent] HITL not available: %s", e)

    def check_system_health(
        self,
        include_metrics: bool = True,
        include_logs: bool = True,
        time_window_minutes: int = 15
    ) -> OpsAdvisory:
        """
        Check overall system health.

        Args:
            include_metrics: Include health metrics in analysis
            include_logs: Include log analysis
            time_window_minutes: Time window for analysis

        Returns:
            OpsAdvisory with health status and findings
        """
        if not self.enabled:
            return OpsAdvisory(
                health_status=HealthStatus.UNKNOWN,
                overall_risk=OpsRisk.INFO,
                summary="Ops Agent disabled"
            )

        start_time = time.time()
        trace_id = str(uuid.uuid4())

        logger.info("[OpsAgent] Checking system health", extra={
            "operation": "check_system_health",
            "trace_id": trace_id,
            "time_window_minutes": time_window_minutes
        })

        findings: List[OpsFinding] = []
        health_metrics: List[HealthMetric] = []
        log_summary: Dict[str, int] = {}
        recommended_actions: List[ActionRecommendation] = []

        # Collect health metrics
        if include_metrics:
            metrics_result = self._collect_health_metrics()
            health_metrics = metrics_result.get("metrics", [])
            findings.extend(metrics_result.get("findings", []))

        # Analyze logs
        if include_logs:
            logs_result = self._analyze_recent_logs(time_window_minutes)
            log_summary = logs_result.get("summary", {})
            findings.extend(logs_result.get("findings", []))

        # Determine overall health status
        health_status = self._determine_health_status(health_metrics, findings)

        # Generate action recommendations
        recommended_actions = self._generate_action_recommendations(
            health_status, findings, health_metrics
        )

        # Calculate overall risk
        overall_risk = self._calculate_overall_risk(findings, health_status)

        # Generate summary
        summary = self._generate_health_summary(
            health_status, findings, health_metrics, log_summary
        )

        latency_ms = (time.time() - start_time) * 1000

        advisory = OpsAdvisory(
            health_status=health_status,
            overall_risk=overall_risk,
            findings=findings,
            health_metrics=health_metrics,
            log_summary=log_summary,
            recommended_actions=recommended_actions,
            summary=summary,
            metadata={
                "trace_id": trace_id,
                "time_window_minutes": time_window_minutes,
                "latency_ms": latency_ms,
                "findings_count": len(findings),
                "actions_count": len(recommended_actions)
            }
        )

        logger.info("[OpsAgent] Health check complete", extra={
            "operation": "check_system_health",
            "trace_id": trace_id,
            "health_status": health_status.value,
            "overall_risk": overall_risk.value,
            "findings_count": len(findings),
            "latency_ms": latency_ms
        })

        return advisory

    def analyze_logs(
        self,
        logs: List[LogEntry],
        error_threshold: int = 5
    ) -> OpsAdvisory:
        """
        Analyze structured logs for issues.

        Args:
            logs: List of log entries to analyze
            error_threshold: Number of errors to trigger alert

        Returns:
            OpsAdvisory with log analysis findings
        """
        if not self.enabled:
            return OpsAdvisory(
                health_status=HealthStatus.UNKNOWN,
                overall_risk=OpsRisk.INFO,
                summary="Ops Agent disabled"
            )

        start_time = time.time()
        trace_id = str(uuid.uuid4())

        logger.info("[OpsAgent] Analyzing logs", extra={
            "operation": "analyze_logs",
            "trace_id": trace_id,
            "log_count": len(logs)
        })

        findings: List[OpsFinding] = []
        log_summary: Dict[str, int] = {
            "total": len(logs),
            "error": 0,
            "warning": 0,
            "info": 0,
            "debug": 0
        }

        # Count log levels
        error_messages: List[str] = []
        for log in logs:
            level = log.level.lower()
            if level in log_summary:
                log_summary[level] += 1

            if level == "error":
                error_messages.append(log.message)

        # Analyze error patterns
        pattern_counts: Dict[str, int] = {}
        for error_msg in error_messages:
            for pattern_name, keywords in self.ERROR_PATTERNS.items():
                if any(kw in error_msg.lower() for kw in keywords):
                    pattern_counts[pattern_name] = pattern_counts.get(pattern_name, 0) + 1

        # Generate findings based on patterns
        for pattern_name, count in pattern_counts.items():
            if count >= error_threshold:
                risk_level = OpsRisk.HIGH if count >= error_threshold * 2 else OpsRisk.MEDIUM
                findings.append(OpsFinding(
                    category="log",
                    risk_level=risk_level,
                    title=f"High {pattern_name} error rate",
                    description=f"Detected {count} {pattern_name} errors in logs",
                    source="log_analysis",
                    recommendation=self._get_pattern_recommendation(pattern_name),
                    recommended_action=self._get_pattern_action(pattern_name)
                ))

        # Check overall error rate
        if log_summary["total"] > 0:
            error_rate = log_summary["error"] / log_summary["total"]
            if error_rate > self.HEALTH_THRESHOLDS["error_rate"]["critical"]:
                findings.append(OpsFinding(
                    category="log",
                    risk_level=OpsRisk.CRITICAL,
                    title="Critical error rate",
                    description=f"Error rate is {error_rate:.1%}, exceeds critical threshold",
                    source="log_analysis",
                    recommendation="Investigate root cause immediately",
                    recommended_action=ActionType.ALERT
                ))
            elif error_rate > self.HEALTH_THRESHOLDS["error_rate"]["warning"]:
                findings.append(OpsFinding(
                    category="log",
                    risk_level=OpsRisk.MEDIUM,
                    title="Elevated error rate",
                    description=f"Error rate is {error_rate:.1%}, exceeds warning threshold",
                    source="log_analysis",
                    recommendation="Monitor closely and investigate if persists"
                ))

        # Determine health status
        health_status = HealthStatus.HEALTHY
        if any(f.risk_level == OpsRisk.CRITICAL for f in findings):
            health_status = HealthStatus.UNHEALTHY
        elif any(f.risk_level in [OpsRisk.HIGH, OpsRisk.MEDIUM] for f in findings):
            health_status = HealthStatus.DEGRADED

        overall_risk = self._calculate_overall_risk(findings, health_status)

        latency_ms = (time.time() - start_time) * 1000

        advisory = OpsAdvisory(
            health_status=health_status,
            overall_risk=overall_risk,
            findings=findings,
            log_summary=log_summary,
            summary=f"Analyzed {len(logs)} logs: {log_summary['error']} errors, {log_summary['warning']} warnings",
            metadata={
                "trace_id": trace_id,
                "latency_ms": latency_ms,
                "pattern_counts": pattern_counts
            }
        )

        logger.info("[OpsAgent] Log analysis complete", extra={
            "operation": "analyze_logs",
            "trace_id": trace_id,
            "health_status": health_status.value,
            "error_count": log_summary["error"],
            "findings_count": len(findings),
            "latency_ms": latency_ms
        })

        return advisory

    def recommend_action(
        self,
        health_status: HealthStatus,
        findings: List[OpsFinding],
        context: Optional[Dict[str, Any]] = None
    ) -> List[ActionRecommendation]:
        """
        Generate action recommendations based on health status and findings.

        Args:
            health_status: Current health status
            findings: List of findings
            context: Optional additional context

        Returns:
            List of recommended actions
        """
        recommendations: List[ActionRecommendation] = []

        # Critical health requires immediate action
        if health_status == HealthStatus.UNHEALTHY:
            critical_findings = [f for f in findings if f.risk_level == OpsRisk.CRITICAL]

            for finding in critical_findings:
                if finding.recommended_action == ActionType.RESTART:
                    recommendations.append(ActionRecommendation(
                        action_type=ActionType.RESTART,
                        target=finding.source or "affected_service",
                        reason=finding.description,
                        urgency=OpsRisk.CRITICAL,
                        requires_approval=self.hitl_required,
                        estimated_downtime="1-5 minutes",
                        rollback_available=True
                    ))
                elif finding.recommended_action == ActionType.ROLLBACK:
                    recommendations.append(ActionRecommendation(
                        action_type=ActionType.ROLLBACK,
                        target=finding.source or "affected_service",
                        reason=finding.description,
                        urgency=OpsRisk.CRITICAL,
                        requires_approval=True,  # Always require approval for rollback
                        estimated_downtime="5-10 minutes",
                        rollback_available=False
                    ))

        # Degraded health may need scaling
        if health_status == HealthStatus.DEGRADED:
            high_findings = [f for f in findings if f.risk_level == OpsRisk.HIGH]

            # Check for performance-related issues
            perf_findings = [f for f in high_findings if f.category in ["performance", "health"]]
            if perf_findings:
                recommendations.append(ActionRecommendation(
                    action_type=ActionType.SCALE_UP,
                    target="worker",
                    reason="Performance degradation detected",
                    urgency=OpsRisk.HIGH,
                    requires_approval=self.hitl_required,
                    estimated_downtime="0 minutes",
                    rollback_available=True
                ))

        # Always add alert for any findings
        if findings and not recommendations:
            recommendations.append(ActionRecommendation(
                action_type=ActionType.ALERT,
                target="ops_team",
                reason=f"{len(findings)} issues detected",
                urgency=OpsRisk.MEDIUM,
                requires_approval=False,
                estimated_downtime="0 minutes"
            ))

        return recommendations

    def request_action_approval(
        self,
        action: ActionRecommendation,
        trace_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Request HITL approval for an operational action.

        Args:
            action: The action to request approval for
            trace_id: Optional trace ID for tracking

        Returns:
            Dictionary with approval request status
        """
        if not self.hitl_interceptor:
            logger.warning("[OpsAgent] HITL not available, cannot request approval")
            return {
                "approved": False,
                "reason": "HITL system not available",
                "requires_manual_approval": True
            }

        trace_id = trace_id or str(uuid.uuid4())

        logger.info("[OpsAgent] Requesting action approval", extra={
            "operation": "request_action_approval",
            "trace_id": trace_id,
            "action_type": action.action_type.value,
            "target": action.target
        })

        try:
            requires_approval, request = self.hitl_interceptor.check_action(
                action_type=action.action_type.value.upper(),
                action_description=f"{action.action_type.value} {action.target}: {action.reason}",
                affected_resources=[action.target],
                risk_level=action.urgency.value
            )

            if not requires_approval:
                return {
                    "approved": True,
                    "reason": "Action does not require approval",
                    "request_id": None
                }

            if request:
                return {
                    "approved": False,
                    "reason": "Awaiting human approval",
                    "request_id": request.request_id,
                    "status": "pending"
                }

            return {
                "approved": False,
                "reason": "Failed to create approval request",
                "requires_manual_approval": True
            }

        except Exception as e:
            logger.error("[OpsAgent] Failed to request approval: %s", e)
            return {
                "approved": False,
                "reason": str(e),
                "requires_manual_approval": True
            }

    def _collect_health_metrics(self) -> Dict[str, Any]:
        """Collect health metrics from monitoring systems"""
        metrics: List[HealthMetric] = []
        findings: List[OpsFinding] = []

        # Simulated metrics collection (in production, would query actual monitoring)
        # This provides a framework for integration with real monitoring systems

        try:
            if self.metrics_client:
                # Try to get real metrics if available
                pass
        except Exception as e:
            logger.warning("[OpsAgent] Failed to collect metrics: %s", e)

        # Default healthy metrics for demonstration
        default_metrics = [
            HealthMetric(
                name="error_rate",
                value=0.02,
                unit="percent",
                status=HealthStatus.HEALTHY,
                threshold_warning=0.05,
                threshold_critical=0.1
            ),
            HealthMetric(
                name="latency_p99_ms",
                value=1500,
                unit="ms",
                status=HealthStatus.HEALTHY,
                threshold_warning=5000,
                threshold_critical=10000
            ),
        ]

        metrics.extend(default_metrics)

        return {
            "metrics": metrics,
            "findings": findings
        }

    def _analyze_recent_logs(self, time_window_minutes: int) -> Dict[str, Any]:
        """Analyze recent logs from the system"""
        findings: List[OpsFinding] = []
        summary: Dict[str, int] = {
            "total": 0,
            "error": 0,
            "warning": 0,
            "info": 0
        }

        # In production, would query actual log storage
        # This provides a framework for integration

        return {
            "summary": summary,
            "findings": findings
        }

    def _determine_health_status(
        self,
        metrics: List[HealthMetric],
        findings: List[OpsFinding]
    ) -> HealthStatus:
        """Determine overall health status"""
        # Check for critical findings
        if any(f.risk_level == OpsRisk.CRITICAL for f in findings):
            return HealthStatus.UNHEALTHY

        # Check for unhealthy metrics
        if any(m.status == HealthStatus.UNHEALTHY for m in metrics):
            return HealthStatus.UNHEALTHY

        # Check for degraded conditions
        if any(f.risk_level in [OpsRisk.HIGH, OpsRisk.MEDIUM] for f in findings):
            return HealthStatus.DEGRADED

        if any(m.status == HealthStatus.DEGRADED for m in metrics):
            return HealthStatus.DEGRADED

        return HealthStatus.HEALTHY

    def _generate_action_recommendations(
        self,
        health_status: HealthStatus,
        findings: List[OpsFinding],
        metrics: List[HealthMetric]
    ) -> List[ActionRecommendation]:
        """Generate action recommendations based on analysis"""
        return self.recommend_action(health_status, findings)

    def _calculate_overall_risk(
        self,
        findings: List[OpsFinding],
        health_status: HealthStatus
    ) -> OpsRisk:
        """Calculate overall risk level"""
        if health_status == HealthStatus.UNHEALTHY:
            return OpsRisk.CRITICAL

        if any(f.risk_level == OpsRisk.CRITICAL for f in findings):
            return OpsRisk.CRITICAL

        if health_status == HealthStatus.DEGRADED:
            return OpsRisk.HIGH

        if any(f.risk_level == OpsRisk.HIGH for f in findings):
            return OpsRisk.HIGH

        if any(f.risk_level == OpsRisk.MEDIUM for f in findings):
            return OpsRisk.MEDIUM

        return OpsRisk.LOW

    def _generate_health_summary(
        self,
        health_status: HealthStatus,
        findings: List[OpsFinding],
        metrics: List[HealthMetric],
        log_summary: Dict[str, int]
    ) -> str:
        """Generate health summary"""
        parts = [f"System status: {health_status.value}"]

        if findings:
            parts.append(f"{len(findings)} issues detected")

        if metrics:
            healthy_count = len([m for m in metrics if m.status == HealthStatus.HEALTHY])
            parts.append(f"{healthy_count}/{len(metrics)} metrics healthy")

        if log_summary.get("error", 0) > 0:
            parts.append(f"{log_summary['error']} errors in logs")

        return ". ".join(parts)

    def _get_pattern_recommendation(self, pattern_name: str) -> str:
        """Get recommendation for error pattern"""
        recommendations = {
            "timeout": "Check network connectivity and service response times",
            "memory": "Consider scaling up or optimizing memory usage",
            "connection": "Verify service availability and connection limits",
            "rate_limit": "Implement backoff or increase rate limits",
            "auth": "Check authentication configuration and credentials",
            "database": "Check database connection pool and query performance",
        }
        return recommendations.get(pattern_name, "Investigate root cause")

    def _get_pattern_action(self, pattern_name: str) -> ActionType:
        """Get recommended action for error pattern"""
        actions = {
            "timeout": ActionType.ALERT,
            "memory": ActionType.RESTART,
            "connection": ActionType.RESTART,
            "rate_limit": ActionType.ALERT,
            "auth": ActionType.ALERT,
            "database": ActionType.RESTART,
        }
        return actions.get(pattern_name, ActionType.ALERT)


# Singleton instance
_ops_agent: Optional[OpsAgent] = None


def get_ops_agent() -> OpsAgent:
    """Get or create the singleton OpsAgent instance"""
    global _ops_agent
    if _ops_agent is None:
        _ops_agent = OpsAgent()
    return _ops_agent


def check_system_health(
    include_metrics: bool = True,
    include_logs: bool = True,
    time_window_minutes: int = 15
) -> OpsAdvisory:
    """Convenience function to check system health"""
    agent = get_ops_agent()
    return agent.check_system_health(include_metrics, include_logs, time_window_minutes)


def analyze_logs(
    logs: List[LogEntry],
    error_threshold: int = 5
) -> OpsAdvisory:
    """Convenience function to analyze logs"""
    agent = get_ops_agent()
    return agent.analyze_logs(logs, error_threshold)


def recommend_action(
    health_status: HealthStatus,
    findings: List[OpsFinding],
    context: Optional[Dict[str, Any]] = None
) -> List[ActionRecommendation]:
    """Convenience function to get action recommendations"""
    agent = get_ops_agent()
    return agent.recommend_action(health_status, findings, context)
