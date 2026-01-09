"""
Tests for RuntimePolicyEnforcer - Safety Governor v2

Epic #2311 Phase 2: Policy 執行驗證

Test Cases:
1. deny write (should block)
2. deny network (should block)
3. exceed task budget (should block)
4. exceed daily budget (should block)
5. within budget (should allow)
6. risky action → require approval (should return pending state)
7. shell execution with dangerous patterns (should block)
8. read access to allowed files (should allow)
"""
import pytest
from unittest.mock import MagicMock, patch

from governance.runtime_policy_enforcer import (
    RuntimePolicyEnforcer,
    PolicyCheckResult,
    EnforcementAction,
    PolicyViolationType,
    get_runtime_policy_enforcer,
)


@pytest.fixture
def mock_settings():
    """Create mock settings"""
    settings = MagicMock()
    settings.cost_exceeded_action = "block"
    return settings


@pytest.fixture
def mock_policy_guard():
    """Create mock PolicyGuard"""
    guard = MagicMock()
    guard.check_file_access.return_value = True
    guard.check_network_access.return_value = True
    guard.check_risk_level.return_value = "low_risk"
    return guard


@pytest.fixture
def mock_cost_tracker():
    """Create mock CostTracker"""
    tracker = MagicMock()
    tracker.check_budget.return_value = (
        True,
        MagicMock(tokens=1000, usd=0.5, requests=10),
        {"max_tokens": 10000, "max_usd": 5.0},
    )
    tracker.estimate_cost.return_value = 0.03
    return tracker


@pytest.fixture
def enforcer(mock_settings, mock_policy_guard, mock_cost_tracker):
    """Create RuntimePolicyEnforcer with mocked dependencies"""
    enforcer = RuntimePolicyEnforcer(settings=mock_settings)
    enforcer._policy_guard = mock_policy_guard
    enforcer._cost_tracker = mock_cost_tracker
    return enforcer


class TestDenyWrite:
    """Test Case 1: deny write (should block)"""

    def test_deny_write_to_secrets_directory(self, enforcer, mock_policy_guard):
        """Write to secrets directory should be blocked"""
        from governance.policy_guard import PolicyViolation
        mock_policy_guard.check_file_access.side_effect = PolicyViolation("File access denied: ./secrets/api_key.txt")

        result = enforcer.check_resource_access("write", "./secrets/api_key.txt")

        assert not result.allowed
        assert result.action == EnforcementAction.BLOCK
        assert result.violation_type == PolicyViolationType.FILE_WRITE
        assert "denied" in result.reason.lower()

    def test_deny_write_to_env_file(self, enforcer, mock_policy_guard):
        """Write to .env file should be blocked"""
        from governance.policy_guard import PolicyViolation
        mock_policy_guard.check_file_access.side_effect = PolicyViolation("File access denied: .env")

        result = enforcer.check_resource_access("write", ".env")

        assert not result.allowed
        assert result.action == EnforcementAction.BLOCK


class TestDenyNetwork:
    """Test Case 2: deny network (should block)"""

    def test_deny_network_to_unauthorized_domain(self, enforcer, mock_policy_guard):
        """Network access to unauthorized domain should be blocked"""
        from governance.policy_guard import PolicyViolation
        mock_policy_guard.check_network_access.side_effect = PolicyViolation("Network access denied: malicious.com")

        result = enforcer.check_resource_access("network", "malicious.com")

        assert not result.allowed
        assert result.action == EnforcementAction.BLOCK
        assert result.violation_type == PolicyViolationType.NETWORK_ACCESS

    def test_allow_network_to_authorized_domain(self, enforcer, mock_policy_guard):
        """Network access to authorized domain should be allowed"""
        mock_policy_guard.check_network_access.return_value = True

        result = enforcer.check_resource_access("network", "api.github.com")

        assert result.allowed
        assert result.action == EnforcementAction.ALLOW


