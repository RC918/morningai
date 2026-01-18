#!/usr/bin/env python3
"""
Tests for Debugger Agent v2 - EPIC D Phase 5 (P2-medium)

Blueprint Reference: Section 3.3 (Agent Catalog V2) - Debugger Agent
Issue: #4104 (EPIC D P2: Debugger Agent v2 Complete Implementation)

These tests verify:
1. DebuggerAgentV2 initialization and configuration
2. CI output parsing and error classification
3. Fix generation and retry logic
4. Escalation behavior
5. Edge cases and error handling
"""

from unittest.mock import Mock, patch

from debugger_agent.debugger_agent_v2 import (
    DebuggerAgentV2,
    DebugResult,
    DebugAction,
    DebugSeverity,
    ErrorClassification,
    ErrorType,
    FixAttempt,
    get_debugger_agent,
    reset_debugger_agent,
    debug_ci_failure,
    analyze_error,
    MAX_DEBUG_ATTEMPTS,
)


class TestDebuggerAgentV2Initialization:
    """Tests for DebuggerAgentV2 initialization."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_debugger_agent()

    def test_default_initialization(self):
        """Test default initialization values."""
        agent = DebuggerAgentV2()
        assert agent.enabled is True
        assert agent.enable_llm is True
        assert agent.max_attempts == MAX_DEBUG_ATTEMPTS

    def test_custom_initialization(self):
        """Test custom initialization values."""
        agent = DebuggerAgentV2(
            enabled=False,
            enable_llm=False,
            max_attempts=5,
        )
        assert agent.enabled is False
        assert agent.enable_llm is False
        assert agent.max_attempts == 5

    def test_singleton_pattern(self):
        """Test singleton pattern for get_debugger_agent."""
        agent1 = get_debugger_agent()
        agent2 = get_debugger_agent()
        assert agent1 is agent2

    def test_reset_singleton(self):
        """Test reset_debugger_agent clears singleton."""
        agent1 = get_debugger_agent()
        reset_debugger_agent()
        agent2 = get_debugger_agent()
        assert agent1 is not agent2


class TestErrorClassification:
    """Tests for error classification."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_debugger_agent()

    def test_classify_syntax_error(self):
        """Test classification of syntax errors."""
        agent = DebuggerAgentV2()
        error_output = """
FAILED tests/test_foo.py::test_bar - SyntaxError: invalid syntax
  File "src/foo.py", line 10
    def broken(
              ^
SyntaxError: invalid syntax
"""
        result = agent.analyze_error(error_output)
        assert result.error_type == ErrorType.SYNTAX
        assert result.severity == DebugSeverity.CRITICAL
        assert result.is_simple_fix is True

    def test_classify_assertion_error(self):
        """Test classification of assertion errors."""
        agent = DebuggerAgentV2()
        error_output = """
FAILED tests/test_foo.py::test_bar - AssertionError: assert 1 == 2
E       AssertionError: assert 1 == 2
"""
        result = agent.analyze_error(error_output)
        assert result.error_type == ErrorType.ASSERTION
        assert result.severity == DebugSeverity.MEDIUM
        assert result.is_simple_fix is False

    def test_classify_import_error(self):
        """Test classification of import errors."""
        agent = DebuggerAgentV2()
        error_output = """
FAILED tests/test_foo.py::test_bar - ImportError: No module named 'missing_module'
E       ImportError: No module named 'missing_module'
"""
        result = agent.analyze_error(error_output)
        assert result.error_type == ErrorType.IMPORT
        assert result.severity == DebugSeverity.HIGH
        assert result.is_simple_fix is True

    def test_classify_type_error(self):
        """Test classification of type errors."""
        agent = DebuggerAgentV2()
        error_output = """
FAILED tests/test_foo.py::test_bar - TypeError: unsupported operand type(s)
E       TypeError: unsupported operand type(s) for +: 'int' and 'str'
"""
        result = agent.analyze_error(error_output)
        assert result.error_type == ErrorType.TYPE
        assert result.severity == DebugSeverity.HIGH
        assert result.is_simple_fix is True

    def test_classify_runtime_error(self):
        """Test classification of runtime errors."""
        agent = DebuggerAgentV2()
        error_output = """
FAILED tests/test_foo.py::test_bar - RuntimeError: something went wrong
E       RuntimeError: something went wrong
"""
        result = agent.analyze_error(error_output)
        assert result.error_type == ErrorType.RUNTIME
        assert result.severity == DebugSeverity.LOW

    def test_classify_timeout_error(self):
        """Test classification of timeout errors."""
        agent = DebuggerAgentV2()
        error_output = """
FAILED tests/test_foo.py::test_bar - TimeoutError: operation timed out
E       TimeoutError: operation timed out
"""
        result = agent.analyze_error(error_output)
        assert result.error_type == ErrorType.TIMEOUT

    def test_extract_file_and_line(self):
        """Test extraction of file path and line number."""
        agent = DebuggerAgentV2()
        error_output = """
FAILED tests/test_foo.py::test_bar - AssertionError
  File "src/foo.py", line 42
src/foo.py:42: AssertionError
"""
        result = agent.analyze_error(error_output)
        assert result.file_path == "src/foo.py"
        assert result.line_number == 42

    def test_extract_assertion_values(self):
        """Test extraction of expected and actual values."""
        agent = DebuggerAgentV2()
        error_output = """
FAILED tests/test_foo.py::test_bar - AssertionError
E       assert result == expected
E       assert 42 == 100
"""
        result = agent.analyze_error(error_output)
        # The pattern extracts from "assert X == Y"
        assert result.expected_value is not None or result.actual_value is not None


