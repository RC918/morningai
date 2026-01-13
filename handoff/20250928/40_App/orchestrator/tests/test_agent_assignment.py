"""
Unit tests for F-4 Agent Assignment + Flow Template Selection

Tests for AgentAssigner and FlowTemplateSelector classes.
"""

from unittest.mock import patch

from core.planner.agent_assignment import (
    AgentAssigner,
    AssignmentContext,
    FlowTemplateSelector,
    SelectionContext,
    assign_and_select,
)
from core.planner.planner_types import (
    PlannerOutput,
    RiskLevel,
    RiskMetadata,
    TaskNode,
    TaskTree,
    TaskType,
)


class TestAssignmentContext:
    """Tests for AssignmentContext dataclass"""

    def test_default_values(self):
        """Test default context values"""
        context = AssignmentContext()
        assert context.trust_score is None
        assert "dev_agent" in context.available_agents
        assert "senior_coder" in context.available_agents
        assert context.is_retry is False
        assert context.previous_agent is None

    def test_custom_values(self):
        """Test custom context values"""
        context = AssignmentContext(
            trust_score=0.8,
            available_agents=["dev_agent", "reviewer_agent"],
            is_retry=True,
            previous_agent="dev_agent",
        )
        assert context.trust_score == 0.8
        assert context.available_agents == ["dev_agent", "reviewer_agent"]
        assert context.is_retry is True
        assert context.previous_agent == "dev_agent"


class TestSelectionContext:
    """Tests for SelectionContext dataclass"""

    def test_default_values(self):
        """Test default context values"""
        context = SelectionContext()
        assert context.is_hotfix is False
        assert context.time_constraint_minutes is None
        assert context.user_preference is None
        assert context.trust_score is None

    def test_custom_values(self):
        """Test custom context values"""
        context = SelectionContext(
            is_hotfix=True,
            time_constraint_minutes=30,
            user_preference="review_heavy",
            trust_score=0.7,
        )
        assert context.is_hotfix is True
        assert context.time_constraint_minutes == 30
        assert context.user_preference == "review_heavy"
        assert context.trust_score == 0.7


