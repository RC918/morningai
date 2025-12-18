"""
Base Agent Class with Dynamic Routing and Telemetry v2

EPIC #2594 - Ticket 3: Agent Base Class Upgrade (AIP v2)

This module provides the BaseAgent class that integrates:
- RoutingEngine for dynamic model selection based on task type and risk level
- Telemetry v2 for structured JSON logging
- Standardized Input/Output schemas

Reference: "Agent Interaction Protocol v2"
"""
import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class TelemetryEventType(str, Enum):
    """Types of telemetry events for Telemetry v2"""
    MODEL_CALL = "model_call"
    AGENT_START = "agent_start"
    AGENT_END = "agent_end"
    TASK_START = "task_start"
    TASK_END = "task_end"
    ERROR = "error"


@dataclass
class TelemetryEvent:
    """
    Telemetry v2 Event for structured JSON logging

    Format matches the specification in Ticket #2655:
    {
      "event_type": "model_call",
      "timestamp": "2025-12-17T19:00:00Z",
      "agent_id": "dev_agent",
      "task_type": "coding",
      "model_selected": "qwen-max",
      "provider": "alicloud",
      "latency_ms": 1500,
      "tokens_in": 500,
      "tokens_out": 200
    }
    """
    event_type: TelemetryEventType
    timestamp: str
    agent_id: str
    task_type: Optional[str] = None
    model_selected: Optional[str] = None
    provider: Optional[str] = None
    latency_ms: Optional[float] = None
    tokens_in: Optional[int] = None
    tokens_out: Optional[int] = None
    success: Optional[bool] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = {
            "event_type": self.event_type.value,
            "timestamp": self.timestamp,
            "agent_id": self.agent_id,
        }
        if self.task_type is not None:
            result["task_type"] = self.task_type
        if self.model_selected is not None:
            result["model_selected"] = self.model_selected
        if self.provider is not None:
            result["provider"] = self.provider
        if self.latency_ms is not None:
            result["latency_ms"] = self.latency_ms
        if self.tokens_in is not None:
            result["tokens_in"] = self.tokens_in
        if self.tokens_out is not None:
            result["tokens_out"] = self.tokens_out
        if self.success is not None:
            result["success"] = self.success
        if self.error is not None:
            result["error"] = self.error
        if self.metadata:
            result["metadata"] = self.metadata
        return result

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())


@dataclass
class AgentInput:
    """
    Standardized Input Schema for Agent tasks

    Provides a consistent interface for all agent inputs.
    """
    task_id: str
    prompt: str
    task_type: str = "general"
    risk_level: str = "medium"
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentInput":
        """Create from dictionary"""
        return cls(**data)


@dataclass
class AgentOutput:
    """
    Standardized Output Schema for Agent tasks

    Provides a consistent interface for all agent outputs.
    """
    task_id: str
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    latency_ms: float = 0.0
    model_used: Optional[str] = None
    provider_used: Optional[str] = None
    tokens_in: Optional[int] = None
    tokens_out: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {
            "task_id": self.task_id,
            "success": self.success,
            "data": self.data,
            "latency_ms": self.latency_ms,
        }
        if self.error is not None:
            result["error"] = self.error
        if self.model_used is not None:
            result["model_used"] = self.model_used
        if self.provider_used is not None:
            result["provider_used"] = self.provider_used
        if self.tokens_in is not None:
            result["tokens_in"] = self.tokens_in
        if self.tokens_out is not None:
            result["tokens_out"] = self.tokens_out
        if self.metadata:
            result["metadata"] = self.metadata
        return result


