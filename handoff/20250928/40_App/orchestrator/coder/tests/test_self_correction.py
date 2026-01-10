"""
Unit tests for D-4 Self-Correction Loop

Issue #2764: D-4 Self-Correction Loop
Parent EPIC #2759: EPIC D - Autonomous Coder Agent Family

Tests cover:
1. TestLogParser - Parsing pytest/npm test output
2. ErrorAnalyzer - Error classification and analysis
3. SelfCorrectionLoop - Retry logic and escalation
"""
from unittest.mock import patch, MagicMock

from coder.self_correction import (
    TestLogParser,
    ErrorAnalyzer,
    SelfCorrectionLoop,
    ErrorType,
    ParsedTestFailure,
    TestLogParseResult,
    SelfCorrectionResult,
    parse_test_output,
    analyze_test_failure,
    get_self_correction_loop,
    MAX_CORRECTION_ATTEMPTS,
    SELF_CORRECTION_SCHEMA_VERSION,
)


class TestErrorType:
    """Tests for ErrorType enum."""

    def test_error_type_values(self):
        """Test ErrorType enum has expected values."""
        assert ErrorType.SYNTAX.value == "syntax"
        assert ErrorType.ASSERTION.value == "assertion"
        assert ErrorType.IMPORT.value == "import"
        assert ErrorType.TYPE.value == "type"
        assert ErrorType.RUNTIME.value == "runtime"
        assert ErrorType.UNKNOWN.value == "unknown"


class TestParsedTestFailure:
    """Tests for ParsedTestFailure dataclass."""

    def test_basic_failure(self):
        """Test creating a basic test failure."""
        failure = ParsedTestFailure(
            test_name="test_foo.py::test_bar",
            error_type=ErrorType.ASSERTION,
            error_message="assert 1 == 2"
        )
        assert failure.test_name == "test_foo.py::test_bar"
        assert failure.error_type == ErrorType.ASSERTION
        assert failure.error_message == "assert 1 == 2"
        assert failure.file_path is None
        assert failure.line_number is None

    def test_failure_with_details(self):
        """Test creating a failure with all details."""
        failure = ParsedTestFailure(
            test_name="test_foo.py::test_bar",
            error_type=ErrorType.ASSERTION,
            error_message="assert 1 == 2",
            file_path="src/foo.py",
            line_number=42,
            traceback="Traceback...",
            expected_value="2",
            actual_value="1"
        )
        assert failure.file_path == "src/foo.py"
        assert failure.line_number == 42
        assert failure.expected_value == "2"
        assert failure.actual_value == "1"

    def test_to_dict(self):
        """Test converting failure to dictionary."""
        failure = ParsedTestFailure(
            test_name="test_foo",
            error_type=ErrorType.SYNTAX,
            error_message="invalid syntax",
            file_path="foo.py",
            line_number=10
        )
        d = failure.to_dict()
        assert d["test_name"] == "test_foo"
        assert d["error_type"] == "syntax"
        assert d["error_message"] == "invalid syntax"
        assert d["file_path"] == "foo.py"
        assert d["line_number"] == 10


class TestTestLogParseResult:
    """Tests for TestLogParseResult dataclass."""

    def test_empty_result(self):
        """Test empty parse result."""
        result = TestLogParseResult()
        assert result.failures == []
        assert result.total_tests == 0
        assert result.test_framework == "unknown"

    def test_to_dict(self):
        """Test converting result to dictionary."""
        failure = ParsedTestFailure(
            test_name="test_foo",
            error_type=ErrorType.ASSERTION,
            error_message="failed"
        )
        result = TestLogParseResult(
            failures=[failure],
            total_tests=10,
            passed_tests=9,
            failed_tests=1,
            test_framework="pytest"
        )
        d = result.to_dict()
        assert len(d["failures"]) == 1
        assert d["total_tests"] == 10
        assert d["test_framework"] == "pytest"


