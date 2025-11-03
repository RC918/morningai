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
