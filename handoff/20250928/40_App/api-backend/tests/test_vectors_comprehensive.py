"""
Comprehensive tests for Vector routes

Tests all vector endpoints including:
- Vector visualization (t-SNE, PCA)
- Cluster analysis
- Drift detection
- Statistics
- Refresh operations
"""
import pytest
import json
import os
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from src.main import app
from src.middleware.auth_middleware import create_admin_token


@pytest.fixture
def client():
    """Flask test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def auth_headers():
    """Generate admin JWT token for authentication"""
    token = create_admin_token()
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


class TestVectorVisualization:
    """Test vector visualization endpoint"""
    
    def test_visualize_tsne_2d(self, client, mock_db_connection, auth_headers):
        """Test t-SNE 2D visualization"""
        mock_conn, mock_cursor = mock_db_connection
        
        mock_results = [
            {
                'id': f'vec-{i}',
                'embedding': [float(j) for j in range(128)],
                'source': 'test',
                'category': 'general',
                'text_preview': f'Test text {i}',
                'query_count': i * 10,
                'created_at': datetime.now()
            }
            for i in range(50)
        ]
        mock_cursor.fetchall.return_value = mock_results
        
        mock_tsne = MagicMock()
        mock_tsne.fit_transform.return_value = np.random.rand(50, 2)
        
        with patch('src.routes.vectors.TSNE', return_value=mock_tsne):
            response = client.get(
                '/api/vectors/visualize?method=tsne&limit=50&dimensions=2',
                headers=auth_headers
            )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'data' in data
        assert data['data']['method'] == 'tsne'
        assert data['data']['dimensions'] == 2
        assert data['data']['vector_count'] == 50
        assert 'figure' in data['data']
    
    def test_visualize_pca_3d(self, client, mock_db_connection, auth_headers):
        """Test PCA 3D visualization"""
        mock_conn, mock_cursor = mock_db_connection
        
        mock_results = [
            {
                'id': f'vec-{i}',
                'embedding': [float(j) for j in range(128)],
                'source': 'docs',
                'category': 'tech',
                'text_preview': f'Doc {i}',
                'query_count': i,
                'created_at': datetime.now()
            }
            for i in range(30)
        ]
        mock_cursor.fetchall.return_value = mock_results
        
        mock_pca = MagicMock()
        mock_pca.fit_transform.return_value = np.random.rand(30, 3)
        
        with patch('src.routes.vectors.PCA', return_value=mock_pca):
            response = client.get(
                '/api/vectors/visualize?method=pca&limit=30&dimensions=3',
                headers=auth_headers
            )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['data']['method'] == 'pca'
        assert data['data']['dimensions'] == 3
    
    def test_visualize_with_source_filter(self, client, mock_db_connection, auth_headers):
        """Test visualization with source filter"""
        mock_conn, mock_cursor = mock_db_connection
        
        mock_results = [
            {
                'id': f'vec-{i}',
                'embedding': [float(j) for j in range(128)],
                'source': 'filtered_source',
                'category': 'test',
                'text_preview': f'Text {i}',
                'query_count': 1,
                'created_at': datetime.now()
            }
            for i in range(20)
        ]
        mock_cursor.fetchall.return_value = mock_results
        
        mock_tsne = MagicMock()
        mock_tsne.fit_transform.return_value = np.random.rand(20, 2)
        
        with patch('src.routes.vectors.TSNE', return_value=mock_tsne):
            response = client.get(
                '/api/vectors/visualize?source=filtered_source&limit=20',
                headers=auth_headers
            )
        
        assert response.status_code == 200
        mock_cursor.execute.assert_called_once()
        sql_query = mock_cursor.execute.call_args[0][0]
        assert 'WHERE source = %s' in sql_query
    
    def test_visualize_limit_exceeded(self, client, auth_headers):
        """Test visualization with limit exceeding maximum"""
        response = client.get(
            '/api/vectors/visualize?limit=10000',
            headers=auth_headers
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'Limit cannot exceed 5000' in data['error']
    
    def test_visualize_invalid_dimensions(self, client, auth_headers):
        """Test visualization with invalid dimensions"""
        response = client.get(
            '/api/vectors/visualize?dimensions=4',
            headers=auth_headers
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'Dimensions must be 2 or 3' in data['error']
    
    def test_visualize_invalid_method(self, client, mock_db_connection, auth_headers):
        """Test visualization with invalid method"""
        mock_conn, mock_cursor = mock_db_connection
        
        mock_results = [
            {
                'id': f'vec-{i}',
                'embedding': [float(j) for j in range(128)],
                'source': 'test',
                'category': 'test',
                'text_preview': 'test',
                'query_count': 1,
                'created_at': datetime.now()
            }
            for i in range(10)
        ]
        mock_cursor.fetchall.return_value = mock_results
        
        response = client.get(
            '/api/vectors/visualize?method=invalid',
            headers=auth_headers
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "Method must be 'tsne' or 'pca'" in data['error']
    
    def test_visualize_no_vectors(self, client, mock_db_connection, auth_headers):
        """Test visualization with no vectors found"""
        mock_conn, mock_cursor = mock_db_connection
        mock_cursor.fetchall.return_value = []
        
        response = client.get(
            '/api/vectors/visualize?limit=100',
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_visualize_insufficient_vectors(self, client, mock_db_connection, auth_headers):
        """Test visualization with insufficient vectors"""
        mock_conn, mock_cursor = mock_db_connection
        
        mock_results = [
            {
                'id': 'vec-1',
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
            headers=auth_headers
        )
        
        assert response.status_code == 400


class TestVectorClusters:
    """Test vector clusters endpoint"""
    
    def test_get_clusters_success(self, client, mock_db_connection, auth_headers):
        """Test successful cluster retrieval"""
        mock_conn, mock_cursor = mock_db_connection
        
        mock_results = [
            {'cluster_id': 1, 'size': 50, 'centroid': [0.1, 0.2], 'avg_similarity': 0.85},
            {'cluster_id': 2, 'size': 30, 'centroid': [0.3, 0.4], 'avg_similarity': 0.78},
            {'cluster_id': 3, 'size': 20, 'centroid': [0.5, 0.6], 'avg_similarity': 0.92}
        ]
        mock_cursor.fetchall.return_value = mock_results
        
        response = client.get(
            '/api/vectors/clusters?sample_size=1000&min_cluster_size=5',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['data']['cluster_count'] == 3
        assert data['data']['sample_size'] == 1000
        assert data['data']['min_cluster_size'] == 5
        assert len(data['data']['clusters']) == 3
    
    def test_get_clusters_default_params(self, client, mock_db_connection, auth_headers):
        """Test clusters with default parameters"""
        mock_conn, mock_cursor = mock_db_connection
        mock_cursor.fetchall.return_value = []
        
        response = client.get(
            '/api/vectors/clusters',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args[0]
        assert call_args[1] == (1000, 5)  # Default sample_size=1000, min_cluster_size=5
    
    def test_get_clusters_custom_params(self, client, mock_db_connection, auth_headers):
        """Test clusters with custom parameters"""
        mock_conn, mock_cursor = mock_db_connection
        mock_cursor.fetchall.return_value = []
        
        response = client.get(
            '/api/vectors/clusters?sample_size=500&min_cluster_size=10',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        call_args = mock_cursor.execute.call_args[0]
        assert call_args[1] == (500, 10)


class TestVectorDrift:
    """Test vector drift detection endpoint"""
    
    def test_detect_drift_success(self, client, mock_db_connection, auth_headers):
        """Test successful drift detection"""
        mock_conn, mock_cursor = mock_db_connection
        
        mock_results = [
            {'source': 'docs', 'drift_score': 0.85, 'status': 'HIGH_GROWTH', 'vector_count': 150},
            {'source': 'code', 'drift_score': 0.45, 'status': 'MODERATE_DRIFT', 'vector_count': 80},
            {'source': 'logs', 'drift_score': 0.15, 'status': 'STABLE', 'vector_count': 200}
        ]
        mock_cursor.fetchall.return_value = mock_results
        
        response = client.get(
            '/api/vectors/drift?lookback_days=7',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['data']['summary']['total_sources'] == 3
        assert data['data']['summary']['high_drift_count'] == 1
        assert data['data']['summary']['moderate_drift_count'] == 1
        assert data['data']['summary']['stable_count'] == 1
        assert data['data']['lookback_days'] == 7
    
    def test_detect_drift_default_lookback(self, client, mock_db_connection, auth_headers):
        """Test drift detection with default lookback period"""
        mock_conn, mock_cursor = mock_db_connection
        mock_cursor.fetchall.return_value = []
        
        response = client.get(
            '/api/vectors/drift',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        call_args = mock_cursor.execute.call_args[0]
        assert call_args[1] == (7,)
    
    def test_detect_drift_invalid_lookback_too_small(self, client, auth_headers):
        """Test drift detection with lookback days too small"""
        response = client.get(
            '/api/vectors/drift?lookback_days=0',
            headers=auth_headers
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'lookback_days must be between 1 and 90' in data['error']
    
    def test_detect_drift_invalid_lookback_too_large(self, client, auth_headers):
        """Test drift detection with lookback days too large"""
        response = client.get(
            '/api/vectors/drift?lookback_days=100',
            headers=auth_headers
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'lookback_days must be between 1 and 90' in data['error']
    
    def test_detect_drift_high_decline(self, client, mock_db_connection, auth_headers):
        """Test drift detection with high decline status"""
        mock_conn, mock_cursor = mock_db_connection
        
        mock_results = [
            {'source': 'deprecated', 'drift_score': -0.9, 'status': 'HIGH_DECLINE', 'vector_count': 10}
        ]
        mock_cursor.fetchall.return_value = mock_results
        
        response = client.get(
            '/api/vectors/drift?lookback_days=30',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['data']['summary']['high_drift_count'] == 1


class TestVectorStatistics:
    """Test vector statistics endpoint"""
    
    def test_get_statistics_success(self, client, mock_db_connection, auth_headers):
        """Test successful statistics retrieval"""
        mock_conn, mock_cursor = mock_db_connection
        
        mock_results = [
            {
                'source': 'docs',
                'vector_count': 500,
                'avg_query_count': 25.5,
                'oldest_vector': datetime(2024, 1, 1),
                'newest_vector': datetime(2024, 10, 23)
            },
            {
                'source': 'code',
                'vector_count': 300,
                'avg_query_count': 15.2,
                'oldest_vector': datetime(2024, 2, 1),
                'newest_vector': datetime(2024, 10, 20)
            }
        ]
        mock_cursor.fetchall.return_value = mock_results
        
        response = client.get(
            '/api/vectors/statistics',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['data']['total_sources'] == 2
        assert len(data['data']['statistics']) == 2
        assert '2024-01-01' in data['data']['statistics'][0]['oldest_vector']
    
    def test_get_statistics_empty(self, client, mock_db_connection, auth_headers):
        """Test statistics with no data"""
        mock_conn, mock_cursor = mock_db_connection
        mock_cursor.fetchall.return_value = []
        
        response = client.get(
            '/api/vectors/statistics',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['data']['total_sources'] == 0
        assert data['data']['statistics'] == []
    
    def test_get_statistics_null_dates(self, client, mock_db_connection, auth_headers):
        """Test statistics with null date fields"""
        mock_conn, mock_cursor = mock_db_connection
        
        mock_results = [
            {
                'source': 'new_source',
                'vector_count': 10,
                'avg_query_count': 0,
                'oldest_vector': None,
                'newest_vector': None
            }
        ]
        mock_cursor.fetchall.return_value = mock_results
        
        response = client.get(
            '/api/vectors/statistics',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['data']['statistics'][0]['oldest_vector'] is None
        assert data['data']['statistics'][0]['newest_vector'] is None


class TestVectorRefresh:
    """Test vector visualization refresh endpoint"""
    
    def test_refresh_success(self, client, mock_db_connection, auth_headers):
        """Test successful refresh"""
        mock_conn, mock_cursor = mock_db_connection
        
        response = client.post(
            '/api/vectors/refresh',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['data']['status'] == 'success'
        assert 'refreshed' in data['data']['message']
        
        mock_cursor.execute.assert_called_once_with("SELECT refresh_vector_viz()")
        mock_conn.commit.assert_called_once()
    
    def test_refresh_database_error(self, client, auth_headers):
        """Test refresh with database error"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.execute.side_effect = Exception('Database error')
        
        with patch('src.routes.vectors.get_db_connection', return_value=mock_conn), \
             patch('src.routes.vectors.release_db_connection'):
            response = client.post(
                '/api/vectors/refresh',
                headers=auth_headers
            )
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data


