"""
Flow Controller v3 - Router Node Interface (C-2)

Issue #2745: C-2 Router Node interface + Decision Validator
EPIC C: Flow Controller v3 - LLM-driven Dynamic Routing
Stage 0: Foundations

This module implements the RouterNode class which:
- Calls LLM to make routing decisions
- Validates decisions against candidate whitelist
- Falls back to deterministic routing on any failure

Fail-safe Mechanisms:
1. Validation: next_node must be in candidates list
2. Guardrails: timeout/JSON error/empty output -> fallback
3. Rollback: Any failure -> deterministic rule-based routing

Usage:
    from core.flow import RouterNode, RoutingContext, RoutingCandidate

    def fallback_fn(context: RoutingContext) -> RoutingDecision:
        # Deterministic rule-based routing
        return RoutingDecision(
            next_node="finalizer",
            reasoning="Fallback: default to finalizer",
            risk_assessment="Low - deterministic fallback"
        )

    router = RouterNode(llm_client=my_llm, fallback_fn=fallback_fn)
    decision = router.route(context)
"""
import json
import logging
import time
from json import JSONDecodeError
from typing import Callable, Optional, Protocol

from pydantic import ValidationError

from .schema import (
    InvalidNextNodeError,
    RoutingContext,
    RoutingDecision,
    validate_decision,
)

logger = logging.getLogger(__name__)


class LLMClient(Protocol):
    """Protocol for LLM client interface.

    Any LLM client that implements this protocol can be used with RouterNode.
    """

    def generate(
        self,
        prompt: str,
        timeout_seconds: Optional[float] = None
    ) -> str:
        """Generate a response from the LLM.

        Args:
            prompt: The prompt to send to the LLM
            timeout_seconds: Optional timeout in seconds

        Returns:
            The LLM's response as a string (expected to be JSON)

        Raises:
            TimeoutError: If the LLM call times out
            Exception: For any other LLM errors
        """
        ...


class FallbackReason:
    """Constants for fallback reasons (for metrics)."""

    TIMEOUT = "timeout"
    JSON_PARSE_ERROR = "json_parse_error"
    VALIDATION_ERROR = "validation_error"
    INVALID_NEXT_NODE = "invalid_next_node"
    EMPTY_OUTPUT = "empty_output"
    LLM_ERROR = "llm_error"
    UNKNOWN = "unknown"


