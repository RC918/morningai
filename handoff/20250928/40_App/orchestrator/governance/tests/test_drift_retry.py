"""
Unit tests for Drift-Triggered Retry

EPIC I-2b: Active Recovery (Blueprint 4.3 - Model Governance Framework v2)
"""

from unittest.mock import patch, MagicMock

from governance.drift_retry import (
    DriftRetryPolicy,
    DriftRetryDecision,
    RetryDecision,
    RetryModelTier,
    MODEL_TIER_ESCALATION,
    HIGHEST_TIER_MODELS,
    get_drift_retry_policy,
    get_drift_retry_decision,
    should_retry_on_drift,
    reset_drift_retry,
)


class MockDriftEvent:
    """Mock DriftEvent for testing"""
    def __init__(self, drift_type: str):
        self.drift_type = drift_type


class MockDriftType:
    """Mock DriftType enum for testing"""
    def __init__(self, value: str):
        self.value = value


class TestDriftRetryPolicy:
    """Tests for DriftRetryPolicy dataclass"""

    def test_default_values(self):
        """Test default policy values"""
        policy = DriftRetryPolicy()
        assert policy.enabled is False
        assert policy.max_retries == 1
        assert "json_parse_error" in policy.eligible_drift_types
        assert "schema_violation" in policy.eligible_drift_types
        assert "empty_response" in policy.eligible_drift_types
        assert policy.retry_model_tier == RetryModelTier.HIGHER
        assert policy.cost_cap_multiplier == 2.0
        assert "code_generation" in policy.eligible_task_types
        assert "code_review" in policy.eligible_task_types

    def test_custom_values(self):
        """Test custom policy values"""
        policy = DriftRetryPolicy(
            enabled=True,
            max_retries=2,
            eligible_drift_types={"json_parse_error"},
            retry_model_tier=RetryModelTier.HIGHEST,
            cost_cap_multiplier=3.0,
            eligible_task_types={"code_generation"}
        )
        assert policy.enabled is True
        assert policy.max_retries == 2
        assert policy.eligible_drift_types == {"json_parse_error"}
        assert policy.retry_model_tier == RetryModelTier.HIGHEST
        assert policy.cost_cap_multiplier == 3.0
        assert policy.eligible_task_types == {"code_generation"}

    def test_to_dict(self):
        """Test policy serialization"""
        policy = DriftRetryPolicy(enabled=True)
        result = policy.to_dict()
        assert result["enabled"] is True
        assert result["max_retries"] == 1
        assert result["retry_model_tier"] == "higher"
        assert result["cost_cap_multiplier"] == 2.0


class TestRetryDecision:
    """Tests for RetryDecision dataclass"""

    def test_should_not_retry(self):
        """Test decision to not retry"""
        decision = RetryDecision(
            should_retry=False,
            reason="retry_disabled"
        )
        assert decision.should_retry is False
        assert decision.reason == "retry_disabled"
        assert decision.retry_model is None

    def test_should_retry(self):
        """Test decision to retry"""
        decision = RetryDecision(
            should_retry=True,
            reason="drift_detected_eligible_for_retry",
            retry_model="qwen-max",
            retry_provider="alicloud",
            estimated_cost=0.02
        )
        assert decision.should_retry is True
        assert decision.retry_model == "qwen-max"
        assert decision.retry_provider == "alicloud"
        assert decision.estimated_cost == 0.02

    def test_to_dict(self):
        """Test decision serialization"""
        decision = RetryDecision(
            should_retry=True,
            reason="test",
            metadata={"key": "value"}
        )
        result = decision.to_dict()
        assert result["should_retry"] is True
        assert result["reason"] == "test"
        assert result["metadata"] == {"key": "value"}


