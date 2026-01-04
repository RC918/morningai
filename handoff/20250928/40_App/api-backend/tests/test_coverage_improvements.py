"""
Targeted tests to improve code coverage to 80%+

Tests cover specific missing lines in:
- models/user.py: __repr__, to_dict, get_preferences, set_preferences (lines 15, 18, 27-30, 34)
- utils/i18n.py: Translation file loading edge cases (lines 34-36, 46-48, 50-51)
- utils/helpers.py: _as_bool function edge cases (line 42)
- bootstrap_paths.py: orchestrator directory not found warning (lines 115-119)
- services/monitoring_dashboard.py: Exception handling (lines 117-119, 235-236, 268-269)
"""
import json
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from src.models.user import User
from src.services.monitoring_dashboard import MonitoringDashboard, DashboardMetrics


class TestUserModelRepr:
    """Test User model __repr__ method to cover line 15"""

    @pytest.mark.parametrize(
        "username, expected_repr",
        [
            ("testuser", "<User testuser>"),
            ("test_user_123", "<User test_user_123>"),
        ],
    )
    def test_user_repr(self, username, expected_repr):
        """Test User __repr__ returns expected format for various usernames"""
        user = User()
        user.username = username
        repr_str = repr(user)
        assert repr_str == expected_repr


class TestUserModelMethods:
    """Test User model methods to cover lines 18, 27-30, 34"""

    def test_to_dict(self):
        """Test User.to_dict returns correct dictionary (line 18)"""
        user = User()
        user.id = 1
        user.username = "testuser"
        user.email = "test@example.com"
        user.created_at = datetime(2025, 1, 1, 12, 0, 0)

        result = user.to_dict()

        assert result['id'] == 1
        assert result['username'] == "testuser"
        assert result['email'] == "test@example.com"
        assert result['created_at'] == "2025-01-01T12:00:00"

    def test_to_dict_with_none_created_at(self):
        """Test User.to_dict handles None created_at"""
        user = User()
        user.id = 2
        user.username = "testuser2"
        user.email = "test2@example.com"
        user.created_at = None

        result = user.to_dict()

        assert result['created_at'] is None

    def test_get_preferences_valid_json(self):
        """Test User.get_preferences with valid JSON (line 28)"""
        user = User()
        user.preferences = '{"theme": "dark", "language": "en"}'

        result = user.get_preferences()

        assert result == {"theme": "dark", "language": "en"}

    def test_get_preferences_empty_string(self):
        """Test User.get_preferences with empty preferences"""
        user = User()
        user.preferences = None

        result = user.get_preferences()

        assert result == {}

    def test_get_preferences_invalid_json(self):
        """Test User.get_preferences with invalid JSON (lines 29-30)"""
        user = User()
        user.preferences = "not valid json {"

        result = user.get_preferences()

        assert result == {}

    def test_set_preferences(self):
        """Test User.set_preferences sets JSON string (line 34)"""
        user = User()
        prefs = {"theme": "light", "notifications": True}

        user.set_preferences(prefs)

        assert json.loads(user.preferences) == prefs

    def test_get_preferences_type_error(self):
        """Test User.get_preferences with TypeError (line 29-30 TypeError branch)"""
        user = User()
        user.preferences = 12345

        result = user.get_preferences()

        assert result == {}


class TestI18nTranslationLoading:
    """Test I18n translation file loading edge cases"""

    def test_load_translations_directory_not_found(self):
        """Test _load_translations when directory doesn't exist (lines 34-36)"""
        from src.utils.i18n import I18n

        with patch('os.path.exists', return_value=False):
            i18n = I18n()
            assert 'zh-TW' in i18n.translations
            assert 'en-US' in i18n.translations

    def test_load_translations_file_load_error(self):
        """Test _load_translations when file loading fails (lines 46-48)"""
        from src.utils.i18n import I18n

        def mock_exists(path):
            return True

        def mock_open_error(*args, **kwargs):
            raise IOError("Cannot read file")

        with patch('os.path.exists', mock_exists), \
             patch('builtins.open', mock_open_error):
            i18n = I18n()
            assert 'zh-TW' in i18n.translations

    def test_load_translations_file_not_found(self):
        """Test _load_translations when translation file doesn't exist (lines 50-51)"""
        from src.utils.i18n import I18n

        def mock_exists(path):
            if 'translations' in path and not path.endswith('.json'):
                return True
            return False

        with patch('os.path.exists', mock_exists):
            i18n = I18n()
            assert 'zh-TW' in i18n.translations
            assert i18n.translations.get('zh-TW') == {}