class TestSelfCorrectionResult:
    """Tests for SelfCorrectionResult dataclass."""

    def test_success_result(self):
        """Test successful correction result."""
        result = SelfCorrectionResult(
            success=True,
            attempts=2,
            feedback="Fixed after 2 attempts"
        )
        assert result.success is True
        assert result.attempts == 2
        assert result.escalated is False

    def test_escalated_result(self):
        """Test escalated correction result."""
        result = SelfCorrectionResult(
            success=False,
            attempts=3,
            escalated=True,
            final_error="Max attempts reached"
        )
        assert result.success is False
        assert result.escalated is True

    def test_to_dict(self):
        """Test converting result to dictionary."""
        result = SelfCorrectionResult(
            success=True,
            attempts=1,
            corrections_applied=[{"coder": "simple_coder"}]
        )
        d = result.to_dict()
        assert d["schema_version"] == SELF_CORRECTION_SCHEMA_VERSION
        assert d["success"] is True
        assert d["attempts"] == 1
        assert len(d["corrections_applied"]) == 1

    def test_to_json(self):
        """Test converting result to JSON."""
        result = SelfCorrectionResult(success=True, attempts=1)
        json_str = result.to_json()
        assert '"success": true' in json_str
        assert '"attempts": 1' in json_str


class TestTestLogParser:
    """Tests for TestLogParser class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = TestLogParser()

    def test_detect_pytest_framework(self):
        """Test detecting pytest framework."""
        output = """
============================= test session starts ==============================
FAILED tests/test_foo.py::test_bar - AssertionError
============================= 1 failed in 0.12s ================================
"""
        result = self.parser.parse(output)
        assert result.test_framework == "pytest"

    def test_detect_jest_framework(self):
        """Test detecting Jest framework."""
        output = """
FAIL src/foo.test.js
  Test suite failed to run
"""
        result = self.parser.parse(output)
        assert result.test_framework == "jest"

    def test_parse_pytest_single_failure(self):
        """Test parsing single pytest failure."""
        output = """
============================= test session starts ==============================
FAILED tests/test_foo.py::test_bar - AssertionError: assert 1 == 2
============================= 1 failed in 0.12s ================================
"""
        result = self.parser.parse(output)
        assert len(result.failures) == 1
        assert result.failures[0].test_name == "tests/test_foo.py::test_bar"
        assert result.failures[0].error_type == ErrorType.ASSERTION

    def test_parse_pytest_multiple_failures(self):
        """Test parsing multiple pytest failures."""
        output = """
FAILED tests/test_foo.py::test_one - AssertionError
FAILED tests/test_bar.py::test_two - TypeError: 'NoneType' object
============================= 2 failed in 0.15s ================================
"""
        result = self.parser.parse(output)
        assert len(result.failures) == 2

    def test_parse_pytest_syntax_error(self):
        """Test parsing pytest syntax error."""
        output = """
FAILED tests/test_foo.py::test_bar - SyntaxError: invalid syntax
"""
        result = self.parser.parse(output)
        assert len(result.failures) == 1
        assert result.failures[0].error_type == ErrorType.SYNTAX

    def test_parse_pytest_import_error(self):
        """Test parsing pytest import error."""
        output = """
FAILED tests/test_foo.py::test_bar - ImportError: No module named 'missing'
"""
        result = self.parser.parse(output)
        assert len(result.failures) == 1
        assert result.failures[0].error_type == ErrorType.IMPORT

    def test_parse_pytest_type_error(self):
        """Test parsing pytest type error."""
        output = """
FAILED tests/test_foo.py::test_bar - TypeError: unsupported operand type
"""
        result = self.parser.parse(output)
        assert len(result.failures) == 1
        assert result.failures[0].error_type == ErrorType.TYPE

    def test_parse_pytest_summary(self):
        """Test parsing pytest summary line."""
        output = """
FAILED tests/test_foo.py::test_bar - AssertionError
============================= 2 failed, 8 passed in 0.50s =====================
"""
        result = self.parser.parse(output)
        assert result.failed_tests == 2
        assert result.passed_tests == 8
        assert result.total_tests == 10

    def test_parse_jest_failure(self):
        """Test parsing Jest failure."""
        output = """
FAIL src/components/Button.test.js
  Button component
    Error: expect(received).toBe(expected)
    Expected: "Click me"
    Received: "Click"
"""
        result = self.parser.parse(output)
        assert len(result.failures) >= 1
        assert result.test_framework == "jest"

    def test_parse_generic_error(self):
        """Test parsing generic error output."""
        output = """
RuntimeError: Something went wrong
  File "foo.py", line 42