class TestDriftRetryDecision:
    """Tests for DriftRetryDecision class"""

    def setup_method(self):
        """Reset global state before each test"""
        reset_drift_retry()

    def test_retry_disabled(self):
        """Test that retry is rejected when disabled"""
        policy = DriftRetryPolicy(enabled=False)
        decision_engine = DriftRetryDecision(policy)

        events = [MockDriftEvent("json_parse_error")]
        result = decision_engine.should_retry(drift_events=events)

        assert result.should_retry is False
        assert result.reason == "retry_disabled"

    def test_max_retries_exceeded(self):
        """Test that retry is rejected when max retries exceeded"""
        policy = DriftRetryPolicy(enabled=True, max_retries=1)
        decision_engine = DriftRetryDecision(policy)

        events = [MockDriftEvent("json_parse_error")]
        result = decision_engine.should_retry(
            drift_events=events,
            attempt_count=1
        )

        assert result.should_retry is False
        assert result.reason == "max_retries_exceeded"

    def test_no_drift_events(self):
        """Test that retry is rejected when no drift events"""
        policy = DriftRetryPolicy(enabled=True)
        decision_engine = DriftRetryDecision(policy)

        result = decision_engine.should_retry(drift_events=[])

        assert result.should_retry is False
        assert result.reason == "no_drift_events"

    def test_drift_type_not_eligible(self):
        """Test that retry is rejected for ineligible drift types"""
        policy = DriftRetryPolicy(
            enabled=True,
            eligible_drift_types={"json_parse_error"}
        )
        decision_engine = DriftRetryDecision(policy)

        events = [MockDriftEvent("unexpected_format")]
        result = decision_engine.should_retry(drift_events=events)

        assert result.should_retry is False
        assert result.reason == "drift_type_not_eligible"

    def test_task_type_not_eligible(self):
        """Test that retry is rejected for ineligible task types"""
        policy = DriftRetryPolicy(
            enabled=True,
            eligible_task_types={"code_generation"}
        )
        decision_engine = DriftRetryDecision(policy)

        events = [MockDriftEvent("json_parse_error")]
        result = decision_engine.should_retry(
            drift_events=events,
            task_type="ux_copy"
        )

        assert result.should_retry is False
        assert result.reason == "task_type_not_eligible"

    def test_cost_cap_exceeded(self):
        """Test that retry is rejected when cost cap exceeded"""
        policy = DriftRetryPolicy(
            enabled=True,
            cost_cap_multiplier=1.0
        )
        decision_engine = DriftRetryDecision(policy)

        events = [MockDriftEvent("json_parse_error")]
        result = decision_engine.should_retry(
            drift_events=events,
            original_cost=0.01,
            current_model="gpt-3.5-turbo"
        )

        assert result.should_retry is False
        assert result.reason == "cost_cap_exceeded"

    def test_retry_approved(self):
        """Test that retry is approved when all conditions met"""
        policy = DriftRetryPolicy(
            enabled=True,
            max_retries=2,
            cost_cap_multiplier=3.0
        )
        decision_engine = DriftRetryDecision(policy)

        events = [MockDriftEvent("json_parse_error")]
        result = decision_engine.should_retry(
            drift_events=events,
            task_type="code_generation",
            attempt_count=0,
            original_cost=0.01,
            current_model="qwen-plus",
            current_provider="alicloud"
        )

        assert result.should_retry is True
        assert result.reason == "drift_detected_eligible_for_retry"
        assert result.retry_model == "qwen-max"
        assert result.retry_provider == "alicloud"

    def test_retry_with_enum_drift_type(self):
        """Test retry with DriftType enum"""
        policy = DriftRetryPolicy(enabled=True)
        decision_engine = DriftRetryDecision(policy)

        mock_event = MagicMock()
        mock_event.drift_type = MockDriftType("json_parse_error")

        result = decision_engine.should_retry(
            drift_events=[mock_event],
            task_type="code_generation"
        )

        assert result.should_retry is True

    def test_model_tier_escalation_same(self):
        """Test model tier escalation with SAME policy"""
        policy = DriftRetryPolicy(
            enabled=True,
            retry_model_tier=RetryModelTier.SAME
        )
        decision_engine = DriftRetryDecision(policy)

        events = [MockDriftEvent("json_parse_error")]
        result = decision_engine.should_retry(
            drift_events=events,
            current_model="qwen-plus",
            current_provider="alicloud"
        )

        assert result.should_retry is True
        assert result.retry_model == "qwen-plus"

    def test_model_tier_escalation_highest(self):
        """Test model tier escalation with HIGHEST policy"""
        policy = DriftRetryPolicy(
            enabled=True,
            retry_model_tier=RetryModelTier.HIGHEST
        )
        decision_engine = DriftRetryDecision(policy)

        events = [MockDriftEvent("json_parse_error")]
        result = decision_engine.should_retry(
            drift_events=events,
            current_model="qwen-plus",
            current_provider="alicloud"
        )

        assert result.should_retry is True
        assert result.retry_model == "qwen-max"


