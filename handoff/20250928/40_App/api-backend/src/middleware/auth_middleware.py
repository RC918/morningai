import jwt
import os
import logging
from functools import wraps
from flask import request, jsonify, current_app
from common.config.settings import get_settings

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
                version = pkg_resources.get_distribution("PyJWT").version
            except (ImportError, ModuleNotFoundError):
                from importlib import metadata
                version = metadata.version("PyJWT")
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
        'message': 'Please provide a valid JWT token via Authorization header, X-Access-Token header, or access_token cookie.'
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

def _try_decode_token(token, jwt_secret):
    """
    Try to decode a JWT token.
    
    Args:
        token: JWT token string
        jwt_secret: Secret key for decoding
        
    Returns:
        tuple: (payload, exception) where exception is None if successful
    """
    try:
        payload = jwt.decode(token, jwt_secret, algorithms=['HS256'])
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
    jwt_secret = get_settings().jwt_secret_key or 'test-secret-key-for-testing'
    primary_error = None
    
    auth_header = request.headers.get('Authorization')
    if auth_header:
        token, parse_error = _parse_bearer_token(auth_header)
        if parse_error:
            primary_error = parse_error
            logging.warning(f"Invalid Authorization header format, trying fallback methods: {parse_error[0].get_json()}")
        else:
            payload, decode_error = _try_decode_token(token, jwt_secret)
            if payload:
                return payload, None
            primary_error = _error_response_from_exception(decode_error)
            logging.warning(f"Authorization token decode failed, trying fallback methods: {primary_error[0].get_json()}")
    
    x_access_token = request.headers.get('X-Access-Token')
    if x_access_token:
        payload, decode_error = _try_decode_token(x_access_token, jwt_secret)
        if payload:
            return payload, None
    
    cookie_token = request.cookies.get('access_token')
    if cookie_token:
        payload, decode_error = _try_decode_token(cookie_token, jwt_secret)
        if payload:
            return payload, None
    
    if primary_error:
        return None, primary_error
    
    return None, (jsonify({
        'error': 'Authorization header missing',
        'message': 'Please provide a valid JWT token via Authorization header, X-Access-Token header, or access_token cookie.'
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
        
        request.current_user = {
            'user_id': user_id,
            'username': payload.get('username') or payload.get('email'),
            'role': normalized_role,
            'raw_role': raw_role,
            'is_super_admin': raw_role == '超級管理員'
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
        if normalized_role not in ['admin'] and raw_role not in ['超級管理員']:
            return jsonify({
                'error': 'Insufficient privileges',
                'message': 'Admin access required for this endpoint.'
            }), 403
        
        request.current_user = {
            'user_id': payload.get('user_id'),
            'username': payload.get('username'),
            'role': normalized_role,
            'raw_role': raw_role,
            'is_super_admin': raw_role == '超級管理員'
        }
        
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
        if normalized_role not in ['admin', 'analyst'] and raw_role not in ['超級管理員', '分析師']:
            return jsonify({
                'error': 'Insufficient privileges',
                'message': 'Analyst access or higher required for this endpoint.'
            }), 403
        
        request.current_user = {
            'user_id': payload.get('user_id'),
            'username': payload.get('username'),
            'role': normalized_role,
            'raw_role': raw_role,
            'is_super_admin': raw_role == '超級管理員'
        }
        
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
    
    Note: Uses a default test secret if JWT_SECRET_KEY is not set.
    This is for testing purposes only. Production deployments must set JWT_SECRET_KEY.
    """
    import datetime
    
    jwt_secret = get_settings().jwt_secret_key or 'test-secret-key-for-testing'
    
    original_role = user_data.get('role')
    normalized_role = normalize_role(original_role)
    
    payload = {
        'user_id': user_data.get('id'),
        'username': user_data.get('username'),
        'role': normalized_role,
        'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=expires_hours),
        'iat': datetime.datetime.now(datetime.UTC)
    }
    
    return jwt.encode(payload, jwt_secret, algorithm='HS256')

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
            
            if normalized_role not in allowed_roles and raw_role not in ['超級管理員']:
                return jsonify({
                    'error': 'Insufficient privileges',
                    'message': f'Access denied. Required role(s): {", ".join(allowed_roles)}'
                }), 403
            
            request.current_user = {
                'user_id': payload.get('user_id'),
                'username': payload.get('username'),
                'role': normalized_role,
                'raw_role': raw_role,
                'is_super_admin': raw_role == '超級管理員'
            }
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator
