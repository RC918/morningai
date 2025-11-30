"""
Google Gemini LLM Provider implementation

Provides Gemini Pro and Gemini 3 Pro support for MorningAI Orchestrator.
Uses the new google-genai SDK (GA since May 2025).

Supports:
- gemini-pro (legacy, default for backward compatibility)
- gemini-3-pro-preview (Gemini 3, recommended for new features)

Fallback Behavior:
- When a Gemini 3 model fails, automatically falls back to gemini-pro
- Fallback is logged for monitoring and A/B test analysis
- LLMResponse.model reflects the actual model used (including fallback)

Environment Variables:
- GEMINI_API_KEY: Google AI API key
"""
import logging
from typing import Optional, Literal

from common.config.settings import settings
from .base import BaseLLMProvider, LLMResponse

# Import google-genai SDK at module level
try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

logger = logging.getLogger(__name__)

# Thinking level for Gemini 3 models
ThinkingLevel = Literal["low", "high"]

# Fallback model for Gemini 3 failures
FALLBACK_MODEL = "gemini-pro"


class GeminiProvider(BaseLLMProvider):
    """
    Google Gemini provider using the new google-genai SDK

    Supports both legacy Gemini Pro and new Gemini 3 Pro models.
    The SDK automatically handles thought signatures for function calling.

    Features:
    - thinking_level: Control reasoning depth for Gemini 3 models
      (parameter on generate() method, only applied for Gemini 3 models)
    - json_mode: Request JSON-formatted responses
    - Automatic fallback: Gemini 3 failures fall back to gemini-pro
    """

    provider_name = "gemini"
    default_model = "gemini-pro"  # Keep legacy default for backward compatibility

    # Gemini 3 models that support thinking_level
    GEMINI_3_MODELS = ["gemini-3-pro-preview", "gemini-3-pro-image-preview"]

    def __init__(self, model: Optional[str] = None):
        """
        Initialize Gemini provider

        Args:
            model: Model to use (default: gemini-pro)
                   Use "gemini-3-pro-preview" for Gemini 3 features
        """
        self.model = model or self.default_model
        self._client = None

    def _get_client(self):
        """Lazy initialization of Gemini client using new SDK"""
        if self._client is None:
            if genai is None or types is None:
                raise NotImplementedError(
                    "Google GenAI SDK not installed. "
                    "Install with: pip install google-genai"
                )

            api_key = getattr(settings, 'gemini_api_key', None)
            if not api_key:
                raise ValueError(
                    "Gemini API key not configured. "
                    "Set GEMINI_API_KEY environment variable."
                )

            self._client = genai.Client(api_key=api_key)

        return self._client

    def is_available(self) -> bool:
        """
        Check if Gemini API key is configured

        Returns:
            True if GEMINI_API_KEY is set
        """
        gemini_key = getattr(settings, 'gemini_api_key', None)
        return bool(gemini_key)

    def _is_gemini_3_model(self, model: str) -> bool:
        """Check if the model is a Gemini 3 model"""
        return any(g3_model in model for g3_model in self.GEMINI_3_MODELS)

    def _call_model(
        self,
        client,
        model_name: str,
        full_prompt: str,
        config_dict: dict,
    ):
        """
        Internal method to call the Gemini API

        Args:
            client: Gemini client instance
            model_name: Model to use
            full_prompt: Combined system + user prompt
            config_dict: Generation configuration dictionary

        Returns:
            API response object
        """
        return client.models.generate_content(
            model=model_name,
            contents=full_prompt,
            config=types.GenerateContentConfig(**config_dict),
        )

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,  # Keep 0.7 for backward compatibility
        max_tokens: int = 1000,
        json_mode: bool = False,
        thinking_level: ThinkingLevel = "high",
        model: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate text using Google Gemini

        Args:
            prompt: User prompt/message
            system_prompt: Optional system prompt for context
            temperature: Sampling temperature (0.0-2.0, default 0.7)
                         Note: Gemini 3 recommends 1.0 for best results
            max_tokens: Maximum tokens to generate
            json_mode: If True, request JSON-formatted response
            thinking_level: "low" for speed, "high" for depth (Gemini 3 only)
            model: Override default model
            **kwargs: Additional parameters

        Returns:
            LLMResponse with generated content
            Note: LLMResponse.model reflects actual model used (may be fallback)

        Raises:
            ValueError: If API key not configured
            NotImplementedError: If SDK not installed
            Exception: If API call fails (after fallback attempt for Gemini 3)
        """
        use_model = model or self.model
        client = self._get_client()

        # Build generation config
        config_dict = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }

        # Add thinking config for Gemini 3 models
        if self._is_gemini_3_model(use_model):
            config_dict["thinking_config"] = types.ThinkingConfig(
                thinking_level=thinking_level
            )

        if json_mode:
            config_dict["response_mime_type"] = "application/json"

        # Combine system prompt with user prompt
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        logger.debug(
            f"[Gemini] Calling API with model={use_model}, "
            f"thinking_level={thinking_level if self._is_gemini_3_model(use_model) else 'N/A'}, "
            f"json_mode={json_mode}, max_tokens={max_tokens}"
        )

        primary_model = use_model
        response = None

        try:
            response = self._call_model(
                client, primary_model, full_prompt, config_dict
            )
        except Exception as e:
            # Only attempt fallback for Gemini 3 models
            if self._is_gemini_3_model(primary_model):
                logger.warning(
                    f"[Gemini] Primary model {primary_model} failed, "
                    f"falling back to {FALLBACK_MODEL}",
                    extra={
                        "operation": "llm_generate",
                        "provider": self.provider_name,
                        "primary_model": primary_model,
                        "fallback_model": FALLBACK_MODEL,
                        "error": str(e),
                    },
                )

                # Build fallback config without thinking_config
                fallback_config = dict(config_dict)
                fallback_config.pop("thinking_config", None)

                try:
                    response = self._call_model(
                        client, FALLBACK_MODEL, full_prompt, fallback_config
                    )
                    # Update use_model to reflect actual model used
                    use_model = FALLBACK_MODEL
                except Exception as fallback_err:
                    logger.error(
                        f"[Gemini] Fallback to {FALLBACK_MODEL} also failed",
                        extra={
                            "operation": "llm_generate",
                            "provider": self.provider_name,
                            "primary_model": primary_model,
                            "fallback_model": FALLBACK_MODEL,
                            "error": str(fallback_err),
                        },
                    )
                    raise fallback_err
            else:
                # Non-Gemini-3 model: no fallback, re-raise original error
                logger.error(
                    f"[Gemini] API call failed: {e}",
                    extra={
                        "operation": "llm_generate",
                        "provider": self.provider_name,
                        "model": use_model,
                        "error": str(e)
                    }
                )
                raise

        content = response.text if response.text else ""

        # Extract usage metadata
        usage = None
        if hasattr(response, 'usage_metadata') and response.usage_metadata:
            usage = {
                "prompt_tokens": getattr(
                    response.usage_metadata, 'prompt_token_count', 0
                ),
                "completion_tokens": getattr(
                    response.usage_metadata, 'candidates_token_count', 0
                ),
                "total_tokens": getattr(
                    response.usage_metadata, 'total_token_count', 0
                )
            }

        llm_response = LLMResponse(
            content=content,
            model=use_model,  # Reflects actual model used (may be fallback)
            provider=self.provider_name,
            usage=usage,
            raw_response=response
        )
        self._log_generation(prompt=full_prompt, response=llm_response)
        return llm_response
