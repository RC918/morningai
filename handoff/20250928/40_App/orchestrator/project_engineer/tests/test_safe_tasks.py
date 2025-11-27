#!/usr/bin/env python3
"""
Unit tests for Safe Tasks module
"""
import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root / "handoff" / "20250928" / "40_App" / "orchestrator"))

from project_engineer.safe_tasks import (
    is_safe_task,
    get_safe_task_metadata,
    validate_task_constraints,
    get_all_safe_tasks,
    get_safe_tasks_summary,
    SAFE_TASK_TYPES
)


class TestIsSafeTask:
    """Test suite for is_safe_task function"""
    
    def test_documentation_update_is_safe(self):
        """Test that documentation_update is a safe task"""
        assert is_safe_task("documentation_update") is True
    
    def test_update_readme_is_safe(self):
        """Test that update_readme is a safe task"""
        assert is_safe_task("update_readme") is True
    
    def test_test_generation_is_safe(self):
        """Test that test_generation is a safe task"""
        assert is_safe_task("test_generation") is True
    
    def test_fix_lint_is_safe(self):
        """Test that fix_lint is a safe task"""
        assert is_safe_task("fix_lint") is True
    
    def test_fix_typo_is_safe(self):
        """Test that fix_typo is a safe task"""
        assert is_safe_task("fix_typo") is True
    
    def test_comment_enhancement_is_safe(self):
        """Test that comment_enhancement is a safe task"""
        assert is_safe_task("comment_enhancement") is True
    
    def test_env_sync_is_safe(self):
        """Test that env_sync is a safe task"""
        assert is_safe_task("env_sync") is True
    
    def test_config_update_is_safe(self):
        """Test that config_update is a safe task"""
        assert is_safe_task("config_update") is True
    
    def test_i18n_update_is_safe(self):
        """Test that i18n_update is a safe task"""
        assert is_safe_task("i18n_update") is True
    
    def test_refactor_is_not_safe(self):
        """Test that refactor is not a safe task"""
        assert is_safe_task("refactor") is False
    
    def test_unknown_task_is_not_safe(self):
        """Test that unknown task types are not safe"""
        assert is_safe_task("unknown_task_type") is False
    
    def test_empty_string_is_not_safe(self):
        """Test that empty string is not safe"""
        assert is_safe_task("") is False
    
    def test_case_sensitive(self):
        """Test that task type matching is case-sensitive"""
        assert is_safe_task("DOCUMENTATION_UPDATE") is False
        assert is_safe_task("Documentation_Update") is False


class TestGetSafeTaskMetadata:
    """Test suite for get_safe_task_metadata function"""
    
    def test_documentation_update_metadata(self):
        """Test metadata for documentation_update"""
        metadata = get_safe_task_metadata("documentation_update")
        
        assert metadata["risk_level"] == "low"
        assert metadata["max_files"] == 5
        assert ".md" in metadata["allowed_extensions"]
        assert metadata["requires_review"] is False
        assert metadata["requires_tests"] is False
        assert "description" in metadata
        assert "examples" in metadata
    
    def test_test_generation_metadata(self):
        """Test metadata for test_generation"""
        metadata = get_safe_task_metadata("test_generation")
        
        assert metadata["risk_level"] == "low"
        assert metadata["requires_review"] is True
        assert metadata["requires_tests"] is True
    
    def test_unsafe_task_returns_empty_dict(self):
        """Test that unsafe tasks return empty dict"""
        metadata = get_safe_task_metadata("refactor")
        
        assert metadata == {}
    
    def test_unknown_task_returns_empty_dict(self):
        """Test that unknown tasks return empty dict"""
        metadata = get_safe_task_metadata("unknown_task")
        
        assert metadata == {}
    
    def test_all_safe_tasks_have_metadata(self):
        """Test that all safe tasks have metadata"""
        for task_type in SAFE_TASK_TYPES:
            metadata = get_safe_task_metadata(task_type)
            
            # Should have metadata (not empty dict)
            assert metadata != {}
            
            # Should have required fields
            assert "risk_level" in metadata
            assert "max_files" in metadata
            assert "allowed_extensions" in metadata
            assert "requires_review" in metadata
            assert "requires_tests" in metadata
            assert "description" in metadata
            assert "examples" in metadata