# Note: I18n imports are kept inline because they trigger file system operations
# at import time that need to be mocked before the import occurs.


class TestMonitoringDashboardEdgeCases:
    """Test monitoring dashboard edge cases for coverage"""

    @pytest.mark.asyncio
    async def test_calculate_system_health_exception(self):
        """Test _calculate_system_health exception handling (lines 117-119)"""
        dashboard = MonitoringDashboard()

        bad_metrics = {
            'circuit_breakers': None,
            'bulkheads': None
        }

        health = await dashboard._calculate_system_health(bad_metrics)

        assert health['overall_status'] == 'unknown'

    def test_calculate_trends_decreasing_error_rate(self):
        """Test _calculate_trends with decreasing error rate (lines 235-236)"""
        dashboard = MonitoringDashboard()
        base_time = datetime.now()

        metrics = [
            DashboardMetrics(
                timestamp=base_time,
                circuit_breakers={},
                bulkheads={},
                saga_orchestrator={},
                storage_stats={},
                system_health={'error_rate': 0.50}
            ),
            DashboardMetrics(
                timestamp=base_time + timedelta(minutes=1),
                circuit_breakers={},
                bulkheads={},
                saga_orchestrator={},
                storage_stats={},
                system_health={'error_rate': 0.10}
            )
        ]

        trends = dashboard._calculate_trends(metrics)

        assert trends['error_rate_trend'] == 'decreasing'

    def test_generate_alerts_rejected_requests(self):
        """Test _generate_alerts with rejected requests > 10 (lines 268-269)"""
        dashboard = MonitoringDashboard()

        metrics = DashboardMetrics(
            timestamp=datetime.now(),
            circuit_breakers={},
            bulkheads={},
            saga_orchestrator={},
            storage_stats={},
            system_health={
                'error_rate': 0.01,
                'open_circuit_breakers': 0,
                'rejected_requests': 15
            }
        )

        alerts = dashboard._generate_alerts(metrics)

        assert len(alerts) == 1
        assert alerts[0]['level'] == 'warning'
        assert '15 requests rejected' in alerts[0]['message']


class TestVectorsGetDbConnection:
    """Test vectors.py get_db_connection function"""

    def test_get_db_connection(self):
        """Test get_db_connection returns connection from pool"""
        from src.routes.vectors import get_db_connection

        mock_pool = MagicMock()
        mock_conn = MagicMock()
        mock_pool.getconn.return_value = mock_conn

        with patch('src.routes.vectors._get_db_pool', return_value=mock_pool):
            conn = get_db_connection()
            assert conn == mock_conn
            mock_pool.getconn.assert_called_once()


class TestVectorsVisualizationUnavailable:
    """Test vectors.py when visualization libraries are unavailable"""

    @pytest.fixture
    def client(self):
        """Create a test client with proper isolation"""
        from src.main import app
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client

    def test_visualize_returns_503_when_libs_unavailable(self, client):
        """Test visualization endpoint returns 503 when libraries unavailable"""
        from src.middleware.auth_middleware import create_admin_token

        token = create_admin_token()
        headers = {'Authorization': f'Bearer {token}'}

        with patch('src.routes.vectors.VISUALIZATION_AVAILABLE', False):
            response = client.get('/api/vectors/visualize', headers=headers)

            assert response.status_code == 503
            data = json.loads(response.data)
            assert 'Visualization libraries not available' in data['error']


class TestBootstrapPathsDebugMode:
    """Test bootstrap_paths debug mode to cover lines 40, 71"""

    def test_debug_log_with_debug_enabled(self):
        """Test _debug_log with BOOTSTRAP_PATHS_DEBUG=1 (line 40)"""
        import os
        import importlib
        original_debug = os.environ.get('BOOTSTRAP_PATHS_DEBUG', '')
        try:
            os.environ['BOOTSTRAP_PATHS_DEBUG'] = '1'
            import src.bootstrap_paths as bp
            importlib.reload(bp)
            # Call _debug_log which should use logger.info when debug is enabled
            bp._debug_log("test message")
            assert bp._DEBUG is True
        finally:
            os.environ['BOOTSTRAP_PATHS_DEBUG'] = original_debug
            importlib.reload(bp)

    def test_ensure_path_at_front_with_debug(self):
        """Test _ensure_path_at_front with debug enabled (line 71)"""
        import os
        import sys
        import importlib
        original_debug = os.environ.get('BOOTSTRAP_PATHS_DEBUG', '')
        try:
            os.environ['BOOTSTRAP_PATHS_DEBUG'] = '1'
            import src.bootstrap_paths as bp
            importlib.reload(bp)
            # Call _ensure_path_at_front which logs sys.path when debug is enabled
            test_path = '/tmp/test_path_for_coverage'
            bp._ensure_path_at_front(test_path, "test description")
            # Clean up sys.path
            if test_path in sys.path:
                sys.path.remove(test_path)
        finally:
            os.environ['BOOTSTRAP_PATHS_DEBUG'] = original_debug
            importlib.reload(bp)


