"""
D-4: Self-Correction Loop - Autonomous Test Failure Recovery

Issue #2764: D-4 Self-Correction Loop
Parent EPIC #2759: EPIC D - Autonomous Coder Agent Family
CTO Approved: 2026-01-10

This module implements the Self-Correction Loop for autonomous test failure recovery:
1. Test Log Parser - Parses pytest/npm test output to extract failure information
2. Error Analyzer - Classifies errors by type (syntax, assertion, import, type, runtime)
3. Self-Correction Controller - Manages retry logic (max 3 attempts)
4. Integration with GeneralCoder/SimpleCoder for fix generation

Workflow:
    Test Failure → TestLogParser → ErrorAnalyzer → Coder Fix → Retry (max 3) → Escalate

Usage:
    from coder.self_correction import SelfCorrectionLoop, TestLogParser

    loop = SelfCorrectionLoop()
    result = loop.attempt_correction(
        test_output="FAILED tests/test_foo.py::test_bar - AssertionError",
        files=[{"path": "src/foo.py", "content": "..."}]
    )

    if result.success:
        # Apply the fix
        ...
    else:
        # Escalate to Reviewer
        ...
"""
import json
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


# =============================================================================
# Constants and Configuration
# =============================================================================

# Maximum retry attempts before escalating to Reviewer
MAX_CORRECTION_ATTEMPTS = 3

# Schema version for SelfCorrectionResult
SELF_CORRECTION_SCHEMA_VERSION = 1


class ErrorType(Enum):
    """Classification of test failure error types.

    Issue #2764: D-4 Self-Correction Loop
    """
    SYNTAX = "syntax"           # SyntaxError, IndentationError
    ASSERTION = "assertion"     # AssertionError, expect().toBe()
    IMPORT = "import"           # ImportError, ModuleNotFoundError
    TYPE = "type"               # TypeError, AttributeError
    RUNTIME = "runtime"         # Other runtime errors
    UNKNOWN = "unknown"         # Unclassified errors


@dataclass
class ParsedTestFailure:
    """Parsed information from a single test failure.

    Attributes:
        test_name: Name of the failed test (e.g., "test_foo.py::test_bar")
        error_type: Classified error type
        error_message: The error message
        file_path: File path where the error occurred (if identifiable)
        line_number: Line number where the error occurred (if identifiable)
        traceback: Full traceback (if available)
        expected_value: Expected value in assertion (if applicable)
        actual_value: Actual value in assertion (if applicable)
    """
    test_name: str
    error_type: ErrorType
    error_message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    traceback: Optional[str] = None
    expected_value: Optional[str] = None
    actual_value: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "test_name": self.test_name,
            "error_type": self.error_type.value,
            "error_message": self.error_message,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "traceback": self.traceback,
            "expected_value": self.expected_value,
            "actual_value": self.actual_value,
        }


@dataclass
class TestLogParseResult:
    """Result of parsing test output.

    Attributes:
        failures: List of parsed test failures
        total_tests: Total number of tests run
        passed_tests: Number of tests passed
        failed_tests: Number of tests failed
        test_framework: Detected test framework (pytest, jest, mocha, etc.)
        raw_output: Original test output
    """
    failures: List[ParsedTestFailure] = field(default_factory=list)
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    test_framework: str = "unknown"
    raw_output: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "failures": [f.to_dict() for f in self.failures],
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "test_framework": self.test_framework,
        }


@dataclass
class SelfCorrectionResult:
    """Result of a self-correction attempt.

    Attributes:
        success: Whether the correction was successful
        attempts: Number of attempts made
        final_error: Final error message if failed
        corrections_applied: List of corrections applied
        escalated: Whether the issue was escalated to Reviewer
        feedback: Human-readable feedback about the correction process
    """
    success: bool
    attempts: int = 0
    final_error: Optional[str] = None
    corrections_applied: List[Dict[str, Any]] = field(default_factory=list)
    escalated: bool = False
    feedback: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "schema_version": SELF_CORRECTION_SCHEMA_VERSION,
            "success": self.success,
            "attempts": self.attempts,
            "final_error": self.final_error,
            "corrections_applied": self.corrections_applied,
            "escalated": self.escalated,
            "feedback": self.feedback,
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


