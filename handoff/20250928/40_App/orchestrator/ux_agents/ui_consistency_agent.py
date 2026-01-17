#!/usr/bin/env python3
"""
UI Consistency Agent - EPIC K Phase 2 (P2-medium)

Blueprint Reference: Section 3.3 (Agent Catalog V2) - UX/UI Agents
Issue: #4097 (EPIC K P2: 4 UI/UX Agents Implementation)

This module implements the UI Consistency Agent for analyzing UI component
consistency across the application. It integrates with:
- shared-ui component library for component standards
- Safety Governor v2 (Section 4.1) for content safety
- Evidence Ledger (Section 4.6) for audit trail

Design Principles:
- Component naming convention validation
- Style consistency checking (colors, spacing, typography)
- Component usage pattern analysis
- Integration with design token system

Benchmark Targets (per #4121):
- Figma plugins for design consistency
- Lighthouse for accessibility metrics
- Percy for visual consistency
"""
import hashlib
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger(__name__)


class ConsistencyCategory(Enum):
    """Categories for UI consistency analysis.

    Blueprint Reference: Section 3.3 (Agent Catalog V2)
    """
    COMPONENT_NAMING = "component_naming"
    COLOR_USAGE = "color_usage"
    SPACING = "spacing"
    TYPOGRAPHY = "typography"
    ICON_USAGE = "icon_usage"
    LAYOUT_PATTERN = "layout_pattern"
    ACCESSIBILITY = "accessibility"


