"""
Unit tests for F-6 Model Tier Selection + Decision Hooks

Tests for:
- ModelTierSelector: Rule-based model tier selection
- TierContext: Context for tier selection decisions
- DebateHook: Integration with Debate Engine v2
- MemoryHook: Placeholder for Memory v2 integration
- HookChain: Chain of planner hooks
- apply_model_tiers_and_hooks: Convenience function
"""

import uuid
from unittest.mock import patch

from core.planner.model_tier_selection import (
    TierContext,
    ProviderStatus,
    ProviderHealthSnapshot,
    SimulationResult,
    ModelTierSelector,
    DebateHook,
    MemoryHook,
    HookChain,
    apply_model_tiers_and_hooks,
)
from core.planner.planner_types import (
    PlannerOutput,
    PlanType,
    RiskLevel,
    RiskMetadata,
    TaskNode,
    TaskTree,
    TaskType,
)


class TestTierContext:
    """Tests for TierContext dataclass."""

    def test_default_values(self):
        """Test default values for TierContext."""
        context = TierContext()
        assert context.complexity == "medium"
        assert context.provider_preference is None
        assert context.cost_sensitive is False
        assert context.latency_sensitive is False

    def test_custom_values(self):
        """Test custom values for TierContext."""
        context = TierContext(
            complexity="high",
            provider_preference="openai",
            cost_sensitive=True,
            latency_sensitive=True,
        )
        assert context.complexity == "high"
        assert context.provider_preference == "openai"
        assert context.cost_sensitive is True
        assert context.latency_sensitive is True


class TestProviderStatus:
    """Tests for ProviderStatus dataclass."""

    def test_default_values(self):
        """Test default values for ProviderStatus."""
        status = ProviderStatus()
        assert status.health_score == 1.0
        assert status.rate_limit_remaining == 1000
        assert status.latency_p99_ms == 100.0
        assert status.recommended_tier is None

    def test_custom_values(self):
        """Test custom values for ProviderStatus."""
        status = ProviderStatus(
            health_score=0.8,
            rate_limit_remaining=500,
            latency_p99_ms=200.0,
            recommended_tier="tier_1",
        )
        assert status.health_score == 0.8
        assert status.rate_limit_remaining == 500
        assert status.latency_p99_ms == 200.0
        assert status.recommended_tier == "tier_1"


class TestProviderHealthSnapshot:
    """Tests for ProviderHealthSnapshot dataclass."""

    def test_default_values(self):
        """Test default values for ProviderHealthSnapshot."""
        snapshot = ProviderHealthSnapshot()
        assert snapshot.timestamp == ""
        assert snapshot.providers == {}

    def test_custom_values(self):
        """Test custom values for ProviderHealthSnapshot."""
        snapshot = ProviderHealthSnapshot(
            timestamp="2026-01-14T10:00:00Z",
            providers={
                "openai": ProviderStatus(health_score=0.9),
                "gemini": ProviderStatus(health_score=0.8),
            },
        )
        assert snapshot.timestamp == "2026-01-14T10:00:00Z"
        assert len(snapshot.providers) == 2
        assert snapshot.providers["openai"].health_score == 0.9


class TestSimulationResult:
    """Tests for SimulationResult dataclass."""

    def test_default_values(self):
        """Test default values for SimulationResult."""
        result = SimulationResult()
        assert result.estimated_cost_usd == 0.0
        assert result.estimated_duration_minutes == 0
        assert result.risk_assessment == "low"
        assert result.requires_approval is False
        assert result.warnings == []

    def test_custom_values(self):
        """Test custom values for SimulationResult."""
        result = SimulationResult(
            estimated_cost_usd=10.5,
            estimated_duration_minutes=30,
            risk_assessment="high",
            requires_approval=True,
            warnings=["High cost", "Long duration"],
        )
        assert result.estimated_cost_usd == 10.5
        assert result.estimated_duration_minutes == 30
        assert result.risk_assessment == "high"
        assert result.requires_approval is True
        assert len(result.warnings) == 2


