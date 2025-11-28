"""
LLM integration module for MorningAI Orchestrator

Provides AI-powered content generation with multiple LLM provider support.

Providers:
- OpenAI GPT-4 (default)
- Google Gemini (staging, Phase 2 Extra)

Usage:
    from llm import LLMClient

    client = LLMClient()
    response = client.generate("Explain dependency injection")
"""
from .client import LLMClient
from .providers import (
    BaseLLMProvider,
    LLMResponse,
    OpenAIProvider,
    GeminiProvider,
)
from .faq_generator import (
    generate_faq_content,
    generate_fallback_faq,
    get_cached_or_generate
)

__all__ = [
    'LLMClient',
    'BaseLLMProvider',
    'LLMResponse',
    'OpenAIProvider',
    'GeminiProvider',
    'generate_faq_content',
    'generate_fallback_faq',
    'get_cached_or_generate'
]
