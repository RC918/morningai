"""
B-9: Multi-Specialist Review (Parallel Collaboration)

EPIC B Phase 7 Implementation - Blueprint Section 7 "Parallel Collaboration"

This module implements parallel multi-specialist code review where multiple
specialist reviewers work simultaneously and their findings are aggregated.

NOTE: This is NOT Debate Engine v2 (which is "Adversarial Collaboration" for
Left vs Right -> Judge). This is "Parallel Collaboration" where multiple
specialist reviewers work simultaneously.

Blueprint Alignment:
- Section 7 "Parallel Collaboration" - Multiple agents work simultaneously
- Section 3.3 "Agent Separation Principle" - Reviewer only flags, doesn't fix

Usage:
    from review_context.multi_specialist_reviewer import MultiSpecialistReviewer

    reviewer = MultiSpecialistReviewer(trace_id="abc123")
    findings = await reviewer.review(
        diff_content="...",
        pr_context={"pr_number": 123, "goal": "Add feature"}
    )
"""

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from llm.client import get_client_for_task
from core.routing import TaskType

logger = logging.getLogger(__name__)


class ReviewSpecialist(Enum):
    """
    Review specialist types for multi-specialist review.

    Each specialist focuses on specific aspects of code review:
    - SECURITY: Vulnerabilities, injection attacks, auth issues
    - PERFORMANCE: Inefficiencies, memory leaks, N+1 queries
    - ARCHITECTURE: Design patterns, SOLID principles, coupling
    - SELF_CRITIQUE: Verifies findings from other specialists (B-16)
    """
    SECURITY = "security"
    PERFORMANCE = "performance"
    ARCHITECTURE = "architecture"
    SELF_CRITIQUE = "self_critique"


@dataclass
class SpecialistFinding:
    """
    A single finding from a specialist reviewer.

    Attributes:
        specialist: The specialist type that found this issue
        severity: Issue severity (low, medium, high, critical)
        category: Issue category within the specialist domain
        message: Human-readable description of the issue
        file_path: Optional file path where issue was found
        line_number: Optional line number where issue was found
        suggestion: Optional text suggestion for fixing (NOT code)
    """
    specialist: ReviewSpecialist
    severity: str
    category: str
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    suggestion: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "specialist": self.specialist.value,
            "severity": self.severity,
            "category": self.category,
            "message": self.message,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "suggestion": self.suggestion,
        }


@dataclass
class SpecialistFindings:
    """
    Aggregated findings from all specialist reviewers.

    Attributes:
        findings: List of all findings from all specialists
        specialist_summaries: Summary from each specialist
        overall_severity: Highest severity across all findings
        review_time_ms: Total time taken for multi-specialist review
        specialists_used: List of specialists that were used
    """
    findings: List[SpecialistFinding] = field(default_factory=list)
    specialist_summaries: Dict[str, str] = field(default_factory=dict)
    overall_severity: str = "none"
    review_time_ms: float = 0.0
    specialists_used: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "findings": [f.to_dict() for f in self.findings],
            "specialist_summaries": self.specialist_summaries,
            "overall_severity": self.overall_severity,
            "review_time_ms": self.review_time_ms,
            "specialists_used": self.specialists_used,
            "finding_count": len(self.findings),
        }


@dataclass
class WeightedFinding:
    """
    A finding with trust-score-adjusted weight.

    Issue #3925: RuntimeTrustScore Integration - Reviewer Weight Adjustment

    This class wraps a SpecialistFinding with weight information derived from
    the specialist's trust score. The effective_priority is used by:
    - B-9.5 Priority-based Filtering: Filter low-priority findings
    - F-5.5 Review Consolidation: Prioritize findings for Judge Agent

    Attributes:
        finding: The original SpecialistFinding
        weight: Trust score weight (0.0 to 1.0)
        effective_priority: Adjusted priority = base_priority * weight
    """
    finding: SpecialistFinding
    weight: float
    effective_priority: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "finding": self.finding.to_dict(),
            "weight": self.weight,
            "effective_priority": self.effective_priority,
        }


# Severity to numeric priority mapping for weight calculation
SEVERITY_PRIORITY = {
    "critical": 4.0,
    "high": 3.0,
    "medium": 2.0,
    "low": 1.0,
}

