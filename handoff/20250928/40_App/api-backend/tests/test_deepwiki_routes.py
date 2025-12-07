"""
Tests for DeepWiki API routes (Knowledge Base Query Endpoints)
Issue #2158: API endpoints for querying DeepWiki session insights
"""
import pytest
import os
import sys
import json
from unittest.mock import patch, MagicMock
from dataclasses import dataclass
from enum import Enum


class MockQueryType(Enum):
    """Mock QueryType for testing when DeepWiki is not available."""
    CODE_QUESTION = "code_question"
    ERROR_LOOKUP = "error_lookup"
    PATTERN_SEARCH = "pattern_search"
    SESSION_INSIGHT = "session_insight"
    IMPROVEMENT_SUGGESTION = "improvement_suggestion"


@dataclass
class MockQueryResult:
    """Mock QueryResult for testing."""
    query_id: str
    query_type: MockQueryType
    question: str
    answer: str
    sources: list
    confidence: float
    latency_ms: float
    metadata: dict


@dataclass
class MockSessionInsight:
    """Mock SessionInsight for testing."""
    session_id: str
    insight_type: str
    summary: str
    recommendations: list
    metrics: dict


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
def mock_deepwiki_service():
    """Create mock DeepWiki service"""
    mock = MagicMock()
    return mock


class TestDeepWikiHealthEndpoint:
    """Tests for GET /api/deepwiki/health endpoint"""

    def test_health_check_deepwiki_unavailable(self, client):
        """Test GET /api/deepwiki/health when DeepWiki is unavailable"""
        with patch('src.routes.deepwiki.DEEPWIKI_AVAILABLE', False):
            response = client.get('/api/deepwiki/health')

            assert response.status_code == 200
            data = response.get_json()
            assert data['deepwiki_available'] is False
            assert data['status'] == 'unavailable'
            assert 'timestamp' in data

    def test_health_check_deepwiki_available(self, client, mock_deepwiki_service):
        """Test GET /api/deepwiki/health when DeepWiki is available"""
        mock_deepwiki_service.health_check.return_value = {
            'status': 'healthy',
            'components': {
                'knowledge_graph': {'enabled': True, 'available': True},
                'error_pairs': {'enabled': True, 'available': True},
            }
        }

        with patch('src.routes.deepwiki.DEEPWIKI_AVAILABLE', True):
            with patch('src.routes.deepwiki.get_deepwiki_service', return_value=mock_deepwiki_service):
                response = client.get('/api/deepwiki/health')

                assert response.status_code == 200
                data = response.get_json()
                assert data['deepwiki_available'] is True
                assert data['status'] == 'healthy'
                assert 'components' in data
                assert 'timestamp' in data


