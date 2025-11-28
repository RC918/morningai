"""
Google Gemini LLM Provider implementation (Staging)

Provides Gemini Pro support for MorningAI Orchestrator.
This is a staging implementation for Phase 2 Extra.
"""
import logging
from typing import Optional

from common.config.settings import settings
from .base import BaseLLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class GeminiProvider(BaseLLMProvider):
    """
    Google Gemini provider implementation (Staging)

    Supports:
    - gemini-pro (default)
    - gemini-pro-vision (future)

    Note: This is a staging implementation. Full production support
    will be added in Phase 2 Extra after validation.

    Environment Variables:
    - GEMINI_API_KEY: Google AI API key
    """

    provider_name = "gemini"
    default_model = "gemini-pro"

    def __init__(self, model: Optional[str] = None):
        """
        Initialize Gemini provider

        Args:
            model: Model to use (default: gemini-pro)
        """
        self.model = model or self.default_model
        self._genai = None
        self._configured = False

    def _get_genai(self):
        """Lazy initialization of Gemini SDK"""
        if self._genai is None:
            try:
                import google.generativeai as genai
                self._genai = genai
            except ImportError:
                raise NotImplementedError(
                    "Gemini SDK not installed. "
                    "Install with: pip install google-generativeai"
                )
        if not self._configured:
            if not self.is_available():
                raise ValueError(
                    "Gemini API key not configured. "
                    "Set GEMINI_API_KEY environment variable."
                )
            gemini_key = getattr(settings, 'gemini_api_key', None)
            self._genai.configure(api_key=gemini_key)
            self._configured = True
        return self._genai

    def is_available(self) -> bool:
        """
        Check if Gemini API key is configured

        Returns:
            True if GEMINI_API_KEY is set
        """
        gemini_key = getattr(settings, 'gemini_api_key', None)
        return bool(gemini_key)

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        json_mode: bool = False,
        model: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate text using Google Gemini

        Args:
            prompt: User prompt/message
            system_prompt: Optional system prompt for context
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            json_mode: If True, request JSON-formatted response
            model: Override default model
            **kwargs: Additional Gemini API parameters

        Returns:
            LLMResponse with generated content

        Raises:
            ValueError: If API key not configured
            NotImplementedError: If Gemini SDK not installed
            Exception: If API call fails
        """
        use_model = model or self.model
        genai = self._get_genai()

        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }

        if json_mode:
            generation_config["response_mime_type"] = "application/json"

        gemini_model = genai.GenerativeModel(
            model_name=use_model,
            generation_config=generation_config
        )

        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        logger.debug(
            f"[Gemini] Calling API with model={use_model}, "
            f"json_mode={json_mode}, max_tokens={max_tokens}"
        )

        try:
            response = gemini_model.generate_content(full_prompt)

            content = response.text if response.text else ""

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
                model=use_model,
                provider=self.provider_name,
                usage=usage,
                raw_response=response
            )
            self._log_generation(prompt=full_prompt, response=llm_response)
            return llm_response

        except Exception as e:
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
