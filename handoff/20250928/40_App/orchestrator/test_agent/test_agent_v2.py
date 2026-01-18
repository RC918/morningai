#!/usr/bin/env python3
"""
Test Agent v2 - EPIC D Phase 5 (P2-medium)

Blueprint Reference: Section 3.3 (Agent Catalog V2) - Test Agent
Issue: #4102 (EPIC D P2: Test Agent v2 Complete Implementation)

This module implements the Test Agent v2 as a standalone agent that:
1. Integrates with B-11 Test Coverage Flagging to identify coverage gaps
2. Generates tests from coverage gaps using LLM or templates
3. Validates test quality (syntax, assertions, coverage)
4. Provides test recommendations and improvements

Design Principles (Blueprint Section 3.3 - Agent Separation):
- Reviewer Agent flags coverage gaps (B-11)
- Test Agent generates tests (D-7)
- CI executes tests
- Debugger Agent fixes failing tests (D-4)

What Test Agent v2 CAN do:
- Read coverage gaps from B-11 output
- Generate actual test code using LLM
- Create test files in appropriate locations
- Validate test quality (syntax, assertions, coverage)

What Test Agent v2 CANNOT do (belongs to other agents):
- Identify coverage gaps (that's B-11 Reviewer's job)
- Execute tests (that's CI's job)
- Fix failing tests (that's D-4 Self-Correction's job)
"""

import ast
import hashlib
import json
import logging
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class TestQualityLevel(Enum):
    """Quality levels for test validation."""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    INVALID = "invalid"


class TestQualityCategory(Enum):
    """Categories for test quality analysis."""
    SYNTAX = "syntax"
    ASSERTIONS = "assertions"
    COVERAGE = "coverage"
    NAMING = "naming"
    STRUCTURE = "structure"
    MOCKING = "mocking"


class TestQualityAction(Enum):
    """Actions to take based on test quality analysis."""
    APPROVE = "approve"
    SUGGEST_IMPROVEMENTS = "suggest_improvements"
    REQUIRE_CHANGES = "require_changes"
    REJECT = "reject"


@dataclass
class TestQualityFinding:
    """Represents a single test quality finding."""
    category: TestQualityCategory
    level: TestQualityLevel
    finding_id: str
    title: str
    description: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    test_name: Optional[str] = None
    recommendation: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "category": self.category.value,
            "level": self.level.value,
            "finding_id": self.finding_id,
            "title": self.title,
            "description": self.description,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "test_name": self.test_name,
            "recommendation": self.recommendation,
            "metadata": self.metadata,
        }


@dataclass
class TestQualityResult:
    """Result of test quality validation."""
    overall_score: int
    overall_level: TestQualityLevel
    action: TestQualityAction
    findings: List[TestQualityFinding] = field(default_factory=list)
    category_scores: Dict[TestQualityCategory, int] = field(default_factory=dict)
    test_count: int = 0
    assertion_count: int = 0
    mock_count: int = 0
    summary: str = ""
    analyzer_id: str = "test_agent_v2"
    analysis_duration_ms: float = 0.0
    evidence_hash: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "overall_score": self.overall_score,
            "overall_level": self.overall_level.value,
            "action": self.action.value,
            "findings": [f.to_dict() for f in self.findings],
            "category_scores": {k.value: v for k, v in self.category_scores.items()},
            "test_count": self.test_count,
            "assertion_count": self.assertion_count,
            "mock_count": self.mock_count,
            "summary": self.summary,
            "analyzer_id": self.analyzer_id,
            "analysis_duration_ms": self.analysis_duration_ms,
            "evidence_hash": self.evidence_hash,
        }


@dataclass
class TestGenerationRequest:
    """Request for test generation."""
    coverage_gaps: List[Dict[str, Any]]
    repo_path: str
    trace_id: str
    source_contents: Optional[Dict[str, str]] = None
    max_tests_per_run: int = 5
    enable_llm: bool = True
    validate_quality: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "coverage_gaps": self.coverage_gaps,
            "repo_path": self.repo_path,
            "trace_id": self.trace_id,
            "source_contents": self.source_contents,
            "max_tests_per_run": self.max_tests_per_run,
            "enable_llm": self.enable_llm,
            "validate_quality": self.validate_quality,
        }