class TestAgentAssigner:
    """Tests for AgentAssigner class"""

    def _create_task(
        self,
        task_type: TaskType = TaskType.CODE,
        risk_level: RiskLevel = RiskLevel.LOW,
        task_id: str = "task-1",
    ) -> TaskNode:
        """Helper to create a test task"""
        return TaskNode(
            task_id=task_id,
            task_type=task_type,
            description="Test task",
            risk_level=risk_level,
        )

    def test_assign_code_task(self):
        """Test assignment for code task"""
        assigner = AgentAssigner()
        task = self._create_task(TaskType.CODE)
        agent = assigner.assign(task)
        assert agent == "dev_agent"

    def test_assign_review_task(self):
        """Test assignment for review task"""
        assigner = AgentAssigner()
        task = self._create_task(TaskType.REVIEW)
        agent = assigner.assign(task)
        assert agent == "reviewer_agent"

    def test_assign_test_task(self):
        """Test assignment for test task"""
        assigner = AgentAssigner()
        task = self._create_task(TaskType.TEST)
        agent = assigner.assign(task)
        assert agent == "tester_agent"

    def test_assign_deploy_task(self):
        """Test assignment for deploy task"""
        assigner = AgentAssigner()
        task = self._create_task(TaskType.DEPLOY)
        agent = assigner.assign(task)
        assert agent == "ops_agent"

    def test_assign_document_task(self):
        """Test assignment for document task"""
        assigner = AgentAssigner()
        task = self._create_task(TaskType.DOCUMENT)
        agent = assigner.assign(task)
        assert agent == "doc_agent"

    def test_upgrade_to_senior_for_critical_risk(self):
        """Test upgrade to senior agent for critical risk"""
        assigner = AgentAssigner()
        task = self._create_task(TaskType.CODE, RiskLevel.CRITICAL)
        agent = assigner.assign(task)
        assert agent == "senior_coder"

    def test_upgrade_to_senior_for_high_risk_code(self):
        """Test upgrade to senior agent for high risk code task"""
        assigner = AgentAssigner()
        task = self._create_task(TaskType.CODE, RiskLevel.HIGH)
        agent = assigner.assign(task)
        assert agent == "senior_coder"

    def test_upgrade_to_senior_for_high_risk_deploy(self):
        """Test upgrade to senior agent for high risk deploy task"""
        assigner = AgentAssigner()
        task = self._create_task(TaskType.DEPLOY, RiskLevel.HIGH)
        context = AssignmentContext(
            available_agents=["dev_agent", "ops_agent", "senior_coder"]
        )
        agent = assigner.assign(task, context)
        assert agent == "ops_agent"

    def test_no_upgrade_for_high_risk_review(self):
        """Test no upgrade for high risk review task (not in HIGH_RISK_TASK_TYPES)"""
        assigner = AgentAssigner()
        task = self._create_task(TaskType.REVIEW, RiskLevel.HIGH)
        agent = assigner.assign(task)
        assert agent == "reviewer_agent"

    def test_upgrade_for_low_trust_score(self):
        """Test upgrade to senior for low trust score"""
        assigner = AgentAssigner()
        task = self._create_task(TaskType.CODE, RiskLevel.LOW)
        context = AssignmentContext(trust_score=0.3)
        agent = assigner.assign(task, context)
        assert agent == "senior_coder"

    def test_no_upgrade_for_high_trust_score(self):
        """Test no upgrade for high trust score"""
        assigner = AgentAssigner()
        task = self._create_task(TaskType.CODE, RiskLevel.LOW)
        context = AssignmentContext(trust_score=0.8)
        agent = assigner.assign(task, context)
        assert agent == "dev_agent"

    def test_upgrade_on_retry_with_same_agent(self):
        """Test upgrade to senior on retry with same agent"""
        assigner = AgentAssigner()
        task = self._create_task(TaskType.CODE, RiskLevel.LOW)
        context = AssignmentContext(is_retry=True, previous_agent="dev_agent")
        agent = assigner.assign(task, context)
        assert agent == "senior_coder"

    def test_no_upgrade_on_retry_with_different_agent(self):
        """Test no upgrade on retry with different agent"""
        assigner = AgentAssigner()
        task = self._create_task(TaskType.CODE, RiskLevel.LOW)
        context = AssignmentContext(is_retry=True, previous_agent="reviewer_agent")
        agent = assigner.assign(task, context)
        assert agent == "dev_agent"

    def test_fallback_when_agent_unavailable(self):
        """Test fallback to dev_agent when assigned agent unavailable"""
        assigner = AgentAssigner()
        task = self._create_task(TaskType.DEPLOY, RiskLevel.LOW)
        context = AssignmentContext(available_agents=["dev_agent"])
        agent = assigner.assign(task, context)
        assert agent == "dev_agent"

    def test_assign_all(self):
        """Test assigning agents to all tasks in a plan"""
        assigner = AgentAssigner()
        plan = PlannerOutput(
            goal="Test goal",
            task_tree=TaskTree(
                nodes=[
                    self._create_task(TaskType.CODE, task_id="task-1"),
                    self._create_task(TaskType.REVIEW, task_id="task-2"),
                    self._create_task(TaskType.TEST, task_id="task-3"),
                ]
            ),
        )
        assignments = assigner.assign_all(plan)
        assert assignments["task-1"] == "dev_agent"
        assert assignments["task-2"] == "reviewer_agent"
        assert assignments["task-3"] == "tester_agent"

    @patch("core.planner.agent_assignment._use_agent_assignment", return_value=True)
    def test_apply_assignments_enabled(self, mock_use):
        """Test applying assignments when feature is enabled"""
        assigner = AgentAssigner()
        plan = PlannerOutput(
            goal="Test goal",
            task_tree=TaskTree(
                nodes=[
                    self._create_task(TaskType.CODE, task_id="task-1"),
                    self._create_task(TaskType.REVIEW, task_id="task-2"),
                ]
            ),
        )
        result = assigner.apply_assignments(plan)
        assert result.task_tree.nodes[0].agent_assignment == "dev_agent"
        assert result.task_tree.nodes[1].agent_assignment == "reviewer_agent"

    @patch("core.planner.agent_assignment._use_agent_assignment", return_value=False)
    def test_apply_assignments_disabled(self, mock_use):
        """Test skipping assignments when feature is disabled"""
        assigner = AgentAssigner()
        plan = PlannerOutput(
            goal="Test goal",
            task_tree=TaskTree(
                nodes=[
                    TaskNode(
                        task_id="task-1",
                        task_type=TaskType.CODE,
                        description="Test",
                        agent_assignment="original_agent",
                    ),
                ]
            ),
        )
        result = assigner.apply_assignments(plan)
        assert result.task_tree.nodes[0].agent_assignment == "original_agent"


