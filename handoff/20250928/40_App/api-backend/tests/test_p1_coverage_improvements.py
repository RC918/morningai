"""
P1 Coverage Improvement Tests

Target: Improve coverage to 70% for:
- main.py (64.5% -> 70%)
- auth_middleware.py (68.2% -> 70%)
- redis_client.py (51% -> 70%)
- env_schema_validator.py (58.6% -> 70%)
"""
import pytest
import os
import jwt
from datetime import datetime, timedelta, UTC
from unittest.mock import Mock, patch
from flask import Flask


class TestAuthMiddlewareFallbackPaths:
    """Test X-Access-Token and cookie fallback authentication paths"""

    @pytest.fixture
    def app(self):
        """Create Flask app for testing"""
        app = Flask(__name__)
        app.config['TESTING'] = True

        from src.middleware.auth_middleware import jwt_required, admin_required

        @app.route('/test')
        @jwt_required
        def test_endpoint():
            from flask import request
            return {
                'message': 'success',
                'user_id': request.current_user.get('user_id'),
                'role': request.current_user.get('role')
            }, 200

        @app.route('/admin')
        @admin_required
        def admin_endpoint():
            from flask import request
            return {
                'message': 'admin success',
                'user_id': request.current_user.get('user_id')
            }, 200

        return app

    def test_x_access_token_header_fallback(self, app):
        """Test authentication via X-Access-Token header when Authorization is missing"""
        client = app.test_client()

        jwt_secret = os.environ.get('JWT_SECRET_KEY', 'test-secret-key-for-testing')
        payload = {
            'user_id': 1,
            'username': 'test',
            'role': 'user',
            'exp': datetime.now(UTC) + timedelta(hours=1),
            'iat': datetime.now(UTC)
        }
        token = jwt.encode(payload, jwt_secret, algorithm='HS256')

        response = client.get('/test', headers={
            'X-Access-Token': token
        })

        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'success'

    def test_cookie_token_fallback(self, app):
        """Test authentication via access_token cookie when headers are missing"""
        client = app.test_client()

        jwt_secret = os.environ.get('JWT_SECRET_KEY', 'test-secret-key-for-testing')
        payload = {
            'user_id': 2,
            'username': 'cookie_user',
            'role': 'user',
            'exp': datetime.now(UTC) + timedelta(hours=1),
            'iat': datetime.now(UTC)
        }
        token = jwt.encode(payload, jwt_secret, algorithm='HS256')

        client.set_cookie('access_token', token, domain='localhost')
        response = client.get('/test')

        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'success'

    def test_x_access_token_fallback_when_auth_header_invalid(self, app):
        """Test X-Access-Token is used when Authorization header is invalid"""
        client = app.test_client()

        jwt_secret = os.environ.get('JWT_SECRET_KEY', 'test-secret-key-for-testing')
        payload = {
            'user_id': 3,
            'username': 'fallback_user',
            'role': 'admin',
            'exp': datetime.now(UTC) + timedelta(hours=1),
            'iat': datetime.now(UTC)
        }
        valid_token = jwt.encode(payload, jwt_secret, algorithm='HS256')

        response = client.get('/admin', headers={
            'Authorization': 'InvalidFormat',
            'X-Access-Token': valid_token
        })

        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'admin success'

    def test_cookie_fallback_when_both_headers_invalid(self, app):
        """Test cookie is used when both Authorization and X-Access-Token are invalid"""
        client = app.test_client()

        jwt_secret = os.environ.get('JWT_SECRET_KEY', 'test-secret-key-for-testing')
        payload = {
            'user_id': 4,
            'username': 'cookie_fallback',
            'role': 'user',
            'exp': datetime.now(UTC) + timedelta(hours=1),
            'iat': datetime.now(UTC)
        }
        valid_token = jwt.encode(payload, jwt_secret, algorithm='HS256')

        expired_token = jwt.encode({
            'user_id': 99,
            'role': 'user',
            'exp': datetime.now(UTC) - timedelta(hours=1)
        }, jwt_secret, algorithm='HS256')

        client.set_cookie('access_token', valid_token, domain='localhost')
        response = client.get('/test', headers={
            'Authorization': f'Bearer {expired_token}',
            'X-Access-Token': expired_token
        })

        assert response.status_code == 200

    def test_all_auth_methods_fail_returns_original_error(self, app):
        """Test that original Authorization error is returned when all fallbacks fail"""
        client = app.test_client()

        jwt_secret = os.environ.get('JWT_SECRET_KEY', 'test-secret-key-for-testing')
        expired_token = jwt.encode({
            'user_id': 99,
            'role': 'user',
            'exp': datetime.now(UTC) - timedelta(hours=1)
        }, jwt_secret, algorithm='HS256')

        client.set_cookie('access_token', expired_token, domain='localhost')
        response = client.get('/test', headers={
            'Authorization': f'Bearer {expired_token}',
            'X-Access-Token': expired_token
        })

        assert response.status_code == 401
        data = response.get_json()
        assert data['error'] == 'Token expired'


