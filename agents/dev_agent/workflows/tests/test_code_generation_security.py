#!/usr/bin/env python3
"""
Security tests for CodeGenerationWorkflow._is_safe_file_path()
Phase 2 Step B-1 Follow-up: Path Traversal Protection Tests

Tests the security of the per-task directory whitelist implementation,
specifically focusing on path traversal attack prevention.
"""
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock

from workflows.code_generation_workflow import CodeGenerationWorkflow


@pytest.fixture
def workflow():
    """Create a CodeGenerationWorkflow instance for testing"""
    mock_dev_agent = Mock()
    with tempfile.TemporaryDirectory() as tmpdir:
        workflow = CodeGenerationWorkflow(mock_dev_agent)
        workflow.repo_root = tmpdir
        yield workflow


class TestCodeGenerationSecurityPathTraversal:
    """Test path traversal attack prevention in per-task directory whitelist"""

    def test_docs_exploit_bypass_attack_blocked(self, workflow):
        """
        Test that 'docs-exploit/' does NOT bypass 'docs/' whitelist
        
        This is the critical security vulnerability identified by Gemini Code Assist.
        Before the fix, using startswith(allowed.rstrip('/')) would incorrectly allow
        'docs-exploit/file.md' when only 'docs/' was whitelisted.
        """
        # Create test directories
        docs_dir = Path(workflow.repo_root) / "docs"
        docs_dir.mkdir()
        
        docs_exploit_dir = Path(workflow.repo_root) / "docs-exploit"
        docs_exploit_dir.mkdir()
        
        # Create test files
        safe_file = docs_dir / "README.md"
        safe_file.write_text("Safe content")
        
        exploit_file = docs_exploit_dir / "malicious.md"
        exploit_file.write_text("Exploit content")
        
        # Task metadata with 'docs/' whitelist
        task_metadata = {
            "allowed_directories": ["docs/"]
        }
        
        # Safe file should be allowed
        assert workflow._is_safe_file_path(str(safe_file), task_metadata) is True
        
        # Exploit file should be BLOCKED
        assert workflow._is_safe_file_path(str(exploit_file), task_metadata) is False

    def test_tests_exploit_bypass_attack_blocked(self, workflow):
        """Test that 'tests-malicious/' does NOT bypass 'tests/' whitelist"""
        # Create test directories
        tests_dir = Path(workflow.repo_root) / "tests"
        tests_dir.mkdir()
        
        tests_malicious_dir = Path(workflow.repo_root) / "tests-malicious"
        tests_malicious_dir.mkdir()
        
        # Create test files
        safe_file = tests_dir / "test_utils.py"
        safe_file.write_text("def test_example(): pass")
        
        malicious_file = tests_malicious_dir / "test_exploit.py"
        malicious_file.write_text("import os; os.system('rm -rf /')")
        
        # Task metadata with 'tests/' whitelist
        task_metadata = {
            "allowed_directories": ["tests/"]
        }
        
        # Safe file should be allowed
        assert workflow._is_safe_file_path(str(safe_file), task_metadata) is True
        
        # Malicious file should be BLOCKED
        assert workflow._is_safe_file_path(str(malicious_file), task_metadata) is False

    def test_exact_file_match_with_similar_directory(self, workflow):
        """Test that exact file match doesn't allow similar directory names"""
        # Create test structure
        readme_file = Path(workflow.repo_root) / "README.md"
        readme_file.write_text("Project README")
        
        readme_backup_dir = Path(workflow.repo_root) / "README.md.backup"
        readme_backup_dir.mkdir()
        
        backup_file = readme_backup_dir / "old.md"
        backup_file.write_text("Old content")
        
        # Task metadata with exact file whitelist (using allowed_files for exact matches)
        task_metadata = {
            "allowed_files": ["README.md"],
            "allowed_directories": []
        }
        
        # Exact file should be allowed
        assert workflow._is_safe_file_path(str(readme_file), task_metadata) is True
        
        # Similar directory should be BLOCKED
        assert workflow._is_safe_file_path(str(backup_file), task_metadata) is False

    def test_subdirectory_prefix_attack_blocked(self, workflow):
        """Test that 'docsXYZ/' does NOT bypass 'docs/' whitelist"""
        # Create test directories
        docs_dir = Path(workflow.repo_root) / "docs"
        docs_dir.mkdir()
        
        docs_xyz_dir = Path(workflow.repo_root) / "docsXYZ"
        docs_xyz_dir.mkdir()
        
        # Create test files
        safe_file = docs_dir / "guide.md"
        safe_file.write_text("Safe guide")
        
        attack_file = docs_xyz_dir / "attack.md"
        attack_file.write_text("Attack content")
        
        # Task metadata with 'docs/' whitelist
        task_metadata = {
            "allowed_directories": ["docs/"]
        }
        
        # Safe file should be allowed
        assert workflow._is_safe_file_path(str(safe_file), task_metadata) is True
        
        # Attack file should be BLOCKED
        assert workflow._is_safe_file_path(str(attack_file), task_metadata) is False

    def test_nested_directory_allowed(self, workflow):
        """Test that nested directories within whitelist are allowed"""
        # Create nested directory structure
        docs_dir = Path(workflow.repo_root) / "docs"
        docs_dir.mkdir()
        
        api_dir = docs_dir / "api"
        api_dir.mkdir()
        
        nested_file = api_dir / "endpoints.md"
        nested_file.write_text("API endpoints")
        
        # Task metadata with 'docs/' whitelist
        task_metadata = {
            "allowed_directories": ["docs/"]
        }
        
        # Nested file should be allowed
        assert workflow._is_safe_file_path(str(nested_file), task_metadata) is True

    def test_multiple_whitelists_with_similar_names(self, workflow):
        """Test multiple whitelists with similar directory names"""
        # Create test directories
        src_dir = Path(workflow.repo_root) / "src"
        src_dir.mkdir()
        
        src_test_dir = Path(workflow.repo_root) / "src-test"
        src_test_dir.mkdir()
        
        src_backup_dir = Path(workflow.repo_root) / "src_backup"
        src_backup_dir.mkdir()
        
        # Create test files
        src_file = src_dir / "app.py"
        src_file.write_text("app code")
        
        src_test_file = src_test_dir / "test.py"
        src_test_file.write_text("test code")
        
        src_backup_file = src_backup_dir / "old.py"
        src_backup_file.write_text("backup code")
        
        # Task metadata with only 'src/' whitelist
        task_metadata = {
            "allowed_directories": ["src/"]
        }
        
        # Only src/ file should be allowed
        assert workflow._is_safe_file_path(str(src_file), task_metadata) is True
        assert workflow._is_safe_file_path(str(src_test_file), task_metadata) is False
        assert workflow._is_safe_file_path(str(src_backup_file), task_metadata) is False

    def test_whitelist_without_trailing_slash(self, workflow):
        """Test that whitelist works correctly without trailing slash"""
        # Create test directory
        docs_dir = Path(workflow.repo_root) / "docs"
        docs_dir.mkdir()
        
        docs_file = docs_dir / "README.md"
        docs_file.write_text("Documentation")
        
        # Task metadata WITHOUT trailing slash
        task_metadata = {
            "allowed_directories": ["docs"]  # No trailing slash
        }
        
        # File should still be allowed
        assert workflow._is_safe_file_path(str(docs_file), task_metadata) is True

    def test_cross_platform_path_separator(self, workflow):
        """Test that path matching works with different path separators"""
        # Create test directory
        docs_dir = Path(workflow.repo_root) / "docs"
        docs_dir.mkdir()
        
        docs_file = docs_dir / "guide.md"
        docs_file.write_text("Guide")
        
        # Task metadata with forward slash (Unix-style)
        task_metadata = {
            "allowed_directories": ["docs/"]
        }
        
        # Should work regardless of platform
        assert workflow._is_safe_file_path(str(docs_file), task_metadata) is True


