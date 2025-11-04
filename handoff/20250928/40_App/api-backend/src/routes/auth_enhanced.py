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
    COOKIE_SAMESITE
)
from src.middleware.csrf import csrf_protect, should_enforce_csrf
import logging

logger = logging.getLogger(__name__)

from src.routes.totp import verify_backup_code_for_login, verify_totp_for_login, check_2fa_required

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
    Login with email and password, with 2FA support
    
    Sets HttpOnly cookies for access and refresh tokens
    
    Request body:
        {
            "email": "user@example.com",
            "password": "password123",
            "totp_code": "123456",  // Optional: for 2FA verification
            "backup_code": "XXXX-XXXX-XXXX-XXXX"  // Optional: alternative to totp_code
        }
    
    Response (2FA required):
        {
            "requires_2fa": true,
            "user": {
                "id": "user-001",
                "email": "user@example.com",
                "role": "owner"
            }
        }
    
    Response (success):
        {
            "user": {
                "id": "user-001",
                "email": "user@example.com",
                "name": "User Name",
                "role": "owner",
                "tenantId": "tenant-001"
            },
            "tokens": {
                "expiresAt": 1234567890000
            },
            "backup_codes_remaining": 7  // Only if backup_code was used
        }
    """
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        totp_code = data.get('totp_code')
        backup_code = data.get('backup_code')
        
        if not email or not password:
            return jsonify({'message': 'Email and password are required'}), 400
        
        user = authenticate_user(email, password)
        if not user:
            return jsonify({'message': 'Invalid email or password'}), 401
        
        user_id = user['id']
        user_role = user['role']
        
        is_2fa_enabled = check_2fa_required(user_id)
        
        if user_role == 'owner' and not is_2fa_enabled:
            return jsonify({
                'requires_2fa': True,
                'message': 'Owner accounts must enable 2FA before login',
                'user': {
                    'id': user_id,
                    'email': user['email'],
                    'role': user_role
                }
            }), 200
        
        if is_2fa_enabled:
            if not totp_code and not backup_code:
                return jsonify({
                    'requires_2fa': True,
                    'user': {
                        'id': user_id,
                        'email': user['email'],
                        'role': user_role
                    }
                }), 200
            
            if totp_code:
                if not verify_totp_for_login(user_id, totp_code):
                    return jsonify({'message': 'Invalid TOTP code'}), 401
            elif backup_code:
                is_valid, remaining_codes = verify_backup_code_for_login(user_id, backup_code)
                if not is_valid:
                    return jsonify({'message': 'Invalid backup code'}), 401
        
        access_token, access_expiry_ms = generate_access_token(
            user_id, user['email'], user_role
        )
        refresh_token = generate_refresh_token(user_id, user['email'])
        
        response_data = {
            'user': {
                'id': user_id,
                'email': user['email'],
                'name': user['name'],
                'role': user_role,
                'tenantId': user['tenant_id'],
                'avatar': user.get('avatar')
            },
            'tokens': {
                'expiresAt': access_expiry_ms
            }
        }
        
        if backup_code and is_2fa_enabled:
            _, remaining_codes = verify_backup_code_for_login(user_id, backup_code)
            response_data['backup_codes_remaining'] = remaining_codes
        
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
