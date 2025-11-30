"""
Unified LLM Client for MorningAI Orchestrator

Provides a single interface for multiple LLM providers (OpenAI, Gemini).
This abstraction layer enables:
- Easy provider switching via configuration
- Consistent API across providers
- Automatic fallback handling
- Centralized logging and monitoring
- A/B testing support via ExperimentManager (Phase 5 PR-5)

Usage:
    from llm.client import LLMClient, get_client_for_component

    # Default provider (OpenAI)
    client = LLMClient()
    response = client.generate("Explain dependency injection")

    # Specify provider
    client = LLMClient(provider="gemini")
    response = client.generate(
        prompt="Review this code",
        system_prompt="You are a code reviewer"
    )

    # Auto provider selection (uses available provider)
    client = LLMClient(provider="auto")
    response = client.generate("Generate unit tests")

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

logger = logging.getLogger(__name__)

ProviderType = Literal["openai", "gemini", "auto"]

_default_client_lock = threading.Lock()


class LLMClient:
    """
    Unified LLM client supporting multiple providers

    Providers:
    - openai: OpenAI GPT-4 (default)
    - gemini: Google Gemini Pro (staging)
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
            provider: Provider to use (openai, gemini, auto)
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
        3. Raise error if none available
        """
        openai_provider = OpenAIProvider()
        if openai_provider.is_available():
            logger.info("[LLMClient] Auto-selected OpenAI provider")
            return "openai"

        gemini_provider = GeminiProvider()
        if gemini_provider.is_available():
            logger.info("[LLMClient] Auto-selected Gemini provider")
            return "gemini"

        raise ValueError(
            "No LLM provider available. "
            "Configure OPENAI_API_KEY or GEMINI_API_KEY."
        )

    def _create_provider(self):
        """Create the appropriate provider instance"""
        if self._provider_name == "openai":
            return OpenAIProvider(model=self._model)
        elif self._provider_name == "gemini":
            return GeminiProvider(model=self._model)
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