class TestCodeGenerationSecurityGlobalDenyList:
    """Test global deny list still works with per-task whitelist"""

    def test_git_directory_blocked_even_with_whitelist(self, workflow):
        """Test that .git/ is blocked even if whitelisted"""
        # Create .git directory
        git_dir = Path(workflow.repo_root) / ".git"
        git_dir.mkdir()
        
        git_file = git_dir / "config"
        git_file.write_text("git config")
        
        # Task metadata that tries to whitelist .git/
        task_metadata = {
            "allowed_directories": [".git/"]
        }
        
        # Should be blocked by global deny list
        assert workflow._is_safe_file_path(str(git_file), task_metadata) is False

    def test_migrations_blocked_even_with_whitelist(self, workflow):
        """Test that migrations/ is blocked even if whitelisted"""
        # Create migrations directory
        migrations_dir = Path(workflow.repo_root) / "migrations"
        migrations_dir.mkdir()
        
        migration_file = migrations_dir / "001_initial.sql"
        migration_file.write_text("CREATE TABLE users;")
        
        # Task metadata that tries to whitelist migrations/
        task_metadata = {
            "allowed_directories": ["migrations/"]
        }
        
        # Should be blocked by global deny list
        assert workflow._is_safe_file_path(str(migration_file), task_metadata) is False

    def test_env_file_blocked_even_with_whitelist(self, workflow):
        """Test that .env is blocked even if whitelisted"""
        # Create .env file
        env_file = Path(workflow.repo_root) / ".env"
        env_file.write_text("SECRET_KEY=abc123")
        
        # Task metadata that tries to whitelist .env
        task_metadata = {
            "allowed_directories": [".env"]
        }
        
        # Should be blocked by global deny list
        assert workflow._is_safe_file_path(str(env_file), task_metadata) is False


class TestCodeGenerationSecurityEdgeCases:
    """Test edge cases in path validation"""

    def test_empty_whitelist_allows_all(self, workflow):
        """Test that empty whitelist allows all files (no restriction)"""
        # Create test file
        test_file = Path(workflow.repo_root) / "test.txt"
        test_file.write_text("test")
        
        # Task metadata with empty whitelist
        task_metadata = {
            "allowed_directories": []
        }
        
        # Empty whitelist means no restriction, so file should be allowed
        assert workflow._is_safe_file_path(str(test_file), task_metadata) is True

    def test_no_whitelist_allows_all_except_deny_list(self, workflow):
        """Test that no whitelist allows all files (except global deny list)"""
        # Create test file
        test_file = Path(workflow.repo_root) / "test.txt"
        test_file.write_text("test")
        
        # Task metadata without whitelist
        task_metadata = {}
        
        # Should be allowed (no whitelist restriction)
        assert workflow._is_safe_file_path(str(test_file), task_metadata) is True

    def test_none_task_metadata_allows_all_except_deny_list(self, workflow):
        """Test that None task_metadata allows all files (except global deny list)"""
        # Create test file
        test_file = Path(workflow.repo_root) / "test.txt"
        test_file.write_text("test")
        
        # No task metadata
        task_metadata = None
        
        # Should be allowed (no whitelist restriction)
        assert workflow._is_safe_file_path(str(test_file), task_metadata) is True

    def test_symlink_resolution_with_whitelist(self, workflow):
        """Test that symlinks are resolved before whitelist check"""
        # Create test directory and file
        docs_dir = Path(workflow.repo_root) / "docs"
        docs_dir.mkdir()
        
        real_file = docs_dir / "real.md"
        real_file.write_text("Real content")
        
        # Create symlink outside docs/
        symlink_file = Path(workflow.repo_root) / "link.md"
        try:
            symlink_file.symlink_to(real_file)
        except OSError:
            pytest.skip("Symlinks not supported on this platform")
        
        # Task metadata with 'docs/' whitelist
        task_metadata = {
            "allowed_directories": ["docs/"]
        }
        
        # Real file should be allowed
        assert workflow._is_safe_file_path(str(real_file), task_metadata) is True
        
        # Symlink resolves to real_file which is in docs/, so it should be allowed
        # The security check uses os.path.realpath() which resolves symlinks
        result = workflow._is_safe_file_path(str(symlink_file), task_metadata)
        # After symlink resolution, the path points to docs/real.md which is allowed
        assert result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
