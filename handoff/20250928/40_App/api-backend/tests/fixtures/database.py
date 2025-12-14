"""
Database fixtures for testing.

Provides database setup and teardown for integration tests.

Part of PR1e improvements - adds session-scoped cleanup fixtures
to ensure test database isolation and proper teardown.

See: docs/database/DATABASE_INITIALIZATION.md
"""

import os
import shutil
from pathlib import Path
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


@pytest.fixture(scope='session', autouse=True)
def database_cleanup_safety_net():
    """
    Session-scoped fixture to ensure test database cleanup.
    
    This fixture:
    1. Records whether the src/database/ directory existed before tests
    2. After all tests complete, disposes SQLAlchemy engine/session if created
    3. Only removes the database directory if it was created during tests
    
    This prevents:
    - Accidental deletion of developer's local database
    - Cross-test database state leakage
    - Orphaned database files from failed tests
    
    Part of PR1e improvements for test environment safety.
    """
    # Get the database directory path
    backend_dir = Path(__file__).resolve().parent.parent.parent
    db_dir = backend_dir / "src" / "database"
    
    # Record pre-test state
    db_dir_existed_before = db_dir.exists()
    db_dir_contents_before = set()
    if db_dir_existed_before:
        try:
            db_dir_contents_before = set(os.listdir(db_dir))
        except OSError:
            pass
    
    yield  # Run all tests
    
    # Cleanup after all tests complete
    try:
        # Try to dispose SQLAlchemy engine to release connections
        try:
            from src.models.user import db
            if hasattr(db, 'engine') and db.engine is not None:
                db.engine.dispose()
        except (ImportError, AttributeError, RuntimeError):
            # db module not available or engine not initialized
            pass
        
        # Only cleanup database directory if it was created during tests
        if db_dir.exists():
            if not db_dir_existed_before:
                # Directory was created during tests - safe to remove entirely
                try:
                    shutil.rmtree(db_dir)
                except OSError:
                    pass
            else:
                # Directory existed before - only remove files created during tests
                try:
                    current_contents = set(os.listdir(db_dir))
                    new_files = current_contents - db_dir_contents_before
                    for filename in new_files:
                        filepath = db_dir / filename
                        try:
                            if filepath.is_file():
                                filepath.unlink()
                            elif filepath.is_dir():
                                shutil.rmtree(filepath)
                        except OSError:
                            pass
                except OSError:
                    pass
    except Exception:
        # Don't let cleanup failures break the test session
        pass


@pytest.fixture
def clean_test_database():
    """
    Function-scoped fixture for tests that need a guaranteed clean database.
    
    Usage:
        def test_with_clean_db(clean_test_database):
            # Database tables are freshly created
            # Any data from previous tests is cleared
            pass
    
    This fixture:
    1. Drops all tables before the test
    2. Creates fresh tables
    3. Yields control to the test
    4. Drops all tables after the test
    """
    try:
        from src.models.user import db
        from flask import current_app
        
        # Check if we're in an app context
        if current_app:
            # Drop and recreate all tables
            db.drop_all()
            db.create_all()
            
            yield db
            
            # Cleanup after test
            db.session.remove()
            db.drop_all()
        else:
            # No app context - just yield None
            yield None
    except (ImportError, RuntimeError):
        # Not in Flask context or db not available
        yield None