class TestBootstrapPaths:
    """Test bootstrap_paths.py edge cases to cover lines 115-119"""

    def test_bootstrap_orchestrator_paths_missing_directory(self):
        """Test bootstrap_orchestrator_paths when orchestrator dir doesn't exist (lines 115-119)"""
        from pathlib import Path
        from src import bootstrap_paths
        import importlib

        original_bootstrapped = bootstrap_paths._bootstrapped
        try:
            with patch.object(Path, 'is_dir', return_value=False):
                importlib.reload(bootstrap_paths)
                bootstrap_paths._bootstrapped = False

                result = bootstrap_paths.bootstrap_orchestrator_paths()

                assert result is False
        finally:
            bootstrap_paths._bootstrapped = original_bootstrapped
            importlib.reload(bootstrap_paths)


class TestHelpersAsBool:
    """Test helpers._as_bool function edge cases"""

    @pytest.mark.parametrize(
        "value, expected",
        [
            (True, True),
            (False, False),
            (None, False),
            ('1', True),
            ('true', True),
            ('TRUE', True),
            ('yes', True),
            ('on', True),
            ('0', False),
            ('false', False),
            ('no', False),
            ('off', False),
            ('', False),
            ('  true  ', True),
            ('  1  ', True),
        ]
    )
    def test_as_bool(self, value, expected):
        """Test _as_bool with various inputs."""
        from src.utils.helpers import _as_bool
        assert _as_bool(value) is expected


class TestMonitoringDashboardExportMetrics:
    """Test monitoring dashboard export_metrics function to cover lines 290-300"""

    def test_export_metrics_no_history(self):
        """Test export_metrics when no metrics history (line 291)"""
        dashboard = MonitoringDashboard()
        dashboard.metrics_history = []
        result = dashboard.export_metrics()
        assert 'error' in result
        assert 'No metrics available' in result

    def test_export_metrics_json_format(self):
        """Test export_metrics with json format (lines 295-296)"""
        dashboard = MonitoringDashboard()
        dashboard.metrics_history = [
            DashboardMetrics(
                timestamp=datetime.now(),
                circuit_breakers={'test': {'state': 'closed'}},
                bulkheads={},
                saga_orchestrator={},
                storage_stats={},
                system_health={'error_rate': 0.01}
            )
        ]
        result = dashboard.export_metrics(format='json')
        assert 'circuit_breakers' in result
        assert 'test' in result

    def test_export_metrics_prometheus_format(self):
        """Test export_metrics with prometheus format (lines 297-298)"""
        dashboard = MonitoringDashboard()
        dashboard.metrics_history = [
            DashboardMetrics(
                timestamp=datetime.now(),
                circuit_breakers={'api': {'total_requests': 100, 'failed_requests': 5, 'failure_rate': 0.05}},
                bulkheads={},
                saga_orchestrator={},
                storage_stats={},
                system_health={'error_rate': 0.05, 'open_circuit_breakers': 0}
            )
        ]
        result = dashboard.export_metrics(format='prometheus')
        assert 'circuit_breaker_total_requests' in result
        assert 'system_error_rate' in result

    def test_export_metrics_unsupported_format(self):
        """Test export_metrics with unsupported format (lines 299-300)"""
        dashboard = MonitoringDashboard()
        dashboard.metrics_history = [
            DashboardMetrics(
                timestamp=datetime.now(),
                circuit_breakers={},
                bulkheads={},
                saga_orchestrator={},
                storage_stats={},
                system_health={}
            )
        ]
        result = dashboard.export_metrics(format='xml')
        assert 'Unsupported format' in result