class TestModelTierEscalation:
    """Tests for model tier escalation mappings"""

    def test_tier_3_to_tier_2(self):
        """Test Tier 3 to Tier 2 escalation"""
        assert MODEL_TIER_ESCALATION["qwen-14b"] == "qwen-72b"
        assert MODEL_TIER_ESCALATION["qwen-turbo"] == "qwen-plus"

    def test_tier_2_to_tier_1(self):
        """Test Tier 2 to Tier 1 escalation"""
        assert MODEL_TIER_ESCALATION["qwen-72b"] == "qwen-max"
        assert MODEL_TIER_ESCALATION["qwen-plus"] == "qwen-max"
        assert MODEL_TIER_ESCALATION["gpt-3.5-turbo"] == "gpt-4o"
        assert MODEL_TIER_ESCALATION["gemini-1.5-flash"] == "gemini-1.5-pro"

    def test_highest_tier_models(self):
        """Test highest tier model mappings"""
        assert HIGHEST_TIER_MODELS["alicloud"] == "qwen-max"
        assert HIGHEST_TIER_MODELS["openai"] == "gpt-4o"
        assert HIGHEST_TIER_MODELS["gemini"] == "gemini-3-pro-preview"  # Issue #4112: Updated to Gemini 3


class TestGlobalFunctions:
    """Tests for global singleton functions"""

    def setup_method(self):
        """Reset global state before each test"""
        reset_drift_retry()

    def test_get_drift_retry_policy_from_settings(self):
        """Test policy creation from settings (uses defaults when settings unavailable)"""
        reset_drift_retry()
        policy = get_drift_retry_policy()
        assert policy.enabled is False
        assert policy.max_retries == 1

    def test_should_retry_on_drift_convenience_function(self):
        """Test the convenience function using direct DriftRetryDecision"""
        policy = DriftRetryPolicy(enabled=False)
        decision_engine = DriftRetryDecision(policy)

        events = [MockDriftEvent("json_parse_error")]
        result = decision_engine.should_retry(
            drift_events=events,
            task_type="code_generation"
        )

        assert result.should_retry is False
        assert result.reason == "retry_disabled"

    def test_reset_drift_retry(self):
        """Test reset function clears global state"""
        get_drift_retry_policy()
        get_drift_retry_decision()

        reset_drift_retry()

        from governance.drift_retry import _drift_retry_policy, _drift_retry_decision
        assert _drift_retry_policy is None
        assert _drift_retry_decision is None


class TestEdgeCases:
    """Tests for edge cases and error handling"""

    def setup_method(self):
        """Reset global state before each test"""
        reset_drift_retry()

    def test_none_task_type_allowed(self):
        """Test that None task_type is allowed (skips task type check)"""
        policy = DriftRetryPolicy(enabled=True)
        decision_engine = DriftRetryDecision(policy)

        events = [MockDriftEvent("json_parse_error")]
        result = decision_engine.should_retry(
            drift_events=events,
            task_type=None
        )

        assert result.should_retry is True

    def test_zero_original_cost(self):
        """Test that zero original cost skips cost cap check"""
        policy = DriftRetryPolicy(
            enabled=True,
            cost_cap_multiplier=1.0
        )
        decision_engine = DriftRetryDecision(policy)

        events = [MockDriftEvent("json_parse_error")]
        result = decision_engine.should_retry(
            drift_events=events,
            original_cost=0.0,
            current_model="gpt-4o"
        )

        assert result.should_retry is True

    def test_unknown_model_uses_same(self):
        """Test that unknown model uses same model for retry"""
        policy = DriftRetryPolicy(
            enabled=True,
            retry_model_tier=RetryModelTier.HIGHER
        )
        decision_engine = DriftRetryDecision(policy)

        events = [MockDriftEvent("json_parse_error")]
        result = decision_engine.should_retry(
            drift_events=events,
            current_model="unknown-model",
            current_provider="unknown"
        )

        assert result.should_retry is True
        assert result.retry_model == "unknown-model"

    def test_multiple_drift_events_one_eligible(self):
        """Test that one eligible event is enough for retry"""
        policy = DriftRetryPolicy(
            enabled=True,
            eligible_drift_types={"json_parse_error"}
        )
        decision_engine = DriftRetryDecision(policy)

        events = [
            MockDriftEvent("unexpected_format"),
            MockDriftEvent("json_parse_error"),
            MockDriftEvent("missing_required_field")
        ]
        result = decision_engine.should_retry(drift_events=events)

        assert result.should_retry is True

    def test_all_drift_events_ineligible(self):
        """Test that all ineligible events results in no retry"""
        policy = DriftRetryPolicy(
            enabled=True,
            eligible_drift_types={"json_parse_error"}
        )
        decision_engine = DriftRetryDecision(policy)

        events = [
            MockDriftEvent("unexpected_format"),
            MockDriftEvent("missing_required_field")
        ]
        result = decision_engine.should_retry(drift_events=events)

        assert result.should_retry is False
        assert result.reason == "drift_type_not_eligible"