class TestDatabaseConnectionPool:
    """Test database connection pool management"""
    
    def test_db_pool_initialization(self):
        """Test database pool is initialized correctly"""
        with patch.dict(os.environ, {'DATABASE_URL': 'postgresql://test'}), \
             patch('src.routes.vectors.ThreadedConnectionPool') as mock_pool:
            from src.routes.vectors import _get_db_pool
            
            import src.routes.vectors as vectors_module
            vectors_module._DB_POOL = None
            
            pool = _get_db_pool()
            
            mock_pool.assert_called_once()
            call_kwargs = mock_pool.call_args.kwargs
            assert call_kwargs['minconn'] == 1
            assert call_kwargs['dsn'] == 'postgresql://test'
    
    def test_db_pool_missing_url(self):
        """Test error when DATABASE_URL is missing"""
        with patch.dict(os.environ, {}, clear=True):
            import src.routes.vectors as vectors_module
            vectors_module._DB_POOL = None
            
            with pytest.raises(ValueError, match="DATABASE_URL"):
                from src.routes.vectors import _get_db_pool
                _get_db_pool()
    
    def test_connection_release(self):
        """Test connection is properly released"""
        mock_pool = MagicMock()
        mock_conn = MagicMock()
        
        with patch('src.routes.vectors._get_db_pool', return_value=mock_pool):
            from src.routes.vectors import release_db_connection
            release_db_connection(mock_conn)
            
            mock_pool.putconn.assert_called_once_with(mock_conn)
    
    def test_connection_release_error_fallback(self):
        """Test connection close fallback on release error"""
        mock_pool = MagicMock()
        mock_pool.putconn.side_effect = Exception('Pool error')
        mock_conn = MagicMock()
        
        with patch('src.routes.vectors._get_db_pool', return_value=mock_pool):
            from src.routes.vectors import release_db_connection
            release_db_connection(mock_conn)
            
            mock_conn.close.assert_called_once()