class TestCIOutputParsing:
    """Tests for CI output parsing."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_debugger_agent()

    def test_parse_single_pytest_failure(self):
        """Test parsing single pytest failure."""
        agent = DebuggerAgentV2()
        ci_output = """
============================= test session starts ==============================
FAILED tests/test_foo.py::test_bar - AssertionError: assert 1 == 2
=========================== short test summary info ============================
FAILED tests/test_foo.py::test_bar - AssertionError: assert 1 == 2
============================== 1 failed in 0.5s ================================
"""
        errors = agent._parse_ci_output(ci_output)
        assert len(errors) >= 1
        assert errors[0].test_name == "tests/test_foo.py::test_bar"

    def test_parse_multiple_pytest_failures(self):
        """Test parsing multiple pytest failures."""
        agent = DebuggerAgentV2()
        ci_output = """
FAILED tests/test_foo.py::test_one - AssertionError: assert 1 == 2
FAILED tests/test_foo.py::test_two - TypeError: bad type
FAILED tests/test_bar.py::test_three - ImportError: no module
"""
        errors = agent._parse_ci_output(ci_output)
        assert len(errors) == 3

    def test_parse_no_failures(self):
        """Test parsing output with no failures."""
        agent = DebuggerAgentV2()
        ci_output = """
============================= test session starts ==============================
============================== 5 passed in 0.5s ================================
"""
        errors = agent._parse_ci_output(ci_output)
        assert len(errors) == 0

    def test_parse_generic_error(self):
        """Test parsing generic error output."""
        agent = DebuggerAgentV2()
        ci_output = """
