#!/usr/bin/env python3
"""
Unit Tests for Issue #301 P0 Fixes
Tests for:
1. _is_safe_file_path() whitelist/blacklist logic
2. _sanitize_code() with improved file operation checking
3. _rollback_changes() automatic rollback mechanism
"""
import pytest
from dev_agent_wrapper import DevAgent
from workflows.bug_fix_workflow import (
    BugFixWorkflow,
    BugFixState
)


@pytest.fixture
def dev_agent():
    """Create DevAgent instance for testing"""
    return DevAgent()


@pytest.fixture
def workflow(dev_agent):
    """Create BugFixWorkflow instance"""
    return BugFixWorkflow(dev_agent)


class TestSafeFilePath:
    """Tests for _is_safe_file_path() method"""

    def test_safe_python_file_write(self, workflow):
        """Test that writing to .py files is allowed"""
        code = 'open("src/app.py", "w")'
        assert workflow._is_safe_file_path(code) is True

    def test_safe_test_file_write(self, workflow):
        """Test that writing to test files is allowed"""
        code = 'open("tests/app_test.py", "w")'
        assert workflow._is_safe_file_path(code) is True

    def test_safe_json_file_write(self, workflow):
        """Test that writing to .json files is allowed"""
        code = 'open("config.json", "w")'
        assert workflow._is_safe_file_path(code) is True

    def test_safe_yaml_file_write(self, workflow):
        """Test that writing to .yaml files is allowed"""
        code = 'open("config.yaml", "w")'
        assert workflow._is_safe_file_path(code) is True

    def test_unsafe_env_file_write(self, workflow):
        """Test that writing to .env files is blocked"""
        code = 'open(".env", "w")'
        assert workflow._is_safe_file_path(code) is False

    def test_unsafe_credentials_file(self, workflow):
        """Test that writing to credentials files is blocked"""
        code = 'open("credentials.json", "w")'
        assert workflow._is_safe_file_path(code) is False

    def test_unsafe_system_path_etc(self, workflow):
        """Test that writing to /etc/ is blocked"""
        code = 'open("/etc/passwd", "w")'
        assert workflow._is_safe_file_path(code) is False

    def test_unsafe_system_path_bin(self, workflow):
        """Test that writing to /bin/ is blocked"""
        code = 'open("/bin/sh", "w")'
        assert workflow._is_safe_file_path(code) is False

    def test_unsafe_ssh_key(self, workflow):
        """Test that writing to SSH keys is blocked"""
        code = 'open("~/.ssh/id_rsa", "w")'
        assert workflow._is_safe_file_path(code) is False

    def test_unsafe_pem_file(self, workflow):
        """Test that writing to .pem files is blocked"""
        code = 'open("certificate.pem", "w")'
        assert workflow._is_safe_file_path(code) is False

    def test_safe_read_mode_any_file(self, workflow):
        """Test that read mode is less restrictive"""
        code = 'open("data.txt", "r")'
        assert workflow._is_safe_file_path(code) is True

    def test_no_open_calls(self, workflow):
        """Test that code without open() calls is safe"""
        code = 'x = 5\ny = 10\nprint(x + y)'
        assert workflow._is_safe_file_path(code) is True


class TestSanitizeCode:
    """Tests for _sanitize_code() method"""

    def test_sanitize_safe_code_with_write(self, workflow):
        """Test that safe code with file write passes"""
        code = '''
import os
with open("output.py", "w") as f:
    f.write("print('hello')")
'''
        result = workflow._sanitize_code(code)
        assert result is not None

    def test_sanitize_blocks_eval(self, workflow):
        """Test that eval() is blocked"""
        code = 'result = eval("2 + 2")'
        result = workflow._sanitize_code(code)
        assert result is None

    def test_sanitize_blocks_exec(self, workflow):
        """Test that exec() is blocked"""
        code = 'exec("import os")'
        result = workflow._sanitize_code(code)
        assert result is None

    def test_sanitize_blocks_os_system(self, workflow):
        """Test that os.system() is blocked"""
        code = 'import os\nos.system("rm -rf /")'
        result = workflow._sanitize_code(code)
        assert result is None

    def test_sanitize_blocks_subprocess(self, workflow):
        """Test that subprocess is blocked"""
        code = 'import subprocess\nsubprocess.run(["ls", "-la"])'
        result = workflow._sanitize_code(code)
        assert result is None

    def test_sanitize_blocks_unsafe_file_path(self, workflow):
        """Test that unsafe file paths are blocked"""
        code = 'open(".env", "w").write("SECRET=123")'
        result = workflow._sanitize_code(code)
        assert result is None

    def test_sanitize_blocks_sql_injection(self, workflow):
        """Test that SQL injection patterns are blocked"""
        code = 'query = "DROP TABLE users"'
        result = workflow._sanitize_code(code)
        assert result is None

    def test_sanitize_blocks_pickle_loads(self, workflow):
        """Test that pickle.loads() is blocked"""
        code = 'import pickle\ndata = pickle.loads(untrusted_data)'
        result = workflow._sanitize_code(code)
        assert result is None

    def test_sanitize_blocks_too_long_code(self, workflow):
        """Test that code exceeding max length is blocked"""
        code = "x = 1" * 20000
        result = workflow._sanitize_code(code)
        assert result is None

    def test_sanitize_allows_safe_python_code(self, workflow):
        """Test that normal Python code passes"""
        code = '''
def calculate_sum(a, b):
    return a + b

result = calculate_sum(5, 10)
print(result)
'''
        result = workflow._sanitize_code(code)
        assert result is not None


