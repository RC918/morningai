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
from common.config.settings import get_settings, settings

logger = logging.getLogger(__name__)

# Token Configuration
ACCESS_TOKEN_EXPIRY_MINUTES = 15
REFRESH_TOKEN_EXPIRY_DAYS = 7
JWT_ALGORITHM = 'HS256'

def _as_bool(val):
    """Convert value to boolean"""
    if isinstance(val, bool):
        return val
    if val is None:
        return False
    s = str(val).strip().lower()
    return s in ("1", "true", "yes", "on")

def is_testing_mode():
    """Check if running in testing mode (dynamic check)"""
    try:
        from flask import current_app
        if current_app:
            v = current_app.config.get("TESTING")
            if v is not None:
                return _as_bool(v)
    except Exception:
        pass
    return _as_bool(os.getenv("TESTING"))

def is_production():
    """Check if running in production mode (dynamic check)
    
    Priority order:
    1. os.environ ENVIRONMENT (explicit production setting - highest priority for tests)
    2. os.environ FLASK_ENV (fallback if ENVIRONMENT not set)
    3. Flask app.config ENVIRONMENT (explicit production setting)
    4. Flask app.config FLASK_ENV (fallback if ENVIRONMENT not set)
    5. Flask app.config TESTING (if True and no explicit env, return False)
    6. settings.is_production (fallback)
    
    This ensures tests can explicitly set ENVIRONMENT=production to test production
    behavior, even when FLASK_ENV=development or TESTING=True.
    """
    env = os.environ.get("ENVIRONMENT")
    if env:
        return env.lower() in ("production", "prod")
    
    flask_env = os.environ.get("FLASK_ENV")
    if flask_env:
        return flask_env.lower() in ("production", "prod")
    
    try:
        from flask import current_app
        if current_app:
            env = current_app.config.get("ENVIRONMENT")
            if env:
                return str(env).lower() in ("production", "prod")
            
            flask_env = current_app.config.get("FLASK_ENV")
            if flask_env:
                return str(flask_env).lower() in ("production", "prod")
    except Exception:
        pass
    
    try:
        from flask import current_app
        if current_app and _as_bool(current_app.config.get("TESTING")):
            return False
    except Exception:
        pass
    
    try:
        return bool(get_settings().is_production)
    except Exception:
        return False

def is_mock_users_enabled():
    """Check if mock users are enabled (dynamic check)
    
    Priority order:
    1. Flask app.config ENABLE_MOCK_USERS (explicit override)
    2. os.environ ENABLE_MOCK_USERS (explicit override)
    3. Default to True if TESTING mode (for test compatibility)
    4. settings.enable_mock_users (fallback for non-test environments)
    """
    try:
        from flask import current_app
        if current_app:
            v = current_app.config.get("ENABLE_MOCK_USERS")
            if v is not None:
                return _as_bool(v)
    except Exception:
        pass
    
    env_v = os.getenv("ENABLE_MOCK_USERS")
    if env_v is not None:
        return _as_bool(env_v)
    
    if is_testing_mode():
        return True
    
    try:
        v = getattr(get_settings(), "enable_mock_users", None)
        if v is not None:
            return _as_bool(v)
    except Exception:
        pass
    
    return False

def _get_jwt_secret():
    """Get JWT secret key from settings at runtime"""
    return get_settings().jwt_secret_key or 'test-secret-key-for-testing'

# Cookie Configuration (read from settings at module load - these are less critical for tests)
COOKIE_SECURE = settings.cookie_secure if settings.cookie_secure is not None else (True if settings.is_production else False)
COOKIE_SAMESITE = settings.cookie_samesite or 'Lax'  # Configurable: 'Strict', 'Lax', or 'None'
COOKIE_HTTPONLY = True
COOKIE_DOMAIN = settings.cookie_domain  # Optional: restrict to specific domain
COOKIE_PATH = settings.cookie_path or '/'  # Optional: restrict to specific path

# CSRF Configuration
CSRF_TOKEN_LENGTH = 32  # bytes

FEATURE_2FA_PREAUTH = settings.feature_2fa_preauth if settings.feature_2fa_preauth is not None else False
PREAUTH_TOKEN_TTL = settings.preauth_token_ttl or 300  # 5 minutes default