class TestModelTierSelector:
    """Tests for ModelTierSelector class."""

    def _create_task(
        self,
        task_type: TaskType,
        risk_level: RiskLevel = RiskLevel.LOW,
    ) -> TaskNode:
        """Helper to create a TaskNode for testing."""
        return TaskNode(
            task_id=str(uuid.uuid4()),
            task_type=task_type,
            description=f"Test {task_type.value} task",
            risk_level=risk_level,
        )

    def _create_plan(
        self,
        task_types: list,
        risk_level: RiskLevel = RiskLevel.LOW,
    ) -> PlannerOutput:
        """Helper to create a PlannerOutput for testing."""
        nodes = [
            TaskNode(
                task_id=f"task-{i}",
                task_type=tt,
                description=f"Test {tt.value} task",
                risk_level=risk_level,
            )
            for i, tt in enumerate(task_types)
        ]
        return PlannerOutput(
            plan_id=str(uuid.uuid4()),
            plan_type=PlanType.DETAILED,
            goal="Test goal",
            task_tree=TaskTree(nodes=nodes, edges=[]),
            risk_metadata=RiskMetadata(overall_risk=risk_level),
        )

    def test_select_tier_critical_risk(self):
        """Test tier_0 selection for critical risk tasks."""
        selector = ModelTierSelector()
        task = self._create_task(TaskType.CODE, RiskLevel.CRITICAL)
        tier = selector.select_tier(task)
        assert tier == "tier_0"

    def test_select_tier_high_risk_code(self):
        """Test tier_0 selection for high risk code tasks."""
        selector = ModelTierSelector()
        task = self._create_task(TaskType.CODE, RiskLevel.HIGH)
        tier = selector.select_tier(task)
        assert tier == "tier_0"

    def test_select_tier_high_risk_deploy(self):
        """Test tier_0 selection for high risk deploy tasks."""
        selector = ModelTierSelector()
        task = self._create_task(TaskType.DEPLOY, RiskLevel.HIGH)
        tier = selector.select_tier(task)
        assert tier == "tier_0"

    def test_select_tier_high_risk_review(self):
        """Test tier_1 selection for high risk review tasks."""
        selector = ModelTierSelector()
        task = self._create_task(TaskType.REVIEW, RiskLevel.HIGH)
        tier = selector.select_tier(task)
        assert tier == "tier_1"

    def test_select_tier_deploy_medium_risk(self):
        """Test tier_1 selection for medium risk deploy tasks."""
        selector = ModelTierSelector()
        task = self._create_task(TaskType.DEPLOY, RiskLevel.MEDIUM)
        tier = selector.select_tier(task)
        assert tier == "tier_1"

    def test_select_tier_code_high_complexity(self):
        """Test tier_1 selection for high complexity code tasks."""
        selector = ModelTierSelector()
        task = self._create_task(TaskType.CODE, RiskLevel.LOW)
        context = TierContext(complexity="high")
        tier = selector.select_tier(task, context)
        assert tier == "tier_1"

    def test_select_tier_code_standard(self):
        """Test tier_2 selection for standard code tasks."""
        selector = ModelTierSelector()
        task = self._create_task(TaskType.CODE, RiskLevel.LOW)
        tier = selector.select_tier(task)
        assert tier == "tier_2"

    def test_select_tier_cleanup_cost_sensitive(self):
        """Test tier_3 selection for cost-sensitive cleanup tasks."""
        selector = ModelTierSelector()
        task = self._create_task(TaskType.CLEANUP, RiskLevel.LOW)
        context = TierContext(cost_sensitive=True)
        tier = selector.select_tier(task, context)
        assert tier == "tier_3"

    def test_select_tier_setup_latency_sensitive(self):
        """Test tier_3 selection for latency-sensitive setup tasks."""
        selector = ModelTierSelector()
        task = self._create_task(TaskType.SETUP, RiskLevel.LOW)
        context = TierContext(latency_sensitive=True)
        tier = selector.select_tier(task, context)
        assert tier == "tier_3"

    def test_select_tier_default(self):
        """Test default tier_2 selection for analyze tasks."""
        selector = ModelTierSelector()
        task = self._create_task(TaskType.ANALYZE, RiskLevel.LOW)
        tier = selector.select_tier(task)
        assert tier == "tier_2"

    def test_get_plan_tiers(self):
        """Test getting tier assignments for all tasks in a plan."""
        selector = ModelTierSelector()
        plan = self._create_plan(
            [TaskType.CODE, TaskType.TEST, TaskType.DEPLOY],
            RiskLevel.LOW,
        )
        tiers = selector.get_plan_tiers(plan)
        assert len(tiers) == 3
        assert tiers["task-0"] == "tier_2"
        assert tiers["task-1"] == "tier_2"
        assert tiers["task-2"] == "tier_1"

    @patch("core.planner.model_tier_selection._use_model_tier_selection", return_value=True)
    def test_apply_tiers_enabled(self, mock_use):
        """Test applying tiers when feature is enabled."""
        selector = ModelTierSelector()
        plan = self._create_plan(
            [TaskType.CODE, TaskType.TEST, TaskType.CLEANUP],
            RiskLevel.LOW,
        )
        result = selector.apply_tiers(plan)
        assert "default_tier" in result.model_tier_hints
        assert "per_task_overrides" in result.model_tier_hints

    @patch("core.planner.model_tier_selection._use_model_tier_selection", return_value=False)
    def test_apply_tiers_disabled(self, mock_use):
        """Test skipping tiers when feature is disabled."""
        selector = ModelTierSelector()
        plan = self._create_plan([TaskType.CODE], RiskLevel.LOW)
        original_hints = plan.model_tier_hints.copy()
        result = selector.apply_tiers(plan)
        assert result.model_tier_hints == original_hints


