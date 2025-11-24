#!/usr/bin/env python3
"""
Unit tests for Task Classifier - P0 Missing Tests
Phase 0-Lite Supplement: Basic tests for TaskClassifier
"""
import pytest
import sys
import os

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# noqa: E402
# noqa: E402
from agents.dev_agent.workflows.task_classifier import TaskClassifier, TaskType, classify_task


class TestTaskClassifierInitialization:
    """Test TaskClassifier initialization"""

    def test_init_creates_patterns(self):
        """Test that initialization creates pattern dictionary"""
        classifier = TaskClassifier()

        assert hasattr(classifier, 'patterns')
        assert isinstance(classifier.patterns, dict)
        assert len(classifier.patterns) == 5  # 5 task types (excluding UNKNOWN)

    def test_init_patterns_have_correct_task_types(self):
        """Test that patterns dictionary has all expected task types"""
        classifier = TaskClassifier()

        expected_types = [
            TaskType.BACKEND_UTILS_BUG_FIX,
            TaskType.FRONTEND_UI_TOKENS,
            TaskType.SIMPLE_API_ENDPOINT,
            TaskType.TEST_GENERATION,
            TaskType.DOCUMENTATION_UPDATE
        ]

        for task_type in expected_types:
            assert task_type in classifier.patterns
            assert isinstance(classifier.patterns[task_type], list)
            assert len(classifier.patterns[task_type]) > 0


class TestTaskClassifierPatternMatching:
    """Test pattern-based classification"""

    def test_classify_backend_bug_fix_pattern(self):
        """Test classification of backend bug fix tasks"""
        classifier = TaskClassifier()

        # Test various backend bug fix patterns
        test_cases = [
            "Fix bug in utils.py file",
            "Bug in python util function",
            "Error in function helper.py",
            "TypeError in backend.py",
            "ValueError in util.py",
            "Fix helper function in backend util"
        ]

        for description in test_cases:
            result = classifier.classify(description)
            assert result == TaskType.BACKEND_UTILS_BUG_FIX, f"Failed for: {description}"

    def test_classify_frontend_ui_tokens_pattern(self):
        """Test classification of frontend UI token tasks"""
        classifier = TaskClassifier()

        test_cases = [
            "Update prop in React component",
            "Change token in component",
            "UI token update in Button.jsx",
            "UI token change in Card.tsx",
            "Update component prop values",
            "Change React prop names",
            "Frontend token updates"
        ]

        for description in test_cases:
            result = classifier.classify(description)
            assert result == TaskType.FRONTEND_UI_TOKENS, f"Failed for: {description}"

    def test_classify_api_endpoint_pattern(self):
        """Test classification of API endpoint tasks"""
        classifier = TaskClassifier()

        test_cases = [
            "Create API endpoint for users",
            "Add REST endpoint for products",
            "New API route for orders",
            "CRUD endpoint for customers",
            "API with GET POST PUT DELETE methods",
            "Create route in API server"
        ]

        for description in test_cases:
            result = classifier.classify(description)
            assert result == TaskType.SIMPLE_API_ENDPOINT, f"Failed for: {description}"

    def test_classify_test_generation_pattern(self):
        """Test classification of test generation tasks"""
        classifier = TaskClassifier()

        test_cases = [
            "Generate test for UserService",
            "Create test for authentication",
            "Add unit test for validator",
            "Write test for helper function",
            "Improve test coverage for utils",
            "Add test case for edge cases"
        ]

        for description in test_cases:
            result = classifier.classify(description)
            assert result == TaskType.TEST_GENERATION, f"Failed for: {description}"

    def test_classify_documentation_update_pattern(self):
        """Test classification of documentation tasks"""
        classifier = TaskClassifier()

        test_cases = [
            "Update README file",
            "Update documentation for API",
            "Add docstring to functions",
            "Improve documentation quality",
            "Update comment in code",
            "Fix documentation errors",
            "Update CONTRIBUTING.md"
        ]

        for description in test_cases:
            result = classifier.classify(description)
            assert result == TaskType.DOCUMENTATION_UPDATE, f"Failed for: {description}"