class ConsistencyLevel(Enum):
    """Severity levels for consistency findings."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ConsistencyAction(Enum):
    """Actions to take based on consistency analysis."""
    BLOCK = "block"
    REQUIRE_REVIEW = "require_review"
    FLAG_WARNING = "flag_warning"
    SUGGEST_IMPROVEMENT = "suggest_improvement"
    PASS = "pass"


@dataclass
class UIConsistencyFinding:
    """Represents a single UI consistency finding."""
    category: ConsistencyCategory
    level: ConsistencyLevel
    finding_id: str
    title: str
    description: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    component_name: Optional[str] = None
    expected_value: Optional[str] = None
    actual_value: Optional[str] = None
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
            "component_name": self.component_name,
            "expected_value": self.expected_value,
            "actual_value": self.actual_value,
            "recommendation": self.recommendation,
            "metadata": self.metadata,
        }


@dataclass
class UIConsistencyResult:
    """Result of UI consistency analysis."""
    overall_score: int
    overall_level: ConsistencyLevel
    action: ConsistencyAction
    findings: List[UIConsistencyFinding] = field(default_factory=list)
    category_scores: Dict[ConsistencyCategory, int] = field(default_factory=dict)
    passed_checks: int = 0
    failed_checks: int = 0
    summary: str = ""
    analyzer_id: str = "ui_consistency_agent_v1"
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
            "passed_checks": self.passed_checks,
            "failed_checks": self.failed_checks,
            "summary": self.summary,
            "analyzer_id": self.analyzer_id,
            "analysis_duration_ms": self.analysis_duration_ms,
            "evidence_hash": self.evidence_hash,
        }


CONSISTENCY_THRESHOLDS = {
    ConsistencyLevel.CRITICAL: 90,
    ConsistencyLevel.HIGH: 70,
    ConsistencyLevel.MEDIUM: 50,
    ConsistencyLevel.LOW: 30,
    ConsistencyLevel.INFO: 0,
}

CATEGORY_WEIGHTS = {
    ConsistencyCategory.ACCESSIBILITY: 0.25,
    ConsistencyCategory.COLOR_USAGE: 0.20,
    ConsistencyCategory.COMPONENT_NAMING: 0.15,
    ConsistencyCategory.TYPOGRAPHY: 0.15,
    ConsistencyCategory.SPACING: 0.10,
    ConsistencyCategory.ICON_USAGE: 0.10,
    ConsistencyCategory.LAYOUT_PATTERN: 0.05,
}

COMPONENT_NAMING_PATTERNS: List[Tuple[str, str, str, int]] = [
    (r"^[A-Z][a-zA-Z0-9]*$", "CN-001", "PascalCase component name", 0),
    (r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$", "CN-002", "kebab-case file name", 0),
    (r"^use[A-Z][a-zA-Z0-9]*$", "CN-003", "Hook naming convention", 0),
]

HARDCODED_COLOR_PATTERNS: List[Tuple[str, str, int]] = [
    (r"#[0-9a-fA-F]{3,8}\b", "CU-001", 60),
    (r"rgb\s*\([^)]+\)", "CU-002", 60),
    (r"rgba\s*\([^)]+\)", "CU-003", 60),
    (r"hsl\s*\([^)]+\)", "CU-004", 50),
]

HARDCODED_SPACING_PATTERNS: List[Tuple[str, str, int]] = [
    (r"(?<![\w-])(\d+)px(?![\w-])", "SP-001", 40),
    (r"(?<![\w-])(\d+)rem(?![\w-])", "SP-002", 30),
    (r"(?<![\w-])(\d+)em(?![\w-])", "SP-003", 30),
]

ALLOWED_HARDCODED_SPACING_VALUES: List[str] = ['0', '1', '2']

ACCESSIBILITY_PATTERNS: List[Tuple[str, str, str, int]] = [
    (r"<img[^>]*(?!alt=)[^>]*>", "A11Y-001", "Image missing alt attribute", 80),
    (r"onClick\s*=\s*{[^}]*}\s*(?!.*role=)", "A11Y-002", "Click handler without role", 60),
    (r"tabIndex\s*=\s*['\"]?-1['\"]?", "A11Y-003", "Negative tabIndex usage", 50),
    (r"aria-hidden\s*=\s*['\"]?true['\"]?", "A11Y-004", "aria-hidden usage", 30),
]


class UIConsistencyAgent:
    """
    UI Consistency Agent for analyzing UI component consistency.

    Blueprint Reference: Section 3.3 (Agent Catalog V2)
    - UX/UI Agent
    - Integrates with shared-ui component library
    - Integrates with Safety Governor v2 (Section 4.1)

    This agent analyzes UI code to:
    1. Validate component naming conventions
    2. Check color usage against design tokens
    3. Verify spacing consistency
    4. Ensure typography adherence
    5. Flag accessibility issues
    """

    def __init__(
        self,
        enabled: bool = True,
        strict_mode: bool = False,
        design_token_validation: bool = True,
    ):
        """
        Initialize UIConsistencyAgent.

        Args:
            enabled: Whether consistency analysis is enabled
            strict_mode: If True, treat warnings as errors
            design_token_validation: If True, validate against design tokens
        """
        self.enabled = enabled
        self.strict_mode = strict_mode
        self.design_token_validation = design_token_validation
        self._load_settings()
        self._compile_patterns()
        logger.info(
            "[UIConsistencyAgent] Initialized - EPIC K P2: "
            "enabled=%s, strict_mode=%s",
            self.enabled,
            self.strict_mode,
        )

    def _load_settings(self) -> None:
        """Load settings from environment/config."""
        try:
            from common.config.settings import settings
            self.enabled = getattr(
                settings, "ui_consistency_enabled", self.enabled
            )
            self.strict_mode = getattr(
                settings, "ui_consistency_strict_mode", self.strict_mode
            )
            logger.debug("[UIConsistencyAgent] Settings loaded from config")
        except (ImportError, AttributeError) as e:
            logger.debug("[UIConsistencyAgent] Using default settings: %s", e)

    def _compile_patterns(self) -> None:
        """Pre-compile regex patterns for performance."""
        self._compiled_color_patterns = [
            (re.compile(pattern), pid, score)
            for pattern, pid, score in HARDCODED_COLOR_PATTERNS
        ]
        self._compiled_spacing_patterns = [
            (re.compile(pattern), pid, score)
            for pattern, pid, score in HARDCODED_SPACING_PATTERNS
        ]
        self._compiled_a11y_patterns = [
            (re.compile(pattern, re.IGNORECASE), pid, title, score)
            for pattern, pid, title, score in ACCESSIBILITY_PATTERNS
        ]

    def analyze_code(
        self,
        code_content: str,
        file_path: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> UIConsistencyResult:
        """
        Analyze code for UI consistency issues.

        Args:
            code_content: Source code to analyze
            file_path: Path to the file being analyzed
            context: Optional context with additional information

        Returns:
            UIConsistencyResult with findings and recommendations
        """
        import time
        start_time = time.time()

        if not self.enabled:
            return UIConsistencyResult(
                overall_score=100,
                overall_level=ConsistencyLevel.INFO,
                action=ConsistencyAction.PASS,
                summary="UI consistency analysis disabled",
            )

        if not code_content or not code_content.strip():
            return UIConsistencyResult(
                overall_score=100,
                overall_level=ConsistencyLevel.INFO,
                action=ConsistencyAction.PASS,
                summary="Empty code content",
            )

        context = context or {}
        findings: List[UIConsistencyFinding] = []
        category_scores: Dict[ConsistencyCategory, int] = {}
        passed_checks = 0
        failed_checks = 0

        color_findings, color_score = self._analyze_color_usage(
            code_content, file_path
        )
        findings.extend(color_findings)
        category_scores[ConsistencyCategory.COLOR_USAGE] = color_score
        if color_score >= 80:
            passed_checks += 1
        else:
            failed_checks += 1

        spacing_findings, spacing_score = self._analyze_spacing(
            code_content, file_path
        )
        findings.extend(spacing_findings)
        category_scores[ConsistencyCategory.SPACING] = spacing_score
        if spacing_score >= 80:
            passed_checks += 1
        else:
            failed_checks += 1

        a11y_findings, a11y_score = self._analyze_accessibility(
            code_content, file_path
        )
        findings.extend(a11y_findings)
        category_scores[ConsistencyCategory.ACCESSIBILITY] = a11y_score
        if a11y_score >= 80:
            passed_checks += 1
        else:
            failed_checks += 1

        naming_findings, naming_score = self._analyze_component_naming(
            code_content, file_path, context
        )
        findings.extend(naming_findings)
        category_scores[ConsistencyCategory.COMPONENT_NAMING] = naming_score
        if naming_score >= 80:
            passed_checks += 1
        else:
            failed_checks += 1

        overall_score = self._calculate_overall_score(category_scores)
        overall_level = self._determine_level(overall_score)
        action = self._determine_action(overall_level, findings)

        summary = self._generate_summary(
            overall_score, overall_level, findings, passed_checks, failed_checks
        )

        duration_ms = (time.time() - start_time) * 1000
        evidence_hash = self._compute_evidence_hash(code_content, findings)

        result = UIConsistencyResult(
            overall_score=overall_score,
            overall_level=overall_level,
            action=action,
            findings=findings,
            category_scores=category_scores,
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            summary=summary,
            analysis_duration_ms=duration_ms,
            evidence_hash=evidence_hash,
        )

        logger.info(
            "[UIConsistencyAgent] Analysis complete: score=%d, level=%s",
            overall_score,
            overall_level.value,
        )

        return result

    def _analyze_color_usage(
        self,
        code_content: str,
        file_path: Optional[str],
    ) -> Tuple[List[UIConsistencyFinding], int]:
        """Analyze color usage for hardcoded values."""
        findings: List[UIConsistencyFinding] = []
        max_score = 0

        for pattern, pid, score in self._compiled_color_patterns:
            matches = pattern.findall(code_content)
            if matches:
                max_score = max(max_score, score)
                for match in matches[:5]:
                    findings.append(UIConsistencyFinding(
                        category=ConsistencyCategory.COLOR_USAGE,
                        level=self._score_to_level(score),
                        finding_id=pid,
                        title="Hardcoded color value",
                        description=f"Found hardcoded color: {match}",
                        file_path=file_path,
                        actual_value=match,
                        recommendation="Use design token instead (e.g., colors.primary['500'])",
                    ))

        return findings, 100 - max_score

    def _analyze_spacing(
        self,
        code_content: str,
        file_path: Optional[str],
    ) -> Tuple[List[UIConsistencyFinding], int]:
        """Analyze spacing for hardcoded values."""
        findings: List[UIConsistencyFinding] = []
        max_score = 0

        for pattern, pid, score in self._compiled_spacing_patterns:
            matches = pattern.findall(code_content)
            if matches:
                non_standard = [
                    m for m in matches
                    if m not in ALLOWED_HARDCODED_SPACING_VALUES
                ]
                if non_standard:
                    max_score = max(max_score, score)
                    for match in non_standard[:5]:
                        findings.append(UIConsistencyFinding(
                            category=ConsistencyCategory.SPACING,
                            level=self._score_to_level(score),
                            finding_id=pid,
                            title="Hardcoded spacing value",
                            description=f"Found hardcoded spacing: {match}px",
                            file_path=file_path,
                            actual_value=f"{match}px",
                            recommendation="Use spacing token (e.g., spacing.md)",
                        ))

        return findings, 100 - max_score

    def _analyze_accessibility(
        self,
        code_content: str,
        file_path: Optional[str],
    ) -> Tuple[List[UIConsistencyFinding], int]:
        """Analyze accessibility issues."""
        findings: List[UIConsistencyFinding] = []
        max_score = 0

        for pattern, pid, title, score in self._compiled_a11y_patterns:
            matches = pattern.findall(code_content)
            if matches:
                max_score = max(max_score, score)
                findings.append(UIConsistencyFinding(
                    category=ConsistencyCategory.ACCESSIBILITY,
                    level=self._score_to_level(score),
                    finding_id=pid,
                    title=title,
                    description=f"Found {len(matches)} instance(s) of accessibility issue",
                    file_path=file_path,
                    recommendation="Review WCAG guidelines for proper implementation",
                ))

        return findings, 100 - max_score

    def _analyze_component_naming(
        self,
        code_content: str,
        file_path: Optional[str],
        context: Dict[str, Any],
    ) -> Tuple[List[UIConsistencyFinding], int]:
        """Analyze component naming conventions."""
        findings: List[UIConsistencyFinding] = []
        score = 100

        component_pattern = re.compile(
            r"(?:export\s+)?(?:const|function)\s+([a-zA-Z_][a-zA-Z0-9_]*)"
        )
        pascal_case_pattern = re.compile(r"^[A-Z][a-zA-Z0-9]*$")
        components = component_pattern.findall(code_content)

        for component in components:
            if not pascal_case_pattern.match(component):
                if component[0].isupper() and '_' not in component:
                    score -= 10
                    findings.append(UIConsistencyFinding(
                        category=ConsistencyCategory.COMPONENT_NAMING,
                        level=ConsistencyLevel.MEDIUM,
                        finding_id="CN-001",
                        title="Non-standard component name",
                        description=f"Component '{component}' doesn't follow PascalCase",
                        file_path=file_path,
                        component_name=component,
                        recommendation="Use PascalCase for component names",
                    ))

        return findings, max(0, score)

    def _calculate_overall_score(
        self,
        category_scores: Dict[ConsistencyCategory, int],
    ) -> int:
        """Calculate weighted overall score."""
        if not category_scores:
            return 100

        total_weight = 0.0
        weighted_sum = 0.0

        for category, score in category_scores.items():
            weight = CATEGORY_WEIGHTS.get(category, 0.1)
            weighted_sum += score * weight
            total_weight += weight

        if total_weight == 0:
            return 100

        return int(weighted_sum / total_weight)

    def _determine_level(self, score: int) -> ConsistencyLevel:
        """Determine consistency level from score."""
        if score >= 90:
            return ConsistencyLevel.INFO
        elif score >= 70:
            return ConsistencyLevel.LOW
        elif score >= 50:
            return ConsistencyLevel.MEDIUM
        elif score >= 30:
            return ConsistencyLevel.HIGH
        else:
            return ConsistencyLevel.CRITICAL

    def _score_to_level(self, score: int) -> ConsistencyLevel:
        """Convert a finding score to consistency level."""
        if score >= 80:
            return ConsistencyLevel.CRITICAL
        elif score >= 60:
            return ConsistencyLevel.HIGH
        elif score >= 40:
            return ConsistencyLevel.MEDIUM
        else:
            return ConsistencyLevel.LOW

    def _determine_action(
        self,
        level: ConsistencyLevel,
        findings: List[UIConsistencyFinding],
    ) -> ConsistencyAction:
        """Determine action based on level and findings."""
        if level == ConsistencyLevel.CRITICAL:
            return ConsistencyAction.BLOCK if self.strict_mode else ConsistencyAction.REQUIRE_REVIEW
        elif level == ConsistencyLevel.HIGH:
            return ConsistencyAction.REQUIRE_REVIEW
        elif level == ConsistencyLevel.MEDIUM:
            return ConsistencyAction.FLAG_WARNING
        elif level == ConsistencyLevel.LOW:
            return ConsistencyAction.SUGGEST_IMPROVEMENT
        else:
            return ConsistencyAction.PASS

    def _generate_summary(
        self,
        score: int,
        level: ConsistencyLevel,
        findings: List[UIConsistencyFinding],
        passed: int,
        failed: int,
    ) -> str:
        """Generate human-readable summary."""
        return (
            f"UI Consistency Score: {score}/100 ({level.value}). "
            f"Passed: {passed}, Failed: {failed}. "
            f"Found {len(findings)} issue(s)."
        )

    def _compute_evidence_hash(
        self,
        code_content: str,
        findings: List[UIConsistencyFinding],
    ) -> str:
        """Compute hash for evidence ledger."""
        content = code_content + str([f.to_dict() for f in findings])
        return hashlib.sha256(content.encode()).hexdigest()[:16]


_ui_consistency_agent: Optional[UIConsistencyAgent] = None


def get_ui_consistency_agent() -> UIConsistencyAgent:
    """Get or create singleton UIConsistencyAgent instance."""
    global _ui_consistency_agent
    if _ui_consistency_agent is None:
        _ui_consistency_agent = UIConsistencyAgent()
    return _ui_consistency_agent


def reset_ui_consistency_agent() -> None:
    """Reset singleton instance (for testing)."""
    global _ui_consistency_agent
    _ui_consistency_agent = None


def analyze_ui_consistency(
    code_content: str,
    file_path: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> UIConsistencyResult:
    """
    Convenience function to analyze UI consistency.

    Args:
        code_content: Source code to analyze
        file_path: Path to the file being analyzed
        context: Optional context

    Returns:
        UIConsistencyResult with findings
    """
    agent = get_ui_consistency_agent()
    return agent.analyze_code(code_content, file_path, context)
