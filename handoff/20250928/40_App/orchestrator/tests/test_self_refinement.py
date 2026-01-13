"""
Unit tests for F-5 Self-refinement Loop

EPIC F Phase F-5: Self-refinement Loop

Tests for:
- FeedbackCollector: Collecting and aggregating execution feedback
- Replanner: Partial and full replanning
- SelfRefinementLoop: Closed loop execution with refinement
"""

from unittest.mock import MagicMock, patch

from core.planner.consumer import ExecutionStatus, TaskResult
from core.planner.planner_types import (
    PlannerMetadata,
    PlannerOutput,
    PlanType,
    RiskLevel,
    TaskEdge,
    TaskNode,
    TaskTree,
    TaskType,
)
from core.planner.self_refinement import (
    ExecutionFeedback,
    FeedbackCollector,
    FeedbackStatus,
    PlanFeedback,
    RefinementResult,
    Replanner,
    SelfRefinementLoop,
)


class TestExecutionFeedback:
    """Tests for ExecutionFeedback dataclass"""

    def test_from_task_result_success(self):
        """Test creating feedback from successful task result"""
        result = TaskResult(
            task_id="task-1",
            status=ExecutionStatus.COMPLETED,
            outputs={"result": "success"},
            actual_duration_minutes=5,
        )

        feedback = ExecutionFeedback.from_task_result(result)

        assert feedback.task_id == "task-1"
        assert feedback.status == FeedbackStatus.SUCCESS
        assert feedback.actual_duration_minutes == 5
        assert feedback.outputs == {"result": "success"}
        assert feedback.error_message is None

    def test_from_task_result_failed(self):
        """Test creating feedback from failed task result"""
        result = TaskResult(
            task_id="task-2",
            status=ExecutionStatus.FAILED,
            outputs={},
            error_message="Task failed due to error",
            actual_duration_minutes=3,
        )

        feedback = ExecutionFeedback.from_task_result(result)

        assert feedback.task_id == "task-2"
        assert feedback.status == FeedbackStatus.FAILED
        assert feedback.error_message == "Task failed due to error"

    def test_from_task_result_partial(self):
        """Test creating feedback from partial task result"""
        result = TaskResult(
            task_id="task-3",
            status=ExecutionStatus.IN_PROGRESS,
            outputs={"partial": True},
        )

        feedback = ExecutionFeedback.from_task_result(result)

        assert feedback.task_id == "task-3"
        assert feedback.status == FeedbackStatus.PARTIAL

    def test_to_dict(self):
        """Test serialization to dictionary"""
        feedback = ExecutionFeedback(
            task_id="task-1",
            status=FeedbackStatus.SUCCESS,
            actual_duration_minutes=5,
            outputs={"result": "success"},
        )

        data = feedback.to_dict()

        assert data["task_id"] == "task-1"
        assert data["status"] == "success"
        assert data["actual_duration_minutes"] == 5


