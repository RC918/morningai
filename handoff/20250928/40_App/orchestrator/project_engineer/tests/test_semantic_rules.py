#!/usr/bin/env python3
"""
Unit tests for Semantic Rules v2 - Phase 4 PR-1

Tests for:
- Path normalization and traversal prevention
- Directory validation
- Task type validation
- Repository validation
- Full task validation
"""
import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add project_engineer to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from semantic_rules import (
    SemanticRulesValidator,
    SemanticRuleViolation,
    normalize_path,
    validate_directory,
    validate_task_type,
    validate_repo,
    validate_task,
    get_validator,
)


class TestPathNormalization:
    """Test path normalization and traversal detection"""

    def test_normalize_simple_path(self):
        """Should normalize simple paths correctly"""
        validator = SemanticRulesValidator()
        normalized, is_safe = validator.normalize_path("docs/README.md")
        assert is_safe is True
        assert normalized == "docs/README.md"

    def test_normalize_path_with_leading_slash(self):
        """Should remove leading slash"""
        validator = SemanticRulesValidator()
        normalized, is_safe = validator.normalize_path("/docs/README.md")
        assert is_safe is True
        assert normalized == "docs/README.md"

    def test_detect_double_dot_traversal(self):
        """Should detect .. traversal attempts"""
        validator = SemanticRulesValidator()
        normalized, is_safe = validator.normalize_path("../etc/passwd")
        assert is_safe is False

    def test_detect_double_dot_in_middle(self):
        """Should detect .. in middle of path"""
        validator = SemanticRulesValidator()
        normalized, is_safe = validator.normalize_path("docs/../../../etc/passwd")
        assert is_safe is False

    def test_detect_dot_slash(self):
        """Should detect ./ patterns"""
        validator = SemanticRulesValidator()
        normalized, is_safe = validator.normalize_path("./docs/README.md")
        assert is_safe is False

    def test_detect_url_encoded_traversal(self):
        """Should detect URL-encoded traversal"""
        validator = SemanticRulesValidator()
        normalized, is_safe = validator.normalize_path("docs%2f..%2f..%2fetc")
        assert is_safe is False

    def test_detect_backslash(self):
        """Should detect backslash (Windows path)"""
        validator = SemanticRulesValidator()
        normalized, is_safe = validator.normalize_path("docs\\..\\etc")
        assert is_safe is False

    def test_detect_multiple_slashes(self):
        """Should detect multiple consecutive slashes"""
        validator = SemanticRulesValidator()
        normalized, is_safe = validator.normalize_path("docs//README.md")
        assert is_safe is False

    def test_empty_path(self):
        """Should handle empty path"""
        validator = SemanticRulesValidator()
        normalized, is_safe = validator.normalize_path("")
        assert is_safe is True
        assert normalized == ""

    def test_whitespace_path(self):
        """Should handle whitespace path"""
        validator = SemanticRulesValidator()
        normalized, is_safe = validator.normalize_path("  docs/README.md  ")
        assert is_safe is True
        assert normalized == "docs/README.md"


class TestDirectoryValidation:
    """Test directory validation"""

    def test_validate_allowed_directory(self):
        """Should allow paths in allowed directories"""
        validator = SemanticRulesValidator()
        validator.allowed_directories = ["docs/", "tests/"]
        
        is_valid, violation = validator.validate_directory("docs/README.md")
        assert is_valid is True
        assert violation is None

    def test_validate_disallowed_directory(self):
        """Should reject paths not in allowed directories"""
        validator = SemanticRulesValidator()
        validator.allowed_directories = ["docs/", "tests/"]
        
        is_valid, violation = validator.validate_directory("src/main.py")
        assert is_valid is False
        assert violation is not None
        assert violation.rule_type == "directory"

    def test_validate_nested_allowed_directory(self):
        """Should allow nested paths in allowed directories"""
        validator = SemanticRulesValidator()
        validator.allowed_directories = ["docs/"]
        
        is_valid, violation = validator.validate_directory("docs/api/endpoints.md")
        assert is_valid is True

    def test_validate_empty_allowed_directories(self):
        """Should allow all paths when allowed_directories is empty"""
        validator = SemanticRulesValidator()
        validator.allowed_directories = []
        
        is_valid, violation = validator.validate_directory("any/path/file.py")
        assert is_valid is True

    def test_validate_traversal_in_directory(self):
        """Should reject paths with traversal even in allowed directories"""
        validator = SemanticRulesValidator()
        validator.allowed_directories = ["docs/"]
        
        is_valid, violation = validator.validate_directory("docs/../etc/passwd")
        assert is_valid is False
        assert violation.rule_type == "path_traversal"


