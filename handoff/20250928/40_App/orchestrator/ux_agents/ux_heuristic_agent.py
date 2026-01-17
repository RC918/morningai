#!/usr/bin/env python3
"""
UX Heuristic Agent - EPIC K Phase 2 (P2-medium)

Blueprint Reference: Section 3.3 (Agent Catalog V2) - UX/UI Agents
Issue: #4097 (EPIC K P2: 4 UI/UX Agents Implementation)

This module implements the UX Heuristic Agent for evaluating UX patterns
against Nielsen's 10 Usability Heuristics. It integrates with:
- Safety Governor v2 (Section 4.1) for content safety
- Evidence Ledger (Section 4.6) for audit trail

Design Principles:
- Nielsen's 10 Usability Heuristics evaluation
- Pattern-based UX issue detection
- Severity scoring based on user impact
- Actionable recommendations

Benchmark Targets (per #4121):
- Nielsen Norman Group heuristic evaluation methodology
- Lighthouse UX metrics
- Industry-standard UX audit frameworks
"""
import hashlib
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger(__name__)


class NielsenHeuristic(Enum):
    """Nielsen's 10 Usability Heuristics.

    Reference: https://www.nngroup.com/articles/ten-usability-heuristics/
    """
    VISIBILITY_OF_SYSTEM_STATUS = "visibility_of_system_status"
    MATCH_SYSTEM_REAL_WORLD = "match_system_real_world"
    USER_CONTROL_FREEDOM = "user_control_freedom"
    CONSISTENCY_STANDARDS = "consistency_standards"
    ERROR_PREVENTION = "error_prevention"
    RECOGNITION_OVER_RECALL = "recognition_over_recall"
    FLEXIBILITY_EFFICIENCY = "flexibility_efficiency"
    AESTHETIC_MINIMALIST = "aesthetic_minimalist"
    ERROR_RECOVERY = "error_recovery"
    HELP_DOCUMENTATION = "help_documentation"


class HeuristicSeverity(Enum):
    """Severity levels for heuristic violations."""
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    COSMETIC = "cosmetic"
    GOOD_PRACTICE = "good_practice"


class HeuristicAction(Enum):
    """Actions to take based on heuristic analysis."""
    BLOCK = "block"
    REQUIRE_REVIEW = "require_review"
    FLAG_WARNING = "flag_warning"
    SUGGEST_IMPROVEMENT = "suggest_improvement"
    PASS = "pass"


@dataclass
class HeuristicFinding:
    """Represents a single heuristic finding."""
    heuristic: NielsenHeuristic
    severity: HeuristicSeverity
    finding_id: str
    title: str
    description: str
    user_impact: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    recommendation: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "heuristic": self.heuristic.value,
            "severity": self.severity.value,
            "finding_id": self.finding_id,
            "title": self.title,
            "description": self.description,
            "user_impact": self.user_impact,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "code_snippet": self.code_snippet[:100] if self.code_snippet else None,
            "recommendation": self.recommendation,
            "metadata": self.metadata,
        }


@dataclass
class HeuristicResult:
    """Result of heuristic analysis."""
    overall_score: int
    overall_severity: HeuristicSeverity
    action: HeuristicAction
    findings: List[HeuristicFinding] = field(default_factory=list)
    heuristic_scores: Dict[NielsenHeuristic, int] = field(default_factory=dict)
    passed_heuristics: int = 0
    violated_heuristics: int = 0
    summary: str = ""
    analyzer_id: str = "ux_heuristic_agent_v1"
    analysis_duration_ms: float = 0.0
    evidence_hash: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "overall_score": self.overall_score,
            "overall_severity": self.overall_severity.value,
            "action": self.action.value,
            "findings": [f.to_dict() for f in self.findings],
            "heuristic_scores": {k.value: v for k, v in self.heuristic_scores.items()},
            "passed_heuristics": self.passed_heuristics,
            "violated_heuristics": self.violated_heuristics,
            "summary": self.summary,
            "analyzer_id": self.analyzer_id,
            "analysis_duration_ms": self.analysis_duration_ms,
            "evidence_hash": self.evidence_hash,
        }


SEVERITY_THRESHOLDS = {
    HeuristicSeverity.CRITICAL: 90,
    HeuristicSeverity.MAJOR: 70,
    HeuristicSeverity.MINOR: 50,
    HeuristicSeverity.COSMETIC: 30,
    HeuristicSeverity.GOOD_PRACTICE: 0,
}

