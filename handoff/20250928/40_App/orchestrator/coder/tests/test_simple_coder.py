"""
Tests for SimpleCoder Agent - D-1 Phase 0

Issue #3211: D-1.1 Coder Three Don'ts Safety Guardrails
"""
import json
import pytest
from unittest.mock import patch

from coder.simple_coder import (
    SimpleCoder,
    CoderOutput,
    CoderStatus,
    validate_python_syntax,
    is_python_file,
    get_simple_coder,
)
from core.agents import AgentInput


class TestCoderOutput:
    """Tests for CoderOutput dataclass."""

    def test_skipped_output(self):
        """Test creating a skipped output."""
        output = CoderOutput.create_skipped("Not confident", file_path="test.py")
        assert output.status == CoderStatus.SKIPPED
        assert output.reason == "Not confident"
        assert output.patch is None
        assert output.file_path == "test.py"

    def test_patch_output(self):
        """Test creating a patch output."""
        output = CoderOutput.create_patch(
            patch_content="def foo(): pass",
            file_path="test.py",
            syntax_valid=True
        )
        assert output.status == CoderStatus.PATCH
        assert output.patch == "def foo(): pass"
        assert output.reason is None
        assert output.file_path == "test.py"
        assert output.syntax_valid is True

    def test_to_dict_skipped(self):
        """Test to_dict for skipped output."""
        output = CoderOutput.create_skipped("Reason", file_path="test.py")
        d = output.to_dict()
        assert d["status"] == "skipped"
        assert d["reason"] == "Reason"
        assert "patch" not in d
        assert d["file_path"] == "test.py"

    def test_to_dict_patch(self):
        """Test to_dict for patch output."""
        output = CoderOutput.create_patch("code", file_path="test.py", syntax_valid=True)
        d = output.to_dict()
        assert d["status"] == "patch"
        assert d["patch"] == "code"
        assert "reason" not in d
        assert d["file_path"] == "test.py"
        assert d["syntax_valid"] is True

    def test_to_json(self):
        """Test to_json serialization."""
        output = CoderOutput.create_skipped("Reason")
        j = output.to_json()
        parsed = json.loads(j)
        assert parsed["status"] == "skipped"
        assert parsed["reason"] == "Reason"


class TestValidatePythonSyntax:
    """Tests for validate_python_syntax function."""

    def test_valid_python_code(self):
        """Valid Python code should pass."""
        code = """
def hello():
    print("Hello, World!")

class Foo:
    def __init__(self):
        self.x = 1
"""
        is_valid, error = validate_python_syntax(code)
        assert is_valid is True
        assert error is None

    def test_invalid_python_code(self):
        """Invalid Python code should fail."""
        code = """
def hello(
    print("Missing closing paren"
"""
        is_valid, error = validate_python_syntax(code)
        assert is_valid is False
        assert error is not None
        assert "SyntaxError" in error

    def test_empty_code(self):
        """Empty code should pass (valid Python)."""
        is_valid, error = validate_python_syntax("")
        assert is_valid is True
        assert error is None

    def test_syntax_error_with_line_number(self):
        """Syntax error should include line number."""
        code = "def foo(\n    x = 1"
        is_valid, error = validate_python_syntax(code, "test.py")
        assert is_valid is False
        assert "line" in error.lower()


class TestIsPythonFile:
    """Tests for is_python_file function."""

    def test_python_files(self):
        """Python files should be detected."""
        assert is_python_file("test.py") is True
        assert is_python_file("src/utils.py") is True
        assert is_python_file("TEST.PY") is True
        assert is_python_file("module.Py") is True

    def test_non_python_files(self):
        """Non-Python files should not be detected."""
        assert is_python_file("test.js") is False
        assert is_python_file("test.ts") is False
        assert is_python_file("test.java") is False
        assert is_python_file("test.pyc") is False
        assert is_python_file("test.pyx") is False