ValueError: invalid value provided
"""
        errors = agent._parse_ci_output(ci_output)
        assert len(errors) >= 1
        assert errors[0].error_type == ErrorType.RUNTIME


class TestDebugCIFailure:
    """Tests for debug_ci_failure method."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_debugger_agent()

    def test_debug_disabled_agent(self):
        """Test debugging with disabled agent."""
        agent = DebuggerAgentV2(enabled=False)
        result = agent.debug_ci_failure("FAILED test - Error")
        assert result.success is False
        assert result.action == DebugAction.NO_ACTION
        assert "disabled" in result.summary.lower()

    def test_debug_empty_output(self):
        """Test debugging with empty output."""
        agent = DebuggerAgentV2()
        result = agent.debug_ci_failure("")
        assert result.success is True
        assert result.action == DebugAction.NO_ACTION

    def test_debug_no_errors(self):
        """Test debugging output with no errors."""
        agent = DebuggerAgentV2()
        result = agent.debug_ci_failure("All tests passed!")
        assert result.success is True
        assert result.action == DebugAction.NO_ACTION

    def test_debug_with_errors_no_callback(self):
        """Test debugging with errors but no test callback."""
        agent = DebuggerAgentV2(enable_llm=False)
        ci_output = """
FAILED tests/test_foo.py::test_bar - ImportError: No module named 'missing'
"""
        files = [{"path": "tests/test_foo.py", "content": "import missing"}]
        result = agent.debug_ci_failure(ci_output, files)

        # Without callback, should suggest fix
        assert result.action in [DebugAction.FIX_SUGGESTED, DebugAction.ESCALATE]
        assert len(result.errors_found) >= 1

    def test_debug_escalation_after_max_attempts(self):
        """Test escalation after max attempts."""
        agent = DebuggerAgentV2(enable_llm=False, max_attempts=2)
        ci_output = """
FAILED tests/test_foo.py::test_bar - RuntimeError: complex error
"""
        files = [{"path": "tests/test_foo.py", "content": "def test_bar(): pass"}]

        # Mock callback that always returns failures
        def always_fail(patches):
            return ci_output

        result = agent.debug_ci_failure(ci_output, files, run_tests_callback=always_fail)

        assert result.escalated is True
        assert result.action == DebugAction.ESCALATE
        assert result.total_attempts == 2

    def test_debug_success_on_first_attempt(self):
        """Test successful fix on first attempt."""
        agent = DebuggerAgentV2(enable_llm=False)
        ci_output = """
FAILED tests/test_foo.py::test_bar - ImportError: No module named 'missing'
"""
        files = [{"path": "tests/test_foo.py", "content": "import missing"}]

        # Mock callback that returns success after fix
        def success_after_fix(patches):
            return "All tests passed!"

        result = agent.debug_ci_failure(ci_output, files, run_tests_callback=success_after_fix)

        assert result.success is True
        assert result.action == DebugAction.FIX_APPLIED
        assert result.total_attempts == 1


class TestFixAttempt:
    """Tests for FixAttempt dataclass."""

    def test_fix_attempt_to_dict(self):
        """Test FixAttempt serialization."""
        attempt = FixAttempt(
            attempt_number=1,
            fix_description="Fixed import error",
            patches=[{"file_path": "foo.py", "patch": "..."}],
            success=True,
        )
        result = attempt.to_dict()
        assert result["attempt_number"] == 1
        assert result["fix_description"] == "Fixed import error"
        assert result["success"] is True
        assert len(result["patches"]) == 1


class TestErrorClassificationDataclass:
    """Tests for ErrorClassification dataclass."""

    def test_error_classification_to_dict(self):
        """Test ErrorClassification serialization."""
        error = ErrorClassification(
            error_type=ErrorType.SYNTAX,
            error_message="invalid syntax",
            file_path="foo.py",
            line_number=10,
            severity=DebugSeverity.CRITICAL,
            is_simple_fix=True,
        )
        result = error.to_dict()
        assert result["error_type"] == "syntax"
        assert result["error_message"] == "invalid syntax"
        assert result["file_path"] == "foo.py"
        assert result["line_number"] == 10
        assert result["severity"] == "critical"
        assert result["is_simple_fix"] is True


class TestDebugResult:
    """Tests for DebugResult dataclass."""

    def test_debug_result_to_dict(self):
        """Test DebugResult serialization."""
        result = DebugResult(
            success=True,
            action=DebugAction.FIX_APPLIED,
            total_attempts=1,
            summary="Fixed successfully",
        )
        result_dict = result.to_dict()
        assert result_dict["success"] is True
        assert result_dict["action"] == "fix_applied"
        assert result_dict["total_attempts"] == 1
        assert result_dict["summary"] == "Fixed successfully"


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_debugger_agent()

    def test_debug_ci_failure_function(self):
        """Test debug_ci_failure convenience function."""
        result = debug_ci_failure("All tests passed!")
        assert isinstance(result, dict)
        assert result["success"] is True
        assert result["action"] == "no_action"

    def test_analyze_error_function(self):
        """Test analyze_error convenience function."""
        result = analyze_error("SyntaxError: invalid syntax")
        assert isinstance(result, dict)
        assert result["error_type"] == "syntax"


