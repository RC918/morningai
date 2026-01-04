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

        assert user.preferences == '{"theme": "light", "notifications": true}'


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


class TestBootstrapPaths:
    """Test bootstrap_paths.py edge cases to cover lines 115-119"""

    def test_bootstrap_orchestrator_paths_missing_directory(self):
        """Test bootstrap_orchestrator_paths when orchestrator dir doesn't exist (lines 115-119)"""
        from pathlib import Path

        with patch.object(Path, 'is_dir', return_value=False):
            from src import bootstrap_paths
            bootstrap_paths._bootstrapped = False

            result = bootstrap_paths.bootstrap_orchestrator_paths()

            assert result is False


class TestHelpersAsBool:
    """Test helpers._as_bool function edge cases"""

    def test_as_bool_with_true_bool(self):
        """Test _as_bool with True boolean"""
        from src.utils.helpers import _as_bool
        assert _as_bool(True) is True

    def test_as_bool_with_false_bool(self):
        """Test _as_bool with False boolean"""
        from src.utils.helpers import _as_bool
        assert _as_bool(False) is False

    def test_as_bool_with_none(self):
        """Test _as_bool with None"""
        from src.utils.helpers import _as_bool
        assert _as_bool(None) is False

    def test_as_bool_with_truthy_strings(self):
        """Test _as_bool with truthy string values"""
        from src.utils.helpers import _as_bool
        assert _as_bool('1') is True
        assert _as_bool('true') is True
        assert _as_bool('TRUE') is True
        assert _as_bool('yes') is True
        assert _as_bool('on') is True

    def test_as_bool_with_falsy_strings(self):
        """Test _as_bool with falsy string values"""
        from src.utils.helpers import _as_bool
        assert _as_bool('0') is False
        assert _as_bool('false') is False
        assert _as_bool('no') is False
        assert _as_bool('off') is False
        assert _as_bool('') is False
