#!/usr/bin/env python3
"""
Visual Regression Agent - EPIC K Phase 2 (P2-medium)

Blueprint Reference: Section 3.3 (Agent Catalog V2) - UX/UI Agents
Issue: #4097 (EPIC K P2: 4 UI/UX Agents Implementation)

This module implements the Visual Regression Agent for detecting visual
changes and regressions in UI components. It integrates with:
- Safety Governor v2 (Section 4.1) for content safety
- Evidence Ledger (Section 4.6) for audit trail
- BrowserNode v2 (Section 3.4) for screenshot capture

Design Principles:
- CSS change impact analysis
- Layout shift detection
- Component visual diff detection
- Responsive breakpoint validation

Benchmark Targets (per #4121):
- Percy for visual regression testing
- Chromatic for Storybook visual testing
- BackstopJS for responsive testing
"""
import hashlib
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple, Set

logger = logging.getLogger(__name__)


class RegressionType(Enum):
    """Types of visual regressions.

    Blueprint Reference: Section 3.3 (Agent Catalog V2)
    """
    LAYOUT_SHIFT = "layout_shift"
    COLOR_CHANGE = "color_change"
    TYPOGRAPHY_CHANGE = "typography_change"
    SPACING_CHANGE = "spacing_change"
    SIZE_CHANGE = "size_change"
    VISIBILITY_CHANGE = "visibility_change"
    ANIMATION_CHANGE = "animation_change"
    RESPONSIVE_BREAK = "responsive_break"