class TestSimpleCoder:
    """Tests for SimpleCoder class."""

    @pytest.fixture
    def coder(self):
        """Create a SimpleCoder instance."""
        return SimpleCoder()

    def test_init(self, coder):
        """Test SimpleCoder initialization."""
        assert coder.agent_id == "simple_coder"

    @patch.object(SimpleCoder, 'call_llm')
    def test_generate_fix_skipped(self, mock_call_llm, coder):
        """Test generate_fix when LLM returns skipped."""
        mock_call_llm.return_value = {
            "content": json.dumps({
                "status": "skipped",
                "reason": "Complex logic change required"
            })
        }

        result = coder.generate_fix(
            file_path="test.py",
            file_content="def foo(): pass",
            review_comment="Refactor this function",
            severity="low"
        )

        assert result.status == CoderStatus.SKIPPED
        assert "Complex logic" in result.reason

    @patch.object(SimpleCoder, 'call_llm')
    def test_generate_fix_patch_valid_syntax(self, mock_call_llm, coder):
        """Test generate_fix when LLM returns valid patch."""
        mock_call_llm.return_value = {
            "content": json.dumps({
                "status": "patch",
                "patch": "def foo():\n    '''Docstring.'''\n    pass"
            })
        }

        result = coder.generate_fix(
            file_path="test.py",
            file_content="def foo(): pass",
            review_comment="Add docstring",
            severity="low"
        )

        assert result.status == CoderStatus.PATCH
        assert "Docstring" in result.patch
        assert result.syntax_valid is True

    @patch.object(SimpleCoder, 'call_llm')
    def test_generate_fix_patch_invalid_syntax(self, mock_call_llm, coder):
        """Test generate_fix when LLM returns invalid syntax."""
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

        # Should be skipped due to syntax error
        assert result.status == CoderStatus.SKIPPED
        assert "Syntax check failed" in result.reason

    @patch.object(SimpleCoder, 'call_llm')
    def test_generate_fix_non_python_no_syntax_check(self, mock_call_llm, coder):
        """Test that non-Python files skip syntax check."""
        mock_call_llm.return_value = {
            "content": json.dumps({
                "status": "patch",
                "patch": "function foo() { return 1; }"
            })
        }

        result = coder.generate_fix(
            file_path="test.js",
            file_content="function foo() {}",
            review_comment="Add return",
            severity="low"
        )

        assert result.status == CoderStatus.PATCH
        assert result.syntax_valid is None  # No syntax check for JS

    @patch.object(SimpleCoder, 'call_llm')
    def test_generate_fix_invalid_json(self, mock_call_llm, coder):
        """Test generate_fix when LLM returns invalid JSON."""
        mock_call_llm.return_value = {
            "content": "This is not JSON"
        }

        result = coder.generate_fix(
            file_path="test.py",
            file_content="def foo(): pass",
            review_comment="Fix it",
            severity="low"
        )

        assert result.status == CoderStatus.SKIPPED
        assert "JSON" in result.reason

    @patch.object(SimpleCoder, 'call_llm')
    def test_generate_fix_llm_error(self, mock_call_llm, coder):
        """Test generate_fix when LLM call fails."""
        mock_call_llm.side_effect = Exception("API Error")

        result = coder.generate_fix(
            file_path="test.py",
            file_content="def foo(): pass",
            review_comment="Fix it",
            severity="low"
        )

        assert result.status == CoderStatus.SKIPPED
        assert "LLM call failed" in result.reason

    @patch.object(SimpleCoder, 'call_llm')
    def test_execute_success(self, mock_call_llm, coder):
        """Test execute method with successful patch."""
        mock_call_llm.return_value = {
            "content": json.dumps({
                "status": "patch",
                "patch": "def foo():\n    pass"
            })
        }

        input = AgentInput(
            task_id="test-001",
            prompt="Fix the code",
            context={
                "file_path": "test.py",
                "file_content": "def foo(): pass",
                "review_comment": "Add newline",
                "severity": "low"
            }
        )

        output = coder.execute(input)

        assert output.success is True
        assert output.data["status"] == "patch"

    def test_execute_missing_context(self, coder):
        """Test execute method with missing context."""
        input = AgentInput(
            task_id="test-001",
            prompt="Fix the code",
            context={}
        )

        output = coder.execute(input)

        assert output.success is False
        assert "Missing" in output.error


class TestGetSimpleCoder:
    """Tests for get_simple_coder factory function."""

    def test_returns_simple_coder(self):
        """Factory should return SimpleCoder instance."""
        coder = get_simple_coder()
        assert isinstance(coder, SimpleCoder)

    def test_returns_cached_instance(self):
        """Factory should return cached instance."""
        coder1 = get_simple_coder()
        coder2 = get_simple_coder()
        assert coder1 is coder2