"""
        result = self.parser.parse(output)
        assert len(result.failures) >= 1
        assert result.failures[0].error_type == ErrorType.RUNTIME

    def test_parse_empty_output(self):
        """Test parsing empty output."""
        result = self.parser.parse("")
        assert len(result.failures) == 0
        assert result.test_framework == "unknown"

    def test_parse_no_failures(self):
        """Test parsing output with no failures."""
        output = """
============================= test session starts ==============================
============================= 10 passed in 0.50s ===============================
"""
        result = self.parser.parse(output)
        assert len(result.failures) == 0

    def test_extract_file_path_from_test_name(self):
        """Test extracting file path from test name."""
        output = """
FAILED tests/unit/test_foo.py::TestClass::test_method - AssertionError
"""
        result = self.parser.parse(output)
        assert result.failures[0].file_path == "tests/unit/test_foo.py"


class TestErrorAnalyzer:
    """Tests for ErrorAnalyzer class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = ErrorAnalyzer()

    def test_analyze_syntax_error(self):
        """Test analyzing syntax error."""
        failure = ParsedTestFailure(
            test_name="test_foo",
            error_type=ErrorType.SYNTAX,
            error_message="SyntaxError: unexpected indent"
        )
        analysis = self.analyzer.analyze(failure)
        assert analysis["error_type"] == "syntax"
        assert analysis["fix_strategy"] == "syntax_fix"
        assert analysis["is_simple_fix"] is True
        assert analysis["confidence"] > 0.5

    def test_analyze_assertion_error_with_values(self):
        """Test analyzing assertion error with expected/actual values."""
        failure = ParsedTestFailure(
            test_name="test_foo",
            error_type=ErrorType.ASSERTION,
            error_message="AssertionError",
            expected_value="2",
            actual_value="1"
        )
        analysis = self.analyzer.analyze(failure)
        assert analysis["error_type"] == "assertion"
        assert analysis["fix_strategy"] == "assertion_fix"
        assert analysis["is_simple_fix"] is True

    def test_analyze_assertion_error_without_values(self):
        """Test analyzing assertion error without expected/actual values."""
        failure = ParsedTestFailure(
            test_name="test_foo",
            error_type=ErrorType.ASSERTION,
            error_message="AssertionError: complex condition failed"
        )
        analysis = self.analyzer.analyze(failure)
        assert analysis["is_simple_fix"] is False
        assert analysis["confidence"] < 0.5

    def test_analyze_import_error(self):
        """Test analyzing import error."""
        failure = ParsedTestFailure(
            test_name="test_foo",
            error_type=ErrorType.IMPORT,
            error_message="ImportError: No module named 'missing_module'"
        )
        analysis = self.analyzer.analyze(failure)
        assert analysis["error_type"] == "import"
        assert analysis["fix_strategy"] == "import_fix"
        assert analysis["is_simple_fix"] is True
        assert analysis["confidence"] > 0.8

    def test_analyze_type_error_nonetype(self):
        """Test analyzing NoneType error."""
        failure = ParsedTestFailure(
            test_name="test_foo",
            error_type=ErrorType.TYPE,
            error_message="TypeError: 'NoneType' object is not subscriptable"
        )
        analysis = self.analyzer.analyze(failure)
        assert analysis["error_type"] == "type"
        assert analysis["is_simple_fix"] is True
        assert "None" in str(analysis["suggestions"])

    def test_analyze_runtime_error(self):
        """Test analyzing runtime error."""
        failure = ParsedTestFailure(
            test_name="test_foo",
            error_type=ErrorType.RUNTIME,
            error_message="RuntimeError: something went wrong"
        )
        analysis = self.analyzer.analyze(failure)
        assert analysis["error_type"] == "runtime"
        assert analysis["is_simple_fix"] is False
        assert analysis["confidence"] < 0.5

    def test_analyze_unknown_error(self):
        """Test analyzing unknown error."""
        failure = ParsedTestFailure(
            test_name="test_foo",
            error_type=ErrorType.UNKNOWN,
            error_message="Something happened"
        )
        analysis = self.analyzer.analyze(failure)
        assert analysis["error_type"] == "unknown"

    def test_suggestions_for_indent_error(self):
        """Test suggestions for indentation error."""
        failure = ParsedTestFailure(
            test_name="test_foo",
            error_type=ErrorType.SYNTAX,
            error_message="IndentationError: unexpected indent"
        )
        analysis = self.analyzer.analyze(failure)
        suggestions_str = " ".join(analysis["suggestions"])
        assert "indent" in suggestions_str.lower()


