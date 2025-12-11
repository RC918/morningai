"""
Tests for action_requests API routes to improve coverage
Covers HITL (Human-in-the-Loop) functionality for high-risk operations
"""
import pytest
import sys
import os
from unittest.mock import patch


@pytest.fixture
def app():
    """Create Flask app instance for testing"""
    with patch.dict(os.environ, {'SENTRY_DSN': '', 'SECRET_KEY': 'test-secret'}):
        if 'src.main' in sys.modules:
            del sys.modules['src.main']

        from src.main import app as flask_app
        flask_app.config['TESTING'] = True
        yield flask_app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def admin_headers():
    """Create authentication headers with admin JWT token"""
    from src.middleware.auth_middleware import create_admin_token
    token = create_admin_token()
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture
def user_headers():
    """Create authentication headers with user JWT token"""
    from src.middleware.auth_middleware import create_user_token
    token = create_user_token()
    return {'Authorization': f'Bearer {token}'}


class TestActionRequestsHealth:
    """Test action requests health endpoint"""

    def test_health_check_hitl_available(self, client):
        """Test health check when HITL is available"""
        with patch('src.routes.action_requests.HITL_AVAILABLE', True):
            response = client.get('/api/action-requests/health')

            assert response.status_code == 200
            data = response.get_json()
            assert data['hitl_available'] is True
            assert data['status'] == 'healthy'

    def test_health_check_hitl_unavailable(self, client):
        """Test health check when HITL is unavailable"""
        with patch('src.routes.action_requests.HITL_AVAILABLE', False):
            response = client.get('/api/action-requests/health')

            assert response.status_code == 200
            data = response.get_json()
            assert data['hitl_available'] is False
            assert data['status'] == 'degraded'


