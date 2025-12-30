"""
Exception and Error Path Tests for SimpleCoder - Issue #3240

This module tests exception handling and error recovery paths in the SimpleCoder flow:
1. LLM response parsing errors (malformed JSON, missing fields, unknown status)
2. LLM call failures (timeout, connection, rate limit, generic exceptions)
3. Syntax validation edge cases
4. Singleton initialization failure handling
5. Autofix gate edge cases with malformed inputs

Issue #3240: Exception/error path tests
Parent Issue #2760: D-1 General Coder Agent MVP
Parent EPIC #2759: EPIC D - Autonomous Coder Agent Family
"""
import json
import pytest
from unittest.mock import patch

import coder.simple_coder as sc_module
from coder.simple_coder import (
    SimpleCoder,
    CoderOutput,
    CoderStatus,
    validate_python_syntax,
    get_simple_coder,
)
from coder.autofix_gate import is_autofix_allowed, is_path_excluded
from core.agents import AgentInput


class TestLLMResponseParsingErrors:
    """Tests for error handling when parsing LLM responses."""

    @pytest.fixture
    def coder(self):
        """Create a SimpleCoder instance."""
        return SimpleCoder()

    @patch.object(SimpleCoder, 'call_llm')
    def test_empty_patch_content(self, mock_call_llm, coder):
        """Test handling when LLM returns patch status but empty patch content."""
        mock_call_llm.return_value = {
            "content": json.dumps({
                "status": "patch",
                "patch": ""
            })
        }

        result = coder.generate_fix(
            file_path="test.py",
            file_content="def foo(): pass",
            review_comment="Add docstring",
            severity="low"
        )

        assert result.status == CoderStatus.SKIPPED
        assert "no patch content" in result.reason.lower()

    @patch.object(SimpleCoder, 'call_llm')
    def test_whitespace_only_patch_content(self, mock_call_llm, coder):
        """Test handling when LLM returns patch with only whitespace.

        Note: Current implementation accepts whitespace-only patches and
        lets syntax validation handle them. For Python files, whitespace-only
        content is valid Python (empty module), so it passes syntax check.
        """
        mock_call_llm.return_value = {
            "content": json.dumps({
                "status": "patch",
                "patch": "   \n\t  "
            })
        }

        result = coder.generate_fix(
            file_path="test.py",
            file_content="def foo(): pass",
            review_comment="Add docstring",
            severity="low"
        )

        assert result.status == CoderStatus.PATCH
        assert result.syntax_valid is True

    @patch.object(SimpleCoder, 'call_llm')
    def test_unknown_status_value(self, mock_call_llm, coder):
        """Test handling when LLM returns unknown status value."""
        mock_call_llm.return_value = {
            "content": json.dumps({
                "status": "unknown_status",
                "reason": "Something"
            })
        }

        result = coder.generate_fix(
            file_path="test.py",
            file_content="def foo(): pass",
            review_comment="Fix it",
            severity="low"
        )

        assert result.status == CoderStatus.SKIPPED
        assert "unknown status" in result.reason.lower()

    @patch.object(SimpleCoder, 'call_llm')
    def test_missing_status_field(self, mock_call_llm, coder):
        """Test handling when LLM response is missing status field."""
        mock_call_llm.return_value = {
            "content": json.dumps({
                "reason": "Some reason",
                "patch": "def foo(): pass"
            })
        }

        result = coder.generate_fix(
            file_path="test.py",
            file_content="def foo(): pass",
            review_comment="Fix it",
            severity="low"
        )

        assert result.status == CoderStatus.SKIPPED
        assert "unknown status" in result.reason.lower()

    @patch.object(SimpleCoder, 'call_llm')
    def test_null_status_field(self, mock_call_llm, coder):
        """Test handling when LLM returns null status."""
        mock_call_llm.return_value = {
            "content": json.dumps({
                "status": None,
                "patch": "def foo(): pass"
            })
        }

        result = coder.generate_fix(
            file_path="test.py",
            file_content="def foo(): pass",
            review_comment="Fix it",
            severity="low"
        )

        assert result.status == CoderStatus.SKIPPED

    @patch.object(SimpleCoder, 'call_llm')
    def test_empty_json_object(self, mock_call_llm, coder):
        """Test handling when LLM returns empty JSON object."""
        mock_call_llm.return_value = {
            "content": "{}"
        }

        result = coder.generate_fix(
            file_path="test.py",
            file_content="def foo(): pass",
            review_comment="Fix it",
            severity="low"
        )

        assert result.status == CoderStatus.SKIPPED

    @patch.object(SimpleCoder, 'call_llm')
    def test_json_array_instead_of_object(self, mock_call_llm, coder):
        """Test handling when LLM returns JSON array instead of object."""
        mock_call_llm.return_value = {
            "content": '["status", "patch"]'
        }

        result = coder.generate_fix(
            file_path="test.py",
            file_content="def foo(): pass",
            review_comment="Fix it",
            severity="low"
        )

        assert result.status == CoderStatus.SKIPPED

    @patch.object(SimpleCoder, 'call_llm')
    def test_truncated_json(self, mock_call_llm, coder):
        """Test handling when LLM returns truncated JSON."""
        mock_call_llm.return_value = {
            "content": '{"status": "patch", "patch": "def foo():'
        }

        result = coder.generate_fix(
            file_path="test.py",
            file_content="def foo(): pass",
            review_comment="Fix it",
            severity="low"
        )

        assert result.status == CoderStatus.SKIPPED
        assert "json" in result.reason.lower()

    @patch.object(SimpleCoder, 'call_llm')
    def test_json_with_extra_text(self, mock_call_llm, coder):
        """Test handling when LLM returns JSON with extra text."""
        mock_call_llm.return_value = {
            "content": 'Here is the fix: {"status": "patch", "patch": "def foo(): pass"}'
        }

        result = coder.generate_fix(
            file_path="test.py",
            file_content="def foo(): pass",
            review_comment="Fix it",
            severity="low"
        )

        assert result.status == CoderStatus.SKIPPED
        assert "json" in result.reason.lower()

    @patch.object(SimpleCoder, 'call_llm')
    def test_skipped_without_reason(self, mock_call_llm, coder):
        """Test handling when LLM returns skipped status without reason."""
        mock_call_llm.return_value = {
            "content": json.dumps({
                "status": "skipped"
            })
        }

        result = coder.generate_fix(
            file_path="test.py",
            file_content="def foo(): pass",
            review_comment="Fix it",
            severity="low"
        )

        assert result.status == CoderStatus.SKIPPED
        assert result.reason is not None
        assert "no reason" in result.reason.lower()

    @patch.object(SimpleCoder, 'call_llm')
    def test_case_insensitive_status(self, mock_call_llm, coder):
        """Test that status field is case-insensitive."""
        mock_call_llm.return_value = {
            "content": json.dumps({
                "status": "PATCH",
                "patch": "def foo():\n    pass"
            })
        }

        result = coder.generate_fix(
            file_path="test.py",
            file_content="def foo(): pass",
            review_comment="Fix it",
            severity="low"
        )

        assert result.status == CoderStatus.PATCH

    @patch.object(SimpleCoder, 'call_llm')
    def test_mixed_case_status(self, mock_call_llm, coder):
        """Test that mixed case status is handled."""
        mock_call_llm.return_value = {
            "content": json.dumps({
                "status": "Skipped",
                "reason": "Too complex"
            })
        }

        result = coder.generate_fix(
            file_path="test.py",
            file_content="def foo(): pass",
            review_comment="Fix it",
            severity="low"
        )

        assert result.status == CoderStatus.SKIPPED