class TestFeedbackCollector:
    """Tests for FeedbackCollector class"""

    def test_collect_success(self):
        """Test collecting feedback from successful task"""
        collector = FeedbackCollector()
        result = TaskResult(
            task_id="task-1",
            status=ExecutionStatus.COMPLETED,
            outputs={"result": "success"},
        )

        feedback = collector.collect("task-1", result)

        assert feedback.task_id == "task-1"
        assert feedback.status == FeedbackStatus.SUCCESS

    def test_collect_failure_with_context(self):
        """Test collecting feedback from failed task with failure context"""
        collector = FeedbackCollector()
        result = TaskResult(
            task_id="task-2",
            status=ExecutionStatus.FAILED,
            outputs={},
            error_message="Test error",
        )

        with patch.object(collector, "_get_failure_context", return_value="context"):
            feedback = collector.collect("task-2", result)

        assert feedback.task_id == "task-2"
        assert feedback.status == FeedbackStatus.FAILED
        assert feedback.failure_context == "context"

    def test_aggregate_all_success(self):
        """Test aggregating all successful feedbacks"""
        collector = FeedbackCollector()
        feedbacks = [
            ExecutionFeedback(task_id="task-1", status=FeedbackStatus.SUCCESS),
            ExecutionFeedback(task_id="task-2", status=FeedbackStatus.SUCCESS),
        ]

        plan_feedback = collector.aggregate(feedbacks, "plan-1")

        assert plan_feedback.plan_id == "plan-1"
        assert plan_feedback.has_failures is False
        assert plan_feedback.recoverable is True
        assert plan_feedback.success_rate == 1.0
        assert len(plan_feedback.failed_task_ids) == 0

    def test_aggregate_with_failures(self):
        """Test aggregating feedbacks with failures"""
        collector = FeedbackCollector()
        feedbacks = [
            ExecutionFeedback(task_id="task-1", status=FeedbackStatus.SUCCESS),
            ExecutionFeedback(task_id="task-2", status=FeedbackStatus.FAILED),
        ]

        plan_feedback = collector.aggregate(feedbacks, "plan-1")

        assert plan_feedback.has_failures is True
        assert plan_feedback.success_rate == 0.5
        assert "task-2" in plan_feedback.failed_task_ids

    def test_aggregate_non_recoverable_high_failure_rate(self):
        """Test that high failure rate is non-recoverable"""
        collector = FeedbackCollector()
        feedbacks = [
            ExecutionFeedback(task_id="task-1", status=FeedbackStatus.FAILED),
            ExecutionFeedback(task_id="task-2", status=FeedbackStatus.FAILED),
            ExecutionFeedback(task_id="task-3", status=FeedbackStatus.SUCCESS),
        ]

        plan_feedback = collector.aggregate(feedbacks, "plan-1")

        assert plan_feedback.recoverable is False

    def test_aggregate_non_recoverable_auth_error(self):
        """Test that authentication errors are non-recoverable"""
        collector = FeedbackCollector()
        feedbacks = [
            ExecutionFeedback(
                task_id="task-1",
                status=FeedbackStatus.FAILED,
                error_message="Authentication failed",
            ),
        ]

        plan_feedback = collector.aggregate(feedbacks, "plan-1")

        assert plan_feedback.recoverable is False


