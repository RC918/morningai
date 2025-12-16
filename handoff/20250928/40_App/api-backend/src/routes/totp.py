"""
TOTP/2FA Routes for Authentication

Provides endpoints for:
- TOTP setup and enrollment
- TOTP verification
- TOTP disable
- Backup code management
- Login with TOTP

Security:
- All endpoints require authentication (except login)
- Password confirmation required for sensitive operations
- Rate limiting applied to prevent brute force
- TOTP secrets encrypted at rest
"""

import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, make_response
from supabase import create_client

from ..services.auth_service import (
    get_user_by_id,
    authenticate_user,
    COOKIE_SECURE,
    COOKIE_SAMESITE
)
from ..utils.totp_utils import TOTPManager, BackupCodeManager, generate_device_fingerprint, calculate_device_expiry
from ..utils.pre_auth_token import get_pre_auth_manager
from ..middleware.auth_middleware import jwt_required
from ..middleware.rate_limit import rate_limit
from ..middleware.csrf import csrf_protect
from common.config.settings import get_settings

logger = logging.getLogger(__name__)

totp_bp = Blueprint('totp', __name__, url_prefix='/api/auth/v2/totp')


def validate_and_consume_preauth_token(token: str):
    """
    Validate and consume a pre-authentication token (JWT-based).
    
    This is a compatibility wrapper for the new JWT-based pre-auth system.
    
    Args:
        token: JWT token string
    
    Returns:
        Dict with 'id' and 'email' if valid and consumed, None otherwise
    """
    try:
        pre_auth_manager = get_pre_auth_manager()
        
        payload = pre_auth_manager.verify_token(token)
        if not payload:
            return None
        
        if payload.get('scope') != 'challenge':
            logger.warning(f"Token has wrong scope: {payload.get('scope')}, expected 'challenge'")
            return None
        
        jti = payload.get('jti')
        if not jti:
            logger.warning("Token missing jti claim")
            return None
        
        consumed = pre_auth_manager.consume_token_atomic(jti)
        if not consumed:
            logger.warning(f"Failed to consume token jti {jti}")
            return None
        
        return {
            'id': payload.get('user_id'),
            'email': payload.get('email')
        }
    except Exception as e:
        logger.error(f"Error validating/consuming pre-auth token: {e}", exc_info=True)
        return None

_totp_manager = None
_backup_manager = None


def is_2fa_feature_enabled() -> bool:
    """
    Check if 2FA feature is enabled via feature flag.
    
    2FA is disabled in test mode (Flask TESTING=True) to keep existing tests unchanged,
    unless FORCE_ENABLE_2FA_IN_TESTS is set to 'true' (for TOTP API tests).
    In production/staging, Owner role enforcement remains active.
    
    Returns:
        True if FEATURE_2FA_ENABLED is set to 'true' (case-insensitive), False otherwise
        False if running in Flask test mode (TESTING=True) unless forced
    """
    from common.config.settings import settings
    
    try:
        from flask import current_app
        if current_app and current_app.config.get('TESTING'):
            return settings.force_enable_2fa_in_tests
    except (ImportError, RuntimeError):
        pass
    
    return settings.feature_2fa_enabled


def get_totp_manager():
    """Get or create TOTPManager instance (lazy initialization)."""
    global _totp_manager
    if _totp_manager is None:
        _totp_manager = TOTPManager()
    return _totp_manager


def get_backup_manager():
    """Get or create BackupCodeManager instance (lazy initialization)."""
    global _backup_manager
    if _backup_manager is None:
        _backup_manager = BackupCodeManager()
    return _backup_manager