@dataclass
class TestGenerationResponse:
    """Response from test generation."""
    success: bool
    generated_tests: List[Dict[str, Any]] = field(default_factory=list)
    failed_generations: List[Dict[str, str]] = field(default_factory=list)
    quality_results: List[TestQualityResult] = field(default_factory=list)
    summary: str = ""
    total_generated: int = 0
    total_failed: int = 0
    trace_id: str = ""
    duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "success": self.success,
            "generated_tests": self.generated_tests,
            "failed_generations": self.failed_generations,
            "quality_results": [q.to_dict() for q in self.quality_results],
            "summary": self.summary,
            "total_generated": self.total_generated,
            "total_failed": self.total_failed,
            "trace_id": self.trace_id,
            "duration_ms": self.duration_ms,
        }


# Quality thresholds
QUALITY_THRESHOLDS = {
    TestQualityLevel.EXCELLENT: 90,
    TestQualityLevel.GOOD: 75,
    TestQualityLevel.ACCEPTABLE: 60,
    TestQualityLevel.POOR: 40,
    TestQualityLevel.INVALID: 0,
}

# Category weights for overall score
CATEGORY_WEIGHTS = {
    TestQualityCategory.SYNTAX: 0.25,
    TestQualityCategory.ASSERTIONS: 0.30,
    TestQualityCategory.COVERAGE: 0.20,
    TestQualityCategory.NAMING: 0.10,
    TestQualityCategory.STRUCTURE: 0.10,
    TestQualityCategory.MOCKING: 0.05,
}

# Test naming patterns
PYTEST_TEST_PATTERN = re.compile(r"^test_[a-z][a-z0-9_]*$")
PYTEST_CLASS_PATTERN = re.compile(r"^Test[A-Z][a-zA-Z0-9]*$")

# Assertion patterns
ASSERTION_PATTERNS = [
    re.compile(r"\bassert\s+"),
    re.compile(r"\bassertEqual\s*\("),
    re.compile(r"\bassertTrue\s*\("),
    re.compile(r"\bassertFalse\s*\("),
    re.compile(r"\bassertRaises\s*\("),
    re.compile(r"\bassertIn\s*\("),
    re.compile(r"\bassertIsNone\s*\("),
    re.compile(r"\bassertIsNotNone\s*\("),
    re.compile(r"\.assert_called"),
    re.compile(r"pytest\.raises\s*\("),
]

# Mock patterns
MOCK_PATTERNS = [
    re.compile(r"\bMock\s*\("),
    re.compile(r"\bMagicMock\s*\("),
    re.compile(r"\bpatch\s*\("),
    re.compile(r"\b@patch"),
    re.compile(r"\bmocker\."),
]