class TestLLMCallFailures:
    """Tests for error handling when LLM calls fail."""

    @pytest.fixture
    def coder(self):
        """Create a SimpleCoder instance."""
        return SimpleCoder()

    @patch.object(SimpleCoder, 'call_llm')
    def test_timeout_error(self, mock_call_llm, coder):
        """Test handling of timeout errors from LLM."""
        mock_call_llm.side_effect = TimeoutError("Request timed out")

        result = coder.generate_fix(
            file_path="test.py",
            file_content="def foo(): pass",
            review_comment="Fix it",
            severity="low"
        )

        assert result.status == CoderStatus.SKIPPED
        assert "llm call failed" in result.reason.lower()
        assert "timed out" in result.reason.lower()

    @patch.object(SimpleCoder, 'call_llm')
    def test_connection_error(self, mock_call_llm, coder):
        """Test handling of connection errors from LLM."""
        mock_call_llm.side_effect = ConnectionError("Connection refused")

        result = coder.generate_fix(
            file_path="test.py",
            file_content="def foo(): pass",
            review_comment="Fix it",
            severity="low"
        )

        assert result.status == CoderStatus.SKIPPED
        assert "llm call failed" in result.reason.lower()

    @patch.object(SimpleCoder, 'call_llm')
    def test_value_error(self, mock_call_llm, coder):
        """Test handling of ValueError from LLM."""
        mock_call_llm.side_effect = ValueError("Invalid parameter")

        result = coder.generate_fix(
            file_path="test.py",
            file_content="def foo(): pass",
            review_comment="Fix it",
            severity="low"
        )

        assert result.status == CoderStatus.SKIPPED
        assert "llm call failed" in result.reason.lower()

    @patch.object(SimpleCoder, 'call_llm')
    def test_runtime_error(self, mock_call_llm, coder):
        """Test handling of RuntimeError from LLM."""
        mock_call_llm.side_effect = RuntimeError("Internal error")

        result = coder.generate_fix(
            file_path="test.py",
            file_content="def foo(): pass",
            review_comment="Fix it",
            severity="low"
        )

        assert result.status == CoderStatus.SKIPPED
        assert "llm call failed" in result.reason.lower()

    @patch.object(SimpleCoder, 'call_llm')
    def test_keyboard_interrupt_propagates(self, mock_call_llm, coder):
        """Test that KeyboardInterrupt is not caught."""
        mock_call_llm.side_effect = KeyboardInterrupt()

        with pytest.raises(KeyboardInterrupt):
            coder.generate_fix(
                file_path="test.py",
                file_content="def foo(): pass",
                review_comment="Fix it",
                severity="low"
            )

    @patch.object(SimpleCoder, 'call_llm')
    def test_system_exit_propagates(self, mock_call_llm, coder):
        """Test that SystemExit is not caught."""
        mock_call_llm.side_effect = SystemExit(1)

        with pytest.raises(SystemExit):
            coder.generate_fix(
                file_path="test.py",
                file_content="def foo(): pass",
                review_comment="Fix it",
                severity="low"
            )

    @patch.object(SimpleCoder, 'call_llm')
    def test_llm_returns_none(self, mock_call_llm, coder):
        """Test handling when LLM returns None."""
        mock_call_llm.return_value = None

        result = coder.generate_fix(
            file_path="test.py",
            file_content="def foo(): pass",
            review_comment="Fix it",
            severity="low"
        )

        assert result.status == CoderStatus.SKIPPED

    @patch.object(SimpleCoder, 'call_llm')
    def test_llm_returns_empty_dict(self, mock_call_llm, coder):
        """Test handling when LLM returns empty dict."""
        mock_call_llm.return_value = {}

        result = coder.generate_fix(
            file_path="test.py",
            file_content="def foo(): pass",
            review_comment="Fix it",
            severity="low"
        )

        assert result.status == CoderStatus.SKIPPED

    @patch.object(SimpleCoder, 'call_llm')
    def test_llm_returns_missing_content_key(self, mock_call_llm, coder):
        """Test handling when LLM returns dict without content key."""
        mock_call_llm.return_value = {"response": "something"}

        result = coder.generate_fix(
            file_path="test.py",
            file_content="def foo(): pass",
            review_comment="Fix it",
            severity="low"
        )

        assert result.status == CoderStatus.SKIPPED


