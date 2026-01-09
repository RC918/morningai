"""
Tests for Syntax Safety Guardrail - Probe 3 Validation

Issue: EPIC D Probe 3 - Syntax Safety Guardrail
Purpose: Verify that validate_python_syntax() correctly catches invalid Python
         syntax and prevents bad commits from being made by the coder agents.

This test suite validates:
1. Basic syntax validation (valid/invalid code)
2. Complex Python syntax patterns that might confuse LLMs
3. Edge cases and boundary conditions
4. Integration with SimpleCoder and GeneralCoder

The syntax validation is the last line of defense before code is committed.
If an LLM generates syntactically invalid Python, this guardrail catches it.
"""
import json
import logging
import pytest
from unittest.mock import patch

from coder.simple_coder import (
    SimpleCoder,
    CoderStatus,
    validate_python_syntax,
    is_python_file,
)
from coder.general_coder import GeneralCoder


class TestSyntaxValidationBasic:
    """Basic syntax validation tests."""

    def test_valid_simple_function(self):
        """Simple function should pass."""
        code = "def hello(): pass"
        is_valid, error = validate_python_syntax(code)
        assert is_valid is True
        assert error is None

    def test_valid_class_definition(self):
        """Class definition should pass."""
        code = """
class Foo:
    def __init__(self):
        self.x = 1
"""
        is_valid, error = validate_python_syntax(code)
        assert is_valid is True
        assert error is None

    def test_invalid_unclosed_parenthesis(self):
        """Unclosed parenthesis should fail."""
        code = "def foo(x, y:"
        is_valid, error = validate_python_syntax(code)
        assert is_valid is False
        assert "SyntaxError" in error

    def test_invalid_unclosed_bracket(self):
        """Unclosed bracket should fail."""
        code = "x = [1, 2, 3"
        is_valid, error = validate_python_syntax(code)
        assert is_valid is False
        assert "SyntaxError" in error

    def test_invalid_unclosed_brace(self):
        """Unclosed brace should fail."""
        code = "x = {'a': 1, 'b': 2"
        is_valid, error = validate_python_syntax(code)
        assert is_valid is False
        assert "SyntaxError" in error

    def test_invalid_indentation(self):
        """Invalid indentation should fail."""
        code = """
def foo():
x = 1
"""
        is_valid, error = validate_python_syntax(code)
        assert is_valid is False
        assert "SyntaxError" in error


