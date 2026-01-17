#!/usr/bin/env python3
"""
Design Token Governance Agent - EPIC K Phase 2 (P2-medium)

Blueprint Reference: Section 3.3 (Agent Catalog V2) - UX/UI Agents
Issue: #4097 (EPIC K P2: 4 UI/UX Agents Implementation)

This module implements the Design Token Governance Agent for enforcing
design token usage and compliance. It integrates with:
- shared-ui component library (design-tokens.ts)
- Safety Governor v2 (Section 4.1) for content safety
- Evidence Ledger (Section 4.6) for audit trail

Design Principles:
- Design token usage validation
- Hardcoded value detection
- Token naming convention enforcement
- Cross-platform token consistency

Benchmark Targets (per #4121):
- Style Dictionary for token management
- Figma Tokens for design-code sync
- Theo for multi-platform token generation
"""
import hashlib
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple, Set

logger = logging.getLogger(__name__)


class ViolationType(Enum):
    """Types of design token violations.

    Blueprint Reference: Section 3.3 (Agent Catalog V2)
    """
    HARDCODED_COLOR = "hardcoded_color"
    HARDCODED_SPACING = "hardcoded_spacing"
    HARDCODED_TYPOGRAPHY = "hardcoded_typography"
    HARDCODED_SHADOW = "hardcoded_shadow"
    HARDCODED_RADIUS = "hardcoded_radius"
    INVALID_TOKEN_NAME = "invalid_token_name"
    DEPRECATED_TOKEN = "deprecated_token"
    MISSING_TOKEN = "missing_token"
    INCONSISTENT_USAGE = "inconsistent_usage"