class TestDeepWikiQueryEndpoint:
    """Tests for POST /api/deepwiki/query endpoint"""

    def test_query_no_auth(self, client):
        """Test POST /api/deepwiki/query without authentication returns 401"""
        response = client.post('/api/deepwiki/query', json={'question': 'test'})

        assert response.status_code == 401
        data = response.get_json()
        assert 'error' in data

    def test_query_deepwiki_unavailable(self, client, auth_headers_admin):
        """Test POST /api/deepwiki/query returns 503 when DeepWiki is unavailable"""
        with patch('src.routes.deepwiki.DEEPWIKI_AVAILABLE', False):
            response = client.post(
                '/api/deepwiki/query',
                headers=auth_headers_admin,
                json={'question': 'test'}
            )

            assert response.status_code == 503
            data = response.get_json()
            assert 'error' in data
            assert data['deepwiki_available'] is False

    def test_query_missing_question(self, client, auth_headers_admin):
        """Test POST /api/deepwiki/query returns 400 when question is missing"""
        with patch('src.routes.deepwiki.DEEPWIKI_AVAILABLE', True):
            response = client.post(
                '/api/deepwiki/query',
                headers=auth_headers_admin,
                json={}
            )

            assert response.status_code == 400
            data = response.get_json()
            assert 'error' in data

    def test_query_empty_question(self, client, auth_headers_admin):
        """Test POST /api/deepwiki/query returns 400 when question is empty"""
        with patch('src.routes.deepwiki.DEEPWIKI_AVAILABLE', True):
            response = client.post(
                '/api/deepwiki/query',
                headers=auth_headers_admin,
                json={'question': '   '}
            )

            assert response.status_code == 400
            data = response.get_json()
            assert 'error' in data

    def test_query_invalid_query_type(self, client, auth_headers_admin):
        """Test POST /api/deepwiki/query returns 400 for invalid query_type"""
        with patch('src.routes.deepwiki.DEEPWIKI_AVAILABLE', True):
            with patch('src.routes.deepwiki.QueryType', MockQueryType):
                response = client.post(
                    '/api/deepwiki/query',
                    headers=auth_headers_admin,
                    json={'question': 'test', 'query_type': 'invalid_type'}
                )

                assert response.status_code == 400
                data = response.get_json()
                assert 'error' in data
                assert 'Invalid query_type' in data['error']

    def test_query_success(self, client, auth_headers_admin, mock_deepwiki_service):
        """Test POST /api/deepwiki/query returns query results"""
        mock_result = MockQueryResult(
            query_id='dw-test-123',
            query_type=MockQueryType.CODE_QUESTION,
            question='How to fix this error?',
            answer='Here is the solution...',
            sources=[{'type': 'error_fix_pair', 'id': 1}],
            confidence=0.85,
            latency_ms=150.5,
            metadata={'language': 'python'}
        )
        mock_deepwiki_service.query.return_value = mock_result

        with patch('src.routes.deepwiki.DEEPWIKI_AVAILABLE', True):
            with patch('src.routes.deepwiki.get_deepwiki_service', return_value=mock_deepwiki_service):
                with patch('src.routes.deepwiki.QueryType', MockQueryType):
                    response = client.post(
                        '/api/deepwiki/query',
                        headers=auth_headers_admin,
                        json={
                            'question': 'How to fix this error?',
                            'query_type': 'code_question',
                            'language': 'python',
                            'limit': 5
                        }
                    )

                    assert response.status_code == 200
                    data = response.get_json()
                    assert data['query_id'] == 'dw-test-123'
                    assert data['answer'] == 'Here is the solution...'
                    assert data['confidence'] == 0.85
                    assert 'timestamp' in data


