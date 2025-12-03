"""
Unified Embedding Client for MorningAI Orchestrator

Provides a single interface for generating text embeddings.
This abstraction layer enables:
- Easy provider switching via configuration
- Consistent API across providers
- Centralized logging and monitoring

Usage:
    from llm.embedding_client import EmbeddingClient

    # Default provider (OpenAI)
    client = EmbeddingClient()
    embedding = client.embed("Some text to embed")

    # Check availability
    if client.is_available():
        embedding = client.embed("Text")

Related Issues:
- #1812: LLMProvider abstraction layer
"""
import logging
from typing import Optional, List

from common.config.settings import settings

logger = logging.getLogger(__name__)

DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536


class EmbeddingClient:
    """
    Unified embedding client supporting OpenAI embeddings.

    Currently supports:
    - OpenAI text-embedding-3-small (default)

    Future providers can be added by extending this class
    with provider selection logic similar to LLMClient.
    """

    def __init__(
        self,
        model: Optional[str] = None
    ):
        """
        Initialize embedding client.

        Args:
            model: Embedding model to use (default: text-embedding-3-small)
        """
        self._model = model or DEFAULT_EMBEDDING_MODEL
        self._client = None

        logger.debug(
            f"[EmbeddingClient] Initialized with model={self._model}"
        )

    @property
    def client(self):
        """Lazy initialization of OpenAI client"""
        if self._client is None:
            if not self.is_available():
                raise ValueError("OpenAI API key not configured for embeddings")
            from openai import OpenAI
            self._client = OpenAI(api_key=settings.openai_api_key)
        return self._client

    @property
    def model(self) -> str:
        """Get the current embedding model name"""
        return self._model

    def is_available(self) -> bool:
        """Check if embedding generation is available"""
        return bool(settings.openai_api_key)

    def embed(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding vector for text.

        Args:
            text: Text to embed

        Returns:
            List of floats (embedding vector) or None if failed
        """
        if not self.is_available():
            logger.debug("[EmbeddingClient] OpenAI API key not available")
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
                    "model": self._model,
                    "text_length": len(text),
                    "embedding_dimensions": len(embedding)
                }
            )

            return embedding

        except Exception as e:
            logger.warning(f"[EmbeddingClient] Failed to generate embedding: {e}")
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
            logger.debug("[EmbeddingClient] OpenAI API key not available")
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
                    "model": self._model,
                    "batch_size": len(texts),
                    "embedding_dimensions": len(embeddings[0]) if embeddings else 0
                }
            )

            return embeddings

        except Exception as e:
            logger.warning(f"[EmbeddingClient] Failed to generate batch embeddings: {e}")
            return [None] * len(texts)


_default_embedding_client: Optional[EmbeddingClient] = None


def get_embedding_client() -> EmbeddingClient:
    """
    Get a default EmbeddingClient instance (singleton).

    Returns:
        EmbeddingClient instance
    """
    global _default_embedding_client
    if _default_embedding_client is None:
        _default_embedding_client = EmbeddingClient()
    return _default_embedding_client


def embed(text: str) -> Optional[List[float]]:
    """
    Convenience function to generate embedding using default client.

    Args:
        text: Text to embed

    Returns:
        List of floats (embedding vector) or None if failed
    """
    return get_embedding_client().embed(text)