class TestSyntaxValidationComplexPatterns:
    """Tests for complex Python syntax patterns that might confuse LLMs."""

    def test_valid_nested_fstring(self):
        """Nested f-string should pass."""
        code = '''
def format_nested(outer, inner):
    return f"outer={{{outer}}} inner={{{inner}}}"
'''
        is_valid, error = validate_python_syntax(code)
        assert is_valid is True
        assert error is None

    def test_valid_quadruple_braces_fstring(self):
        """Quadruple braces in f-string should pass."""
        code = '''
def format_literal_braces(value):
    return f"value={{{{{value}}}}}"
'''
        is_valid, error = validate_python_syntax(code)
        assert is_valid is True
        assert error is None

    def test_invalid_unbalanced_fstring_braces(self):
        """Unbalanced braces in f-string should fail."""
        code = '''
def bad_fstring(x):
    return f"value={{{{x}}}"
'''
        is_valid, error = validate_python_syntax(code)
        assert is_valid is False
        assert "SyntaxError" in error

    def test_valid_walrus_operator(self):
        """Walrus operator should pass."""
        code = """
def process(items):
    return [(x, y) for item in items if (x := item.get('x')) and (y := x * 2)]
"""
        is_valid, error = validate_python_syntax(code)
        assert is_valid is True
        assert error is None

    def test_valid_match_case(self):
        """Match-case statement should pass (Python 3.10+)."""
        code = """
def parse_command(cmd):
    match cmd:
        case str(s) if s.startswith("!"):
            return f"command:{s[1:]}"
        case {"action": action, **rest}:
            return f"{action}:{rest}"
        case _:
            return "unknown"
"""
        is_valid, error = validate_python_syntax(code)
        assert is_valid is True
        assert error is None

    def test_valid_lambda_with_lambda_default(self):
        """Lambda with lambda default should pass."""
        code = """
nested_lambda = lambda f=lambda x: x: lambda y: f(y)
"""
        is_valid, error = validate_python_syntax(code)
        assert is_valid is True
        assert error is None

    def test_valid_complex_type_hints(self):
        """Complex type hints should pass."""
        code = """
from typing import Callable, Awaitable

def process(
    data: dict[str, list[tuple[int, str | None, bool]]],
    transform: Callable[[int], Awaitable[str]] | None = None,
) -> tuple[bool, list[str]]:
    return (True, [])
"""
        is_valid, error = validate_python_syntax(code)
        assert is_valid is True
        assert error is None

    def test_valid_async_comprehension(self):
        """Async comprehension should pass."""
        code = """
async def process(items):
    async def gen():
        for item in items:
            yield item
    return [x async for x in gen()]
"""
        is_valid, error = validate_python_syntax(code)
        assert is_valid is True
        assert error is None

    def test_valid_metaclass(self):
        """Metaclass definition should pass."""
        code = """
class Meta(type):
    def __new__(mcs, name, bases, namespace):
        return super().__new__(mcs, name, bases, namespace)

class Base(metaclass=Meta):
    __slots__ = ('_id',)
"""
        is_valid, error = validate_python_syntax(code)
        assert is_valid is True
        assert error is None

    def test_valid_decorator_chain(self):
        """Decorator chain should pass."""
        code = """
def decorator(arg):
    def inner(func):
        return func
    return inner

@decorator("test")
@decorator(
    arg="multi-line",
)
def decorated():
    pass
"""
        is_valid, error = validate_python_syntax(code)
        assert is_valid is True
        assert error is None

    def test_valid_raw_strings_with_escapes(self):
        """Raw strings with escapes should pass."""
        code = r'''
PATTERNS = {
    "escape": "\\n\\t\\r",
    "raw": r"\n\t\r",
    "regex": r"(?P<name>\w+)(?::\s*(?P<value>[^,]+))?",
}
'''
        is_valid, error = validate_python_syntax(code)
        assert is_valid is True
        assert error is None

    def test_valid_mixed_quotes(self):
        """Mixed quote types should pass."""
        code = """
QUOTES = {
    "single": 'value with "double" quotes',
    "double": "value with 'single' quotes",
    "triple": '''multi
    line''',
    "escaped": "escaped \\"double\\" quotes",
}
"""
        is_valid, error = validate_python_syntax(code)
        assert is_valid is True
        assert error is None


class TestSyntaxValidationEdgeCases:
    """Edge cases and boundary conditions."""

    def test_empty_string(self):
        """Empty string should pass."""
        is_valid, error = validate_python_syntax("")
        assert is_valid is True
        assert error is None

    def test_whitespace_only(self):
        """Whitespace only should pass."""
        is_valid, error = validate_python_syntax("   \n\t\n   ")
        assert is_valid is True
        assert error is None

    def test_comment_only(self):
        """Comment only should pass."""
        is_valid, error = validate_python_syntax("# This is a comment")
        assert is_valid is True
        assert error is None

    def test_docstring_only(self):
        """Docstring only should pass."""
        is_valid, error = validate_python_syntax('"""This is a docstring."""')
        assert is_valid is True
        assert error is None

    def test_unicode_identifiers(self):
        """Unicode identifiers should pass."""
        code = """
def 计算(数值):
    return 数值 * 2
"""
        is_valid, error = validate_python_syntax(code)
        assert is_valid is True
        assert error is None

    def test_very_long_line(self):
        """Very long line should pass."""
        code = f"x = {'a' * 10000!r}"
        is_valid, error = validate_python_syntax(code)
        assert is_valid is True
        assert error is None

    def test_deeply_nested_structure(self):
        """Deeply nested structure should pass."""
        code = "x = " + "[[" * 50 + "1" + "]]" * 50
        is_valid, error = validate_python_syntax(code)
        assert is_valid is True
        assert error is None

    def test_error_includes_line_number(self):
        """Error message should include line number."""
        code = """
def foo():
    pass

def bar(
    x = 1
"""
        is_valid, error = validate_python_syntax(code, "test.py")
        assert is_valid is False
        assert "line" in error.lower()

    def test_error_includes_error_message(self):
        """Error message should include the actual error."""
        code = "def foo( pass"
        is_valid, error = validate_python_syntax(code)
        assert is_valid is False
        assert error is not None
        assert len(error) > 10  # Should have meaningful error message


