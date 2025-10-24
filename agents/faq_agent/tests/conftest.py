#!/usr/bin/env python3
"""
Pytest configuration and fixtures for FAQ Agent tests
"""
import pytest
import os
import sys
import jwt
from datetime import datetime, timedelta

api_backend_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'handoff', '20250928', '40_App', 'api-backend')
sys.path.insert(0, os.path.join(api_backend_path, 'src'))
sys.path.insert(0, api_backend_path)

from flask import Flask
from api_backend import create_app


@pytest.fixture(scope='session')
def app():
    """Create Flask app for testing"""
    os.environ['TESTING'] = 'true'
    os.environ['JWT_SECRET_KEY'] = 'test-secret-key-for-ci'
    os.environ['REDIS_URL'] = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    app = create_app()
    app.config['TESTING'] = True
    
    yield app


@pytest.fixture(scope='session')
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture(scope='session')
def jwt_secret():
    """JWT secret key for testing"""
    return os.getenv('JWT_SECRET_KEY', 'test-secret-key-for-ci')


@pytest.fixture
def valid_jwt_token(jwt_secret):
    """Generate a valid JWT token for testing"""
    payload = {
        'user_id': 'test-user-123',
        'email': 'test@example.com',
        'role': 'user',
        'exp': datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, jwt_secret, algorithm='HS256')


@pytest.fixture
def admin_jwt_token(jwt_secret):
    """Generate an admin JWT token for testing"""
    payload = {
        'user_id': 'admin-user-123',
        'email': 'admin@example.com',
        'role': 'admin',
        'exp': datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, jwt_secret, algorithm='HS256')


@pytest.fixture
def expired_jwt_token(jwt_secret):
    """Generate an expired JWT token for testing"""
    payload = {
        'user_id': 'test-user-123',
        'email': 'test@example.com',
        'role': 'user',
        'exp': datetime.utcnow() - timedelta(hours=1)
    }
    return jwt.encode(payload, jwt_secret, algorithm='HS256')
