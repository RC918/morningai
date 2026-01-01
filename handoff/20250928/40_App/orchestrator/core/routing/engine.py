"""
Routing Engine for Multi-Model LLM Selection

Implements the routing policy for selecting appropriate LLM models
based on task type, risk level, and context size.

EPIC #2594 - Ticket 2: Routing Policy v1.1

Reference: "Routing Policy for Multi-Model Use in MorningAI"
"""
import copy
import json
import logging
from dataclasses import dataclass
from enum import Enum, StrEnum
from pathlib import Path
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class Tier(Enum):
    """
    Model capability tiers for routing decisions

    Tier 0: Highest capability - Complex reasoning, planning, critical decisions
    Tier 1: High capability - Code generation, detailed analysis
    Tier 2: Medium capability - Standard tasks, reviews
    Tier 3: Basic capability - Simple tasks, UX copy, translations
    """
    TIER_0 = 0
    TIER_1 = 1
    TIER_2 = 2
    TIER_3 = 3


class TaskType(Enum):
    """
    Task types for routing decisions

    Each task type maps to a default tier and fallback tier
    """
    PLANNING = "planning"
    CODING = "coding"
    REVIEW = "review"
    ROUTING = "routing"
    UX_COPY = "ux_copy"
    TRANSLATION = "translation"
    SUMMARIZATION = "summarization"
    ANALYSIS = "analysis"
    CHAT = "chat"


class RiskLevel(StrEnum):
    """
    Risk levels for routing decisions

    Risk level affects tier selection:
    - HIGH: Prefer higher capability (lower tier number)
    - MEDIUM: Use default tier
    - LOW: Can use lower capability (higher tier number)
    """
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ModelInfo:
    """
    Information about a selected model

    Attributes:
        model_name: Full model identifier (e.g., "qwen-max", "gpt-4o")
        provider: Provider name (e.g., "alicloud", "openai")
        tier: Capability tier of the model
        is_fallback: Whether this is a fallback selection
        reason: Reason for selection (for logging/debugging)
    """
    model_name: str
    provider: str
    tier: Tier
    is_fallback: bool = False
    reason: str = ""


# Default model mappings per tier
# Format: {tier: [(provider, model_name), ...]}
# Cross-Generation Fallback: Tier 0/1 use AliCloud (Qwen3) as primary,
# SiliconFlow (Qwen2.5) as degraded backup - no OpenAI/Gemini in fallback path
DEFAULT_TIER_MODELS: Dict[Tier, List[tuple]] = {
    Tier.TIER_0: [
        ("alicloud", "qwen-max"),
        ("siliconflow", "Qwen/Qwen2.5-72B-Instruct"),  # Cross-gen fallback
    ],
    Tier.TIER_1: [
        ("alicloud", "qwen-plus"),
        ("siliconflow", "Qwen/Qwen2.5-32B-Instruct"),  # Cross-gen fallback
    ],
    Tier.TIER_2: [
        ("alicloud", "qwen-turbo"),
        ("siliconflow", "Qwen/Qwen2.5-32B-Instruct"),
    ],
    Tier.TIER_3: [
        ("siliconflow", "Qwen/Qwen2.5-14B-Instruct"),
        ("siliconflow", "Qwen/Qwen2.5-7B-Instruct"),
    ],
}

# Issue #2874: Provider cost multipliers for best candidate selection
# Lower values = more cost-effective (preferred when cost_weight > 0)
# Values are relative cost per 1K tokens (normalized)
DEFAULT_PROVIDER_COSTS: Dict[str, float] = {
    "alicloud": 0.5,      # Most cost-effective
    "siliconflow": 0.6,   # Very cost-effective
    "gemini": 0.8,        # Moderate cost
    "openai": 1.0,        # Baseline cost
}

# Issue #2874: Provider preference scores (higher = more preferred)
# Used when multiple providers have similar costs
DEFAULT_PROVIDER_PREFERENCES: Dict[str, float] = {
    "alicloud": 1.0,      # Primary provider
    "siliconflow": 0.9,   # Secondary provider
    "gemini": 0.8,        # Tertiary provider
    "openai": 0.7,        # Fallback provider
}

# Default task type to tier mappings
DEFAULT_TASK_ROUTING: Dict[str, Dict[str, int]] = {
    "planning": {"tier": 0, "fallback": 1},
    "coding": {"tier": 1, "fallback": 2},
    "review": {"tier": 1, "fallback": 2},
    "routing": {"tier": 1, "fallback": 2},
    "ux_copy": {"tier": 3, "fallback": 2},
    "translation": {"tier": 2, "fallback": 3},
    "summarization": {"tier": 2, "fallback": 3},
    "analysis": {"tier": 1, "fallback": 2},
    "chat": {"tier": 2, "fallback": 3},
}

