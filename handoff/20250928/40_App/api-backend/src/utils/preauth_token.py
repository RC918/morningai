"""
Pre-Auth Token utilities for 2FA authentication flow.

This module provides functions to generate, validate, and consume pre-auth tokens
that are used to eliminate password re-transmission during 2FA verification.
"""

import secrets
import json
import logging
from typing import Optional, Dict
from datetime import datetime

from .redis_client import get_redis_client

logger = logging.getLogger(__name__)


def generate_preauth_token(user_id: str, email: str, ttl: int = 300) -> str:
    """
    Generate a pre-auth token and store it in Redis.
    
    Uses O(1) Redis lookup by storing token as key: preauth:{token}
    
    Args:
        user_id: User ID
        email: User email
        ttl: Time-to-live in seconds (default: 300 = 5 minutes)
    
    Returns:
        Token string (opaque, 256-bit entropy)
    """
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
    
    logger.info(f"Pre-auth token issued for user {user_id}, expires in {ttl}s")
    
    return token


def validate_and_consume_preauth_token(token: str) -> Optional[Dict]:
    """
    Validate and consume pre-auth token (one-time-use).
    
    Uses O(1) Redis GET lookup instead of SCAN for performance.
    
    Args:
        token: Pre-auth token from cookie
    
    Returns:
        User dict with id, email if valid, None otherwise
    """
    if not token:
        return None
    
    redis_client = get_redis_client()
    redis_key = f"preauth:{token}"
    
    try:
        stored_data = redis_client.get(redis_key)
        
        if not stored_data:
            logger.warning("Pre-auth token not found or expired")
            return None
        
        # Parse stored data
        data = json.loads(stored_data)
        user_id = data.get('user_id')
        email = data.get('email')
        
        if not user_id or not email:
            logger.error(f"Invalid pre-auth token data structure")
            return None
        
        # Delete token (one-time-use)
        redis_client.delete(redis_key)
        
        logger.info(f"Pre-auth token consumed for user {user_id}")
        
        return {
            'id': user_id,
            'email': email
        }
    
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse pre-auth token data: {e}")
        return None
    except Exception as e:
        logger.error(f"Error validating pre-auth token: {e}")
        return None


def revoke_preauth_tokens_for_user(user_id: str) -> int:
    """
    Revoke all pre-auth tokens for a user.
    
    Note: With token-as-key design, we need to scan all preauth:* keys
    and check user_id in the value. This is acceptable for revocation
    (rare operation) but not for validation (frequent operation).
    
    Args:
        user_id: User ID
    
    Returns:
        Number of tokens revoked
    """
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
