#!/usr/bin/env python3
"""
Risk Analyzer Agent - EPIC K Phase 1 (P1-high)

Blueprint Reference: Section 3.3 (Agent Catalog V2) - Governance/Reasoning Agents
Issue: #4096 (EPIC K P1: Risk Analyzer Agent)

This module implements the Risk Analyzer Agent for pre-scanning high-risk tasks
before execution. It integrates with:
- Safety Governor v2 (Section 4.1) for content safety
- Flow Controller v3 (Section 3.2) for task routing decisions
- Evidence Ledger (Section 4.6) for audit trail

Design Principles:
- Multi-dimensional risk assessment (complexity, security, scope, compliance, cost)
- Configurable thresholds via feature flags
- Integration with existing governance modules
- Mitigation recommendations for high-risk tasks

Benchmark Targets (per #4121):
- Lakera Guard / Azure Safety for security risk detection
- Arize AI / LangSmith for observability integration
"""
import hashlib
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger(__name__)


class RiskCategory(Enum):
    """Risk categories for task analysis.

    Blueprint Reference: Section 4.1 (Safety Governor v2)
    """
    TASK_COMPLEXITY = "task_complexity"
    SECURITY = "security"
    SCOPE = "scope"
    COMPLIANCE = "compliance"
    COST = "cost"
    CONTENT_SAFETY = "content_safety"


class RiskLevel(Enum):
    """Risk levels for task analysis.

    Aligned with ContentRiskLevel from content_safety_scanner.py
    """
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MINIMAL = "minimal"


class RiskAction(Enum):
    """Actions to take based on risk analysis."""
    BLOCK = "block"
    REQUIRE_APPROVAL = "require_approval"
    FLAG_FOR_REVIEW = "flag_for_review"
    PROCEED_WITH_CAUTION = "proceed_with_caution"
    ALLOW = "allow"


@dataclass
class RiskFinding:
    """Represents a single risk finding."""
    category: RiskCategory
    level: RiskLevel
    finding_id: str
    title: str
    description: str
    score: int
    evidence: Optional[str] = None
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
            "score": self.score,
            "evidence": self.evidence[:200] if self.evidence else None,
            "recommendation": self.recommendation,
            "metadata": self.metadata,
        }


@dataclass
class RiskAnalysisResult:
    """Result of risk analysis for a task."""
    overall_score: int
    overall_level: RiskLevel
    action: RiskAction
    findings: List[RiskFinding] = field(default_factory=list)
    category_scores: Dict[RiskCategory, int] = field(default_factory=dict)
    should_block: bool = False
    requires_approval: bool = False
    mitigation_recommendations: List[str] = field(default_factory=list)
    summary: str = ""
    analyzer_id: str = "risk_analyzer_v1"
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
            "should_block": self.should_block,
            "requires_approval": self.requires_approval,
            "mitigation_recommendations": self.mitigation_recommendations,
            "summary": self.summary,
            "analyzer_id": self.analyzer_id,
            "analysis_duration_ms": self.analysis_duration_ms,
            "evidence_hash": self.evidence_hash,
        }


# Risk score thresholds (0-100)
RISK_THRESHOLDS = {
    RiskLevel.CRITICAL: 90,
    RiskLevel.HIGH: 70,
    RiskLevel.MEDIUM: 50,
    RiskLevel.LOW: 30,
    RiskLevel.MINIMAL: 0,
}

# Category weights for overall score calculation
CATEGORY_WEIGHTS = {
    RiskCategory.SECURITY: 0.30,
    RiskCategory.COMPLIANCE: 0.25,
    RiskCategory.TASK_COMPLEXITY: 0.20,
    RiskCategory.SCOPE: 0.15,
    RiskCategory.COST: 0.10,
}

