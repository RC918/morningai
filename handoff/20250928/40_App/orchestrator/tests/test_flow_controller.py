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
