"""
SiliconFlow LLM Provider implementation

Provides Qwen model support via SiliconFlow API for MorningAI Orchestrator.
Uses OpenAI-compatible interface for seamless integration.

Supports:
- Qwen/Qwen2.5-72B-Instruct (default, highest capability)
- Qwen/Qwen2.5-32B-Instruct (balanced performance)
- Qwen/Qwen2.5-14B-Instruct (cost-effective)
- Qwen/Qwen2.5-7B-Instruct (fastest, lowest cost)

Environment Variables:
- SILICONFLOW_API_KEY: SiliconFlow API key

Reference:
- EPIC #2594: Qwen3 Provider Integration
- Ticket 1: Provider Adapters
"""
import logging
from typing import Optional, Dict, Any

from common.config.settings import settings
from .base import BaseLLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class SiliconFlowProvider(BaseLLMProvider):
    """
    SiliconFlow provider using OpenAI-compatible interface

    Supports Qwen models via SiliconFlow API with OpenAI SDK compatibility.

    Features:
    - JSON mode support via response_format
    - Configurable temperature and max_tokens
    - Token usage tracking
    - Automatic error handling with detailed logging
    - Cost-effective alternative to AliCloud DashScope
    """

    provider_name = "siliconflow"
    default_model = "Qwen/Qwen2.5-72B-Instruct"

    SUPPORTED_MODELS = [
        "Qwen/Qwen2.5-72B-Instruct",
        "Qwen/Qwen2.5-32B-Instruct",
        "Qwen/Qwen2.5-14B-Instruct",
        "Qwen/Qwen2.5-7B-Instruct",
    ]

    def __init__(self, model: Optional[str] = None):
        """
        Initialize SiliconFlow provider

        Args:
            model: Model to use (default: Qwen/Qwen2.5-72B-Instruct)
        """
        self.model = model or self.default_model
        self._client = None

    @property
    def client(self):
        """Lazy initialization of OpenAI client with SiliconFlow base URL"""
        if self._client is None:
            if not self.is_available():
                raise ValueError(
                    "SiliconFlow API key not configured. "
                    "Please set SILICONFLOW_API_KEY environment variable."
                )
            from openai import OpenAI
            self._client = OpenAI(
                api_key=settings.siliconflow_api_key,
                base_url=settings.siliconflow_base_url
            )
        return self._client

    def is_available(self) -> bool:
        """Check if SiliconFlow API key is configured"""
        return bool(settings.siliconflow_api_key)

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        json_mode: bool = False,
        model: Optional[str] = None,
        timeout: int = 60,
        **kwargs
    ) -> LLMResponse:
        """
        Generate text using SiliconFlow Qwen models

        Args:
            prompt: User prompt/message
            system_prompt: Optional system prompt for context
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            json_mode: If True, request JSON-formatted response
            model: Override default model
            timeout: Request timeout in seconds (default: 60)
            **kwargs: Additional API parameters
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
            raise ValueError(
                "SiliconFlow API key not configured. "
                "Please set SILICONFLOW_API_KEY environment variable."
            )

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
            f"[SiliconFlow] Calling API with model={use_model}, "
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

            llm_response = LLMResponse(
                content=content,
                model=use_model,
                provider=self.provider_name,
                usage=usage,
                raw_response=response
            )
            self._log_generation(prompt=prompt, response=llm_response)
            return llm_response

        except Exception as e:
            logger.error(
                f"[SiliconFlow] API call failed: {e}",
                extra={
                    "operation": "llm_generate",
                    "provider": self.provider_name,
                    "model": use_model,
                    "error": str(e)
                }
            )
            raise
