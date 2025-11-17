"""
Tests for totp_utils module.

Tests cover:
- TOTPManager: secret generation, encryption/decryption, verification
- BackupCodeManager: code generation, hashing, verification
- Helper functions: device fingerprint, expiry calculation
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
import os


@pytest.fixture
def encryption_key():
    """Generate a test encryption key"""
    return Fernet.generate_key().decode()


@pytest.fixture
def totp_manager(encryption_key, monkeypatch):
    """Create a TOTPManager with test encryption key"""
    monkeypatch.setenv('TOTP_ENCRYPTION_KEY', encryption_key)
    from utils.totp_utils import TOTPManager
    return TOTPManager(encryption_key=encryption_key)


class TestTOTPManager:
    """Test TOTPManager class"""
    
    def test_generate_secret(self, totp_manager):
        """Should generate a 32-character Base32 secret"""
        secret = totp_manager.generate_secret()
        
        assert len(secret) == 32
        assert secret.isalnum()
        assert secret.isupper()
    
    def test_encrypt_decrypt_roundtrip(self, totp_manager):
        """Should encrypt and decrypt secret successfully"""
        secret = totp_manager.generate_secret()
        
        encrypted = totp_manager.encrypt_secret(secret)
        decrypted = totp_manager.decrypt_secret(encrypted)
        
        assert decrypted == secret
        assert encrypted != secret
    
    def test_verify_totp_valid_code(self, totp_manager):
        """Should verify valid TOTP code"""
        secret = totp_manager.generate_secret()
        current_code = totp_manager.get_current_code(secret)
        
        result = totp_manager.verify_totp(secret, current_code)
        
        assert result is True
    
    def test_verify_totp_invalid_code(self, totp_manager):
        """Should reject invalid TOTP code"""
        secret = totp_manager.generate_secret()
        
        result = totp_manager.verify_totp(secret, '000000')
        
        assert result is False
    
    def test_get_current_code(self, totp_manager):
        """Should return 6-digit TOTP code"""
        secret = totp_manager.generate_secret()
        
        code = totp_manager.get_current_code(secret)
        
        assert len(code) == 6
        assert code.isdigit()
    
    def test_generate_provisioning_uri(self, totp_manager):
        """Should generate otpauth:// URI"""
        secret = totp_manager.generate_secret()
        
        uri = totp_manager.generate_provisioning_uri(secret, 'test@example.com')
        
        assert uri.startswith('otpauth://totp/')
        assert 'test%40example.com' in uri or 'test@example.com' in uri
        assert 'MorningAI' in uri
    
    def test_generate_provisioning_uri_custom_issuer(self, totp_manager):
        """Should generate URI with custom issuer"""
        secret = totp_manager.generate_secret()
        
        uri = totp_manager.generate_provisioning_uri(secret, 'test@example.com', 'CustomApp')
        
        assert 'CustomApp' in uri
    
    def test_generate_qr_code(self, totp_manager):
        """Should generate base64-encoded QR code"""
        secret = totp_manager.generate_secret()
        
        qr_code = totp_manager.generate_qr_code(secret, 'test@example.com')
        
        assert qr_code.startswith('data:image/png;base64,')
        assert len(qr_code) > 100
    
    def test_init_without_key_raises_error(self, monkeypatch):
        """Should raise ValueError when encryption key not provided"""
        from utils.totp_utils import TOTPManager
        
        monkeypatch.delenv('TOTP_ENCRYPTION_KEY', raising=False)
        
        mock_settings = MagicMock()
        mock_settings.totp_encryption_key = None
        
        with patch('utils.totp_utils.get_settings', return_value=mock_settings):
            with pytest.raises(ValueError, match='TOTP_ENCRYPTION_KEY'):
                TOTPManager()
    
    def test_decrypt_invalid_token_raises_error(self, totp_manager):
        """Should raise error when decrypting invalid token"""
        from cryptography.fernet import InvalidToken
        
        with pytest.raises(InvalidToken):
            totp_manager.decrypt_secret('invalid-encrypted-data')


