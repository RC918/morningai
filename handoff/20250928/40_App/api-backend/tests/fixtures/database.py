"""
Database fixtures for testing.

Provides database setup and teardown for integration tests.
"""

import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_db_session():
    """
    Mock database session for unit tests.
    
    Usage:
        def test_db_operation(mock_db_session):
            result = perform_db_query(mock_db_session)
            assert result is not None
    """
    session = MagicMock()
    session.query.return_value.filter.return_value.first.return_value = None
    return session


@pytest.fixture
def mock_supabase_client():
    """
    Mock Supabase client for unit tests.
    
    Usage:
        def test_supabase_query(mock_supabase_client):
            result = fetch_data(mock_supabase_client)
            assert result is not None
    """
    client = MagicMock()
    client.table.return_value.select.return_value.execute.return_value.data = []
    return client


@pytest.fixture(scope='function')
def db_transaction():
    """
    Database transaction fixture for integration tests.
    
    Automatically rolls back changes after each test to ensure isolation.
    
    Usage:
        def test_create_user(db_transaction):
            user = create_user(name='Test User')
            assert user.id is not None
            # Changes will be rolled back after test
    """
    # Phase 2 TODO: Implement real database transaction management
    raise NotImplementedError(
        "db_transaction fixture is not yet implemented. "
        "This will be completed in RFC #619 Phase 2. "
        "For now, use mock_db_session for unit tests."
    )
