"""
AIP v2 Agent Type to Capability Mapping

Blueprint Reference: Section 3.3 - Agent Catalog V2
Maps agent types to their default capabilities.

Issue #4139: This mapping could be externalized to a configuration file
in the future for easier modification without code changes.
"""

from typing import Dict, List

from .handshake import AgentCapability


# =============================================================================
# Agent Type to Capability Mapping
# =============================================================================


AGENT_TYPE_CAPABILITIES: Dict[str, List[AgentCapability]] = {
    "planner": [AgentCapability.CODE_ANALYSIS],
    "coding": [AgentCapability.CODE_WRITING, AgentCapability.CODE_ANALYSIS],
    "reviewer": [AgentCapability.CODE_REVIEW, AgentCapability.CODE_ANALYSIS],
    "test": [AgentCapability.TEST_WRITING, AgentCapability.TEST_EXECUTION],
    "debugger": [AgentCapability.CODE_ANALYSIS, AgentCapability.CODE_WRITING],
    "ui_consistency": [AgentCapability.UI_ANALYSIS],
    "ux_heuristic": [AgentCapability.UX_EVALUATION],
    "visual_regression": [AgentCapability.UI_ANALYSIS],
    "design_token_governance": [AgentCapability.UI_ANALYSIS, AgentCapability.GOVERNANCE],
    "judge": [AgentCapability.GOVERNANCE],
    "debate_left": [AgentCapability.CODE_ANALYSIS],
    "debate_right": [AgentCapability.CODE_ANALYSIS],
    "risk_analyzer": [AgentCapability.RISK_ASSESSMENT, AgentCapability.GOVERNANCE],
    "dev_agent": [
        AgentCapability.CODE_ANALYSIS,
        AgentCapability.CODE_WRITING,
        AgentCapability.CODE_REVIEW,
        AgentCapability.TEST_WRITING,
        AgentCapability.TEST_EXECUTION,
    ],
    "ops_agent": [
        AgentCapability.DEPLOYMENT,
        AgentCapability.MONITORING,
        AgentCapability.INCIDENT_RESPONSE,
    ],
    "pm_agent": [AgentCapability.DOCUMENTATION],
    "growth_strategist": [AgentCapability.DOCUMENTATION],
    "meta_agent": [AgentCapability.GOVERNANCE],
}


def get_capabilities_for_agent_type(agent_type: str) -> List[AgentCapability]:
    """Get the default capabilities for a given agent type.

    Args:
        agent_type: The agent type string (from AgentType enum).

    Returns:
        List of AgentCapability for the agent type (a copy to prevent mutation).
    """
    # Return a copy to prevent callers from mutating the module constant
    return list(AGENT_TYPE_CAPABILITIES.get(agent_type, []))
