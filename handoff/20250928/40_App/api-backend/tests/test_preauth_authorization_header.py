"""
Integration Tests for Pre-Auth Authorization Header Handling

Tests that verify the pre_auth_required decorator correctly handles various
Authorization header formats and edge cases. These tests complement the existing
tests in test_auth_2fa_preauth.py by focusing specifically on Authorization header
parsing and validation edge cases.

Coverage:
1. Authorization header format validation (Bearer scheme)
2. Case sensitivity of Bearer scheme
3. Whitespace handling in Authorization header
4. Empty and missing token handling
5. Special characters and encoding in tokens
6. Integration with scope enforcement
7. Error messages and status codes
"""

import pytest
import json
import os
from unittest.mock import patch, MagicMock

os.environ['TOTP_ENCRYPTION_KEY'] = 'test-key-for-totp-encryption-32bytes=='
os.environ['TESTING'] = 'true'

from src.utils.pre_auth_token import get_pre_auth_manager


@pytest.fixture
def mock_get_user():
    """Mock get_user_by_id to return test user"""
    with patch("src.routes.auth_2fa.get_user_by_id") as mock:
        mock.return_value = {
            "id": "user-001",
            "email": "test@example.com",
            "name": "Test User",
            "role": "owner",
            "tenant_id": "tenant-001",
        }
        yield mock


@pytest.fixture
def client(mock_redis, mock_supabase, mock_totp, mock_get_user):
    """Create test client with all mocks active before app import"""
    from src.main import app
    
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_redis():
    """Mock Redis client using fakeredis for stateful behavior"""
    from fakeredis import FakeRedis
    import src.utils.pre_auth_token
    
    src.utils.pre_auth_token._pre_auth_manager = None
    
    redis_client = FakeRedis(decode_responses=True)
    with patch("src.utils.redis_client.get_redis_client") as mock1, patch(
        "src.utils.pre_auth_token.get_redis_client"
    ) as mock2:
        mock1.return_value = redis_client
        mock2.return_value = redis_client
        
        yield redis_client
        
        src.utils.pre_auth_token._pre_auth_manager = None
        redis_client.flushall()


@pytest.fixture
def mock_supabase():
    """Mock Supabase client with environment variables set"""
    import os
    with patch.dict(os.environ, {
        "SUPABASE_URL": "http://test.supabase.co",
        "SUPABASE_SERVICE_ROLE_KEY": "test-service-role-key"
    }, clear=False), \
         patch("supabase.create_client") as mock_create, \
         patch("src.routes.auth_2fa.create_client") as mock_create_2fa:
        supabase_mock = MagicMock()
        
        user_2fa_mock = MagicMock()
        user_2fa_mock.data = []
        supabase_mock.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            user_2fa_mock
        )
        
        mock_create.return_value = supabase_mock
        mock_create_2fa.return_value = supabase_mock
        
        yield supabase_mock


@pytest.fixture
def mock_totp():
    """Mock TOTP manager"""
    with patch("src.routes.auth_2fa.get_totp_manager") as mock:
        totp_mock = MagicMock()
        totp_mock.generate_secret.return_value = "BASE32SECRET123"
        totp_mock.encrypt_secret.return_value = "encrypted_secret"
        totp_mock.decrypt_secret.return_value = "BASE32SECRET123"
        totp_mock.generate_qr_code.return_value = "data:image/png;base64,QRCODE"
        totp_mock.verify_totp.return_value = True
        mock.return_value = totp_mock
        yield totp_mock


class TestAuthorizationHeaderFormat:
    """Test Authorization header format validation"""
    
    def test_missing_authorization_header(self, client, mock_redis):
        """Test request without Authorization header returns 401"""
        response = client.post(
            "/api/auth/v2/2fa/enroll",
            json={"secret": "test_secret"}
        )
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data["error"] == "TMP_TOKEN_MISSING"
        assert "Pre-authentication token required" in data["message"]
    
    def test_wrong_scheme_basic(self, client, mock_redis):
        """Test Authorization header with Basic scheme returns 401"""
        manager = get_pre_auth_manager()
        token = manager.generate_token("user-001", "test@example.com", "enroll")
        
        response = client.post(
            "/api/auth/v2/2fa/enroll",
            headers={"Authorization": f"Basic {token}"},
            json={"secret": "test_secret"}
        )
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data["error"] == "INVALID_TOKEN_FORMAT"
        assert "Bearer" in data["message"]
    
    def test_wrong_scheme_token(self, client, mock_redis):
        """Test Authorization header with Token scheme returns 401"""
        manager = get_pre_auth_manager()
        token = manager.generate_token("user-001", "test@example.com", "enroll")
        
        response = client.post(
            "/api/auth/v2/2fa/enroll",
            headers={"Authorization": f"Token {token}"},
            json={"secret": "test_secret"}
        )
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data["error"] == "INVALID_TOKEN_FORMAT"
    
    def test_bearer_lowercase(self, client, mock_redis, mock_supabase, mock_totp):
        """Test Authorization header with lowercase 'bearer' is accepted"""
        manager = get_pre_auth_manager()
        token = manager.generate_token("user-001", "test@example.com", "enroll")
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        
        response = client.post(
            "/api/auth/v2/2fa/enroll",
            headers={"Authorization": f"bearer {token}"}
        )
        
        assert response.status_code == 200
    
    def test_bearer_uppercase(self, client, mock_redis, mock_supabase, mock_totp):
        """Test Authorization header with uppercase 'BEARER' is accepted"""
        manager = get_pre_auth_manager()
        token = manager.generate_token("user-001", "test@example.com", "enroll")
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        
        response = client.post(
            "/api/auth/v2/2fa/enroll",
            headers={"Authorization": f"BEARER {token}"}
        )
        
        assert response.status_code == 200
    
    def test_bearer_mixed_case(self, client, mock_redis, mock_supabase, mock_totp):
        """Test Authorization header with mixed case 'BeArEr' is accepted"""
        manager = get_pre_auth_manager()
        token = manager.generate_token("user-001", "test@example.com", "enroll")
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        
        response = client.post(
            "/api/auth/v2/2fa/enroll",
            headers={"Authorization": f"BeArEr {token}"}
        )
        
        assert response.status_code == 200


