"""
Authentication Middleware for Owner Console

Issue #4220: Refactored to use centralized TokenService for JWT operations.
"""

import jwt
import logging
from functools import wraps
from flask import request, jsonify
from src.services.token_service import get_token_service


def _get_jwt_algorithm() -> str:
    """Get JWT algorithm from settings.

    Note: This function is kept for backward compatibility.
    New code should use get_token_service().algorithm instead.
    """
    return get_token_service().algorithm


def verify_jwt_library():
    """
    Verify that the correct PyJWT library is installed.
    This prevents issues where the wrong 'jwt' package (jwt==1.4.0) is installed
    instead of PyJWT (PyJWT>=2.8.0).

    Raises:
        RuntimeError: If the wrong jwt library is detected
    """
    if not hasattr(jwt, 'encode') or not hasattr(jwt, 'decode'):
        raise RuntimeError(
            "Wrong 'jwt' package detected! "
            "The package 'jwt==1.4.0' is installed instead of 'PyJWT>=2.8.0'. "
            "Please run: pip uninstall -y jwt && pip install PyJWT==2.8.0"
        )

    jwt_file = getattr(jwt, '__file__', '')
    if 'PyJWT' not in jwt_file and 'pyjwt' not in jwt_file.lower():
        try:
            try:
                import pkg_resources
                _version = pkg_resources.get_distribution("PyJWT").version  # noqa: F841
            except (ImportError, ModuleNotFoundError):
                from importlib import metadata
                _version = metadata.version("PyJWT")  # noqa: F841 - check only
        except Exception:
            raise RuntimeError(
                "Wrong 'jwt' package detected! "
                "The package 'jwt==1.4.0' is installed instead of 'PyJWT>=2.8.0'. "
                "Please run: pip uninstall -y jwt && pip install PyJWT==2.8.0"
            )

verify_jwt_library()

def _parse_bearer_token(auth_header):
    """
    Parse and validate Bearer token from Authorization header.

    Args:
        auth_header: Authorization header value

    Returns:
        tuple: (token, error_response) where error_response is None if successful
    """
    if not auth_header:
        return None, (jsonify({
            'error': 'Authorization header missing',
            'message': 'Access denied. Please provide a valid JWT token.'
        }), 401)

    try:
        parts = auth_header.split(' ')
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return None, (jsonify({
                'error': 'Invalid authorization format',
                'message': 'Authorization header must be in format: Bearer <token>'
            }), 401)
        return parts[1], None
    except (IndexError, AttributeError):
        return None, (jsonify({
            'error': 'Invalid authorization format',
            'message': 'Authorization header must be in format: Bearer <token>'
        }), 401)

def _extract_jwt_from_request():
    """
    Extract JWT token from request (Authorization header, X-Access-Token header, or access_token cookie).

    Priority:
    1. Authorization header (for API clients and backward compatibility)
    2. X-Access-Token header (fallback for environments where cookies are blocked)
    3. access_token cookie (for browser-based authentication)

    If Authorization header is present but invalid, we continue to try X-Access-Token and cookie
    to enable true fallback behavior (e.g., when stale/malformed Authorization header exists).
    However, if no fallback methods succeed, we return the original Authorization error to preserve
    error semantics for API consumers.

    Returns:
        tuple: (token, error_response) where error_response is None if successful
    """
    invalid_format_error = None

    auth_header = request.headers.get('Authorization')
    if auth_header:
        token, error = _parse_bearer_token(auth_header)
        if not error:
            return token, None
        invalid_format_error = error
        logging.warning(f"Invalid Authorization header, trying fallback methods: {error[0].get_json()}")

    x_access_token = request.headers.get('X-Access-Token')
    if x_access_token:
        return x_access_token, None

    cookie_token = request.cookies.get('access_token')
    if cookie_token:
        return cookie_token, None

    if invalid_format_error:
        return None, invalid_format_error

    return None, (jsonify({
        'error': 'Authorization header missing',
        'message': 'Please provide a valid JWT token via Authorization header, '
                   'X-Access-Token header, or access_token cookie.'
    }), 401)