class TestExceedTaskBudget:
    """Test Case 3: exceed task budget (should block)"""

    def test_exceed_task_token_budget(self, enforcer, mock_cost_tracker):
        """Exceeding task token budget should block"""
        mock_cost_tracker.check_budget.return_value = (
            False,
            MagicMock(tokens=9500, usd=0.5, requests=10),
            {"max_tokens": 10000, "max_usd": 5.0},
        )

        result = enforcer.check_cost("task-123", 1000, "gpt-4")

        assert not result.allowed
        assert result.action == EnforcementAction.BLOCK
        assert "budget exceeded" in result.reason.lower()
        assert result.budget_type == "task"

    def test_exceed_task_usd_budget(self, enforcer, mock_cost_tracker):
        """Exceeding task USD budget should block"""
        mock_cost_tracker.check_budget.return_value = (
            False,
            MagicMock(tokens=5000, usd=0.48, requests=10),
            {"max_tokens": 10000, "max_usd": 0.5},
        )
        mock_cost_tracker.estimate_cost.return_value = 0.05

        result = enforcer.check_cost("task-123", 1000, "gpt-4")

        assert not result.allowed
        assert result.action == EnforcementAction.BLOCK


class TestExceedDailyBudget:
    """Test Case 4: exceed daily budget (should block)"""

    def test_exceed_daily_token_budget(self, enforcer, mock_cost_tracker):
        """Exceeding daily token budget should block"""
        def mock_check_budget(task_id, period):
            if period == "task":
                return (
                    True,
                    MagicMock(tokens=5000, usd=0.5, requests=10),
                    {"max_tokens": 100000, "max_usd": 50.0},
                )
            else:
                return (
                    True,
                    MagicMock(tokens=95000, usd=4.5, requests=100),
                    {"max_tokens": 100000, "max_usd": 5.0},
                )

        mock_cost_tracker.check_budget.side_effect = mock_check_budget

        result = enforcer.check_cost("task-123", 10000, "gpt-4")

        assert not result.allowed
        assert result.action == EnforcementAction.BLOCK
        assert result.budget_type == "daily"


class TestWithinBudget:
    """Test Case 5: within budget (should allow)"""

    def test_within_all_budgets(self, enforcer, mock_cost_tracker):
        """Operations within all budgets should be allowed"""
        mock_cost_tracker.check_budget.return_value = (
            True,
            MagicMock(tokens=1000, usd=0.1, requests=5),
            {"max_tokens": 10000, "max_usd": 5.0},
        )

        result = enforcer.check_cost("task-123", 500, "gpt-4")

        assert result.allowed
        assert result.action == EnforcementAction.ALLOW

    def test_within_budget_returns_current_usage(self, enforcer, mock_cost_tracker):
        """Within budget check should return current usage metrics"""
        def mock_check_budget(task_id, period):
            return (
                True,
                MagicMock(tokens=2000, usd=0.2, requests=10),
                {"max_tokens": 10000, "max_usd": 5.0},
            )

        mock_cost_tracker.check_budget.side_effect = mock_check_budget

        result = enforcer.check_cost("task-123", 500, "gpt-4")

        assert result.current_tokens == 2000
        assert result.max_tokens == 10000


class TestRiskyActionRequireApproval:
    """Test Case 6: risky action → require approval (should return pending state)"""

    def test_high_risk_write_requires_approval(self, enforcer, mock_policy_guard):
        """Write to high-risk file should require approval"""
        mock_policy_guard.check_file_access.return_value = True
        mock_policy_guard.check_risk_level.return_value = "high_risk"

        result = enforcer.check_resource_access("write", "./migrations/001_schema.sql")

        assert not result.allowed
        assert result.action == EnforcementAction.REQUIRE_APPROVAL
        assert result.violation_type == PolicyViolationType.FILE_WRITE
        assert "approval" in result.reason.lower()

    def test_delete_always_requires_approval(self, enforcer):
        """Delete operations should always require approval"""
        result = enforcer.check_resource_access("delete", "./some_file.txt")

        assert not result.allowed
        assert result.action == EnforcementAction.REQUIRE_APPROVAL
        assert result.violation_type == PolicyViolationType.FILE_DELETE