class TestTaskClassifierHeuristics:
    """Test heuristic-based classification"""

    def test_classify_backend_bug_fix_heuristic(self):
        """Test heuristic classification for backend bug fixes"""
        classifier = TaskClassifier()

        # These don't match exact patterns but should match heuristics
        description = "There's an error in the Python backend helper"
        result = classifier.classify(description)
        assert result == TaskType.BACKEND_UTILS_BUG_FIX

    def test_classify_frontend_ui_tokens_heuristic(self):
        """Test heuristic classification for frontend UI tokens"""
        classifier = TaskClassifier()

        description = "Need to update the React component UI with new token"
        result = classifier.classify(description)
        assert result == TaskType.FRONTEND_UI_TOKENS

    def test_classify_api_endpoint_heuristic(self):
        """Test heuristic classification for API endpoints"""
        classifier = TaskClassifier()

        description = "We need to add a new endpoint to the API for GET requests"
        result = classifier.classify(description)
        assert result == TaskType.SIMPLE_API_ENDPOINT

    def test_classify_test_generation_heuristic(self):
        """Test heuristic classification for test generation"""
        classifier = TaskClassifier()

        description = "Need to create testing for the new feature"
        result = classifier.classify(description)
        assert result == TaskType.TEST_GENERATION

    def test_classify_documentation_update_heuristic(self):
        """Test heuristic classification for documentation"""
        classifier = TaskClassifier()

        description = "The README needs to be improved with better documentation"
        result = classifier.classify(description)
        assert result == TaskType.DOCUMENTATION_UPDATE

    def test_classify_unknown_no_match(self):
        """Test that unmatched tasks return UNKNOWN"""
        classifier = TaskClassifier()

        description = "This is a completely random task that doesn't match anything"
        result = classifier.classify(description)
        assert result == TaskType.UNKNOWN


class TestTaskClassifierWithTitle:
    """Test classification using both title and description"""

    def test_classify_with_title_and_description(self):
        """Test that both title and description are considered"""
        classifier = TaskClassifier()

        title = "Bug Fix"
        description = "Fix error in utils.py"
        result = classifier.classify(description, title)
        assert result == TaskType.BACKEND_UTILS_BUG_FIX

    def test_classify_title_only_match(self):
        """Test classification when only title matches"""
        classifier = TaskClassifier()

        title = "Fix bug in helper.py"
        description = "Some generic description"
        result = classifier.classify(description, title)
        assert result == TaskType.BACKEND_UTILS_BUG_FIX

    def test_classify_case_insensitive(self):
        """Test that classification is case insensitive"""
        classifier = TaskClassifier()

        test_cases = [
            "FIX BUG IN UTILS.PY",
            "fix bug in utils.py",
            "Fix Bug In Utils.Py"
        ]

        for description in test_cases:
            result = classifier.classify(description)
            assert result == TaskType.BACKEND_UTILS_BUG_FIX


