"""
PM Agent - Phase 3 PR-3 (#1815)

Product Manager Agent for task decomposition and planning.
Accepts high-level goals and decomposes them into actionable sub-tasks.
"""

from .agent import (
    PMAgent,
    PMAdvisory,
    PMFinding,
    PMRisk,
    get_pm_agent,
    decompose_goal,
    plan_implementation,
)

__all__ = [
    "PMAgent",
    "PMAdvisory",
    "PMFinding",
    "PMRisk",
    "get_pm_agent",
    "decompose_goal",
    "plan_implementation",
]