class TestReplanner:
    """Tests for Replanner class"""

    def _create_test_plan(self) -> PlannerOutput:
        """Create a test plan for replanning tests"""
        nodes = [
            TaskNode(
                task_id="task-1",
                task_type=TaskType.ANALYZE,
                description="Analyze code",
            ),
            TaskNode(
                task_id="task-2",
                task_type=TaskType.CODE,
                description="Write code",
            ),
        ]
        edges = [
            TaskEdge(from_task="task-1", to_task="task-2"),
        ]
        return PlannerOutput(
            plan_id="test-plan",
            plan_type=PlanType.DETAILED,
            goal="Test goal",
            task_tree=TaskTree(nodes=nodes, edges=edges),
            planner_metadata=PlannerMetadata(planner_type="test"),
        )

    def test_should_replan_no_failures(self):
        """Test that no replan is needed when no failures"""
        replanner = Replanner()
        plan = self._create_test_plan()
        feedback = PlanFeedback(
            plan_id="test-plan",
            has_failures=False,
            recoverable=True,
        )

        assert replanner.should_replan(plan, feedback) is False

    def test_should_replan_non_recoverable(self):
        """Test that no replan when failures are non-recoverable"""
        replanner = Replanner()
        plan = self._create_test_plan()
        feedback = PlanFeedback(
            plan_id="test-plan",
            has_failures=True,
            recoverable=False,
            failed_task_ids=["task-1"],
        )

        assert replanner.should_replan(plan, feedback) is False

    def test_should_replan_recoverable(self):
        """Test that replan is needed for recoverable failures"""
        replanner = Replanner()
        plan = self._create_test_plan()
        feedback = PlanFeedback(
            plan_id="test-plan",
            has_failures=True,
            recoverable=True,
            failed_task_ids=["task-1"],
        )

        assert replanner.should_replan(plan, feedback) is True

    def test_should_replan_max_task_replans_exceeded(self):
        """Test that no replan when max task replans exceeded"""
        replanner = Replanner(max_task_replans=2)
        plan = self._create_test_plan()
        feedback = PlanFeedback(
            plan_id="test-plan",
            has_failures=True,
            recoverable=True,
            failed_task_ids=["task-1"],
        )

        replanner._task_replan_counts["task-1"] = 2

        assert replanner.should_replan(plan, feedback) is False

    def test_should_replan_max_full_replans_exceeded(self):
        """Test that no replan when max full replans exceeded"""
        replanner = Replanner(max_full_replans=1)
        plan = self._create_test_plan()
        feedback = PlanFeedback(
            plan_id="test-plan",
            has_failures=True,
            recoverable=True,
            failed_task_ids=["task-1"],
        )

        replanner._full_replan_count = 1

        assert replanner.should_replan(plan, feedback) is False

    def test_replan_partial(self):
        """Test partial replan for single task failure"""
        replanner = Replanner()
        plan = self._create_test_plan()
        feedback = ExecutionFeedback(
            task_id="task-1",
            status=FeedbackStatus.FAILED,
            error_message="Test error",
        )

        new_plan = replanner.replan_partial(plan, "task-1", feedback)

        assert len(new_plan.task_tree.nodes) == 4
        recovery_tasks = [n for n in new_plan.task_tree.nodes if "recovery" in n.task_id]
        retry_tasks = [n for n in new_plan.task_tree.nodes if "retry" in n.task_id]
        assert len(recovery_tasks) == 1
        assert len(retry_tasks) == 1
        assert replanner._task_replan_counts["task-1"] == 1

    def test_replan_partial_increments_count(self):
        """Test that partial replan increments task replan count"""
        replanner = Replanner()
        plan = self._create_test_plan()
        feedback = ExecutionFeedback(
            task_id="task-1",
            status=FeedbackStatus.FAILED,
            error_message="Test error",
        )

        replanner.replan_partial(plan, "task-1", feedback)
        replanner.replan_partial(plan, "task-1", feedback)

        assert replanner._task_replan_counts["task-1"] == 2

    def test_replan_full(self):
        """Test full replan with failure context"""
        replanner = Replanner()
        plan = self._create_test_plan()
        feedback = PlanFeedback(
            plan_id="test-plan",
            has_failures=True,
            recoverable=True,
            failed_task_ids=["task-1", "task-2"],
            feedbacks=[
                ExecutionFeedback(
                    task_id="task-1",
                    status=FeedbackStatus.FAILED,
                    error_message="Error 1",
                ),
                ExecutionFeedback(
                    task_id="task-2",
                    status=FeedbackStatus.FAILED,
                    error_message="Error 2",
                ),
            ],
        )

        new_plan = replanner.replan_full(plan, feedback)

        assert "replan-1" in new_plan.plan_id
        assert "[Replan Context]" in new_plan.goal
        assert new_plan.risk_metadata.overall_risk == RiskLevel.HIGH
        assert new_plan.risk_metadata.requires_approval is True
        assert replanner._full_replan_count == 1

    def test_reset(self):
        """Test resetting replan counts"""
        replanner = Replanner()
        replanner._task_replan_counts["task-1"] = 2
        replanner._full_replan_count = 1

        replanner.reset()

        assert len(replanner._task_replan_counts) == 0
        assert replanner._full_replan_count == 0

    def test_get_replan_counts(self):
        """Test getting replan counts"""
        replanner = Replanner(max_task_replans=3, max_full_replans=2)
        replanner._task_replan_counts["task-1"] = 1
        replanner._full_replan_count = 1

        counts = replanner.get_replan_counts()

        assert counts["task_replans"] == {"task-1": 1}
        assert counts["full_replans"] == 1
        assert counts["max_task_replans"] == 3
        assert counts["max_full_replans"] == 2


