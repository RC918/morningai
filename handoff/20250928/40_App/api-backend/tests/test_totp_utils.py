"""Unit tests for TOTP utilities"""

import pytest
from cryptography.fernet import Fernet
from src.utils.totp_utils import TOTPManager, BackupCodeManager, generate_device_fingerprint, calculate_device_expiry


@pytest.fixture
def totp_manager():
    test_key = Fernet.generate_key()
    return TOTPManager(encryption_key=test_key.decode())


@pytest.fixture
def backup_manager():
    return BackupCodeManager()


class TestTOTPManager:
    def test_generate_secret(self, totp_manager):
        secret = totp_manager.generate_secret()
        assert secret is not None and len(secret) == 32 and secret.isalnum() and secret.isupper()
    
    def test_encrypt_decrypt_secret(self, totp_manager):
        secret = totp_manager.generate_secret()
        encrypted = totp_manager.encrypt_secret(secret)
        assert encrypted != secret and totp_manager.decrypt_secret(encrypted) == secret
    
    def test_verify_totp_valid_code(self, totp_manager):
        secret = totp_manager.generate_secret()
        current_code = totp_manager.get_current_code(secret)
        assert totp_manager.verify_totp(secret, current_code, valid_window=1)
    
    def test_generate_qr_code(self, totp_manager):
        secret = totp_manager.generate_secret()
        qr_code = totp_manager.generate_qr_code(secret, "test@example.com", "TestApp")
        assert qr_code.startswith("data:image/png;base64,") and len(qr_code) > 100


class TestBackupCodeManager:
    def test_generate_backup_codes(self, backup_manager):
        codes = backup_manager.generate_backup_codes()
        assert len(codes) == 8 and all(len(c) == 19 and c.count('-') == 3 for c in codes)
    
    def test_hash_and_verify_backup_code(self, backup_manager):
        code = "ABCD-EFGH-IJKL-MNOP"
        code_hash = backup_manager.hash_backup_code(code)
        assert code_hash != code and code_hash.startswith("$argon2") and backup_manager.verify_backup_code(code, code_hash)


class TestDeviceFingerprinting:
    def test_generate_device_fingerprint(self):
        fingerprint = generate_device_fingerprint("Mozilla/5.0", "192.168.1.1")
        assert fingerprint is not None and len(fingerprint) == 64
    
    def test_calculate_device_expiry(self):
        from datetime import datetime, timedelta
        expiry = calculate_device_expiry(days=30)
        assert abs((expiry - (datetime.utcnow() + timedelta(days=30))).total_seconds()) < 1
    
    def test_device_fingerprint_consistency(self):
        """Test that same inputs produce same fingerprint."""
        fp1 = generate_device_fingerprint("Mozilla/5.0", "192.168.1.1")
        fp2 = generate_device_fingerprint("Mozilla/5.0", "192.168.1.1")
        assert fp1 == fp2
    
    def test_device_fingerprint_uniqueness(self):
        """Test that different inputs produce different fingerprints."""
        fp1 = generate_device_fingerprint("Mozilla/5.0", "192.168.1.1")
        fp2 = generate_device_fingerprint("Chrome/90.0", "192.168.1.1")
        fp3 = generate_device_fingerprint("Mozilla/5.0", "10.0.0.1")
        assert fp1 != fp2
        assert fp1 != fp3
        assert fp2 != fp3


class TestTOTPManagerEdgeCases:
    """Test edge cases and error handling for TOTPManager."""
    
    def test_verify_totp_with_invalid_secret(self, totp_manager):
        """Test TOTP verification with invalid secret format."""
        result = totp_manager.verify_totp("INVALID", "123456")
        assert result is False
    
    def test_verify_totp_with_empty_code(self, totp_manager):
        """Test TOTP verification with empty code."""
        secret = totp_manager.generate_secret()
        result = totp_manager.verify_totp(secret, "")
        assert result is False
    
    def test_verify_totp_with_non_numeric_code(self, totp_manager):
        """Test TOTP verification with non-numeric code."""
        secret = totp_manager.generate_secret()
        result = totp_manager.verify_totp(secret, "ABCDEF")
        assert result is False
    
    def test_encrypt_decrypt_multiple_secrets(self, totp_manager):
        """Test encrypting and decrypting multiple secrets."""
        secrets = [totp_manager.generate_secret() for _ in range(10)]
        encrypted = [totp_manager.encrypt_secret(s) for s in secrets]
        decrypted = [totp_manager.decrypt_secret(e) for e in encrypted]
        assert secrets == decrypted
    
    def test_generate_qr_code_with_special_characters(self, totp_manager):
        """Test QR code generation with special characters in email."""
        secret = totp_manager.generate_secret()
        qr_code = totp_manager.generate_qr_code(secret, "user+test@example.com", "Test App")
        assert qr_code.startswith("data:image/png;base64,")
        assert len(qr_code) > 100
    
    def test_totp_manager_without_encryption_key(self):
        """Test TOTPManager initialization without encryption key."""
        import os
        old_key = os.environ.get('TOTP_ENCRYPTION_KEY')
        if 'TOTP_ENCRYPTION_KEY' in os.environ:
            del os.environ['TOTP_ENCRYPTION_KEY']
        
        try:
            with pytest.raises(ValueError, match="TOTP_ENCRYPTION_KEY"):
                TOTPManager()
        finally:
            if old_key:
                os.environ['TOTP_ENCRYPTION_KEY'] = old_key


