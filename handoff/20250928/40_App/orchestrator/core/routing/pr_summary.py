"""
PRSummary Schema - Track C Interface & Output Contract

Standardized PR Summary artifact for consistent review output across all sinks
(GitHub comments, Slack/Jira/Linear notifications, Signals ingestion).

Issue #3221: PR Summary artifact standardization

This module provides:
1. PRSummary Pydantic model for structured PR summary data
2. Helper functions for building PRSummary from reviewer state
3. Renderers for different output formats (GitHub markdown, etc.)

Usage:
    from core.routing.pr_summary import PRSummary, build_pr_summary

    # Build from reviewer state
    summary = build_pr_summary(
        review_outcome=state.get("review_outcome", {}),
        review_result=state.get("review_result", {}),
        code_quality_score=state.get("code_quality_score", 0),
        trace_id=state.get("trace_id"),
        pr_number=state.get("pr_number"),
        repo=state.get("repo"),
        head_sha=state.get("diff_head_sha")
    )

    # Render to GitHub markdown
    markdown = summary.to_github_markdown()

Design Principles (Blueprint aligned):
- Deterministic: No LLM in rendering, pure transformation
- Versioned: schema_version for backward compatibility
- Sink-agnostic: Core data separate from presentation
"""
import logging
from typing import Literal, Optional, List, Dict, Any
from datetime import datetime, timezone

from pydantic import BaseModel, Field, field_validator, ConfigDict

logger = logging.getLogger(__name__)

# Verdict types aligned with ReviewOutcome
VerdictType = Literal["approve", "request_changes", "comment", "blocked", "unknown"]

# Display decision types (what's shown to users)
DisplayDecisionType = Literal["approve", "needs_changes", "block", "reviewed"]

# Schema version for backward-compatible evolution
SCHEMA_VERSION = 1


def sanitize_markdown(text: str) -> str:
    """
    Sanitize text for safe markdown rendering.

    Defense-in-depth: Escapes markdown/HTML control characters to prevent
    injection attacks. While data sources are internal MorningAI analyzers,
    this follows Blueprint Section 4.1 Safety Governor principles.

    Issue #4141: Add markdown sanitization for PRSummary rendering.

    Args:
        text: Raw text that may contain markdown control characters

    Returns:
        Sanitized text with control characters escaped

    Example:
        >>> sanitize_markdown("Check [link](http://evil.com)")
        'Check \\[link\\]\\(http://evil.com\\)'
    """
    if not text:
        return text

    # Escape backslash first to avoid double-escaping
    result = text.replace("\\", "\\\\")
    # Escape markdown link/image syntax characters
    result = result.replace("[", "\\[")
    result = result.replace("]", "\\]")
    result = result.replace("(", "\\(")
    result = result.replace(")", "\\)")
    # Escape HTML tag characters
    result = result.replace("<", "\\<")
    result = result.replace(">", "\\>")

    return result


# Senior Architect policy note (shared constant)
SENIOR_ARCHITECT_POLICY_NOTE = (
    "This review follows the Senior Architect policy - style, formatting, "
    "and naming convention issues are intentionally filtered out to reduce noise. "
    "The reviewer focuses on logic errors, security vulnerabilities, performance "
    "problems, and API contract changes."
)


class FileLevelComment(BaseModel):
    """File-level comment that couldn't be posted inline."""
    file: str = Field(description="File path")
    message: str = Field(description="Comment message")
    reason: Optional[str] = Field(
        default=None,
        description="Why this was downgraded to file-level"
    )


class SpecialistFindingSummary(BaseModel):
    """Summary of a specialist finding for PR summary rendering.

    Issue #4133: Include Multi-Specialist findings in PRSummary output.
    """
    specialist: str = Field(description="Specialist type (security/performance/architecture)")
    severity: str = Field(description="Finding severity (low/medium/high/critical)")
    category: str = Field(description="Issue category")
    message: str = Field(description="Finding description")
    file_path: Optional[str] = Field(default=None, description="File path if applicable")
    suggestion: Optional[str] = Field(default=None, description="Suggested fix")


class CoverageGapSummary(BaseModel):
    """Summary of a test coverage gap for PR summary rendering.

    Issue #4133: Include B-11 Test Coverage gaps in PRSummary output.
    Maps from CoverageGap.to_dict() structure.
    """
    function_name: str = Field(description="Name of function/class missing tests")
    file_path: str = Field(description="File path containing the function")
    function_type: str = Field(default="function", description="Type: function or class")
    reason: str = Field(default="New code without corresponding test")
    suggested_test_types: List[str] = Field(
        default_factory=lambda: ["unit"],
        description="Suggested test types"
    )