# Context size limits per tier (in tokens)
# Models in lower tiers may have smaller context windows
TIER_CONTEXT_LIMITS: Dict[Tier, int] = {
    Tier.TIER_0: 128000,  # qwen-max, gpt-4o support large contexts
    Tier.TIER_1: 128000,  # qwen-plus, gpt-4o-mini
    Tier.TIER_2: 32000,   # qwen-turbo, smaller models
    Tier.TIER_3: 8000,    # smaller instruction models
}


class RoutingEngine:
    """
    Engine for selecting appropriate LLM models based on task requirements

    The routing engine considers:
    1. Task type (planning, coding, review, etc.)
    2. Risk level (high, medium, low)
    3. Context size (token count)
    4. Provider availability

    Usage:
        engine = RoutingEngine()
        model_info = engine.select_model(
            task_type=TaskType.PLANNING,
            risk_level="high",
            context_size=1000
        )
    """

    def __init__(
        self,
        policy_path: Optional[Path] = None,
        available_providers: Optional[List[str]] = None
    ):
        """
        Initialize the routing engine

        Args:
            policy_path: Path to routing_policy.json (optional)
            available_providers: List of available provider names (optional)
                                If None, all providers are considered available
        """
        self._policy = self._load_policy(policy_path)
        self._available_providers = available_providers
        self._tier_models = copy.deepcopy(DEFAULT_TIER_MODELS)
        self._task_routing = copy.deepcopy(
            self._policy.get("task_types", DEFAULT_TASK_ROUTING)
        )

        logger.info(
            f"[RoutingEngine] Initialized with {len(self._task_routing)} task types, "
            f"available_providers={available_providers or 'all'}"
        )

    def _load_policy(self, policy_path: Optional[Path]) -> Dict[str, Any]:
        """Load routing policy from JSON file"""
        if policy_path is None:
            # Try default location
            default_path = Path(__file__).parent / "routing_policy.json"
            if default_path.exists():
                policy_path = default_path
            else:
                logger.info("[RoutingEngine] No policy file found, using defaults")
                return {}

        try:
            with open(policy_path, 'r', encoding='utf-8') as f:
                policy = json.load(f)
            logger.info(f"[RoutingEngine] Loaded policy from {policy_path}")
            return policy
        except (FileNotFoundError, json.JSONDecodeError, OSError) as e:
            logger.warning(f"[RoutingEngine] Failed to load policy: {e}, using defaults")
            return {}

    def select_model(
        self,
        task_type: TaskType,
        risk_level: RiskLevel | str = RiskLevel.MEDIUM,
        context_size: int = 0
    ) -> ModelInfo:
        """
        Select the appropriate model for a given task

        Args:
            task_type: Type of task to perform
            risk_level: Risk level (RiskLevel enum or "high", "medium", "low")
            context_size: Estimated context size in tokens

        Returns:
            ModelInfo with selected model details

        Raises:
            ValueError: If no suitable model is available or invalid risk level
        """
        normalized_risk = self._normalize_risk_level(risk_level)

        task_key = task_type.value
        routing_config = self._task_routing.get(task_key, {"tier": 2, "fallback": 3})

        # Determine target tier based on task and risk
        target_tier_value = routing_config["tier"]
        fallback_tier_value = routing_config["fallback"]

        # Adjust tier based on risk level
        if normalized_risk == RiskLevel.HIGH:
            # For high-risk tasks, prefer higher capability (lower tier number)
            target_tier_value = max(0, target_tier_value - 1)
        elif normalized_risk == RiskLevel.LOW:
            # For low-risk tasks, can use lower capability (higher tier number)
            target_tier_value = min(3, target_tier_value + 1)

        target_tier = Tier(target_tier_value)
        fallback_tier = Tier(fallback_tier_value)

        # Check context size constraints
        if context_size > 0:
            target_tier = self._adjust_tier_for_context(target_tier, context_size)

        # Try to find available model in target tier
        model_info = self._find_available_model(target_tier)
        if model_info:
            # Preserve cross-generation fallback reason if set, otherwise use default
            if not model_info.reason:
                model_info.reason = f"Selected for {task_key} task (tier {target_tier.value})"
            else:
                # Append task context to cross-generation fallback reason
                model_info.reason = f"{model_info.reason} for {task_key} task"
            return model_info

        # Fallback to fallback tier
        logger.info(
            f"[RoutingEngine] No model available in tier {target_tier.value}, "
            f"falling back to tier {fallback_tier.value}"
        )
        model_info = self._find_available_model(fallback_tier)
        if model_info:
            model_info.is_fallback = True
            model_info.reason = (
                f"Fallback for {task_key} task "
                f"(original tier {target_tier.value} unavailable)"
            )
            return model_info

        # Try any available tier
        for tier in Tier:
            model_info = self._find_available_model(tier)
            if model_info:
                model_info.is_fallback = True
                model_info.reason = f"Emergency fallback to tier {tier.value}"
                logger.warning(
                    f"[RoutingEngine] Using emergency fallback: {model_info.model_name}"
                )
                return model_info

        raise ValueError(
            f"No suitable model available for task type '{task_key}'. "
            f"Check provider configurations."
        )

    def _normalize_risk_level(self, risk_level: RiskLevel | str) -> RiskLevel:
        """Normalize risk level to RiskLevel enum"""
        if isinstance(risk_level, RiskLevel):
            return risk_level

        risk_str = str(risk_level).lower().strip()
        try:
            return RiskLevel(risk_str)
        except ValueError:
            valid_values = [r.value for r in RiskLevel]
            raise ValueError(
                f"Invalid risk level '{risk_level}'. "
                f"Valid values are: {valid_values}"
            )

    def _adjust_tier_for_context(self, tier: Tier, context_size: int) -> Tier:
        """Adjust tier based on context size requirements"""
        tier_limit = TIER_CONTEXT_LIMITS.get(tier, 8000)

        if context_size <= tier_limit:
            return tier

        # Need a tier with larger context window
        for candidate_tier in Tier:
            candidate_limit = TIER_CONTEXT_LIMITS.get(candidate_tier, 8000)
            if context_size <= candidate_limit:
                logger.info(
                    f"[RoutingEngine] Adjusted tier from {tier.value} to "
                    f"{candidate_tier.value} due to context size ({context_size} tokens)"
                )
                return candidate_tier

        # Return highest capability tier if context is very large
        logger.warning(
            f"[RoutingEngine] Context size {context_size} exceeds all tier limits, "
            f"using TIER_0"
        )
        return Tier.TIER_0

    def _find_available_model(self, tier: Tier) -> Optional[ModelInfo]:
        """
        Find the best available model in the specified tier.

        Issue #2874: Improved candidate selection using scoring that considers:
        - Provider cost (lower cost = higher score when cost_weight > 0)
        - Provider preference (configurable preference order)
        - Provider availability

        The scoring formula is:
        score = (preference * preference_weight) + ((1 - cost) * cost_weight)

        Higher scores are better. The model with the highest score is selected.

        Cross-Generation Fallback (Routing Policy v1.2):
        When the primary provider (e.g., AliCloud) is unavailable and a secondary
        provider (e.g., SiliconFlow) is selected within the same tier, this is
        logged as a "cross-generation fallback" for observability.
        """
        tier_models = self._tier_models.get(tier, [])

        if not tier_models:
            return None

        # Get scoring weights from settings (Issue #2874)
        try:
            from common.config.settings import settings
            cost_weight = getattr(settings, 'routing_cost_weight', 0.3)
            preference_weight = getattr(settings, 'routing_preference_weight', 0.7)
        except ImportError:
            cost_weight = 0.3
            preference_weight = 0.7

        # Track primary provider for cross-generation fallback logging
        primary_provider = tier_models[0][0] if tier_models else None
        primary_available = self._is_provider_available(primary_provider) if primary_provider else False

        # Score all available candidates
        candidates = []
        for provider, model_name in tier_models:
            if self._is_provider_available(provider):
                score = self._score_candidate(provider, cost_weight, preference_weight)
                candidates.append((score, provider, model_name))

        if not candidates:
            return None

        # Select the best candidate (highest score)
        candidates.sort(key=lambda x: x[0], reverse=True)
        best_score, best_provider, best_model = candidates[0]

        # Cross-Generation Fallback logging (Routing Policy v1.2)
        # Log when primary provider is unavailable and secondary is used
        if primary_provider and not primary_available and best_provider != primary_provider:
            logger.info(
                f"[RoutingEngine] Cross-generation fallback in tier {tier.value}: "
                f"{primary_provider} unavailable, using {best_provider} ({best_model})"
            )
        else:
            logger.debug(
                f"[RoutingEngine] Selected {best_model} ({best_provider}) with score {best_score:.3f} "
                f"from {len(candidates)} candidates in tier {tier.value}"
            )

        # Build reason string for observability
        if primary_provider and not primary_available and best_provider != primary_provider:
            reason = f"Cross-generation fallback: {primary_provider} unavailable, using {best_provider}"
        else:
            reason = ""

        return ModelInfo(
            model_name=best_model,
            provider=best_provider,
            tier=tier,
            reason=reason
        )

    def _score_candidate(
        self,
        provider: str,
        cost_weight: float = 0.3,
        preference_weight: float = 0.7
    ) -> float:
        """
        Score a candidate provider for selection.

        Issue #2874: Improved best candidate selection scoring.
        EPIC I-4 Phase B-2: Soft Weighting based on degradation state.

        Args:
            provider: Provider name
            cost_weight: Weight for cost factor (0-1)
            preference_weight: Weight for preference factor (0-1)

        Returns:
            Score between 0 and 1 (higher is better)

        Soft Weighting (EPIC I-4 Phase B-2):
        - HEALTHY: 1.0x multiplier (no change)
        - DEGRADED: 0.7x multiplier (reduced likelihood)
        - CRITICAL: 0.3x multiplier (significantly reduced)
        - AVOID: Handled by Hard Gating (Phase B-1), not here

        Fail-open: If DegradationAdvisor is unavailable, use original score.
        """
        # Get cost (lower is better, so we invert it)
        cost = DEFAULT_PROVIDER_COSTS.get(provider, 1.0)
        cost_score = 1.0 - min(cost, 1.0)  # Invert so lower cost = higher score

        # Get preference (higher is better)
        preference = DEFAULT_PROVIDER_PREFERENCES.get(provider, 0.5)

        # Calculate weighted score
        total_weight = cost_weight + preference_weight
        if total_weight == 0:
            base_score = preference  # Fallback to preference only
        else:
            base_score = (preference * preference_weight + cost_score * cost_weight) / total_weight

        # EPIC I-4 Phase B-2: Apply Soft Weighting based on degradation state
        degradation_multiplier = self._get_degradation_multiplier(provider)
        final_score = base_score * degradation_multiplier

        return final_score

    def _get_degradation_multiplier(self, provider: str) -> float:
        """
        Get the degradation multiplier for a provider.

        EPIC I-4 Phase B-2: Soft Weighting

        This method retrieves the provider's degradation state from DegradationAdvisor
        and returns the appropriate score multiplier from SEVERITY_MULTIPLIERS (SSOT).

        Args:
            provider: Provider name

        Returns:
            Multiplier from governance.degradation_types.SEVERITY_MULTIPLIERS.
            See that constant for current values (HEALTHY=1.0, DEGRADED=0.7, etc.)

        Fail-open: Returns 1.0 if DegradationAdvisor is unavailable.
        """
        try:
            from governance.degradation_advisor import get_degradation_advisor
            from governance.degradation_types import (
                DegradationSeverity,
                SEVERITY_MULTIPLIERS,
            )

            advisor = get_degradation_advisor()
            if advisor is None:
                return 1.0

            state = advisor.get_provider_state(provider)

            # Use SEVERITY_MULTIPLIERS as single source of truth (EPIC I-4 Phase B-2)
            multiplier = SEVERITY_MULTIPLIERS.get(state, 1.0)

            if state != DegradationSeverity.HEALTHY:
                logger.info(
                    f"[I-4-SOFT-WEIGHTING] Provider {provider} has {state.value} state, "
                    f"applying {multiplier}x score multiplier"
                )

            return multiplier

        except ImportError:
            logger.debug(
                "[RoutingEngine] Governance module not available, skipping Soft Weighting"
            )
            return 1.0
        except Exception as e:
            logger.warning(
                f"[RoutingEngine] Soft Weighting error (fail-open): {e}. "
                f"Using default multiplier 1.0."
            )
            return 1.0

    def _is_provider_available(self, provider: str) -> bool:
        """Check if a provider is available"""
        if self._available_providers is None:
            return True
        return provider in self._available_providers

    def get_tier_for_task(self, task_type: TaskType) -> Tier:
        """Get the default tier for a task type"""
        task_key = task_type.value
        routing_config = self._task_routing.get(task_key, {"tier": 2})
        return Tier(routing_config["tier"])

    def get_models_for_tier(self, tier: Tier) -> List[tuple]:
        """Get all models configured for a tier"""
        return self._tier_models.get(tier, [])

    def set_available_providers(self, providers: List[str]):
        """Update the list of available providers"""
        self._available_providers = providers
        logger.info(f"[RoutingEngine] Updated available providers: {providers}")

    def register_model(self, tier: Tier, provider: str, model_name: str):
        """Register a new model for a tier"""
        if tier not in self._tier_models:
            self._tier_models[tier] = []
        self._tier_models[tier].append((provider, model_name))
        logger.info(
            f"[RoutingEngine] Registered model {model_name} ({provider}) for tier {tier.value}"
        )