class TestSelfRefinementLoop:
    """Tests for SelfRefinementLoop class"""

    def _create_test_plan(self) -> PlannerOutput:
        """Create a test plan for loop tests"""
        nodes = [
            TaskNode(
                task_id="task-1",
                task_type=TaskType.ANALYZE,
                description="Analyze code",
            ),
        ]
        return PlannerOutput(
            plan_id="test-plan",
            plan_type=PlanType.DETAILED,
            goal="Test goal",
            task_tree=TaskTree(nodes=nodes, edges=[]),
            planner_metadata=PlannerMetadata(planner_type="test"),
        )

    def _create_mock_executor(self, results: list) -> MagicMock:
        """Create a mock executor that returns specified results"""
        executor = MagicMock()
        executor.execute.side_effect = results
        return executor

    @patch("core.planner.self_refinement.USE_SELF_REFINEMENT", False)
    def test_execute_without_refinement_disabled(self):
        """Test execution when self-refinement is disabled"""
        plan = self._create_test_plan()
        executor = self._create_mock_executor([
            TaskResult(
                task_id="task-1",
                status=ExecutionStatus.COMPLETED,
                outputs={},
            )
        ])

        loop = SelfRefinementLoop(executor=executor)
        result = loop.execute_with_refinement(plan)

        assert result.execution_result.status == ExecutionStatus.COMPLETED
        assert result.total_replans == 0
        assert result.escalated_to_hitl is False

    @patch("core.planner.self_refinement.USE_SELF_REFINEMENT", True)
    def test_execute_with_refinement_success(self):
        """Test successful execution with refinement enabled"""
        plan = self._create_test_plan()
        executor = self._create_mock_executor([
            TaskResult(
                task_id="task-1",
                status=ExecutionStatus.COMPLETED,
                outputs={},
            )
        ])

        loop = SelfRefinementLoop(executor=executor)
        result = loop.execute_with_refinement(plan)

        assert result.execution_result.status == ExecutionStatus.COMPLETED
        assert result.total_replans == 0

    @patch("core.planner.self_refinement.USE_SELF_REFINEMENT", True)
    def test_execute_with_refinement_failure_escalates(self):
        """Test that non-recoverable failure escalates to HITL"""
        plan = self._create_test_plan()
        executor = self._create_mock_executor([
            TaskResult(
                task_id="task-1",
                status=ExecutionStatus.FAILED,
                outputs={},
                error_message="Authentication failed",
            )
        ])

        loop = SelfRefinementLoop(executor=executor)
        result = loop.execute_with_refinement(plan)

        assert result.execution_result.status == ExecutionStatus.FAILED
        assert result.escalated_to_hitl is True

    def test_get_replan_history(self):
        """Test getting replan history"""
        executor = MagicMock()
        loop = SelfRefinementLoop(executor=executor)
        loop._replan_history = [{"type": "partial", "failed_task_id": "task-1"}]

        history = loop.get_replan_history()

        assert len(history) == 1
        assert history[0]["type"] == "partial"

    def test_get_replan_counts(self):
        """Test getting replan counts from replanner"""
        executor = MagicMock()
        loop = SelfRefinementLoop(executor=executor, max_task_replans=5, max_full_replans=3)

        counts = loop.get_replan_counts()

        assert counts["max_task_replans"] == 5
        assert counts["max_full_replans"] == 3


class TestRefinementResult:
    """Tests for RefinementResult class"""

    def test_to_dict(self):
        """Test serialization to dictionary"""
        from core.planner.consumer import ExecutionResult

        execution_result = ExecutionResult(
            plan_id="test-plan",
            status=ExecutionStatus.COMPLETED,
            task_results=[],
        )

        result = RefinementResult(
            execution_result=execution_result,
            replan_history=[{"type": "partial"}],
            escalated_to_hitl=False,
        )

        data = result.to_dict()

        assert data["execution_result"]["plan_id"] == "test-plan"
        assert data["total_replans"] == 1
        assert data["escalated_to_hitl"] is False
