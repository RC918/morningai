"""
Pre-Authentication Token Management

Handles temporary login tokens (tmp_login_token) used for 2FA enrollment and challenge flows.
These tokens are issued after successful first-factor authentication (email/password)
and are valid for 5 minutes with single-use enforcement via Redis.

Security Features:
- Short-lived (5 minutes)
- Single-use enforcement via Redis jti tracking
- Rate limiting per jti and user_id
- Automatic cleanup on success or expiry
"""

import os
import uuid
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Literal
import jwt
import redis.exceptions

from .redis_client import get_redis_client
from common.config.settings import settings

logger = logging.getLogger(__name__)

PRE_AUTH_TOKEN_EXPIRY_MINUTES = 5
MAX_ATTEMPTS_PER_TOKEN = 5
REDIS_KEY_PREFIX = settings.redis_key_prefix or "morningai"


class PreAuthTokenManager:
    """Manages pre-authentication tokens for 2FA flows"""

    def __init__(self):
        self._redis_client = None  # Lazy initialization
        
        secret = self._resolve_jwt_secret()
        self.jwt_secret = secret if secret is not None else "test-secret-key-for-testing"

        from src.services.auth_service import is_production
        if is_production():
            if not self.jwt_secret or self.jwt_secret == "test-secret-key-for-testing":
                raise RuntimeError(
                    "JWT_SECRET_KEY must be set to a secure value in production environment. "
                    "The default test key is not allowed."
                )
    
    def _resolve_jwt_secret(self) -> Optional[str]:
        """Resolve JWT secret with proper precedence for test compatibility
        
        Precedence: os.environ → app.config → settings
        This ensures pytest's monkeypatch.setenv() takes effect even when Flask app context exists.
        """
        if "JWT_SECRET_KEY" in os.environ:
            return os.environ["JWT_SECRET_KEY"]
        
        try:
            from flask import current_app
            if current_app:
                secret = current_app.config.get("JWT_SECRET_KEY")
                if secret is not None:
                    return secret
        except Exception:
            pass
        
        return settings.jwt_secret_key
    
    @property
    def redis_client(self):
        """Lazy initialization of Redis client"""
        if self._redis_client is None:
            self._redis_client = get_redis_client()
        return self._redis_client

    def generate_token(
        self, user_id: str, email: str, scope: Literal["enroll", "challenge"]
    ) -> str:
        """
        Generate a pre-authentication token.

        Args:
            user_id: User ID
            email: User email
            scope: Token scope ('enroll' for first-time setup, 'challenge' for login)

        Returns:
            JWT token string
        """
        jti = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        expiry = now + timedelta(minutes=PRE_AUTH_TOKEN_EXPIRY_MINUTES)

        payload = {
            "pre_auth": True,
            "scope": scope,
            "user_id": user_id,
            "email": email,
            "jti": jti,
            "iat": now,
            "exp": expiry,
        }

        token = jwt.encode(payload, self.jwt_secret, algorithm="HS256")

        redis_key = f"{REDIS_KEY_PREFIX}:pre_auth:jti:{jti}"
        token_data = {
            "user_id": user_id,
            "email": email,
            "scope": scope,
            "issued_at": now.isoformat(),
            "attempts": "0",
            "consumed": "False",
        }

        self.redis_client.hset(redis_key, mapping=token_data)
        self.redis_client.expire(redis_key, PRE_AUTH_TOKEN_EXPIRY_MINUTES * 60)

        logger.info(
            f"Pre-auth token generated for user {user_id}, scope: {scope}, jti: {jti}"
        )

        return token

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify a pre-authentication token.

        Args:
            token: JWT token string

        Returns:
            Token payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])

            if not payload.get("pre_auth"):
                logger.warning("Token is not a pre-auth token")
                return None

            jti = payload.get("jti")
            if not jti:
                logger.warning("Token missing jti claim")
                return None

            redis_key = f"{REDIS_KEY_PREFIX}:pre_auth:jti:{jti}"
            token_data = self.redis_client.hgetall(redis_key)

            if not token_data:
                logger.warning(
                    f"Token jti {jti} not found in Redis (expired or invalid)"
                )
                return None

            if token_data.get("consumed") == "True":
                logger.warning(f"Token jti {jti} already consumed")
                return None

            attempts = int(token_data.get("attempts", 0))
            if attempts >= MAX_ATTEMPTS_PER_TOKEN:
                logger.warning(
                    f"Token jti {jti} exceeded max attempts ({MAX_ATTEMPTS_PER_TOKEN})"
                )
                return None

            return payload

        except jwt.ExpiredSignatureError:
            logger.warning("Pre-auth token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid pre-auth token: {e}")
            return None
        except Exception as e:
            logger.error(f"Error verifying pre-auth token: {e}", exc_info=True)
            return None

    def increment_attempts(self, jti: str) -> int:
        """
        Increment attempt counter for a token.

        Args:
            jti: Token JTI

        Returns:
            New attempt count
        """
        redis_key = f"{REDIS_KEY_PREFIX}:pre_auth:jti:{jti}"
        new_attempts = self.redis_client.hincrby(redis_key, "attempts", 1)
        logger.debug(f"Token jti {jti} attempts: {new_attempts}")
        return new_attempts

    def consume_token(self, jti: str) -> bool:
        """
        Mark a token as consumed (single-use enforcement).

        DEPRECATED: Use consume_token_atomic() for production code.
        This method is kept for backward compatibility but is not atomic.

        Args:
            jti: Token JTI

        Returns:
            True if successfully consumed, False otherwise
        """
        redis_key = f"{REDIS_KEY_PREFIX}:pre_auth:jti:{jti}"

        token_data = self.redis_client.hgetall(redis_key)
        if not token_data:
            logger.warning(f"Cannot consume token jti {jti}: not found")
            return False

        if token_data.get("consumed") == "True":
            logger.warning(f"Token jti {jti} already consumed")
            return False

        self.redis_client.hset(redis_key, "consumed", "True")
        self.redis_client.hset(redis_key, "consumed_at", datetime.now(timezone.utc).isoformat())

        logger.info(f"Token jti {jti} consumed successfully")
        return True

    def consume_token_atomic(self, jti: str, max_retries: int = 3) -> bool:
        """
        Atomically mark a token as consumed using Redis WATCH/MULTI transaction.

        This method provides race-condition-free single-use enforcement by using
        optimistic locking. If two concurrent requests try to consume the same token,
        only one will succeed.

        Args:
            jti: Token JTI
            max_retries: Maximum number of retry attempts on contention (default: 3)

        Returns:
            True if successfully consumed (first use), False if already consumed or not found
        """
        redis_key = f"{REDIS_KEY_PREFIX}:pre_auth:jti:{jti}"
        now_iso = datetime.now(timezone.utc).isoformat()

        for attempt in range(max_retries):
            pipeline = self.redis_client.pipeline()
            try:
                pipeline.watch(redis_key)

                token_data = pipeline.hgetall(redis_key)
                if not token_data:
                    pipeline.unwatch()
                    logger.warning(f"Cannot consume token jti {jti}: not found")
                    return False

                consumed = token_data.get("consumed")
                if str(consumed) in ("True", "1"):
                    pipeline.unwatch()
                    logger.warning(f"Token jti {jti} already consumed")
                    return False

                ttl = pipeline.ttl(redis_key)
                
                pipeline.multi()
                pipeline.hset(
                    redis_key, mapping={"consumed": "True", "consumed_at": now_iso}
                )
                
                if ttl > 0:
                    pipeline.expire(redis_key, ttl)
                
                pipeline.execute()

                logger.info(f"Token jti {jti} consumed successfully (atomic), TTL preserved: {ttl}s")
                return True

            except redis.exceptions.WatchError:
                logger.debug(
                    f"Contention consuming token jti {jti}, attempt {attempt + 1}/{max_retries}"
                )
                continue
            finally:
                try:
                    pipeline.reset()
                except Exception:
                    pass

        logger.warning(
            f"Failed to consume token jti {jti} after {max_retries} attempts due to contention"
        )
        return False

    def get_token_info(self, jti: str) -> Optional[Dict[str, Any]]:
        """
        Get token information from Redis.

        Args:
            jti: Token JTI

        Returns:
            Token data dict or None
        """
        redis_key = f"{REDIS_KEY_PREFIX}:pre_auth:jti:{jti}"
        token_data = self.redis_client.hgetall(redis_key)
        return token_data if token_data else None

    def revoke_token(self, jti: str) -> bool:
        """
        Revoke a token (delete from Redis).

        Args:
            jti: Token JTI

        Returns:
            True if revoked, False if not found
        """
        redis_key = f"{REDIS_KEY_PREFIX}:pre_auth:jti:{jti}"
        deleted = self.redis_client.delete(redis_key)

        if deleted:
            logger.info(f"Token jti {jti} revoked")
        else:
            logger.warning(f"Token jti {jti} not found for revocation")

        return bool(deleted)


_pre_auth_manager: Optional[PreAuthTokenManager] = None


def get_pre_auth_manager() -> PreAuthTokenManager:
    """Get or create PreAuthTokenManager singleton"""
    global _pre_auth_manager
    if _pre_auth_manager is None:
        _pre_auth_manager = PreAuthTokenManager()
    return _pre_auth_manager
