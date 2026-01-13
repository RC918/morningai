"""
Unit tests for D-8 Diagnostic Agent Node.

Tests the DiagnosticAgentNode class and related functions for:
- Root Cause Analysis
- MRE (Minimal Reproducible Example) Generation
- Blast Radius Assessment
- Error categorization

Blueprint Section 3.5: Diagnostic Agent
"""
from diagnostic_agent_node import (
    DiagnosticAgentNode,
    DiagnosticResult,
    RootCauseAnalysis,
    MinimalReproducibleExample,
    BlastRadiusAssessment,
    ErrorCategory,
    BlastRadiusLevel,
    diagnose_error,
)


class TestErrorCategory:
    """Tests for ErrorCategory enum."""

    def test_all_categories_defined(self):
        """Verify all expected error categories are defined."""
        expected = {
            "syntax", "type_mismatch", "null_reference", "import_failure",
            "assertion_failure", "resource_not_found", "permission_denied",
            "timeout", "configuration", "dependency", "logic", "unknown"
        }
        actual = {cat.value for cat in ErrorCategory}
        assert actual == expected


class TestBlastRadiusLevel:
    """Tests for BlastRadiusLevel enum."""

    def test_all_levels_defined(self):
        """Verify all expected blast radius levels are defined."""
        expected = {"isolated", "module", "service", "system"}
        actual = {level.value for level in BlastRadiusLevel}
        assert actual == expected


class TestRootCauseAnalysis:
    """Tests for RootCauseAnalysis dataclass."""

    def test_to_dict(self):
        """Test RootCauseAnalysis.to_dict() serialization."""
        rca = RootCauseAnalysis(
            category=ErrorCategory.SYNTAX,
            description="Syntax error in file",
            confidence=0.9,
            evidence=["Error type: SyntaxError"],
            suggested_fix="Check brackets",
            related_files=["src/main.py"],
        )
        result = rca.to_dict()

        assert result["category"] == "syntax"
        assert result["description"] == "Syntax error in file"
        assert result["confidence"] == 0.9
        assert result["evidence"] == ["Error type: SyntaxError"]
        assert result["suggested_fix"] == "Check brackets"
        assert result["related_files"] == ["src/main.py"]

    def test_default_values(self):
        """Test RootCauseAnalysis default values."""
        rca = RootCauseAnalysis(
            category=ErrorCategory.UNKNOWN,
            description="Unknown error",
        )
        assert rca.confidence == 0.0
        assert rca.evidence == []
        assert rca.suggested_fix is None
        assert rca.related_files == []


class TestMinimalReproducibleExample:
    """Tests for MinimalReproducibleExample dataclass."""

    def test_to_dict(self):
        """Test MinimalReproducibleExample.to_dict() serialization."""
        mre = MinimalReproducibleExample(
            code="def foo(): pass",
            language="python",
            setup_instructions="pip install pytest",
            expected_error="SyntaxError",
            dependencies=["pytest"],
        )
        result = mre.to_dict()

        assert result["code"] == "def foo(): pass"
        assert result["language"] == "python"
        assert result["setup_instructions"] == "pip install pytest"
        assert result["expected_error"] == "SyntaxError"
        assert result["dependencies"] == ["pytest"]

    def test_default_values(self):
        """Test MinimalReproducibleExample default values."""
        mre = MinimalReproducibleExample(code="pass")
        assert mre.language == "python"
        assert mre.setup_instructions is None
        assert mre.expected_error is None
        assert mre.dependencies == []


class TestBlastRadiusAssessment:
    """Tests for BlastRadiusAssessment dataclass."""

    def test_to_dict(self):
        """Test BlastRadiusAssessment.to_dict() serialization."""
        bra = BlastRadiusAssessment(
            level=BlastRadiusLevel.MODULE,
            affected_files=["src/main.py", "src/utils.py"],
            affected_functions=["foo", "bar"],
            affected_tests=["test_foo"],
            description="Module-level impact",
        )
        result = bra.to_dict()

        assert result["level"] == "module"
        assert result["affected_files"] == ["src/main.py", "src/utils.py"]
        assert result["affected_functions"] == ["foo", "bar"]
        assert result["affected_tests"] == ["test_foo"]
        assert result["description"] == "Module-level impact"

    def test_default_values(self):
        """Test BlastRadiusAssessment default values."""
        bra = BlastRadiusAssessment(level=BlastRadiusLevel.ISOLATED)
        assert bra.affected_files == []
        assert bra.affected_functions == []
        assert bra.affected_tests == []
        assert bra.description == ""


