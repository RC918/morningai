"""
Enhanced Authentication Routes for Owner Console
Task 1: Enhanced Token Security

Endpoints:
- POST /api/auth/login - Login with HttpOnly cookies
- POST /api/auth/refresh - Refresh access token with rotation
- POST /api/auth/logout - Logout and blacklist refresh token
- GET /api/auth/me - Get current user info
"""

from flask import Blueprint, request, jsonify, make_response
from src.services.auth_service import (
    authenticate_user,
    generate_access_token,
    generate_refresh_token,
    verify_access_token,
    verify_refresh_token,
    rotate_refresh_token,
    blacklist_refresh_token,
    set_auth_cookies,
    clear_auth_cookies,
    get_user_by_id,
    generate_csrf_token,
    COOKIE_SAMESITE,
    COOKIE_SECURE,
    FEATURE_2FA_PREAUTH,
    PREAUTH_TOKEN_TTL
)
from common.config.settings import get_settings
from src.middleware.csrf import csrf_protect
from src.utils.pre_auth_token import get_pre_auth_manager
import logging

logger = logging.getLogger(__name__)


def generate_preauth_token(user_id: str, email: str, ttl: int = None) -> str:
    """
    Generate a pre-authentication token (JWT-based).
    
    This is a compatibility wrapper for the new JWT-based pre-auth system.
    The ttl parameter is ignored as the token expiry is managed by PreAuthTokenManager.
    
    Args:
        user_id: User ID
        email: User email
        ttl: Token TTL in seconds (ignored, kept for compatibility)
    
    Returns:
        JWT token string
    """
    pre_auth_manager = get_pre_auth_manager()
    return pre_auth_manager.generate_token(user_id, email, scope='challenge')

auth_enhanced_bp = Blueprint('auth_enhanced', __name__)


@auth_enhanced_bp.route('/csrf', methods=['GET'])
def get_csrf_token():
    """
    Get CSRF token for authentication
    
    This endpoint allows the frontend to bootstrap CSRF protection
    before making authenticated requests.
    
    P1 Enhancement: Cache-Control headers to prevent token caching
    - Ensures each request generates a fresh CSRF token
    - Prevents browsers/proxies from serving stale tokens
    
    Response:
        {
            "csrf_token": "abc123..."
        }
    """
    try:
        csrf_token = generate_csrf_token()
        
        response_data = {
            'csrf_token': csrf_token
        }
        
        response = make_response(jsonify(response_data), 200)
        
        response.headers['Cache-Control'] = (
            'no-store, no-cache, must-revalidate, max-age=0'
        )
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        from src.services.auth_service import create_cookie_config, ACCESS_TOKEN_EXPIRY_MINUTES
        response.set_cookie(
            **create_cookie_config('csrf_token', csrf_token, ACCESS_TOKEN_EXPIRY_MINUTES * 60, httponly=False)
        )
        
        logger.debug("CSRF token generated")
        return response
        
    except Exception as e:
        logger.exception(f"CSRF token generation failed: {e}")
        return jsonify({'message': 'Failed to generate CSRF token'}), 500


