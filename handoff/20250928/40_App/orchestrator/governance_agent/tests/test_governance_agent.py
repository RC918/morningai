#!/usr/bin/env python3
"""
Tests for Governance Agent - Phase 4 PR-3

Comprehensive test suite for GovernanceAgent functionality.
"""
from unittest.mock import Mock, patch

from ..agent import (
    GovernanceAgent,
    GovernanceRisk,
    GovernanceFinding,
    GovernanceAdvisory,
    get_governance_agent,
    analyze_governance,
)


class TestGovernanceRisk:
    """Tests for GovernanceRisk enum"""

    def test_risk_levels_exist(self):
        """Test all risk levels are defined"""
        assert GovernanceRisk.CRITICAL.value == "critical"
        assert GovernanceRisk.HIGH.value == "high"
        assert GovernanceRisk.MEDIUM.value == "medium"
        assert GovernanceRisk.LOW.value == "low"
        assert GovernanceRisk.INFO.value == "info"

    def test_risk_level_count(self):
        """Test correct number of risk levels"""
        assert len(GovernanceRisk) == 5


class TestGovernanceFinding:
    """Tests for GovernanceFinding dataclass"""

    def test_create_finding(self):
        """Test creating a governance finding"""
        finding = GovernanceFinding(
            category="policy",
            risk_level=GovernanceRisk.HIGH,
            title="Test Finding",
            description="Test description"
        )
        assert finding.category == "policy"
        assert finding.risk_level == GovernanceRisk.HIGH
        assert finding.title == "Test Finding"
        assert finding.description == "Test description"

    def test_finding_with_optional_fields(self):
        """Test finding with all optional fields"""
        finding = GovernanceFinding(
            category="cost",
            risk_level=GovernanceRisk.MEDIUM,
            title="Budget Warning",
            description="Budget at 80%",
            source="CostTracker",
            recommendation="Monitor usage",
            metadata={"percent": 80}
        )
        assert finding.source == "CostTracker"
        assert finding.recommendation == "Monitor usage"
        assert finding.metadata == {"percent": 80}


class TestGovernanceAdvisory:
    """Tests for GovernanceAdvisory dataclass"""

    def test_create_advisory(self):
        """Test creating a governance advisory"""
        advisory = GovernanceAdvisory(
            is_compliant=True,
            overall_risk=GovernanceRisk.INFO
        )
        assert advisory.is_compliant is True
        assert advisory.overall_risk == GovernanceRisk.INFO
        assert advisory.findings == []
        assert advisory.summary == ""

    def test_advisory_to_dict(self):
        """Test advisory serialization"""
        finding = GovernanceFinding(
            category="policy",
            risk_level=GovernanceRisk.HIGH,
            title="Test",
            description="Test desc",
            source="PolicyGuard",
            recommendation="Fix it"
        )
        advisory = GovernanceAdvisory(
            is_compliant=False,
            overall_risk=GovernanceRisk.HIGH,
            findings=[finding],
            summary="1 issue found",
            recommendations=["Fix it"],
            policy_status={"violations": 1}
        )

        result = advisory.to_dict()

        assert result["is_compliant"] is False
        assert result["overall_risk"] == "high"
        assert len(result["findings"]) == 1
        assert result["findings"][0]["category"] == "policy"
        assert result["findings"][0]["risk_level"] == "high"
        assert result["summary"] == "1 issue found"
        assert result["policy_status"] == {"violations": 1}


class TestGovernanceAgentInit:
    """Tests for GovernanceAgent initialization"""

    def test_agent_initialization(self):
        """Test agent initializes correctly"""
        with patch('governance_agent.agent.GovernanceAgent._load_settings'):
            with patch('governance_agent.agent.GovernanceAgent._init_governance_modules'):
                agent = GovernanceAgent()
                assert agent is not None

    def test_agent_default_settings(self):
        """Test agent has default settings when settings unavailable"""
        with patch('governance_agent.agent.GovernanceAgent._init_governance_modules'):
            agent = GovernanceAgent()
            assert agent.enabled is True
            assert agent.strict_mode is False


