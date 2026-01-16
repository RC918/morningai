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
from resource_telemetry import log_prompt_build_bytes, log_llm_response_bytes

from review_context import (
    generate_multi_specialist_review,
    analyze_test_coverage,
    analyze_dependencies,
    get_feedback_loop,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Issue #3775: PR description truncation limit constant
# Extracted from magic number to improve maintainability (gemini-code-assist review of PR #3771)
MAX_PR_DESCRIPTION_CHARS = 500

# EPIC B Phase 3: Pre-compiled prompt injection patterns (MorningAI Code Review feedback)
# These patterns detect common prompt injection attempts to prevent hijacking LLM repair prompts
# Pre-compiled at module level for performance (avoids re-compilation on each call)
PROMPT_INJECTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    # Common instruction override attempts
    re.compile(r'(?i)ignore\s+(all\s+)?previous\s+instructions?'),
    re.compile(r'(?i)disregard\s+(all\s+)?previous\s+instructions?'),
    re.compile(r'(?i)forget\s+(all\s+)?previous\s+instructions?'),
    # Role manipulation attempts
    re.compile(r'(?i)you\s+are\s+now\s+a'),
    re.compile(r'(?i)act\s+as\s+if\s+you\s+are'),
    re.compile(r'(?i)pretend\s+you\s+are'),
    # Chat role markers (could be used to inject fake messages)
    re.compile(r'(?i)system:\s*'),
    re.compile(r'(?i)assistant:\s*'),
    re.compile(r'(?i)user:\s*'),
    # Model-specific control tokens (Llama, Mistral, ChatML formats)
    re.compile(re.escape('[INST]')),
    re.compile(re.escape('[/INST]')),
    re.compile(re.escape('<<SYS>>')),
    re.compile(re.escape('<</SYS>>')),
    re.compile(re.escape('<|im_start|>')),
    re.compile(re.escape('<|im_end|>')),
    re.compile(re.escape('<|system|>')),
    re.compile(re.escape('<|user|>')),
    re.compile(re.escape('<|assistant|>')),
)


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


def annotate_diff_with_line_numbers(diff: str) -> str:
    """
    Annotate unified diff with explicit line numbers for LLM consumption.

    Tactic 3 (Line Number Mapping): Pre-annotate diff so LLM can "copy" line numbers
    instead of calculating them from hunk headers.

    Format:
        + (Line 50) print("hello")
        - (Line 49) print("old")
          (Line 51) existing_code()  # context line

    This significantly reduces line number hallucination by Qwen and other models.

    Args:
        diff: Raw unified diff string

    Returns:
        Annotated diff with explicit line numbers
    """
    if not diff:
        return diff

    lines = diff.split('\n')
    result = []
    old_line = 0
    new_line = 0
    in_hunk = False

    # Regex for hunk header: @@ -old_start,old_len +new_start,new_len @@
    hunk_pattern = re.compile(r'^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@')

    for line in lines:
        # Check for hunk header
        hunk_match = hunk_pattern.match(line)
        if hunk_match:
            old_line = int(hunk_match.group(1))
            new_line = int(hunk_match.group(2))
            in_hunk = True
            result.append(line)
            continue

        # Check for file headers (not in hunk)
        if line.startswith('diff ') or line.startswith('---') or line.startswith('+++'):
            in_hunk = False
            result.append(line)
            continue

        # Process hunk body
        if in_hunk and line:
            first_char = line[0] if line else ''
            rest = line[1:] if len(line) > 1 else ''

            if first_char == '+':
                # Addition: show new line number (this is what LLM should reference)
                result.append(f'+ (Line {new_line}) {rest}')
                new_line += 1
            elif first_char == '-':
                # Deletion: show old line number (for reference, but LLM should NOT comment on these)
                result.append(f'- (Line {old_line}) {rest}')
                old_line += 1
            elif first_char == ' ':
                # Context: show new line number (LLM can reference but prefer + lines)
                result.append(f'  (Line {new_line}) {rest}')
                old_line += 1
                new_line += 1
            elif first_char == '\\':
                # "\ No newline at end of file" - keep as-is
                result.append(line)
            else:
                # Unknown or empty - keep as-is
                result.append(line)
        else:
            result.append(line)

    return '\n'.join(result)


