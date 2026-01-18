#!/usr/bin/env python3
"""
Test Agent v2 Module - EPIC D Phase 5 (P2-medium)

Blueprint Reference: Section 3.3 (Agent Catalog V2) - Test Agent
Issue: #4102 (EPIC D P2: Test Agent v2 Complete Implementation)

This module implements the Test Agent v2 as a standalone agent that:
1. Integrates with B-11 Test Coverage Flagging to identify coverage gaps
2. Generates tests from coverage gaps using LLM or templates
3. Validates test quality (syntax, assertions, coverage)
4. Provides test recommendations and improvements

All agents integrate with:
- Safety Governor v2 (Section 4.1) for content safety
- Flow Controller v3 (Section 3.2) for task routing decisions
- Evidence Ledger (Section 4.6) for audit trail
- B-11 Test Coverage Flagging for coverage gap detection

Design Principles (Blueprint Section 3.3 - Agent Separation):
- Reviewer Agent flags coverage gaps (B-11)
- Test Agent generates tests (D-7)
- CI executes tests
- Debugger Agent fixes failing tests (D-4)
"""

from test_agent.test_agent_v2 import (
    TestAgentV2,
    TestGenerationRequest,
    TestGenerationResponse,
    TestQualityResult,
    TestQualityLevel,
    TestQualityCategory,
    get_test_agent,
    reset_test_agent,
    generate_tests,
    validate_test_quality,
)

__all__ = [
    "TestAgentV2",
    "TestGenerationRequest",
    "TestGenerationResponse",
    "TestQualityResult",
    "TestQualityLevel",
    "TestQualityCategory",
    "get_test_agent",
    "reset_test_agent",
    "generate_tests",
    "validate_test_quality",
]
