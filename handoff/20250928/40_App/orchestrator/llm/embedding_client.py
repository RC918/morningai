"""
Unified Embedding Client for MorningAI Orchestrator

Provides a single interface for generating text embeddings.
This abstraction layer enables:
- Easy provider switching via configuration
- Consistent API across providers
- Centralized logging and monitoring

Usage:
    from llm.embedding_client import EmbeddingClient, get_embedding_client

    # Default provider (OpenAI)
    client = get_embedding_client()
    embedding = client.embed("Some text to embed")

    # Specify provider explicitly
    client = get_embedding_client(provider="openai")
    embedding = client.embed("Text")

Related Issues:
- #1812: LLMProvider abstraction layer
"""
import logging
from functools import lru_cache
from typing import Optional, List

from common.config.settings import settings

logger = logging.getLogger(__name__)

DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"


class EmbeddingClient:
    """
    Unified embedding client supporting multiple providers.

    Currently supports:
    - OpenAI text-embedding-3-small (default)

    Future providers (e.g., Gemini) can be added by extending
    the _create_client method with provider-specific logic.
    """

    def __init__(
        self,
        model: Optional[str] = None,
        provider: str = "openai"
    ):
        """
        Initialize embedding client.

        Args:
            model: Embedding model to use (default: text-embedding-3-small)
            provider: Embedding provider ("openai", "gemini")
        """
        self._model = model or DEFAULT_EMBEDDING_MODEL
        self._provider = provider
        self._client = None

        logger.debug(
            "[EmbeddingClient] Initialized with provider=%s model=%s",
            self._provider,
            self._model
        )

    def _create_client(self):
        """Create provider-specific client"""
        if self._provider == "openai":
            if not settings.openai_api_key:
                return None
            from openai import OpenAI
            return OpenAI(api_key=settings.openai_api_key)
        elif self._provider == "gemini":
            raise NotImplementedError("Gemini embeddings not yet supported")
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

    def is_available(self) -> bool:
        """Check if embedding generation is available"""
        if self._provider == "openai":
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
            response = self.client.embeddings.create(
                model=self._model,
                input=text
            )
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
            response = self.client.embeddings.create(
                model=self._model,
                input=texts
            )

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
def get_embedding_client(
    model: Optional[str] = None,
    provider: str = "openai"
) -> EmbeddingClient:
    """
    Get an EmbeddingClient instance (thread-safe singleton per provider/model).

    Uses lru_cache for thread-safe singleton behavior. Each unique
    (provider, model) combination gets its own cached instance.

    Args:
        model: Embedding model to use (default: text-embedding-3-small)
        provider: Embedding provider ("openai", "gemini")

    Returns:
        EmbeddingClient instance
    """
    return EmbeddingClient(model=model, provider=provider)


def embed(text: str) -> Optional[List[float]]:
    """
    Convenience function to generate embedding using default client.

    Args:
        text: Text to embed

    Returns:
        List of floats (embedding vector) or None if failed
    """
    return get_embedding_client().embed(text)
