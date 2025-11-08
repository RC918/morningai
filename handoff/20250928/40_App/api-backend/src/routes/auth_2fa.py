"""
2FA Pre-Authentication Routes

Provides endpoints for 2FA enrollment and challenge flows using pre-authentication tokens.
These endpoints are called after successful first-factor authentication (email/password).

Endpoints:
- POST /api/auth/v2/2fa/enroll - Start 2FA enrollment (returns secret + QR code)
- POST /api/auth/v2/2fa/verify-enroll - Complete 2FA enrollment (returns backup codes + session)
- POST /api/auth/v2/2fa/challenge - Verify 2FA code during login (returns session)

Security:
- All endpoints require pre-authentication token (tmp_login_token)
- Single-use token enforcement via Redis
- Rate limiting to prevent brute force
- TOTP secrets encrypted at rest
"""

import os
import logging
from flask import Blueprint, request, jsonify, make_response
from supabase import create_client

from ..middleware.pre_auth import pre_auth_required, pre_auth_scope_required
from ..middleware.rate_limit import rate_limit
from ..utils.totp_utils import (
    TOTPManager,
    BackupCodeManager,
    generate_device_fingerprint,
    calculate_device_expiry,
)
from ..utils.pre_auth_token import get_pre_auth_manager
from ..services.auth_service import (
    generate_access_token,
    generate_refresh_token,
    set_auth_cookies,
    get_user_by_id,
)
from common.config.settings import get_settings

logger = logging.getLogger(__name__)

auth_2fa_bp = Blueprint("auth_2fa", __name__, url_prefix="/api/auth/v2/2fa")

_totp_manager = None
_backup_manager = None


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