class TestSyntaxValidationEdgeCases:
    """Tests for edge cases in Python syntax validation."""

    def test_syntax_error_with_unicode(self):
        """Test syntax validation with unicode characters."""
        code = "def foo():\n    print('Hello \u4e16\u754c')"
        is_valid, error = validate_python_syntax(code)
        assert is_valid is True

    def test_syntax_error_with_invalid_unicode(self):
        """Test syntax validation with invalid syntax containing unicode."""
        code = "def foo(\n    print('\u4e16\u754c'"
        is_valid, error = validate_python_syntax(code)
        assert is_valid is False

    def test_syntax_error_indentation(self):
        """Test syntax validation catches indentation errors."""
        code = "def foo():\nprint('no indent')"
        is_valid, error = validate_python_syntax(code)
        assert is_valid is False
        assert error is not None

    def test_syntax_error_missing_colon(self):
        """Test syntax validation catches missing colon."""
        code = "def foo()\n    pass"
        is_valid, error = validate_python_syntax(code)
        assert is_valid is False

    def test_syntax_error_unmatched_brackets(self):
        """Test syntax validation catches unmatched brackets."""
        code = "def foo():\n    return [1, 2, 3"
        is_valid, error = validate_python_syntax(code)
        assert is_valid is False

    def test_syntax_error_unmatched_quotes(self):
        """Test syntax validation catches unmatched quotes."""
        code = "def foo():\n    return 'hello"
        is_valid, error = validate_python_syntax(code)
        assert is_valid is False

    def test_valid_complex_code(self):
        """Test syntax validation with complex valid code."""
        code = '''
import asyncio
from typing import Optional, List

class MyClass:
    """A docstring."""

    def __init__(self, value: int = 0):
        self.value = value

    async def async_method(self) -> List[int]:
        return [self.value * i for i in range(10)]

    @property
    def doubled(self) -> int:
        return self.value * 2

def decorator(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

@decorator
def my_func(x: Optional[int] = None) -> int:
    return x or 0
'''
        is_valid, error = validate_python_syntax(code)
        assert is_valid is True
        assert error is None

    def test_syntax_with_f_strings(self):
        """Test syntax validation with f-strings."""
        code = 'def foo(name):\n    return f"Hello, {name}!"'
        is_valid, error = validate_python_syntax(code)
        assert is_valid is True

    def test_syntax_with_walrus_operator(self):
        """Test syntax validation with walrus operator."""
        code = "if (n := len(items)) > 10:\n    print(n)"
        is_valid, error = validate_python_syntax(code)
        assert is_valid is True

    def test_syntax_with_match_statement(self):
        """Test syntax validation with match statement (Python 3.10+)."""
        code = '''
def handle(command):
    match command:
        case "quit":
            return False
        case "help":
            return True
        case _:
            return None
'''
        is_valid, error = validate_python_syntax(code)
        assert is_valid is True

    def test_only_comments(self):
        """Test syntax validation with only comments."""
        code = "# This is a comment\n# Another comment"
        is_valid, error = validate_python_syntax(code)
        assert is_valid is True

    def test_only_docstring(self):
        """Test syntax validation with only docstring."""
        code = '"""This is a module docstring."""'
        is_valid, error = validate_python_syntax(code)
        assert is_valid is True