class TestGovernanceAgentPolicyCompliance:
    """Tests for policy compliance analysis"""

    def test_analyze_policy_no_guard(self):
        """Test policy analysis when PolicyGuard not available"""
        with patch('governance_agent.agent.GovernanceAgent._load_settings'):
            with patch('governance_agent.agent.GovernanceAgent._init_governance_modules'):
                agent = GovernanceAgent()
                agent.policy_guard = None

                advisory = agent.analyze_policy_compliance(
                    file_paths=["test.py"],
                    operations=["read"]
                )

                assert advisory.is_compliant is True
                assert advisory.overall_risk == GovernanceRisk.INFO
                assert "PolicyGuard not available" in advisory.summary

    def test_analyze_policy_file_access_allowed(self):
        """Test policy analysis with allowed file access"""
        with patch('governance_agent.agent.GovernanceAgent._load_settings'):
            with patch('governance_agent.agent.GovernanceAgent._init_governance_modules'):
                agent = GovernanceAgent()

                mock_guard = Mock()
                mock_guard.check_file_access.return_value = True
                mock_guard.check_risk_level.return_value = "low_risk"
                mock_guard.check_tool_permission.return_value = True
                agent.policy_guard = mock_guard

                advisory = agent.analyze_policy_compliance(
                    file_paths=["src/app.py"],
                    operations=["read"]
                )

                assert advisory.is_compliant is True
                assert len([f for f in advisory.findings if f.risk_level == GovernanceRisk.HIGH]) == 0

    def test_analyze_policy_file_access_denied(self):
        """Test policy analysis with denied file access"""
        with patch('governance_agent.agent.GovernanceAgent._load_settings'):
            with patch('governance_agent.agent.GovernanceAgent._init_governance_modules'):
                agent = GovernanceAgent()

                mock_guard = Mock()
                mock_guard.check_file_access.side_effect = Exception("File access denied: .env")
                mock_guard.check_risk_level.return_value = "high_risk"
                agent.policy_guard = mock_guard

                advisory = agent.analyze_policy_compliance(
                    file_paths=[".env"]
                )

                assert advisory.is_compliant is False
                assert len([f for f in advisory.findings if f.category == "policy"]) > 0

    def test_analyze_policy_high_risk_files(self):
        """Test policy analysis detects high risk files"""
        with patch('governance_agent.agent.GovernanceAgent._load_settings'):
            with patch('governance_agent.agent.GovernanceAgent._init_governance_modules'):
                agent = GovernanceAgent()

                mock_guard = Mock()
                mock_guard.check_file_access.return_value = True
                mock_guard.check_risk_level.return_value = "high_risk"
                mock_guard.check_tool_permission.return_value = True
                agent.policy_guard = mock_guard

                advisory = agent.analyze_policy_compliance(
                    file_paths=["config/production.yaml"]
                )

                assert advisory.policy_status["risk_level"] == "high_risk"
                assert any(f.title == "High Risk File Pattern Detected" for f in advisory.findings)


class TestGovernanceAgentViolations:
    """Tests for violation detection"""

    def test_analyze_violations_no_detector(self):
        """Test violation analysis when ViolationDetector not available"""
        with patch('governance_agent.agent.GovernanceAgent._load_settings'):
            with patch('governance_agent.agent.GovernanceAgent._init_governance_modules'):
                agent = GovernanceAgent()
                agent.violation_detector = None

                advisory = agent.analyze_violations(
                    content="test content",
                    operation="general"
                )

                assert advisory.is_compliant is True
                assert "ViolationDetector not available" in advisory.summary

    def test_analyze_violations_clean_content(self):
        """Test violation analysis with clean content"""
        with patch('governance_agent.agent.GovernanceAgent._load_settings'):
            with patch('governance_agent.agent.GovernanceAgent._init_governance_modules'):
                agent = GovernanceAgent()

                mock_detector = Mock()
                mock_detector.check_all.return_value = None
                mock_detector.check_secrets_access.return_value = None
                agent.violation_detector = mock_detector

                advisory = agent.analyze_violations(
                    content="print('hello world')",
                    operation="general"
                )

                assert advisory.is_compliant is True
                assert len(advisory.findings) == 0

    def test_analyze_violations_secrets_detected(self):
        """Test violation analysis detects secrets"""
        with patch('governance_agent.agent.GovernanceAgent._load_settings'):
            with patch('governance_agent.agent.GovernanceAgent._init_governance_modules'):
                agent = GovernanceAgent()

                mock_detector = Mock()
                mock_detector.check_all.return_value = None
                mock_detector.check_secrets_access.side_effect = Exception("Secrets access violation")
                agent.violation_detector = mock_detector

                advisory = agent.analyze_violations(
                    content="API_KEY=secret123",
                    operation="general"
                )

                assert advisory.is_compliant is False
                assert any(f.category == "violation" for f in advisory.findings)

    def test_analyze_violations_dangerous_command(self):
        """Test violation analysis detects dangerous commands"""
        with patch('governance_agent.agent.GovernanceAgent._load_settings'):
            with patch('governance_agent.agent.GovernanceAgent._init_governance_modules'):
                agent = GovernanceAgent()

                mock_detector = Mock()
                mock_detector.check_all.return_value = None
                mock_detector.check_secrets_access.return_value = None
                mock_detector.check_dangerous_operations.side_effect = Exception("Dangerous operation: rm -rf /")
                agent.violation_detector = mock_detector

                advisory = agent.analyze_violations(
                    content="rm -rf /",
                    operation="shell_command"
                )

                assert any(f.title == "Dangerous Operation Detected" for f in advisory.findings)


