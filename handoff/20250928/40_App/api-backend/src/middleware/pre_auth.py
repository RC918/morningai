"""
Pre-Authentication Middleware

Provides decorator for protecting endpoints that require pre-authentication tokens.
These tokens are issued after successful first-factor authentication (email/password)
and are used for 2FA enrollment and challenge flows.

Usage:
    @pre_auth_required
    def enroll_2fa():
        user_id = request.pre_auth_user_id
        scope = request.pre_auth_scope
        ...
"""

import logging
from functools import wraps
from flask import request, jsonify

from ..utils.pre_auth_token import get_pre_auth_manager

logger = logging.getLogger(__name__)


def pre_auth_required(f):
    """
    Decorator for endpoints requiring pre-authentication token.
    
    Validates the token, checks single-use enforcement, and rate limiting.
    Sets request.pre_auth_user_id, request.pre_auth_email, and request.pre_auth_scope.
    
    Usage:
        @pre_auth_required
        def my_endpoint():
            user_id = request.pre_auth_user_id
            scope = request.pre_auth_scope  # 'enroll' or 'challenge'
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({
                'error': 'TMP_TOKEN_MISSING',
                'message': 'Pre-authentication token required. Please login first.'
            }), 401
        
        try:
            parts = auth_header.split(' ')
            if len(parts) != 2 or parts[0].lower() != 'bearer':
                return jsonify({
                    'error': 'INVALID_TOKEN_FORMAT',
                    'message': 'Authorization header must be in format: Bearer <token>'
                }), 401
            
            token = parts[1]
        except (IndexError, AttributeError):
            return jsonify({
                'error': 'INVALID_TOKEN_FORMAT',
                'message': 'Authorization header must be in format: Bearer <token>'
            }), 401
        
        manager = get_pre_auth_manager()
        payload = manager.verify_token(token)
        
        if not payload:
            return jsonify({
                'error': 'TMP_TOKEN_INVALID',
                'message': 'Pre-authentication token is invalid, expired, or already used.'
            }), 401
        
        user_id = payload.get('user_id')
        email = payload.get('email')
        scope = payload.get('scope')
        jti = payload.get('jti')
        
        if not all([user_id, email, scope, jti]):
            logger.error(f"Pre-auth token missing required claims: {payload}")
            return jsonify({
                'error': 'TMP_TOKEN_INVALID',
                'message': 'Pre-authentication token is malformed.'
            }), 401
        
        request.pre_auth_user_id = user_id
        request.pre_auth_email = email
        request.pre_auth_scope = scope
        request.pre_auth_jti = jti
        
        logger.debug(f"Pre-auth request: user_id={user_id}, scope={scope}, jti={jti}")
        
        return f(*args, **kwargs)
    
    return decorated_function


def pre_auth_scope_required(required_scope: str):
    """
    Decorator for endpoints requiring specific pre-auth scope.
    
    Args:
        required_scope: Required scope ('enroll' or 'challenge')
    
    Usage:
        @pre_auth_required
        @pre_auth_scope_required('enroll')
        def enroll_endpoint():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            scope = getattr(request, 'pre_auth_scope', None)
            
            if not scope:
                return jsonify({
                    'error': 'SCOPE_MISSING',
                    'message': 'Pre-authentication scope not found. Use @pre_auth_required first.'
                }), 500
            
            if scope != required_scope:
                return jsonify({
                    'error': 'SCOPE_MISMATCH',
                    'message': f'This endpoint requires scope "{required_scope}", got "{scope}".'
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator
