"""
Base LLM Provider interface

Defines the contract that all LLM providers must implement.
"""
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """
    Standardized response from LLM providers

    Attributes:
        content: Generated text content
        model: Model used for generation
        provider: Provider name (openai, gemini, etc.)
        usage: Token usage statistics
        raw_response: Original provider response (for debugging)
    """
    content: str
    model: str
    provider: str
    usage: Optional[Dict[str, int]] = None
    raw_response: Optional[Any] = None

    def __post_init__(self):
        if self.usage is None:
            self.usage = {}


class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers

    All LLM providers must implement:
    - generate(): Text generation
    - is_available(): Check if provider is configured
    """

    provider_name: str = "base"

    @abstractmethod
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
        Generate text using the LLM

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
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the provider is properly configured

        Returns:
            True if API key and dependencies are available
        """
        pass

    def get_provider_name(self) -> str:
        """Get the provider name"""
        return self.provider_name

    def _log_generation(
        self,
        prompt: str,
        response: LLMResponse,
        trace_id: Optional[str] = None
    ):
        """Log generation details for monitoring"""
        logger.info(
            f"[{self.provider_name}] Generated response",
            extra={
                "operation": "llm_generate",
                "provider": self.provider_name,
                "model": response.model,
                "prompt_length": len(prompt),
                "response_length": len(response.content),
                "usage": response.usage,
                "trace_id": trace_id
            }
        )