class TestGovernanceAgentCostBudget:
    """Tests for cost budget analysis"""

    def test_analyze_cost_no_tracker(self):
        """Test cost analysis when CostTracker not available"""
        with patch('governance_agent.agent.GovernanceAgent._load_settings'):
            with patch('governance_agent.agent.GovernanceAgent._init_governance_modules'):
                agent = GovernanceAgent()
                agent.cost_tracker = None

                advisory = agent.analyze_cost_budget(
                    trace_id="test-123",
                    estimated_tokens=1000
                )

                assert advisory.is_compliant is True
                assert "CostTracker not available" in advisory.summary

    def test_analyze_cost_within_budget(self):
        """Test cost analysis within budget"""
        with patch('governance_agent.agent.GovernanceAgent._load_settings'):
            with patch('governance_agent.agent.GovernanceAgent._init_governance_modules'):
                agent = GovernanceAgent()

                mock_tracker = Mock()
                mock_tracker.get_cost_summary.return_value = {
                    "daily": {"within_budget": True, "alert_level": "ok"},
                    "hourly": {"within_budget": True, "alert_level": "ok"},
                    "task": {"within_budget": True, "alert_level": "ok"}
                }
                mock_tracker.estimate_cost.return_value = 0.03
                agent.cost_tracker = mock_tracker

                advisory = agent.analyze_cost_budget(
                    trace_id="test-123",
                    estimated_tokens=1000
                )

                assert advisory.is_compliant is True
                assert advisory.cost_status["estimated_cost_usd"] == 0.03

    def test_analyze_cost_budget_exceeded(self):
        """Test cost analysis with exceeded budget"""
        with patch('governance_agent.agent.GovernanceAgent._load_settings'):
            with patch('governance_agent.agent.GovernanceAgent._init_governance_modules'):
                agent = GovernanceAgent()

                mock_tracker = Mock()
                mock_tracker.get_cost_summary.return_value = {
                    "daily": {"within_budget": False, "alert_level": "critical"},
                    "hourly": {"within_budget": True, "alert_level": "ok"},
                    "task": {"within_budget": True, "alert_level": "ok"}
                }
                agent.cost_tracker = mock_tracker

                advisory = agent.analyze_cost_budget(
                    trace_id="test-123"
                )

                assert advisory.is_compliant is False
                assert any(f.title == "Daily Budget Exceeded" for f in advisory.findings)

    def test_analyze_cost_warning_level(self):
        """Test cost analysis at warning level"""
        with patch('governance_agent.agent.GovernanceAgent._load_settings'):
            with patch('governance_agent.agent.GovernanceAgent._init_governance_modules'):
                agent = GovernanceAgent()

                mock_tracker = Mock()
                mock_tracker.get_cost_summary.return_value = {
                    "daily": {"within_budget": True, "alert_level": "warning"},
                    "hourly": {"within_budget": True, "alert_level": "ok"},
                    "task": {"within_budget": True, "alert_level": "ok"}
                }
                agent.cost_tracker = mock_tracker

                advisory = agent.analyze_cost_budget(
                    trace_id="test-123"
                )

                assert advisory.is_compliant is True
                assert any(f.title == "Daily Budget Warning" for f in advisory.findings)