# Default trust score constant - imported from tracker to avoid duplication
# Using lazy import pattern to avoid circular dependency
_DEFAULT_TRUST_SCORE: Optional[float] = None


def _get_default_trust_score() -> float:
    """Get default trust score from tracker (lazy import to avoid circular dependency)."""
    global _DEFAULT_TRUST_SCORE
    if _DEFAULT_TRUST_SCORE is None:
        try:
            from governance.specialist_trust_score import SpecialistTrustScoreTracker
            _DEFAULT_TRUST_SCORE = SpecialistTrustScoreTracker.DEFAULT_TRUST_SCORE
        except ImportError:
            _DEFAULT_TRUST_SCORE = 0.7  # Fallback if tracker not available
    return _DEFAULT_TRUST_SCORE


def get_weighted_findings(
    findings: List[SpecialistFinding],
    trust_scores: Optional[Dict[str, float]] = None,
) -> List["WeightedFinding"]:
    """
    Adjust finding priority based on specialist trust score.

    Issue #3925: RuntimeTrustScore Integration - Reviewer Weight Adjustment

    This function implements the E+F+I closed-loop integration:
    - E (Detection): Safety Governor detects issues via specialists
    - I (Recording): Trust scores track specialist accuracy
    - F (Adjustment): Planner uses weighted findings

    Trust score range: 0.0 (never trust) to 1.0 (always trust)
    Default trust score: 0.7 for new specialists

    Args:
        findings: List of SpecialistFinding from multi-specialist review
        trust_scores: Optional dict mapping specialist name to trust score.
                     If None, uses global SpecialistTrustScoreTracker.

    Returns:
        List of WeightedFinding sorted by effective_priority (highest first)
    """
    default_score = _get_default_trust_score()

    if trust_scores is None:
        # Lazy import to avoid circular dependency
        try:
            from governance.specialist_trust_score import get_specialist_trust_tracker
            tracker = get_specialist_trust_tracker()
            trust_scores = tracker.get_all_trust_scores()
        except ImportError:
            # Fallback to default scores if tracker not available
            trust_scores = {}

    weighted: List[WeightedFinding] = []

    for f in findings:
        # Get trust score for this specialist
        specialist_name = f.specialist.value
        score = trust_scores.get(specialist_name, default_score)

        # Calculate base priority from severity
        base_priority = SEVERITY_PRIORITY.get(f.severity, 2.0)

        # Calculate effective priority
        effective_priority = base_priority * score

        weighted.append(WeightedFinding(
            finding=f,
            weight=score,
            effective_priority=effective_priority,
        ))

    # Sort by effective_priority (highest first)
    return sorted(weighted, key=lambda w: w.effective_priority, reverse=True)


