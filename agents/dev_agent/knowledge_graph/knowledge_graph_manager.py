#!/usr/bin/env python3
"""
Knowledge Graph Manager - Core manager for code knowledge graph
Phase 1 Week 5: Knowledge Graph System
"""
import logging
import os
import time
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import psycopg2
from psycopg2 import extras, pool

from agents.dev_agent.knowledge_graph.db_schema import QUERIES
from agents.dev_agent.knowledge_graph.embeddings_cache import EmbeddingsCache
from agents.dev_agent.error_handler import ErrorCode, create_error, create_success
from common.config.settings import settings

try:
    from llm.embedding_client import get_embedding_client, EmbeddingClient
except ImportError:
    from handoff.orchestrator.llm.embedding_client import get_embedding_client, EmbeddingClient

logger = logging.getLogger(__name__)


class EmbeddingProvider(str, Enum):
    """
    Standardized embedding provider names for health checks and monitoring.

    Using an enum ensures consistent naming across the codebase and prevents
    breaking changes when provider names are used in external contracts
    (e.g., monitoring dashboards, alerting systems).
    """
    ALICLOUD = "alicloud"
    OPENAI = "openai"
    UNKNOWN = "unknown"

    @classmethod
    def from_string(cls, provider_name: Optional[str]) -> "EmbeddingProvider":
        """Convert provider name string to enum, with fallback to UNKNOWN."""
        if not provider_name:
            return cls.UNKNOWN
        try:
            return cls(provider_name.lower())
        except ValueError:
            return cls.UNKNOWN


# Provider-specific embedding costs per 1K tokens (USD)
# These costs should be updated when provider pricing changes
EMBEDDING_COSTS_PER_1K_TOKENS: Dict[str, Dict[str, float]] = {
    "alicloud": {
        "text-embedding-v3": 0.0007,  # AliCloud DashScope pricing
        "text-embedding-v2": 0.0007,
    },
    "openai": {
        "text-embedding-3-small": 0.00002,  # OpenAI pricing
        "text-embedding-3-large": 0.00013,
        "text-embedding-ada-002": 0.0001,
    },
}

# Default cost when provider/model not found in pricing table
DEFAULT_COST_PER_1K_TOKENS = 0.0001