class TestSyntaxValidationLLMFailureModes:
    """Tests for common LLM failure modes that syntax validation should catch."""

    def test_catches_truncated_code(self):
        """Should catch truncated code (common LLM failure)."""
        code = """
def process_data(items):
    results = []
    for item in items:
        if item.is_valid():
            results.append(
"""
        is_valid, error = validate_python_syntax(code)
        assert is_valid is False
        assert "SyntaxError" in error

    def test_catches_mixed_indentation(self):
        """Should catch mixed tabs/spaces (common LLM failure)."""
        code = "def foo():\n\tif True:\n        pass"  # Mixed tab and spaces
        is_valid, error = validate_python_syntax(code)
        assert is_valid is False
        # Python 3.12+ reports this as SyntaxError with "inconsistent use of tabs and spaces"
        # Earlier versions report it as TabError
        assert "TabError" in error or "inconsistent use of tabs and spaces" in error

    def test_catches_incomplete_string(self):
        """Should catch incomplete string literal."""
        code = 'x = "hello'
        is_valid, error = validate_python_syntax(code)
        assert is_valid is False
        assert "SyntaxError" in error

    def test_catches_incomplete_fstring(self):
        """Should catch incomplete f-string."""
        code = 'x = f"hello {name'
        is_valid, error = validate_python_syntax(code)
        assert is_valid is False
        assert "SyntaxError" in error

    def test_catches_invalid_escape_sequence(self):
        """Should catch invalid escape sequence that is a SyntaxError."""
        # An unterminated unicode escape like '\u' is a hard SyntaxError.
        code = "'\\u'"
        is_valid, error = validate_python_syntax(code)
        assert is_valid is False
        assert "SyntaxError" in error

    def test_catches_mismatched_brackets(self):
        """Should catch mismatched brackets."""
        code = "x = [1, 2, 3)"
        is_valid, error = validate_python_syntax(code)
        assert is_valid is False
        assert "SyntaxError" in error


class TestSimpleCoderSyntaxIntegration:
    """Integration tests for SimpleCoder syntax validation."""

    @pytest.fixture
    def coder(self):
        """Create a SimpleCoder instance."""
        return SimpleCoder()

    @patch.object(SimpleCoder, 'call_llm')
    def test_rejects_invalid_syntax_patch(self, mock_call_llm, coder):
        """SimpleCoder should reject patches with invalid syntax."""
        mock_call_llm.return_value = {
            "content": json.dumps({
                "status": "patch",
                "patch": "def foo(\n    pass"  # Invalid syntax
            })
        }

        result = coder.generate_fix(
            file_path="test.py",
            file_content="def foo(): pass",
            review_comment="Add docstring",
            severity="low"
        )

        assert result.status == CoderStatus.SKIPPED
        assert "Syntax check failed" in result.reason

    @patch.object(SimpleCoder, 'call_llm')
    def test_accepts_valid_complex_syntax(self, mock_call_llm, coder):
        """SimpleCoder should accept valid complex syntax."""
        complex_code = '''
def format_nested(outer, inner):
    """Format with nested f-string."""
    return f"outer={{{outer}}} inner={{{inner}}}"
'''
        mock_call_llm.return_value = {
            "content": json.dumps({
                "status": "patch",
                "patch": complex_code
            })
        }

        result = coder.generate_fix(
            file_path="test.py",
            file_content="def foo(): pass",
            review_comment="Add complex formatting",
            severity="low"
        )

        assert result.status == CoderStatus.PATCH
        assert result.syntax_valid is True

    @patch.object(SimpleCoder, 'call_llm')
    def test_logs_syntax_abort_event(self, mock_call_llm, coder, caplog):
        """SimpleCoder should log [CODER_SYNTAX_ABORT] event."""
        mock_call_llm.return_value = {
            "content": json.dumps({
                "status": "patch",
                "patch": "def foo( pass"  # Invalid syntax
            })
        }

        with caplog.at_level(logging.WARNING):
            result = coder.generate_fix(
                file_path="test.py",
                file_content="def foo(): pass",
                review_comment="Fix it",
                severity="low"
            )

        assert result.status == CoderStatus.SKIPPED
        assert any("[CODER_SYNTAX_ABORT]" in record.message for record in caplog.records)