class TestDiagnosticResult:
    """Tests for DiagnosticResult dataclass."""

    def test_to_dict_success(self):
        """Test DiagnosticResult.to_dict() with successful diagnosis."""
        result = DiagnosticResult(
            success=True,
            root_cause=RootCauseAnalysis(
                category=ErrorCategory.SYNTAX,
                description="Syntax error",
            ),
            mre=MinimalReproducibleExample(code="pass"),
            blast_radius=BlastRadiusAssessment(level=BlastRadiusLevel.ISOLATED),
            regression_test_suggestion="def test_regression(): pass",
            feedback="Diagnosis complete",
        )
        d = result.to_dict()

        assert d["success"] is True
        assert d["root_cause"]["category"] == "syntax"
        assert d["mre"]["code"] == "pass"
        assert d["blast_radius"]["level"] == "isolated"
        assert d["regression_test_suggestion"] == "def test_regression(): pass"
        assert d["feedback"] == "Diagnosis complete"
        assert "schema_version" in d

    def test_to_dict_failure(self):
        """Test DiagnosticResult.to_dict() with failed diagnosis."""
        result = DiagnosticResult(
            success=False,
            feedback="Diagnosis failed",
        )
        d = result.to_dict()

        assert d["success"] is False
        assert d["root_cause"] is None
        assert d["mre"] is None
        assert d["blast_radius"] is None
        assert d["feedback"] == "Diagnosis failed"

    def test_to_json(self):
        """Test DiagnosticResult.to_json() serialization."""
        result = DiagnosticResult(success=True, feedback="OK")
        json_str = result.to_json()
        assert '"success": true' in json_str or '"success":true' in json_str