# High-risk patterns for task descriptions
HIGH_RISK_TASK_PATTERNS: List[Tuple[str, str, str, int]] = [
    (
        r"(?i)(delete|remove|drop)\s+(all|every|entire)\s+"
        r"(files?|data|records?|tables?|databases?)",
        "TR-001",
        "Mass deletion operation",
        85,
    ),
    (
        r"(?i)(deploy|push|release)\s+to\s+(production|prod|live)",
        "TR-002",
        "Production deployment",
        75,
    ),
    (
        r"(?i)(modify|change|update)\s+(credentials?|secrets?|api[_\s]?keys?|tokens?)",
        "TR-003",
        "Credential modification",
        90,
    ),
    (
        r"(?i)(execute|run)\s+(shell|bash|command|script)\s+as\s+(root|admin|sudo)",
        "TR-004",
        "Privileged command execution",
        95,
    ),
    (
        r"(?i)(access|read|export)\s+(customer|user|personal)\s+(data|information|pii)",
        "TR-005",
        "PII access operation",
        80,
    ),
    (
        r"(?i)(disable|turn\s+off|bypass)\s+(security|auth|validation|checks?)",
        "TR-006",
        "Security bypass attempt",
        95,
    ),
    (
        r"(?i)(migrate|transfer)\s+(database|data|schema)",
        "TR-007",
        "Database migration",
        70,
    ),
    (
        r"(?i)(rollback|revert)\s+(production|prod|live)",
        "TR-008",
        "Production rollback",
        75,
    ),
]

# File patterns indicating high-risk operations
HIGH_RISK_FILE_PATTERNS: List[Tuple[str, str, int]] = [
    (r"\.env", "Env-001", 80),
    (r"secrets?\.ya?ml", "Env-002", 85),
    (r"credentials?\.json", "Env-003", 85),
    (r"\.pem$", "Env-004", 90),
    (r"\.key$", "Env-005", 90),
    (r"docker-compose.*\.ya?ml", "Infra-001", 60),
    (r"Dockerfile", "Infra-002", 55),
    (r"terraform/", "Infra-003", 75),
    (r"\.github/workflows/", "CI-001", 65),
    (r"migrations?/", "DB-001", 70),
]

# Scope thresholds
SCOPE_THRESHOLDS = {
    "files_critical": 50,
    "files_high": 20,
    "files_medium": 10,
    "lines_critical": 1000,
    "lines_high": 500,
    "lines_medium": 100,
}


