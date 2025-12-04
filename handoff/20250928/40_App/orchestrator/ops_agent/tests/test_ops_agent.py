#!/usr/bin/env python3
"""
Tests for Ops Agent - Phase 3 PR-3 (#1815)
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ops_agent.agent import (
    OpsAgent,
    OpsAdvisory,
    OpsFinding,
    OpsRisk,
    HealthStatus,
    ActionType,
    LogEntry,
    HealthMetric,
    ActionRecommendation,
    get_ops_agent,
    check_system_health,
    analyze_logs,
    recommend_action,
)


class TestOpsRisk:
    """Tests for OpsRisk enum"""

    def test_risk_values(self):
        """Test OpsRisk enum values"""
        assert OpsRisk.CRITICAL.value == "critical"
        assert OpsRisk.HIGH.value == "high"
        assert OpsRisk.MEDIUM.value == "medium"
        assert OpsRisk.LOW.value == "low"
        assert OpsRisk.INFO.value == "info"


class TestHealthStatus:
    """Tests for HealthStatus enum"""

    def test_health_status_values(self):
        """Test HealthStatus enum values"""
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"
        assert HealthStatus.UNKNOWN.value == "unknown"


class TestActionType:
    """Tests for ActionType enum"""

    def test_action_type_values(self):
        """Test ActionType enum values"""
        assert ActionType.RESTART.value == "restart"
        assert ActionType.ROLLBACK.value == "rollback"
        assert ActionType.SCALE_UP.value == "scale_up"
        assert ActionType.SCALE_DOWN.value == "scale_down"
        assert ActionType.ALERT.value == "alert"
        assert ActionType.NO_ACTION.value == "no_action"


class TestLogEntry:
    """Tests for LogEntry dataclass"""

    def test_log_entry_creation(self):
        """Test LogEntry creation"""
        entry = LogEntry(
            timestamp="2024-01-01T00:00:00Z",
            level="error",
            message="Test error message",
            source="test_service",
            trace_id="trace-123"
        )
        assert entry.level == "error"
        assert entry.message == "Test error message"
        assert entry.trace_id == "trace-123"


class TestHealthMetric:
    """Tests for HealthMetric dataclass"""

    def test_health_metric_creation(self):
        """Test HealthMetric creation"""
        metric = HealthMetric(
            name="error_rate",
            value=0.05,
            unit="percent",
            status=HealthStatus.HEALTHY,
            threshold_warning=0.1,
            threshold_critical=0.2
        )
        assert metric.name == "error_rate"
        assert metric.value == 0.05
        assert metric.status == HealthStatus.HEALTHY


class TestOpsFinding:
    """Tests for OpsFinding dataclass"""

    def test_finding_creation(self):
        """Test OpsFinding creation"""
        finding = OpsFinding(
            category="health",
            risk_level=OpsRisk.HIGH,
            title="High error rate",
            description="Error rate exceeds threshold",
            source="log_analysis",
            recommendation="Investigate root cause",
            recommended_action=ActionType.ALERT
        )
        assert finding.category == "health"
        assert finding.risk_level == OpsRisk.HIGH
        assert finding.recommended_action == ActionType.ALERT


class TestActionRecommendation:
    """Tests for ActionRecommendation dataclass"""

    def test_action_recommendation_creation(self):
        """Test ActionRecommendation creation"""
        action = ActionRecommendation(
            action_type=ActionType.RESTART,
            target="worker",
            reason="Memory leak detected",
            urgency=OpsRisk.HIGH,
            requires_approval=True,
            estimated_downtime="1-5 minutes"
        )
        assert action.action_type == ActionType.RESTART
        assert action.target == "worker"
        assert action.requires_approval is True


class TestOpsAdvisory:
    """Tests for OpsAdvisory dataclass"""

    def test_advisory_creation(self):
        """Test OpsAdvisory creation"""
        advisory = OpsAdvisory(
            health_status=HealthStatus.HEALTHY,
            overall_risk=OpsRisk.LOW,
            summary="System healthy"
        )
        assert advisory.health_status == HealthStatus.HEALTHY
        assert advisory.overall_risk == OpsRisk.LOW

    def test_advisory_to_dict(self):
        """Test OpsAdvisory to_dict method"""
        finding = OpsFinding(
            category="health",
            risk_level=OpsRisk.LOW,
            title="Test",
            description="Desc"
        )
        metric = HealthMetric(
            name="cpu",
            value=50.0,
            unit="percent",
            status=HealthStatus.HEALTHY
        )
        advisory = OpsAdvisory(
            health_status=HealthStatus.HEALTHY,
            overall_risk=OpsRisk.LOW,
            findings=[finding],
            health_metrics=[metric],
            summary="Test"
        )
        result = advisory.to_dict()
        assert result["health_status"] == "healthy"
        assert result["overall_risk"] == "low"
        assert len(result["findings"]) == 1
        assert len(result["health_metrics"]) == 1


class TestOpsAgent:
    """Tests for OpsAgent class"""

    def test_agent_initialization(self):
        """Test OpsAgent initialization"""
        agent = OpsAgent()
        assert agent.enabled is True
        assert agent.hitl_required is True

    def test_check_system_health(self):
        """Test system health check"""
        agent = OpsAgent()
        advisory = agent.check_system_health()
        assert advisory.health_status in [
            HealthStatus.HEALTHY,
            HealthStatus.DEGRADED,
            HealthStatus.UNHEALTHY,
            HealthStatus.UNKNOWN
        ]
        assert advisory.overall_risk is not None

    def test_check_system_health_disabled(self):
        """Test check_system_health when agent is disabled"""
        agent = OpsAgent()
        agent.enabled = False
        advisory = agent.check_system_health()
        assert advisory.health_status == HealthStatus.UNKNOWN
        assert "disabled" in advisory.summary.lower()

    def test_analyze_logs_empty(self):
        """Test log analysis with empty logs"""
        agent = OpsAgent()
        advisory = agent.analyze_logs([])
        assert advisory.log_summary["total"] == 0

    def test_analyze_logs_with_errors(self):
        """Test log analysis with error logs"""
        agent = OpsAgent()
        logs = [
            LogEntry("2024-01-01T00:00:00Z", "error", "Connection timeout", "service"),
            LogEntry("2024-01-01T00:00:01Z", "error", "Connection timeout", "service"),
            LogEntry("2024-01-01T00:00:02Z", "error", "Connection timeout", "service"),
            LogEntry("2024-01-01T00:00:03Z", "error", "Connection timeout", "service"),
            LogEntry("2024-01-01T00:00:04Z", "error", "Connection timeout", "service"),
            LogEntry("2024-01-01T00:00:05Z", "info", "Request processed", "service"),
        ]
        advisory = agent.analyze_logs(logs, error_threshold=5)
        assert advisory.log_summary["error"] == 5
        assert advisory.log_summary["info"] == 1

    def test_analyze_logs_pattern_detection(self):
        """Test log analysis detects error patterns"""
        agent = OpsAgent()
        logs = [
            LogEntry("2024-01-01T00:00:00Z", "error", "Out of memory error", "service"),
            LogEntry("2024-01-01T00:00:01Z", "error", "OOM killed", "service"),
            LogEntry("2024-01-01T00:00:02Z", "error", "Memory limit exceeded", "service"),
            LogEntry("2024-01-01T00:00:03Z", "error", "Heap overflow", "service"),
            LogEntry("2024-01-01T00:00:04Z", "error", "Memory allocation failed", "service"),
        ]
        advisory = agent.analyze_logs(logs, error_threshold=3)
        assert any(f.category == "log" for f in advisory.findings)

    def test_recommend_action_unhealthy(self):
        """Test action recommendations for unhealthy system"""
        agent = OpsAgent()
        findings = [
            OpsFinding(
                category="health",
                risk_level=OpsRisk.CRITICAL,
                title="Critical error",
                description="System critical",
                recommended_action=ActionType.RESTART
            )
        ]
        actions = agent.recommend_action(HealthStatus.UNHEALTHY, findings)
        assert len(actions) > 0

    def test_recommend_action_healthy(self):
        """Test action recommendations for healthy system"""
        agent = OpsAgent()
        actions = agent.recommend_action(HealthStatus.HEALTHY, [])
        assert len(actions) == 0 or all(
            a.action_type == ActionType.NO_ACTION for a in actions
        )

    def test_get_pattern_recommendation(self):
        """Test pattern-specific recommendations"""
        agent = OpsAgent()
        assert "memory" in agent._get_pattern_recommendation("memory").lower()
        assert "connection" in agent._get_pattern_recommendation("connection").lower()

    def test_get_pattern_action(self):
        """Test pattern-specific actions"""
        agent = OpsAgent()
        assert agent._get_pattern_action("memory") == ActionType.RESTART
        assert agent._get_pattern_action("timeout") == ActionType.ALERT

    def test_determine_health_status(self):
        """Test health status determination"""
        agent = OpsAgent()

        critical_findings = [
            OpsFinding("test", OpsRisk.CRITICAL, "Critical", "Desc")
        ]
        status = agent._determine_health_status([], critical_findings)
        assert status == HealthStatus.UNHEALTHY

        medium_findings = [
            OpsFinding("test", OpsRisk.MEDIUM, "Medium", "Desc")
        ]
        status = agent._determine_health_status([], medium_findings)
        assert status == HealthStatus.DEGRADED

        status = agent._determine_health_status([], [])
        assert status == HealthStatus.HEALTHY

    def test_calculate_overall_risk(self):
        """Test overall risk calculation"""
        agent = OpsAgent()

        critical_findings = [
            OpsFinding("test", OpsRisk.CRITICAL, "Critical", "Desc")
        ]
        risk = agent._calculate_overall_risk(critical_findings, HealthStatus.UNHEALTHY)
        assert risk == OpsRisk.CRITICAL

        risk = agent._calculate_overall_risk([], HealthStatus.HEALTHY)
        assert risk == OpsRisk.LOW


class TestConvenienceFunctions:
    """Tests for module-level convenience functions"""

    def test_get_ops_agent_singleton(self):
        """Test get_ops_agent returns singleton"""
        agent1 = get_ops_agent()
        agent2 = get_ops_agent()
        assert agent1 is agent2

    def test_check_system_health_function(self):
        """Test check_system_health convenience function"""
        advisory = check_system_health()
        assert isinstance(advisory, OpsAdvisory)

    def test_analyze_logs_function(self):
        """Test analyze_logs convenience function"""
        advisory = analyze_logs([])
        assert isinstance(advisory, OpsAdvisory)

    def test_recommend_action_function(self):
        """Test recommend_action convenience function"""
        actions = recommend_action(HealthStatus.HEALTHY, [])
        assert isinstance(actions, list)


class TestEdgeCases:
    """Tests for edge cases"""

    def test_empty_log_message(self):
        """Test handling of empty log message"""
        agent = OpsAgent()
        logs = [LogEntry("2024-01-01T00:00:00Z", "error", "", "service")]
        advisory = agent.analyze_logs(logs)
        assert advisory is not None

    def test_mixed_log_levels(self):
        """Test handling of mixed log levels"""
        agent = OpsAgent()
        logs = [
            LogEntry("2024-01-01T00:00:00Z", "error", "Error", "service"),
            LogEntry("2024-01-01T00:00:01Z", "warning", "Warning", "service"),
            LogEntry("2024-01-01T00:00:02Z", "info", "Info", "service"),
            LogEntry("2024-01-01T00:00:03Z", "debug", "Debug", "service"),
        ]
        advisory = agent.analyze_logs(logs)
        assert advisory.log_summary["error"] == 1
        assert advisory.log_summary["warning"] == 1
        assert advisory.log_summary["info"] == 1
        assert advisory.log_summary["debug"] == 1

    def test_unicode_log_message(self):
        """Test handling of unicode in log messages"""
        agent = OpsAgent()
        logs = [LogEntry("2024-01-01T00:00:00Z", "error", "錯誤訊息", "service")]
        advisory = agent.analyze_logs(logs)
        assert advisory is not None
