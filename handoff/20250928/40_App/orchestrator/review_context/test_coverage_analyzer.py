"""
B-11: Test Coverage Flagging

EPIC B Phase 8 Implementation - Blueprint Agent Separation Principle

This module analyzes PR diffs to identify functions/classes that lack test coverage
and flags them in the review. It does NOT generate test code (that belongs to
Test Agent v2 per Blueprint Section 3.3).

Blueprint Alignment:
- Section 3.3 "Agent Separation Principle" - Reviewer flags, doesn't generate
- Reviewer Agent -> Test Agent v2 handoff for test generation

What Reviewer Agent CAN do (within EPIC B scope):
- Detect functions/classes without test coverage
- Flag missing test coverage in review
- Describe what tests are needed (text)

What Reviewer Agent CANNOT do (belongs to Test Agent v2):
- Generate actual test code
- Execute tests
- Validate test results

Usage:
    from review_context.test_coverage_analyzer import TestCoverageAnalyzer

    analyzer = TestCoverageAnalyzer(trace_id="abc123")
    gaps = analyzer.analyze(diff_content="...", diff_files=["src/foo.py"])
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class CoverageGap:
    """
    Represents a test coverage gap identified by the analyzer.

    Attributes:
        function_name: Name of the function/method lacking tests
        file_path: Path to the file containing the function
        line_number: Line number where the function is defined
        function_type: Type of function (function, method, class)
        reason: Why this needs test coverage
        suggested_test_types: Types of tests recommended (unit, integration, etc.)
    """
    function_name: str
    file_path: str
    line_number: Optional[int] = None
    function_type: str = "function"
    reason: str = "New code without corresponding test"
    suggested_test_types: List[str] = field(default_factory=lambda: ["unit"])

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "function_name": self.function_name,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "function_type": self.function_type,
            "reason": self.reason,
            "suggested_test_types": self.suggested_test_types,
        }


@dataclass
class TestCoverageAnalysis:
    """
    Result of test coverage analysis.

    Attributes:
        coverage_gaps: List of identified coverage gaps
        analyzed_files: List of files that were analyzed
        test_files_found: List of test files found in the diff
        summary: Human-readable summary of the analysis
    """
    coverage_gaps: List[CoverageGap] = field(default_factory=list)
    analyzed_files: List[str] = field(default_factory=list)
    test_files_found: List[str] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "coverage_gaps": [g.to_dict() for g in self.coverage_gaps],
            "analyzed_files": self.analyzed_files,
            "test_files_found": self.test_files_found,
            "summary": self.summary,
            "gap_count": len(self.coverage_gaps),
        }


class TestCoverageAnalyzer:
    """
    Analyzes PR diffs to identify test coverage gaps.

    This analyzer parses the diff to find new/modified functions and checks
    if corresponding test files exist. It flags missing coverage but does
    NOT generate test code (per Blueprint Agent Separation Principle).

    Usage:
        analyzer = TestCoverageAnalyzer(trace_id="abc123")
        analysis = analyzer.analyze(diff_content="...", diff_files=["src/foo.py"])
    """

    # Patterns for identifying test files
    TEST_FILE_PATTERNS = [
        r'test_.*\.py$',
        r'.*_test\.py$',
        r'.*\.test\.(ts|tsx|js|jsx)$',
        r'.*\.spec\.(ts|tsx|js|jsx)$',
        r'tests?/.*\.(py|ts|tsx|js|jsx)$',
        r'__tests__/.*\.(ts|tsx|js|jsx)$',
    ]

    # Patterns for identifying function/class definitions in Python
    PYTHON_FUNCTION_PATTERN = re.compile(
        r'^\+\s*(async\s+)?def\s+(\w+)\s*\(',
        re.MULTILINE
    )
    PYTHON_CLASS_PATTERN = re.compile(
        r'^\+\s*class\s+(\w+)\s*[:\(]',
        re.MULTILINE
    )

    # Patterns for identifying function/class definitions in TypeScript/JavaScript
    TS_FUNCTION_PATTERN = re.compile(
        r'^\+\s*(export\s+)?(async\s+)?function\s+(\w+)\s*[<\(]',
        re.MULTILINE
    )
    TS_ARROW_FUNCTION_PATTERN = re.compile(
        r'^\+\s*(export\s+)?(const|let)\s+(\w+)\s*=\s*(async\s+)?\([^)]*\)\s*=>',
        re.MULTILINE
    )
    TS_CLASS_PATTERN = re.compile(
        r'^\+\s*(export\s+)?class\s+(\w+)',
        re.MULTILINE
    )

    def __init__(self, trace_id: str):
        """
        Initialize the test coverage analyzer.

        Args:
            trace_id: Trace ID for telemetry
        """
        self.trace_id = trace_id

    def analyze(
        self,
        diff_content: str,
        diff_files: Optional[List[str]] = None,
    ) -> TestCoverageAnalysis:
        """
        Analyze the diff for test coverage gaps.

        Args:
            diff_content: The PR diff content
            diff_files: Optional list of files in the diff

        Returns:
            TestCoverageAnalysis with identified coverage gaps
        """
        logger.info(
            "[TestCoverageAnalyzer] Starting analysis",
            extra={
                "operation": "test_coverage_analysis",
                "trace_id": self.trace_id,
                "diff_length": len(diff_content) if diff_content else 0,
            }
        )

        if not diff_content:
            return TestCoverageAnalysis(summary="No diff content to analyze")

        # Parse diff into file sections
        file_diffs = self._parse_diff_by_file(diff_content)

        # Identify test files and source files
        test_files: List[str] = []
        source_files: List[str] = []

        for file_path in file_diffs.keys():
            if self._is_test_file(file_path):
                test_files.append(file_path)
            else:
                source_files.append(file_path)

        # Find new functions/classes in source files
        coverage_gaps: List[CoverageGap] = []

        for file_path in source_files:
            file_diff = file_diffs[file_path]
            gaps = self._find_coverage_gaps(file_path, file_diff, test_files, file_diffs)
            coverage_gaps.extend(gaps)

        # Generate summary
        if coverage_gaps:
            summary = (
                f"Found {len(coverage_gaps)} functions/classes without test coverage. "
                f"Consider adding tests for: {', '.join(g.function_name for g in coverage_gaps[:5])}"
                + ("..." if len(coverage_gaps) > 5 else "")
            )
        else:
            summary = "All new functions/classes appear to have corresponding tests."

        logger.info(
            "[TestCoverageAnalyzer] Analysis completed",
            extra={
                "operation": "test_coverage_analysis",
                "trace_id": self.trace_id,
                "gap_count": len(coverage_gaps),
                "source_files": len(source_files),
                "test_files": len(test_files),
            }
        )

        return TestCoverageAnalysis(
            coverage_gaps=coverage_gaps,
            analyzed_files=source_files,
            test_files_found=test_files,
            summary=summary,
        )

    def _parse_diff_by_file(self, diff_content: str) -> Dict[str, str]:
        """Parse diff content into per-file sections."""
        file_diffs: Dict[str, str] = {}
        current_file: Optional[str] = None
        current_content: List[str] = []

        for line in diff_content.split('\n'):
            # Match diff header: diff --git a/path/to/file b/path/to/file
            if line.startswith('diff --git'):
                if current_file:
                    file_diffs[current_file] = '\n'.join(current_content)
                # Extract file path from diff header
                match = re.search(r'b/(.+)$', line)
                if match:
                    current_file = match.group(1)
                    current_content = [line]
                else:
                    current_file = None
                    current_content = []
            elif current_file:
                current_content.append(line)

        # Don't forget the last file
        if current_file:
            file_diffs[current_file] = '\n'.join(current_content)

        return file_diffs

    def _is_test_file(self, file_path: str) -> bool:
        """Check if a file path is a test file."""
        for pattern in self.TEST_FILE_PATTERNS:
            if re.search(pattern, file_path, re.IGNORECASE):
                return True
        return False

    def _find_coverage_gaps(
        self,
        file_path: str,
        file_diff: str,
        test_files: List[str],
        file_diffs: Dict[str, str],
    ) -> List[CoverageGap]:
        """Find functions/classes in the diff that lack test coverage."""
        gaps: List[CoverageGap] = []

        # Determine file type
        is_python = file_path.endswith('.py')
        is_typescript = file_path.endswith(('.ts', '.tsx', '.js', '.jsx'))

        if is_python:
            gaps.extend(self._find_python_gaps(file_path, file_diff, test_files, file_diffs))
        elif is_typescript:
            gaps.extend(self._find_typescript_gaps(file_path, file_diff, test_files, file_diffs))

        return gaps

    def _find_python_gaps(
        self,
        file_path: str,
        file_diff: str,
        test_files: List[str],
        file_diffs: Dict[str, str],
    ) -> List[CoverageGap]:
        """Find Python functions/classes without test coverage."""
        gaps: List[CoverageGap] = []

        # Find new functions
        for match in self.PYTHON_FUNCTION_PATTERN.finditer(file_diff):
            func_name = match.group(2)
            # Skip private/dunder methods (usually tested indirectly)
            if func_name.startswith('__') and func_name.endswith('__'):
                continue
            if not self._has_test_for_function(func_name, test_files, file_diffs):
                gaps.append(CoverageGap(
                    function_name=func_name,
                    file_path=file_path,
                    function_type="function",
                    reason="New function without corresponding test",
                    suggested_test_types=["unit"],
                ))

        # Find new classes
        for match in self.PYTHON_CLASS_PATTERN.finditer(file_diff):
            class_name = match.group(1)
            if not self._has_test_for_function(class_name, test_files, file_diffs):
                gaps.append(CoverageGap(
                    function_name=class_name,
                    file_path=file_path,
                    function_type="class",
                    reason="New class without corresponding test",
                    suggested_test_types=["unit", "integration"],
                ))

        return gaps

    def _find_typescript_gaps(
        self,
        file_path: str,
        file_diff: str,
        test_files: List[str],
        file_diffs: Dict[str, str],
    ) -> List[CoverageGap]:
        """Find TypeScript/JavaScript functions/classes without test coverage."""
        gaps: List[CoverageGap] = []

        # Find new functions
        for match in self.TS_FUNCTION_PATTERN.finditer(file_diff):
            func_name = match.group(3)
            if not self._has_test_for_function(func_name, test_files, file_diffs):
                gaps.append(CoverageGap(
                    function_name=func_name,
                    file_path=file_path,
                    function_type="function",
                    reason="New function without corresponding test",
                    suggested_test_types=["unit"],
                ))

        # Find new arrow functions
        for match in self.TS_ARROW_FUNCTION_PATTERN.finditer(file_diff):
            func_name = match.group(3)
            if not self._has_test_for_function(func_name, test_files, file_diffs):
                gaps.append(CoverageGap(
                    function_name=func_name,
                    file_path=file_path,
                    function_type="function",
                    reason="New arrow function without corresponding test",
                    suggested_test_types=["unit"],
                ))

        # Find new classes
        for match in self.TS_CLASS_PATTERN.finditer(file_diff):
            class_name = match.group(2)
            if not self._has_test_for_function(class_name, test_files, file_diffs):
                gaps.append(CoverageGap(
                    function_name=class_name,
                    file_path=file_path,
                    function_type="class",
                    reason="New class without corresponding test",
                    suggested_test_types=["unit", "integration"],
                ))

        return gaps

    def _has_test_for_function(
        self,
        func_name: str,
        test_files: List[str],
        file_diffs: Dict[str, str],
    ) -> bool:
        """
        Check if a function/class has a corresponding test in any of the test file diffs.

        This is a heuristic check that looks for:
        1. Test files with the function name in the diff
        2. Test function names like test_<func_name> in the diff

        Args:
            func_name: Name of the function/class to check
            test_files: List of test file paths in the diff
            file_diffs: Dictionary mapping file paths to their diff content
        """
        test_patterns = [
            f'test_{func_name}',
            f'Test{func_name}',
            f'{func_name}Test',
            f'{func_name}Spec',
            f"describe('{func_name}'",
            f'describe("{func_name}"',
            f"it('{func_name}",
            f'it("{func_name}',
        ]

        for test_file_path in test_files:
            test_file_diff = file_diffs.get(test_file_path, "")
            if not test_file_diff:
                continue

            test_file_diff_lower = test_file_diff.lower()
            for pattern in test_patterns:
                if pattern.lower() in test_file_diff_lower:
                    return True

        return False


def analyze_test_coverage(
    diff_content: str,
    diff_files: Optional[List[str]],
    trace_id: str,
) -> Dict[str, Any]:
    """
    Synchronous wrapper for test coverage analysis.

    Args:
        diff_content: The PR diff content
        diff_files: Optional list of files in the diff
        trace_id: Trace ID for telemetry

    Returns:
        Dictionary with coverage analysis results
    """
    analyzer = TestCoverageAnalyzer(trace_id=trace_id)
    analysis = analyzer.analyze(diff_content, diff_files)
    return analysis.to_dict()
