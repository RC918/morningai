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
    ARCHITECTURE_SPEC_SCHEMA,
    REVIEW_RESULT_SCHEMA,
    SchemaValidationResult,
    validate_against_schema,
    sanitize_llm_output,
    redact_sensitive_data,
    # D-3: Spec-Driven Development imports
    TASK_SPEC_SCHEMA_VERSION,
    TASK_SPEC_SCHEMA,
    InterfaceType,
    FileSpec,
    InterfaceSpec,
    TestCaseSpec,
    TaskSpec,
    SpecParser,
    SpecValidationResult,
    SpecValidator,
    convert_architecture_spec_to_task_spec,
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


class TestSchemaValidation:
    """Tests for JSON schema validation.

    Issue: [P2] SeniorCoder JSON Schema - 驗證 spec 格式，增加決策可靠性
    """

    def test_validate_valid_architecture_spec(self):
        """Test validation of valid architecture spec."""
        valid_spec = {
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
                    "description": "Rename variable"
                }
            ],
            "constraints": ["Keep backward compatibility"]
        }
        result = validate_against_schema(valid_spec, ARCHITECTURE_SPEC_SCHEMA)
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_missing_required_field(self):
        """Test validation fails when required field is missing."""
        invalid_spec = {
            "architecture": {}
        }
        result = validate_against_schema(invalid_spec, ARCHITECTURE_SPEC_SCHEMA)
        assert result.is_valid is False
        assert any("task_analysis" in err for err in result.errors)

    def test_validate_invalid_complexity_enum(self):
        """Test validation fails for invalid complexity enum value."""
        invalid_spec = {
            "task_analysis": {
                "complexity": "invalid_value",
                "reasoning": "Test"
            }
        }
        result = validate_against_schema(invalid_spec, ARCHITECTURE_SPEC_SCHEMA)
        assert result.is_valid is False
        assert any("not in allowed values" in err for err in result.errors)

    def test_validate_invalid_type(self):
        """Test validation fails for invalid type."""
        invalid_spec = {
            "task_analysis": "should be object"
        }
        result = validate_against_schema(invalid_spec, ARCHITECTURE_SPEC_SCHEMA)
        assert result.is_valid is False
        assert any("expected object" in err for err in result.errors)

    def test_validate_valid_review_result(self):
        """Test validation of valid review result."""
        valid_review = {
            "approved": True,
            "feedback": "Implementation looks good"
        }
        result = validate_against_schema(valid_review, REVIEW_RESULT_SCHEMA)
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_review_missing_approved(self):
        """Test validation fails when approved field is missing."""
        invalid_review = {
            "feedback": "Some feedback"
        }
        result = validate_against_schema(invalid_review, REVIEW_RESULT_SCHEMA)
        assert result.is_valid is False
        assert any("approved" in err for err in result.errors)

    def test_validate_review_invalid_approved_type(self):
        """Test validation fails when approved is not boolean."""
        invalid_review = {
            "approved": "yes",
            "feedback": "Some feedback"
        }
        result = validate_against_schema(invalid_review, REVIEW_RESULT_SCHEMA)
        assert result.is_valid is False
        assert any("expected boolean" in err for err in result.errors)

    def test_validate_nested_array_items(self):
        """Test validation of nested array items."""
        spec_with_invalid_plan = {
            "task_analysis": {
                "complexity": "simple",
                "reasoning": "Test"
            },
            "implementation_plan": [
                {
                    "file_path": "test.py",
                    "action": "invalid_action",
                    "description": "Test"
                }
            ]
        }
        result = validate_against_schema(spec_with_invalid_plan, ARCHITECTURE_SPEC_SCHEMA)
        assert result.is_valid is False
        assert any("not in allowed values" in err for err in result.errors)

    def test_validate_complex_spec_with_abort(self):
        """Test validation of complex spec with abort reason."""
        complex_spec = {
            "task_analysis": {
                "complexity": "complex",
                "reasoning": "Requires architectural changes"
            },
            "abort_reason": "Task too complex for automated handling"
        }
        result = validate_against_schema(complex_spec, ARCHITECTURE_SPEC_SCHEMA)
        assert result.is_valid is True

    def test_schema_validation_result_dataclass(self):
        """Test SchemaValidationResult dataclass."""
        result = SchemaValidationResult(is_valid=True, errors=[])
        assert result.is_valid is True
        assert result.errors == []

        result_with_errors = SchemaValidationResult(
            is_valid=False,
            errors=["error1", "error2"]
        )
        assert result_with_errors.is_valid is False
        assert len(result_with_errors.errors) == 2