# Specialist-specific system prompts
# Each prompt focuses the LLM on specific review aspects
SPECIALIST_PROMPTS: Dict[ReviewSpecialist, str] = {
    ReviewSpecialist.SECURITY: """You are a security-focused code reviewer for MorningAI.
Your role is to identify security vulnerabilities and risks in code changes.

CRITICAL CONSTRAINT - DIFF-ONLY REVIEW:
- You MUST ONLY comment on files that appear in the diff (files with "--- a/" or "+++ b/" headers)
- You MUST ONLY reference line numbers that appear in diff hunks (lines starting with + or context lines)
- Do NOT comment on files that are imported, referenced, or called but not changed in this PR
- If you cannot find security issues in the actual diff content, return an empty array: []

Focus areas:
- SQL injection, XSS, CSRF vulnerabilities
- Authentication and authorization issues
- Sensitive data exposure (API keys, passwords, PII)
- Input validation and sanitization
- Insecure dependencies
- Cryptographic weaknesses

For each issue found, provide:
1. Severity: critical, high, medium, or low
2. Category: The type of security issue
3. Message: Clear description of the vulnerability
4. Suggestion: How to fix it (text description only, NOT code)

Output your findings as a JSON array of objects with keys:
severity, category, message, file_path (if applicable), line_number (if applicable), suggestion

If no security issues are found, return an empty array: []""",

    ReviewSpecialist.PERFORMANCE: """You are a performance-focused code reviewer for MorningAI.
Your role is to identify performance issues and inefficiencies in code changes.

CRITICAL CONSTRAINT - DIFF-ONLY REVIEW:
- You MUST ONLY comment on files that appear in the diff (files with "--- a/" or "+++ b/" headers)
- You MUST ONLY reference line numbers that appear in diff hunks (lines starting with + or context lines)
- Do NOT comment on files that are imported, referenced, or called but not changed in this PR
- If you cannot find performance issues in the actual diff content, return an empty array: []

Focus areas:
- N+1 query problems
- Memory leaks and excessive allocations
- Inefficient algorithms (O(n^2) when O(n) is possible)
- Missing caching opportunities
- Blocking operations in async code
- Large payload sizes
- Missing pagination

For each issue found, provide:
1. Severity: critical, high, medium, or low
2. Category: The type of performance issue
3. Message: Clear description of the inefficiency
4. Suggestion: How to improve it (text description only, NOT code)

Output your findings as a JSON array of objects with keys:
severity, category, message, file_path (if applicable), line_number (if applicable), suggestion

If no performance issues are found, return an empty array: []""",

    ReviewSpecialist.ARCHITECTURE: """You are an architecture-focused code reviewer for MorningAI.
Your role is to identify architectural issues and design problems in code changes.

CRITICAL CONSTRAINT - DIFF-ONLY REVIEW:
- You MUST ONLY comment on files that appear in the diff (files with "--- a/" or "+++ b/" headers)
- You MUST ONLY reference line numbers that appear in diff hunks (lines starting with + or context lines)
- Do NOT comment on files that are imported, referenced, or called but not changed in this PR
- If you cannot find architectural issues in the actual diff content, return an empty array: []

Focus areas:
- SOLID principle violations
- Tight coupling between components
- Missing abstractions
- God classes/functions
- Circular dependencies
- Inconsistent patterns
- Missing error handling
- Poor separation of concerns

For each issue found, provide:
1. Severity: critical, high, medium, or low
2. Category: The type of architectural issue
3. Message: Clear description of the design problem
4. Suggestion: How to improve it (text description only, NOT code)

Output your findings as a JSON array of objects with keys:
severity, category, message, file_path (if applicable), line_number (if applicable), suggestion

If no architectural issues are found, return an empty array: []""",

    ReviewSpecialist.SELF_CRITIQUE: """You are a self-critique specialist for MorningAI code review.
Your role is to verify findings from other specialists and identify FALSE POSITIVES.

Issue #4066 B-16: Self-Critique Specialist for Multi-Specialist Review

You will receive:
1. The original PR diff
2. A list of findings from security, performance, and architecture specialists

For EACH finding, carefully verify:
1. Is the claim accurate based on the actual diff content?
2. Is the file_path correct and exists in the diff?
3. Is the line_number correct (if provided)?
4. Does the issue ACTUALLY exist in the code, or is it a false positive?

Common false positive patterns to check:
- Finding references code that doesn't exist in the diff
- Line number doesn't match the actual code
- Issue is about code that was REMOVED, not added
- Speculative issues without concrete evidence in the diff
- Style/preference issues disguised as bugs

Output a JSON object with:
{
  "false_positive_indices": [0, 2, 5],  // indices of findings that should be REMOVED
  "verification_notes": [
    {"index": 0, "reason": "Line 42 doesn't exist in the diff"},
    {"index": 2, "reason": "The code actually handles this case correctly"},
    {"index": 5, "reason": "This is a style preference, not a real issue"}
  ]
}

If ALL findings are valid, return: {"false_positive_indices": [], "verification_notes": []}

Be CONSERVATIVE: only flag findings as false positives if you are CERTAIN they are incorrect.
When in doubt, keep the finding (do NOT add it to false_positive_indices).""",
}