class TestAuthorizationHeaderWhitespace:
    """Test whitespace handling in Authorization header"""
    
    def test_no_space_after_bearer(self, client, mock_redis):
        """Test Authorization header without space after Bearer returns 401"""
        manager = get_pre_auth_manager()
        token = manager.generate_token("user-001", "test@example.com", "enroll")
        
        response = client.post(
            "/api/auth/v2/2fa/enroll",
            headers={"Authorization": f"Bearer{token}"},
            json={"secret": "test_secret"}
        )
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data["error"] == "INVALID_TOKEN_FORMAT"
    
    def test_multiple_spaces_after_bearer(self, client, mock_redis):
        """Test Authorization header with multiple spaces after Bearer returns 401"""
        manager = get_pre_auth_manager()
        token = manager.generate_token("user-001", "test@example.com", "enroll")
        
        response = client.post(
            "/api/auth/v2/2fa/enroll",
            headers={"Authorization": f"Bearer  {token}"},
            json={"secret": "test_secret"}
        )
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data["error"] == "INVALID_TOKEN_FORMAT"
    
    def test_tab_after_bearer(self, client, mock_redis):
        """Test Authorization header with tab after Bearer returns 401"""
        manager = get_pre_auth_manager()
        token = manager.generate_token("user-001", "test@example.com", "enroll")
        
        response = client.post(
            "/api/auth/v2/2fa/enroll",
            headers={"Authorization": f"Bearer\t{token}"},
            json={"secret": "test_secret"}
        )
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data["error"] == "INVALID_TOKEN_FORMAT"
    
    def test_leading_whitespace(self, client, mock_redis):
        """Test Authorization header with leading whitespace returns 401"""
        manager = get_pre_auth_manager()
        token = manager.generate_token("user-001", "test@example.com", "enroll")
        
        response = client.post(
            "/api/auth/v2/2fa/enroll",
            headers={"Authorization": f" Bearer {token}"},
            json={"secret": "test_secret"}
        )
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data["error"] == "INVALID_TOKEN_FORMAT"
    
    def test_trailing_whitespace(self, client, mock_redis):
        """Test Authorization header with trailing whitespace returns 401"""
        manager = get_pre_auth_manager()
        token = manager.generate_token("user-001", "test@example.com", "enroll")
        
        response = client.post(
            "/api/auth/v2/2fa/enroll",
            headers={"Authorization": f"Bearer {token} "},
            json={"secret": "test_secret"}
        )
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data["error"] == "INVALID_TOKEN_FORMAT"


class TestAuthorizationHeaderEmptyToken:
    """Test empty and missing token handling"""
    
    def test_bearer_only_no_token(self, client, mock_redis):
        """Test Authorization header with only 'Bearer' returns 401"""
        response = client.post(
            "/api/auth/v2/2fa/enroll",
            headers={"Authorization": "Bearer"},
            json={"secret": "test_secret"}
        )
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data["error"] == "INVALID_TOKEN_FORMAT"
    
    def test_bearer_with_empty_token(self, client, mock_redis):
        """Test Authorization header with empty token returns 401"""
        response = client.post(
            "/api/auth/v2/2fa/enroll",
            headers={"Authorization": "Bearer "},
            json={"secret": "test_secret"}
        )
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data["error"] == "TMP_TOKEN_INVALID"
    
    def test_empty_authorization_header(self, client, mock_redis):
        """Test empty Authorization header returns 401"""
        response = client.post(
            "/api/auth/v2/2fa/enroll",
            headers={"Authorization": ""},
            json={"secret": "test_secret"}
        )
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data["error"] == "TMP_TOKEN_MISSING"