class KnowledgeGraphManager:
    """Manages code knowledge graph with embeddings and patterns

    EPIC D Fix: Migrated from hardcoded OpenAI to EmbeddingClient abstraction layer.
    This allows KnowledgeGraphManager to use the configured embedding provider
    (e.g., Qwen via alicloud) instead of always using OpenAI. The provider is
    determined by:
    1. Auto-selection based on available API keys (alicloud-first per EPIC #2594)
    2. DASHSCOPE_API_KEY for alicloud, OPENAI_API_KEY for openai
    """

    MAX_REQUESTS_PER_MINUTE = 500
    MAX_TOKENS_PER_MINUTE = 1_000_000

    # EMBEDDING_DIMENSIONS removed - now dynamically determined by EmbeddingClient
    # based on provider (OpenAI: 1536, AliCloud: 1024)

    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_password: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        enable_cache: bool = True,
        max_daily_cost: Optional[float] = None
    ):
        """
        Initialize Knowledge Graph Manager

        EPIC D Fix: Now uses EmbeddingClient which auto-selects provider based on
        available API keys (alicloud-first to avoid OpenAI billing issues).

        Args:
            supabase_url: Supabase PostgreSQL URL
            supabase_password: Database password
            openai_api_key: Deprecated - kept for backward compatibility but ignored.
                           EmbeddingClient uses provider-specific API keys from settings.
            enable_cache: Whether to enable Redis cache
            max_daily_cost: Maximum daily cost in USD (default from env or None)
        """
        self.supabase_url = supabase_url or os.getenv('SUPABASE_URL')
        self.supabase_password = supabase_password or os.getenv(
            'SUPABASE_DB_PASSWORD')

        self.max_daily_cost = max_daily_cost or (
            float(os.getenv('OPENAI_MAX_DAILY_COST', '0')) or None
        )

        self.db_pool = None
        self.cache = EmbeddingsCache() if enable_cache else None
        self._embedding_client: Optional[EmbeddingClient] = None

        self.request_times: List[float] = []
        self.token_usage: List[Tuple[float, int]] = []

        try:
            # Let EmbeddingClient auto-select dimensions based on provider
            # (OpenAI: 1536, AliCloud: 1024)
            self._embedding_client = get_embedding_client()
            logger.info(
                f"[KnowledgeGraphManager] Initialized with embedding provider="
                f"{self._embedding_client.provider_name}, "
                f"model={self._embedding_client.model}, "
                f"dimensions={self._embedding_client.dimensions}"
            )
        except Exception as e:
            logger.warning(
                f"[KnowledgeGraphManager] Failed to initialize embedding client: {e}. "
                "Embeddings will not work."
            )

        if self.supabase_url and self.supabase_password:
            self._init_connection_pool()
        else:
            logger.warning(
                "Database credentials not configured, database operations will not work")

    def _init_connection_pool(self):
        """Initialize PostgreSQL connection pool"""
        try:
            db_url = self.supabase_url.replace(
                'https://', 'postgresql://postgresql:')
            db_url = db_url.replace(
                '.supabase.co', '.supabase.co:5432/postgres')

            if self.supabase_password:
                db_url = db_url.replace('postgresql:', f'postgresql:{self.supabase_password}@')

            self.db_pool = pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=10,
                dsn=db_url
            )

            logger.info("Database connection pool initialized")

        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            self.db_pool = None

    def _get_connection(self):
        """Get database connection from pool"""
        if not self.db_pool:
            raise RuntimeError("Database pool not initialized")
        return self.db_pool.getconn()

    def _return_connection(self, conn):
        """Return database connection to pool"""
        if self.db_pool and conn:
            self.db_pool.putconn(conn)

    def _check_rate_limit(self, tokens: int = 0):
        """Check and enforce OpenAI API rate limits"""
        current_time = time.time()

        self.request_times = [
            t for t in self.request_times if current_time - t < 60]
        self.token_usage = [
            (t, tokens) for t, tokens in self.token_usage if current_time - t < 60]

        if len(self.request_times) >= self.MAX_REQUESTS_PER_MINUTE:
            sleep_time = 60 - (current_time - self.request_times[0])
            if sleep_time > 0:
                logger.warning(f"Rate limit reached, sleeping for {sleep_time:.2f}s")
                time.sleep(sleep_time)

        total_tokens = sum(t for _, t in self.token_usage)
        if total_tokens + tokens > self.MAX_TOKENS_PER_MINUTE:
            sleep_time = 60 - (current_time - self.token_usage[0][0])
            if sleep_time > 0:
                logger.warning(f"Token limit reached, sleeping for {sleep_time:.2f}s")
                time.sleep(sleep_time)

        self.request_times.append(current_time)
        if tokens > 0:
            self.token_usage.append((current_time, tokens))

    def _check_daily_cost_limit(self) -> Optional[Dict[str, Any]]:
        """Check if daily cost limit has been exceeded"""
        if not self.max_daily_cost or not self.cache:
            return None

        stats = self.cache.get_stats(days=1)
        if not stats.get('summary'):
            return None

        daily_cost = stats['summary'].get('total_cost', 0)

        if daily_cost >= self.max_daily_cost:
            return create_error(
                ErrorCode.RATE_LIMIT_EXCEEDED,
                f"Daily cost limit exceeded: ${daily_cost:.4f} >= ${self.max_daily_cost:.4f}",
                hint="Wait until tomorrow or increase OPENAI_MAX_DAILY_COST")

        return None

    def _get_cost_per_1k_tokens(self) -> float:
        """
        Get the cost per 1K tokens for the current embedding provider and model.

        Uses the EMBEDDING_COSTS_PER_1K_TOKENS lookup table for accurate cost
        tracking across different providers. Falls back to DEFAULT_COST_PER_1K_TOKENS
        if the provider/model combination is not found.

        Returns:
            Cost per 1K tokens in USD
        """
        if not self._embedding_client:
            return DEFAULT_COST_PER_1K_TOKENS

        provider = self._embedding_client.provider_name
        model = self._embedding_client.model

        provider_costs = EMBEDDING_COSTS_PER_1K_TOKENS.get(provider, {})
        cost = provider_costs.get(model, DEFAULT_COST_PER_1K_TOKENS)

        if cost == DEFAULT_COST_PER_1K_TOKENS and model not in provider_costs:
            logger.warning(
                f"[KnowledgeGraphManager] Unknown model {model} for provider {provider}, "
                f"using default cost ${DEFAULT_COST_PER_1K_TOKENS}/1K tokens"
            )

        return cost

    def _estimate_token_count(self, content: str) -> int:
        """
        Estimate token count for content using tiktoken when available.

        Uses tiktoken for accurate token counting when the model is supported,
        with a fallback to len(content) // 4 heuristic for unsupported models
        or when tiktoken is not available.

        Args:
            content: Text content to count tokens for

        Returns:
            Estimated token count
        """
        if not self._embedding_client:
            return len(content) // 4

        model = self._embedding_client.model

        try:
            import tiktoken
            try:
                encoding = tiktoken.encoding_for_model(model)
                return len(encoding.encode(content))
            except KeyError:
                # Model not supported by tiktoken, try cl100k_base (GPT-4/3.5 encoding)
                # which is a reasonable approximation for most modern models
                encoding = tiktoken.get_encoding("cl100k_base")
                return len(encoding.encode(content))
        except ImportError:
            # tiktoken not installed, use heuristic
            logger.debug(
                "[KnowledgeGraphManager] tiktoken not available, using len//4 heuristic"
            )
            return len(content) // 4
        except Exception as e:
            # Any other error, fall back to heuristic
            logger.debug(
                f"[KnowledgeGraphManager] Token counting failed ({e}), using len//4 heuristic"
            )
            return len(content) // 4

    def generate_embedding(
            self, content: str, max_retries: int = 3) -> Dict[str, Any]:
        """
        Generate embedding for code content with caching and retry logic

        EPIC D Fix: Now uses EmbeddingClient which auto-selects provider
        (alicloud-first to avoid OpenAI billing issues).

        Args:
            content: Code content to embed
            max_retries: Maximum number of retry attempts

        Returns:
            Dict with success status and embedding vector
        """
        if not self._embedding_client or not self._embedding_client.is_available():
            return create_error(
                ErrorCode.MISSING_CREDENTIALS,
                "Embedding API not configured",
                hint="Set DASHSCOPE_API_KEY or OPENAI_API_KEY environment variable"
            )

        cost_limit_error = self._check_daily_cost_limit()
        if cost_limit_error:
            return cost_limit_error

        embedding_model = self._embedding_client.model
        if self.cache:
            cached_embedding = self.cache.get(content, embedding_model)
            if cached_embedding:
                return create_success(
                    {'embedding': cached_embedding, 'cached': True})

        token_count = self._estimate_token_count(content)
        cost_per_1k = self._get_cost_per_1k_tokens()

        for attempt in range(max_retries):
            try:
                self._check_rate_limit(token_count)

                embedding = self._embedding_client.embed(content)

                if embedding is None:
                    # Return error instead of raising to maintain return type contract
                    return create_error(
                        ErrorCode.EXTERNAL_API_ERROR,
                        "Embedding generation returned None",
                        hint="Check embedding provider configuration and API availability"
                    )

                cost = (token_count / 1000) * cost_per_1k

                if self.cache:
                    self.cache.set(content, embedding, embedding_model)
                    self.cache.record_api_call(token_count, cost)

                logger.debug(
                    f"[KnowledgeGraphManager] Generated embedding: "
                    f"provider={self._embedding_client.provider_name}, "
                    f"{token_count} tokens, ${cost:.6f}"
                )

                return create_success({
                    'embedding': embedding,
                    'tokens': token_count,
                    'cost': cost,
                    'cached': False
                })

            except Exception as e:
                error_str = str(e)
                error_type = type(e).__name__

                if 'rate_limit' in error_str.lower() or 'RateLimitError' in error_type:
                    if attempt < max_retries - 1:
                        sleep_time = 2 ** attempt
                        logger.warning(
                            f"Rate limit hit, retrying in {sleep_time}s...")
                        time.sleep(sleep_time)
                    else:
                        return create_error(
                            ErrorCode.RATE_LIMIT_EXCEEDED,
                            f"Embedding rate limit exceeded: {error_str}"
                        )
                else:
                    logger.error(f"Embedding generation failed: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(1)
                    else:
                        return create_error(
                            ErrorCode.EXTERNAL_API_ERROR,
                            f"Failed to generate embedding: {error_str}"
                        )

        return create_error(
            ErrorCode.EXTERNAL_API_ERROR,
            "Max retries exceeded")

    def store_embedding(
        self,
        file_path: str,
        file_hash: str,
        content_preview: str,
        embedding: List[float],
        language: str,
        tokens_count: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Store code embedding in database"""
        if not self.db_pool:
            return create_error(
                ErrorCode.DATABASE_ERROR,
                "Database not configured"
            )

        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                QUERIES['insert_embedding'],
                (file_path,
                 file_hash,
                 content_preview,
                 embedding,
                 language,
                 tokens_count,
                 metadata or {}))

            embedding_id = cursor.fetchone()[0]
            conn.commit()

            logger.info(
                f"Stored embedding for {file_path} (ID: {embedding_id})")

            return create_success({'embedding_id': embedding_id})

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Failed to store embedding: {e}")
            return create_error(
                ErrorCode.DATABASE_ERROR,
                f"Database insert failed: {str(e)}"
            )
        finally:
            if conn:
                self._return_connection(conn)

    def search_similar_code(
        self,
        query_embedding: List[float],
        language: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Search for similar code using vector similarity"""
        if not self.db_pool:
            return create_error(
                ErrorCode.DATABASE_ERROR,
                "Database not configured"
            )

        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=extras.RealDictCursor)

            cursor.execute(
                QUERIES['search_similar_code'],
                (query_embedding, language, language, query_embedding, limit)
            )

            results = cursor.fetchall()

            return create_success({
                'results': [dict(row) for row in results],
                'count': len(results)
            })

        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            return create_error(
                ErrorCode.DATABASE_ERROR,
                f"Similarity search failed: {str(e)}"
            )
        finally:
            if conn:
                self._return_connection(conn)

    def search_relevant_patterns(
        self,
        goal: str,
        error_context: Optional[str] = None,
        language: Optional[str] = None,
        limit: int = 3
    ) -> Dict[str, Any]:
        """
        Search for relevant code patterns related to a task goal.

        This method is used by the Observer Node to enrich learning context
        with Knowledge Graph patterns. It searches for both bug patterns
        and fix patterns that might be relevant to the current task using
        PostgreSQL full-text search.

        Args:
            goal: The current task goal or error description
            error_context: Optional additional error context
            language: Optional language filter (e.g., 'python', 'javascript')
            limit: Maximum number of patterns to return (default 3)

        Returns:
            Dict with success status and list of relevant patterns
        """
        if not self.db_pool:
            return create_error(
                ErrorCode.DATABASE_ERROR,
                "Database not configured"
            )

        search_text = goal
        if error_context:
            search_text = f"{goal} {error_context}"

        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=extras.RealDictCursor)

            # Use PostgreSQL full-text search to find relevant patterns
            # ts_rank scores how well the document matches the query
            query = """
                SELECT id, pattern_name, pattern_type, pattern_template,
                       frequency, confidence_score, examples, metadata,
                       language,
                       ts_rank(
                           to_tsvector('english', COALESCE(pattern_name, '') || ' ' ||
                                       COALESCE(pattern_template, '')),
                           plainto_tsquery('english', %s)
                       ) AS search_rank
                FROM code_patterns
                WHERE pattern_type IN ('bug_pattern', 'fix_pattern')
                  AND (
                      to_tsvector('english', COALESCE(pattern_name, '') || ' ' ||
                                  COALESCE(pattern_template, ''))
                      @@ plainto_tsquery('english', %s)
                      OR %s = ''
                  )
            """
            params = [search_text, search_text, search_text]

            if language:
                query += " AND language = %s"
                params.append(language)

            query += """
                ORDER BY
                    search_rank DESC,
                    CASE WHEN pattern_type = 'fix_pattern' THEN 0 ELSE 1 END,
                    confidence_score DESC,
                    frequency DESC
                LIMIT %s
            """
            params.append(limit)

            cursor.execute(query, params)
            results = cursor.fetchall()

            patterns = []
            for row in results:
                pattern = dict(row)
                # Remove search_rank from output (internal use only)
                pattern.pop('search_rank', None)
                if pattern.get('examples'):
                    pattern['examples'] = pattern['examples'][:2]
                patterns.append(pattern)

            logger.debug(
                f"Found {len(patterns)} relevant patterns for goal: {goal[:50]}..."
            )

            return create_success({
                'patterns': patterns,
                'count': len(patterns),
                'search_text': search_text[:100]
            })

        except Exception as e:
            logger.error(f"Failed to search relevant patterns: {e}")
            return create_error(
                ErrorCode.DATABASE_ERROR,
                f"Pattern search failed: {str(e)}"
            )
        finally:
            if conn:
                self._return_connection(conn)

    def health_check(self) -> Dict[str, Any]:
        """
        Check system health.

        Returns standardized provider names via EmbeddingProvider enum to ensure
        consistent naming across the codebase and prevent breaking changes when
        provider names are used in external contracts (e.g., monitoring dashboards).
        """
        # Use EmbeddingProvider enum for standardized provider names
        provider_enum = EmbeddingProvider.from_string(
            self._embedding_client.provider_name if self._embedding_client else None
        )

        health = {
            'timestamp': datetime.now().isoformat(),
            'embedding_configured': (
                self._embedding_client is not None and
                self._embedding_client.is_available()
            ),
            # Standardized provider name via enum (prevents contract breakage)
            'embedding_provider': provider_enum.value,
            # Include version for future compatibility
            'health_check_version': '2.0',
            'database_configured': self.db_pool is not None,
            'cache_enabled': self.cache is not None
        }

        if self.db_pool:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute('SELECT 1')
                cursor.fetchone()
                self._return_connection(conn)
                health['database_healthy'] = True
            except Exception as e:
                health['database_healthy'] = False
                health['database_error'] = str(e)

        if self.cache:
            cache_health = self.cache.health_check()
            health['cache_healthy'] = cache_health.get('success', False)

        overall_healthy = (
            health.get(
                'database_healthy',
                False) or not health['database_configured']) and (
            health.get(
                'cache_healthy',
                False) or not health['cache_enabled'])

        if overall_healthy:
            return create_success(health)
        else:
            return create_error(
                ErrorCode.HEALTH_CHECK_FAILED,
                "System health check failed",
                data=health)

    def close(self):
        """Close database connections"""
        if self.db_pool:
            self.db_pool.closeall()
            logger.info("Database connection pool closed")


def get_knowledge_graph_manager() -> KnowledgeGraphManager:
    """Factory function to create Knowledge Graph Manager"""
    return KnowledgeGraphManager()