class TestI18nGetLocaleEdgeCases:
    """Test i18n get_locale function edge cases to cover lines 109-114"""

    def test_get_locale_with_zh_tw_header(self):
        """Test get_locale with zh-TW Accept-Language header (line 109-110)"""
        from src.utils.i18n import I18n
        from flask import Flask
        app = Flask(__name__)
        with app.test_request_context(headers={'Accept-Language': 'zh-TW,en;q=0.9'}):
            i18n = I18n()
            result = i18n.get_locale()
            assert result == 'zh-TW'

    def test_get_locale_with_zh_header(self):
        """Test get_locale with zh Accept-Language header (line 111-112)"""
        from src.utils.i18n import I18n
        from flask import Flask
        app = Flask(__name__)
        with app.test_request_context(headers={'Accept-Language': 'zh,en;q=0.9'}):
            i18n = I18n()
            result = i18n.get_locale()
            assert result == 'zh-TW'

    def test_get_locale_with_en_header(self):
        """Test get_locale with en Accept-Language header (line 113-114)"""
        from src.utils.i18n import I18n
        from flask import Flask
        app = Flask(__name__)
        with app.test_request_context(headers={'Accept-Language': 'en-US,en;q=0.9'}):
            i18n = I18n()
            result = i18n.get_locale()
            assert result == 'en-US'

    def test_get_locale_with_unknown_header(self):
        """Test get_locale with unknown Accept-Language header (line 116)"""
        from src.utils.i18n import I18n
        from flask import Flask
        app = Flask(__name__)
        with app.test_request_context(headers={'Accept-Language': 'fr-FR,de;q=0.9'}):
            i18n = I18n()
            result = i18n.get_locale()
            assert result == 'zh-TW'  # default locale

    def test_get_locale_exception_handling(self):
        """Test get_locale exception handling (line 117-118)"""
        from src.utils.i18n import I18n
        i18n = I18n()
        # Outside of request context, should return default locale
        result = i18n.get_locale()
        assert result == 'zh-TW'


class TestMonitoringDashboardUtilization:
    """Test monitoring dashboard _calculate_utilization to cover lines 197-203"""

    def test_calculate_utilization_with_active_requests(self):
        """Test _calculate_utilization with active requests (lines 201-202)"""
        from src.services.monitoring_dashboard import MonitoringDashboard
        dashboard = MonitoringDashboard()
        metrics = {'active_requests': 5, 'available_capacity': 15}
        result = dashboard._calculate_utilization(metrics)
        # 5 / (5 + 15) * 100 = 25%
        assert result == 25.0

    def test_calculate_utilization_zero_capacity(self):
        """Test _calculate_utilization with zero capacity (line 203)"""
        from src.services.monitoring_dashboard import MonitoringDashboard
        dashboard = MonitoringDashboard()
        metrics = {'active_requests': 0, 'available_capacity': 0}
        result = dashboard._calculate_utilization(metrics)
        assert result == 0


class TestI18nUncoveredLines:
    """Test i18n uncovered lines 137, 165-166"""

    def test_t_with_unsupported_locale_fallback(self):
        """Test t method falls back to default locale when locale not in translations (line 137)"""
        from src.utils.i18n import I18n
        i18n = I18n()
        # Use a locale that's not in supported_locales
        result = i18n.t('query.success', locale='fr-FR')
        # Should fall back to default locale (zh-TW) and return the translation
        assert result == '查詢成功'

    def test_translate_response_with_underscore_message(self):
        """Test translate_response with message starting with underscore (lines 165-166)"""
        from src.utils.i18n import I18n
        from flask import Flask
        app = Flask(__name__)
        with app.test_request_context():
            i18n = I18n()
            data = {
                'message': '_query.success',
                'status': 'ok'
            }
            result = i18n.translate_response(data)
            # Message should be translated from _query.success to the actual translation
            assert result['message'] != '_query.success'
            assert result['message'] in ['查詢成功', 'Query successful']


class TestI18nConvenienceFunctions:
    """Test i18n convenience functions to cover lines 227, 232, 245"""

    def test_translate_function(self):
        """Test translate convenience function (line 227)"""
        from src.utils.i18n import translate
        result = translate('query.success')
        assert isinstance(result, str)
        assert len(result) > 0

    def test_get_locale_function(self):
        """Test get_locale convenience function (line 232)"""
        from src.utils.i18n import get_locale
        result = get_locale()
        assert result in ['zh-TW', 'en-US']

    def test_localized_response_function(self):
        """Test localized_response convenience function (line 245)"""
        from src.utils.i18n import localized_response
        data = {'message': 'test', 'status': 'ok'}
        result = localized_response(data)
        assert 'message' in result
        assert 'status' in result

    def test_translate_response_with_error_dict(self):
        """Test translate_response with error dict (lines 168-171)"""
        from src.utils.i18n import I18n
        i18n = I18n()
        data = {
            'error': {
                'message': '_error.unauthorized',
                'code': 'unauthorized'
            }
        }
        result = i18n.translate_response(data)
        assert 'error' in result
        assert result['error']['message'] != '_error.unauthorized'

    def test_t_with_missing_interpolation_variable(self):
        """Test t method with missing interpolation variable (lines 144-145)"""
        from src.utils.i18n import I18n
        i18n = I18n()
        result = i18n.t('error.rate_limit', locale='en-US', missing_var='test')
        assert isinstance(result, str)

    def test_error_response_with_kwargs(self):
        """Test error_response with kwargs (lines 207-208)"""
        from src.utils.i18n import I18n
        from flask import Flask
        app = Flask(__name__)
        with app.test_request_context():
            i18n = I18n()
            response, status = i18n.error_response(
                'invalid_parameter',
                status_code=400,
                field='email',
                message='invalid format'
            )
            assert status == 400
            assert 'error' in response
            assert 'details' in response['error']
            assert response['error']['details']['field'] == 'email'