def _error_response_from_exception(e):
    """
    Map JWT exceptions to error responses.

    Args:
        e: Exception from jwt.decode()

    Returns:
        tuple: (jsonify response, status_code)
    """
    if isinstance(e, jwt.ExpiredSignatureError):
        return jsonify({
            'error': 'Token expired',
            'message': 'JWT token has expired. Please login again.'
        }), 401
    elif isinstance(e, jwt.InvalidTokenError):
        return jsonify({
            'error': 'Invalid token',
            'message': 'JWT token is invalid or malformed.'
        }), 401
    else:
        return jsonify({
            'error': 'Authentication failed',
            'message': 'Unable to verify JWT token.'
        }), 401

def _try_decode_token(token, jwt_secret=None):
    """
    Try to decode a JWT token.

    Args:
        token: JWT token string
        jwt_secret: Secret key for decoding (deprecated, uses TokenService)

    Returns:
        tuple: (payload, exception) where exception is None if successful
    """
    try:
        # Issue #4220: Use centralized TokenService for JWT operations
        payload = get_token_service().decode(token)
        return payload, None
    except Exception as e:
        return None, e

def _decode_jwt_with_fallback():
    """
    Decode JWT token with fallback support.

    Tries to decode tokens from multiple sources in priority order:
    1. Authorization header
    2. X-Access-Token header
    3. access_token cookie

    If the Authorization header exists but decode fails (expired/invalid), we try
    fallback sources before returning an error. This handles scenarios where the
    client has a stale in-memory token but a valid cookie.

    Returns:
        tuple: (payload, error_response) where error_response is None if successful
    """
    # Issue #4220: TokenService handles secret retrieval internally
    primary_error = None

    auth_header = request.headers.get('Authorization')
    if auth_header:
        token, parse_error = _parse_bearer_token(auth_header)
        if parse_error:
            primary_error = parse_error
            logging.warning(
                f"Invalid Authorization header format, trying fallback: {parse_error[0].get_json()}"
            )
        else:
            payload, decode_error = _try_decode_token(token)
            if payload:
                return payload, None
            primary_error = _error_response_from_exception(decode_error)
            logging.warning(
                f"Authorization token decode failed, trying fallback: {primary_error[0].get_json()}"
            )

    x_access_token = request.headers.get('X-Access-Token')
    if x_access_token:
        payload, decode_error = _try_decode_token(x_access_token)
        if payload:
            return payload, None

    cookie_token = request.cookies.get('access_token')
    if cookie_token:
        payload, decode_error = _try_decode_token(cookie_token)
        if payload:
            return payload, None

    if primary_error:
        return None, primary_error

    return None, (jsonify({
        'error': 'Authorization header missing',
        'message': 'Please provide a valid JWT token via Authorization header, '
                   'X-Access-Token header, or access_token cookie.'
    }), 401)