class TestTaskMetadata:
    """Test get_task_metadata method"""

    def test_get_metadata_backend_bug_fix(self):
        """Test metadata for backend bug fix"""
        classifier = TaskClassifier()
        metadata = classifier.get_task_metadata(TaskType.BACKEND_UTILS_BUG_FIX)

        assert metadata["complexity"] == "low"
        assert metadata["estimated_time_minutes"] == 15
        assert metadata["requires_tests"] is True
        assert metadata["requires_review"] is True
        assert "*.py" in metadata["file_patterns"]

    def test_get_metadata_frontend_ui_tokens(self):
        """Test metadata for frontend UI tokens"""
        classifier = TaskClassifier()
        metadata = classifier.get_task_metadata(TaskType.FRONTEND_UI_TOKENS)

        assert metadata["complexity"] == "low"
        assert metadata["estimated_time_minutes"] == 10
        assert metadata["requires_tests"] is False
        assert metadata["requires_review"] is True
        assert "*.jsx" in metadata["file_patterns"]
        assert "*.tsx" in metadata["file_patterns"]

    def test_get_metadata_api_endpoint(self):
        """Test metadata for API endpoint"""
        classifier = TaskClassifier()
        metadata = classifier.get_task_metadata(TaskType.SIMPLE_API_ENDPOINT)

        assert metadata["complexity"] == "medium"
        assert metadata["estimated_time_minutes"] == 30
        assert metadata["requires_tests"] is True
        assert metadata["requires_review"] is True

    def test_get_metadata_test_generation(self):
        """Test metadata for test generation"""
        classifier = TaskClassifier()
        metadata = classifier.get_task_metadata(TaskType.TEST_GENERATION)

        assert metadata["complexity"] == "low"
        assert metadata["estimated_time_minutes"] == 20
        assert metadata["requires_tests"] is False
        assert "test_*.py" in metadata["file_patterns"]

    def test_get_metadata_documentation_update(self):
        """Test metadata for documentation update"""
        classifier = TaskClassifier()
        metadata = classifier.get_task_metadata(TaskType.DOCUMENTATION_UPDATE)

        assert metadata["complexity"] == "low"
        assert metadata["estimated_time_minutes"] == 10
        assert metadata["requires_tests"] is False
        assert metadata["requires_review"] is False
        assert "*.md" in metadata["file_patterns"]

    def test_get_metadata_unknown(self):
        """Test metadata for unknown task type"""
        classifier = TaskClassifier()
        metadata = classifier.get_task_metadata(TaskType.UNKNOWN)

        assert metadata["complexity"] == "unknown"
        assert metadata["estimated_time_minutes"] == 0
        assert metadata["requires_tests"] is False
        assert len(metadata["file_patterns"]) == 0


class TestIsSupported:
    """Test is_supported method"""

    def test_is_supported_known_types(self):
        """Test that known task types are supported"""
        classifier = TaskClassifier()

        supported_types = [
            TaskType.BACKEND_UTILS_BUG_FIX,
            TaskType.FRONTEND_UI_TOKENS,
            TaskType.SIMPLE_API_ENDPOINT,
            TaskType.TEST_GENERATION,
            TaskType.DOCUMENTATION_UPDATE
        ]

        for task_type in supported_types:
            assert classifier.is_supported(task_type) is True

    def test_is_supported_unknown_type(self):
        """Test that UNKNOWN task type is not supported"""
        classifier = TaskClassifier()
        assert classifier.is_supported(TaskType.UNKNOWN) is False


class TestClassifyTaskConvenienceFunction:
    """Test classify_task convenience function"""

    def test_classify_task_returns_dict(self):
        """Test that classify_task returns proper dictionary"""
        result = classify_task("Fix bug in utils.py")

        assert isinstance(result, dict)
        assert "task_type" in result
        assert "task_type_enum" in result
        assert "metadata" in result
        assert "supported" in result

    def test_classify_task_backend_bug_fix(self):
        """Test classify_task for backend bug fix"""
        result = classify_task("Fix bug in utils.py")

        assert result["task_type"] == "backend_utils_bug_fix"
        assert result["task_type_enum"] == TaskType.BACKEND_UTILS_BUG_FIX
        assert result["supported"] is True
        assert isinstance(result["metadata"], dict)

    def test_classify_task_with_title(self):
        """Test classify_task with both title and description"""
        result = classify_task("Some description", "Fix bug in helper.py")

        assert result["task_type"] == "backend_utils_bug_fix"
        assert result["supported"] is True

    def test_classify_task_unknown(self):
        """Test classify_task for unknown task"""
        result = classify_task("Random unclassifiable task")

        assert result["task_type"] == "unknown"
        assert result["task_type_enum"] == TaskType.UNKNOWN
        assert result["supported"] is False


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_classify_empty_description(self):
        """Test classification with empty description"""
        classifier = TaskClassifier()
        result = classifier.classify("")
        assert result == TaskType.UNKNOWN

    def test_classify_empty_title_and_description(self):
        """Test classification with both empty"""
        classifier = TaskClassifier()
        result = classifier.classify("", "")
        assert result == TaskType.UNKNOWN

    def test_classify_whitespace_only(self):
        """Test classification with whitespace only"""
        classifier = TaskClassifier()
        result = classifier.classify("   ", "   ")
        assert result == TaskType.UNKNOWN

    def test_classify_special_characters(self):
        """Test classification with special characters"""
        classifier = TaskClassifier()
        description = "Fix bug in @utils.py #123 $error"
        result = classifier.classify(description)
        assert result == TaskType.BACKEND_UTILS_BUG_FIX

    def test_classify_unicode_characters(self):
        """Test classification with unicode characters"""
        classifier = TaskClassifier()
        description = "Fix bug in utils.py 修復錯誤"
        result = classifier.classify(description)
        assert result == TaskType.BACKEND_UTILS_BUG_FIX