class TestGeneralCoderSyntaxIntegration:
    """Integration tests for GeneralCoder syntax validation."""

    @pytest.fixture
    def coder(self):
        """Create a GeneralCoder instance."""
        return GeneralCoder()

    @patch.object(GeneralCoder, 'call_llm')
    def test_rejects_invalid_syntax_in_multi_file(self, mock_call_llm, coder):
        """GeneralCoder should reject patches with invalid syntax in any file."""
        mock_call_llm.return_value = {
            "content": json.dumps({
                "status": "patch",
                "patches": [
                    {"file_path": "valid.py", "patch": "def foo(): pass"},
                    {"file_path": "invalid.py", "patch": "def bar( pass"},  # Invalid
                ]
            })
        }

        result = coder.generate_multi_file_fix(
            files=[
                {"path": "valid.py", "content": "# valid"},
                {"path": "invalid.py", "content": "# invalid"},
            ],
            review_comment="Fix both files",
            severity="low"
        )

        assert result.status == CoderStatus.SKIPPED
        assert "Syntax check failed" in result.reason

    @patch.object(GeneralCoder, 'call_llm')
    def test_accepts_all_valid_syntax(self, mock_call_llm, coder):
        """GeneralCoder should accept when all files have valid syntax."""
        mock_call_llm.return_value = {
            "content": json.dumps({
                "status": "patch",
                "patches": [
                    {"file_path": "a.py", "patch": "def foo(): pass"},
                    {"file_path": "b.py", "patch": "def bar(): pass"},
                ]
            })
        }

        result = coder.generate_multi_file_fix(
            files=[
                {"path": "a.py", "content": "# a"},
                {"path": "b.py", "content": "# b"},
            ],
            review_comment="Fix both files",
            severity="low"
        )

        assert result.status == CoderStatus.PATCH
        assert len(result.patches) == 2
        assert all(p.syntax_valid is True for p in result.patches)

    @patch.object(GeneralCoder, 'call_llm')
    def test_logs_syntax_abort_event_multi_file(self, mock_call_llm, coder, caplog):
        """GeneralCoder should log [GENERAL_CODER_SYNTAX_ABORT] event."""
        mock_call_llm.return_value = {
            "content": json.dumps({
                "status": "patch",
                "patches": [
                    {"file_path": "bad.py", "patch": "def foo( pass"},
                ]
            })
        }

        with caplog.at_level(logging.WARNING):
            result = coder.generate_multi_file_fix(
                files=[{"path": "bad.py", "content": "# bad"}],
                review_comment="Fix it",
                severity="low"
            )

        assert result.status == CoderStatus.SKIPPED
        assert any("[GENERAL_CODER_SYNTAX_ABORT]" in record.message for record in caplog.records)


class TestIsPythonFile:
    """Tests for is_python_file helper function."""

    def test_python_extensions(self):
        """Should detect .py files."""
        assert is_python_file("test.py") is True
        assert is_python_file("src/utils.py") is True
        assert is_python_file("/absolute/path/module.py") is True

    def test_case_insensitive(self):
        """Should be case insensitive."""
        assert is_python_file("TEST.PY") is True
        assert is_python_file("Test.Py") is True
        assert is_python_file("test.PY") is True

    def test_non_python_files(self):
        """Should not detect non-Python files."""
        assert is_python_file("test.js") is False
        assert is_python_file("test.ts") is False
        assert is_python_file("test.java") is False
        assert is_python_file("test.pyc") is False
        assert is_python_file("test.pyx") is False
        assert is_python_file("test.pyi") is False
        assert is_python_file("Makefile") is False
        assert is_python_file("requirements.txt") is False