class TestListPendingRequests:
    """Test list pending requests endpoint"""

    def test_list_pending_hitl_unavailable(self, client, admin_headers):
        """Test list pending when HITL unavailable"""
        with patch('src.routes.action_requests.HITL_AVAILABLE', False):
            response = client.get('/api/action-requests', headers=admin_headers)

            assert response.status_code == 503
            data = response.get_json()
            assert 'error' in data
            assert data['hitl_available'] is False

    @patch('src.routes.action_requests.HITL_AVAILABLE', True)
    @patch('src.routes.action_requests.get_pending_requests')
    def test_list_pending_success(self, mock_get_pending, client, admin_headers):
        """Test successful list pending requests"""
        mock_get_pending.return_value = [
            {'request_id': 'req-1', 'risk_level': 'high'},
            {'request_id': 'req-2', 'risk_level': 'medium'}
        ]

        response = client.get('/api/action-requests', headers=admin_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert 'requests' in data
        assert data['count'] == 2

    @patch('src.routes.action_requests.HITL_AVAILABLE', True)
    @patch('src.routes.action_requests.RiskLevel')
    @patch('src.routes.action_requests.get_pending_requests')
    def test_list_pending_with_risk_filter(self, mock_get_pending, mock_risk_level, client, admin_headers):
        """Test list pending with risk level filter"""
        mock_risk_level.return_value = 'high'
        mock_get_pending.return_value = []

        response = client.get('/api/action-requests?risk_level=high', headers=admin_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data['filters']['risk_level'] == 'high'

    @patch('src.routes.action_requests.HITL_AVAILABLE', True)
    @patch('src.routes.action_requests.RiskLevel')
    def test_list_pending_invalid_risk_level(self, mock_risk_level, client, admin_headers):
        """Test list pending with invalid risk level"""
        mock_risk_level.side_effect = ValueError('Invalid risk level')

        response = client.get('/api/action-requests?risk_level=invalid', headers=admin_headers)

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'valid_values' in data

    @patch('src.routes.action_requests.HITL_AVAILABLE', True)
    @patch('src.routes.action_requests.get_pending_requests')
    def test_list_pending_exception(self, mock_get_pending, client, admin_headers):
        """Test list pending exception handling"""
        mock_get_pending.side_effect = Exception('Database error')

        response = client.get('/api/action-requests', headers=admin_headers)

        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data


class TestGetRequestDetails:
    """Test get request details endpoint"""

    def test_get_details_hitl_unavailable(self, client, admin_headers):
        """Test get details when HITL unavailable"""
        with patch('src.routes.action_requests.HITL_AVAILABLE', False):
            response = client.get('/api/action-requests/req-123', headers=admin_headers)

            assert response.status_code == 503

    @patch('src.routes.action_requests.HITL_AVAILABLE', True)
    @patch('src.routes.action_requests.get_request_status')
    def test_get_details_not_found(self, mock_get_status, client, admin_headers):
        """Test get details when request not found"""
        mock_get_status.return_value = None

        response = client.get('/api/action-requests/non-existent', headers=admin_headers)

        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data

    @patch('src.routes.action_requests.HITL_AVAILABLE', True)
    @patch('src.routes.action_requests.get_request_status')
    def test_get_details_success(self, mock_get_status, client, admin_headers):
        """Test successful get request details"""
        mock_get_status.return_value = {
            'request_id': 'req-123',
            'status': 'pending',
            'risk_level': 'high',
            'action': 'deploy_to_production'
        }

        response = client.get('/api/action-requests/req-123', headers=admin_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data['request_id'] == 'req-123'
        assert data['status'] == 'pending'

    @patch('src.routes.action_requests.HITL_AVAILABLE', True)
    @patch('src.routes.action_requests.get_request_status')
    def test_get_details_exception(self, mock_get_status, client, admin_headers):
        """Test get details exception handling"""
        mock_get_status.side_effect = Exception('Database error')

        response = client.get('/api/action-requests/req-123', headers=admin_headers)

        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data


class TestApproveRequest:
    """Test approve request endpoint"""

    def test_approve_hitl_unavailable(self, client, admin_headers):
        """Test approve when HITL unavailable"""
        with patch('src.routes.action_requests.HITL_AVAILABLE', False):
            response = client.post('/api/action-requests/req-123/approve', headers=admin_headers)

            assert response.status_code == 503

    @patch('src.routes.action_requests.HITL_AVAILABLE', True)
    @patch('src.routes.action_requests.approve_action_request')
    def test_approve_success(self, mock_approve, client, admin_headers):
        """Test successful approve request"""
        mock_approve.return_value = True

        response = client.post('/api/action-requests/req-123/approve', headers=admin_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['status'] == 'approved'
        assert 'approved_by' in data

    @patch('src.routes.action_requests.HITL_AVAILABLE', True)
    @patch('src.routes.action_requests.approve_action_request')
    def test_approve_failed(self, mock_approve, client, admin_headers):
        """Test approve request failed"""
        mock_approve.return_value = False

        response = client.post('/api/action-requests/req-123/approve', headers=admin_headers)

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    @patch('src.routes.action_requests.HITL_AVAILABLE', True)
    @patch('src.routes.action_requests.approve_action_request')
    def test_approve_exception(self, mock_approve, client, admin_headers):
        """Test approve exception handling"""
        mock_approve.side_effect = Exception('Database error')

        response = client.post('/api/action-requests/req-123/approve', headers=admin_headers)

        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data


class TestRejectRequest:
    """Test reject request endpoint"""

    def test_reject_hitl_unavailable(self, client, admin_headers):
        """Test reject when HITL unavailable"""
        with patch('src.routes.action_requests.HITL_AVAILABLE', False):
            response = client.post('/api/action-requests/req-123/reject', headers=admin_headers)

            assert response.status_code == 503

    @patch('src.routes.action_requests.HITL_AVAILABLE', True)
    @patch('src.routes.action_requests.reject_action_request')
    def test_reject_success(self, mock_reject, client, admin_headers):
        """Test successful reject request"""
        mock_reject.return_value = True

        response = client.post(
            '/api/action-requests/req-123/reject',
            headers=admin_headers,
            json={'reason': 'Too risky'}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['status'] == 'rejected'
        assert data['reason'] == 'Too risky'

    @patch('src.routes.action_requests.HITL_AVAILABLE', True)
    @patch('src.routes.action_requests.reject_action_request')
    def test_reject_without_reason(self, mock_reject, client, admin_headers):
        """Test reject request without reason"""
        mock_reject.return_value = True

        response = client.post('/api/action-requests/req-123/reject', headers=admin_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['reason'] is None

    @patch('src.routes.action_requests.HITL_AVAILABLE', True)
    @patch('src.routes.action_requests.reject_action_request')
    def test_reject_failed(self, mock_reject, client, admin_headers):
        """Test reject request failed"""
        mock_reject.return_value = False

        response = client.post('/api/action-requests/req-123/reject', headers=admin_headers)

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    @patch('src.routes.action_requests.HITL_AVAILABLE', True)
    @patch('src.routes.action_requests.reject_action_request')
    def test_reject_exception(self, mock_reject, client, admin_headers):
        """Test reject exception handling"""
        mock_reject.side_effect = Exception('Database error')

        response = client.post('/api/action-requests/req-123/reject', headers=admin_headers)

        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data


class TestProcessTimeouts:
    """Test process timeouts endpoint"""

    def test_process_timeouts_hitl_unavailable(self, client, admin_headers):
        """Test process timeouts when HITL unavailable"""
        with patch('src.routes.action_requests.HITL_AVAILABLE', False):
            response = client.post('/api/action-requests/process-timeouts', headers=admin_headers)

            assert response.status_code == 503

    @patch('src.routes.action_requests.HITL_AVAILABLE', True)
    @patch('src.routes.action_requests.process_timed_out_requests')
    def test_process_timeouts_success(self, mock_process, client, admin_headers):
        """Test successful process timeouts"""
        mock_process.return_value = 5

        response = client.post('/api/action-requests/process-timeouts', headers=admin_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['timed_out_count'] == 5

    @patch('src.routes.action_requests.HITL_AVAILABLE', True)
    @patch('src.routes.action_requests.process_timed_out_requests')
    def test_process_timeouts_exception(self, mock_process, client, admin_headers):
        """Test process timeouts exception handling"""
        mock_process.side_effect = Exception('Database error')

        response = client.post('/api/action-requests/process-timeouts', headers=admin_headers)

        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data


class TestGetStatistics:
    """Test get statistics endpoint"""

    def test_statistics_hitl_unavailable(self, client, admin_headers):
        """Test statistics when HITL unavailable"""
        with patch('src.routes.action_requests.HITL_AVAILABLE', False):
            response = client.get('/api/action-requests/statistics', headers=admin_headers)

            assert response.status_code == 503

    @patch('src.routes.action_requests.HITL_AVAILABLE', True)
    @patch('src.routes.action_requests.get_action_request_statistics')
    def test_statistics_success(self, mock_stats, client, admin_headers):
        """Test successful get statistics"""
        mock_stats.return_value = {
            'pending_count': 10,
            'by_risk_level': {
                'critical': 2,
                'high': 3,
                'medium': 3,
                'low': 2
            }
        }

        response = client.get('/api/action-requests/statistics', headers=admin_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data['pending_count'] == 10
        assert 'by_risk_level' in data

    @patch('src.routes.action_requests.HITL_AVAILABLE', True)
    @patch('src.routes.action_requests.get_action_request_statistics')
    def test_statistics_empty(self, mock_stats, client, admin_headers):
        """Test statistics with empty data"""
        mock_stats.return_value = {}

        response = client.get('/api/action-requests/statistics', headers=admin_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data['pending_count'] == 0
        assert data['by_risk_level'] == {
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0
        }

    @patch('src.routes.action_requests.HITL_AVAILABLE', True)
    @patch('src.routes.action_requests.get_action_request_statistics')
    def test_statistics_exception(self, mock_stats, client, admin_headers):
        """Test statistics exception handling"""
        mock_stats.side_effect = Exception('Database error')

        response = client.get('/api/action-requests/statistics', headers=admin_headers)

        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data


class TestRequireHitlDecorator:
    """Test require_hitl_available decorator"""

    def test_decorator_blocks_when_unavailable(self, client, admin_headers):
        """Test decorator blocks requests when HITL unavailable"""
        with patch('src.routes.action_requests.HITL_AVAILABLE', False):
            response = client.get('/api/action-requests', headers=admin_headers)

            assert response.status_code == 503
            data = response.get_json()
            assert data['hitl_available'] is False


class TestAuthorizationRequirements:
    """Test authorization requirements for endpoints"""

    def test_list_pending_requires_auth(self, client):
        """Test list pending requires authentication"""
        with patch('src.routes.action_requests.HITL_AVAILABLE', True):
            response = client.get('/api/action-requests')

            assert response.status_code == 401

    def test_approve_requires_admin(self, client, user_headers):
        """Test approve requires admin role"""
        with patch('src.routes.action_requests.HITL_AVAILABLE', True):
            response = client.post('/api/action-requests/req-123/approve', headers=user_headers)

            assert response.status_code == 403

    def test_reject_requires_admin(self, client, user_headers):
        """Test reject requires admin role"""
        with patch('src.routes.action_requests.HITL_AVAILABLE', True):
            response = client.post('/api/action-requests/req-123/reject', headers=user_headers)

            assert response.status_code == 403