@totp_bp.route('/setup', methods=['POST'])
@jwt_required
@rate_limit  # 3 attempts per hour
def setup_totp():
    """
    Setup TOTP for the authenticated user.
    
    **DEPRECATED**: This endpoint requires JWT authentication, which breaks forced 2FA flows.
    Use the new pre-authentication endpoints instead:
    - POST /api/auth/v2/2fa/enroll (requires pre_auth_token, no JWT)
    - POST /api/auth/v2/2fa/verify-enroll (requires pre_auth_token, no JWT)
    
    This endpoint will be removed in a future version.
    
    Request:
        {
            "password": "user_password_for_confirmation"
        }
    
    Response:
        {
            "secret": "BASE32_ENCODED_SECRET",
            "qr_code": "data:image/png;base64,...",
            "backup_codes": ["XXXX-XXXX-XXXX-XXXX", ...]
        }
    """
    logger.warning("DEPRECATED: /totp/setup endpoint called. Use /api/auth/v2/2fa/enroll instead.")
    
    if not is_2fa_feature_enabled():
        return jsonify({'error': '2FA feature is not enabled'}), 403
    
    try:
        data = request.get_json()
        password = data.get('password')
        
        if not password:
            return jsonify({'error': 'Password confirmation required'}), 400
        
        user_id = request.user_id
        user = get_user_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Supabase users don't have hashed_password in the user object, so we use authenticate_user
        if not authenticate_user(user.get('email'), password):
            return jsonify({'error': 'Invalid password'}), 401
        
        supabase_url = get_settings().supabase_url
        supabase_key = get_settings().supabase_service_role_key
        supabase = create_client(supabase_url, supabase_key)
        
        existing_2fa = supabase.table('user_2fa').select('*').eq('user_id', user_id).execute()
        
        if existing_2fa.data and existing_2fa.data[0].get('enabled'):
            return jsonify({'error': '2FA is already enabled. Disable it first to re-setup.'}), 400
        
        secret = get_totp_manager().generate_secret()
        encrypted_secret = get_totp_manager().encrypt_secret(secret)
        
        user_email = user.get('email', '')
        qr_code = get_totp_manager().generate_qr_code(secret, user_email)
        
        backup_codes = get_backup_manager().generate_backup_codes(8)
        
        if existing_2fa.data:
            supabase.table('user_2fa').update({
                'secret_encrypted': encrypted_secret,
                'enabled': False,
                'verified_at': None,
                'created_at': datetime.utcnow().isoformat()
            }).eq('user_id', user_id).execute()
        else:
            supabase.table('user_2fa').insert({
                'user_id': user_id,
                'secret_encrypted': encrypted_secret,
                'enabled': False
            }).execute()
        
        supabase.table('totp_backup_codes').delete().eq('user_id', user_id).execute()
        
        backup_code_records = [
            {
                'user_id': user_id,
                'code_hash': get_backup_manager().hash_backup_code(code),
                'used': False
            }
            for code in backup_codes
        ]
        supabase.table('totp_backup_codes').insert(backup_code_records).execute()
        
        logger.info(f"TOTP setup initiated for user {user_id}")
        
        return jsonify({
            'secret': secret,
            'qr_code': qr_code,
            'backup_codes': backup_codes
        }), 200
        
    except Exception as e:
        logger.error(f"Error in TOTP setup: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@totp_bp.route('/verify-setup', methods=['POST'])
@jwt_required
@rate_limit  # 5 attempts per 5 minutes
def verify_totp_setup():
    """
    Verify TOTP code and enable 2FA.
    
    Request:
        {
            "code": "123456"
        }
    
    Response:
        {
            "success": true,
            "enabled": true
        }
    """
    if not is_2fa_feature_enabled():
        return jsonify({'error': '2FA feature is not enabled'}), 403
    
    try:
        data = request.get_json()
        code = data.get('code', '').strip()
        
        if not code or len(code) != 6 or not code.isdigit():
            return jsonify({'error': 'Invalid TOTP code format (must be 6 digits)'}), 400
        
        user_id = request.user_id
        
        supabase_url = get_settings().supabase_url
        supabase_key = get_settings().supabase_service_role_key
        supabase = create_client(supabase_url, supabase_key)
        user_2fa = supabase.table('user_2fa').select('*').eq('user_id', user_id).execute()
        
        if not user_2fa.data:
            return jsonify({'error': '2FA not set up. Call /setup first.'}), 400
        
        user_2fa_record = user_2fa.data[0]
        
        if user_2fa_record.get('enabled'):
            return jsonify({'error': '2FA is already enabled'}), 400
        
        encrypted_secret = user_2fa_record['secret_encrypted']
        secret = get_totp_manager().decrypt_secret(encrypted_secret)
        
        if not get_totp_manager().verify_totp(secret, code, valid_window=1):
            return jsonify({'error': 'Invalid TOTP code'}), 401
        
        supabase.table('user_2fa').update({
            'enabled': True,
            'verified_at': datetime.utcnow().isoformat()
        }).eq('user_id', user_id).execute()
        
        logger.info(f"2FA enabled for user {user_id}")
        
        return jsonify({
            'success': True,
            'enabled': True
        }), 200
        
    except Exception as e:
        logger.error(f"Error in TOTP verification: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@totp_bp.route('/disable', methods=['POST'])
@jwt_required
@rate_limit  # 5 attempts per 5 minutes
def disable_totp():
    """
    Disable TOTP for the authenticated user.
    
    Request:
        {
            "password": "user_password_for_confirmation",
            "totp_code": "123456"
        }
    
    Response:
        {
            "success": true,
            "enabled": false
        }
    """
    if not is_2fa_feature_enabled():
        return jsonify({'error': '2FA feature is not enabled'}), 403
    
    try:
        data = request.get_json()
        password = data.get('password')
        totp_code = data.get('totp_code', '').strip()
        
        if not password or not totp_code or len(totp_code) != 6 or not totp_code.isdigit():
            return jsonify({'error': 'Password and valid TOTP code (6 digits) required'}), 400
        
        user_id = request.user_id
        user = get_user_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Supabase users don't have hashed_password in the user object, so we use authenticate_user
        if not authenticate_user(user.get('email'), password):
            return jsonify({'error': 'Invalid password'}), 401
        
        supabase_url = get_settings().supabase_url
        supabase_key = get_settings().supabase_service_role_key
        supabase = create_client(supabase_url, supabase_key)
        user_2fa = supabase.table('user_2fa').select('*').eq('user_id', user_id).execute()
        
        if not user_2fa.data or not user_2fa.data[0].get('enabled'):
            return jsonify({'error': '2FA is not enabled'}), 400
        
        encrypted_secret = user_2fa.data[0]['secret_encrypted']
        secret = get_totp_manager().decrypt_secret(encrypted_secret)
        
        if not get_totp_manager().verify_totp(secret, totp_code, valid_window=1):
            return jsonify({'error': 'Invalid TOTP code'}), 401
        
        supabase.table('user_2fa').update({
            'enabled': False
        }).eq('user_id', user_id).execute()
        
        supabase.table('totp_backup_codes').delete().eq('user_id', user_id).execute()
        
        supabase.table('trusted_devices').delete().eq('user_id', user_id).execute()
        
        logger.info(f"2FA disabled for user {user_id}")
        
        return jsonify({
            'success': True,
            'enabled': False
        }), 200
        
    except Exception as e:
        logger.error(f"Error disabling TOTP: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@totp_bp.route('/backup-codes/regenerate', methods=['POST'])
@jwt_required
@rate_limit  # 3 attempts per hour
def regenerate_backup_codes():
    """
    Regenerate backup codes for the authenticated user.
    
    Request:
        {
            "password": "user_password_for_confirmation"
        }
    
    Response:
        {
            "backup_codes": ["XXXX-XXXX-XXXX-XXXX", ...]
        }
    """
    if not is_2fa_feature_enabled():
        return jsonify({'error': '2FA feature is not enabled'}), 403
    
    try:
        data = request.get_json()
        password = data.get('password')
        
        if not password:
            return jsonify({'error': 'Password confirmation required'}), 400
        
        user_id = request.user_id
        user = get_user_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Supabase users don't have hashed_password in the user object, so we use authenticate_user
        if not authenticate_user(user.get('email'), password):
            return jsonify({'error': 'Invalid password'}), 401
        
        supabase_url = get_settings().supabase_url
        supabase_key = get_settings().supabase_service_role_key
        supabase = create_client(supabase_url, supabase_key)
        user_2fa = supabase.table('user_2fa').select('*').eq('user_id', user_id).execute()
        
        if not user_2fa.data or not user_2fa.data[0].get('enabled'):
            return jsonify({'error': '2FA is not enabled'}), 400
        
        backup_codes = get_backup_manager().generate_backup_codes(8)
        
        supabase.table('totp_backup_codes').delete().eq('user_id', user_id).execute()
        
        backup_code_records = [
            {
                'user_id': user_id,
                'code_hash': get_backup_manager().hash_backup_code(code),
                'used': False
            }
            for code in backup_codes
        ]
        supabase.table('totp_backup_codes').insert(backup_code_records).execute()
        
        logger.info(f"Backup codes regenerated for user {user_id}")
        
        return jsonify({
            'backup_codes': backup_codes
        }), 200
        
    except Exception as e:
        logger.error(f"Error regenerating backup codes: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@totp_bp.route('/status', methods=['GET'])
@jwt_required
def get_totp_status():
    """
    Get 2FA status for the authenticated user.
    
    Response:
        {
            "enabled": true,
            "verified_at": "2025-11-02T12:00:00",
            "backup_codes_remaining": 7
        }
    """
    if not is_2fa_feature_enabled():
        return jsonify({
            'enabled': False,
            'verified_at': None,
            'backup_codes_remaining': 0,
            'feature_disabled': True
        }), 200
    
    try:
        user_id = request.user_id
        
        supabase_url = get_settings().supabase_url
        supabase_key = get_settings().supabase_service_role_key
        supabase = create_client(supabase_url, supabase_key)
        
        user_2fa = supabase.table('user_2fa').select('*').eq('user_id', user_id).execute()
        
        if not user_2fa.data:
            return jsonify({
                'enabled': False,
                'verified_at': None,
                'backup_codes_remaining': 0
            }), 200
        
        user_2fa_record = user_2fa.data[0]
        
        backup_codes = (
            supabase.table('totp_backup_codes')
            .select('*').eq('user_id', user_id).eq('used', False).execute()
        )
        
        return jsonify({
            'enabled': user_2fa_record.get('enabled', False),
            'verified_at': user_2fa_record.get('verified_at'),
            'backup_codes_remaining': len(backup_codes.data) if backup_codes.data else 0
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting TOTP status: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


def verify_totp_for_login(user_id: str, totp_code: str) -> bool:
    """
    Verify TOTP code during login.
    
    Args:
        user_id: User ID
        totp_code: 6-digit TOTP code from user
        
    Returns:
        True if code is valid, False otherwise
    """
    try:
        supabase_url = get_settings().supabase_url
        supabase_key = get_settings().supabase_service_role_key
        supabase = create_client(supabase_url, supabase_key)
        user_2fa = supabase.table('user_2fa').select('*').eq('user_id', user_id).eq('enabled', True).execute()
        
        if not user_2fa.data:
            return False
        
        encrypted_secret = user_2fa.data[0]['secret_encrypted']
        secret = get_totp_manager().decrypt_secret(encrypted_secret)
        
        is_valid = get_totp_manager().verify_totp(secret, totp_code, valid_window=1)
        
        if is_valid:
            supabase.table('user_2fa').update({
                'last_used_at': datetime.utcnow().isoformat()
            }).eq('user_id', user_id).execute()
        
        return is_valid
        
    except Exception as e:
        logger.error(f"Error verifying TOTP for login: {str(e)}", exc_info=True)
        return False


def verify_backup_code_for_login(user_id: str, backup_code: str) -> tuple[bool, int]:
    """
    Verify backup code during login.
    
    Args:
        user_id: User ID
        backup_code: Backup code from user
        
    Returns:
        Tuple of (is_valid, remaining_codes)
    """
    try:
        supabase_url = get_settings().supabase_url
        supabase_key = get_settings().supabase_service_role_key
        supabase = create_client(supabase_url, supabase_key)
        
        backup_codes = (
            supabase.table('totp_backup_codes')
            .select('*').eq('user_id', user_id).eq('used', False).execute()
        )
        
        if not backup_codes.data:
            return False, 0
        
        for code_record in backup_codes.data:
            if get_backup_manager().verify_backup_code(backup_code, code_record['code_hash']):
                (
                    supabase.table('totp_backup_codes')
                    .update({'used': True, 'used_at': datetime.utcnow().isoformat()})
                    .eq('user_id', user_id).eq('code_hash', code_record['code_hash']).execute()
                )
                
                remaining = (
                    supabase.table('totp_backup_codes')
                    .select('*').eq('user_id', user_id).eq('used', False).execute()
                )
                remaining_count = len(remaining.data) if remaining.data else 0
                
                logger.info(f"Backup code used for user {user_id}, {remaining_count} codes remaining")
                
                return True, remaining_count
        
        return False, len(backup_codes.data)
        
    except Exception as e:
        logger.error(f"Error verifying backup code: {str(e)}", exc_info=True)
        return False, 0


def check_2fa_required(user_id: str, user_role: str = None) -> bool:
    """
    Check if 2FA is required for a user.
    
    Owner role ALWAYS requires 2FA (enforced policy).
    Other roles require 2FA only if they have explicitly enabled it.
    
    Args:
        user_id: User ID
        user_role: User role (optional, will fetch if not provided)
        
    Returns:
        True if 2FA is enabled/required for user, False otherwise
    """
    if not is_2fa_feature_enabled():
        return False
    
    try:
        if not user_role:
            user = get_user_by_id(user_id)
            if user:
                user_role = user.get('role')
        
        if user_role == 'owner':
            logger.info(f"2FA required for Owner role user {user_id}")
            return True
        
        supabase_url = get_settings().supabase_url
        supabase_key = get_settings().supabase_service_role_key
        supabase = create_client(supabase_url, supabase_key)
        user_2fa = supabase.table('user_2fa').select('enabled').eq('user_id', user_id).execute()
        
        return bool(user_2fa.data and user_2fa.data[0].get('enabled'))
        
    except Exception as e:
        logger.error(f"Error checking 2FA requirement: {str(e)}", exc_info=True)
        return False


@totp_bp.route('/verify-login', methods=['POST'])
@rate_limit  # 5 attempts per 5 minutes
@csrf_protect
def verify_totp_login():
    """
    Verify TOTP code during login and complete authentication.
    
    **DEPRECATED**: This endpoint is deprecated in favor of /api/auth/v2/2fa/challenge
    which uses JWT-based pre-auth tokens. This endpoint is kept for backward compatibility
    but will be removed in a future version.
    
    Migration: Use /api/auth/v2/2fa/challenge with the tmp_login_token from login response.
    
    This endpoint is called after initial login credentials are verified
    and 2FA is required. It verifies the TOTP/backup code and issues
    authentication tokens.
    
    Request:
        {
            "email": "user@example.com",
            "password": "user_password",
            "totp_code": "123456",  # Optional, use this OR backup_code
            "backup_code": "XXXX-XXXX-XXXX-XXXX",  # Optional
            "remember_device": false  # Optional
        }
    
    Response:
        {
            "success": true,
            "user_id": "user-001",
            "backup_codes_remaining": 7,  # Only if backup code was used
            "device_trusted": false  # If remember_device was true
        }
    """
    logger.warning("DEPRECATED: /totp/verify-login endpoint called. Use /api/auth/v2/2fa/challenge instead.")
    
    if not is_2fa_feature_enabled():
        return jsonify({'error': '2FA feature is not enabled'}), 403
    
    try:
        data = request.get_json()
        totp_code = data.get('totp_code', '').strip()
        backup_code = data.get('backup_code', '').strip()
        remember_device = data.get('remember_device', False)
        
        if not totp_code and not backup_code:
            return jsonify({'error': 'Either TOTP code or backup code is required'}), 400
        
        user = None
        
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            jwt_token = auth_header.split(' ')[1]
            try:
                pre_auth_manager = get_pre_auth_manager()
                payload = pre_auth_manager.verify_token(jwt_token)
                if payload:
                    user_id = payload.get('user_id')
                    user = get_user_by_id(user_id)
                    if user:
                        logger.info(f"Using JWT pre-auth token for user {user['id']}", extra={
                            'event': 'jwt_preauth_token_used',
                            'user_id': user['id']
                        })
                    else:
                        logger.warning(f"JWT pre-auth token valid but user {user_id} not found", extra={
                            'event': 'jwt_preauth_user_not_found',
                            'user_id': user_id
                        })
            except Exception as e:
                logger.warning(f"Failed to verify JWT pre-auth token: {e}", extra={
                    'event': 'jwt_preauth_verification_failed',
                    'error': str(e)
                })
        
        if not user:
            email = data.get('email')
            password = data.get('password')
            
            if not email or not password:
                return jsonify({'error': 'Authorization header with JWT token or email/password required'}), 400
            
            from ..services.auth_service import authenticate_user
            user = authenticate_user(email, password)
            if not user:
                return jsonify({'error': 'Invalid email or password'}), 401
            
            logger.info(f"Using password fallback for user {user['id']}", extra={
                'event': 'password_fallback_used',
                'user_id': user['id'],
                'reason': 'no_jwt_preauth_token'
            })
        
        user_id = user['id']
        
        if not check_2fa_required(user_id):
            return jsonify({'error': '2FA is not enabled for this user'}), 400
        
        backup_codes_remaining = None
        
        if backup_code:
            is_valid, remaining = verify_backup_code_for_login(user_id, backup_code)
            if not is_valid:
                return jsonify({'error': 'Invalid backup code'}), 401
            backup_codes_remaining = remaining
            logger.info(f"User {user_id} logged in with backup code, {remaining} codes remaining")
        elif totp_code:
            if len(totp_code) != 6 or not totp_code.isdigit():
                return jsonify({'error': 'Invalid TOTP code format (must be 6 digits)'}), 400
            
            is_valid = verify_totp_for_login(user_id, totp_code)
            if not is_valid:
                return jsonify({'error': 'Invalid TOTP code'}), 401
            logger.info(f"User {user_id} logged in with TOTP")
        
        device_trusted = False
        if remember_device:
            try:
                device_fingerprint = generate_device_fingerprint(request)
                device_expiry = calculate_device_expiry(30)
                
                supabase_url = get_settings().supabase_url
                supabase_key = get_settings().supabase_service_role_key
                supabase = create_client(supabase_url, supabase_key)
                
                supabase.table('trusted_devices').insert({
                    'user_id': user_id,
                    'device_fingerprint': device_fingerprint,
                    'expires_at': device_expiry.isoformat()
                }).execute()
                
                device_trusted = True
                logger.info(f"Device trusted for user {user_id}")
            except Exception as e:
                logger.warning(f"Failed to trust device: {str(e)}")
        
        from ..services.auth_service import generate_access_token, generate_refresh_token, set_auth_cookies
        
        access_token, access_expiry_ms = generate_access_token(
            user_id, user['email'], user['role']
        )
        refresh_token = generate_refresh_token(user_id, user['email'])
        
        response_data = {
            'success': True,
            'user_id': user_id,
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
        
        if backup_codes_remaining is not None:
            response_data['backup_codes_remaining'] = backup_codes_remaining
        
        if device_trusted:
            response_data['device_trusted'] = True
        
        response = make_response(jsonify(response_data), 200)
        set_auth_cookies(response, access_token, refresh_token, access_expiry_ms)
        
        response.set_cookie(
            'pre_auth_token',
            '',
            max_age=0,
            httponly=True,
            secure=COOKIE_SECURE,
            samesite=COOKIE_SAMESITE,
            path='/api/auth/v2/2fa'
        )
        
        logger.info(f"2FA login completed successfully for user {user_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error in 2FA login verification: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500