class TestGovernanceAgentPermissions:
    """Tests for permission analysis"""

    def test_analyze_permissions_no_checker(self):
        """Test permission analysis when PermissionChecker not available"""
        with patch('governance_agent.agent.GovernanceAgent._load_settings'):
            with patch('governance_agent.agent.GovernanceAgent._init_governance_modules'):
                agent = GovernanceAgent()
                agent.permission_checker = None

                advisory = agent.analyze_permissions(
                    agent_id="agent-123",
                    operations=["create_pr"],
                    environment="sandbox"
                )

                assert advisory.is_compliant is True
                assert "PermissionChecker not available" in advisory.summary

    def test_analyze_permissions_allowed(self):
        """Test permission analysis with allowed operations"""
        with patch('governance_agent.agent.GovernanceAgent._load_settings'):
            with patch('governance_agent.agent.GovernanceAgent._init_governance_modules'):
                agent = GovernanceAgent()

                mock_checker = Mock()
                mock_checker.can_access_environment.return_value = True
                mock_checker.check_permission.return_value = True
                mock_checker.get_permission_summary.return_value = {"level": "staging_access"}
                agent.permission_checker = mock_checker

                advisory = agent.analyze_permissions(
                    agent_id="agent-123",
                    operations=["create_pr"],
                    environment="sandbox"
                )

                assert advisory.is_compliant is True
                assert len(advisory.permission_status["denied_operations"]) == 0

    def test_analyze_permissions_denied(self):
        """Test permission analysis with denied operations"""
        with patch('governance_agent.agent.GovernanceAgent._load_settings'):
            with patch('governance_agent.agent.GovernanceAgent._init_governance_modules'):
                agent = GovernanceAgent()

                mock_checker = Mock()
                mock_checker.can_access_environment.return_value = True
                mock_checker.check_permission.side_effect = Exception("Permission denied: deploy_prod")
                mock_checker.get_permission_summary.return_value = {"level": "sandbox_only"}
                agent.permission_checker = mock_checker

                advisory = agent.analyze_permissions(
                    agent_id="agent-123",
                    operations=["deploy_prod"],
                    environment="sandbox"
                )

                assert advisory.is_compliant is False
                assert "deploy_prod" in advisory.permission_status["denied_operations"]

    def test_analyze_permissions_environment_denied(self):
        """Test permission analysis with denied environment access"""
        with patch('governance_agent.agent.GovernanceAgent._load_settings'):
            with patch('governance_agent.agent.GovernanceAgent._init_governance_modules'):
                agent = GovernanceAgent()

                mock_checker = Mock()
                mock_checker.can_access_environment.return_value = False
                mock_checker.check_permission.return_value = True
                mock_checker.get_permission_summary.return_value = {"level": "sandbox_only"}
                agent.permission_checker = mock_checker

                advisory = agent.analyze_permissions(
                    agent_id="agent-123",
                    operations=["read"],
                    environment="production"
                )

                assert advisory.is_compliant is False
                assert any(f.title == "Environment Access Denied" for f in advisory.findings)


class TestGovernanceAgentHumanApproval:
    """Tests for human approval analysis"""

    def test_analyze_human_approval_no_guard(self):
        """Test human approval when PolicyGuard not available"""
        with patch('governance_agent.agent.GovernanceAgent._load_settings'):
            with patch('governance_agent.agent.GovernanceAgent._init_governance_modules'):
                agent = GovernanceAgent()
                agent.policy_guard = None

                advisory = agent.analyze_human_approval(
                    labels=["feature"],
                    file_paths=["src/app.py"]
                )

                assert advisory.is_compliant is True
                assert "PolicyGuard not available" in advisory.summary

    def test_analyze_human_approval_not_required(self):
        """Test human approval not required"""
        with patch('governance_agent.agent.GovernanceAgent._load_settings'):
            with patch('governance_agent.agent.GovernanceAgent._init_governance_modules'):
                agent = GovernanceAgent()

                mock_guard = Mock()
                mock_guard.check_risk_level.return_value = "low_risk"
                mock_guard.requires_human_approval.return_value = False
                agent.policy_guard = mock_guard

                advisory = agent.analyze_human_approval(
                    labels=["docs"],
                    file_paths=["README.md"]
                )

                assert advisory.is_compliant is True
                assert advisory.metadata.get("requires_human_approval") is False

    def test_analyze_human_approval_required(self):
        """Test human approval required"""
        with patch('governance_agent.agent.GovernanceAgent._load_settings'):
            with patch('governance_agent.agent.GovernanceAgent._init_governance_modules'):
                agent = GovernanceAgent()

                mock_guard = Mock()
                mock_guard.check_risk_level.return_value = "high_risk"
                mock_guard.requires_human_approval.return_value = True
                agent.policy_guard = mock_guard

                advisory = agent.analyze_human_approval(
                    labels=["security"],
                    file_paths=["config/production.yaml"]
                )

                assert advisory.is_compliant is False
                assert advisory.metadata.get("requires_human_approval") is True
                assert any(f.title == "Human Approval Required" for f in advisory.findings)


