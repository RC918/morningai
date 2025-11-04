"""
TOTP Utilities for 2FA Implementation

This module provides utilities for:
- TOTP secret generation and encryption/decryption
- Backup code generation and hashing
- TOTP verification with time skew tolerance
- QR code generation for authenticator apps

Security:
- TOTP secrets encrypted with Fernet (AES-128-CBC + HMAC-SHA256)
- Backup codes hashed with Argon2id
- Time skew tolerance: ±1 period (30 seconds)
"""

import os
import secrets
import string
from typing import List, Tuple, Optional
from datetime import datetime, timedelta
import io
import base64

import pyotp
import qrcode
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from cryptography.fernet import Fernet


ARGON2_HASHER = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    salt_len=16
)


class TOTPManager:
    """Manages TOTP operations including secret generation, encryption, and verification."""
    
    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize TOTP Manager.
        
        Args:
            encryption_key: Base64-encoded Fernet key for encrypting TOTP secrets.
                          If None, reads from TOTP_ENCRYPTION_KEY environment variable.
        """
        if encryption_key is None:
            encryption_key = os.getenv('TOTP_ENCRYPTION_KEY')
            if not encryption_key:
                raise ValueError(
                    "TOTP_ENCRYPTION_KEY environment variable not set. "
                    "Generate one with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
                )
        
        self.fernet = Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)
    
    def generate_secret(self) -> str:
        """
        Generate a new TOTP secret (Base32 encoded).
        
        Returns:
            Base32-encoded secret (32 characters)
        """
        return pyotp.random_base32()
    
    def encrypt_secret(self, secret: str) -> str:
        """
        Encrypt a TOTP secret using Fernet (AES-128-CBC + HMAC-SHA256).
        
        Args:
            secret: Base32-encoded TOTP secret
            
        Returns:
            Base64-encoded encrypted secret
        """
        encrypted = self.fernet.encrypt(secret.encode())
        return encrypted.decode()
    
    def decrypt_secret(self, encrypted_secret: str) -> str:
        """
        Decrypt a TOTP secret.
        
        Args:
            encrypted_secret: Base64-encoded encrypted secret
            
        Returns:
            Base32-encoded TOTP secret
            
        Raises:
            cryptography.fernet.InvalidToken: If decryption fails
        """
        decrypted = self.fernet.decrypt(encrypted_secret.encode())
        return decrypted.decode()
    
    def generate_totp(self, secret: str) -> pyotp.TOTP:
        """
        Create a TOTP instance from a secret.
        
        Args:
            secret: Base32-encoded TOTP secret
            
        Returns:
            pyotp.TOTP instance
        """
        return pyotp.TOTP(secret)
    
    def verify_totp(self, secret: str, code: str, valid_window: int = 1) -> bool:
        """
        Verify a TOTP code with time skew tolerance.
        
        Args:
            secret: Base32-encoded TOTP secret
            code: 6-digit TOTP code from user
            valid_window: Number of time periods to check before/after current time
                         (default: 1 = ±30 seconds, total 90 seconds)
            
        Returns:
            True if code is valid, False otherwise
        """
        totp = self.generate_totp(secret)
        return totp.verify(code, valid_window=valid_window)
    
    def get_current_code(self, secret: str) -> str:
        """
        Get the current TOTP code (for testing/debugging only).
        
        Args:
            secret: Base32-encoded TOTP secret
            
        Returns:
            Current 6-digit TOTP code
        """
        totp = self.generate_totp(secret)
        return totp.now()
    
    def generate_provisioning_uri(
        self,
        secret: str,
        user_email: str,
        issuer_name: str = "MorningAI"
    ) -> str:
        """
        Generate a provisioning URI for QR code generation.
        
        Args:
            secret: Base32-encoded TOTP secret
            user_email: User's email address
            issuer_name: Name of the service (default: "MorningAI")
            
        Returns:
            otpauth:// URI for QR code
        """
        totp = self.generate_totp(secret)
        return totp.provisioning_uri(name=user_email, issuer_name=issuer_name)
    
    def generate_qr_code(
        self,
        secret: str,
        user_email: str,
        issuer_name: str = "MorningAI"
    ) -> str:
        """
        Generate a QR code image for TOTP setup.
        
        Args:
            secret: Base32-encoded TOTP secret
            user_email: User's email address
            issuer_name: Name of the service (default: "MorningAI")
            
        Returns:
            Base64-encoded PNG image (data URI format)
        """
        uri = self.generate_provisioning_uri(secret, user_email, issuer_name)
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_base64}"


class BackupCodeManager:
    """Manages backup code generation and verification."""
    
    @staticmethod
    def generate_backup_codes(count: int = 8) -> List[str]:
        """
        Generate backup recovery codes.
        
        Format: XXXX-XXXX-XXXX-XXXX (16 characters, 4 groups of 4)
        
        Args:
            count: Number of backup codes to generate (default: 8)
            
        Returns:
            List of backup codes in format XXXX-XXXX-XXXX-XXXX
        """
        codes = []
        alphabet = string.ascii_uppercase + string.digits
        alphabet = alphabet.replace('0', '').replace('O', '').replace('1', '').replace('I', '').replace('L', '')
        
        for _ in range(count):
            code_chars = ''.join(secrets.choice(alphabet) for _ in range(16))
            code = '-'.join([code_chars[i:i+4] for i in range(0, 16, 4)])
            codes.append(code)
        
        return codes
    
    @staticmethod
    def hash_backup_code(code: str) -> str:
        """
        Hash a backup code using Argon2id.
        
        Args:
            code: Backup code in format XXXX-XXXX-XXXX-XXXX
            
        Returns:
            Argon2id hash string
        """
        code_normalized = code.replace('-', '').upper()
        return ARGON2_HASHER.hash(code_normalized)
    
    @staticmethod
    def verify_backup_code(code: str, code_hash: str) -> bool:
        """
        Verify a backup code against its hash.
        
        Args:
            code: Backup code from user (with or without hyphens)
            code_hash: Argon2id hash from database
            
        Returns:
            True if code matches hash, False otherwise
        """
        try:
            code_normalized = code.replace('-', '').replace(' ', '').upper()
            ARGON2_HASHER.verify(code_hash, code_normalized)
            return True
        except VerifyMismatchError:
            return False
    
    @staticmethod
    def format_backup_code(code: str) -> str:
        """
        Format a backup code to XXXX-XXXX-XXXX-XXXX format.
        
        Args:
            code: Backup code (with or without hyphens)
            
        Returns:
            Formatted backup code
        """
        code_clean = code.replace('-', '').replace(' ', '').upper()
        return '-'.join([code_clean[i:i+4] for i in range(0, len(code_clean), 4)])


def generate_device_fingerprint(user_agent: str, ip_address: str) -> str:
    """
    Generate a device fingerprint from user agent and IP address.
    
    This is a simple implementation. In production, consider using more
    sophisticated fingerprinting techniques.
    
    Args:
        user_agent: Browser user agent string
        ip_address: Client IP address
        
    Returns:
        SHA-256 hash of device fingerprint
    """
    import hashlib
    fingerprint_data = f"{user_agent}|{ip_address}"
    return hashlib.sha256(fingerprint_data.encode()).hexdigest()


def calculate_device_expiry(days: int = 30) -> datetime:
    """
    Calculate expiry date for trusted device.
    
    Args:
        days: Number of days until expiry (default: 30)
        
    Returns:
        Expiry datetime
    """
    return datetime.utcnow() + timedelta(days=days)