class ViolationSeverity(Enum):
    """Severity levels for token violations."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class GovernanceAction(Enum):
    """Actions to take based on governance analysis."""
    BLOCK = "block"
    REQUIRE_REVIEW = "require_review"
    FLAG_WARNING = "flag_warning"
    SUGGEST_FIX = "suggest_fix"
    PASS = "pass"


@dataclass
class TokenViolation:
    """Represents a single token violation."""
    violation_type: ViolationType
    severity: ViolationSeverity
    finding_id: str
    title: str
    description: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    hardcoded_value: Optional[str] = None
    suggested_token: Optional[str] = None
    recommendation: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "violation_type": self.violation_type.value,
            "severity": self.severity.value,
            "finding_id": self.finding_id,
            "title": self.title,
            "description": self.description,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "hardcoded_value": self.hardcoded_value,
            "suggested_token": self.suggested_token,
            "recommendation": self.recommendation,
            "metadata": self.metadata,
        }


@dataclass
class TokenGovernanceResult:
    """Result of design token governance analysis."""
    overall_score: int
    overall_severity: ViolationSeverity
    action: GovernanceAction
    violations: List[TokenViolation] = field(default_factory=list)
    type_counts: Dict[ViolationType, int] = field(default_factory=dict)
    token_usage_count: int = 0
    hardcoded_count: int = 0
    compliance_rate: float = 100.0
    summary: str = ""
    analyzer_id: str = "design_token_agent_v1"
    analysis_duration_ms: float = 0.0
    evidence_hash: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "overall_score": self.overall_score,
            "overall_severity": self.overall_severity.value,
            "action": self.action.value,
            "violations": [v.to_dict() for v in self.violations],
            "type_counts": {k.value: v for k, v in self.type_counts.items()},
            "token_usage_count": self.token_usage_count,
            "hardcoded_count": self.hardcoded_count,
            "compliance_rate": self.compliance_rate,
            "summary": self.summary,
            "analyzer_id": self.analyzer_id,
            "analysis_duration_ms": self.analysis_duration_ms,
            "evidence_hash": self.evidence_hash,
        }


SEVERITY_THRESHOLDS = {
    ViolationSeverity.CRITICAL: 90,
    ViolationSeverity.HIGH: 70,
    ViolationSeverity.MEDIUM: 50,
    ViolationSeverity.LOW: 30,
    ViolationSeverity.INFO: 0,
}

TYPE_WEIGHTS = {
    ViolationType.HARDCODED_COLOR: 0.25,
    ViolationType.HARDCODED_SPACING: 0.20,
    ViolationType.HARDCODED_TYPOGRAPHY: 0.15,
    ViolationType.DEPRECATED_TOKEN: 0.12,
    ViolationType.INVALID_TOKEN_NAME: 0.10,
    ViolationType.HARDCODED_SHADOW: 0.08,
    ViolationType.HARDCODED_RADIUS: 0.05,
    ViolationType.MISSING_TOKEN: 0.03,
    ViolationType.INCONSISTENT_USAGE: 0.02,
}

VALID_TOKEN_PATTERNS: Set[str] = {
    r"colors\.(primary|accent|semantic|neutral|background)",
    r"spacing\.(xs|sm|md|lg|xl|2xl|3xl|4xl)",
    r"typography\.(family|size|weight|lineHeight)",
    r"radius\.(sm|md|lg|xl|2xl|full)",
    r"shadows?\.(sm|md|lg|xl|2xl)",
    r"animations?\.(duration|easing)",
    r"breakpoints?\.(mobile|tablet|desktop)",
    r"getToken\(['\"][^'\"]+['\"]\)",
    r"--color-",
    r"--spacing-",
    r"--font-",
    r"--radius-",
    r"--shadow-",
}

HARDCODED_COLOR_PATTERNS: List[Tuple[str, str, int]] = [
    (r"#[0-9a-fA-F]{3}\b", "DT-C01", 60),
    (r"#[0-9a-fA-F]{6}\b", "DT-C02", 60),
    (r"#[0-9a-fA-F]{8}\b", "DT-C03", 60),
    (r"rgb\s*\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*\)", "DT-C04", 55),
    (r"rgba\s*\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*[\d.]+\s*\)", "DT-C05", 55),
    (r"hsl\s*\(\s*\d+\s*,\s*[\d.]+%\s*,\s*[\d.]+%\s*\)", "DT-C06", 50),
]

HARDCODED_SPACING_PATTERNS: List[Tuple[str, str, int]] = [
    (r"(?<![a-zA-Z0-9_-])(\d{2,3})px(?![a-zA-Z0-9_-])", "DT-S01", 50),
    (r"(?<![a-zA-Z0-9_-])(\d+)rem(?![a-zA-Z0-9_-])", "DT-S02", 40),
    (r"(?<![a-zA-Z0-9_-])(\d+)em(?![a-zA-Z0-9_-])", "DT-S03", 40),
]

HARDCODED_TYPOGRAPHY_PATTERNS: List[Tuple[str, str, int]] = [
    (r"font-size\s*:\s*\d+px", "DT-T01", 45),
    (r"font-weight\s*:\s*\d{3}", "DT-T02", 40),
    (r"line-height\s*:\s*[\d.]+", "DT-T03", 35),
    (r"font-family\s*:\s*['\"][^'\"]+['\"]", "DT-T04", 50),
]

HARDCODED_SHADOW_PATTERNS: List[Tuple[str, str, int]] = [
    (r"box-shadow\s*:\s*[^;]+", "DT-SH01", 40),
    (r"text-shadow\s*:\s*[^;]+", "DT-SH02", 35),
]

HARDCODED_RADIUS_PATTERNS: List[Tuple[str, str, int]] = [
    (r"border-radius\s*:\s*\d+px", "DT-R01", 35),
]

ALLOWED_HARDCODED_SPACING_VALUES: List[str] = ['0', '1', '2', '100']

DEPRECATED_TOKENS: Dict[str, str] = {
    "colors.gray": "colors.neutral",
    "colors.blue": "colors.primary",
    "spacing.small": "spacing.sm",
    "spacing.medium": "spacing.md",
    "spacing.large": "spacing.lg",
}

TOKEN_SUGGESTIONS: Dict[str, str] = {
    "#4D7CFE": "colors.primary['500']",
    "#EEF2FF": "colors.primary['50']",
    "#1E1B4B": "colors.primary['900']",
    "#8b5cf6": "colors.accent.purple['500']",
    "#FFAB2B": "colors.accent.orange['500']",
    "#6DD230": "colors.semantic.success['500']",
    "#ef4444": "colors.semantic.error['500']",
    "#0ea5e9": "colors.semantic.info['500']",
    "4px": "spacing.xs",
    "8px": "spacing.sm",
    "16px": "spacing.md",
    "24px": "spacing.lg",
    "32px": "spacing.xl",
}


class DesignTokenGovernanceAgent:
    """
    Design Token Governance Agent for enforcing design token compliance.

    Blueprint Reference: Section 3.3 (Agent Catalog V2)
    - UX/UI Agent
    - Integrates with shared-ui component library
    - Integrates with Safety Governor v2 (Section 4.1)

    This agent analyzes code to:
    1. Detect hardcoded color values
    2. Identify hardcoded spacing
    3. Flag hardcoded typography
    4. Check for deprecated tokens
    5. Suggest appropriate design tokens
    """

    def __init__(
        self,
        enabled: bool = True,
        strict_mode: bool = False,
        auto_suggest: bool = True,
    ):
        """
        Initialize DesignTokenGovernanceAgent.

        Args:
            enabled: Whether token governance is enabled
            strict_mode: If True, treat warnings as errors
            auto_suggest: If True, suggest replacement tokens
        """
        self.enabled = enabled
        self.strict_mode = strict_mode
        self.auto_suggest = auto_suggest
        self._load_settings()
        self._compile_patterns()
        logger.info(
            "[DesignTokenGovernanceAgent] Initialized - EPIC K P2: "
            "enabled=%s, strict_mode=%s",
            self.enabled,
            self.strict_mode,
        )

    def _load_settings(self) -> None:
        """Load settings from environment/config."""
        try:
            from common.config.settings import settings
            self.enabled = getattr(
                settings, "design_token_governance_enabled", self.enabled
            )
            self.strict_mode = getattr(
                settings, "design_token_strict_mode", self.strict_mode
            )
            logger.debug("[DesignTokenGovernanceAgent] Settings loaded from config")
        except (ImportError, AttributeError) as e:
            logger.debug("[DesignTokenGovernanceAgent] Using default settings: %s", e)

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
        self._compiled_typography_patterns = [
            (re.compile(pattern), pid, score)
            for pattern, pid, score in HARDCODED_TYPOGRAPHY_PATTERNS
        ]
        self._compiled_shadow_patterns = [
            (re.compile(pattern), pid, score)
            for pattern, pid, score in HARDCODED_SHADOW_PATTERNS
        ]
        self._compiled_radius_patterns = [
            (re.compile(pattern), pid, score)
            for pattern, pid, score in HARDCODED_RADIUS_PATTERNS
        ]
        self._compiled_valid_tokens = [
            re.compile(pattern) for pattern in VALID_TOKEN_PATTERNS
        ]

    def analyze_code(
        self,
        code_content: str,
        file_path: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> TokenGovernanceResult:
        """
        Analyze code for design token compliance.

        Args:
            code_content: Source code to analyze
            file_path: Path to the file being analyzed
            context: Optional context with additional information

        Returns:
            TokenGovernanceResult with violations and recommendations
        """
        import time
        start_time = time.time()

        if not self.enabled:
            return TokenGovernanceResult(
                overall_score=100,
                overall_severity=ViolationSeverity.INFO,
                action=GovernanceAction.PASS,
                summary="Design token governance disabled",
            )

        if not code_content or not code_content.strip():
            return TokenGovernanceResult(
                overall_score=100,
                overall_severity=ViolationSeverity.INFO,
                action=GovernanceAction.PASS,
                summary="Empty code content",
            )

        context = context or {}
        violations: List[TokenViolation] = []
        type_counts: Dict[ViolationType, int] = {t: 0 for t in ViolationType}

        token_usage_count = self._count_token_usage(code_content)

        color_violations = self._analyze_colors(code_content, file_path)
        violations.extend(color_violations)
        type_counts[ViolationType.HARDCODED_COLOR] = len(color_violations)

        spacing_violations = self._analyze_spacing(code_content, file_path)
        violations.extend(spacing_violations)
        type_counts[ViolationType.HARDCODED_SPACING] = len(spacing_violations)

        typography_violations = self._analyze_typography(code_content, file_path)
        violations.extend(typography_violations)
        type_counts[ViolationType.HARDCODED_TYPOGRAPHY] = len(typography_violations)

        shadow_violations = self._analyze_shadows(code_content, file_path)
        violations.extend(shadow_violations)
        type_counts[ViolationType.HARDCODED_SHADOW] = len(shadow_violations)

        radius_violations = self._analyze_radius(code_content, file_path)
        violations.extend(radius_violations)
        type_counts[ViolationType.HARDCODED_RADIUS] = len(radius_violations)

        deprecated_violations = self._analyze_deprecated_tokens(code_content, file_path)
        violations.extend(deprecated_violations)
        type_counts[ViolationType.DEPRECATED_TOKEN] = len(deprecated_violations)

        hardcoded_count = len(violations)
        total_style_refs = token_usage_count + hardcoded_count
        compliance_rate = (
            (token_usage_count / total_style_refs * 100)
            if total_style_refs > 0 else 100.0
        )

        overall_score = self._calculate_overall_score(violations, compliance_rate)
        overall_severity = self._determine_severity(overall_score)
        action = self._determine_action(overall_severity, violations)

        summary = self._generate_summary(
            overall_score, overall_severity, violations,
            token_usage_count, hardcoded_count, compliance_rate
        )

        duration_ms = (time.time() - start_time) * 1000
        evidence_hash = self._compute_evidence_hash(code_content, violations)

        result = TokenGovernanceResult(
            overall_score=overall_score,
            overall_severity=overall_severity,
            action=action,
            violations=violations,
            type_counts=type_counts,
            token_usage_count=token_usage_count,
            hardcoded_count=hardcoded_count,
            compliance_rate=round(compliance_rate, 2),
            summary=summary,
            analysis_duration_ms=duration_ms,
            evidence_hash=evidence_hash,
        )

        logger.info(
            "[DesignTokenGovernanceAgent] Analysis complete: score=%d, compliance=%.1f%%",
            overall_score,
            compliance_rate,
        )

        return result

    def _count_token_usage(self, code_content: str) -> int:
        """Count valid design token usages."""
        count = 0
        for pattern in self._compiled_valid_tokens:
            matches = pattern.findall(code_content)
            count += len(matches)
        return count

    def _analyze_colors(
        self,
        code_content: str,
        file_path: Optional[str],
    ) -> List[TokenViolation]:
        """Analyze hardcoded color values."""
        violations: List[TokenViolation] = []

        for pattern, pid, score in self._compiled_color_patterns:
            matches = pattern.findall(code_content)
            for match in matches[:10]:
                suggested = TOKEN_SUGGESTIONS.get(match.upper(), None)
                if suggested is None:
                    suggested = TOKEN_SUGGESTIONS.get(match.lower(), None)

                violations.append(TokenViolation(
                    violation_type=ViolationType.HARDCODED_COLOR,
                    severity=self._score_to_severity(score),
                    finding_id=pid,
                    title="Hardcoded color value",
                    description=f"Found hardcoded color: {match}",
                    file_path=file_path,
                    hardcoded_value=match,
                    suggested_token=suggested,
                    recommendation=(
                        f"Replace with {suggested}" if suggested
                        else "Use a design token from colors.*"
                    ),
                ))

        return violations

    def _analyze_spacing(
        self,
        code_content: str,
        file_path: Optional[str],
    ) -> List[TokenViolation]:
        """Analyze hardcoded spacing values."""
        violations: List[TokenViolation] = []

        for pattern, pid, score in self._compiled_spacing_patterns:
            matches = pattern.findall(code_content)
            for match in matches[:10]:
                if isinstance(match, tuple):
                    match = match[0]
                value_with_unit = f"{match}px"
                suggested = TOKEN_SUGGESTIONS.get(value_with_unit, None)

                if match in ALLOWED_HARDCODED_SPACING_VALUES:
                    continue

                violations.append(TokenViolation(
                    violation_type=ViolationType.HARDCODED_SPACING,
                    severity=self._score_to_severity(score),
                    finding_id=pid,
                    title="Hardcoded spacing value",
                    description=f"Found hardcoded spacing: {match}",
                    file_path=file_path,
                    hardcoded_value=match,
                    suggested_token=suggested,
                    recommendation=(
                        f"Replace with {suggested}" if suggested
                        else "Use a design token from spacing.*"
                    ),
                ))

        return violations

    def _analyze_typography(
        self,
        code_content: str,
        file_path: Optional[str],
    ) -> List[TokenViolation]:
        """Analyze hardcoded typography values."""
        violations: List[TokenViolation] = []

        for pattern, pid, score in self._compiled_typography_patterns:
            matches = pattern.findall(code_content)
            if matches:
                for match in matches[:5]:
                    violations.append(TokenViolation(
                        violation_type=ViolationType.HARDCODED_TYPOGRAPHY,
                        severity=self._score_to_severity(score),
                        finding_id=pid,
                        title="Hardcoded typography value",
                        description=f"Found hardcoded typography: {match}",
                        file_path=file_path,
                        hardcoded_value=match,
                        recommendation="Use typography tokens from typography.*",
                    ))

        return violations

    def _analyze_shadows(
        self,
        code_content: str,
        file_path: Optional[str],
    ) -> List[TokenViolation]:
        """Analyze hardcoded shadow values."""
        violations: List[TokenViolation] = []

        for pattern, pid, score in self._compiled_shadow_patterns:
            matches = pattern.findall(code_content)
            if matches:
                for match in matches[:3]:
                    violations.append(TokenViolation(
                        violation_type=ViolationType.HARDCODED_SHADOW,
                        severity=self._score_to_severity(score),
                        finding_id=pid,
                        title="Hardcoded shadow value",
                        description=f"Found hardcoded shadow: {match[:50]}...",
                        file_path=file_path,
                        hardcoded_value=match[:50],
                        recommendation="Use shadow tokens from shadows.*",
                    ))

        return violations

    def _analyze_radius(
        self,
        code_content: str,
        file_path: Optional[str],
    ) -> List[TokenViolation]:
        """Analyze hardcoded border-radius values."""
        violations: List[TokenViolation] = []

        for pattern, pid, score in self._compiled_radius_patterns:
            matches = pattern.findall(code_content)
            if matches:
                for match in matches[:5]:
                    violations.append(TokenViolation(
                        violation_type=ViolationType.HARDCODED_RADIUS,
                        severity=self._score_to_severity(score),
                        finding_id=pid,
                        title="Hardcoded border-radius value",
                        description=f"Found hardcoded radius: {match}",
                        file_path=file_path,
                        hardcoded_value=match,
                        recommendation="Use radius tokens from radius.*",
                    ))

        return violations

    def _analyze_deprecated_tokens(
        self,
        code_content: str,
        file_path: Optional[str],
    ) -> List[TokenViolation]:
        """Analyze deprecated token usage."""
        violations: List[TokenViolation] = []

        for deprecated, replacement in DEPRECATED_TOKENS.items():
            if deprecated in code_content:
                violations.append(TokenViolation(
                    violation_type=ViolationType.DEPRECATED_TOKEN,
                    severity=ViolationSeverity.MEDIUM,
                    finding_id="DT-DEP01",
                    title="Deprecated token usage",
                    description=f"Found deprecated token: {deprecated}",
                    file_path=file_path,
                    hardcoded_value=deprecated,
                    suggested_token=replacement,
                    recommendation=f"Replace with {replacement}",
                ))

        return violations

    def _calculate_overall_score(
        self,
        violations: List[TokenViolation],
        compliance_rate: float,
    ) -> int:
        """Calculate overall score based on violations, compliance, and TYPE_WEIGHTS."""
        if not violations:
            return 100

        base_score = int(compliance_rate)

        total_deduction = 0
        for violation in violations:
            weight = TYPE_WEIGHTS.get(violation.violation_type, 0.05)
            severity_multiplier = {
                ViolationSeverity.CRITICAL: 15,
                ViolationSeverity.HIGH: 10,
                ViolationSeverity.MEDIUM: 5,
                ViolationSeverity.LOW: 2,
                ViolationSeverity.INFO: 1,
            }.get(violation.severity, 1)
            total_deduction += int(severity_multiplier * (1 + weight))

        return max(0, min(base_score, 100 - total_deduction))

    def _determine_severity(self, score: int) -> ViolationSeverity:
        """Determine severity from score using SEVERITY_THRESHOLDS."""
        if score >= SEVERITY_THRESHOLDS[ViolationSeverity.CRITICAL]:
            return ViolationSeverity.INFO
        elif score >= SEVERITY_THRESHOLDS[ViolationSeverity.HIGH]:
            return ViolationSeverity.LOW
        elif score >= SEVERITY_THRESHOLDS[ViolationSeverity.MEDIUM]:
            return ViolationSeverity.MEDIUM
        elif score >= SEVERITY_THRESHOLDS[ViolationSeverity.LOW]:
            return ViolationSeverity.HIGH
        else:
            return ViolationSeverity.CRITICAL

    def _score_to_severity(self, score: int) -> ViolationSeverity:
        """Convert a finding score to severity."""
        if score >= 60:
            return ViolationSeverity.HIGH
        elif score >= 45:
            return ViolationSeverity.MEDIUM
        elif score >= 30:
            return ViolationSeverity.LOW
        else:
            return ViolationSeverity.INFO

    def _determine_action(
        self,
        severity: ViolationSeverity,
        violations: List[TokenViolation],
    ) -> GovernanceAction:
        """Determine action based on severity and violations."""
        if severity == ViolationSeverity.CRITICAL:
            return GovernanceAction.BLOCK if self.strict_mode else GovernanceAction.REQUIRE_REVIEW
        elif severity == ViolationSeverity.HIGH:
            return GovernanceAction.REQUIRE_REVIEW
        elif severity == ViolationSeverity.MEDIUM:
            return GovernanceAction.FLAG_WARNING
        elif severity == ViolationSeverity.LOW:
            return GovernanceAction.SUGGEST_FIX
        else:
            return GovernanceAction.PASS

    def _generate_summary(
        self,
        score: int,
        severity: ViolationSeverity,
        violations: List[TokenViolation],
        token_count: int,
        hardcoded_count: int,
        compliance_rate: float,
    ) -> str:
        """Generate human-readable summary."""
        return (
            f"Design Token Score: {score}/100 ({severity.value}). "
            f"Compliance: {compliance_rate:.1f}%. "
            f"Token usage: {token_count}, Hardcoded: {hardcoded_count}. "
            f"Found {len(violations)} violation(s)."
        )

    def _compute_evidence_hash(
        self,
        code_content: str,
        violations: List[TokenViolation],
    ) -> str:
        """Compute hash for evidence ledger."""
        content = code_content + str([v.to_dict() for v in violations])
        return hashlib.sha256(content.encode()).hexdigest()[:16]


_design_token_agent: Optional[DesignTokenGovernanceAgent] = None


def get_design_token_agent() -> DesignTokenGovernanceAgent:
    """Get or create singleton DesignTokenGovernanceAgent instance."""
    global _design_token_agent
    if _design_token_agent is None:
        _design_token_agent = DesignTokenGovernanceAgent()
    return _design_token_agent


def reset_design_token_agent() -> None:
    """Reset singleton instance (for testing)."""
    global _design_token_agent
    _design_token_agent = None


def analyze_design_tokens(
    code_content: str,
    file_path: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> TokenGovernanceResult:
    """
    Convenience function to analyze design token compliance.

    Args:
        code_content: Source code to analyze
        file_path: Path to the file being analyzed
        context: Optional context

    Returns:
        TokenGovernanceResult with violations
    """
    agent = get_design_token_agent()
    return agent.analyze_code(code_content, file_path, context)
