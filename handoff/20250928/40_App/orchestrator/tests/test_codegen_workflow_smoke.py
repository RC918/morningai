#!/usr/bin/env python3
"""
Smoke tests for Code Generation Workflow - P0 Missing Tests
Phase 0-Lite Supplement: Basic smoke tests for CodeGenerationWorkflow

Note: These are smoke tests focusing on initialization, classification, and security validation.
Full integration tests are deferred to P1/P2 as CodeGen workflow is currently disabled (USE_CODEGEN_WORKFLOW_PERCENT=0).
"""
import sys
import os

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from unittest.mock import MagicMock, patch  # noqa: E402
from agents.dev_agent.workflows.code_generation_workflow import CodeGenerationWorkflow, CodeGenState  # noqa: E402


class TestCodeGenerationWorkflowInitialization:
    """Test CodeGenerationWorkflow initialization"""

    def test_init_creates_workflow(self):
        """Test that initialization creates workflow components"""
        mock_dev_agent = MagicMock()

        with patch('common.config.settings.settings') as mock_settings:
            mock_settings.workspace_path = "/tmp/test_workspace"

            workflow = CodeGenerationWorkflow(mock_dev_agent)

            assert workflow.agent == mock_dev_agent
            assert hasattr(workflow, 'classifier')
            assert hasattr(workflow, 'test_generator')
            assert hasattr(workflow, 'workflow')
            assert hasattr(workflow, 'repo_root')

    def test_init_creates_task_classifier(self):
        """Test that initialization creates TaskClassifier instance"""
        mock_dev_agent = MagicMock()

        with patch('common.config.settings.settings') as mock_settings:
            mock_settings.workspace_path = "/tmp/test_workspace"

            workflow = CodeGenerationWorkflow(mock_dev_agent)

            assert workflow.classifier is not None
            assert hasattr(workflow.classifier, 'classify')

    def test_init_creates_test_generator(self):
        """Test that initialization creates LLMTestGenerator instance"""
        mock_dev_agent = MagicMock()

        with patch('common.config.settings.settings') as mock_settings:
            mock_settings.workspace_path = "/tmp/test_workspace"

            workflow = CodeGenerationWorkflow(mock_dev_agent)

            assert workflow.test_generator is not None

    def test_init_sets_repo_root(self):
        """Test that initialization sets repo_root correctly"""
        mock_dev_agent = MagicMock()

        with patch('common.config.settings.settings') as mock_settings:
            mock_settings.workspace_path = "/tmp/test_workspace"

            workflow = CodeGenerationWorkflow(mock_dev_agent)

            assert workflow.repo_root is not None
            assert isinstance(workflow.repo_root, str)


