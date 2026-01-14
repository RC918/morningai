"""
F-5.5: Review Consolidation - Judge Agent Arbitration

EPIC F Phase F-5.5: Review Consolidation

This module implements conflict detection and Judge Agent arbitration for
consolidating conflicting reviewer opinions from MultiSpecialistReviewer (B-9).

Blueprint Reference: Section F-5.5 (Review Consolidation)

Problem: When MultiSpecialistReviewer returns conflicting opinions from different
specialists, there's no mechanism for the Planner to arbitrate. This can cause
Coder to enter "infinite loop" - fixing A breaks B, fixing B breaks A.

Solution: Extend F-5 Self-refinement Loop with Review Consolidation using Judge Agent.

Key Features:
- ConflictDetector: Detects conflicting recommendations between specialists
- ReviewConsolidator: Consolidates findings using Judge Agent for arbitration
- Context-aware prioritization (e.g., Security > Performance for auth APIs)

Usage:
    from core.planner.review_consolidation import ReviewConsolidator

    consolidator = ReviewConsolidator(trace_id="abc123")
    consolidated = consolidator.consolidate(
        findings=specialist_findings,
        task_context={"api_type": "auth", "risk_level": "high"}
    )
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _get_settings():
    """Get settings with fallback for testing."""
    try:
        from common.config.settings import settings
        return settings
    except ImportError:
        return None


def _use_review_consolidation() -> bool:
    """Lazy evaluation for USE_REVIEW_CONSOLIDATION setting."""
    settings = _get_settings()
    return getattr(settings, 'use_review_consolidation', False) if settings else False


class ConflictType(Enum):
    """Types of conflicts between specialist findings."""
    SECURITY_VS_PERFORMANCE = "security_vs_performance"
    SECURITY_VS_ARCHITECTURE = "security_vs_architecture"
    PERFORMANCE_VS_ARCHITECTURE = "performance_vs_architecture"
    CONTRADICTORY_SUGGESTIONS = "contradictory_suggestions"
    OVERLAPPING_CONCERNS = "overlapping_concerns"


class ConflictResolution(Enum):
    """Resolution outcomes for conflicts."""
    PRIORITIZE_FIRST = "prioritize_first"
    PRIORITIZE_SECOND = "prioritize_second"
    MERGE_BOTH = "merge_both"
    DEFER_TO_HUMAN = "defer_to_human"


@dataclass
class Conflict:
    """
    Represents a conflict between two specialist findings.

    Attributes:
        conflict_type: Type of conflict detected
        finding_a: First conflicting finding
        finding_b: Second conflicting finding
        description: Human-readable description of the conflict
        severity: Severity of the conflict (low, medium, high)
    """
    conflict_type: ConflictType
    finding_a: Dict[str, Any]
    finding_b: Dict[str, Any]
    description: str
    severity: str = "medium"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "conflict_type": self.conflict_type.value,
            "finding_a": self.finding_a,
            "finding_b": self.finding_b,
            "description": self.description,
            "severity": self.severity,
        }


@dataclass
class ArbitrationDecision:
    """
    Decision from Judge Agent arbitration.

    Attributes:
        resolution: How the conflict was resolved
        winning_finding: The finding that takes priority (if applicable)
        rationale: Explanation for the decision
        confidence: Confidence in the decision (0.0 to 1.0)
        requires_human_review: Whether human review is recommended
    """
    resolution: ConflictResolution
    winning_finding: Optional[Dict[str, Any]] = None
    rationale: str = ""
    confidence: float = 0.8
    requires_human_review: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "resolution": self.resolution.value,
            "winning_finding": self.winning_finding,
            "rationale": self.rationale,
            "confidence": self.confidence,
            "requires_human_review": self.requires_human_review,
        }


@dataclass
class ConsolidatedReview:
    """
    Consolidated review output after conflict resolution.

    Attributes:
        findings: List of prioritized, non-conflicting findings
        conflicts_detected: Number of conflicts detected
        conflicts_resolved: Number of conflicts resolved
        arbitration_decisions: List of arbitration decisions made
        requires_human_review: Whether any decision requires human review
        consolidation_time_ms: Time taken for consolidation
    """
    findings: List[Dict[str, Any]] = field(default_factory=list)
    conflicts_detected: int = 0
    conflicts_resolved: int = 0
    arbitration_decisions: List[ArbitrationDecision] = field(default_factory=list)
    requires_human_review: bool = False
    consolidation_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "findings": self.findings,
            "conflicts_detected": self.conflicts_detected,
            "conflicts_resolved": self.conflicts_resolved,
            "arbitration_decisions": [d.to_dict() for d in self.arbitration_decisions],
            "requires_human_review": self.requires_human_review,
            "consolidation_time_ms": self.consolidation_time_ms,
            "finding_count": len(self.findings),
        }


# Priority rules for context-aware arbitration
# Higher number = higher priority
CONTEXT_PRIORITY_RULES: Dict[str, Dict[str, int]] = {
    "auth": {"security": 100, "performance": 50, "architecture": 30},
    "login": {"security": 100, "performance": 50, "architecture": 30},
    "payment": {"security": 100, "performance": 60, "architecture": 40},
    "api": {"security": 80, "performance": 70, "architecture": 50},
    "data": {"security": 90, "performance": 60, "architecture": 50},
    "ui": {"security": 50, "performance": 80, "architecture": 60},
    "default": {"security": 70, "performance": 60, "architecture": 50},
}

# Conflict detection patterns
CONFLICT_PATTERNS: List[Dict[str, Any]] = [
    {
        "pattern": "add.*check",
        "anti_pattern": "remove.*check|reduce.*overhead",
        "conflict_type": ConflictType.SECURITY_VS_PERFORMANCE,
    },
    {
        "pattern": "add.*validation",
        "anti_pattern": "skip.*validation|optimize",
        "conflict_type": ConflictType.SECURITY_VS_PERFORMANCE,
    },
    {
        "pattern": "add.*abstraction|extract.*class",
        "anti_pattern": "inline|simplify|reduce.*complexity",
        "conflict_type": ConflictType.PERFORMANCE_VS_ARCHITECTURE,
    },
    {
        "pattern": "encrypt|hash|sanitize",
        "anti_pattern": "cache|memoize|batch",
        "conflict_type": ConflictType.SECURITY_VS_PERFORMANCE,
    },
]


class ConflictDetector:
    """
    Detects conflicts between specialist findings.

    This class analyzes findings from different specialists and identifies
    cases where their recommendations contradict each other.
    """

    def detect_conflicts(
        self,
        findings: List[Dict[str, Any]],
    ) -> List[Conflict]:
        """
        Detect conflicts between specialist findings.

        Args:
            findings: List of findings from all specialists

        Returns:
            List of detected conflicts
        """
        conflicts: List[Conflict] = []

        # Group findings by specialist
        by_specialist: Dict[str, List[Dict[str, Any]]] = {}
        for finding in findings:
            specialist = finding.get("specialist", "unknown")
            if specialist not in by_specialist:
                by_specialist[specialist] = []
            by_specialist[specialist].append(finding)

        # Check for conflicts between different specialists
        specialists = list(by_specialist.keys())
        for i, spec_a in enumerate(specialists):
            for spec_b in specialists[i + 1:]:
                for finding_a in by_specialist[spec_a]:
                    for finding_b in by_specialist[spec_b]:
                        conflict = self._check_conflict(
                            finding_a, finding_b, spec_a, spec_b
                        )
                        if conflict:
                            conflicts.append(conflict)

        logger.info(
            "[ConflictDetector] Detected %d conflicts among %d findings",
            len(conflicts), len(findings)
        )

        return conflicts

    def _check_conflict(
        self,
        finding_a: Dict[str, Any],
        finding_b: Dict[str, Any],
        specialist_a: str,
        specialist_b: str,
    ) -> Optional[Conflict]:
        """Check if two findings conflict with each other."""
        import re

        suggestion_a = (finding_a.get("suggestion") or "").lower()
        suggestion_b = (finding_b.get("suggestion") or "").lower()
        message_a = (finding_a.get("message") or "").lower()
        message_b = (finding_b.get("message") or "").lower()

        text_a = f"{suggestion_a} {message_a}"
        text_b = f"{suggestion_b} {message_b}"

        # Check against conflict patterns
        for pattern_def in CONFLICT_PATTERNS:
            pattern = pattern_def["pattern"]
            anti_pattern = pattern_def["anti_pattern"]

            if (re.search(pattern, text_a) and re.search(anti_pattern, text_b)) or \
               (re.search(pattern, text_b) and re.search(anti_pattern, text_a)):
                return Conflict(
                    conflict_type=pattern_def["conflict_type"],
                    finding_a=finding_a,
                    finding_b=finding_b,
                    description=(
                        f"{specialist_a} suggests '{suggestion_a[:50]}...' "
                        f"but {specialist_b} suggests '{suggestion_b[:50]}...'"
                    ),
                    severity=self._determine_conflict_severity(finding_a, finding_b),
                )

        # Check for same file/line with different suggestions
        same_file = finding_a.get("file_path") == finding_b.get("file_path")
        same_line = finding_a.get("line_number") == finding_b.get("line_number")
        has_file = finding_a.get("file_path") is not None
        if same_file and same_line and has_file:
            return Conflict(
                conflict_type=ConflictType.OVERLAPPING_CONCERNS,
                finding_a=finding_a,
                finding_b=finding_b,
                description=(
                    f"Both {specialist_a} and {specialist_b} have concerns "
                    f"at {finding_a.get('file_path')}:{finding_a.get('line_number')}"
                ),
                severity=self._determine_conflict_severity(finding_a, finding_b),
            )

        return None

    def _determine_conflict_severity(
        self,
        finding_a: Dict[str, Any],
        finding_b: Dict[str, Any],
    ) -> str:
        """Determine the severity of a conflict based on finding severities."""
        severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}

        sev_a = severity_order.get(finding_a.get("severity", "medium"), 2)
        sev_b = severity_order.get(finding_b.get("severity", "medium"), 2)

        max_sev = max(sev_a, sev_b)

        for sev, order in severity_order.items():
            if order == max_sev:
                return sev

        return "medium"


class ReviewConsolidator:
    """
    Consolidates conflicting reviewer opinions using Judge Agent.

    Blueprint Reference: Section F-5.5 ReviewConsolidator

    This class:
    1. Detects conflicts between specialist opinions
    2. Invokes Judge Agent for arbitration when conflicts exist
    3. Returns prioritized, non-conflicting action items
    """

    def __init__(
        self,
        trace_id: str = "",
        enable_llm: bool = True,
    ):
        """
        Initialize the ReviewConsolidator.

        Args:
            trace_id: Trace ID for telemetry
            enable_llm: Whether to use LLM for Judge Agent decisions
        """
        self.trace_id = trace_id
        self.enable_llm = enable_llm
        self.conflict_detector = ConflictDetector()

    def consolidate(
        self,
        findings: List[Dict[str, Any]],
        task_context: Optional[Dict[str, Any]] = None,
    ) -> ConsolidatedReview:
        """
        Consolidate specialist findings, resolving conflicts.

        Args:
            findings: List of findings from MultiSpecialistReviewer
            task_context: Context about the task (api_type, risk_level, etc.)

        Returns:
            ConsolidatedReview with prioritized, non-conflicting findings
        """
        import time

        start_time = time.time()

        if not _use_review_consolidation():
            logger.debug(
                "[ReviewConsolidator] Review consolidation disabled, "
                "passing through findings"
            )
            return ConsolidatedReview(
                findings=findings,
                conflicts_detected=0,
                conflicts_resolved=0,
                consolidation_time_ms=(time.time() - start_time) * 1000,
            )

        task_context = task_context or {}

        # Step 1: Detect conflicts
        conflicts = self.conflict_detector.detect_conflicts(findings)

        if not conflicts:
            logger.info(
                "[ReviewConsolidator] No conflicts detected, "
                "returning original findings"
            )
            return ConsolidatedReview(
                findings=findings,
                conflicts_detected=0,
                conflicts_resolved=0,
                consolidation_time_ms=(time.time() - start_time) * 1000,
            )

        logger.info(
            "[ReviewConsolidator] Detected %d conflicts, invoking arbitration",
            len(conflicts)
        )

        # Step 2: Create index-based tracking for findings
        # Using index instead of id() to avoid fragility when objects are copied
        finding_to_index: Dict[int, int] = {id(f): i for i, f in enumerate(findings)}
        excluded_indices: set = set()

        arbitration_decisions: List[ArbitrationDecision] = []
        resolved_findings: List[Dict[str, Any]] = []
        requires_human_review = False

        for conflict in conflicts:
            decision = self._arbitrate_conflict(conflict, task_context)
            arbitration_decisions.append(decision)

            if decision.requires_human_review:
                requires_human_review = True

            # Apply resolution using index-based tracking
            if decision.resolution == ConflictResolution.PRIORITIZE_FIRST:
                idx = finding_to_index.get(id(conflict.finding_b))
                if idx is not None:
                    excluded_indices.add(idx)
            elif decision.resolution == ConflictResolution.PRIORITIZE_SECOND:
                idx = finding_to_index.get(id(conflict.finding_a))
                if idx is not None:
                    excluded_indices.add(idx)
            elif decision.resolution == ConflictResolution.DEFER_TO_HUMAN:
                requires_human_review = True

        # Step 3: Build consolidated findings list using index-based exclusion
        for i, finding in enumerate(findings):
            if i not in excluded_indices:
                resolved_findings.append(finding)

        # Step 4: Sort by priority (severity)
        severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        resolved_findings.sort(
            key=lambda f: severity_order.get(f.get("severity", "medium"), 2),
            reverse=True
        )

        consolidation_time_ms = (time.time() - start_time) * 1000

        logger.info(
            "[ReviewConsolidator] Consolidation complete: "
            "%d conflicts detected, %d resolved, %d findings remaining",
            len(conflicts), len(arbitration_decisions), len(resolved_findings)
        )

        return ConsolidatedReview(
            findings=resolved_findings,
            conflicts_detected=len(conflicts),
            conflicts_resolved=len(arbitration_decisions),
            arbitration_decisions=arbitration_decisions,
            requires_human_review=requires_human_review,
            consolidation_time_ms=consolidation_time_ms,
        )

    def _arbitrate_conflict(
        self,
        conflict: Conflict,
        task_context: Dict[str, Any],
    ) -> ArbitrationDecision:
        """
        Arbitrate a single conflict using Judge Agent.

        Args:
            conflict: The conflict to arbitrate
            task_context: Context about the task

        Returns:
            ArbitrationDecision with resolution
        """
        if self.enable_llm:
            try:
                return self._arbitrate_with_judge(conflict, task_context)
            except Exception as e:
                logger.warning(
                    "[ReviewConsolidator] Judge Agent arbitration failed: %s, "
                    "falling back to rule-based",
                    e
                )

        return self._arbitrate_rule_based(conflict, task_context)

    def _arbitrate_with_judge(
        self,
        conflict: Conflict,
        task_context: Dict[str, Any],
    ) -> ArbitrationDecision:
        """Arbitrate using Judge Agent from Debate Engine."""
        from .debate_engine import JudgeAgent, DebateTopic, DebateArgument, DebateRole

        judge = JudgeAgent(trace_id=self.trace_id, enable_llm=True)

        # Create a debate topic from the conflict
        topic = DebateTopic(
            question=f"Which recommendation should take priority: {conflict.description}",
            context=task_context,
            risk_level=conflict.severity,
        )

        # Create arguments representing each finding
        finding_a = conflict.finding_a
        finding_b = conflict.finding_b

        arguments = [
            DebateArgument(
                role=DebateRole.LEFT,
                position=finding_a.get("suggestion", finding_a.get("message", "")),
                reasoning=f"From {finding_a.get('specialist', 'unknown')} specialist: {finding_a.get('message', '')}",
                evidence=[finding_a.get("category", "")],
                counterpoints=[],
                confidence=0.8,
                round_number=1,
            ),
            DebateArgument(
                role=DebateRole.RIGHT,
                position=finding_b.get("suggestion", finding_b.get("message", "")),
                reasoning=f"From {finding_b.get('specialist', 'unknown')} specialist: {finding_b.get('message', '')}",
                evidence=[finding_b.get("category", "")],
                counterpoints=[],
                confidence=0.8,
                round_number=1,
            ),
        ]

        decision = judge.evaluate(topic, arguments)

        # Convert JudgeDecision to ArbitrationDecision
        from .debate_engine import DebateOutcome

        if decision.outcome == DebateOutcome.LEFT_WINS:
            resolution = ConflictResolution.PRIORITIZE_FIRST
            winning = finding_a
        elif decision.outcome == DebateOutcome.RIGHT_WINS:
            resolution = ConflictResolution.PRIORITIZE_SECOND
            winning = finding_b
        elif decision.outcome == DebateOutcome.SYNTHESIS:
            resolution = ConflictResolution.MERGE_BOTH
            winning = None
        else:
            resolution = ConflictResolution.DEFER_TO_HUMAN
            winning = None

        return ArbitrationDecision(
            resolution=resolution,
            winning_finding=winning,
            rationale=decision.rationale,
            confidence=decision.confidence,
            requires_human_review=decision.requires_human_review,
        )

    def _arbitrate_rule_based(
        self,
        conflict: Conflict,
        task_context: Dict[str, Any],
    ) -> ArbitrationDecision:
        """
        Arbitrate using rule-based priority.

        Priority rules:
        - For auth/login/payment APIs: Security > Performance > Architecture
        - For UI components: Performance > Architecture > Security
        - Default: Security > Performance > Architecture
        """
        # Determine context type
        context_type = "default"
        for key in ["api_type", "component_type", "goal"]:
            value = str(task_context.get(key, "")).lower()
            for ctx in CONTEXT_PRIORITY_RULES:
                if ctx in value:
                    context_type = ctx
                    break

        priority_rules = CONTEXT_PRIORITY_RULES.get(
            context_type, CONTEXT_PRIORITY_RULES["default"]
        )

        # Get specialists from findings
        spec_a = conflict.finding_a.get("specialist", "unknown").lower()
        spec_b = conflict.finding_b.get("specialist", "unknown").lower()

        priority_a = priority_rules.get(spec_a, 50)
        priority_b = priority_rules.get(spec_b, 50)

        if priority_a > priority_b:
            resolution = ConflictResolution.PRIORITIZE_FIRST
            winning = conflict.finding_a
            rationale = (
                f"In {context_type} context, {spec_a} ({priority_a}) "
                f"has higher priority than {spec_b} ({priority_b})"
            )
        elif priority_b > priority_a:
            resolution = ConflictResolution.PRIORITIZE_SECOND
            winning = conflict.finding_b
            rationale = (
                f"In {context_type} context, {spec_b} ({priority_b}) "
                f"has higher priority than {spec_a} ({priority_a})"
            )
        else:
            # Equal priority - defer to severity
            sev_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
            sev_a = sev_order.get(conflict.finding_a.get("severity", "medium"), 2)
            sev_b = sev_order.get(conflict.finding_b.get("severity", "medium"), 2)

            if sev_a >= sev_b:
                resolution = ConflictResolution.PRIORITIZE_FIRST
                winning = conflict.finding_a
            else:
                resolution = ConflictResolution.PRIORITIZE_SECOND
                winning = conflict.finding_b

            rationale = (
                f"Equal priority ({priority_a}), resolved by severity"
            )

        return ArbitrationDecision(
            resolution=resolution,
            winning_finding=winning,
            rationale=rationale,
            confidence=0.7,
            requires_human_review=False,
        )


def consolidate_review_findings(
    findings: List[Dict[str, Any]],
    task_context: Optional[Dict[str, Any]] = None,
    trace_id: str = "",
) -> ConsolidatedReview:
    """
    Convenience function to consolidate review findings.

    Args:
        findings: List of findings from MultiSpecialistReviewer
        task_context: Context about the task
        trace_id: Trace ID for telemetry

    Returns:
        ConsolidatedReview with prioritized findings
    """
    consolidator = ReviewConsolidator(trace_id=trace_id)
    return consolidator.consolidate(findings, task_context)
