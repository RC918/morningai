#!/usr/bin/env python3
"""
UX/UI Agents Module - EPIC K Phase 2 (P2-medium)

Blueprint Reference: Section 3.3 (Agent Catalog V2) - UX/UI Agents

This module implements the 4 UI/UX Agents defined in the Blueprint:
1. UI Consistency Agent - Ensures UI component consistency across the application
2. UX Heuristic Agent - Evaluates UX patterns against Nielsen's heuristics
3. Visual Regression Agent - Detects visual changes and regressions
4. Design Token Governance Agent - Enforces design token usage and compliance

All agents integrate with:
- Safety Governor v2 (Section 4.1) for content safety
- Flow Controller v3 (Section 3.2) for task routing decisions
- Evidence Ledger (Section 4.6) for audit trail
- shared-ui component library for design token validation

Issue: #4097 (EPIC K P2: 4 UI/UX Agents Implementation)
"""

from ux_agents.ui_consistency_agent import (
    UIConsistencyAgent,
    UIConsistencyFinding,
    UIConsistencyResult,
    ConsistencyCategory,
    ConsistencyLevel,
    get_ui_consistency_agent,
    analyze_ui_consistency,
)

from ux_agents.ux_heuristic_agent import (
    UXHeuristicAgent,
    HeuristicFinding,
    HeuristicResult,
    NielsenHeuristic,
    HeuristicSeverity,
    get_ux_heuristic_agent,
    analyze_ux_heuristics,
)

from ux_agents.visual_regression_agent import (
    VisualRegressionAgent,
    VisualRegressionFinding,
    VisualRegressionResult,
    RegressionType,
    RegressionSeverity,
    get_visual_regression_agent,
    analyze_visual_regression,
)

from ux_agents.design_token_agent import (
    DesignTokenGovernanceAgent,
    TokenViolation,
    TokenGovernanceResult,
    ViolationType,
    ViolationSeverity,
    get_design_token_agent,
    analyze_design_tokens,
)

__all__ = [
    "UIConsistencyAgent",
    "UIConsistencyFinding",
    "UIConsistencyResult",
    "ConsistencyCategory",
    "ConsistencyLevel",
    "get_ui_consistency_agent",
    "analyze_ui_consistency",
    "UXHeuristicAgent",
    "HeuristicFinding",
    "HeuristicResult",
    "NielsenHeuristic",
    "HeuristicSeverity",
    "get_ux_heuristic_agent",
    "analyze_ux_heuristics",
    "VisualRegressionAgent",
    "VisualRegressionFinding",
    "VisualRegressionResult",
    "RegressionType",
    "RegressionSeverity",
    "get_visual_regression_agent",
    "analyze_visual_regression",
    "DesignTokenGovernanceAgent",
    "TokenViolation",
    "TokenGovernanceResult",
    "ViolationType",
    "ViolationSeverity",
    "get_design_token_agent",
    "analyze_design_tokens",
]