class TestRelativePathTraversal:
    """Tests for relative path traversal protection (Issue #305 Task 1)"""

    def test_blocks_triple_dot_traversal(self, workflow):
        """阻止 ../../../ 路徑遍歷"""
        code = 'open("../../../etc/passwd", "w")'
        assert workflow._is_safe_file_path(code) is False

    def test_blocks_double_dot_traversal(self, workflow):
        """阻止 ../../ 路徑遍歷"""
        code = 'open("../../bin/sh", "w")'
        assert workflow._is_safe_file_path(code) is False

    def test_blocks_single_dot_slash_traversal(self, workflow):
        """阻止 ../etc/ 路徑遍歷"""
        code = 'open("../etc/passwd", "w")'
        assert workflow._is_safe_file_path(code) is False

    def test_blocks_backslash_traversal(self, workflow):
        """阻止 ..\\  (Windows style) 路徑遍歷"""
        code = 'open("..\\\\..\\\\etc\\\\passwd", "w")'
        assert workflow._is_safe_file_path(code) is False

    def test_allows_relative_safe_path(self, workflow):
        """允許相對路徑但在安全目錄（如 ./config.json）"""
        code = 'open("./config.json", "w")'
        assert workflow._is_safe_file_path(code) is True

    def test_allows_subdirectory_safe_path(self, workflow):
        """允許子目錄中的安全文件"""
        code = 'open("src/utils/helpers.py", "w")'
        assert workflow._is_safe_file_path(code) is True


class TestHomeDirectoryProtection:
    """Tests for $HOME and home directory protection (Issue #305 Task 2)"""

    def test_blocks_home_env_var(self, workflow):
        """阻止 $HOME 環境變數"""
        code = 'open("$HOME", "w")'
        assert workflow._is_safe_file_path(code) is False

    def test_blocks_home_with_file(self, workflow):
        """阻止 $HOME/file.txt"""
        code = 'open("$HOME/sensitive.txt", "w")'
        assert workflow._is_safe_file_path(code) is False

    def test_blocks_home_with_slash(self, workflow):
        """阻止 $HOME/"""
        code = 'open("$HOME/", "w")'
        assert workflow._is_safe_file_path(code) is False

    def test_blocks_home_with_subdirectory(self, workflow):
        """阻止 $HOME/Documents/file.txt"""
        code = 'open("$HOME/Documents/secret.txt", "w")'
        assert workflow._is_safe_file_path(code) is False


class TestRollbackMechanism:
    """Tests for _rollback_changes() and backup/rollback integration"""

    @pytest.mark.asyncio
    async def test_rollback_with_backups(self, workflow, dev_agent):
        """Test rollback restores files from backups"""
        state: BugFixState = {
            "issue_id": 1,
            "issue_title": "Test",
            "issue_body": "Test body",
            "bug_type": "test",
            "affected_files": ["test.py"],
            "root_cause": None,
            "fix_strategy": None,
            "fix_code_diff": None,
            "test_results": None,
            "pr_number": None,
            "pr_url": None,
            "approval_status": None,
            "error": None,
            "execution_start": 0.0,
            "patterns_used": [],
            "file_backups": {
                "test.py": "# Original content\nprint('hello')"
            }
        }

        original_write = dev_agent.fs_tool.write_file
        write_calls = []

        async def mock_write(path, content):
            write_calls.append({"path": path, "content": content})
            return {"success": True, "path": path}

        dev_agent.fs_tool.write_file = mock_write

        success = await workflow._rollback_changes(state)

        dev_agent.fs_tool.write_file = original_write

        assert success is True
        assert len(write_calls) == 1
        assert write_calls[0]["path"] == "test.py"
        assert "Original content" in write_calls[0]["content"]

    @pytest.mark.asyncio
    async def test_rollback_with_no_backups(self, workflow):
        """Test rollback returns False when no backups exist"""
        state: BugFixState = {
            "issue_id": 1,
            "issue_title": "Test",
            "issue_body": "Test body",
            "bug_type": "test",
            "affected_files": [],
            "root_cause": None,
            "fix_strategy": None,
            "fix_code_diff": None,
            "test_results": None,
            "pr_number": None,
            "pr_url": None,
            "approval_status": None,
            "error": None,
            "execution_start": 0.0,
            "patterns_used": [],
            "file_backups": {}
        }

        success = await workflow._rollback_changes(state)
        assert success is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
