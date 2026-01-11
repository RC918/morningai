"""
B-12: Dependency Analysis (Flagging Only)

EPIC B Phase 8 Implementation - Blueprint Agent Separation Principle

This module analyzes PR diffs to identify dependency issues (outdated deps,
vulnerabilities, license issues) and flags them in the review. It does NOT
update dependencies (that belongs to Coding Agent per Blueprint Section 3.3).

Blueprint Alignment:
- Section 3.3 "Agent Separation Principle" - Reviewer flags, doesn't fix
- Reviewer Agent can only FLAG dependency issues, not update them

What Reviewer Agent CAN do (within EPIC B scope):
- Flag outdated dependencies
- Flag known vulnerabilities
- Flag license issues
- Recommend actions (text descriptions)

What Reviewer Agent CANNOT do (belongs to Coding Agent):
- Update package.json/requirements.txt
- Run npm update/pip install
- Apply dependency fixes

Usage:
    from review_context.dependency_analyzer import DependencyAnalyzer

    analyzer = DependencyAnalyzer(trace_id="abc123")
    issues = analyzer.analyze(diff_content="...", diff_files=["package.json"])
"""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class DependencyIssueType(Enum):
    """Types of dependency issues that can be flagged."""
    OUTDATED = "outdated"
    VULNERABILITY = "vulnerability"
    LICENSE = "license"
    DEPRECATED = "deprecated"
    UNPINNED = "unpinned"
    DUPLICATE = "duplicate"


@dataclass
class DependencyIssue:
    """
    Represents a dependency issue identified by the analyzer.

    Attributes:
        package_name: Name of the package with the issue
        issue_type: Type of dependency issue
        severity: Issue severity (low, medium, high, critical)
        message: Human-readable description of the issue
        file_path: Path to the dependency file
        current_version: Current version in the project (if applicable)
        recommended_action: Text description of recommended action (NOT code)
    """
    package_name: str
    issue_type: DependencyIssueType
    severity: str
    message: str
    file_path: str
    current_version: Optional[str] = None
    recommended_action: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "package_name": self.package_name,
            "issue_type": self.issue_type.value,
            "severity": self.severity,
            "message": self.message,
            "file_path": self.file_path,
            "current_version": self.current_version,
            "recommended_action": self.recommended_action,
        }


@dataclass
class DependencyAnalysis:
    """
    Result of dependency analysis.

    Attributes:
        issues: List of identified dependency issues
        analyzed_files: List of dependency files that were analyzed
        summary: Human-readable summary of the analysis
        new_dependencies: List of newly added dependencies
        removed_dependencies: List of removed dependencies
    """
    issues: List[DependencyIssue] = field(default_factory=list)
    analyzed_files: List[str] = field(default_factory=list)
    summary: str = ""
    new_dependencies: List[str] = field(default_factory=list)
    removed_dependencies: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "issues": [i.to_dict() for i in self.issues],
            "analyzed_files": self.analyzed_files,
            "summary": self.summary,
            "new_dependencies": self.new_dependencies,
            "removed_dependencies": self.removed_dependencies,
            "issue_count": len(self.issues),
        }