@auth_enhanced_bp.route('/login', methods=['POST'])
def login():
    """
    Login with email and password
    
    Returns next_step to indicate the next action required:
    - "enroll_2fa": User needs to set up 2FA (first time)
    - "challenge_2fa": User needs to verify 2FA code
    - "session": Login complete, session issued
    
    Request body:
        {
            "email": "user@example.com",
            "password": "password123"
        }
    
    Response (2FA enrollment required):
        {
            "requires_2fa": true,
            "next_step": "enroll_2fa",
            "token": "tmp_login_token...",
            "user": {
                "id": "user-001",
                "email": "user@example.com"
            }
        }
    
    Response (2FA challenge required):
        {
            "requires_2fa": true,
            "next_step": "challenge_2fa",
            "token": "tmp_login_token...",
            "user": {
                "id": "user-001",
                "email": "user@example.com"
            }
        }
    
    Response (session issued):
        {
            "next_step": "session",
            "user": {
                "id": "user-001",
                "email": "user@example.com",
                "name": "User Name",
                "role": "owner",
                "tenantId": "tenant-001"
            },
            "tokens": {
                "expiresAt": 1234567890000
            }
        }
    """
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'message': 'Email and password are required'}), 400
        
        user = authenticate_user(email, password)
        if not user:
            return jsonify({'message': 'Invalid email or password'}), 401
        
        from .totp import check_2fa_required
        from supabase import create_client
        
        if check_2fa_required(user['id'], user['role']):
            next_step = 'enroll_2fa'

            supabase_url = get_settings().supabase_url
            supabase_key = get_settings().supabase_service_role_key
            
            if supabase_url and supabase_key:
                try:
                    supabase = create_client(supabase_url, supabase_key)
                    user_2fa = supabase.table('user_2fa').select('*').eq('user_id', user['id']).execute()
                    
                    if user_2fa.data and user_2fa.data[0].get('enabled') and user_2fa.data[0].get('verified_at'):
                        next_step = 'challenge_2fa'
                except Exception as supabase_error:
                    logger.warning(
                        f"Supabase query failed for user {user['email']}, "
                        f"defaulting to enroll_2fa: {supabase_error}"
                    )
            
            tmp_token = generate_preauth_token(
                user_id=user['id'],
                email=user['email'],
                ttl=PREAUTH_TOKEN_TTL
            )
            
            # Generate a short-lived JWT access token for 2FA API calls
            access_token, access_expiry_ms = generate_access_token(
                user['id'], user['email'], user['role']
            )
            
            response_data = {
                'requires_2fa': True,
                'next_step': next_step,
                'token': tmp_token,
                'user': {
                    'id': user['id'],
                    'email': user['email']
                },
                'tokens': {
                    'accessToken': access_token,
                    'expiresAt': access_expiry_ms
                }
            }
            
            logger.info(f"User {user['email']} (role: {user['role']}) requires 2FA: {next_step}")
            
            response = make_response(jsonify(response_data), 200)
            
            if FEATURE_2FA_PREAUTH:
                try:
                    response.set_cookie(
                        'pre_auth_token',
                        tmp_token,
                        max_age=PREAUTH_TOKEN_TTL,
                        httponly=True,
                        secure=COOKIE_SECURE,
                        samesite=COOKIE_SAMESITE,
                        path='/api/auth/v2/2fa'
                    )
                    
                    logger.info(f"Pre-auth token set for user {user['id']}")
                except Exception as e:
                    logger.error(f"Failed to set pre-auth token cookie: {e}")
            
            return response
        
        access_token, access_expiry_ms = generate_access_token(
            user['id'], user['email'], user['role']
        )
        refresh_token = generate_refresh_token(user['id'], user['email'])
        
        response_data = {
            'next_step': 'session',
            'user': {
                'id': user['id'],
                'email': user['email'],
                'name': user['name'],
                'role': user['role'],
                'tenantId': user['tenant_id'],
                'avatar': user.get('avatar')
            },
            'tokens': {
                'accessToken': access_token,
                'expiresAt': access_expiry_ms
            }
        }
        
        response = make_response(jsonify(response_data), 200)
        set_auth_cookies(response, access_token, refresh_token, access_expiry_ms)
        
        logger.info(f"User logged in successfully: {user['email']}")
        return response
        
    except Exception as e:
        logger.exception(f"Login failed: {e}")
        return jsonify({'message': 'Login failed, please try again'}), 500


