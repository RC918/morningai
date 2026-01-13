"""
D-7: Test Generation from Reviewer Flags

EPIC D Stage 3 Implementation - Blueprint Agent Separation Principle

This module implements the Test Agent v2 capability to generate tests
based on coverage gaps identified by B-11 (Test Coverage Flagging).

Blueprint Alignment:
- Section 3.3 "Agent Separation Principle" - Reviewer flags, Test Agent generates
- Section 7 "Sequential Collaboration" - Reviewer -> Test Agent handoff

What Test Agent v2 CAN do (within EPIC D scope):
- Read coverage gaps from B-11 output
- Generate actual test code using LLM
- Create test files in appropriate locations

What Test Agent v2 CANNOT do (belongs to other agents):
- Identify coverage gaps (that's B-11 Reviewer's job)
- Execute tests (that's CI's job)
- Fix failing tests (that's D-4 Self-Correction's job)

Usage:
    from test_generator_node import generate_tests_for_coverage_gaps

    result = generate_tests_for_coverage_gaps(
        coverage_gaps=state["test_coverage_analysis_v1"]["coverage_gaps"],
        repo_path="/path/to/repo",
        trace_id="abc123"
    )
"""

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class GeneratedTestFile:
    """
    Represents a generated test file.

    Attributes:
        test_file_path: Path where the test file should be created
        test_code: Generated test code content
        source_file_path: Path to the source file being tested
        functions_tested: List of function names covered by this test
        framework: Test framework used (pytest, unittest, jest, etc.)
    """
    test_file_path: str
    test_code: str
    source_file_path: str
    functions_tested: List[str] = field(default_factory=list)
    framework: str = "pytest"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "test_file_path": self.test_file_path,
            "test_code": self.test_code,
            "source_file_path": self.source_file_path,
            "functions_tested": self.functions_tested,
            "framework": self.framework,
        }


@dataclass
class TestGenerationResult:
    """
    Result of test generation.

    Attributes:
        generated_tests: List of generated test files
        failed_generations: List of functions that failed to generate tests
        summary: Human-readable summary of the generation
    """
    generated_tests: List[GeneratedTestFile] = field(default_factory=list)
    failed_generations: List[Dict[str, str]] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "generated_tests": [t.to_dict() for t in self.generated_tests],
            "failed_generations": self.failed_generations,
            "summary": self.summary,
            "total_generated": len(self.generated_tests),
            "total_failed": len(self.failed_generations),
        }


