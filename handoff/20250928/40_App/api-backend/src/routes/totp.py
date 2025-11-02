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

import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from flask import Blueprint, request, jsonify, g
from werkzeug.security import check_password_hash

from ..services.auth_service import get_user_by_id
from ..utils.totp_utils import TOTPManager, BackupCodeManager, generate_device_fingerprint, calculate_device_expiry
from ..middleware.auth_middleware import require_auth
from ..middleware.rate_limit import rate_limit
from ..persistence.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

totp_bp = Blueprint('totp', __name__, url_prefix='/api/auth/v2/totp')

totp_manager = TOTPManager()
backup_manager = BackupCodeManager()


@totp_bp.route('/setup', methods=['POST'])
@require_auth
@rate_limit(max_requests=3, window_seconds=3600)  # 3 attempts per hour
def setup_totp():
    """
    Setup TOTP for the authenticated user.
    
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
    try:
        data = request.get_json()
        password = data.get('password')
        
        if not password:
            return jsonify({'error': 'Password confirmation required'}), 400
        
        user_id = g.user_id
        user = get_user_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if not check_password_hash(user.get('password_hash', ''), password):
            return jsonify({'error': 'Invalid password'}), 401
        
        supabase = get_supabase_client()
        existing_2fa = supabase.table('user_2fa').select('*').eq('user_id', user_id).execute()
        
        if existing_2fa.data and existing_2fa.data[0].get('enabled'):
            return jsonify({'error': '2FA is already enabled. Disable it first to re-setup.'}), 400
        
        secret = totp_manager.generate_secret()
        encrypted_secret = totp_manager.encrypt_secret(secret)
        
        user_email = user.get('email', '')
        qr_code = totp_manager.generate_qr_code(secret, user_email)
        
        backup_codes = backup_manager.generate_backup_codes(8)
        
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
                'code_hash': backup_manager.hash_backup_code(code),
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
@require_auth
@rate_limit(max_requests=5, window_seconds=300)  # 5 attempts per 5 minutes
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
    try:
        data = request.get_json()
        code = data.get('code', '').strip()
        
        if not code or len(code) != 6:
            return jsonify({'error': 'Invalid TOTP code format'}), 400
        
        user_id = g.user_id
        
        supabase = get_supabase_client()
        user_2fa = supabase.table('user_2fa').select('*').eq('user_id', user_id).execute()
        
        if not user_2fa.data:
            return jsonify({'error': '2FA not set up. Call /setup first.'}), 400
        
        user_2fa_record = user_2fa.data[0]
        
        if user_2fa_record.get('enabled'):
            return jsonify({'error': '2FA is already enabled'}), 400
        
        encrypted_secret = user_2fa_record['secret_encrypted']
        secret = totp_manager.decrypt_secret(encrypted_secret)
        
        if not totp_manager.verify_totp(secret, code, valid_window=1):
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
@require_auth
@rate_limit(max_requests=5, window_seconds=300)  # 5 attempts per 5 minutes
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
    try:
        data = request.get_json()
        password = data.get('password')
        totp_code = data.get('totp_code', '').strip()
        
        if not password or not totp_code:
            return jsonify({'error': 'Password and TOTP code required'}), 400
        
        user_id = g.user_id
        user = get_user_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if not check_password_hash(user.get('password_hash', ''), password):
            return jsonify({'error': 'Invalid password'}), 401
        
        supabase = get_supabase_client()
        user_2fa = supabase.table('user_2fa').select('*').eq('user_id', user_id).execute()
        
        if not user_2fa.data or not user_2fa.data[0].get('enabled'):
            return jsonify({'error': '2FA is not enabled'}), 400
        
        encrypted_secret = user_2fa.data[0]['secret_encrypted']
        secret = totp_manager.decrypt_secret(encrypted_secret)
        
        if not totp_manager.verify_totp(secret, totp_code, valid_window=1):
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
@require_auth
@rate_limit(max_requests=3, window_seconds=3600)  # 3 attempts per hour
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
    try:
        data = request.get_json()
        password = data.get('password')
        
        if not password:
            return jsonify({'error': 'Password confirmation required'}), 400
        
        user_id = g.user_id
        user = get_user_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if not check_password_hash(user.get('password_hash', ''), password):
            return jsonify({'error': 'Invalid password'}), 401
        
        supabase = get_supabase_client()
        user_2fa = supabase.table('user_2fa').select('*').eq('user_id', user_id).execute()
        
        if not user_2fa.data or not user_2fa.data[0].get('enabled'):
            return jsonify({'error': '2FA is not enabled'}), 400
        
        backup_codes = backup_manager.generate_backup_codes(8)
        
        supabase.table('totp_backup_codes').delete().eq('user_id', user_id).execute()
        
        backup_code_records = [
            {
                'user_id': user_id,
                'code_hash': backup_manager.hash_backup_code(code),
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
@require_auth
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
    try:
        user_id = g.user_id
        
        supabase = get_supabase_client()
        
        user_2fa = supabase.table('user_2fa').select('*').eq('user_id', user_id).execute()
        
        if not user_2fa.data:
            return jsonify({
                'enabled': False,
                'verified_at': None,
                'backup_codes_remaining': 0
            }), 200
        
        user_2fa_record = user_2fa.data[0]
        
        backup_codes = supabase.table('totp_backup_codes').select('*').eq('user_id', user_id).eq('used', False).execute()
        
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
        supabase = get_supabase_client()
        user_2fa = supabase.table('user_2fa').select('*').eq('user_id', user_id).eq('enabled', True).execute()
        
        if not user_2fa.data:
            return False
        
        encrypted_secret = user_2fa.data[0]['secret_encrypted']
        secret = totp_manager.decrypt_secret(encrypted_secret)
        
        is_valid = totp_manager.verify_totp(secret, totp_code, valid_window=1)
        
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
        supabase = get_supabase_client()
        
        backup_codes = supabase.table('totp_backup_codes').select('*').eq('user_id', user_id).eq('used', False).execute()
        
        if not backup_codes.data:
            return False, 0
        
        for code_record in backup_codes.data:
            if backup_manager.verify_backup_code(backup_code, code_record['code_hash']):
                supabase.table('totp_backup_codes').update({
                    'used': True,
                    'used_at': datetime.utcnow().isoformat()
                }).eq('id', code_record['id']).execute()
                
                remaining = supabase.table('totp_backup_codes').select('*').eq('user_id', user_id).eq('used', False).execute()
                remaining_count = len(remaining.data) if remaining.data else 0
                
                logger.info(f"Backup code used for user {user_id}, {remaining_count} codes remaining")
                
                return True, remaining_count
        
        return False, len(backup_codes.data)
        
    except Exception as e:
        logger.error(f"Error verifying backup code: {str(e)}", exc_info=True)
        return False, 0


def check_2fa_required(user_id: str) -> bool:
    """
    Check if 2FA is required for a user.
    
    Args:
        user_id: User ID
        
    Returns:
        True if 2FA is enabled for user, False otherwise
    """
    try:
        supabase = get_supabase_client()
        user_2fa = supabase.table('user_2fa').select('enabled').eq('user_id', user_id).execute()
        
        return bool(user_2fa.data and user_2fa.data[0].get('enabled'))
        
    except Exception as e:
        logger.error(f"Error checking 2FA requirement: {str(e)}", exc_info=True)
        return False
