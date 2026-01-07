"""
Unified Embedding Client for MorningAI Orchestrator

Provides a single interface for generating text embeddings.
This abstraction layer enables:
- Easy provider switching via configuration
- Consistent API across providers
- Centralized logging and monitoring

Usage:
    from llm.embedding_client import EmbeddingClient, get_embedding_client

    # Default provider (auto-selects based on available API keys)
    client = get_embedding_client()
    embedding = client.embed("Some text to embed")

    # Specify provider explicitly
    client = get_embedding_client(provider="alicloud")
    embedding = client.embed("Text")

Supported Providers:
- alicloud: AliCloud DashScope (text-embedding-v3, OpenAI-compatible)
- openai: OpenAI (text-embedding-3-small)

Provider Selection (auto mode):
1. alicloud (if DASHSCOPE_API_KEY is set)
2. openai (if OPENAI_API_KEY is set)

Related Issues:
- #1812: LLMProvider abstraction layer
- Sentry a23d853a: OpenAI billing_not_active error - add AliCloud fallback
"""
import logging
from functools import lru_cache
from typing import Optional, List

from common.config.settings import settings

logger = logging.getLogger(__name__)

DEFAULT_EMBEDDING_MODEL_OPENAI = "text-embedding-3-small"
DEFAULT_EMBEDDING_MODEL_ALICLOUD = "text-embedding-v3"

# Provider-specific dimension defaults
# - OpenAI text-embedding-3-small: supports up to 1536 dimensions
# - AliCloud text-embedding-v3: supports only [512, 768, 1024]
DEFAULT_EMBEDDING_DIMENSIONS_OPENAI = 1536
DEFAULT_EMBEDDING_DIMENSIONS_ALICLOUD = 1024

# Legacy constant for backward compatibility (used when provider is unknown)
DEFAULT_EMBEDDING_DIMENSIONS = 1536

_EMBEDDING_PROVIDER_PRIORITY = ["alicloud", "openai"]


def _resolve_provider(provider: str) -> str:
    """
    Resolve 'auto' provider to actual provider based on available API keys.

    Priority order: alicloud > openai (to avoid OpenAI billing issues)

    Args:
        provider: Provider name or 'auto'

    Returns:
        Resolved provider name
    """
    if provider != "auto":
        return provider

    for p in _EMBEDDING_PROVIDER_PRIORITY:
        if p == "alicloud" and settings.dashscope_api_key:
            logger.info(
                "[EmbeddingClient] Auto-selected provider=alicloud "
                "(DASHSCOPE_API_KEY available)"
            )
            return "alicloud"
        elif p == "openai" and settings.openai_api_key:
            logger.info(
                "[EmbeddingClient] Auto-selected provider=openai "
                "(OPENAI_API_KEY available)"
            )
            return "openai"

    logger.warning(
        "[EmbeddingClient] No embedding API keys available, defaulting to openai"
    )
    return "openai"


def _get_default_model(provider: str) -> str:
    """Get default embedding model for provider."""
    if provider == "alicloud":
        return DEFAULT_EMBEDDING_MODEL_ALICLOUD
    return DEFAULT_EMBEDDING_MODEL_OPENAI


def _get_default_dimensions(provider: str) -> int:
    """Get default embedding dimensions for provider.

    Different providers support different dimension ranges:
    - OpenAI text-embedding-3-small: supports up to 1536 dimensions
    - AliCloud text-embedding-v3: supports only [512, 768, 1024]

    Args:
        provider: Provider name

    Returns:
        Default dimensions for the provider
    """
    if provider == "alicloud":
        return DEFAULT_EMBEDDING_DIMENSIONS_ALICLOUD
    return DEFAULT_EMBEDDING_DIMENSIONS_OPENAI