class TestDeepWikiInsightsEndpoint:
    """Tests for GET /api/deepwiki/insights/:session_id endpoint"""

    def test_insights_no_auth(self, client):
        """Test GET /api/deepwiki/insights/:id without authentication returns 401"""
        response = client.get('/api/deepwiki/insights/test-session-123')

        assert response.status_code == 401
        data = response.get_json()
        assert 'error' in data

    def test_insights_deepwiki_unavailable(self, client, auth_headers_admin):
        """Test GET /api/deepwiki/insights/:id returns 503 when DeepWiki is unavailable"""
        with patch('src.routes.deepwiki.DEEPWIKI_AVAILABLE', False):
            response = client.get(
                '/api/deepwiki/insights/test-session-123',
                headers=auth_headers_admin
            )

            assert response.status_code == 503
            data = response.get_json()
            assert 'error' in data

    def test_insights_from_cache(self, client, auth_headers_admin, mock_deepwiki_service):
        """Test GET /api/deepwiki/insights/:id returns cached insights from Redis"""
        cached_session = {
            'session_id': 'test-session-123',
            'metadata': {
                'deepwiki_insights': {
                    'session_id': 'test-session-123',
                    'insight_type': 'execution_analysis',
                    'summary': 'Execution completed successfully',
                    'recommendations': ['Consider adding more tests'],
                    'metrics': {'tasks_completed': 5, 'tasks_failed': 0}
                }
            }
        }

        mock_redis = MagicMock()
        mock_redis.get.return_value = json.dumps(cached_session)

        with patch('src.routes.deepwiki.DEEPWIKI_AVAILABLE', True):
            with patch('src.routes.deepwiki.get_redis_client', return_value=mock_redis):
                response = client.get(
                    '/api/deepwiki/insights/test-session-123',
                    headers=auth_headers_admin
                )

                assert response.status_code == 200
                data = response.get_json()
                assert data['session_id'] == 'test-session-123'
                assert data['insight_type'] == 'execution_analysis'
                assert data['source'] == 'cached'
                assert 'recommendations' in data
                assert 'metrics' in data

    def test_insights_generated(self, client, auth_headers_admin, mock_deepwiki_service):
        """Test GET /api/deepwiki/insights/:id generates new insights when not cached"""
        mock_insight = MockSessionInsight(
            session_id='test-session-123',
            insight_type='execution_analysis',
            summary='Session analysis complete',
            recommendations=['No specific recommendations'],
            metrics={}
        )
        mock_deepwiki_service.get_session_insights.return_value = mock_insight

        with patch('src.routes.deepwiki.DEEPWIKI_AVAILABLE', True):
            with patch('src.routes.deepwiki.get_deepwiki_service', return_value=mock_deepwiki_service):
                # Mock Redis to return None (no cached insights)
                with patch('src.routes.deepwiki.get_redis_client') as mock_redis_getter:
                    mock_redis = MagicMock()
                    mock_redis.get.return_value = None
                    mock_redis_getter.return_value = mock_redis

                    response = client.get(
                        '/api/deepwiki/insights/test-session-123',
                        headers=auth_headers_admin
                    )

                    assert response.status_code == 200
                    data = response.get_json()
                    assert data['session_id'] == 'test-session-123'
                    assert data['source'] == 'generated'


class TestDeepWikiErrorLookupEndpoint:
    """Tests for POST /api/deepwiki/error-lookup endpoint"""

    def test_error_lookup_no_auth(self, client):
        """Test POST /api/deepwiki/error-lookup without authentication returns 401"""
        response = client.post('/api/deepwiki/error-lookup', json={'error_text': 'test'})

        assert response.status_code == 401
        data = response.get_json()
        assert 'error' in data

    def test_error_lookup_missing_error_text(self, client, auth_headers_admin):
        """Test POST /api/deepwiki/error-lookup returns 400 when error_text is missing"""
        with patch('src.routes.deepwiki.DEEPWIKI_AVAILABLE', True):
            response = client.post(
                '/api/deepwiki/error-lookup',
                headers=auth_headers_admin,
                json={}
            )

            assert response.status_code == 400
            data = response.get_json()
            assert 'error' in data

    def test_error_lookup_success(self, client, auth_headers_admin, mock_deepwiki_service):
        """Test POST /api/deepwiki/error-lookup returns matching errors"""
        mock_result = MockQueryResult(
            query_id='dw-error-123',
            query_type=MockQueryType.ERROR_LOOKUP,
            question='TypeError: cannot read property',
            answer='Similar errors found...',
            sources=[
                {'type': 'error_fix_pair', 'error_text': 'TypeError', 'fix_text': 'Check null'}
            ],
            confidence=0.9,
            latency_ms=100.0,
            metadata={}
        )
        mock_deepwiki_service.query.return_value = mock_result

        with patch('src.routes.deepwiki.DEEPWIKI_AVAILABLE', True):
            with patch('src.routes.deepwiki.get_deepwiki_service', return_value=mock_deepwiki_service):
                with patch('src.routes.deepwiki.QueryType', MockQueryType):
                    response = client.post(
                        '/api/deepwiki/error-lookup',
                        headers=auth_headers_admin,
                        json={'error_text': 'TypeError: cannot read property', 'limit': 3}
                    )

                    assert response.status_code == 200
                    data = response.get_json()
                    assert data['query_id'] == 'dw-error-123'
                    assert 'matches' in data
                    assert data['confidence'] == 0.9


