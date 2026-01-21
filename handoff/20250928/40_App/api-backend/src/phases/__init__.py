"""
Phase API Modules

This package contains the phase API modules that were migrated from the root directory
to follow Blueprint's modular structure.

Blueprint Reference: Section 3.x (API Organization)
Migration: Moved from root directory per docs/phase-api/README.md

Modules:
- phase4_meta_agent_api: Meta-agent coordination and decision-making
- phase5_data_intelligence_api: Data analytics and business intelligence
- phase6_security_governance_api: Security monitoring and compliance
"""

from .phase4_meta_agent_api import (
    MetaAgentDecisionHub,
    LangGraphWorkflowEngine,
    AIGovernanceConsole,
    DecisionPriority,
    AgentRole,
    router as phase4_router,
)

from .phase5_data_intelligence_api import (
    QuickSightIntegration,
    GrowthMarketingEngine,
    DataIntelligencePlatform,
    router as phase5_router,
)

from .phase6_security_governance_api import (
    SecurityMonitoringSystem,
    ComplianceEngine,
    GovernanceFramework,
    SecurityEvent,
    SecurityLevel,
    ThreatType,
    router as phase6_router,
)

__all__ = [
    # Phase 4
    "MetaAgentDecisionHub",
    "LangGraphWorkflowEngine",
    "AIGovernanceConsole",
    "DecisionPriority",
    "AgentRole",
    "phase4_router",
    # Phase 5
    "QuickSightIntegration",
    "GrowthMarketingEngine",
    "DataIntelligencePlatform",
    "phase5_router",
    # Phase 6
    "SecurityMonitoringSystem",
    "ComplianceEngine",
    "GovernanceFramework",
    "SecurityEvent",
    "SecurityLevel",
    "ThreatType",
    "phase6_router",
]
