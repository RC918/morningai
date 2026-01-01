"""
Auto-fix Gate - Three Don'ts Principle #2: Side-effect Gate

Issue #3211: D-1.1 Coder Three Don'ts Safety Guardrails
CTO Approved: 2025-12-29

This module implements the Router-level gate for auto-fix eligibility.
The gate checks three necessary conditions before allowing auto-fix:
1. severity == "low" (MVP proxy for safe changes)
2. diff_truncated == False (we have complete context)
3. schema_validated == True (ReviewOutcome is valid)

Additionally, high-risk paths are excluded from auto-fix.

Usage:
    from coder.autofix_gate import is_autofix_allowed, is_path_excluded

    # In Router
    if is_autofix_allowed(review_outcome) and not is_path_excluded(file_path):
        # Route to Coder for auto-fix
        ...
"""
import logging
from typing import Dict, Any, FrozenSet, List, Optional

logger = logging.getLogger(__name__)

EXCLUDED_PATHS: FrozenSet[str] = frozenset({
    "config/",
    "migrations/",
    ".env",
    "settings.py",
    "pyproject.toml",
    "package.json",
    "package-lock.json",
    "yarn.lock",
    "poetry.lock",
    "Pipfile.lock",
    "requirements.txt",
    "setup.py",
    "setup.cfg",
    "Makefile",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    ".github/",
    ".gitlab-ci.yml",
    "Jenkinsfile",
})


def is_path_excluded(file_path: Optional[str]) -> bool:
    """Check if a file path is in the excluded list.

    High-risk paths are excluded from auto-fix to prevent
    accidental changes to configuration, migrations, or CI/CD.

    Args:
        file_path: File path to check (can be relative or absolute, or None)

    Returns:
        True if the path should be excluded from auto-fix

    Examples:
        >>> is_path_excluded("config/settings.py")
        True
        >>> is_path_excluded("src/utils.py")
        False
        >>> is_path_excluded(".env")
        True
    """
    if not file_path:
        return True

    normalized = file_path.strip()
    normalized_lower = normalized.lower()
    basename = normalized.split("/")[-1] if "/" in normalized else normalized

    for excluded in EXCLUDED_PATHS:
        excluded_lower = excluded.lower()
        if excluded.endswith("/"):
            if normalized_lower.startswith(excluded_lower) or f"/{excluded_lower}" in normalized_lower:
                return True
        else:
            if basename == excluded or basename.lower() == excluded_lower:
                return True
            if normalized_lower.endswith(f"/{excluded_lower}"):
                return True

    return False