class TestSelfCorrectionLoop:
    """Tests for SelfCorrectionLoop class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.loop = SelfCorrectionLoop(max_attempts=3)

    def test_init_default_max_attempts(self):
        """Test default max attempts."""
        loop = SelfCorrectionLoop()
        assert loop.max_attempts == MAX_CORRECTION_ATTEMPTS

    def test_init_custom_max_attempts(self):
        """Test custom max attempts."""
        loop = SelfCorrectionLoop(max_attempts=5)
        assert loop.max_attempts == 5

    def test_no_failures_returns_success(self):
        """Test that no failures returns success."""
        result = self.loop.attempt_correction(
            test_output="===== 10 passed =====",
            files=[]
        )
        assert result.success is True
        assert result.attempts == 0

    def test_escalation_after_max_attempts(self):
        """Test escalation after max attempts."""
        # Mock the internal correction to always fail
        with patch.object(
            self.loop, '_attempt_single_correction', return_value=None
        ):
            result = self.loop.attempt_correction(
                test_output="FAILED test_foo.py::test_bar - AssertionError",
                files=[{"path": "foo.py", "content": "def foo(): pass"}]
            )
            assert result.success is False
            assert result.escalated is True
            assert result.attempts == 3

    def test_unverified_fix_without_callback(self):
        """Test that fix without callback returns success=False (unverified)."""
        mock_correction = {
            "coder": "simple_coder",
            "patches": [{"file_path": "foo.py", "patch": "fixed"}],
            "strategy": "syntax_fix"
        }
        with patch.object(
            self.loop, '_attempt_single_correction', return_value=mock_correction
        ):
            result = self.loop.attempt_correction(
                test_output="FAILED test_foo.py::test_bar - SyntaxError",
                files=[{"path": "foo.py", "content": "def foo( pass"}]
            )
            # Without callback, fix is unverified so success=False
            assert result.success is False
            assert result.attempts == 1
            assert len(result.corrections_applied) == 1
            assert "unverified" in result.feedback.lower()

    def test_success_on_second_attempt(self):
        """Test success on second attempt with callback."""
        call_count = [0]

        def mock_run_tests(correction):
            call_count[0] += 1
            if call_count[0] >= 2:
                return "===== 10 passed ====="
            return "FAILED test_foo.py::test_bar - AssertionError"

        mock_correction = {
            "coder": "simple_coder",
            "patches": [{"file_path": "foo.py", "patch": "fixed"}],
            "strategy": "assertion_fix"
        }
        with patch.object(
            self.loop, '_attempt_single_correction', return_value=mock_correction
        ):
            result = self.loop.attempt_correction(
                test_output="FAILED test_foo.py::test_bar - AssertionError",
                files=[{"path": "foo.py", "content": "def foo(): pass"}],
                run_tests_callback=mock_run_tests
            )
            assert result.success is True
            assert result.attempts == 2

    def test_build_review_comment(self):
        """Test building review comment from failure."""
        failure = ParsedTestFailure(
            test_name="test_foo.py::test_bar",
            error_type=ErrorType.ASSERTION,
            error_message="assert 1 == 2",
            line_number=42,
            expected_value="2",
            actual_value="1"
        )
        analysis = {"suggestions": ["Check the logic"]}
        comment = self.loop._build_review_comment(failure, analysis)
        assert "test_foo.py::test_bar" in comment
        assert "assertion" in comment
        assert "line: 42" in comment.lower()
        assert "Expected: 2" in comment
        assert "Actual: 1" in comment

    @patch('coder.general_coder.get_general_coder')
    @patch('coder.simple_coder.get_simple_coder')
    def test_generate_fix_with_general_coder(
        self, mock_get_simple, mock_get_general
    ):
        """Test generating fix with GeneralCoder for multi-file."""
        mock_coder = MagicMock()
        mock_result = MagicMock()
        mock_result.status.value = "patch"
        mock_result.patches = [MagicMock(to_dict=lambda: {"file_path": "a.py", "patch": "fixed"})]
        mock_coder.generate_multi_file_fix.return_value = mock_result
        mock_get_general.return_value = mock_coder

        failure = ParsedTestFailure(
            test_name="test_foo",
            error_type=ErrorType.SYNTAX,
            error_message="SyntaxError"
        )
        analysis = {"fix_strategy": "syntax_fix", "suggestions": []}

        fix = self.loop._generate_fix(
            failure, analysis, "a.py", "content",
            [{"path": "a.py", "content": "..."}, {"path": "b.py", "content": "..."}]
        )
        assert fix is not None
        assert fix["coder"] == "general_coder"

    @patch('coder.general_coder.get_general_coder')
    @patch('coder.simple_coder.get_simple_coder')
    def test_generate_fix_with_simple_coder(
        self, mock_get_simple, mock_get_general
    ):
        """Test generating fix with SimpleCoder for single file."""
        mock_coder = MagicMock()
        mock_result = MagicMock()
        mock_result.status.value = "patch"
        mock_result.patch = "fixed content"
        mock_coder.generate_fix.return_value = mock_result
        mock_get_simple.return_value = mock_coder

        failure = ParsedTestFailure(
            test_name="test_foo",
            error_type=ErrorType.SYNTAX,
            error_message="SyntaxError"
        )
        analysis = {"fix_strategy": "syntax_fix", "suggestions": []}

        fix = self.loop._generate_fix(
            failure, analysis, "a.py", "content",
            [{"path": "a.py", "content": "content"}]
        )
        assert fix is not None
        assert fix["coder"] == "simple_coder"

    def test_generate_fix_import_error(self):
        """Test that ImportError in coder is handled gracefully."""
        with patch.dict('sys.modules', {'coder.general_coder': None}):
            failure = ParsedTestFailure(
                test_name="test_foo",
                error_type=ErrorType.SYNTAX,
                error_message="SyntaxError"
            )
            analysis = {"fix_strategy": "syntax_fix", "suggestions": []}

            fix = self.loop._generate_fix(
                failure, analysis, "a.py", "content",
                [{"path": "a.py", "content": "content"}, {"path": "b.py", "content": "..."}]
            )
            assert fix is None


class TestModuleFunctions:
    """Tests for module-level convenience functions."""

    def test_parse_test_output(self):
        """Test parse_test_output convenience function."""
        output = "FAILED test_foo.py::test_bar - AssertionError"
        result = parse_test_output(output)
        assert isinstance(result, TestLogParseResult)
        assert len(result.failures) == 1

    def test_analyze_test_failure(self):
        """Test analyze_test_failure convenience function."""
        failure = ParsedTestFailure(
            test_name="test_foo",
            error_type=ErrorType.SYNTAX,
            error_message="SyntaxError"
        )
        analysis = analyze_test_failure(failure)
        assert "error_type" in analysis
        assert "fix_strategy" in analysis

    def test_get_self_correction_loop_singleton(self):
        """Test get_self_correction_loop returns singleton."""
        loop1 = get_self_correction_loop()
        loop2 = get_self_correction_loop()
        assert loop1 is loop2


class TestIntegration:
    """Integration tests for the full self-correction flow."""

    def test_full_flow_syntax_error(self):
        """Test full flow with syntax error."""
        parser = TestLogParser()
        analyzer = ErrorAnalyzer()

        output = """
