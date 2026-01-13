"""
D-8: Diagnostic Agent - Error Diagnosis, MRE Generation, and Root Cause Analysis

Issue: D-8 Debugger Integration + Diagnostic Agent
Parent EPIC #2759: EPIC D - Autonomous Coder Agent Family
Blueprint Section 3.5: Diagnostic Agent

This module implements the Diagnostic Agent for error diagnosis and analysis:
1. Root Cause Analysis - Identifies the underlying cause of errors
2. MRE Generation - Creates Minimal Reproducible Examples
3. Blast Radius Assessment - Evaluates the impact scope of errors
4. Integration with Test Agent v2 for regression test generation

Workflow:
    Error → DiagnosticAgent → RootCauseAnalysis + MRE → Test Agent v2 → Regression Test

Usage:
    from diagnostic_agent_node import DiagnosticAgentNode, diagnose_error

    node = DiagnosticAgentNode()
    result = node.diagnose(
        error_context={
            "error_type": "TypeError",
            "error_message": "Cannot read property 'x' of undefined",
            "file_path": "src/utils.py",
            "line_number": 42,
            "traceback": "...",
        },
        source_contents={"src/utils.py": "def foo(): ..."},
    )

    if result.root_cause:
        print(f"Root cause: {result.root_cause.description}")
    if result.mre:
        print(f"MRE: {result.mre.code}")

Event Codes (greppable):
    [DIAGNOSTIC_AGENT_START] - Started diagnosis
    [DIAGNOSTIC_AGENT_COMPLETE] - Completed diagnosis
    [DIAGNOSTIC_AGENT_ROOT_CAUSE] - Root cause identified
    [DIAGNOSTIC_AGENT_MRE_GENERATED] - MRE generated
    [DIAGNOSTIC_AGENT_BLAST_RADIUS] - Blast radius assessed
    [DIAGNOSTIC_AGENT_ERROR] - Error during diagnosis
    [DIAGNOSTIC_AGENT_SKIP] - Skipped (feature flag disabled)
"""
import json
import logging
import os
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


DIAGNOSTIC_AGENT_SCHEMA_VERSION = 1


class ErrorCategory(Enum):
    """High-level error categories for diagnosis.

    Blueprint Section 3.5: Diagnostic Agent categorizes errors for targeted analysis.
    """
    SYNTAX = "syntax"
    TYPE_MISMATCH = "type_mismatch"
    NULL_REFERENCE = "null_reference"
    IMPORT_FAILURE = "import_failure"
    ASSERTION_FAILURE = "assertion_failure"
    RESOURCE_NOT_FOUND = "resource_not_found"
    PERMISSION_DENIED = "permission_denied"
    TIMEOUT = "timeout"
    CONFIGURATION = "configuration"
    DEPENDENCY = "dependency"
    LOGIC = "logic"
    UNKNOWN = "unknown"


class BlastRadiusLevel(Enum):
    """Blast radius severity levels.

    Blueprint Section 3.5: Blast Radius Assessment evaluates impact scope.
    """
    ISOLATED = "isolated"
    MODULE = "module"
    SERVICE = "service"
    SYSTEM = "system"


@dataclass
class RootCauseAnalysis:
    """Result of root cause analysis.

    Attributes:
        category: High-level error category
        description: Human-readable description of the root cause
        confidence: Confidence score (0.0 to 1.0)
        evidence: Supporting evidence for the analysis
        suggested_fix: Suggested fix strategy
        related_files: Files related to the root cause
    """
    category: ErrorCategory
    description: str
    confidence: float = 0.0
    evidence: List[str] = field(default_factory=list)
    suggested_fix: Optional[str] = None
    related_files: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "category": self.category.value,
            "description": self.description,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "suggested_fix": self.suggested_fix,
            "related_files": self.related_files,
        }