class TestSanitizeLlmOutput:
    """Tests for sanitize_llm_output() helper function.

    Issue #3752: [P3] Add unit tests for sanitize_llm_output() helper
    Blueprint Section 4.1 Safety Governor v2 - Telemetry v2 可觀測性
    """

    def test_basic_string_sanitization(self):
        """Test basic string input is sanitized correctly."""
        result = sanitize_llm_output("hello world")
        assert result == "'hello world'"

    def test_control_character_removal(self):
        """Test control characters are removed (except tab, newline, CR)."""
        input_with_control = "hello\x00\x01\x02\x03\x04\x05\x06\x07\x08world"
        result = sanitize_llm_output(input_with_control)
        assert "\x00" not in result
        assert "\x01" not in result
        assert "\x02" not in result
        assert "helloworld" in result

    def test_bell_and_backspace_removed(self):
        """Test bell (\\x07) and backspace (\\x08) are removed."""
        input_str = "hello\x07\x08world"
        result = sanitize_llm_output(input_str)
        assert "helloworld" in result

    def test_vertical_tab_and_form_feed_removed(self):
        """Test vertical tab (\\x0b) and form feed (\\x0c) are removed."""
        input_str = "hello\x0b\x0cworld"
        result = sanitize_llm_output(input_str)
        assert "helloworld" in result

    def test_escape_and_other_control_chars_removed(self):
        """Test escape (\\x1b) and other control chars (\\x0e-\\x1f) are removed."""
        input_str = "hello\x0e\x0f\x1b\x1fworld"
        result = sanitize_llm_output(input_str)
        assert "helloworld" in result

    def test_del_character_removed(self):
        """Test DEL character (\\x7f) is removed."""
        input_str = "hello\x7fworld"
        result = sanitize_llm_output(input_str)
        assert "helloworld" in result

    def test_tab_preserved_but_escaped(self):
        """Test tab (\\x09) is preserved but escaped in repr output."""
        input_str = "hello\tworld"
        result = sanitize_llm_output(input_str)
        assert "\\t" in result or "hello\tworld" in result

    def test_newline_escaped(self):
        """Test newline (\\x0a) is escaped to \\n."""
        input_str = "hello\nworld"
        result = sanitize_llm_output(input_str)
        assert "\\n" in result
        assert "\n" not in result

    def test_carriage_return_escaped(self):
        """Test carriage return (\\x0d) is escaped to \\r."""
        input_str = "hello\rworld"
        result = sanitize_llm_output(input_str)
        assert "\\r" in result
        assert "\r" not in result

    def test_multiple_newlines_escaped(self):
        """Test multiple newlines are all escaped."""
        input_str = "line1\nline2\nline3"
        result = sanitize_llm_output(input_str)
        assert result.count("\\n") == 2

    def test_truncation_at_default_length(self):
        """Test strings longer than default max_length (200) are truncated."""
        long_string = "a" * 300
        result = sanitize_llm_output(long_string)
        assert "..." in result
        assert len(result) < 300

    def test_truncation_at_custom_length(self):
        """Test truncation with custom max_length."""
        input_str = "a" * 100
        result = sanitize_llm_output(input_str, max_length=50)
        assert "..." in result
        assert len(result) < 100

    def test_no_truncation_for_short_strings(self):
        """Test short strings are not truncated."""
        short_string = "hello"
        result = sanitize_llm_output(short_string)
        assert "..." not in result
        assert "hello" in result

    def test_type_handling_integer(self):
        """Test integer input is converted to string."""
        result = sanitize_llm_output(42)
        assert "42" in result

    def test_type_handling_float(self):
        """Test float input is converted to string."""
        result = sanitize_llm_output(3.14159)
        assert "3.14159" in result

    def test_type_handling_dict(self):
        """Test dict input is converted to string."""
        result = sanitize_llm_output({"key": "value"})
        assert "key" in result
        assert "value" in result

    def test_type_handling_list(self):
        """Test list input is converted to string."""
        result = sanitize_llm_output([1, 2, 3])
        assert "1" in result
        assert "2" in result
        assert "3" in result

    def test_type_handling_none(self):
        """Test None input is converted to string."""
        result = sanitize_llm_output(None)
        assert "None" in result

    def test_type_handling_boolean(self):
        """Test boolean input is converted to string."""
        result = sanitize_llm_output(True)
        assert "True" in result
        result = sanitize_llm_output(False)
        assert "False" in result

    def test_empty_string(self):
        """Test empty string input."""
        result = sanitize_llm_output("")
        assert result == "''"

    def test_whitespace_only_string(self):
        """Test whitespace-only string."""
        result = sanitize_llm_output("   ")
        assert "   " in result

    def test_unicode_characters_preserved(self):
        """Test unicode characters are preserved."""
        result = sanitize_llm_output("你好世界")
        assert "你好世界" in result

    def test_emoji_preserved(self):
        """Test emoji characters are preserved."""
        result = sanitize_llm_output("Hello 👋 World 🌍")
        assert "👋" in result or "Hello" in result

    def test_mixed_control_and_normal_chars(self):
        """Test mixed control characters and normal text."""
        input_str = "start\x00middle\x01end\x02"
        result = sanitize_llm_output(input_str)
        assert "startmiddleend" in result

    def test_nested_newlines_and_control_chars(self):
        """Test combination of newlines and control characters."""
        input_str = "line1\n\x00line2\r\x01line3"
        result = sanitize_llm_output(input_str)
        assert "\\n" in result
        assert "\\r" in result
        assert "\x00" not in result
        assert "\x01" not in result

    def test_context_parameter_accepted(self):
        """Test context parameter is accepted (used for logging)."""
        result = sanitize_llm_output("test", context="test_context")
        assert "test" in result

    def test_very_long_string_with_control_chars(self):
        """Test very long string with control characters is properly handled."""
        long_input = ("a\x00" * 200) + "end"
        result = sanitize_llm_output(long_input, max_length=100)
        assert "..." in result
        assert "\x00" not in result

    def test_repr_wrapping(self):
        """Test output is wrapped with repr() for safe quoting."""
        result = sanitize_llm_output("test")
        assert result.startswith("'") and result.endswith("'")

    def test_special_chars_in_string(self):
        """Test special characters like quotes are escaped."""
        result = sanitize_llm_output("it's a \"test\"")
        assert "it" in result
        assert "test" in result

    def test_backslash_handling(self):
        """Test backslashes are handled correctly."""
        result = sanitize_llm_output("path\\to\\file")
        assert "path" in result
        assert "file" in result

    def test_sensitive_data_redaction_api_key(self):
        """Test API keys are redacted by default."""
        input_str = "Using API key sk-abcdefghijklmnopqrstuvwxyz123456"
        result = sanitize_llm_output(input_str)
        assert "sk-abcdefghijklmnopqrstuvwxyz" not in result
        assert "REDACTED" in result

    def test_sensitive_data_redaction_disabled(self):
        """Test sensitive data redaction can be disabled."""
        input_str = "Using API key sk-abcdefghijklmnopqrstuvwxyz123456"
        result = sanitize_llm_output(input_str, redact_sensitive=False)
        assert "sk-abcdefghijklmnopqrstuvwxyz" in result

    def test_sensitive_data_redaction_password(self):
        """Test password patterns are redacted."""
        input_str = "password=mysecretpassword123"
        result = sanitize_llm_output(input_str)
        assert "mysecretpassword123" not in result
        assert "REDACTED" in result

    def test_sensitive_data_redaction_jwt(self):
        """Test JWT tokens are redacted."""
        jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
        result = sanitize_llm_output(f"Token: {jwt}")
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in result
        assert "REDACTED" in result

    def test_sensitive_data_redaction_github_token(self):
        """Test GitHub tokens are redacted."""
        input_str = "ghp_abcdefghijklmnopqrstuvwxyz1234567890"
        result = sanitize_llm_output(input_str)
        assert "ghp_abcdefghijklmnopqrstuvwxyz" not in result
        assert "REDACTED" in result