class TestGovernanceAgentAnalyzeTask:
    """Tests for comprehensive task analysis"""

    def test_analyze_task_clean(self):
        """Test task analysis with no issues"""
        with patch('governance_agent.agent.GovernanceAgent._load_settings'):
            with patch('governance_agent.agent.GovernanceAgent._init_governance_modules'):
                agent = GovernanceAgent()

                mock_guard = Mock()
                mock_guard.check_file_access.return_value = True
                mock_guard.check_risk_level.return_value = "low_risk"
                mock_guard.check_tool_permission.return_value = True
                mock_guard.requires_human_approval.return_value = False
                agent.policy_guard = mock_guard

                mock_detector = Mock()
                mock_detector.check_all.return_value = None
                mock_detector.check_secrets_access.return_value = None
                agent.violation_detector = mock_detector

                mock_tracker = Mock()
                mock_tracker.get_cost_summary.return_value = {
                    "daily": {"within_budget": True, "alert_level": "ok"},
                    "hourly": {"within_budget": True, "alert_level": "ok"},
                    "task": {"within_budget": True, "alert_level": "ok"}
                }
                agent.cost_tracker = mock_tracker

                mock_checker = Mock()
                mock_checker.can_access_environment.return_value = True
                mock_checker.check_permission.return_value = True
                mock_checker.get_permission_summary.return_value = {}
                agent.permission_checker = mock_checker

                advisory = agent.analyze_task(
                    task_type="code_review",
                    trace_id="test-123",
                    agent_id="agent-123",
                    file_paths=["src/app.py"],
                    operations=["read"],
                    content="print('hello')",
                    labels=["feature"],
                    environment="sandbox"
                )

                assert advisory.is_compliant is True
                assert advisory.metadata["task_type"] == "code_review"
                assert advisory.metadata["trace_id"] == "test-123"

    def test_analyze_task_with_issues(self):
        """Test task analysis with multiple issues"""
        with patch('governance_agent.agent.GovernanceAgent._load_settings'):
            with patch('governance_agent.agent.GovernanceAgent._init_governance_modules'):
                agent = GovernanceAgent()

                mock_guard = Mock()
                mock_guard.check_file_access.side_effect = Exception("Access denied")
                mock_guard.check_risk_level.return_value = "high_risk"
                mock_guard.requires_human_approval.return_value = True
                agent.policy_guard = mock_guard

                mock_detector = Mock()
                mock_detector.check_all.return_value = None
                mock_detector.check_secrets_access.side_effect = Exception("Secrets detected")
                agent.violation_detector = mock_detector

                mock_tracker = Mock()
                mock_tracker.get_cost_summary.return_value = {
                    "daily": {"within_budget": False, "alert_level": "critical"}
                }
                agent.cost_tracker = mock_tracker

                mock_checker = Mock()
                mock_checker.can_access_environment.return_value = False
                mock_checker.check_permission.side_effect = Exception("Permission denied")
                mock_checker.get_permission_summary.return_value = {}
                agent.permission_checker = mock_checker

                advisory = agent.analyze_task(
                    task_type="deploy",
                    trace_id="test-456",
                    agent_id="agent-456",
                    file_paths=[".env"],
                    operations=["deploy_prod"],
                    content="API_KEY=secret",
                    labels=["security"],
                    environment="production"
                )

                assert advisory.is_compliant is False
                assert len(advisory.findings) > 0
                assert advisory.overall_risk in [GovernanceRisk.CRITICAL, GovernanceRisk.HIGH]


