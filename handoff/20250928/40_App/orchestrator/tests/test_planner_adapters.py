"""
Unit tests for Planner Adapters (Phase F-1)

Tests the adapter functions that convert output from existing planners
(LLMPlannerAdapter, TaskPlanner, PMAgent) to the unified PlannerOutput format.
"""

import pytest
from unittest.mock import MagicMock

from core.planner.adapters import (
    adapt_llm_planner_output,
    adapt_task_planner_output,
    adapt_pm_agent_output,
    _infer_task_type_from_description,
    _determine_flow_template,
)
from core.planner.planner_types import (
    PlannerOutput,
    PlanType,
    TaskType,
    EdgeType,
    RiskLevel,
)


class TestAdaptLLMPlannerOutput:
    """Tests for adapt_llm_planner_output function"""

    def test_basic_conversion(self):
        """Test basic LLM planner output conversion"""
        llm_result = {
            "plan": ["Analyze the codebase", "Implement the feature", "Write tests"],
            "plan_details": [
                {"step": "Analyze the codebase", "estimated_minutes": 10},
                {"step": "Implement the feature", "estimated_minutes": 30},
                {"step": "Write tests", "estimated_minutes": 15},
            ],
            "planner_type": "llm",
            "task_type": "feature",
            "planning_time_ms": 1500.0,
            "provider": "openai",
        }

        result = adapt_llm_planner_output(llm_result, goal="Add new feature")

        assert isinstance(result, PlannerOutput)
        assert result.plan_type == PlanType.DETAILED
        assert result.goal == "Add new feature"
        assert len(result.task_tree.nodes) == 3
        assert result.planner_metadata.planner_type == "llm"
        assert result.planner_metadata.planning_time_ms == 1500.0
        assert result.planner_metadata.provider == "openai"

    def test_sequential_dependencies(self):
        """Test that sequential dependencies are created correctly"""
        llm_result = {
            "plan": ["Step 1", "Step 2", "Step 3"],
            "plan_details": [],
            "planner_type": "llm",
            "task_type": "unknown",
            "planning_time_ms": 100.0,
        }

        result = adapt_llm_planner_output(llm_result)

        # Should have 2 edges: task-1 -> task-2, task-2 -> task-3
        assert len(result.task_tree.edges) == 2
        assert result.task_tree.edges[0].from_task == "task-1"
        assert result.task_tree.edges[0].to_task == "task-2"
        assert result.task_tree.edges[1].from_task == "task-2"
        assert result.task_tree.edges[1].to_task == "task-3"

    def test_empty_plan(self):
        """Test handling of empty plan"""
        llm_result = {
            "plan": [],
            "plan_details": [],
            "planner_type": "llm",
            "task_type": "unknown",
            "planning_time_ms": 0.0,
        }

        result = adapt_llm_planner_output(llm_result)

        assert len(result.task_tree.nodes) == 0
        assert len(result.task_tree.edges) == 0

    def test_flow_template_selection(self):
        """Test flow template is selected based on task type"""
        llm_result = {
            "plan": ["Write documentation"],
            "plan_details": [],
            "planner_type": "llm",
            "task_type": "documentation",
            "planning_time_ms": 100.0,
        }

        result = adapt_llm_planner_output(llm_result)

        assert result.flow_template == "doc_only"