HEURISTIC_WEIGHTS = {
    NielsenHeuristic.ERROR_PREVENTION: 0.15,
    NielsenHeuristic.ERROR_RECOVERY: 0.15,
    NielsenHeuristic.VISIBILITY_OF_SYSTEM_STATUS: 0.12,
    NielsenHeuristic.USER_CONTROL_FREEDOM: 0.12,
    NielsenHeuristic.CONSISTENCY_STANDARDS: 0.10,
    NielsenHeuristic.MATCH_SYSTEM_REAL_WORLD: 0.10,
    NielsenHeuristic.RECOGNITION_OVER_RECALL: 0.08,
    NielsenHeuristic.FLEXIBILITY_EFFICIENCY: 0.08,
    NielsenHeuristic.AESTHETIC_MINIMALIST: 0.05,
    NielsenHeuristic.HELP_DOCUMENTATION: 0.05,
}

VISIBILITY_PATTERNS: List[Tuple[str, str, str, int]] = [
    (
        r"(?i)loading|spinner|progress",
        "VIS-001",
        "Loading indicator present",
        0,
    ),
    (
        r"(?i)isLoading\s*[?:&|]",
        "VIS-002",
        "Loading state handling",
        0,
    ),
    (
        r"(?i)status|state|progress",
        "VIS-003",
        "Status indicator",
        0,
    ),
]

ERROR_PREVENTION_PATTERNS: List[Tuple[str, str, str, int]] = [
    (
        r"(?i)disabled\s*=\s*{[^}]*}",
        "ERR-001",
        "Conditional disable for error prevention",
        0,
    ),
    (
        r"(?i)required\s*[=:]",
        "ERR-002",
        "Required field validation",
        0,
    ),
    (
        r"(?i)pattern\s*=\s*['\"][^'\"]+['\"]",
        "ERR-003",
        "Input pattern validation",
        0,
    ),
    (
        r"(?i)maxLength|minLength|max|min",
        "ERR-004",
        "Input length/value constraints",
        0,
    ),
]

ERROR_RECOVERY_PATTERNS: List[Tuple[str, str, str, int]] = [
    (
        r"(?i)error\s*[=:]\s*{",
        "REC-001",
        "Error state handling",
        0,
    ),
    (
        r"(?i)catch\s*\([^)]*\)\s*{",
        "REC-002",
        "Error catching",
        0,
    ),
    (
        r"(?i)onError|handleError|errorHandler",
        "REC-003",
        "Error handler function",
        0,
    ),
    (
        r"(?i)retry|tryAgain|reload",
        "REC-004",
        "Retry mechanism",
        0,
    ),
]

USER_CONTROL_PATTERNS: List[Tuple[str, str, str, int]] = [
    (
        r"(?i)onCancel|handleCancel|cancel",
        "CTL-001",
        "Cancel action available",
        0,
    ),
    (
        r"(?i)onClose|handleClose|close",
        "CTL-002",
        "Close action available",
        0,
    ),
    (
        r"(?i)undo|revert|reset",
        "CTL-003",
        "Undo/revert capability",
        0,
    ),
    (
        r"(?i)confirm|confirmation",
        "CTL-004",
        "Confirmation dialog",
        0,
    ),
]

ANTI_PATTERNS: List[Tuple[str, str, str, NielsenHeuristic, int]] = [
    (
        r"(?i)alert\s*\(",
        "ANTI-001",
        "Using browser alert instead of custom modal",
        NielsenHeuristic.AESTHETIC_MINIMALIST,
        40,
    ),
    (
        r"(?i)confirm\s*\(",
        "ANTI-002",
        "Using browser confirm instead of custom dialog",
        NielsenHeuristic.CONSISTENCY_STANDARDS,
        30,
    ),
    (
        r"(?i)prompt\s*\(",
        "ANTI-003",
        "Using browser prompt instead of custom input",
        NielsenHeuristic.CONSISTENCY_STANDARDS,
        30,
    ),
    (
        r"(?i)window\.location\s*=",
        "ANTI-004",
        "Direct navigation without confirmation",
        NielsenHeuristic.USER_CONTROL_FREEDOM,
        50,
    ),
    (
        r"(?i)autoFocus\s*=\s*{?\s*true",
        "ANTI-005",
        "Auto-focus may disrupt user flow",
        NielsenHeuristic.USER_CONTROL_FREEDOM,
        20,
    ),
]


