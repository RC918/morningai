"""
CSRF Protection Middleware

Implements double-submit cookie pattern for CSRF protection.
Required when using SameSite=None cookies for cross-domain deployments.

How it works:
1. Server sets a non-HttpOnly csrf_token cookie
2. Frontend reads csrf_token from cookie and sends it in X-CSRF-Token header
3. Server validates that header matches cookie for unsafe methods (POST/PUT/PATCH/DELETE)
"""

import logging
from flask import request, jsonify
from functools import wraps

logger = logging.getLogger(__name__)

UNSAFE_METHODS = {'POST', 'PUT', 'PATCH', 'DELETE'}

CSRF_EXEMPT_PATHS = {
    '/api/auth/v2/login',  # Login doesn't have CSRF token yet
    '/api/auth/v2/csrf',   # CSRF bootstrap endpoint
}


def csrf_protect(f):
    """
    Decorator to protect routes with CSRF validation
    
    Usage:
        @app.route('/api/some-route', methods=['POST'])
        @csrf_protect
        def some_route():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method not in UNSAFE_METHODS:
            return f(*args, **kwargs)
        
        if request.path in CSRF_EXEMPT_PATHS:
            return f(*args, **kwargs)
        
        if not should_enforce_csrf():
            logger.debug(f"CSRF protection not enforced for {request.path} (SameSite != None)")
            return f(*args, **kwargs)
        
        csrf_cookie = request.cookies.get('csrf_token')
        if not csrf_cookie:
            logger.warning(f"CSRF validation failed: No csrf_token cookie for {request.path}")
            return jsonify({'error': 'CSRF token missing'}), 403
        
        csrf_header = request.headers.get('X-CSRF-Token')
        if not csrf_header:
            logger.warning(f"CSRF validation failed: No X-CSRF-Token header for {request.path}")
            return jsonify({'error': 'CSRF token missing in header'}), 403
        
        if csrf_cookie != csrf_header:
            logger.warning(f"CSRF validation failed: Token mismatch for {request.path}")
            return jsonify({'error': 'CSRF token invalid'}), 403
        
        logger.debug(f"CSRF validation passed for {request.path}")
        return f(*args, **kwargs)
    
    return decorated_function


def should_enforce_csrf() -> bool:
    """
    Determine if CSRF protection should be enforced
    
    CSRF is required when:
    - SameSite=None (cross-domain cookies)
    
    Returns:
        True if CSRF should be enforced
    """
    from common.config.settings import settings
    cookie_samesite = settings.cookie_samesite or 'Strict'
    return cookie_samesite == 'None'