class BaseAgent(ABC):
    """
    Base Agent Class with Dynamic Routing and Telemetry v2

    EPIC #2594 - Ticket 3: Agent Base Class Upgrade (AIP v2)

    This class provides:
    - Dynamic model selection via RoutingEngine.select_model()
    - Telemetry v2 JSON format logging
    - Standardized Input/Output schemas

    Usage:
        class MyAgent(BaseAgent):
            def __init__(self):
                super().__init__(agent_id="my_agent")

            async def execute(self, input: AgentInput) -> AgentOutput:
                response = await self.call_llm(
                    prompt=input.prompt,
                    task_type=input.task_type,
                    risk_level=input.risk_level
                )
                return AgentOutput(
                    task_id=input.task_id,
                    success=True,
                    data={"response": response}
                )
    """

    def __init__(self, agent_id: str):
        """
        Initialize BaseAgent

        Args:
            agent_id: Unique identifier for this agent (e.g., "dev_agent", "pm_agent")
        """
        self.agent_id = agent_id
        self._routing_engine = None
        self._llm_client = None
        self._telemetry_enabled = True

        logger.info(
            f"[BaseAgent] Initialized agent_id={agent_id}",
            extra={"agent_id": agent_id}
        )

    def _get_routing_engine(self):
        """Get or create RoutingEngine instance"""
        if self._routing_engine is None:
            try:
                from core.routing import RoutingEngine
                from llm.client import _get_available_providers

                available_providers = _get_available_providers()
                self._routing_engine = RoutingEngine(
                    available_providers=available_providers
                )
                logger.info(
                    f"[BaseAgent] RoutingEngine initialized with providers: {available_providers}",
                    extra={"agent_id": self.agent_id, "providers": available_providers}
                )
            except ImportError as e:
                logger.warning(
                    f"[BaseAgent] RoutingEngine not available: {e}",
                    extra={"agent_id": self.agent_id}
                )
        return self._routing_engine

    def _get_llm_client(self, provider: str, model: str):
        """Get LLMClient instance for specified provider and model"""
        try:
            from llm.client import LLMClient
            return LLMClient(provider=provider, model=model)
        except ImportError as e:
            logger.error(
                f"[BaseAgent] LLMClient not available: {e}",
                extra={"agent_id": self.agent_id}
            )
            raise

    def _emit_telemetry(self, event: TelemetryEvent):
        """
        Emit a Telemetry v2 event

        Logs the event in JSON format for structured logging.
        """
        if not self._telemetry_enabled:
            return

        logger.info(
            f"[Telemetry] {event.event_type.value}",
            extra={
                "telemetry_v2": True,
                "event": event.to_dict()
            }
        )

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        return datetime.now(timezone.utc).isoformat()

    def call_llm(
        self,
        prompt: str,
        task_type: str,
        risk_level: str = "medium",
        context_size: Optional[int] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        json_mode: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Call LLM with dynamic routing based on task type and risk level

        This method replaces the old pattern of directly specifying a model:
        - Old: llm_client.chat(model="gpt-4o", messages=[...])
        - New: self.call_llm(prompt, task_type="coding", risk_level="medium")

        Args:
            prompt: User prompt/message
            task_type: Type of task (planning, coding, review, ux_copy, etc.)
            risk_level: Risk level (high, medium, low)
            context_size: Estimated context size in tokens (auto-calculated if None)
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            json_mode: If True, request JSON-formatted response
            **kwargs: Additional provider-specific parameters

        Returns:
            Dict containing:
            - content: Generated text content
            - model: Model used
            - provider: Provider used
            - tokens_in: Input token count
            - tokens_out: Output token count
            - latency_ms: Call latency in milliseconds
        """
        start_time = time.time()

        # Calculate context size if not provided
        if context_size is None:
            context_size = len(prompt) // 4  # Rough estimate: 4 chars per token

        # Get routing engine and select model
        routing_engine = self._get_routing_engine()

        if routing_engine:
            try:
                from core.routing import TaskType, RiskLevel

                # Convert string task_type to TaskType enum
                task_type_enum = TaskType(task_type.lower())
                risk_level_enum = RiskLevel(risk_level.lower())

                model_info = routing_engine.select_model(
                    task_type=task_type_enum,
                    risk_level=risk_level_enum,
                    context_size=context_size
                )

                provider = model_info.provider
                model = model_info.model_name

                logger.info(
                    f"[BaseAgent] Routing selected: provider={provider}, model={model}, "
                    f"tier={model_info.tier.value}, is_fallback={model_info.is_fallback}",
                    extra={
                        "agent_id": self.agent_id,
                        "task_type": task_type,
                        "risk_level": risk_level,
                        "provider": provider,
                        "model": model,
                        "tier": model_info.tier.value,
                        "is_fallback": model_info.is_fallback
                    }
                )
            except (ValueError, ImportError) as e:
                logger.warning(
                    f"[BaseAgent] Routing failed: {e}, using auto provider",
                    extra={"agent_id": self.agent_id}
                )
                provider = "auto"
                model = None
        else:
            provider = "auto"
            model = None

        # Get LLM client and make the call
        try:
            client = self._get_llm_client(provider=provider, model=model)
            response = client.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                json_mode=json_mode,
                **kwargs
            )

            latency_ms = (time.time() - start_time) * 1000

            # Extract token counts from response
            tokens_in = getattr(response, 'prompt_tokens', None)
            tokens_out = getattr(response, 'completion_tokens', None)

            # Emit telemetry event
            self._emit_telemetry(TelemetryEvent(
                event_type=TelemetryEventType.MODEL_CALL,
                timestamp=self._get_timestamp(),
                agent_id=self.agent_id,
                task_type=task_type,
                model_selected=client.model,
                provider=client.provider_name,
                latency_ms=latency_ms,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                success=True
            ))

            return {
                "content": response.content,
                "model": client.model,
                "provider": client.provider_name,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "latency_ms": latency_ms
            }

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000

            # Emit error telemetry
            self._emit_telemetry(TelemetryEvent(
                event_type=TelemetryEventType.MODEL_CALL,
                timestamp=self._get_timestamp(),
                agent_id=self.agent_id,
                task_type=task_type,
                model_selected=model,
                provider=provider,
                latency_ms=latency_ms,
                success=False,
                error=str(e)
            ))

            logger.error(
                f"[BaseAgent] LLM call failed: {e}",
                extra={
                    "agent_id": self.agent_id,
                    "task_type": task_type,
                    "provider": provider,
                    "model": model
                }
            )
            raise

    @abstractmethod
    def execute(self, input: AgentInput) -> AgentOutput:
        """
        Execute the agent's main task

        Subclasses must implement this method to define their behavior.

        Args:
            input: AgentInput with task details

        Returns:
            AgentOutput with results
        """
        pass

    def run(self, input: AgentInput) -> AgentOutput:
        """
        Run the agent with telemetry tracking

        This method wraps execute() with telemetry events for
        agent start/end tracking.

        Args:
            input: AgentInput with task details

        Returns:
            AgentOutput with results
        """
        start_time = time.time()

        # Emit agent start event
        self._emit_telemetry(TelemetryEvent(
            event_type=TelemetryEventType.AGENT_START,
            timestamp=self._get_timestamp(),
            agent_id=self.agent_id,
            task_type=input.task_type,
            metadata={"task_id": input.task_id}
        ))

        try:
            output = self.execute(input)
            latency_ms = (time.time() - start_time) * 1000
            output.latency_ms = latency_ms

            # Emit agent end event
            self._emit_telemetry(TelemetryEvent(
                event_type=TelemetryEventType.AGENT_END,
                timestamp=self._get_timestamp(),
                agent_id=self.agent_id,
                task_type=input.task_type,
                latency_ms=latency_ms,
                success=output.success,
                metadata={"task_id": input.task_id}
            ))

            return output

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000

            # Emit error event
            self._emit_telemetry(TelemetryEvent(
                event_type=TelemetryEventType.ERROR,
                timestamp=self._get_timestamp(),
                agent_id=self.agent_id,
                task_type=input.task_type,
                latency_ms=latency_ms,
                success=False,
                error=str(e),
                metadata={"task_id": input.task_id}
            ))

            return AgentOutput(
                task_id=input.task_id,
                success=False,
                error=str(e),
                latency_ms=latency_ms
            )