class RegressionSeverity(Enum):
    """Severity levels for visual regressions."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class RegressionAction(Enum):
    """Actions to take based on regression analysis."""
    BLOCK = "block"
    REQUIRE_REVIEW = "require_review"
    FLAG_WARNING = "flag_warning"
    SUGGEST_REVIEW = "suggest_review"
    PASS = "pass"


@dataclass
class VisualRegressionFinding:
    """Represents a single visual regression finding."""
    regression_type: RegressionType
    severity: RegressionSeverity
    finding_id: str
    title: str
    description: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    css_property: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    affected_components: List[str] = field(default_factory=list)
    recommendation: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "regression_type": self.regression_type.value,
            "severity": self.severity.value,
            "finding_id": self.finding_id,
            "title": self.title,
            "description": self.description,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "css_property": self.css_property,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "affected_components": self.affected_components,
            "recommendation": self.recommendation,
            "metadata": self.metadata,
        }


@dataclass
class VisualRegressionResult:
    """Result of visual regression analysis."""
    overall_score: int
    overall_severity: RegressionSeverity
    action: RegressionAction
    findings: List[VisualRegressionFinding] = field(default_factory=list)
    type_counts: Dict[RegressionType, int] = field(default_factory=dict)
    affected_files: int = 0
    total_changes: int = 0
    summary: str = ""
    analyzer_id: str = "visual_regression_agent_v1"
    analysis_duration_ms: float = 0.0
    evidence_hash: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "overall_score": self.overall_score,
            "overall_severity": self.overall_severity.value,
            "action": self.action.value,
            "findings": [f.to_dict() for f in self.findings],
            "type_counts": {k.value: v for k, v in self.type_counts.items()},
            "affected_files": self.affected_files,
            "total_changes": self.total_changes,
            "summary": self.summary,
            "analyzer_id": self.analyzer_id,
            "analysis_duration_ms": self.analysis_duration_ms,
            "evidence_hash": self.evidence_hash,
        }


SEVERITY_THRESHOLDS = {
    RegressionSeverity.CRITICAL: 90,
    RegressionSeverity.HIGH: 70,
    RegressionSeverity.MEDIUM: 50,
    RegressionSeverity.LOW: 30,
    RegressionSeverity.INFO: 0,
}

TYPE_WEIGHTS = {
    RegressionType.LAYOUT_SHIFT: 0.20,
    RegressionType.VISIBILITY_CHANGE: 0.18,
    RegressionType.SIZE_CHANGE: 0.15,
    RegressionType.COLOR_CHANGE: 0.12,
    RegressionType.TYPOGRAPHY_CHANGE: 0.12,
    RegressionType.SPACING_CHANGE: 0.10,
    RegressionType.RESPONSIVE_BREAK: 0.08,
    RegressionType.ANIMATION_CHANGE: 0.05,
}

LAYOUT_PROPERTIES: Set[str] = {
    "display", "position", "float", "clear",
    "flex", "flex-direction", "flex-wrap", "justify-content", "align-items",
    "grid", "grid-template-columns", "grid-template-rows",
    "top", "right", "bottom", "left",
    "transform", "translate", "rotate", "scale",
}

SIZE_PROPERTIES: Set[str] = {
    "width", "height", "min-width", "min-height", "max-width", "max-height",
    "padding", "padding-top", "padding-right", "padding-bottom", "padding-left",
    "margin", "margin-top", "margin-right", "margin-bottom", "margin-left",
}

COLOR_PROPERTIES: Set[str] = {
    "color", "background", "background-color",
    "border-color", "outline-color",
    "fill", "stroke",
}

TYPOGRAPHY_PROPERTIES: Set[str] = {
    "font-family", "font-size", "font-weight", "font-style",
    "line-height", "letter-spacing", "text-align", "text-decoration",
}

VISIBILITY_PROPERTIES: Set[str] = {
    "visibility", "opacity", "display", "overflow", "z-index",
}

HIGH_IMPACT_PATTERNS: List[Tuple[str, str, RegressionType, int]] = [
    (
        r"display\s*:\s*none",
        "VR-001",
        RegressionType.VISIBILITY_CHANGE,
        80,
    ),
    (
        r"visibility\s*:\s*hidden",
        "VR-002",
        RegressionType.VISIBILITY_CHANGE,
        70,
    ),
    (
        r"opacity\s*:\s*0(?![.\d])",
        "VR-003",
        RegressionType.VISIBILITY_CHANGE,
        60,
    ),
    (
        r"position\s*:\s*(?:absolute|fixed)",
        "VR-004",
        RegressionType.LAYOUT_SHIFT,
        50,
    ),
    (
        r"transform\s*:\s*(?:translate|scale|rotate)",
        "VR-005",
        RegressionType.LAYOUT_SHIFT,
        40,
    ),
    (
        r"@media\s*\([^)]*\)",
        "VR-006",
        RegressionType.RESPONSIVE_BREAK,
        30,
    ),
]

CSS_CHANGE_PATTERN = re.compile(
    r"([a-zA-Z-]+)\s*:\s*([^;}\n]+)"
)


class VisualRegressionAgent:
    """
    Visual Regression Agent for detecting visual changes and regressions.

    Blueprint Reference: Section 3.3 (Agent Catalog V2)
    - UX/UI Agent
    - Integrates with BrowserNode v2 (Section 3.4)
    - Integrates with Safety Governor v2 (Section 4.1)

    This agent analyzes CSS/style changes to:
    1. Detect layout shifts
    2. Identify color changes
    3. Flag typography modifications
    4. Check spacing consistency
    5. Validate responsive breakpoints
    """

    def __init__(
        self,
        enabled: bool = True,
        strict_mode: bool = False,
        track_all_changes: bool = True,
    ):
        """
        Initialize VisualRegressionAgent.

        Args:
            enabled: Whether regression analysis is enabled
            strict_mode: If True, treat minor changes as major
            track_all_changes: If True, track all CSS changes
        """
        self.enabled = enabled
        self.strict_mode = strict_mode
        self.track_all_changes = track_all_changes
        self._load_settings()
        self._compile_patterns()
        logger.info(
            "[VisualRegressionAgent] Initialized - EPIC K P2: "
            "enabled=%s, strict_mode=%s",
            self.enabled,
            self.strict_mode,
        )

    def _load_settings(self) -> None:
        """Load settings from environment/config."""
        try:
            from common.config.settings import settings
            self.enabled = getattr(
                settings, "visual_regression_enabled", self.enabled
            )
            self.strict_mode = getattr(
                settings, "visual_regression_strict_mode", self.strict_mode
            )
            logger.debug("[VisualRegressionAgent] Settings loaded from config")
        except (ImportError, AttributeError) as e:
            logger.debug("[VisualRegressionAgent] Using default settings: %s", e)

    def _compile_patterns(self) -> None:
        """Pre-compile regex patterns for performance."""
        self._compiled_high_impact = [
            (re.compile(pattern, re.IGNORECASE), pid, reg_type, score)
            for pattern, pid, reg_type, score in HIGH_IMPACT_PATTERNS
        ]

    def analyze_changes(
        self,
        old_content: str,
        new_content: str,
        file_path: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> VisualRegressionResult:
        """
        Analyze CSS/style changes for visual regressions.

        Args:
            old_content: Original CSS/style content
            new_content: Modified CSS/style content
            file_path: Path to the file being analyzed
            context: Optional context with additional information

        Returns:
            VisualRegressionResult with findings and recommendations
        """
        import time
        start_time = time.time()

        if not self.enabled:
            return VisualRegressionResult(
                overall_score=100,
                overall_severity=RegressionSeverity.INFO,
                action=RegressionAction.PASS,
                summary="Visual regression analysis disabled",
            )

        context = context or {}
        findings: List[VisualRegressionFinding] = []
        type_counts: Dict[RegressionType, int] = {t: 0 for t in RegressionType}

        old_props = self._extract_css_properties(old_content)
        new_props = self._extract_css_properties(new_content)

        change_findings = self._analyze_property_changes(
            old_props, new_props, file_path
        )
        findings.extend(change_findings)

        for finding in change_findings:
            type_counts[finding.regression_type] += 1

        impact_findings = self._analyze_high_impact_patterns(
            new_content, file_path
        )
        findings.extend(impact_findings)

        for finding in impact_findings:
            type_counts[finding.regression_type] += 1

        total_changes = len(change_findings)
        overall_score = self._calculate_overall_score(findings)
        overall_severity = self._determine_severity(overall_score)
        action = self._determine_action(overall_severity, findings)

        summary = self._generate_summary(
            overall_score, overall_severity, findings, total_changes
        )

        duration_ms = (time.time() - start_time) * 1000
        evidence_hash = self._compute_evidence_hash(old_content, new_content, findings)

        result = VisualRegressionResult(
            overall_score=overall_score,
            overall_severity=overall_severity,
            action=action,
            findings=findings,
            type_counts=type_counts,
            affected_files=1 if findings else 0,
            total_changes=total_changes,
            summary=summary,
            analysis_duration_ms=duration_ms,
            evidence_hash=evidence_hash,
        )

        logger.info(
            "[VisualRegressionAgent] Analysis complete: score=%d, severity=%s",
            overall_score,
            overall_severity.value,
        )

        return result

    def analyze_code(
        self,
        code_content: str,
        file_path: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> VisualRegressionResult:
        """
        Analyze code for potential visual regression risks.

        This is a single-file analysis (no diff comparison).

        Args:
            code_content: Source code to analyze
            file_path: Path to the file being analyzed
            context: Optional context

        Returns:
            VisualRegressionResult with findings
        """
        import time
        start_time = time.time()

        if not self.enabled:
            return VisualRegressionResult(
                overall_score=100,
                overall_severity=RegressionSeverity.INFO,
                action=RegressionAction.PASS,
                summary="Visual regression analysis disabled",
            )

        if not code_content or not code_content.strip():
            return VisualRegressionResult(
                overall_score=100,
                overall_severity=RegressionSeverity.INFO,
                action=RegressionAction.PASS,
                summary="Empty code content",
            )

        context = context or {}
        findings: List[VisualRegressionFinding] = []
        type_counts: Dict[RegressionType, int] = {t: 0 for t in RegressionType}

        impact_findings = self._analyze_high_impact_patterns(
            code_content, file_path
        )
        findings.extend(impact_findings)

        for finding in impact_findings:
            type_counts[finding.regression_type] += 1

        overall_score = self._calculate_overall_score(findings)
        overall_severity = self._determine_severity(overall_score)
        action = self._determine_action(overall_severity, findings)

        summary = self._generate_summary(
            overall_score, overall_severity, findings, len(findings)
        )

        duration_ms = (time.time() - start_time) * 1000
        evidence_hash = self._compute_evidence_hash("", code_content, findings)

        result = VisualRegressionResult(
            overall_score=overall_score,
            overall_severity=overall_severity,
            action=action,
            findings=findings,
            type_counts=type_counts,
            affected_files=1 if findings else 0,
            total_changes=len(findings),
            summary=summary,
            analysis_duration_ms=duration_ms,
            evidence_hash=evidence_hash,
        )

        logger.info(
            "[VisualRegressionAgent] Analysis complete: score=%d, severity=%s",
            overall_score,
            overall_severity.value,
        )

        return result

    def _extract_css_properties(
        self,
        content: str,
    ) -> Dict[str, str]:
        """Extract CSS properties from content."""
        properties: Dict[str, str] = {}
        matches = CSS_CHANGE_PATTERN.findall(content)
        for prop, value in matches:
            properties[prop.strip().lower()] = value.strip()
        return properties

    def _analyze_property_changes(
        self,
        old_props: Dict[str, str],
        new_props: Dict[str, str],
        file_path: Optional[str],
    ) -> List[VisualRegressionFinding]:
        """Analyze CSS property changes."""
        findings: List[VisualRegressionFinding] = []

        all_props = set(old_props.keys()) | set(new_props.keys())

        for prop in all_props:
            old_val = old_props.get(prop)
            new_val = new_props.get(prop)

            if old_val == new_val:
                continue

            reg_type = self._classify_property(prop)
            severity = self._assess_change_severity(prop, old_val, new_val)

            if old_val is None:
                title = f"New CSS property: {prop}"
                description = f"Added {prop}: {new_val}"
            elif new_val is None:
                title = f"Removed CSS property: {prop}"
                description = f"Removed {prop} (was: {old_val})"
            else:
                title = f"Changed CSS property: {prop}"
                description = f"Changed {prop} from '{old_val}' to '{new_val}'"

            findings.append(VisualRegressionFinding(
                regression_type=reg_type,
                severity=severity,
                finding_id=f"CSS-{prop.upper()[:8]}",
                title=title,
                description=description,
                file_path=file_path,
                css_property=prop,
                old_value=old_val,
                new_value=new_val,
                recommendation=f"Review visual impact of {prop} change",
            ))

        return findings

    def _analyze_high_impact_patterns(
        self,
        content: str,
        file_path: Optional[str],
    ) -> List[VisualRegressionFinding]:
        """Analyze high-impact visual patterns."""
        findings: List[VisualRegressionFinding] = []

        for pattern, pid, reg_type, score in self._compiled_high_impact:
            matches = pattern.findall(content)
            if matches:
                findings.append(VisualRegressionFinding(
                    regression_type=reg_type,
                    severity=self._score_to_severity(score),
                    finding_id=pid,
                    title=f"High-impact visual pattern: {reg_type.value}",
                    description=f"Found {len(matches)} instance(s) of pattern",
                    file_path=file_path,
                    recommendation="Review for unintended visual changes",
                ))

        return findings

    def _classify_property(self, prop: str) -> RegressionType:
        """Classify CSS property into regression type."""
        prop_lower = prop.lower()

        if prop_lower in LAYOUT_PROPERTIES:
            return RegressionType.LAYOUT_SHIFT
        elif prop_lower in SIZE_PROPERTIES:
            return RegressionType.SIZE_CHANGE
        elif prop_lower in COLOR_PROPERTIES:
            return RegressionType.COLOR_CHANGE
        elif prop_lower in TYPOGRAPHY_PROPERTIES:
            return RegressionType.TYPOGRAPHY_CHANGE
        elif prop_lower in VISIBILITY_PROPERTIES:
            return RegressionType.VISIBILITY_CHANGE
        elif "animation" in prop_lower or "transition" in prop_lower:
            return RegressionType.ANIMATION_CHANGE
        else:
            return RegressionType.SPACING_CHANGE

    def _assess_change_severity(
        self,
        prop: str,
        old_val: Optional[str],
        new_val: Optional[str],
    ) -> RegressionSeverity:
        """Assess severity of a CSS property change."""
        prop_lower = prop.lower()

        if prop_lower in LAYOUT_PROPERTIES:
            return RegressionSeverity.HIGH
        elif prop_lower in VISIBILITY_PROPERTIES:
            return RegressionSeverity.HIGH
        elif prop_lower in SIZE_PROPERTIES:
            return RegressionSeverity.MEDIUM
        elif prop_lower in COLOR_PROPERTIES:
            return RegressionSeverity.MEDIUM
        elif prop_lower in TYPOGRAPHY_PROPERTIES:
            return RegressionSeverity.LOW
        else:
            return RegressionSeverity.INFO

    def _calculate_overall_score(
        self,
        findings: List[VisualRegressionFinding],
    ) -> int:
        """Calculate overall score based on findings."""
        if not findings:
            return 100

        total_deduction = 0
        for finding in findings:
            if finding.severity == RegressionSeverity.CRITICAL:
                total_deduction += 30
            elif finding.severity == RegressionSeverity.HIGH:
                total_deduction += 20
            elif finding.severity == RegressionSeverity.MEDIUM:
                total_deduction += 10
            elif finding.severity == RegressionSeverity.LOW:
                total_deduction += 5
            else:
                total_deduction += 2

        return max(0, 100 - total_deduction)

    def _determine_severity(self, score: int) -> RegressionSeverity:
        """Determine severity from score."""
        if score >= 90:
            return RegressionSeverity.INFO
        elif score >= 70:
            return RegressionSeverity.LOW
        elif score >= 50:
            return RegressionSeverity.MEDIUM
        elif score >= 30:
            return RegressionSeverity.HIGH
        else:
            return RegressionSeverity.CRITICAL

    def _score_to_severity(self, score: int) -> RegressionSeverity:
        """Convert a finding score to severity."""
        if score >= 70:
            return RegressionSeverity.HIGH
        elif score >= 50:
            return RegressionSeverity.MEDIUM
        elif score >= 30:
            return RegressionSeverity.LOW
        else:
            return RegressionSeverity.INFO

    def _determine_action(
        self,
        severity: RegressionSeverity,
        findings: List[VisualRegressionFinding],
    ) -> RegressionAction:
        """Determine action based on severity and findings."""
        if severity == RegressionSeverity.CRITICAL:
            return RegressionAction.BLOCK if self.strict_mode else RegressionAction.REQUIRE_REVIEW
        elif severity == RegressionSeverity.HIGH:
            return RegressionAction.REQUIRE_REVIEW
        elif severity == RegressionSeverity.MEDIUM:
            return RegressionAction.FLAG_WARNING
        elif severity == RegressionSeverity.LOW:
            return RegressionAction.SUGGEST_REVIEW
        else:
            return RegressionAction.PASS

    def _generate_summary(
        self,
        score: int,
        severity: RegressionSeverity,
        findings: List[VisualRegressionFinding],
        total_changes: int,
    ) -> str:
        """Generate human-readable summary."""
        return (
            f"Visual Regression Score: {score}/100 ({severity.value}). "
            f"Total changes: {total_changes}. "
            f"Found {len(findings)} potential regression(s)."
        )

    def _compute_evidence_hash(
        self,
        old_content: str,
        new_content: str,
        findings: List[VisualRegressionFinding],
    ) -> str:
        """Compute hash for evidence ledger."""
        content = old_content + new_content + str([f.to_dict() for f in findings])
        return hashlib.sha256(content.encode()).hexdigest()[:16]


_visual_regression_agent: Optional[VisualRegressionAgent] = None


def get_visual_regression_agent() -> VisualRegressionAgent:
    """Get or create singleton VisualRegressionAgent instance."""
    global _visual_regression_agent
    if _visual_regression_agent is None:
        _visual_regression_agent = VisualRegressionAgent()
    return _visual_regression_agent


def reset_visual_regression_agent() -> None:
    """Reset singleton instance (for testing)."""
    global _visual_regression_agent
    _visual_regression_agent = None


def analyze_visual_regression(
    old_content: str,
    new_content: str,
    file_path: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> VisualRegressionResult:
    """
    Convenience function to analyze visual regressions.

    Args:
        old_content: Original CSS/style content
        new_content: Modified CSS/style content
        file_path: Path to the file being analyzed
        context: Optional context

    Returns:
        VisualRegressionResult with findings
    """
    agent = get_visual_regression_agent()
    return agent.analyze_changes(old_content, new_content, file_path, context)
