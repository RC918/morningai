"""
Unit tests for middleware/auth_middleware.py

Tests JWT authentication middleware functionality.
"""

import pytest
import jwt as pyjwt
import datetime
from unittest.mock import MagicMock
import sys
from pathlib import Path
import os

pytestmark = pytest.mark.unit
os.environ['IDEMPOTENCY_TESTS_ALLOWED'] = 'true'

sys.modules['flask'] = MagicMock()
sys.modules['common'] = MagicMock()
sys.modules['common.config'] = MagicMock()
sys.modules['common.config.settings'] = MagicMock()

mock_settings = MagicMock()
mock_settings.jwt_secret_key = 'test-secret-key-for-testing'
sys.modules['common.config.settings'].get_settings.return_value = mock_settings

sys.path.insert(0, str(Path(__file__).parent.parent / 'handoff' / '20250928' / '40_App' / 'api-backend' / 'src'))

from middleware.auth_middleware import (
    normalize_role,
    verify_jwt_library,
    create_admin_token,
    create_analyst_token,
    create_user_token,
    generate_jwt_token
)


class TestVerifyJwtLibrary:
    """Test JWT library verification."""
    
    def test_verify_success(self):
        """Test that PyJWT is correctly installed."""
        verify_jwt_library()
        assert hasattr(pyjwt, 'encode')
        assert hasattr(pyjwt, 'decode')


class TestNormalizeRole:
    """Test role normalization."""
    
    def test_admin_roles(self):
        """Test admin role normalization."""
        assert normalize_role('admin') == 'admin'
        assert normalize_role('超級管理員') == 'admin'
    
    def test_analyst_roles(self):
        """Test analyst role normalization."""
        assert normalize_role('analyst') == 'analyst'
        assert normalize_role('operator') == 'analyst'
        assert normalize_role('分析師') == 'analyst'
        assert normalize_role('操作員') == 'analyst'
    
    def test_user_roles(self):
        """Test user role normalization."""
        assert normalize_role('user') == 'user'
        assert normalize_role('viewer') == 'user'
        assert normalize_role('查看者') == 'user'
    
    def test_unknown_role(self):
        """Test unknown role returns as-is."""
        assert normalize_role('unknown') == 'unknown'
        assert normalize_role('') == ''


class TestGenerateJwtToken:
    """Test JWT token generation."""
    
    def test_basic_token(self):
        """Test basic token generation."""
        user_data = {
            'id': 1,
            'username': 'testuser',
            'role': 'user'
        }
        
        token = generate_jwt_token(user_data)
        
        assert token is not None
        assert isinstance(token, str)
        
        payload = pyjwt.decode(token, 'test-secret-key-for-testing', algorithms=['HS256'])
        assert payload['user_id'] == 1
        assert payload['username'] == 'testuser'
        assert payload['role'] == 'user'
        assert 'exp' in payload
        assert 'iat' in payload
    
    def test_role_normalization(self):
        """Test token generation with role normalization."""
        user_data = {
            'id': 2,
            'username': 'operator',
            'role': 'operator'
        }
        
        token = generate_jwt_token(user_data)
        payload = pyjwt.decode(token, 'test-secret-key-for-testing', algorithms=['HS256'])
        
        assert payload['role'] == 'analyst'
    
    def test_custom_expiry(self):
        """Test token with custom expiry."""
        user_data = {
            'id': 1,
            'username': 'test',
            'role': 'user'
        }
        
        token = generate_jwt_token(user_data, expires_hours=48)
        payload = pyjwt.decode(token, 'test-secret-key-for-testing', algorithms=['HS256'])
        
        exp_time = datetime.datetime.fromtimestamp(payload['exp'], tz=datetime.UTC)
        now = datetime.datetime.now(datetime.UTC)
        time_diff = exp_time - now
        
        assert 47.9 * 3600 < time_diff.total_seconds() < 48.1 * 3600
    
    def test_chinese_role(self):
        """Test token with Chinese role name."""
        user_data = {
            'id': 3,
            'username': 'admin_cn',
            'role': '超級管理員'
        }
        
        token = generate_jwt_token(user_data)
        payload = pyjwt.decode(token, 'test-secret-key-for-testing', algorithms=['HS256'])
        
        assert payload['role'] == 'admin'


class TestTokenHelpers:
    """Test token creation helpers."""
    
    def test_admin_token(self):
        """Test admin token creation."""
        token = create_admin_token()
        
        assert token is not None
        payload = pyjwt.decode(token, 'test-secret-key-for-testing', algorithms=['HS256'])
        
        assert payload['user_id'] == 1
        assert payload['username'] == 'admin'
        assert payload['role'] == 'admin'
    
    def test_admin_token_custom(self):
        """Test admin token with custom parameters."""
        token = create_admin_token(user_id=999, username='custom_admin')
        
        payload = pyjwt.decode(token, 'test-secret-key-for-testing', algorithms=['HS256'])
        
        assert payload['user_id'] == 999
        assert payload['username'] == 'custom_admin'
        assert payload['role'] == 'admin'
    
    def test_analyst_token(self):
        """Test analyst token creation."""
        token = create_analyst_token()
        
        payload = pyjwt.decode(token, 'test-secret-key-for-testing', algorithms=['HS256'])
        
        assert payload['user_id'] == 2
        assert payload['username'] == 'analyst'
        assert payload['role'] == 'analyst'
    
    def test_user_token(self):
        """Test user token creation."""
        token = create_user_token()
        
        payload = pyjwt.decode(token, 'test-secret-key-for-testing', algorithms=['HS256'])
        
        assert payload['user_id'] == 3
        assert payload['username'] == 'user'
        assert payload['role'] == 'user'
    
    def test_all_tokens_valid(self):
        """Test that all helper tokens are valid."""
        admin_token = create_admin_token()
        analyst_token = create_analyst_token()
        user_token = create_user_token()
        
        pyjwt.decode(admin_token, 'test-secret-key-for-testing', algorithms=['HS256'])
        pyjwt.decode(analyst_token, 'test-secret-key-for-testing', algorithms=['HS256'])
        pyjwt.decode(user_token, 'test-secret-key-for-testing', algorithms=['HS256'])
    
    def test_tokens_have_expiry(self):
        """Test that tokens have expiry timestamps."""
        tokens = [
            create_admin_token(),
            create_analyst_token(),
            create_user_token()
        ]
        
        for token in tokens:
            payload = pyjwt.decode(token, 'test-secret-key-for-testing', algorithms=['HS256'])
            assert 'exp' in payload
            assert 'iat' in payload
            
            exp_time = datetime.datetime.fromtimestamp(payload['exp'], tz=datetime.UTC)
            now = datetime.datetime.now(datetime.UTC)
            assert exp_time > now