# =============================================================================
# Test Log Parser
# =============================================================================

class TestLogParser:
    """Parser for test output from various test frameworks.

    Supports:
    - pytest (Python)
    - Jest/Mocha (JavaScript/TypeScript)
    - npm test output

    Event Codes (greppable):
        [TEST_LOG_PARSE_START] - Started parsing test output
        [TEST_LOG_PARSE_COMPLETE] - Completed parsing
        [TEST_LOG_PARSE_FAILURE] - Found a test failure
        [TEST_LOG_PARSE_ERROR] - Error during parsing
    """

    # Pytest patterns
    PYTEST_FAILED_PATTERN = re.compile(
        r"FAILED\s+([^\s]+)\s+-\s+(.+)",
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
    PYTEST_SUMMARY_PATTERN = re.compile(
        r"=+\s*(\d+)\s+failed,?\s*(\d+)?\s*passed",
        re.IGNORECASE
    )
    PYTEST_ASSERTION_PATTERN = re.compile(
        r"assert\s+(.+?)\s*==\s*(.+)",
        re.MULTILINE
    )

    # Jest/npm test patterns
    JEST_FAILED_PATTERN = re.compile(
        r"FAIL\s+([^\s]+)",
        re.MULTILINE
    )
    JEST_ERROR_PATTERN = re.compile(
        r"(Error|TypeError|ReferenceError):\s*(.+)",
        re.MULTILINE
    )
    JEST_EXPECT_PATTERN = re.compile(
        r"Expected:?\s*(.+?)\s*(?:Received|to\s+(?:be|equal)):?\s*(.+)",
        re.MULTILINE | re.IGNORECASE
    )

    # Generic error patterns
    TRACEBACK_PATTERN = re.compile(
        r"Traceback \(most recent call last\):(.+?)(?=\n\n|\Z)",
        re.DOTALL
    )
    GENERIC_ERROR_PATTERN = re.compile(
        r"(\w+Error|\w+Exception):\s*(.+)",
        re.MULTILINE
    )

    def parse(self, test_output: str) -> TestLogParseResult:
        """Parse test output and extract failure information.

        Args:
            test_output: Raw test output string

        Returns:
            TestLogParseResult with parsed failures

        Event Codes:
            [TEST_LOG_PARSE_START] - Started parsing
            [TEST_LOG_PARSE_COMPLETE] - Completed parsing
        """
        logger.info("[TEST_LOG_PARSE_START] Parsing test output")

        result = TestLogParseResult(raw_output=test_output)

        # Detect test framework
        result.test_framework = self._detect_framework(test_output)

        # Parse based on framework
        if result.test_framework == "pytest":
            self._parse_pytest(test_output, result)
        elif result.test_framework in ("jest", "mocha", "npm"):
            self._parse_jest(test_output, result)
        else:
            self._parse_generic(test_output, result)

        logger.info(
            f"[TEST_LOG_PARSE_COMPLETE] Found {len(result.failures)} failures "
            f"(framework={result.test_framework})"
        )

        return result

    def _detect_framework(self, output: str) -> str:
        """Detect the test framework from output."""
        output_lower = output.lower()

        if "pytest" in output_lower or "====" in output and ".py::" in output:
            return "pytest"
        elif "jest" in output_lower or "PASS " in output or "FAIL " in output:
            return "jest"
        elif "mocha" in output_lower:
            return "mocha"
        elif "npm test" in output_lower or "npm run test" in output_lower:
            return "npm"
        else:
            return "unknown"

    def _parse_pytest(self, output: str, result: TestLogParseResult) -> None:
        """Parse pytest output."""
        # Find failed tests
        for match in self.PYTEST_FAILED_PATTERN.finditer(output):
            test_name = match.group(1)
            error_summary = match.group(2)

            failure = ParsedTestFailure(
                test_name=test_name,
                error_type=self._classify_error(error_summary),
                error_message=error_summary,
            )

            # Try to extract file path and line number from test name
            if "::" in test_name:
                file_part = test_name.split("::")[0]
                failure.file_path = file_part

            # Look for detailed error in nearby context
            self._enrich_pytest_failure(output, failure)

            result.failures.append(failure)
            logger.debug(f"[TEST_LOG_PARSE_FAILURE] {test_name}: {error_summary}")

        # Parse summary
        summary_match = self.PYTEST_SUMMARY_PATTERN.search(output)
        if summary_match:
            result.failed_tests = int(summary_match.group(1))
            if summary_match.group(2):
                result.passed_tests = int(summary_match.group(2))
            result.total_tests = result.failed_tests + result.passed_tests

    def _enrich_pytest_failure(
        self,
        output: str,
        failure: ParsedTestFailure
    ) -> None:
        """Enrich pytest failure with additional details."""
        # Find traceback
        traceback_match = self.TRACEBACK_PATTERN.search(output)
        if traceback_match:
            failure.traceback = traceback_match.group(1).strip()

        # Find file:line in traceback
        file_line_match = self.PYTEST_FILE_LINE_PATTERN.search(output)
        if file_line_match:
            if not failure.file_path:
                failure.file_path = file_line_match.group(1)
            failure.line_number = int(file_line_match.group(2))

        # Find assertion values
        assertion_match = self.PYTEST_ASSERTION_PATTERN.search(output)
        if assertion_match:
            failure.expected_value = assertion_match.group(2).strip()
            failure.actual_value = assertion_match.group(1).strip()

    def _parse_jest(self, output: str, result: TestLogParseResult) -> None:
        """Parse Jest/npm test output."""
        # Find failed tests
        for match in self.JEST_FAILED_PATTERN.finditer(output):
            test_file = match.group(1)

            failure = ParsedTestFailure(
                test_name=test_file,
                error_type=ErrorType.UNKNOWN,
                error_message="Test failed",
                file_path=test_file,
            )

            # Look for error details
            error_match = self.JEST_ERROR_PATTERN.search(output)
            if error_match:
                failure.error_type = self._classify_error(error_match.group(1))
                failure.error_message = error_match.group(2)

            # Look for expect values
            expect_match = self.JEST_EXPECT_PATTERN.search(output)
            if expect_match:
                failure.expected_value = expect_match.group(1).strip()
                failure.actual_value = expect_match.group(2).strip()
                failure.error_type = ErrorType.ASSERTION

            result.failures.append(failure)
            logger.debug(f"[TEST_LOG_PARSE_FAILURE] {test_file}")

    def _parse_generic(self, output: str, result: TestLogParseResult) -> None:
        """Parse generic test output."""
        # Find any error patterns
        for match in self.GENERIC_ERROR_PATTERN.finditer(output):
            error_type_str = match.group(1)
            error_message = match.group(2)

            failure = ParsedTestFailure(
                test_name="unknown",
                error_type=self._classify_error(error_type_str),
                error_message=error_message,
            )

            # Try to find file:line
            file_line_match = self.PYTEST_FILE_LINE_PATTERN.search(output)
            if file_line_match:
                failure.file_path = file_line_match.group(1)
                failure.line_number = int(file_line_match.group(2))

            result.failures.append(failure)

    def _classify_error(self, error_str: str) -> ErrorType:
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
        elif "error" in error_lower or "exception" in error_lower:
            return ErrorType.RUNTIME
        else:
            return ErrorType.UNKNOWN


# =============================================================================
# Error Analyzer
# =============================================================================

class ErrorAnalyzer:
    """Analyzes test failures and generates fix suggestions.

    Issue #2764: D-4 Self-Correction Loop

    Event Codes (greppable):
        [ERROR_ANALYZE_START] - Started analyzing error
        [ERROR_ANALYZE_COMPLETE] - Completed analysis
        [ERROR_ANALYZE_SUGGESTION] - Generated fix suggestion
    """

    def analyze(
        self,
        failure: ParsedTestFailure,
        file_content: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze a test failure and generate fix suggestions.

        Args:
            failure: Parsed test failure
            file_content: Content of the file where error occurred

        Returns:
            Analysis result with suggestions
        """
        logger.info(
            f"[ERROR_ANALYZE_START] Analyzing {failure.error_type.value} error"
        )

        analysis = {
            "error_type": failure.error_type.value,
            "is_simple_fix": False,
            "fix_strategy": "unknown",
            "suggestions": [],
            "confidence": 0.0,
        }

        if failure.error_type == ErrorType.SYNTAX:
            self._analyze_syntax_error(failure, file_content, analysis)
        elif failure.error_type == ErrorType.ASSERTION:
            self._analyze_assertion_error(failure, file_content, analysis)
        elif failure.error_type == ErrorType.IMPORT:
            self._analyze_import_error(failure, file_content, analysis)
        elif failure.error_type == ErrorType.TYPE:
            self._analyze_type_error(failure, file_content, analysis)
        else:
            self._analyze_runtime_error(failure, file_content, analysis)

        logger.info(
            f"[ERROR_ANALYZE_COMPLETE] Strategy={analysis['fix_strategy']}, "
            f"confidence={analysis['confidence']}"
        )

        return analysis

    def _analyze_syntax_error(
        self,
        failure: ParsedTestFailure,
        file_content: Optional[str],
        analysis: Dict[str, Any]
    ) -> None:
        """Analyze syntax error."""
        analysis["fix_strategy"] = "syntax_fix"
        analysis["is_simple_fix"] = True
        analysis["confidence"] = 0.8

        suggestions = []
        error_msg = failure.error_message.lower()

        if "indent" in error_msg:
            suggestions.append("Check indentation - may need to fix tabs/spaces")
        if "unexpected" in error_msg:
            suggestions.append("Check for missing brackets, parentheses, or colons")
        if "eof" in error_msg:
            suggestions.append("Check for unclosed brackets or strings")

        if failure.line_number:
            suggestions.append(f"Error at line {failure.line_number}")

        analysis["suggestions"] = suggestions
        logger.debug(f"[ERROR_ANALYZE_SUGGESTION] Syntax: {suggestions}")

    def _analyze_assertion_error(
        self,
        failure: ParsedTestFailure,
        file_content: Optional[str],
        analysis: Dict[str, Any]
    ) -> None:
        """Analyze assertion error."""
        analysis["fix_strategy"] = "assertion_fix"

        # Simple assertion fixes have higher confidence
        if failure.expected_value and failure.actual_value:
            analysis["is_simple_fix"] = True
            analysis["confidence"] = 0.7
            analysis["suggestions"] = [
                f"Expected: {failure.expected_value}",
                f"Actual: {failure.actual_value}",
                "Check if the implementation logic is correct",
            ]
        else:
            analysis["is_simple_fix"] = False
            analysis["confidence"] = 0.4
            analysis["suggestions"] = [
                "Review the assertion logic",
                "Check input/output values",
            ]

        logger.debug(f"[ERROR_ANALYZE_SUGGESTION] Assertion: {analysis['suggestions']}")

    def _analyze_import_error(
        self,
        failure: ParsedTestFailure,
        file_content: Optional[str],
        analysis: Dict[str, Any]
    ) -> None:
        """Analyze import error."""
        analysis["fix_strategy"] = "import_fix"
        analysis["is_simple_fix"] = True
        analysis["confidence"] = 0.9

        suggestions = []
        error_msg = failure.error_message

        # Extract module name from error
        module_match = re.search(r"No module named ['\"]?(\w+)['\"]?", error_msg)
        if module_match:
            module_name = module_match.group(1)
            suggestions.append(f"Missing module: {module_name}")
            suggestions.append(f"Check if '{module_name}' is installed or spelled correctly")

        # Check for relative import issues
        if "relative import" in error_msg.lower():
            suggestions.append("Check relative import syntax (use . or ..)")

        analysis["suggestions"] = suggestions
        logger.debug(f"[ERROR_ANALYZE_SUGGESTION] Import: {suggestions}")

    def _analyze_type_error(
        self,
        failure: ParsedTestFailure,
        file_content: Optional[str],
        analysis: Dict[str, Any]
    ) -> None:
        """Analyze type error."""
        analysis["fix_strategy"] = "type_fix"
        analysis["confidence"] = 0.6

        suggestions = []
        error_msg = failure.error_message.lower()

        if "nonetype" in error_msg:
            analysis["is_simple_fix"] = True
            suggestions.append("Check for None values - add null check")
        elif "not callable" in error_msg:
            suggestions.append("Check if the object is callable")
        elif "argument" in error_msg:
            suggestions.append("Check function arguments - wrong type or count")
        else:
            suggestions.append("Check type compatibility")

        analysis["suggestions"] = suggestions
        logger.debug(f"[ERROR_ANALYZE_SUGGESTION] Type: {suggestions}")

    def _analyze_runtime_error(
        self,
        failure: ParsedTestFailure,
        file_content: Optional[str],
        analysis: Dict[str, Any]
    ) -> None:
        """Analyze runtime error."""
        analysis["fix_strategy"] = "runtime_fix"
        analysis["is_simple_fix"] = False
        analysis["confidence"] = 0.3

        suggestions = [
            "Review the error traceback",
            "Check for edge cases in the code",
        ]

        if failure.traceback:
            suggestions.append("Traceback available - analyze call stack")

        analysis["suggestions"] = suggestions
        logger.debug(f"[ERROR_ANALYZE_SUGGESTION] Runtime: {suggestions}")


# =============================================================================
# Self-Correction Loop Controller
# =============================================================================

class SelfCorrectionLoop:
    """Controller for the self-correction loop.

    Issue #2764: D-4 Self-Correction Loop

    This class manages the retry logic for autonomous test failure recovery:
    1. Parse test output to identify failures
    2. Analyze errors to determine fix strategy
    3. Generate fixes using GeneralCoder/SimpleCoder
    4. Retry up to MAX_CORRECTION_ATTEMPTS times
    5. Escalate to Reviewer if all attempts fail

    Event Codes (greppable):
        [SELF_CORRECTION_START] - Started self-correction loop
        [SELF_CORRECTION_ATTEMPT] - Starting an attempt
        [SELF_CORRECTION_SUCCESS] - Correction successful
        [SELF_CORRECTION_FAIL] - Correction failed
        [SELF_CORRECTION_ESCALATE] - Escalating to Reviewer
    """

    def __init__(self, max_attempts: int = MAX_CORRECTION_ATTEMPTS):
        """Initialize SelfCorrectionLoop.

        Args:
            max_attempts: Maximum correction attempts before escalation
        """
        self.max_attempts = max_attempts
        self.parser = TestLogParser()
        self.analyzer = ErrorAnalyzer()
        logger.info(
            f"[SelfCorrectionLoop] Initialized with max_attempts={max_attempts}"
        )

    def attempt_correction(
        self,
        test_output: str,
        files: List[Dict[str, str]],
        run_tests_callback: Optional[callable] = None
    ) -> SelfCorrectionResult:
        """Attempt to correct test failures.

        Args:
            test_output: Raw test output with failures
            files: List of files with "path" and "content" keys
            run_tests_callback: Optional callback to re-run tests after fix

        Returns:
            SelfCorrectionResult with correction outcome

        Event Codes:
            [SELF_CORRECTION_START] - Started correction
            [SELF_CORRECTION_ATTEMPT] - Each attempt
            [SELF_CORRECTION_SUCCESS] - Success
            [SELF_CORRECTION_FAIL] - Failure
            [SELF_CORRECTION_ESCALATE] - Escalation
        """
        logger.info("[SELF_CORRECTION_START] Starting self-correction loop")

        result = SelfCorrectionResult(success=False)

        # Parse test output
        parse_result = self.parser.parse(test_output)

        if not parse_result.failures:
            logger.info("[SELF_CORRECTION_SUCCESS] No failures found in test output")
            result.success = True
            result.feedback = "No test failures detected"
            return result

        # Attempt corrections
        for attempt in range(1, self.max_attempts + 1):
            result.attempts = attempt

            logger.info(
                f"[SELF_CORRECTION_ATTEMPT] Attempt {attempt}/{self.max_attempts}"
            )

            try:
                correction = self._attempt_single_correction(
                    parse_result.failures,
                    files
                )

                if correction:
                    result.corrections_applied.append(correction)

                    # If we have a callback to re-run tests, use it
                    if run_tests_callback:
                        new_output = run_tests_callback(correction)
                        new_parse = self.parser.parse(new_output)

                        if not new_parse.failures:
                            logger.info(
                                f"[SELF_CORRECTION_SUCCESS] Fixed after {attempt} attempts"
                            )
                            result.success = True
                            result.feedback = f"Successfully fixed after {attempt} attempt(s)"
                            return result

                        # Update failures for next attempt
                        parse_result = new_parse
                    else:
                        # Without callback, assume success if we generated a fix
                        logger.info(
                            "[SELF_CORRECTION_SUCCESS] Generated fix (no test callback)"
                        )
                        result.success = True
                        result.feedback = f"Generated fix after {attempt} attempt(s)"
                        return result

            except Exception as e:
                logger.warning(
                    f"[SELF_CORRECTION_FAIL] Attempt {attempt} failed: {e}"
                )
                result.final_error = str(e)

        # All attempts exhausted - escalate
        logger.warning(
            f"[SELF_CORRECTION_ESCALATE] Max attempts ({self.max_attempts}) reached"
        )
        result.escalated = True
        result.feedback = (
            f"Failed to fix after {self.max_attempts} attempts. "
            "Escalating to Reviewer for human intervention."
        )

        return result

    def _attempt_single_correction(
        self,
        failures: List[ParsedTestFailure],
        files: List[Dict[str, str]]
    ) -> Optional[Dict[str, Any]]:
        """Attempt a single correction for the failures.

        Args:
            failures: List of parsed test failures
            files: List of files to potentially fix

        Returns:
            Correction dict if successful, None otherwise
        """
        # Focus on the first failure (most likely the root cause)
        primary_failure = failures[0]

        # Find the relevant file
        file_content = None
        target_file = None
        for f in files:
            if primary_failure.file_path and f["path"].endswith(
                primary_failure.file_path.lstrip("./")
            ):
                file_content = f["content"]
                target_file = f["path"]
                break

        # Analyze the error
        analysis = self.analyzer.analyze(primary_failure, file_content)

        # Only attempt simple fixes
        if not analysis["is_simple_fix"]:
            logger.info(
                "[SELF_CORRECTION_FAIL] Error is not a simple fix, skipping"
            )
            return None

        # Generate fix using coder
        fix = self._generate_fix(
            primary_failure,
            analysis,
            target_file,
            file_content,
            files
        )

        return fix

    def _generate_fix(
        self,
        failure: ParsedTestFailure,
        analysis: Dict[str, Any],
        target_file: Optional[str],
        file_content: Optional[str],
        all_files: List[Dict[str, str]]
    ) -> Optional[Dict[str, Any]]:
        """Generate a fix using the appropriate coder.

        Args:
            failure: The test failure to fix
            analysis: Error analysis result
            target_file: Target file path
            file_content: Target file content
            all_files: All available files

        Returns:
            Fix dict with patches if successful
        """
        try:
            from coder.general_coder import get_general_coder
            from coder.simple_coder import get_simple_coder

            # Build review comment from failure info
            review_comment = self._build_review_comment(failure, analysis)

            # Try GeneralCoder first for multi-file issues
            if len(all_files) > 1:
                coder = get_general_coder()
                result = coder.generate_multi_file_fix(
                    files=all_files,
                    review_comment=review_comment,
                    severity="low"
                )

                if result.status.value == "patch":
                    return {
                        "coder": "general_coder",
                        "patches": [p.to_dict() for p in result.patches],
                        "strategy": analysis["fix_strategy"],
                    }

            # Fall back to SimpleCoder for single file
            if target_file and file_content:
                coder = get_simple_coder()
                result = coder.generate_fix(
                    file_content=file_content,
                    file_path=target_file,
                    review_comment=review_comment,
                    severity="low"
                )

                if result.status.value == "patch":
                    return {
                        "coder": "simple_coder",
                        "patches": [{
                            "file_path": target_file,
                            "patch": result.patch,
                        }],
                        "strategy": analysis["fix_strategy"],
                    }

            logger.info("[SELF_CORRECTION_FAIL] Coders could not generate a fix")
            return None

        except ImportError as e:
            logger.warning(f"[SELF_CORRECTION_FAIL] Coder not available: {e}")
            return None
        except Exception as e:
            logger.error(f"[SELF_CORRECTION_FAIL] Error generating fix: {e}")
            return None

    def _build_review_comment(
        self,
        failure: ParsedTestFailure,
        analysis: Dict[str, Any]
    ) -> str:
        """Build a review comment from failure and analysis.

        Args:
            failure: The test failure
            analysis: Error analysis result

        Returns:
            Review comment string for the coder
        """
        parts = [
            f"Fix test failure: {failure.test_name}",
            f"Error type: {failure.error_type.value}",
            f"Error message: {failure.error_message}",
        ]

        if failure.line_number:
            parts.append(f"Error at line: {failure.line_number}")

        if failure.expected_value and failure.actual_value:
            parts.append(f"Expected: {failure.expected_value}")
            parts.append(f"Actual: {failure.actual_value}")

        if analysis["suggestions"]:
            parts.append("Suggestions:")
            for suggestion in analysis["suggestions"]:
                parts.append(f"  - {suggestion}")

        return "\n".join(parts)


# =============================================================================
# Module-level functions
# =============================================================================

_self_correction_loop: Optional[SelfCorrectionLoop] = None
_loop_lock = __import__("threading").Lock()


def get_self_correction_loop() -> SelfCorrectionLoop:
    """Get or create the singleton SelfCorrectionLoop instance.

    Returns:
        SelfCorrectionLoop instance
    """
    global _self_correction_loop
    if _self_correction_loop is None:
        with _loop_lock:
            if _self_correction_loop is None:
                _self_correction_loop = SelfCorrectionLoop()
    return _self_correction_loop


def parse_test_output(test_output: str) -> TestLogParseResult:
    """Parse test output and extract failure information.

    Convenience function that uses the singleton parser.

    Args:
        test_output: Raw test output string

    Returns:
        TestLogParseResult with parsed failures
    """
    parser = TestLogParser()
    return parser.parse(test_output)


def analyze_test_failure(
    failure: ParsedTestFailure,
    file_content: Optional[str] = None
) -> Dict[str, Any]:
    """Analyze a test failure and generate fix suggestions.

    Convenience function that uses the singleton analyzer.

    Args:
        failure: Parsed test failure
        file_content: Content of the file where error occurred

    Returns:
        Analysis result with suggestions
    """
    analyzer = ErrorAnalyzer()
    return analyzer.analyze(failure, file_content)