class TestRealWorldCases:
    """Test real-world GitHub/Jira issue formats"""

    def test_classify_noisy_github_issue_bug_report(self):
        """Test classification with noisy GitHub issue format"""
        classifier = TaskClassifier()

        description = """
        **Bug Report**

        There's a TypeError in utils.py line 42 when calling the helper function.

        Steps to reproduce:
        1. Run the app
        2. Click button
        3. See error

        Expected: No error
        Actual: TypeError: 'NoneType' object is not callable

        Stack trace:
        File "utils.py", line 42, in helper
            return self.process()
        """

        result = classifier.classify(description)
        assert result == TaskType.BACKEND_UTILS_BUG_FIX

    def test_classify_jira_style_api_task(self):
        """Test classification with Jira-style task format"""
        classifier = TaskClassifier()

        description = """
        [TASK-123] Create new endpoint for user profile

        As a developer, I want to create a new API endpoint
        so that the frontend can fetch user profile data.

        Acceptance Criteria:
        - Endpoint: GET /api/v1/users/:id/profile
        - Returns JSON with user data
        - Includes proper error handling
        - Add unit tests

        Technical Notes:
        - Use existing UserService
        - Follow REST conventions
        """

        result = classifier.classify(description)
        assert result == TaskType.SIMPLE_API_ENDPOINT

    def test_classify_ambiguous_multi_category(self):
        """Test classification with ambiguous multi-category description"""
        classifier = TaskClassifier()

        description = "Update API endpoint documentation in README and add examples"

        result = classifier.classify(description)

        assert result != TaskType.UNKNOWN

    def test_classify_github_issue_with_code_blocks(self):
        """Test classification with code blocks in description"""
        classifier = TaskClassifier()

        description = """
        Fix button color styling in the UI component

        The primary button color is wrong in the frontend. Should be blue but showing gray.

        ```css
        .btn-primary {
            background-color: #007bff;
            color: white;
        }
        ```

        Need to update the CSS tokens for the button component.
        """

        result = classifier.classify(description)
        assert result in [TaskType.FRONTEND_UI_TOKENS, TaskType.UNKNOWN]

    def test_classify_verbose_test_generation_request(self):
        """Test classification with verbose test generation request"""
        classifier = TaskClassifier()

        description = """
        We need comprehensive test coverage for the new authentication module.

        The auth module currently has:
        - login() function
        - logout() function
        - validateToken() function
        - refreshToken() function

        Please create unit tests covering:
        1. Happy path scenarios
        2. Error cases (invalid credentials, expired tokens)
        3. Edge cases (null inputs, malformed data)

        Target coverage: >80%
        Framework: Jest
        """

        result = classifier.classify(description)
        assert result == TaskType.TEST_GENERATION

    def test_classify_mixed_language_description(self):
        """Test classification with mixed language content"""
        classifier = TaskClassifier()

        description = "Fix API endpoint /users bug - returns 500 error when calling GET /api/users"

        result = classifier.classify(description)
        assert result == TaskType.SIMPLE_API_ENDPOINT


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