class EmbeddingClient:
    """
    Unified embedding client supporting multiple providers.

    Supports:
    - alicloud: AliCloud DashScope (text-embedding-v3, OpenAI-compatible)
    - openai: OpenAI (text-embedding-3-small)

    Provider selection in 'auto' mode prioritizes alicloud over openai
    to avoid OpenAI billing issues (Sentry a23d853a).
    """

    def __init__(
        self,
        model: Optional[str] = None,
        provider: str = "auto",
        dimensions: Optional[int] = None
    ):
        """
        Initialize embedding client.

        Args:
            model: Embedding model to use (auto-selected based on provider if None)
            provider: Embedding provider ("auto", "alicloud", "openai").
                      Note: When called via get_embedding_client(), provider is
                      already resolved. Direct instantiation will still resolve.
            dimensions: Embedding dimensions (auto-selected based on provider if None)
                        - OpenAI: 1536 (text-embedding-3-small default)
                        - AliCloud: 1024 (text-embedding-v3 max supported)
        """
        self._provider = provider if provider != "auto" else _resolve_provider(provider)
        self._model = model or _get_default_model(self._provider)
        self._dimensions = dimensions if dimensions is not None else _get_default_dimensions(self._provider)
        self._client = None

        logger.info(
            "[EmbeddingClient] Initialized with provider=%s model=%s dimensions=%d",
            self._provider,
            self._model,
            self._dimensions
        )

    def _create_client(self):
        """Create provider-specific client using OpenAI SDK"""
        from openai import OpenAI

        if self._provider == "alicloud":
            if not settings.dashscope_api_key:
                return None
            return OpenAI(
                api_key=settings.dashscope_api_key,
                base_url=settings.dashscope_base_url
            )
        elif self._provider == "openai":
            if not settings.openai_api_key:
                return None
            return OpenAI(api_key=settings.openai_api_key)
        else:
            raise ValueError("Unsupported embedding provider: %s" % self._provider)

    @property
    def client(self):
        """Lazy initialization of provider client"""
        if self._client is None:
            self._client = self._create_client()
            if self._client is None:
                raise ValueError(
                    "API key not configured for %s embeddings" % self._provider
                )
        return self._client

    @property
    def model(self) -> str:
        """Get the current embedding model name"""
        return self._model

    @property
    def provider_name(self) -> str:
        """Get the current provider name"""
        return self._provider

    @property
    def dimensions(self) -> int:
        """Get the embedding dimensions"""
        return self._dimensions

    def is_available(self) -> bool:
        """Check if embedding generation is available"""
        if self._provider == "alicloud":
            return bool(settings.dashscope_api_key)
        elif self._provider == "openai":
            return bool(settings.openai_api_key)
        return False

    def embed(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding vector for text.

        Args:
            text: Text to embed

        Returns:
            List of floats (embedding vector) or None if failed
        """
        if not self.is_available():
            logger.debug(
                "[EmbeddingClient] %s API key not available",
                self._provider
            )
            return None

        try:
            params = {
                "model": self._model,
                "input": text,
                "dimensions": self._dimensions
            }

            response = self.client.embeddings.create(**params)
            embedding = response.data[0].embedding

            logger.debug(
                "[EmbeddingClient] Generated embedding",
                extra={
                    "operation": "embed",
                    "provider": self._provider,
                    "model": self._model,
                    "text_length": len(text),
                    "embedding_dimensions": len(embedding)
                }
            )

            return embedding

        except Exception as e:
            logger.warning(
                "[EmbeddingClient] Failed to generate embedding: %s",
                e
            )
            return None

    def embed_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors (or None for failed items)
        """
        if not self.is_available():
            logger.debug(
                "[EmbeddingClient] %s API key not available",
                self._provider
            )
            return [None] * len(texts)

        try:
            params = {
                "model": self._model,
                "input": texts,
                "dimensions": self._dimensions
            }

            response = self.client.embeddings.create(**params)

            embeddings = [item.embedding for item in response.data]

            logger.debug(
                "[EmbeddingClient] Generated batch embeddings",
                extra={
                    "operation": "embed_batch",
                    "provider": self._provider,
                    "model": self._model,
                    "batch_size": len(texts),
                    "embedding_dimensions": len(embeddings[0]) if embeddings else 0
                }
            )

            return embeddings

        except Exception as e:
            logger.warning(
                "[EmbeddingClient] Failed to generate batch embeddings: %s",
                e
            )
            return [None] * len(texts)


@lru_cache(maxsize=None)
def _get_cached_client(
    resolved_provider: str,
    model: Optional[str],
    dimensions: int
) -> EmbeddingClient:
    """
    Internal cached client factory. Cache is keyed on resolved provider,
    model, and dimensions to ensure correct behavior when API keys change.

    Args:
        resolved_provider: Already-resolved provider name (not "auto")
        model: Embedding model to use
        dimensions: Embedding dimensions

    Returns:
        EmbeddingClient instance
    """
    return EmbeddingClient(
        model=model,
        provider=resolved_provider,
        dimensions=dimensions
    )


def get_embedding_client(
    model: Optional[str] = None,
    provider: str = "auto",
    dimensions: Optional[int] = None
) -> EmbeddingClient:
    """
    Get an EmbeddingClient instance (thread-safe singleton per resolved provider/model).

    Provider resolution happens BEFORE caching to ensure correct behavior
    when API keys change at runtime. Each unique (resolved_provider, model, dimensions)
    combination gets its own cached instance.

    Args:
        model: Embedding model to use (auto-selected based on provider if None)
        provider: Embedding provider ("auto", "alicloud", "openai")
        dimensions: Embedding dimensions (auto-selected based on provider if None)
                    - OpenAI: 1536 (text-embedding-3-small default)
                    - AliCloud: 1024 (text-embedding-v3 max supported)

    Returns:
        EmbeddingClient instance
    """
    resolved_provider = _resolve_provider(provider)
    resolved_model = model or _get_default_model(resolved_provider)
    resolved_dimensions = dimensions if dimensions is not None else _get_default_dimensions(resolved_provider)
    return _get_cached_client(resolved_provider, resolved_model, resolved_dimensions)


def embed(text: str) -> Optional[List[float]]:
    """
    Convenience function to generate embedding using default client.

    Args:
        text: Text to embed

    Returns:
        List of floats (embedding vector) or None if failed
    """
    return get_embedding_client().embed(text)