class TestErrorHandling:
    """Test error handling across all endpoints"""
    
    def test_visualize_database_error(self, client, auth_headers):
        """Test visualization with database error"""
        mock_conn = MagicMock()
        mock_conn.cursor.side_effect = Exception('Database connection failed')
        
        with patch('src.routes.vectors.get_db_connection', return_value=mock_conn):
            response = client.get(
                '/api/vectors/visualize?limit=10',
                headers=auth_headers
            )
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_clusters_database_error(self, client, auth_headers):
        """Test clusters with database error"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.execute.side_effect = Exception('Query failed')
        
        with patch('src.routes.vectors.get_db_connection', return_value=mock_conn), \
             patch('src.routes.vectors.release_db_connection'):
            response = client.get(
                '/api/vectors/clusters',
                headers=auth_headers
            )
        
        assert response.status_code == 500
    
    def test_drift_database_error(self, client, auth_headers):
        """Test drift detection with database error"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.execute.side_effect = Exception('RPC function not found')
        
        with patch('src.routes.vectors.get_db_connection', return_value=mock_conn), \
             patch('src.routes.vectors.release_db_connection'):
            response = client.get(
                '/api/vectors/drift',
                headers=auth_headers
            )
        
        assert response.status_code == 500
    
    def test_statistics_database_error(self, client, auth_headers):
        """Test statistics with database error"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.execute.side_effect = Exception('View not found')
        
        with patch('src.routes.vectors.get_db_connection', return_value=mock_conn), \
             patch('src.routes.vectors.release_db_connection'):
            response = client.get(
                '/api/vectors/statistics',
                headers=auth_headers
            )
        
        assert response.status_code == 500