def jwt_required(f):
    """
    JWT authentication decorator for protecting endpoints.

    Supports multiple authentication sources with fallback:
    1. Authorization header (primary)
    2. X-Access-Token header (fallback)
    3. access_token cookie (fallback)
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        payload, error = _decode_jwt_with_fallback()
        if error:
            return error

        user_id = payload.get('sub') or payload.get('user_id')
        raw_role = payload.get('role', 'user')
        normalized_role = normalize_role(raw_role)

        from flask import g

        is_platform_admin = payload.get('is_platform_admin', False)

        request.current_user = {
            'user_id': user_id,
            'username': payload.get('username') or payload.get('email'),
            'role': normalized_role,
            'raw_role': raw_role,
            'is_super_admin': raw_role == '超級管理員',
            'is_platform_admin': is_platform_admin
        }

        request.user_id = user_id
        g.user_id = user_id

        return f(*args, **kwargs)

    return decorated_function

def admin_required(f):
    """
    Decorator for endpoints requiring admin role.

    Supports multiple authentication sources with fallback:
    1. Authorization header (primary)
    2. X-Access-Token header (fallback)
    3. access_token cookie (fallback)
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        payload, error = _decode_jwt_with_fallback()
        if error:
            return error

        raw_role = payload.get('role', 'user')
        normalized_role = normalize_role(raw_role)
        is_platform_admin = payload.get('is_platform_admin', False)

        # Allow admin, owner, platform admin, and super admin roles to access admin endpoints
        # Owner role is the tenant owner who should have full access to Owner Console
        if normalized_role not in ['admin', 'owner'] and raw_role not in ['超級管理員'] and not is_platform_admin:
            return jsonify({
                'error': 'Insufficient privileges',
                'message': 'Admin access required for this endpoint.'
            }), 403

        user_id = payload.get('sub') or payload.get('user_id')

        request.current_user = {
            'user_id': user_id,
            'username': payload.get('username') or payload.get('email'),
            'role': normalized_role,
            'raw_role': raw_role,
            'is_super_admin': raw_role == '超級管理員',
            'is_platform_admin': is_platform_admin
        }

        request.user_id = user_id

        return f(*args, **kwargs)

    return decorated_function