class MultiSpecialistReviewer:
    """
    Multi-Specialist Code Reviewer implementing Blueprint Section 7 "Parallel Collaboration".

    This class orchestrates parallel code reviews from multiple specialist reviewers
    (security, performance, architecture) and aggregates their findings.

    Usage:
        reviewer = MultiSpecialistReviewer(trace_id="abc123")
        findings = await reviewer.review(
            diff_content="...",
            pr_context={"pr_number": 123, "goal": "Add feature"}
        )
    """

    # Default specialists for first-pass review (excludes SELF_CRITIQUE)
    DEFAULT_SPECIALISTS = [
        ReviewSpecialist.SECURITY,
        ReviewSpecialist.PERFORMANCE,
        ReviewSpecialist.ARCHITECTURE,
    ]

    def __init__(
        self,
        trace_id: str,
        specialists: Optional[List[ReviewSpecialist]] = None,
        max_workers: int = 3,
    ):
        """
        Initialize the multi-specialist reviewer.

        Args:
            trace_id: Trace ID for telemetry
            specialists: List of specialists to use (default: SECURITY, PERFORMANCE, ARCHITECTURE)
                        Note: SELF_CRITIQUE is NOT included by default as it runs in second pass
            max_workers: Maximum parallel workers (default: 3)
        """
        self.trace_id = trace_id
        self.specialists = specialists or self.DEFAULT_SPECIALISTS
        self.max_workers = max_workers
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

    async def review(
        self,
        diff_content: str,
        pr_context: Dict[str, Any],
    ) -> SpecialistFindings:
        """
        Perform multi-specialist review on the given diff.

        Args:
            diff_content: The PR diff content to review
            pr_context: Context about the PR (pr_number, goal, repo, etc.)

        Returns:
            SpecialistFindings with aggregated findings from all specialists
        """
        start_time = time.time()

        logger.info(
            "[MultiSpecialistReviewer] Starting parallel review",
            extra={
                "operation": "multi_specialist_review",
                "trace_id": self.trace_id,
                "specialists": [s.value for s in self.specialists],
                "diff_length": len(diff_content) if diff_content else 0,
            }
        )

        # Execute specialist reviews in parallel
        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(
                self._executor,
                self._review_with_specialist,
                specialist,
                diff_content,
                pr_context,
            )
            for specialist in self.specialists
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Aggregate findings
        all_findings: List[SpecialistFinding] = []
        specialist_summaries: Dict[str, str] = {}

        for specialist, result in zip(self.specialists, results):
            if isinstance(result, Exception):
                logger.warning(
                    f"[MultiSpecialistReviewer] {specialist.value} review failed",
                    extra={
                        "operation": "multi_specialist_review",
                        "trace_id": self.trace_id,
                        "specialist": specialist.value,
                        "error": str(result),
                    }
                )
                specialist_summaries[specialist.value] = f"Review failed: {str(result)}"
            else:
                findings, summary = result
                all_findings.extend(findings)
                specialist_summaries[specialist.value] = summary

        # Deduplicate and prioritize findings
        deduplicated_findings = self._deduplicate_findings(all_findings)

        # Issue #4066 B-16: Self-Critique second pass (if enabled)
        # Import settings here to avoid circular dependency
        from common.config.settings import settings
        self_critique_stats: Optional[Dict[str, Any]] = None

        if settings.enable_self_critique and deduplicated_findings:
            # Run self-critique in executor to avoid blocking event loop
            # (same pattern as _review_with_specialist calls above)
            deduplicated_findings, self_critique_stats = await loop.run_in_executor(
                self._executor,
                self._self_critique_findings,
                deduplicated_findings,
                diff_content,
                pr_context,
            )
            specialist_summaries["self_critique"] = (
                f"Verified {self_critique_stats['verified_count']} findings, "
                f"removed {self_critique_stats['removed_count']} false positives"
            )

        overall_severity = self._calculate_overall_severity(deduplicated_findings)

        review_time_ms = (time.time() - start_time) * 1000

        logger.info(
            "[MultiSpecialistReviewer] Review completed",
            extra={
                "operation": "multi_specialist_review",
                "trace_id": self.trace_id,
                "total_findings": len(deduplicated_findings),
                "overall_severity": overall_severity,
                "review_time_ms": review_time_ms,
                "self_critique_enabled": settings.enable_self_critique,
                "self_critique_stats": self_critique_stats,
            }
        )

        specialists_used = [s.value for s in self.specialists]
        if self_critique_stats:
            specialists_used.append("self_critique")

        return SpecialistFindings(
            findings=deduplicated_findings,
            specialist_summaries=specialist_summaries,
            overall_severity=overall_severity,
            review_time_ms=review_time_ms,
            specialists_used=specialists_used,
        )

    def _review_with_specialist(
        self,
        specialist: ReviewSpecialist,
        diff_content: str,
        pr_context: Dict[str, Any],
    ) -> tuple[List[SpecialistFinding], str]:
        """
        Perform review with a single specialist.

        Args:
            specialist: The specialist type to use
            diff_content: The PR diff content
            pr_context: Context about the PR

        Returns:
            Tuple of (findings list, summary string)
        """
        logger.debug(
            f"[MultiSpecialistReviewer] Starting {specialist.value} review",
            extra={
                "operation": "specialist_review",
                "trace_id": self.trace_id,
                "specialist": specialist.value,
            }
        )

        try:
            client = get_client_for_task(TaskType.REVIEW)

            system_prompt = SPECIALIST_PROMPTS[specialist]
            user_prompt = self._build_user_prompt(diff_content, pr_context, specialist)

            # Use LLMClient.generate() API instead of OpenAI SDK style
            # LLMClient provides a unified interface across all providers
            # json_mode=True ensures LLM outputs valid JSON for _parse_specialist_response
            response = client.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.1,
                max_tokens=2000,
                json_mode=True,
            )

            response_text = response.content or "[]"

            # Parse JSON response
            findings = self._parse_specialist_response(response_text, specialist)

            # Generate summary
            if findings:
                severity_counts = {}
                for f in findings:
                    severity_counts[f.severity] = severity_counts.get(f.severity, 0) + 1
                summary = f"Found {len(findings)} issues: " + ", ".join(
                    f"{count} {sev}" for sev, count in severity_counts.items()
                )
            else:
                summary = "No issues found"

            logger.debug(
                f"[MultiSpecialistReviewer] {specialist.value} review completed",
                extra={
                    "operation": "specialist_review",
                    "trace_id": self.trace_id,
                    "specialist": specialist.value,
                    "finding_count": len(findings),
                }
            )

            return findings, summary

        except Exception as e:
            logger.error(
                f"[MultiSpecialistReviewer] {specialist.value} review error",
                extra={
                    "operation": "specialist_review",
                    "trace_id": self.trace_id,
                    "specialist": specialist.value,
                    "error": str(e),
                }
            )
            raise

    def _build_user_prompt(
        self,
        diff_content: str,
        pr_context: Dict[str, Any],
        specialist: ReviewSpecialist,
    ) -> str:
        """Build the user prompt for a specialist review."""
        pr_number = pr_context.get("pr_number", "unknown")
        goal = pr_context.get("goal", "")
        repo = pr_context.get("repo", "")

        return f"""Review the following PR diff for {specialist.value} issues.

PR #{pr_number} in {repo}
Goal: {goal}

=== DIFF START ===
{diff_content[:50000]}
=== DIFF END ===

Analyze this diff and identify any {specialist.value} issues.
Return your findings as a JSON array."""

    def _parse_specialist_response(
        self,
        response_text: str,
        specialist: ReviewSpecialist,
    ) -> List[SpecialistFinding]:
        """Parse the LLM response into SpecialistFinding objects."""
        import json
        import re

        findings: List[SpecialistFinding] = []

        # Extract JSON from response (handle markdown code blocks)
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response_text)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find JSON array directly
            json_match = re.search(r'\[[\s\S]*\]', response_text)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = response_text

        try:
            parsed = json.loads(json_str)
            if not isinstance(parsed, list):
                parsed = [parsed] if parsed else []

            for item in parsed:
                if isinstance(item, dict):
                    findings.append(SpecialistFinding(
                        specialist=specialist,
                        severity=item.get("severity", "medium"),
                        category=item.get("category", "general"),
                        message=item.get("message", ""),
                        file_path=item.get("file_path"),
                        line_number=item.get("line_number"),
                        suggestion=item.get("suggestion"),
                    ))
        except json.JSONDecodeError as e:
            logger.warning(
                f"[MultiSpecialistReviewer] Failed to parse {specialist.value} response",
                extra={
                    "operation": "parse_response",
                    "trace_id": self.trace_id,
                    "specialist": specialist.value,
                    "error": str(e),
                }
            )

        return findings

    def _deduplicate_findings(
        self,
        findings: List[SpecialistFinding],
    ) -> List[SpecialistFinding]:
        """
        Deduplicate findings that overlap across specialists.

        Uses a simple heuristic: if two findings have the same file_path and
        line_number, keep the one with higher severity.
        """
        if not findings:
            return []

        # Group by (file_path, line_number)
        grouped: Dict[tuple, List[SpecialistFinding]] = {}
        no_location: List[SpecialistFinding] = []

        for finding in findings:
            if finding.file_path and finding.line_number:
                key = (finding.file_path, finding.line_number)
                if key not in grouped:
                    grouped[key] = []
                grouped[key].append(finding)
            else:
                no_location.append(finding)

        # For each group, keep the highest severity finding
        severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        deduplicated: List[SpecialistFinding] = []

        for key, group in grouped.items():
            if len(group) == 1:
                deduplicated.append(group[0])
            else:
                # Keep highest severity
                best = max(group, key=lambda f: severity_order.get(f.severity, 0))
                deduplicated.append(best)

        # Add findings without location (can't deduplicate these)
        deduplicated.extend(no_location)

        # Sort by severity (highest first)
        deduplicated.sort(key=lambda f: severity_order.get(f.severity, 0), reverse=True)

        return deduplicated

    def _calculate_overall_severity(
        self,
        findings: List[SpecialistFinding],
    ) -> str:
        """Calculate the overall severity from all findings."""
        if not findings:
            return "none"

        severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1, "none": 0}
        max_severity = max(
            (severity_order.get(f.severity, 0) for f in findings),
            default=0
        )

        for sev, order in severity_order.items():
            if order == max_severity:
                return sev

        return "none"

    def _self_critique_findings(
        self,
        findings: List[SpecialistFinding],
        diff_content: str,
        pr_context: Dict[str, Any],
    ) -> tuple[List[SpecialistFinding], Dict[str, Any]]:
        """
        Run self-critique on findings to filter false positives.

        Issue #4066 B-16: Self-Critique Specialist for Multi-Specialist Review

        This is the second pass of the two-pass review pipeline:
        1. First pass: Run specialists in parallel (SECURITY, PERFORMANCE, ARCHITECTURE)
        2. Second pass: Run SELF_CRITIQUE to verify findings and remove false positives

        Args:
            findings: List of findings from first-pass specialists
            diff_content: The original PR diff content
            pr_context: Context about the PR

        Returns:
            Tuple of (verified_findings, self_critique_stats)
        """
        import json
        import re

        if not findings:
            return findings, {
                "original_count": 0,
                "removed_count": 0,
                "verified_count": 0,
                "removal_rate": 0.0,
            }

        logger.info(
            "[MultiSpecialistReviewer] B-16: Starting self-critique verification",
            extra={
                "operation": "self_critique",
                "trace_id": self.trace_id,
                "finding_count": len(findings),
            }
        )

        try:
            client = get_client_for_task(TaskType.REVIEW)

            system_prompt = SPECIALIST_PROMPTS[ReviewSpecialist.SELF_CRITIQUE]

            findings_json = json.dumps([f.to_dict() for f in findings], indent=2)

            # Dynamically adjust diff truncation based on findings size
            # to prevent the overall prompt from exceeding token limits.
            # Reserve ~10k chars for prompt template and response buffer.
            max_total_chars = 40000
            diff_budget = max(5000, max_total_chars - len(findings_json))
            diff_snippet = diff_content[:diff_budget]

            user_prompt = f"""Verify the following findings from code review specialists.

=== ORIGINAL PR DIFF ===
{diff_snippet}
=== END DIFF ===

=== FINDINGS TO VERIFY ({len(findings)} total) ===
{findings_json}
=== END FINDINGS ===

For each finding (indexed 0 to {len(findings) - 1}), verify if it is accurate.
Output the indices of FALSE POSITIVES that should be removed."""

            response = client.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.1,
                max_tokens=2000,
                json_mode=True,
            )

            response_text = response.content or "{}"

            # Use non-greedy regex to match first complete JSON object
            json_match = re.search(r'\{[\s\S]*?\}', response_text)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = response_text

            try:
                result = json.loads(json_str)
                # Validate that result is a dict (LLM could return null, array, etc.)
                if not isinstance(result, dict):
                    logger.warning(
                        "[MultiSpecialistReviewer] B-16: Self-critique response is not a dict",
                        extra={
                            "operation": "self_critique",
                            "trace_id": self.trace_id,
                            "result_type": type(result).__name__,
                        }
                    )
                    false_positive_indices = []
                    verification_notes = []
                else:
                    false_positive_indices = result.get("false_positive_indices", [])
                    verification_notes = result.get("verification_notes", [])
            except json.JSONDecodeError as e:
                logger.warning(
                    "[MultiSpecialistReviewer] B-16: Failed to parse self-critique JSON",
                    extra={
                        "operation": "self_critique",
                        "trace_id": self.trace_id,
                        "error": str(e),
                        "response_preview": response_text[:500],
                    }
                )
                false_positive_indices = []
                verification_notes = []

            valid_indices = set(range(len(findings)))
            indices_to_remove = set()
            for idx in false_positive_indices:
                # Handle string indices (LLM may return "0" instead of 0)
                if isinstance(idx, str) and idx.isdigit():
                    idx = int(idx)

                if isinstance(idx, int) and idx in valid_indices:
                    indices_to_remove.add(idx)
                elif idx is not None:
                    # Log invalid indices for debugging (sanitize to prevent log injection)
                    logger.debug(
                        "[MultiSpecialistReviewer] B-16: Skipping invalid index",
                        extra={
                            "operation": "self_critique",
                            "trace_id": self.trace_id,
                            "invalid_index": repr(idx)[:50],
                        }
                    )

            verified_findings = [
                f for i, f in enumerate(findings) if i not in indices_to_remove
            ]

            removal_rate = len(indices_to_remove) / len(findings) if findings else 0.0

            stats = {
                "original_count": len(findings),
                "removed_count": len(indices_to_remove),
                "verified_count": len(verified_findings),
                "removal_rate": removal_rate,
                "removed_indices": list(indices_to_remove),
                "verification_notes": verification_notes,
            }

            logger.info(
                f"[MultiSpecialistReviewer] B-16: Self-critique completed, "
                f"removed {len(indices_to_remove)}/{len(findings)} false positives "
                f"({removal_rate:.1%})",
                extra={
                    "operation": "self_critique",
                    "trace_id": self.trace_id,
                    **stats,
                }
            )

            return verified_findings, stats

        except Exception as e:
            logger.error(
                "[MultiSpecialistReviewer] B-16: Self-critique failed, keeping all findings",
                extra={
                    "operation": "self_critique",
                    "trace_id": self.trace_id,
                    "error": str(e),
                }
            )
            return findings, {
                "original_count": len(findings),
                "removed_count": 0,
                "verified_count": len(findings),
                "removal_rate": 0.0,
                "error": str(e),
            }

    def __del__(self):
        """Cleanup executor on deletion."""
        if hasattr(self, '_executor'):
            self._executor.shutdown(wait=False)