class TestAuthorizationHeaderSpecialCases:
    """Test special cases and edge cases"""
    
    def test_token_with_spaces_inside(self, client, mock_redis):
        """Test token containing spaces is rejected"""
        response = client.post(
            "/api/auth/v2/2fa/enroll",
            headers={"Authorization": "Bearer token with spaces"},
            json={"secret": "test_secret"}
        )
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data["error"] == "INVALID_TOKEN_FORMAT"
    
    def test_very_long_token(self, client, mock_redis):
        """Test very long token (10KB) is rejected gracefully"""
        long_token = "a" * 10240
        
        response = client.post(
            "/api/auth/v2/2fa/enroll",
            headers={"Authorization": f"Bearer {long_token}"},
            json={"secret": "test_secret"}
        )
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data["error"] == "TMP_TOKEN_INVALID"
    
    def test_token_with_special_characters(self, client, mock_redis):
        """Test token with special characters is rejected"""
        special_token = "token!@#$%^&*()"
        
        response = client.post(
            "/api/auth/v2/2fa/enroll",
            headers={"Authorization": f"Bearer {special_token}"},
            json={"secret": "test_secret"}
        )
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data["error"] == "TMP_TOKEN_INVALID"
    
    def test_token_with_null_byte(self, client, mock_redis):
        """Test token with null byte is rejected"""
        response = client.post(
            "/api/auth/v2/2fa/enroll",
            headers={"Authorization": "Bearer token\x00withNull"},
            json={"secret": "test_secret"}
        )
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data["error"] == "TMP_TOKEN_INVALID"


class TestAuthorizationHeaderWithScopeEnforcement:
    """Test Authorization header integration with scope enforcement"""
    
    def test_enroll_scope_on_enroll_endpoint(self, client, mock_redis, mock_supabase, mock_totp):
        """Test enroll scope token works on enroll endpoint"""
        manager = get_pre_auth_manager()
        token = manager.generate_token("user-001", "test@example.com", "enroll")
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        
        response = client.post(
            "/api/auth/v2/2fa/enroll",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
    
    def test_challenge_scope_on_enroll_endpoint(self, client, mock_redis):
        """Test challenge scope token fails on enroll endpoint"""
        manager = get_pre_auth_manager()
        token = manager.generate_token("user-001", "test@example.com", "challenge")
        
        response = client.post(
            "/api/auth/v2/2fa/enroll",
            headers={"Authorization": f"Bearer {token}"},
            json={"secret": "test_secret"}
        )
        
        assert response.status_code == 403
        data = json.loads(response.data)
        assert data["error"] == "SCOPE_MISMATCH"
        assert "enroll" in data["message"]
    
    def test_challenge_scope_on_challenge_endpoint(
        self, client, mock_redis, mock_supabase, mock_totp
    ):
        """Test challenge scope token works on challenge endpoint"""
        manager = get_pre_auth_manager()
        token = manager.generate_token("user-001", "test@example.com", "challenge")
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {
                "user_id": "user-001",
                "enabled": True,
                "secret_encrypted": "encrypted_secret",
            }
        ]
        
        response = client.post(
            "/api/auth/v2/2fa/challenge",
            headers={"Authorization": f"Bearer {token}"},
            json={"code": "123456"}
        )
        
        assert response.status_code == 200
    
    def test_enroll_scope_on_challenge_endpoint(
        self, client, mock_redis, mock_supabase
    ):
        """Test enroll scope token fails on challenge endpoint"""
        manager = get_pre_auth_manager()
        token = manager.generate_token("user-001", "test@example.com", "enroll")
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {
                "user_id": "user-001",
                "enabled": True,
                "secret_encrypted": "encrypted_secret",
            }
        ]
        
        response = client.post(
            "/api/auth/v2/2fa/challenge",
            headers={"Authorization": f"Bearer {token}"},
            json={"code": "123456"}
        )
        
        assert response.status_code == 403
        data = json.loads(response.data)
        assert data["error"] == "SCOPE_MISMATCH"
        assert "challenge" in data["message"]


class TestAuthorizationHeaderErrorMessages:
    """Test error messages are clear and actionable"""
    
    def test_missing_header_error_message(self, client, mock_redis):
        """Test missing Authorization header returns clear error message"""
        response = client.post(
            "/api/auth/v2/2fa/enroll",
            json={"secret": "test_secret"}
        )
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert "Pre-authentication token required" in data["message"]
        assert "login first" in data["message"].lower()
    
    def test_invalid_format_error_message(self, client, mock_redis):
        """Test invalid format returns clear error message"""
        response = client.post(
            "/api/auth/v2/2fa/enroll",
            headers={"Authorization": "InvalidFormat"},
            json={"secret": "test_secret"}
        )
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert "Bearer" in data["message"]
        assert "format" in data["message"].lower()
    
    def test_invalid_token_error_message(self, client, mock_redis):
        """Test invalid token returns clear error message"""
        response = client.post(
            "/api/auth/v2/2fa/enroll",
            headers={"Authorization": "Bearer invalid_token"},
            json={"secret": "test_secret"}
        )
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert "invalid" in data["message"].lower() or "expired" in data["message"].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
