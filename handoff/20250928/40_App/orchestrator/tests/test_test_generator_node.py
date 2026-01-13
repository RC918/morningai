"""
Unit tests for D-7 Test Generation from Reviewer Flags

Tests the TestGeneratorNode and related functions that generate tests
based on B-11 coverage gaps.
"""

from unittest.mock import patch, MagicMock
import os
import tempfile

from test_generator_node import (
    TestGeneratorNode,
    GeneratedTestFile,
    TestGenerationResult,
    generate_tests_for_coverage_gaps,
)


class TestGeneratedTestFile:
    """Tests for GeneratedTestFile dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        test_file = GeneratedTestFile(
            test_file_path="tests/test_example.py",
            test_code="def test_foo(): pass",
            source_file_path="src/example.py",
            functions_tested=["foo", "bar"],
            framework="pytest",
        )

        result = test_file.to_dict()

        assert result["test_file_path"] == "tests/test_example.py"
        assert result["test_code"] == "def test_foo(): pass"
        assert result["source_file_path"] == "src/example.py"
        assert result["functions_tested"] == ["foo", "bar"]
        assert result["framework"] == "pytest"

    def test_default_values(self):
        """Test default values for optional fields."""
        test_file = GeneratedTestFile(
            test_file_path="tests/test_example.py",
            test_code="def test_foo(): pass",
            source_file_path="src/example.py",
        )

        assert test_file.functions_tested == []
        assert test_file.framework == "pytest"


class TestTestGenerationResult:
    """Tests for TestGenerationResult dataclass."""

    def test_to_dict_empty(self):
        """Test conversion to dictionary with empty results."""
        result = TestGenerationResult()

        dict_result = result.to_dict()

        assert dict_result["generated_tests"] == []
        assert dict_result["failed_generations"] == []
        assert dict_result["summary"] == ""
        assert dict_result["total_generated"] == 0
        assert dict_result["total_failed"] == 0

    def test_to_dict_with_data(self):
        """Test conversion to dictionary with data."""
        test_file = GeneratedTestFile(
            test_file_path="tests/test_example.py",
            test_code="def test_foo(): pass",
            source_file_path="src/example.py",
        )
        result = TestGenerationResult(
            generated_tests=[test_file],
            failed_generations=[{"file_path": "src/broken.py", "reason": "error"}],
            summary="Generated 1 test file",
        )

        dict_result = result.to_dict()

        assert len(dict_result["generated_tests"]) == 1
        assert len(dict_result["failed_generations"]) == 1
        assert dict_result["summary"] == "Generated 1 test file"
        assert dict_result["total_generated"] == 1
        assert dict_result["total_failed"] == 1


class TestTestGeneratorNode:
    """Tests for TestGeneratorNode class."""

    def test_init_default_values(self):
        """Test initialization with default values."""
        generator = TestGeneratorNode(trace_id="test-123")

        assert generator.trace_id == "test-123"
        assert generator.max_tests_per_run == 5
        assert generator.enable_llm is True

    def test_init_custom_values(self):
        """Test initialization with custom values."""
        generator = TestGeneratorNode(
            trace_id="test-456",
            max_tests_per_run=10,
            enable_llm=False,
        )

        assert generator.trace_id == "test-456"
        assert generator.max_tests_per_run == 10
        assert generator.enable_llm is False

    def test_generate_empty_gaps(self):
        """Test generation with no coverage gaps."""
        generator = TestGeneratorNode(trace_id="test-123", enable_llm=False)

        result = generator.generate(
            coverage_gaps=[],
            repo_path="/tmp/repo",
        )

        assert result.summary == "No coverage gaps to generate tests for"
        assert len(result.generated_tests) == 0

    def test_group_gaps_by_file(self):
        """Test grouping coverage gaps by file."""
        generator = TestGeneratorNode(trace_id="test-123")

        gaps = [
            {"file_path": "src/a.py", "function_name": "foo"},
            {"file_path": "src/a.py", "function_name": "bar"},
            {"file_path": "src/b.py", "function_name": "baz"},
        ]

        grouped = generator._group_gaps_by_file(gaps)

        assert len(grouped) == 2
        assert len(grouped["src/a.py"]) == 2
        assert len(grouped["src/b.py"]) == 1

    def test_get_test_file_path_pytest(self):
        """Test test file path generation for pytest."""
        generator = TestGeneratorNode(trace_id="test-123")

        result = generator._get_test_file_path("src/example.py", "pytest")

        assert result == "src/tests/test_example.py"

    def test_get_test_file_path_jest(self):
        """Test test file path generation for Jest."""
        generator = TestGeneratorNode(trace_id="test-123")

        result = generator._get_test_file_path("src/example.ts", "jest")

        assert result == "src/tests/example.test.ts"

    def test_get_test_file_path_existing_tests_dir(self):
        """Test test file path when source is already in tests dir."""
        generator = TestGeneratorNode(trace_id="test-123")

        result = generator._get_test_file_path("tests/unit/example.py", "pytest")

        assert result == "tests/unit/test_example.py"

    def test_generate_pytest_template(self):
        """Test pytest template generation."""
        generator = TestGeneratorNode(trace_id="test-123")

        result = generator._generate_pytest_template(
            module_name="example",
            function_names=["foo", "bar"],
            source_file="src/example.py",
        )

        assert "import pytest" in result
        assert "def test_foo():" in result
        assert "def test_bar():" in result
        assert "Auto-generated by D-7 Test Generator" in result
        assert "Source file: src/example.py" in result

    def test_generate_jest_template(self):
        """Test Jest template generation."""
        generator = TestGeneratorNode(trace_id="test-123")

        result = generator._generate_jest_template(
            module_name="example",
            function_names=["foo", "bar"],
            source_file="src/example.ts",
        )

        assert "describe('example'" in result
        assert "describe('foo'" in result
        assert "describe('bar'" in result
        assert "Auto-generated by D-7 Test Generator" in result

    def test_generate_with_source_contents(self):
        """Test generation with provided source contents."""
        generator = TestGeneratorNode(trace_id="test-123", enable_llm=False)

        gaps = [
            {"file_path": "src/example.py", "function_name": "foo"},
        ]
        source_contents = {
            "src/example.py": "def foo(): pass"
        }

        result = generator.generate(
            coverage_gaps=gaps,
            repo_path="/tmp/repo",
            source_contents=source_contents,
        )

        assert len(result.generated_tests) == 1
        assert result.generated_tests[0].source_file_path == "src/example.py"
        assert "test_foo" in result.generated_tests[0].test_code

    def test_generate_with_file_on_disk(self):
        """Test generation with file on disk."""
        generator = TestGeneratorNode(trace_id="test-123", enable_llm=False)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create source file
            src_dir = os.path.join(tmpdir, "src")
            os.makedirs(src_dir)
            src_file = os.path.join(src_dir, "example.py")
            with open(src_file, "w") as f:
                f.write("def foo(): pass")

            gaps = [
                {"file_path": "src/example.py", "function_name": "foo"},
            ]

            result = generator.generate(
                coverage_gaps=gaps,
                repo_path=tmpdir,
            )

            assert len(result.generated_tests) == 1
            assert "test_foo" in result.generated_tests[0].test_code

    def test_generate_missing_source_file(self):
        """Test generation when source file is missing."""
        generator = TestGeneratorNode(trace_id="test-123", enable_llm=False)

        gaps = [
            {"file_path": "src/nonexistent.py", "function_name": "foo"},
        ]

        result = generator.generate(
            coverage_gaps=gaps,
            repo_path="/tmp/nonexistent",
        )

        assert len(result.generated_tests) == 0
        assert len(result.failed_generations) == 1
        assert result.failed_generations[0]["file_path"] == "src/nonexistent.py"

    def test_generate_respects_max_tests_per_run(self):
        """Test that generation respects max_tests_per_run limit."""
        generator = TestGeneratorNode(
            trace_id="test-123",
            max_tests_per_run=2,
            enable_llm=False,
        )

        gaps = [
            {"file_path": "src/a.py", "function_name": "foo"},
            {"file_path": "src/b.py", "function_name": "bar"},
            {"file_path": "src/c.py", "function_name": "baz"},
        ]
        source_contents = {
            "src/a.py": "def foo(): pass",
            "src/b.py": "def bar(): pass",
            "src/c.py": "def baz(): pass",
        }

        result = generator.generate(
            coverage_gaps=gaps,
            repo_path="/tmp/repo",
            source_contents=source_contents,
        )

        # Should only process 2 files due to max_tests_per_run=2
        assert len(result.generated_tests) == 2

    def test_framework_detection_python(self):
        """Test framework detection for Python files."""
        generator = TestGeneratorNode(trace_id="test-123")

        assert generator.FRAMEWORK_BY_EXTENSION[".py"] == "pytest"

    def test_framework_detection_typescript(self):
        """Test framework detection for TypeScript files."""
        generator = TestGeneratorNode(trace_id="test-123")

        assert generator.FRAMEWORK_BY_EXTENSION[".ts"] == "jest"
        assert generator.FRAMEWORK_BY_EXTENSION[".tsx"] == "jest"

    def test_framework_detection_javascript(self):
        """Test framework detection for JavaScript files."""
        generator = TestGeneratorNode(trace_id="test-123")

        assert generator.FRAMEWORK_BY_EXTENSION[".js"] == "jest"
        assert generator.FRAMEWORK_BY_EXTENSION[".jsx"] == "jest"


class TestGenerateTestsForCoverageGaps:
    """Tests for the synchronous wrapper function."""

    def test_basic_usage(self):
        """Test basic usage of the wrapper function."""
        gaps = [
            {"file_path": "src/example.py", "function_name": "foo"},
        ]
        source_contents = {
            "src/example.py": "def foo(): pass"
        }

        result = generate_tests_for_coverage_gaps(
            coverage_gaps=gaps,
            repo_path="/tmp/repo",
            trace_id="test-123",
            source_contents=source_contents,
            enable_llm=False,
        )

        assert result["total_generated"] == 1
        assert len(result["generated_tests"]) == 1

    def test_empty_gaps(self):
        """Test with empty coverage gaps."""
        result = generate_tests_for_coverage_gaps(
            coverage_gaps=[],
            repo_path="/tmp/repo",
            trace_id="test-123",
            enable_llm=False,
        )

        assert result["total_generated"] == 0
        assert result["summary"] == "No coverage gaps to generate tests for"

    def test_custom_max_tests(self):
        """Test with custom max_tests_per_run."""
        gaps = [
            {"file_path": "src/a.py", "function_name": "foo"},
            {"file_path": "src/b.py", "function_name": "bar"},
        ]
        source_contents = {
            "src/a.py": "def foo(): pass",
            "src/b.py": "def bar(): pass",
        }

        result = generate_tests_for_coverage_gaps(
            coverage_gaps=gaps,
            repo_path="/tmp/repo",
            trace_id="test-123",
            source_contents=source_contents,
            max_tests_per_run=1,
            enable_llm=False,
        )

        # Should only generate 1 test file due to max_tests_per_run=1
        assert result["total_generated"] == 1


class TestLLMIntegration:
    """Tests for LLM integration (mocked)."""

    @patch("test_generator_node.TestGeneratorNode._get_llm_generator")
    def test_llm_generation_success(self, mock_get_llm):
        """Test successful LLM-based test generation."""
        mock_generator = MagicMock()
        mock_generator.generate_tests.return_value = {
            "success": True,
            "data": {
                "test_code": "def test_foo(): assert True"
            }
        }
        mock_get_llm.return_value = mock_generator

        generator = TestGeneratorNode(trace_id="test-123", enable_llm=True)
        generator._llm_generator = mock_generator

        gaps = [
            {"file_path": "src/example.py", "function_name": "foo"},
        ]
        source_contents = {
            "src/example.py": "def foo(): pass"
        }

        result = generator.generate(
            coverage_gaps=gaps,
            repo_path="/tmp/repo",
            source_contents=source_contents,
        )

        assert len(result.generated_tests) == 1
        assert "test_foo" in result.generated_tests[0].test_code

    @patch("test_generator_node.TestGeneratorNode._get_llm_generator")
    def test_llm_generation_failure_fallback(self, mock_get_llm):
        """Test fallback to template when LLM fails."""
        mock_generator = MagicMock()
        mock_generator.generate_tests.side_effect = Exception("LLM error")
        mock_get_llm.return_value = mock_generator

        generator = TestGeneratorNode(trace_id="test-123", enable_llm=True)
        generator._llm_generator = mock_generator

        gaps = [
            {"file_path": "src/example.py", "function_name": "foo"},
        ]
        source_contents = {
            "src/example.py": "def foo(): pass"
        }

        result = generator.generate(
            coverage_gaps=gaps,
            repo_path="/tmp/repo",
            source_contents=source_contents,
        )

        # Should fall back to template generation
        assert len(result.generated_tests) == 1
        assert "test_foo" in result.generated_tests[0].test_code
        assert "TODO" in result.generated_tests[0].test_code  # Template has TODOs
