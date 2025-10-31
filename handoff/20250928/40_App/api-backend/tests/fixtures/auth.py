"""
Authentication fixtures for testing.

Provides both mock and real JWT token fixtures for unit and integration tests.
"""

import os
import pytest
from unittest.mock import patch


@pytest.fixture(autouse=True)
def test_jwt_secret():
    """
    Ensure test environment uses a dedicated JWT secret.
    
    This fixture automatically runs for all tests to prevent
    accidental use of production secrets in tests.
    """
    original_secret = os.environ.get('JWT_SECRET')
    os.environ['JWT_SECRET'] = 'test-secret-do-not-use-in-production'
    yield
    
    if original_secret:
        os.environ['JWT_SECRET'] = original_secret
    elif 'JWT_SECRET' in os.environ:
        del os.environ['JWT_SECRET']


@pytest.fixture
def mock_jwt_required():
    """
    Mock JWT authentication for unit tests.
    
    Usage:
        def test_endpoint(client, mock_jwt_required):
            response = client.get('/protected-endpoint')
            assert response.status_code == 200
    """
    with patch('src.middleware.auth_middleware.jwt_required', lambda f: f):
        yield


@pytest.fixture
def mock_admin_jwt():
    """
    Mock admin JWT authentication for unit tests.
    
    Usage:
        def test_admin_endpoint(client, mock_admin_jwt):
            response = client.get('/admin-endpoint')
            assert response.status_code == 200
    """
    with patch('src.middleware.auth_middleware.jwt_required', lambda f: f), \
         patch('src.middleware.auth_middleware.get_jwt_identity', return_value='admin'):
        yield


@pytest.fixture
def auth_headers():
    """
    Real JWT token for integration tests.
    
    Usage:
        def test_protected_route(client, auth_headers):
            response = client.get('/api/vectors', headers=auth_headers)
            assert response.status_code == 200
    """
    from src.middleware.auth_middleware import create_admin_token
    token = create_admin_token()
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture
def user_auth_headers():
    """
    Real JWT token for regular user (integration tests).
    
    Usage:
        def test_user_route(client, user_auth_headers):
            response = client.get('/api/user/profile', headers=user_auth_headers)
            assert response.status_code == 200
    """
    from src.middleware.auth_middleware import create_user_token
    # create_user_token() has no parameters - it creates a default test user token
    token = create_user_token()
    return {'Authorization': f'Bearer {token}'}