class TestFlowTemplateSelector:
    """Tests for FlowTemplateSelector class"""

    def _create_plan(
        self,
        task_types: list = None,
        risk_level: RiskLevel = RiskLevel.LOW,
    ) -> PlannerOutput:
        """Helper to create a test plan"""
        if task_types is None:
            task_types = [TaskType.CODE]

        nodes = [
            TaskNode(
                task_id=f"task-{i}",
                task_type=tt,
                description=f"Task {i}",
            )
            for i, tt in enumerate(task_types)
        ]

        return PlannerOutput(
            goal="Test goal",
            task_tree=TaskTree(nodes=nodes),
            risk_metadata=RiskMetadata(overall_risk=risk_level),
        )

    def test_select_full_pipeline_default(self):
        """Test default selection is full_pipeline"""
        selector = FlowTemplateSelector()
        plan = self._create_plan([TaskType.CODE, TaskType.TEST, TaskType.REVIEW])
        template = selector.select(plan)
        assert template == "full_pipeline"

    def test_select_user_preference(self):
        """Test user preference overrides default"""
        selector = FlowTemplateSelector()
        plan = self._create_plan()
        context = SelectionContext(user_preference="test_heavy")
        template = selector.select(plan, context)
        assert template == "test_heavy"

    def test_select_hotfix_mode(self):
        """Test hotfix mode selects code_only"""
        selector = FlowTemplateSelector()
        plan = self._create_plan()
        context = SelectionContext(is_hotfix=True)
        template = selector.select(plan, context)
        assert template == "code_only"

    def test_select_review_heavy_for_high_risk(self):
        """Test high risk selects review_heavy"""
        selector = FlowTemplateSelector()
        plan = self._create_plan(risk_level=RiskLevel.HIGH)
        template = selector.select(plan)
        assert template == "review_heavy"

    def test_select_review_heavy_for_critical_risk(self):
        """Test critical risk selects review_heavy"""
        selector = FlowTemplateSelector()
        plan = self._create_plan(risk_level=RiskLevel.CRITICAL)
        template = selector.select(plan)
        assert template == "review_heavy"

    def test_select_review_heavy_for_low_trust(self):
        """Test low trust score selects review_heavy"""
        selector = FlowTemplateSelector()
        plan = self._create_plan()
        context = SelectionContext(trust_score=0.3)
        template = selector.select(plan, context)
        assert template == "review_heavy"

    def test_select_code_only_for_tight_time(self):
        """Test tight time constraint selects code_only"""
        selector = FlowTemplateSelector()
        plan = self._create_plan()
        context = SelectionContext(time_constraint_minutes=20)
        template = selector.select(plan, context)
        assert template == "code_only"

    def test_infer_doc_only(self):
        """Test inference of doc_only template"""
        selector = FlowTemplateSelector()
        plan = self._create_plan([TaskType.DOCUMENT])
        template = selector.select(plan)
        assert template == "doc_only"

    def test_infer_analysis_only(self):
        """Test inference of analysis_only template"""
        selector = FlowTemplateSelector()
        plan = self._create_plan([TaskType.ANALYZE])
        template = selector.select(plan)
        assert template == "analysis_only"

    def test_infer_code_only(self):
        """Test inference of code_only template"""
        selector = FlowTemplateSelector()
        plan = self._create_plan([TaskType.CODE])
        template = selector.select(plan)
        assert template == "code_only"

    def test_infer_test_heavy(self):
        """Test inference of test_heavy template"""
        selector = FlowTemplateSelector()
        plan = self._create_plan([TaskType.CODE, TaskType.TEST])
        template = selector.select(plan)
        assert template == "test_heavy"

    def test_apply_template(self):
        """Test applying template to plan"""
        selector = FlowTemplateSelector()
        plan = self._create_plan([TaskType.DOCUMENT])
        result = selector.apply_template(plan)
        assert result.flow_template == "doc_only"


class TestAssignAndSelect:
    """Tests for assign_and_select convenience function"""

    def _create_plan(self) -> PlannerOutput:
        """Helper to create a test plan"""
        return PlannerOutput(
            goal="Test goal",
            task_tree=TaskTree(
                nodes=[
                    TaskNode(
                        task_id="task-1",
                        task_type=TaskType.CODE,
                        description="Code task",
                        risk_level=RiskLevel.HIGH,
                    ),
                    TaskNode(
                        task_id="task-2",
                        task_type=TaskType.REVIEW,
                        description="Review task",
                    ),
                ]
            ),
            risk_metadata=RiskMetadata(overall_risk=RiskLevel.HIGH),
        )

    @patch("core.planner.agent_assignment._use_agent_assignment", return_value=True)
    def test_assign_and_select(self, mock_use):
        """Test combined assignment and selection"""
        plan = self._create_plan()
        result = assign_and_select(plan)

        assert result.task_tree.nodes[0].agent_assignment == "senior_coder"
        assert result.task_tree.nodes[1].agent_assignment == "reviewer_agent"
        assert result.flow_template == "review_heavy"

    @patch("core.planner.agent_assignment._use_agent_assignment", return_value=True)
    def test_assign_and_select_with_contexts(self, mock_use):
        """Test combined assignment and selection with custom contexts"""
        plan = self._create_plan()
        assignment_context = AssignmentContext(trust_score=0.9)
        selection_context = SelectionContext(user_preference="full_pipeline")

        result = assign_and_select(plan, assignment_context, selection_context)

        assert result.task_tree.nodes[0].agent_assignment == "senior_coder"
        assert result.flow_template == "full_pipeline"
