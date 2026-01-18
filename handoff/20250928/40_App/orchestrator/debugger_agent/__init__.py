"""
Debugger Agent v2 - EPIC D Phase 5 (P2-medium)

Blueprint Reference: Section 3.3 (Agent Catalog V2) - Debugger Agent
Issue: #4104 (EPIC D P2: Debugger Agent v2 Complete Implementation)

This module provides the Debugger Agent v2 standalone agent for autonomous
test failure recovery and CI failure debugging.

Design Principles (Blueprint Section 3.3 - Agent Separation):
- Test Agent generates tests (D-7)
- CI executes tests
- Debugger Agent fixes failing tests (D-4)
- Reviewer Agent validates fixes

What Debugger Agent v2 CAN do:
- Parse CI/test failure logs
- Analyze error types and root causes
- Generate fix suggestions using LLM
- Apply fixes with retry logic (max 3 attempts)
- Escalate to Reviewer when fixes fail

What Debugger Agent v2 CANNOT do (belongs to other agents):
- Generate new tests (that's Test Agent's job)
- Execute tests (that's CI's job)
- Review code quality (that's Reviewer's job)

Usage:
    from debugger_agent import DebuggerAgentV2, get_debugger_agent

    agent = get_debugger_agent()
    result = agent.debug_ci_failure(
        ci_output="FAILED tests/test_foo.py::test_bar - AssertionError",
        files=[{"path": "src/foo.py", "content": "..."}],
        trace_id="trace-123",
    )
"""

from debugger_agent.debugger_agent_v2 import (
    DebuggerAgentV2,
    DebugResult,
    DebugAction,
    DebugSeverity,
    ErrorClassification,
    FixAttempt,
    get_debugger_agent,
    reset_debugger_agent,
    debug_ci_failure,
    analyze_error,
)

__all__ = [
    "DebuggerAgentV2",
    "DebugResult",
    "DebugAction",
    "DebugSeverity",
    "ErrorClassification",
    "FixAttempt",
    "get_debugger_agent",
    "reset_debugger_agent",
    "debug_ci_failure",
    "analyze_error",
]
