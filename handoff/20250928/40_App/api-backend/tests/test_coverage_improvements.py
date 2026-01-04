"""
Targeted tests to improve code coverage to 80%+

Tests cover specific missing lines in:
- models/user.py: __repr__ method (line 15)
- utils/i18n.py: Translation file loading edge cases (lines 34-36, 46-48, 50-51)
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
