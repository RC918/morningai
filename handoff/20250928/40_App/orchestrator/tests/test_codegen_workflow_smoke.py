"""
Smoke Tests for Code Generation Workflow

Phase 0-Lite Supplement: Basic smoke tests for CodeGenerationWorkflow
Tests workflow structure and security validation without external dependencies
"""
import pytest
from unittest.mock import Mock, patch
import re
import sys
import os

# Add agents directory to path
agents_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))), 'agents')
if agents_path not in sys.path:
    sys.path.insert(0, agents_path)

try:
    from dev_agent.workflows.code_generation_workflow import CodeGenerationWorkflow
    CODEGEN_AVAILABLE = True
except ImportError:
    CODEGEN_AVAILABLE = False
    CodeGenerationWorkflow = None


@pytest.mark.skipif(not CODEGEN_AVAILABLE, reason="CodeGenerationWorkflow not available")
class TestCodeGenerationWorkflowStructure:
    """Test CodeGenerationWorkflow class structure"""

    def test_dangerous_patterns_defined(self):
        """Test that dangerous patterns are properly defined"""
        patterns = CodeGenerationWorkflow.DANGEROUS_PATTERNS

        assert len(patterns) > 0
        assert any('eval' in p for p in patterns)
        assert any('exec' in p for p in patterns)
        assert any('DROP' in p for p in patterns)

    @patch('dev_agent.workflows.code_generation_workflow.TaskClassifier')
    @patch('dev_agent.workflows.code_generation_workflow.LLMTestGenerator')
    def test_workflow_initialization(self, mock_test_gen, mock_classifier):
        """Test CodeGenerationWorkflow can be initialized"""
        mock_dev_agent = Mock()
        mock_dev_agent.llm = Mock()

        workflow = CodeGenerationWorkflow(mock_dev_agent)

        assert workflow.agent == mock_dev_agent
        assert workflow.classifier is not None
        assert workflow.test_generator is not None
        assert workflow.workflow is not None


@pytest.mark.skipif(not CODEGEN_AVAILABLE, reason="CodeGenerationWorkflow not available")
class TestSecurityValidation:
    """Test security validation methods"""

    @patch('dev_agent.workflows.code_generation_workflow.TaskClassifier')
    @patch('dev_agent.workflows.code_generation_workflow.LLMTestGenerator')
    def test_is_safe_file_path_relative(self, mock_test_gen, mock_classifier):
        """Test _is_safe_file_path accepts safe relative paths"""
        mock_dev_agent = Mock()
        workflow = CodeGenerationWorkflow(mock_dev_agent)

        # Safe relative path
        assert workflow._is_safe_file_path("src/utils/helper.py") is True

    @patch('dev_agent.workflows.code_generation_workflow.TaskClassifier')
    @patch('dev_agent.workflows.code_generation_workflow.LLMTestGenerator')
    def test_is_safe_file_path_blocks_traversal(self, mock_test_gen, mock_classifier):
        """Test _is_safe_file_path blocks directory traversal"""
        mock_dev_agent = Mock()
        workflow = CodeGenerationWorkflow(mock_dev_agent)

        # Directory traversal attempt
        assert workflow._is_safe_file_path("../../etc/passwd") is False

    @patch('dev_agent.workflows.code_generation_workflow.TaskClassifier')
    @patch('dev_agent.workflows.code_generation_workflow.LLMTestGenerator')
    def test_is_safe_file_path_blocks_git_directory(self, mock_test_gen, mock_classifier):
        """Test _is_safe_file_path blocks .git directory"""
        mock_dev_agent = Mock()
        workflow = CodeGenerationWorkflow(mock_dev_agent)

        # .git directory access
        assert workflow._is_safe_file_path(".git/config") is False