class UXHeuristicAgent:
    """
    UX Heuristic Agent for evaluating UX patterns against Nielsen's heuristics.

    Blueprint Reference: Section 3.3 (Agent Catalog V2)
    - UX/UI Agent
    - Integrates with Safety Governor v2 (Section 4.1)

    This agent analyzes UI code to:
    1. Evaluate visibility of system status
    2. Check error prevention mechanisms
    3. Verify error recovery patterns
    4. Assess user control and freedom
    5. Identify UX anti-patterns
    """

    def __init__(
        self,
        enabled: bool = True,
        strict_mode: bool = False,
    ):
        """
        Initialize UXHeuristicAgent.

        Args:
            enabled: Whether heuristic analysis is enabled
            strict_mode: If True, treat minor issues as major
        """
        self.enabled = enabled
        self.strict_mode = strict_mode
        self._load_settings()
        self._compile_patterns()
        logger.info(
            "[UXHeuristicAgent] Initialized - EPIC K P2: "
            "enabled=%s, strict_mode=%s",
            self.enabled,
            self.strict_mode,
        )

    def _load_settings(self) -> None:
        """Load settings from environment/config."""
        try:
            from common.config.settings import settings
            self.enabled = getattr(
                settings, "ux_heuristic_enabled", self.enabled
            )
            self.strict_mode = getattr(
                settings, "ux_heuristic_strict_mode", self.strict_mode
            )
            logger.debug("[UXHeuristicAgent] Settings loaded from config")
        except (ImportError, AttributeError) as e:
            logger.debug("[UXHeuristicAgent] Using default settings: %s", e)

    def _compile_patterns(self) -> None:
        """Pre-compile regex patterns for performance."""
        self._compiled_visibility = [
            (re.compile(pattern), pid, title, score)
            for pattern, pid, title, score in VISIBILITY_PATTERNS
        ]
        self._compiled_error_prevention = [
            (re.compile(pattern), pid, title, score)
            for pattern, pid, title, score in ERROR_PREVENTION_PATTERNS
        ]
        self._compiled_error_recovery = [
            (re.compile(pattern), pid, title, score)
            for pattern, pid, title, score in ERROR_RECOVERY_PATTERNS
        ]
        self._compiled_user_control = [
            (re.compile(pattern), pid, title, score)
            for pattern, pid, title, score in USER_CONTROL_PATTERNS
        ]
        self._compiled_anti_patterns = [
            (re.compile(pattern), pid, title, heuristic, score)
            for pattern, pid, title, heuristic, score in ANTI_PATTERNS
        ]

    def analyze_code(
        self,
        code_content: str,
        file_path: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> HeuristicResult:
        """
        Analyze code for UX heuristic compliance.

        Args:
            code_content: Source code to analyze
            file_path: Path to the file being analyzed
            context: Optional context with additional information

        Returns:
            HeuristicResult with findings and recommendations
        """
        import time
        start_time = time.time()

        if not self.enabled:
            return HeuristicResult(
                overall_score=100,
                overall_severity=HeuristicSeverity.GOOD_PRACTICE,
                action=HeuristicAction.PASS,
                summary="UX heuristic analysis disabled",
            )

        if not code_content or not code_content.strip():
            return HeuristicResult(
                overall_score=100,
                overall_severity=HeuristicSeverity.GOOD_PRACTICE,
                action=HeuristicAction.PASS,
                summary="Empty code content",
            )

        context = context or {}
        findings: List[HeuristicFinding] = []
        heuristic_scores: Dict[NielsenHeuristic, int] = {}
        passed_heuristics = 0
        violated_heuristics = 0

        vis_findings, vis_score = self._analyze_visibility(
            code_content, file_path
        )
        findings.extend(vis_findings)
        heuristic_scores[NielsenHeuristic.VISIBILITY_OF_SYSTEM_STATUS] = vis_score
        if vis_score >= 70:
            passed_heuristics += 1
        else:
            violated_heuristics += 1

        err_prev_findings, err_prev_score = self._analyze_error_prevention(
            code_content, file_path
        )
        findings.extend(err_prev_findings)
        heuristic_scores[NielsenHeuristic.ERROR_PREVENTION] = err_prev_score
        if err_prev_score >= 70:
            passed_heuristics += 1
        else:
            violated_heuristics += 1

        err_rec_findings, err_rec_score = self._analyze_error_recovery(
            code_content, file_path
        )
        findings.extend(err_rec_findings)
        heuristic_scores[NielsenHeuristic.ERROR_RECOVERY] = err_rec_score
        if err_rec_score >= 70:
            passed_heuristics += 1
        else:
            violated_heuristics += 1

        ctrl_findings, ctrl_score = self._analyze_user_control(
            code_content, file_path
        )
        findings.extend(ctrl_findings)
        heuristic_scores[NielsenHeuristic.USER_CONTROL_FREEDOM] = ctrl_score
        if ctrl_score >= 70:
            passed_heuristics += 1
        else:
            violated_heuristics += 1

        anti_findings = self._analyze_anti_patterns(code_content, file_path)
        findings.extend(anti_findings)

        overall_score = self._calculate_overall_score(heuristic_scores)
        overall_severity = self._determine_severity(overall_score)
        action = self._determine_action(overall_severity, findings)

        summary = self._generate_summary(
            overall_score, overall_severity, findings,
            passed_heuristics, violated_heuristics
        )

        duration_ms = (time.time() - start_time) * 1000
        evidence_hash = self._compute_evidence_hash(code_content, findings)

        result = HeuristicResult(
            overall_score=overall_score,
            overall_severity=overall_severity,
            action=action,
            findings=findings,
            heuristic_scores=heuristic_scores,
            passed_heuristics=passed_heuristics,
            violated_heuristics=violated_heuristics,
            summary=summary,
            analysis_duration_ms=duration_ms,
            evidence_hash=evidence_hash,
        )

        logger.info(
            "[UXHeuristicAgent] Analysis complete: score=%d, severity=%s",
            overall_score,
            overall_severity.value,
        )

        return result

    def _analyze_visibility(
        self,
        code_content: str,
        file_path: Optional[str],
    ) -> Tuple[List[HeuristicFinding], int]:
        """Analyze visibility of system status."""
        findings: List[HeuristicFinding] = []
        score = 50

        for pattern, pid, title, _ in self._compiled_visibility:
            if pattern.search(code_content):
                score += 15

        if score < 70:
            findings.append(HeuristicFinding(
                heuristic=NielsenHeuristic.VISIBILITY_OF_SYSTEM_STATUS,
                severity=HeuristicSeverity.MINOR,
                finding_id="VIS-MISSING",
                title="Limited visibility of system status",
                description="Code lacks loading indicators or status feedback",
                user_impact="Users may not know if actions are processing",
                file_path=file_path,
                recommendation="Add loading states and progress indicators",
            ))

        return findings, min(100, score)

    def _analyze_error_prevention(
        self,
        code_content: str,
        file_path: Optional[str],
    ) -> Tuple[List[HeuristicFinding], int]:
        """Analyze error prevention mechanisms."""
        findings: List[HeuristicFinding] = []
        score = 50

        for pattern, pid, title, _ in self._compiled_error_prevention:
            if pattern.search(code_content):
                score += 12

        if score < 70:
            findings.append(HeuristicFinding(
                heuristic=NielsenHeuristic.ERROR_PREVENTION,
                severity=HeuristicSeverity.MAJOR,
                finding_id="ERR-PREV-MISSING",
                title="Insufficient error prevention",
                description="Code lacks input validation or constraints",
                user_impact="Users may submit invalid data",
                file_path=file_path,
                recommendation="Add input validation, required fields, and constraints",
            ))

        return findings, min(100, score)

    def _analyze_error_recovery(
        self,
        code_content: str,
        file_path: Optional[str],
    ) -> Tuple[List[HeuristicFinding], int]:
        """Analyze error recovery patterns."""
        findings: List[HeuristicFinding] = []
        score = 50

        for pattern, pid, title, _ in self._compiled_error_recovery:
            if pattern.search(code_content):
                score += 12

        if score < 70:
            findings.append(HeuristicFinding(
                heuristic=NielsenHeuristic.ERROR_RECOVERY,
                severity=HeuristicSeverity.MAJOR,
                finding_id="ERR-REC-MISSING",
                title="Limited error recovery options",
                description="Code lacks error handling or retry mechanisms",
                user_impact="Users may be stuck when errors occur",
                file_path=file_path,
                recommendation="Add error handlers, retry buttons, and clear error messages",
            ))

        return findings, min(100, score)

    def _analyze_user_control(
        self,
        code_content: str,
        file_path: Optional[str],
    ) -> Tuple[List[HeuristicFinding], int]:
        """Analyze user control and freedom."""
        findings: List[HeuristicFinding] = []
        score = 50

        for pattern, pid, title, _ in self._compiled_user_control:
            if pattern.search(code_content):
                score += 12

        if score < 70:
            findings.append(HeuristicFinding(
                heuristic=NielsenHeuristic.USER_CONTROL_FREEDOM,
                severity=HeuristicSeverity.MINOR,
                finding_id="CTL-MISSING",
                title="Limited user control",
                description="Code lacks cancel, undo, or close actions",
                user_impact="Users may feel trapped in workflows",
                file_path=file_path,
                recommendation="Add cancel buttons, close handlers, and undo options",
            ))

        return findings, min(100, score)

    def _analyze_anti_patterns(
        self,
        code_content: str,
        file_path: Optional[str],
    ) -> List[HeuristicFinding]:
        """Analyze UX anti-patterns."""
        findings: List[HeuristicFinding] = []

        for pattern, pid, title, heuristic, score in self._compiled_anti_patterns:
            matches = pattern.findall(code_content)
            if matches:
                findings.append(HeuristicFinding(
                    heuristic=heuristic,
                    severity=self._score_to_severity(score),
                    finding_id=pid,
                    title=title,
                    description=f"Found {len(matches)} instance(s) of UX anti-pattern",
                    user_impact="May disrupt user experience or break consistency",
                    file_path=file_path,
                    recommendation="Replace with custom UI components",
                ))

        return findings

    def _calculate_overall_score(
        self,
        heuristic_scores: Dict[NielsenHeuristic, int],
    ) -> int:
        """Calculate weighted overall score."""
        if not heuristic_scores:
            return 100

        total_weight = 0.0
        weighted_sum = 0.0

        for heuristic, score in heuristic_scores.items():
            weight = HEURISTIC_WEIGHTS.get(heuristic, 0.1)
            weighted_sum += score * weight
            total_weight += weight

        if total_weight == 0:
            return 100

        return int(weighted_sum / total_weight)

    def _determine_severity(self, score: int) -> HeuristicSeverity:
        """Determine severity from score."""
        if score >= 90:
            return HeuristicSeverity.GOOD_PRACTICE
        elif score >= 70:
            return HeuristicSeverity.COSMETIC
        elif score >= 50:
            return HeuristicSeverity.MINOR
        elif score >= 30:
            return HeuristicSeverity.MAJOR
        else:
            return HeuristicSeverity.CRITICAL

    def _score_to_severity(self, score: int) -> HeuristicSeverity:
        """Convert a finding score to severity."""
        if score >= 70:
            return HeuristicSeverity.MAJOR
        elif score >= 50:
            return HeuristicSeverity.MINOR
        else:
            return HeuristicSeverity.COSMETIC

    def _determine_action(
        self,
        severity: HeuristicSeverity,
        findings: List[HeuristicFinding],
    ) -> HeuristicAction:
        """Determine action based on severity and findings."""
        if severity == HeuristicSeverity.CRITICAL:
            return HeuristicAction.BLOCK if self.strict_mode else HeuristicAction.REQUIRE_REVIEW
        elif severity == HeuristicSeverity.MAJOR:
            return HeuristicAction.REQUIRE_REVIEW
        elif severity == HeuristicSeverity.MINOR:
            return HeuristicAction.FLAG_WARNING
        elif severity == HeuristicSeverity.COSMETIC:
            return HeuristicAction.SUGGEST_IMPROVEMENT
        else:
            return HeuristicAction.PASS

    def _generate_summary(
        self,
        score: int,
        severity: HeuristicSeverity,
        findings: List[HeuristicFinding],
        passed: int,
        violated: int,
    ) -> str:
        """Generate human-readable summary."""
        return (
            f"UX Heuristic Score: {score}/100 ({severity.value}). "
            f"Passed: {passed}/10, Violated: {violated}/10. "
            f"Found {len(findings)} issue(s)."
        )

    def _compute_evidence_hash(
        self,
        code_content: str,
        findings: List[HeuristicFinding],
    ) -> str:
        """Compute hash for evidence ledger."""
        content = code_content + str([f.to_dict() for f in findings])
        return hashlib.sha256(content.encode()).hexdigest()[:16]


_ux_heuristic_agent: Optional[UXHeuristicAgent] = None


def get_ux_heuristic_agent() -> UXHeuristicAgent:
    """Get or create singleton UXHeuristicAgent instance."""
    global _ux_heuristic_agent
    if _ux_heuristic_agent is None:
        _ux_heuristic_agent = UXHeuristicAgent()
    return _ux_heuristic_agent


def reset_ux_heuristic_agent() -> None:
    """Reset singleton instance (for testing)."""
    global _ux_heuristic_agent
    _ux_heuristic_agent = None


def analyze_ux_heuristics(
    code_content: str,
    file_path: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> HeuristicResult:
    """
    Convenience function to analyze UX heuristics.

    Args:
        code_content: Source code to analyze
        file_path: Path to the file being analyzed
        context: Optional context

    Returns:
        HeuristicResult with findings
    """
    agent = get_ux_heuristic_agent()
    return agent.analyze_code(code_content, file_path, context)