class TestDiagnosticAgentNode:
    """Tests for DiagnosticAgentNode class."""

    def test_init_default_values(self):
        """Test DiagnosticAgentNode initialization with defaults."""
        node = DiagnosticAgentNode()
        assert node.enable_llm is True
        assert node.max_mre_lines == 50

    def test_init_custom_values(self):
        """Test DiagnosticAgentNode initialization with custom values."""
        node = DiagnosticAgentNode(enable_llm=False, max_mre_lines=100)
        assert node.enable_llm is False
        assert node.max_mre_lines == 100

    def test_diagnose_syntax_error(self):
        """Test diagnosis of syntax error."""
        node = DiagnosticAgentNode(enable_llm=False)
        result = node.diagnose(
            error_context={
                "error_type": "SyntaxError",
                "error_message": "unexpected EOF while parsing",
                "file_path": "src/main.py",
                "line_number": 10,
            }
        )

        assert result.success is True
        assert result.root_cause is not None
        assert result.root_cause.category == ErrorCategory.SYNTAX
        assert result.mre is not None
        assert result.blast_radius is not None

    def test_diagnose_type_error(self):
        """Test diagnosis of type error."""
        node = DiagnosticAgentNode(enable_llm=False)
        result = node.diagnose(
            error_context={
                "error_type": "TypeError",
                "error_message": "cannot concatenate str and int",
                "file_path": "src/utils.py",
            }
        )

        assert result.success is True
        assert result.root_cause.category == ErrorCategory.TYPE_MISMATCH

    def test_diagnose_null_reference(self):
        """Test diagnosis of null reference error."""
        node = DiagnosticAgentNode(enable_llm=False)
        result = node.diagnose(
            error_context={
                "error_type": "AttributeError",
                "error_message": "'NoneType' object has no attribute 'foo'",
            }
        )

        assert result.success is True
        assert result.root_cause.category == ErrorCategory.NULL_REFERENCE

    def test_diagnose_import_error(self):
        """Test diagnosis of import error."""
        node = DiagnosticAgentNode(enable_llm=False)
        result = node.diagnose(
            error_context={
                "error_type": "ImportError",
                "error_message": "No module named 'nonexistent'",
            }
        )

        assert result.success is True
        assert result.root_cause.category == ErrorCategory.IMPORT_FAILURE
        assert result.blast_radius.level == BlastRadiusLevel.MODULE

    def test_diagnose_assertion_error(self):
        """Test diagnosis of assertion error."""
        node = DiagnosticAgentNode(enable_llm=False)
        result = node.diagnose(
            error_context={
                "error_type": "AssertionError",
                "error_message": "assert 1 == 2",
            }
        )

        assert result.success is True
        assert result.root_cause.category == ErrorCategory.ASSERTION_FAILURE

    def test_diagnose_with_source_contents(self):
        """Test diagnosis with source file contents."""
        node = DiagnosticAgentNode(enable_llm=False)
        source_contents = {
            "src/main.py": "def foo():\n    x = None\n    x.bar()  # Error here\n"
        }
        result = node.diagnose(
            error_context={
                "error_type": "AttributeError",
                "error_message": "'NoneType' object has no attribute 'bar'",
                "file_path": "src/main.py",
                "line_number": 3,
            },
            source_contents=source_contents,
        )

        assert result.success is True
        assert result.mre is not None
        assert "Error here" in result.mre.code or "x.bar()" in result.mre.code

    def test_diagnose_unknown_error(self):
        """Test diagnosis of unknown error type."""
        node = DiagnosticAgentNode(enable_llm=False)
        result = node.diagnose(
            error_context={
                "error_type": "CustomError",
                "error_message": "Something went wrong",
            }
        )

        assert result.success is True
        assert result.root_cause.category == ErrorCategory.UNKNOWN

    def test_diagnose_empty_context(self):
        """Test diagnosis with empty error context."""
        node = DiagnosticAgentNode(enable_llm=False)
        result = node.diagnose(error_context={})

        assert result.success is True
        assert result.root_cause.category == ErrorCategory.UNKNOWN

    def test_categorize_error_patterns(self):
        """Test error categorization for various patterns."""
        node = DiagnosticAgentNode(enable_llm=False)

        test_cases = [
            ("SyntaxError: invalid syntax", ErrorCategory.SYNTAX),
            ("IndentationError: unexpected indent", ErrorCategory.SYNTAX),
            ("TypeError: cannot add str and int", ErrorCategory.TYPE_MISMATCH),
            ("NoneType has no attribute", ErrorCategory.NULL_REFERENCE),
            ("undefined is not a function", ErrorCategory.NULL_REFERENCE),
            ("ModuleNotFoundError: No module named", ErrorCategory.IMPORT_FAILURE),
            ("AssertionError: expected True", ErrorCategory.ASSERTION_FAILURE),
            ("FileNotFoundError: No such file", ErrorCategory.RESOURCE_NOT_FOUND),
            ("PermissionError: Access denied", ErrorCategory.PERMISSION_DENIED),
            ("TimeoutError: timed out", ErrorCategory.TIMEOUT),
            ("ConfigError: missing config", ErrorCategory.CONFIGURATION),
            ("version mismatch", ErrorCategory.DEPENDENCY),
            ("random unknown error", ErrorCategory.UNKNOWN),
        ]

        for error_text, expected_category in test_cases:
            category = node._categorize_error(error_text)
            assert category == expected_category, f"Failed for: {error_text}"

    def test_detect_language(self):
        """Test language detection from file path."""
        node = DiagnosticAgentNode(enable_llm=False)

        test_cases = [
            ("src/main.py", "python"),
            ("src/app.js", "javascript"),
            ("src/app.jsx", "javascript"),
            ("src/app.ts", "typescript"),
            ("src/app.tsx", "typescript"),
            ("src/Main.java", "java"),
            ("src/main.go", "go"),
            ("src/main.rs", "rust"),
            ("src/main.rb", "ruby"),
            ("", "python"),  # Default
            ("unknown.xyz", "python"),  # Unknown extension
        ]

        for file_path, expected_lang in test_cases:
            lang = node._detect_language(file_path)
            assert lang == expected_lang, f"Failed for: {file_path}"

    def test_confidence_calculation(self):
        """Test confidence score calculation."""
        node = DiagnosticAgentNode(enable_llm=False)

        low_confidence = node._calculate_confidence(
            ErrorCategory.UNKNOWN,
            {}
        )
        assert low_confidence == 0.5

        high_confidence = node._calculate_confidence(
            ErrorCategory.SYNTAX,
            {
                "error_type": "SyntaxError",
                "file_path": "src/main.py",
                "line_number": 10,
                "traceback": "Traceback...",
            }
        )
        assert high_confidence > low_confidence
        assert high_confidence <= 1.0

    def test_regression_test_suggestion_python(self):
        """Test regression test suggestion for Python."""
        node = DiagnosticAgentNode(enable_llm=False)
        result = node.diagnose(
            error_context={
                "error_type": "TypeError",
                "error_message": "type error",
                "file_path": "src/utils.py",
            }
        )

        assert result.regression_test_suggestion is not None
        assert "def test_regression" in result.regression_test_suggestion
        assert "utils" in result.regression_test_suggestion

    def test_regression_test_suggestion_javascript(self):
        """Test regression test suggestion for JavaScript."""
        node = DiagnosticAgentNode(enable_llm=False)
        result = node.diagnose(
            error_context={
                "error_type": "TypeError",
                "error_message": "type error",
                "file_path": "src/utils.js",
            }
        )

        assert result.regression_test_suggestion is not None
        assert "describe" in result.regression_test_suggestion
        assert "expect" in result.regression_test_suggestion


