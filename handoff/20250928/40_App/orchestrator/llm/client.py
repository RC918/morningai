"""
Unified LLM Client for MorningAI Orchestrator

Provides a single interface for multiple LLM providers (OpenAI, Gemini, AliCloud, SiliconFlow).
This abstraction layer enables:
- Easy provider switching via configuration
- Consistent API across providers
- Automatic fallback handling
- Centralized logging and monitoring
- A/B testing support via ExperimentManager (Phase 5 PR-5)
- Task-based routing via RoutingEngine (EPIC #2594)

Usage:
    from llm.client import LLMClient, get_client_for_component, get_client_for_task

    # Default provider (OpenAI)
    client = LLMClient()
    response = client.generate("Explain dependency injection")

    # Specify provider
    client = LLMClient(provider="gemini")
    response = client.generate(
        prompt="Review this code",
        system_prompt="You are a code reviewer"
    )

    # Qwen providers (EPIC #2594)
    client = LLMClient(provider="alicloud")  # DashScope API
    client = LLMClient(provider="siliconflow")  # SiliconFlow API

    # Auto provider selection (uses available provider)
    client = LLMClient(provider="auto")
    response = client.generate("Generate unit tests")

    # Task-based routing (EPIC #2594 Ticket 2)
    from core.routing import TaskType
    client = get_client_for_task(TaskType.PLANNING, risk_level="high")
    response = client.generate("Create a project plan")

    # Experiment-aware client for component (Phase 5 PR-5)
    client = get_client_for_component("reviewer", trace_id="abc123")
    response = client.generate("Review this PR")
"""
import logging
import threading
from typing import Optional, Literal

from common.config.settings import settings
from .providers.base import LLMResponse
from .providers.openai_provider import OpenAIProvider
from .providers.gemini_provider import GeminiProvider
from .providers.alicloud_provider import AliCloudProvider
from .providers.siliconflow_provider import SiliconFlowProvider

logger = logging.getLogger(__name__)

ProviderType = Literal["openai", "gemini", "alicloud", "siliconflow", "auto"]

_default_client_lock = threading.Lock()

# Provider registry for availability checks
# Order determines priority for auto-selection
_PROVIDER_REGISTRY = [
    ("openai", OpenAIProvider),
    ("gemini", GeminiProvider),
    ("alicloud", AliCloudProvider),
    ("siliconflow", SiliconFlowProvider),
]


def _get_available_providers() -> list[str]:
    """Get list of available provider names based on configuration and governance allowlist.

    The provider selection follows this logic:
    1. Check which providers have valid API keys configured
    2. If ROUTING_ALLOWED_PROVIDERS is set (non-empty), filter to only allowed providers
    3. Return the intersection of available and allowed providers

    Governance Control (Blueprint: Model Governance Framework v2):
    - Empty allowlist (default): Use all providers with valid API keys
    - Non-empty allowlist: Only use providers in the allowlist that also have valid API keys
    - If allowlist is set but no allowed providers have valid API keys, return empty list
      (caller should handle this as an error condition)

    Security Policy (Fail-Closed):
    - When governance mode is enabled (allowlist is non-empty), any exception during
      allowlist processing will block ALL providers and log a critical error
    - This prevents accidental bypass of governance controls due to configuration errors
    - When governance mode is NOT enabled (empty allowlist), exceptions are not expected
      as no allowlist processing occurs
    """
    available = []
    for name, provider_class in _PROVIDER_REGISTRY:
        if provider_class().is_available():
            available.append(name)

    # Check if governance mode is enabled (allowlist is set)
    allowlist_str = getattr(settings, 'routing_allowed_providers', '')

    if not allowlist_str:
        # Governance mode NOT enabled - return all available providers
        return available

    # Governance mode IS enabled - apply strict fail-closed policy
    try:
        allowed = [p.strip().lower() for p in allowlist_str.split(',') if p.strip()]
        filtered = [p for p in available if p.lower() in allowed]
        logger.info(
            f"[LLMClient] Applied provider governance allowlist: "
            f"allowlist={allowed}, available_with_keys={available}, "
            f"filtered_result={filtered}"
        )
        return filtered
    except Exception as e:
        # FAIL-CLOSED: When governance is enabled, any error blocks all providers
        # This prevents accidental bypass of governance controls
        logger.error(
            f"[LLMClient] CRITICAL: Failed to apply provider governance allowlist. "
            f"Blocking all providers for security. "
            f"ROUTING_ALLOWED_PROVIDERS='{allowlist_str}', Error: {e}. "
            f"Please check your configuration."
        )
        return []