class TestSingletonInitializationFailure:
    """Tests for singleton initialization failure handling."""

    @pytest.fixture(autouse=True)
    def reset_singleton_cache(self):
        """Reset the cached coder before and after each test.

        Uses autouse=True to ensure proper isolation without explicit calls.
        Saves and restores original value to avoid affecting other tests.
        """
        original_cached_coder = sc_module._CACHED_CODER
        sc_module._CACHED_CODER = None
        yield
        sc_module._CACHED_CODER = original_cached_coder

    def test_singleton_init_exception_not_cached(self):
        """Test that failed initialization doesn't cache a broken instance."""
        original_init = SimpleCoder.__init__
        call_count = [0]

        def failing_init(self, *args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise RuntimeError("Init failed")
            original_init(self, *args, **kwargs)

        with patch.object(SimpleCoder, '__init__', failing_init):
            with pytest.raises(RuntimeError):
                get_simple_coder()

            assert sc_module._CACHED_CODER is None

            coder = get_simple_coder()
            assert coder is not None
            assert isinstance(coder, SimpleCoder)

    def test_singleton_recovers_after_failure(self):
        """Test that singleton can recover after initialization failure."""
        original_init = SimpleCoder.__init__
        should_fail = [True]

        def conditional_init(self, *args, **kwargs):
            if should_fail[0]:
                raise ValueError("Temporary failure")
            original_init(self, *args, **kwargs)

        with patch.object(SimpleCoder, '__init__', conditional_init):
            with pytest.raises(ValueError):
                get_simple_coder()

            assert sc_module._CACHED_CODER is None

            should_fail[0] = False
            coder = get_simple_coder()
            assert coder is not None


class TestAutofixGateEdgeCases:
    """Tests for edge cases in autofix gate."""

    def test_none_review_outcome(self):
        """Test gate with None review_outcome."""
        assert is_autofix_allowed(None) is False

    def test_empty_review_outcome(self):
        """Test gate with empty review_outcome."""
        assert is_autofix_allowed({}) is False

    def test_missing_severity(self):
        """Test gate with missing severity field."""
        outcome = {
            "diff_truncated": False,
            "schema_validated": True
        }
        assert is_autofix_allowed(outcome) is False

    def test_missing_diff_truncated(self):
        """Test gate with missing diff_truncated field."""
        outcome = {
            "severity": "low",
            "schema_validated": True
        }
        assert is_autofix_allowed(outcome) is False

    def test_missing_schema_validated(self):
        """Test gate with missing schema_validated field."""
        outcome = {
            "severity": "low",
            "diff_truncated": False
        }
        assert is_autofix_allowed(outcome) is False

    def test_severity_case_insensitive(self):
        """Test that severity check is case-insensitive."""
        outcome = {
            "severity": "LOW",
            "diff_truncated": False,
            "schema_validated": True
        }
        assert is_autofix_allowed(outcome) is True

        outcome["severity"] = "Low"
        assert is_autofix_allowed(outcome) is True

    def test_severity_with_whitespace(self):
        """Test severity with leading/trailing whitespace."""
        outcome = {
            "severity": " low ",
            "diff_truncated": False,
            "schema_validated": True
        }
        assert is_autofix_allowed(outcome) is False

    def test_diff_truncated_truthy_values(self):
        """Test diff_truncated with various truthy values."""
        base_outcome = {
            "severity": "low",
            "schema_validated": True
        }

        base_outcome["diff_truncated"] = 1
        assert is_autofix_allowed(base_outcome) is False

        base_outcome["diff_truncated"] = "false"
        assert is_autofix_allowed(base_outcome) is False

        base_outcome["diff_truncated"] = []
        assert is_autofix_allowed(base_outcome) is False

    def test_schema_validated_falsy_values(self):
        """Test schema_validated with various falsy values."""
        base_outcome = {
            "severity": "low",
            "diff_truncated": False
        }

        base_outcome["schema_validated"] = 0
        assert is_autofix_allowed(base_outcome) is False

        base_outcome["schema_validated"] = ""
        assert is_autofix_allowed(base_outcome) is False

        base_outcome["schema_validated"] = None
        assert is_autofix_allowed(base_outcome) is False

    def test_path_exclusion_none(self):
        """Test path exclusion with None path."""
        assert is_path_excluded(None) is True

    def test_path_exclusion_empty_string(self):
        """Test path exclusion with empty string."""
        assert is_path_excluded("") is True

    def test_path_exclusion_whitespace_only(self):
        """Test path exclusion with whitespace-only path."""
        assert is_path_excluded("   ") is False

    def test_path_exclusion_case_sensitivity(self):
        """Test path exclusion case handling."""
        assert is_path_excluded("CONFIG/settings.py") is True
        assert is_path_excluded("Config/settings.py") is True
        assert is_path_excluded(".ENV") is True

    def test_path_exclusion_nested_paths(self):
        """Test path exclusion with deeply nested paths."""
        assert is_path_excluded("src/config/settings.py") is True
        assert is_path_excluded("deep/nested/config/file.py") is True
        assert is_path_excluded("src/migrations/001_initial.py") is True

    def test_path_exclusion_similar_names(self):
        """Test path exclusion doesn't match similar but different names."""
        assert is_path_excluded("src/configuration.py") is False
        assert is_path_excluded("src/migrate.py") is False
        assert is_path_excluded("src/env_utils.py") is False


class TestExecuteMethodEdgeCases:
    """Tests for edge cases in SimpleCoder.execute() method."""

    @pytest.fixture
    def coder(self):
        """Create a SimpleCoder instance."""
        return SimpleCoder()

    def test_execute_empty_file_path(self, coder):
        """Test execute with empty file_path."""
        input_data = AgentInput(
            task_id="test-001",
            prompt="Fix the code",
            context={
                "file_path": "",
                "file_content": "def foo(): pass",
                "review_comment": "Fix it",
                "severity": "low"
            }
        )

        output = coder.execute(input_data)
        assert output.success is False
        assert "missing" in output.error.lower()

    def test_execute_empty_file_content(self, coder):
        """Test execute with empty file_content."""
        input_data = AgentInput(
            task_id="test-001",
            prompt="Fix the code",
            context={
                "file_path": "test.py",
                "file_content": "",
                "review_comment": "Fix it",
                "severity": "low"
            }
        )

        output = coder.execute(input_data)
        assert output.success is False
        assert "missing" in output.error.lower()

    def test_execute_none_context(self, coder):
        """Test execute with None in context values."""
        input_data = AgentInput(
            task_id="test-001",
            prompt="Fix the code",
            context={
                "file_path": None,
                "file_content": None,
                "review_comment": "Fix it",
                "severity": "low"
            }
        )

        output = coder.execute(input_data)
        assert output.success is False

    @patch.object(SimpleCoder, 'call_llm')
    def test_execute_missing_review_comment(self, mock_call_llm, coder):
        """Test execute with missing review_comment (should use default)."""
        mock_call_llm.return_value = {
            "content": json.dumps({
                "status": "skipped",
                "reason": "No comment provided"
            })
        }

        input_data = AgentInput(
            task_id="test-001",
            prompt="Fix the code",
            context={
                "file_path": "test.py",
                "file_content": "def foo(): pass"
            }
        )

        output = coder.execute(input_data)
        assert output.data["status"] == "skipped"

    @patch.object(SimpleCoder, 'call_llm')
    def test_execute_missing_severity(self, mock_call_llm, coder):
        """Test execute with missing severity (should use default 'low')."""
        mock_call_llm.return_value = {
            "content": json.dumps({
                "status": "patch",
                "patch": "def foo():\n    pass"
            })
        }

        input_data = AgentInput(
            task_id="test-001",
            prompt="Fix the code",
            context={
                "file_path": "test.py",
                "file_content": "def foo(): pass",
                "review_comment": "Fix it"
            }
        )

        output = coder.execute(input_data)
        assert output.success is True


class TestCoderOutputEdgeCases:
    """Tests for edge cases in CoderOutput dataclass."""

    def test_to_dict_with_all_none_optional_fields(self):
        """Test to_dict when all optional fields are None."""
        output = CoderOutput(status=CoderStatus.SKIPPED)
        d = output.to_dict()

        assert "schema_version" in d
        assert d["status"] == "skipped"
        assert "reason" not in d
        assert "patch" not in d
        assert "file_path" not in d
        assert "syntax_valid" not in d

    def test_to_dict_with_false_syntax_valid(self):
        """Test to_dict includes syntax_valid when False."""
        output = CoderOutput(
            status=CoderStatus.PATCH,
            patch="def foo(): pass",
            syntax_valid=False
        )
        d = output.to_dict()

        assert d["syntax_valid"] is False

    def test_to_json_unicode(self):
        """Test to_json handles unicode correctly."""
        output = CoderOutput.create_skipped(
            reason="Unicode test: \u4e2d\u6587",
            file_path="test_\u6d4b\u8bd5.py"
        )
        j = output.to_json()

        assert "\u4e2d\u6587" in j or "\\u" in j

    def test_create_skipped_with_empty_reason(self):
        """Test create_skipped with empty reason."""
        output = CoderOutput.create_skipped("")
        assert output.status == CoderStatus.SKIPPED
        assert output.reason == ""

    def test_create_patch_with_multiline_content(self):
        """Test create_patch with multiline content."""
        patch = """def foo():
    '''Docstring.'''
    x = 1
    y = 2
    return x + y
"""
        output = CoderOutput.create_patch(patch, file_path="test.py", syntax_valid=True)
        assert output.patch == patch
        assert "\n" in output.patch