class TestDiagnoseErrorFunction:
    """Tests for the diagnose_error convenience function."""

    def test_basic_usage(self):
        """Test basic usage of diagnose_error function."""
        result = diagnose_error(
            error_context={
                "error_type": "SyntaxError",
                "error_message": "invalid syntax",
            },
            enable_llm=False,
        )

        assert isinstance(result, DiagnosticResult)
        assert result.success is True
        assert result.root_cause.category == ErrorCategory.SYNTAX

    def test_with_source_contents(self):
        """Test diagnose_error with source contents."""
        result = diagnose_error(
            error_context={
                "error_type": "TypeError",
                "error_message": "type error",
                "file_path": "src/main.py",
            },
            source_contents={"src/main.py": "x = 1 + 'str'"},
            enable_llm=False,
        )

        assert result.success is True
        assert result.mre is not None


class TestBlastRadiusAssessmentLogic:
    """Tests for blast radius assessment logic."""

    def test_isolated_blast_radius(self):
        """Test isolated blast radius for simple errors."""
        node = DiagnosticAgentNode(enable_llm=False)
        result = node.diagnose(
            error_context={
                "error_type": "SyntaxError",
                "error_message": "syntax error",
                "file_path": "src/isolated.py",
            }
        )

        assert result.blast_radius.level == BlastRadiusLevel.ISOLATED

    def test_module_blast_radius_for_import_error(self):
        """Test module-level blast radius for import errors."""
        node = DiagnosticAgentNode(enable_llm=False)
        result = node.diagnose(
            error_context={
                "error_type": "ImportError",
                "error_message": "No module named 'foo'",
            }
        )

        assert result.blast_radius.level == BlastRadiusLevel.MODULE

    def test_service_blast_radius_for_config_error(self):
        """Test service-level blast radius for config errors."""
        node = DiagnosticAgentNode(enable_llm=False)
        result = node.diagnose(
            error_context={
                "error_type": "ConfigError",
                "error_message": "missing configuration",
            }
        )

        assert result.blast_radius.level == BlastRadiusLevel.SERVICE

    def test_affected_files_from_source_contents(self):
        """Test that affected files are identified from source contents."""
        node = DiagnosticAgentNode(enable_llm=False)
        source_contents = {
            "src/main.py": "from utils import foo",
            "src/utils.py": "def foo(): pass",
            "src/other.py": "import something_else",
        }
        result = node.diagnose(
            error_context={
                "error_type": "ImportError",
                "error_message": "error in utils",
                "file_path": "src/utils.py",
            },
            source_contents=source_contents,
        )

        assert "src/utils.py" in result.blast_radius.affected_files