class TestShellExecution:
    """Test Case 7: shell execution with dangerous patterns (should block)"""

    def test_block_rm_rf_command(self, enforcer):
        """rm -rf command should be blocked"""
        result = enforcer.check_resource_access("execute", "rm -rf /")

        assert not result.allowed
        assert result.action == EnforcementAction.BLOCK
        assert result.violation_type == PolicyViolationType.SHELL_EXECUTION

    def test_block_sudo_command(self, enforcer):
        """sudo command should be blocked"""
        result = enforcer.check_resource_access("execute", "sudo apt-get install")

        assert not result.allowed
        assert result.action == EnforcementAction.BLOCK

    def test_block_chmod_777(self, enforcer):
        """chmod 777 command should be blocked"""
        result = enforcer.check_resource_access("execute", "chmod 777 /etc/passwd")

        assert not result.allowed
        assert result.action == EnforcementAction.BLOCK

    def test_allow_safe_shell_command(self, enforcer):
        """Safe shell commands should be allowed"""
        result = enforcer.check_resource_access("execute", "git status")

        assert result.allowed
        assert result.action == EnforcementAction.ALLOW


class TestReadAccess:
    """Test Case 8: read access to allowed files (should allow)"""

    def test_allow_read_access_to_docs(self, enforcer, mock_policy_guard):
        """Read access to docs should be allowed"""
        mock_policy_guard.check_file_access.return_value = True

        result = enforcer.check_resource_access("read", "./docs/README.md")

        assert result.allowed
        assert result.action == EnforcementAction.ALLOW

    def test_block_read_access_to_secrets(self, enforcer, mock_policy_guard):
        """Read access to secrets should be blocked"""
        from governance.policy_guard import PolicyViolation
        mock_policy_guard.check_file_access.side_effect = PolicyViolation("File access denied")

        result = enforcer.check_resource_access("read", "./secrets/api_key.txt")

        assert not result.allowed
        assert result.action == EnforcementAction.BLOCK


class TestCostExceededActions:
    """Test different actions when cost is exceeded"""

    def test_degrade_model_action(self, mock_settings, mock_policy_guard, mock_cost_tracker):
        """When cost_exceeded_action is 'degrade', should suggest cheaper model"""
        mock_settings.cost_exceeded_action = "degrade"
        enforcer = RuntimePolicyEnforcer(settings=mock_settings)
        enforcer._policy_guard = mock_policy_guard
        enforcer._cost_tracker = mock_cost_tracker

        mock_cost_tracker.check_budget.return_value = (
            False,
            MagicMock(tokens=9500, usd=0.5, requests=10),
            {"max_tokens": 10000, "max_usd": 5.0},
        )

        result = enforcer.check_cost("task-123", 1000, "gpt-4")

        assert not result.allowed
        assert result.action == EnforcementAction.DEGRADE_MODEL
        assert result.suggested_model == "gpt-3.5-turbo"

    def test_require_approval_action(self, mock_settings, mock_policy_guard, mock_cost_tracker):
        """When cost_exceeded_action is 'approval', should require approval"""
        mock_settings.cost_exceeded_action = "approval"
        enforcer = RuntimePolicyEnforcer(settings=mock_settings)
        enforcer._policy_guard = mock_policy_guard
        enforcer._cost_tracker = mock_cost_tracker

        mock_cost_tracker.check_budget.return_value = (
            False,
            MagicMock(tokens=9500, usd=0.5, requests=10),
            {"max_tokens": 10000, "max_usd": 5.0},
        )

        result = enforcer.check_cost("task-123", 1000, "gpt-4")

        assert not result.allowed
        assert result.action == EnforcementAction.REQUIRE_APPROVAL


class TestEnforcement:
    """Test enforcement execution"""

    def test_enforce_allowed_result(self, enforcer):
        """Allowed results should not be enforced"""
        check_result = PolicyCheckResult(
            allowed=True,
            action=EnforcementAction.ALLOW,
            reason="Access allowed",
        )

        result = enforcer.enforce(check_result)

        assert not result.enforced
        assert result.action_taken == EnforcementAction.ALLOW

    def test_enforce_blocked_result(self, enforcer):
        """Blocked results should be enforced"""
        check_result = PolicyCheckResult(
            allowed=False,
            action=EnforcementAction.BLOCK,
            reason="Access denied",
            violation_type=PolicyViolationType.FILE_WRITE,
        )

        result = enforcer.enforce(check_result)

        assert result.enforced
        assert result.action_taken == EnforcementAction.BLOCK


