"""
Flow Controller v3 - Hybrid Router (C-2)

Issue #2745: C-2 Router Node Logic
EPIC C: Flow Controller v3 - LLM-driven Dynamic Routing
Stage 1: Hybrid Router Implementation

This module implements the HybridRoutingPolicy which:
- Fast Path: Deterministic routing for clear-cut cases (approve -> publisher)
- Slow Path: LLM-driven routing for ambiguous cases (request_changes -> fixer vs executor)

Strategy: "Rules as Guardrails, AI as Driver"
- Deterministic rules handle obvious cases without LLM cost/latency
- LLM provides judgment for cases requiring analysis

Node Name Mapping:
- CTO terminology -> Actual graph node IDs
- publisher_node -> publisher
- fixer_node -> fixer
- coder_node -> executor
- human_fallback -> decision (with requires_hitl_approval=True)

Event Codes (greppable):
- [ROUTER_FAST_PATH] - Deterministic routing (approve/blocked/unknown/low severity)
- [ROUTER_SLOW_PATH] - LLM-driven routing (request_changes with medium+ severity)
- [ROUTER_HITL] - Human-in-the-loop required (blocked/unknown verdict)
- [ROUTER_LLM_FALLBACK] - LLM failed, using deterministic fallback

Usage:
    from core.flow.hybrid_router import HybridRoutingPolicy, get_hybrid_router

    policy = get_hybrid_router()
    decision = policy.route(
        verdict="request_changes",
        severity="medium",
        summary="Variable naming issues",
        blocker_count=0
    )
"""
import logging
from typing import Optional, Dict, Callable, FrozenSet

from .schema import (
    RoutingContext,
    RoutingDecision,
)

logger = logging.getLogger(__name__)


NODE_ALIASES: Dict[str, str] = {
    "publisher_node": "publisher",
    "fixer_node": "fixer",
    "coder_node": "executor",
    "human_fallback": "decision",
}

CANONICAL_NODES: FrozenSet[str] = frozenset({
    "publisher",
    "fixer",
    "executor",
    "decision",
    "finalizer",
    "reviewer",
    "planner",
    "ci_monitor",
})

SEVERITY_ORDER: Dict[str, int] = {
    "low": 0,
    "medium": 1,
    "high": 2,
    "critical": 3,
}


def canonicalize_node_name(name: str) -> str:
    """Convert alias or raw node name to canonical graph node ID.

    Args:
        name: Node name (may be alias like 'coder_node' or canonical like 'executor')

    Returns:
        Canonical graph node ID

    Raises:
        ValueError: If name cannot be mapped to a known node
    """
    normalized = name.strip().lower()

    if normalized in NODE_ALIASES:
        return NODE_ALIASES[normalized]

    if normalized in CANONICAL_NODES:
        return normalized

    raise ValueError(
        f"Unknown node name '{name}'. "
        f"Valid aliases: {list(NODE_ALIASES.keys())}, "
        f"Valid nodes: {list(CANONICAL_NODES)}"
    )


def severity_gte(severity: str, threshold: str) -> bool:
    """Check if severity is greater than or equal to threshold.

    Args:
        severity: Severity level to check (low/medium/high/critical)
        threshold: Threshold to compare against

    Returns:
        True if severity >= threshold
    """
    sev_val = SEVERITY_ORDER.get(severity.lower(), 0)
    thresh_val = SEVERITY_ORDER.get(threshold.lower(), 0)
    return sev_val >= thresh_val


