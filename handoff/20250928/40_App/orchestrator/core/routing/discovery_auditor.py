"""
Discovery Auditor - Reviewer Agent capability for test discovery audit.

Issue #3310: Discovery 全鏈路治理 - Layer 2 (Reviewer Agent Auditor)

This module provides the DiscoveryAuditor capability that enables the Reviewer Agent
to cross-reference PR diffs with CI logs to detect "silent failures" - cases where
new test files are added but not executed in CI.

Architecture:
    PR Diff → Extract test files → CI Logs → Extract executed tests → Cross-reference

    If new_test_files - executed_tests != empty:
        → Request Changes with specific file list

Blueprint Alignment:
    - Deterministic: Uses exact file matching, no LLM inference
    - Safe by Design: Prevents silent test failures from reaching production
    - Self-Governed: Automated detection without human intervention
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Set


class AuditStatus(Enum):
    """Status of the discovery audit."""
    APPROVED = "APPROVED"
    REQUEST_CHANGES = "REQUEST_CHANGES"
    SKIPPED = "SKIPPED"  # No test files in diff


@dataclass
class AuditResult:
    """Result of the discovery audit.

    Attributes:
        status: The audit status (APPROVED, REQUEST_CHANGES, or SKIPPED)
        message: Human-readable message explaining the result
        missing_tests: List of test files that were not executed
        new_test_files: List of new/modified test files found in diff
        executed_tests: List of tests found in CI logs
    """
    status: AuditStatus
    message: str
    missing_tests: List[str] = field(default_factory=list)
    new_test_files: List[str] = field(default_factory=list)
    executed_tests: List[str] = field(default_factory=list)

    def to_review_comment(self) -> Optional[str]:
        """Generate a review comment for REQUEST_CHANGES status.

        Returns:
            Review comment string if status is REQUEST_CHANGES, None otherwise.
        """
        if self.status != AuditStatus.REQUEST_CHANGES:
            return None

        comment_lines = [
            "## Discovery Audit: Silent Failure Detected",
            "",
            "The following test files were added/modified in this PR but were **not executed** in CI:",
            "",
        ]

        for test_file in self.missing_tests:
            comment_lines.append(f"- `{test_file}`")

        comment_lines.extend([
            "",
            "### Possible Causes",
            "1. Test directory not listed in `pytest.ini` testpaths",
            "2. Test file naming doesn't match `test_*.py` pattern",
            "3. Test collection error (check CI logs for import errors)",
            "",
            "### How to Fix",
            "1. Verify the test directory is in `pytest.ini` under `testpaths`",
            "2. Check CI logs for collection errors",
            "3. Run `pytest --collect-only` locally to verify discovery",
            "",
            "---",
            "*This check is part of [Discovery 全鏈路治理](https://github.com/RC918/morningai/issues/3310)*",
        ])

        return "\n".join(comment_lines)


class DiscoveryAuditor:
    """Reviewer Agent capability for Discovery audit.

    Cross-references PR diff with CI logs to detect silent test failures.
    This is Layer 2 of the dual-layer verification system (Issue #3310).

    Layer 1 (CI Gatekeeper): Ensures all test directories are in pytest.ini
    Layer 2 (This): Ensures all new test files are actually executed

    Example:
        >>> auditor = DiscoveryAuditor()
        >>> result = auditor.audit_test_execution(pr_diff, ci_logs)
        >>> if result.status == AuditStatus.REQUEST_CHANGES:
        ...     post_review_comment(result.to_review_comment())
    """

    # Pattern to match test file paths in git diff
    # Matches: +++ b/path/to/test_something.py or --- a/path/to/test_something.py
    DIFF_FILE_PATTERN = re.compile(r'^[+-]{3} [ab]/(.+/test_[^/]+\.py)$', re.MULTILINE)

    # Pattern to match new files in git diff (files that didn't exist before)
    NEW_FILE_PATTERN = re.compile(r'^--- /dev/null\n\+\+\+ b/(.+/test_[^/]+\.py)$', re.MULTILINE)

    # Pattern to match modified test files (both --- and +++ have paths)
    MODIFIED_FILE_PATTERN = re.compile(
        r'^--- a/(.+/test_[^/]+\.py)\n\+\+\+ b/\1$',
        re.MULTILINE
    )

    # Patterns to extract executed tests from CI logs
    # pytest collection output: <Module path/to/test_file.py>
    PYTEST_COLLECTION_PATTERN = re.compile(r'<Module ([^>]+\.py)>')

    # pytest execution output: path/to/test_file.py::TestClass::test_method
    PYTEST_EXECUTION_PATTERN = re.compile(r'^([^\s:]+\.py)::', re.MULTILINE)

    # pytest summary: PASSED/FAILED path/to/test_file.py::test_name
    PYTEST_RESULT_PATTERN = re.compile(r'(?:PASSED|FAILED|ERROR|SKIPPED)\s+([^\s:]+\.py)::', re.MULTILINE)

    def audit_test_execution(
        self,
        pr_diff: str,
        ci_logs: str,
        base_path: str = "handoff/20250928/40_App/orchestrator/"
    ) -> AuditResult:
        """Cross-reference PR diff with CI logs to detect silent failures.

        Args:
            pr_diff: Git diff of the PR (unified diff format)
            ci_logs: CI test collection/execution logs
            base_path: Base path prefix to strip from file paths for matching

        Returns:
            AuditResult with status and any missing test executions
        """
        # 1. Extract test files from diff
        new_test_files = self._extract_test_files_from_diff(pr_diff)

        if not new_test_files:
            return AuditResult(
                status=AuditStatus.SKIPPED,
                message="No test files found in PR diff",
                new_test_files=[],
                executed_tests=[]
            )

        # 2. Extract executed tests from CI logs
        executed_tests = self._extract_executed_tests_from_logs(ci_logs)

        # 3. Normalize paths for comparison
        normalized_new_tests = self._normalize_paths(new_test_files, base_path)
        normalized_executed = self._normalize_paths(executed_tests, base_path)

        # 4. Cross-reference: find tests in diff but not in CI logs
        missing_tests = normalized_new_tests - normalized_executed

        if missing_tests:
            return AuditResult(
                status=AuditStatus.REQUEST_CHANGES,
                message=f"Silent failure detected: {len(missing_tests)} test file(s) not executed in CI",
                missing_tests=sorted(missing_tests),
                new_test_files=sorted(normalized_new_tests),
                executed_tests=sorted(normalized_executed)
            )

        return AuditResult(
            status=AuditStatus.APPROVED,
            message=f"All {len(normalized_new_tests)} test file(s) in diff were executed in CI",
            new_test_files=sorted(normalized_new_tests),
            executed_tests=sorted(normalized_executed)
        )

    def _extract_test_files_from_diff(self, pr_diff: str) -> Set[str]:
        """Extract test file paths from git diff.

        Extracts both new files (--- /dev/null) and modified files.
        Only includes files matching test_*.py pattern.

        Args:
            pr_diff: Git diff in unified format

        Returns:
            Set of test file paths found in the diff
        """
        test_files: Set[str] = set()

        # Find all +++ b/path lines for test files
        for match in self.DIFF_FILE_PATTERN.finditer(pr_diff):
            file_path = match.group(1)
            # Only include if it's a test file (test_*.py)
            if '/test_' in file_path and file_path.endswith('.py'):
                test_files.add(file_path)

        return test_files

    def _extract_executed_tests_from_logs(self, ci_logs: str) -> Set[str]:
        """Extract executed test file paths from CI logs.

        Parses pytest output to find which test files were actually executed.
        Handles multiple output formats:
        - Collection output: <Module path/to/test.py>
        - Execution output: path/to/test.py::TestClass::test_method
        - Result output: PASSED/FAILED path/to/test.py::test_name

        Args:
            ci_logs: CI test execution logs

        Returns:
            Set of test file paths that were executed
        """
        executed_tests: Set[str] = set()

        # Try collection pattern
        for match in self.PYTEST_COLLECTION_PATTERN.finditer(ci_logs):
            executed_tests.add(match.group(1))

        # Try execution pattern
        for match in self.PYTEST_EXECUTION_PATTERN.finditer(ci_logs):
            executed_tests.add(match.group(1))

        # Try result pattern
        for match in self.PYTEST_RESULT_PATTERN.finditer(ci_logs):
            executed_tests.add(match.group(1))

        return executed_tests

    def _normalize_paths(self, paths: Set[str], base_path: str) -> Set[str]:
        """Normalize file paths for comparison.

        Strips the base_path prefix and normalizes path separators.

        Args:
            paths: Set of file paths to normalize
            base_path: Base path prefix to strip

        Returns:
            Set of normalized paths
        """
        normalized: Set[str] = set()

        for path in paths:
            # Strip base path prefix if present
            if path.startswith(base_path):
                path = path[len(base_path):]

            # Also try without leading slash
            if path.startswith('/'):
                path = path[1:]

            # Normalize path separators
            path = path.replace('\\', '/')

            normalized.add(path)

        return normalized


def create_discovery_auditor() -> DiscoveryAuditor:
    """Factory function to create a DiscoveryAuditor instance.

    Returns:
        Configured DiscoveryAuditor instance
    """
    return DiscoveryAuditor()
