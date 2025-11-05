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
from datetime import datetime, timedelta, UTC
from typing import Optional, Dict, Any, Literal
import jwt

from .redis_client import get_redis_client

logger = logging.getLogger(__name__)

PRE_AUTH_TOKEN_EXPIRY_MINUTES = 5
MAX_ATTEMPTS_PER_TOKEN = 5
REDIS_KEY_PREFIX = os.getenv("REDIS_KEY_PREFIX", "morningai")


class PreAuthTokenManager:
    """Manages pre-authentication tokens for 2FA flows"""

    def __init__(self):
        self.redis_client = get_redis_client()
        self.jwt_secret = os.environ.get(
            "JWT_SECRET_KEY", "test-secret-key-for-testing"
        )

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
        now = datetime.now(UTC)
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
            "attempts": 0,
            "consumed": False,
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
        self.redis_client.hset(
            redis_key, "consumed_at", datetime.now(UTC).isoformat()
        )

        logger.info(f"Token jti {jti} consumed successfully")
        return True

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