class TestCodeGenerationWorkflowSecurityValidation:
    """Test security validation (_is_safe_file_path)"""

    def test_is_safe_file_path_valid_python(self):
        """Test that valid Python files are accepted"""
        mock_dev_agent = MagicMock()

        with patch('common.config.settings.settings') as mock_settings:
            mock_settings.workspace_path = "/tmp/test_workspace"

            workflow = CodeGenerationWorkflow(mock_dev_agent)

            valid_paths = [
                "src/utils.py",
                "lib/helpers.py",
                "tests/test_utils.py",
                "app/models/user.py"
            ]

            for path in valid_paths:
                assert workflow._is_safe_file_path(path) is True, f"Failed for: {path}"

    def test_is_safe_file_path_valid_javascript(self):
        """Test that valid JavaScript/TypeScript files are accepted"""
        mock_dev_agent = MagicMock()

        with patch('common.config.settings.settings') as mock_settings:
            mock_settings.workspace_path = "/tmp/test_workspace"

            workflow = CodeGenerationWorkflow(mock_dev_agent)

            valid_paths = [
                "src/components/Button.jsx",
                "src/components/Card.tsx",
                "lib/utils.js",
                "tests/unit.test.ts"
            ]

            for path in valid_paths:
                assert workflow._is_safe_file_path(path) is True, f"Failed for: {path}"

    def test_is_safe_file_path_rejects_path_traversal(self):
        """Test that path traversal attempts are rejected"""
        mock_dev_agent = MagicMock()

        with patch('common.config.settings.settings') as mock_settings:
            mock_settings.workspace_path = "/tmp/test_workspace"

            workflow = CodeGenerationWorkflow(mock_dev_agent)

            traversal_paths = [
                "../utils.py",
                "../../lib/helpers.py",
                "src/../../../etc/passwd",
                "./../../sensitive.py"
            ]

            for path in traversal_paths:
                assert workflow._is_safe_file_path(path) is False, f"Should reject: {path}"

    def test_is_safe_file_path_allows_relative_safe_paths(self):
        """Test that safe relative paths within project are allowed"""
        mock_dev_agent = MagicMock()

        with patch('common.config.settings.settings') as mock_settings:
            mock_settings.workspace_path = "/tmp/test_workspace"

            workflow = CodeGenerationWorkflow(mock_dev_agent)

            safe_paths = [
                "src/utils.py",
                "lib/helpers.py",
                "app/models/user.py",
                "tests/test_integration.py"
            ]

            for path in safe_paths:
                assert workflow._is_safe_file_path(path) is True, f"Should allow: {path}"

    def test_is_safe_file_path_rejects_absolute_paths(self):
        """Test that absolute paths are rejected"""
        mock_dev_agent = MagicMock()

        with patch('common.config.settings.settings') as mock_settings:
            mock_settings.workspace_path = "/tmp/test_workspace"

            workflow = CodeGenerationWorkflow(mock_dev_agent)

            dangerous_paths = [
                "/etc/passwd",
                "/root/.ssh/id_rsa",
                "/sys/kernel/debug",
                "/proc/self/environ",
                "/dev/null"
            ]

            for path in dangerous_paths:
                assert workflow._is_safe_file_path(path) is False, f"Should reject: {path}"

    def test_is_safe_file_path_rejects_home_sensitive(self):
        """Test that sensitive home paths are rejected when they exist outside repo"""
        mock_dev_agent = MagicMock()

        with patch('common.config.settings.settings') as mock_settings:
            mock_settings.workspace_path = "/tmp/test_workspace"

            workflow = CodeGenerationWorkflow(mock_dev_agent)

            import os
            home_dir = os.path.expanduser('~')
            dangerous_paths = [
                f"{home_dir}/.ssh/id_rsa",
                f"{home_dir}/.aws/credentials",
                f"{home_dir}/.config/secrets"
            ]

            for path in dangerous_paths:
                assert workflow._is_safe_file_path(path) is False, f"Should reject: {path}"

    def test_is_safe_file_path_rejects_git_directory(self):
        """Test that .git directory writes are blocked when .git exists"""
        mock_dev_agent = MagicMock()

        with patch('common.config.settings.settings') as mock_settings:
            test_workspace = "/tmp/test_workspace_git"
            mock_settings.workspace_path = test_workspace

            import os
            import tempfile
            with tempfile.TemporaryDirectory() as tmpdir:
                git_dir = os.path.join(tmpdir, '.git')
                os.makedirs(git_dir, exist_ok=True)

                with patch.object(CodeGenerationWorkflow, '__init__', lambda self, agent: None):
                    workflow = CodeGenerationWorkflow.__new__(CodeGenerationWorkflow)
                    workflow.agent = mock_dev_agent
                    workflow.repo_root = tmpdir
                    workflow.classifier = MagicMock()
                    workflow.test_generator = MagicMock()

                    git_paths = [
                        ".git/config",
                        ".git/hooks/pre-commit",
                        ".git/HEAD"
                    ]

                    for path in git_paths:
                        result = workflow._is_safe_file_path(path)
                        assert result is False, f"Should reject: {path}"


class TestCodeGenerationWorkflowDangerousPatterns:
    """Test dangerous pattern detection in security validation"""

    def test_dangerous_patterns_defined(self):
        """Test that dangerous patterns are defined"""
        assert hasattr(CodeGenerationWorkflow, 'DANGEROUS_PATTERNS')
        assert isinstance(CodeGenerationWorkflow.DANGEROUS_PATTERNS, list)
        assert len(CodeGenerationWorkflow.DANGEROUS_PATTERNS) > 0

    def test_dangerous_patterns_include_eval(self):
        """Test that dangerous patterns include eval/exec"""
        patterns = CodeGenerationWorkflow.DANGEROUS_PATTERNS

        has_eval = any('eval' in pattern for pattern in patterns)
        has_exec = any('exec' in pattern for pattern in patterns)

        assert has_eval, "Should include eval pattern"
        assert has_exec, "Should include exec pattern"

    def test_dangerous_patterns_include_system_calls(self):
        """Test that dangerous patterns include system calls"""
        patterns = CodeGenerationWorkflow.DANGEROUS_PATTERNS

        has_os_system = any('os.system' in pattern or 'os\\.system' in pattern for pattern in patterns)
        has_subprocess = any('subprocess' in pattern for pattern in patterns)

        assert has_os_system or has_subprocess, "Should include system call patterns"

    def test_dangerous_patterns_include_sql_injection(self):
        """Test that dangerous patterns include SQL injection risks"""
        patterns = CodeGenerationWorkflow.DANGEROUS_PATTERNS

        has_drop = any('DROP' in pattern for pattern in patterns)
        has_delete = any('DELETE' in pattern for pattern in patterns)

        assert has_drop or has_delete, "Should include SQL injection patterns"