class TestDebateHook:
    """Tests for DebateHook class."""

    def _create_plan(
        self,
        risk_level: RiskLevel = RiskLevel.LOW,
        task_risk_levels: list = None,
    ) -> PlannerOutput:
        """Helper to create a PlannerOutput for testing."""
        if task_risk_levels is None:
            task_risk_levels = [risk_level]

        nodes = [
            TaskNode(
                task_id=f"task-{i}",
                task_type=TaskType.CODE,
                description=f"Test task {i}",
                risk_level=rl,
            )
            for i, rl in enumerate(task_risk_levels)
        ]
        return PlannerOutput(
            plan_id=str(uuid.uuid4()),
            plan_type=PlanType.DETAILED,
            goal="Test goal",
            task_tree=TaskTree(nodes=nodes, edges=[]),
            risk_metadata=RiskMetadata(overall_risk=risk_level),
        )

    def test_should_trigger_debate_high_risk(self):
        """Test debate triggers for high risk plans."""
        hook = DebateHook(trace_id="test")
        plan = self._create_plan(RiskLevel.HIGH)
        assert hook._should_trigger_debate(plan) is True

    def test_should_trigger_debate_critical_risk(self):
        """Test debate triggers for critical risk plans."""
        hook = DebateHook(trace_id="test")
        plan = self._create_plan(RiskLevel.CRITICAL)
        assert hook._should_trigger_debate(plan) is True

    def test_should_trigger_debate_multiple_high_risk_tasks(self):
        """Test debate triggers for multiple high risk tasks."""
        hook = DebateHook(trace_id="test")
        plan = self._create_plan(
            RiskLevel.MEDIUM,
            task_risk_levels=[RiskLevel.HIGH, RiskLevel.HIGH],
        )
        assert hook._should_trigger_debate(plan) is True

    def test_should_not_trigger_debate_low_risk(self):
        """Test debate does not trigger for low risk plans."""
        hook = DebateHook(trace_id="test")
        plan = self._create_plan(RiskLevel.LOW)
        assert hook._should_trigger_debate(plan) is False

    def test_should_not_trigger_debate_single_high_risk_task(self):
        """Test debate does not trigger for single high risk task."""
        hook = DebateHook(trace_id="test")
        plan = self._create_plan(
            RiskLevel.MEDIUM,
            task_risk_levels=[RiskLevel.HIGH],
        )
        assert hook._should_trigger_debate(plan) is False

    @patch("core.planner.model_tier_selection._use_debate_hook", return_value=False)
    def test_on_plan_created_disabled(self, mock_use):
        """Test hook passes through when disabled."""
        hook = DebateHook(trace_id="test")
        plan = self._create_plan(RiskLevel.HIGH)
        result = hook.on_plan_created(plan)
        assert result is plan

    @patch("core.planner.model_tier_selection._use_debate_hook", return_value=True)
    def test_on_plan_created_low_risk(self, mock_use):
        """Test hook passes through for low risk plans."""
        hook = DebateHook(trace_id="test")
        plan = self._create_plan(RiskLevel.LOW)
        result = hook.on_plan_created(plan)
        assert result is plan

    def test_on_task_assigned_passthrough(self):
        """Test task assignment passes through unchanged."""
        hook = DebateHook(trace_id="test")
        task = TaskNode(
            task_id="test-task",
            task_type=TaskType.CODE,
            description="Test task",
        )
        result_task, result_agent = hook.on_task_assigned(task, "dev_agent")
        assert result_task is task
        assert result_agent == "dev_agent"


