"""
LLM integration module for MorningAI Orchestrator

Provides AI-powered content generation with multiple LLM provider support.

Providers:
- OpenAI GPT-4 (default)
- Google Gemini (staging, Phase 2 Extra)

Usage:
    from llm import LLMClient, EmbeddingClient

    # Text generation
    client = LLMClient()
    response = client.generate("Explain dependency injection")

    # Embeddings
    embed_client = EmbeddingClient()
    embedding = embed_client.embed("Some text")
"""
from .client import LLMClient, get_client_for_component
from .embedding_client import EmbeddingClient, get_embedding_client, embed
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
    'get_client_for_component',
    'EmbeddingClient',
    'get_embedding_client',
    'embed',
    'BaseLLMProvider',
    'LLMResponse',
    'OpenAIProvider',
    'GeminiProvider',
    'generate_faq_content',
    'generate_fallback_faq',
    'get_cached_or_generate'
]
