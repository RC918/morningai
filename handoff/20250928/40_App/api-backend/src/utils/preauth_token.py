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


def generate_preauth_token(user_id: str, email: str, ttl: int = 300) -> tuple[str, str]:
    """
    Generate a pre-auth token and store it in Redis.
    
    Args:
        user_id: User ID
        email: User email
        ttl: Time-to-live in seconds (default: 300 = 5 minutes)
    
    Returns:
        Tuple of (token, nonce)
    """
    # Generate cryptographically secure random token
    token = secrets.token_urlsafe(32)  # 256-bit entropy
    nonce = secrets.token_urlsafe(16)
    
    # Store in Redis
    redis_client = get_redis_client()
    redis_key = f"preauth:{user_id}:{nonce}"
    
    token_data = {
        "token": token,
        "issued_at": datetime.utcnow().isoformat(),
        "attempts": 0,
        "email": email,
        "nonce": nonce
    }
    
    redis_client.setex(
        redis_key,
        ttl,
        json.dumps(token_data)
    )
    
    logger.info(f"Pre-auth token issued for user {user_id}, expires in {ttl}s")
    
    return token, nonce


def validate_and_consume_preauth_token(token: str) -> Optional[Dict]:
    """
    Validate and consume pre-auth token (one-time-use).
    
    This function searches for a matching token in Redis, validates it,
    and deletes it to ensure one-time-use.
    
    Args:
        token: Pre-auth token from cookie
    
    Returns:
        User dict with id, email if valid, None otherwise
    """
    if not token:
        return None
    
    redis_client = get_redis_client()
    
    # Scan for matching pre-auth tokens
    # Pattern: preauth:*:*
    for key in redis_client.scan_iter(match="preauth:*:*"):
        try:
            # Get stored data
            stored_data = redis_client.get(key)
            if not stored_data:
                continue
            
            data = json.loads(stored_data)
            stored_token = data.get('token')
            
            # Constant-time comparison to prevent timing attacks
            if stored_token and secrets.compare_digest(token, stored_token):
                # Extract user_id from key (format: preauth:user_id:nonce)
                key_parts = key.split(':')
                if len(key_parts) != 3:
                    continue
                
                user_id = key_parts[1]
                email = data.get('email')
                
                # Delete token (one-time-use)
                redis_client.delete(key)
                
                logger.info(f"Pre-auth token consumed for user {user_id}")
                
                return {
                    'id': user_id,
                    'email': email
                }
        
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Error processing pre-auth token key {key}: {e}")
            continue
    
    logger.warning("Invalid or expired pre-auth token")
    return None


def revoke_preauth_token(user_id: str) -> int:
    """
    Revoke all pre-auth tokens for a user.
    
    Args:
        user_id: User ID
    
    Returns:
        Number of tokens revoked
    """
    redis_client = get_redis_client()
    pattern = f"preauth:{user_id}:*"
    
    revoked_count = 0
    for key in redis_client.scan_iter(match=pattern):
        redis_client.delete(key)
        revoked_count += 1
    
    if revoked_count > 0:
        logger.info(f"Revoked {revoked_count} pre-auth token(s) for user {user_id}")
    
    return revoked_count