class TestGovernanceAgentHelpers:
    """Tests for helper methods"""

    def test_calculate_overall_risk_empty(self):
        """Test risk calculation with no findings"""
        with patch('governance_agent.agent.GovernanceAgent._load_settings'):
            with patch('governance_agent.agent.GovernanceAgent._init_governance_modules'):
                agent = GovernanceAgent()
                risk = agent._calculate_overall_risk([])
                assert risk == GovernanceRisk.INFO

    def test_calculate_overall_risk_critical(self):
        """Test risk calculation with critical finding"""
        with patch('governance_agent.agent.GovernanceAgent._load_settings'):
            with patch('governance_agent.agent.GovernanceAgent._init_governance_modules'):
                agent = GovernanceAgent()
                findings = [
                    GovernanceFinding("policy", GovernanceRisk.LOW, "Low", "desc"),
                    GovernanceFinding("cost", GovernanceRisk.CRITICAL, "Critical", "desc"),
                    GovernanceFinding("permission", GovernanceRisk.MEDIUM, "Medium", "desc"),
                ]
                risk = agent._calculate_overall_risk(findings)
                assert risk == GovernanceRisk.CRITICAL

    def test_generate_recommendations_unique(self):
        """Test recommendations are unique"""
        with patch('governance_agent.agent.GovernanceAgent._load_settings'):
            with patch('governance_agent.agent.GovernanceAgent._init_governance_modules'):
                agent = GovernanceAgent()
                findings = [
                    GovernanceFinding("policy", GovernanceRisk.HIGH, "F1", "d1", recommendation="Fix A"),
                    GovernanceFinding("cost", GovernanceRisk.HIGH, "F2", "d2", recommendation="Fix A"),
                    GovernanceFinding("permission", GovernanceRisk.HIGH, "F3", "d3", recommendation="Fix B"),
                ]
                recommendations = agent._generate_recommendations(findings)
                assert len(recommendations) == 2
                assert "Fix A" in recommendations
                assert "Fix B" in recommendations

    def test_generate_summary_no_findings(self):
        """Test summary with no findings"""
        with patch('governance_agent.agent.GovernanceAgent._load_settings'):
            with patch('governance_agent.agent.GovernanceAgent._init_governance_modules'):
                agent = GovernanceAgent()
                summary = agent._generate_summary([], "governance")
                assert "No governance issues detected" in summary

    def test_generate_summary_with_findings(self):
        """Test summary with findings"""
        with patch('governance_agent.agent.GovernanceAgent._load_settings'):
            with patch('governance_agent.agent.GovernanceAgent._init_governance_modules'):
                agent = GovernanceAgent()
                findings = [
                    GovernanceFinding("policy", GovernanceRisk.CRITICAL, "F1", "d1"),
                    GovernanceFinding("cost", GovernanceRisk.HIGH, "F2", "d2"),
                    GovernanceFinding("permission", GovernanceRisk.MEDIUM, "F3", "d3"),
                ]
                summary = agent._generate_summary(findings, "governance")
                assert "3 governance findings" in summary
                assert "1 critical" in summary
                assert "1 high" in summary
                assert "1 medium" in summary


class TestModuleFunctions:
    """Tests for module-level functions"""

    def test_get_governance_agent_singleton(self):
        """Test singleton pattern for get_governance_agent"""
        import governance_agent.agent as agent_module
        agent_module._governance_agent = None

        with patch('governance_agent.agent.GovernanceAgent._load_settings'):
            with patch('governance_agent.agent.GovernanceAgent._init_governance_modules'):
                agent1 = get_governance_agent()
                agent2 = get_governance_agent()
                assert agent1 is agent2

        agent_module._governance_agent = None

    def test_analyze_governance_function(self):
        """Test convenience function analyze_governance"""
        import governance_agent.agent as agent_module
        agent_module._governance_agent = None

        with patch('governance_agent.agent.GovernanceAgent._load_settings'):
            with patch('governance_agent.agent.GovernanceAgent._init_governance_modules'):
                with patch.object(GovernanceAgent, 'analyze_task') as mock_analyze:
                    mock_analyze.return_value = GovernanceAdvisory(
                        is_compliant=True,
                        overall_risk=GovernanceRisk.INFO
                    )

                    result = analyze_governance(
                        task_type="test",
                        trace_id="test-123"
                    )

                    assert result.is_compliant is True
                    mock_analyze.assert_called_once()

        agent_module._governance_agent = None