FAILED tests/test_foo.py::test_bar - SyntaxError: invalid syntax
  File "src/foo.py", line 10
"""
        parse_result = parser.parse(output)
        assert len(parse_result.failures) == 1

        failure = parse_result.failures[0]
        analysis = analyzer.analyze(failure)
        assert analysis["is_simple_fix"] is True
        assert analysis["fix_strategy"] == "syntax_fix"

    def test_full_flow_assertion_error(self):
        """Test full flow with assertion error."""
        parser = TestLogParser()
        analyzer = ErrorAnalyzer()

        output = """
FAILED tests/test_calc.py::test_add - AssertionError: assert 3 == 4
E       assert add(1, 2) == 4
"""
        parse_result = parser.parse(output)
        failure = parse_result.failures[0]
        analysis = analyzer.analyze(failure)
        assert analysis["fix_strategy"] == "assertion_fix"

    def test_full_flow_import_error(self):
        """Test full flow with import error."""
        parser = TestLogParser()
        analyzer = ErrorAnalyzer()

        output = """
FAILED tests/test_app.py::test_main - ImportError: No module named 'missing_lib'
"""
        parse_result = parser.parse(output)
        failure = parse_result.failures[0]
        analysis = analyzer.analyze(failure)
        assert analysis["is_simple_fix"] is True
        assert "missing" in str(analysis["suggestions"]).lower()
