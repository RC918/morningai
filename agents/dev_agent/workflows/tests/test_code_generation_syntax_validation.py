#!/usr/bin/env python3
"""
Unit tests for CodeGenerationWorkflow syntax validation and retry mechanism.
Issue #3697: P7 - Add syntax validation for LLM-generated code

Tests cover:
1. _validate_python_syntax() - valid/invalid code detection
2. _regenerate_code_with_syntax_feedback() - retry prompt generation
3. apply_code() retry loop - success, failure, LLM unavailable cases
4. State mutation verification
"""
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, AsyncMock

from workflows.code_generation_workflow import CodeGenerationWorkflow


@pytest.fixture
def workflow():
    """Create a CodeGenerationWorkflow instance for testing"""
    mock_dev_agent = Mock()
    mock_dev_agent.llm = None
    with tempfile.TemporaryDirectory() as tmpdir:
        workflow = CodeGenerationWorkflow(mock_dev_agent)
        workflow.repo_root = tmpdir
        yield workflow


@pytest.fixture
def workflow_with_llm():
    """Create a CodeGenerationWorkflow instance with mock LLM for testing"""
    mock_dev_agent = Mock()
    mock_dev_agent.llm = AsyncMock()
    with tempfile.TemporaryDirectory() as tmpdir:
        workflow = CodeGenerationWorkflow(mock_dev_agent)
        workflow.repo_root = tmpdir
        yield workflow


class TestValidatePythonSyntax:
    """Test _validate_python_syntax() method"""

    def test_valid_python_code_returns_true(self, workflow):
        """Test that valid Python code passes validation"""
        valid_code = '''
def hello_world():
    print("Hello, World!")
    return True

class MyClass:
    def __init__(self):
        self.value = 42
'''
        is_valid, error_msg = workflow._validate_python_syntax(valid_code, "test.py")
        assert is_valid is True
        assert error_msg is None

    def test_invalid_python_syntax_returns_false(self, workflow):
        """Test that invalid Python syntax fails validation"""
        invalid_code = '''
def broken_function(
    print("Missing closing parenthesis"
'''
        is_valid, error_msg = workflow._validate_python_syntax(invalid_code, "test.py")
        assert is_valid is False
        assert error_msg is not None
        assert "invalid Python syntax" in error_msg

    def test_syntax_error_includes_line_number(self, workflow):
        """Test that syntax error message includes line number"""
        invalid_code = '''
def valid_line():
    pass

def broken_line(
    x = 1
'''
        is_valid, error_msg = workflow._validate_python_syntax(invalid_code, "test.py")
        assert is_valid is False
        assert "line" in error_msg.lower()

    def test_syntax_error_includes_erroneous_line_text(self, workflow):
        """Test that syntax error message includes the erroneous line (e.text)

        Issue #3697: gemini-code-assist suggestion to include e.text
        """
        invalid_code = '''x = 1
y = 2
z = (3 + 4
'''
        is_valid, error_msg = workflow._validate_python_syntax(invalid_code, "test.py")
        assert is_valid is False
        assert "Erroneous line:" in error_msg

    def test_empty_code_is_valid(self, workflow):
        """Test that empty code is valid Python"""
        is_valid, error_msg = workflow._validate_python_syntax("", "test.py")
        assert is_valid is True
        assert error_msg is None

    def test_conversational_text_fails_validation(self, workflow):
        """Test that LLM conversational text fails validation

        Issue #3629: Prevent writing invalid LLM output to disk
        """
        conversational_text = '''
As an AI language model, I need to see the full context of your code
before I can help you. Please provide the following:
1. The complete file contents
2. Any error messages you're seeing
'''
        is_valid, error_msg = workflow._validate_python_syntax(
            conversational_text, "test.py"
        )
        assert is_valid is False


