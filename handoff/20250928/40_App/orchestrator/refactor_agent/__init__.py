"""
Refactor Agent - Phase 4 (#1818)

Automated TypeScript strict mode error fixing agent.
Runs nightly to fix TS errors and submit PRs automatically.

.. note::
    The legacy RefactorAgent is deprecated. New code should use RefactorAgentV2
    which provides BaseAgent integration and RoutingEngine support.

    Recommended imports for new code::

        from refactor_agent.agent_v2 import (
            RefactorAgentV2,
            get_refactor_agent_v2,
        )

    Legacy imports (deprecated, will emit warnings)::

        from refactor_agent import RefactorAgent, get_refactor_agent
"""
# V2 imports (recommended)
from refactor_agent.agent_v2 import (
    RefactorAgentV2,
    RefactorRisk,
    RefactorTask,
    RefactorResultV2,
    TSError,
    get_refactor_agent_v2,
)

# Legacy imports (deprecated - will emit DeprecationWarning when used)
from refactor_agent.agent import (
    RefactorAgent,
    RefactorResult,
    get_refactor_agent,
    run_nightly_refactor,
)

__all__ = [
    # V2 exports (recommended)
    "RefactorAgentV2",
    "RefactorResultV2",
    "get_refactor_agent_v2",
    # Shared types
    "RefactorRisk",
    "RefactorTask",
    "TSError",
    # Legacy exports (deprecated)
    "RefactorAgent",
    "RefactorResult",
    "get_refactor_agent",
    "run_nightly_refactor",
]