class RouterNode:
    """LLM-driven Flow Router with fail-safe mechanisms.

    This class implements the core routing logic for Flow Controller v3.
    It calls an LLM to make routing decisions, validates the output,
    and falls back to deterministic routing on any failure.

    Attributes:
        llm_client: LLM client implementing the LLMClient protocol
        fallback_fn: Function to call when LLM routing fails
        max_retries: Maximum number of LLM call retries (default: 2)
        timeout_seconds: Timeout for LLM calls in seconds (default: 10)
    """

    def __init__(
        self,
        llm_client: LLMClient,
        fallback_fn: Callable[[RoutingContext], RoutingDecision],
        max_retries: int = 2,
        timeout_seconds: float = 10.0
    ):
        """Initialize RouterNode.

        Args:
            llm_client: LLM client for making routing decisions
            fallback_fn: Fallback function for deterministic routing
            max_retries: Maximum retries for LLM calls (default: 2)
            timeout_seconds: Timeout for LLM calls (default: 10.0)
        """
        self.llm_client = llm_client
        self.fallback_fn = fallback_fn
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds

    def route(
        self,
        context: RoutingContext,
        metrics_callback: Optional[Callable[[dict], None]] = None
    ) -> RoutingDecision:
        """Determine the next node based on context.

        This method attempts to use the LLM to make a routing decision.
        If the LLM fails for any reason, it falls back to deterministic routing.

        Args:
            context: The routing context with candidates
            metrics_callback: Optional callback for recording metrics

        Returns:
            RoutingDecision with the selected next node

        Note:
            This method never raises exceptions - it always returns a decision.
            On any failure, it returns the fallback decision.
        """
        start_time = time.time()
        fallback_reason: Optional[str] = None
        success = False

        try:
            decision = self._call_llm_with_retry(context)
            validate_decision(decision, context)
            success = True
            return decision

        except TimeoutError as e:
            fallback_reason = FallbackReason.TIMEOUT
            logger.warning(
                f"[Router] Timeout after {self.timeout_seconds}s, using fallback: {e}"
            )

        except JSONDecodeError as e:
            fallback_reason = FallbackReason.JSON_PARSE_ERROR
            logger.warning(
                f"[Router] JSON parse error, using fallback: {e}"
            )

        except ValidationError as e:
            fallback_reason = FallbackReason.VALIDATION_ERROR
            logger.warning(
                f"[Router] Pydantic validation error, using fallback: {e}"
            )

        except InvalidNextNodeError as e:
            fallback_reason = FallbackReason.INVALID_NEXT_NODE
            logger.warning(
                f"[Router] Invalid next_node '{e.next_node}', "
                f"valid nodes: {e.valid_nodes}, using fallback"
            )

        except Exception as e:
            fallback_reason = FallbackReason.UNKNOWN
            logger.warning(
                f"[Router] Unexpected error, using fallback: {type(e).__name__}: {e}"
            )

        finally:
            latency_ms = (time.time() - start_time) * 1000
            if metrics_callback:
                try:
                    metrics_callback({
                        "latency_ms": latency_ms,
                        "success": success,
                        "fallback_reason": fallback_reason,
                    })
                except Exception as e:
                    logger.debug(f"[Router] Metrics callback error: {e}")

        # Fallback to deterministic routing
        return self._fallback(context, fallback_reason)

    def _call_llm_with_retry(self, context: RoutingContext) -> RoutingDecision:
        """Call LLM with retry logic.

        Args:
            context: The routing context

        Returns:
            Parsed RoutingDecision from LLM

        Raises:
            TimeoutError: If all retries timeout
            JSONDecodeError: If LLM output is not valid JSON
            ValidationError: If JSON doesn't match RoutingDecision schema
            Exception: For any other LLM errors
        """
        last_error: Optional[Exception] = None
        prompt = self._build_prompt(context)

        for attempt in range(self.max_retries + 1):
            try:
                response = self.llm_client.generate(
                    prompt=prompt,
                    timeout_seconds=self.timeout_seconds
                )

                if not response or not response.strip():
                    raise ValueError("Empty LLM response")

                decision_dict = json.loads(response)
                return RoutingDecision(**decision_dict)

            except (TimeoutError, JSONDecodeError, ValidationError) as e:
                last_error = e
                if attempt < self.max_retries:
                    logger.debug(
                        f"[Router] Attempt {attempt + 1} failed: {e}, retrying..."
                    )
                    continue
                raise

            except Exception as e:
                last_error = e
                if attempt < self.max_retries:
                    logger.debug(
                        f"[Router] Attempt {attempt + 1} failed: {e}, retrying..."
                    )
                    continue
                raise

        # Should not reach here, but just in case
        if last_error:
            raise last_error
        raise RuntimeError("Unexpected state in _call_llm_with_retry")

    def _build_prompt(self, context: RoutingContext) -> str:
        """Build the prompt for the LLM.

        Args:
            context: The routing context

        Returns:
            Formatted prompt string
        """
        candidates_str = "\n".join(
            f"- {c.node_name}: {c.description}"
            for c in context.candidates
        )

        history_str = " -> ".join(context.step_history) if context.step_history else "None"

        # Include ReviewOutcome context if available
        review_context = ""
        if context.review_verdict:
            review_context = f"""
Review Outcome:
- Verdict: {context.review_verdict}
- Severity: {context.review_severity or 'N/A'}
- Blocker Count: {context.blocker_count or 0}
"""

        prompt = f"""You are a workflow router. Based on the context below, decide which node to route to next.

Task Type: {context.task_type}
Current Stage: {context.current_stage}
Step History: {history_str}
Last Agent Feedback: {context.last_agent_feedback or 'None'}
{review_context}
Available Candidates:
{candidates_str}

Respond with a JSON object containing:
- next_node: The node_name to route to (must be one of the candidates)
- reasoning: Brief explanation of your choice
- risk_assessment: Brief risk assessment of this routing decision

Example response:
{{"next_node": "fixer", "reasoning": "Code issues need fixing before deployment", "risk_assessment": "Low risk - standard code fix"}}

Your response (JSON only):"""

        return prompt

    def _fallback(
        self,
        context: RoutingContext,
        reason: Optional[str] = None
    ) -> RoutingDecision:
        """Execute fallback to deterministic routing.

        Args:
            context: The routing context
            reason: Optional reason for fallback (for logging)

        Returns:
            RoutingDecision from the fallback function
        """
        try:
            decision = self.fallback_fn(context)
            logger.info(
                f"[Router] Fallback decision: {decision.next_node} "
                f"(reason: {reason or 'unknown'})"
            )
            return decision

        except Exception as e:
            # Last resort: return first candidate
            logger.error(
                f"[Router] Fallback function failed: {e}, "
                f"using first candidate as last resort"
            )
            first_candidate = context.candidates[0]
            return RoutingDecision(
                next_node=first_candidate.node_name,
                reasoning=f"Last resort fallback: {e}",
                risk_assessment="High - fallback function failed"
            )


class DeterministicRouter:
    """Deterministic rule-based router for fallback.

    This class provides a simple rule-based routing implementation
    that can be used as the fallback_fn for RouterNode.
    """

    def __init__(self, rules: Optional[dict] = None):
        """Initialize with optional routing rules.

        Args:
            rules: Dict mapping (task_type, current_stage) to next_node
        """
        self.rules = rules or {}

    def route(self, context: RoutingContext) -> RoutingDecision:
        """Make a deterministic routing decision.

        Args:
            context: The routing context

        Returns:
            RoutingDecision based on rules or first candidate
        """
        key = (context.task_type, context.current_stage)

        if key in self.rules:
            next_node = self.rules[key]
            if context.is_valid_next_node(next_node):
                return RoutingDecision(
                    next_node=next_node,
                    reasoning=f"Deterministic rule: {key} -> {next_node}",
                    risk_assessment="Low - deterministic routing"
                )

        # Default: return first candidate
        first_candidate = context.candidates[0]
        return RoutingDecision(
            next_node=first_candidate.node_name,
            reasoning="Default: first candidate (no matching rule)",
            risk_assessment="Low - deterministic fallback"
        )
