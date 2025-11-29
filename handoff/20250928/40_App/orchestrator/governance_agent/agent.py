#!/usr/bin/env python3
"""
Governance Agent - Phase 4 PR-3

Advisory agent for governance analysis in the 5-Agent Advisory Pipeline.
Provides governance recommendations for task execution, integrating with
existing governance modules (PolicyGuard, ViolationDetector, CostTracker,
PermissionChecker, ReputationEngine).

Design Principles:
- Advisory role: Provides recommendations, does not block execution
- Unified governance: Integrates all existing governance modules
- Configurable: Governance policies configurable via policies.yaml
- Risk assessment: Evaluates policy compliance, cost, and permission risks
"""
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)


class GovernanceRisk(Enum):
    """Governance risk levels"""
    CRITICAL = "critical"  # Policy violation, should block
    HIGH = "high"          # Budget exceeded or permission denied
    MEDIUM = "medium"      # Warning threshold reached
    LOW = "low"            # Minor governance concern
    INFO = "info"          # No risk, informational only


@dataclass
class GovernanceFinding:
    """Represents a governance finding"""
    category: str           # e.g., "policy", "cost", "permission", "violation"
    risk_level: GovernanceRisk
    title: str
    description: str
    source: str = ""        # Which governance module detected this
    recommendation: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class GovernanceAdvisory:
    """Governance advisory result from GovernanceAgent analysis"""
    is_compliant: bool
    overall_risk: GovernanceRisk
    findings: List[GovernanceFinding] = field(default_factory=list)
    summary: str = ""
    recommendations: List[str] = field(default_factory=list)
    policy_status: Dict[str, Any] = field(default_factory=dict)
    cost_status: Dict[str, Any] = field(default_factory=dict)
    permission_status: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "is_compliant": self.is_compliant,
            "overall_risk": self.overall_risk.value,
            "findings": [
                {
                    "category": f.category,
                    "risk_level": f.risk_level.value,
                    "title": f.title,
                    "description": f.description,
                    "source": f.source,
                    "recommendation": f.recommendation,
                    "metadata": f.metadata,
                }
                for f in self.findings
            ],
            "summary": self.summary,
            "recommendations": self.recommendations,
            "policy_status": self.policy_status,
            "cost_status": self.cost_status,
            "permission_status": self.permission_status,
            "metadata": self.metadata,
        }