class TestTaskTypeValidation:
    """Test task type validation"""

    @patch('semantic_rules.SemanticRulesValidator._load_settings')
    def test_validate_safe_task_type(self, mock_load):
        """Should allow safe task types when allowed_task_types is empty"""
        validator = SemanticRulesValidator()
        validator.allowed_task_types = []
        validator.allowed_directories = []
        validator.allowed_repos = []
        
        with patch.object(validator, 'validate_task_type', wraps=validator.validate_task_type):
            # Mock the is_safe_task import inside the method
            with patch('project_engineer.safe_tasks.is_safe_task', return_value=True):
                is_valid, violation = validator.validate_task_type("documentation_update")
                assert is_valid is True

    @patch('semantic_rules.SemanticRulesValidator._load_settings')
    def test_validate_unsafe_task_type(self, mock_load):
        """Should reject unsafe task types"""
        validator = SemanticRulesValidator()
        validator.allowed_task_types = []
        validator.allowed_directories = []
        validator.allowed_repos = []
        
        with patch('project_engineer.safe_tasks.is_safe_task', return_value=False):
            is_valid, violation = validator.validate_task_type("refactor")
            assert is_valid is False
            assert violation.rule_type == "task_type"

    @patch('semantic_rules.SemanticRulesValidator._load_settings')
    def test_validate_explicit_allowed_task_type(self, mock_load):
        """Should allow explicitly allowed task types"""
        validator = SemanticRulesValidator()
        validator.allowed_task_types = ["documentation_update", "test_generation"]
        validator.allowed_directories = []
        validator.allowed_repos = []
        
        is_valid, violation = validator.validate_task_type("documentation_update")
        assert is_valid is True

    @patch('semantic_rules.SemanticRulesValidator._load_settings')
    def test_validate_not_in_explicit_allowed_task_types(self, mock_load):
        """Should reject task types not in explicit allowed list"""
        validator = SemanticRulesValidator()
        validator.allowed_task_types = ["documentation_update"]
        validator.allowed_directories = []
        validator.allowed_repos = []
        
        is_valid, violation = validator.validate_task_type("test_generation")
        assert is_valid is False
        assert violation.rule_type == "task_type"


class TestRepoValidation:
    """Test repository validation"""

    def test_validate_allowed_repo(self):
        """Should allow repos in allowed list"""
        validator = SemanticRulesValidator()
        validator.allowed_repos = ["RC918/morningai"]
        
        is_valid, violation = validator.validate_repo("RC918/morningai")
        assert is_valid is True

    def test_validate_disallowed_repo(self):
        """Should reject repos not in allowed list"""
        validator = SemanticRulesValidator()
        validator.allowed_repos = ["RC918/morningai"]
        
        is_valid, violation = validator.validate_repo("other/repo")
        assert is_valid is False
        assert violation.rule_type == "repo"

    def test_validate_empty_allowed_repos(self):
        """Should allow all repos when allowed_repos is empty"""
        validator = SemanticRulesValidator()
        validator.allowed_repos = []
        
        is_valid, violation = validator.validate_repo("any/repo")
        assert is_valid is True


class TestFullTaskValidation:
    """Test full task validation"""

    @patch('semantic_rules.SemanticRulesValidator._load_settings')
    def test_validate_valid_task(self, mock_load):
        """Should validate a fully valid task"""
        validator = SemanticRulesValidator()
        validator.allowed_repos = ["RC918/morningai"]
        validator.allowed_directories = ["docs/"]
        validator.allowed_task_types = []
        # Phase 1 Security Foundation attributes
        validator.allowed_actions = []
        validator.blocked_file_patterns = []
        validator.require_hitl_for_high_risk = False
        
        with patch('project_engineer.safe_tasks.is_safe_task', return_value=True):
            is_valid, violations = validator.validate_task(
                repo="RC918/morningai",
                task_type="documentation_update",
                file_paths=["docs/README.md"]
            )
            assert is_valid is True
            assert len(violations) == 0

    @patch('semantic_rules.SemanticRulesValidator._load_settings')
    def test_validate_task_with_multiple_violations(self, mock_load):
        """Should collect multiple violations"""
        validator = SemanticRulesValidator()
        validator.allowed_repos = ["RC918/morningai"]
        validator.allowed_directories = ["docs/"]
        validator.allowed_task_types = ["documentation_update"]
        # Phase 1 Security Foundation attributes
        validator.allowed_actions = []
        validator.blocked_file_patterns = []
        validator.require_hitl_for_high_risk = False
        
        is_valid, violations = validator.validate_task(
            repo="other/repo",
            task_type="refactor",
            file_paths=["src/main.py", "../etc/passwd"]
        )
        assert is_valid is False
        # Should have violations for: repo, task_type, directory (src/), path_traversal (../)
        assert len(violations) >= 3


class TestConvenienceFunctions:
    """Test module-level convenience functions"""

    def test_normalize_path_function(self):
        """Test normalize_path convenience function"""
        normalized, is_safe = normalize_path("docs/README.md")
        assert is_safe is True
        assert normalized == "docs/README.md"

    def test_validate_directory_function(self):
        """Test validate_directory convenience function"""
        # This will use default settings
        is_valid, error = validate_directory("docs/README.md")
        assert is_valid is True

    def test_validate_repo_function(self):
        """Test validate_repo convenience function"""
        # This will use default settings (RC918/morningai allowed)
        is_valid, error = validate_repo("RC918/morningai")
        assert is_valid is True

    def test_get_validator_singleton(self):
        """Test that get_validator returns same instance"""
        validator1 = get_validator()
        validator2 = get_validator()
        assert validator1 is validator2


class TestSemanticRuleViolation:
    """Test SemanticRuleViolation dataclass"""

    def test_violation_creation(self):
        """Should create violation with all fields"""
        violation = SemanticRuleViolation(
            rule_type="directory",
            message="File not in allowed directory",
            severity="error",
            details="Allowed: docs/, tests/"
        )
        assert violation.rule_type == "directory"
        assert violation.message == "File not in allowed directory"
        assert violation.severity == "error"
        assert violation.details == "Allowed: docs/, tests/"

    def test_violation_optional_details(self):
        """Should allow optional details"""
        violation = SemanticRuleViolation(
            rule_type="repo",
            message="Repo not allowed",
            severity="error"
        )
        assert violation.details is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
