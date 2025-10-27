#!/usr/bin/env python3
"""
Knowledge Graph Manager - Core manager for code knowledge graph
Phase 1 Week 5: Knowledge Graph System
"""
import logging
import os
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import psycopg2
from psycopg2 import extras, pool
from openai import OpenAI

from agents.dev_agent.knowledge_graph.db_schema import QUERIES
from agents.dev_agent.knowledge_graph.embeddings_cache import EmbeddingsCache
from agents.dev_agent.error_handler import ErrorCode, create_error, create_success

logger = logging.getLogger(__name__)


class KnowledgeGraphManager:
    """Manages code knowledge graph with embeddings and patterns"""

    MAX_REQUESTS_PER_MINUTE = 500
    MAX_TOKENS_PER_MINUTE = 1_000_000

    EMBEDDING_MODEL = "text-embedding-3-small"
    EMBEDDING_DIMENSIONS = 1536
    COST_PER_1K_TOKENS = 0.00002

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

        Args:
            supabase_url: Supabase PostgreSQL URL
            supabase_password: Database password
            openai_api_key: OpenAI API key
            enable_cache: Whether to enable Redis cache
            max_daily_cost: Maximum daily cost in USD (default from env or None)
        """
        self.supabase_url = supabase_url or os.getenv('SUPABASE_URL')
        self.supabase_password = supabase_password or os.getenv(
            'SUPABASE_DB_PASSWORD')
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')

        self.max_daily_cost = max_daily_cost or (
            float(os.getenv('OPENAI_MAX_DAILY_COST', '0')) or None
        )

        self.db_pool = None
        self.cache = EmbeddingsCache() if enable_cache else None
        self.openai_client = None

        self.request_times: List[float] = []
        self.token_usage: List[Tuple[float, int]] = []

        if self.openai_api_key:
            self.openai_client = OpenAI(api_key=self.openai_api_key)
            logger.info("OpenAI API key configured")
        else:
            logger.warning(
                "OpenAI API key not configured, embeddings will not work")

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

    def generate_embedding(
            self, content: str, max_retries: int = 3) -> Dict[str, Any]:
        """
        Generate embedding for code content with caching and retry logic

        Args:
            content: Code content to embed
            max_retries: Maximum number of retry attempts

        Returns:
            Dict with success status and embedding vector
        """
        if not self.openai_api_key:
            return create_error(
                ErrorCode.MISSING_CREDENTIALS,
                "OpenAI API key not configured",
                hint="Set OPENAI_API_KEY environment variable"
            )

        cost_limit_error = self._check_daily_cost_limit()
        if cost_limit_error:
            return cost_limit_error

        if self.cache:
            cached_embedding = self.cache.get(content, self.EMBEDDING_MODEL)
            if cached_embedding:
                return create_success(
                    {'embedding': cached_embedding, 'cached': True})

        import tiktoken
        try:
            encoding = tiktoken.encoding_for_model(self.EMBEDDING_MODEL)
            tokens = encoding.encode(content)
            token_count = len(tokens)
        except Exception:
            token_count = len(content) // 4

        for attempt in range(max_retries):
            try:
                self._check_rate_limit(token_count)

                response = self.openai_client.embeddings.create(
                    model=self.EMBEDDING_MODEL,
                    input=content,
                    encoding_format="float"
                )

                embedding = response.data[0].embedding

                cost = (token_count / 1000) * self.COST_PER_1K_TOKENS

                if self.cache:
                    self.cache.set(content, embedding, self.EMBEDDING_MODEL)
                    self.cache.record_api_call(token_count, cost)

                logger.debug(f"Generated embedding: {token_count} tokens, ${cost:.6f}")

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
                            f"OpenAI rate limit exceeded: {error_str}"
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

    def health_check(self) -> Dict[str, Any]:
        """Check system health"""
        health = {
            'timestamp': datetime.now().isoformat(),
            'openai_configured': self.openai_api_key is not None,
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