class TestEvidenceHash:
    """Tests for evidence hash computation."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_debugger_agent()

    def test_evidence_hash_computed(self):
        """Test that evidence hash is computed."""
        agent = DebuggerAgentV2(enable_llm=False)
        ci_output = """
FAILED tests/test_foo.py::test_bar - ImportError: No module named 'missing'
"""
        files = [{"path": "tests/test_foo.py", "content": "import missing"}]
        result = agent.debug_ci_failure(ci_output, files)

        # Evidence hash should be computed for non-empty results
        if result.fix_attempts:
            assert result.evidence_hash != ""
            assert len(result.evidence_hash) == 16

    def test_evidence_hash_deterministic(self):
        """Test that evidence hash is deterministic."""
        agent = DebuggerAgentV2(enable_llm=False)
        ci_output = """
FAILED tests/test_foo.py::test_bar - ImportError: No module named 'missing'
"""
        files = [{"path": "tests/test_foo.py", "content": "import missing"}]

        result1 = agent.debug_ci_failure(ci_output, files)
        reset_debugger_agent()
        agent2 = DebuggerAgentV2(enable_llm=False)
        result2 = agent2.debug_ci_failure(ci_output, files)

        # Same input should produce same hash
        if result1.evidence_hash and result2.evidence_hash:
            assert result1.evidence_hash == result2.evidence_hash


class TestHeuristicFixes:
    """Tests for heuristic fix generation."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_debugger_agent()

    def test_import_error_suggestion(self):
        """Test import error fix suggestion."""
        agent = DebuggerAgentV2(enable_llm=False)
        error = ErrorClassification(
            error_type=ErrorType.IMPORT,
            error_message="ImportError: No module named 'missing_module'",
            file_path="tests/test_foo.py",
        )
        patches = agent._generate_heuristic_fix(
            error,
            "tests/test_foo.py",
            "import missing_module",
        )
        assert len(patches) >= 1
        assert "missing_module" in str(patches)

    def test_syntax_error_suggestion(self):
        """Test syntax error fix suggestion."""
        agent = DebuggerAgentV2(enable_llm=False)
        error = ErrorClassification(
            error_type=ErrorType.SYNTAX,
            error_message="SyntaxError: invalid syntax",
            file_path="src/foo.py",
            line_number=10,
        )
        patches = agent._generate_heuristic_fix(
            error,
            "src/foo.py",
            "def broken(",
        )
        assert len(patches) >= 1
        assert patches[0]["type"] == "suggestion"


class TestSeverityDetermination:
    """Tests for severity determination."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_debugger_agent()

    def test_syntax_is_critical(self):
        """Test that syntax errors are critical."""
        agent = DebuggerAgentV2()
        severity = agent._determine_severity(ErrorType.SYNTAX)
        assert severity == DebugSeverity.CRITICAL

    def test_import_is_high(self):
        """Test that import errors are high severity."""
        agent = DebuggerAgentV2()
        severity = agent._determine_severity(ErrorType.IMPORT)
        assert severity == DebugSeverity.HIGH

    def test_assertion_is_medium(self):
        """Test that assertion errors are medium severity."""
        agent = DebuggerAgentV2()
        severity = agent._determine_severity(ErrorType.ASSERTION)
        assert severity == DebugSeverity.MEDIUM

    def test_runtime_is_low(self):
        """Test that runtime errors are low severity."""
        agent = DebuggerAgentV2()
        severity = agent._determine_severity(ErrorType.RUNTIME)
        assert severity == DebugSeverity.LOW
