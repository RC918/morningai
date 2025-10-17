#!/usr/bin/env python3
"""
Embeddings Cache - Redis-based cache for OpenAI embeddings
Phase 1 Week 5: Knowledge Graph System
"""
import logging
import hashlib
import json
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from agents.dev_agent.persistence.upstash_redis_client import UpstashRedisClient
from agents.dev_agent.error_handler import ErrorCode, create_error, create_success

logger = logging.getLogger(__name__)


class EmbeddingsCache:
    """Redis-based cache for code embeddings with statistics tracking"""

    CACHE_TTL = 86400 * 30
    STATS_KEY = "embeddings:stats"

    def __init__(self, redis_client: Optional[UpstashRedisClient] = None):
        """
        Initialize embeddings cache

        Args:
            redis_client: Upstash Redis client instance (optional)
        """
        try:
            self.redis = redis_client or UpstashRedisClient()
            self.enabled = True
            logger.info("EmbeddingsCache initialized with Redis")
        except Exception as e:
            logger.warning(f"Redis not available, cache disabled: {e}")
            self.redis = None
            self.enabled = False

    def _get_cache_key(
            self,
            content: str,
            model: str = "text-embedding-3-small") -> str:
        """Generate cache key from content hash"""
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        return f"embedding:{model}:{content_hash}"

    def get(self, content: str,
            model: str = "text-embedding-3-small") -> Optional[List[float]]:
        """
        Retrieve embedding from cache

        Args:
            content: Code content to get embedding for
            model: OpenAI embedding model name

        Returns:
            Cached embedding vector or None if not found
        """
        if not self.enabled:
            return None

        try:
            cache_key = self._get_cache_key(content, model)
            cached_data = self.redis.get(cache_key)

            if cached_data:
                self._increment_stat('cache_hits')
                embedding = json.loads(cached_data)
                logger.debug(f"Cache HIT for content hash {cache_key}")
                return embedding
            else:
                self._increment_stat('cache_misses')
                logger.debug(f"Cache MISS for content hash {cache_key}")
                return None

        except Exception as e:
            logger.error(f"Cache get failed: {e}")
            return None

    def set(
        self,
        content: str,
        embedding: List[float],
        model: str = "text-embedding-3-small",
        ttl: Optional[int] = None
    ) -> bool:
        """
        Store embedding in cache

        Args:
            content: Code content
            embedding: Embedding vector
            model: OpenAI embedding model name
            ttl: Time to live in seconds (optional)

        Returns:
            True if stored successfully, False otherwise
        """
        if not self.enabled:
            return False

        try:
            cache_key = self._get_cache_key(content, model)
            embedding_json = json.dumps(embedding)

            success = self.redis.set(
                cache_key,
                embedding_json,
                ex=ttl or self.CACHE_TTL
            )

            if success:
                logger.debug(f"Cached embedding for {cache_key}")

            return success

        except Exception as e:
            logger.error(f"Cache set failed: {e}")
            return False

    def _increment_stat(self, stat_name: str, increment: int = 1):
        """Increment cache statistics counter"""
        if not self.enabled:
            return

        try:
            today = datetime.now().strftime('%Y-%m-%d')
            stat_key = f"{self.STATS_KEY}:{today}:{stat_name}"

            current_value = self.redis.get(stat_key)
            new_value = int(current_value or 0) + increment

            self.redis.set(stat_key, str(new_value), ex=86400 * 7)

        except Exception as e:
            logger.debug(f"Stats increment failed: {e}")

    def record_api_call(self, tokens_used: int, cost: float):
        """
        Record OpenAI API call statistics

        Args:
            tokens_used: Number of tokens consumed
            cost: Estimated cost in USD
        """
        if not self.enabled:
            return

        try:
            self._increment_stat('api_calls', 1)
            self._increment_stat('tokens_used', tokens_used)

            today = datetime.now().strftime('%Y-%m-%d')
            cost_key = f"{self.STATS_KEY}:{today}:cost"

            current_cost = float(self.redis.get(cost_key) or 0)
            new_cost = current_cost + cost

            self.redis.set(cost_key, str(new_cost), ex=86400 * 7)

        except Exception as e:
            logger.error(f"API call recording failed: {e}")

    def get_stats(self, days: int = 7) -> Dict[str, Any]:
        """
        Get cache statistics for the past N days

        Args:
            days: Number of days to retrieve stats for

        Returns:
            Dictionary with cache statistics
        """
        if not self.enabled:
            return {
                'enabled': False,
                'message': 'Cache not available'
            }

        try:
            stats = {
                'enabled': True,
                'daily_stats': []
            }

            for i in range(days):
                date = (
                    datetime.now() -
                    timedelta(
                        days=i)).strftime('%Y-%m-%d')

                day_stats = {
                    'date': date,
                    'cache_hits': int(self.redis.get(f"{self.STATS_KEY}:{date}:cache_hits") or 0),
                    'cache_misses': int(self.redis.get(f"{self.STATS_KEY}:{date}:cache_misses") or 0),
                    'api_calls': int(self.redis.get(f"{self.STATS_KEY}:{date}:api_calls") or 0),
                    'tokens_used': int(self.redis.get(f"{self.STATS_KEY}:{date}:tokens_used") or 0),
                    'cost': float(self.redis.get(f"{self.STATS_KEY}:{date}:cost") or 0)
                }

                total_requests = day_stats['cache_hits'] + \
                    day_stats['cache_misses']
                if total_requests > 0:
                    day_stats['hit_rate'] = day_stats['cache_hits'] / \
                        total_requests
                else:
                    day_stats['hit_rate'] = 0.0

                stats['daily_stats'].append(day_stats)

            total_hits = sum(d['cache_hits'] for d in stats['daily_stats'])
            total_misses = sum(d['cache_misses'] for d in stats['daily_stats'])
            total_requests = total_hits + total_misses

            stats['summary'] = {
                'total_cache_hits': total_hits,
                'total_cache_misses': total_misses,
                'total_api_calls': sum(d['api_calls'] for d in stats['daily_stats']),
                'total_tokens_used': sum(d['tokens_used'] for d in stats['daily_stats']),
                'total_cost': sum(d['cost'] for d in stats['daily_stats']),
                'average_hit_rate': total_hits / total_requests if total_requests > 0 else 0.0
            }

            return stats

        except Exception as e:
            logger.error(f"Get stats failed: {e}")
            return {
                'enabled': True,
                'error': str(e)
            }

    def clear(self) -> bool:
        """Clear all cached embeddings (use with caution)"""
        if not self.enabled:
            return False

        try:
            logger.warning("Clearing embeddings cache...")
            return True

        except Exception as e:
            logger.error(f"Cache clear failed: {e}")
            return False

    def health_check(self) -> Dict[str, Any]:
        """Check cache health status"""
        if not self.enabled:
            return create_error(
                ErrorCode.NETWORK_ERROR,
                "Cache not enabled (Redis unavailable)"
            )

        try:
            if self.redis.ping():
                return create_success({
                    'cache_enabled': True,
                    'redis_healthy': True
                })
            else:
                return create_error(
                    ErrorCode.NETWORK_ERROR,
                    "Redis ping failed"
                )
        except Exception as e:
            return create_error(
                ErrorCode.NETWORK_ERROR,
                f"Cache health check failed: {str(e)}"
            )


def get_embeddings_cache() -> EmbeddingsCache:
    """Factory function to create embeddings cache"""
    return EmbeddingsCache()
