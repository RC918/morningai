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

    # Default provider (auto-selects based on availability, Qwen-first)
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
import time
from typing import Any, Optional, Literal

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
# Gemini is prioritized as primary provider, with AliCloud (Qwen) as secondary
_PROVIDER_REGISTRY = [
    ("gemini", GeminiProvider),
    ("alicloud", AliCloudProvider),
    ("openai", OpenAIProvider),
]


def _get_available_providers(bypass_governance: bool = False) -> list[str]:
    """Get list of available provider names based on configuration and governance.

    The provider selection follows this logic:
    1. Check which providers have valid API keys configured
    2. If ROUTING_ALLOWED_PROVIDERS is set (non-empty), filter to only allowed providers
    3. If DEGRADATION_ENFORCEMENT_ENABLED is true, filter out AVOID providers (Hard Gating)
    4. Return the intersection of available and allowed providers

    Governance Control (Blueprint: Model Governance Framework v2):
    - Empty allowlist (default): Use all providers with valid API keys
    - Non-empty allowlist: Only use providers in the allowlist that also have valid API keys
    - If allowlist is set but no allowed providers have valid API keys, return empty list
      (caller should handle this as an error condition)

    EPIC I-4 Phase B: Hard Gating (Degradation Enforcement):
    - When DEGRADATION_ENFORCEMENT_ENABLED is true, AVOID providers are filtered out
    - Floor protection ensures at least 1 provider remains available (absolute red line)
    - Fail-open: If DegradationAdvisor is unavailable, all providers remain available

    Security Policy (Fail-Closed for allowlist, Fail-Open for degradation):
    - When governance mode is enabled (allowlist is non-empty), any exception during
      allowlist processing will block ALL providers and log a critical error
    - When degradation enforcement is enabled, any exception will NOT block providers
      (fail-open to prevent cascading failures)

    Args:
        bypass_governance: If True, skip all governance filtering (emergency/diagnostic only)
    """
    available = []
    for name, provider_class in _PROVIDER_REGISTRY:
        if provider_class().is_available():
            available.append(name)

    # Emergency bypass for diagnostic/staging use
    if bypass_governance:
        logger.warning(
            "[LLMClient] BYPASS_GOVERNANCE enabled - skipping all governance filtering. "
            "This should only be used for emergency/diagnostic purposes."
        )
        return available

    # Check if governance mode is enabled (allowlist is set)
    allowlist_str = getattr(settings, 'routing_allowed_providers', '')

    if allowlist_str:
        # Governance mode IS enabled - apply strict fail-closed policy
        try:
            allowed = [p.strip().lower() for p in allowlist_str.split(',') if p.strip()]
            available = [p for p in available if p.lower() in allowed]
            logger.info(
                f"[LLMClient] Applied provider governance allowlist: "
                f"allowlist={allowed}, filtered_result={available}"
            )
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

    # EPIC I-4 Phase B: Hard Gating (Degradation Enforcement)
    if getattr(settings, 'degradation_enforcement_enabled', False):
        available = _apply_hard_gating(available)

    return available