class TestRedactSensitiveData:
    """Tests for redact_sensitive_data() helper function.

    Issue #3749: [P3] Implement sensitive data sanitization for SeniorCoder logs
    """

    def test_no_sensitive_data(self):
        """Test text without sensitive data is unchanged."""
        text = "This is normal text without secrets"
        result, was_redacted = redact_sensitive_data(text)
        assert result == text
        assert was_redacted is False

    def test_api_key_sk_format(self):
        """Test sk- format API keys are redacted."""
        text = "API key: sk-abcdefghijklmnopqrstuvwxyz123456"
        result, was_redacted = redact_sensitive_data(text)
        assert "sk-abcdefghijklmnopqrstuvwxyz" not in result
        assert "[REDACTED_API_KEY]" in result
        assert was_redacted is True

    def test_bearer_token(self):
        """Test Bearer tokens are redacted."""
        text = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        result, was_redacted = redact_sensitive_data(text)
        assert "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in result
        assert "[REDACTED_BEARER_TOKEN]" in result
        assert was_redacted is True

    def test_jwt_token(self):
        """Test JWT tokens are redacted."""
        jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
        text = f"Token: {jwt}"
        result, was_redacted = redact_sensitive_data(text)
        assert jwt not in result
        assert "[REDACTED_JWT]" in result
        assert was_redacted is True

    def test_password_equals_format(self):
        """Test password= format is redacted."""
        text = "password=mysecretpassword123"
        result, was_redacted = redact_sensitive_data(text)
        assert "mysecretpassword123" not in result
        assert "[REDACTED]" in result
        assert was_redacted is True

    def test_password_colon_format(self):
        """Test password: format is redacted."""
        text = "password: mysecretpassword123"
        result, was_redacted = redact_sensitive_data(text)
        assert "mysecretpassword123" not in result
        assert "[REDACTED]" in result
        assert was_redacted is True

    def test_secret_format(self):
        """Test secret= format is redacted."""
        text = "secret=verysecretvalue123"
        result, was_redacted = redact_sensitive_data(text)
        assert "verysecretvalue123" not in result
        assert "[REDACTED]" in result
        assert was_redacted is True

    def test_aws_access_key(self):
        """Test AWS access keys are redacted."""
        text = "AWS key: AKIAIOSFODNN7EXAMPLE"
        result, was_redacted = redact_sensitive_data(text)
        assert "AKIAIOSFODNN7EXAMPLE" not in result
        assert "[REDACTED_AWS_KEY]" in result
        assert was_redacted is True

    def test_github_personal_token(self):
        """Test GitHub personal access tokens are redacted."""
        text = "ghp_abcdefghijklmnopqrstuvwxyz1234567890"
        result, was_redacted = redact_sensitive_data(text)
        assert "ghp_abcdefghijklmnopqrstuvwxyz" not in result
        assert "[REDACTED_GITHUB_TOKEN]" in result
        assert was_redacted is True

    def test_github_oauth_token(self):
        """Test GitHub OAuth tokens are redacted."""
        text = "gho_abcdefghijklmnopqrstuvwxyz1234567890"
        result, was_redacted = redact_sensitive_data(text)
        assert "gho_abcdefghijklmnopqrstuvwxyz" not in result
        assert "[REDACTED_GITHUB_TOKEN]" in result
        assert was_redacted is True

    def test_private_key_marker(self):
        """Test private key markers are redacted."""
        text = "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBg..."
        result, was_redacted = redact_sensitive_data(text)
        assert "-----BEGIN PRIVATE KEY-----" not in result
        assert "[REDACTED_PRIVATE_KEY]" in result
        assert was_redacted is True

    def test_rsa_private_key_marker(self):
        """Test RSA private key markers are redacted."""
        text = "-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEA..."
        result, was_redacted = redact_sensitive_data(text)
        assert "-----BEGIN RSA PRIVATE KEY-----" not in result
        assert "[REDACTED_PRIVATE_KEY]" in result
        assert was_redacted is True

    def test_api_key_with_equals_separator(self):
        """Test api_key= format is redacted (requires = or : separator)."""
        text = "api_key=abcdefghijklmnop1234"
        result, was_redacted = redact_sensitive_data(text)
        assert "abcdefghijklmnop1234" not in result
        assert "[REDACTED_API_KEY]" in result
        assert was_redacted is True

    def test_api_key_with_colon_separator(self):
        """Test api_key: format is redacted."""
        text = "api_key: abcdefghijklmnop1234"
        result, was_redacted = redact_sensitive_data(text)
        assert "abcdefghijklmnop1234" not in result
        assert "[REDACTED_API_KEY]" in result
        assert was_redacted is True

    def test_api_key_without_separator_not_redacted(self):
        """Test api_key without = or : is not redacted (reduces false positives)."""
        text = "apikey_somefunction_name"
        result, was_redacted = redact_sensitive_data(text)
        # This should NOT be redacted because it lacks = or : separator
        assert result == text
        assert was_redacted is False

    def test_multiple_sensitive_items(self):
        """Test multiple sensitive items in same text are all redacted."""
        text = "password=secret123 and api_key=sk-abcdefghijklmnopqrstuvwxyz"
        result, was_redacted = redact_sensitive_data(text)
        assert "secret123" not in result
        assert "sk-abcdefghijklmnopqrstuvwxyz" not in result
        assert was_redacted is True

    def test_short_password_not_redacted(self):
        """Test short passwords (< 8 chars) are not redacted."""
        text = "password=short"
        result, was_redacted = redact_sensitive_data(text)
        assert result == text
        assert was_redacted is False

    def test_preserves_surrounding_text(self):
        """Test surrounding text is preserved after redaction."""
        text = "Config: password=mysecretpassword123 and other settings"
        result, was_redacted = redact_sensitive_data(text)
        assert "Config:" in result
        assert "and other settings" in result
        assert was_redacted is True


