"""
Tests for rollout routes (LangGraph Rollout Dashboard API)
Issue #2600: Unit tests for rollout.py API endpoints

Tests cover:
- GET /api/rollout/dashboard - Full dashboard summary
- GET /api/rollout/health - Health status
- POST /api/rollout/circuit-breaker/reset - Manual reset (requires admin auth)
- GET /api/rollout/comparison - LangGraph vs Simple Mode comparison
- GET /api/rollout/slo - SLO compliance status
"""
import pytest
import os
import sys
from unittest.mock import patch, MagicMock
from enum import Enum


class MockCircuitState(Enum):
    """Mock circuit breaker state enum"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@pytest.fixture
def app():
    """Create Flask app for testing"""
    with patch.dict(os.environ, {
        'TESTING': 'true',
        'JWT_SECRET_KEY': 'test-secret-key-that-is-at-least-32-characters-long',
        'FLASK_SECRET_KEY': 'test-flask-secret-key-at-least-32-chars',
        'SENTRY_DSN': ''
    }):
        if 'src.main' in sys.modules:
            del sys.modules['src.main']

        from src.main import app as flask_app
        from src.models.user import db

        flask_app.config['TESTING'] = True
        flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

        with flask_app.app_context():
            db.create_all()
            yield flask_app
            db.session.remove()
            db.drop_all()


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def mock_rollout_tracker():
    """Create mock RolloutTracker with autospec-like behavior.

    Note: We use MagicMock with spec_set to ensure only valid attributes
    are accessed, providing similar safety to autospec without requiring
    the actual RolloutTracker class import.
    """
    mock = MagicMock()
    # Define expected methods to catch typos in test code
    mock.get_dashboard_summary = MagicMock()
    mock.get_rollout_health = MagicMock()
    mock.get_comparison = MagicMock()
    mock.evaluate_slo_compliance = MagicMock()
    mock.get_circuit_breaker_state = MagicMock()
    mock.reset_circuit_breaker = MagicMock()
    return mock


@pytest.fixture
def mock_health_result():
    """Create mock health result"""
    mock = MagicMock()
    mock.healthy = True
    mock.slo_compliant = True
    mock.circuit_state = MockCircuitState.CLOSED
    mock.to_dict.return_value = {
        "healthy": True,
        "slo_compliant": True,
        "circuit_state": "closed",
        "can_advance": False,
        "should_rollback": False,
        "issues": [],
        "recommendations": []
    }
    return mock


@pytest.fixture
def mock_comparison_result():
    """Create mock comparison result"""
    mock = MagicMock()
    mock.to_dict.return_value = {
        "langgraph": {
            "total_tasks": 100,
            "success_rate": 98.5,
            "p95_latency_ms": 2500
        },
        "simple": {
            "total_tasks": 200,
            "success_rate": 97.0,
            "p95_latency_ms": 3000
        },
        "langgraph_advantage": {
            "success_rate_diff": 1.5,
            "p95_latency_diff_ms": 500
        }
    }
    return mock


@pytest.fixture
def mock_circuit_breaker_state():
    """Create mock circuit breaker state"""
    mock = MagicMock()
    mock.state = MockCircuitState.CLOSED
    return mock


class TestRolloutDashboardEndpoint:
    """Tests for GET /api/rollout/dashboard endpoint"""

    def test_dashboard_tracker_unavailable_returns_503(self, client):
        """Test GET /api/rollout/dashboard returns 503 when tracker unavailable"""
        with patch('src.routes.rollout._get_rollout_tracker', return_value=None):
            response = client.get('/api/rollout/dashboard')

            assert response.status_code == 503
            data = response.get_json()
            assert data['error'] == 'RolloutTracker unavailable'
            assert data['available'] is False
            assert 'timestamp' in data

    def test_dashboard_success(self, client, mock_rollout_tracker):
        """Test GET /api/rollout/dashboard returns dashboard data"""
        mock_rollout_tracker.get_dashboard_summary.return_value = {
            "rollout_info": {
                "current_stage": "STAGE_1",
                "current_percent": 5,
                "can_advance": False,
                "should_rollback": False
            },
            "health": {
                "healthy": True,
                "slo_compliant": True,
                "issues": [],
                "recommendations": []
            },
            "comparison": {},
            "circuit_breaker": {
                "state": "closed",
                "failure_count": 0
            }
        }

        with patch('src.routes.rollout._get_rollout_tracker', return_value=mock_rollout_tracker):
            with patch('src.routes.rollout._get_current_rollout_percent', return_value=5):
                response = client.get('/api/rollout/dashboard')

                assert response.status_code == 200
                data = response.get_json()
                assert data['available'] is True
                assert 'timestamp' in data
                assert data['window_minutes'] == 15
                assert 'rollout_info' in data
                assert 'health' in data

    def test_dashboard_custom_window(self, client, mock_rollout_tracker):
        """Test GET /api/rollout/dashboard with custom window parameter"""
        mock_rollout_tracker.get_dashboard_summary.return_value = {}

        with patch('src.routes.rollout._get_rollout_tracker', return_value=mock_rollout_tracker):
            with patch('src.routes.rollout._get_current_rollout_percent', return_value=0):
                response = client.get('/api/rollout/dashboard?window=60')

                assert response.status_code == 200
                data = response.get_json()
                assert data['window_minutes'] == 60

    def test_dashboard_window_out_of_range_uses_default(self, client, mock_rollout_tracker):
        """Test GET /api/rollout/dashboard with out-of-range window uses default"""
        mock_rollout_tracker.get_dashboard_summary.return_value = {}

        with patch('src.routes.rollout._get_rollout_tracker', return_value=mock_rollout_tracker):
            with patch('src.routes.rollout._get_current_rollout_percent', return_value=0):
                response = client.get('/api/rollout/dashboard?window=500')

                assert response.status_code == 200
                data = response.get_json()
                assert data['window_minutes'] == 15

    def test_dashboard_invalid_window_uses_default(self, client, mock_rollout_tracker):
        """Test GET /api/rollout/dashboard with invalid window uses default"""
        mock_rollout_tracker.get_dashboard_summary.return_value = {}

        with patch('src.routes.rollout._get_rollout_tracker', return_value=mock_rollout_tracker):
            with patch('src.routes.rollout._get_current_rollout_percent', return_value=0):
                response = client.get('/api/rollout/dashboard?window=invalid')

                assert response.status_code == 200
                data = response.get_json()
                assert data['window_minutes'] == 15

    def test_dashboard_exception_returns_500(self, client, mock_rollout_tracker):
        """Test GET /api/rollout/dashboard returns 500 on exception"""
        mock_rollout_tracker.get_dashboard_summary.side_effect = Exception("Database error")

        with patch('src.routes.rollout._get_rollout_tracker', return_value=mock_rollout_tracker):
            with patch('src.routes.rollout._get_current_rollout_percent', return_value=0):
                response = client.get('/api/rollout/dashboard')

                assert response.status_code == 500
                data = response.get_json()
                assert 'error' in data
                assert data['available'] is False


class TestRolloutHealthEndpoint:
    """Tests for GET /api/rollout/health endpoint"""

    def test_health_tracker_unavailable_returns_503(self, client):
        """Test GET /api/rollout/health returns 503 when tracker unavailable"""
        with patch('src.routes.rollout._get_rollout_tracker', return_value=None):
            response = client.get('/api/rollout/health')

            assert response.status_code == 503
            data = response.get_json()
            assert data['status'] == 'unavailable'
            assert data['error'] == 'RolloutTracker unavailable'
            assert 'timestamp' in data

    def test_health_success_healthy(self, client, mock_rollout_tracker, mock_health_result):
        """Test GET /api/rollout/health returns healthy status"""
        mock_rollout_tracker.get_rollout_health.return_value = mock_health_result

        with patch('src.routes.rollout._get_rollout_tracker', return_value=mock_rollout_tracker):
            with patch('src.routes.rollout._get_current_rollout_percent', return_value=5):
                response = client.get('/api/rollout/health')

                assert response.status_code == 200
                data = response.get_json()
                assert data['status'] == 'healthy'
                assert data['healthy'] is True
                assert data['slo_compliant'] is True
                assert 'timestamp' in data
                assert data['window_minutes'] == 15

    def test_health_degraded_when_slo_not_compliant(self, client, mock_rollout_tracker):
        """Test GET /api/rollout/health returns degraded when SLO not compliant"""
        mock_health = MagicMock()
        mock_health.healthy = True
        mock_health.slo_compliant = False
        mock_health.circuit_state = MockCircuitState.CLOSED
        mock_health.to_dict.return_value = {
            "healthy": True,
            "slo_compliant": False,
            "circuit_state": "closed"
        }
        mock_rollout_tracker.get_rollout_health.return_value = mock_health

        with patch('src.routes.rollout._get_rollout_tracker', return_value=mock_rollout_tracker):
            with patch('src.routes.rollout._get_current_rollout_percent', return_value=5):
                response = client.get('/api/rollout/health')

                assert response.status_code == 200
                data = response.get_json()
                assert data['status'] == 'degraded'

    def test_health_degraded_when_circuit_open(self, client, mock_rollout_tracker):
        """Test GET /api/rollout/health returns degraded when circuit breaker open"""
        mock_health = MagicMock()
        mock_health.healthy = True
        mock_health.slo_compliant = True
        mock_health.circuit_state = MockCircuitState.OPEN
        mock_health.to_dict.return_value = {
            "healthy": True,
            "slo_compliant": True,
            "circuit_state": "open"
        }
        mock_rollout_tracker.get_rollout_health.return_value = mock_health

        with patch('src.routes.rollout._get_rollout_tracker', return_value=mock_rollout_tracker):
            with patch('src.routes.rollout._get_current_rollout_percent', return_value=5):
                response = client.get('/api/rollout/health')

                assert response.status_code == 200
                data = response.get_json()
                assert data['status'] == 'degraded'

    def test_health_unhealthy(self, client, mock_rollout_tracker):
        """Test GET /api/rollout/health returns unhealthy status"""
        mock_health = MagicMock()
        mock_health.healthy = False
        mock_health.slo_compliant = False
        mock_health.circuit_state = MockCircuitState.OPEN
        mock_health.to_dict.return_value = {
            "healthy": False,
            "slo_compliant": False,
            "circuit_state": "open"
        }
        mock_rollout_tracker.get_rollout_health.return_value = mock_health

        with patch('src.routes.rollout._get_rollout_tracker', return_value=mock_rollout_tracker):
            with patch('src.routes.rollout._get_current_rollout_percent', return_value=5):
                response = client.get('/api/rollout/health')

                assert response.status_code == 200
                data = response.get_json()
                assert data['status'] == 'unhealthy'

    def test_health_exception_returns_500(self, client, mock_rollout_tracker):
        """Test GET /api/rollout/health returns 500 on exception"""
        mock_rollout_tracker.get_rollout_health.side_effect = Exception("Redis error")

        with patch('src.routes.rollout._get_rollout_tracker', return_value=mock_rollout_tracker):
            with patch('src.routes.rollout._get_current_rollout_percent', return_value=0):
                response = client.get('/api/rollout/health')

                assert response.status_code == 500
                data = response.get_json()
                assert data['status'] == 'error'
                assert 'error' in data


class TestCircuitBreakerResetEndpoint:
    """Tests for POST /api/rollout/circuit-breaker/reset endpoint"""

    def test_reset_no_auth_returns_401(self, client):
        """Test POST /api/rollout/circuit-breaker/reset without auth returns 401"""
        response = client.post('/api/rollout/circuit-breaker/reset')

        assert response.status_code == 401
        data = response.get_json()
        assert 'error' in data

    def test_reset_non_admin_returns_403(self, client, auth_headers_user):
        """Test POST /api/rollout/circuit-breaker/reset with non-admin returns 403"""
        response = client.post('/api/rollout/circuit-breaker/reset', headers=auth_headers_user)

        assert response.status_code == 403
        data = response.get_json()
        assert 'error' in data

    def test_reset_tracker_unavailable_returns_503(self, client, auth_headers_admin):
        """Test POST /api/rollout/circuit-breaker/reset returns 503 when tracker unavailable"""
        with patch('src.routes.rollout._get_rollout_tracker', return_value=None):
            response = client.post('/api/rollout/circuit-breaker/reset', headers=auth_headers_admin)

            assert response.status_code == 503
            data = response.get_json()
            assert data['success'] is False
            assert data['error'] == 'RolloutTracker unavailable'

    def test_reset_success(self, client, auth_headers_admin, mock_rollout_tracker, mock_circuit_breaker_state):
        """Test POST /api/rollout/circuit-breaker/reset successfully resets"""
        mock_rollout_tracker.get_circuit_breaker_state.return_value = mock_circuit_breaker_state

        with patch('src.routes.rollout._get_rollout_tracker', return_value=mock_rollout_tracker):
            response = client.post('/api/rollout/circuit-breaker/reset', headers=auth_headers_admin)

            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert data['message'] == 'Circuit breaker manually reset'
            assert 'timestamp' in data
            assert 'previous_state' in data
            assert 'new_state' in data
            mock_rollout_tracker.reset_circuit_breaker.assert_called_once()

    def test_reset_with_reason(self, client, auth_headers_admin, mock_rollout_tracker, mock_circuit_breaker_state):
        """Test POST /api/rollout/circuit-breaker/reset with custom reason"""
        mock_rollout_tracker.get_circuit_breaker_state.return_value = mock_circuit_breaker_state

        with patch('src.routes.rollout._get_rollout_tracker', return_value=mock_rollout_tracker):
            response = client.post(
                '/api/rollout/circuit-breaker/reset',
                headers=auth_headers_admin,
                json={"reason": "Investigated and resolved the issue"}
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert data['reason'] == 'Investigated and resolved the issue'

    def test_reset_reason_truncation(self, client, auth_headers_admin, mock_rollout_tracker, mock_circuit_breaker_state):
        """Test POST /api/rollout/circuit-breaker/reset truncates long reason"""
        mock_rollout_tracker.get_circuit_breaker_state.return_value = mock_circuit_breaker_state
        long_reason = "x" * 600

        with patch('src.routes.rollout._get_rollout_tracker', return_value=mock_rollout_tracker):
            response = client.post(
                '/api/rollout/circuit-breaker/reset',
                headers=auth_headers_admin,
                json={"reason": long_reason}
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert len(data['reason']) == 503
            assert data['reason'].endswith('...')

    def test_reset_exception_returns_500(self, client, auth_headers_admin, mock_rollout_tracker, mock_circuit_breaker_state):
        """Test POST /api/rollout/circuit-breaker/reset returns 500 on exception"""
        mock_rollout_tracker.get_circuit_breaker_state.return_value = mock_circuit_breaker_state
        mock_rollout_tracker.reset_circuit_breaker.side_effect = Exception("Redis error")

        with patch('src.routes.rollout._get_rollout_tracker', return_value=mock_rollout_tracker):
            response = client.post('/api/rollout/circuit-breaker/reset', headers=auth_headers_admin)

            assert response.status_code == 500
            data = response.get_json()
            assert data['success'] is False
            assert 'error' in data


class TestRolloutComparisonEndpoint:
    """Tests for GET /api/rollout/comparison endpoint"""

    def test_comparison_tracker_unavailable_returns_503(self, client):
        """Test GET /api/rollout/comparison returns 503 when tracker unavailable"""
        with patch('src.routes.rollout._get_rollout_tracker', return_value=None):
            response = client.get('/api/rollout/comparison')

            assert response.status_code == 503
            data = response.get_json()
            assert data['error'] == 'RolloutTracker unavailable'
            assert data['available'] is False

    def test_comparison_success(self, client, mock_rollout_tracker, mock_comparison_result):
        """Test GET /api/rollout/comparison returns comparison data"""
        mock_rollout_tracker.get_comparison.return_value = mock_comparison_result

        with patch('src.routes.rollout._get_rollout_tracker', return_value=mock_rollout_tracker):
            response = client.get('/api/rollout/comparison')

            assert response.status_code == 200
            data = response.get_json()
            assert data['available'] is True
            assert 'timestamp' in data
            assert data['window_minutes'] == 15
            assert 'langgraph' in data
            assert 'simple' in data
            assert 'langgraph_advantage' in data

    def test_comparison_custom_window(self, client, mock_rollout_tracker, mock_comparison_result):
        """Test GET /api/rollout/comparison with custom window"""
        mock_rollout_tracker.get_comparison.return_value = mock_comparison_result

        with patch('src.routes.rollout._get_rollout_tracker', return_value=mock_rollout_tracker):
            response = client.get('/api/rollout/comparison?window=30')

            assert response.status_code == 200
            data = response.get_json()
            assert data['window_minutes'] == 30

    def test_comparison_exception_returns_500(self, client, mock_rollout_tracker):
        """Test GET /api/rollout/comparison returns 500 on exception"""
        mock_rollout_tracker.get_comparison.side_effect = Exception("Calculation error")

        with patch('src.routes.rollout._get_rollout_tracker', return_value=mock_rollout_tracker):
            response = client.get('/api/rollout/comparison')

            assert response.status_code == 500
            data = response.get_json()
            assert 'error' in data
            assert data['available'] is False


class TestSLOComplianceEndpoint:
    """Tests for GET /api/rollout/slo endpoint"""

    def test_slo_tracker_unavailable_returns_503(self, client):
        """Test GET /api/rollout/slo returns 503 when tracker unavailable"""
        with patch('src.routes.rollout._get_rollout_tracker', return_value=None):
            response = client.get('/api/rollout/slo')

            assert response.status_code == 503
            data = response.get_json()
            assert data['error'] == 'RolloutTracker unavailable'
            assert data['available'] is False

    def test_slo_success(self, client, mock_rollout_tracker):
        """Test GET /api/rollout/slo returns SLO compliance data"""
        mock_rollout_tracker.evaluate_slo_compliance.return_value = {
            "compliant": True,
            "thresholds": {
                "p95_latency_ms": 5000,
                "failure_rate_percent": 5.0,
                "error_5xx_rate_percent": 1.0
            },
            "current_values": {
                "p95_latency_ms": 2500,
                "failure_rate_percent": 1.5,
                "error_5xx_rate_percent": 0.2
            },
            "violations": []
        }

        with patch('src.routes.rollout._get_rollout_tracker', return_value=mock_rollout_tracker):
            response = client.get('/api/rollout/slo')

            assert response.status_code == 200
            data = response.get_json()
            assert data['available'] is True
            assert 'timestamp' in data
            assert data['window_minutes'] == 15
            assert data['compliant'] is True
            assert 'thresholds' in data
            assert 'current_values' in data
            assert 'violations' in data

    def test_slo_with_violations(self, client, mock_rollout_tracker):
        """Test GET /api/rollout/slo returns violations when SLO breached"""
        mock_rollout_tracker.evaluate_slo_compliance.return_value = {
            "compliant": False,
            "thresholds": {
                "p95_latency_ms": 5000,
                "failure_rate_percent": 5.0
            },
            "current_values": {
                "p95_latency_ms": 6000,
                "failure_rate_percent": 2.0
            },
            "violations": ["P95 latency exceeds threshold: 6000ms > 5000ms"]
        }

        with patch('src.routes.rollout._get_rollout_tracker', return_value=mock_rollout_tracker):
            response = client.get('/api/rollout/slo')

            assert response.status_code == 200
            data = response.get_json()
            assert data['compliant'] is False
            assert len(data['violations']) == 1

    def test_slo_exception_returns_500(self, client, mock_rollout_tracker):
        """Test GET /api/rollout/slo returns 500 on exception"""
        mock_rollout_tracker.evaluate_slo_compliance.side_effect = Exception("SLO calculation error")

        with patch('src.routes.rollout._get_rollout_tracker', return_value=mock_rollout_tracker):
            response = client.get('/api/rollout/slo')

            assert response.status_code == 500
            data = response.get_json()
            assert 'error' in data
            assert data['available'] is False


class TestWindowParameterValidation:
    """Tests for window parameter validation across all endpoints"""

    @pytest.mark.parametrize("window,expected", [
        (None, 15),
        ("15", 15),
        ("1", 1),
        ("240", 240),
        ("0", 15),
        ("-1", 15),
        ("241", 15),
        ("abc", 15),
        ("", 15),
    ])
    def test_window_parameter_validation(self, client, mock_rollout_tracker, window, expected):
        """Test window parameter validation with various inputs"""
        mock_rollout_tracker.get_dashboard_summary.return_value = {}

        with patch('src.routes.rollout._get_rollout_tracker', return_value=mock_rollout_tracker):
            with patch('src.routes.rollout._get_current_rollout_percent', return_value=0):
                url = '/api/rollout/dashboard'
                if window is not None:
                    url += f'?window={window}'

                response = client.get(url)

                assert response.status_code == 200
                data = response.get_json()
                assert data['window_minutes'] == expected


class TestHelperFunctions:
    """Tests for helper functions in rollout.py"""

    def test_get_tracker_or_503_returns_tracker(self, app):
        """Test _get_tracker_or_503 returns tracker when available"""
        from src.routes.rollout import _get_tracker_or_503

        mock_tracker = MagicMock()
        with patch('src.routes.rollout._get_rollout_tracker', return_value=mock_tracker):
            with app.app_context():
                tracker, error = _get_tracker_or_503()

                assert tracker is mock_tracker
                assert error is None

    def test_get_tracker_or_503_returns_error(self, app):
        """Test _get_tracker_or_503 returns 503 error when tracker unavailable"""
        from src.routes.rollout import _get_tracker_or_503

        with patch('src.routes.rollout._get_rollout_tracker', return_value=None):
            with app.app_context():
                tracker, error = _get_tracker_or_503()

                assert tracker is None
                assert error is not None
                response, status_code = error
                assert status_code == 503

    def test_json_error_default(self, app):
        """Test _json_error creates error response with defaults"""
        from src.routes.rollout import _json_error

        with app.app_context():
            response, status_code = _json_error("Test error")

            assert status_code == 500
            data = response.get_json()
            assert data['error'] == 'Test error'
            assert data['available'] is False
            assert 'timestamp' in data

    def test_json_error_custom_status(self, app):
        """Test _json_error with custom status code"""
        from src.routes.rollout import _json_error

        with app.app_context():
            response, status_code = _json_error("Not found", status=404)

            assert status_code == 404
            data = response.get_json()
            assert data['error'] == 'Not found'

    def test_json_error_without_available(self, app):
        """Test _json_error without available field"""
        from src.routes.rollout import _json_error

        with app.app_context():
            response, status_code = _json_error("Error", include_available=False)

            data = response.get_json()
            assert 'available' not in data

    def test_get_current_rollout_percent_returns_100(self, app):
        """Test _get_current_rollout_percent returns 100 (LangGraph 100% rolled out)
        
        Since LangGraph is now 100% rolled out and the use_langgraph_percent
        setting has been removed from Settings, this function always returns 100.
        """
        from src.routes.rollout import _get_current_rollout_percent

        result = _get_current_rollout_percent()
        assert result == 100

    def test_get_current_rollout_percent_does_not_use_settings(self, app):
        """Test _get_current_rollout_percent does not depend on get_settings
        
        This test ensures the function doesn't accidentally reintroduce
        a dependency on the deleted use_langgraph_percent setting.
        """
        from src.routes.rollout import _get_current_rollout_percent

        with patch('src.routes.rollout.get_settings', side_effect=Exception("Should not be called"), create=True):
            result = _get_current_rollout_percent()
            assert result == 100

    def test_parse_window_minutes_valid(self, app):
        """Test _parse_window_minutes with valid input"""
        from src.routes.rollout import _parse_window_minutes

        assert _parse_window_minutes("30") == 30
        assert _parse_window_minutes("1") == 1
        assert _parse_window_minutes("240") == 240

    def test_parse_window_minutes_none(self, app):
        """Test _parse_window_minutes with None returns default"""
        from src.routes.rollout import _parse_window_minutes

        assert _parse_window_minutes(None) == 15

    def test_parse_window_minutes_invalid(self, app):
        """Test _parse_window_minutes with invalid input returns default"""
        from src.routes.rollout import _parse_window_minutes

        assert _parse_window_minutes("abc") == 15
        assert _parse_window_minutes("") == 15

    def test_parse_window_minutes_out_of_range(self, app):
        """Test _parse_window_minutes with out-of-range input returns default"""
        from src.routes.rollout import _parse_window_minutes

        assert _parse_window_minutes("0") == 15
        assert _parse_window_minutes("-5") == 15
        assert _parse_window_minutes("500") == 15


class TestErrorResponseBodyValidation:
    """Tests to verify error response body structure and content.

    These tests ensure that error responses follow a consistent format
    and contain all required fields for proper error handling by clients.
    """

    def test_503_error_response_structure_dashboard(self, client):
        """Verify 503 error response has correct structure for dashboard endpoint"""
        with patch('src.routes.rollout._get_rollout_tracker', return_value=None):
            response = client.get('/api/rollout/dashboard')

            assert response.status_code == 503
            data = response.get_json()

            # Verify required fields
            assert 'error' in data, "Error response must contain 'error' field"
            assert 'timestamp' in data, "Error response must contain 'timestamp' field"
            assert 'available' in data, "Error response must contain 'available' field"

            # Verify field values
            assert data['error'] == 'RolloutTracker unavailable'
            assert data['available'] is False
            assert isinstance(data['timestamp'], str)
            assert len(data['timestamp']) > 0

    def test_503_error_response_structure_comparison(self, client):
        """Verify 503 error response has correct structure for comparison endpoint"""
        with patch('src.routes.rollout._get_rollout_tracker', return_value=None):
            response = client.get('/api/rollout/comparison')

            assert response.status_code == 503
            data = response.get_json()

            assert 'error' in data
            assert 'timestamp' in data
            assert 'available' in data
            assert data['error'] == 'RolloutTracker unavailable'
            assert data['available'] is False

    def test_503_error_response_structure_slo(self, client):
        """Verify 503 error response has correct structure for SLO endpoint"""
        with patch('src.routes.rollout._get_rollout_tracker', return_value=None):
            response = client.get('/api/rollout/slo')

            assert response.status_code == 503
            data = response.get_json()

            assert 'error' in data
            assert 'timestamp' in data
            assert 'available' in data
            assert data['error'] == 'RolloutTracker unavailable'
            assert data['available'] is False

    def test_500_error_response_contains_exception_message(self, client, mock_rollout_tracker):
        """Verify 500 error response contains the exception message"""
        error_message = "Specific database connection error"
        mock_rollout_tracker.get_dashboard_summary.side_effect = Exception(error_message)

        with patch('src.routes.rollout._get_rollout_tracker', return_value=mock_rollout_tracker):
            with patch('src.routes.rollout._get_current_rollout_percent', return_value=0):
                response = client.get('/api/rollout/dashboard')

                assert response.status_code == 500
                data = response.get_json()

                assert 'error' in data
                assert error_message in data['error']
                assert data['available'] is False

    def test_health_503_error_has_status_field(self, client):
        """Verify health endpoint 503 error includes status field"""
        with patch('src.routes.rollout._get_rollout_tracker', return_value=None):
            response = client.get('/api/rollout/health')

            assert response.status_code == 503
            data = response.get_json()

            # Health endpoint has special 'status' field
            assert 'status' in data
            assert data['status'] == 'unavailable'
            assert 'error' in data
            assert 'timestamp' in data

    def test_health_500_error_has_status_error(self, client, mock_rollout_tracker):
        """Verify health endpoint 500 error has status='error'"""
        mock_rollout_tracker.get_rollout_health.side_effect = Exception("Redis timeout")

        with patch('src.routes.rollout._get_rollout_tracker', return_value=mock_rollout_tracker):
            with patch('src.routes.rollout._get_current_rollout_percent', return_value=0):
                response = client.get('/api/rollout/health')

                assert response.status_code == 500
                data = response.get_json()

                assert data['status'] == 'error'
                assert 'error' in data
                assert 'Redis timeout' in data['error']

    def test_reset_503_error_has_success_false(self, client, auth_headers_admin):
        """Verify reset endpoint 503 error has success=False"""
        with patch('src.routes.rollout._get_rollout_tracker', return_value=None):
            response = client.post('/api/rollout/circuit-breaker/reset', headers=auth_headers_admin)

            assert response.status_code == 503
            data = response.get_json()

            assert 'success' in data
            assert data['success'] is False
            assert 'error' in data
            assert 'timestamp' in data

    def test_reset_500_error_has_success_false(self, client, auth_headers_admin, mock_rollout_tracker, mock_circuit_breaker_state):
        """Verify reset endpoint 500 error has success=False"""
        mock_rollout_tracker.get_circuit_breaker_state.return_value = mock_circuit_breaker_state
        mock_rollout_tracker.reset_circuit_breaker.side_effect = Exception("Reset failed")

        with patch('src.routes.rollout._get_rollout_tracker', return_value=mock_rollout_tracker):
            response = client.post('/api/rollout/circuit-breaker/reset', headers=auth_headers_admin)

            assert response.status_code == 500
            data = response.get_json()

            assert data['success'] is False
            assert 'error' in data
            assert 'Reset failed' in data['error']

    def test_timestamp_format_is_iso8601(self, client):
        """Verify timestamp follows ISO 8601 format"""
        import re

        with patch('src.routes.rollout._get_rollout_tracker', return_value=None):
            response = client.get('/api/rollout/dashboard')

            data = response.get_json()
            timestamp = data['timestamp']

            # ISO 8601 format: YYYY-MM-DDTHH:MM:SSZ
            iso_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$'
            assert re.match(iso_pattern, timestamp), f"Timestamp '{timestamp}' does not match ISO 8601 format"