class LLMClient:
    """
    Unified LLM client supporting multiple providers

    Providers:
    - openai: OpenAI GPT-4 (default)
    - gemini: Google Gemini Pro
    - alicloud: Qwen models via DashScope API (EPIC #2594)
    - siliconflow: Qwen models via SiliconFlow API (EPIC #2594)
    - auto: Automatic provider selection based on availability

    The provider can be configured via:
    1. Constructor parameter
    2. LLM_PROVIDER environment variable
    3. Default: openai
    """

    def __init__(
        self,
        provider: Optional[ProviderType] = None,
        model: Optional[str] = None
    ):
        """
        Initialize LLM client with specified provider

        Args:
            provider: Provider to use (openai, gemini, alicloud, siliconflow, auto)
                     If None, uses LLM_PROVIDER env var or defaults to openai
            model: Model to use (provider-specific)
                   If None, uses provider's default model
        """
        self._provider_name = self._resolve_provider(provider)
        self._model = model
        self._provider = self._create_provider()

        logger.info(
            f"[LLMClient] Initialized with provider={self._provider_name}, "
            f"model={self._model or 'default'}"
        )

    def _resolve_provider(self, provider: Optional[ProviderType]) -> str:
        """
        Resolve which provider to use

        Priority:
        1. Explicit provider parameter
        2. LLM_PROVIDER environment variable (has default: openai)
        """
        provider_name = provider or getattr(settings, 'llm_provider', None) or "openai"
        if provider_name == "auto":
            return self._auto_select_provider()
        return provider_name

    def _auto_select_provider(self) -> str:
        """
        Automatically select available provider

        Priority:
        1. OpenAI (if configured)
        2. Gemini (if configured)
        3. AliCloud/DashScope (if configured) - EPIC #2594
        4. SiliconFlow (if configured) - EPIC #2594
        5. Raise error if none available
        """
        available = _get_available_providers()
        if available:
            selected = available[0]
            logger.info(f"[LLMClient] Auto-selected {selected} provider")
            return selected

        raise ValueError(
            "No LLM provider available. "
            "Configure OPENAI_API_KEY, GEMINI_API_KEY, DASHSCOPE_API_KEY, "
            "or SILICONFLOW_API_KEY."
        )

    def _create_provider(self):
        """Create the appropriate provider instance"""
        if self._provider_name == "openai":
            return OpenAIProvider(model=self._model)
        elif self._provider_name == "gemini":
            return GeminiProvider(model=self._model)
        elif self._provider_name == "alicloud":
            return AliCloudProvider(model=self._model)
        elif self._provider_name == "siliconflow":
            return SiliconFlowProvider(model=self._model)
        else:
            raise ValueError(f"Unknown provider: {self._provider_name}")

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        json_mode: bool = False,
        **kwargs
    ) -> LLMResponse:
        """
        Generate text using the configured LLM provider

        Args:
            prompt: User prompt/message
            system_prompt: Optional system prompt for context
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            json_mode: If True, request JSON-formatted response
            **kwargs: Provider-specific parameters

        Returns:
            LLMResponse with generated content

        Raises:
            ValueError: If provider is not configured
            Exception: If API call fails
        """
        if not self._provider.is_available():
            raise ValueError(
                f"Provider {self._provider_name} is not available. "
                f"Check API key configuration."
            )

        return self._provider.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=json_mode,
            **kwargs
        )

    def is_available(self) -> bool:
        """Check if the configured provider is available"""
        return self._provider.is_available()

    @property
    def provider_name(self) -> str:
        """Get the current provider name"""
        return self._provider_name

    @property
    def model(self) -> str:
        """Get the current model name"""
        return self._provider.model

    @classmethod
    def get_default_client(cls) -> "LLMClient":
        """
        Get a default LLMClient instance (thread-safe)

        Uses settings from environment variables.
        Cached for reuse across calls.
        """
        if not hasattr(cls, '_default_client'):
            with _default_client_lock:
                if not hasattr(cls, '_default_client'):
                    cls._default_client = cls()
        return cls._default_client

    @classmethod
    def reset_default_client(cls):
        """Reset the default client (useful for testing)"""
        if hasattr(cls, '_default_client'):
            delattr(cls, '_default_client')