class TestMemoryHook:
    """Tests for MemoryHook class."""

    def _create_plan(self) -> PlannerOutput:
        """Helper to create a PlannerOutput for testing."""
        return PlannerOutput(
            plan_id=str(uuid.uuid4()),
            plan_type=PlanType.DETAILED,
            goal="Test goal",
            task_tree=TaskTree(nodes=[], edges=[]),
            risk_metadata=RiskMetadata(overall_risk=RiskLevel.LOW),
        )

    def test_on_plan_created_passthrough(self):
        """Test plan passes through unchanged (stub implementation)."""
        hook = MemoryHook(trace_id="test")
        plan = self._create_plan()
        result = hook.on_plan_created(plan)
        assert result is plan

    def test_on_task_assigned_passthrough(self):
        """Test task assignment passes through unchanged."""
        hook = MemoryHook(trace_id="test")
        task = TaskNode(
            task_id="test-task",
            task_type=TaskType.CODE,
            description="Test task",
        )
        result_task, result_agent = hook.on_task_assigned(task, "dev_agent")
        assert result_task is task
        assert result_agent == "dev_agent"


class TestHookChain:
    """Tests for HookChain class."""

    def _create_plan(self) -> PlannerOutput:
        """Helper to create a PlannerOutput for testing."""
        return PlannerOutput(
            plan_id=str(uuid.uuid4()),
            plan_type=PlanType.DETAILED,
            goal="Test goal",
            task_tree=TaskTree(nodes=[], edges=[]),
            risk_metadata=RiskMetadata(overall_risk=RiskLevel.LOW),
        )

    def test_empty_chain(self):
        """Test empty hook chain passes through unchanged."""
        chain = HookChain()
        plan = self._create_plan()
        result = chain.apply_to_plan(plan)
        assert result is plan

    def test_add_hook(self):
        """Test adding hooks to chain."""
        chain = HookChain()
        chain.add_hook(MemoryHook())
        assert len(chain.hooks) == 1

    def test_apply_to_plan(self):
        """Test applying hooks to plan."""
        chain = HookChain([MemoryHook()])
        plan = self._create_plan()
        result = chain.apply_to_plan(plan)
        assert result is plan

    def test_apply_to_assignment(self):
        """Test applying hooks to task assignment."""
        chain = HookChain([MemoryHook()])
        task = TaskNode(
            task_id="test-task",
            task_type=TaskType.CODE,
            description="Test task",
        )
        result_task, result_agent = chain.apply_to_assignment(task, "dev_agent")
        assert result_task is task
        assert result_agent == "dev_agent"


class TestApplyModelTiersAndHooks:
    """Tests for apply_model_tiers_and_hooks convenience function."""

    def _create_plan(self) -> PlannerOutput:
        """Helper to create a PlannerOutput for testing."""
        nodes = [
            TaskNode(
                task_id="task-0",
                task_type=TaskType.CODE,
                description="Test code task",
                risk_level=RiskLevel.LOW,
            ),
        ]
        return PlannerOutput(
            plan_id=str(uuid.uuid4()),
            plan_type=PlanType.DETAILED,
            goal="Test goal",
            task_tree=TaskTree(nodes=nodes, edges=[]),
            risk_metadata=RiskMetadata(overall_risk=RiskLevel.LOW),
        )

    @patch("core.planner.model_tier_selection._use_model_tier_selection", return_value=True)
    @patch("core.planner.model_tier_selection._use_debate_hook", return_value=False)
    def test_apply_with_defaults(self, mock_debate, mock_tier):
        """Test applying with default hooks."""
        plan = self._create_plan()
        result = apply_model_tiers_and_hooks(plan, trace_id="test")
        assert "default_tier" in result.model_tier_hints

    @patch("core.planner.model_tier_selection._use_model_tier_selection", return_value=True)
    def test_apply_with_custom_hooks(self, mock_tier):
        """Test applying with custom hooks."""
        plan = self._create_plan()
        custom_hooks = [MemoryHook(trace_id="test")]
        result = apply_model_tiers_and_hooks(
            plan,
            hooks=custom_hooks,
            trace_id="test",
        )
        assert "default_tier" in result.model_tier_hints

    @patch("core.planner.model_tier_selection._use_model_tier_selection", return_value=False)
    @patch("core.planner.model_tier_selection._use_debate_hook", return_value=False)
    def test_apply_all_disabled(self, mock_debate, mock_tier):
        """Test applying when all features are disabled."""
        plan = self._create_plan()
        result = apply_model_tiers_and_hooks(plan, trace_id="test")
        assert result.model_tier_hints == {}
