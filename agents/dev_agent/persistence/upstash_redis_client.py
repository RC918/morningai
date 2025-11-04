#!/usr/bin/env python3
"""
Upstash Redis REST API Client
Phase 1 Week 4: Redis-based session state caching
"""
import os
import logging
import json
import base64
from typing import Optional, Dict, Any, List
import requests

logger = logging.getLogger(__name__)


class UpstashRedisClient:
    """REST API client for Upstash Redis"""

    def __init__(
        self,
        rest_url: Optional[str] = None,
        rest_token: Optional[str] = None
    ):
        self.rest_url = rest_url or os.getenv('UPSTASH_REDIS_REST_URL')
        self.rest_token = rest_token or os.getenv('UPSTASH_REDIS_REST_TOKEN')

        if not self.rest_url or not self.rest_token:
            raise ValueError(
                "Upstash Redis credentials required: "
                "UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN"
            )

        self.rest_url = self.rest_url.split('\u2028')[0].split('\u2029')[0].split()[0].strip()
        self.rest_token = self.rest_token.split('\u2028')[0].split('\u2029')[0].split()[0].strip()

        self.headers = {
            'Authorization': f'Bearer {self.rest_token}',
            'Content-Type': 'application/json'
        }

    def _request(self, command: List[str]) -> Any:
        """Execute Redis command via REST API"""
        try:
            response = requests.post(
                self.rest_url,
                headers=self.headers,
                json=command,
                timeout=5
            )
            response.raise_for_status()
            result = response.json()
            return result.get('result')
        except requests.RequestException as e:
            logger.error(f"Upstash Redis request failed: {e}")
            raise

    def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """Set key-value with optional expiration (seconds)"""
        try:
            logger.debug(f"SET: key={key[:50]}, value_len={len(value)}, contains_u2028={chr(0x2028) in value}")
            encoded_value = base64.b64encode(value.encode('utf-8')).decode('ascii')
            logger.debug(f"SET: encoded_value_len={len(encoded_value)}, is_ascii={encoded_value.isascii()}")
            if ex:
                self._request(['SET', key, encoded_value, 'EX', str(ex)])
            else:
                self._request(['SET', key, encoded_value])
            return True
        except Exception as e:
            logger.error(f"Redis SET failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def get(self, key: str) -> Optional[str]:
        """Get value by key"""
        try:
            encoded_value = self._request(['GET', key])
            if encoded_value is None:
                return None
            return base64.b64decode(encoded_value.encode('ascii')).decode('utf-8')
        except Exception as e:
            logger.error(f"Redis GET failed: {e}")
            return None

    def delete(self, key: str) -> bool:
        """Delete key"""
        try:
            self._request(['DEL', key])
            return True
        except Exception as e:
            logger.error(f"Redis DEL failed: {e}")
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            result = self._request(['EXISTS', key])
            return result == 1
        except Exception as e:
            logger.error(f"Redis EXISTS failed: {e}")
            return False

    def lpush(self, key: str, *values: str) -> Optional[int]:
        """Push values to head of list"""
        try:
            return self._request(['LPUSH', key, *values])
        except Exception as e:
            logger.error(f"Redis LPUSH failed: {e}")
            return None

    def ltrim(self, key: str, start: int, stop: int) -> bool:
        """Trim list to specified range"""
        try:
            self._request(['LTRIM', key, str(start), str(stop)])
            return True
        except Exception as e:
            logger.error(f"Redis LTRIM failed: {e}")
            return False

    def lrange(self, key: str, start: int, stop: int) -> List[str]:
        """Get list range"""
        try:
            result = self._request(['LRANGE', key, str(start), str(stop)])
            return result or []
        except Exception as e:
            logger.error(f"Redis LRANGE failed: {e}")
            return []

    def hset(self, key: str, field: str, value: str) -> bool:
        """Set hash field"""
        try:
            encoded_value = base64.b64encode(value.encode('utf-8')).decode('ascii')
            self._request(['HSET', key, field, encoded_value])
            return True
        except Exception as e:
            logger.error(f"Redis HSET failed: {e}")
            return False

    def hget(self, key: str, field: str) -> Optional[str]:
        """Get hash field"""
        try:
            encoded_value = self._request(['HGET', key, field])
            if encoded_value is None:
                return None
            return base64.b64decode(encoded_value.encode('ascii')).decode('utf-8')
        except Exception as e:
            logger.error(f"Redis HGET failed: {e}")
            return None

    def hgetall(self, key: str) -> Dict[str, str]:
        """Get all hash fields"""
        try:
            result = self._request(['HGETALL', key])
            if not result:
                return {}
            return {result[i]: result[i + 1] for i in range(0, len(result), 2)}
        except Exception as e:
            logger.error(f"Redis HGETALL failed: {e}")
            return {}

    def expire(self, key: str, seconds: int) -> bool:
        """Set key expiration"""
        try:
            self._request(['EXPIRE', key, str(seconds)])
            return True
        except Exception as e:
            logger.error(f"Redis EXPIRE failed: {e}")
            return False

    def ping(self) -> bool:
        """Test connection"""
        try:
            result = self._request(['PING'])
            return result == 'PONG'
        except Exception as e:
            logger.error(f"Redis PING failed: {e}")
            return False

    def set_json(self, key: str, value: Dict[str, Any], ex: Optional[int] = None) -> bool:
        """Set JSON value"""
        try:
            return self.set(key, json.dumps(value), ex=ex)
        except Exception as e:
            logger.error(f"Redis set_json failed: {e}")
            return False

    def get_json(self, key: str) -> Optional[Dict[str, Any]]:
        """Get JSON value"""
        try:
            value = self.get(key)
            return json.loads(value) if value else None
        except Exception as e:
            logger.error(f"Redis get_json failed: {e}")
            return None


def get_redis_client() -> UpstashRedisClient:
    """Factory function to create Redis client"""
    return UpstashRedisClient()