class TestAdaptTaskPlannerOutput:
    """Tests for adapt_task_planner_output function"""

    def test_basic_conversion(self):
        """Test basic TaskPlanner output conversion"""
        # Create mock SubTask and TaskPlan
        mock_subtask_type = MagicMock()
        mock_subtask_type.value = "write_code"

        mock_subtask = MagicMock()
        mock_subtask.task_id = "task-1"
        mock_subtask.task_type = mock_subtask_type
        mock_subtask.description = "Implement the feature"
        mock_subtask.estimated_duration_minutes = 30
        mock_subtask.inputs = {}
        mock_subtask.outputs = {}
        mock_subtask.requires_approval = False
        mock_subtask.agent_type = "dev_agent"
        mock_subtask.priority = 0
        mock_subtask.dependencies = []

        mock_goal = MagicMock()
        mock_goal.summary = "Add new feature"
        mock_goal.goal_type = MagicMock()
        mock_goal.goal_type.value = "feature_development"

        mock_task_plan = MagicMock()
        mock_task_plan.plan_id = "plan-123"
        mock_task_plan.subtasks = [mock_subtask]
        mock_task_plan.total_estimated_minutes = 30
        mock_task_plan.goal = mock_goal
        mock_task_plan.metadata = {"planner_version": "1.1.0"}

        result = adapt_task_planner_output(mock_task_plan)

        assert isinstance(result, PlannerOutput)
        assert result.plan_id == "plan-123"
        assert result.goal == "Add new feature"
        assert len(result.task_tree.nodes) == 1
        assert result.task_tree.nodes[0].task_type == TaskType.CODE
        assert result.planner_metadata.planner_type == "task_planner"

    def test_dependency_conversion(self):
        """Test that dependencies are converted to edges"""
        mock_subtask_type = MagicMock()
        mock_subtask_type.value = "write_code"

        mock_subtask1 = MagicMock()
        mock_subtask1.task_id = "task-1"
        mock_subtask1.task_type = mock_subtask_type
        mock_subtask1.description = "Step 1"
        mock_subtask1.estimated_duration_minutes = 10
        mock_subtask1.inputs = {}
        mock_subtask1.outputs = {}
        mock_subtask1.requires_approval = False
        mock_subtask1.agent_type = "dev_agent"
        mock_subtask1.priority = 0
        mock_subtask1.dependencies = []

        mock_subtask2 = MagicMock()
        mock_subtask2.task_id = "task-2"
        mock_subtask2.task_type = mock_subtask_type
        mock_subtask2.description = "Step 2"
        mock_subtask2.estimated_duration_minutes = 20
        mock_subtask2.inputs = {}
        mock_subtask2.outputs = {}
        mock_subtask2.requires_approval = False
        mock_subtask2.agent_type = "dev_agent"
        mock_subtask2.priority = 0
        mock_subtask2.dependencies = ["task-1"]

        mock_goal = MagicMock()
        mock_goal.summary = "Test goal"
        mock_goal.goal_type = MagicMock()
        mock_goal.goal_type.value = "feature"

        mock_task_plan = MagicMock()
        mock_task_plan.plan_id = "plan-456"
        mock_task_plan.subtasks = [mock_subtask1, mock_subtask2]
        mock_task_plan.total_estimated_minutes = 30
        mock_task_plan.goal = mock_goal
        mock_task_plan.metadata = {}

        result = adapt_task_planner_output(mock_task_plan)

        assert len(result.task_tree.edges) == 1
        assert result.task_tree.edges[0].from_task == "task-1"
        assert result.task_tree.edges[0].to_task == "task-2"
        assert result.task_tree.edges[0].edge_type == EdgeType.DEPENDS_ON


class TestAdaptPMAgentOutput:
    """Tests for adapt_pm_agent_output function"""

    def test_basic_conversion(self):
        """Test basic PMAgent output conversion"""
        mock_subtask = MagicMock()
        mock_subtask.task_id = "pm-task-1"
        mock_subtask.task_type = "feature"
        mock_subtask.description = "Implement feature"
        mock_subtask.title = "Feature Implementation"
        mock_subtask.estimated_effort = "medium"
        mock_subtask.affected_files = ["src/main.py"]
        mock_subtask.priority = 1
        mock_subtask.dependencies = []

        mock_risk = MagicMock()
        mock_risk.value = "medium"

        mock_finding = MagicMock()
        mock_finding.title = "Complexity risk"

        mock_advisory = MagicMock()
        mock_advisory.goal = "Add new feature"
        mock_advisory.sub_tasks = [mock_subtask]
        mock_advisory.overall_risk = mock_risk
        mock_advisory.confidence_score = 0.85
        mock_advisory.findings = [mock_finding]
        mock_advisory.recommendations = ["Consider breaking into smaller tasks"]
        mock_advisory.metadata = {"latency_ms": 500.0}

        result = adapt_pm_agent_output(mock_advisory)

        assert isinstance(result, PlannerOutput)
        assert result.goal == "Add new feature"
        assert len(result.task_tree.nodes) == 1
        assert result.task_tree.nodes[0].task_type == TaskType.CODE
        assert result.task_tree.nodes[0].estimated_duration_minutes == 30  # medium effort
        assert result.risk_metadata.overall_risk == RiskLevel.MEDIUM
        assert result.planner_metadata.planner_type == "pm_agent"
        assert result.planner_metadata.confidence_score == 0.85

    def test_effort_to_duration_mapping(self):
        """Test effort levels are mapped to correct durations"""
        for effort, expected_minutes in [("small", 15), ("medium", 30), ("large", 60)]:
            mock_subtask = MagicMock()
            mock_subtask.task_id = "task-1"
            mock_subtask.task_type = "feature"
            mock_subtask.description = "Task"
            mock_subtask.title = "Task"
            mock_subtask.estimated_effort = effort
            mock_subtask.affected_files = []
            mock_subtask.priority = 0
            mock_subtask.dependencies = []

            mock_risk = MagicMock()
            mock_risk.value = "low"

            mock_advisory = MagicMock()
            mock_advisory.goal = "Test"
            mock_advisory.sub_tasks = [mock_subtask]
            mock_advisory.overall_risk = mock_risk
            mock_advisory.confidence_score = 0.9
            mock_advisory.findings = []
            mock_advisory.recommendations = []
            mock_advisory.metadata = {}

            result = adapt_pm_agent_output(mock_advisory)

            assert result.task_tree.nodes[0].estimated_duration_minutes == expected_minutes


class TestInferTaskTypeFromDescription:
    """Tests for _infer_task_type_from_description helper"""

    @pytest.mark.parametrize("description,expected_type", [
        ("Setup the development environment", TaskType.SETUP),
        ("Install dependencies", TaskType.SETUP),
        ("Configure the project", TaskType.SETUP),
        ("Analyze the codebase", TaskType.ANALYZE),
        ("Investigate the bug", TaskType.ANALYZE),
        ("Write unit tests", TaskType.TEST),
        ("Run integration tests", TaskType.TEST),
        ("Code review the changes", TaskType.REVIEW),
        ("Self-review the implementation", TaskType.REVIEW),
        ("Document the API", TaskType.DOCUMENT),
        ("Update the README", TaskType.DOCUMENT),
        ("Deploy to production", TaskType.DEPLOY),
        ("Release the new version", TaskType.DEPLOY),
        ("Verify the fix works", TaskType.VERIFY),
        ("Validate the implementation", TaskType.VERIFY),
        ("Cleanup temporary files", TaskType.CLEANUP),
        ("Implement the feature", TaskType.CODE),
        ("Fix the bug", TaskType.CODE),
        ("Create new component", TaskType.CODE),
        ("Unknown task description", TaskType.CODE),  # Default
    ])
    def test_task_type_inference(self, description, expected_type):
        """Test task type is correctly inferred from description"""
        result = _infer_task_type_from_description(description)
        assert result == expected_type


class TestDetermineFlowTemplate:
    """Tests for _determine_flow_template helper"""

    @pytest.mark.parametrize("task_type,expected_template", [
        ("documentation", "doc_only"),
        ("doc", "doc_only"),
        ("test", "test_heavy"),
        ("testing", "test_heavy"),
        ("bug_fix", "review_heavy"),
        ("bugfix", "review_heavy"),
        ("refactor", "review_heavy"),
        ("refactoring", "review_heavy"),
        ("feature", "full_pipeline"),
        ("feature_development", "full_pipeline"),
        ("investigation", "analysis_only"),
        ("unknown", "full_pipeline"),  # Default
    ])
    def test_flow_template_selection(self, task_type, expected_template):
        """Test flow template is correctly selected based on task type"""
        result = _determine_flow_template(task_type)
        assert result == expected_template
