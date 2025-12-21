#!/usr/bin/env python3
"""
LLM Reviewer Adapter - Phase 6 PR-3 Implementation + EPIC B Diff-Aware Review
Integrates LLM-powered code review into LangGraph orchestrator

This module provides:
1. LLM-based code review using multiple providers (OpenAI, Gemini, Qwen)
2. A/B testing support via ExperimentManager
3. JSON response parsing with retry logic
4. Graceful fallback to CI-only review on failure
5. EPIC B: Diff-aware review with actual code changes (Issue #2595)

Usage:
    from llm_reviewer_adapter import generate_llm_review

    review = generate_llm_review(
        pr_number=123,
        pr_url="https://github.com/owner/repo/pull/123",
        ci_state="success",
        goal="Add new feature",
        repo="owner/repo",
        trace_id="abc123",
        diff="--- a/file.py\n+++ b/file.py\n...",  # EPIC B: actual diff
        diff_truncated=False
    )
"""
import json
import logging
import re
import time
from typing import Dict, Any, Optional

from common.config.settings import settings
from llm.client import get_client_for_task
from core.routing import TaskType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Phase B-2.5: Secrets redaction patterns (#2703)
# These patterns detect common secret formats to prevent leakage to LLM providers
# Uses capturing groups to preserve original formatting (spaces, quotes, delimiters)
# Includes negative lookahead (?!\[REDACTED) to avoid double-redaction
SECRETS_REDACTION_PATTERNS = [
    # AWS Access Keys (AKIA followed by 16 alphanumeric chars)
    (r'AKIA[0-9A-Z]{16}', '[REDACTED_AWS_KEY]'),
    # AWS Secret Keys (40 char base64-like string after common prefixes)
    # Preserves delimiter and spacing
    (r'(?i)(aws_secret_access_key|aws_secret_key)(\s*[=:]\s*)(["\']?)(?!\[REDACTED)[A-Za-z0-9/+=]{40}\3',
     r'\1\2\3[REDACTED_AWS_SECRET]\3'),
    # GitHub tokens (ghp_, gho_, github_pat_)
    (r'ghp_[A-Za-z0-9]{36,}', '[REDACTED_GITHUB_TOKEN]'),
    (r'gho_[A-Za-z0-9]{36,}', '[REDACTED_GITHUB_TOKEN]'),
    (r'github_pat_[A-Za-z0-9_]{22,}', '[REDACTED_GITHUB_TOKEN]'),
    # Generic API keys (sk-... pattern used by OpenAI, Anthropic, etc.)
    (r'sk-[A-Za-z0-9]{32,}', '[REDACTED_API_KEY]'),
    # Bearer tokens - preserve "Bearer " prefix with original spacing
    (r'(?i)(Bearer\s+)(?!\[REDACTED)[A-Za-z0-9\-_.~+/]+=*', r'\1[REDACTED_TOKEN]'),
    # Private keys (PEM format)
    (r'-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----[\s\S]*?-----END\s+(RSA\s+)?PRIVATE\s+KEY-----',
     '[REDACTED_PRIVATE_KEY]'),
    (r'-----BEGIN\s+EC\s+PRIVATE\s+KEY-----[\s\S]*?-----END\s+EC\s+PRIVATE\s+KEY-----',
     '[REDACTED_PRIVATE_KEY]'),
    # Generic secret assignments (PASSWORD=, SECRET=, TOKEN=, API_KEY=)
    # Preserves delimiter, spacing, and quote style
    (r'(?i)\b(PASSWORD|SECRET|TOKEN|API_KEY|APIKEY|SECRET_KEY|PRIVATE_KEY)\b'
     r'(\s*[=:]\s*)'
     r'(["\'])(?!\[REDACTED)[^"\']{8,}\3',
     r'\1\2\3[REDACTED_SECRET]\3'),
    # Environment variable style (export SECRET=value)
    # Preserves "export " prefix and spacing
    (r'(?i)(export\s+)(PASSWORD|SECRET|TOKEN|API_KEY|APIKEY|SECRET_KEY)(\s*=\s*)(?!\[REDACTED)[^\s]+',
     r'\1\2\3[REDACTED_SECRET]'),
    # JSON style secrets ("api_key": "value")
    # Preserves key name, colon spacing, and quotes
    (r'(?i)("(?:password|secret|token|api_key|apikey|secret_key|private_key|access_token)")(\s*:\s*)"(?!\[REDACTED)[^"]{8,}"',
     r'\1\2"[REDACTED_SECRET]"'),
    # YAML style secrets (api_key: value)
    # Preserves indentation and colon spacing
    (r'(?i)^(\s*)(password|secret|token|api_key|apikey|secret_key|private_key|access_token)(\s*:\s*)(?!\[REDACTED)[^\s#][^\n]*',
     r'\1\2\3[REDACTED_SECRET]'),
]


def sanitize_diff_content(diff: str) -> tuple[str, int]:
    """
    Sanitize diff content by redacting potential secrets.

    Phase B-2.5: Apply secrets redaction to diff context (#2703)
    This prevents secrets from being sent to LLM providers.

    Args:
        diff: Raw diff content

    Returns:
        Tuple of (sanitized_diff, redaction_count)
    """
    if not diff:
        return diff, 0

    sanitized = diff
    total_redactions = 0

    for pattern, replacement in SECRETS_REDACTION_PATTERNS:
        try:
            # Count matches before replacement
            matches = len(re.findall(pattern, sanitized, re.MULTILINE))
            if matches > 0:
                sanitized = re.sub(pattern, replacement, sanitized, flags=re.MULTILINE)
                total_redactions += matches
        except re.error as e:
            logger.warning(f"[LLM Reviewer] Regex error in secrets redaction: {e}")
            continue

    if total_redactions > 0:
        logger.info(
            f"[LLM Reviewer] Redacted {total_redactions} potential secrets from diff",
            extra={
                "operation": "sanitize_diff",
                "redaction_count": total_redactions
            }
        )

    return sanitized, total_redactions


SEVERITY_ORDER = {
    "none": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}


def combine_severity(ci_severity: str, llm_severity: str) -> str:
    """
    Combine CI and LLM severities, taking the worse (higher) severity.

    Args:
        ci_severity: Severity from CI-based review
        llm_severity: Severity from LLM review

    Returns:
        Combined severity (the worse of the two)
    """
    ci_val = SEVERITY_ORDER.get(ci_severity, 0)
    llm_val = SEVERITY_ORDER.get(llm_severity, 0)
    final_val = max(ci_val, llm_val)

    for name, val in SEVERITY_ORDER.items():
        if val == final_val:
            return name
    return llm_severity or ci_severity


class LLMReviewerAdapter:
    """
    Adapter for LLM-powered code review in LangGraph orchestrator

    Features:
    - Multi-provider LLM support via get_client_for_task (task-based routing)
    - RoutingEngine integration for policy-driven model selection
    - JSON response parsing with retry/repair logic
    - Graceful fallback on failure
    """

    def __init__(self, trace_id: str, risk_level: str = "medium"):
        """
        Initialize LLM reviewer adapter

        Args:
            trace_id: Trace ID for logging
            risk_level: Risk level for routing decision ("high", "medium", "low")
        """
        self.trace_id = trace_id
        self.llm_client = None
        try:
            # Use task-based routing via RoutingEngine instead of component-based
            # This ensures Routing Policy is respected, not bypassed by ExperimentManager
            self.llm_client = get_client_for_task(
                task_type=TaskType.REVIEW,
                risk_level=risk_level
            )
            logger.info(
                f"[LLM Reviewer] Initialized with provider={self.llm_client.provider_name} via task-based routing",
                extra={
                    "operation": "llm_reviewer_init",
                    "trace_id": trace_id,
                    "provider": self.llm_client.provider_name,
                    "routing_method": "task_based",
                    "task_type": TaskType.REVIEW.value,
                    "risk_level": risk_level
                }
            )
        except Exception as e:
            logger.warning(f"[LLM Reviewer] LLM client not available: {e}")

    def generate_review(
        self,
        pr_number: Optional[int],
        pr_url: Optional[str],
        ci_state: str,
        goal: str,
        repo: str,
        base_quality_score: int,
        base_severity: str,
        diff: Optional[str] = None,
        diff_truncated: bool = False,
        diff_files: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Generate LLM-powered code review

        Args:
            pr_number: Pull request number
            pr_url: Pull request URL
            ci_state: CI check state (success, failure, pending, unknown)
            goal: Original user goal/task description
            repo: GitHub repository (owner/repo format)
            base_quality_score: Base quality score from CI-only review
            base_severity: Base severity from CI-only review
            diff: PR diff content (EPIC B Phase B-1)
            diff_truncated: Whether diff was truncated (EPIC B Phase B-2)
            diff_files: List of changed files metadata (EPIC B Phase B-1)

        Returns:
            Dict with review results:
            - quality_score: Combined quality score (0-100)
            - severity: Combined severity level
            - summary: Review summary
            - decision: Review decision (approve, needs_changes, block)
            - comments: List of review comments
            - llm_used: Whether LLM was used
            - provider: LLM provider used (if any)
            - diff_aware: Whether diff was available for review (EPIC B)
        """
        if not self.llm_client or not self.llm_client.is_available():
            logger.warning("[LLM Reviewer] LLM client not available, skipping LLM review")
            return self._get_fallback_result(base_quality_score, base_severity)

        try:
            has_diff = bool(diff and diff.strip())
            logger.info(
                f"[LLM Reviewer] Generating review for PR #{pr_number}",
                extra={
                    "operation": "llm_reviewer",
                    "trace_id": self.trace_id,
                    "pr_number": pr_number,
                    "ci_state": ci_state,
                    "diff_aware": has_diff,
                    "diff_truncated": diff_truncated,
                    "diff_file_count": len(diff_files) if diff_files else 0
                }
            )

            review_data = self._call_llm(
                pr_number=pr_number,
                pr_url=pr_url,
                ci_state=ci_state,
                goal=goal,
                repo=repo,
                diff=diff,
                diff_truncated=diff_truncated,
                diff_files=diff_files
            )

            llm_score = review_data.get("quality_score", base_quality_score)
            llm_severity = review_data.get("severity", "none")

            final_score = max(0, min(int(llm_score), base_quality_score, 100))
            final_severity = combine_severity(base_severity, llm_severity)

            logger.info(
                f"[LLM Reviewer] Review completed: score={final_score}, severity={final_severity}",
                extra={
                    "operation": "llm_reviewer",
                    "trace_id": self.trace_id,
                    "llm_score": llm_score,
                    "base_score": base_quality_score,
                    "final_score": final_score,
                    "llm_severity": llm_severity,
                    "base_severity": base_severity,
                    "final_severity": final_severity,
                    "review_time_ms": review_data.get("review_time_ms", 0)
                }
            )

            return {
                "quality_score": final_score,
                "severity": final_severity,
                "summary": review_data.get("summary", ""),
                "decision": review_data.get("decision", "needs_changes"),
                "comments": review_data.get("comments", []),
                "llm_used": True,
                "provider": self.llm_client.provider_name,
                "review_time_ms": review_data.get("review_time_ms", 0),
                "diff_aware": has_diff
            }

        except json.JSONDecodeError as e:
            # Phase 1 Quick Win: Distinguish JSON parse failures from LLM unavailability
            logger.error(
                f"[LLM Reviewer] LLM JSON parse failed: {e}",
                extra={
                    "operation": "llm_reviewer",
                    "trace_id": self.trace_id,
                    "error": str(e),
                    "error_type": "json_parse_failed"
                },
                exc_info=True
            )
            return self._get_fallback_result(
                base_quality_score, base_severity, fallback_reason="llm_json_parse_failed"
            )
        except Exception as e:
            # P2 Follow-up: Determine fallback reason based on exception type
            # Prefer checking exception types over string matching for robustness
            fallback_reason = self._classify_exception(e)

            logger.error(
                f"[LLM Reviewer] Review failed ({fallback_reason}): {e}",
                extra={
                    "operation": "llm_reviewer",
                    "trace_id": self.trace_id,
                    "error": str(e),
                    "error_type": fallback_reason
                },
                exc_info=True
            )
            return self._get_fallback_result(
                base_quality_score, base_severity, fallback_reason=fallback_reason
            )

    def _call_llm(
        self,
        pr_number: Optional[int],
        pr_url: Optional[str],
        ci_state: str,
        goal: str,
        repo: str,
        diff: Optional[str] = None,
        diff_truncated: bool = False,
        diff_files: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Call LLM to generate review

        Args:
            pr_number: Pull request number
            pr_url: Pull request URL
            ci_state: CI check state
            goal: User's goal
            repo: GitHub repository
            diff: PR diff content (EPIC B)
            diff_truncated: Whether diff was truncated (EPIC B)
            diff_files: List of changed files metadata (EPIC B)

        Returns:
            Dict with review data and timing
        """
        use_json_mode = getattr(settings, 'reviewer_json_mode', True)
        has_diff = bool(diff and diff.strip())

        # EPIC B: Use diff-aware prompt if diff is available
        if has_diff:
            system_prompt = self._get_diff_aware_system_prompt()
            user_prompt = self._build_diff_aware_user_prompt(
                repo=repo,
                pr_number=pr_number,
                pr_url=pr_url,
                ci_state=ci_state,
                goal=goal,
                diff=diff,
                diff_truncated=diff_truncated,
                diff_files=diff_files
            )
        else:
            # Fallback to metadata-only review (original behavior)
            system_prompt = self._get_metadata_only_system_prompt()
            user_prompt = self._build_metadata_only_user_prompt(
                repo=repo,
                pr_number=pr_number,
                pr_url=pr_url,
                ci_state=ci_state,
                goal=goal
            )

        start_time = time.time()

        try:
            if use_json_mode:
                logger.info(f"[LLM Reviewer] Using JSON mode for trace_id={self.trace_id}")

            # Build kwargs for provider-specific parameters
            # Phase 1 Quick Win: Increase max_tokens to prevent JSON truncation
            # Previous value of 1000 caused truncated JSON responses for longer reviews
            generate_kwargs = {
                "prompt": user_prompt,
                "system_prompt": system_prompt,
                "temperature": 0.5,
                "max_tokens": 4000,
                "json_mode": use_json_mode,
                "timeout": 30
            }

            # Add thinking_level for Gemini 3 models based on reasoning_mode_enabled setting
            if self.llm_client.provider_name == "gemini":
                reasoning_mode_enabled = getattr(settings, 'reasoning_mode_enabled', False)
                thinking_level = "high" if reasoning_mode_enabled else "low"
                generate_kwargs["thinking_level"] = thinking_level
                logger.info(
                    f"[LLM Reviewer] Using thinking_level={thinking_level} for Gemini provider",
                    extra={
                        "operation": "llm_reviewer",
                        "trace_id": self.trace_id,
                        "thinking_level": thinking_level,
                        "reasoning_mode_enabled": reasoning_mode_enabled
                    }
                )

            response = self.llm_client.generate(**generate_kwargs)

            review_time_ms = (time.time() - start_time) * 1000

            content = response.content
            review = self._parse_json_with_retry(content, use_json_mode)

            logger.info(
                f"[LLM Reviewer] Generated review using {response.provider}/{response.model}",
                extra={
                    "operation": "llm_reviewer",
                    "trace_id": self.trace_id,
                    "provider": response.provider,
                    "model": response.model,
                    "usage": response.usage,
                    "review_time_ms": review_time_ms
                }
            )

            review["review_time_ms"] = review_time_ms
            return review

        except json.JSONDecodeError as e:
            logger.error(f"[LLM Reviewer] Failed to parse LLM response as JSON: {e}")
            raise
        except Exception as e:
            logger.error(f"[LLM Reviewer] LLM API call failed: {e}")
            raise

    def _get_diff_aware_system_prompt(self) -> str:
        """
        Get system prompt for diff-aware code review (EPIC B Phase B-3)

        Phase B-3.1: Updated to clarify line number semantics for inline comments.
        Line numbers must be RIGHT-side (new file) line numbers that appear in
        the diff hunks, not absolute file line numbers.

        Returns:
            System prompt string for LLM
        """
        return """You are a senior software engineer performing code review for a pull request.

You receive:
1. The CI status for this PR (success, failure, pending, or unknown)
2. The task goal/description
3. Repository and PR metadata
4. The actual code diff showing the changes made

Your job is to:
1. Review the actual code changes in the diff
2. Identify bugs, security issues, performance problems, and style concerns
3. Assess overall code quality based on the changes
4. Produce a JSON object that summarizes your review

Rules:
- Focus on the actual code changes, not hypothetical issues
- Be specific: reference file names and line numbers when possible
- Be constructive: suggest improvements, not just criticisms
- Be conservative with severity: only use "critical" for serious bugs or security issues
- If CI failed, investigate if the diff might be related
- Always respond with valid JSON only, no extra commentary

IMPORTANT - Line Number Semantics:
When providing line numbers in comments, use the NEW FILE line numbers (RIGHT side of diff).
These are the line numbers shown after the "+" in hunk headers: @@ -old,len +NEW,len @@
Only reference lines that appear in the diff you can see. If the diff is truncated or you
cannot see the exact line, omit the line fields and provide a file-level comment instead.

Example: For a hunk "@@ -10,5 +12,7 @@", lines 12-18 are valid RIGHT-side line numbers.
Lines marked with "+" or " " (context) in the hunk body are valid targets.
Lines marked with "-" are deletions and should NOT be referenced.

Output format (strict JSON):
{
  "summary": "Brief summary of the code changes and overall assessment",
  "quality_score": 0-100,
  "severity": "none" | "low" | "medium" | "high" | "critical",
  "decision": "approve" | "needs_changes" | "block",
  "comments": [
    {
      "severity": "nit" | "suggestion" | "warning" | "error",
      "category": "style" | "bug" | "performance" | "security" | "maintainability" | "other",
      "file": "path/to/file.py",
      "start_line": 40,
      "end_line": 42,
      "message": "Specific feedback about this code"
    }
  ]
}

Note on comments:
- Use "start_line" and "end_line" for multi-line comments (preferred)
- For single-line comments, set start_line = end_line
- If you cannot determine the exact line from the diff, omit line fields entirely
- File-level comments (no line fields) are acceptable when line precision is uncertain

Guidelines for scoring:
- Clean code, good practices, CI passed: quality_score 80-95
- Minor issues, style concerns: quality_score 65-80
- Moderate issues, needs refactoring: quality_score 50-65
- Serious bugs or security issues: quality_score 30-50
- Critical issues requiring immediate attention: quality_score 0-30
"""

    def _build_diff_aware_user_prompt(
        self,
        repo: str,
        pr_number: Optional[int],
        pr_url: Optional[str],
        ci_state: str,
        goal: str,
        diff: str,
        diff_truncated: bool,
        diff_files: Optional[list]
    ) -> str:
        """
        Build user prompt for diff-aware code review (EPIC B Phase B-3)

        Args:
            repo: GitHub repository
            pr_number: Pull request number
            pr_url: Pull request URL
            ci_state: CI check state
            goal: User's goal
            diff: PR diff content
            diff_truncated: Whether diff was truncated
            diff_files: List of changed files metadata

        Returns:
            User prompt string for LLM
        """
        # Phase B-2.5: Sanitize diff content to redact secrets (#2703)
        sanitized_diff, redaction_count = sanitize_diff_content(diff)
        if redaction_count > 0:
            logger.debug(
                f"[LLM Reviewer] Sanitized diff for PR #{pr_number}: "
                f"{redaction_count} secrets redacted",
                extra={
                    "operation": "build_diff_aware_prompt",
                    "pr_number": pr_number,
                    "redaction_count": redaction_count
                }
            )

        # Build file summary if available
        file_summary = ""
        if diff_files:
            file_list = []
            for f in diff_files[:10]:  # Limit to first 10 files
                file_list.append(
                    f"  - {f['filename']} (+{f['additions']}/-{f['deletions']})"
                )
            file_summary = "\n**Changed Files:**\n" + "\n".join(file_list)
            if len(diff_files) > 10:
                file_summary += f"\n  ... and {len(diff_files) - 10} more files"

        # Build truncation warning if applicable
        truncation_warning = ""
        if diff_truncated:
            truncation_warning = "\n\n**Note:** The diff has been truncated due to size limits. Some files may not be shown."

        return f"""**Pull Request Information**
- Repository: {repo}
- PR Number: {pr_number or "Unknown"}
- PR URL: {pr_url or "Not available"}
- CI Status: {ci_state}
{file_summary}

**Task Goal/Description:**
{goal}
{truncation_warning}

**Code Diff:**
```diff
{sanitized_diff}
```

Please review the code changes above and provide your assessment as JSON."""

    def _get_metadata_only_system_prompt(self) -> str:
        """
        Get system prompt for metadata-only review (original behavior)

        Returns:
            System prompt string for LLM
        """
        return """You are a senior software engineer performing code review for a pull request.

You receive:
1. The CI status for this PR (success, failure, pending, or unknown)
2. The task goal/description
3. Repository and PR metadata

IMPORTANT: You do NOT see the actual code diff. You are providing a high-level risk assessment based on the available metadata and CI status. Be conservative in your assessment.

Your job is to:
1. Assess overall code quality risk based on CI status and task complexity
2. Identify potential concerns based on the task description
3. Produce a JSON object that summarizes your assessment

Rules:
- Be conservative: if CI failed, severity should be at least "high"
- If CI passed, you can still flag concerns based on task complexity
- If information is limited, default to moderate scores and "needs_changes" decision
- Always respond with valid JSON only, no extra commentary

Output format (strict JSON):
{
  "summary": "Brief assessment of the PR based on available information",
  "quality_score": 0-100,
  "severity": "none" | "low" | "medium" | "high" | "critical",
  "decision": "approve" | "needs_changes" | "block",
  "comments": [
    {
      "severity": "nit" | "suggestion" | "warning" | "error",
      "category": "style" | "bug" | "performance" | "security" | "maintainability" | "other",
      "message": "Description of concern or suggestion"
    }
  ]
}

Guidelines for scoring:
- CI success + simple task: quality_score 70-85, severity "none" or "low"
- CI success + complex task: quality_score 60-75, severity "low" or "medium"
- CI pending: quality_score 50-65, severity "medium"
- CI failure: quality_score 30-50, severity "high" or "critical"
"""

    def _build_metadata_only_user_prompt(
        self,
        repo: str,
        pr_number: Optional[int],
        pr_url: Optional[str],
        ci_state: str,
        goal: str
    ) -> str:
        """
        Build user prompt for metadata-only review (original behavior)

        Args:
            repo: GitHub repository
            pr_number: Pull request number
            pr_url: Pull request URL
            ci_state: CI check state
            goal: User's goal

        Returns:
            User prompt string for LLM
        """
        return f"""**Pull Request Information**
- Repository: {repo}
- PR Number: {pr_number or "Unknown"}
- PR URL: {pr_url or "Not available"}
- CI Status: {ci_state}

**Task Goal/Description**:
{goal}

Based on this information, provide your code review assessment as JSON.
Remember: You cannot see the actual code changes, so focus on risk assessment based on CI status and task complexity."""

    def _parse_json_with_retry(self, content: str, use_json_mode: bool) -> Dict[str, Any]:
        """
        Parse JSON with retry and repair logic

        Args:
            content: Raw LLM response
            use_json_mode: Whether JSON mode was used

        Returns:
            Parsed review dict

        Raises:
            json.JSONDecodeError: If parsing fails after retry
        """
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.warning(f"[LLM Reviewer] First parse attempt failed: {e}, attempting repair")

            try:
                cleaned_content = self._clean_json_response(content)
                logger.info(f"[LLM Reviewer] Cleaned content for trace_id={self.trace_id}")
                return json.loads(cleaned_content)
            except json.JSONDecodeError as e2:
                logger.error(f"[LLM Reviewer] Failed to parse even after cleaning: {e2}")
                raise e2

    def _clean_json_response(self, content: str) -> str:
        """
        Clean and repair JSON response from LLM

        Handles common issues:
        - Markdown code blocks (```json ... ```)
        - Explanatory text before/after JSON
        - Extra whitespace

        Args:
            content: Raw LLM response

        Returns:
            Cleaned JSON string
        """
        content = content.strip()

        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]

        if content.endswith("```"):
            content = content[:-3]

        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1 and end > start:
            content = content[start:end + 1]

        return content.strip()

    def _classify_exception(self, e: Exception) -> str:
        """
        Classify exception to determine fallback reason.

        P2 Follow-up: Uses exception type checking instead of string matching
        for more robust error classification.

        Args:
            e: The exception to classify

        Returns:
            Fallback reason string: llm_timeout, llm_connection_error, or llm_api_error
        """
        # Check exception type first (more robust than string matching)
        exception_type = type(e).__name__.lower()

        # Timeout exceptions
        if any(timeout_type in exception_type for timeout_type in [
            'timeout', 'timedout', 'readtimeout', 'connecttimeout'
        ]):
            return "llm_timeout"

        # Connection exceptions (excluding 'http' to avoid misclassifying HTTPStatusError)
        if any(conn_type in exception_type for conn_type in [
            'connection', 'network', 'socket', 'dns', 'ssl'
        ]):
            return "llm_connection_error"

        # Check exception message as fallback (for wrapped exceptions)
        error_str = str(e).lower()
        if "timeout" in error_str:
            return "llm_timeout"
        if any(conn_word in error_str for conn_word in ["connection", "network", "socket"]):
            return "llm_connection_error"

        # Default to API error for other exceptions
        return "llm_api_error"

    def _get_fallback_result(
        self,
        base_quality_score: int,
        base_severity: str,
        fallback_reason: str = "llm_unavailable"
    ) -> Dict[str, Any]:
        """
        Get fallback result when LLM review fails

        Args:
            base_quality_score: Base quality score from CI-only review
            base_severity: Base severity from CI-only review
            fallback_reason: Reason for fallback (llm_unavailable, llm_json_parse_failed,
                           llm_timeout, llm_connection_error, llm_api_error)

        Returns:
            Dict with fallback review results including fallback_reason
        """
        if base_severity == "none":
            decision = "approve"
        else:
            decision = "needs_changes"

        # Phase 1 Quick Win: Generate descriptive summary based on fallback reason
        reason_summaries = {
            "llm_unavailable": "LLM review unavailable, using CI-based assessment",
            "llm_json_parse_failed": "LLM response parsing failed, using CI-based assessment",
            "llm_timeout": "LLM request timed out, using CI-based assessment",
            "llm_connection_error": "LLM connection failed, using CI-based assessment",
            "llm_api_error": "LLM API error occurred, using CI-based assessment"
        }
        summary = reason_summaries.get(fallback_reason, reason_summaries["llm_unavailable"])

        return {
            "quality_score": base_quality_score,
            "severity": base_severity,
            "summary": summary,
            "decision": decision,
            "comments": [],
            "llm_used": False,
            "provider": None,
            "review_time_ms": 0,
            "diff_aware": False,
            "fallback_reason": fallback_reason
        }


def generate_llm_review(
    pr_number: Optional[int],
    pr_url: Optional[str],
    ci_state: str,
    goal: str,
    repo: str,
    trace_id: str,
    base_quality_score: int,
    base_severity: str,
    diff: Optional[str] = None,
    diff_truncated: bool = False,
    diff_files: Optional[list] = None
) -> Dict[str, Any]:
    """
    Convenience function to generate LLM-powered code review

    Args:
        pr_number: Pull request number
        pr_url: Pull request URL
        ci_state: CI check state (success, failure, pending, unknown)
        goal: Original user goal/task description
        repo: GitHub repository (owner/repo format)
        trace_id: Unique trace identifier
        base_quality_score: Base quality score from CI-only review
        base_severity: Base severity from CI-only review
        diff: PR diff content (EPIC B Phase B-1)
        diff_truncated: Whether diff was truncated (EPIC B Phase B-2)
        diff_files: List of changed files metadata (EPIC B Phase B-1)

    Returns:
        Dict with review results
    """
    adapter = LLMReviewerAdapter(trace_id=trace_id)
    return adapter.generate_review(
        pr_number=pr_number,
        pr_url=pr_url,
        ci_state=ci_state,
        goal=goal,
        repo=repo,
        base_quality_score=base_quality_score,
        base_severity=base_severity,
        diff=diff,
        diff_truncated=diff_truncated,
        diff_files=diff_files
    )