@dataclass
class MinimalReproducibleExample:
    """Minimal Reproducible Example (MRE) for an error.

    Blueprint Section 3.5: MRE Generation creates simplified code that reproduces errors.

    Attributes:
        code: The minimal code that reproduces the error
        language: Programming language of the code
        setup_instructions: Instructions to set up the environment
        expected_error: The expected error message
        dependencies: Required dependencies
    """
    code: str
    language: str = "python"
    setup_instructions: Optional[str] = None
    expected_error: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "code": self.code,
            "language": language_to_str(self.language),
            "setup_instructions": self.setup_instructions,
            "expected_error": self.expected_error,
            "dependencies": self.dependencies,
        }


def language_to_str(lang: str) -> str:
    """Convert language to string representation."""
    return lang if isinstance(lang, str) else str(lang)


@dataclass
class BlastRadiusAssessment:
    """Assessment of error blast radius.

    Blueprint Section 3.5: Blast Radius Assessment evaluates impact scope.

    Attributes:
        level: Severity level of the blast radius
        affected_files: List of files potentially affected
        affected_functions: List of functions potentially affected
        affected_tests: List of tests that may fail
        description: Human-readable description of the impact
    """
    level: BlastRadiusLevel
    affected_files: List[str] = field(default_factory=list)
    affected_functions: List[str] = field(default_factory=list)
    affected_tests: List[str] = field(default_factory=list)
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "level": self.level.value,
            "affected_files": self.affected_files,
            "affected_functions": self.affected_functions,
            "affected_tests": self.affected_tests,
            "description": self.description,
        }


@dataclass
class DiagnosticResult:
    """Complete result of diagnostic analysis.

    Attributes:
        success: Whether diagnosis was successful
        root_cause: Root cause analysis result
        mre: Minimal reproducible example
        blast_radius: Blast radius assessment
        regression_test_suggestion: Suggested regression test code
        feedback: Human-readable feedback
    """
    success: bool
    root_cause: Optional[RootCauseAnalysis] = None
    mre: Optional[MinimalReproducibleExample] = None
    blast_radius: Optional[BlastRadiusAssessment] = None
    regression_test_suggestion: Optional[str] = None
    feedback: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "schema_version": DIAGNOSTIC_AGENT_SCHEMA_VERSION,
            "success": self.success,
            "root_cause": self.root_cause.to_dict() if self.root_cause else None,
            "mre": self.mre.to_dict() if self.mre else None,
            "blast_radius": self.blast_radius.to_dict() if self.blast_radius else None,
            "regression_test_suggestion": self.regression_test_suggestion,
            "feedback": self.feedback,
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