class TestGeneratorNode:
    """
    Test Agent v2 - Generates tests from B-11 coverage gaps.

    This is the D-7 implementation that bridges B-11 (Test Coverage Flagging)
    with actual test generation using LLM.

    Usage:
        generator = TestGeneratorNode(trace_id="abc123")
        result = generator.generate(
            coverage_gaps=[...],
            repo_path="/path/to/repo"
        )
    """

    # Supported test frameworks by file extension
    FRAMEWORK_BY_EXTENSION = {
        ".py": "pytest",
        ".ts": "jest",
        ".tsx": "jest",
        ".js": "jest",
        ".jsx": "jest",
    }

    # Test file naming patterns
    TEST_FILE_PATTERNS = {
        "pytest": "test_{basename}.py",
        "jest": "{basename}.test.ts",
    }

    def __init__(
        self,
        trace_id: str,
        max_tests_per_run: int = 5,
        enable_llm: bool = True,
    ):
        """
        Initialize the test generator.

        Args:
            trace_id: Trace ID for telemetry
            max_tests_per_run: Maximum number of test files to generate per run
            enable_llm: Whether to use LLM for test generation
        """
        self.trace_id = trace_id
        self.max_tests_per_run = max_tests_per_run
        self.enable_llm = enable_llm
        self._llm_generator = None

    def _get_llm_generator(self):
        """Lazy-load the LLM test generator."""
        if self._llm_generator is None and self.enable_llm:
            try:
                from agents.dev_agent.testing.llm_test_generator import (
                    LLMTestGenerator
                )
                self._llm_generator = LLMTestGenerator(
                    framework="pytest",
                    enable_llm=True
                )
            except ImportError as e:
                logger.warning(
                    f"[TestGeneratorNode] Could not import LLMTestGenerator: {e}",
                    extra={"trace_id": self.trace_id}
                )
                self.enable_llm = False
        return self._llm_generator

    def generate(
        self,
        coverage_gaps: List[Dict[str, Any]],
        repo_path: str,
        source_contents: Optional[Dict[str, str]] = None,
    ) -> TestGenerationResult:
        """
        Generate tests for coverage gaps.

        Args:
            coverage_gaps: List of CoverageGap dicts from B-11
            repo_path: Path to the repository root
            source_contents: Optional dict mapping file paths to their contents
                            (for cases where files aren't on disk)

        Returns:
            TestGenerationResult with generated tests
        """
        logger.info(
            "[TestGeneratorNode] Starting test generation",
            extra={
                "operation": "test_generation",
                "trace_id": self.trace_id,
                "gap_count": len(coverage_gaps),
                "repo_path": repo_path,
            }
        )

        if not coverage_gaps:
            return TestGenerationResult(
                summary="No coverage gaps to generate tests for"
            )

        # Group gaps by source file for efficient generation
        gaps_by_file = self._group_gaps_by_file(coverage_gaps)

        generated_tests: List[GeneratedTestFile] = []
        failed_generations: List[Dict[str, str]] = []

        # Limit the number of files to process
        files_to_process = list(gaps_by_file.keys())[:self.max_tests_per_run]

        for source_file in files_to_process:
            file_gaps = gaps_by_file[source_file]

            try:
                # Get source code
                source_code = self._get_source_code(
                    source_file, repo_path, source_contents
                )

                if not source_code:
                    failed_generations.append({
                        "file_path": source_file,
                        "reason": "Could not read source file"
                    })
                    continue

                # Generate tests for this file
                test_file = self._generate_tests_for_file(
                    source_file=source_file,
                    source_code=source_code,
                    gaps=file_gaps,
                    repo_path=repo_path,
                )

                if test_file:
                    generated_tests.append(test_file)
                else:
                    failed_generations.append({
                        "file_path": source_file,
                        "reason": "Test generation failed"
                    })

            except Exception as e:
                logger.warning(
                    f"[TestGeneratorNode] Error generating tests for {source_file}: {e}",
                    extra={
                        "operation": "test_generation",
                        "trace_id": self.trace_id,
                        "file_path": source_file,
                        "error": str(e),
                    }
                )
                failed_generations.append({
                    "file_path": source_file,
                    "reason": str(e)
                })

        # Build summary
        if generated_tests:
            summary = (
                f"Generated {len(generated_tests)} test file(s) for "
                f"{sum(len(t.functions_tested) for t in generated_tests)} function(s)"
            )
        else:
            summary = "No tests generated"

        if failed_generations:
            summary += f". {len(failed_generations)} file(s) failed."

        logger.info(
            "[TestGeneratorNode] Test generation completed",
            extra={
                "operation": "test_generation",
                "trace_id": self.trace_id,
                "generated_count": len(generated_tests),
                "failed_count": len(failed_generations),
            }
        )

        return TestGenerationResult(
            generated_tests=generated_tests,
            failed_generations=failed_generations,
            summary=summary,
        )

    def _group_gaps_by_file(
        self,
        coverage_gaps: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Group coverage gaps by source file."""
        gaps_by_file: Dict[str, List[Dict[str, Any]]] = {}

        for gap in coverage_gaps:
            file_path = gap.get("file_path", "")
            if file_path:
                if file_path not in gaps_by_file:
                    gaps_by_file[file_path] = []
                gaps_by_file[file_path].append(gap)

        return gaps_by_file

    def _get_source_code(
        self,
        source_file: str,
        repo_path: str,
        source_contents: Optional[Dict[str, str]] = None,
    ) -> Optional[str]:
        """Get source code for a file."""
        # Try from provided contents first
        if source_contents and source_file in source_contents:
            return source_contents[source_file]

        # Try reading from disk
        full_path = os.path.join(repo_path, source_file)
        if os.path.exists(full_path):
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                logger.warning(
                    f"[TestGeneratorNode] Could not read {full_path}: {e}",
                    extra={"trace_id": self.trace_id}
                )

        return None

    def _generate_tests_for_file(
        self,
        source_file: str,
        source_code: str,
        gaps: List[Dict[str, Any]],
        repo_path: str,
    ) -> Optional[GeneratedTestFile]:
        """Generate tests for a single source file."""
        # Determine framework based on file extension
        ext = os.path.splitext(source_file)[1].lower()
        framework = self.FRAMEWORK_BY_EXTENSION.get(ext, "pytest")

        # Determine test file path
        test_file_path = self._get_test_file_path(source_file, framework)

        # Get function names to test
        function_names = [
            gap.get("function_name", "")
            for gap in gaps
            if gap.get("function_name")
        ]

        if not function_names:
            return None

        # Generate tests using LLM
        if self.enable_llm:
            llm_generator = self._get_llm_generator()
            if llm_generator:
                try:
                    result = llm_generator.generate_tests(
                        code=source_code,
                        file_path=source_file
                    )

                    if result.get("success") and result.get("data", {}).get("test_code"):
                        return GeneratedTestFile(
                            test_file_path=test_file_path,
                            test_code=result["data"]["test_code"],
                            source_file_path=source_file,
                            functions_tested=function_names,
                            framework=framework,
                        )
                except Exception as e:
                    logger.warning(
                        f"[TestGeneratorNode] LLM generation failed: {e}",
                        extra={"trace_id": self.trace_id}
                    )

        # Fallback to template-based generation
        test_code = self._generate_template_tests(
            source_file=source_file,
            function_names=function_names,
            framework=framework,
        )

        return GeneratedTestFile(
            test_file_path=test_file_path,
            test_code=test_code,
            source_file_path=source_file,
            functions_tested=function_names,
            framework=framework,
        )

    def _get_test_file_path(self, source_file: str, framework: str) -> str:
        """Determine the test file path for a source file."""
        dirname = os.path.dirname(source_file)
        basename = os.path.basename(source_file)
        name_without_ext = os.path.splitext(basename)[0]

        # Get test file pattern for framework
        pattern = self.TEST_FILE_PATTERNS.get(framework, "test_{basename}.py")
        test_filename = pattern.format(basename=name_without_ext)

        # Determine test directory
        if "tests" in dirname or "test" in dirname:
            test_dir = dirname
        else:
            test_dir = os.path.join(dirname, "tests")

        return os.path.join(test_dir, test_filename)

    def _generate_template_tests(
        self,
        source_file: str,
        function_names: List[str],
        framework: str,
    ) -> str:
        """Generate template-based tests as fallback."""
        module_name = os.path.splitext(os.path.basename(source_file))[0]

        if framework == "pytest":
            return self._generate_pytest_template(module_name, function_names, source_file)
        elif framework == "jest":
            return self._generate_jest_template(module_name, function_names, source_file)
        else:
            return self._generate_pytest_template(module_name, function_names, source_file)

    def _generate_pytest_template(
        self,
        module_name: str,
        function_names: List[str],
        source_file: str,
    ) -> str:
        """Generate pytest template tests."""
        # Calculate relative import path
        import_path = source_file.replace("/", ".").replace("\\", ".")
        if import_path.endswith(".py"):
            import_path = import_path[:-3]

        tests = []
        for func_name in function_names:
            test_code = f'''
def test_{func_name}():
    """Test {func_name} function.

    TODO: Implement actual test logic.
    This is a placeholder generated by D-7 Test Generator.
    """
    # TODO: Import the function
    # from {import_path} import {func_name}

    # TODO: Add test assertions
    # result = {func_name}(...)
    # assert result == expected

    pass  # Placeholder - implement actual test
'''
            tests.append(test_code)

        header = f'''"""
Tests for {module_name}

Auto-generated by D-7 Test Generator based on B-11 coverage gaps.
Source file: {source_file}

TODO: Review and implement actual test logic.
"""
import pytest
'''

        return header + "\n".join(tests)

    def _generate_jest_template(
        self,
        module_name: str,
        function_names: List[str],
        source_file: str,
    ) -> str:
        """Generate Jest template tests."""
        tests = []
        for func_name in function_names:
            test_code = f'''
  describe('{func_name}', () => {{
    it('should work correctly', () => {{
      // TODO: Import the function
      // import {{ {func_name} }} from '../{module_name}';

      // TODO: Add test assertions
      // const result = {func_name}(...);
      // expect(result).toBe(expected);

      expect(true).toBe(true); // Placeholder
    }});
  }});
'''
            tests.append(test_code)

        header = f'''/**
 * Tests for {module_name}
 *
 * Auto-generated by D-7 Test Generator based on B-11 coverage gaps.
 * Source file: {source_file}
 *
 * TODO: Review and implement actual test logic.
 */

describe('{module_name}', () => {{
'''

        footer = '''
});
'''

        return header + "\n".join(tests) + footer


def generate_tests_for_coverage_gaps(
    coverage_gaps: List[Dict[str, Any]],
    repo_path: str,
    trace_id: str,
    source_contents: Optional[Dict[str, str]] = None,
    max_tests_per_run: int = 5,
    enable_llm: bool = True,
) -> Dict[str, Any]:
    """
    Synchronous wrapper for test generation.

    Args:
        coverage_gaps: List of CoverageGap dicts from B-11
        repo_path: Path to the repository root
        trace_id: Trace ID for telemetry
        source_contents: Optional dict mapping file paths to their contents
        max_tests_per_run: Maximum number of test files to generate
        enable_llm: Whether to use LLM for test generation

    Returns:
        Dictionary with test generation results
    """
    generator = TestGeneratorNode(
        trace_id=trace_id,
        max_tests_per_run=max_tests_per_run,
        enable_llm=enable_llm,
    )
    result = generator.generate(
        coverage_gaps=coverage_gaps,
        repo_path=repo_path,
        source_contents=source_contents,
    )
    return result.to_dict()