class TestBackupCodeManager:
    """Test BackupCodeManager class"""
    
    def test_generate_backup_codes(self):
        """Should generate 8 backup codes by default"""
        from utils.totp_utils import BackupCodeManager
        
        codes = BackupCodeManager.generate_backup_codes()
        
        assert len(codes) == 8
        for code in codes:
            assert len(code) == 19
            assert code.count('-') == 3
    
    def test_generate_backup_codes_custom_count(self):
        """Should generate custom number of backup codes"""
        from utils.totp_utils import BackupCodeManager
        
        codes = BackupCodeManager.generate_backup_codes(count=5)
        
        assert len(codes) == 5
    
    def test_hash_backup_code(self):
        """Should hash backup code with Argon2"""
        from utils.totp_utils import BackupCodeManager
        
        code = 'ABCD-EFGH-IJKL-MNOP'
        
        hashed = BackupCodeManager.hash_backup_code(code)
        
        assert hashed.startswith('$argon2')
        assert len(hashed) > 50
    
    def test_verify_backup_code_valid(self):
        """Should verify valid backup code"""
        from utils.totp_utils import BackupCodeManager
        
        code = 'ABCD-EFGH-IJKL-MNOP'
        hashed = BackupCodeManager.hash_backup_code(code)
        
        result = BackupCodeManager.verify_backup_code(code, hashed)
        
        assert result is True
    
    def test_verify_backup_code_without_hyphens(self):
        """Should verify backup code without hyphens"""
        from utils.totp_utils import BackupCodeManager
        
        code = 'ABCD-EFGH-IJKL-MNOP'
        hashed = BackupCodeManager.hash_backup_code(code)
        
        result = BackupCodeManager.verify_backup_code('ABCDEFGHIJKLMNOP', hashed)
        
        assert result is True
    
    def test_verify_backup_code_invalid(self):
        """Should reject invalid backup code"""
        from utils.totp_utils import BackupCodeManager
        
        code = 'ABCD-EFGH-IJKL-MNOP'
        hashed = BackupCodeManager.hash_backup_code(code)
        
        result = BackupCodeManager.verify_backup_code('WRONG-CODE-HERE-XXXX', hashed)
        
        assert result is False
    
    def test_format_backup_code(self):
        """Should format backup code with hyphens"""
        from utils.totp_utils import BackupCodeManager
        
        result = BackupCodeManager.format_backup_code('ABCDEFGHIJKLMNOP')
        
        assert result == 'ABCD-EFGH-IJKL-MNOP'
    
    def test_format_backup_code_already_formatted(self):
        """Should handle already formatted backup code"""
        from utils.totp_utils import BackupCodeManager
        
        result = BackupCodeManager.format_backup_code('ABCD-EFGH-IJKL-MNOP')
        
        assert result == 'ABCD-EFGH-IJKL-MNOP'


class TestHelperFunctions:
    """Test helper functions"""
    
    def test_generate_device_fingerprint(self):
        """Should generate device fingerprint from user agent and IP"""
        from utils.totp_utils import generate_device_fingerprint
        
        fingerprint = generate_device_fingerprint('Mozilla/5.0', '192.168.1.1')
        
        assert len(fingerprint) == 64
        assert fingerprint.isalnum()
    
    def test_generate_device_fingerprint_consistent(self):
        """Should generate same fingerprint for same inputs"""
        from utils.totp_utils import generate_device_fingerprint
        
        fp1 = generate_device_fingerprint('Mozilla/5.0', '192.168.1.1')
        fp2 = generate_device_fingerprint('Mozilla/5.0', '192.168.1.1')
        
        assert fp1 == fp2
    
    def test_generate_device_fingerprint_different_inputs(self):
        """Should generate different fingerprints for different inputs"""
        from utils.totp_utils import generate_device_fingerprint
        
        fp1 = generate_device_fingerprint('Mozilla/5.0', '192.168.1.1')
        fp2 = generate_device_fingerprint('Chrome/90.0', '192.168.1.1')
        
        assert fp1 != fp2
    
    def test_calculate_device_expiry_default(self):
        """Should calculate expiry 30 days from now"""
        from utils.totp_utils import calculate_device_expiry
        
        before = datetime.utcnow()
        expiry = calculate_device_expiry()
        after = datetime.utcnow()
        
        expected_min = before + timedelta(days=30)
        expected_max = after + timedelta(days=30)
        
        assert expected_min <= expiry <= expected_max
    
    def test_calculate_device_expiry_custom_days(self):
        """Should calculate expiry with custom days"""
        from utils.totp_utils import calculate_device_expiry
        
        before = datetime.utcnow()
        expiry = calculate_device_expiry(days=60)
        after = datetime.utcnow()
        
        expected_min = before + timedelta(days=60)
        expected_max = after + timedelta(days=60)
        
        assert expected_min <= expiry <= expected_max