def is_senior_coder_required(
    state: Dict[str, Any],
    review_outcome: Optional[Dict[str, Any]] = None
) -> bool:
    """Check if SeniorCoder should be invoked for this fix attempt.

    Issue #3366: Smart gate logic for CI failure auto-fix scenarios.
    CTO Directive: "方案 A + B 混合體"

    This function implements smarter gate logic that distinguishes between:
    1. Review comment auto-fix (D-1): Uses strict is_autofix_allowed() rules
    2. CI failure auto-fix (D-3): Bypasses severity check, only requires schema_validated

    Logic:
    - If ci_failure_trigger=True: Only require schema_validated=True (ignore severity)
    - If ci_failure_trigger=False: Fall back to is_autofix_allowed() logic
    - For diff_truncated: Pass through to SeniorCoder decision (don't block)

    Args:
        state: AgentState dict containing ci_failure_trigger flag
        review_outcome: Optional ReviewOutcome dict (will be fetched from state if not provided)

    Returns:
        True if SeniorCoder should be invoked, False otherwise

    Event Codes (greppable):
        [SENIOR_CODER_GATE_PASS] - SeniorCoder gate passed
        [SENIOR_CODER_GATE_FAIL] - SeniorCoder gate failed
        [SENIOR_CODER_GATE_CI_FAILURE] - CI failure trigger detected, using relaxed rules
    """
    if not state:
        logger.info("[SENIOR_CODER_GATE_FAIL] state is None or empty")
        return False

    # Get review_outcome from state if not provided
    if review_outcome is None:
        review_outcome = state.get("review_outcome", {})

    if not review_outcome:
        logger.info("[SENIOR_CODER_GATE_FAIL] review_outcome is None or empty")
        return False

    # Check if this is a CI failure trigger scenario
    ci_failure_trigger = state.get("ci_failure_trigger", False)

    # Extract review_outcome fields
    schema_validated = review_outcome.get("schema_validated", False)
    severity = review_outcome.get("severity", "").lower()
    diff_truncated = review_outcome.get("diff_truncated", True)

    # P0: schema_validated is non-negotiable (data format must be valid)
    if not schema_validated:
        logger.info(
            f"[SENIOR_CODER_GATE_FAIL] schema_validated={schema_validated} (required: True)"
        )
        return False

    if ci_failure_trigger:
        # CI failure scenario: bypass severity check
        # CTO: "如果 ci_failure_trigger 為 True，無視 severity == 'low' 的限制"
        logger.info(
            f"[SENIOR_CODER_GATE_CI_FAILURE] CI failure trigger detected, "
            f"bypassing severity check. severity={severity}, diff_truncated={diff_truncated}"
        )

        # For diff_truncated, let SeniorCoder decide instead of blocking
        # CTO: "對於 diff_truncated，如果為 True，由 SeniorCoder 決定是否能處理"
        if diff_truncated:
            logger.info(
                "[SENIOR_CODER_GATE_PASS] diff_truncated=True, "
                "passing to SeniorCoder for decision"
            )

        logger.info(
            "[SENIOR_CODER_GATE_PASS] CI failure trigger: "
            f"schema_validated=True, severity={severity} (ignored)"
        )
        return True
    else:
        # Non-CI failure scenario: use standard is_autofix_allowed() logic
        # This preserves the original D-1 review comment auto-fix behavior
        severity_ok = severity == "low"
        diff_ok = diff_truncated is False

        if not severity_ok:
            logger.info(
                f"[SENIOR_CODER_GATE_FAIL] severity={severity} (expected: low)"
            )
            return False

        if not diff_ok:
            logger.info(
                f"[SENIOR_CODER_GATE_FAIL] diff_truncated={diff_truncated} (expected: False)"
            )
            return False

        logger.info(
            "[SENIOR_CODER_GATE_PASS] severity=low, diff_truncated=False, schema_validated=True"
        )
        return True


def is_autofix_allowed(
    review_outcome: Dict[str, Any],
    file_paths: Optional[List[str]] = None
) -> bool:
    """Check if auto-fix is allowed based on ReviewOutcome.

    Three Don'ts Principle #2: Side-effect Gate
    All three conditions MUST be True for auto-fix to be allowed:
    1. severity == "low"
    2. diff_truncated == False
    3. schema_validated == True

    Additionally, if file_paths are provided, none of them can be
    in the EXCLUDED_PATHS list.

    Args:
        review_outcome: ReviewOutcome dict from state["review_outcome"]
        file_paths: Optional list of file paths to check for exclusion

    Returns:
        True if auto-fix is allowed, False otherwise

    Event Codes (greppable):
        [AUTOFIX_GATE_PASS] - All conditions met, auto-fix allowed
        [AUTOFIX_GATE_FAIL] - One or more conditions failed

    Examples:
        >>> outcome = {"severity": "low", "diff_truncated": False, "schema_validated": True}
        >>> is_autofix_allowed(outcome)
        True

        >>> outcome = {"severity": "medium", "diff_truncated": False, "schema_validated": True}
        >>> is_autofix_allowed(outcome)
        False
    """
    if not review_outcome:
        logger.info("[AUTOFIX_GATE_FAIL] review_outcome is None or empty")
        return False

    severity = review_outcome.get("severity", "").lower()
    diff_truncated = review_outcome.get("diff_truncated", True)
    schema_validated = review_outcome.get("schema_validated", False)

    severity_ok = severity == "low"
    diff_ok = diff_truncated is False
    schema_ok = schema_validated is True

    if not severity_ok:
        logger.info(
            f"[AUTOFIX_GATE_FAIL] severity={severity} (expected: low)"
        )
        return False

    if not diff_ok:
        logger.info(
            f"[AUTOFIX_GATE_FAIL] diff_truncated={diff_truncated} (expected: False)"
        )
        return False

    if not schema_ok:
        logger.info(
            f"[AUTOFIX_GATE_FAIL] schema_validated={schema_validated} (expected: True)"
        )
        return False

    if file_paths:
        for path in file_paths:
            if is_path_excluded(path):
                logger.info(
                    f"[AUTOFIX_GATE_FAIL] excluded path: {path}"
                )
                return False

    logger.info(
        "[AUTOFIX_GATE_PASS] severity=low, diff_truncated=False, "
        "schema_validated=True, no excluded paths"
    )
    return True