class DependencyAnalyzer:
    """
    Analyzes PR diffs to identify dependency issues.

    This analyzer parses dependency files (package.json, requirements.txt,
    pyproject.toml) and flags potential issues. It does NOT update
    dependencies (per Blueprint Agent Separation Principle).

    Usage:
        analyzer = DependencyAnalyzer(trace_id="abc123")
        analysis = analyzer.analyze(diff_content="...", diff_files=["package.json"])
    """

    # Dependency file patterns
    DEPENDENCY_FILE_PATTERNS = [
        r'package\.json$',
        r'package-lock\.json$',
        r'yarn\.lock$',
        r'pnpm-lock\.yaml$',
        r'requirements\.txt$',
        r'requirements.*\.txt$',
        r'pyproject\.toml$',
        r'Pipfile$',
        r'Pipfile\.lock$',
        r'poetry\.lock$',
        r'Cargo\.toml$',
        r'Cargo\.lock$',
        r'go\.mod$',
        r'go\.sum$',
    ]

    # Known deprecated packages (sample list - in production, use external API)
    DEPRECATED_PACKAGES = {
        # npm
        "request": "Use 'node-fetch' or 'axios' instead",
        "moment": "Use 'date-fns' or 'dayjs' instead",
        "lodash": "Consider native JS methods or 'lodash-es' for tree-shaking",
        # Python
        "nose": "Use 'pytest' instead",
        "pycrypto": "Use 'pycryptodome' instead",
    }

    # Patterns that indicate unpinned versions
    UNPINNED_PATTERNS = [
        r'^\*$',
        r'^latest$',
        r'^\^',  # npm caret range
        r'^~',   # npm tilde range
        r'^>=',  # Python greater than or equal
        r'^>',   # Python greater than
    ]

    def __init__(self, trace_id: str):
        """
        Initialize the dependency analyzer.

        Args:
            trace_id: Trace ID for telemetry
        """
        self.trace_id = trace_id

    def analyze(
        self,
        diff_content: str,
        diff_files: Optional[List[str]] = None,
    ) -> DependencyAnalysis:
        """
        Analyze the diff for dependency issues.

        Args:
            diff_content: The PR diff content
            diff_files: Optional list of files in the diff

        Returns:
            DependencyAnalysis with identified issues
        """
        logger.info(
            "[DependencyAnalyzer] Starting analysis",
            extra={
                "operation": "dependency_analysis",
                "trace_id": self.trace_id,
                "diff_length": len(diff_content) if diff_content else 0,
            }
        )

        if not diff_content:
            return DependencyAnalysis(summary="No diff content to analyze")

        # Parse diff into file sections
        file_diffs = self._parse_diff_by_file(diff_content)

        # Find dependency files
        dependency_files: List[str] = []
        for file_path in file_diffs.keys():
            if self._is_dependency_file(file_path):
                dependency_files.append(file_path)

        if not dependency_files:
            return DependencyAnalysis(
                summary="No dependency files modified in this PR"
            )

        # Analyze each dependency file
        all_issues: List[DependencyIssue] = []
        new_deps: List[str] = []
        removed_deps: List[str] = []

        for file_path in dependency_files:
            file_diff = file_diffs[file_path]
            issues, added, removed = self._analyze_dependency_file(
                file_path, file_diff
            )
            all_issues.extend(issues)
            new_deps.extend(added)
            removed_deps.extend(removed)

        # Generate summary
        if all_issues:
            severity_counts: Dict[str, int] = {}
            for issue in all_issues:
                severity_counts[issue.severity] = severity_counts.get(issue.severity, 0) + 1
            summary = (
                f"Found {len(all_issues)} dependency issues: "
                + ", ".join(f"{count} {sev}" for sev, count in severity_counts.items())
            )
        else:
            summary = "No dependency issues found"

        if new_deps:
            summary += f". Added {len(new_deps)} new dependencies"
        if removed_deps:
            summary += f". Removed {len(removed_deps)} dependencies"

        logger.info(
            "[DependencyAnalyzer] Analysis completed",
            extra={
                "operation": "dependency_analysis",
                "trace_id": self.trace_id,
                "issue_count": len(all_issues),
                "new_deps": len(new_deps),
                "removed_deps": len(removed_deps),
            }
        )

        return DependencyAnalysis(
            issues=all_issues,
            analyzed_files=dependency_files,
            summary=summary,
            new_dependencies=new_deps,
            removed_dependencies=removed_deps,
        )

    def _parse_diff_by_file(self, diff_content: str) -> Dict[str, str]:
        """Parse diff content into per-file sections."""
        file_diffs: Dict[str, str] = {}
        current_file: Optional[str] = None
        current_content: List[str] = []

        for line in diff_content.split('\n'):
            if line.startswith('diff --git'):
                if current_file:
                    file_diffs[current_file] = '\n'.join(current_content)
                match = re.search(r'b/(.+)$', line)
                if match:
                    current_file = match.group(1)
                    current_content = [line]
                else:
                    current_file = None
                    current_content = []
            elif current_file:
                current_content.append(line)

        if current_file:
            file_diffs[current_file] = '\n'.join(current_content)

        return file_diffs

    def _is_dependency_file(self, file_path: str) -> bool:
        """Check if a file path is a dependency file."""
        for pattern in self.DEPENDENCY_FILE_PATTERNS:
            if re.search(pattern, file_path, re.IGNORECASE):
                return True
        return False

    def _analyze_dependency_file(
        self,
        file_path: str,
        file_diff: str,
    ) -> tuple[List[DependencyIssue], List[str], List[str]]:
        """
        Analyze a dependency file for issues.

        Returns:
            Tuple of (issues, added_deps, removed_deps)
        """
        issues: List[DependencyIssue] = []
        added_deps: List[str] = []
        removed_deps: List[str] = []

        # Determine file type and parse accordingly
        if file_path.endswith('package.json'):
            issues, added_deps, removed_deps = self._analyze_package_json(
                file_path, file_diff
            )
        elif file_path.endswith('.txt') and 'requirements' in file_path.lower():
            issues, added_deps, removed_deps = self._analyze_requirements_txt(
                file_path, file_diff
            )
        elif file_path.endswith('pyproject.toml'):
            issues, added_deps, removed_deps = self._analyze_pyproject_toml(
                file_path, file_diff
            )

        return issues, added_deps, removed_deps

    def _analyze_package_json(
        self,
        file_path: str,
        file_diff: str,
    ) -> tuple[List[DependencyIssue], List[str], List[str]]:
        """Analyze package.json changes."""
        issues: List[DependencyIssue] = []
        added_deps: List[str] = []
        removed_deps: List[str] = []

        # Pattern for npm dependency lines
        dep_pattern = re.compile(r'^([+-])\s*"([^"]+)":\s*"([^"]+)"')

        for line in file_diff.split('\n'):
            match = dep_pattern.match(line.strip())
            if match:
                change_type = match.group(1)
                package_name = match.group(2)
                version = match.group(3)

                if change_type == '+':
                    added_deps.append(package_name)

                    # Check for deprecated packages
                    if package_name.lower() in self.DEPRECATED_PACKAGES:
                        issues.append(DependencyIssue(
                            package_name=package_name,
                            issue_type=DependencyIssueType.DEPRECATED,
                            severity="medium",
                            message=f"Package '{package_name}' is deprecated",
                            file_path=file_path,
                            current_version=version,
                            recommended_action=self.DEPRECATED_PACKAGES[package_name.lower()],
                        ))

                    # Check for unpinned versions
                    if self._is_unpinned_version(version):
                        issues.append(DependencyIssue(
                            package_name=package_name,
                            issue_type=DependencyIssueType.UNPINNED,
                            severity="low",
                            message=f"Package '{package_name}' has unpinned version '{version}'",
                            file_path=file_path,
                            current_version=version,
                            recommended_action="Consider pinning to a specific version for reproducible builds",
                        ))

                elif change_type == '-':
                    removed_deps.append(package_name)

        return issues, added_deps, removed_deps

    def _analyze_requirements_txt(
        self,
        file_path: str,
        file_diff: str,
    ) -> tuple[List[DependencyIssue], List[str], List[str]]:
        """Analyze requirements.txt changes."""
        issues: List[DependencyIssue] = []
        added_deps: List[str] = []
        removed_deps: List[str] = []

        # Pattern for Python dependency lines
        dep_pattern = re.compile(r'^([+-])\s*([a-zA-Z0-9_-]+)([<>=!~]+.*)?$')

        for line in file_diff.split('\n'):
            # Skip comments and empty lines
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue

            match = dep_pattern.match(stripped)
            if match:
                change_type = match.group(1)
                package_name = match.group(2)
                version_spec = match.group(3) or ""

                if change_type == '+':
                    added_deps.append(package_name)

                    # Check for deprecated packages
                    if package_name.lower() in self.DEPRECATED_PACKAGES:
                        issues.append(DependencyIssue(
                            package_name=package_name,
                            issue_type=DependencyIssueType.DEPRECATED,
                            severity="medium",
                            message=f"Package '{package_name}' is deprecated",
                            file_path=file_path,
                            current_version=version_spec,
                            recommended_action=self.DEPRECATED_PACKAGES[package_name.lower()],
                        ))

                    # Check for unpinned versions
                    if not version_spec or version_spec.startswith('>='):
                        issues.append(DependencyIssue(
                            package_name=package_name,
                            issue_type=DependencyIssueType.UNPINNED,
                            severity="low",
                            message=f"Package '{package_name}' has unpinned version",
                            file_path=file_path,
                            current_version=version_spec or "unspecified",
                            recommended_action="Consider pinning to a specific version (e.g., ==1.2.3)",
                        ))

                elif change_type == '-':
                    removed_deps.append(package_name)

        return issues, added_deps, removed_deps

    def _analyze_pyproject_toml(
        self,
        file_path: str,
        file_diff: str,
    ) -> tuple[List[DependencyIssue], List[str], List[str]]:
        """Analyze pyproject.toml changes."""
        issues: List[DependencyIssue] = []
        added_deps: List[str] = []
        removed_deps: List[str] = []

        # Pattern for pyproject.toml dependency lines
        # Matches: "package" = "^1.0.0" or package = ">=1.0.0" or "package" = "*"
        dep_pattern = re.compile(
            r'^([+-])\s*"?([a-zA-Z0-9_-]+)"?\s*=\s*"?([^"]+)"?'
        )

        for line in file_diff.split('\n'):
            match = dep_pattern.match(line.strip())
            if match:
                change_type = match.group(1)
                package_name = match.group(2)
                version_spec = match.group(3).strip('"\'') if match.group(3) else ""

                if change_type == '+':
                    added_deps.append(package_name)

                    # Check for deprecated packages
                    if package_name.lower() in self.DEPRECATED_PACKAGES:
                        issues.append(DependencyIssue(
                            package_name=package_name,
                            issue_type=DependencyIssueType.DEPRECATED,
                            severity="medium",
                            message=f"Package '{package_name}' is deprecated",
                            file_path=file_path,
                            current_version=version_spec,
                            recommended_action=self.DEPRECATED_PACKAGES[package_name.lower()],
                        ))

                    # Check for unpinned versions (consistency with package.json/requirements.txt)
                    if self._is_unpinned_version(version_spec):
                        issues.append(DependencyIssue(
                            package_name=package_name,
                            issue_type=DependencyIssueType.UNPINNED,
                            severity="low",
                            message=f"Package '{package_name}' has unpinned version '{version_spec}'",
                            file_path=file_path,
                            current_version=version_spec,
                            recommended_action="Consider pinning to a specific version for reproducible builds",
                        ))

                elif change_type == '-':
                    removed_deps.append(package_name)

        return issues, added_deps, removed_deps

    def _is_unpinned_version(self, version: str) -> bool:
        """Check if a version string indicates an unpinned version."""
        for pattern in self.UNPINNED_PATTERNS:
            if re.match(pattern, version):
                return True
        return False


def analyze_dependencies(
    diff_content: str,
    diff_files: Optional[List[str]],
    trace_id: str,
) -> Dict[str, Any]:
    """
    Synchronous wrapper for dependency analysis.

    Args:
        diff_content: The PR diff content
        diff_files: Optional list of files in the diff
        trace_id: Trace ID for telemetry

    Returns:
        Dictionary with dependency analysis results
    """
    analyzer = DependencyAnalyzer(trace_id=trace_id)
    analysis = analyzer.analyze(diff_content, diff_files)
    return analysis.to_dict()
