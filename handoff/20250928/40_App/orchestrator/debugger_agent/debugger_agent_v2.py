#!/usr/bin/env python3
"""
Debugger Agent v2 - EPIC D Phase 5 (P2-medium)

Blueprint Reference: Section 3.3 (Agent Catalog V2) - Debugger Agent
Issue: #4104 (EPIC D P2: Debugger Agent v2 Complete Implementation)

This module implements the Debugger Agent v2 as a standalone agent that:
1. Parses CI/test failure logs to identify errors
2. Classifies errors by type (syntax, assertion, import, type, runtime)
3. Generates fix suggestions using LLM or heuristics
4. Applies fixes with retry logic (max 3 attempts)
5. Escalates to Reviewer when fixes fail

Design Principles (Blueprint Section 3.3 - Agent Separation):
- Test Agent generates tests (D-7)
- CI executes tests
- Debugger Agent fixes failing tests (D-4)
- Reviewer Agent validates fixes

What Debugger Agent v2 CAN do:
- Parse CI/test failure logs
- Analyze error types and root causes
- Generate fix suggestions using LLM
- Apply fixes with retry logic (max 3 attempts)
- Escalate to Reviewer when fixes fail

What Debugger Agent v2 CANNOT do (belongs to other agents):
- Generate new tests (that's Test Agent's job)
- Execute tests (that's CI's job)
- Review code quality (that's Reviewer's job)
"""

import hashlib
import json
import logging
import os
import re
import signal
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# Security Constants (Issue #4196)
MAX_CI_OUTPUT_LENGTH = 100000  # 100KB max CI output
MAX_ERROR_MESSAGE_LENGTH = 2000  # 2KB max error message for LLM
MAX_TRACEBACK_LENGTH = 5000  # 5KB max traceback
MAX_FILE_PATH_LENGTH = 500  # Max file path length
REGEX_TIMEOUT_SECONDS = 5  # Timeout for regex operations

# Prompt injection patterns to sanitize (Issue #4196 - HIGH priority)
PROMPT_INJECTION_PATTERNS = [
    r"(?i)ignore\s+(all\s+)?previous\s+instructions?",
    r"(?i)disregard\s+(all\s+)?previous",
    r"(?i)forget\s+(all\s+)?previous",
    r"(?i)system\s*:\s*",
    r"(?i)assistant\s*:\s*",
    r"(?i)user\s*:\s*",
    r"(?i)human\s*:\s*",
    r"(?i)<\|im_start\|>",
    r"(?i)<\|im_end\|>",
    r"(?i)\[INST\]",
    r"(?i)\[/INST\]",
    r"(?i)<<SYS>>",
    r"(?i)<</SYS>>",
]

# Path traversal patterns to block (Issue #4196 - MEDIUM priority)
PATH_TRAVERSAL_PATTERNS = [
    r"\.\./",
    r"\.\.\\",
    r"%2e%2e%2f",
    r"%2e%2e/",
    r"\.%2e/",
    r"%2e\./",
]


