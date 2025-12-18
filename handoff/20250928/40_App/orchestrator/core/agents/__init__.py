"""
Agent Base Classes for MorningAI Orchestrator

EPIC #2594 - Ticket 3: Agent Base Class Upgrade (AIP v2)

This module provides base classes for agents that integrate with:
- RoutingEngine for dynamic model selection
- Telemetry v2 for structured JSON logging
- Standardized Input/Output schemas

Usage:
    from core.agents import BaseAgent, AgentInput, AgentOutput, TelemetryEvent

    class MyAgent(BaseAgent):
        def __init__(self):
            super().__init__(agent_id="my_agent")

        async def execute(self, input: AgentInput) -> AgentOutput:
            # Use routing-aware LLM call
            response = await self.call_llm(
                prompt="Your prompt",
                task_type=TaskType.CODING,
                risk_level=RiskLevel.MEDIUM
            )
            return AgentOutput(success=True, data={"response": response})
"""

from .base import (
    BaseAgent,
    AgentInput,
    AgentOutput,
    TelemetryEvent,
    TelemetryEventType,
)

__all__ = [
    'BaseAgent',
    'AgentInput',
    'AgentOutput',
    'TelemetryEvent',
    'TelemetryEventType',
]