def validate_security_config():
    """
    Validate security configuration at startup
    Fails fast in production if configuration is insecure
    In non-production, logs warning if secret is missing (fallback used)
    """
    errors = []
    warnings = []
    jwt_errors = []
    
    prod = is_production()
    mock_users = is_mock_users_enabled()
    
    jwt_secret = _get_jwt_secret()
    if not jwt_secret:
        if prod:
            jwt_errors.append("JWT_SECRET_KEY environment variable is not set")
        else:
            logger.warning(
                "JWT_SECRET_KEY not set in non-production environment. "
                "Using fallback test secret. DO NOT USE IN PRODUCTION."
            )
    elif prod:
        if len(jwt_secret) < 32:
            jwt_errors.append(f"JWT_SECRET_KEY must be at least 32 characters in production (current: {len(jwt_secret)})")
        if jwt_secret in ['your-secret-key', 'secret', 'changeme', 'test', 'test-secret-key-for-testing']:
            jwt_errors.append("JWT_SECRET_KEY is using a known weak/default value")
    
    if prod and mock_users:
        errors.append("ENABLE_MOCK_USERS must be false in production (current: true)")
    
    # P0-3: Validate Cookie Configuration
    if COOKIE_SAMESITE == 'None' and not COOKIE_SECURE:
        errors.append("COOKIE_SAMESITE=None requires COOKIE_SECURE=True (browsers will reject)")
    
    if prod and not COOKIE_SECURE:
        warnings.append("COOKIE_SECURE should be True in production")
    
    if COOKIE_SAMESITE not in ['Strict', 'Lax', 'None']:
        errors.append(f"COOKIE_SAMESITE must be 'Strict', 'Lax', or 'None' (current: {COOKIE_SAMESITE})")
    
    if jwt_errors:
        for error in jwt_errors:
            logger.error(f"Security configuration error: {error}")
        raise RuntimeError(f"Invalid JWT secret in production: {'; '.join(jwt_errors)}")
    
    if errors:
        for error in errors:
            logger.error(f"Security configuration error: {error}")
        raise SystemExit(f"Security configuration validation failed with {len(errors)} error(s). See logs for details.")
    
    if warnings:
        for warning in warnings:
            logger.warning(f"Security configuration warning: {warning}")
    
    logger.info("Security configuration validated successfully")
    env_name = settings.environment or 'development'
    logger.info(f"Environment: {env_name}")
    logger.info(f"Cookie SameSite: {COOKIE_SAMESITE}")
    logger.info(f"Cookie Secure: {COOKIE_SECURE}")
    logger.info(f"Mock Users Enabled: {is_mock_users_enabled()}")


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
    
    token = jwt.encode(payload, _get_jwt_secret(), algorithm=JWT_ALGORITHM)
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
    
    token = jwt.encode(payload, _get_jwt_secret(), algorithm=JWT_ALGORITHM)
    return token


def verify_access_token(token: str) -> Optional[Dict]:
    """
    Verify access token
    
    Returns:
        Decoded payload or None if invalid
    """
    try:
        payload = jwt.decode(token, _get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        
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
        payload = jwt.decode(token, _get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        
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
    if not is_mock_users_enabled():
        return {}
    
    return {
        'owner@morningai.com': {
            'id': 'owner-001',
            'email': 'owner@morningai.com',
            'hashed_password': generate_password_hash(settings.owner_password or 'owner123'),
            'name': 'Platform Owner',
            'role': 'owner',
            'tenant_id': 'platform',
            'avatar': None
        },
        'admin@morningai.com': {
            'id': 'admin-001',
            'email': 'admin@morningai.com',
            'hashed_password': generate_password_hash(settings.admin_password or 'admin123'),
            'name': 'System Admin',
            'role': 'admin',
            'tenant_id': 'tenant-001',
            'avatar': None
        }
    }


def authenticate_user(email: str, password: str) -> Optional[Dict]:
    """
    Authenticate user with email and password
    
    In production: Uses Supabase Auth
    In development: Uses mock users if ENABLE_MOCK_USERS=true, otherwise Supabase Auth
    
    Returns:
        User dict or None if authentication failed
    """
    if is_production() and is_mock_users_enabled():
        logger.error("Mock users should not be enabled in production")
        return None
    
    if is_mock_users_enabled():
        mock_users = _get_mock_users()
        
        user = mock_users.get(email)
        if not user:
            logger.warning(f"User not found: {email}")
            return None
        
        if not check_password_hash(user['hashed_password'], password):
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
    
    import requests
    
    supabase_url = get_settings().supabase_url
    supabase_anon_key = get_settings().supabase_anon_key
    
    if not supabase_url or not supabase_anon_key:
        logger.error("SUPABASE_URL and SUPABASE_ANON_KEY must be set when ENABLE_MOCK_USERS=false")
        return None
    
    try:
        auth_url = f"{supabase_url}/auth/v1/token?grant_type=password"
        headers = {
            'apikey': supabase_anon_key,
            'Content-Type': 'application/json'
        }
        payload = {
            'email': email,
            'password': password
        }
        
        response = requests.post(auth_url, headers=headers, json=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            user_data = data.get('user', {})
            user_metadata = user_data.get('user_metadata', {}) or user_data.get('raw_user_meta_data', {})
            
            user_id = user_data.get('id')
            user_email = user_data.get('email', email)
            user_name = user_metadata.get('name', user_email.split('@')[0])
            user_role = user_metadata.get('role', 'member')
            tenant_id = user_metadata.get('tenant_id', user_metadata.get('tenantId'))
            avatar = user_metadata.get('avatar')
            
            logger.info(f"User authenticated via Supabase: {user_email} (role: {user_role})")
            
            return {
                'id': user_id,
                'email': user_email,
                'name': user_name,
                'role': user_role,
                'tenant_id': tenant_id,
                'avatar': avatar
            }
        else:
            logger.warning(f"Supabase Auth failed for {email}: {response.status_code}")
            return None
            
    except Exception as e:
        logger.exception(f"Supabase Auth error for {email}: {e}")
        return None


def get_user_by_id(user_id: str) -> Optional[Dict]:
    """
    Get user by ID
    
    In production: Uses Supabase Auth
    In development: Uses mock users if ENABLE_MOCK_USERS=true, otherwise Supabase Auth
    
    Returns:
        User dict or None if not found
    """
    if is_production() and is_mock_users_enabled():
        logger.error("Mock users should not be enabled in production")
        return None
    
    if is_mock_users_enabled():
        mock_users = _get_mock_users()
        
        for user in mock_users.values():
            if user['id'] == user_id:
                return {
                    'id': user['id'],
                    'email': user['email'],
                    'name': user['name'],
                    'role': user['role'],
                    'tenant_id': user['tenant_id'],
                    'avatar': user['avatar'],
                    'hashed_password': user['hashed_password']
                }
        return None
    
    import requests
    
    supabase_url = get_settings().supabase_url
    supabase_service_key = get_settings().supabase_service_role_key
    
    if not supabase_url or not supabase_service_key:
        logger.error("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set when ENABLE_MOCK_USERS=false")
        return None
    
    try:
        admin_url = f"{supabase_url}/auth/v1/admin/users/{user_id}"
        headers = {
            'apikey': supabase_service_key,
            'Authorization': f'Bearer {supabase_service_key}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(admin_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            user_data = response.json()
            user_metadata = user_data.get('user_metadata', {}) or user_data.get('raw_user_meta_data', {})
            
            user_email = user_data.get('email')
            user_name = user_metadata.get('name', user_email.split('@')[0] if user_email else 'User')
            user_role = user_metadata.get('role', 'member')
            tenant_id = user_metadata.get('tenant_id', user_metadata.get('tenantId'))
            avatar = user_metadata.get('avatar')
            
            return {
                'id': user_id,
                'email': user_email,
                'name': user_name,
                'role': user_role,
                'tenant_id': tenant_id,
                'avatar': avatar
            }
        else:
            logger.warning(f"Supabase get user failed for {user_id}: {response.status_code}")
            return None
            
    except Exception as e:
        logger.exception(f"Supabase get user error for {user_id}: {e}")
        return None
