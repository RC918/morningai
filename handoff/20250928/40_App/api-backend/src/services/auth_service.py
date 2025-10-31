"""
Authentication Service for Owner Console
Task 1: Enhanced Token Security

Provides:
- JWT token generation with access (15min) + refresh (7 days) tokens
- Token rotation on refresh
- Redis blacklist for token revocation
- HttpOnly cookie management
"""

import os
import jwt
import datetime
import hashlib
import logging
import secrets
from typing import Optional, Dict, Tuple
from werkzeug.security import check_password_hash, generate_password_hash

logger = logging.getLogger(__name__)

ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development')
IS_PRODUCTION = ENVIRONMENT == 'production'

# Token Configuration
ACCESS_TOKEN_EXPIRY_MINUTES = 15
REFRESH_TOKEN_EXPIRY_DAYS = 7
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')  # No default - must be set
JWT_ALGORITHM = 'HS256'

# Cookie Configuration
COOKIE_SECURE = IS_PRODUCTION  # Always secure in production
COOKIE_SAMESITE = os.environ.get('COOKIE_SAMESITE', 'Strict')  # Configurable: 'Strict', 'Lax', or 'None'
COOKIE_HTTPONLY = True
COOKIE_DOMAIN = os.environ.get('COOKIE_DOMAIN', None)  # Optional: restrict to specific domain
COOKIE_PATH = os.environ.get('COOKIE_PATH', '/')  # Optional: restrict to specific path

ENABLE_MOCK_USERS = os.environ.get('ENABLE_MOCK_USERS', 'true').lower() == 'true'

# CSRF Configuration
CSRF_TOKEN_LENGTH = 32  # bytes


def validate_security_config():
    """
    Validate security configuration at startup
    Fails fast in production if configuration is insecure
    """
    errors = []
    warnings = []
    
    if not JWT_SECRET_KEY:
        errors.append("JWT_SECRET_KEY environment variable is not set")
    elif IS_PRODUCTION:
        if len(JWT_SECRET_KEY) < 32:
            errors.append(f"JWT_SECRET_KEY must be at least 32 characters in production (current: {len(JWT_SECRET_KEY)})")
        if JWT_SECRET_KEY in ['your-secret-key', 'secret', 'changeme', 'test']:
            errors.append("JWT_SECRET_KEY is using a known weak/default value")
    
    if IS_PRODUCTION and ENABLE_MOCK_USERS:
        errors.append("ENABLE_MOCK_USERS must be false in production (current: true)")
    
    # P0-3: Validate Cookie Configuration
    if COOKIE_SAMESITE == 'None' and not COOKIE_SECURE:
        errors.append("COOKIE_SAMESITE=None requires COOKIE_SECURE=True (browsers will reject)")
    
    if IS_PRODUCTION and not COOKIE_SECURE:
        warnings.append("COOKIE_SECURE should be True in production")
    
    if COOKIE_SAMESITE not in ['Strict', 'Lax', 'None']:
        errors.append(f"COOKIE_SAMESITE must be 'Strict', 'Lax', or 'None' (current: {COOKIE_SAMESITE})")
    
    if errors:
        for error in errors:
            logger.error(f"Security configuration error: {error}")
        raise SystemExit(f"Security configuration validation failed with {len(errors)} error(s). See logs for details.")
    
    if warnings:
        for warning in warnings:
            logger.warning(f"Security configuration warning: {warning}")
    
    logger.info("Security configuration validated successfully")
    logger.info(f"Environment: {ENVIRONMENT}")
    logger.info(f"Cookie SameSite: {COOKIE_SAMESITE}")
    logger.info(f"Cookie Secure: {COOKIE_SECURE}")
    logger.info(f"Mock Users Enabled: {ENABLE_MOCK_USERS}")


def get_redis_client():
    """Get Redis client for token blacklist"""
    try:
        from src.utils.redis_client import get_redis_client as get_redis
        return get_redis()
    except Exception as e:
        logger.error(f"Failed to get Redis client: {e}")
        return None


def hash_token(token: str) -> str:
    """Hash token for storage in blacklist"""
    return hashlib.sha256(token.encode()).hexdigest()


def generate_access_token(user_id: str, email: str, role: str) -> Tuple[str, int]:
    """
    Generate access token (15 minutes)
    
    Returns:
        Tuple of (token, expiry_timestamp_ms)
    """
    now = datetime.datetime.now(datetime.UTC)
    expiry = now + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRY_MINUTES)
    expiry_timestamp = int(expiry.timestamp() * 1000)  # milliseconds
    
    payload = {
        'user_id': user_id,
        'email': email,
        'role': role,
        'type': 'access',
        'iat': now,
        'exp': expiry
    }
    
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token, expiry_timestamp