def get_client_for_component(
    component: str,
    trace_id: str,
    default_provider: str = "openai",
    model: Optional[str] = None
) -> LLMClient:
    """
    Get an LLMClient configured based on active experiments for a component.

    This function integrates with ExperimentManager to enable A/B testing
    of different LLM providers for specific components (planner, reviewer, etc.).

    In production, this is a no-op and returns the default provider.
    In staging, it checks for active experiments and routes accordingly.

    Args:
        component: Component name (e.g., "planner", "reviewer")
        trace_id: Unique trace identifier for consistent variant assignment
        default_provider: Default provider if no experiment is active
        model: Optional model override (takes precedence over experiment model)

    Returns:
        LLMClient configured with the appropriate provider and model

    Usage:
        # In reviewer code:
        client = get_client_for_component("reviewer", trace_id)
        response = client.generate("Review this code...")
    """
    try:
        from experiment_manager import get_experiment_manager

        manager = get_experiment_manager()
        experiment_info = manager.get_experiment_for_component(component, trace_id)

        if experiment_info:
            provider = experiment_info["provider"]
            # Use experiment model if no explicit model override provided
            experiment_model = experiment_info.get("model")
            final_model = model or experiment_model

            logger.info(
                f"[LLMClient] Creating client for component={component}, "
                f"provider={provider}, model={final_model}, trace_id={trace_id}, "
                f"experiment={experiment_info['experiment_name']}, variant={experiment_info['variant']}",
                extra={
                    "operation": "get_client_for_component",
                    "component": component,
                    "provider": provider,
                    "model": final_model,
                    "trace_id": trace_id,
                    "experiment_name": experiment_info["experiment_name"],
                    "variant": experiment_info["variant"]
                }
            )

            return LLMClient(provider=provider, model=final_model)
        else:
            logger.info(
                f"[LLMClient] No active experiment for component={component}, "
                f"using default provider={default_provider}",
                extra={
                    "operation": "get_client_for_component",
                    "component": component,
                    "provider": default_provider,
                    "trace_id": trace_id
                }
            )
            return LLMClient(provider=default_provider, model=model)

    except ImportError:
        logger.debug(
            "[LLMClient] ExperimentManager not available, using default provider"
        )
        return LLMClient(provider=default_provider, model=model)
    except Exception as e:
        logger.warning(
            f"[LLMClient] Failed to get experiment provider: {e}, "
            f"using default provider={default_provider}"
        )
        return LLMClient(provider=default_provider, model=model)


def get_client_for_task(
    task_type,
    risk_level: str = "medium",
    context_size: int = 0
) -> LLMClient:
    """
    Get an LLMClient configured based on task type using the RoutingEngine.

    This function implements task-based routing (EPIC #2594 Ticket 2),
    selecting the appropriate model based on:
    - Task type (planning, coding, review, etc.)
    - Risk level (high, medium, low)
    - Context size (token count)

    Args:
        task_type: Type of task (from core.routing.TaskType)
        risk_level: Risk level ("high", "medium", "low")
        context_size: Estimated context size in tokens

    Returns:
        LLMClient configured with the appropriate provider and model

    Raises:
        ValueError: If no suitable model is available

    Usage:
        from core.routing import TaskType
        from llm.client import get_client_for_task

        # Planning task - will select Tier 0 model (qwen-max or gpt-4o)
        client = get_client_for_task(TaskType.PLANNING, risk_level="high")
        response = client.generate("Create a project plan")

        # UX copy task - will select Tier 3 model (qwen-14b)
        client = get_client_for_task(TaskType.UX_COPY)
        response = client.generate("Write button label")
    """
    try:
        from core.routing import RoutingEngine

        # Determine available providers using shared helper
        available_providers = _get_available_providers()

        if not available_providers:
            raise ValueError(
                "No LLM provider available. "
                "Configure OPENAI_API_KEY, GEMINI_API_KEY, DASHSCOPE_API_KEY, "
                "or SILICONFLOW_API_KEY."
            )

        engine = RoutingEngine(available_providers=available_providers)
        model_info = engine.select_model(
            task_type=task_type,
            risk_level=risk_level,
            context_size=context_size
        )

        logger.info(
            f"[LLMClient] Task-based routing selected: "
            f"provider={model_info.provider}, model={model_info.model_name}, "
            f"tier={model_info.tier.value}, task={task_type.value}, "
            f"risk={risk_level}, is_fallback={model_info.is_fallback}",
            extra={
                "operation": "get_client_for_task",
                "task_type": task_type.value,
                "risk_level": risk_level,
                "context_size": context_size,
                "provider": model_info.provider,
                "model": model_info.model_name,
                "tier": model_info.tier.value,
                "is_fallback": model_info.is_fallback,
                "reason": model_info.reason
            }
        )

        return LLMClient(provider=model_info.provider, model=model_info.model_name)

    except ImportError as e:
        logger.warning(
            f"[LLMClient] RoutingEngine not available: {e}, "
            f"falling back to auto provider selection"
        )
        return LLMClient(provider="auto")
    except Exception as e:
        logger.warning(
            f"[LLMClient] Task-based routing failed: {e}, "
            f"falling back to auto provider selection"
        )
        return LLMClient(provider="auto")