def analyst_required(f):
    """
    Decorator for endpoints requiring analyst role or higher.

    Supports multiple authentication sources with fallback:
    1. Authorization header (primary)
    2. X-Access-Token header (fallback)
    3. access_token cookie (fallback)
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        payload, error = _decode_jwt_with_fallback()
        if error:
            return error

        raw_role = payload.get('role', 'user')
        normalized_role = normalize_role(raw_role)
        is_platform_admin = payload.get('is_platform_admin', False)

        is_analyst_or_admin = normalized_role in ['admin', 'analyst']
        is_legacy_admin = raw_role in ['超級管理員', '分析師']
        if not is_analyst_or_admin and not is_legacy_admin and not is_platform_admin:
            return jsonify({
                'error': 'Insufficient privileges',
                'message': 'Analyst access or higher required for this endpoint.'
            }), 403

        user_id = payload.get('sub') or payload.get('user_id')

        request.current_user = {
            'user_id': user_id,
            'username': payload.get('username') or payload.get('email'),
            'role': normalized_role,
            'raw_role': raw_role,
            'is_super_admin': raw_role == '超級管理員',
            'is_platform_admin': is_platform_admin
        }

        request.user_id = user_id

        return f(*args, **kwargs)

    return decorated_function

def normalize_role(role):
    """
    Normalize role names for backward compatibility.
    Maps legacy role names to current standard role names.

    Role mapping:
    - operator -> analyst
    - viewer -> user
    - admin -> admin (unchanged)

    Args:
        role (str): The role name to normalize

    Returns:
        str: The normalized role name
    """
    role_mapping = {
        'operator': 'analyst',
        'viewer': 'user',
        'admin': 'admin',
        'analyst': 'analyst',
        'user': 'user',
        '超級管理員': 'admin',
        '分析師': 'analyst',
        '操作員': 'analyst',
        '查看者': 'user'
    }

    normalized = role_mapping.get(role, role)
    return normalized

def generate_jwt_token(user_data, expires_hours=24):
    """Generate JWT token for user authentication

    Note: Uses TokenService for centralized JWT operations (Issue #4220).
    """
    import datetime

    original_role = user_data.get('role')
    normalized_role = normalize_role(original_role)

    payload = {
        'user_id': user_data.get('id'),
        'username': user_data.get('username'),
        'role': normalized_role,
        'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=expires_hours),
        'iat': datetime.datetime.now(datetime.UTC)
    }

    # Issue #4220: Use centralized TokenService for JWT operations
    return get_token_service().encode(payload)

def create_admin_token(user_id=1, username='admin'):
    """Create admin JWT token for testing purposes"""
    admin_data = {
        'id': user_id,
        'username': username,
        'role': 'admin'
    }
    return generate_jwt_token(admin_data)

def create_analyst_token():
    """Create analyst JWT token for testing purposes"""
    analyst_data = {
        'id': 2,
        'username': 'analyst',
        'role': 'analyst'
    }
    return generate_jwt_token(analyst_data)

def create_user_token():
    """Create user JWT token for testing purposes"""
    user_data = {
        'id': 3,
        'username': 'user',
        'role': 'user'
    }
    return generate_jwt_token(user_data)

def roles_required(*allowed_roles):
    """
    Decorator for endpoints requiring specific roles.

    Supports multiple authentication sources with fallback:
    1. Authorization header (primary)
    2. X-Access-Token header (fallback)
    3. access_token cookie (fallback)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            payload, error = _decode_jwt_with_fallback()
            if error:
                return error

            raw_role = payload.get('role', 'user')
            normalized_role = normalize_role(raw_role)
            is_platform_admin = payload.get('is_platform_admin', False)

            if normalized_role not in allowed_roles and raw_role not in ['超級管理員'] and not is_platform_admin:
                return jsonify({
                    'error': 'Insufficient privileges',
                    'message': f'Access denied. Required role(s): {", ".join(allowed_roles)}'
                }), 403

            request.current_user = {
                'user_id': payload.get('user_id'),
                'username': payload.get('username'),
                'role': normalized_role,
                'raw_role': raw_role,
                'is_super_admin': raw_role == '超級管理員',
                'is_platform_admin': is_platform_admin
            }

            return f(*args, **kwargs)

        return decorated_function
    return decorator


def platform_admin_required(f):
    """
    Decorator for endpoints requiring platform admin access.

    Platform admins have cross-tenant access and can manage all tenants.
    This is the highest privilege level in the three-tier permission architecture:
    1. Platform Admin - Cross-tenant access (this decorator)
    2. Tenant Admin - Tenant-level management
    3. Tenant User - Standard tenant access

    Supports multiple authentication sources with fallback:
    1. Authorization header (primary)
    2. X-Access-Token header (fallback)
    3. access_token cookie (fallback)
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        payload, error = _decode_jwt_with_fallback()
        if error:
            return error

        raw_role = payload.get('role', 'user')
        normalized_role = normalize_role(raw_role)
        is_platform_admin = payload.get('is_platform_admin', False)

        if not is_platform_admin and raw_role not in ['超級管理員']:
            return jsonify({
                'error': 'Insufficient privileges',
                'message': 'Platform admin access required for this endpoint.'
            }), 403

        user_id = payload.get('sub') or payload.get('user_id')

        request.current_user = {
            'user_id': user_id,
            'username': payload.get('username') or payload.get('email'),
            'role': normalized_role,
            'raw_role': raw_role,
            'is_super_admin': raw_role == '超級管理員',
            'is_platform_admin': True
        }

        request.user_id = user_id

        return f(*args, **kwargs)

    return decorated_function


def check_platform_admin(user_id):
    """
    Check if a user is a platform admin by querying the database.

    Args:
        user_id: UUID of the user to check

    Returns:
        bool: True if user is a platform admin, False otherwise
    """
    try:
        from persistence.db_client import get_client
        client = get_client()
        if client is None:
            logging.warning(f"Supabase client unavailable, cannot check platform admin status for user {user_id}")
            return False
        response = client.table('user_profiles').select(
            'is_platform_admin'
        ).eq('id', user_id).single().execute()
        if response.data:
            return response.data.get('is_platform_admin', False)
        return False
    except Exception:
        logging.exception(f"Failed to check platform admin status for user {user_id}")
        return False


def create_platform_admin_token(user_id=0, username='platform_admin'):
    """Create platform admin JWT token for testing purposes"""
    import datetime

    payload = {
        'user_id': user_id,
        'username': username,
        'role': 'admin',
        'is_platform_admin': True,
        'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=24),
        'iat': datetime.datetime.now(datetime.UTC)
    }

    # Issue #4220: Use centralized TokenService for JWT operations
    return get_token_service().encode(payload)