class TestCodeGenerationWorkflowSecurityBehavior:
    """Test validate_security() actual behavior with async tests"""

    async def test_validate_security_rejects_eval(self):
        """Test that validate_security rejects eval()"""
        mock_dev_agent = MagicMock()

        with patch('common.config.settings.settings') as mock_settings:
            mock_settings.workspace_path = "/tmp/test_workspace"

            workflow = CodeGenerationWorkflow(mock_dev_agent)

            state = {
                "task_id": 1,
                "generated_code": "result = eval(user_input)",
                "target_files": ["safe/path.py"],
                "security_validated": False,
            }

            result = await workflow.validate_security(state)

            assert result["security_validated"] is False
            assert result.get("error") is not None
            assert "dangerous pattern" in result["error"].lower() or "security" in result["error"].lower()

    async def test_validate_security_rejects_exec(self):
        """Test that validate_security rejects exec()"""
        mock_dev_agent = MagicMock()

        with patch('common.config.settings.settings') as mock_settings:
            mock_settings.workspace_path = "/tmp/test_workspace"

            workflow = CodeGenerationWorkflow(mock_dev_agent)

            state = {
                "task_id": 2,
                "generated_code": "exec(malicious_code)",
                "target_files": ["safe/path.py"],
                "security_validated": False,
            }

            result = await workflow.validate_security(state)

            assert result["security_validated"] is False
            assert result.get("error") is not None

    async def test_validate_security_rejects_os_system(self):
        """Test that validate_security rejects os.system()"""
        mock_dev_agent = MagicMock()

        with patch('common.config.settings.settings') as mock_settings:
            mock_settings.workspace_path = "/tmp/test_workspace"

            workflow = CodeGenerationWorkflow(mock_dev_agent)

            state = {
                "task_id": 3,
                "generated_code": "import os\nos.system('rm -rf /')",
                "target_files": ["safe/path.py"],
                "security_validated": False,
            }

            result = await workflow.validate_security(state)

            assert result["security_validated"] is False
            assert result.get("error") is not None

    async def test_validate_security_accepts_safe_code(self):
        """Test that validate_security accepts safe code"""
        mock_dev_agent = MagicMock()

        with patch('common.config.settings.settings') as mock_settings:
            mock_settings.workspace_path = "/tmp/test_workspace"

            workflow = CodeGenerationWorkflow(mock_dev_agent)

            state = {
                "task_id": 4,
                "generated_code": "def add(a, b):\n    return a + b",
                "target_files": ["safe/path.py"],
                "security_validated": False,
            }

            result = await workflow.validate_security(state)

            assert result["security_validated"] is True
            assert result.get("error") is None

    async def test_validate_security_rejects_unsafe_file_paths(self):
        """Test that validate_security rejects unsafe file paths"""
        mock_dev_agent = MagicMock()

        with patch('common.config.settings.settings') as mock_settings:
            mock_settings.workspace_path = "/tmp/test_workspace"

            workflow = CodeGenerationWorkflow(mock_dev_agent)

            state = {
                "task_id": 5,
                "generated_code": "def safe_function():\n    pass",
                "target_files": ["../../../etc/passwd"],
                "security_validated": False,
            }

            result = await workflow.validate_security(state)

            assert result["security_validated"] is False
            assert result.get("error") is not None
            assert "unsafe file path" in result["error"].lower() or "path" in result["error"].lower()


class TestCodeGenerationWorkflowStateStructure:
    """Test CodeGenState structure"""

    def test_codegen_state_has_required_fields(self):
        """Test that CodeGenState has all required fields"""
        required_fields = [
            'task_id',
            'task_title',
            'task_description',
            'task_type',
            'task_metadata',
            'target_files',
            'generated_code',
            'generated_tests',
            'code_diff',
            'test_results',
            'pr_number',
            'pr_url',
            'error',
            'execution_start',
            'file_backups',
            'security_validated'
        ]

        annotations = CodeGenState.__annotations__

        for field in required_fields:
            assert field in annotations, f"Missing field: {field}"
