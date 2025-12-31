"""
Tests for SeniorCoder Agent - D-2 Reasoning-First Architecture

Issue #2761: D-2 Senior Coder Logic (Tier 1)
Parent EPIC #2759: EPIC D - Autonomous Coder Agent Family
"""
import json
from unittest.mock import patch

from coder.senior_coder import (
    SeniorCoder,
    ArchitectureSpec,
    TaskAnalysis,
    TaskComplexity,
    ArchitecturePlan,
    ImplementationStep,
    FileAction,
    ReviewResult,
    get_senior_coder,
    ARCHITECTURE_SPEC_SCHEMA_VERSION,
    REVIEW_RESULT_SCHEMA_VERSION,
    MAX_FILES_IN_PLAN,
)
from core.agents import AgentInput


class TestTaskAnalysis:
    """Tests for TaskAnalysis dataclass."""

    def test_to_dict(self):
        """Test TaskAnalysis serialization."""
        analysis = TaskAnalysis(
            complexity=TaskComplexity.SIMPLE,
            reasoning="Simple variable rename"
        )
        result = analysis.to_dict()
        assert result["complexity"] == "simple"
        assert result["reasoning"] == "Simple variable rename"

    def test_complexity_values(self):
        """Test all complexity enum values."""
        assert TaskComplexity.SIMPLE.value == "simple"
        assert TaskComplexity.MODERATE.value == "moderate"
        assert TaskComplexity.COMPLEX.value == "complex"


class TestArchitecturePlan:
    """Tests for ArchitecturePlan dataclass."""

    def test_to_dict_empty(self):
        """Test empty ArchitecturePlan serialization."""
        plan = ArchitecturePlan()
        result = plan.to_dict()
        assert result["files_to_modify"] == []
        assert result["files_to_create"] == []
        assert result["dependencies"] == {}

    def test_to_dict_with_data(self):
        """Test ArchitecturePlan serialization with data."""
        plan = ArchitecturePlan(
            files_to_modify=["src/utils.py"],
            files_to_create=["src/helpers.py"],
            dependencies={"src/utils.py": ["src/helpers.py"]}
        )
        result = plan.to_dict()
        assert result["files_to_modify"] == ["src/utils.py"]
        assert result["files_to_create"] == ["src/helpers.py"]
        assert result["dependencies"] == {"src/utils.py": ["src/helpers.py"]}


class TestImplementationStep:
    """Tests for ImplementationStep dataclass."""

    def test_to_dict(self):
        """Test ImplementationStep serialization."""
        step = ImplementationStep(
            file_path="src/utils.py",
            action=FileAction.MODIFY,
            description="Add helper function",
            function_signatures=["def helper(x: int) -> str"],
            test_cases=["test helper returns string"]
        )
        result = step.to_dict()
        assert result["file_path"] == "src/utils.py"
        assert result["action"] == "modify"
        assert result["description"] == "Add helper function"
        assert result["function_signatures"] == ["def helper(x: int) -> str"]
        assert result["test_cases"] == ["test helper returns string"]

    def test_file_action_values(self):
        """Test FileAction enum values."""
        assert FileAction.MODIFY.value == "modify"
        assert FileAction.CREATE.value == "create"


class TestArchitectureSpec:
    """Tests for ArchitectureSpec dataclass."""

    def test_to_dict_simple(self):
        """Test simple ArchitectureSpec serialization."""
        spec = ArchitectureSpec(
            task_analysis=TaskAnalysis(
                complexity=TaskComplexity.SIMPLE,
                reasoning="Simple task"
            )
        )
        result = spec.to_dict()
        assert result["schema_version"] == ARCHITECTURE_SPEC_SCHEMA_VERSION
        assert result["task_analysis"]["complexity"] == "simple"
        assert "abort_reason" not in result

    def test_to_dict_with_abort(self):
        """Test ArchitectureSpec with abort reason."""
        spec = ArchitectureSpec.create_abort(
            reason="Task too complex",
            reasoning="Requires architectural changes"
        )
        result = spec.to_dict()
        assert result["task_analysis"]["complexity"] == "complex"
        assert result["abort_reason"] == "Task too complex"

    def test_to_json(self):
        """Test JSON serialization."""
        spec = ArchitectureSpec(
            task_analysis=TaskAnalysis(
                complexity=TaskComplexity.MODERATE,
                reasoning="Moderate task"
            )
        )
        json_str = spec.to_json()
        data = json.loads(json_str)
        assert data["schema_version"] == ARCHITECTURE_SPEC_SCHEMA_VERSION

    def test_should_proceed_simple(self):
        """Test should_proceed for simple task."""
        spec = ArchitectureSpec(
            task_analysis=TaskAnalysis(
                complexity=TaskComplexity.SIMPLE,
                reasoning="Simple task"
            )
        )
        assert spec.should_proceed is True

    def test_should_proceed_moderate(self):
        """Test should_proceed for moderate task."""
        spec = ArchitectureSpec(
            task_analysis=TaskAnalysis(
                complexity=TaskComplexity.MODERATE,
                reasoning="Moderate task"
            )
        )
        assert spec.should_proceed is True

    def test_should_proceed_complex(self):
        """Test should_proceed for complex task."""
        spec = ArchitectureSpec(
            task_analysis=TaskAnalysis(
                complexity=TaskComplexity.COMPLEX,
                reasoning="Complex task"
            )
        )
        assert spec.should_proceed is False

    def test_should_proceed_with_abort(self):
        """Test should_proceed with abort reason."""
        spec = ArchitectureSpec(
            task_analysis=TaskAnalysis(
                complexity=TaskComplexity.SIMPLE,
                reasoning="Simple task"
            ),
            abort_reason="Manual abort"
        )
        assert spec.should_proceed is False

    def test_create_abort(self):
        """Test create_abort factory method."""
        spec = ArchitectureSpec.create_abort(
            reason="Too complex",
            reasoning="Requires new architecture"
        )
        assert spec.task_analysis.complexity == TaskComplexity.COMPLEX
        assert spec.abort_reason == "Too complex"
        assert spec.should_proceed is False