class DebugSeverity(Enum):
    """Severity levels for debug issues."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DebugAction(Enum):
    """Actions the debugger can take."""
    FIX_APPLIED = "fix_applied"
    FIX_SUGGESTED = "fix_suggested"
    ESCALATE = "escalate"
    NO_ACTION = "no_action"


class ErrorType(Enum):
    """Classification of error types."""
    SYNTAX = "syntax"
    ASSERTION = "assertion"
    IMPORT = "import"
    TYPE = "type"
    RUNTIME = "runtime"
    TIMEOUT = "timeout"
    MEMORY = "memory"
    UNKNOWN = "unknown"


@dataclass
class ErrorClassification:
    """Classification of an error from CI/test output.

    Attributes:
        error_type: Type of error
        error_message: The error message
        file_path: File path where error occurred
        line_number: Line number where error occurred
        test_name: Name of the failed test
        traceback: Full traceback if available
        expected_value: Expected value in assertion
        actual_value: Actual value in assertion
        severity: Severity of the error
        is_simple_fix: Whether this is likely a simple fix
    """
    error_type: ErrorType
    error_message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    test_name: Optional[str] = None
    traceback: Optional[str] = None
    expected_value: Optional[str] = None
    actual_value: Optional[str] = None
    severity: DebugSeverity = DebugSeverity.MEDIUM
    is_simple_fix: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "error_type": self.error_type.value,
            "error_message": self.error_message,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "test_name": self.test_name,
            "traceback": self.traceback,
            "expected_value": self.expected_value,
            "actual_value": self.actual_value,
            "severity": self.severity.value,
            "is_simple_fix": self.is_simple_fix,
        }


@dataclass
class FixAttempt:
    """Record of a fix attempt.

    Attributes:
        attempt_number: Which attempt this is (1-3)
        fix_description: Description of the fix
        patches: List of patches applied
        success: Whether the fix was successful
        error_after_fix: Error message after fix (if still failing)
    """
    attempt_number: int
    fix_description: str
    patches: List[Dict[str, Any]] = field(default_factory=list)
    success: bool = False
    error_after_fix: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "attempt_number": self.attempt_number,
            "fix_description": self.fix_description,
            "patches": self.patches,
            "success": self.success,
            "error_after_fix": self.error_after_fix,
        }


@dataclass
class DebugResult:
    """Result of a debug operation.

    Attributes:
        success: Whether debugging was successful
        action: Action taken by the debugger
        errors_found: List of errors found
        fix_attempts: List of fix attempts made
        total_attempts: Total number of attempts
        escalated: Whether the issue was escalated
        summary: Human-readable summary
        evidence_hash: Hash for evidence ledger
        analysis_duration_ms: Time taken for analysis
    """
    success: bool
    action: DebugAction
    errors_found: List[ErrorClassification] = field(default_factory=list)
    fix_attempts: List[FixAttempt] = field(default_factory=list)
    total_attempts: int = 0
    escalated: bool = False
    summary: str = ""
    evidence_hash: str = ""
    analysis_duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "success": self.success,
            "action": self.action.value,
            "errors_found": [e.to_dict() for e in self.errors_found],
            "fix_attempts": [f.to_dict() for f in self.fix_attempts],
            "total_attempts": self.total_attempts,
            "escalated": self.escalated,
            "summary": self.summary,
            "evidence_hash": self.evidence_hash,
            "analysis_duration_ms": self.analysis_duration_ms,
        }


# Constants
MAX_DEBUG_ATTEMPTS = 3
SIMPLE_FIX_ERROR_TYPES = {ErrorType.SYNTAX, ErrorType.IMPORT, ErrorType.TYPE}

# Regex patterns for error parsing
PYTEST_FAILED_PATTERN = re.compile(
    r"FAILED\s+([^\s]+\.py(?:::[^\s]+)+)\s+-\s+(.+)",
    re.MULTILINE
)
PYTEST_ERROR_PATTERN = re.compile(
    r"E\s+(\w+Error|AssertionError):\s*(.+)",
    re.MULTILINE
)
PYTEST_FILE_LINE_PATTERN = re.compile(
    r"([^\s]+\.py):(\d+):",
    re.MULTILINE
)
TRACEBACK_PATTERN = re.compile(
    r"Traceback \(most recent call last\):(.+?)(?=\n\n|\Z)",
    re.DOTALL
)
GENERIC_ERROR_PATTERN = re.compile(
    r"(\w+Error|\w+Exception):\s*(.+)",
    re.MULTILINE
)


class DebuggerAgentV2:
    """
    Debugger Agent v2 - Standalone agent for autonomous test failure recovery.

    Blueprint Reference: Section 3.3 (Agent Catalog V2) - Debugger Agent
    Issue: #4104 (EPIC D P2: Debugger Agent v2 Complete Implementation)

    This agent:
    1. Parses CI/test failure logs to identify errors
    2. Classifies errors by type
    3. Generates fix suggestions
    4. Applies fixes with retry logic
    5. Escalates to Reviewer when fixes fail

    Event Codes (greppable):
        [DebuggerAgentV2] - General agent events
        [DEBUG_START] - Started debugging
        [DEBUG_PARSE] - Parsing CI output
        [DEBUG_CLASSIFY] - Classifying errors
        [DEBUG_FIX_ATTEMPT] - Attempting a fix
        [DEBUG_FIX_SUCCESS] - Fix successful
        [DEBUG_FIX_FAIL] - Fix failed
        [DEBUG_ESCALATE] - Escalating to Reviewer
    """

    def __init__(
        self,
        enabled: Optional[bool] = None,
        enable_llm: Optional[bool] = None,
        max_attempts: Optional[int] = None,
    ):
        """Initialize DebuggerAgentV2.

        Args:
            enabled: Whether the agent is enabled (default: True or from settings)
            enable_llm: Whether to use LLM for fix generation (default: True or from settings)
            max_attempts: Maximum fix attempts before escalation (default: 3 or from settings)
        """
        # Load defaults from settings first, then override with explicit args
        default_enabled, default_enable_llm, default_max_attempts = self._load_settings()

        self.enabled = enabled if enabled is not None else default_enabled
        self.enable_llm = enable_llm if enable_llm is not None else default_enable_llm
        self.max_attempts = max_attempts if max_attempts is not None else default_max_attempts

        logger.info(
            "[DebuggerAgentV2] Initialized: enabled=%s, enable_llm=%s, max_attempts=%d",
            self.enabled,
            self.enable_llm,
            self.max_attempts,
        )

    def _load_settings(self) -> Tuple[bool, bool, int]:
        """Load settings from config if available.

        Returns:
            Tuple of (enabled, enable_llm, max_attempts) defaults
        """
        default_enabled = True
        default_enable_llm = True
        default_max_attempts = MAX_DEBUG_ATTEMPTS

        try:
            from common.config.settings import settings
            if hasattr(settings, "debugger_agent_enabled"):
                default_enabled = settings.debugger_agent_enabled
            if hasattr(settings, "debugger_agent_enable_llm"):
                default_enable_llm = settings.debugger_agent_enable_llm
            if hasattr(settings, "self_correction_max_attempts"):
                default_max_attempts = settings.self_correction_max_attempts
        except ImportError:
            pass

        return default_enabled, default_enable_llm, default_max_attempts

    def _get_coder(self) -> Optional[Any]:
        """Get coder instance for fix generation."""
        try:
            from coder.general_coder import get_general_coder
            return get_general_coder()
        except ImportError:
            logger.warning("[DebuggerAgentV2] GeneralCoder not available")
            return None

    def _sanitize_for_llm(self, text: str, max_length: int = MAX_ERROR_MESSAGE_LENGTH) -> str:
        """Sanitize text before passing to LLM to prevent prompt injection.

        Issue #4196 - HIGH priority security enhancement.

        Args:
            text: Text to sanitize
            max_length: Maximum allowed length

        Returns:
            Sanitized text safe for LLM consumption
        """
        if not text:
            return ""

        # Truncate to max length first
        sanitized = text[:max_length]

        # Remove prompt injection patterns
        for pattern in PROMPT_INJECTION_PATTERNS:
            sanitized = re.sub(pattern, "[REDACTED]", sanitized)

        # Remove control characters that could manipulate LLM
        sanitized = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", sanitized)

        # Escape potential markdown/formatting that could confuse LLM
        sanitized = sanitized.replace("```", "'''")

        logger.debug(
            "[DebuggerAgentV2] Sanitized text: original_len=%d, sanitized_len=%d",
            len(text),
            len(sanitized),
        )

        return sanitized

    def _safe_regex_search(
        self,
        pattern: re.Pattern,
        text: str,
        timeout_seconds: int = REGEX_TIMEOUT_SECONDS,
    ) -> Optional[re.Match]:
        """Execute regex search with timeout to prevent ReDoS.

        Issue #4196 - MEDIUM priority security enhancement.

        Args:
            pattern: Compiled regex pattern
            text: Text to search
            timeout_seconds: Maximum time allowed for regex operation

        Returns:
            Match object or None if no match or timeout
        """
        # Limit input length to prevent catastrophic backtracking
        if len(text) > MAX_CI_OUTPUT_LENGTH:
            logger.warning(
                "[DebuggerAgentV2] Input too long for regex: %d > %d, truncating",
                len(text),
                MAX_CI_OUTPUT_LENGTH,
            )
            text = text[:MAX_CI_OUTPUT_LENGTH]

        def timeout_handler(signum: int, frame: Any) -> None:
            raise TimeoutError("Regex operation timed out")

        # Set up timeout (Unix only)
        old_handler = None
        try:
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout_seconds)

            result = pattern.search(text)

            signal.alarm(0)  # Cancel the alarm
            return result

        except TimeoutError:
            logger.warning(
                "[DebuggerAgentV2] Regex timed out after %d seconds",
                timeout_seconds,
            )
            return None
        except (ValueError, OSError):
            # signal.alarm not available (e.g., Windows or threading)
            # Fall back to direct execution with length limit
            return pattern.search(text)
        finally:
            if old_handler is not None:
                try:
                    signal.signal(signal.SIGALRM, old_handler)
                except (ValueError, OSError):
                    pass

    def _safe_regex_finditer(
        self,
        pattern: re.Pattern,
        text: str,
        max_matches: int = 100,
    ) -> List[re.Match]:
        """Execute regex finditer with match limit to prevent ReDoS.

        Issue #4196 - MEDIUM priority security enhancement.

        Args:
            pattern: Compiled regex pattern
            text: Text to search
            max_matches: Maximum number of matches to return

        Returns:
            List of match objects (limited to max_matches)
        """
        # Limit input length
        if len(text) > MAX_CI_OUTPUT_LENGTH:
            text = text[:MAX_CI_OUTPUT_LENGTH]

        matches = []
        try:
            for i, match in enumerate(pattern.finditer(text)):
                if i >= max_matches:
                    logger.warning(
                        "[DebuggerAgentV2] Max matches (%d) reached, stopping",
                        max_matches,
                    )
                    break
                matches.append(match)
        except Exception as e:
            logger.warning("[DebuggerAgentV2] Regex finditer error: %s", e)

        return matches

    def _validate_file_path(self, file_path: str, allowed_files: List[str]) -> bool:
        """Validate file path to prevent path traversal attacks.

        Issue #4196 - MEDIUM priority security enhancement.

        Args:
            file_path: Path to validate
            allowed_files: List of allowed file paths

        Returns:
            True if path is valid and safe, False otherwise
        """
        if not file_path:
            return False

        # Check length limit
        if len(file_path) > MAX_FILE_PATH_LENGTH:
            logger.warning(
                "[DebuggerAgentV2] File path too long: %d > %d",
                len(file_path),
                MAX_FILE_PATH_LENGTH,
            )
            return False

        # Check for path traversal patterns
        for pattern in PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, file_path, re.IGNORECASE):
                logger.warning(
                    "[DebuggerAgentV2] Path traversal detected in: %s",
                    file_path[:100],
                )
                return False

        # Normalize the path
        normalized = os.path.normpath(file_path)

        # Check if normalized path still contains traversal
        if ".." in normalized:
            logger.warning(
                "[DebuggerAgentV2] Path traversal after normalization: %s",
                normalized[:100],
            )
            return False

        # Verify the path matches one of the allowed files
        # Security fix: Use path boundary checks to prevent partial matches
        # (e.g., 'file.py' should not match 'super_file.py')
        for allowed in allowed_files:
            allowed_normalized = os.path.normpath(allowed)
            # Normalize paths for comparison, using forward slashes
            norm_path = normalized.lstrip("./").replace("\\", "/")
            allowed_path = allowed_normalized.replace("\\", "/")
            # Check for exact match or path boundary match (with / prefix)
            if (
                allowed_path == norm_path
                or f"/{allowed_path}".endswith(f"/{norm_path}")
                or f"/{norm_path}".endswith(f"/{allowed_path}")
            ):
                return True

        return False

    def _sanitize_ci_output(self, ci_output: str) -> str:
        """Sanitize CI output before processing.

        Issue #4196 - Combined security enhancement.

        Args:
            ci_output: Raw CI output

        Returns:
            Sanitized CI output
        """
        if not ci_output:
            return ""

        # Truncate to max length
        sanitized = ci_output[:MAX_CI_OUTPUT_LENGTH]

        # Remove null bytes and other dangerous characters
        sanitized = sanitized.replace("\x00", "")

        return sanitized

    def debug_ci_failure(
        self,
        ci_output: str,
        files: Optional[List[Dict[str, str]]] = None,
        trace_id: str = "",
        run_tests_callback: Optional[callable] = None,
    ) -> DebugResult:
        """
        Debug a CI failure and attempt to fix it.

        This is the main entry point for debugging CI failures.

        Args:
            ci_output: Raw CI/test output with failures
            files: List of files with "path" and "content" keys
            trace_id: Trace ID for telemetry
            run_tests_callback: Optional callback to re-run tests after fix

        Returns:
            DebugResult with debugging outcome
        """
        start_time = time.time()
        logger.info("[DEBUG_START] Starting debug for trace_id=%s", trace_id)

        if not self.enabled:
            return DebugResult(
                success=False,
                action=DebugAction.NO_ACTION,
                summary="Debugger Agent is disabled",
            )

        if not ci_output or not ci_output.strip():
            return DebugResult(
                success=True,
                action=DebugAction.NO_ACTION,
                summary="No CI output to debug",
            )

        # Security: Sanitize CI output before processing (Issue #4196)
        ci_output = self._sanitize_ci_output(ci_output)

        files = files or []

        # Step 1: Parse CI output to find errors
        logger.info("[DEBUG_PARSE] Parsing CI output")
        errors = self._parse_ci_output(ci_output)

        if not errors:
            return DebugResult(
                success=True,
                action=DebugAction.NO_ACTION,
                summary="No errors found in CI output",
            )

        # Step 2: Attempt fixes
        fix_attempts: List[FixAttempt] = []
        current_errors = errors
        current_output = ci_output

        for attempt_num in range(1, self.max_attempts + 1):
            logger.info(
                "[DEBUG_FIX_ATTEMPT] Attempt %d/%d",
                attempt_num,
                self.max_attempts,
            )

            # Focus on the first error (most likely root cause)
            primary_error = current_errors[0]

            # Generate fix
            fix_attempt = self._attempt_fix(
                primary_error,
                files,
                attempt_num,
                trace_id,
            )
            fix_attempts.append(fix_attempt)

            if not fix_attempt.patches:
                logger.info("[DEBUG_FIX_FAIL] No fix generated for attempt %d", attempt_num)
                continue

            # If we have a callback, verify the fix
            if run_tests_callback:
                try:
                    new_output = run_tests_callback(fix_attempt.patches)
                    new_errors = self._parse_ci_output(new_output)

                    if not new_errors:
                        logger.info(
                            "[DEBUG_FIX_SUCCESS] Fixed after %d attempts",
                            attempt_num,
                        )
                        fix_attempt.success = True

                        duration_ms = (time.time() - start_time) * 1000
                        return DebugResult(
                            success=True,
                            action=DebugAction.FIX_APPLIED,
                            errors_found=errors,
                            fix_attempts=fix_attempts,
                            total_attempts=attempt_num,
                            summary=f"Successfully fixed after {attempt_num} attempt(s)",
                            evidence_hash=self._compute_evidence_hash(ci_output, fix_attempts),
                            analysis_duration_ms=duration_ms,
                        )

                    # Update for next attempt
                    current_errors = new_errors
                    current_output = new_output
                    fix_attempt.error_after_fix = new_errors[0].error_message

                except Exception as e:
                    logger.warning("[DEBUG_FIX_FAIL] Error running tests: %s", e)
                    fix_attempt.error_after_fix = str(e)
            else:
                # Without callback, return suggested fix
                logger.info(
                    "[DEBUG_FIX_SUGGEST] Generated fix but cannot verify (no callback)"
                )
                duration_ms = (time.time() - start_time) * 1000
                return DebugResult(
                    success=False,
                    action=DebugAction.FIX_SUGGESTED,
                    errors_found=errors,
                    fix_attempts=fix_attempts,
                    total_attempts=attempt_num,
                    summary=f"Generated unverified fix after {attempt_num} attempt(s)",
                    evidence_hash=self._compute_evidence_hash(ci_output, fix_attempts),
                    analysis_duration_ms=duration_ms,
                )

        # All attempts exhausted - escalate
        logger.warning(
            "[DEBUG_ESCALATE] Max attempts (%d) reached, escalating",
            self.max_attempts,
        )

        duration_ms = (time.time() - start_time) * 1000
        return DebugResult(
            success=False,
            action=DebugAction.ESCALATE,
            errors_found=errors,
            fix_attempts=fix_attempts,
            total_attempts=self.max_attempts,
            escalated=True,
            summary=f"Failed to fix after {self.max_attempts} attempts. Escalating to Reviewer.",
            evidence_hash=self._compute_evidence_hash(ci_output, fix_attempts),
            analysis_duration_ms=duration_ms,
        )

    def analyze_error(
        self,
        error_output: str,
        file_content: Optional[str] = None,
    ) -> ErrorClassification:
        """
        Analyze a single error and classify it.

        Args:
            error_output: Error output string
            file_content: Optional file content for context

        Returns:
            ErrorClassification with error details
        """
        logger.info("[DEBUG_CLASSIFY] Analyzing error")

        # Detect error type
        error_type = self._classify_error_type(error_output)

        # Extract error message
        error_message = self._extract_error_message(error_output)

        # Extract file and line info
        file_path, line_number = self._extract_file_line(error_output)

        # Extract test name
        test_name = self._extract_test_name(error_output)

        # Extract assertion values
        expected, actual = self._extract_assertion_values(error_output)

        # Determine severity
        severity = self._determine_severity(error_type)

        # Determine if simple fix
        is_simple = error_type in SIMPLE_FIX_ERROR_TYPES

        return ErrorClassification(
            error_type=error_type,
            error_message=error_message,
            file_path=file_path,
            line_number=line_number,
            test_name=test_name,
            traceback=self._extract_traceback(error_output),
            expected_value=expected,
            actual_value=actual,
            severity=severity,
            is_simple_fix=is_simple,
        )

    def _parse_ci_output(self, ci_output: str) -> List[ErrorClassification]:
        """Parse CI output and extract all errors.

        Security: Uses safe regex operations to prevent ReDoS (Issue #4196).
        """
        errors: List[ErrorClassification] = []

        # Security: Use safe regex with match limits (Issue #4196)
        # Try pytest pattern first
        for match in self._safe_regex_finditer(PYTEST_FAILED_PATTERN, ci_output):
            test_name = match.group(1)
            error_summary = match.group(2)

            error = self.analyze_error(ci_output)
            error.test_name = test_name
            error.error_message = error_summary

            # Extract file path from test name
            if "::" in test_name:
                error.file_path = test_name.split("::")[0]

            errors.append(error)

        # If no pytest failures, try generic patterns
        if not errors:
            for match in self._safe_regex_finditer(GENERIC_ERROR_PATTERN, ci_output):
                error_type_str = match.group(1)
                error_message = match.group(2)

                error = ErrorClassification(
                    error_type=self._classify_error_type(error_type_str),
                    error_message=error_message,
                )

                # Try to extract file/line
                file_path, line_number = self._extract_file_line(ci_output)
                error.file_path = file_path
                error.line_number = line_number

                errors.append(error)

        return errors

    def _classify_error_type(self, error_str: str) -> ErrorType:
        """Classify error type from error string."""
        error_lower = error_str.lower()

        if "syntaxerror" in error_lower or "indentationerror" in error_lower:
            return ErrorType.SYNTAX
        elif "assertionerror" in error_lower or "assert" in error_lower:
            return ErrorType.ASSERTION
        elif "importerror" in error_lower or "modulenotfounderror" in error_lower:
            return ErrorType.IMPORT
        elif "typeerror" in error_lower or "attributeerror" in error_lower:
            return ErrorType.TYPE
        elif "timeout" in error_lower:
            return ErrorType.TIMEOUT
        elif "memoryerror" in error_lower or "oom" in error_lower:
            return ErrorType.MEMORY
        elif "error" in error_lower or "exception" in error_lower:
            return ErrorType.RUNTIME
        else:
            return ErrorType.UNKNOWN

    def _extract_error_message(self, output: str) -> str:
        """Extract error message from output."""
        match = PYTEST_ERROR_PATTERN.search(output)
        if match:
            return f"{match.group(1)}: {match.group(2)}"

        match = GENERIC_ERROR_PATTERN.search(output)
        if match:
            return f"{match.group(1)}: {match.group(2)}"

        return "Unknown error"

    def _extract_file_line(self, output: str) -> Tuple[Optional[str], Optional[int]]:
        """Extract file path and line number from output."""
        match = PYTEST_FILE_LINE_PATTERN.search(output)
        if match:
            return match.group(1), int(match.group(2))
        return None, None

    def _extract_test_name(self, output: str) -> Optional[str]:
        """Extract test name from output."""
        match = PYTEST_FAILED_PATTERN.search(output)
        if match:
            return match.group(1)
        return None

    def _extract_traceback(self, output: str) -> Optional[str]:
        """Extract traceback from output."""
        match = TRACEBACK_PATTERN.search(output)
        if match:
            return match.group(1).strip()
        return None

    def _extract_assertion_values(self, output: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract expected and actual values from assertion error."""
        # Look for pytest assertion patterns
        expected_pattern = re.compile(r"assert\s+(.+?)\s*==\s*(.+)", re.MULTILINE)
        match = expected_pattern.search(output)
        if match:
            return match.group(2).strip(), match.group(1).strip()

        # Look for "Expected: X, Received: Y" pattern
        expected_received = re.compile(
            r"Expected:?\s*(.+?)\s*(?:Received|Actual|Got):?\s*(.+)",
            re.MULTILINE | re.IGNORECASE
        )
        match = expected_received.search(output)
        if match:
            return match.group(1).strip(), match.group(2).strip()

        return None, None

    def _determine_severity(self, error_type: ErrorType) -> DebugSeverity:
        """Determine severity based on error type."""
        if error_type == ErrorType.SYNTAX:
            return DebugSeverity.CRITICAL
        elif error_type in {ErrorType.IMPORT, ErrorType.TYPE}:
            return DebugSeverity.HIGH
        elif error_type == ErrorType.ASSERTION:
            return DebugSeverity.MEDIUM
        else:
            return DebugSeverity.LOW

    def _attempt_fix(
        self,
        error: ErrorClassification,
        files: List[Dict[str, str]],
        attempt_num: int,
        trace_id: str,
    ) -> FixAttempt:
        """Attempt to generate a fix for the error.

        Security: Uses path validation to prevent path traversal (Issue #4196).
        """
        fix_attempt = FixAttempt(
            attempt_number=attempt_num,
            fix_description=f"Attempting to fix {error.error_type.value} error",
        )

        # Security: Validate file path before processing (Issue #4196)
        if error.file_path:
            allowed_paths = [f["path"] for f in files]
            if not self._validate_file_path(error.file_path, allowed_paths):
                logger.warning(
                    "[DebuggerAgentV2] Invalid file path rejected: %s",
                    error.file_path[:100] if error.file_path else "None",
                )
                fix_attempt.fix_description = "Invalid or unsafe file path"
                return fix_attempt

        # Find the relevant file
        target_file = None
        file_content = None
        for f in files:
            if error.file_path and f["path"].endswith(error.file_path.lstrip("./")):
                target_file = f["path"]
                file_content = f["content"]
                break

        if not target_file or not file_content:
            fix_attempt.fix_description = "Could not find target file"
            return fix_attempt

        # Generate fix based on error type
        if self.enable_llm:
            patches = self._generate_llm_fix(error, target_file, file_content, trace_id)
        else:
            patches = self._generate_heuristic_fix(error, target_file, file_content)

        fix_attempt.patches = patches
        fix_attempt.fix_description = f"Generated {len(patches)} patch(es) for {error.error_type.value} error"

        return fix_attempt

    def _generate_llm_fix(
        self,
        error: ErrorClassification,
        target_file: str,
        file_content: str,
        trace_id: str,
    ) -> List[Dict[str, Any]]:
        """Generate fix using LLM."""
        coder = self._get_coder()
        if not coder:
            return []

        try:
            # Build review comment for coder
            review_comment = self._build_review_comment(error)

            result = coder.generate_fix(
                file_content=file_content,
                file_path=target_file,
                review_comment=review_comment,
                severity=error.severity.value,
            )

            if hasattr(result, "status") and result.status.value == "patch":
                return [{
                    "file_path": target_file,
                    "patch": result.patch if hasattr(result, "patch") else "",
                }]

        except Exception as e:
            logger.warning("[DebuggerAgentV2] LLM fix generation failed: %s", e)

        return []

    def _generate_heuristic_fix(
        self,
        error: ErrorClassification,
        target_file: str,
        file_content: str,
    ) -> List[Dict[str, Any]]:
        """Generate fix using heuristics (no LLM)."""
        patches: List[Dict[str, Any]] = []

        if error.error_type == ErrorType.IMPORT:
            # Try to suggest import fix
            if error.error_message and "No module named" in error.error_message:
                module_match = re.search(r"No module named '([^']+)'", error.error_message)
                if module_match:
                    module_name = module_match.group(1)
                    patches.append({
                        "file_path": target_file,
                        "suggestion": f"Add 'import {module_name}' or install the package",
                        "type": "suggestion",
                    })

        elif error.error_type == ErrorType.SYNTAX:
            # Syntax errors usually need manual review
            patches.append({
                "file_path": target_file,
                "suggestion": f"Fix syntax error at line {error.line_number}: {error.error_message}",
                "type": "suggestion",
            })

        return patches

    def _build_review_comment(self, error: ErrorClassification) -> str:
        """Build a review comment from error classification.

        Security: Sanitizes all error content before passing to LLM (Issue #4196).
        """
        # Security: Sanitize error message to prevent prompt injection (Issue #4196)
        sanitized_message = self._sanitize_for_llm(
            error.error_message or "", MAX_ERROR_MESSAGE_LENGTH
        )

        parts = [
            f"Fix {error.error_type.value} error: {sanitized_message}",
        ]

        if error.file_path:
            # Security: Sanitize file path to prevent prompt injection (Issue #4196)
            # File paths from CI output could contain injection patterns like "system:.py"
            safe_path = self._sanitize_for_llm(
                error.file_path, MAX_FILE_PATH_LENGTH
            )
            parts.append(f"File: {safe_path}")

        if error.line_number:
            parts.append(f"Line: {error.line_number}")

        if error.expected_value and error.actual_value:
            # Security: Sanitize assertion values
            safe_expected = self._sanitize_for_llm(error.expected_value, 500)
            safe_actual = self._sanitize_for_llm(error.actual_value, 500)
            parts.append(f"Expected: {safe_expected}")
            parts.append(f"Actual: {safe_actual}")

        if error.traceback:
            # Security: Sanitize traceback
            safe_traceback = self._sanitize_for_llm(
                error.traceback, MAX_TRACEBACK_LENGTH
            )[:500]
            parts.append(f"Traceback:\n{safe_traceback}")

        return "\n".join(parts)

    def _compute_evidence_hash(
        self,
        ci_output: str,
        fix_attempts: List[FixAttempt],
    ) -> str:
        """Compute hash for evidence ledger."""
        sorted_attempts = sorted(
            [f.to_dict() for f in fix_attempts],
            key=lambda x: x.get("attempt_number", 0),
        )
        attempts_json = json.dumps(sorted_attempts, sort_keys=True)
        content = ci_output + attempts_json
        return hashlib.sha256(content.encode()).hexdigest()[:16]


# Singleton instance
_debugger_agent_instance: Optional[DebuggerAgentV2] = None


def get_debugger_agent() -> DebuggerAgentV2:
    """Get or create the singleton DebuggerAgentV2 instance."""
    global _debugger_agent_instance
    if _debugger_agent_instance is None:
        _debugger_agent_instance = DebuggerAgentV2()
    return _debugger_agent_instance


def reset_debugger_agent() -> None:
    """Reset the singleton instance (for testing)."""
    global _debugger_agent_instance
    _debugger_agent_instance = None


def debug_ci_failure(
    ci_output: str,
    files: Optional[List[Dict[str, str]]] = None,
    trace_id: str = "",
    run_tests_callback: Optional[callable] = None,
) -> Dict[str, Any]:
    """
    Convenience function for debugging CI failures.

    Args:
        ci_output: Raw CI/test output with failures
        files: List of files with "path" and "content" keys
        trace_id: Trace ID for telemetry
        run_tests_callback: Optional callback to re-run tests after fix

    Returns:
        Dictionary with debug results
    """
    agent = get_debugger_agent()
    result = agent.debug_ci_failure(ci_output, files, trace_id, run_tests_callback)
    return result.to_dict()


def analyze_error(
    error_output: str,
    file_content: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Convenience function for analyzing errors.

    Args:
        error_output: Error output string
        file_content: Optional file content for context

    Returns:
        Dictionary with error classification
    """
    agent = get_debugger_agent()
    result = agent.analyze_error(error_output, file_content)
    return result.to_dict()
