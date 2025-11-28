"""
OpenAI LLM Provider implementation

Provides GPT-4 and GPT-4-turbo support for MorningAI Orchestrator.
"""
import logging
from typing import Optional, Dict, Any

from common.config.settings import settings
from .base import BaseLLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI GPT-4 provider implementation

    Supports:
    - gpt-4-turbo-preview (default)
    - gpt-4
    - gpt-4-32k
    - gpt-3.5-turbo

    Features:
    - JSON mode support
    - Configurable temperature and max_tokens
    - Token usage tracking
    """

    provider_name = "openai"
    default_model = "gpt-4-turbo-preview"

    def __init__(self, model: Optional[str] = None):
        """
        Initialize OpenAI provider

        Args:
            model: Model to use (default: gpt-4-turbo-preview)
        """
        self.model = model or self.default_model
        self._client = None

    @property
    def client(self):
        """Lazy initialization of OpenAI client"""
        if self._client is None:
            if not self.is_available():
                raise ValueError("OpenAI API key not configured")
            from openai import OpenAI
            self._client = OpenAI(api_key=settings.openai_api_key)
        return self._client

    def is_available(self) -> bool:
        """Check if OpenAI API key is configured"""
        return bool(settings.openai_api_key)

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        json_mode: bool = False,
        model: Optional[str] = None,
        timeout: int = 30,
        **kwargs
    ) -> LLMResponse:
        """
        Generate text using OpenAI GPT-4

        Args:
            prompt: User prompt/message
            system_prompt: Optional system prompt for context
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            json_mode: If True, request JSON-formatted response
            model: Override default model
            timeout: Request timeout in seconds
            **kwargs: Additional OpenAI API parameters
                - top_p: Nucleus sampling parameter
                - frequency_penalty: Repetition penalty
                - presence_penalty: Topic diversity penalty

        Returns:
            LLMResponse with generated content

        Raises:
            ValueError: If API key not configured
            Exception: If API call fails
        """
        if not self.is_available():
            raise ValueError("OpenAI API key not configured")

        use_model = model or self.model

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        api_params: Dict[str, Any] = {
            "model": use_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "timeout": timeout
        }

        if json_mode:
            api_params["response_format"] = {"type": "json_object"}

        for key in ["top_p", "frequency_penalty", "presence_penalty"]:
            if key in kwargs:
                api_params[key] = kwargs[key]

        logger.debug(
            f"[OpenAI] Calling API with model={use_model}, "
            f"json_mode={json_mode}, max_tokens={max_tokens}"
        )

        try:
            response = self.client.chat.completions.create(**api_params)

            content = response.choices[0].message.content or ""

            usage = None
            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }

            return LLMResponse(
                content=content,
                model=use_model,
                provider=self.provider_name,
                usage=usage,
                raw_response=response
            )

        except Exception as e:
            logger.error(
                f"[OpenAI] API call failed: {e}",
                extra={
                    "operation": "llm_generate",
                    "provider": self.provider_name,
                    "model": use_model,
                    "error": str(e)
                }
            )
            raise