class TestRegenerateCodeWithSyntaxFeedback:
    """Test _regenerate_code_with_syntax_feedback() method"""

    @pytest.mark.asyncio
    async def test_returns_none_when_llm_unavailable(self, workflow):
        """Test that method returns None when LLM is not available"""
        state = {
            "task_id": 123,
            "task_type": "bug_fix",
            "task_description": "Fix the bug",
            "target_files": ["test.py"],
            "generated_code": "invalid code",
        }
        result = await workflow._regenerate_code_with_syntax_feedback(
            state, "syntax error at line 1", attempt=1
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_calls_llm_with_retry_prompt(self, workflow_with_llm):
        """Test that method calls LLM with proper retry prompt"""
        workflow_with_llm.agent.llm.generate = AsyncMock(
            return_value="def fixed_code(): pass"
        )
        workflow_with_llm._extract_code_from_response = Mock(
            return_value="def fixed_code(): pass"
        )

        state = {
            "task_id": 123,
            "task_type": "bug_fix",
            "task_description": "Fix the bug",
            "target_files": ["test.py"],
            "generated_code": "def broken(: pass",
        }

        result = await workflow_with_llm._regenerate_code_with_syntax_feedback(
            state, "syntax error: invalid syntax at line 1", attempt=1
        )

        assert result is not None
        workflow_with_llm.agent.llm.generate.assert_called_once()
        call_args = workflow_with_llm.agent.llm.generate.call_args[0][0]
        assert "SYNTAX ERROR" in call_args
        assert "syntax error: invalid syntax at line 1" in call_args

    @pytest.mark.asyncio
    async def test_returns_none_on_llm_exception(self, workflow_with_llm):
        """Test that method returns None when LLM raises exception"""
        workflow_with_llm.agent.llm.generate = AsyncMock(
            side_effect=Exception("LLM API error")
        )

        state = {
            "task_id": 123,
            "task_type": "bug_fix",
            "task_description": "Fix the bug",
            "target_files": ["test.py"],
            "generated_code": "invalid code",
        }

        result = await workflow_with_llm._regenerate_code_with_syntax_feedback(
            state, "syntax error", attempt=1
        )
        assert result is None


class TestApplyCodeRetryMechanism:
    """Test apply_code() retry mechanism for syntax validation"""

    @pytest.mark.asyncio
    async def test_valid_code_applied_without_retry(self, workflow):
        """Test that valid code is applied without triggering retry"""
        target_file = Path(workflow.repo_root) / "test.py"
        target_file.write_text("# original")

        state = {
            "task_id": 123,
            "generated_code": "def hello(): pass",
            "target_files": [str(target_file)],
            "task_metadata": None,
        }

        result = await workflow.apply_code(state)

        assert "error" not in result or result.get("error") is None
        assert target_file.read_text() == "def hello(): pass"

    @pytest.mark.asyncio
    async def test_invalid_code_triggers_retry(self, workflow_with_llm):
        """Test that invalid code triggers retry mechanism"""
        target_file = Path(workflow_with_llm.repo_root) / "test.py"
        target_file.write_text("# original")

        workflow_with_llm.agent.llm.generate = AsyncMock(
            return_value="def fixed(): pass"
        )
        workflow_with_llm._extract_code_from_response = Mock(
            return_value="def fixed(): pass"
        )

        state = {
            "task_id": 123,
            "generated_code": "def broken(: pass",
            "target_files": [str(target_file)],
            "task_metadata": None,
        }

        result = await workflow_with_llm.apply_code(state)

        assert result.get("error") is None
        assert result["generated_code"] == "def fixed(): pass"
        assert target_file.read_text() == "def fixed(): pass"

    @pytest.mark.asyncio
    async def test_retry_exhausted_returns_error(self, workflow_with_llm):
        """Test that exhausted retries return error"""
        target_file = Path(workflow_with_llm.repo_root) / "test.py"
        target_file.write_text("# original")

        workflow_with_llm.agent.llm.generate = AsyncMock(
            return_value="still broken(: code"
        )
        workflow_with_llm._extract_code_from_response = Mock(
            return_value="still broken(: code"
        )

        state = {
            "task_id": 123,
            "generated_code": "def broken(: pass",
            "target_files": [str(target_file)],
            "task_metadata": None,
        }

        result = await workflow_with_llm.apply_code(state)

        assert result.get("error") is not None
        assert "invalid Python syntax" in result["error"]
        assert target_file.read_text() == "# original"

    @pytest.mark.asyncio
    async def test_llm_unavailable_fails_gracefully(self, workflow):
        """Test that LLM unavailable fails gracefully without infinite loop"""
        target_file = Path(workflow.repo_root) / "test.py"
        target_file.write_text("# original")

        state = {
            "task_id": 123,
            "generated_code": "def broken(: pass",
            "target_files": [str(target_file)],
            "task_metadata": None,
        }

        result = await workflow.apply_code(state)

        assert result.get("error") is not None
        assert target_file.read_text() == "# original"

    @pytest.mark.asyncio
    async def test_state_updated_on_successful_retry(self, workflow_with_llm):
        """Test that state['generated_code'] is updated on successful retry"""
        target_file = Path(workflow_with_llm.repo_root) / "test.py"
        target_file.write_text("# original")

        workflow_with_llm.agent.llm.generate = AsyncMock(
            return_value="def fixed_function(): return 42"
        )
        workflow_with_llm._extract_code_from_response = Mock(
            return_value="def fixed_function(): return 42"
        )

        state = {
            "task_id": 123,
            "generated_code": "def broken(: pass",
            "target_files": [str(target_file)],
            "task_metadata": None,
        }

        original_code = state["generated_code"]
        result = await workflow_with_llm.apply_code(state)

        assert result["generated_code"] != original_code
        assert result["generated_code"] == "def fixed_function(): return 42"

    @pytest.mark.asyncio
    async def test_max_retry_attempts_respected(self, workflow_with_llm):
        """Test that MAX_SYNTAX_RETRY_ATTEMPTS is respected"""
        target_file = Path(workflow_with_llm.repo_root) / "test.py"
        target_file.write_text("# original")

        call_count = 0

        async def mock_generate(prompt):
            nonlocal call_count
            call_count += 1
            return "still broken(: code"

        workflow_with_llm.agent.llm.generate = mock_generate
        workflow_with_llm._extract_code_from_response = Mock(
            return_value="still broken(: code"
        )

        state = {
            "task_id": 123,
            "generated_code": "def broken(: pass",
            "target_files": [str(target_file)],
            "task_metadata": None,
        }

        await workflow_with_llm.apply_code(state)

        assert call_count == workflow_with_llm.MAX_SYNTAX_RETRY_ATTEMPTS

    @pytest.mark.asyncio
    async def test_non_python_files_skip_validation(self, workflow):
        """Test that non-Python files skip syntax validation"""
        target_file = Path(workflow.repo_root) / "config.json"
        target_file.write_text("{}")

        state = {
            "task_id": 123,
            "generated_code": '{"key": "value"}',
            "target_files": [str(target_file)],
            "task_metadata": None,
        }

        result = await workflow.apply_code(state)

        assert result.get("error") is None
        assert target_file.read_text() == '{"key": "value"}'


class TestEventCodes:
    """Test greppable event codes for observability"""

    def test_coder_syntax_error_logged(self, workflow, caplog):
        """Test that [CODER_SYNTAX_ERROR] is logged on syntax error"""
        import logging
        caplog.set_level(logging.ERROR)

        invalid_code = "def broken(: pass"
        workflow._validate_python_syntax(invalid_code, "test.py")

        assert any("[CODER_SYNTAX_ERROR]" in record.message for record in caplog.records)

    @pytest.mark.asyncio
    async def test_coder_syntax_retry_logged(self, workflow_with_llm, caplog):
        """Test that [CODER_SYNTAX_RETRY] is logged on retry attempt"""
        import logging
        caplog.set_level(logging.INFO)

        workflow_with_llm.agent.llm.generate = AsyncMock(
            return_value="def fixed(): pass"
        )
        workflow_with_llm._extract_code_from_response = Mock(
            return_value="def fixed(): pass"
        )

        state = {
            "task_id": 123,
            "task_type": "bug_fix",
            "task_description": "Fix bug",
            "target_files": ["test.py"],
            "generated_code": "invalid",
        }

        await workflow_with_llm._regenerate_code_with_syntax_feedback(
            state, "syntax error", attempt=1
        )

        assert any("[CODER_SYNTAX_RETRY]" in record.message for record in caplog.records)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