class TestAgentV2:
    """
    Test Agent v2 - Standalone agent for test generation and validation.

    Blueprint Reference: Section 3.3 (Agent Catalog V2)
    - Test Agent
    - Integrates with B-11 Test Coverage Flagging
    - Integrates with Safety Governor v2 (Section 4.1)

    This agent:
    1. Receives coverage gaps from B-11 (TestCoverageAnalyzer)
    2. Generates tests using TestGeneratorNode (D-7)
    3. Validates test quality (syntax, assertions, coverage)
    4. Returns generated tests with quality assessment
    """

    def __init__(
        self,
        enabled: bool = True,
        enable_llm: bool = True,
        validate_quality: bool = True,
        max_tests_per_run: int = 5,
    ):
        """
        Initialize TestAgentV2.

        Args:
            enabled: Whether test generation is enabled
            enable_llm: Whether to use LLM for test generation
            validate_quality: Whether to validate generated test quality
            max_tests_per_run: Maximum number of test files to generate per run
        """
        self.enabled = enabled
        self.enable_llm = enable_llm
        self.validate_quality = validate_quality
        self.max_tests_per_run = max_tests_per_run
        self._test_generator = None
        self._coverage_analyzer = None
        self._load_settings()
        logger.info(
            "[TestAgentV2] Initialized - EPIC D P2: "
            "enabled=%s, enable_llm=%s, validate_quality=%s",
            self.enabled,
            self.enable_llm,
            self.validate_quality,
        )

    def _load_settings(self) -> None:
        """Load settings from environment/config."""
        try:
            from common.config.settings import settings
            self.enabled = getattr(
                settings, "USE_TEST_GENERATION", self.enabled
            )
            self.enable_llm = getattr(
                settings, "test_agent_enable_llm", self.enable_llm
            )
            self.validate_quality = getattr(
                settings, "test_agent_validate_quality", self.validate_quality
            )
            logger.debug("[TestAgentV2] Settings loaded from config")
        except (ImportError, AttributeError) as e:
            logger.debug("[TestAgentV2] Using default settings: %s", e)

    def _get_test_generator(self):
        """Lazy-load the TestGeneratorNode (D-7)."""
        if self._test_generator is None:
            try:
                from test_generator_node import TestGeneratorNode
                self._test_generator = TestGeneratorNode(
                    trace_id="test_agent_v2",
                    max_tests_per_run=self.max_tests_per_run,
                    enable_llm=self.enable_llm,
                )
            except ImportError as e:
                logger.warning(
                    "[TestAgentV2] Could not import TestGeneratorNode: %s", e
                )
        return self._test_generator

    def _get_coverage_analyzer(self):
        """Lazy-load the TestCoverageAnalyzer (B-11)."""
        if self._coverage_analyzer is None:
            try:
                from review_context.test_coverage_analyzer import TestCoverageAnalyzer
                self._coverage_analyzer = TestCoverageAnalyzer(
                    trace_id="test_agent_v2"
                )
            except ImportError as e:
                logger.warning(
                    "[TestAgentV2] Could not import TestCoverageAnalyzer: %s", e
                )
        return self._coverage_analyzer

    def generate_tests(
        self,
        request: TestGenerationRequest,
    ) -> TestGenerationResponse:
        """
        Generate tests from coverage gaps.

        This is the main entry point for test generation. It:
        1. Uses TestGeneratorNode (D-7) to generate tests
        2. Optionally validates test quality
        3. Returns generated tests with quality assessment

        Args:
            request: TestGenerationRequest with coverage gaps and options

        Returns:
            TestGenerationResponse with generated tests and quality results
        """
        start_time = time.time()

        if not self.enabled:
            return TestGenerationResponse(
                success=False,
                summary="Test generation is disabled",
                trace_id=request.trace_id,
            )

        if not request.coverage_gaps:
            return TestGenerationResponse(
                success=True,
                summary="No coverage gaps to generate tests for",
                trace_id=request.trace_id,
            )

        logger.info(
            "[TestAgentV2] Starting test generation",
            extra={
                "operation": "test_generation",
                "trace_id": request.trace_id,
                "gap_count": len(request.coverage_gaps),
            }
        )

        # Use TestGeneratorNode (D-7) for actual generation
        generator = self._get_test_generator()
        if not generator:
            return TestGenerationResponse(
                success=False,
                summary="TestGeneratorNode not available",
                trace_id=request.trace_id,
            )

        # Update generator settings from request
        generator.trace_id = request.trace_id
        generator.max_tests_per_run = request.max_tests_per_run
        generator.enable_llm = request.enable_llm

        # Generate tests
        result = generator.generate(
            coverage_gaps=request.coverage_gaps,
            repo_path=request.repo_path,
            source_contents=request.source_contents,
        )

        # Convert to response format
        generated_tests = [t.to_dict() for t in result.generated_tests]
        failed_generations = result.failed_generations

        # Validate quality if enabled
        quality_results: List[TestQualityResult] = []
        if request.validate_quality and self.validate_quality:
            for test in result.generated_tests:
                quality = self.validate_test_quality(
                    test_code=test.test_code,
                    file_path=test.test_file_path,
                )
                quality_results.append(quality)

        duration_ms = (time.time() - start_time) * 1000

        # Build summary
        if generated_tests:
            summary = (
                f"Generated {len(generated_tests)} test file(s) for "
                f"{sum(len(t.get('functions_tested', [])) for t in generated_tests)} function(s)"
            )
            if quality_results:
                avg_score = sum(q.overall_score for q in quality_results) / len(quality_results)
                summary += f". Average quality score: {avg_score:.0f}/100"
        else:
            summary = "No tests generated"

        if failed_generations:
            summary += f". {len(failed_generations)} file(s) failed."

        logger.info(
            "[TestAgentV2] Test generation completed",
            extra={
                "operation": "test_generation",
                "trace_id": request.trace_id,
                "generated_count": len(generated_tests),
                "failed_count": len(failed_generations),
                "duration_ms": duration_ms,
            }
        )

        return TestGenerationResponse(
            success=len(generated_tests) > 0,
            generated_tests=generated_tests,
            failed_generations=failed_generations,
            quality_results=quality_results,
            summary=summary,
            total_generated=len(generated_tests),
            total_failed=len(failed_generations),
            trace_id=request.trace_id,
            duration_ms=duration_ms,
        )

    def analyze_coverage_gaps(
        self,
        diff_content: str,
        diff_files: Optional[List[str]] = None,
        trace_id: str = "",
    ) -> Dict[str, Any]:
        """
        Analyze diff for coverage gaps using B-11 TestCoverageAnalyzer.

        This is a convenience method that wraps B-11 functionality.
        In production, coverage gaps typically come from the Reviewer Agent.

        Args:
            diff_content: The PR diff content
            diff_files: Optional list of files in the diff
            trace_id: Trace ID for telemetry

        Returns:
            Dictionary with coverage analysis results
        """
        analyzer = self._get_coverage_analyzer()
        if not analyzer:
            return {
                "coverage_gaps": [],
                "summary": "TestCoverageAnalyzer not available",
            }

        analyzer.trace_id = trace_id
        analysis = analyzer.analyze(diff_content, diff_files)
        return analysis.to_dict()

    def validate_test_quality(
        self,
        test_code: str,
        file_path: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> TestQualityResult:
        """
        Validate the quality of generated test code.

        This method analyzes test code for:
        1. Syntax validity (Python AST parsing)
        2. Assertion presence and quality
        3. Test naming conventions
        4. Test structure (setup, teardown, etc.)
        5. Mocking patterns

        Args:
            test_code: Test code to validate
            file_path: Path to the test file
            context: Optional context with additional information

        Returns:
            TestQualityResult with findings and recommendations
        """
        start_time = time.time()

        if not test_code or not test_code.strip():
            return TestQualityResult(
                overall_score=0,
                overall_level=TestQualityLevel.INVALID,
                action=TestQualityAction.REJECT,
                summary="Empty test code",
            )

        context = context or {}
        findings: List[TestQualityFinding] = []
        category_scores: Dict[TestQualityCategory, int] = {}

        # 1. Syntax validation
        syntax_findings, syntax_score = self._validate_syntax(test_code, file_path)
        findings.extend(syntax_findings)
        category_scores[TestQualityCategory.SYNTAX] = syntax_score

        # If syntax is invalid, return early
        if syntax_score == 0:
            return TestQualityResult(
                overall_score=0,
                overall_level=TestQualityLevel.INVALID,
                action=TestQualityAction.REJECT,
                findings=findings,
                category_scores=category_scores,
                summary="Test code has syntax errors",
            )

        # 2. Assertion analysis
        assertion_findings, assertion_score, assertion_count = self._analyze_assertions(
            test_code, file_path
        )
        findings.extend(assertion_findings)
        category_scores[TestQualityCategory.ASSERTIONS] = assertion_score

        # 3. Naming convention analysis
        naming_findings, naming_score, test_count = self._analyze_naming(
            test_code, file_path
        )
        findings.extend(naming_findings)
        category_scores[TestQualityCategory.NAMING] = naming_score

        # 4. Structure analysis
        structure_findings, structure_score = self._analyze_structure(
            test_code, file_path
        )
        findings.extend(structure_findings)
        category_scores[TestQualityCategory.STRUCTURE] = structure_score

        # 5. Mocking analysis
        mocking_findings, mocking_score, mock_count = self._analyze_mocking(
            test_code, file_path
        )
        findings.extend(mocking_findings)
        category_scores[TestQualityCategory.MOCKING] = mocking_score

        # 6. Coverage estimation (based on test count vs function count)
        coverage_score = min(100, test_count * 20)  # Simple heuristic
        category_scores[TestQualityCategory.COVERAGE] = coverage_score

        # Calculate overall score
        overall_score = self._calculate_overall_score(category_scores)
        overall_level = self._determine_level(overall_score)
        action = self._determine_action(overall_level, findings)

        summary = self._generate_summary(
            overall_score, overall_level, test_count, assertion_count
        )

        duration_ms = (time.time() - start_time) * 1000
        evidence_hash = self._compute_evidence_hash(test_code, findings)

        result = TestQualityResult(
            overall_score=overall_score,
            overall_level=overall_level,
            action=action,
            findings=findings,
            category_scores=category_scores,
            test_count=test_count,
            assertion_count=assertion_count,
            mock_count=mock_count,
            summary=summary,
            analysis_duration_ms=duration_ms,
            evidence_hash=evidence_hash,
        )

        logger.info(
            "[TestAgentV2] Quality validation complete: score=%d, level=%s",
            overall_score,
            overall_level.value,
        )

        return result

    def _validate_syntax(
        self,
        test_code: str,
        file_path: Optional[str],
    ) -> Tuple[List[TestQualityFinding], int]:
        """Validate Python syntax."""
        findings: List[TestQualityFinding] = []

        try:
            ast.parse(test_code)
            return findings, 100
        except SyntaxError as e:
            findings.append(TestQualityFinding(
                category=TestQualityCategory.SYNTAX,
                level=TestQualityLevel.INVALID,
                finding_id="SYN-001",
                title="Syntax error",
                description=f"Python syntax error: {e.msg}",
                file_path=file_path,
                line_number=e.lineno,
                recommendation="Fix the syntax error before using this test",
            ))
            return findings, 0

    def _analyze_assertions(
        self,
        test_code: str,
        file_path: Optional[str],
    ) -> Tuple[List[TestQualityFinding], int, int]:
        """Analyze assertion usage."""
        findings: List[TestQualityFinding] = []
        assertion_count = 0

        for pattern in ASSERTION_PATTERNS:
            matches = pattern.findall(test_code)
            assertion_count += len(matches)

        if assertion_count == 0:
            findings.append(TestQualityFinding(
                category=TestQualityCategory.ASSERTIONS,
                level=TestQualityLevel.POOR,
                finding_id="AST-001",
                title="No assertions found",
                description="Test code contains no assertions",
                file_path=file_path,
                recommendation="Add assertions to verify expected behavior",
            ))
            return findings, 20, 0

        # Check for trivial assertions using AST (more robust than string matching)
        # This avoids false positives from comments or strings containing "assert True"
        try:
            tree = ast.parse(test_code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Assert):
                    # Check if assertion is trivial (assert True or assert False)
                    if isinstance(node.test, ast.Constant):
                        if node.test.value is True or node.test.value is False:
                            findings.append(TestQualityFinding(
                                category=TestQualityCategory.ASSERTIONS,
                                level=TestQualityLevel.ACCEPTABLE,
                                finding_id="AST-002",
                                title="Trivial assertion",
                                description="Found trivial assertion (assert True/False)",
                                file_path=file_path,
                                line_number=node.lineno,
                                recommendation="Replace with meaningful assertions",
                            ))
                            break  # Only report once
                    # Also check for NameConstant (Python 3.7 compatibility)
                    elif isinstance(node.test, ast.NameConstant):
                        if node.test.value is True or node.test.value is False:
                            findings.append(TestQualityFinding(
                                category=TestQualityCategory.ASSERTIONS,
                                level=TestQualityLevel.ACCEPTABLE,
                                finding_id="AST-002",
                                title="Trivial assertion",
                                description="Found trivial assertion (assert True/False)",
                                file_path=file_path,
                                line_number=node.lineno,
                                recommendation="Replace with meaningful assertions",
                            ))
                            break  # Only report once
        except SyntaxError:
            pass  # Syntax errors are handled in _validate_syntax

        # Score based on assertion count
        score = min(100, 50 + assertion_count * 10)
        return findings, score, assertion_count

    def _analyze_naming(
        self,
        test_code: str,
        file_path: Optional[str],
    ) -> Tuple[List[TestQualityFinding], int, int]:
        """Analyze test naming conventions."""
        findings: List[TestQualityFinding] = []
        test_count = 0
        naming_issues = 0

        try:
            tree = ast.parse(test_code)
        except SyntaxError:
            return findings, 0, 0

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.name.startswith("test_"):
                    test_count += 1
                    if not PYTEST_TEST_PATTERN.match(node.name):
                        naming_issues += 1
                        findings.append(TestQualityFinding(
                            category=TestQualityCategory.NAMING,
                            level=TestQualityLevel.ACCEPTABLE,
                            finding_id="NAM-001",
                            title="Non-standard test name",
                            description=f"Test '{node.name}' doesn't follow naming convention",
                            file_path=file_path,
                            line_number=node.lineno,
                            test_name=node.name,
                            recommendation="Use snake_case: test_<description>",
                        ))
            elif isinstance(node, ast.ClassDef):
                if node.name.startswith("Test"):
                    if not PYTEST_CLASS_PATTERN.match(node.name):
                        naming_issues += 1
                        findings.append(TestQualityFinding(
                            category=TestQualityCategory.NAMING,
                            level=TestQualityLevel.ACCEPTABLE,
                            finding_id="NAM-002",
                            title="Non-standard test class name",
                            description=f"Test class '{node.name}' doesn't follow naming convention",
                            file_path=file_path,
                            line_number=node.lineno,
                            test_name=node.name,
                            recommendation="Use PascalCase: Test<Description>",
                        ))

        if test_count == 0:
            findings.append(TestQualityFinding(
                category=TestQualityCategory.NAMING,
                level=TestQualityLevel.POOR,
                finding_id="NAM-003",
                title="No test functions found",
                description="No functions starting with 'test_' found",
                file_path=file_path,
                recommendation="Add test functions with 'test_' prefix",
            ))
            return findings, 30, 0

        score = max(0, 100 - naming_issues * 20)
        return findings, score, test_count

    def _analyze_structure(
        self,
        test_code: str,
        file_path: Optional[str],
    ) -> Tuple[List[TestQualityFinding], int]:
        """Analyze test structure."""
        findings: List[TestQualityFinding] = []
        score = 100

        # Check for module-level docstring using AST (more robust than string matching)
        # This correctly identifies actual docstrings vs triple-quoted strings in code
        has_docstrings = False
        try:
            tree = ast.parse(test_code)
            # Check for module-level docstring
            if ast.get_docstring(tree) is not None:
                has_docstrings = True
            else:
                # Also check for function/class docstrings
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        if ast.get_docstring(node) is not None:
                            has_docstrings = True
                            break
        except SyntaxError:
            pass  # Syntax errors are handled in _validate_syntax

        if not has_docstrings:
            score -= 10
            findings.append(TestQualityFinding(
                category=TestQualityCategory.STRUCTURE,
                level=TestQualityLevel.ACCEPTABLE,
                finding_id="STR-001",
                title="Missing docstrings",
                description="Test file lacks docstrings",
                file_path=file_path,
                recommendation="Add docstrings to describe test purpose",
            ))

        # Check for imports
        if "import pytest" not in test_code and "from pytest" not in test_code:
            if "import unittest" not in test_code:
                score -= 5
                findings.append(TestQualityFinding(
                    category=TestQualityCategory.STRUCTURE,
                    level=TestQualityLevel.GOOD,
                    finding_id="STR-002",
                    title="No test framework import",
                    description="No pytest or unittest import found",
                    file_path=file_path,
                    recommendation="Import pytest for better test features",
                ))

        return findings, max(0, score)

    def _analyze_mocking(
        self,
        test_code: str,
        file_path: Optional[str],
    ) -> Tuple[List[TestQualityFinding], int, int]:
        """Analyze mocking patterns."""
        findings: List[TestQualityFinding] = []
        mock_count = 0

        for pattern in MOCK_PATTERNS:
            matches = pattern.findall(test_code)
            mock_count += len(matches)

        # Mocking is optional, so no penalty for not having mocks
        score = 100 if mock_count == 0 else min(100, 70 + mock_count * 10)

        return findings, score, mock_count

    def _calculate_overall_score(
        self,
        category_scores: Dict[TestQualityCategory, int],
    ) -> int:
        """Calculate weighted overall score."""
        if not category_scores:
            return 0

        total_weight = 0.0
        weighted_sum = 0.0

        for category, score in category_scores.items():
            weight = CATEGORY_WEIGHTS.get(category, 0.1)
            weighted_sum += score * weight
            total_weight += weight

        if total_weight == 0:
            return 0

        return int(weighted_sum / total_weight)

    def _determine_level(self, score: int) -> TestQualityLevel:
        """Determine quality level from score."""
        if score >= 90:
            return TestQualityLevel.EXCELLENT
        elif score >= 75:
            return TestQualityLevel.GOOD
        elif score >= 60:
            return TestQualityLevel.ACCEPTABLE
        elif score >= 40:
            return TestQualityLevel.POOR
        else:
            return TestQualityLevel.INVALID

    def _determine_action(
        self,
        level: TestQualityLevel,
        findings: List[TestQualityFinding],
    ) -> TestQualityAction:
        """Determine action based on quality level and findings."""
        if level == TestQualityLevel.INVALID:
            return TestQualityAction.REJECT
        elif level == TestQualityLevel.POOR:
            return TestQualityAction.REQUIRE_CHANGES
        elif level == TestQualityLevel.ACCEPTABLE:
            return TestQualityAction.SUGGEST_IMPROVEMENTS
        else:
            return TestQualityAction.APPROVE

    def _generate_summary(
        self,
        score: int,
        level: TestQualityLevel,
        test_count: int,
        assertion_count: int,
    ) -> str:
        """Generate human-readable summary."""
        return (
            f"Quality score: {score}/100 ({level.value}). "
            f"Found {test_count} test(s) with {assertion_count} assertion(s)."
        )

    def _compute_evidence_hash(
        self,
        test_code: str,
        findings: List[TestQualityFinding],
    ) -> str:
        """Compute hash for evidence ledger.

        Uses json.dumps with sort_keys=True for deterministic serialization,
        ensuring consistent hash values regardless of dict ordering.
        """
        # Sort findings by finding_id for deterministic ordering
        sorted_findings = sorted(
            [f.to_dict() for f in findings],
            key=lambda x: x.get("finding_id", ""),
        )
        # Use json.dumps with sort_keys for deterministic serialization
        findings_json = json.dumps(sorted_findings, sort_keys=True)
        content = test_code + findings_json
        return hashlib.sha256(content.encode()).hexdigest()[:16]


# Singleton instance
_test_agent_instance: Optional[TestAgentV2] = None


def get_test_agent() -> TestAgentV2:
    """Get or create the singleton TestAgentV2 instance."""
    global _test_agent_instance
    if _test_agent_instance is None:
        _test_agent_instance = TestAgentV2()
    return _test_agent_instance


def reset_test_agent() -> None:
    """Reset the singleton instance (for testing)."""
    global _test_agent_instance
    _test_agent_instance = None


def generate_tests(
    coverage_gaps: List[Dict[str, Any]],
    repo_path: str,
    trace_id: str,
    source_contents: Optional[Dict[str, str]] = None,
    max_tests_per_run: int = 5,
    enable_llm: bool = True,
    validate_quality: bool = True,
) -> Dict[str, Any]:
    """
    Convenience function for test generation.

    Args:
        coverage_gaps: List of CoverageGap dicts from B-11
        repo_path: Path to the repository root
        trace_id: Trace ID for telemetry
        source_contents: Optional dict mapping file paths to their contents
        max_tests_per_run: Maximum number of test files to generate
        enable_llm: Whether to use LLM for test generation
        validate_quality: Whether to validate generated test quality

    Returns:
        Dictionary with test generation results
    """
    agent = get_test_agent()
    request = TestGenerationRequest(
        coverage_gaps=coverage_gaps,
        repo_path=repo_path,
        trace_id=trace_id,
        source_contents=source_contents,
        max_tests_per_run=max_tests_per_run,
        enable_llm=enable_llm,
        validate_quality=validate_quality,
    )
    response = agent.generate_tests(request)
    return response.to_dict()


def validate_test_quality(
    test_code: str,
    file_path: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Convenience function for test quality validation.

    Args:
        test_code: Test code to validate
        file_path: Path to the test file
        context: Optional context with additional information

    Returns:
        Dictionary with quality validation results
    """
    agent = get_test_agent()
    result = agent.validate_test_quality(test_code, file_path, context)
    return result.to_dict()