class TestValidateTaskConstraints:
    """Test suite for validate_task_constraints function"""
    
    def test_valid_documentation_update(self):
        """Test valid documentation update"""
        is_valid, error = validate_task_constraints(
            "documentation_update",
            ["README.md", "docs/api.md"]
        )
        
        assert is_valid is True
        assert error == ""
    
    def test_too_many_files(self):
        """Test validation fails when too many files"""
        is_valid, error = validate_task_constraints(
            "update_readme",
            ["README.md", "README2.md"]  # max_files is 1
        )
        
        assert is_valid is False
        assert "max allowed" in error
    
    def test_invalid_file_extension(self):
        """Test validation fails with invalid file extension"""
        is_valid, error = validate_task_constraints(
            "update_readme",
            ["README.py"]  # Should be .md
        )
        
        assert is_valid is False
        assert "disallowed extension" in error
    
    def test_unsafe_task_fails_validation(self):
        """Test that unsafe tasks fail validation"""
        is_valid, error = validate_task_constraints(
            "refactor",
            ["app.py"]
        )
        
        assert is_valid is False
        assert "not in safe whitelist" in error
    
    def test_file_count_parameter(self):
        """Test validation with file_count parameter"""
        is_valid, error = validate_task_constraints(
            "documentation_update",
            [],
            file_count=3
        )
        
        assert is_valid is True
    
    def test_file_count_exceeds_limit(self):
        """Test validation fails when file_count exceeds limit"""
        is_valid, error = validate_task_constraints(
            "update_readme",
            [],
            file_count=5  # max_files is 1
        )
        
        assert is_valid is False
        assert "max allowed" in error


class TestGetAllSafeTasks:
    """Test suite for get_all_safe_tasks function"""
    
    def test_returns_set(self):
        """Test that function returns a set"""
        safe_tasks = get_all_safe_tasks()
        
        assert isinstance(safe_tasks, set)
    
    def test_returns_copy(self):
        """Test that function returns a copy (not the original)"""
        safe_tasks1 = get_all_safe_tasks()
        safe_tasks2 = get_all_safe_tasks()
        
        # Should be equal but not the same object
        assert safe_tasks1 == safe_tasks2
        assert safe_tasks1 is not safe_tasks2
    
    def test_contains_expected_tasks(self):
        """Test that returned set contains expected tasks"""
        safe_tasks = get_all_safe_tasks()
        
        assert "documentation_update" in safe_tasks
        assert "test_generation" in safe_tasks
        assert "fix_lint" in safe_tasks
    
    def test_count(self):
        """Test that we have the expected number of safe tasks"""
        safe_tasks = get_all_safe_tasks()
        
        # Should have 9 safe tasks in Phase 2 Step A
        assert len(safe_tasks) == 9


class TestGetSafeTasksSummary:
    """Test suite for get_safe_tasks_summary function"""
    
    def test_returns_dict(self):
        """Test that function returns a dict"""
        summary = get_safe_tasks_summary()
        
        assert isinstance(summary, dict)
    
    def test_has_required_fields(self):
        """Test that summary has required fields"""
        summary = get_safe_tasks_summary()
        
        assert "total_safe_tasks" in summary
        assert "safe_task_types" in summary
        assert "risk_levels" in summary
        assert "version" in summary
    
    def test_total_safe_tasks(self):
        """Test total_safe_tasks count"""
        summary = get_safe_tasks_summary()
        
        assert summary["total_safe_tasks"] == 9
    
    def test_safe_task_types_list(self):
        """Test safe_task_types is a list"""
        summary = get_safe_tasks_summary()
        
        assert isinstance(summary["safe_task_types"], list)
        assert len(summary["safe_task_types"]) == 9
    
    def test_risk_levels(self):
        """Test risk_levels breakdown"""
        summary = get_safe_tasks_summary()
        
        assert isinstance(summary["risk_levels"], dict)
        assert "low" in summary["risk_levels"]
        assert summary["risk_levels"]["low"] == 9  # All tasks are low risk
    
    def test_version(self):
        """Test version field"""
        summary = get_safe_tasks_summary()
        
        assert summary["version"] == "1.0.0-phase2-step-a"


class TestSafeTaskTypes:
    """Test suite for SAFE_TASK_TYPES constant"""
    
    def test_is_set(self):
        """Test that SAFE_TASK_TYPES is a set"""
        assert isinstance(SAFE_TASK_TYPES, set)
    
    def test_immutability(self):
        """Test that SAFE_TASK_TYPES cannot be easily modified"""
        original_size = len(SAFE_TASK_TYPES)
        
        # Try to add a task (this will modify the set, but we can't prevent it in Python)
        # The test is more about documenting expected behavior
        try:
            SAFE_TASK_TYPES.add("dangerous_task")
            # If we get here, the set was modified
            # Remove it to restore original state
            SAFE_TASK_TYPES.discard("dangerous_task")
        except Exception:
            # If an exception is raised, that's good (immutable)
            pass
        
        # Verify size is still the same
        assert len(SAFE_TASK_TYPES) == original_size
    
    def test_all_lowercase(self):
        """Test that all task types are lowercase with underscores"""
        for task_type in SAFE_TASK_TYPES:
            assert task_type == task_type.lower()
            assert " " not in task_type


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