@auth_2fa_bp.route("/enroll", methods=["POST"])
@pre_auth_required
@pre_auth_scope_required("enroll")
@rate_limit
def enroll_2fa():
    """
    Start 2FA enrollment for the user.

    This endpoint generates a new TOTP secret and QR code for the user to scan.
    The secret is stored in the database but NOT yet enabled until verify-enroll is called.

    Request:
        Authorization: Bearer <tmp_login_token>

    Response:
        {
            "secret": "BASE32_ENCODED_SECRET",
            "qr_code": "data:image/png;base64,..."
        }

    Note: backup_codes are NOT returned here. They are only returned after successful
    verification in /verify-enroll endpoint.
    """
    try:
        user_id = request.pre_auth_user_id
        email = request.pre_auth_email

        user = get_user_by_id(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        totp_manager = get_totp_manager()

        supabase_url = get_settings().supabase_url
        supabase_key = get_settings().supabase_service_role_key
        supabase = create_client(supabase_url, supabase_key)

        existing_2fa = (
            supabase.table("user_2fa").select("*").eq("user_id", user_id).execute()
        )

        if (
            existing_2fa.data
            and existing_2fa.data[0].get("enabled")
            and existing_2fa.data[0].get("verified_at")
        ):
            return (
                jsonify({"error": "2FA is already enabled for this user"}),
                400,
            )

        secret = totp_manager.generate_secret()
        encrypted_secret = totp_manager.encrypt_secret(secret)

        qr_code = totp_manager.generate_qr_code(secret, email)

        if existing_2fa.data:
            supabase.table("user_2fa").update(
                {
                    "secret_encrypted": encrypted_secret,
                    "enabled": False,
                    "verified_at": None,
                }
            ).eq("user_id", user_id).execute()
        else:
            supabase.table("user_2fa").insert(
                {
                    "user_id": user_id,
                    "secret_encrypted": encrypted_secret,
                    "enabled": False,
                    "verified_at": None,
                }
            ).execute()

        logger.info(f"2FA enrollment started for user {user_id}")

        return jsonify({"secret": secret, "qr_code": qr_code}), 200

    except Exception as e:
        logger.error(f"Error in 2FA enrollment: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@auth_2fa_bp.route("/verify-enroll", methods=["POST"])
@pre_auth_required
@pre_auth_scope_required("enroll")
@rate_limit
def verify_enroll_2fa():
    """
    Complete 2FA enrollment by verifying the TOTP code.

    This endpoint verifies the TOTP code, enables 2FA, generates backup codes,
    and issues a full session (access + refresh tokens).

    Request:
        Authorization: Bearer <tmp_login_token>
        {
            "code": "123456"
        }

    Response:
        {
            "success": true,
            "backup_codes": ["XXXX-XXXX-XXXX-XXXX", ...],
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

    Note: This is the ONLY time backup_codes are returned. The user must save them.
    """
    try:
        user_id = request.pre_auth_user_id
        email = request.pre_auth_email
        jti = request.pre_auth_jti

        data = request.get_json()
        code = data.get("code", "").strip()

        if not code:
            return jsonify({"error": "TOTP code is required"}), 400

        if len(code) != 6 or not code.isdigit():
            return (
                jsonify({"error": "Invalid TOTP code format (must be 6 digits)"}),
                400,
            )

        user = get_user_by_id(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        supabase_url = get_settings().supabase_url
        supabase_key = get_settings().supabase_service_role_key
        supabase = create_client(supabase_url, supabase_key)

        user_2fa = (
            supabase.table("user_2fa").select("*").eq("user_id", user_id).execute()
        )

        if not user_2fa.data:
            return (
                jsonify({"error": "2FA enrollment not started. Call /enroll first."}),
                400,
            )

        encrypted_secret = user_2fa.data[0].get("secret_encrypted")
        if not encrypted_secret:
            return (
                jsonify({"error": "2FA enrollment not started. Call /enroll first."}),
                400,
            )

        totp_manager = get_totp_manager()
        secret = totp_manager.decrypt_secret(encrypted_secret)

        if not totp_manager.verify_totp(secret, code):
            pre_auth_manager = get_pre_auth_manager()
            attempts = pre_auth_manager.increment_attempts(jti)

            logger.warning(
                f"Invalid TOTP code for user {user_id} during enrollment (attempt {attempts})"
            )
            return jsonify({"error": "Invalid TOTP code"}), 401

        from datetime import datetime, UTC

        supabase.table("user_2fa").update(
            {"enabled": True, "verified_at": datetime.now(UTC).isoformat()}
        ).eq("user_id", user_id).execute()

        backup_manager = get_backup_manager()
        backup_codes = backup_manager.generate_backup_codes()

        for code in backup_codes:
            hashed_code = backup_manager.hash_backup_code(code)
            supabase.table("totp_backup_codes").insert(
                {"user_id": user_id, "code_hash": hashed_code, "used": False}
            ).execute()

        pre_auth_manager = get_pre_auth_manager()
        if not pre_auth_manager.consume_token_atomic(jti):
            return (
                jsonify(
                    {
                        "error": "TMP_TOKEN_CONSUMED",
                        "message": "This token has already been used.",
                    }
                ),
                401,
            )

        access_token, access_expiry_ms = generate_access_token(
            user_id, email, user["role"]
        )
        refresh_token = generate_refresh_token(user_id, email)

        response_data = {
            "success": True,
            "backup_codes": backup_codes,
            "user": {
                "id": user["id"],
                "email": user["email"],
                "name": user["name"],
                "role": user["role"],
                "tenantId": user["tenant_id"],
                "avatar": user.get("avatar"),
            },
            "tokens": {"expiresAt": access_expiry_ms},
        }

        response = make_response(jsonify(response_data), 200)
        set_auth_cookies(response, access_token, refresh_token, access_expiry_ms)

        logger.info(f"2FA enrollment completed successfully for user {user_id}")
        return response

    except Exception as e:
        logger.error(f"Error in 2FA enrollment verification: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@auth_2fa_bp.route("/challenge", methods=["POST"])
@pre_auth_required
@pre_auth_scope_required("challenge")
@rate_limit
def challenge_2fa():
    """
    Verify 2FA code during login and issue session.

    This endpoint verifies the TOTP code or backup code and issues a full session.
    Optionally supports "remember device" functionality.

    Request:
        Authorization: Bearer <tmp_login_token>
        {
            "code": "123456",  # Optional, use this OR backup_code
            "backup_code": "XXXX-XXXX-XXXX-XXXX",  # Optional
            "remember_device": false  # Optional
        }

    Response:
        {
            "success": true,
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
            "backup_codes_remaining": 7,  # Only if backup code was used
            "device_trusted": false  # If remember_device was true
        }
    """
    try:
        user_id = request.pre_auth_user_id
        email = request.pre_auth_email
        jti = request.pre_auth_jti

        data = request.get_json()
        code = data.get("code", "").strip()
        backup_code = data.get("backup_code", "").strip()
        remember_device = data.get("remember_device", False)

        if not code and not backup_code:
            return (
                jsonify({"error": "Either TOTP code or backup code is required"}),
                400,
            )

        user = get_user_by_id(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        supabase_url = get_settings().supabase_url
        supabase_key = get_settings().supabase_service_role_key
        supabase = create_client(supabase_url, supabase_key)

        user_2fa = (
            supabase.table("user_2fa").select("*").eq("user_id", user_id).execute()
        )

        if not user_2fa.data or not user_2fa.data[0].get("enabled"):
            return jsonify({"error": "2FA is not enabled for this user"}), 400

        backup_codes_remaining = None

        if backup_code:
            backup_manager = get_backup_manager()

            backup_codes_data = (
                supabase.table("totp_backup_codes")
                .select("*")
                .eq("user_id", user_id)
                .eq("used", False)
                .execute()
            )

            if not backup_codes_data.data:
                return (
                    jsonify({"error": "No valid backup codes remaining"}),
                    401,
                )

            valid_code_id = None
            for code_record in backup_codes_data.data:
                if backup_manager.verify_backup_code(
                    backup_code, code_record["code_hash"]
                ):
                    valid_code_id = code_record["id"]
                    break

            if not valid_code_id:
                pre_auth_manager = get_pre_auth_manager()
                attempts = pre_auth_manager.increment_attempts(jti)

                logger.warning(
                    f"Invalid backup code for user {user_id} during login (attempt {attempts})"
                )
                return jsonify({"error": "Invalid backup code"}), 401

            supabase.table("totp_backup_codes").update(
                {
                    "used": True,
                    "used_at": __import__("datetime")
                    .datetime.now(__import__("datetime").UTC)
                    .isoformat(),
                }
            ).eq("id", valid_code_id).execute()

            remaining_codes = (
                supabase.table("totp_backup_codes")
                .select("id")
                .eq("user_id", user_id)
                .eq("used", False)
                .execute()
            )
            backup_codes_remaining = (
                len(remaining_codes.data) if remaining_codes.data else 0
            )

            logger.info(
                f"User {user_id} logged in with backup code, {backup_codes_remaining} codes remaining"
            )

        elif code:
            if len(code) != 6 or not code.isdigit():
                return (
                    jsonify({"error": "Invalid TOTP code format (must be 6 digits)"}),
                    400,
                )

            encrypted_secret = user_2fa.data[0].get("secret_encrypted")
            if not encrypted_secret:
                return jsonify({"error": "2FA secret not found"}), 500

            totp_manager = get_totp_manager()
            secret = totp_manager.decrypt_secret(encrypted_secret)

            if not totp_manager.verify_totp(secret, code):
                pre_auth_manager = get_pre_auth_manager()
                attempts = pre_auth_manager.increment_attempts(jti)

                logger.warning(
                    f"Invalid TOTP code for user {user_id} during login (attempt {attempts})"
                )
                return jsonify({"error": "Invalid TOTP code"}), 401

            logger.info(f"User {user_id} logged in with TOTP")

        device_trusted = False
        if remember_device:
            try:
                user_agent = request.headers.get("User-Agent", "")
                remote_addr = request.remote_addr or "unknown"
                device_fingerprint = generate_device_fingerprint(
                    user_agent, remote_addr
                )
                device_expiry = calculate_device_expiry(30)

                supabase.table("trusted_devices").insert(
                    {
                        "user_id": user_id,
                        "device_fingerprint": device_fingerprint,
                        "expires_at": device_expiry.isoformat(),
                    }
                ).execute()

                device_trusted = True
                logger.info(f"Device trusted for user {user_id}")
            except Exception as e:
                logger.warning(f"Failed to trust device: {str(e)}")

        pre_auth_manager = get_pre_auth_manager()
        if not pre_auth_manager.consume_token_atomic(jti):
            return (
                jsonify(
                    {
                        "error": "TMP_TOKEN_CONSUMED",
                        "message": "This token has already been used.",
                    }
                ),
                401,
            )

        access_token, access_expiry_ms = generate_access_token(
            user_id, email, user["role"]
        )
        refresh_token = generate_refresh_token(user_id, email)

        response_data = {
            "success": True,
            "user": {
                "id": user["id"],
                "email": user["email"],
                "name": user["name"],
                "role": user["role"],
                "tenantId": user["tenant_id"],
                "avatar": user.get("avatar"),
            },
            "tokens": {"expiresAt": access_expiry_ms},
        }

        if backup_codes_remaining is not None:
            response_data["backup_codes_remaining"] = backup_codes_remaining

        if device_trusted:
            response_data["device_trusted"] = True

        response = make_response(jsonify(response_data), 200)
        set_auth_cookies(response, access_token, refresh_token, access_expiry_ms)

        logger.info(f"2FA login completed successfully for user {user_id}")
        return response

    except Exception as e:
        logger.error(f"Error in 2FA challenge: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500
