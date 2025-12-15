"""
Pre-Auth Token utilities for 2FA authentication flow.

**DEPRECATED**: This module is deprecated in favor of pre_auth_token.py which uses
JWT-based tokens with better security features including:
- TTL preservation on token consumption
- Scope-based access control (enroll vs challenge)
- Atomic token consumption with race condition protection

This module is kept for backward compatibility but will be removed in a future version.

Migration Guide:
- Replace generate_preauth_token() with PreAuthTokenManager.generate_token()
- Replace validate_and_consume_preauth_token() with PreAuthTokenManager.verify_token()
  followed by PreAuthTokenManager.consume_token_atomic()
- Replace revoke_preauth_tokens_for_user() with PreAuthTokenManager.revoke_token()
"""

import secrets
import json
import logging
import warnings
from typing import Optional, Dict
from datetime import datetime

from .redis_client import get_redis_client

logger = logging.getLogger(__name__)


def generate_preauth_token(user_id: str, email: str, ttl: int = 300) -> str:
    """
    Generate a pre-auth token and store it in Redis.
    
    **DEPRECATED**: Use PreAuthTokenManager.generate_token() from pre_auth_token.py instead.
    
    Uses O(1) Redis lookup by storing token as key: preauth:{token}
    
    Args:
        user_id: User ID
        email: User email
        ttl: Time-to-live in seconds (default: 300 = 5 minutes)
    
    Returns:
        Token string (opaque, 256-bit entropy)
    """
    warnings.warn(
        "generate_preauth_token() is deprecated. Use PreAuthTokenManager.generate_token() "
        "from pre_auth_token.py instead for JWT-based tokens with better security.",
        DeprecationWarning,
        stacklevel=2
    )
    
    # Generate cryptographically secure random token
    token = secrets.token_urlsafe(32)  # 256-bit entropy
    
    # Store in Redis with token as key for O(1) lookup
    redis_client = get_redis_client()
    redis_key = f"preauth:{token}"
    
    token_data = {
        "user_id": user_id,
        "email": email,
        "issued_at": datetime.utcnow().isoformat(),
        "attempts": 0
    }
    
    redis_client.setex(
        redis_key,
        ttl,
        json.dumps(token_data)
    )
    
    logger.info(f"Pre-auth token issued for user {user_id}, expires in {ttl}s", extra={
        'event': 'preauth_token_issued',
        'user_id': user_id,
        'ttl': ttl
    })
    
    return token


def validate_and_consume_preauth_token(token: str) -> Optional[Dict]:
    """
    Validate and consume pre-auth token (one-time-use).
    
    **DEPRECATED**: Use PreAuthTokenManager.verify_token() followed by
    PreAuthTokenManager.consume_token_atomic() from pre_auth_token.py instead.
    
    Uses atomic Lua script to prevent race conditions where multiple concurrent
    requests could consume the same token.
    
    Args:
        token: Pre-auth token from cookie
    
    Returns:
        User dict with id, email if valid, None otherwise
    """
    warnings.warn(
        "validate_and_consume_preauth_token() is deprecated. Use PreAuthTokenManager.verify_token() "
        "followed by PreAuthTokenManager.consume_token_atomic() from pre_auth_token.py instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    if not token:
        return None
    
    redis_client = get_redis_client()
    redis_key = f"preauth:{token}"
    
    try:
        lua_script = """
        local value = redis.call('GET', KEYS[1])
        if not value then
            return nil
        end
        redis.call('DEL', KEYS[1])
        return value
        """
        
        stored_data = redis_client.eval(lua_script, 1, redis_key)
        
        if not stored_data:
            logger.warning("Pre-auth token not found or expired", extra={
                'event': 'preauth_token_expired',
                'token_prefix': token[:8] if token else None
            })
            return None
        
        if isinstance(stored_data, bytes):
            stored_data = stored_data.decode('utf-8')
        
        # Parse stored data
        data = json.loads(stored_data)
        user_id = data.get('user_id')
        email = data.get('email')
        
        if not user_id or not email:
            logger.error("Invalid pre-auth token data structure")
            return None
        
        logger.info(f"Pre-auth token consumed for user {user_id}", extra={
            'event': 'preauth_token_consumed',
            'user_id': user_id
        })
        
        return {
            'id': user_id,
            'email': email
        }
    
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse pre-auth token data: {e}", extra={
            'event': 'preauth_validation_failed',
            'error': 'json_decode_error'
        })
        return None
    except Exception as e:
        logger.error(f"Error validating pre-auth token: {e}", extra={
            'event': 'preauth_validation_failed',
            'error': str(e)
        })
        return None


def revoke_preauth_tokens_for_user(user_id: str) -> int:
    """
    Revoke all pre-auth tokens for a user.
    
    **DEPRECATED**: Use PreAuthTokenManager.revoke_token() from pre_auth_token.py instead.
    
    Note: With token-as-key design, we need to scan all preauth:* keys
    and check user_id in the value. This is acceptable for revocation
    (rare operation) but not for validation (frequent operation).
    
    Args:
        user_id: User ID
    
    Returns:
        Number of tokens revoked
    """
    warnings.warn(
        "revoke_preauth_tokens_for_user() is deprecated. Use PreAuthTokenManager.revoke_token() "
        "from pre_auth_token.py instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    redis_client = get_redis_client()
    pattern = "preauth:*"
    
    revoked_count = 0
    try:
        for key in redis_client.scan_iter(match=pattern):
            try:
                stored_data = redis_client.get(key)
                if stored_data:
                    data = json.loads(stored_data)
                    if data.get('user_id') == user_id:
                        redis_client.delete(key)
                        revoked_count += 1
            except (json.JSONDecodeError, Exception) as e:
                logger.warning(f"Error checking key {key} for revocation: {e}")
                continue
        
        if revoked_count > 0:
            logger.info(f"Revoked {revoked_count} pre-auth token(s) for user {user_id}")
    
    except Exception as e:
        logger.error(f"Error revoking pre-auth tokens for user {user_id}: {e}")
    
    return revoked_count