def generate_refresh_token(user_id: str, email: str) -> str:
    """
    Generate refresh token (7 days)
    
    Returns:
        Refresh token string
    """
    import uuid
    now = datetime.datetime.now(datetime.UTC)
    expiry = now + datetime.timedelta(days=REFRESH_TOKEN_EXPIRY_DAYS)
    
    payload = {
        'user_id': user_id,
        'email': email,
        'type': 'refresh',
        'jti': str(uuid.uuid4()),  # Add unique ID to ensure tokens are different
        'iat': now,
        'exp': expiry
    }
    
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token


def verify_access_token(token: str) -> Optional[Dict]:
    """
    Verify access token
    
    Returns:
        Decoded payload or None if invalid
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        if payload.get('type') != 'access':
            logger.warning("Token is not an access token")
            return None
        
        return payload
    except jwt.ExpiredSignatureError:
        logger.debug("Access token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid access token: {e}")
        return None


def verify_refresh_token(token: str) -> Optional[Dict]:
    """
    Verify refresh token and check blacklist
    
    Returns:
        Decoded payload or None if invalid/blacklisted
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        if payload.get('type') != 'refresh':
            logger.warning("Token is not a refresh token")
            return None
        
        if is_token_blacklisted(token):
            logger.warning("Refresh token is blacklisted")
            return None
        
        return payload
    except jwt.ExpiredSignatureError:
        logger.debug("Refresh token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid refresh token: {e}")
        return None


def is_token_blacklisted(token: str) -> bool:
    """
    Check if refresh token is blacklisted
    
    Returns:
        True if blacklisted, False otherwise
    """
    redis_client = get_redis_client()
    if not redis_client:
        logger.warning("Redis not available, cannot check blacklist")
        return False
    
    try:
        token_hash = hash_token(token)
        key = f"blacklist:refresh:{token_hash}"
        return redis_client.exists(key) > 0
    except Exception as e:
        logger.error(f"Failed to check token blacklist: {e}")
        return False


def blacklist_refresh_token(token: str) -> bool:
    """
    Add refresh token to blacklist
    
    Returns:
        True if successful, False otherwise
    """
    redis_client = get_redis_client()
    if not redis_client:
        logger.error("Redis not available, cannot blacklist token")
        return False
    
    try:
        token_hash = hash_token(token)
        key = f"blacklist:refresh:{token_hash}"
        
        ttl_seconds = REFRESH_TOKEN_EXPIRY_DAYS * 24 * 60 * 60
        redis_client.setex(key, ttl_seconds, "1")
        
        logger.info(f"Refresh token blacklisted: {token_hash[:16]}...")
        return True
    except Exception as e:
        logger.error(f"Failed to blacklist token: {e}")
        return False


def rotate_refresh_token(old_token: str, user_id: str, email: str) -> Optional[str]:
    """
    Rotate refresh token: blacklist old token and generate new one
    
    Returns:
        New refresh token or None if rotation failed
    """
    if not blacklist_refresh_token(old_token):
        logger.error("Failed to blacklist old refresh token during rotation")
        return None
    
    new_token = generate_refresh_token(user_id, email)
    logger.info(f"Refresh token rotated for user: {user_id}")
    return new_token


def generate_csrf_token() -> str:
    """
    Generate a cryptographically secure CSRF token
    
    Returns:
        CSRF token string (hex encoded)
    """
    return secrets.token_hex(CSRF_TOKEN_LENGTH)


def create_cookie_config(name: str, value: str, max_age_seconds: int, httponly: bool = True) -> Dict:
    """
    Create cookie configuration for Flask response
    
    Args:
        name: Cookie name
        value: Cookie value
        max_age_seconds: Cookie max age in seconds
        httponly: Whether cookie should be HttpOnly (default: True)
    
    Returns:
        Dict with cookie configuration
    """
    config = {
        'key': name,
        'value': value,
        'max_age': max_age_seconds,
        'secure': COOKIE_SECURE,
        'httponly': httponly,
        'samesite': COOKIE_SAMESITE,
        'path': COOKIE_PATH
    }
    
    if COOKIE_DOMAIN:
        config['domain'] = COOKIE_DOMAIN
    
    return config