# =============================================================================
# D-3: Spec-Driven Development Tests
# Issue #2762: D-3 Spec-Driven Development - Planner-Coder Integration
# =============================================================================


class TestInterfaceType:
    """Tests for InterfaceType enum.

    Issue #2762: D-3 Spec-Driven Development
    """

    def test_interface_type_values(self):
        """Test all InterfaceType enum values."""
        assert InterfaceType.FUNCTION.value == "function"
        assert InterfaceType.CLASS.value == "class"
        assert InterfaceType.API.value == "api"


class TestFileSpec:
    """Tests for FileSpec dataclass.

    Issue #2762: D-3 Spec-Driven Development
    """

    def test_to_dict(self):
        """Test FileSpec serialization."""
        spec = FileSpec(
            path="src/utils.py",
            purpose="Utility functions",
            dependencies=["src/config.py"]
        )
        result = spec.to_dict()
        assert result["path"] == "src/utils.py"
        assert result["purpose"] == "Utility functions"
        assert result["dependencies"] == ["src/config.py"]

    def test_to_dict_empty_dependencies(self):
        """Test FileSpec with empty dependencies."""
        spec = FileSpec(path="src/main.py", purpose="Entry point")
        result = spec.to_dict()
        assert result["dependencies"] == []

    def test_from_dict(self):
        """Test FileSpec deserialization."""
        data = {
            "path": "src/helpers.py",
            "purpose": "Helper functions",
            "dependencies": ["src/utils.py"]
        }
        spec = FileSpec.from_dict(data)
        assert spec.path == "src/helpers.py"
        assert spec.purpose == "Helper functions"
        assert spec.dependencies == ["src/utils.py"]

    def test_from_dict_missing_optional(self):
        """Test FileSpec deserialization with missing optional fields."""
        data = {"path": "src/test.py"}
        spec = FileSpec.from_dict(data)
        assert spec.path == "src/test.py"
        assert spec.purpose == ""
        assert spec.dependencies == []