class TestDeepWikiPatternsEndpoint:
    """Tests for POST /api/deepwiki/patterns endpoint"""

    def test_patterns_no_auth(self, client):
        """Test POST /api/deepwiki/patterns without authentication returns 401"""
        response = client.post('/api/deepwiki/patterns', json={'query': 'test'})

        assert response.status_code == 401
        data = response.get_json()
        assert 'error' in data

    def test_patterns_missing_query(self, client, auth_headers_admin):
        """Test POST /api/deepwiki/patterns returns 400 when query is missing"""
        with patch('src.routes.deepwiki.DEEPWIKI_AVAILABLE', True):
            response = client.post(
                '/api/deepwiki/patterns',
                headers=auth_headers_admin,
                json={}
            )

            assert response.status_code == 400
            data = response.get_json()
            assert 'error' in data

    def test_patterns_success(self, client, auth_headers_admin, mock_deepwiki_service):
        """Test POST /api/deepwiki/patterns returns matching patterns"""
        mock_result = MockQueryResult(
            query_id='dw-pattern-123',
            query_type=MockQueryType.PATTERN_SEARCH,
            question='error handling pattern',
            answer='Found patterns...',
            sources=[
                {'type': 'knowledge_graph_pattern', 'pattern_name': 'try-catch'}
            ],
            confidence=0.75,
            latency_ms=80.0,
            metadata={'language': 'python'}
        )
        mock_deepwiki_service.query.return_value = mock_result

        with patch('src.routes.deepwiki.DEEPWIKI_AVAILABLE', True):
            with patch('src.routes.deepwiki.get_deepwiki_service', return_value=mock_deepwiki_service):
                with patch('src.routes.deepwiki.QueryType', MockQueryType):
                    response = client.post(
                        '/api/deepwiki/patterns',
                        headers=auth_headers_admin,
                        json={'query': 'error handling pattern', 'language': 'python'}
                    )

                    assert response.status_code == 200
                    data = response.get_json()
                    assert data['query_id'] == 'dw-pattern-123'
                    assert 'patterns' in data
                    assert data['confidence'] == 0.75


class TestDeepWikiSuggestionsEndpoint:
    """Tests for POST /api/deepwiki/suggestions endpoint"""

    def test_suggestions_no_auth(self, client):
        """Test POST /api/deepwiki/suggestions without authentication returns 401"""
        response = client.post('/api/deepwiki/suggestions', json={'context': 'test'})

        assert response.status_code == 401
        data = response.get_json()
        assert 'error' in data

    def test_suggestions_missing_context(self, client, auth_headers_admin):
        """Test POST /api/deepwiki/suggestions returns 400 when context is missing"""
        with patch('src.routes.deepwiki.DEEPWIKI_AVAILABLE', True):
            response = client.post(
                '/api/deepwiki/suggestions',
                headers=auth_headers_admin,
                json={}
            )

            assert response.status_code == 400
            data = response.get_json()
            assert 'error' in data

    def test_suggestions_success(self, client, auth_headers_admin, mock_deepwiki_service):
        """Test POST /api/deepwiki/suggestions returns improvement suggestions"""
        mock_result = MockQueryResult(
            query_id='dw-suggest-123',
            query_type=MockQueryType.IMPROVEMENT_SUGGESTION,
            question='def process_data(): pass',
            answer='## Improvement Suggestions\n- Add error handling\n- Add logging',
            sources=[],
            confidence=0.7,
            latency_ms=200.0,
            metadata={}
        )
        mock_deepwiki_service.query.return_value = mock_result

        with patch('src.routes.deepwiki.DEEPWIKI_AVAILABLE', True):
            with patch('src.routes.deepwiki.get_deepwiki_service', return_value=mock_deepwiki_service):
                with patch('src.routes.deepwiki.QueryType', MockQueryType):
                    response = client.post(
                        '/api/deepwiki/suggestions',
                        headers=auth_headers_admin,
                        json={'context': 'def process_data(): pass', 'language': 'python'}
                    )

                    assert response.status_code == 200
                    data = response.get_json()
                    assert data['query_id'] == 'dw-suggest-123'
                    assert 'suggestions' in data
                    assert 'Improvement Suggestions' in data['suggestions']