def set_auth_cookies(response, access_token: str, refresh_token: str, access_expiry_ms: int, csrf_token: Optional[str] = None):
    """
    Set authentication cookies on Flask response
    
    Args:
        response: Flask response object
        access_token: Access token string
        refresh_token: Refresh token string
        access_expiry_ms: Access token expiry in milliseconds
        csrf_token: Optional CSRF token (required if SameSite=None)
    """
    access_max_age = ACCESS_TOKEN_EXPIRY_MINUTES * 60
    response.set_cookie(
        **create_cookie_config('access_token', access_token, access_max_age, httponly=True)
    )
    
    refresh_max_age = REFRESH_TOKEN_EXPIRY_DAYS * 24 * 60 * 60
    response.set_cookie(
        **create_cookie_config('refresh_token', refresh_token, refresh_max_age, httponly=True)
    )
    
    if csrf_token or COOKIE_SAMESITE == 'None':
        csrf_token = csrf_token or generate_csrf_token()
        # CSRF token expires with access token
        response.set_cookie(
            **create_cookie_config('csrf_token', csrf_token, access_max_age, httponly=False)
        )
    
    logger.debug("Auth cookies set successfully")


def clear_auth_cookies(response):
    """
    Clear authentication cookies from Flask response
    
    Args:
        response: Flask response object
    """
    cookie_attrs = {
        'max_age': 0,
        'path': COOKIE_PATH,
        'secure': COOKIE_SECURE,
        'samesite': COOKIE_SAMESITE
    }
    if COOKIE_DOMAIN:
        cookie_attrs['domain'] = COOKIE_DOMAIN
    
    response.set_cookie('access_token', '', **cookie_attrs)
    response.set_cookie('refresh_token', '', **cookie_attrs)
    response.set_cookie('csrf_token', '', **cookie_attrs)
    logger.debug("Auth cookies cleared")


def _get_mock_users() -> Dict:
    """
    Get mock users for development/testing
    
    WARNING: Only available when ENABLE_MOCK_USERS=true
    In production, this returns empty dict
    """
    if not ENABLE_MOCK_USERS:
        return {}
    
    return {
        'owner@morningai.com': {
            'id': 'owner-001',
            'email': 'owner@morningai.com',
            'password_hash': generate_password_hash(os.environ.get('OWNER_PASSWORD', 'owner123')),
            'name': 'Platform Owner',
            'role': 'owner',
            'tenant_id': 'platform',
            'avatar': None
        },
        'admin@morningai.com': {
            'id': 'admin-001',
            'email': 'admin@morningai.com',
            'password_hash': generate_password_hash(os.environ.get('ADMIN_PASSWORD', 'admin123')),
            'name': 'System Admin',
            'role': 'admin',
            'tenant_id': 'tenant-001',
            'avatar': None
        }
    }


def authenticate_user(email: str, password: str) -> Optional[Dict]:
    """
    Authenticate user with email and password
    
    In production: Should integrate with real user database
    In development: Uses mock users if ENABLE_MOCK_USERS=true
    
    Returns:
        User dict or None if authentication failed
    """
    if IS_PRODUCTION and ENABLE_MOCK_USERS:
        logger.error("Mock users should not be enabled in production")
        return None
    
    mock_users = _get_mock_users()
    
    user = mock_users.get(email)
    if not user:
        logger.warning(f"User not found: {email}")
        return None
    
    if not check_password_hash(user['password_hash'], password):
        logger.warning(f"Invalid password for user: {email}")
        return None
    
    return {
        'id': user['id'],
        'email': user['email'],
        'name': user['name'],
        'role': user['role'],
        'tenant_id': user['tenant_id'],
        'avatar': user['avatar']
    }


def get_user_by_id(user_id: str) -> Optional[Dict]:
    """
    Get user by ID
    
    In production: Should integrate with real user database
    In development: Uses mock users if ENABLE_MOCK_USERS=true
    
    Returns:
        User dict or None if not found
    """
    if IS_PRODUCTION and ENABLE_MOCK_USERS:
        logger.error("Mock users should not be enabled in production")
        return None
    
    mock_users = _get_mock_users()
    
    for user in mock_users.values():
        if user['id'] == user_id:
            return {
                'id': user['id'],
                'email': user['email'],
                'name': user['name'],
                'role': user['role'],
                'tenant_id': user['tenant_id'],
                'avatar': user['avatar']
            }
    return None
