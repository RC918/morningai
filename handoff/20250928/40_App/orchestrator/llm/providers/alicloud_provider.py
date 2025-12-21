"""
AliCloud DashScope LLM Provider implementation

Provides Qwen model support via AliCloud DashScope API for MorningAI Orchestrator.
Uses OpenAI-compatible interface for seamless integration.

Supports:
- qwen-max (default, highest capability)
- qwen-plus (balanced performance)
- qwen-turbo (fastest, cost-effective)

Environment Variables:
- DASHSCOPE_API_KEY: AliCloud DashScope API key
- DASHSCOPE_BASE_URL: API endpoint (optional, defaults to international endpoint)

IMPORTANT - Regional Endpoints:
DashScope has TWO different endpoints with region-specific API keys:
- International (default): https://dashscope-intl.aliyuncs.com/compatible-mode/v1
- China:                   https://dashscope.aliyuncs.com/compatible-mode/v1

Your API key is region-specific! A China API key will NOT work with the
International endpoint, and vice versa. Set DASHSCOPE_BASE_URL to match
your API key's region.

Get API keys:
- China: https://dashscope.console.aliyun.com/apiKey
- International: https://dashscope-intl.console.aliyun.com/apiKey

Reference:
- EPIC #2594: Qwen3 Provider Integration
- Ticket 1: Provider Adapters
"""
import logging
from typing import Optional, Dict, Any
from urllib.parse import urlparse

from common.config.settings import settings
from .base import BaseLLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class AliCloudProvider(BaseLLMProvider):
    """
    AliCloud DashScope provider using OpenAI-compatible interface

    Supports Qwen models via DashScope API with OpenAI SDK compatibility.

    Features:
    - JSON mode support via response_format
    - Configurable temperature and max_tokens
    - Token usage tracking
    - Automatic error handling with detailed logging
    """

    provider_name = "alicloud"
    default_model = "qwen-max"

    SUPPORTED_MODELS = [
        "qwen-max",
        "qwen-max-latest",
        "qwen-plus",
        "qwen-plus-latest",
        "qwen-turbo",
        "qwen-turbo-latest",
        "qwen3-235b-a22b",  # Qwen3 MoE flagship model
    ]

    def __init__(self, model: Optional[str] = None):
        """
        Initialize AliCloud DashScope provider

        Args:
            model: Model to use (default: qwen-max)
        """
        self.model = model or self.default_model
        self._client = None

    @property
    def client(self):
        """Lazy initialization of OpenAI client with DashScope base URL"""
        if self._client is None:
            if not self.is_available():
                raise ValueError(
                    "DashScope API key not configured. "
                    "Please set DASHSCOPE_API_KEY environment variable."
                )
            from openai import OpenAI

            base_url = settings.dashscope_base_url

            # Determine region from hostname for logging purposes
            region = "unknown"
            if isinstance(base_url, str):
                parsed = urlparse(base_url)
                hostname = parsed.hostname
                if not hostname and base_url:
                    parsed = urlparse("https://" + base_url)
                    hostname = parsed.hostname

                if hostname == "dashscope-intl.aliyuncs.com":
                    region = "international"
                elif hostname == "dashscope.aliyuncs.com":
                    region = "china"
                else:
                    region = "custom"

            logger.info(
                f"[AliCloud] Initializing DashScope client with {region} endpoint",
                extra={
                    "operation": "alicloud_client_init",
                    "base_url": base_url,
                    "region": region,
                    "hint": "API keys are region-specific. If auth fails, verify endpoint matches key region."
                }
            )

            self._client = OpenAI(
                api_key=settings.dashscope_api_key,
                base_url=base_url
            )
        return self._client

    def is_available(self) -> bool:
        """Check if DashScope API key is configured"""
        return bool(settings.dashscope_api_key)

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
        Generate text using AliCloud DashScope Qwen models

        Args:
            prompt: User prompt/message
            system_prompt: Optional system prompt for context
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            json_mode: If True, request JSON-formatted response
            model: Override default model
            timeout: Request timeout in seconds (default: 60, higher for Qwen)
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
                "DashScope API key not configured. "
                "Please set DASHSCOPE_API_KEY environment variable."
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
            f"[AliCloud] Calling DashScope API with model={use_model}, "
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
                f"[AliCloud] DashScope API call failed: {e}",
                extra={
                    "operation": "llm_generate",
                    "provider": self.provider_name,
                    "model": use_model,
                    "error": str(e)
                }
            )
            raise