class TestReviewResult:
    """Tests for ReviewResult dataclass."""

    def test_to_dict_approved(self):
        """Test approved ReviewResult serialization."""
        result = ReviewResult(
            approved=True,
            feedback="Implementation looks good"
        )
        data = result.to_dict()
        assert data["schema_version"] == REVIEW_RESULT_SCHEMA_VERSION
        assert data["approved"] is True
        assert data["feedback"] == "Implementation looks good"
        assert "required_changes" not in data

    def test_to_dict_rejected(self):
        """Test rejected ReviewResult serialization."""
        result = ReviewResult(
            approved=False,
            feedback="Needs improvements",
            required_changes=["Fix error handling", "Add tests"]
        )
        data = result.to_dict()
        assert data["approved"] is False
        assert data["required_changes"] == ["Fix error handling", "Add tests"]

    def test_to_json(self):
        """Test JSON serialization."""
        result = ReviewResult(approved=True, feedback="OK")
        json_str = result.to_json()
        data = json.loads(json_str)
        assert data["approved"] is True


class TestSeniorCoder:
    """Tests for SeniorCoder agent."""

    def test_init(self):
        """Test SeniorCoder initialization."""
        coder = SeniorCoder()
        assert coder.agent_id == "senior_coder"

    @patch.object(SeniorCoder, "call_llm")
    def test_analyze_and_plan_simple(self, mock_llm):
        """Test analyze_and_plan for simple task."""
        mock_llm.return_value = {
            "content": json.dumps({
                "task_analysis": {
                    "complexity": "simple",
                    "reasoning": "Simple variable rename"
                },
                "architecture": {
                    "files_to_modify": ["src/utils.py"],
                    "files_to_create": [],
                    "dependencies": {}
                },
                "implementation_plan": [
                    {
                        "file_path": "src/utils.py",
                        "action": "modify",
                        "description": "Rename variable",
                        "function_signatures": [],
                        "test_cases": []
                    }
                ],
                "constraints": ["Keep backward compatibility"]
            })
        }

        coder = SeniorCoder()
        spec = coder.analyze_and_plan(
            task_description="Rename variable foo to bar",
            files=[{"path": "src/utils.py", "content": "foo = 1"}]
        )

        assert spec.task_analysis.complexity == TaskComplexity.SIMPLE
        assert spec.should_proceed is True
        assert len(spec.implementation_plan) == 1
        assert spec.implementation_plan[0].file_path == "src/utils.py"

    @patch.object(SeniorCoder, "call_llm")
    def test_analyze_and_plan_complex(self, mock_llm):
        """Test analyze_and_plan for complex task."""
        mock_llm.return_value = {
            "content": json.dumps({
                "task_analysis": {
                    "complexity": "complex",
                    "reasoning": "Requires new authentication system"
                },
                "architecture": {},
                "implementation_plan": [],
                "constraints": [],
                "abort_reason": "Task requires architectural changes"
            })
        }

        coder = SeniorCoder()
        spec = coder.analyze_and_plan(
            task_description="Add OAuth2 authentication",
            files=[]
        )

        assert spec.task_analysis.complexity == TaskComplexity.COMPLEX
        assert spec.should_proceed is False
        assert spec.abort_reason == "Task requires architectural changes"

    @patch.object(SeniorCoder, "call_llm")
    def test_analyze_and_plan_too_many_files(self, mock_llm):
        """Test analyze_and_plan rejects too many files."""
        mock_llm.return_value = {
            "content": json.dumps({
                "task_analysis": {
                    "complexity": "moderate",
                    "reasoning": "Multiple files"
                },
                "architecture": {
                    "files_to_modify": ["f1.py", "f2.py", "f3.py"],
                    "files_to_create": ["f4.py", "f5.py", "f6.py"],
                    "dependencies": {}
                },
                "implementation_plan": [],
                "constraints": []
            })
        }

        coder = SeniorCoder()
        spec = coder.analyze_and_plan(
            task_description="Large refactor",
            files=[]
        )

        assert spec.should_proceed is False
        assert "too many files" in spec.abort_reason.lower()

    @patch.object(SeniorCoder, "call_llm")
    def test_analyze_and_plan_llm_error(self, mock_llm):
        """Test analyze_and_plan handles LLM errors."""
        mock_llm.side_effect = Exception("LLM unavailable")

        coder = SeniorCoder()
        spec = coder.analyze_and_plan(
            task_description="Some task",
            files=[]
        )

        assert spec.should_proceed is False
        assert "failed" in spec.abort_reason.lower()

    @patch.object(SeniorCoder, "call_llm")
    def test_analyze_and_plan_invalid_json(self, mock_llm):
        """Test analyze_and_plan handles invalid JSON."""
        mock_llm.return_value = {"content": "not valid json"}

        coder = SeniorCoder()
        spec = coder.analyze_and_plan(
            task_description="Some task",
            files=[]
        )

        assert spec.should_proceed is False
        assert "parse" in spec.abort_reason.lower()

    @patch.object(SeniorCoder, "call_llm")
    def test_review_implementation_approved(self, mock_llm):
        """Test review_implementation approves good implementation."""
        mock_llm.return_value = {
            "content": json.dumps({
                "approved": True,
                "feedback": "Implementation matches spec"
            })
        }

        coder = SeniorCoder()
        result = coder.review_implementation(
            task_description="Add docstring",
            spec_dict={"task_analysis": {"complexity": "simple"}},
            implementation={"status": "patch", "patch": "..."}
        )

        assert result.approved is True
        assert "matches" in result.feedback.lower()

    @patch.object(SeniorCoder, "call_llm")
    def test_review_implementation_rejected(self, mock_llm):
        """Test review_implementation rejects bad implementation."""
        mock_llm.return_value = {
            "content": json.dumps({
                "approved": False,
                "feedback": "Missing error handling",
                "required_changes": ["Add try/except block"]
            })
        }

        coder = SeniorCoder()
        result = coder.review_implementation(
            task_description="Add error handling",
            spec_dict={},
            implementation={}
        )

        assert result.approved is False
        assert len(result.required_changes) == 1

    @patch.object(SeniorCoder, "call_llm")
    def test_review_implementation_llm_error(self, mock_llm):
        """Test review_implementation handles LLM errors."""
        mock_llm.side_effect = Exception("LLM unavailable")

        coder = SeniorCoder()
        result = coder.review_implementation(
            task_description="Some task",
            spec_dict={},
            implementation={}
        )

        assert result.approved is False
        assert "failed" in result.feedback.lower()

    @patch.object(SeniorCoder, "call_llm")
    def test_execute_plan_mode(self, mock_llm):
        """Test execute in plan mode."""
        mock_llm.return_value = {
            "content": json.dumps({
                "task_analysis": {
                    "complexity": "simple",
                    "reasoning": "Simple task"
                },
                "architecture": {},
                "implementation_plan": [],
                "constraints": []
            })
        }

        coder = SeniorCoder()
        input_data = AgentInput(
            task_id="test-123",
            prompt="Add docstring",
            context={"mode": "plan", "files": []}
        )
        output = coder.execute(input_data)

        assert output.task_id == "test-123"
        assert output.success is True
        assert output.data["task_analysis"]["complexity"] == "simple"

    @patch.object(SeniorCoder, "call_llm")
    def test_execute_review_mode(self, mock_llm):
        """Test execute in review mode."""
        mock_llm.return_value = {
            "content": json.dumps({
                "approved": True,
                "feedback": "Looks good"
            })
        }

        coder = SeniorCoder()
        input_data = AgentInput(
            task_id="test-456",
            prompt="Review implementation",
            context={
                "mode": "review",
                "spec": {},
                "implementation": {}
            }
        )
        output = coder.execute(input_data)

        assert output.task_id == "test-456"
        assert output.success is True
        assert output.data["approved"] is True

    def test_execute_unknown_mode(self):
        """Test execute with unknown mode."""
        coder = SeniorCoder()
        input_data = AgentInput(
            task_id="test-789",
            prompt="Unknown",
            context={"mode": "unknown"}
        )
        output = coder.execute(input_data)

        assert output.success is False
        assert "unknown" in output.error.lower()


class TestGetSeniorCoder:
    """Tests for get_senior_coder factory function."""

    def test_returns_senior_coder(self):
        """Test factory returns SeniorCoder instance."""
        coder = get_senior_coder()
        assert isinstance(coder, SeniorCoder)

    def test_returns_cached_instance(self):
        """Test factory returns cached instance."""
        coder1 = get_senior_coder()
        coder2 = get_senior_coder()
        assert coder1 is coder2


class TestSchemaVersions:
    """Tests for schema version constants."""

    def test_architecture_spec_version(self):
        """Test architecture spec schema version."""
        assert ARCHITECTURE_SPEC_SCHEMA_VERSION == 1

    def test_review_result_version(self):
        """Test review result schema version."""
        assert REVIEW_RESULT_SCHEMA_VERSION == 1

    def test_max_files_in_plan(self):
        """Test max files constant matches GeneralCoder."""
        assert MAX_FILES_IN_PLAN == 5