def _apply_hard_gating(providers: list[str]) -> list[str]:
    """
    Apply Hard Gating logic to filter AVOID providers.

    EPIC I-4 Phase B-1: Degradation Enforcement

    This function filters out providers with AVOID severity from the available list,
    while ensuring floor protection (at least 1 provider remains available).

    Args:
        providers: List of available provider names

    Returns:
        Filtered list of providers with AVOID providers removed (floor protected)

    Safety Features:
    - Floor protection: At least 1 provider always remains available
    - Fail-open: If DegradationAdvisor is unavailable, all providers remain available
    - Governance telemetry: ERROR-level logging when Hard Gating occurs

    Floor Protection Strategy (consistent priority):
    - Priority 1: Dynamic floor_provider (from DegradationAdvisor) if available and in providers
    - Priority 2: Fixed floor_provider (from settings) if available and in providers
    - Priority 3: First provider in list as emergency fallback
    """
    if not providers:
        return providers

    try:
        from governance.degradation_advisor import get_degradation_advisor
        from governance.degradation_types import DegradationSeverity

        advisor = get_degradation_advisor()
        if advisor is None:
            # Fail-open: Advisory not available, return all providers
            logger.debug(
                "[LLMClient] DegradationAdvisor not available, skipping Hard Gating"
            )
            return providers

        # Get floor provider candidates
        dynamic_floor = advisor.get_current_floor_provider()
        fixed_floor = getattr(settings, 'degradation_fixed_floor_provider', 'openai')

        # Determine effective floor provider using consistent priority:
        # 1. Dynamic floor (if available and in providers)
        # 2. Fixed floor (if in providers)
        # 3. First provider (emergency fallback)
        effective_floor = None
        if dynamic_floor and dynamic_floor in providers:
            effective_floor = dynamic_floor
        elif fixed_floor in providers:
            effective_floor = fixed_floor
        elif providers:
            effective_floor = providers[0]

        logger.debug(
            f"[I-4-ENFORCEMENT] Floor provider selection: "
            f"dynamic={dynamic_floor}, fixed={fixed_floor}, "
            f"effective={effective_floor}"
        )

        # Filter out AVOID providers (except floor protected)
        filtered = []
        gated_providers = []

        for provider in providers:
            state = advisor.get_provider_state(provider)

            # Check if provider should be gated
            if state == DegradationSeverity.AVOID:
                # Check floor protection (only effective_floor is protected)
                is_floor_protected = (provider == effective_floor)

                if is_floor_protected:
                    # Floor protected - keep this provider
                    filtered.append(provider)
                    logger.warning(
                        f"[I-4-ENFORCEMENT] Provider {provider} has AVOID state but is "
                        f"floor-protected (effective_floor). Keeping in available list."
                    )
                else:
                    # Not floor protected - gate this provider
                    gated_providers.append(provider)
                    logger.error(
                        f"[I-4-ENFORCEMENT] Hard-gating provider {provider} due to "
                        f"AVOID state."
                    )
            else:
                # Not AVOID - keep this provider
                filtered.append(provider)

        # Absolute floor protection: Never return empty list
        if not filtered and providers:
            # All providers were gated - use effective_floor as fallback
            fallback = effective_floor if effective_floor else providers[0]
            filtered = [fallback]
            logger.error(
                f"[I-4-ENFORCEMENT] FLOOR PROTECTION ACTIVATED: All providers would be "
                f"gated. Keeping {fallback} as emergency fallback. "
                f"Original providers: {providers}, Gated: {gated_providers}"
            )

        if gated_providers:
            logger.info(
                f"[I-4-ENFORCEMENT] Hard Gating summary: "
                f"original={providers}, gated={gated_providers}, "
                f"remaining={filtered}, effective_floor={effective_floor}"
            )

        return filtered

    except ImportError:
        # Fail-open: Governance module not available
        logger.debug(
            "[LLMClient] Governance module not available, skipping Hard Gating"
        )
        return providers
    except Exception as e:
        # Fail-open: Any error during Hard Gating should not block providers
        logger.warning(
            f"[LLMClient] Hard Gating error (fail-open): {e}. "
            f"Returning all providers to prevent service disruption."
        )
        return providers


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

    # Default timeout values per provider (in seconds)
    # These can be overridden via constructor or per-call
    DEFAULT_TIMEOUTS = {
        "openai": 30,
        "gemini": 60,
        "alicloud": 60,
        "siliconflow": 60,
    }

    def __init__(
        self,
        provider: Optional[ProviderType] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None
    ):
        """
        Initialize LLM client with specified provider

        Args:
            provider: Provider to use (openai, gemini, alicloud, siliconflow, auto)
                     If None, uses LLM_PROVIDER env var or defaults to openai
            model: Model to use (provider-specific)
                   If None, uses provider's default model
            timeout: Request timeout in seconds (Issue #3653)
                    If None, uses provider-specific default from DEFAULT_TIMEOUTS
        """
        self._provider_name = self._resolve_provider(provider)
        self._model = model
        self._timeout = timeout
        self._provider = self._create_provider()

        logger.info(
            f"[LLMClient] Initialized with provider={self._provider_name}, "
            f"model={self._model or 'default'}, timeout={self._timeout or 'default'}"
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
        timeout: Optional[int] = None,
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
            timeout: Request timeout in seconds (Issue #3653)
                    If None, uses instance timeout or provider default
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

        # Issue #3653: Resolve timeout with priority:
        # 1. Per-call timeout parameter
        # 2. Instance-level timeout (from __init__)
        # 3. Provider-specific default from DEFAULT_TIMEOUTS
        # Note: Use explicit `is not None` checks to preserve timeout=0 if specified
        user_specified_timeout = timeout is not None or self._timeout is not None
        if timeout is not None:
            effective_timeout = timeout
        elif self._timeout is not None:
            effective_timeout = self._timeout
        else:
            effective_timeout = self.DEFAULT_TIMEOUTS.get(self._provider_name, 60)

        # Issue #3653: Gemini provider compatibility warning
        # GeminiProvider uses google-genai SDK which doesn't support timeout parameter
        # in the same way as OpenAI-compatible providers. Log warning for transparency.
        if self._provider_name == "gemini" and user_specified_timeout:
            logger.warning(
                f"[LLMClient] Gemini provider does not enforce timeout parameter. "
                f"Specified timeout={effective_timeout}s will be passed but may not be honored. "
                f"Consider using OpenAI/AliCloud/SiliconFlow for strict timeout enforcement.",
                extra={
                    "operation": "llm_generate",
                    "provider": self._provider_name,
                    "timeout": effective_timeout,
                    "timeout_enforced": False
                }
            )

        # EPIC I-2: Record request timing for health scoring
        start_time = time.time()
        success = False
        error_type = None

        try:
            response = self._provider.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                json_mode=json_mode,
                timeout=effective_timeout,
                **kwargs
            )
            success = True
        except Exception as e:
            # Classify error type for health scoring
            error_type = self._classify_error(e)
            raise
        finally:
            # EPIC I-2: Record provider metrics for health scoring
            latency_ms = (time.time() - start_time) * 1000
            self._record_provider_metrics(latency_ms, success, error_type)

        # EPIC I-1: Runtime Drift Detection (observe-only by default)
        # This hook validates LLM responses without blocking requests
        # unless DRIFT_DETECTION_BLOCK_ON_FAIL=true
        drift_result = None
        try:
            from governance.drift_detector import observe_response, DriftDetectedError
            drift_result = observe_response(
                response=response,
                json_mode=json_mode,
                provider=self._provider_name,
                model=self.model
            )
        except ImportError:
            pass  # Drift detection not available, continue normally
        except DriftDetectedError:
            raise  # Re-raise if blocking is enabled, as designed
        except Exception as e:
            # Log other unexpected drift detection errors but don't block
            logger.warning(
                f"[LLMClient] Drift detection error (non-blocking): {e}",
                extra={"provider": self._provider_name, "model": self.model}
            )

        # EPIC I-2b: Drift-Triggered Retry (disabled by default)
        # Issue #3933: Extracted to _handle_drift_retry() for SRP compliance
        if drift_result and drift_result.has_drift:
            retry_response = self._handle_drift_retry(
                drift_result=drift_result,
                response=response,
                start_time=start_time,
                effective_timeout=effective_timeout,
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                json_mode=json_mode,
                **kwargs
            )
            if retry_response is not None:
                return retry_response

        return response

    def _handle_drift_retry(
        self,
        drift_result: Any,
        response: "LLMResponse",
        start_time: float,
        effective_timeout: Optional[int],
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
        json_mode: bool,
        **kwargs
    ) -> Optional["LLMResponse"]:
        """
        Handle drift-triggered retry logic.

        Issue #3933: Extracted from generate() for SRP compliance and
        to reduce C901 complexity.

        EPIC I-2b: If drift is detected and retry is enabled, attempt
        retry with higher-tier model.

        Returns:
            LLMResponse if retry was successful, None if retry was not
            attempted or failed (caller should return original response).
        """
        try:
            from governance.drift_retry import should_retry_on_drift

            # Calculate elapsed time for remaining timeout
            elapsed_seconds = time.time() - start_time
            remaining_timeout = None
            if effective_timeout:
                remaining_timeout = max(0, effective_timeout - elapsed_seconds)
                if remaining_timeout <= 0:
                    logger.warning(
                        "[LLMClient] Drift retry skipped: timeout exhausted",
                        extra={"provider": self._provider_name, "model": self.model}
                    )
                    return None

            # Calculate original cost from response usage for cost cap enforcement
            # Use the cost from the very first attempt, not subsequent retries
            current_cost = self._estimate_request_cost(response)
            original_cost = kwargs.get('_original_cost') or current_cost

            retry_decision = should_retry_on_drift(
                drift_events=drift_result.events,
                task_type=kwargs.get('task_type'),
                attempt_count=kwargs.get('_drift_retry_attempt', 0),
                original_cost=original_cost,
                current_model=self.model,
                current_provider=self._provider_name
            )

            if retry_decision.should_retry:
                logger.info(
                    f"[LLMClient] Drift retry triggered: "
                    f"reason={retry_decision.reason}, "
                    f"retry_model={retry_decision.retry_model}",
                    extra={
                        "operation": "drift_retry",
                        "original_model": self.model,
                        "retry_model": retry_decision.retry_model,
                        "attempt": retry_decision.metadata.get('attempt_count', 1),
                        "original_cost": original_cost,
                        "remaining_timeout": remaining_timeout
                    }
                )

                # Create new client with higher-tier model and retry
                retry_client = LLMClient(
                    provider=retry_decision.retry_provider or self._provider_name,
                    model=retry_decision.retry_model,
                    timeout=self._timeout
                )

                # Track retry attempt and original cost to prevent infinite loops
                retry_kwargs = kwargs.copy()
                retry_kwargs['_drift_retry_attempt'] = kwargs.get('_drift_retry_attempt', 0) + 1
                retry_kwargs['_original_cost'] = original_cost

                return retry_client.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    json_mode=json_mode,
                    timeout=remaining_timeout,
                    **retry_kwargs
                )
        except ImportError:
            pass  # Drift retry not available, continue normally
        except Exception as e:
            # Log retry errors but don't block - return original response
            logger.warning(
                f"[LLMClient] Drift retry error (non-blocking): {e}",
                extra={"provider": self._provider_name, "model": self.model}
            )

        return None

    def _classify_error(self, error: Exception) -> str:
        """
        Classify error type for health scoring metrics

        EPIC I-2: Provider Health Scoring
        """
        error_str = str(error).lower()

        if "timeout" in error_str or "timed out" in error_str:
            return "timeout"
        elif "rate" in error_str and "limit" in error_str:
            return "rate_limit"
        elif "401" in error_str or "unauthorized" in error_str:
            return "auth_error"
        elif "429" in error_str:
            return "rate_limit"
        elif "500" in error_str or "502" in error_str or "503" in error_str:
            return "server_error"
        elif "connection" in error_str or "network" in error_str:
            return "connection_error"
        else:
            return "api_error"

    def _record_provider_metrics(
        self,
        latency_ms: float,
        success: bool,
        error_type: Optional[str] = None
    ) -> None:
        """
        Record provider metrics for health scoring

        EPIC I-2: Provider Health Scoring

        This method is designed to never block or raise exceptions.
        """
        if not getattr(settings, 'provider_health_enabled', True):
            return

        try:
            from metrics import get_canary_metrics
            metrics = get_canary_metrics()
            if metrics:
                metrics.record_provider_request(
                    provider=self._provider_name,
                    latency_ms=latency_ms,
                    success=success,
                    error_type=error_type
                )
        except ImportError:
            pass  # Metrics not available
        except Exception as e:
            # Never block on metrics errors
            logger.debug(
                f"[LLMClient] Failed to record provider metrics: {e}",
                extra={"provider": self._provider_name}
            )

    def _estimate_request_cost(self, response: Any) -> float:
        """
        Estimate the cost of a request based on response usage.

        EPIC I-2b: Cost estimation for drift retry cost cap enforcement.

        This uses approximate token costs. For more accurate costs,
        integrate with a dedicated cost tracking service.

        Args:
            response: The LLM response object with usage information

        Returns:
            Estimated cost in USD (approximate)
        """
        try:
            usage = getattr(response, 'usage', None)
            if not usage:
                return 0.0

            prompt_tokens = getattr(usage, 'prompt_tokens', 0) or 0
            completion_tokens = getattr(usage, 'completion_tokens', 0) or 0
            total_tokens = prompt_tokens + completion_tokens

            if total_tokens == 0:
                return 0.0

            # Approximate cost per 1K tokens (USD)
            # These are rough estimates and may need adjustment
            cost_per_1k = {
                "qwen-max": 0.004,
                "qwen-plus": 0.002,
                "qwen-turbo": 0.001,
                "qwen-72b": 0.003,
                "qwen-14b": 0.001,
                "gpt-4o": 0.01,
                "gpt-3.5-turbo": 0.002,
                "gemini-1.5-pro": 0.007,
                "gemini-1.5-flash": 0.0015,
            }

            rate = cost_per_1k.get(self.model, 0.002)  # Default to mid-tier cost
            estimated_cost = (total_tokens / 1000) * rate

            return estimated_cost

        except Exception as e:
            logger.debug(
                f"[LLMClient] Failed to estimate request cost: {e}",
                extra={"provider": self._provider_name, "model": self.model}
            )
            return 0.0

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

    @property
    def timeout(self) -> int:
        """Get the effective timeout in seconds (Issue #3653)"""
        if self._timeout is not None:
            return self._timeout
        return self.DEFAULT_TIMEOUTS.get(self._provider_name, 60)

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
    default_provider: str = "auto",
    model: Optional[str] = None,
    timeout: Optional[int] = None
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
        timeout: Optional timeout in seconds (Issue #3653)

    Returns:
        LLMClient configured with the appropriate provider, model, and timeout

    Usage:
        # In reviewer code:
        client = get_client_for_component("reviewer", trace_id)
        response = client.generate("Review this code...")

        # With custom timeout:
        client = get_client_for_component("reviewer", trace_id, timeout=120)
        response = client.generate("Review this large codebase...")
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

            return LLMClient(provider=provider, model=final_model, timeout=timeout)
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
            return LLMClient(provider=default_provider, model=model, timeout=timeout)

    except ImportError:
        logger.debug(
            "[LLMClient] ExperimentManager not available, using default provider"
        )
        return LLMClient(provider=default_provider, model=model, timeout=timeout)
    except Exception as e:
        logger.warning(
            f"[LLMClient] Failed to get experiment provider: {e}, "
            f"using default provider={default_provider}"
        )
        return LLMClient(provider=default_provider, model=model, timeout=timeout)


def get_client_for_task(
    task_type,
    risk_level: str = "medium",
    context_size: int = 0,
    escalation_count: int = 0,
    retry_count: int = 0,
    timeout: Optional[int] = None
) -> LLMClient:
    """
    Get an LLMClient configured based on task type using the RoutingEngine.

    This function implements task-based routing (EPIC #2594 Ticket 2),
    selecting the appropriate model based on:
    - Task type (planning, coding, review, etc.)
    - Risk level (high, medium, low)
    - Context size (token count)
    - Escalation count (for hard cap enforcement)
    - Retry count (for hard cap enforcement)

    Args:
        task_type: Type of task (from core.routing.TaskType)
        risk_level: Risk level ("high", "medium", "low")
        context_size: Estimated context size in tokens
        escalation_count: Number of tier escalations already performed (Issue #3640)
        retry_count: Number of retries already attempted (Issue #3640)
        timeout: Optional timeout in seconds (Issue #3653)

    Returns:
        LLMClient configured with the appropriate provider, model, and timeout

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

        # With escalation tracking (Issue #3640)
        # Note: 'state' refers to AgentState from langgraph_orchestrator
        client = get_client_for_task(
            TaskType.CODING,
            risk_level="medium",
            escalation_count=state.get("escalation_count", 0),  # from AgentState
            retry_count=state.get("retry_count", 0)  # from AgentState
        )
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
            context_size=context_size,
            escalation_count=escalation_count,
            retry_count=retry_count
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

        return LLMClient(
            provider=model_info.provider,
            model=model_info.model_name,
            timeout=timeout
        )

    except ImportError as e:
        logger.warning(
            f"[LLMClient] RoutingEngine not available: {e}, "
            f"falling back to auto provider selection"
        )
        return LLMClient(provider="auto", timeout=timeout)
    except Exception as e:
        logger.warning(
            f"[LLMClient] Task-based routing failed: {e}, "
            f"falling back to auto provider selection"
        )
        return LLMClient(provider="auto", timeout=timeout)
