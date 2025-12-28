"""
Flow Controller v3 - Unit Tests (C-0 Stage 0)

EPIC C: Flow Controller v3 - LLM-driven Dynamic Routing
Issues #2744-#2747: Schema, RouterNode, Feature Flag, Metrics

This module provides comprehensive unit tests for:
- C-1: Schema definitions (RoutingCandidate, RoutingDecision, RoutingContext)
- C-2: RouterNode interface with decision validation
- C-4: Router metrics and telemetry
"""
import json
from datetime import datetime
from typing import Optional
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from core.flow.schema import (
    InvalidNextNodeError,
    RoutingCandidate,
    RoutingContext,
    RoutingDecision,
    validate_decision,
)
from core.flow.router_node import (
    DeterministicRouter,
    FallbackReason,
    RouterNode,
)
from core.flow.router_metrics import (
    RouterDecisionRecord,
    RouterMetrics,
    get_router_metrics,
)


# =============================================================================
# C-1: Schema Tests
# =============================================================================


class TestRoutingCandidate:
    """Tests for RoutingCandidate schema."""

    def test_valid_candidate(self):
        """Test creating a valid RoutingCandidate."""
        candidate = RoutingCandidate(
            node_name="publisher",
            description="Deploy changes to GitHub"
        )
        assert candidate.node_name == "publisher"
        assert candidate.description == "Deploy changes to GitHub"

    def test_empty_node_name_raises_error(self):
        """Test that empty node_name raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            RoutingCandidate(node_name="", description="Some description")
        assert "node_name cannot be empty" in str(exc_info.value)

    def test_whitespace_node_name_raises_error(self):
        """Test that whitespace-only node_name raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            RoutingCandidate(node_name="   ", description="Some description")
        assert "node_name cannot be empty" in str(exc_info.value)

    def test_empty_description_raises_error(self):
        """Test that empty description raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            RoutingCandidate(node_name="publisher", description="")
        assert "description cannot be empty" in str(exc_info.value)

    def test_node_name_stripped(self):
        """Test that node_name is stripped of whitespace."""
        candidate = RoutingCandidate(
            node_name="  publisher  ",
            description="Deploy changes"
        )
        assert candidate.node_name == "publisher"

    def test_frozen_model(self):
        """Test that RoutingCandidate is immutable."""
        candidate = RoutingCandidate(
            node_name="publisher",
            description="Deploy changes"
        )
        with pytest.raises(ValidationError):
            candidate.node_name = "fixer"


class TestRoutingDecision:
    """Tests for RoutingDecision schema."""

    def test_valid_decision(self):
        """Test creating a valid RoutingDecision."""
        decision = RoutingDecision(
            next_node="fixer",
            reasoning="Code issues need fixing",
            risk_assessment="Low risk - standard fix"
        )
        assert decision.next_node == "fixer"
        assert decision.reasoning == "Code issues need fixing"
        assert decision.risk_assessment == "Low risk - standard fix"
        assert decision.confidence is None

    def test_decision_with_confidence(self):
        """Test creating a RoutingDecision with confidence score."""
        decision = RoutingDecision(
            next_node="fixer",
            reasoning="Code issues need fixing",
            risk_assessment="Low risk",
            confidence=0.95
        )
        assert decision.confidence == 0.95

    def test_confidence_out_of_range(self):
        """Test that confidence outside 0-1 raises ValidationError."""
        with pytest.raises(ValidationError):
            RoutingDecision(
                next_node="fixer",
                reasoning="Reason",
                risk_assessment="Risk",
                confidence=1.5
            )

    def test_empty_next_node_raises_error(self):
        """Test that empty next_node raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            RoutingDecision(
                next_node="",
                reasoning="Reason",
                risk_assessment="Risk"
            )
        assert "next_node cannot be empty" in str(exc_info.value)

    def test_empty_reasoning_raises_error(self):
        """Test that empty reasoning raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            RoutingDecision(
                next_node="fixer",
                reasoning="",
                risk_assessment="Risk"
            )
        assert "reasoning cannot be empty" in str(exc_info.value)

    def test_empty_risk_assessment_raises_error(self):
        """Test that empty risk_assessment raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            RoutingDecision(
                next_node="fixer",
                reasoning="Reason",
                risk_assessment=""
            )
        assert "risk_assessment cannot be empty" in str(exc_info.value)


