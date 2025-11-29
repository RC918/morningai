#!/usr/bin/env python3
"""
Governance Dashboard Module - Phase 4 PR-5

Aggregates 5-Agent Advisory Pipeline results into a unified dashboard view.
Provides governance summary for monitoring and reporting.

Design Principles:
- Read-only: Only surfaces information, does not change behavior
- Advisory-only: Aggregates advisory results without blocking execution
- Consistent: Follows Phase 3 dashboard patterns
"""

import logging
from typing import Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class DashboardRiskLevel(Enum):
    """Dashboard risk level classification"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class GovernanceDashboardSummary:
    """Summary of governance dashboard data"""
    overall_risk: DashboardRiskLevel
    requires_human_approval: bool
    timestamp: str
    trace_id: str

    security_risk: str
    governance_risk: str
    cost_risk: str
    permission_risk: str
    reputation_level: str

    security_compliant: bool
    governance_compliant: bool
    cost_within_budget: bool
    permission_granted: bool
    reputation_score: int

    findings_by_category: Dict[str, int] = field(default_factory=dict)
    high_risk_findings: int = 0
    total_findings: int = 0

    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "overall_risk": self.overall_risk.value,
            "requires_human_approval": self.requires_human_approval,
            "timestamp": self.timestamp,
            "trace_id": self.trace_id,
            "risk_levels": {
                "security": self.security_risk,
                "governance": self.governance_risk,
                "cost": self.cost_risk,
                "permission": self.permission_risk,
                "reputation": self.reputation_level
            },
            "compliance": {
                "security_compliant": self.security_compliant,
                "governance_compliant": self.governance_compliant,
                "cost_within_budget": self.cost_within_budget,
                "permission_granted": self.permission_granted,
                "reputation_score": self.reputation_score
            },
            "findings": {
                "by_category": self.findings_by_category,
                "high_risk_count": self.high_risk_findings,
                "total_count": self.total_findings
            },
            "recommendations": self.recommendations,
            "metadata": self.metadata
        }


def _get_risk_priority(risk: str) -> int:
    """Get priority value for risk level (higher = more severe)"""
    priority_map = {
        "critical": 5,
        "high": 4,
        "medium": 3,
        "low": 2,
        "info": 1,
        "trusted": 0
    }
    return priority_map.get(risk.lower(), 0)


def _calculate_overall_risk(
    security_risk: str,
    governance_risk: str,
    cost_risk: str,
    permission_risk: str
) -> DashboardRiskLevel:
    """Calculate overall risk from individual risk levels"""
    risks = [security_risk, governance_risk, cost_risk, permission_risk]
    max_priority = max(_get_risk_priority(r) for r in risks)

    if max_priority >= 5:
        return DashboardRiskLevel.CRITICAL
    elif max_priority >= 4:
        return DashboardRiskLevel.HIGH
    elif max_priority >= 3:
        return DashboardRiskLevel.MEDIUM
    elif max_priority >= 2:
        return DashboardRiskLevel.LOW
    else:
        return DashboardRiskLevel.INFO


def _count_findings(advisory: Dict[str, Any]) -> tuple:
    """Count findings from an advisory dict"""
    findings = advisory.get("findings", [])
    total = len(findings)
    high_risk = sum(
        1 for f in findings
        if f.get("risk_level", "").lower() in ["critical", "high"]
    )
    return total, high_risk


def _extract_recommendations(state: Dict[str, Any]) -> List[str]:
    """Extract recommendations from all advisories"""
    recommendations = []

    for advisory_key in ["security_advisory", "governance_advisory", "cost_advisory",
                         "permission_advisory", "reputation_advisory"]:
        advisory = state.get(advisory_key, {})
        if isinstance(advisory, dict):
            recs = advisory.get("recommendations", [])
            if isinstance(recs, list):
                recommendations.extend(recs)

    return list(set(recommendations))


def build_governance_dashboard(state: Dict[str, Any]) -> GovernanceDashboardSummary:
    """
    Build governance dashboard summary from AgentState.

    Takes the full AgentState (with all 5 advisories populated) and returns
    a normalized summary with overall risk, counts per category, and flags.

    Args:
        state: AgentState dict with advisory results from 5-Agent Pipeline

    Returns:
        GovernanceDashboardSummary with aggregated governance data
    """
    trace_id = state.get("trace_id", "unknown")
    timestamp = datetime.utcnow().isoformat()

    security_risk = state.get("security_risk", "info")
    governance_risk = state.get("governance_risk", "info")
    cost_risk = state.get("cost_risk", "info")
    permission_risk = state.get("permission_risk", "info")
    reputation_level = state.get("reputation_level", "trusted")

    security_compliant = state.get("security_compliant", True)
    governance_compliant = state.get("governance_compliant", True)
    cost_within_budget = state.get("cost_within_budget", True)
    permission_granted = state.get("permission_granted", True)
    reputation_score = state.get("reputation_score", 100)

    overall_risk = _calculate_overall_risk(
        security_risk, governance_risk, cost_risk, permission_risk
    )

    requires_human_approval = (
        overall_risk in [DashboardRiskLevel.CRITICAL, DashboardRiskLevel.HIGH] or
        not security_compliant or
        not governance_compliant or
        not permission_granted
    )

    findings_by_category = {}
    total_findings = 0
    high_risk_findings = 0

    for category, advisory_key in [
        ("security", "security_advisory"),
        ("governance", "governance_advisory"),
        ("cost", "cost_advisory"),
        ("permission", "permission_advisory"),
        ("reputation", "reputation_advisory")
    ]:
        advisory = state.get(advisory_key, {})
        if isinstance(advisory, dict):
            count, high_count = _count_findings(advisory)
            findings_by_category[category] = count
            total_findings += count
            high_risk_findings += high_count

    recommendations = _extract_recommendations(state)

    metadata = {
        "task_type": state.get("task_type", "unknown"),
        "goal": state.get("goal", "")[:100] if state.get("goal") else "",
        "plan_steps": len(state.get("plan", [])),
        "agent_id": state.get("agent_id", "orchestrator"),
        "environment": state.get("environment", "sandbox")
    }

    return GovernanceDashboardSummary(
        overall_risk=overall_risk,
        requires_human_approval=requires_human_approval,
        timestamp=timestamp,
        trace_id=trace_id,
        security_risk=security_risk,
        governance_risk=governance_risk,
        cost_risk=cost_risk,
        permission_risk=permission_risk,
        reputation_level=reputation_level,
        security_compliant=security_compliant,
        governance_compliant=governance_compliant,
        cost_within_budget=cost_within_budget,
        permission_granted=permission_granted,
        reputation_score=reputation_score,
        findings_by_category=findings_by_category,
        high_risk_findings=high_risk_findings,
        total_findings=total_findings,
        recommendations=recommendations,
        metadata=metadata
    )


def format_dashboard_text(summary: GovernanceDashboardSummary) -> str:
    """
    Format dashboard summary as human-readable text.

    Args:
        summary: GovernanceDashboardSummary to format

    Returns:
        Formatted text string for CLI display
    """
    lines = []
    lines.append("=" * 70)
    lines.append("Governance Dashboard - 5-Agent Advisory Summary")
    lines.append(f"Time: {summary.timestamp} UTC")
    lines.append(f"Trace ID: {summary.trace_id}")
    lines.append("=" * 70)
    lines.append("")

    risk_status = "PASS" if summary.overall_risk == DashboardRiskLevel.INFO else (
        "WARN" if summary.overall_risk == DashboardRiskLevel.LOW else "FAIL"
    )
    lines.append(f"Overall Risk: {summary.overall_risk.value.upper()} [{risk_status}]")
    lines.append(f"Human Approval Required: {'YES' if summary.requires_human_approval else 'NO'}")
    lines.append("")

    lines.append("Risk Levels by Category")
    lines.append("-" * 40)
    lines.append(f"  Security:    {summary.security_risk:12} [{'PASS' if summary.security_compliant else 'FAIL'}]")
    lines.append(f"  Governance:  {summary.governance_risk:12} [{'PASS' if summary.governance_compliant else 'FAIL'}]")
    lines.append(f"  Cost:        {summary.cost_risk:12} [{'PASS' if summary.cost_within_budget else 'FAIL'}]")
    lines.append(f"  Permission:  {summary.permission_risk:12} [{'PASS' if summary.permission_granted else 'FAIL'}]")
    lines.append(f"  Reputation:  {summary.reputation_level:12} (score: {summary.reputation_score})")
    lines.append("")

    lines.append("Findings Summary")
    lines.append("-" * 40)
    for category, count in summary.findings_by_category.items():
        lines.append(f"  {category.capitalize():12}: {count:5}")
    lines.append(f"  {'High Risk':12}: {summary.high_risk_findings:5}")
    lines.append(f"  {'Total':12}: {summary.total_findings:5}")
    lines.append("")

    if summary.recommendations:
        lines.append("Recommendations")
        lines.append("-" * 40)
        for i, rec in enumerate(summary.recommendations[:5], 1):
            lines.append(f"  {i}. {rec}")
        if len(summary.recommendations) > 5:
            lines.append(f"  ... and {len(summary.recommendations) - 5} more")
        lines.append("")

    lines.append("Task Metadata")
    lines.append("-" * 40)
    lines.append(f"  Task Type:   {summary.metadata.get('task_type', 'unknown')}")
    lines.append(f"  Plan Steps:  {summary.metadata.get('plan_steps', 0)}")
    lines.append(f"  Agent ID:    {summary.metadata.get('agent_id', 'orchestrator')}")
    lines.append(f"  Environment: {summary.metadata.get('environment', 'sandbox')}")
    lines.append("")

    lines.append("=" * 70)

    return "\n".join(lines)


def get_governance_status(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get governance status as a simple dict for API responses.

    Args:
        state: AgentState dict with advisory results

    Returns:
        Dict with governance status suitable for JSON response
    """
    summary = build_governance_dashboard(state)
    return summary.to_dict()
