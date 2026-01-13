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
    """
    SECURITY = "security"
    PERFORMANCE = "performance"
    ARCHITECTURE = "architecture"


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


# Specialist-specific system prompts
# Each prompt focuses the LLM on specific review aspects
SPECIALIST_PROMPTS: Dict[ReviewSpecialist, str] = {
    ReviewSpecialist.SECURITY: """You are a security-focused code reviewer for MorningAI.
Your role is to identify security vulnerabilities and risks in code changes.

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
            specialists: List of specialists to use (default: all)
            max_workers: Maximum parallel workers (default: 3)
        """
        self.trace_id = trace_id
        self.specialists = specialists or list(ReviewSpecialist)
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
            }
        )

        return SpecialistFindings(
            findings=deduplicated_findings,
            specialist_summaries=specialist_summaries,
            overall_severity=overall_severity,
            review_time_ms=review_time_ms,
            specialists_used=[s.value for s in self.specialists],
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
            response = client.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.1,
                max_tokens=2000,
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