@auth_enhanced_bp.route('/refresh', methods=['POST'])
@csrf_protect
def refresh():
    """
    Refresh access token using refresh token
    
    Implements token rotation: old refresh token is blacklisted, new one is issued
    
    Request: Reads refresh_token from HttpOnly cookie
    
    Response:
        {
            "tokens": {
                "expiresAt": 1234567890000
            }
        }
    """
    try:
        refresh_token = request.cookies.get('refresh_token')
        
        if not refresh_token:
            return jsonify({'message': 'No refresh token provided'}), 401
        
        payload = verify_refresh_token(refresh_token)
        if not payload:
            return jsonify({'message': 'Invalid or expired refresh token'}), 401
        
        user_id = payload.get('user_id')
        email = payload.get('email')
        
        user = get_user_by_id(user_id)
        if not user:
            return jsonify({'message': 'User not found'}), 401
        
        access_token, access_expiry_ms = generate_access_token(
            user_id, email, user['role']
        )
        
        new_refresh_token = rotate_refresh_token(refresh_token, user_id, email)
        if not new_refresh_token:
            logger.error("Failed to rotate refresh token")
            return jsonify({'message': 'Token refresh failed'}), 500
        
        response_data = {
            'tokens': {
                'accessToken': access_token,
                'expiresAt': access_expiry_ms
            }
        }
        
        response = make_response(jsonify(response_data), 200)
        set_auth_cookies(response, access_token, new_refresh_token, access_expiry_ms)
        
        logger.info(f"Token refreshed successfully for user: {user_id}")
        return response
        
    except Exception as e:
        logger.exception(f"Token refresh failed: {e}")
        return jsonify({'message': 'Token refresh failed'}), 500


@auth_enhanced_bp.route('/logout', methods=['POST'])
@csrf_protect
def logout():
    """
    Logout and blacklist refresh token
    
    Request: Reads refresh_token from HttpOnly cookie
    
    Response:
        {
            "message": "Logged out successfully"
        }
    """
    try:
        refresh_token = request.cookies.get('refresh_token')
        
        if refresh_token:
            blacklist_refresh_token(refresh_token)
            logger.info("Refresh token blacklisted on logout")
        
        response = make_response(jsonify({'message': 'Logged out successfully'}), 200)
        clear_auth_cookies(response)
        
        return response
        
    except Exception as e:
        logger.exception(f"Logout failed: {e}")
        response = make_response(jsonify({'message': 'Logged out successfully'}), 200)
        clear_auth_cookies(response)
        return response


@auth_enhanced_bp.route('/me', methods=['GET'])
def get_current_user():
    """
    Get current authenticated user
    
    Request: Reads access_token from HttpOnly cookie
    
    Response:
        {
            "id": "user-001",
            "email": "user@example.com",
            "name": "User Name",
            "role": "owner",
            "tenantId": "tenant-001"
        }
    """
    try:
        access_token = request.cookies.get('access_token')
        
        if not access_token:
            return jsonify({'message': 'Not authenticated'}), 401
        
        payload = verify_access_token(access_token)
        if not payload:
            return jsonify({'message': 'Invalid or expired access token'}), 401
        
        user_id = payload.get('user_id')
        
        user = get_user_by_id(user_id)
        if not user:
            return jsonify({'message': 'User not found'}), 401
        
        return jsonify({
            'id': user['id'],
            'email': user['email'],
            'name': user['name'],
            'role': user['role'],
            'tenantId': user['tenant_id'],
            'avatar': user.get('avatar')
        }), 200
        
    except Exception as e:
        logger.exception(f"Get current user failed: {e}")
        return jsonify({'message': 'Failed to get user info'}), 500


@auth_enhanced_bp.route('/verify', methods=['GET'])
def verify_token():
    """
    Verify access token (legacy endpoint for compatibility)
    
    Request: Reads access_token from HttpOnly cookie or Authorization header
    
    Response:
        {
            "id": "user-001",
            "email": "user@example.com",
            "name": "User Name",
            "role": "owner"
        }
    """
    try:
        access_token = request.cookies.get('access_token')
        
        if not access_token:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                access_token = auth_header.split(' ')[1]
        
        if not access_token:
            return jsonify({'message': 'Not authenticated'}), 401
        
        payload = verify_access_token(access_token)
        if not payload:
            return jsonify({'message': 'Invalid or expired token'}), 401
        
        user_id = payload.get('user_id')
        
        user = get_user_by_id(user_id)
        if not user:
            return jsonify({'message': 'User not found'}), 401
        
        return jsonify({
            'id': user['id'],
            'email': user['email'],
            'name': user['name'],
            'role': user['role']
        }), 200
        
    except Exception as e:
        logger.exception(f"Token verification failed: {e}")
        return jsonify({'message': 'Token verification failed'}), 500