class TestAuthServiceErrorHandling:
    """Test auth_service.py error handling paths to cover exception branches"""

    def test_log_token_config_on_startup_exception(self):
        """Test _log_token_config_on_startup exception handling (lines 58-65)"""
        from src.services import auth_service
        import importlib
        
        # Save original state
        original_warned = auth_service._warned_startup_config_failed
        
        try:
            # Reset warning flag to test the warning path
            auth_service._warned_startup_config_failed = False
            
            # Mock get_settings to raise an exception
            with patch('src.services.auth_service.get_settings') as mock_settings:
                mock_settings.side_effect = Exception("Settings validation error")
                
                # Call the function - should catch exception and log warning
                auth_service._log_token_config_on_startup()
                
                # Warning flag should be set
                assert auth_service._warned_startup_config_failed is True
        finally:
            # Restore original state
            auth_service._warned_startup_config_failed = original_warned

    def test_is_testing_mode_settings_exception(self):
        """Test is_testing_mode exception handling (lines 106-114)"""
        import os
        from src.services import auth_service
        
        # Save original state
        original_warned = auth_service._warned_settings_load_failed
        original_testing = os.environ.get('TESTING', '')
        
        try:
            # Reset warning flag and remove TESTING env var
            auth_service._warned_settings_load_failed = False
            if 'TESTING' in os.environ:
                del os.environ['TESTING']
            
            # Mock get_settings to raise an exception
            with patch('src.services.auth_service.get_settings') as mock_settings:
                mock_settings.side_effect = Exception("Settings validation error")
                
                # Call the function - should catch exception and return False
                result = auth_service.is_testing_mode()
                
                # Should return False and set warning flag
                assert result is False
                assert auth_service._warned_settings_load_failed is True
        finally:
            # Restore original state
            auth_service._warned_settings_load_failed = original_warned
            if original_testing:
                os.environ['TESTING'] = original_testing

    def test_is_production_with_env_var(self):
        """Test is_production with ENVIRONMENT env var set (lines 130-132)"""
        import os
        from src.services import auth_service
        
        # Save original env var
        original_env = os.environ.get('ENVIRONMENT', '')
        
        try:
            # Set ENVIRONMENT to production
            os.environ['ENVIRONMENT'] = 'production'
            result = auth_service.is_production()
            assert result is True
            
            # Set ENVIRONMENT to development
            os.environ['ENVIRONMENT'] = 'development'
            result = auth_service.is_production()
            assert result is False
        finally:
            # Restore original state
            if original_env:
                os.environ['ENVIRONMENT'] = original_env
            elif 'ENVIRONMENT' in os.environ:
                del os.environ['ENVIRONMENT']

    def test_is_mock_users_enabled_with_env_var(self):
        """Test is_mock_users_enabled with ENABLE_MOCK_USERS env var (lines 181-183)"""
        import os
        from src.services import auth_service
        
        # Save original env var
        original_mock = os.environ.get('ENABLE_MOCK_USERS', '')
        
        try:
            # Mock is_testing_mode to return True
            with patch.object(auth_service, 'is_testing_mode', return_value=True):
                # Set ENABLE_MOCK_USERS to false
                os.environ['ENABLE_MOCK_USERS'] = 'false'
                result = auth_service.is_mock_users_enabled()
                assert result is False
                
                # Set ENABLE_MOCK_USERS to true
                os.environ['ENABLE_MOCK_USERS'] = 'true'
                result = auth_service.is_mock_users_enabled()
                assert result is True
        finally:
            # Restore original state
            if original_mock:
                os.environ['ENABLE_MOCK_USERS'] = original_mock
            elif 'ENABLE_MOCK_USERS' in os.environ:
                del os.environ['ENABLE_MOCK_USERS']