class TestDeepWikiUnavailable:
    """Tests for DeepWiki unavailable scenarios"""

    def test_query_deepwiki_unavailable(self, client, auth_headers_admin):
        """Test POST /api/deepwiki/query returns 503 when DeepWiki is unavailable"""
        with patch('src.routes.deepwiki.DEEPWIKI_AVAILABLE', False):
            response = client.post(
                '/api/deepwiki/query',
                headers=auth_headers_admin,
                json={'question': 'test'}
            )

            assert response.status_code == 503
            data = response.get_json()
            assert data['deepwiki_available'] is False

    def test_error_lookup_deepwiki_unavailable(self, client, auth_headers_admin):
        """Test POST /api/deepwiki/error-lookup returns 503 when DeepWiki is unavailable"""
        with patch('src.routes.deepwiki.DEEPWIKI_AVAILABLE', False):
            response = client.post(
                '/api/deepwiki/error-lookup',
                headers=auth_headers_admin,
                json={'error_text': 'test'}
            )

            assert response.status_code == 503
            data = response.get_json()
            assert data['deepwiki_available'] is False

    def test_patterns_deepwiki_unavailable(self, client, auth_headers_admin):
        """Test POST /api/deepwiki/patterns returns 503 when DeepWiki is unavailable"""
        with patch('src.routes.deepwiki.DEEPWIKI_AVAILABLE', False):
            response = client.post(
                '/api/deepwiki/patterns',
                headers=auth_headers_admin,
                json={'query': 'test'}
            )

            assert response.status_code == 503
            data = response.get_json()
            assert data['deepwiki_available'] is False

    def test_suggestions_deepwiki_unavailable(self, client, auth_headers_admin):
        """Test POST /api/deepwiki/suggestions returns 503 when DeepWiki is unavailable"""
        with patch('src.routes.deepwiki.DEEPWIKI_AVAILABLE', False):
            response = client.post(
                '/api/deepwiki/suggestions',
                headers=auth_headers_admin,
                json={'context': 'test'}
            )

            assert response.status_code == 503
            data = response.get_json()
            assert data['deepwiki_available'] is False


class TestRequireDeepWikiAvailableDecorator:
    """Tests for require_deepwiki_available decorator"""

    def test_decorator_allows_when_deepwiki_available(self, client, auth_headers_admin, mock_deepwiki_service):
        """Test decorator allows request when DeepWiki is available"""
        mock_result = MockQueryResult(
            query_id='dw-test',
            query_type=MockQueryType.CODE_QUESTION,
            question='test',
            answer='answer',
            sources=[],
            confidence=0.5,
            latency_ms=50.0,
            metadata={}
        )
        mock_deepwiki_service.query.return_value = mock_result

        with patch('src.routes.deepwiki.DEEPWIKI_AVAILABLE', True):
            with patch('src.routes.deepwiki.get_deepwiki_service', return_value=mock_deepwiki_service):
                with patch('src.routes.deepwiki.QueryType', MockQueryType):
                    response = client.post(
                        '/api/deepwiki/query',
                        headers=auth_headers_admin,
                        json={'question': 'test'}
                    )

                    assert response.status_code == 200

    def test_decorator_blocks_when_deepwiki_unavailable(self, client, auth_headers_admin):
        """Test decorator blocks request when DeepWiki is unavailable"""
        with patch('src.routes.deepwiki.DEEPWIKI_AVAILABLE', False):
            response = client.post(
                '/api/deepwiki/query',
                headers=auth_headers_admin,
                json={'question': 'test'}
            )

            assert response.status_code == 503
            data = response.get_json()
            assert 'error' in data
            assert data['deepwiki_available'] is False