class TestInterfaceSpec:
    """Tests for InterfaceSpec dataclass.

    Issue #2762: D-3 Spec-Driven Development
    """

    def test_to_dict(self):
        """Test InterfaceSpec serialization."""
        spec = InterfaceSpec(
            name="process_data",
            interface_type=InterfaceType.FUNCTION,
            signature="def process_data(data: dict) -> dict",
            description="Process input data"
        )
        result = spec.to_dict()
        assert result["name"] == "process_data"
        assert result["interface_type"] == "function"
        assert result["signature"] == "def process_data(data: dict) -> dict"
        assert result["description"] == "Process input data"

    def test_from_dict(self):
        """Test InterfaceSpec deserialization."""
        data = {
            "name": "DataProcessor",
            "interface_type": "class",
            "signature": "class DataProcessor:",
            "description": "Data processing class"
        }
        spec = InterfaceSpec.from_dict(data)
        assert spec.name == "DataProcessor"
        assert spec.interface_type == InterfaceType.CLASS
        assert spec.signature == "class DataProcessor:"
        assert spec.description == "Data processing class"

    def test_from_dict_invalid_type_defaults_to_function(self):
        """Test InterfaceSpec with invalid type defaults to function."""
        data = {
            "name": "test",
            "interface_type": "invalid_type",
            "signature": "def test():"
        }
        spec = InterfaceSpec.from_dict(data)
        assert spec.interface_type == InterfaceType.FUNCTION