class DependencyIssueSummary(BaseModel):
    """Summary of a dependency issue for PR summary rendering.

    Issue #4133: Include B-12 Dependency issues in PRSummary output.
    Maps from DependencyIssue.to_dict() structure.
    """
    package_name: str = Field(description="Name of the package")
    issue_type: str = Field(description="Type of issue (outdated/vulnerability/license/etc)")
    severity: str = Field(default="low", description="Issue severity")
    description: str = Field(default="", description="Issue description")
    current_version: Optional[str] = Field(default=None, description="Current version")
    recommended_action: Optional[str] = Field(default=None, description="Recommended fix")


class PRSummary(BaseModel):
    """Standardized PR Summary artifact (Issue #3221)

    Schema Version: 1
    Evolution Strategy: Only additive changes (new optional fields).
    Breaking changes require version bump and consumer compatibility handling.

    This is the contract for PR summary output. All sinks (GitHub, Slack, etc.)
    should consume this schema rather than re-deriving their own summaries.
    """

    # Schema version for backward compatibility
    schema_version: Literal[1] = Field(
        default=1,
        description="Schema version for backward compatibility"
    )

    # Core review data
    verdict: VerdictType = Field(
        description="Router verdict (from ReviewOutcome)"
    )
    display_decision: DisplayDecisionType = Field(
        description="User-facing decision label (approve/needs_changes/block/reviewed)"
    )
    score: int = Field(
        ge=0,
        le=100,
        description="Code quality score (0-100)"
    )
    analysis: str = Field(
        description="LLM analysis summary (llm_summary from review_result)"
    )

    # File-level comments (for appendix rendering)
    file_level_comments: List[FileLevelComment] = Field(
        default_factory=list,
        description="Comments that couldn't be posted inline"
    )

    # Multi-Specialist Review findings (Issue #4133)
    # B-9: Security, Performance, Architecture specialist findings
    specialist_findings: List[SpecialistFindingSummary] = Field(
        default_factory=list,
        description="Findings from multi-specialist review (B-9)"
    )

    # B-11: Test coverage gaps
    test_coverage_gaps: List[CoverageGapSummary] = Field(
        default_factory=list,
        description="Test coverage gaps identified by B-11 analyzer"
    )

    # B-12: Dependency issues
    dependency_issues: List[DependencyIssueSummary] = Field(
        default_factory=list,
        description="Dependency issues identified by B-12 analyzer"
    )

    # Metadata (optional, for tracing and debugging)
    trace_id: Optional[str] = Field(
        default=None,
        description="Trace ID for debugging"
    )
    pr_number: Optional[int] = Field(
        default=None,
        description="PR number"
    )
    repo: Optional[str] = Field(
        default=None,
        description="Repository in owner/repo format"
    )
    head_sha: Optional[str] = Field(
        default=None,
        description="Head commit SHA"
    )
    generated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO timestamp when summary was generated"
    )

    # Pydantic V2 configuration
    model_config = ConfigDict(
        frozen=True,  # Immutable after creation
        extra="forbid"  # No extra fields allowed
    )

    @field_validator("analysis")
    @classmethod
    def analysis_default_if_empty(cls, v: str) -> str:
        """Provide default analysis if empty."""
        if not v or not v.strip():
            return "No significant issues found."
        return v.strip()

    def _get_verdict_icon(self) -> str:
        """Get GitHub emoji icon for verdict."""
        icon_map = {
            "approve": "white_check_mark",
            "needs_changes": "warning",
            "block": "x",
            "reviewed": "mag",
        }
        return icon_map.get(self.display_decision, "mag")

    def _get_verdict_label(self) -> str:
        """Get human-readable verdict label."""
        label_map = {
            "approve": "Approve",
            "needs_changes": "Needs Changes",
            "block": "Block",
            "reviewed": "Reviewed",
        }
        return label_map.get(self.display_decision, "Reviewed")

    @property
    def verdict_label(self) -> str:
        """Public property for human-readable verdict label."""
        return self._get_verdict_label()

    @property
    def verdict_icon(self) -> str:
        """Public property for GitHub emoji icon."""
        return self._get_verdict_icon()

    def to_github_markdown(self, include_policy_note: bool = True) -> str:
        """
        Render PR summary to GitHub-flavored markdown.

        Args:
            include_policy_note: Whether to include the Senior Architect policy note

        Returns:
            GitHub markdown string ready for posting
        """
        icon = self._get_verdict_icon()
        label = self._get_verdict_label()

        parts = [
            "## :robot: MorningAI Review Summary",
            "",
            f"**Verdict:** :{icon}: {label} (Score: {self.score})",
            "",
            "**Analysis:**",
            self.analysis,
        ]

        # Add Multi-Specialist Review findings (Issue #4133)
        if self.specialist_findings:
            parts.append("")
            parts.append("---")
            parts.append("")
            parts.append("### Multi-Specialist Analysis")
            parts.append("")

            security_findings = [f for f in self.specialist_findings if f.specialist.lower() == "security"]
            performance_findings = [f for f in self.specialist_findings if f.specialist.lower() == "performance"]
            architecture_findings = [f for f in self.specialist_findings if f.specialist.lower() == "architecture"]

            severity_icons = {
                "critical": ":red_circle:",
                "high": ":orange_circle:",
                "medium": ":yellow_circle:",
                "low": ":white_circle:"
            }

            if security_findings:
                parts.append("#### :shield: Security")
                for finding in security_findings:
                    icon = severity_icons.get(finding.severity.lower(), ":white_circle:")
                    # Issue #4141: Sanitize message for defense-in-depth
                    parts.append(f"- {icon} **[{finding.category}]** {sanitize_markdown(finding.message)}")
                    if finding.file_path:
                        # Issue #4141: Sanitize file_path for defense-in-depth
                        parts.append(f"  - File: `{sanitize_markdown(finding.file_path)}`")
                    if finding.suggestion:
                        # Issue #4141: Sanitize suggestion for defense-in-depth
                        parts.append(f"  - Suggestion: {sanitize_markdown(finding.suggestion)}")
                parts.append("")

            if performance_findings:
                parts.append("#### :zap: Performance")
                for finding in performance_findings:
                    icon = severity_icons.get(finding.severity.lower(), ":white_circle:")
                    # Issue #4141: Sanitize message for defense-in-depth
                    parts.append(f"- {icon} **[{finding.category}]** {sanitize_markdown(finding.message)}")
                    if finding.file_path:
                        # Issue #4141: Sanitize file_path for defense-in-depth
                        parts.append(f"  - File: `{sanitize_markdown(finding.file_path)}`")
                    if finding.suggestion:
                        # Issue #4141: Sanitize suggestion for defense-in-depth
                        parts.append(f"  - Suggestion: {sanitize_markdown(finding.suggestion)}")
                parts.append("")

            if architecture_findings:
                parts.append("#### :building_construction: Architecture")
                for finding in architecture_findings:
                    icon = severity_icons.get(finding.severity.lower(), ":white_circle:")
                    # Issue #4141: Sanitize message for defense-in-depth
                    parts.append(f"- {icon} **[{finding.category}]** {sanitize_markdown(finding.message)}")
                    if finding.file_path:
                        # Issue #4141: Sanitize file_path for defense-in-depth
                        parts.append(f"  - File: `{sanitize_markdown(finding.file_path)}`")
                    if finding.suggestion:
                        # Issue #4141: Sanitize suggestion for defense-in-depth
                        parts.append(f"  - Suggestion: {sanitize_markdown(finding.suggestion)}")
                parts.append("")

        # Add Test Coverage gaps (B-11)
        if self.test_coverage_gaps:
            parts.append("")
            parts.append("---")
            parts.append("")
            parts.append("### :test_tube: Test Coverage Gaps")
            parts.append("")
            for gap in self.test_coverage_gaps:
                type_label = "class" if gap.function_type == "class" else "function"
                test_types = ", ".join(gap.suggested_test_types)
                # Issue #4141: Sanitize function_name, file_path, and reason for defense-in-depth
                parts.append(f"- **{sanitize_markdown(gap.function_name)}** ({type_label}) in `{sanitize_markdown(gap.file_path)}`")
                parts.append(f"  - {sanitize_markdown(gap.reason)}")
                parts.append(f"  - Suggested tests: {test_types}")
            parts.append("")

        # Add Dependency issues (B-12)
        if self.dependency_issues:
            parts.append("")
            parts.append("---")
            parts.append("")
            parts.append("### :package: Dependency Issues")
            parts.append("")
            severity_icons = {
                "critical": ":red_circle:",
                "high": ":orange_circle:",
                "medium": ":yellow_circle:",
                "low": ":white_circle:"
            }
            for issue in self.dependency_issues:
                icon = severity_icons.get(issue.severity.lower(), ":white_circle:")
                parts.append(f"- {icon} **{issue.package_name}** [{issue.issue_type}]")
                if issue.description:
                    # Issue #4141: Sanitize description for defense-in-depth
                    parts.append(f"  - {sanitize_markdown(issue.description)}")
                if issue.current_version:
                    parts.append(f"  - Current version: `{issue.current_version}`")
                if issue.recommended_action:
                    # Issue #4141: Sanitize recommended_action for defense-in-depth
                    parts.append(f"  - Recommended: {sanitize_markdown(issue.recommended_action)}")
            parts.append("")

        # Add file-level comments appendix if present
        if self.file_level_comments:
            parts.append("")
            parts.append("---")
            parts.append("")
            parts.append("### File-Level Comments")
            parts.append("")
            parts.append("*The following comments could not be posted inline:*")
            parts.append("")
            for comment in self.file_level_comments:
                # Issue #4141: Sanitize file path, message, and reason for defense-in-depth
                parts.append(f"**`{sanitize_markdown(comment.file)}`**")
                parts.append(f"> {sanitize_markdown(comment.message)}")
                if comment.reason:
                    parts.append(f"> *(Reason: {sanitize_markdown(comment.reason)})*")
                parts.append("")

        # Add policy note
        if include_policy_note:
            parts.append("")
            parts.append("---")
            parts.append(f"*Note: {SENIOR_ARCHITECT_POLICY_NOTE}*")

        return "\n".join(parts)

    def to_simple_markdown(self) -> str:
        """
        Render simple markdown header for inline comment reviews.

        This is used when there are inline comments - the full summary
        is not needed, just a header with optional file-level appendix.

        Returns:
            Simple markdown header string
        """
        parts = ["## MorningAI Code Review"]

        # Add file-level comments appendix if present
        if self.file_level_comments:
            parts.append("")
            parts.append("### File-Level Comments")
            parts.append("")
            parts.append("*The following comments could not be posted inline:*")
            parts.append("")
            for comment in self.file_level_comments:
                # Issue #4141: Sanitize file path, message, and reason for defense-in-depth
                parts.append(f"**`{sanitize_markdown(comment.file)}`**")
                parts.append(f"> {sanitize_markdown(comment.message)}")
                if comment.reason:
                    parts.append(f"> *(Reason: {sanitize_markdown(comment.reason)})*")
                parts.append("")

        return "\n".join(parts)


