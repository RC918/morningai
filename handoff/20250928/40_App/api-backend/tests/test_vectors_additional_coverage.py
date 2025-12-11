"""
Additional tests for Vector routes to improve coverage to 80%+

Tests cover:
- Visualization library unavailable scenarios
- Database pool edge cases
- Connection release error handling
- Authentication requirements
- Additional error paths
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from datetime import datetime
from src.main import app
from src.middleware.auth_middleware import create_admin_token, create_user_token


@pytest.fixture
def client():
    """Flask test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def admin_headers():
    """Generate admin JWT token for authentication"""
    token = create_admin_token()
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture
def user_headers():
    """Generate user JWT token for authentication"""
    token = create_user_token()
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture
def mock_db_connection():
    """Mock database connection"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    with patch('src.routes.vectors.get_db_connection', return_value=mock_conn), \
         patch('src.routes.vectors.release_db_connection'):
        yield mock_conn, mock_cursor


class TestVisualizationUnavailable:
    """Test when visualization libraries are not available"""

    @patch('src.routes.vectors.VISUALIZATION_AVAILABLE', False)
    def test_visualize_returns_503_when_libs_unavailable(self, client, admin_headers):
        """Visualization endpoint returns 503 when libraries unavailable"""
        response = client.get(
            '/api/vectors/visualize',
            headers=admin_headers
        )

        assert response.status_code == 503
        data = json.loads(response.data)
        assert 'Visualization libraries not available' in data['error']


class TestAuthentication:
    """Test authentication requirements for vector endpoints"""

    def test_visualize_without_token_returns_401(self, client):
        """Visualization endpoint without JWT returns 401"""
        response = client.get('/api/vectors/visualize')
        assert response.status_code == 401

    def test_clusters_without_token_returns_401(self, client):
        """Clusters endpoint without JWT returns 401"""
        response = client.get('/api/vectors/clusters')
        assert response.status_code == 401

    def test_drift_without_token_returns_401(self, client):
        """Drift endpoint without JWT returns 401"""
        response = client.get('/api/vectors/drift')
        assert response.status_code == 401

    def test_statistics_without_token_returns_401(self, client):
        """Statistics endpoint without JWT returns 401"""
        response = client.get('/api/vectors/statistics')
        assert response.status_code == 401

    def test_refresh_without_token_returns_401(self, client):
        """Refresh endpoint without JWT returns 401"""
        response = client.post('/api/vectors/refresh')
        assert response.status_code == 401


class TestVisualizationEdgeCases:
    """Test visualization edge cases"""

    def test_visualize_with_null_embeddings(self, client, mock_db_connection, admin_headers):
        """Visualization handles null embeddings gracefully"""
        mock_conn, mock_cursor = mock_db_connection

        mock_results = [
            {
                'id': 'vec-1',
                'embedding': None,
                'source': 'test',
                'category': 'test',
                'text_preview': 'test',
                'query_count': 1,
                'created_at': datetime.now()
            },
            {
                'id': 'vec-2',
                'embedding': [float(j) for j in range(128)],
                'source': 'test',
                'category': 'test',
                'text_preview': 'test',
                'query_count': 1,
                'created_at': datetime.now()
            }
        ]
        mock_cursor.fetchall.return_value = mock_results

        response = client.get(
            '/api/vectors/visualize?limit=10',
            headers=admin_headers
        )

        assert response.status_code == 400

    def test_visualize_with_null_metadata(self, client, mock_db_connection, admin_headers):
        """Visualization handles null metadata fields"""
        import numpy as np
        mock_conn, mock_cursor = mock_db_connection

        mock_results = [
            {
                'id': f'vec-{i}',
                'embedding': [float(j) for j in range(128)],
                'source': None,
                'category': None,
                'text_preview': None,
                'query_count': None,
                'created_at': None
            }
            for i in range(10)
        ]
        mock_cursor.fetchall.return_value = mock_results

        mock_tsne = MagicMock()
        mock_tsne.fit_transform.return_value = np.random.rand(10, 2)

        with patch('src.routes.vectors.TSNE', return_value=mock_tsne):
            response = client.get(
                '/api/vectors/visualize?limit=10',
                headers=admin_headers
            )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['data']['vector_count'] == 10


class TestDriftEdgeCases:
    """Test drift detection edge cases"""

    def test_drift_with_mixed_statuses(self, client, mock_db_connection, admin_headers):
        """Drift detection handles all status types"""
        mock_conn, mock_cursor = mock_db_connection

        mock_results = [
            {'source': 'growing', 'drift_score': 0.9, 'status': 'HIGH_GROWTH', 'vector_count': 100},
            {'source': 'declining', 'drift_score': -0.8, 'status': 'HIGH_DECLINE', 'vector_count': 50},
            {'source': 'moderate', 'drift_score': 0.4, 'status': 'MODERATE_DRIFT', 'vector_count': 75},
            {'source': 'stable1', 'drift_score': 0.1, 'status': 'STABLE', 'vector_count': 200},
            {'source': 'stable2', 'drift_score': -0.05, 'status': 'STABLE', 'vector_count': 150}
        ]
        mock_cursor.fetchall.return_value = mock_results

        response = client.get(
            '/api/vectors/drift?lookback_days=14',
            headers=admin_headers
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        summary = data['data']['summary']
        assert summary['total_sources'] == 5
        assert summary['high_drift_count'] == 2
        assert summary['moderate_drift_count'] == 1
        assert summary['stable_count'] == 2

    def test_drift_boundary_lookback_days(self, client, mock_db_connection, admin_headers):
        """Drift detection with boundary lookback values"""
        mock_conn, mock_cursor = mock_db_connection
        mock_cursor.fetchall.return_value = []

        response = client.get(
            '/api/vectors/drift?lookback_days=1',
            headers=admin_headers
        )
        assert response.status_code == 200

        response = client.get(
            '/api/vectors/drift?lookback_days=90',
            headers=admin_headers
        )
        assert response.status_code == 200


class TestStatisticsEdgeCases:
    """Test statistics edge cases"""

    def test_statistics_with_partial_dates(self, client, mock_db_connection, admin_headers):
        """Statistics handles partial date fields"""
        mock_conn, mock_cursor = mock_db_connection

        mock_results = [
            {
                'source': 'partial',
                'vector_count': 100,
                'avg_query_count': 10.5,
                'oldest_vector': datetime(2024, 1, 1),
                'newest_vector': None
            }
        ]
        mock_cursor.fetchall.return_value = mock_results

        response = client.get(
            '/api/vectors/statistics',
            headers=admin_headers
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        stats = data['data']['statistics'][0]
        assert stats['oldest_vector'] is not None
        assert stats['newest_vector'] is None


class TestClustersEdgeCases:
    """Test clusters edge cases"""

    def test_clusters_with_large_sample_size(self, client, mock_db_connection, admin_headers):
        """Clusters with large sample size"""
        mock_conn, mock_cursor = mock_db_connection

        mock_results = [
            {'cluster_id': i, 'size': 100 - i * 10, 'centroid': [0.1 * i], 'avg_similarity': 0.9 - i * 0.1}
            for i in range(5)
        ]
        mock_cursor.fetchall.return_value = mock_results

        response = client.get(
            '/api/vectors/clusters?sample_size=5000&min_cluster_size=20',
            headers=admin_headers
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['data']['sample_size'] == 5000
        assert data['data']['min_cluster_size'] == 20


class TestConnectionPoolEdgeCases:
    """Test connection pool edge cases"""

    def test_release_connection_with_pool_error(self):
        """Connection release handles pool errors gracefully"""
        from src.routes.vectors import release_db_connection

        mock_pool = MagicMock()
        mock_pool.putconn.side_effect = Exception('Pool exhausted')
        mock_conn = MagicMock()

        with patch('src.routes.vectors._get_db_pool', return_value=mock_pool):
            release_db_connection(mock_conn)
            mock_conn.close.assert_called_once()

    def test_release_connection_with_close_error(self):
        """Connection release handles close errors gracefully"""
        from src.routes.vectors import release_db_connection

        mock_pool = MagicMock()
        mock_pool.putconn.side_effect = Exception('Pool error')
        mock_conn = MagicMock()
        mock_conn.close.side_effect = Exception('Close error')

        with patch('src.routes.vectors._get_db_pool', return_value=mock_pool):
            release_db_connection(mock_conn)


class TestRefreshEdgeCases:
    """Test refresh edge cases"""

    def test_refresh_with_user_token(self, client, mock_db_connection, user_headers):
        """Refresh works with user token (not admin-only)"""
        mock_conn, mock_cursor = mock_db_connection

        response = client.post(
            '/api/vectors/refresh',
            headers=user_headers
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['data']['status'] == 'success'


class TestDatabaseErrors:
    """Test database error handling"""

    def test_visualize_connection_error(self, client, admin_headers):
        """Visualization handles connection errors"""
        with patch('src.routes.vectors.get_db_connection', side_effect=Exception('Connection refused')):
            response = client.get(
                '/api/vectors/visualize',
                headers=admin_headers
            )

        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data

    def test_clusters_connection_error(self, client, admin_headers):
        """Clusters handles connection errors"""
        with patch('src.routes.vectors.get_db_connection', side_effect=Exception('Connection timeout')):
            response = client.get(
                '/api/vectors/clusters',
                headers=admin_headers
            )

        assert response.status_code == 500

    def test_drift_connection_error(self, client, admin_headers):
        """Drift handles connection errors"""
        with patch('src.routes.vectors.get_db_connection', side_effect=Exception('Network error')):
            response = client.get(
                '/api/vectors/drift',
                headers=admin_headers
            )

        assert response.status_code == 500

    def test_statistics_connection_error(self, client, admin_headers):
        """Statistics handles connection errors"""
        with patch('src.routes.vectors.get_db_connection', side_effect=Exception('Database unavailable')):
            response = client.get(
                '/api/vectors/statistics',
                headers=admin_headers
            )

        assert response.status_code == 500

    def test_refresh_connection_error(self, client, admin_headers):
        """Refresh handles connection errors"""
        with patch('src.routes.vectors.get_db_connection', side_effect=Exception('Pool exhausted')):
            response = client.post(
                '/api/vectors/refresh',
                headers=admin_headers
            )

        assert response.status_code == 500