class HybridRoutingPolicy:
    """Hybrid Router: Rules as Guardrails, AI as Driver.

    This class implements the C-2 routing logic:
    - Fast Path (deterministic): approve -> publisher, blocked/unknown -> decision+HITL
    - Slow Path (LLM): request_changes -> LLM decides fixer vs executor

    CTO Directive: Application Layer (Router) should not know specific model strings.
    Model selection is delegated to RoutingEngine via get_client_for_task(TaskType.ROUTING).

    Attributes:
        llm_generate_fn: Function to call LLM for slow path decisions
    """

    def __init__(
        self,
        llm_generate_fn: Optional[Callable[[str], str]] = None
    ):
        """Initialize HybridRoutingPolicy.

        Args:
            llm_generate_fn: Function that takes a prompt and returns LLM response.
                            If None, slow path will fall back to deterministic.
        """
        self.llm_generate_fn = llm_generate_fn

    def route(
        self,
        verdict: str,
        severity: str,
        summary: str,
        blocker_count: int = 0,
        context: Optional[RoutingContext] = None
    ) -> RoutingDecision:
        """Route based on ReviewOutcome fields.

        Routing Rules:
        1. approve -> publisher (Fast Path)
        2. blocked/unknown -> decision + HITL (Fast Path)
        3. request_changes + low severity -> fixer (Fast Path)
        4. request_changes + medium+ severity -> LLM decides fixer vs executor (Slow Path)
        5. comment -> fixer (Fast Path, treat as minor suggestions)

        Args:
            verdict: Review verdict (approve/request_changes/comment/blocked/unknown)
            severity: Review severity (low/medium/high/critical)
            summary: Review summary for LLM context
            blocker_count: Number of blocking issues
            context: Optional routing context for additional info

        Returns:
            RoutingDecision with next_node and reasoning
        """
        verdict_lower = verdict.lower()
        severity_lower = severity.lower()

        if verdict_lower == "approve":
            return self._fast_path_approve()

        if verdict_lower in ("blocked", "unknown"):
            return self._fast_path_hitl(verdict_lower)

        if verdict_lower == "request_changes":
            if severity_gte(severity_lower, "medium"):
                return self._slow_path_request_changes(
                    severity_lower, summary, blocker_count
                )
            else:
                return self._fast_path_fixer(severity_lower)

        if verdict_lower == "comment":
            return self._fast_path_fixer_comment()

        logger.warning(f"[HybridRouter] Unknown verdict '{verdict}', defaulting to HITL")
        return self._fast_path_hitl(verdict_lower)

    def _fast_path_approve(self) -> RoutingDecision:
        """Fast path: approve -> publisher."""
        logger.info("[ROUTER_FAST_PATH] approve -> publisher")
        return RoutingDecision(
            next_node="publisher",
            reasoning="Review approved, proceeding to publish",
            risk_assessment="Low - review passed without issues",
            requires_hitl_approval=False
        )

    def _fast_path_hitl(self, verdict: str) -> RoutingDecision:
        """Fast path: blocked/unknown -> decision with HITL."""
        logger.info(f"[ROUTER_FAST_PATH] {verdict} -> decision")
        logger.info(f"[ROUTER_HITL] requires_hitl_approval=True for verdict={verdict}")
        return RoutingDecision(
            next_node="decision",
            reasoning=f"Verdict '{verdict}' requires human review",
            risk_assessment="High - requires human-in-the-loop approval",
            requires_hitl_approval=True
        )

    def _fast_path_fixer(self, severity: str) -> RoutingDecision:
        """Fast path: request_changes with low severity -> fixer."""
        logger.info(f"[ROUTER_FAST_PATH] request_changes (severity={severity}) -> fixer")
        return RoutingDecision(
            next_node="fixer",
            reasoning=f"Low severity ({severity}) issues can be auto-fixed",
            risk_assessment="Low - minor issues suitable for auto-fix",
            requires_hitl_approval=False
        )

    def _fast_path_fixer_comment(self) -> RoutingDecision:
        """Fast path: comment verdict -> fixer (treat as suggestions)."""
        logger.info("[ROUTER_FAST_PATH] comment -> fixer")
        return RoutingDecision(
            next_node="fixer",
            reasoning="Comment suggestions can be addressed by fixer",
            risk_assessment="Low - suggestions only, no blocking issues",
            requires_hitl_approval=False
        )

    def _slow_path_request_changes(
        self,
        severity: str,
        summary: str,
        blocker_count: int
    ) -> RoutingDecision:
        """Slow path: LLM decides between fixer and executor.

        For request_changes with medium+ severity, we need LLM judgment
        to determine if issues can be auto-fixed or require re-generation.

        Args:
            severity: Review severity
            summary: Review summary
            blocker_count: Number of blocking issues

        Returns:
            RoutingDecision from LLM or deterministic fallback
        """
        logger.info(
            f"[ROUTER_SLOW_PATH] request_changes (severity={severity}, "
            f"blockers={blocker_count}) -> LLM decision"
        )

        if self.llm_generate_fn is None:
            logger.info("[ROUTER_LLM_FALLBACK] No LLM configured, using deterministic fallback")
            return self._deterministic_fallback(severity, blocker_count)

        try:
            prompt = self._build_slow_path_prompt(severity, summary, blocker_count)
            response = self.llm_generate_fn(prompt)
            return self._parse_llm_response(response, severity, blocker_count)

        except Exception as e:
            logger.warning(f"[ROUTER_LLM_FALLBACK] LLM call failed: {e}, using fallback")
            return self._deterministic_fallback(severity, blocker_count)

    def _build_slow_path_prompt(
        self,
        severity: str,
        summary: str,
        blocker_count: int
    ) -> str:
        """Build prompt for LLM slow path decision.

        Args:
            severity: Review severity
            summary: Review summary
            blocker_count: Number of blocking issues

        Returns:
            Formatted prompt string
        """
        return f"""You are a Senior Technical Program Manager deciding the next step for a code review.

Review Context:
- Verdict: request_changes
- Severity: {severity}
- Blocker Count: {blocker_count}
- Summary: {summary}

Decision Options:
1. "fixer" - Auto-fix minor issues (naming, formatting, small logic fixes)
2. "executor" - Re-generate code (architectural issues, major refactoring needed)

Rules:
- Choose "fixer" if issues are localized and can be patched
- Choose "executor" if issues require significant restructuring or re-thinking

You MUST respond with ONLY a JSON object:
{{"next_node": "fixer" or "executor", "reasoning": "brief explanation"}}

Your response (JSON only):"""

    def _parse_llm_response(
        self,
        response: str,
        severity: str,
        blocker_count: int
    ) -> RoutingDecision:
        """Parse LLM response and create RoutingDecision.

        Args:
            response: Raw LLM response (expected JSON)
            severity: Review severity for fallback
            blocker_count: Blocker count for fallback

        Returns:
            RoutingDecision from parsed response or fallback
        """
        import json
        import re

        try:
            json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL)
            if json_match:
                response_clean = json_match.group(1)
            else:
                response_clean = response.strip()

            data = json.loads(response_clean)
            raw_node = data.get("next_node", "")
            reasoning = data.get("reasoning", "LLM decision")

            try:
                next_node = canonicalize_node_name(raw_node)
            except ValueError:
                logger.warning(
                    f"[HybridRouter] LLM returned invalid node '{raw_node}', "
                    f"using fallback"
                )
                return self._deterministic_fallback(severity, blocker_count)

            if next_node not in ("fixer", "executor"):
                logger.warning(
                    f"[HybridRouter] LLM returned unexpected node '{next_node}', "
                    f"constraining to fixer/executor"
                )
                next_node = "fixer" if severity == "medium" else "executor"

            logger.info(
                f"[HybridRouter] Slow path: LLM decided -> {next_node} "
                f"(reasoning: {reasoning[:50]}...)"
            )

            return RoutingDecision(
                next_node=next_node,
                reasoning=f"LLM decision: {reasoning}",
                risk_assessment=f"Medium - LLM-driven decision for {severity} severity",
                requires_hitl_approval=False
            )

        except json.JSONDecodeError as e:
            logger.warning(f"[HybridRouter] Failed to parse LLM JSON: {e}")
            return self._deterministic_fallback(severity, blocker_count)

    def _deterministic_fallback(
        self,
        severity: str,
        blocker_count: int
    ) -> RoutingDecision:
        """Deterministic fallback when LLM is unavailable or fails.

        Logic:
        - medium severity with 0 blockers -> fixer
        - high/critical severity or blockers -> executor

        Args:
            severity: Review severity
            blocker_count: Number of blocking issues

        Returns:
            RoutingDecision based on deterministic rules
        """
        if severity == "medium" and blocker_count == 0:
            next_node = "fixer"
            reasoning = "Medium severity with no blockers, attempting auto-fix"
        else:
            next_node = "executor"
            reasoning = f"High severity ({severity}) or blockers ({blocker_count}), requires re-generation"

        logger.info(f"[HybridRouter] Deterministic fallback: {next_node}")

        return RoutingDecision(
            next_node=next_node,
            reasoning=f"Deterministic fallback: {reasoning}",
            risk_assessment="Medium - rule-based decision without LLM",
            requires_hitl_approval=False
        )