class TestAuthMiddlewareErrorResponses:
    """Test error response mapping in auth_middleware"""

    @pytest.fixture
    def app(self):
        """Create Flask app for testing"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        return app

    def test_error_response_expired_signature(self, app):
        """Test _error_response_from_exception with ExpiredSignatureError"""
        from src.middleware.auth_middleware import _error_response_from_exception

        with app.app_context():
            error = jwt.ExpiredSignatureError("Token expired")
            response, status = _error_response_from_exception(error)

            assert status == 401
            data = response.get_json()
            assert data['error'] == 'Token expired'

    def test_error_response_invalid_token(self, app):
        """Test _error_response_from_exception with InvalidTokenError"""
        from src.middleware.auth_middleware import _error_response_from_exception

        with app.app_context():
            error = jwt.InvalidTokenError("Invalid token")
            response, status = _error_response_from_exception(error)

            assert status == 401
            data = response.get_json()
            assert data['error'] == 'Invalid token'

    def test_error_response_generic_exception(self, app):
        """Test _error_response_from_exception with generic Exception"""
        from src.middleware.auth_middleware import _error_response_from_exception

        with app.app_context():
            error = Exception("Some other error")
            response, status = _error_response_from_exception(error)

            assert status == 401
            data = response.get_json()
            assert data['error'] == 'Authentication failed'


class TestRedisClientConnectionInfo:
    """Test redis_client.py connection info and security check functions"""

    def test_get_redis_connection_info_upstash(self):
        """Test get_redis_connection_info with Upstash configuration"""
        with patch('src.utils.redis_client.get_settings') as mock_settings:
            mock_settings.return_value.upstash_redis_rest_url = 'https://test@upstash.io'
            mock_settings.return_value.redis_url = None

            from src.utils.redis_client import get_redis_connection_info
            info = get_redis_connection_info()

            assert info['type'] == 'upstash'
            assert info['protocol'] == 'https'
            assert info['tls_enabled'] is True

    def test_get_redis_connection_info_redis_tls(self):
        """Test get_redis_connection_info with Redis TLS configuration"""
        with patch('src.utils.redis_client.get_settings') as mock_settings:
            mock_settings.return_value.upstash_redis_rest_url = None
            mock_settings.return_value.redis_url = 'rediss://user:pass@redis.example.com:6379'

            from src.utils.redis_client import get_redis_connection_info
            info = get_redis_connection_info()

            assert info['type'] == 'redis'
            assert info['protocol'] == 'rediss'
            assert info['tls_enabled'] is True

    def test_get_redis_connection_info_redis_no_tls(self):
        """Test get_redis_connection_info with Redis non-TLS configuration"""
        with patch('src.utils.redis_client.get_settings') as mock_settings:
            mock_settings.return_value.upstash_redis_rest_url = None
            mock_settings.return_value.redis_url = 'redis://localhost:6379'

            from src.utils.redis_client import get_redis_connection_info
            info = get_redis_connection_info()

            assert info['type'] == 'redis'
            assert info['protocol'] == 'redis'
            assert info['tls_enabled'] is False

    def test_get_redis_connection_info_none(self):
        """Test get_redis_connection_info with no configuration"""
        with patch('src.utils.redis_client.get_settings') as mock_settings:
            mock_settings.return_value.upstash_redis_rest_url = None
            mock_settings.return_value.redis_url = None

            from src.utils.redis_client import get_redis_connection_info
            info = get_redis_connection_info()

            assert info['type'] == 'none'
            assert info['url'] == 'not_configured'

    def test_check_redis_security_upstash(self):
        """Test check_redis_security with Upstash (always secure)"""
        mock_client = Mock()

        with patch('src.utils.redis_client.get_redis_client', return_value=mock_client):
            with patch('src.utils.redis_client.get_settings') as mock_settings:
                mock_settings.return_value.upstash_redis_rest_url = 'https://test@upstash.io'
                mock_settings.return_value.redis_url = None

                from src.utils.redis_client import check_redis_security
                result = check_redis_security()

                assert result['status'] == 'secure'
                assert result['type'] == 'upstash'
                assert result['cve_2025_49844_risk'] == 'low'

    def test_check_redis_security_vulnerable_version(self):
        """Test check_redis_security with vulnerable Redis version"""
        mock_client = Mock()
        mock_client.info.return_value = {'redis_version': '7.0.0'}

        with patch('src.utils.redis_client.get_redis_client', return_value=mock_client):
            with patch('src.utils.redis_client.get_settings') as mock_settings:
                mock_settings.return_value.upstash_redis_rest_url = None
                mock_settings.return_value.redis_url = 'redis://localhost:6379'

                from src.utils.redis_client import check_redis_security
                result = check_redis_security()

                assert result['status'] == 'vulnerable'
                assert result['cve_2025_49844_risk'] == 'high'
                assert len(result['recommendations']) > 0

    def test_check_redis_security_secure_version(self):
        """Test check_redis_security with secure Redis version"""
        mock_client = Mock()
        mock_client.info.return_value = {'redis_version': '8.2.2'}

        with patch('src.utils.redis_client.get_redis_client', return_value=mock_client):
            with patch('src.utils.redis_client.get_settings') as mock_settings:
                mock_settings.return_value.upstash_redis_rest_url = None
                mock_settings.return_value.redis_url = 'rediss://localhost:6379'

                from src.utils.redis_client import check_redis_security
                result = check_redis_security()

                assert result['status'] == 'secure'
                assert result['cve_2025_49844_risk'] == 'low'

    def test_check_redis_security_no_config(self):
        """Test check_redis_security with no Redis configuration"""
        mock_client = Mock()

        with patch('src.utils.redis_client.get_redis_client', return_value=mock_client):
            with patch('src.utils.redis_client.get_settings') as mock_settings:
                mock_settings.return_value.upstash_redis_rest_url = None
                mock_settings.return_value.redis_url = None

                from src.utils.redis_client import check_redis_security
                result = check_redis_security()

                assert result['status'] == 'unknown'
                assert result['type'] == 'none'

    def test_check_redis_security_connection_error(self):
        """Test check_redis_security handles connection errors"""
        with patch('src.utils.redis_client.get_redis_client', side_effect=Exception("Connection failed")):
            from src.utils.redis_client import check_redis_security
            result = check_redis_security()

            assert result['status'] == 'error'
            assert 'Connection failed' in result['message']

    def test_check_redis_security_version_parse_error(self):
        """Test check_redis_security handles version parsing errors"""
        mock_client = Mock()
        mock_client.info.return_value = {'redis_version': 'invalid-version'}

        with patch('src.utils.redis_client.get_redis_client', return_value=mock_client):
            with patch('src.utils.redis_client.get_settings') as mock_settings:
                mock_settings.return_value.upstash_redis_rest_url = None
                mock_settings.return_value.redis_url = 'redis://localhost:6379'

                from src.utils.redis_client import check_redis_security
                result = check_redis_security()

                assert result['status'] == 'vulnerable'


class TestEnvSchemaValidator:
    """Test env_schema_validator.py validation functions"""

    def test_validate_environment_missing_required(self):
        """Test validate_environment with missing required variables"""
        with patch.dict(os.environ, {}, clear=True):
            from src.utils.env_schema_validator import validate_environment
            result = validate_environment()

            assert result['valid'] is False
            assert len(result['errors']) > 0
            assert any('DATABASE_URL' in e for e in result['errors'])

    def test_validate_environment_all_present(self):
        """Test validate_environment with all required variables present"""
        env_vars = {
            'DATABASE_URL': 'postgresql://localhost/test',
            'APP_VERSION': '1.0.0'
        }
        with patch.dict(os.environ, env_vars, clear=True):
            from src.utils.env_schema_validator import validate_environment
            result = validate_environment()

            assert result['valid'] is True
            assert len(result['errors']) == 0

    def test_validate_environment_with_optional_vars(self):
        """Test validate_environment with optional variables"""
        env_vars = {
            'DATABASE_URL': 'postgresql://localhost/test',
            'APP_VERSION': '1.0.0',
            'REDIS_URL': 'redis://localhost:6379',
            'SENTRY_DSN': 'https://sentry.io/123'
        }
        with patch.dict(os.environ, env_vars, clear=True):
            from src.utils.env_schema_validator import validate_environment
            result = validate_environment()

            assert result['valid'] is True
            assert len(result['warnings']) == 0


class TestMainAppFeatureFlags:
    """Test main.py feature flag and initialization branches"""

    def test_as_bool_function(self):
        """Test _as_bool helper function"""
        from src.main import _as_bool

        assert _as_bool(True) is True
        assert _as_bool(False) is False
        assert _as_bool(None) is False
        assert _as_bool('1') is True
        assert _as_bool('true') is True
        assert _as_bool('yes') is True
        assert _as_bool('on') is True
        assert _as_bool('0') is False
        assert _as_bool('false') is False
        assert _as_bool('no') is False
        assert _as_bool('  TRUE  ') is True

    def test_is_vercel_preview_valid_origin(self):
        """Test is_vercel_preview with valid Vercel preview URL"""
        with patch('src.main.app_settings') as mock_settings:
            mock_settings.environment = 'staging'

            from src.main import is_vercel_preview
            assert is_vercel_preview('https://my-app-abc123.vercel.app') is True

    def test_is_vercel_preview_production_blocked(self):
        """Test is_vercel_preview blocks in production"""
        with patch('src.main.app_settings') as mock_settings:
            mock_settings.environment = 'production'

            from src.main import is_vercel_preview
            assert is_vercel_preview('https://my-app-abc123.vercel.app') is False

    def test_is_vercel_preview_empty_origin(self):
        """Test is_vercel_preview with empty origin"""
        from src.main import is_vercel_preview
        assert is_vercel_preview(None) is False
        assert is_vercel_preview('') is False

    def test_is_vercel_preview_non_vercel_url(self):
        """Test is_vercel_preview with non-Vercel URL"""
        with patch('src.main.app_settings') as mock_settings:
            mock_settings.environment = 'staging'

            from src.main import is_vercel_preview
            assert is_vercel_preview('https://example.com') is False

    def test_get_health_payload_structure(self):
        """Test get_health_payload returns correct structure"""
        with patch('src.main.db') as mock_db:
            mock_conn = Mock()
            mock_db.engine.connect.return_value.__enter__ = Mock(return_value=mock_conn)
            mock_db.engine.connect.return_value.__exit__ = Mock(return_value=False)

            from src.main import get_health_payload
            payload = get_health_payload()

            assert 'status' in payload
            assert 'database' in payload
            assert 'redis' in payload
            assert 'phase' in payload
            assert 'version' in payload
            assert 'timestamp' in payload
            assert 'services' in payload

    def test_get_health_payload_db_error(self):
        """Test get_health_payload handles database errors"""
        with patch('src.main.db') as mock_db:
            mock_db.engine.connect.side_effect = Exception("DB connection failed")

            from src.main import get_health_payload
            payload = get_health_payload()

            assert 'error' in payload['database']

    def test_before_send_filters_400_errors(self):
        """Test before_send filters 400 errors
        
        NOTE: before_send is now in src/extensions/sentry.py (Phase 1 refactoring: PR1f)
        """
        from src.extensions.sentry import before_send

        class MockException:
            code = 400

        event = {'request': {}}
        hint = {'exc_info': (type(MockException), MockException(), None)}

        result = before_send(event, hint)
        assert result is None

    def test_before_send_filters_404_errors(self):
        """Test before_send filters 404 errors
        
        NOTE: before_send is now in src/extensions/sentry.py (Phase 1 refactoring: PR1f)
        """
        from src.extensions.sentry import before_send

        class MockException:
            code = 404

        event = {'request': {}}
        hint = {'exc_info': (type(MockException), MockException(), None)}

        result = before_send(event, hint)
        assert result is None

    def test_before_send_passes_500_errors(self):
        """Test before_send passes through 500 errors
        
        NOTE: before_send is now in src/extensions/sentry.py (Phase 1 refactoring: PR1f)
        """
        from src.extensions.sentry import before_send

        class MockException:
            code = 500

        event = {'request': {}}
        hint = {'exc_info': (type(MockException), MockException(), None)}

        result = before_send(event, hint)
        assert result == event

    def test_before_send_filters_status_code_400(self):
        """Test before_send filters events with status_code 400
        
        NOTE: before_send is now in src/extensions/sentry.py (Phase 1 refactoring: PR1f)
        """
        from src.extensions.sentry import before_send

        event = {'request': {'status_code': 400}}
        hint = {}

        result = before_send(event, hint)
        assert result is None

    def test_before_send_passes_normal_events(self):
        """Test before_send passes normal events
        
        NOTE: before_send is now in src/extensions/sentry.py (Phase 1 refactoring: PR1f)
        """
        from src.extensions.sentry import before_send

        event = {'request': {'status_code': 200}}
        hint = {}

        result = before_send(event, hint)
        assert result == event


class TestRedisClientCreateFunctions:
    """Test redis_client.py create_redis_client function branches"""

    def test_create_redis_client_upstash_success(self):
        """Test create_redis_client with Upstash Redis"""
        mock_upstash_client = Mock()

        with patch('src.utils.redis_client.get_settings') as mock_settings:
            mock_settings.return_value.upstash_redis_rest_url = 'https://test.upstash.io'
            mock_settings.return_value.upstash_redis_rest_token = 'test-token'
            mock_settings.return_value.redis_url = None

            with patch.dict('sys.modules', {'upstash_redis': Mock()}):
                import sys
                sys.modules['upstash_redis'].Redis = Mock(return_value=mock_upstash_client)

                from src.utils.redis_client import create_redis_client
                result = create_redis_client(skip_ping=True)
                assert result is not None

    def test_create_redis_client_standard_redis(self):
        """Test create_redis_client with standard Redis"""
        mock_redis_client = Mock()

        with patch('src.utils.redis_client.get_settings') as mock_settings:
            mock_settings.return_value.upstash_redis_rest_url = None
            mock_settings.return_value.redis_url = 'redis://localhost:6379'

            with patch('redis.from_url', return_value=mock_redis_client):
                from src.utils.redis_client import create_redis_client
                result = create_redis_client(skip_ping=True)
                assert result is mock_redis_client

    def test_create_redis_client_no_config_raises(self):
        """Test create_redis_client raises when no config"""
        with patch('src.utils.redis_client.get_settings') as mock_settings:
            mock_settings.return_value.upstash_redis_rest_url = None
            mock_settings.return_value.redis_url = None

            from src.utils.redis_client import create_redis_client

            with pytest.raises(ValueError, match="No Redis configuration found"):
                create_redis_client(skip_ping=True)