def generate_multi_specialist_review(
    diff_content: str,
    pr_context: Dict[str, Any],
    trace_id: str,
) -> Dict[str, Any]:
    """
    Synchronous wrapper for multi-specialist review.

    This function provides a synchronous interface for the async
    MultiSpecialistReviewer, suitable for use in non-async contexts.

    Args:
        diff_content: The PR diff content to review
        pr_context: Context about the PR
        trace_id: Trace ID for telemetry

    Returns:
        Dictionary with review findings and metadata
    """
    reviewer = MultiSpecialistReviewer(trace_id=trace_id)

    # Run async review in event loop
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    findings = loop.run_until_complete(
        reviewer.review(diff_content, pr_context)
    )

    return findings.to_dict()


def review_with_specialists(
    diff_content: str,
    trace_id: str = "reviewer-node",
) -> SpecialistFindings:
    """
    Simplified synchronous wrapper for multi-specialist review.

    This function provides a simple interface for the langgraph_orchestrator
    reviewer_node integration. It returns SpecialistFindings directly (not dict)
    to allow access to .findings attribute.

    Args:
        diff_content: The PR diff content to review
        trace_id: Trace ID for telemetry (default: "reviewer-node")

    Returns:
        SpecialistFindings object with review findings and metadata
    """
    reviewer = MultiSpecialistReviewer(trace_id=trace_id)

    # Run async review in event loop
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # Use empty pr_context since langgraph_orchestrator only passes diff_content
    findings = loop.run_until_complete(
        reviewer.review(diff_content, pr_context={})
    )

    return findings
