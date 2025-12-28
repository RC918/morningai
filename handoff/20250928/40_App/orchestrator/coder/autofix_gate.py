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


def is_path_excluded(file_path: str) -> bool:
    """Check if a file path is in the excluded list.

    High-risk paths are excluded from auto-fix to prevent
    accidental changes to configuration, migrations, or CI/CD.

    Args:
        file_path: File path to check (can be relative or absolute)

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