class RiskAnalyzerAgent:
    """
    Risk Analyzer Agent for pre-scanning high-risk tasks.

    Blueprint Reference: Section 3.3 (Agent Catalog V2)
    - Governance/Reasoning Agent
    - Integrates with Safety Governor v2 (Section 4.1)
    - Integrates with Flow Controller v3 (Section 3.2)

    This agent analyzes tasks before execution to:
    1. Identify potential risks across multiple dimensions
    2. Calculate an overall risk score
    3. Provide mitigation recommendations
    4. Flag tasks that require human approval
    """

    def __init__(
        self,
        enabled: bool = True,
        block_on_critical: bool = True,
        require_approval_on_high: bool = True,
        content_safety_integration: bool = True,
    ):
        """
        Initialize RiskAnalyzerAgent.

        Args:
            enabled: Whether risk analysis is enabled
            block_on_critical: If True, block tasks with CRITICAL risk
            require_approval_on_high: If True, require approval for HIGH risk
            content_safety_integration: If True, integrate with ContentSafetyScanner
        """
        self.enabled = enabled
        self.block_on_critical = block_on_critical
        self.require_approval_on_high = require_approval_on_high
        self.content_safety_integration = content_safety_integration
        self._load_settings()
        self._compile_patterns()
        logger.info(
            "[RiskAnalyzerAgent] Initialized - EPIC K P1: "
            "enabled=%s, block_on_critical=%s",
            self.enabled,
            self.block_on_critical,
        )

    def _load_settings(self) -> None:
        """Load settings from environment/config."""
        try:
            from common.config.settings import settings
            self.enabled = getattr(
                settings, "risk_analyzer_enabled", self.enabled
            )
            self.block_on_critical = getattr(
                settings, "risk_analyzer_block_on_critical", self.block_on_critical
            )
            self.require_approval_on_high = getattr(
                settings,
                "risk_analyzer_require_approval_on_high",
                self.require_approval_on_high,
            )
            logger.debug("[RiskAnalyzerAgent] Settings loaded from config")
        except (ImportError, AttributeError) as e:
            logger.debug("[RiskAnalyzerAgent] Using default settings: %s", e)

    def _compile_patterns(self) -> None:
        """Pre-compile regex patterns for performance."""
        self._compiled_task_patterns = [
            (re.compile(pattern, re.IGNORECASE), pid, title, score)
            for pattern, pid, title, score in HIGH_RISK_TASK_PATTERNS
        ]
        self._compiled_file_patterns = [
            (re.compile(pattern, re.IGNORECASE), pid, score)
            for pattern, pid, score in HIGH_RISK_FILE_PATTERNS
        ]

    def analyze_task(
        self,
        task_description: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> RiskAnalysisResult:
        """
        Analyze a task for potential risks.

        This is the main entry point for risk analysis. It evaluates:
        - Task complexity based on description
        - Security risks from patterns and file access
        - Scope risks from affected files/lines
        - Compliance risks from PII/sensitive data
        - Cost risks from expensive operations

        Args:
            task_description: Natural language description of the task
            context: Optional context with additional information:
                - files: List of files to be modified
                - lines_added: Number of lines to add
                - lines_removed: Number of lines to remove
                - agent_type: Type of agent executing the task
                - task_type: Type of task (fix_lint, feature, etc.)

        Returns:
            RiskAnalysisResult with findings and recommendations
        """
        import time
        start_time = time.time()

        if not self.enabled:
            return RiskAnalysisResult(
                overall_score=0,
                overall_level=RiskLevel.MINIMAL,
                action=RiskAction.ALLOW,
                summary="Risk analysis disabled",
            )

        if not task_description or not task_description.strip():
            return RiskAnalysisResult(
                overall_score=0,
                overall_level=RiskLevel.MINIMAL,
                action=RiskAction.ALLOW,
                summary="Empty task description",
            )

        context = context or {}
        findings: List[RiskFinding] = []
        category_scores: Dict[RiskCategory, int] = {}

        # Analyze task complexity
        complexity_findings, complexity_score = self._analyze_task_complexity(
            task_description, context
        )
        findings.extend(complexity_findings)
        category_scores[RiskCategory.TASK_COMPLEXITY] = complexity_score

        # Analyze security risks
        security_findings, security_score = self._analyze_security_risks(
            task_description, context
        )
        findings.extend(security_findings)
        category_scores[RiskCategory.SECURITY] = security_score

        # Analyze scope risks
        scope_findings, scope_score = self._analyze_scope_risks(context)
        findings.extend(scope_findings)
        category_scores[RiskCategory.SCOPE] = scope_score

        # Analyze compliance risks
        compliance_findings, compliance_score = self._analyze_compliance_risks(
            task_description, context
        )
        findings.extend(compliance_findings)
        category_scores[RiskCategory.COMPLIANCE] = compliance_score

        # Analyze cost risks
        cost_findings, cost_score = self._analyze_cost_risks(context)
        findings.extend(cost_findings)
        category_scores[RiskCategory.COST] = cost_score

        # Integrate with ContentSafetyScanner if enabled
        if self.content_safety_integration:
            content_findings, content_score = self._check_content_safety(
                task_description
            )
            findings.extend(content_findings)
            category_scores[RiskCategory.CONTENT_SAFETY] = content_score

        # Calculate overall score
        overall_score = self._calculate_overall_score(category_scores)
        overall_level = self._determine_risk_level(overall_score)
        action = self._determine_action(overall_level, findings)

        # Generate mitigation recommendations
        recommendations = self._generate_recommendations(findings, overall_level)

        # Build summary
        summary = self._generate_summary(
            overall_score, overall_level, findings, category_scores
        )

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000

        # Generate evidence hash
        evidence_hash = self._compute_evidence_hash(task_description, findings)

        result = RiskAnalysisResult(
            overall_score=overall_score,
            overall_level=overall_level,
            action=action,
            findings=findings,
            category_scores=category_scores,
            should_block=(
                action == RiskAction.BLOCK and self.block_on_critical
            ),
            requires_approval=(
                action == RiskAction.REQUIRE_APPROVAL and self.require_approval_on_high
            ),
            mitigation_recommendations=recommendations,
            summary=summary,
            analysis_duration_ms=duration_ms,
            evidence_hash=evidence_hash,
        )

        # Log the analysis
        logger.info(
            "[RiskAnalyzerAgent] Analysis complete: score=%d, level=%s, action=%s",
            overall_score,
            overall_level.value,
            action.value,
            extra={
                "operation": "risk_analysis",
                "overall_score": overall_score,
                "overall_level": overall_level.value,
                "action": action.value,
                "findings_count": len(findings),
                "duration_ms": duration_ms,
            },
        )

        return result

    def _analyze_task_complexity(
        self,
        task_description: str,
        context: Dict[str, Any],
    ) -> Tuple[List[RiskFinding], int]:
        """Analyze task complexity based on description and context."""
        findings: List[RiskFinding] = []
        score = 0

        # Check for high-risk task patterns
        for pattern, pid, title, pattern_score in self._compiled_task_patterns:
            match = pattern.search(task_description)
            if match:
                findings.append(RiskFinding(
                    category=RiskCategory.TASK_COMPLEXITY,
                    level=self._score_to_level(pattern_score),
                    finding_id=pid,
                    title=title,
                    description=f"Task matches high-risk pattern: {title}",
                    score=pattern_score,
                    evidence=match.group(0)[:100],
                    recommendation=f"Review {title.lower()} carefully before execution",
                ))
                score = max(score, pattern_score)

        # Check task type complexity
        task_type = context.get("task_type", "unknown")
        task_type_scores = {
            "fix_lint": 10,
            "fix_typo": 10,
            "documentation_update": 15,
            "add_tests": 20,
            "fix_import": 15,
            "fix_formatting": 10,
            "bugfix": 40,
            "feature": 60,
            "refactor": 50,
            "migration": 75,
            "deployment": 80,
            "unknown": 30,
        }
        type_score = task_type_scores.get(task_type, 30)
        if type_score > 30:
            findings.append(RiskFinding(
                category=RiskCategory.TASK_COMPLEXITY,
                level=self._score_to_level(type_score),
                finding_id="TC-001",
                title=f"Task type: {task_type}",
                description=f"Task type '{task_type}' has elevated complexity",
                score=type_score,
            ))
            score = max(score, type_score)

        return findings, score

    def _analyze_security_risks(
        self,
        task_description: str,
        context: Dict[str, Any],
    ) -> Tuple[List[RiskFinding], int]:
        """Analyze security risks from task and file patterns."""
        findings: List[RiskFinding] = []
        score = 0

        # Check files for high-risk patterns
        files = context.get("files", [])
        for file_path in files:
            for pattern, pid, pattern_score in self._compiled_file_patterns:
                if pattern.search(file_path):
                    findings.append(RiskFinding(
                        category=RiskCategory.SECURITY,
                        level=self._score_to_level(pattern_score),
                        finding_id=pid,
                        title=f"High-risk file: {file_path}",
                        description=f"File '{file_path}' matches security-sensitive pattern",
                        score=pattern_score,
                        evidence=file_path,
                        recommendation=f"Ensure proper review for changes to {file_path}",
                    ))
                    score = max(score, pattern_score)

        # Check for shell/command execution in task
        shell_patterns = [
            (r"(?i)(os\.system|subprocess|shell=True)", "SEC-001", 70),
            (r"(?i)(eval|exec)\s*\(", "SEC-002", 85),
            (r"(?i)(rm\s+-rf|chmod\s+777)", "SEC-003", 90),
        ]
        for pattern_str, pid, pattern_score in shell_patterns:
            pattern = re.compile(pattern_str)
            if pattern.search(task_description):
                findings.append(RiskFinding(
                    category=RiskCategory.SECURITY,
                    level=self._score_to_level(pattern_score),
                    finding_id=pid,
                    title="Dangerous code pattern detected",
                    description="Task contains potentially dangerous code pattern",
                    score=pattern_score,
                    recommendation="Review code for security implications",
                ))
                score = max(score, pattern_score)

        return findings, score

    def _analyze_scope_risks(
        self,
        context: Dict[str, Any],
    ) -> Tuple[List[RiskFinding], int]:
        """Analyze scope risks based on affected files and lines."""
        findings: List[RiskFinding] = []
        score = 0

        files = context.get("files", [])
        lines_added = context.get("lines_added", 0)
        lines_removed = context.get("lines_removed", 0)
        total_lines = lines_added + lines_removed

        # Check file count
        file_count = len(files)
        if file_count >= SCOPE_THRESHOLDS["files_critical"]:
            findings.append(RiskFinding(
                category=RiskCategory.SCOPE,
                level=RiskLevel.CRITICAL,
                finding_id="SCOPE-001",
                title=f"Very large scope: {file_count} files",
                description=f"Task affects {file_count} files (critical threshold: {SCOPE_THRESHOLDS['files_critical']})",
                score=90,
                recommendation="Consider breaking into smaller tasks",
            ))
            score = max(score, 90)
        elif file_count >= SCOPE_THRESHOLDS["files_high"]:
            findings.append(RiskFinding(
                category=RiskCategory.SCOPE,
                level=RiskLevel.HIGH,
                finding_id="SCOPE-002",
                title=f"Large scope: {file_count} files",
                description=f"Task affects {file_count} files",
                score=70,
                recommendation="Review all affected files carefully",
            ))
            score = max(score, 70)
        elif file_count >= SCOPE_THRESHOLDS["files_medium"]:
            findings.append(RiskFinding(
                category=RiskCategory.SCOPE,
                level=RiskLevel.MEDIUM,
                finding_id="SCOPE-003",
                title=f"Moderate scope: {file_count} files",
                description=f"Task affects {file_count} files",
                score=50,
            ))
            score = max(score, 50)

        # Check line count
        if total_lines >= SCOPE_THRESHOLDS["lines_critical"]:
            findings.append(RiskFinding(
                category=RiskCategory.SCOPE,
                level=RiskLevel.HIGH,
                finding_id="SCOPE-004",
                title=f"Large change: {total_lines} lines",
                description=f"Task modifies {total_lines} lines (+{lines_added}/-{lines_removed})",
                score=75,
                recommendation="Consider incremental changes",
            ))
            score = max(score, 75)

        return findings, score

    def _analyze_compliance_risks(
        self,
        task_description: str,
        context: Dict[str, Any],
    ) -> Tuple[List[RiskFinding], int]:
        """Analyze compliance risks (PII, sensitive data)."""
        findings: List[RiskFinding] = []
        score = 0

        # PII patterns
        pii_patterns = [
            (r"(?i)(email|e-mail)\s*(address)?", "COMP-001", "Email handling", 40),
            (r"(?i)(phone|mobile|cell)\s*(number)?", "COMP-002", "Phone number handling", 45),
            (r"(?i)(ssn|social\s*security)", "COMP-003", "SSN handling", 90),
            (r"(?i)(credit\s*card|cc\s*number)", "COMP-004", "Credit card handling", 90),
            (r"(?i)(passport|driver.?s?\s*license)", "COMP-005", "ID document handling", 80),
            (r"(?i)(medical|health)\s*(record|data|info)", "COMP-006", "Medical data handling", 85),
            (r"(?i)(gdpr|ccpa|hipaa)", "COMP-007", "Compliance-regulated data", 75),
        ]

        for pattern_str, pid, title, pattern_score in pii_patterns:
            pattern = re.compile(pattern_str)
            if pattern.search(task_description):
                findings.append(RiskFinding(
                    category=RiskCategory.COMPLIANCE,
                    level=self._score_to_level(pattern_score),
                    finding_id=pid,
                    title=title,
                    description=f"Task involves {title.lower()}",
                    score=pattern_score,
                    recommendation=f"Ensure {title.lower()} complies with regulations",
                ))
                score = max(score, pattern_score)

        return findings, score

    def _analyze_cost_risks(
        self,
        context: Dict[str, Any],
    ) -> Tuple[List[RiskFinding], int]:
        """Analyze cost risks from expensive operations."""
        findings: List[RiskFinding] = []
        score = 0

        # Check for expensive LLM operations
        model_tier = context.get("model_tier", 2)
        if model_tier == 0:
            findings.append(RiskFinding(
                category=RiskCategory.COST,
                level=RiskLevel.MEDIUM,
                finding_id="COST-001",
                title="Tier 0 model usage",
                description="Task uses expensive Tier 0 model",
                score=50,
                recommendation="Consider if Tier 1/2 model would suffice",
            ))
            score = max(score, 50)

        # Check for multiple LLM calls
        estimated_calls = context.get("estimated_llm_calls", 1)
        if estimated_calls > 10:
            findings.append(RiskFinding(
                category=RiskCategory.COST,
                level=RiskLevel.MEDIUM,
                finding_id="COST-002",
                title=f"High LLM call count: {estimated_calls}",
                description=f"Task estimated to make {estimated_calls} LLM calls",
                score=55,
                recommendation="Consider batching or caching",
            ))
            score = max(score, 55)

        return findings, score

    def _check_content_safety(
        self,
        task_description: str,
    ) -> Tuple[List[RiskFinding], int]:
        """Integrate with ContentSafetyScanner for content-based risks."""
        findings: List[RiskFinding] = []
        score = 0

        try:
            from .content_safety_scanner import get_content_safety_scanner
            scanner = get_content_safety_scanner()
            result = scanner.scan(task_description)

            if not result.is_safe:
                for finding in result.findings:
                    risk_level = RiskLevel.HIGH
                    if finding.risk_level.value == "critical":
                        risk_level = RiskLevel.CRITICAL
                    elif finding.risk_level.value == "medium":
                        risk_level = RiskLevel.MEDIUM

                    findings.append(RiskFinding(
                        category=RiskCategory.CONTENT_SAFETY,
                        level=risk_level,
                        finding_id=f"CS-{finding.pattern_id}",
                        title=finding.title,
                        description=finding.description,
                        score=finding.confidence * 100,
                        evidence=finding.matched_text,
                        recommendation=finding.recommendation,
                    ))
                    score = max(score, int(finding.confidence * 100))

        except Exception as e:
            logger.debug(
                "[RiskAnalyzerAgent] ContentSafetyScanner unavailable: %s", e
            )

        return findings, score

    def _calculate_overall_score(
        self,
        category_scores: Dict[RiskCategory, int],
    ) -> int:
        """Calculate weighted overall risk score."""
        if not category_scores:
            return 0

        weighted_sum = 0.0
        total_weight = 0.0

        for category, score in category_scores.items():
            weight = CATEGORY_WEIGHTS.get(category, 0.1)
            weighted_sum += score * weight
            total_weight += weight

        if total_weight == 0:
            return 0

        # Also consider the maximum score (worst case)
        max_score = max(category_scores.values()) if category_scores else 0
        weighted_avg = weighted_sum / total_weight

        # Final score is 70% weighted average + 30% max score
        return int(weighted_avg * 0.7 + max_score * 0.3)

    def _determine_risk_level(self, score: int) -> RiskLevel:
        """Determine risk level from score."""
        if score >= RISK_THRESHOLDS[RiskLevel.CRITICAL]:
            return RiskLevel.CRITICAL
        elif score >= RISK_THRESHOLDS[RiskLevel.HIGH]:
            return RiskLevel.HIGH
        elif score >= RISK_THRESHOLDS[RiskLevel.MEDIUM]:
            return RiskLevel.MEDIUM
        elif score >= RISK_THRESHOLDS[RiskLevel.LOW]:
            return RiskLevel.LOW
        else:
            return RiskLevel.MINIMAL

    def _score_to_level(self, score: int) -> RiskLevel:
        """Convert a score to a risk level."""
        return self._determine_risk_level(score)

    def _determine_action(
        self,
        level: RiskLevel,
        findings: List[RiskFinding],
    ) -> RiskAction:
        """Determine action based on risk level and findings."""
        # Check for any CRITICAL findings
        has_critical = any(f.level == RiskLevel.CRITICAL for f in findings)
        has_high = any(f.level == RiskLevel.HIGH for f in findings)

        if level == RiskLevel.CRITICAL or has_critical:
            return RiskAction.BLOCK
        elif level == RiskLevel.HIGH or has_high:
            return RiskAction.REQUIRE_APPROVAL
        elif level == RiskLevel.MEDIUM:
            return RiskAction.FLAG_FOR_REVIEW
        elif level == RiskLevel.LOW:
            return RiskAction.PROCEED_WITH_CAUTION
        else:
            return RiskAction.ALLOW

    def _generate_recommendations(
        self,
        findings: List[RiskFinding],
        level: RiskLevel,
    ) -> List[str]:
        """Generate mitigation recommendations based on findings."""
        recommendations: List[str] = []

        # Collect unique recommendations from findings
        seen = set()
        for finding in findings:
            if finding.recommendation and finding.recommendation not in seen:
                recommendations.append(finding.recommendation)
                seen.add(finding.recommendation)

        # Add level-specific recommendations
        if level == RiskLevel.CRITICAL:
            recommendations.insert(
                0, "CRITICAL: This task requires human approval before execution"
            )
        elif level == RiskLevel.HIGH:
            recommendations.insert(
                0, "HIGH RISK: Consider additional review before proceeding"
            )

        return recommendations[:10]  # Limit to 10 recommendations

    def _generate_summary(
        self,
        score: int,
        level: RiskLevel,
        findings: List[RiskFinding],
        category_scores: Dict[RiskCategory, int],
    ) -> str:
        """Generate human-readable summary of risk analysis."""
        parts = [
            f"Risk Score: {score}/100 ({level.value.upper()})",
            f"Findings: {len(findings)}",
        ]

        # Add top category scores
        if category_scores:
            top_categories = sorted(
                category_scores.items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]
            category_str = ", ".join(
                f"{cat.value}={score}" for cat, score in top_categories
            )
            parts.append(f"Top risks: {category_str}")

        return " | ".join(parts)

    def _compute_evidence_hash(
        self,
        task_description: str,
        findings: List[RiskFinding],
    ) -> str:
        """Compute hash of evidence for audit trail."""
        evidence_str = task_description + str([f.to_dict() for f in findings])
        return hashlib.sha256(evidence_str.encode()).hexdigest()[:16]


# Module-level singleton
_risk_analyzer: Optional[RiskAnalyzerAgent] = None


def get_risk_analyzer() -> RiskAnalyzerAgent:
    """Get or create the singleton RiskAnalyzerAgent instance."""
    global _risk_analyzer
    if _risk_analyzer is None:
        _risk_analyzer = RiskAnalyzerAgent()
    return _risk_analyzer


def reset_risk_analyzer() -> None:
    """Reset the singleton instance (for testing)."""
    global _risk_analyzer
    _risk_analyzer = None


def analyze_task_risk(
    task_description: str,
    context: Optional[Dict[str, Any]] = None,
) -> RiskAnalysisResult:
    """
    Convenience function to analyze task risk.

    Blueprint Integration:
    - Called by Flow Controller v3 before task execution
    - Results can be used for routing decisions
    - Findings are logged to Evidence Ledger

    Args:
        task_description: Natural language description of the task
        context: Optional context with files, lines, agent_type, etc.

    Returns:
        RiskAnalysisResult with score, level, and recommendations
    """
    analyzer = get_risk_analyzer()
    return analyzer.analyze_task(task_description, context)