def _map_verdict_to_display_decision(
    verdict: str,
    llm_decision: Optional[str] = None
) -> DisplayDecisionType:
    """
    Map ReviewOutcome verdict to display decision.

    Uses llm_decision if available (for backward compatibility with existing
    summary format), otherwise maps from verdict.

    Args:
        verdict: ReviewOutcome verdict
        llm_decision: Optional llm_decision from review_result

    Returns:
        Display decision for user-facing output
    """
    # Prefer llm_decision if available (backward compatibility)
    if llm_decision:
        llm_lower = llm_decision.lower()
        if llm_lower == "approve":
            return "approve"
        elif llm_lower in ("needs_changes", "request_changes"):
            return "needs_changes"
        elif llm_lower == "block":
            return "block"
        return "reviewed"

    # Map from verdict
    verdict_lower = verdict.lower() if verdict else "unknown"
    if verdict_lower == "approve":
        return "approve"
    elif verdict_lower == "request_changes":
        return "needs_changes"
    elif verdict_lower == "blocked":
        return "block"
    elif verdict_lower == "comment":
        return "reviewed"
    return "reviewed"


def build_pr_summary(
    review_outcome: Dict[str, Any],
    review_result: Dict[str, Any],
    code_quality_score: int = 0,
    file_level_comments: Optional[List[Dict[str, Any]]] = None,
    trace_id: Optional[str] = None,
    pr_number: Optional[int] = None,
    repo: Optional[str] = None,
    head_sha: Optional[str] = None,
    specialist_findings: Optional[List[Dict[str, Any]]] = None,
    test_coverage_gaps: Optional[List[Dict[str, Any]]] = None,
    dependency_issues: Optional[List[Dict[str, Any]]] = None
) -> PRSummary:
    """
    Build PRSummary from reviewer state fields.

    This is the primary entry point for constructing PRSummary.
    It handles all the mapping and normalization logic.

    Args:
        review_outcome: ReviewOutcome dict from state["review_outcome"]
        review_result: Review result dict from state["review_result"]
        code_quality_score: Code quality score from state["code_quality_score"]
        file_level_comments: Optional list of file-level comment dicts
        trace_id: Optional trace ID for debugging
        pr_number: Optional PR number
        repo: Optional repository in owner/repo format
        head_sha: Optional head commit SHA
        specialist_findings: Optional list of specialist finding dicts (Issue #4133)
        test_coverage_gaps: Optional list of coverage gap dicts from B-11 analyzer
        dependency_issues: Optional list of dependency issue dicts from B-12 analyzer

    Returns:
        PRSummary instance ready for rendering

    Example:
        summary = build_pr_summary(
            review_outcome=state.get("review_outcome", {}),
            review_result=state.get("review_result", {}),
            code_quality_score=state.get("code_quality_score", 0),
            file_level_comments=downgraded_comments,
            trace_id=state.get("trace_id"),
            pr_number=state.get("pr_number"),
            specialist_findings=state.get("multi_specialist_review_v1", {}).get("findings", [])
        )
        markdown = summary.to_github_markdown()
    """
    # Extract fields from review_outcome and review_result
    verdict = review_outcome.get("verdict", "unknown")
    llm_decision = review_result.get("llm_decision")
    llm_summary = review_result.get("llm_summary", "")

    # Map to display decision
    display_decision = _map_verdict_to_display_decision(verdict, llm_decision)

    # Convert file-level comments to FileLevelComment objects
    file_comments = []
    if file_level_comments:
        for c in file_level_comments:
            file_comments.append(FileLevelComment(
                file=c.get("file", "unknown"),
                message=c.get("message", ""),
                reason=c.get("downgrade_reason")
            ))

    # Convert specialist findings to SpecialistFindingSummary objects (Issue #4133)
    specialist_finding_objs = []
    if specialist_findings:
        for f in specialist_findings:
            specialist_finding_objs.append(SpecialistFindingSummary(
                specialist=f.get("specialist", "unknown"),
                severity=f.get("severity", "low"),
                category=f.get("category", "general"),
                message=f.get("message", ""),
                file_path=f.get("file_path"),
                suggestion=f.get("suggestion")
            ))

    # Convert test coverage gaps to CoverageGapSummary objects (Issue #4133, B-11)
    coverage_gap_objs = []
    if test_coverage_gaps:
        for g in test_coverage_gaps:
            coverage_gap_objs.append(CoverageGapSummary(
                function_name=g.get("function_name", "unknown"),
                file_path=g.get("file_path", "unknown"),
                function_type=g.get("function_type", "function"),
                reason=g.get("reason", "New code without corresponding test"),
                suggested_test_types=g.get("suggested_test_types", ["unit"])
            ))

    # Convert dependency issues to DependencyIssueSummary objects (Issue #4133, B-12)
    dependency_issue_objs = []
    if dependency_issues:
        for i in dependency_issues:
            dependency_issue_objs.append(DependencyIssueSummary(
                package_name=i.get("package_name", "unknown"),
                issue_type=i.get("issue_type", "unknown"),
                severity=i.get("severity", "low"),
                description=i.get("description", ""),
                current_version=i.get("current_version"),
                recommended_action=i.get("recommended_action")
            ))

    # Normalize head_sha: only accept non-empty strings, convert invalid types to None
    # This ensures graceful degradation when diff_head_sha is missing or invalid
    normalized_head_sha = head_sha if isinstance(head_sha, str) and head_sha.strip() else None

    return PRSummary(
        verdict=verdict if verdict in ("approve", "request_changes", "comment", "blocked", "unknown") else "unknown",
        display_decision=display_decision,
        score=max(0, min(100, code_quality_score)),  # Clamp to 0-100
        analysis=llm_summary,
        file_level_comments=file_comments,
        specialist_findings=specialist_finding_objs,
        test_coverage_gaps=coverage_gap_objs,
        dependency_issues=dependency_issue_objs,
        trace_id=trace_id,
        pr_number=pr_number,
        repo=repo,
        head_sha=normalized_head_sha
    )


def build_unknown_pr_summary(
    error: str,
    trace_id: Optional[str] = None,
    pr_number: Optional[int] = None
) -> PRSummary:
    """
    Build a minimal PRSummary for error/timeout scenarios.

    Args:
        error: Error message describing what went wrong
        trace_id: Optional trace ID for debugging
        pr_number: Optional PR number

    Returns:
        PRSummary with unknown verdict and error analysis
    """
    return PRSummary(
        verdict="unknown",
        display_decision="reviewed",
        score=0,
        analysis=f"Review failed: {error}",
        trace_id=trace_id,
        pr_number=pr_number
    )