def truncate_diff_for_token_budget(
    annotated_diff: str,
    max_chars: int = 80000
) -> tuple[str, dict]:
    """
    Truncate annotated diff to fit within token budget while preserving Strict Mode semantics.

    Strategy (hybrid approach per Blueprint Stability requirements):
    1. First pass: Aggressively reduce context lines (keep only 1 line around + lines)
    2. Second pass: If still too large, drop later hunks/files while keeping structure

    This preserves the most reviewable content (+ lines) since Strict Mode only allows
    inline comments on addition lines anyway.

    Args:
        annotated_diff: Diff already annotated with line numbers via annotate_diff_with_line_numbers()
        max_chars: Maximum characters allowed (default 80k chars ~= 20k tokens)

    Returns:
        Tuple of (truncated_diff, telemetry_dict) where telemetry_dict contains:
        - original_chars: Original diff length
        - truncated_chars: Final diff length
        - was_truncated: Whether truncation occurred
        - context_lines_dropped: Number of context lines removed
        - hunks_dropped: Number of hunks removed
        - files_dropped: Number of files removed
    """
    telemetry = {
        "original_chars": len(annotated_diff),
        "truncated_chars": len(annotated_diff),
        "was_truncated": False,
        "context_lines_dropped": 0,
        "hunks_dropped": 0,
        "files_dropped": 0,
    }

    if not annotated_diff or len(annotated_diff) <= max_chars:
        return annotated_diff, telemetry

    lines = annotated_diff.split('\n')

    # Phase 1: Identify line types and structure
    # Track which lines are: file headers, hunk headers, additions, deletions, context
    line_types = []
    current_file = None
    files_structure = []  # List of (file_header_start, file_header_end, hunks)
    current_file_start = None
    current_hunks = []
    current_hunk_start = None

    for i, line in enumerate(lines):
        if line.startswith('diff '):
            # New file
            if current_file is not None and current_file_start is not None:
                if current_hunk_start is not None:
                    current_hunks.append((current_hunk_start, i - 1))
                files_structure.append((current_file_start, current_hunks))
            current_file = line
            current_file_start = i
            current_hunks = []
            current_hunk_start = None
            line_types.append('file_header')
        elif line.startswith('---') or line.startswith('+++'):
            line_types.append('file_header')
        elif line.startswith('@@'):
            if current_hunk_start is not None:
                current_hunks.append((current_hunk_start, i - 1))
            current_hunk_start = i
            line_types.append('hunk_header')
        elif line.startswith('+ (Line'):
            line_types.append('addition')
        elif line.startswith('- (Line'):
            line_types.append('deletion')
        elif line.startswith('  (Line'):
            line_types.append('context')
        elif line.startswith('\\'):
            line_types.append('no_newline')
        else:
            line_types.append('other')

    # Finalize last file/hunk
    if current_file_start is not None:
        if current_hunk_start is not None:
            current_hunks.append((current_hunk_start, len(lines) - 1))
        files_structure.append((current_file_start, current_hunks))

    # Truncation sentinel to signal incomplete diff to LLM
    TRUNCATION_SENTINEL = "\n\n... [DIFF TRUNCATED - remaining content omitted due to size limit] ..."

    # Fallback: If no 'diff ' headers found, treat entire input as single reviewable block
    # This prevents returning empty diff when input uses non-standard format (e.g., patch files)
    if not files_structure:
        # Simple truncation: keep all lines up to max_chars with newline-safe boundary
        if len(annotated_diff) > max_chars:
            # Reserve space for sentinel
            effective_max = max_chars - len(TRUNCATION_SENTINEL)
            # Find last newline before effective_max to avoid cutting mid-line
            truncate_at = annotated_diff.rfind('\n', 0, effective_max)
            if truncate_at == -1:
                truncate_at = effective_max
            truncated = annotated_diff[:truncate_at] + TRUNCATION_SENTINEL
            telemetry["truncated_chars"] = len(truncated)
            telemetry["was_truncated"] = True
            return truncated, telemetry
        return annotated_diff, telemetry

    # Format guard: Check if input appears to be properly annotated
    # If no annotated line prefixes found, the Phase 2 logic won't work correctly
    has_annotated_format = any(
        lt in ('addition', 'deletion', 'context') for lt in line_types
    )
    if not has_annotated_format and len(annotated_diff) > max_chars:
        # Input is not in expected annotated format - use conservative truncation
        effective_max = max_chars - len(TRUNCATION_SENTINEL)
        truncate_at = annotated_diff.rfind('\n', 0, effective_max)
        if truncate_at == -1:
            truncate_at = effective_max
        truncated = annotated_diff[:truncate_at] + TRUNCATION_SENTINEL
        telemetry["truncated_chars"] = len(truncated)
        telemetry["was_truncated"] = True
        return truncated, telemetry

    # Phase 2: Reduce context lines (keep only 1 line before/after each + line)
    # This is the primary truncation strategy for Strict Mode
    keep_lines = set()

    for i, line_type in enumerate(line_types):
        if line_type in ('file_header', 'hunk_header', 'addition', 'deletion', 'no_newline'):
            keep_lines.add(i)
        elif line_type == 'context':
            # Keep context line only if adjacent to an addition
            prev_is_addition = i > 0 and line_types[i - 1] == 'addition'
            next_is_addition = i < len(line_types) - 1 and line_types[i + 1] == 'addition'
            if prev_is_addition or next_is_addition:
                keep_lines.add(i)
            else:
                telemetry["context_lines_dropped"] += 1
        else:
            keep_lines.add(i)

    # Build reduced diff
    reduced_lines = [lines[i] for i in sorted(keep_lines)]
    reduced_diff = '\n'.join(reduced_lines)

    if len(reduced_diff) <= max_chars:
        telemetry["truncated_chars"] = len(reduced_diff)
        telemetry["was_truncated"] = telemetry["context_lines_dropped"] > 0
        return reduced_diff, telemetry

    # Phase 3: Still too large - drop later files/hunks
    # Keep structure intact by dropping complete hunks from the end
    result_lines = []
    current_chars = 0
    files_kept = 0
    hunks_kept = 0
    total_hunks = sum(len(hunks) for _, hunks in files_structure)
    total_files = len(files_structure)

    for file_start, hunks in files_structure:
        # Calculate file header size by finding first hunk or next file boundary
        # This avoids hardcoded assumptions about header line count
        if hunks:
            file_header_end = hunks[0][0]
        else:
            # No hunks: scan forward to find next 'diff ' or '@@' or end of lines
            file_header_end = len(lines)
            for j in range(file_start + 1, len(lines)):
                if lines[j].startswith('diff ') or lines[j].startswith('@@'):
                    file_header_end = j
                    break
        file_header_lines = [lines[i] for i in range(file_start, file_header_end) if i in keep_lines]
        file_header_text = '\n'.join(file_header_lines)

        if current_chars + len(file_header_text) > max_chars:
            break

        result_lines.extend(file_header_lines)
        current_chars += len(file_header_text) + 1
        files_kept += 1

        for hunk_start, hunk_end in hunks:
            hunk_lines = [lines[i] for i in range(hunk_start, hunk_end + 1) if i in keep_lines]
            hunk_text = '\n'.join(hunk_lines)

            if current_chars + len(hunk_text) > max_chars:
                break

            result_lines.extend(hunk_lines)
            current_chars += len(hunk_text) + 1
            hunks_kept += 1

    telemetry["hunks_dropped"] = total_hunks - hunks_kept
    telemetry["files_dropped"] = total_files - files_kept
    telemetry["was_truncated"] = True

    final_diff = '\n'.join(result_lines)
    # Add truncation sentinel if we actually dropped content
    if telemetry["hunks_dropped"] > 0 or telemetry["files_dropped"] > 0:
        final_diff += TRUNCATION_SENTINEL
    telemetry["truncated_chars"] = len(final_diff)

    return final_diff, telemetry


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

