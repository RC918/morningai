"""
Refactor Agent - Phase 4 (#1818)

Automated TypeScript strict mode error fixing agent.
Runs nightly to fix TS errors and submit PRs automatically.
"""
from refactor_agent.agent import (
    RefactorAgent,
    RefactorTask,
    RefactorResult,
    RefactorRisk,
    get_refactor_agent,
    run_nightly_refactor,
)

__all__ = [
    "RefactorAgent",
    "RefactorTask",
    "RefactorResult",
    "RefactorRisk",
    "get_refactor_agent",
    "run_nightly_refactor",
]