def create_llm_generate_fn(
    timeout: int = 30
) -> Callable[[str], str]:
    """Create an LLM generate function for the HybridRouter.

    CTO Directive: Application Layer (Router) should not know specific model strings.
    Model selection is delegated to RoutingEngine via get_client_for_task(TaskType.ROUTING).

    The RoutingEngine will:
    - Select Tier 1 model by default (qwen-plus on AliCloud, or Qwen2.5-32B on SiliconFlow)
    - Handle cross-generation fallback automatically
    - Consider provider availability and cost

    Args:
        timeout: Request timeout in seconds

    Returns:
        Function that takes a prompt and returns LLM response
    """
    from llm.client import get_client_for_task
    from core.routing import TaskType

    client = get_client_for_task(TaskType.ROUTING, risk_level="medium")

    def generate(prompt: str) -> str:
        response = client.generate(
            prompt=prompt,
            temperature=0.3,
            max_tokens=200,
            json_mode=True,
            timeout=timeout
        )
        return response.content

    return generate


def get_hybrid_router(
    llm_generate_fn: Optional[Callable[[str], str]] = None,
    use_llm: bool = True
) -> HybridRoutingPolicy:
    """Factory function to create a HybridRoutingPolicy.

    CTO Directive: Application Layer (Router) should not know specific model strings.
    Model selection is delegated to RoutingEngine via get_client_for_task(TaskType.ROUTING).

    Args:
        llm_generate_fn: Optional custom LLM function. If None and use_llm=True,
                        creates one using get_client_for_task(TaskType.ROUTING).
        use_llm: Whether to enable LLM for slow path. If False, uses deterministic only.

    Returns:
        Configured HybridRoutingPolicy instance
    """
    if llm_generate_fn is not None:
        return HybridRoutingPolicy(llm_generate_fn=llm_generate_fn)

    if use_llm:
        try:
            fn = create_llm_generate_fn()
            return HybridRoutingPolicy(llm_generate_fn=fn)
        except Exception as e:
            logger.warning(
                f"[ROUTER_LLM_FALLBACK] Failed to create LLM function: {e}, "
                f"using deterministic-only mode"
            )
            return HybridRoutingPolicy(llm_generate_fn=None)

    return HybridRoutingPolicy(llm_generate_fn=None)