# EPIC B Phase 3 P3: Module-level constant for JSON repair prompt
# Moved from _repair_json_with_llm() for better code organization (Gemini feedback)
_REPAIR_JSON_PROMPT = """You are a JSON repair assistant. The following JSON is malformed or truncated.
Please complete and fix it to be valid JSON. Output ONLY the repaired JSON, nothing else.

The JSON should have this structure:
{
  "quality_score": <integer 0-100>,
  "severity": "<none|low|medium|high|critical>",
  "summary": "<string>",
  "decision": "<approve|needs_changes|request_changes>",
  "comments": [{"file": "<path>", "line": <int or null>, "message": "<string>", "severity": "<string>"}]
}

Broken JSON:
"""


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

    def __init__(
        self,
        trace_id: str,
        risk_level: str = "medium",
        escalation_count: int = 0,
        retry_count: int = 0
    ):
        """
        Initialize LLM reviewer adapter

        Args:
            trace_id: Trace ID for logging
            risk_level: Risk level for routing decision ("high", "medium", "low")
            escalation_count: Number of tier escalations already performed (Issue #3640)
            retry_count: Number of retries already attempted (Issue #3640)
        """
        self.trace_id = trace_id
        self.llm_client = None
        try:
            # Use task-based routing via RoutingEngine instead of component-based
            # This ensures Routing Policy is respected, not bypassed by ExperimentManager
            self.llm_client = get_client_for_task(
                task_type=TaskType.REVIEW,
                risk_level=risk_level,
                escalation_count=escalation_count,
                retry_count=retry_count
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
        diff_files: Optional[list] = None,
        pr_title: Optional[str] = None,
        pr_description: Optional[str] = None,
        reference_context: Optional[str] = None
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
            pr_title: Pull request title (Issue #3767)
            pr_description: Pull request description/body (Issue #3767)
            reference_context: Issue #3223 Cross-file reference context (optional)

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
            return self._get_fallback_result(
                base_quality_score, base_severity, diff_files=diff_files
            )

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
                diff_files=diff_files,
                pr_title=pr_title,
                pr_description=pr_description,
                reference_context=reference_context
            )

            # Issue #4065 B-15: Filter low-confidence findings before publishing
            review_data = self._filter_by_confidence(review_data, pr_number)

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

            result = {
                "quality_score": final_score,
                "severity": final_severity,
                "summary": review_data.get("summary", ""),
                "decision": review_data.get("decision", "needs_changes"),
                "comments": review_data.get("comments", []),
                "llm_used": True,
                "provider": self.llm_client.provider_name,
                "review_time_ms": review_data.get("review_time_ms", 0),
                "diff_aware": has_diff,
                "multi_specialist_findings": None,
                "test_coverage_gaps": None,
                "dependency_issues": None,
            }

            result = self._run_enhanced_review_modules(
                result=result,
                diff=diff,
                diff_files=diff_files,
                pr_number=pr_number,
                goal=goal,
                repo=repo,
            )

            # EPIC B-13: Save review feedback to Memory v2 for learning
            # Observability: Log before calling to diagnose if this code path is reached
            logger.info(
                "[LLM Reviewer] B-13: About to save review feedback",
                extra={
                    "operation": "save_review_feedback_entry",
                    "trace_id": self.trace_id,
                    "pr_number": pr_number,
                    "repo": repo,
                    "has_result": result is not None,
                }
            )
            self._save_review_feedback(
                pr_number=pr_number,
                repo=repo,
                result=result,
                diff=diff,
                diff_files=diff_files,
            )

            return result

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
                base_quality_score, base_severity,
                fallback_reason="llm_json_parse_failed",
                diff_files=diff_files
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
                base_quality_score, base_severity,
                fallback_reason=fallback_reason,
                diff_files=diff_files
            )

    def _run_enhanced_review_modules(
        self,
        result: Dict[str, Any],
        diff: Optional[str],
        diff_files: Optional[list],
        pr_number: Optional[int],
        goal: str,
        repo: str,
    ) -> Dict[str, Any]:
        """
        Run EPIC B Phase 7-8 enhanced review modules (B-9, B-11, B-12).

        Blueprint Alignment:
        - Section 3.3 "Agent Separation Principle" - Reviewer can FLAG but NOT fix
        - All modules respect this principle: they identify issues but don't generate fixes

        Args:
            result: Base review result to enhance
            diff: PR diff content
            diff_files: List of changed files metadata
            pr_number: Pull request number
            goal: Original user goal/task description
            repo: GitHub repository (owner/repo format)

        Returns:
            Enhanced result dict with multi_specialist_findings, test_coverage_gaps,
            and dependency_issues fields populated based on feature flags.
        """
        pr_context = {
            "pr_number": pr_number,
            "goal": goal,
            "repo": repo,
        }

        file_list = None
        if diff_files:
            file_list = [
                f.get("filename", "") if isinstance(f, dict) else str(f)
                for f in diff_files
            ]

        if settings.use_multi_specialist_review and diff:
            try:
                logger.info(
                    "[LLM Reviewer] Running B-9 Multi-Specialist Review",
                    extra={
                        "operation": "multi_specialist_review",
                        "trace_id": self.trace_id,
                        "pr_number": pr_number,
                    }
                )
                specialist_findings = generate_multi_specialist_review(
                    diff_content=diff,
                    pr_context=pr_context,
                    trace_id=self.trace_id,
                )
                result["multi_specialist_findings"] = specialist_findings

                if specialist_findings and specialist_findings.get("finding_count", 0) > 0:
                    specialist_severity = specialist_findings.get("overall_severity", "none")
                    result["severity"] = combine_severity(
                        result["severity"], specialist_severity
                    )

                finding_count = specialist_findings.get("finding_count", 0) if specialist_findings else 0
                overall_severity = specialist_findings.get("overall_severity", "none") if specialist_findings else "none"
                logger.info(
                    "[LLM Reviewer] B-9 Multi-Specialist Review completed",
                    extra={
                        "operation": "multi_specialist_review",
                        "trace_id": self.trace_id,
                        "finding_count": finding_count,
                        "overall_severity": overall_severity,
                    }
                )
            except Exception as e:
                logger.warning(
                    "[LLM Reviewer] B-9 Multi-Specialist Review failed: %s",
                    e,
                    extra={
                        "operation": "multi_specialist_review",
                        "trace_id": self.trace_id,
                        "error": str(e),
                    }
                )

        if settings.use_test_coverage_flagging and diff:
            try:
                logger.info(
                    "[LLM Reviewer] Running B-11 Test Coverage Flagging",
                    extra={
                        "operation": "test_coverage_flagging",
                        "trace_id": self.trace_id,
                        "pr_number": pr_number,
                    }
                )
                coverage_gaps = analyze_test_coverage(
                    diff_content=diff,
                    diff_files=file_list,
                    trace_id=self.trace_id,
                )
                result["test_coverage_gaps"] = coverage_gaps

                gap_count = coverage_gaps.get("gap_count", 0) if coverage_gaps else 0
                logger.info(
                    "[LLM Reviewer] B-11 Test Coverage Flagging completed",
                    extra={
                        "operation": "test_coverage_flagging",
                        "trace_id": self.trace_id,
                        "gap_count": gap_count,
                    }
                )
            except Exception as e:
                logger.warning(
                    "[LLM Reviewer] B-11 Test Coverage Flagging failed: %s",
                    e,
                    extra={
                        "operation": "test_coverage_flagging",
                        "trace_id": self.trace_id,
                        "error": str(e),
                    }
                )

        if settings.use_dependency_analysis and diff:
            try:
                logger.info(
                    "[LLM Reviewer] Running B-12 Dependency Analysis",
                    extra={
                        "operation": "dependency_analysis",
                        "trace_id": self.trace_id,
                        "pr_number": pr_number,
                    }
                )
                dependency_issues = analyze_dependencies(
                    diff_content=diff,
                    diff_files=file_list,
                    trace_id=self.trace_id,
                )
                result["dependency_issues"] = dependency_issues

                if dependency_issues and dependency_issues.get("issue_count", 0) > 0:
                    for issue in dependency_issues.get("issues", []):
                        issue_severity = issue.get("severity", "low")
                        if issue_severity in ("high", "critical"):
                            result["severity"] = combine_severity(
                                result["severity"], issue_severity
                            )
                            break

                issue_count = dependency_issues.get("issue_count", 0) if dependency_issues else 0
                logger.info(
                    "[LLM Reviewer] B-12 Dependency Analysis completed",
                    extra={
                        "operation": "dependency_analysis",
                        "trace_id": self.trace_id,
                        "issue_count": issue_count,
                    }
                )
            except Exception as e:
                logger.warning(
                    "[LLM Reviewer] B-12 Dependency Analysis failed: %s",
                    e,
                    extra={
                        "operation": "dependency_analysis",
                        "trace_id": self.trace_id,
                        "error": str(e),
                    }
                )

        return result

    def _call_llm(
        self,
        pr_number: Optional[int],
        pr_url: Optional[str],
        ci_state: str,
        goal: str,
        repo: str,
        diff: Optional[str] = None,
        diff_truncated: bool = False,
        diff_files: Optional[list] = None,
        pr_title: Optional[str] = None,
        pr_description: Optional[str] = None,
        reference_context: Optional[str] = None
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
            pr_title: Pull request title (Issue #3767)
            pr_description: Pull request description/body (Issue #3767)
            reference_context: Issue #3223 Cross-file reference context (optional)

        Returns:
            Dict with review data and timing
        """
        use_json_mode = getattr(settings, 'reviewer_json_mode', True)
        has_diff = bool(diff and diff.strip())

        # EPIC B-14: Retrieve past review patterns for informed review
        pattern_context = None
        if has_diff and settings.enable_review_pattern_retrieval:
            try:
                feedback_loop = get_feedback_loop(trace_id=self.trace_id)
                # Use defensive access consistent with other parts of the codebase (lines 769, 1924-1927)
                file_paths = [
                    f.get("filename", "") if isinstance(f, dict) else str(f)
                    for f in (diff_files or [])
                ]
                pattern_data = feedback_loop.enhance_review_context(
                    diff_snippet=diff[:2000] if diff else "",
                    file_paths=file_paths if file_paths else None,
                )
                if pattern_data.get("has_patterns"):
                    pattern_context = pattern_data.get("context_text", "")
                    # Calculate actual average similarity for accurate telemetry
                    patterns = pattern_data.get("patterns", [])
                    avg_sim = (
                        sum(p.get("similarity", 0) for p in patterns) / len(patterns)
                        if patterns else 0
                    )
                    logger.info(
                        "[LLM Reviewer] B-14: Retrieved %d past patterns for review",
                        pattern_data.get("pattern_count", 0),
                        extra={
                            "operation": "pattern_retrieval",
                            "trace_id": self.trace_id,
                            "pr_number": pr_number,
                            "pattern_count": pattern_data.get("pattern_count", 0),
                            "avg_similarity": avg_sim,
                        }
                    )
            except Exception as e:
                logger.warning(
                    "[LLM Reviewer] B-14: Pattern retrieval failed: %s",
                    type(e).__name__,
                    extra={
                        "operation": "pattern_retrieval",
                        "trace_id": self.trace_id,
                        "pr_number": pr_number,
                        "error": type(e).__name__,
                    }
                )

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
                diff_files=diff_files,
                pr_title=pr_title,
                pr_description=pr_description,
                pattern_context=pattern_context,
                reference_context=reference_context,
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

        # P1 瘦身計畫 (#3197): Log prompt bytes for resource profiling
        system_prompt_bytes = len(system_prompt.encode('utf-8'))
        user_prompt_bytes = len(user_prompt.encode('utf-8'))
        total_prompt_bytes = system_prompt_bytes + user_prompt_bytes
        log_prompt_build_bytes(
            trace_id=self.trace_id,
            prompt_bytes=total_prompt_bytes,
            system_prompt_bytes=system_prompt_bytes,
            user_prompt_bytes=user_prompt_bytes,
            diff_included=has_diff
        )

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

            # P1 瘦身計畫 (#3197): Log LLM response bytes for resource profiling
            response_bytes = len(content.encode('utf-8')) if content else 0
            token_count = None
            if response.usage:
                token_count = response.usage.get('completion_tokens') or response.usage.get('output_tokens')
            log_llm_response_bytes(
                trace_id=self.trace_id,
                response_bytes=response_bytes,
                token_count=token_count,
                provider=response.provider,
                model=response.model
            )

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

        Major Brain Upgrade (2025-12):
        - Tactic 1 (Quote-First CoT): Force LLM to quote code before giving line number
        - Senior Architect Persona: Prohibit nitpicks, focus on logic/architecture
        - Contract Awareness: Timestamp/API schema change validation
        - Strict Mode: Only allow inline comments on + (addition) lines

        B-9.5 Enhancement (2026-01, Issue #3881):
        - Multi-Line Statement Awareness: Prevent false positives on multi-line function calls
        - Require LLM to see complete statement before claiming arguments are missing

        Returns:
            System prompt string for LLM
        """
        return """You are a SENIOR SOFTWARE ARCHITECT performing code review for a pull request.
You will be shown the actual code diff for this PR with line numbers annotated.

=== SCOPE RESTRICTION (CRITICAL - Issue #3765) ===
You may ONLY comment on files that are explicitly shown in the diff below.
- NEVER comment on files that are not in the diff
- NEVER reference files from your training data or memory
- If a file path is not visible in the diff, you CANNOT comment on it
- The "ALLOWED FILES" list in the user prompt defines your ENTIRE scope

Violation of this rule will cause your comments to be rejected by the validation system.

=== ROLE SEPARATION: REVIEWER ≠ LINTER (Issue #3766) ===
You are a CODE REVIEWER, NOT a LINTER. This distinction is CRITICAL.

**LINTER's Job (NOT yours - handled by CI pipeline):**
- Indentation, formatting, whitespace issues
- Naming conventions (camelCase vs snake_case)
- Missing semicolons, trailing commas
- Import ordering
- Line length violations
- ESLint/Flake8/Prettier detectable issues
- React Hooks dependency arrays (eslint-plugin-react-hooks)
- Accessibility warnings (eslint-plugin-jsx-a11y)

**YOUR Job (High-Value Reviewer Focus):**
- Logical Bugs: Race conditions, off-by-one errors, null pointer risks
- Security Vulnerabilities: Injection, XSS, auth bypass, secret exposure
- Performance Issues: N+1 queries, memory leaks, unnecessary re-renders
- Edge Cases: Boundary conditions, error handling, timeout scenarios
- Architecture Concerns: Coupling, abstraction leaks, contract violations

DO NOT comment on issues that ESLint, Flake8, Prettier, or any linter can detect.
If CI has a linter configured, assume it will catch style issues - focus on what it CANNOT catch.

=== PERSONA: SENIOR ARCHITECT (NOT INTERN) ===
You are a seasoned architect who focuses on IMPACT, not style.
- You DO NOT comment on formatting, naming conventions, or cosmetic issues
- You DO NOT nitpick about code style unless it causes bugs or security issues
- You FOCUS on: logic errors, security vulnerabilities, performance problems, API contract changes
- Every comment you make must have REAL IMPACT on code quality or system stability

=== ROBUSTNESS & MAINTAINABILITY (Senior Architect Scope) ===
While you ignore style, you MUST flag code that is:
- **Brittle**: Prone to edge-case failures (e.g., greedy regex like `.*` that may over-match)
- **Hard to maintain**: Complex logic without clear structure, magic numbers, or hidden dependencies
- **Fragile to change**: Code that will break easily when requirements evolve

These are NOT style nitpicks - they are architectural concerns that impact system reliability.

=== PR CONTEXT AWARENESS (Issue #3767) ===
You will receive the PR Title and Description in the user prompt. Use this context to:
1. **Understand Intent**: What is the PR trying to achieve? What problem does it solve?
2. **Validate Alignment**: Do the code changes actually accomplish the stated goal?
3. **Goal-Oriented Feedback**: Provide feedback relevant to the PR's purpose, not generic observations
4. **Flag Misalignment**: If code changes don't match the PR description, flag this as a concern

Example: If PR title says "Add rate limiting" but code only adds logging, flag the discrepancy.
Do NOT provide generic feedback that ignores the PR's stated purpose.

=== REVIEW METHODOLOGY: QUOTE-FIRST (Chain of Thought) ===
For EVERY issue you find, you MUST follow this process:
1. QUOTE: First, find the problematic code and copy it exactly as shown in the diff
2. LOCATE: Look at the "(Line N)" annotation in the diff to get the exact line number
3. ANALYZE: Explain why this is a problem and what the impact is
4. SUGGEST: Provide a concrete fix or improvement

If you cannot quote the exact code from the diff, DO NOT provide a line number.
Put the comment in the review body instead (omit start_line/end_line fields).

=== MULTI-LINE STATEMENT AWARENESS (Issue #3881) ===
When analyzing function calls, class definitions, or any statements that span multiple lines:

1. **ALWAYS look at the COMPLETE statement** - from opening parenthesis/bracket to closing
2. **DO NOT conclude arguments are missing** based on seeing only the first line
3. **Multi-line function calls are common** - look for continuation lines before making claims

**INCORRECT analysis (causes false positives):**
```
Seeing only: `result = analyze_test_coverage(`
Concluding: "analyze_test_coverage() is missing required arguments" <- WRONG
```

**CORRECT analysis:**
```
Seeing the complete call:
  result = analyze_test_coverage(
      diff_content=diff_content,
      diff_files=diff_files,
      trace_id=trace_id
  )
Concluding: "analyze_test_coverage() receives all required arguments" <- CORRECT
```

**Before claiming a function/list/dict is missing elements:**
1. Find the opening delimiter (`(`, `[`, or `{`)
2. Scan forward to find the matching closing delimiter (`)`, `]`, or `}`)
3. List ALL elements between them
4. ONLY THEN determine if any are missing

If you cannot see the complete statement in the diff, DO NOT comment on missing elements.

=== STRICT MODE: ONLY COMMENT ON + LINES ===
You may ONLY provide inline comments (with line numbers) on lines marked with "+".
These are NEW or MODIFIED lines that are part of THIS PR's changes.

FORBIDDEN targets for inline comments:
- Lines marked with "-" (deletions) - these no longer exist
- Lines marked with " " (context) - these are unchanged, not this PR's responsibility
- Lines outside the visible diff - you cannot see them

If you see an issue in a context line (" "), that's "technical debt" from before this PR.
Mention it in the summary or as a file-level comment, but DO NOT attach a line number.

=== CONTRACT CHANGE CHECKLIST ===
When you see changes to ANY of these, you MUST check and comment:

1. **Structured Output Fields** (JSON keys, log fields, API responses, diagnostic fields):
   - Is there a version bump (e.g., DIAGNOSTIC_VERSION, API_VERSION)?
   - Are all consumers/docs/runbooks updated?
   - Is there backward compatibility or fallback behavior?

2. **Timestamp Fields** (_ts, timestamp, created_at, updated_at):
   - What is the unit? (seconds vs milliseconds vs microseconds)
   - Is it UTC epoch? (cross-service correlation requires UTC)
   - Is precision sufficient for log correlation? (usually need milliseconds)
   - Is the unit documented in docstring/comments?

3. **Event Names / Telemetry Keys**:
   - Will this break existing dashboards or alerts?
   - Is the naming consistent with existing events?

=== STATE MACHINE / ORCHESTRATOR SAFETY CHECKLIST ===
When reviewing changes to state machines, orchestrators, or graph-based workflows:

1. **One-Shot Flag Consumption** (CRITICAL - Issue #3541):
   - If a flag triggers special behavior (e.g., `ci_failure_trigger`), is there a "consumed" flag?
   - Is the consumed flag set on FIRST pass to prevent re-triggering?
   - Example pattern: `if trigger and not consumed: consumed = True; do_action()`

2. **Edge/Router Safety**:
   - Do new edges create potential cycles?
   - Is there a bounded retry/loop limit?
   - Are terminal conditions reachable from all paths?

3. **State Flag Preservation**:
   - Are routing flags preserved through node transitions?
   - Could a node accidentally clear a flag needed downstream?

4. **Infinite Loop Detection**:
   - If node A routes to B routes to C routes back to A, what breaks the cycle?
   - Is there a max_steps or max_iterations guard?

Flag these as CRITICAL severity if the code could cause infinite loops.

=== NOISE BUDGET: QUALITY OVER QUANTITY ===
- Maximum 5 comments per review (focus on the most important issues)
- Every comment MUST include:
  - IMPACT: Why does this matter? What could go wrong?
  - SUGGESTED FIX: Concrete code or approach to fix it
- If you have no high-impact issues to report, say so in the summary
- DO NOT pad the review with low-value suggestions

=== ACTIONABLE SUGGESTIONS REQUIRED (Issue #3768) ===
When pointing out an issue, you MUST provide a concrete code fix, not just criticism.

**BAD (criticism without solution):**
"This function doesn't handle null values" - unhelpful, leaves developer guessing

**GOOD (actionable with code snippet):**
"This function doesn't handle null values. Suggested fix:
```python
def process(value):
    if value is None:
        return default_value
    return transform(value)
```"

Rules for actionable suggestions:
1. Every criticism MUST include a code snippet showing the fix
2. The code snippet should be copy-paste ready (not pseudocode)
3. If you cannot provide a specific code snippet, explain the recommended approach in detail within the `message` field after the IMPACT statement
4. The code snippet for the fix MUST be placed in the `suggested_fix` field

Comments without actionable suggestions will be considered low-value and should be omitted.

=== LINE NUMBER FORMAT ===
The diff is annotated with explicit line numbers in this format:
  + (Line 50) print("hello")    <- Addition at line 50 (VALID target)
  - (Line 49) print("old")      <- Deletion (INVALID target)
    (Line 51) existing_code()   <- Context (INVALID target for inline)

Simply COPY the number from "(Line N)" - do not calculate it yourself.
If you cannot see "(Line N)" for a piece of code, omit line fields entirely.

=== OUTPUT FORMAT (strict JSON) ===
{
  "summary": "Brief summary focusing on architecture/logic issues found (or 'No significant issues')",
  "quality_score": 0-100,
  "severity": "none" | "low" | "medium" | "high" | "critical",
  "decision": "approve" | "needs_changes" | "block",
  "comments": [
    {
      "severity": "suggestion" | "warning" | "error",
      "category": "bug" | "performance" | "security" | "maintainability" | "contract" | "other",
      "confidence": 0.0-1.0,
      "file": "path/to/file.py",
      "start_line": 50,
      "end_line": 50,
      "quote": "the exact code you're commenting on",
      "message": "IMPACT: [why this matters].",
      "suggested_fix": "```python\n# Copy-paste ready code fix\ndef fixed_function():\n    pass\n```"
    }
  ]
}

IMPORTANT:
- "nit" severity is REMOVED - do not use it
- "style" category is REMOVED - do not use it
- "contract" category is NEW - use for API/schema/timestamp changes
- "quote" field is NEW - include the code snippet you're referencing
- "suggested_fix" field is REQUIRED (Issue #3768) - include copy-paste ready code
- "confidence" field is NEW (Issue #4065) - your confidence in this finding (0.0-1.0)
  - 0.9-1.0: Certain - clear bug, security issue, or contract violation
  - 0.7-0.9: High confidence - likely issue based on code analysis
  - 0.5-0.7: Medium confidence - potential issue, may need context
  - 0.0-0.5: Low confidence - uncertain, speculative, or stylistic
- Only use start_line/end_line for "+" lines you can see in the diff

=== SCORING GUIDELINES ===
- Clean code, good practices, CI passed: quality_score 85-95
- Minor logic issues, missing edge cases: quality_score 70-85
- Contract changes without version bump: quality_score 50-70
- Security issues or data integrity risks: quality_score 30-50
- Critical bugs requiring immediate attention: quality_score 0-30
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
        diff_files: Optional[list],
        pr_title: Optional[str] = None,
        pr_description: Optional[str] = None,
        pattern_context: Optional[str] = None,
        reference_context: Optional[str] = None
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
            pr_title: Pull request title (Issue #3767)
            pr_description: Pull request description/body (Issue #3767)
            pattern_context: B-14 Pattern Retrieval context from past reviews (optional)
            reference_context: Issue #3223 Cross-file reference context (optional)

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

        # Tactic 3 (Line Number Mapping): Annotate diff with explicit line numbers
        # This allows LLM to "copy" line numbers instead of calculating them
        annotated_diff = annotate_diff_with_line_numbers(sanitized_diff)

        # Issue #3080: Truncation safeguard for token budget
        # Preserve + lines (Strict Mode requirement), sacrifice context lines first
        max_diff_chars = settings.llm_review_max_diff_chars
        truncated_diff, truncation_telemetry = truncate_diff_for_token_budget(
            annotated_diff, max_chars=max_diff_chars
        )

        # Issue #3790: Sanitize diff content to prevent prompt injection attacks
        # Diff is user-controllable (attackers can craft malicious diffs with injection payloads)
        # Apply same sanitization as other user-controlled inputs (goal, pr_title, pr_description)
        truncated_diff = self._sanitize_prompt_input(truncated_diff)

        # Log truncation telemetry (WARNING level for visibility per Blueprint Telemetry v2)
        if truncation_telemetry["was_truncated"]:
            logger.warning(
                f"[LLM Reviewer] Diff truncated for PR #{pr_number}: "
                f"{truncation_telemetry['original_chars']} -> {truncation_telemetry['truncated_chars']} chars "
                f"(context_lines_dropped={truncation_telemetry['context_lines_dropped']}, "
                f"hunks_dropped={truncation_telemetry['hunks_dropped']}, "
                f"files_dropped={truncation_telemetry['files_dropped']})",
                extra={
                    "operation": "truncate_diff_for_token_budget",
                    "pr_number": pr_number,
                    "diff_truncated_by_budget": True,
                    **truncation_telemetry
                }
            )
            # Mark diff as truncated for downstream handling
            diff_truncated = True
        else:
            logger.debug(
                f"[LLM Reviewer] Annotated diff with line numbers for PR #{pr_number}",
                extra={
                    "operation": "build_diff_aware_prompt",
                    "pr_number": pr_number,
                    "original_length": len(sanitized_diff),
                    "annotated_length": len(annotated_diff),
                    "truncated_length": len(truncated_diff),
                    "diff_truncated_by_budget": False
                }
            )

        # Build file summary if available
        # Issue #3765: Build explicit ALLOWED FILES list for scope enforcement
        file_summary = ""
        allowed_files_section = ""
        if diff_files:
            file_list = []
            allowed_file_names = []
            for f in diff_files[:10]:  # Limit to first 10 files
                file_list.append(
                    f"  - {f['filename']} (+{f['additions']}/-{f['deletions']})"
                )
                allowed_file_names.append(f['filename'])
            file_summary = "\n**Changed Files:**\n" + "\n".join(file_list)
            if len(diff_files) > 10:
                file_summary += f"\n  ... and {len(diff_files) - 10} more files"
                # Add remaining file names to allowed list
                for f in diff_files[10:]:
                    allowed_file_names.append(f['filename'])

            # Issue #3765: Explicit ALLOWED FILES section for scope enforcement
            # Sanitize filenames to prevent prompt injection (gemini-code-assist review)
            def sanitize_filename(fn: str) -> str:
                """Escape backticks and newlines to prevent prompt injection."""
                return fn.replace('`', '').replace('\n', ' ').replace('\r', ' ')

            allowed_files_section = (
                "\n\n**ALLOWED FILES (Issue #3765 - Scope Enforcement):**\n"
                "You may ONLY comment on these files. Any comment on a file not in this list will be REJECTED.\n"
                + "\n".join(f"  - `{sanitize_filename(fn)}`" for fn in allowed_file_names)
            )

        # Build truncation warning if applicable (enhanced for #3080)
        truncation_warning = ""
        if diff_truncated:
            warning_parts = ["**Note:** The diff has been truncated due to size limits."]
            if truncation_telemetry["was_truncated"]:
                if truncation_telemetry["files_dropped"] > 0:
                    warning_parts.append(
                        f"{truncation_telemetry['files_dropped']} file(s) not shown."
                    )
                if truncation_telemetry["hunks_dropped"] > 0:
                    warning_parts.append(
                        f"{truncation_telemetry['hunks_dropped']} hunk(s) not shown."
                    )
                if truncation_telemetry["context_lines_dropped"] > 0:
                    warning_parts.append(
                        f"{truncation_telemetry['context_lines_dropped']} context line(s) removed."
                    )
                warning_parts.append(
                    "Focus your review on the visible + lines. "
                    "Do NOT claim 'no issues found' based on this partial view."
                )
            truncation_warning = "\n\n" + " ".join(warning_parts)

        # Issue #3780: Sanitize externally-sourced inputs to prevent prompt injection
        # (supersedes #3774 which only sanitized goal)
        sanitized_repo = self._sanitize_prompt_input(repo)
        sanitized_pr_url = self._sanitize_prompt_input(pr_url or "")
        sanitized_goal = self._sanitize_prompt_input(goal)

        # Issue #3767: Build PR context section for context-aware review
        # Issue #3783: Sanitize pr_title and pr_description to prevent prompt injection
        pr_context_section = ""
        if pr_title or pr_description:
            sanitized_pr_title = self._sanitize_prompt_input(pr_title or "")
            sanitized_pr_description = self._sanitize_prompt_input(pr_description or "")
            pr_context_section = "\n**PR Context (Issue #3767):**"
            if sanitized_pr_title:
                pr_context_section += f"\n- Title: {sanitized_pr_title}"
            if sanitized_pr_description:
                # Issue #3775: Use constant for truncation limit
                desc_preview = sanitized_pr_description[:MAX_PR_DESCRIPTION_CHARS]
                if len(sanitized_pr_description) > MAX_PR_DESCRIPTION_CHARS:
                    desc_preview += "... (truncated)"
                pr_context_section += f"\n- Description: {desc_preview}"
            pr_context_section += "\n"

        # EPIC B-14: Build past patterns section for informed review
        # Pattern context is pre-formatted by enhance_review_context()
        # Apply sanitization for defense-in-depth (Issue #3780 pattern)
        pattern_section = ""
        if pattern_context:
            sanitized_pattern_context = self._sanitize_prompt_input(pattern_context)
            pattern_section = f"\n{sanitized_pattern_context}\n"

        # Issue #3223: Build cross-file reference context section
        # Reference context is pre-formatted by format_reference_context_for_prompt()
        # This provides context from imported/referenced files to reduce false positives
        reference_section = ""
        if reference_context:
            sanitized_reference_context = self._sanitize_prompt_input(reference_context)
            reference_section = f"\n{sanitized_reference_context}\n"

        return f"""**Pull Request Information**
- Repository: {sanitized_repo}
- PR Number: {pr_number or "Unknown"}
- PR URL: {sanitized_pr_url or "Not available"}
- CI Status: {ci_state}
{file_summary}{allowed_files_section}{pr_context_section}{pattern_section}{reference_section}
**Task Goal/Description:**
{sanitized_goal}
{truncation_warning}

**Code Diff (with line numbers annotated):**
```diff
{truncated_diff}
```

Please review the code changes above and provide your assessment as JSON.
Remember: Only comment on lines marked with "+" (additions). Copy line numbers from "(Line N)" annotations.
CRITICAL: Only comment on files listed in ALLOWED FILES above. Comments on other files will be rejected.
IMPORTANT: Consider the PR Title and Description when reviewing - validate if the code changes align with the stated intent."""

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
        # Issue #3780: Sanitize externally-sourced inputs to prevent prompt injection
        # (supersedes #3774 which only sanitized goal)
        sanitized_repo = self._sanitize_prompt_input(repo)
        sanitized_pr_url = self._sanitize_prompt_input(pr_url or "")
        sanitized_goal = self._sanitize_prompt_input(goal)

        return f"""**Pull Request Information**
- Repository: {sanitized_repo}
- PR Number: {pr_number or "Unknown"}
- PR URL: {sanitized_pr_url or "Not available"}
- CI Status: {ci_state}

**Task Goal/Description**:
{sanitized_goal}

Based on this information, provide your code review assessment as JSON.
Remember: You cannot see the actual code changes, so focus on risk assessment based on CI status and task complexity."""

    def _parse_json_with_retry(self, content: str, use_json_mode: bool) -> Dict[str, Any]:
        """
        Parse JSON with three-stage retry and repair logic.

        EPIC B Phase 3 P3: Three-stage JSON repair pipeline:
        1. Direct parse - Try json.loads() on raw content
        2. String cleaning - Remove markdown blocks, extract JSON object
        3. LLM repair - Use LLM to fix truncated/malformed JSON (if enabled via settings)

        The LLM repair stage is controlled by settings.enable_llm_json_repair (default: False).
        To enable: set ENABLE_LLM_JSON_REPAIR=true in environment.

        Args:
            content: Raw LLM response
            use_json_mode: Whether JSON mode was used (affects logging only)

        Returns:
            Parsed review dict

        Raises:
            json.JSONDecodeError: If parsing fails after all repair attempts
        """
        # First attempt: direct parse
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.warning(f"[LLM Reviewer] First parse attempt failed: {e}, attempting regex repair")

        # Second attempt: regex-based cleaning
        try:
            cleaned_content = self._clean_json_response(content)
            logger.info(f"[LLM Reviewer] Cleaned content for trace_id={self.trace_id}")
            return json.loads(cleaned_content)
        except json.JSONDecodeError as e2:
            logger.warning(f"[LLM Reviewer] Regex repair failed: {e2}, attempting LLM repair")

        # Third attempt: LLM-based repair (EPIC B Phase 3 P3)
        # Only attempt if feature is enabled and we have a client
        # Enable via settings.enable_llm_json_repair = True after testing
        if settings.enable_llm_json_repair and self.llm_client:
            try:
                repaired_json = self._repair_json_with_llm(content)
                if repaired_json:
                    return json.loads(repaired_json)
            except json.JSONDecodeError as e3:
                logger.error(f"[LLM Reviewer] LLM repair also failed: {e3}")
            except Exception as repair_error:
                logger.warning(f"[LLM Reviewer] LLM repair error: {repair_error}")

        # All repair attempts failed
        logger.error("[LLM Reviewer] Failed to parse JSON after all repair attempts")
        raise json.JSONDecodeError("All JSON repair attempts failed", content, 0)

    def _repair_json_with_llm(self, broken_json: str) -> Optional[str]:
        """
        Use LLM to repair truncated or malformed JSON.

        Args:
            broken_json: The malformed JSON string

        Returns:
            Repaired JSON string, or None if repair fails
        """
        # Truncate broken JSON to avoid token limits (keep first 2000 chars)
        # Python slicing handles out-of-bounds gracefully (Gemini feedback)
        truncated_input = broken_json[:2000]

        # Prompt injection protection: sanitize input to prevent malicious content
        # from hijacking the repair prompt (MorningAI Code Review feedback)
        sanitized_input = self._sanitize_json_input(truncated_input)

        try:
            start_time = time.time()
            response = self.llm_client.chat(
                messages=[
                    {"role": "system", "content": "You are a JSON repair assistant. Output only valid JSON."},
                    {"role": "user", "content": _REPAIR_JSON_PROMPT + sanitized_input}
                ],
                temperature=0.0,  # Deterministic for repair
                max_tokens=settings.llm_json_repair_max_tokens
            )
            repair_time_ms = (time.time() - start_time) * 1000

            repaired = response.content if hasattr(response, 'content') else str(response)
            repaired = self._clean_json_response(repaired)

            logger.info(
                "[LLM Reviewer] JSON repair attempted",
                extra={
                    "operation": "llm_json_repair",
                    "trace_id": self.trace_id,
                    "repair_time_ms": repair_time_ms,
                    "input_length": len(truncated_input),
                    "output_length": len(repaired)
                }
            )

            return repaired

        except Exception as e:
            logger.warning(
                f"[LLM Reviewer] JSON repair LLM call failed: {e}",
                extra={
                    "operation": "llm_json_repair",
                    "trace_id": self.trace_id,
                    "error": str(e)
                }
            )
            return None

    def _sanitize_json_input(self, content: str) -> str:
        """
        Sanitize JSON input to prevent prompt injection attacks.

        EPIC B Phase 3: Prompt injection protection (MorningAI Code Review feedback)
        Removes or escapes potentially malicious content that could hijack the repair prompt.

        Uses pre-compiled regex patterns from PROMPT_INJECTION_PATTERNS for performance.
        Patterns include common instruction overrides, role manipulation attempts,
        and model-specific control tokens (Llama [INST], Mistral <<SYS>>, ChatML <|im_start|>).

        Args:
            content: Raw broken JSON string

        Returns:
            Sanitized JSON string safe for LLM input
        """
        if not content:
            return content

        sanitized = content
        for pattern in PROMPT_INJECTION_PATTERNS:
            sanitized = pattern.sub('[SANITIZED]', sanitized)

        return sanitized

    def _sanitize_prompt_input(self, content: str) -> str:
        """
        Sanitize user-controlled input to prevent prompt injection attacks.

        Issue #3780: Externally-sourced variables (repo, pr_url, goal) are directly
        embedded into LLM prompts. This method sanitizes them to prevent prompt injection.

        Uses pre-compiled regex patterns from PROMPT_INJECTION_PATTERNS for performance.
        Patterns include common instruction overrides, role manipulation attempts,
        and model-specific control tokens (Llama [INST], Mistral <<SYS>>, ChatML <|im_start|>).

        Args:
            content: User-controlled input string (e.g., goal, repo, pr_url)

        Returns:
            Sanitized string safe for embedding in LLM prompts
        """
        if not content:
            return content

        sanitized = content
        for pattern in PROMPT_INJECTION_PATTERNS:
            sanitized = pattern.sub('[SANITIZED]', sanitized)

        return sanitized

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

    def _filter_by_confidence(
        self,
        review_data: Dict[str, Any],
        pr_number: Optional[int]
    ) -> Dict[str, Any]:
        """
        Filter low-confidence findings before publishing.

        Issue #4065 B-15: Confidence Scoring for review findings.
        Findings with confidence < threshold are filtered out to reduce false positives.

        Args:
            review_data: Review data from LLM containing comments
            pr_number: Pull request number for logging

        Returns:
            Review data with low-confidence comments filtered out
        """
        threshold = settings.review_confidence_threshold
        comments = review_data.get("comments", [])

        if not comments:
            return review_data

        original_count = len(comments)
        filtered_comments = []
        filtered_out = []

        for comment in comments:
            confidence = comment.get("confidence")
            if confidence is None:
                confidence = 0.8
                comment["confidence"] = confidence

            if confidence >= threshold:
                filtered_comments.append(comment)
            else:
                filtered_out.append({
                    "confidence": confidence,
                    "category": comment.get("category", "unknown"),
                    "severity": comment.get("severity", "unknown"),
                })

        filtered_count = original_count - len(filtered_comments)

        if filtered_count > 0:
            logger.info(
                f"[LLM Reviewer] B-15: Filtered {filtered_count}/{original_count} "
                f"low-confidence findings (threshold={threshold})",
                extra={
                    "operation": "confidence_filter",
                    "trace_id": self.trace_id,
                    "pr_number": pr_number,
                    "original_count": original_count,
                    "filtered_count": filtered_count,
                    "remaining_count": len(filtered_comments),
                    "threshold": threshold,
                    "filtered_details": filtered_out,
                }
            )
        else:
            logger.debug(
                f"[LLM Reviewer] B-15: All {original_count} findings passed "
                f"confidence threshold ({threshold})",
                extra={
                    "operation": "confidence_filter",
                    "trace_id": self.trace_id,
                    "pr_number": pr_number,
                    "original_count": original_count,
                    "threshold": threshold,
                }
            )

        review_data["comments"] = filtered_comments
        review_data["confidence_filter_stats"] = {
            "original_count": original_count,
            "filtered_count": filtered_count,
            "remaining_count": len(filtered_comments),
            "threshold": threshold,
        }

        return review_data

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

    def _save_review_feedback(
        self,
        pr_number: Optional[int],
        repo: str,
        result: Dict[str, Any],
        diff: Optional[str],
        diff_files: Optional[list],
    ) -> None:
        """
        Save review feedback to Memory v2 for learning.

        EPIC B Phase B-13: Real-time Feedback Loop
        Blueprint: Reviewer feedback stored in Memory v2 for accumulated experience.

        This method is called after a successful review to store the outcome
        in the Knowledge Base for future pattern matching.

        Args:
            pr_number: Pull request number
            repo: Repository name (owner/repo format)
            result: Review result dictionary
            diff: PR diff content
            diff_files: List of changed files metadata
        """
        # Observability: Log pr_number value in message (not just extra) for diagnosis
        # Issue: extra fields may not appear in log output depending on configuration
        if pr_number is None:
            logger.info(
                "[LLM Reviewer] B-13: pr_number is None, skipping feedback save",
                extra={
                    "operation": "save_review_feedback_skipped",
                    "trace_id": self.trace_id,
                    "repo": repo,
                    "reason": "pr_number_is_none",
                }
            )
            return

        try:
            # Observability: Log before creating feedback loop instance
            logger.info(
                "[LLM Reviewer] B-13: Creating feedback loop for PR #%d",
                pr_number,
                extra={
                    "operation": "save_review_feedback_init",
                    "trace_id": self.trace_id,
                    "pr_number": pr_number,
                    "repo": repo,
                }
            )
            feedback_loop = get_feedback_loop(trace_id=self.trace_id)
            if not feedback_loop.is_enabled:
                # Include feature flag values in message (not just extra) for diagnosis
                logger.info(
                    "[LLM Reviewer] B-13 Feedback Loop disabled for PR #%d "
                    "(ENABLE_MEMORY_V2=%s, ENABLE_REVIEW_FEEDBACK_LOOP=%s)",
                    pr_number,
                    settings.enable_memory_v2,
                    settings.enable_review_feedback_loop,
                    extra={
                        "operation": "save_review_feedback_skipped",
                        "trace_id": self.trace_id,
                        "pr_number": pr_number,
                        "repo": repo,
                        "reason": "feedback_loop_disabled",
                        "enable_memory_v2": settings.enable_memory_v2,
                        "enable_review_feedback_loop": settings.enable_review_feedback_loop,
                    }
                )
                return

            file_paths = []
            if diff_files:
                for file_info in diff_files:
                    if isinstance(file_info, dict):
                        file_paths.append(file_info.get("filename", ""))
                    else:
                        file_paths.append(str(file_info))

            # Map decision to verdict using dict lookup (Gemini suggestion)
            verdict_map = {
                "approve": "approve",
                "needs_changes": "request_changes",
                "block": "blocked",
            }
            verdict = verdict_map.get(result.get("decision", "unknown"), "comment")

            comments = result.get("comments", [])
            blocker_count = sum(
                1 for c in comments
                if c.get("severity", "").lower() in ("high", "critical")
            )

            feedback_loop.save_feedback(
                pr_number=pr_number,
                repo=repo,
                verdict=verdict,
                severity=result.get("severity", "low"),
                summary=result.get("summary", ""),
                review_comments=comments,
                file_paths=file_paths,
                diff_snippet=diff[:2000] if diff else None,
                blocker_count=blocker_count,
            )

        except Exception as e:
            logger.warning(
                "[LLM Reviewer] Failed to save review feedback: %s",
                e,
                extra={
                    "operation": "save_review_feedback",
                    "trace_id": self.trace_id,
                    "pr_number": pr_number,
                    "repo": repo,
                }
            )

    def _get_fallback_result(
        self,
        base_quality_score: int,
        base_severity: str,
        fallback_reason: str = "llm_unavailable",
        diff_files: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Get fallback result when LLM review fails

        Args:
            base_quality_score: Base quality score from CI-only review
            base_severity: Base severity from CI-only review
            fallback_reason: Reason for fallback (llm_unavailable, llm_json_parse_failed,
                           llm_timeout, llm_connection_error, llm_api_error)
            diff_files: List of changed files metadata for risk assessment

        Returns:
            Dict with fallback review results including fallback_reason

        Safety Net (P1): When LLM fails on high-risk files, escalate severity
        to ensure human review. This prevents silent approval of critical changes.
        """
        final_severity = base_severity
        escalation_reason = None

        orchestrator_path_prefixes = [
            "handoff/20250928/40_app/orchestrator/",
            "orchestrator/",
        ]

        high_risk_exact_files = [
            "langgraph_orchestrator.py",
            "langgraph_orchestrator",
        ]

        high_risk_orchestrator_patterns = [
            "/routing/",
            "/router",
            "router.py",
            "_trigger",
            "ci_monitor",
            "conditional_edge",
            "state_machine",
            "add_edge",
            "graph_builder",
        ]

        if diff_files:
            high_risk_files = []
            for file_info in diff_files:
                filename = file_info.get("filename", "") if isinstance(file_info, dict) else str(file_info)
                filename_lower = filename.lower()

                for exact_file in high_risk_exact_files:
                    if filename_lower.endswith(exact_file):
                        high_risk_files.append(filename)
                        break
                else:
                    is_orchestrator_file = any(
                        prefix in filename_lower for prefix in orchestrator_path_prefixes
                    )
                    if is_orchestrator_file:
                        for pattern in high_risk_orchestrator_patterns:
                            if pattern in filename_lower:
                                high_risk_files.append(filename)
                                break

            if high_risk_files:
                if base_severity in ("none", "low"):
                    final_severity = "high"
                    escalation_reason = (
                        f"LLM review failed on high-risk files: {', '.join(high_risk_files[:3])}. "
                        "Escalating severity for human review."
                    )
                    logger.warning(
                        f"[LLM Reviewer] Fail-closed escalation: {escalation_reason}",
                        extra={
                            "operation": "llm_reviewer_fallback",
                            "trace_id": self.trace_id,
                            "high_risk_files": high_risk_files,
                            "original_severity": base_severity,
                            "escalated_severity": final_severity,
                            "fallback_reason": fallback_reason
                        }
                    )

        if final_severity == "none":
            decision = "approve"
        else:
            decision = "needs_changes"

        reason_summaries = {
            "llm_unavailable": "LLM review unavailable, using CI-based assessment",
            "llm_json_parse_failed": "LLM response parsing failed, using CI-based assessment",
            "llm_timeout": "LLM request timed out, using CI-based assessment",
            "llm_connection_error": "LLM connection failed, using CI-based assessment",
            "llm_api_error": "LLM API error occurred, using CI-based assessment"
        }
        summary = reason_summaries.get(fallback_reason, reason_summaries["llm_unavailable"])

        if escalation_reason:
            summary = f"{summary}. {escalation_reason}"

        return {
            "quality_score": base_quality_score,
            "severity": final_severity,
            "summary": summary,
            "decision": decision,
            "comments": [],
            "llm_used": False,
            "provider": None,
            "review_time_ms": 0,
            "diff_aware": False,
            "fallback_reason": fallback_reason,
            "multi_specialist_findings": None,
            "test_coverage_gaps": None,
            "dependency_issues": None,
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
    diff_files: Optional[list] = None,
    escalation_count: int = 0,
    retry_count: int = 0,
    pr_title: Optional[str] = None,
    pr_description: Optional[str] = None,
    reference_context: Optional[str] = None
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
        escalation_count: Number of tier escalations already performed (Issue #3640)
        retry_count: Number of retries already attempted (Issue #3640)
        pr_title: Pull request title (Issue #3767)
        pr_description: Pull request description/body (Issue #3767)
        reference_context: Issue #3223 Cross-file reference context (optional)

    Returns:
        Dict with review results
    """
    adapter = LLMReviewerAdapter(
        trace_id=trace_id,
        escalation_count=escalation_count,
        retry_count=retry_count
    )
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
        diff_files=diff_files,
        pr_title=pr_title,
        pr_description=pr_description,
        reference_context=reference_context
    )