@pytest.mark.skipif(not CODEGEN_AVAILABLE, reason="CodeGenerationWorkflow not available")
class TestFilePathExtraction:
    """Test file path extraction"""

    @patch('dev_agent.workflows.code_generation_workflow.TaskClassifier')
    @patch('dev_agent.workflows.code_generation_workflow.LLMTestGenerator')
    def test_extract_file_paths_from_backticks(self, mock_test_gen, mock_classifier):
        """Test _extract_file_paths extracts paths from backticks"""
        mock_dev_agent = Mock()
        workflow = CodeGenerationWorkflow(mock_dev_agent)

        text = "Please update `src/utils/helper.py` and `tests/test_helper.py`"
        paths = workflow._extract_file_paths(text)

        assert "src/utils/helper.py" in paths
        assert "tests/test_helper.py" in paths

    @patch('dev_agent.workflows.code_generation_workflow.TaskClassifier')
    @patch('dev_agent.workflows.code_generation_workflow.LLMTestGenerator')
    def test_extract_file_paths_from_plain_text(self, mock_test_gen, mock_classifier):
        """Test _extract_file_paths extracts paths from plain text"""
        mock_dev_agent = Mock()
        workflow = CodeGenerationWorkflow(mock_dev_agent)

        text = "Modify src/components/Button.tsx"
        paths = workflow._extract_file_paths(text)

        assert "src/components/Button.tsx" in paths


@pytest.mark.skipif(not CODEGEN_AVAILABLE, reason="CodeGenerationWorkflow not available")
class TestDangerousPatternDetection:
    """Test dangerous pattern detection in security validation"""

    def test_dangerous_pattern_eval(self):
        """Test dangerous pattern detection for eval"""
        if not CODEGEN_AVAILABLE:
            pytest.skip("CodeGenerationWorkflow not available")
        patterns = CodeGenerationWorkflow.DANGEROUS_PATTERNS

        code = "result = eval(user_input)"

        found = False
        for pattern in patterns:
            if re.search(pattern, code, re.IGNORECASE):
                found = True
                break

        assert found is True

    def test_dangerous_pattern_sql_injection(self):
        """Test dangerous pattern detection for SQL injection"""
        if not CODEGEN_AVAILABLE:
            pytest.skip("CodeGenerationWorkflow not available")
        patterns = CodeGenerationWorkflow.DANGEROUS_PATTERNS

        code = "query = 'DROP TABLE users'"

        found = False
        for pattern in patterns:
            if re.search(pattern, code, re.IGNORECASE):
                found = True
                break

        assert found is True

    def test_safe_code_passes(self):
        """Test safe code passes security validation"""
        if not CODEGEN_AVAILABLE:
            pytest.skip("CodeGenerationWorkflow not available")
        patterns = CodeGenerationWorkflow.DANGEROUS_PATTERNS

        code = """
def calculate_sum(a, b):
    return a + b

result = calculate_sum(5, 10)
print(result)
"""

        found = False
        for pattern in patterns:
            if re.search(pattern, code, re.IGNORECASE):
                found = True
                break

        assert found is False


@pytest.mark.skipif(not CODEGEN_AVAILABLE, reason="CodeGenerationWorkflow not available")
class TestWorkflowConditionalEdges:
    """Test workflow conditional edge functions"""

    @patch('dev_agent.workflows.code_generation_workflow.TaskClassifier')
    @patch('dev_agent.workflows.code_generation_workflow.LLMTestGenerator')
    def test_should_continue_after_classify_with_error(self, mock_test_gen, mock_classifier):
        """Test _should_continue_after_classify returns end on error"""
        mock_dev_agent = Mock()
        workflow = CodeGenerationWorkflow(mock_dev_agent)

        state = {"error": "Classification failed"}
        result = workflow._should_continue_after_classify(state)

        assert result == "end"

    @patch('dev_agent.workflows.code_generation_workflow.TaskClassifier')
    @patch('dev_agent.workflows.code_generation_workflow.LLMTestGenerator')
    def test_should_continue_after_security_with_validation_failure(self, mock_test_gen, mock_classifier):
        """Test _should_continue_after_security returns end on validation failure"""
        mock_dev_agent = Mock()
        workflow = CodeGenerationWorkflow(mock_dev_agent)

        state = {"security_validated": False, "error": "Security violation"}
        result = workflow._should_continue_after_security(state)

        assert result == "end"

    @patch('dev_agent.workflows.code_generation_workflow.TaskClassifier')
    @patch('dev_agent.workflows.code_generation_workflow.LLMTestGenerator')
    def test_should_generate_tests_when_required(self, mock_test_gen, mock_classifier):
        """Test _should_generate_tests returns tests when required"""
        mock_dev_agent = Mock()
        workflow = CodeGenerationWorkflow(mock_dev_agent)

        state = {"task_metadata": {"requires_tests": True}}
        result = workflow._should_generate_tests(state)

        assert result == "tests"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
