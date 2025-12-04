"""
Ops Agent - Phase 3 PR-3 (#1815)

Operations Agent for system health monitoring and operational tasks.
Monitors system health, reads structured logs, and executes restart/rollback operations.
"""

from .agent import (
    OpsAgent,
    OpsAdvisory,
    OpsFinding,
    OpsRisk,
    HealthStatus,
    get_ops_agent,
    check_system_health,
    analyze_logs,
    recommend_action,
)

__all__ = [
    "OpsAgent",
    "OpsAdvisory",
    "OpsFinding",
    "OpsRisk",
    "HealthStatus",
    "get_ops_agent",
    "check_system_health",
    "analyze_logs",
    "recommend_action",
]