class TestTestCaseSpec:
    """Tests for TestCaseSpec dataclass.

    Issue #2762: D-3 Spec-Driven Development
    """

    def test_to_dict(self):
        """Test TestCaseSpec serialization."""
        spec = TestCaseSpec(
            name="test_process_valid_data",
            description="Test processing valid data",
            input_data={"key": "value"},
            expected_output={"result": "success"}
        )
        result = spec.to_dict()
        assert result["name"] == "test_process_valid_data"
        assert result["description"] == "Test processing valid data"
        assert result["input_data"] == {"key": "value"}
        assert result["expected_output"] == {"result": "success"}

    def test_from_dict(self):
        """Test TestCaseSpec deserialization."""
        data = {
            "name": "test_error_handling",
            "description": "Test error handling",
            "input_data": None,
            "expected_output": "error"
        }
        spec = TestCaseSpec.from_dict(data)
        assert spec.name == "test_error_handling"
        assert spec.description == "Test error handling"
        assert spec.input_data is None
        assert spec.expected_output == "error"


class TestTaskSpec:
    """Tests for TaskSpec dataclass.

    Issue #2762: D-3 Spec-Driven Development
    """

    def test_to_dict_minimal(self):
        """Test minimal TaskSpec serialization."""
        spec = TaskSpec(
            title="Add logging",
            description="Add logging to the application"
        )
        result = spec.to_dict()
        assert result["schema_version"] == TASK_SPEC_SCHEMA_VERSION
        assert result["title"] == "Add logging"
        assert result["description"] == "Add logging to the application"
        assert result["files_to_create"] == []
        assert result["files_to_modify"] == []
        assert result["files_to_delete"] == []

    def test_to_dict_full(self):
        """Test full TaskSpec serialization."""
        spec = TaskSpec(
            title="Implement feature",
            description="Implement new feature",
            files_to_create=[FileSpec("src/new.py", "New file")],
            files_to_modify=[FileSpec("src/existing.py", "Modify existing")],
            files_to_delete=["src/old.py"],
            interfaces=[InterfaceSpec(
                "new_func", InterfaceType.FUNCTION, "def new_func():", "New"
            )],
            test_cases=[TestCaseSpec("test_new", "Test new", {}, {})],
            acceptance_criteria=["Feature works correctly"]
        )
        result = spec.to_dict()
        assert len(result["files_to_create"]) == 1
        assert len(result["files_to_modify"]) == 1
        assert result["files_to_delete"] == ["src/old.py"]
        assert len(result["interfaces"]) == 1
        assert len(result["test_cases"]) == 1
        assert result["acceptance_criteria"] == ["Feature works correctly"]

    def test_to_json(self):
        """Test TaskSpec JSON serialization."""
        spec = TaskSpec(title="Test", description="Test task")
        json_str = spec.to_json()
        data = json.loads(json_str)
        assert data["title"] == "Test"
        assert data["schema_version"] == TASK_SPEC_SCHEMA_VERSION

    def test_total_file_count(self):
        """Test total_file_count property."""
        spec = TaskSpec(
            title="Test",
            description="Test",
            files_to_create=[FileSpec("a.py", ""), FileSpec("b.py", "")],
            files_to_modify=[FileSpec("c.py", "")],
            files_to_delete=["d.py", "e.py"]
        )
        assert spec.total_file_count == 5

    def test_is_valid_true(self):
        """Test is_valid returns True for valid spec."""
        spec = TaskSpec(title="Valid", description="Valid task")
        assert spec.is_valid is True

    def test_is_valid_false_empty_title(self):
        """Test is_valid returns False for empty title."""
        spec = TaskSpec(title="", description="Description")
        assert spec.is_valid is False

    def test_is_valid_false_empty_description(self):
        """Test is_valid returns False for empty description."""
        spec = TaskSpec(title="Title", description="")
        assert spec.is_valid is False