class TestBackupCodeManagerEdgeCases:
    """Test edge cases for BackupCodeManager."""
    
    def test_generate_multiple_backup_code_sets(self, backup_manager):
        """Test generating multiple sets of backup codes."""
        sets = [backup_manager.generate_backup_codes() for _ in range(5)]
        all_codes = [code for code_set in sets for code in code_set]
        assert len(all_codes) == len(set(all_codes))
    
    def test_verify_backup_code_case_insensitive(self, backup_manager):
        """Test backup code verification is case-insensitive."""
        code = "ABCD-EFGH-IJKL-MNOP"
        code_hash = backup_manager.hash_backup_code(code)
        
        assert backup_manager.verify_backup_code("abcd-efgh-ijkl-mnop", code_hash)
        
        assert backup_manager.verify_backup_code("AbCd-EfGh-IjKl-MnOp", code_hash)
    
    def test_verify_backup_code_without_hyphens(self, backup_manager):
        """Test backup code verification without hyphens."""
        code = "ABCD-EFGH-IJKL-MNOP"
        code_hash = backup_manager.hash_backup_code(code)
        
        assert backup_manager.verify_backup_code("ABCDEFGHIJKLMNOP", code_hash)
    
    def test_verify_backup_code_with_spaces(self, backup_manager):
        """Test backup code verification with spaces."""
        code = "ABCD-EFGH-IJKL-MNOP"
        code_hash = backup_manager.hash_backup_code(code)
        
        assert backup_manager.verify_backup_code("ABCD EFGH IJKL MNOP", code_hash)
    
    def test_format_backup_code(self, backup_manager):
        """Test backup code formatting."""
        assert backup_manager.format_backup_code("ABCDEFGHIJKLMNOP") == "ABCD-EFGH-IJKL-MNOP"
        assert backup_manager.format_backup_code("abcd-efgh-ijkl-mnop") == "ABCD-EFGH-IJKL-MNOP"
        assert backup_manager.format_backup_code("ABCD EFGH IJKL MNOP") == "ABCD-EFGH-IJKL-MNOP"
    
    def test_backup_code_no_ambiguous_characters(self, backup_manager):
        """Test that backup codes don't contain ambiguous characters."""
        codes = backup_manager.generate_backup_codes(100)
        ambiguous = ['0', 'O', '1', 'I', 'L']
        
        for code in codes:
            code_clean = code.replace('-', '')
            for char in ambiguous:
                assert char not in code_clean, f"Ambiguous character {char} found in code {code}"
    
    def test_hash_backup_code_consistency(self, backup_manager):
        """Test that hashing same code produces verifiable hash."""
        code = "ABCD-EFGH-IJKL-MNOP"
        hash1 = backup_manager.hash_backup_code(code)
        hash2 = backup_manager.hash_backup_code(code)
        
        assert hash1 != hash2
        
        assert backup_manager.verify_backup_code(code, hash1)
        assert backup_manager.verify_backup_code(code, hash2)
    
    def test_verify_invalid_backup_code(self, backup_manager):
        """Test verification fails for invalid backup code."""
        code = "ABCD-EFGH-IJKL-MNOP"
        code_hash = backup_manager.hash_backup_code(code)
        
        assert not backup_manager.verify_backup_code("WXYZ-WXYZ-WXYZ-WXYZ", code_hash)


class TestTOTPTimeWindow:
    """Test TOTP time window behavior."""
    
    def test_verify_totp_current_time(self, totp_manager):
        """Test TOTP verification at current time."""
        secret = totp_manager.generate_secret()
        current_code = totp_manager.get_current_code(secret)
        assert totp_manager.verify_totp(secret, current_code, valid_window=1)
    
    def test_verify_totp_different_windows(self, totp_manager):
        """Test TOTP verification with different time windows."""
        import pyotp
        from datetime import datetime, timedelta
        
        secret = totp_manager.generate_secret()
        totp = pyotp.TOTP(secret)
        
        old_time = datetime.utcnow() - timedelta(seconds=90)
        old_code = totp.at(old_time)
        
        assert not totp_manager.verify_totp(secret, old_code, valid_window=1)
        
        assert totp_manager.verify_totp(secret, old_code, valid_window=3)
    
    def test_provisioning_uri_format(self, totp_manager):
        """Test provisioning URI format."""
        secret = totp_manager.generate_secret()
        uri = totp_manager.generate_provisioning_uri(secret, "test@example.com", "TestApp")
        
        assert uri.startswith("otpauth://totp/")
        assert "test%40example.com" in uri or "test@example.com" in uri
        assert "TestApp" in uri
        assert f"secret={secret}" in uri
