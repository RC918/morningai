"""
Unit tests for CSRF middleware.

Tests the csrf_protect decorator and should_enforce_csrf function
to ensure proper CSRF protection behavior.
"""

import pytest
from flask import Flask
from unittest.mock import patch, MagicMock

from src.middleware.csrf import csrf_protect, should_enforce_csrf, UNSAFE_METHODS, CSRF_EXEMPT_PATHS


class TestCsrfProtectDecorator:
    """Test the csrf_protect decorator."""
    
    def test_safe_method_bypasses_csrf_check(self):
        """GET requests should bypass CSRF check (line 40)."""
        app = Flask(__name__)
        
        @app.route('/test', methods=['GET'])
        @csrf_protect
        def test_route():
            return {'status': 'ok'}
        
        with app.test_client() as client:
            response = client.get('/test')
            assert response.status_code == 200
            assert response.json == {'status': 'ok'}
    
    def test_exempt_path_bypasses_csrf_check(self):
        """Exempt paths should bypass CSRF check (line 43)."""
        app = Flask(__name__)
        
        @app.route('/api/auth/v2/login', methods=['POST'])
        @csrf_protect
        def login_route():
            return {'status': 'logged_in'}
        
        with app.test_client() as client:
            response = client.post('/api/auth/v2/login')
            assert response.status_code == 200
            assert response.json == {'status': 'logged_in'}
    
    def test_csrf_bootstrap_endpoint_exempt(self):
        """CSRF bootstrap endpoint should be exempt."""
        app = Flask(__name__)
        
        @app.route('/api/auth/v2/csrf', methods=['POST'])
        @csrf_protect
        def csrf_route():
            return {'csrf_token': 'test'}
        
        with app.test_client() as client:
            response = client.post('/api/auth/v2/csrf')
            assert response.status_code == 200
    
    @patch('src.middleware.csrf.should_enforce_csrf')
    def test_csrf_not_enforced_when_samesite_not_none(self, mock_enforce):
        """CSRF should not be enforced when SameSite != None (lines 45-47)."""
        mock_enforce.return_value = False
        
        app = Flask(__name__)
        
        @app.route('/api/protected', methods=['POST'])
        @csrf_protect
        def protected_route():
            return {'status': 'ok'}
        
        with app.test_client() as client:
            response = client.post('/api/protected')
            assert response.status_code == 200
            assert response.json == {'status': 'ok'}
    
    @patch('src.middleware.csrf.should_enforce_csrf')
    def test_missing_csrf_cookie_returns_403(self, mock_enforce):
        """Missing CSRF cookie should return 403 (lines 49-52)."""
        mock_enforce.return_value = True
        
        app = Flask(__name__)
        
        @app.route('/api/protected', methods=['POST'])
        @csrf_protect
        def protected_route():
            return {'status': 'ok'}
        
        with app.test_client() as client:
            response = client.post('/api/protected')
            assert response.status_code == 403
            assert 'CSRF token missing' in response.json['error']
    
    @patch('src.middleware.csrf.should_enforce_csrf')
    def test_missing_csrf_header_returns_403(self, mock_enforce):
        """Missing CSRF header should return 403 (lines 54-57)."""
        mock_enforce.return_value = True
        
        app = Flask(__name__)
        
        @app.route('/api/protected', methods=['POST'])
        @csrf_protect
        def protected_route():
            return {'status': 'ok'}
        
        with app.test_client() as client:
            # Set cookie but no header
            client.set_cookie('csrf_token', 'test-token')
            response = client.post('/api/protected')
            assert response.status_code == 403
            assert 'CSRF token missing in header' in response.json['error']
    
    @patch('src.middleware.csrf.should_enforce_csrf')
    def test_mismatched_csrf_tokens_returns_403(self, mock_enforce):
        """Mismatched CSRF tokens should return 403 (lines 59-61)."""
        mock_enforce.return_value = True
        
        app = Flask(__name__)
        
        @app.route('/api/protected', methods=['POST'])
        @csrf_protect
        def protected_route():
            return {'status': 'ok'}
        
        with app.test_client() as client:
            client.set_cookie('csrf_token', 'cookie-token')
            response = client.post(
                '/api/protected',
                headers={'X-CSRF-Token': 'different-header-token'}
            )
            assert response.status_code == 403
            assert 'CSRF token invalid' in response.json['error']
    
    @patch('src.middleware.csrf.should_enforce_csrf')
    def test_matching_csrf_tokens_passes(self, mock_enforce):
        """Matching CSRF tokens should pass validation (lines 63-64)."""
        mock_enforce.return_value = True
        
        app = Flask(__name__)
        
        @app.route('/api/protected', methods=['POST'])
        @csrf_protect
        def protected_route():
            return {'status': 'ok'}
        
        with app.test_client() as client:
            client.set_cookie('csrf_token', 'matching-token')
            response = client.post(
                '/api/protected',
                headers={'X-CSRF-Token': 'matching-token'}
            )
            assert response.status_code == 200
            assert response.json == {'status': 'ok'}
    
    def test_put_method_requires_csrf(self):
        """PUT method should require CSRF check."""
        assert 'PUT' in UNSAFE_METHODS
    
    def test_patch_method_requires_csrf(self):
        """PATCH method should require CSRF check."""
        assert 'PATCH' in UNSAFE_METHODS
    
    def test_delete_method_requires_csrf(self):
        """DELETE method should require CSRF check."""
        assert 'DELETE' in UNSAFE_METHODS
    
    def test_post_method_requires_csrf(self):
        """POST method should require CSRF check."""
        assert 'POST' in UNSAFE_METHODS


class TestShouldEnforceCsrf:
    """Test the should_enforce_csrf function."""
    
    @patch('common.config.settings.settings')
    def test_returns_true_when_samesite_none(self, mock_settings):
        """Should return True when cookie_samesite is 'None'."""
        mock_settings.cookie_samesite = 'None'
        assert should_enforce_csrf() is True
    
    @patch('common.config.settings.settings')
    def test_returns_false_when_samesite_strict(self, mock_settings):
        """Should return False when cookie_samesite is 'Strict'."""
        mock_settings.cookie_samesite = 'Strict'
        assert should_enforce_csrf() is False
    
    @patch('common.config.settings.settings')
    def test_returns_false_when_samesite_lax(self, mock_settings):
        """Should return False when cookie_samesite is 'Lax'."""
        mock_settings.cookie_samesite = 'Lax'
        assert should_enforce_csrf() is False
    
    @patch('common.config.settings.settings')
    def test_returns_false_when_samesite_not_set(self, mock_settings):
        """Should return False when cookie_samesite is None (defaults to Strict)."""
        mock_settings.cookie_samesite = None
        assert should_enforce_csrf() is False


class TestCsrfExemptPaths:
    """Test CSRF exempt paths configuration."""
    
    def test_login_path_is_exempt(self):
        """Login path should be exempt from CSRF."""
        assert '/api/auth/v2/login' in CSRF_EXEMPT_PATHS
    
    def test_csrf_bootstrap_path_is_exempt(self):
        """CSRF bootstrap path should be exempt from CSRF."""
        assert '/api/auth/v2/csrf' in CSRF_EXEMPT_PATHS