class GovernanceAgent:
    """
    Governance Agent for the 5-Agent Advisory Pipeline.

    Phase 4 PR-3 Features:
    - Policy compliance checking (PolicyGuard integration)
    - Violation detection (ViolationDetector integration)
    - Cost budget monitoring (CostTracker integration)
    - Permission verification (PermissionChecker integration)
    - Risk level assessment based on file patterns
    - Human approval requirement detection
    """

    def __init__(self):
        """Initialize GovernanceAgent with governance module integration"""
        self._load_settings()
        self._init_governance_modules()
        logger.info("[GovernanceAgent] Initialized - Phase 4 PR-3")

    def _load_settings(self):
        """Load settings from environment"""
        try:
            from common.config.settings import settings
            self.enabled = getattr(settings, 'governance_agent_enabled', True)
            self.strict_mode = getattr(settings, 'governance_agent_strict_mode', False)
            logger.info(f"[GovernanceAgent] Settings loaded: enabled={self.enabled}, strict_mode={self.strict_mode}")
        except ImportError:
            self.enabled = True
            self.strict_mode = False
            logger.warning("[GovernanceAgent] Settings not available, using defaults")

    def _init_governance_modules(self):
        """Initialize governance module integrations"""
        self.policy_guard = None
        self.violation_detector = None
        self.cost_tracker = None
        self.permission_checker = None
        self.reputation_engine = None

        try:
            from governance.policy_guard import get_policy_guard
            self.policy_guard = get_policy_guard()
            logger.info("[GovernanceAgent] PolicyGuard integration enabled")
        except ImportError as e:
            logger.warning(f"[GovernanceAgent] PolicyGuard not available: {e}")

        try:
            from governance.violation_detector import get_violation_detector
            self.violation_detector = get_violation_detector()
            logger.info("[GovernanceAgent] ViolationDetector integration enabled")
        except ImportError as e:
            logger.warning(f"[GovernanceAgent] ViolationDetector not available: {e}")

        try:
            from governance.cost_tracker import get_cost_tracker
            self.cost_tracker = get_cost_tracker()
            logger.info("[GovernanceAgent] CostTracker integration enabled")
        except ImportError as e:
            logger.warning(f"[GovernanceAgent] CostTracker not available: {e}")

        try:
            from governance.permission_checker import get_permission_checker
            self.permission_checker = get_permission_checker()
            logger.info("[GovernanceAgent] PermissionChecker integration enabled")
        except ImportError as e:
            logger.warning(f"[GovernanceAgent] PermissionChecker not available: {e}")

        try:
            from governance.reputation_engine import get_reputation_engine
            self.reputation_engine = get_reputation_engine()
            logger.info("[GovernanceAgent] ReputationEngine integration enabled")
        except ImportError as e:
            logger.warning(f"[GovernanceAgent] ReputationEngine not available: {e}")

    def analyze_policy_compliance(
        self,
        file_paths: List[str],
        operations: Optional[List[str]] = None,
        agent_permission_level: str = "sandbox_only"
    ) -> GovernanceAdvisory:
        """
        Analyze policy compliance for file access and operations.

        Args:
            file_paths: List of file paths to check
            operations: List of operations to check
            agent_permission_level: Current agent permission level

        Returns:
            GovernanceAdvisory with policy compliance findings
        """
        findings: List[GovernanceFinding] = []
        policy_status = {
            "files_checked": len(file_paths),
            "operations_checked": len(operations) if operations else 0,
            "violations": [],
            "risk_level": "low_risk"
        }

        if not self.policy_guard:
            return GovernanceAdvisory(
                is_compliant=True,
                overall_risk=GovernanceRisk.INFO,
                findings=[],
                summary="PolicyGuard not available, skipping policy checks",
                policy_status=policy_status
            )

        for file_path in file_paths:
            try:
                self.policy_guard.check_file_access(file_path)
            except Exception as e:
                findings.append(GovernanceFinding(
                    category="policy",
                    risk_level=GovernanceRisk.HIGH,
                    title="File Access Policy Violation",
                    description=str(e),
                    source="PolicyGuard",
                    recommendation=f"Remove or modify access to: {file_path}"
                ))
                policy_status["violations"].append({
                    "type": "file_access",
                    "path": file_path,
                    "error": str(e)
                })

        risk_level = self.policy_guard.check_risk_level(file_paths)
        policy_status["risk_level"] = risk_level

        if risk_level == "high_risk":
            findings.append(GovernanceFinding(
                category="policy",
                risk_level=GovernanceRisk.MEDIUM,
                title="High Risk File Pattern Detected",
                description=f"Files match high-risk patterns: {file_paths}",
                source="PolicyGuard",
                recommendation="Review changes carefully before proceeding"
            ))

        operations = operations or []
        for operation in operations:
            try:
                self.policy_guard.check_tool_permission(
                    tool_name=operation,
                    operation="execute",
                    agent_permission_level=agent_permission_level
                )
            except Exception as e:
                findings.append(GovernanceFinding(
                    category="policy",
                    risk_level=GovernanceRisk.HIGH,
                    title="Tool Permission Denied",
                    description=str(e),
                    source="PolicyGuard",
                    recommendation=f"Request elevated permissions for: {operation}"
                ))
                policy_status["violations"].append({
                    "type": "tool_permission",
                    "operation": operation,
                    "error": str(e)
                })

        overall_risk = self._calculate_overall_risk(findings)
        is_compliant = len([f for f in findings if f.risk_level in [GovernanceRisk.CRITICAL, GovernanceRisk.HIGH]]) == 0

        return GovernanceAdvisory(
            is_compliant=is_compliant,
            overall_risk=overall_risk,
            findings=findings,
            summary=self._generate_summary(findings, "policy"),
            recommendations=self._generate_recommendations(findings),
            policy_status=policy_status
        )

    def analyze_violations(
        self,
        content: str,
        operation: str = "general",
        metadata: Optional[Dict[str, Any]] = None
    ) -> GovernanceAdvisory:
        """
        Analyze content for policy violations.

        Args:
            content: Content to analyze (code, command, etc.)
            operation: Type of operation (file_access, shell_command, api_call)
            metadata: Additional metadata for analysis

        Returns:
            GovernanceAdvisory with violation findings
        """
        findings: List[GovernanceFinding] = []

        if not self.violation_detector:
            return GovernanceAdvisory(
                is_compliant=True,
                overall_risk=GovernanceRisk.INFO,
                findings=[],
                summary="ViolationDetector not available, skipping violation checks"
            )

        try:
            self.violation_detector.check_secrets_access(content)
        except Exception as e:
            findings.append(GovernanceFinding(
                category="violation",
                risk_level=GovernanceRisk.CRITICAL,
                title="Secrets Access Violation",
                description=str(e),
                source="ViolationDetector",
                recommendation="Remove secrets access patterns from content"
            ))

        if operation == "shell_command":
            try:
                self.violation_detector.check_dangerous_operations(content)
            except Exception as e:
                findings.append(GovernanceFinding(
                    category="violation",
                    risk_level=GovernanceRisk.HIGH,
                    title="Dangerous Operation Detected",
                    description=str(e),
                    source="ViolationDetector",
                    recommendation="Use safer alternatives for this operation"
                ))

        overall_risk = self._calculate_overall_risk(findings)
        is_compliant = len([f for f in findings if f.risk_level in [GovernanceRisk.CRITICAL, GovernanceRisk.HIGH]]) == 0

        return GovernanceAdvisory(
            is_compliant=is_compliant,
            overall_risk=overall_risk,
            findings=findings,
            summary=self._generate_summary(findings, "violation"),
            recommendations=self._generate_recommendations(findings)
        )

    def analyze_cost_budget(
        self,
        trace_id: str,
        estimated_tokens: int = 0,
        model: str = "gpt-4"
    ) -> GovernanceAdvisory:
        """
        Analyze cost budget status.

        Args:
            trace_id: Task trace ID
            estimated_tokens: Estimated tokens for upcoming operation
            model: Model to use for cost estimation

        Returns:
            GovernanceAdvisory with cost budget findings
        """
        findings: List[GovernanceFinding] = []
        cost_status = {
            "trace_id": trace_id,
            "estimated_tokens": estimated_tokens,
            "model": model,
            "budget_status": {}
        }

        if not self.cost_tracker:
            return GovernanceAdvisory(
                is_compliant=True,
                overall_risk=GovernanceRisk.INFO,
                findings=[],
                summary="CostTracker not available, skipping cost checks",
                cost_status=cost_status
            )

        try:
            budget_status = self.cost_tracker.get_cost_summary(trace_id)
            cost_status["budget_status"] = budget_status

            for period, status in budget_status.items():
                if not status.get("within_budget", True):
                    findings.append(GovernanceFinding(
                        category="cost",
                        risk_level=GovernanceRisk.HIGH,
                        title=f"{period.capitalize()} Budget Exceeded",
                        description=f"Budget exceeded for {period}: {status}",
                        source="CostTracker",
                        recommendation=f"Wait for {period} budget to reset or request budget increase",
                        metadata=status
                    ))

                alert_level = status.get("alert_level", "ok")
                if alert_level == "critical":
                    findings.append(GovernanceFinding(
                        category="cost",
                        risk_level=GovernanceRisk.MEDIUM,
                        title=f"{period.capitalize()} Budget Critical",
                        description=f"Budget at critical level for {period}",
                        source="CostTracker",
                        recommendation="Monitor usage closely, approaching budget limit"
                    ))
                elif alert_level == "warning":
                    findings.append(GovernanceFinding(
                        category="cost",
                        risk_level=GovernanceRisk.LOW,
                        title=f"{period.capitalize()} Budget Warning",
                        description=f"Budget at warning level for {period}",
                        source="CostTracker",
                        recommendation="Consider reducing token usage"
                    ))

            if estimated_tokens > 0:
                estimated_cost = self.cost_tracker.estimate_cost(estimated_tokens, model)
                cost_status["estimated_cost_usd"] = estimated_cost

        except Exception as e:
            logger.warning(f"[GovernanceAgent] Cost analysis error: {e}")
            cost_status["error"] = str(e)

        overall_risk = self._calculate_overall_risk(findings)
        is_compliant = len([f for f in findings if f.risk_level == GovernanceRisk.HIGH]) == 0

        return GovernanceAdvisory(
            is_compliant=is_compliant,
            overall_risk=overall_risk,
            findings=findings,
            summary=self._generate_summary(findings, "cost"),
            recommendations=self._generate_recommendations(findings),
            cost_status=cost_status
        )

    def analyze_permissions(
        self,
        agent_id: str,
        operations: List[str],
        environment: str = "sandbox"
    ) -> GovernanceAdvisory:
        """
        Analyze agent permissions for operations.

        Args:
            agent_id: Agent UUID
            operations: List of operations to check
            environment: Target environment (sandbox, staging, production)

        Returns:
            GovernanceAdvisory with permission findings
        """
        findings: List[GovernanceFinding] = []
        permission_status = {
            "agent_id": agent_id,
            "environment": environment,
            "operations_checked": operations,
            "denied_operations": []
        }

        if not self.permission_checker:
            return GovernanceAdvisory(
                is_compliant=True,
                overall_risk=GovernanceRisk.INFO,
                findings=[],
                summary="PermissionChecker not available, skipping permission checks",
                permission_status=permission_status
            )

        try:
            permission_summary = self.permission_checker.get_permission_summary(agent_id)
            permission_status["permission_summary"] = permission_summary
        except Exception as e:
            logger.warning(f"[GovernanceAgent] Permission summary error: {e}")

        can_access_env = self.permission_checker.can_access_environment(agent_id, environment)
        if not can_access_env:
            findings.append(GovernanceFinding(
                category="permission",
                risk_level=GovernanceRisk.HIGH,
                title="Environment Access Denied",
                description=f"Agent {agent_id} cannot access {environment} environment",
                source="PermissionChecker",
                recommendation=f"Request access to {environment} environment or use sandbox"
            ))

        for operation in operations:
            try:
                self.permission_checker.check_permission(agent_id, operation)
            except Exception as e:
                findings.append(GovernanceFinding(
                    category="permission",
                    risk_level=GovernanceRisk.HIGH,
                    title="Operation Permission Denied",
                    description=str(e),
                    source="PermissionChecker",
                    recommendation=f"Build reputation to unlock: {operation}"
                ))
                permission_status["denied_operations"].append(operation)

        overall_risk = self._calculate_overall_risk(findings)
        is_compliant = len([f for f in findings if f.risk_level in [GovernanceRisk.CRITICAL, GovernanceRisk.HIGH]]) == 0

        return GovernanceAdvisory(
            is_compliant=is_compliant,
            overall_risk=overall_risk,
            findings=findings,
            summary=self._generate_summary(findings, "permission"),
            recommendations=self._generate_recommendations(findings),
            permission_status=permission_status
        )

    def analyze_human_approval(
        self,
        labels: List[str],
        file_paths: List[str]
    ) -> GovernanceAdvisory:
        """
        Check if human approval is required.

        Args:
            labels: Task labels
            file_paths: Files being modified

        Returns:
            GovernanceAdvisory with human approval findings
        """
        findings: List[GovernanceFinding] = []

        if not self.policy_guard:
            return GovernanceAdvisory(
                is_compliant=True,
                overall_risk=GovernanceRisk.INFO,
                findings=[],
                summary="PolicyGuard not available, skipping human approval check"
            )

        risk_level = self.policy_guard.check_risk_level(file_paths)
        requires_approval = self.policy_guard.requires_human_approval(labels, risk_level)

        if requires_approval:
            findings.append(GovernanceFinding(
                category="approval",
                risk_level=GovernanceRisk.MEDIUM,
                title="Human Approval Required",
                description=f"Task requires human approval (risk_level={risk_level}, labels={labels})",
                source="PolicyGuard",
                recommendation="Request human review before proceeding"
            ))

        overall_risk = GovernanceRisk.MEDIUM if requires_approval else GovernanceRisk.INFO
        is_compliant = not requires_approval

        return GovernanceAdvisory(
            is_compliant=is_compliant,
            overall_risk=overall_risk,
            findings=findings,
            summary="Human approval required" if requires_approval else "No human approval required",
            recommendations=["Request human review"] if requires_approval else [],
            metadata={"requires_human_approval": requires_approval, "risk_level": risk_level}
        )

    def analyze_task(
        self,
        task_type: str,
        trace_id: str,
        agent_id: str = "default",
        file_paths: Optional[List[str]] = None,
        operations: Optional[List[str]] = None,
        content: Optional[str] = None,
        labels: Optional[List[str]] = None,
        environment: str = "sandbox",
        estimated_tokens: int = 0
    ) -> GovernanceAdvisory:
        """
        Comprehensive governance analysis for a task.

        Args:
            task_type: Type of task
            trace_id: Task trace ID
            agent_id: Agent UUID
            file_paths: Files being accessed/modified
            operations: Operations being performed
            content: Content to analyze for violations
            labels: Task labels
            environment: Target environment
            estimated_tokens: Estimated tokens for the task

        Returns:
            GovernanceAdvisory with comprehensive governance findings
        """
        all_findings: List[GovernanceFinding] = []
        file_paths = file_paths or []
        operations = operations or []
        labels = labels or []
        content = content or ""

        logger.info(f"[GovernanceAgent] Analyzing task: type={task_type}, trace_id={trace_id}")

        policy_advisory = self.analyze_policy_compliance(
            file_paths=file_paths,
            operations=operations
        )
        all_findings.extend(policy_advisory.findings)

        if content:
            violation_advisory = self.analyze_violations(
                content=content,
                operation="general"
            )
            all_findings.extend(violation_advisory.findings)

        cost_advisory = self.analyze_cost_budget(
            trace_id=trace_id,
            estimated_tokens=estimated_tokens
        )
        all_findings.extend(cost_advisory.findings)

        permission_advisory = self.analyze_permissions(
            agent_id=agent_id,
            operations=operations,
            environment=environment
        )
        all_findings.extend(permission_advisory.findings)

        approval_advisory = self.analyze_human_approval(
            labels=labels,
            file_paths=file_paths
        )
        all_findings.extend(approval_advisory.findings)

        overall_risk = self._calculate_overall_risk(all_findings)
        is_compliant = len([f for f in all_findings if f.risk_level in [GovernanceRisk.CRITICAL, GovernanceRisk.HIGH]]) == 0

        return GovernanceAdvisory(
            is_compliant=is_compliant,
            overall_risk=overall_risk,
            findings=all_findings,
            summary=self._generate_summary(all_findings, "governance"),
            recommendations=self._generate_recommendations(all_findings),
            policy_status=policy_advisory.policy_status,
            cost_status=cost_advisory.cost_status,
            permission_status=permission_advisory.permission_status,
            metadata={
                "task_type": task_type,
                "trace_id": trace_id,
                "agent_id": agent_id,
                "environment": environment,
                "requires_human_approval": approval_advisory.metadata.get("requires_human_approval", False)
            }
        )

    def _calculate_overall_risk(self, findings: List[GovernanceFinding]) -> GovernanceRisk:
        """Calculate overall risk level from findings"""
        if not findings:
            return GovernanceRisk.INFO

        risk_priority = {
            GovernanceRisk.CRITICAL: 4,
            GovernanceRisk.HIGH: 3,
            GovernanceRisk.MEDIUM: 2,
            GovernanceRisk.LOW: 1,
            GovernanceRisk.INFO: 0
        }

        max_risk = max(findings, key=lambda f: risk_priority.get(f.risk_level, 0))
        return max_risk.risk_level

    def _generate_recommendations(self, findings: List[GovernanceFinding]) -> List[str]:
        """Generate unique recommendations from findings"""
        recommendations = []
        seen = set()

        for finding in findings:
            if finding.recommendation and finding.recommendation not in seen:
                recommendations.append(finding.recommendation)
                seen.add(finding.recommendation)

        return recommendations

    def _generate_summary(self, findings: List[GovernanceFinding], context: str) -> str:
        """Generate summary from findings"""
        if not findings:
            return f"No {context} issues detected"

        critical_count = len([f for f in findings if f.risk_level == GovernanceRisk.CRITICAL])
        high_count = len([f for f in findings if f.risk_level == GovernanceRisk.HIGH])
        medium_count = len([f for f in findings if f.risk_level == GovernanceRisk.MEDIUM])
        low_count = len([f for f in findings if f.risk_level == GovernanceRisk.LOW])

        parts = []
        if critical_count > 0:
            parts.append(f"{critical_count} critical")
        if high_count > 0:
            parts.append(f"{high_count} high")
        if medium_count > 0:
            parts.append(f"{medium_count} medium")
        if low_count > 0:
            parts.append(f"{low_count} low")

        return f"Found {len(findings)} {context} findings: {', '.join(parts)}"


_governance_agent: Optional[GovernanceAgent] = None


def get_governance_agent() -> GovernanceAgent:
    """Get or create global GovernanceAgent instance (singleton pattern)"""
    global _governance_agent
    if _governance_agent is None:
        _governance_agent = GovernanceAgent()
    return _governance_agent


def analyze_governance(
    task_type: str,
    trace_id: str,
    agent_id: str = "default",
    file_paths: Optional[List[str]] = None,
    operations: Optional[List[str]] = None,
    content: Optional[str] = None,
    labels: Optional[List[str]] = None,
    environment: str = "sandbox",
    estimated_tokens: int = 0
) -> GovernanceAdvisory:
    """Convenience function for governance analysis"""
    agent = get_governance_agent()
    return agent.analyze_task(
        task_type=task_type,
        trace_id=trace_id,
        agent_id=agent_id,
        file_paths=file_paths,
        operations=operations,
        content=content,
        labels=labels,
        environment=environment,
        estimated_tokens=estimated_tokens
    )