class DiagnosticAgentNode:
    """Diagnostic Agent for error diagnosis and analysis.

    Blueprint Section 3.5: Diagnostic Agent provides:
    - Error Reproduction: Reproduce errors in isolated environment
    - MRE Generation: Generate Minimal Reproducible Examples
    - Root Cause Analysis: Identify error root causes
    - Blast Radius Assessment: Evaluate impact scope

    Event Codes:
        [DIAGNOSTIC_AGENT_START] - Started diagnosis
        [DIAGNOSTIC_AGENT_COMPLETE] - Completed diagnosis
        [DIAGNOSTIC_AGENT_ERROR] - Error during diagnosis
    """

    ERROR_PATTERNS = {
        ErrorCategory.SYNTAX: [
            r"SyntaxError",
            r"IndentationError",
            r"TabError",
            r"unexpected token",
            r"parsing error",
        ],
        ErrorCategory.TYPE_MISMATCH: [
            r"TypeError",
            r"type mismatch",
            r"expected .+ but got",
            r"cannot convert",
        ],
        ErrorCategory.NULL_REFERENCE: [
            r"NoneType",
            r"undefined",
            r"null",
            r"AttributeError.*None",
            r"Cannot read propert",
        ],
        ErrorCategory.IMPORT_FAILURE: [
            r"ImportError",
            r"ModuleNotFoundError",
            r"No module named",
            r"Cannot find module",
        ],
        ErrorCategory.ASSERTION_FAILURE: [
            r"AssertionError",
            r"assert",
            r"expect.*to",
            r"should.*be",
        ],
        ErrorCategory.RESOURCE_NOT_FOUND: [
            r"FileNotFoundError",
            r"ENOENT",
            r"No such file",
            r"(?:file|path|resource|directory).*not found|not found.*(?:file|path|resource|directory)",
            r"(?:file|path|directory).*(?:does not|doesn't) exist",
            r"(?:file|path|resource|directory).*(?:was not|wasn't) found",
            r"(?:file|path|resource|directory).*(?:is )?missing",
            r"(?:file|path|resource|directory).*unavailable",
        ],
        ErrorCategory.PERMISSION_DENIED: [
            r"PermissionError",
            r"EACCES",
            r"Permission denied",
            r"Access denied",
        ],
        ErrorCategory.TIMEOUT: [
            r"TimeoutError",
            r"timed out",
            r"deadline exceeded",
        ],
        ErrorCategory.CONFIGURATION: [
            r"ConfigError",
            r"configuration",
            r"missing.*config",
            r"invalid.*setting",
        ],
        ErrorCategory.DEPENDENCY: [
            r"DependencyError",
            r"version.*mismatch",
            r"incompatible",
            r"requires.*version",
        ],
    }

    def __init__(
        self,
        enable_llm: bool = True,
        max_mre_lines: int = 50,
    ):
        """Initialize DiagnosticAgentNode.

        Args:
            enable_llm: Whether to use LLM for enhanced analysis
            max_mre_lines: Maximum lines in generated MRE
        """
        self.enable_llm = enable_llm
        self.max_mre_lines = max_mre_lines
        self._llm_client = None

    def _get_llm_client(self):
        """Lazy load LLM client."""
        if self._llm_client is None and self.enable_llm:
            try:
                from llm.client import LLMClient
                self._llm_client = LLMClient()
            except ImportError:
                logger.warning(
                    "[DIAGNOSTIC_AGENT_ERROR] LLM client not available, "
                    "falling back to pattern-based analysis"
                )
                self.enable_llm = False
        return self._llm_client

    def diagnose(
        self,
        error_context: Dict[str, Any],
        source_contents: Optional[Dict[str, str]] = None,
        test_output: Optional[str] = None,
    ) -> DiagnosticResult:
        """Perform comprehensive error diagnosis.

        Args:
            error_context: Error information including:
                - error_type: Type of error (e.g., "TypeError")
                - error_message: Error message
                - file_path: File where error occurred
                - line_number: Line number of error
                - traceback: Full traceback (optional)
            source_contents: Dict mapping file paths to their contents
            test_output: Raw test output (optional)

        Returns:
            DiagnosticResult with root cause, MRE, and blast radius

        Event Codes:
            [DIAGNOSTIC_AGENT_START] - Started diagnosis
            [DIAGNOSTIC_AGENT_COMPLETE] - Completed diagnosis
        """
        logger.info(
            f"[DIAGNOSTIC_AGENT_START] Diagnosing error: "
            f"{error_context.get('error_type', 'unknown')}"
        )

        try:
            root_cause = self._analyze_root_cause(error_context, source_contents)

            mre = self._generate_mre(error_context, source_contents, root_cause)

            blast_radius = self._assess_blast_radius(
                error_context, source_contents, root_cause
            )

            regression_test = self._suggest_regression_test(
                error_context, root_cause, mre
            )

            result = DiagnosticResult(
                success=True,
                root_cause=root_cause,
                mre=mre,
                blast_radius=blast_radius,
                regression_test_suggestion=regression_test,
                feedback=self._generate_feedback(root_cause, blast_radius),
            )

            logger.info(
                f"[DIAGNOSTIC_AGENT_COMPLETE] Diagnosis complete: "
                f"category={root_cause.category.value}, "
                f"confidence={root_cause.confidence:.2f}"
            )

            return result

        except Exception as e:
            logger.error(f"[DIAGNOSTIC_AGENT_ERROR] Diagnosis failed: {e}")
            return DiagnosticResult(
                success=False,
                feedback=f"Diagnosis failed: {str(e)}",
            )

    def _analyze_root_cause(
        self,
        error_context: Dict[str, Any],
        source_contents: Optional[Dict[str, str]],
    ) -> RootCauseAnalysis:
        """Analyze the root cause of an error.

        Event Codes:
            [DIAGNOSTIC_AGENT_ROOT_CAUSE] - Root cause identified
        """
        error_type = error_context.get("error_type", "")
        error_message = error_context.get("error_message", "")
        traceback = error_context.get("traceback", "")
        file_path = error_context.get("file_path", "")

        combined_text = f"{error_type} {error_message} {traceback}"

        category = self._categorize_error(combined_text)

        evidence = []
        if error_type:
            evidence.append(f"Error type: {error_type}")
        if error_message:
            evidence.append(f"Error message: {error_message}")
        if file_path:
            evidence.append(f"File: {file_path}")

        description = self._generate_root_cause_description(
            category, error_context, source_contents
        )

        suggested_fix = self._suggest_fix_strategy(
            category, error_context, source_contents
        )

        related_files = self._find_related_files(
            error_context, source_contents
        )

        confidence = self._calculate_confidence(category, error_context)

        root_cause = RootCauseAnalysis(
            category=category,
            description=description,
            confidence=confidence,
            evidence=evidence,
            suggested_fix=suggested_fix,
            related_files=related_files,
        )

        logger.info(
            f"[DIAGNOSTIC_AGENT_ROOT_CAUSE] Identified: {category.value} "
            f"(confidence={confidence:.2f})"
        )

        return root_cause

    def _categorize_error(self, text: str) -> ErrorCategory:
        """Categorize error based on patterns."""
        for category, patterns in self.ERROR_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return category

        return ErrorCategory.UNKNOWN

    def _generate_root_cause_description(
        self,
        category: ErrorCategory,
        error_context: Dict[str, Any],
        source_contents: Optional[Dict[str, str]],
    ) -> str:
        """Generate human-readable root cause description."""
        error_type = error_context.get("error_type", "Unknown error")
        error_message = error_context.get("error_message", "")
        file_path = error_context.get("file_path", "")
        line_number = error_context.get("line_number")

        location = ""
        if file_path:
            location = f" in {file_path}"
            if line_number:
                location += f" at line {line_number}"

        descriptions = {
            ErrorCategory.SYNTAX: (
                f"Syntax error{location}. The code contains invalid syntax that "
                f"prevents parsing. Check for missing brackets, quotes, or colons."
            ),
            ErrorCategory.TYPE_MISMATCH: (
                f"Type mismatch{location}. An operation received an unexpected type. "
                f"Verify that variables have the expected types before operations."
            ),
            ErrorCategory.NULL_REFERENCE: (
                f"Null/None reference{location}. Code attempted to access an attribute "
                f"or method on a None/null value. Add null checks before access."
            ),
            ErrorCategory.IMPORT_FAILURE: (
                f"Import failure{location}. A required module could not be imported. "
                f"Check that the module is installed and the import path is correct."
            ),
            ErrorCategory.ASSERTION_FAILURE: (
                f"Assertion failure{location}. A test assertion did not pass. "
                f"The actual value differs from the expected value."
            ),
            ErrorCategory.RESOURCE_NOT_FOUND: (
                f"Resource not found{location}. A required file or resource is missing. "
                f"Verify the path exists and is accessible."
            ),
            ErrorCategory.PERMISSION_DENIED: (
                f"Permission denied{location}. Insufficient permissions to access "
                f"a resource. Check file/directory permissions."
            ),
            ErrorCategory.TIMEOUT: (
                f"Timeout{location}. An operation exceeded its time limit. "
                f"Consider increasing timeout or optimizing the operation."
            ),
            ErrorCategory.CONFIGURATION: (
                f"Configuration error{location}. Invalid or missing configuration. "
                f"Check environment variables and config files."
            ),
            ErrorCategory.DEPENDENCY: (
                f"Dependency error{location}. A dependency version conflict or "
                f"missing dependency. Check package versions."
            ),
            ErrorCategory.LOGIC: (
                f"Logic error{location}. The code logic produces incorrect results. "
                f"Review the algorithm and edge cases."
            ),
            ErrorCategory.UNKNOWN: (
                f"Unknown error{location}: {error_type}. {error_message}"
            ),
        }

        return descriptions.get(category, descriptions[ErrorCategory.UNKNOWN])

    def _suggest_fix_strategy(
        self,
        category: ErrorCategory,
        error_context: Dict[str, Any],
        source_contents: Optional[Dict[str, str]],
    ) -> str:
        """Suggest a fix strategy based on error category."""
        strategies = {
            ErrorCategory.SYNTAX: (
                "1. Check for missing or extra brackets, parentheses, or braces\n"
                "2. Verify proper indentation\n"
                "3. Check for missing colons after if/for/def/class statements\n"
                "4. Ensure strings are properly quoted"
            ),
            ErrorCategory.TYPE_MISMATCH: (
                "1. Add type checking before operations\n"
                "2. Use type conversion functions (int(), str(), etc.)\n"
                "3. Add type hints and validate inputs\n"
                "4. Check function return types"
            ),
            ErrorCategory.NULL_REFERENCE: (
                "1. Add null/None checks before accessing attributes\n"
                "2. Use optional chaining or getattr with defaults\n"
                "3. Initialize variables before use\n"
                "4. Check function return values for None"
            ),
            ErrorCategory.IMPORT_FAILURE: (
                "1. Verify the module is installed (pip install / npm install)\n"
                "2. Check the import path is correct\n"
                "3. Ensure __init__.py exists for packages\n"
                "4. Check for circular imports"
            ),
            ErrorCategory.ASSERTION_FAILURE: (
                "1. Review expected vs actual values\n"
                "2. Check test data and fixtures\n"
                "3. Verify the implementation logic\n"
                "4. Update test if requirements changed"
            ),
            ErrorCategory.RESOURCE_NOT_FOUND: (
                "1. Verify the file/resource path exists\n"
                "2. Check for typos in the path\n"
                "3. Ensure the resource is created before access\n"
                "4. Use absolute paths or proper path resolution"
            ),
            ErrorCategory.PERMISSION_DENIED: (
                "1. Check file/directory permissions\n"
                "2. Run with appropriate privileges\n"
                "3. Verify the user has access to the resource\n"
                "4. Check for file locks"
            ),
            ErrorCategory.TIMEOUT: (
                "1. Increase timeout value\n"
                "2. Optimize the slow operation\n"
                "3. Add caching for expensive operations\n"
                "4. Consider async/parallel execution"
            ),
            ErrorCategory.CONFIGURATION: (
                "1. Check environment variables are set\n"
                "2. Verify config file exists and is valid\n"
                "3. Check for typos in config keys\n"
                "4. Use default values for optional configs"
            ),
            ErrorCategory.DEPENDENCY: (
                "1. Update dependencies to compatible versions\n"
                "2. Check for version conflicts\n"
                "3. Use a lock file (package-lock.json, poetry.lock)\n"
                "4. Consider using virtual environments"
            ),
            ErrorCategory.LOGIC: (
                "1. Add debug logging to trace execution\n"
                "2. Write unit tests for edge cases\n"
                "3. Review the algorithm step by step\n"
                "4. Check boundary conditions"
            ),
            ErrorCategory.UNKNOWN: (
                "1. Review the full error traceback\n"
                "2. Search for the error message online\n"
                "3. Add logging to narrow down the issue\n"
                "4. Try to reproduce in isolation"
            ),
        }

        return strategies.get(category, strategies[ErrorCategory.UNKNOWN])

    def _find_related_files(
        self,
        error_context: Dict[str, Any],
        source_contents: Optional[Dict[str, str]],
    ) -> List[str]:
        """Find files related to the error."""
        related = []

        file_path = error_context.get("file_path")
        if file_path:
            related.append(file_path)

        traceback = error_context.get("traceback", "")
        file_pattern = re.compile(r'File "([^"]+)"')
        for match in file_pattern.finditer(traceback):
            path = match.group(1)
            if path not in related and not path.startswith("<"):
                related.append(path)

        return related[:10]

    def _calculate_confidence(
        self,
        category: ErrorCategory,
        error_context: Dict[str, Any],
    ) -> float:
        """Calculate confidence score for the diagnosis."""
        confidence = 0.5

        if category != ErrorCategory.UNKNOWN:
            confidence += 0.2

        if error_context.get("error_type"):
            confidence += 0.1

        if error_context.get("file_path"):
            confidence += 0.1

        if error_context.get("line_number"):
            confidence += 0.05

        if error_context.get("traceback"):
            confidence += 0.05

        return min(confidence, 1.0)

    def _generate_mre(
        self,
        error_context: Dict[str, Any],
        source_contents: Optional[Dict[str, str]],
        root_cause: RootCauseAnalysis,
    ) -> Optional[MinimalReproducibleExample]:
        """Generate a Minimal Reproducible Example.

        Event Codes:
            [DIAGNOSTIC_AGENT_MRE_GENERATED] - MRE generated
        """
        file_path = error_context.get("file_path", "")
        line_number = error_context.get("line_number")
        error_message = error_context.get("error_message", "")

        language = self._detect_language(file_path)

        source_code = None
        if source_contents and file_path in source_contents:
            source_code = source_contents[file_path]

        if source_code and line_number:
            mre_code = self._extract_relevant_code(
                source_code, line_number, self.max_mre_lines
            )
        else:
            mre_code = self._generate_template_mre(root_cause.category, language)

        mre = MinimalReproducibleExample(
            code=mre_code,
            language=language,
            setup_instructions=self._generate_setup_instructions(root_cause.category),
            expected_error=error_message,
            dependencies=self._extract_dependencies(source_code) if source_code else [],
        )

        logger.info(
            f"[DIAGNOSTIC_AGENT_MRE_GENERATED] Generated MRE "
            f"({len(mre_code.splitlines())} lines)"
        )

        return mre

    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file path."""
        if not file_path:
            return "python"

        ext = os.path.splitext(file_path)[1].lower()
        language_map = {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".java": "java",
            ".go": "go",
            ".rs": "rust",
            ".rb": "ruby",
            ".php": "php",
        }

        return language_map.get(ext, "python")

    def _extract_relevant_code(
        self,
        source_code: str,
        line_number: int,
        max_lines: int,
    ) -> str:
        """Extract relevant code around the error line."""
        lines = source_code.splitlines()

        if line_number < 1 or line_number > len(lines):
            return source_code[:max_lines * 80]

        context_before = max_lines // 3
        context_after = max_lines // 3

        start = max(0, line_number - 1 - context_before)
        end = min(len(lines), line_number + context_after)

        relevant_lines = lines[start:end]

        error_line_idx = line_number - 1 - start
        if 0 <= error_line_idx < len(relevant_lines):
            relevant_lines[error_line_idx] = (
                f"{relevant_lines[error_line_idx]}  # <-- Error here"
            )

        return "\n".join(relevant_lines)

    def _generate_template_mre(
        self,
        category: ErrorCategory,
        language: str,
    ) -> str:
        """Generate a template MRE based on error category."""
        if language == "python":
            templates = {
                ErrorCategory.SYNTAX: (
                    "# Syntax error example\n"
                    "def example():\n"
                    "    # Missing colon or bracket\n"
                    "    pass\n"
                ),
                ErrorCategory.TYPE_MISMATCH: (
                    "# Type mismatch example\n"
                    "def example():\n"
                    "    value = 'string'\n"
                    "    result = value + 1  # TypeError\n"
                ),
                ErrorCategory.NULL_REFERENCE: (
                    "# Null reference example\n"
                    "def example():\n"
                    "    obj = None\n"
                    "    obj.method()  # AttributeError\n"
                ),
                ErrorCategory.IMPORT_FAILURE: (
                    "# Import failure example\n"
                    "from nonexistent_module import something  # ImportError\n"
                ),
                ErrorCategory.ASSERTION_FAILURE: (
                    "# Assertion failure example\n"
                    "def test_example():\n"
                    "    expected = 1\n"
                    "    actual = 2\n"
                    "    assert expected == actual  # AssertionError\n"
                ),
            }
            return templates.get(category, "# Error reproduction code\npass\n")

        elif language in ("javascript", "typescript"):
            templates = {
                ErrorCategory.SYNTAX: (
                    "// Syntax error example\n"
                    "function example() {\n"
                    "    // Missing bracket or semicolon\n"
                    "}\n"
                ),
                ErrorCategory.TYPE_MISMATCH: (
                    "// Type mismatch example\n"
                    "function example() {\n"
                    "    const value = 'string';\n"
                    "    const result = value + 1; // Unexpected behavior\n"
                    "}\n"
                ),
                ErrorCategory.NULL_REFERENCE: (
                    "// Null reference example\n"
                    "function example() {\n"
                    "    const obj = null;\n"
                    "    obj.method(); // TypeError\n"
                    "}\n"
                ),
            }
            return templates.get(category, "// Error reproduction code\n")

        return "# Error reproduction code\n"

    def _generate_setup_instructions(self, category: ErrorCategory) -> str:
        """Generate setup instructions for reproducing the error."""
        instructions = {
            ErrorCategory.IMPORT_FAILURE: (
                "1. Create a virtual environment\n"
                "2. Install required dependencies\n"
                "3. Run the code to reproduce the import error"
            ),
            ErrorCategory.CONFIGURATION: (
                "1. Set up required environment variables\n"
                "2. Create necessary config files\n"
                "3. Run the code to reproduce the config error"
            ),
            ErrorCategory.DEPENDENCY: (
                "1. Check current dependency versions\n"
                "2. Install specific versions mentioned in error\n"
                "3. Run the code to reproduce the dependency error"
            ),
        }

        return instructions.get(
            category,
            "1. Copy the code to a new file\n"
            "2. Run the code to reproduce the error"
        )

    def _extract_dependencies(self, source_code: str) -> List[str]:
        """Extract dependencies from source code.

        Handles both simple imports and submodule imports:
        - `import package` -> extracts 'package'
        - `from package.module import item` -> extracts 'package'
        """
        dependencies = []

        import_pattern = re.compile(
            r'^(?:from\s+([\w.]+)|import\s+([\w.]+))',
            re.MULTILINE
        )

        for match in import_pattern.finditer(source_code):
            module_path = match.group(1) or match.group(2)
            if module_path:
                module = module_path.split('.')[0]
                if module and module not in dependencies:
                    stdlib = {
                        "os", "sys", "re", "json", "logging", "typing",
                        "dataclasses", "enum", "collections", "itertools",
                        "functools", "pathlib", "datetime", "time",
                    }
                    if module not in stdlib:
                        dependencies.append(module)

        return dependencies[:10]

    def _assess_blast_radius(
        self,
        error_context: Dict[str, Any],
        source_contents: Optional[Dict[str, str]],
        root_cause: RootCauseAnalysis,
    ) -> BlastRadiusAssessment:
        """Assess the blast radius of an error.

        Event Codes:
            [DIAGNOSTIC_AGENT_BLAST_RADIUS] - Blast radius assessed
        """
        file_path = error_context.get("file_path", "")

        level = BlastRadiusLevel.ISOLATED
        affected_files = [file_path] if file_path else []
        affected_functions = []
        affected_tests = []

        if root_cause.category in (
            ErrorCategory.IMPORT_FAILURE,
            ErrorCategory.DEPENDENCY,
        ):
            level = BlastRadiusLevel.MODULE

        if root_cause.category == ErrorCategory.CONFIGURATION:
            level = BlastRadiusLevel.SERVICE

        if source_contents:
            for path, content in source_contents.items():
                if path == file_path:
                    continue
                if file_path:
                    module_name = os.path.splitext(os.path.basename(file_path))[0]
                    import_pattern = re.compile(
                        fr'^\s*(?:from|import)\s+{re.escape(module_name)}\b',
                        re.MULTILINE
                    )
                    if import_pattern.search(content):
                        affected_files.append(path)
                        if level == BlastRadiusLevel.ISOLATED:
                            level = BlastRadiusLevel.MODULE

        description = self._generate_blast_radius_description(
            level, len(affected_files)
        )

        assessment = BlastRadiusAssessment(
            level=level,
            affected_files=affected_files[:10],
            affected_functions=affected_functions,
            affected_tests=affected_tests,
            description=description,
        )

        logger.info(
            f"[DIAGNOSTIC_AGENT_BLAST_RADIUS] Level: {level.value}, "
            f"affected files: {len(affected_files)}"
        )

        return assessment

    def _generate_blast_radius_description(
        self,
        level: BlastRadiusLevel,
        affected_count: int,
    ) -> str:
        """Generate blast radius description."""
        descriptions = {
            BlastRadiusLevel.ISOLATED: (
                f"Impact is isolated to a single file. "
                f"{affected_count} file(s) may be affected."
            ),
            BlastRadiusLevel.MODULE: (
                f"Impact extends to the module level. "
                f"{affected_count} file(s) may be affected. "
                f"Other files importing this module may also fail."
            ),
            BlastRadiusLevel.SERVICE: (
                f"Impact affects the entire service. "
                f"{affected_count} file(s) may be affected. "
                f"Service functionality may be degraded."
            ),
            BlastRadiusLevel.SYSTEM: (
                f"Impact is system-wide. "
                f"{affected_count} file(s) may be affected. "
                f"Multiple services may be affected."
            ),
        }

        return descriptions.get(level, f"{affected_count} file(s) may be affected.")

    def _suggest_regression_test(
        self,
        error_context: Dict[str, Any],
        root_cause: RootCauseAnalysis,
        mre: Optional[MinimalReproducibleExample],
    ) -> Optional[str]:
        """Suggest a regression test for the error.

        Blueprint Section 3.5: Diagnostic Agent collaborates with Test Agent v2
        to convert errors into regression tests.
        """
        error_type = error_context.get("error_type", "Error")
        file_path = error_context.get("file_path", "unknown")

        test_name = f"test_regression_{root_cause.category.value}"
        if file_path:
            module_name = os.path.splitext(os.path.basename(file_path))[0]
            test_name = f"test_regression_{module_name}_{root_cause.category.value}"

        if mre and mre.language == "python":
            return f'''
def {test_name}():
    """
    Regression test for {error_type} in {file_path}.

    Root cause: {root_cause.category.value}
    Description: {root_cause.description[:100]}...
    """
    # TODO: Implement regression test
    # Expected behavior: Should not raise {error_type}
    pass
'''

        elif mre and mre.language in ("javascript", "typescript"):
            return f'''
describe('Regression: {file_path}', () => {{
    it('{test_name}', () => {{
        // Regression test for {error_type}
        // Root cause: {root_cause.category.value}
        // TODO: Implement regression test
        expect(true).toBe(true);
    }});
}});
'''

        return None

    def _generate_feedback(
        self,
        root_cause: RootCauseAnalysis,
        blast_radius: BlastRadiusAssessment,
    ) -> str:
        """Generate human-readable feedback."""
        return (
            f"Diagnosis complete.\n\n"
            f"Root Cause: {root_cause.category.value}\n"
            f"Confidence: {root_cause.confidence:.0%}\n"
            f"Description: {root_cause.description}\n\n"
            f"Blast Radius: {blast_radius.level.value}\n"
            f"{blast_radius.description}\n\n"
            f"Suggested Fix:\n{root_cause.suggested_fix}"
        )


def diagnose_error(
    error_context: Dict[str, Any],
    source_contents: Optional[Dict[str, str]] = None,
    enable_llm: bool = True,
) -> DiagnosticResult:
    """Convenience function to diagnose an error.

    Args:
        error_context: Error information
        source_contents: Source file contents
        enable_llm: Whether to use LLM for enhanced analysis

    Returns:
        DiagnosticResult with diagnosis information
    """
    node = DiagnosticAgentNode(enable_llm=enable_llm)
    return node.diagnose(error_context, source_contents)