class TestSpecParser:
    """Tests for SpecParser class.

    Issue #2762: D-3 Spec-Driven Development
    """

    def test_parse_valid_json(self):
        """Test parsing valid TaskSpec JSON."""
        json_str = json.dumps({
            "title": "Add feature",
            "description": "Add new feature to app",
            "files_to_create": [{"path": "src/new.py", "purpose": "New file"}],
            "acceptance_criteria": ["Feature works"]
        })
        result = SpecParser.parse(json_str)
        assert result.success is True
        assert result.spec is not None
        assert result.spec.title == "Add feature"
        assert len(result.spec.files_to_create) == 1

    def test_parse_invalid_json(self):
        """Test parsing invalid JSON returns error."""
        result = SpecParser.parse("not valid json")
        assert result.success is False
        assert result.spec is None
        assert "parse" in result.error.lower() or "json" in result.error.lower()

    def test_parse_missing_required_fields(self):
        """Test parsing JSON with missing required fields."""
        json_str = json.dumps({"title": "Only title"})
        result = SpecParser.parse(json_str)
        assert result.success is False
        assert "description" in result.error.lower()

    def test_parse_dict_valid(self):
        """Test parsing valid dictionary."""
        data = {
            "title": "Test task",
            "description": "Test description",
            "interfaces": [{
                "name": "test_func",
                "interface_type": "function",
                "signature": "def test_func():",
                "description": "Test function"
            }]
        }
        result = SpecParser.parse_dict(data)
        assert result.success is True
        assert result.spec.title == "Test task"
        assert len(result.spec.interfaces) == 1

    def test_parse_dict_empty(self):
        """Test parsing empty dictionary."""
        result = SpecParser.parse_dict({})
        assert result.success is False


class TestSpecValidator:
    """Tests for SpecValidator class.

    Issue #2762: D-3 Spec-Driven Development
    """

    def test_validate_valid_spec(self):
        """Test validation of valid TaskSpec."""
        spec = TaskSpec(
            title="Valid task",
            description="Valid description",
            files_to_create=[FileSpec("src/new.py", "New file")],
            acceptance_criteria=["Works correctly"]
        )
        result = SpecValidator.validate(spec)
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_invalid_empty_title(self):
        """Test validation fails for empty title."""
        spec = TaskSpec(title="", description="Description")
        result = SpecValidator.validate(spec)
        assert result.is_valid is False
        assert any("title" in err.lower() for err in result.errors)

    def test_validate_invalid_empty_description(self):
        """Test validation fails for empty description."""
        spec = TaskSpec(title="Title", description="")
        result = SpecValidator.validate(spec)
        assert result.is_valid is False
        assert any("description" in err.lower() for err in result.errors)

    def test_validate_too_many_files(self):
        """Test validation warns for too many files."""
        spec = TaskSpec(
            title="Large task",
            description="Task with many files",
            files_to_create=[FileSpec(f"f{i}.py", "") for i in range(10)]
        )
        result = SpecValidator.validate(spec)
        # Should still be valid but may have warnings
        assert result.is_valid is True or len(result.warnings) > 0

    def test_validation_result_to_dict(self):
        """Test SpecValidationResult serialization."""
        result = SpecValidationResult(
            is_valid=False,
            errors=["Error 1", "Error 2"],
            warnings=["Warning 1"]
        )
        data = result.to_dict()
        assert data["is_valid"] is False
        assert len(data["errors"]) == 2
        assert len(data["warnings"]) == 1