class TestGovernanceAgentIntegration:
    """Integration tests for GovernanceAgent"""

    def test_full_governance_flow(self):
        """Test complete governance analysis flow"""
        with patch('governance_agent.agent.GovernanceAgent._load_settings'):
            with patch('governance_agent.agent.GovernanceAgent._init_governance_modules'):
                agent = GovernanceAgent()

                mock_guard = Mock()
                mock_guard.check_file_access.return_value = True
                mock_guard.check_risk_level.return_value = "medium_risk"
                mock_guard.check_tool_permission.return_value = True
                mock_guard.requires_human_approval.return_value = False
                agent.policy_guard = mock_guard

                mock_detector = Mock()
                mock_detector.check_all.return_value = None
                mock_detector.check_secrets_access.return_value = None
                agent.violation_detector = mock_detector

                mock_tracker = Mock()
                mock_tracker.get_cost_summary.return_value = {
                    "daily": {"within_budget": True, "alert_level": "warning"},
                    "hourly": {"within_budget": True, "alert_level": "ok"},
                    "task": {"within_budget": True, "alert_level": "ok"}
                }
                mock_tracker.estimate_cost.return_value = 0.05
                agent.cost_tracker = mock_tracker

                mock_checker = Mock()
                mock_checker.can_access_environment.return_value = True
                mock_checker.check_permission.return_value = True
                mock_checker.get_permission_summary.return_value = {"level": "staging_access"}
                agent.permission_checker = mock_checker

                advisory = agent.analyze_task(
                    task_type="feature_implementation",
                    trace_id="integration-test-123",
                    agent_id="test-agent",
                    file_paths=["src/feature.py", "tests/test_feature.py"],
                    operations=["create_file", "run_tests"],
                    content="def new_feature(): pass",
                    labels=["feature", "enhancement"],
                    environment="staging",
                    estimated_tokens=5000
                )

                assert advisory.is_compliant is True
                assert advisory.metadata["task_type"] == "feature_implementation"
                assert advisory.metadata["environment"] == "staging"
                assert advisory.cost_status["estimated_cost_usd"] == 0.05

    def test_governance_modules_integration(self):
        """Test that all governance modules are called"""
        with patch('governance_agent.agent.GovernanceAgent._load_settings'):
            with patch('governance_agent.agent.GovernanceAgent._init_governance_modules'):
                agent = GovernanceAgent()

                mock_guard = Mock()
                mock_guard.check_file_access.return_value = True
                mock_guard.check_risk_level.return_value = "low_risk"
                mock_guard.check_tool_permission.return_value = True
                mock_guard.requires_human_approval.return_value = False
                agent.policy_guard = mock_guard

                mock_detector = Mock()
                mock_detector.check_all.return_value = None
                mock_detector.check_secrets_access.return_value = None
                agent.violation_detector = mock_detector

                mock_tracker = Mock()
                mock_tracker.get_cost_summary.return_value = {
                    "daily": {"within_budget": True, "alert_level": "ok"}
                }
                agent.cost_tracker = mock_tracker

                mock_checker = Mock()
                mock_checker.can_access_environment.return_value = True
                mock_checker.check_permission.return_value = True
                mock_checker.get_permission_summary.return_value = {}
                agent.permission_checker = mock_checker

                agent.analyze_task(
                    task_type="test",
                    trace_id="test-123",
                    agent_id="agent-123",
                    file_paths=["test.py"],
                    operations=["read"],
                    content="test",
                    labels=["test"],
                    environment="sandbox"
                )

                mock_guard.check_file_access.assert_called()
                mock_guard.check_risk_level.assert_called()
                mock_guard.requires_human_approval.assert_called()
                mock_detector.check_all.assert_called()
                mock_detector.check_secrets_access.assert_called()
                mock_tracker.get_cost_summary.assert_called()
                mock_checker.can_access_environment.assert_called()
