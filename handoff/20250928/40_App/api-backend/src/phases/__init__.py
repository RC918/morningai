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
    OODAContext,
    DecisionResult,
    api_meta_agent_ooda_cycle,
    api_create_langgraph_workflow,
    api_execute_workflow,
    api_governance_status,
    api_create_governance_policy,
)

from .phase5_data_intelligence_api import (
    QuickSightIntegration,
    GrowthMarketingEngine,
    DataIntelligencePlatform,
    DataInsight,
    GrowthMetric,
    api_create_quicksight_dashboard,
    api_get_dashboard_insights,
    api_generate_automated_report,
    api_create_referral_program,
    api_get_referral_analytics,
    api_generate_marketing_content,
    api_get_business_intelligence,
)

from .phase6_security_governance_api import (
    ZeroTrustSecurityModel,
    SecurityReviewerAgent,
    HITLSecurityAnalysis,
    SecurityAuditSystem,
    SecurityEvent,
    SecurityLevel,
    ThreatType,
    ZeroTrustPolicy,
    api_evaluate_access_request,
    api_review_security_event,
    api_submit_hitl_review,
    api_get_pending_reviews,
    api_perform_security_audit,
)

__all__ = [
    # Phase 4
    "MetaAgentDecisionHub",
    "LangGraphWorkflowEngine",
    "AIGovernanceConsole",
    "DecisionPriority",
    "AgentRole",
    "OODAContext",
    "DecisionResult",
    "api_meta_agent_ooda_cycle",
    "api_create_langgraph_workflow",
    "api_execute_workflow",
    "api_governance_status",
    "api_create_governance_policy",
    # Phase 5
    "QuickSightIntegration",
    "GrowthMarketingEngine",
    "DataIntelligencePlatform",
    "DataInsight",
    "GrowthMetric",
    "api_create_quicksight_dashboard",
    "api_get_dashboard_insights",
    "api_generate_automated_report",
    "api_create_referral_program",
    "api_get_referral_analytics",
    "api_generate_marketing_content",
    "api_get_business_intelligence",
    # Phase 6
    "ZeroTrustSecurityModel",
    "SecurityReviewerAgent",
    "HITLSecurityAnalysis",
    "SecurityAuditSystem",
    "SecurityEvent",
    "SecurityLevel",
    "ThreatType",
    "ZeroTrustPolicy",
    "api_evaluate_access_request",
    "api_review_security_event",
    "api_submit_hitl_review",
    "api_get_pending_reviews",
    "api_perform_security_audit",
]