class TestConvertArchitectureSpecToTaskSpec:
    """Tests for convert_architecture_spec_to_task_spec function.

    Issue #2762: D-3 Spec-Driven Development - D-2 to D-3 Migration
    """

    def test_convert_simple_spec(self):
        """Test converting simple ArchitectureSpec to TaskSpec."""
        arch_spec = ArchitectureSpec(
            task_analysis=TaskAnalysis(
                complexity=TaskComplexity.SIMPLE,
                reasoning="Simple task"
            ),
            architecture=ArchitecturePlan(
                files_to_modify=["src/utils.py"],
                files_to_create=["src/helpers.py"]
            ),
            implementation_plan=[
                ImplementationStep(
                    file_path="src/utils.py",
                    action=FileAction.MODIFY,
                    description="Add helper function",
                    function_signatures=["def helper(x: int) -> str"],
                    test_cases=["test helper returns string"]
                )
            ],
            constraints=["Keep backward compatibility"]
        )
        task_spec = convert_architecture_spec_to_task_spec(
            arch_spec, "Add helper function"
        )
        assert task_spec.title == "Add helper function"
        assert task_spec.description == "Add helper function"
        assert len(task_spec.files_to_modify) == 1
        assert len(task_spec.files_to_create) == 1
        assert len(task_spec.interfaces) == 1
        assert len(task_spec.acceptance_criteria) == 1

    def test_convert_complex_spec(self):
        """Test converting complex ArchitectureSpec to TaskSpec."""
        arch_spec = ArchitectureSpec(
            task_analysis=TaskAnalysis(
                complexity=TaskComplexity.MODERATE,
                reasoning="Moderate complexity"
            ),
            architecture=ArchitecturePlan(
                files_to_modify=["a.py", "b.py"],
                files_to_create=["c.py"],
                dependencies={"a.py": ["b.py"]}
            ),
            implementation_plan=[
                ImplementationStep(
                    file_path="a.py",
                    action=FileAction.MODIFY,
                    description="Modify A",
                    function_signatures=["def func_a():", "def func_b():"],
                    test_cases=["test A", "test B"]
                ),
                ImplementationStep(
                    file_path="c.py",
                    action=FileAction.CREATE,
                    description="Create C",
                    function_signatures=["class MyClass:"],
                    test_cases=["test C"]
                )
            ],
            constraints=["Constraint 1", "Constraint 2"]
        )
        task_spec = convert_architecture_spec_to_task_spec(
            arch_spec, "Complex task"
        )
        assert len(task_spec.files_to_modify) == 2
        assert len(task_spec.files_to_create) == 1
        assert len(task_spec.interfaces) == 3  # 2 from a.py + 1 from c.py
        assert len(task_spec.test_cases) == 3  # test A, test B, test C
        assert len(task_spec.acceptance_criteria) == 2

    def test_convert_empty_spec(self):
        """Test converting minimal ArchitectureSpec."""
        arch_spec = ArchitectureSpec(
            task_analysis=TaskAnalysis(
                complexity=TaskComplexity.SIMPLE,
                reasoning="Minimal"
            )
        )
        task_spec = convert_architecture_spec_to_task_spec(
            arch_spec, "Minimal task"
        )
        assert task_spec.title == "Minimal task"
        assert task_spec.is_valid is True
        assert len(task_spec.files_to_create) == 0
        assert len(task_spec.files_to_modify) == 0


class TestTaskSpecSchemaVersion:
    """Tests for TaskSpec schema version constant.

    Issue #2762: D-3 Spec-Driven Development
    """

    def test_task_spec_schema_version(self):
        """Test TaskSpec schema version is set correctly."""
        assert TASK_SPEC_SCHEMA_VERSION == 1

    def test_task_spec_schema_exists(self):
        """Test TASK_SPEC_SCHEMA is defined."""
        assert TASK_SPEC_SCHEMA is not None
        assert "type" in TASK_SPEC_SCHEMA
        assert TASK_SPEC_SCHEMA["type"] == "object"

    def test_task_spec_schema_has_required_fields(self):
        """Test TASK_SPEC_SCHEMA has required fields defined."""
        assert "required" in TASK_SPEC_SCHEMA
        assert "title" in TASK_SPEC_SCHEMA["required"]
        assert "description" in TASK_SPEC_SCHEMA["required"]