class TestRoutingContext:
    """Tests for RoutingContext schema."""

    def test_valid_context(self):
        """Test creating a valid RoutingContext."""
        candidates = [
            RoutingCandidate(node_name="publisher", description="Deploy"),
            RoutingCandidate(node_name="fixer", description="Fix code"),
        ]
        context = RoutingContext(
            task_type="code_review",
            current_stage="review",
            candidates=candidates
        )
        assert context.task_type == "code_review"
        assert context.current_stage == "review"
        assert len(context.candidates) == 2
        assert context.step_history == []
        assert context.last_agent_feedback == ""

    def test_context_with_all_fields(self):
        """Test creating a RoutingContext with all optional fields."""
        candidates = [
            RoutingCandidate(node_name="publisher", description="Deploy"),
        ]
        context = RoutingContext(
            task_type="code_review",
            current_stage="review",
            step_history=["planner", "coder", "reviewer"],
            last_agent_feedback="Variable naming issues found",
            candidates=candidates,
            review_verdict="request_changes",
            review_severity="medium",
            blocker_count=2
        )
        assert context.step_history == ["planner", "coder", "reviewer"]
        assert context.last_agent_feedback == "Variable naming issues found"
        assert context.review_verdict == "request_changes"
        assert context.review_severity == "medium"
        assert context.blocker_count == 2

    def test_empty_candidates_raises_error(self):
        """Test that empty candidates list raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            RoutingContext(
                task_type="code_review",
                current_stage="review",
                candidates=[]
            )
        assert "candidates list cannot be empty" in str(exc_info.value)

    def test_empty_task_type_raises_error(self):
        """Test that empty task_type raises ValidationError."""
        candidates = [
            RoutingCandidate(node_name="publisher", description="Deploy"),
        ]
        with pytest.raises(ValidationError) as exc_info:
            RoutingContext(
                task_type="",
                current_stage="review",
                candidates=candidates
            )
        assert "task_type cannot be empty" in str(exc_info.value)

    def test_get_candidate_names(self):
        """Test get_candidate_names method."""
        candidates = [
            RoutingCandidate(node_name="publisher", description="Deploy"),
            RoutingCandidate(node_name="fixer", description="Fix code"),
            RoutingCandidate(node_name="finalizer", description="Finalize"),
        ]
        context = RoutingContext(
            task_type="code_review",
            current_stage="review",
            candidates=candidates
        )
        assert context.get_candidate_names() == ["publisher", "fixer", "finalizer"]

    def test_is_valid_next_node(self):
        """Test is_valid_next_node method."""
        candidates = [
            RoutingCandidate(node_name="publisher", description="Deploy"),
            RoutingCandidate(node_name="fixer", description="Fix code"),
        ]
        context = RoutingContext(
            task_type="code_review",
            current_stage="review",
            candidates=candidates
        )
        assert context.is_valid_next_node("publisher") is True
        assert context.is_valid_next_node("fixer") is True
        assert context.is_valid_next_node("invalid") is False


class TestValidateDecision:
    """Tests for validate_decision function."""

    def test_valid_decision_passes(self):
        """Test that valid decision passes validation."""
        candidates = [
            RoutingCandidate(node_name="publisher", description="Deploy"),
            RoutingCandidate(node_name="fixer", description="Fix code"),
        ]
        context = RoutingContext(
            task_type="code_review",
            current_stage="review",
            candidates=candidates
        )
        decision = RoutingDecision(
            next_node="fixer",
            reasoning="Code issues need fixing",
            risk_assessment="Low risk"
        )
        validate_decision(decision, context)

    def test_invalid_next_node_raises_error(self):
        """Test that invalid next_node raises InvalidNextNodeError."""
        candidates = [
            RoutingCandidate(node_name="publisher", description="Deploy"),
            RoutingCandidate(node_name="fixer", description="Fix code"),
        ]
        context = RoutingContext(
            task_type="code_review",
            current_stage="review",
            candidates=candidates
        )
        decision = RoutingDecision(
            next_node="invalid_node",
            reasoning="Reason",
            risk_assessment="Risk"
        )
        with pytest.raises(InvalidNextNodeError) as exc_info:
            validate_decision(decision, context)
        assert exc_info.value.next_node == "invalid_node"
        assert exc_info.value.valid_nodes == ["publisher", "fixer"]


# =============================================================================
# C-2: RouterNode Tests
# =============================================================================


class MockLLMClient:
    """Mock LLM client for testing."""

    def __init__(
        self,
        response: Optional[str] = None,
        raise_timeout: bool = False,
        raise_error: bool = False
    ):
        self.response = response
        self.raise_timeout = raise_timeout
        self.raise_error = raise_error
        self.call_count = 0

    def generate(
        self,
        prompt: str,
        timeout_seconds: Optional[float] = None
    ) -> str:
        self.call_count += 1
        if self.raise_timeout:
            raise TimeoutError("LLM call timed out")
        if self.raise_error:
            raise RuntimeError("LLM error")
        return self.response or ""


class TestRouterNode:
    """Tests for RouterNode class."""

    def _create_context(self):
        """Create a test RoutingContext."""
        candidates = [
            RoutingCandidate(node_name="publisher", description="Deploy"),
            RoutingCandidate(node_name="fixer", description="Fix code"),
            RoutingCandidate(node_name="finalizer", description="Finalize"),
        ]
        return RoutingContext(
            task_type="code_review",
            current_stage="review",
            step_history=["planner", "coder"],
            last_agent_feedback="Code looks good",
            candidates=candidates
        )

    def _create_fallback_fn(self):
        """Create a test fallback function."""
        def fallback_fn(context: RoutingContext) -> RoutingDecision:
            return RoutingDecision(
                next_node="finalizer",
                reasoning="Fallback: default to finalizer",
                risk_assessment="Low - deterministic fallback"
            )
        return fallback_fn

    def test_successful_routing(self):
        """Test successful LLM routing."""
        response = json.dumps({
            "next_node": "fixer",
            "reasoning": "Code issues need fixing",
            "risk_assessment": "Low risk"
        })
        llm_client = MockLLMClient(response=response)
        router = RouterNode(
            llm_client=llm_client,
            fallback_fn=self._create_fallback_fn()
        )
        context = self._create_context()
        decision = router.route(context)

        assert decision.next_node == "fixer"
        assert decision.reasoning == "Code issues need fixing"
        assert llm_client.call_count == 1

    def test_timeout_triggers_fallback(self):
        """Test that timeout triggers fallback."""
        llm_client = MockLLMClient(raise_timeout=True)
        router = RouterNode(
            llm_client=llm_client,
            fallback_fn=self._create_fallback_fn()
        )
        context = self._create_context()
        decision = router.route(context)

        assert decision.next_node == "finalizer"
        assert "Fallback" in decision.reasoning

    def test_json_error_triggers_fallback(self):
        """Test that JSON parse error triggers fallback."""
        llm_client = MockLLMClient(response="not valid json")
        router = RouterNode(
            llm_client=llm_client,
            fallback_fn=self._create_fallback_fn()
        )
        context = self._create_context()
        decision = router.route(context)

        assert decision.next_node == "finalizer"

    def test_invalid_next_node_triggers_fallback(self):
        """Test that invalid next_node triggers fallback."""
        response = json.dumps({
            "next_node": "invalid_node",
            "reasoning": "Reason",
            "risk_assessment": "Risk"
        })
        llm_client = MockLLMClient(response=response)
        router = RouterNode(
            llm_client=llm_client,
            fallback_fn=self._create_fallback_fn()
        )
        context = self._create_context()
        decision = router.route(context)

        assert decision.next_node == "finalizer"

    def test_empty_response_triggers_fallback(self):
        """Test that empty LLM response triggers fallback."""
        llm_client = MockLLMClient(response="")
        router = RouterNode(
            llm_client=llm_client,
            fallback_fn=self._create_fallback_fn()
        )
        context = self._create_context()
        decision = router.route(context)

        assert decision.next_node == "finalizer"

    def test_llm_error_triggers_fallback(self):
        """Test that LLM error triggers fallback."""
        llm_client = MockLLMClient(raise_error=True)
        router = RouterNode(
            llm_client=llm_client,
            fallback_fn=self._create_fallback_fn()
        )
        context = self._create_context()
        decision = router.route(context)

        assert decision.next_node == "finalizer"

    def test_retry_on_failure(self):
        """Test that router retries on failure."""
        call_count = [0]
        responses = ["invalid", "invalid", json.dumps({
            "next_node": "fixer",
            "reasoning": "Reason",
            "risk_assessment": "Risk"
        })]

        class RetryLLMClient:
            def generate(self, prompt, timeout_seconds=None):
                idx = min(call_count[0], len(responses) - 1)
                call_count[0] += 1
                return responses[idx]

        router = RouterNode(
            llm_client=RetryLLMClient(),
            fallback_fn=self._create_fallback_fn(),
            max_retries=2
        )
        context = self._create_context()
        router.route(context)

        assert call_count[0] == 3

    def test_metrics_callback(self):
        """Test that metrics callback is called."""
        response = json.dumps({
            "next_node": "fixer",
            "reasoning": "Reason",
            "risk_assessment": "Risk"
        })
        llm_client = MockLLMClient(response=response)
        router = RouterNode(
            llm_client=llm_client,
            fallback_fn=self._create_fallback_fn()
        )
        context = self._create_context()

        metrics_data = {}

        def metrics_callback(data):
            metrics_data.update(data)

        router.route(context, metrics_callback=metrics_callback)

        assert "latency_ms" in metrics_data
        assert metrics_data["success"] is True
        assert metrics_data["fallback_reason"] is None

    def test_fallback_function_failure_uses_first_candidate(self):
        """Test that fallback function failure uses first candidate."""
        llm_client = MockLLMClient(raise_error=True)

        def failing_fallback(context):
            raise RuntimeError("Fallback failed")

        router = RouterNode(
            llm_client=llm_client,
            fallback_fn=failing_fallback
        )
        context = self._create_context()
        decision = router.route(context)

        assert decision.next_node == "publisher"
        assert "Last resort fallback" in decision.reasoning


class TestDeterministicRouter:
    """Tests for DeterministicRouter class."""

    def _create_context(self):
        """Create a test RoutingContext."""
        candidates = [
            RoutingCandidate(node_name="publisher", description="Deploy"),
            RoutingCandidate(node_name="fixer", description="Fix code"),
        ]
        return RoutingContext(
            task_type="code_review",
            current_stage="review",
            candidates=candidates
        )

    def test_rule_based_routing(self):
        """Test rule-based routing."""
        rules = {
            ("code_review", "review"): "fixer",
            ("bug_fix", "coding"): "publisher",
        }
        router = DeterministicRouter(rules=rules)
        context = self._create_context()
        decision = router.route(context)

        assert decision.next_node == "fixer"
        assert "Deterministic rule" in decision.reasoning

    def test_no_matching_rule_uses_first_candidate(self):
        """Test that no matching rule uses first candidate."""
        rules = {
            ("bug_fix", "coding"): "publisher",
        }
        router = DeterministicRouter(rules=rules)
        context = self._create_context()
        decision = router.route(context)

        assert decision.next_node == "publisher"
        assert "first candidate" in decision.reasoning

    def test_empty_rules_uses_first_candidate(self):
        """Test that empty rules uses first candidate."""
        router = DeterministicRouter()
        context = self._create_context()
        decision = router.route(context)

        assert decision.next_node == "publisher"


# =============================================================================
# C-4: Router Metrics Tests
# =============================================================================


class TestRouterMetrics:
    """Tests for RouterMetrics class."""

    def test_record_decision(self):
        """Test recording a decision."""
        metrics = RouterMetrics()
        metrics.record_decision(
            trace_id="test-123",
            latency_ms=150.5,
            success=True,
            chosen_node="fixer"
        )

        summary = metrics.get_all_time_summary()
        assert summary["total_decisions"] == 1
        assert summary["total_successes"] == 1
        assert summary["total_fallbacks"] == 0
        assert summary["chosen_nodes"]["fixer"] == 1

    def test_record_fallback(self):
        """Test recording a fallback decision."""
        metrics = RouterMetrics()
        metrics.record_decision(
            trace_id="test-123",
            latency_ms=100.0,
            success=False,
            chosen_node="finalizer",
            fallback_reason=FallbackReason.TIMEOUT
        )

        summary = metrics.get_all_time_summary()
        assert summary["total_decisions"] == 1
        assert summary["total_successes"] == 0
        assert summary["total_fallbacks"] == 1
        assert summary["fallback_reasons"][FallbackReason.TIMEOUT] == 1

    def test_get_fallback_rate(self):
        """Test getting fallback rate."""
        metrics = RouterMetrics()
        for i in range(10):
            metrics.record_decision(
                trace_id=f"test-{i}",
                latency_ms=100.0,
                success=(i < 7),
                chosen_node="fixer"
            )

        rate = metrics.get_fallback_rate(window_minutes=60)
        assert rate == 0.3

    def test_get_success_rate(self):
        """Test getting success rate."""
        metrics = RouterMetrics()
        for i in range(10):
            metrics.record_decision(
                trace_id=f"test-{i}",
                latency_ms=100.0,
                success=(i < 7),
                chosen_node="fixer"
            )

        rate = metrics.get_success_rate(window_minutes=60)
        assert rate == 0.7

    def test_get_average_latency(self):
        """Test getting average latency."""
        metrics = RouterMetrics()
        latencies = [100.0, 150.0, 200.0, 250.0]
        for i, latency in enumerate(latencies):
            metrics.record_decision(
                trace_id=f"test-{i}",
                latency_ms=latency,
                success=True,
                chosen_node="fixer"
            )

        avg = metrics.get_average_latency(window_minutes=60)
        assert avg == 175.0

    def test_get_fallback_distribution(self):
        """Test getting fallback distribution."""
        metrics = RouterMetrics()
        metrics.record_decision(
            trace_id="test-1",
            latency_ms=100.0,
            success=False,
            chosen_node="finalizer",
            fallback_reason=FallbackReason.TIMEOUT
        )
        metrics.record_decision(
            trace_id="test-2",
            latency_ms=100.0,
            success=False,
            chosen_node="finalizer",
            fallback_reason=FallbackReason.TIMEOUT
        )
        metrics.record_decision(
            trace_id="test-3",
            latency_ms=100.0,
            success=False,
            chosen_node="finalizer",
            fallback_reason=FallbackReason.JSON_PARSE_ERROR
        )

        dist = metrics.get_fallback_distribution(window_minutes=60)
        assert dist[FallbackReason.TIMEOUT] == 2
        assert dist[FallbackReason.JSON_PARSE_ERROR] == 1

    def test_get_node_distribution(self):
        """Test getting node distribution."""
        metrics = RouterMetrics()
        metrics.record_decision(
            trace_id="test-1",
            latency_ms=100.0,
            success=True,
            chosen_node="fixer"
        )
        metrics.record_decision(
            trace_id="test-2",
            latency_ms=100.0,
            success=True,
            chosen_node="fixer"
        )
        metrics.record_decision(
            trace_id="test-3",
            latency_ms=100.0,
            success=True,
            chosen_node="publisher"
        )

        dist = metrics.get_node_distribution(window_minutes=60)
        assert dist["fixer"] == 2
        assert dist["publisher"] == 1

    def test_get_summary(self):
        """Test getting summary."""
        metrics = RouterMetrics()
        metrics.record_decision(
            trace_id="test-1",
            latency_ms=100.0,
            success=True,
            chosen_node="fixer",
            token_usage=250,
            cost_estimate=0.001
        )

        summary = metrics.get_summary(window_minutes=60)
        assert summary["total_decisions"] == 1
        assert summary["successes"] == 1
        assert summary["fallbacks"] == 0
        assert summary["success_rate"] == 1.0
        assert summary["average_latency_ms"] == 100.0
        assert summary["total_tokens"] == 250
        assert summary["total_cost_usd"] == 0.001

    def test_reset(self):
        """Test resetting metrics."""
        metrics = RouterMetrics()
        metrics.record_decision(
            trace_id="test-1",
            latency_ms=100.0,
            success=True,
            chosen_node="fixer"
        )
        metrics.reset()

        summary = metrics.get_all_time_summary()
        assert summary["total_decisions"] == 0

    def test_max_records_limit(self):
        """Test that max_records limit is enforced."""
        metrics = RouterMetrics(max_records=5)
        for i in range(10):
            metrics.record_decision(
                trace_id=f"test-{i}",
                latency_ms=100.0,
                success=True,
                chosen_node="fixer"
            )

        assert len(metrics._records) == 5
        assert metrics._records[0].trace_id == "test-5"

    def test_get_router_metrics_singleton(self):
        """Test that get_router_metrics returns singleton."""
        metrics1 = get_router_metrics()
        metrics2 = get_router_metrics()
        assert metrics1 is metrics2


class TestRouterDecisionRecord:
    """Tests for RouterDecisionRecord dataclass."""

    def test_create_record(self):
        """Test creating a RouterDecisionRecord."""
        record = RouterDecisionRecord(
            trace_id="test-123",
            timestamp=datetime.utcnow(),
            latency_ms=150.5,
            success=True,
            chosen_node="fixer"
        )
        assert record.trace_id == "test-123"
        assert record.latency_ms == 150.5
        assert record.success is True
        assert record.chosen_node == "fixer"
        assert record.fallback_reason is None

    def test_create_record_with_fallback(self):
        """Test creating a RouterDecisionRecord with fallback."""
        record = RouterDecisionRecord(
            trace_id="test-123",
            timestamp=datetime.utcnow(),
            latency_ms=100.0,
            success=False,
            chosen_node="finalizer",
            fallback_reason=FallbackReason.TIMEOUT
        )
        assert record.success is False
        assert record.fallback_reason == FallbackReason.TIMEOUT


# =============================================================================
# Feature Flag Integration Tests
# =============================================================================


class TestFeatureFlagIntegration:
    """Tests for Feature Flag integration with settings."""

    def test_default_dynamic_routing_disabled(self):
        """Test that dynamic routing is disabled by default."""
        with patch.dict("os.environ", {}, clear=True):
            from common.config.settings import Settings
            settings = Settings()
            assert settings.enable_dynamic_routing is False

    def test_enable_dynamic_routing(self):
        """Test enabling dynamic routing via environment variable."""
        with patch.dict("os.environ", {"ENABLE_DYNAMIC_ROUTING": "true"}):
            from common.config.settings import Settings
            settings = Settings()
            assert settings.enable_dynamic_routing is True

    def test_router_timeout_default(self):
        """Test default router timeout."""
        with patch.dict("os.environ", {}, clear=True):
            from common.config.settings import Settings
            settings = Settings()
            assert settings.router_timeout_seconds == 10

    def test_router_max_retries_default(self):
        """Test default router max retries."""
        with patch.dict("os.environ", {}, clear=True):
            from common.config.settings import Settings
            settings = Settings()
            assert settings.router_max_retries == 2

    def test_router_model_tier_default(self):
        """Test default router model tier."""
        with patch.dict("os.environ", {}, clear=True):
            from common.config.settings import Settings
            settings = Settings()
            assert settings.router_model_tier == "tier1"


# =============================================================================
# FallbackReason Constants Tests
# =============================================================================


class TestFallbackReason:
    """Tests for FallbackReason constants."""

    def test_fallback_reason_values(self):
        """Test FallbackReason constant values."""
        assert FallbackReason.TIMEOUT == "timeout"
        assert FallbackReason.JSON_PARSE_ERROR == "json_parse_error"
        assert FallbackReason.VALIDATION_ERROR == "validation_error"
        assert FallbackReason.INVALID_NEXT_NODE == "invalid_next_node"
        assert FallbackReason.EMPTY_OUTPUT == "empty_output"
        assert FallbackReason.LLM_ERROR == "llm_error"
        assert FallbackReason.UNKNOWN == "unknown"

    def test_json_safety_error_fallback_reason(self):
        """Test JSON_SAFETY_ERROR fallback reason exists."""
        assert FallbackReason.JSON_SAFETY_ERROR == "json_safety_error"


# =============================================================================
# JSON Safety Tests
# =============================================================================


class TestJSONSafety:
    """Tests for JSON safety checks in RouterNode."""

    def _create_context(self):
        """Create a test RoutingContext."""
        candidates = [
            RoutingCandidate(node_name="publisher", description="Deploy"),
            RoutingCandidate(node_name="fixer", description="Fix code"),
        ]
        return RoutingContext(
            task_type="code_review",
            current_stage="review",
            candidates=candidates
        )

    def _create_fallback_fn(self):
        """Create a test fallback function."""
        def fallback_fn(context: RoutingContext) -> RoutingDecision:
            return RoutingDecision(
                next_node="fixer",
                reasoning="Fallback: default to fixer",
                risk_assessment="Low - deterministic fallback"
            )
        return fallback_fn

    def test_oversized_response_triggers_fallback(self):
        """Test that oversized LLM response triggers fallback."""
        from core.flow.llm_safety import MAX_RESPONSE_SIZE

        # Create a response larger than MAX_RESPONSE_SIZE
        oversized_response = '{"next_node": "fixer", "reasoning": "' + 'x' * (MAX_RESPONSE_SIZE + 100) + '", "risk_assessment": "Low"}'

        llm_client = MockLLMClient(response=oversized_response)
        router = RouterNode(
            llm_client=llm_client,
            fallback_fn=self._create_fallback_fn()
        )
        context = self._create_context()
        decision = router.route(context)

        # Should fall back due to size limit
        assert decision.next_node == "fixer"
        assert "Fallback" in decision.reasoning

    def test_deeply_nested_json_triggers_fallback(self):
        """Test that deeply nested JSON triggers fallback."""
        from core.flow.llm_safety import MAX_NESTING_DEPTH

        # Create deeply nested JSON (exceeds MAX_NESTING_DEPTH)
        nested = '{"a": ' * (MAX_NESTING_DEPTH + 5) + '"value"' + '}' * (MAX_NESTING_DEPTH + 5)

        llm_client = MockLLMClient(response=nested)
        router = RouterNode(
            llm_client=llm_client,
            fallback_fn=self._create_fallback_fn()
        )
        context = self._create_context()
        decision = router.route(context)

        # Should fall back due to nesting depth
        assert decision.next_node == "fixer"

    def test_valid_json_passes_safety_check(self):
        """Test that valid JSON passes safety check."""
        valid_response = json.dumps({
            "next_node": "publisher",
            "reasoning": "Code looks good",
            "risk_assessment": "Low risk"
        })

        llm_client = MockLLMClient(response=valid_response)
        router = RouterNode(
            llm_client=llm_client,
            fallback_fn=self._create_fallback_fn()
        )
        context = self._create_context()
        decision = router.route(context)

        # Should succeed
        assert decision.next_node == "publisher"
        assert decision.reasoning == "Code looks good"


# =============================================================================
# Metrics Version Tests
# =============================================================================


class TestMetricsVersion:
    """Tests for metrics versioning."""

    def test_summary_includes_metrics_version(self):
        """Test that get_summary includes metrics_version."""
        from core.flow.router_metrics import METRICS_VERSION

        metrics = RouterMetrics()
        metrics.record_decision(
            trace_id="test-1",
            latency_ms=100.0,
            success=True,
            chosen_node="fixer"
        )

        summary = metrics.get_summary(window_minutes=60)
        assert "metrics_version" in summary
        assert summary["metrics_version"] == METRICS_VERSION

    def test_all_time_summary_includes_metrics_version(self):
        """Test that get_all_time_summary includes metrics_version."""
        from core.flow.router_metrics import METRICS_VERSION

        metrics = RouterMetrics()
        metrics.record_decision(
            trace_id="test-1",
            latency_ms=100.0,
            success=True,
            chosen_node="fixer"
        )

        summary = metrics.get_all_time_summary()
        assert "metrics_version" in summary
        assert summary["metrics_version"] == METRICS_VERSION

    def test_metrics_version_is_v1(self):
        """Test that current metrics version is v1."""
        from core.flow.router_metrics import METRICS_VERSION
        assert METRICS_VERSION == "v1"


# =============================================================================
# Deque Optimization Tests
# =============================================================================


class TestDequeOptimization:
    """Tests for deque-based record storage optimization."""

    def test_records_use_deque(self):
        """Test that _records is a deque."""
        from collections import deque
        metrics = RouterMetrics(max_records=10)
        assert isinstance(metrics._records, deque)

    def test_deque_maxlen_enforced(self):
        """Test that deque maxlen is enforced."""
        metrics = RouterMetrics(max_records=5)
        for i in range(10):
            metrics.record_decision(
                trace_id=f"test-{i}",
                latency_ms=100.0,
                success=True,
                chosen_node="fixer"
            )

        # Should only have 5 records (FIFO eviction)
        assert len(metrics._records) == 5
        # First record should be test-5 (oldest 5 were evicted)
        assert metrics._records[0].trace_id == "test-5"

    def test_deque_fifo_order(self):
        """Test that deque maintains FIFO order."""
        metrics = RouterMetrics(max_records=3)
        for i in range(5):
            metrics.record_decision(
                trace_id=f"test-{i}",
                latency_ms=float(i * 10),
                success=True,
                chosen_node="fixer"
            )

        # Should have test-2, test-3, test-4
        trace_ids = [r.trace_id for r in metrics._records]
        assert trace_ids == ["test-2", "test-3", "test-4"]


# =============================================================================
# Thread-Safe Singleton Tests
# =============================================================================


class TestThreadSafeSingleton:
    """Tests for thread-safe singleton pattern in get_router_metrics."""

    def test_singleton_uses_lock(self):
        """Test that get_router_metrics uses a module-level lock."""
        from core.flow import router_metrics
        assert hasattr(router_metrics, '_global_metrics_lock')
        from threading import Lock
        assert isinstance(router_metrics._global_metrics_lock, type(Lock()))

    def test_concurrent_access_returns_same_instance(self):
        """Test that concurrent calls return the same instance."""
        import threading
        from core.flow import router_metrics

        # Reset global metrics for test
        router_metrics._global_metrics = None

        results = []
        errors = []

        def get_metrics():
            try:
                m = router_metrics.get_router_metrics()
                results.append(id(m))
            except Exception as e:
                errors.append(e)

        # Create multiple threads to call get_router_metrics concurrently
        threads = [threading.Thread(target=get_metrics) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All threads should get the same instance
        assert len(errors) == 0
        assert len(set(results)) == 1  # All IDs should be the same


# =============================================================================
# Literal Type Validation Tests
# =============================================================================


class TestLiteralTypeValidation:
    """Tests for Literal type validation in settings."""

    def test_router_model_tier_valid_values(self):
        """Test that router_model_tier accepts valid values."""
        with patch.dict("os.environ", {"ROUTER_MODEL_TIER": "tier1"}):
            from common.config.settings import Settings
            settings = Settings()
            assert settings.router_model_tier == "tier1"

        with patch.dict("os.environ", {"ROUTER_MODEL_TIER": "tier2"}):
            from common.config.settings import Settings
            settings = Settings()
            assert settings.router_model_tier == "tier2"

    def test_router_model_tier_invalid_value_raises_error(self):
        """Test that invalid router_model_tier raises ValidationError."""
        with patch.dict("os.environ", {"ROUTER_MODEL_TIER": "tier3"}):
            from common.config.settings import Settings
            with pytest.raises(ValidationError):
                Settings()


# =============================================================================
# C-2: Hybrid Router Tests (Stage 1)
# =============================================================================


class TestNodeNameMapping:
    """Tests for node name canonicalization and mapping."""

    def test_canonicalize_alias_publisher_node(self):
        """Test that publisher_node maps to publisher."""
        from core.flow.hybrid_router import canonicalize_node_name
        assert canonicalize_node_name("publisher_node") == "publisher"

    def test_canonicalize_alias_fixer_node(self):
        """Test that fixer_node maps to fixer."""
        from core.flow.hybrid_router import canonicalize_node_name
        assert canonicalize_node_name("fixer_node") == "fixer"

    def test_canonicalize_alias_coder_node(self):
        """Test that coder_node maps to executor."""
        from core.flow.hybrid_router import canonicalize_node_name
        assert canonicalize_node_name("coder_node") == "executor"

    def test_canonicalize_alias_human_fallback(self):
        """Test that human_fallback maps to decision."""
        from core.flow.hybrid_router import canonicalize_node_name
        assert canonicalize_node_name("human_fallback") == "decision"

    def test_canonicalize_canonical_node(self):
        """Test that canonical node names pass through."""
        from core.flow.hybrid_router import canonicalize_node_name
        assert canonicalize_node_name("publisher") == "publisher"
        assert canonicalize_node_name("fixer") == "fixer"
        assert canonicalize_node_name("executor") == "executor"
        assert canonicalize_node_name("decision") == "decision"

    def test_canonicalize_case_insensitive(self):
        """Test that canonicalization is case-insensitive."""
        from core.flow.hybrid_router import canonicalize_node_name
        assert canonicalize_node_name("PUBLISHER_NODE") == "publisher"
        assert canonicalize_node_name("Fixer_Node") == "fixer"

    def test_canonicalize_strips_whitespace(self):
        """Test that canonicalization strips whitespace."""
        from core.flow.hybrid_router import canonicalize_node_name
        assert canonicalize_node_name("  publisher  ") == "publisher"

    def test_canonicalize_unknown_raises_error(self):
        """Test that unknown node names raise ValueError."""
        from core.flow.hybrid_router import canonicalize_node_name
        with pytest.raises(ValueError) as exc_info:
            canonicalize_node_name("unknown_node")
        assert "Unknown node name" in str(exc_info.value)


class TestSeverityComparison:
    """Tests for severity comparison logic."""

    def test_severity_gte_low_vs_low(self):
        """Test low >= low is True."""
        from core.flow.hybrid_router import severity_gte
        assert severity_gte("low", "low") is True

    def test_severity_gte_medium_vs_low(self):
        """Test medium >= low is True."""
        from core.flow.hybrid_router import severity_gte
        assert severity_gte("medium", "low") is True

    def test_severity_gte_low_vs_medium(self):
        """Test low >= medium is False."""
        from core.flow.hybrid_router import severity_gte
        assert severity_gte("low", "medium") is False

    def test_severity_gte_high_vs_medium(self):
        """Test high >= medium is True."""
        from core.flow.hybrid_router import severity_gte
        assert severity_gte("high", "medium") is True

    def test_severity_gte_critical_vs_high(self):
        """Test critical >= high is True."""
        from core.flow.hybrid_router import severity_gte
        assert severity_gte("critical", "high") is True

    def test_severity_gte_case_insensitive(self):
        """Test severity comparison is case-insensitive."""
        from core.flow.hybrid_router import severity_gte
        assert severity_gte("MEDIUM", "low") is True
        assert severity_gte("Low", "MEDIUM") is False


class TestHybridRoutingPolicyFastPath:
    """Tests for HybridRoutingPolicy fast path (deterministic) routing."""

    def test_fast_path_approve_routes_to_publisher(self):
        """Test that approve verdict routes to publisher."""
        from core.flow.hybrid_router import HybridRoutingPolicy
        policy = HybridRoutingPolicy(llm_generate_fn=None)
        decision = policy.route(
            verdict="approve",
            severity="low",
            summary="All good",
            blocker_count=0
        )
        assert decision.next_node == "publisher"
        assert decision.requires_hitl_approval is False

    def test_fast_path_blocked_routes_to_decision_with_hitl(self):
        """Test that blocked verdict routes to decision with HITL."""
        from core.flow.hybrid_router import HybridRoutingPolicy
        policy = HybridRoutingPolicy(llm_generate_fn=None)
        decision = policy.route(
            verdict="blocked",
            severity="critical",
            summary="Blocked",
            blocker_count=5
        )
        assert decision.next_node == "decision"
        assert decision.requires_hitl_approval is True

    def test_fast_path_unknown_routes_to_decision_with_hitl(self):
        """Test that unknown verdict routes to decision with HITL."""
        from core.flow.hybrid_router import HybridRoutingPolicy
        policy = HybridRoutingPolicy(llm_generate_fn=None)
        decision = policy.route(
            verdict="unknown",
            severity="low",
            summary="Unknown",
            blocker_count=0
        )
        assert decision.next_node == "decision"
        assert decision.requires_hitl_approval is True

    def test_fast_path_request_changes_low_severity_routes_to_fixer(self):
        """Test that request_changes with low severity routes to fixer."""
        from core.flow.hybrid_router import HybridRoutingPolicy
        policy = HybridRoutingPolicy(llm_generate_fn=None)
        decision = policy.route(
            verdict="request_changes",
            severity="low",
            summary="Minor issues",
            blocker_count=0
        )
        assert decision.next_node == "fixer"
        assert decision.requires_hitl_approval is False

    def test_fast_path_comment_routes_to_fixer(self):
        """Test that comment verdict routes to fixer."""
        from core.flow.hybrid_router import HybridRoutingPolicy
        policy = HybridRoutingPolicy(llm_generate_fn=None)
        decision = policy.route(
            verdict="comment",
            severity="low",
            summary="Suggestions",
            blocker_count=0
        )
        assert decision.next_node == "fixer"
        assert decision.requires_hitl_approval is False


class TestHybridRoutingPolicySlowPath:
    """Tests for HybridRoutingPolicy slow path (LLM) routing."""

    def test_slow_path_request_changes_medium_calls_llm(self):
        """Test that request_changes with medium severity calls LLM."""
        from core.flow.hybrid_router import HybridRoutingPolicy

        llm_called = [False]

        def mock_llm(prompt: str) -> str:
            llm_called[0] = True
            return '{"next_node": "fixer", "reasoning": "Can be auto-fixed"}'

        policy = HybridRoutingPolicy(llm_generate_fn=mock_llm)
        decision = policy.route(
            verdict="request_changes",
            severity="medium",
            summary="Medium issues",
            blocker_count=0
        )
        assert llm_called[0] is True
        assert decision.next_node == "fixer"

    def test_slow_path_llm_returns_executor(self):
        """Test that LLM can return executor for major issues."""
        from core.flow.hybrid_router import HybridRoutingPolicy

        def mock_llm(prompt: str) -> str:
            return '{"next_node": "executor", "reasoning": "Needs re-generation"}'

        policy = HybridRoutingPolicy(llm_generate_fn=mock_llm)
        decision = policy.route(
            verdict="request_changes",
            severity="high",
            summary="Major issues",
            blocker_count=3
        )
        assert decision.next_node == "executor"

    def test_slow_path_llm_alias_canonicalized(self):
        """Test that LLM returning alias is canonicalized."""
        from core.flow.hybrid_router import HybridRoutingPolicy

        def mock_llm(prompt: str) -> str:
            return '{"next_node": "coder_node", "reasoning": "Needs re-generation"}'

        policy = HybridRoutingPolicy(llm_generate_fn=mock_llm)
        decision = policy.route(
            verdict="request_changes",
            severity="high",
            summary="Major issues",
            blocker_count=3
        )
        assert decision.next_node == "executor"

    def test_slow_path_llm_failure_uses_fallback(self):
        """Test that LLM failure uses deterministic fallback."""
        from core.flow.hybrid_router import HybridRoutingPolicy

        def mock_llm(prompt: str) -> str:
            raise RuntimeError("LLM error")

        policy = HybridRoutingPolicy(llm_generate_fn=mock_llm)
        decision = policy.route(
            verdict="request_changes",
            severity="medium",
            summary="Issues",
            blocker_count=0
        )
        assert decision.next_node == "fixer"

    def test_slow_path_llm_invalid_json_uses_fallback(self):
        """Test that invalid JSON from LLM uses fallback."""
        from core.flow.hybrid_router import HybridRoutingPolicy

        def mock_llm(prompt: str) -> str:
            return "not valid json"

        policy = HybridRoutingPolicy(llm_generate_fn=mock_llm)
        decision = policy.route(
            verdict="request_changes",
            severity="high",
            summary="Issues",
            blocker_count=2
        )
        assert decision.next_node == "executor"

    def test_slow_path_llm_invalid_node_uses_fallback(self):
        """Test that invalid node from LLM uses fallback."""
        from core.flow.hybrid_router import HybridRoutingPolicy

        def mock_llm(prompt: str) -> str:
            return '{"next_node": "invalid_node", "reasoning": "Bad"}'

        policy = HybridRoutingPolicy(llm_generate_fn=mock_llm)
        decision = policy.route(
            verdict="request_changes",
            severity="medium",
            summary="Issues",
            blocker_count=0
        )
        assert decision.next_node == "fixer"


class TestHybridRoutingPolicyDeterministicFallback:
    """Tests for deterministic fallback logic."""

    def test_fallback_medium_no_blockers_routes_to_fixer(self):
        """Test that medium severity with no blockers routes to fixer."""
        from core.flow.hybrid_router import HybridRoutingPolicy
        policy = HybridRoutingPolicy(llm_generate_fn=None)
        decision = policy.route(
            verdict="request_changes",
            severity="medium",
            summary="Issues",
            blocker_count=0
        )
        assert decision.next_node == "fixer"

    def test_fallback_high_severity_routes_to_executor(self):
        """Test that high severity routes to executor."""
        from core.flow.hybrid_router import HybridRoutingPolicy
        policy = HybridRoutingPolicy(llm_generate_fn=None)
        decision = policy.route(
            verdict="request_changes",
            severity="high",
            summary="Issues",
            blocker_count=0
        )
        assert decision.next_node == "executor"

    def test_fallback_medium_with_blockers_routes_to_executor(self):
        """Test that medium severity with blockers routes to executor."""
        from core.flow.hybrid_router import HybridRoutingPolicy
        policy = HybridRoutingPolicy(llm_generate_fn=None)
        decision = policy.route(
            verdict="request_changes",
            severity="medium",
            summary="Issues",
            blocker_count=2
        )
        assert decision.next_node == "executor"


class TestRoutingDecisionHITL:
    """Tests for requires_hitl_approval field in RoutingDecision."""

    def test_routing_decision_default_hitl_false(self):
        """Test that requires_hitl_approval defaults to False."""
        decision = RoutingDecision(
            next_node="fixer",
            reasoning="Reason",
            risk_assessment="Risk"
        )
        assert decision.requires_hitl_approval is False

    def test_routing_decision_hitl_true(self):
        """Test that requires_hitl_approval can be set to True."""
        decision = RoutingDecision(
            next_node="decision",
            reasoning="Reason",
            risk_assessment="Risk",
            requires_hitl_approval=True
        )
        assert decision.requires_hitl_approval is True


class TestTaskTypeRouting:
    """Tests for TaskType.ROUTING in RoutingEngine."""

    def test_task_type_routing_exists(self):
        """Test that TaskType.ROUTING exists."""
        from core.routing import TaskType
        assert hasattr(TaskType, "ROUTING")
        assert TaskType.ROUTING.value == "routing"

    def test_routing_task_maps_to_tier_1(self):
        """Test that ROUTING task maps to Tier 1."""
        from core.routing import RoutingEngine, TaskType, Tier
        engine = RoutingEngine(available_providers=["alicloud", "siliconflow"])
        tier = engine.get_tier_for_task(TaskType.ROUTING)
        assert tier == Tier.TIER_1


# =============================================================================
# EPIC C Phase C-5: HITL Gate Node Tests (Issue #3155)
# =============================================================================


class TestHITLRoutingDecision:
    """Tests for HITL-related routing decisions.

    EPIC C Phase C-5: HITL Wiring (Issue #3155)

    CTO Directive:
    - Router's Job: DECIDE (set requires_hitl_approval=True in state)
    - Orchestrator's Job: EXECUTE (implement interrupt logic in LangGraph)

    Note: These tests verify the routing logic without importing the full
    langgraph_orchestrator module to avoid import chain issues in CI.
    """

    def test_routing_decision_supports_hitl_approval(self):
        """Test that RoutingDecision supports requires_hitl_approval field."""
        decision = RoutingDecision(
            next_node="fixer",
            reasoning="Code needs fixing",
            risk_assessment="Low risk",
            requires_hitl_approval=True
        )
        assert decision.requires_hitl_approval is True

    def test_routing_decision_hitl_default_false(self):
        """Test that requires_hitl_approval defaults to False."""
        decision = RoutingDecision(
            next_node="publisher",
            reasoning="Ready to publish",
            risk_assessment="Low risk"
        )
        assert decision.requires_hitl_approval is False

    def test_routing_decision_hitl_serialization(self):
        """Test that requires_hitl_approval is included in serialization."""
        decision = RoutingDecision(
            next_node="executor",
            reasoning="Execute changes",
            risk_assessment="Medium risk",
            requires_hitl_approval=True
        )
        data = decision.model_dump()
        assert "requires_hitl_approval" in data
        assert data["requires_hitl_approval"] is True


class TestHITLStateManagement:
    """Tests for HITL state management patterns.

    EPIC C Phase C-5: HITL Wiring (Issue #3155)

    CTO Directive: "實作 hitl_approved 時，請確保它在任務完成後會被重置 (Reset)，
    以免影響同一個 Session 的下一次執行。"

    Note: These tests verify state management patterns without importing
    the full langgraph_orchestrator module.
    """

    def test_hitl_state_fields_exist_in_schema(self):
        """Test that HITL fields are defined in RoutingDecision schema."""
        assert "requires_hitl_approval" in RoutingDecision.model_fields

    def test_hitl_approval_field_is_boolean(self):
        """Test that requires_hitl_approval is typed as boolean."""
        field_info = RoutingDecision.model_fields["requires_hitl_approval"]
        assert field_info.annotation == bool

    def test_hitl_approval_has_default(self):
        """Test that requires_hitl_approval has a default value."""
        field_info = RoutingDecision.model_fields["requires_hitl_approval"]
        assert field_info.default is False


class TestHITLRoutingIntegration:
    """Tests for HITL integration with routing policy.

    EPIC C Phase C-5: HITL Wiring (Issue #3155)

    These tests verify that the routing policy correctly sets
    requires_hitl_approval for slow path decisions.
    """

    def test_fast_path_no_hitl_required(self):
        """Test that fast path decisions don't require HITL."""
        from core.flow.hybrid_router import HybridRoutingPolicy

        policy = HybridRoutingPolicy()
        decision = policy.route(
            verdict="approve",
            severity="low",
            summary="All good",
            blocker_count=0
        )
        assert decision.requires_hitl_approval is False

    def test_blocked_verdict_requires_hitl(self):
        """Test that blocked verdict requires HITL approval."""
        from core.flow.hybrid_router import HybridRoutingPolicy

        policy = HybridRoutingPolicy()
        decision = policy.route(
            verdict="blocked",
            severity="critical",
            summary="Security issue",
            blocker_count=1
        )
        assert decision.requires_hitl_approval is True

    def test_unknown_verdict_requires_hitl(self):
        """Test that unknown verdict requires HITL approval."""
        from core.flow.hybrid_router import HybridRoutingPolicy

        policy = HybridRoutingPolicy()
        decision = policy.route(
            verdict="unknown",
            severity="medium",
            summary="Unclear outcome",
            blocker_count=0
        )
        assert decision.requires_hitl_approval is True

    def test_slow_path_llm_decision_no_hitl(self):
        """Test that slow path LLM decisions don't require HITL by default."""
        from core.flow.hybrid_router import HybridRoutingPolicy

        def mock_llm(prompt: str) -> str:
            return '{"next_node": "fixer", "reasoning": "Fix needed"}'

        policy = HybridRoutingPolicy(llm_generate_fn=mock_llm)
        decision = policy.route(
            verdict="request_changes",
            severity="medium",
            summary="Medium issues",
            blocker_count=0
        )
        assert decision.requires_hitl_approval is False


class TestHITLGateNodeDesign:
    """Tests for HITL Gate Node design requirements.

    EPIC C Phase C-5: HITL Wiring (Issue #3155)

    CTO Directive: "請將 HITL Gate Node 設計為一個獨立的節點，置於 router_node 下游。
    這樣我們可以保持 Router 的純粹性（只做決策），將控制權交給 Gate。"

    Note: These tests verify design requirements without importing
    the full langgraph_orchestrator module.
    """

    def test_langgraph_interrupt_import_available(self):
        """Test that LangGraph interrupt function is available."""
        from langgraph.types import interrupt
        assert callable(interrupt)

    def test_langgraph_memory_saver_available(self):
        """Test that LangGraph MemorySaver is available for checkpointing."""
        from langgraph.checkpoint.memory import MemorySaver
        saver = MemorySaver()
        assert saver is not None

    def test_state_graph_available(self):
        """Test that LangGraph StateGraph is available."""
        from langgraph.graph import StateGraph, END
        assert StateGraph is not None
        assert END is not None


# =============================================================================
# C-5 Pilot: CANONICAL_NODES Validation Tests (Issue #3157)
# =============================================================================


class TestCanonicalNodesValidation:
    """Tests to validate CANONICAL_NODES against actual LangGraph node IDs.

    Issue #3157: Ensure CANONICAL_NODES in hybrid_router.py matches actual
    graph nodes in langgraph_orchestrator.py to prevent runtime routing failures.

    Risk: If CANONICAL_NODES doesn't match actual graph nodes:
    - Router may route to non-existent nodes
    - Flow Controller will fail at runtime
    """

    ACTUAL_GRAPH_NODES = frozenset({
        "review_intake",
        "internal_review",
        "planner",
        "pm_advisor",
        "ops_advisor",
        "security_advisor",
        "governance_advisor",
        "cost_advisor",
        "permission_advisor",
        "reputation_advisor",
        "policy_enforcement",
        "executor",
        "ci_monitor",
        "reviewer",
        "decision",
        "fixer",
        "publisher",
        "finalizer",
        "evaluation",
        "hitl_gate",
    })

    def test_all_canonical_nodes_exist_in_graph(self):
        """Test that all CANONICAL_NODES exist in actual LangGraph definition.

        This is the primary validation test to prevent routing to non-existent nodes.
        """
        from core.flow.hybrid_router import CANONICAL_NODES

        missing_nodes = CANONICAL_NODES - self.ACTUAL_GRAPH_NODES
        assert not missing_nodes, (
            f"CANONICAL_NODES contains nodes not in actual graph: {missing_nodes}. "
            f"Either add these nodes to langgraph_orchestrator.py or remove from CANONICAL_NODES."
        )

    def test_canonical_nodes_contains_required_routing_targets(self):
        """Test that CANONICAL_NODES contains all nodes the router can route to.

        These are the nodes that HybridRoutingPolicy can return as next_node.
        """
        from core.flow.hybrid_router import CANONICAL_NODES

        required_routing_targets = {"publisher", "fixer", "executor", "decision"}
        missing = required_routing_targets - CANONICAL_NODES
        assert not missing, (
            f"CANONICAL_NODES missing required routing targets: {missing}. "
            f"HybridRoutingPolicy routes to these nodes."
        )

    def test_canonical_nodes_is_frozen(self):
        """Test that CANONICAL_NODES is immutable (frozenset)."""
        from core.flow.hybrid_router import CANONICAL_NODES

        assert isinstance(CANONICAL_NODES, frozenset), (
            "CANONICAL_NODES should be a frozenset to prevent accidental modification"
        )

    def test_node_aliases_map_to_canonical_nodes(self):
        """Test that all NODE_ALIASES values are in CANONICAL_NODES."""
        from core.flow.hybrid_router import NODE_ALIASES, CANONICAL_NODES

        for alias, canonical in NODE_ALIASES.items():
            assert canonical in CANONICAL_NODES, (
                f"NODE_ALIASES['{alias}'] = '{canonical}' is not in CANONICAL_NODES. "
                f"Add '{canonical}' to CANONICAL_NODES or fix the alias mapping."
            )

    def test_canonical_nodes_count(self):
        """Test that CANONICAL_NODES has expected count.

        This test will fail if nodes are added/removed, prompting review.
        """
        from core.flow.hybrid_router import CANONICAL_NODES

        expected_count = 8
        assert len(CANONICAL_NODES) == expected_count, (
            f"CANONICAL_NODES count changed from {expected_count} to {len(CANONICAL_NODES)}. "
            f"If intentional, update this test. Current nodes: {sorted(CANONICAL_NODES)}"
        )

    def test_canonical_nodes_subset_of_actual_graph(self):
        """Test that CANONICAL_NODES is a subset of actual graph nodes.

        CANONICAL_NODES doesn't need to contain ALL graph nodes, just the ones
        the router can route to. But all CANONICAL_NODES must exist in the graph.
        """
        from core.flow.hybrid_router import CANONICAL_NODES

        assert CANONICAL_NODES.issubset(self.ACTUAL_GRAPH_NODES), (
            f"CANONICAL_NODES is not a subset of actual graph nodes. "
            f"Extra nodes: {CANONICAL_NODES - self.ACTUAL_GRAPH_NODES}"
        )

    def test_hybrid_router_routing_targets_in_canonical_nodes(self):
        """Test that all nodes HybridRoutingPolicy can route to are in CANONICAL_NODES.

        This validates the routing logic won't produce invalid node names.
        """
        from core.flow.hybrid_router import HybridRoutingPolicy, CANONICAL_NODES

        policy = HybridRoutingPolicy(llm_generate_fn=None)

        test_cases = [
            ("approve", "low", "Test", 0),
            ("blocked", "high", "Test", 1),
            ("unknown", "medium", "Test", 0),
            ("request_changes", "low", "Test", 0),
            ("request_changes", "medium", "Test", 0),
            ("request_changes", "high", "Test", 2),
            ("comment", "low", "Test", 0),
        ]

        for verdict, severity, summary, blockers in test_cases:
            decision = policy.route(verdict, severity, summary, blockers)
            assert decision.next_node in CANONICAL_NODES, (
                f"HybridRoutingPolicy.route({verdict}, {severity}) returned "
                f"'{decision.next_node}' which is not in CANONICAL_NODES"
            )

    def test_document_canonical_nodes_mapping(self):
        """Document the expected mapping between CANONICAL_NODES and graph nodes.

        This test serves as documentation and will fail if the mapping changes.
        """
        from core.flow.hybrid_router import CANONICAL_NODES

        expected_canonical_nodes = {
            "publisher",
            "fixer",
            "executor",
            "decision",
            "finalizer",
            "reviewer",
            "planner",
            "ci_monitor",
        }

        assert CANONICAL_NODES == expected_canonical_nodes, (
            f"CANONICAL_NODES changed. Expected: {sorted(expected_canonical_nodes)}, "
            f"Got: {sorted(CANONICAL_NODES)}. Update this test if change is intentional."
        )