class TestTelemetry:
    """Test telemetry event generation"""

    def test_telemetry_event_contains_required_fields(self, enforcer, mock_policy_guard):
        """Telemetry events should contain required fields"""
        mock_policy_guard.check_file_access.return_value = True
        mock_policy_guard.check_risk_level.return_value = "low_risk"

        result = enforcer.check_resource_access("write", "./docs/test.md")

        assert "event_type" in result.telemetry_event
        assert "timestamp" in result.telemetry_event
        assert "component" in result.telemetry_event
        assert result.telemetry_event["component"] == "RuntimePolicyEnforcer"


class TestGlobalInstance:
    """Test global instance management"""

    def test_get_runtime_policy_enforcer_returns_singleton(self):
        """get_runtime_policy_enforcer should return singleton"""
        import governance.runtime_policy_enforcer as module
        module._runtime_policy_enforcer = None

        enforcer1 = get_runtime_policy_enforcer()
        enforcer2 = get_runtime_policy_enforcer()

        assert enforcer1 is enforcer2

        module._runtime_policy_enforcer = None


class TestSSOTTelemetryPhase2:
    """
    Issue #3578 Phase 2: SSOT Telemetry Schema v3 integration tests.

    Validates that RuntimePolicyEnforcer correctly emits TelemetryRecordV3 spans
    when ENABLE_SSOT_TELEMETRY is enabled.
    """

    def test_telemetry_event_includes_trace_id_from_context(self, mock_settings, mock_policy_guard, mock_cost_tracker):
        """Telemetry event should include trace_id from context"""
        mock_settings.enable_ssot_telemetry = False
        enforcer = RuntimePolicyEnforcer(settings=mock_settings)
        enforcer._policy_guard = mock_policy_guard
        enforcer._cost_tracker = mock_cost_tracker

        context = {
            "trace_id": "test-trace-123",
            "current_span_id": "parent-span-456",
        }

        result = enforcer.check_resource_access("read", "./docs/test.md", context=context)

        assert result.telemetry_event.get("trace_id") == "test-trace-123"
        assert result.telemetry_event.get("parent_span_id") == "parent-span-456"

    def test_telemetry_event_includes_parent_span_id_from_context(self, mock_settings, mock_policy_guard, mock_cost_tracker):
        """Telemetry event should include parent_span_id from context"""
        mock_settings.enable_ssot_telemetry = False
        enforcer = RuntimePolicyEnforcer(settings=mock_settings)
        enforcer._policy_guard = mock_policy_guard
        enforcer._cost_tracker = mock_cost_tracker

        context = {
            "trace_id": "test-trace-789",
            "parent_span_id": "explicit-parent-span",
        }

        result = enforcer.check_resource_access("read", "./docs/test.md", context=context)

        assert result.telemetry_event.get("trace_id") == "test-trace-789"
        assert result.telemetry_event.get("parent_span_id") == "explicit-parent-span"

    def test_cost_check_telemetry_includes_trace_id(self, mock_settings, mock_policy_guard, mock_cost_tracker):
        """Cost check telemetry should include trace_id from context"""
        mock_settings.enable_ssot_telemetry = False
        enforcer = RuntimePolicyEnforcer(settings=mock_settings)
        enforcer._policy_guard = mock_policy_guard
        enforcer._cost_tracker = mock_cost_tracker

        context = {
            "trace_id": "cost-trace-123",
            "current_span_id": "cost-parent-span",
        }

        result = enforcer.check_cost("task-123", 500, "gpt-4", context=context)

        assert result.telemetry_event.get("trace_id") == "cost-trace-123"
        assert result.telemetry_event.get("parent_span_id") == "cost-parent-span"

    def test_ssot_telemetry_emits_when_enabled(self, mock_settings, mock_policy_guard, mock_cost_tracker):
        """SSOT telemetry should emit TelemetryRecordV3 when enabled"""
        mock_settings.enable_ssot_telemetry = True
        enforcer = RuntimePolicyEnforcer(settings=mock_settings)
        enforcer._policy_guard = mock_policy_guard
        enforcer._cost_tracker = mock_cost_tracker

        context = {
            "trace_id": "ssot-trace-123",
            "current_span_id": "ssot-parent-span",
        }

        with patch("core.telemetry.from_policy_telemetry_event") as mock_adapter:
            mock_record = MagicMock()
            mock_adapter.return_value = mock_record

            enforcer.check_resource_access("read", "./docs/test.md", context=context)

            mock_adapter.assert_called()
            call_args = mock_adapter.call_args
            assert call_args.kwargs["trace_id"] == "ssot-trace-123"
            assert call_args.kwargs["parent_span_id"] == "ssot-parent-span"
            mock_record.emit.assert_called_once()

    def test_ssot_telemetry_skipped_without_trace_id(self, mock_settings, mock_policy_guard, mock_cost_tracker):
        """SSOT telemetry should be skipped if no trace_id in context"""
        mock_settings.enable_ssot_telemetry = True
        enforcer = RuntimePolicyEnforcer(settings=mock_settings)
        enforcer._policy_guard = mock_policy_guard
        enforcer._cost_tracker = mock_cost_tracker

        context = {}

        with patch("core.telemetry.from_policy_telemetry_event") as mock_adapter:
            enforcer.check_resource_access("read", "./docs/test.md", context=context)

            mock_adapter.assert_not_called()

    def test_ssot_telemetry_graceful_degradation_on_import_error(self, mock_settings, mock_policy_guard, mock_cost_tracker):
        """SSOT telemetry should gracefully degrade if core.telemetry is unavailable"""
        mock_settings.enable_ssot_telemetry = True
        enforcer = RuntimePolicyEnforcer(settings=mock_settings)
        enforcer._policy_guard = mock_policy_guard
        enforcer._cost_tracker = mock_cost_tracker

        context = {
            "trace_id": "test-trace-123",
            "current_span_id": "parent-span-456",
        }

        with patch.dict("sys.modules", {"core.telemetry": None}):
            with patch("governance.runtime_policy_enforcer.logger"):
                result = enforcer.check_resource_access("read", "./docs/test.md", context=context)

                assert result.allowed

    def test_ssot_telemetry_graceful_degradation_on_emit_error(self, mock_settings, mock_policy_guard, mock_cost_tracker):
        """SSOT telemetry should gracefully degrade if emit fails"""
        mock_settings.enable_ssot_telemetry = True
        enforcer = RuntimePolicyEnforcer(settings=mock_settings)
        enforcer._policy_guard = mock_policy_guard
        enforcer._cost_tracker = mock_cost_tracker

        context = {
            "trace_id": "test-trace-123",
            "current_span_id": "parent-span-456",
        }

        with patch("core.telemetry.from_policy_telemetry_event") as mock_adapter:
            mock_record = MagicMock()
            mock_record.emit.side_effect = Exception("Emit failed")
            mock_adapter.return_value = mock_record

            result = enforcer.check_resource_access("read", "./docs/test.md", context=context)

            assert result.allowed

    def test_current_span_id_takes_precedence_over_parent_span_id(self, mock_settings, mock_policy_guard, mock_cost_tracker):
        """current_span_id should take precedence over parent_span_id in context"""
        mock_settings.enable_ssot_telemetry = False
        enforcer = RuntimePolicyEnforcer(settings=mock_settings)
        enforcer._policy_guard = mock_policy_guard
        enforcer._cost_tracker = mock_cost_tracker

        context = {
            "trace_id": "test-trace-123",
            "current_span_id": "current-span-from-node",
            "parent_span_id": "explicit-parent-span",
        }

        result = enforcer.check_resource_access("read", "./docs/test.md", context=context)

        assert result.telemetry_event.get("parent_span_id") == "current-span-from-node"
