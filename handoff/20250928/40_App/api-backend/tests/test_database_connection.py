"""
Unit tests for database connection logic in main.py

Tests cover:
- Development environment fallback to SQLite
- Production environment fail-fast on missing/invalid DATABASE_URL
- PostgreSQL connection with valid DATABASE_URL
- Logging behavior
- Connection pool configuration
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock
import logging


class TestDatabaseConnection:
    """Test database connection configuration logic"""
    
    @patch.dict(os.environ, {
        'ENVIRONMENT': 'development',
        'DATABASE_URL': ''
    }, clear=True)
    def test_dev_fallback_to_sqlite_when_no_database_url(self, caplog):
        """Development environment should fallback to SQLite when DATABASE_URL is not set"""
        with caplog.at_level(logging.INFO):
            from src.main import app
            
            assert 'sqlite:///' in app.config['SQLALCHEMY_DATABASE_URI']
            
            assert any('Using SQLite for development' in record.message for record in caplog.records)
    
    @patch.dict(os.environ, {
        'ENVIRONMENT': 'development',
        'DATABASE_URL': 'postgresql://user:pass@localhost:5432/testdb'
    }, clear=True)
    def test_dev_uses_postgresql_when_valid_database_url(self, caplog):
        """Development environment should use PostgreSQL when valid DATABASE_URL is provided"""
        with caplog.at_level(logging.INFO):
            from src.main import app
            
            assert app.config['SQLALCHEMY_DATABASE_URI'] == 'postgresql://user:pass@localhost:5432/testdb'
            
            assert 'pool_size' in app.config['SQLALCHEMY_ENGINE_OPTIONS']
            assert app.config['SQLALCHEMY_ENGINE_OPTIONS']['pool_size'] == 10
            
            assert any('Using PostgreSQL' in record.message for record in caplog.records)
    
    @patch.dict(os.environ, {
        'ENVIRONMENT': 'development',
        'DATABASE_URL': 'invalid://bad-url'
    }, clear=True)
    def test_dev_fallback_to_sqlite_on_invalid_database_url(self, caplog):
        """Development environment should fallback to SQLite when DATABASE_URL is invalid"""
        with caplog.at_level(logging.WARNING):
            from src.main import app
            
            assert 'sqlite:///' in app.config['SQLALCHEMY_DATABASE_URI']
            
            assert any('Invalid DATABASE_URL' in record.message for record in caplog.records)
            assert any('falling back to SQLite' in record.message for record in caplog.records)
    
    @patch.dict(os.environ, {
        'ENVIRONMENT': 'production',
        'DATABASE_URL': ''
    }, clear=True)
    def test_production_fails_fast_when_no_database_url(self, caplog):
        """Production environment should exit immediately when DATABASE_URL is not set"""
        with caplog.at_level(logging.CRITICAL):
            with pytest.raises(SystemExit) as exc_info:
                from src.main import app
            
            assert exc_info.value.code == 1
            
            assert any('Production environment requires DATABASE_URL' in record.message for record in caplog.records)
    
    @patch.dict(os.environ, {
        'ENVIRONMENT': 'production',
        'DATABASE_URL': 'invalid://bad-url'
    }, clear=True)
    def test_production_fails_fast_on_invalid_database_url(self, caplog):
        """Production environment should exit immediately when DATABASE_URL is invalid"""
        with caplog.at_level(logging.CRITICAL):
            with pytest.raises(SystemExit) as exc_info:
                from src.main import app
            
            assert exc_info.value.code == 1
            
            assert any('FATAL' in record.message for record in caplog.records)
    
    @patch.dict(os.environ, {
        'ENVIRONMENT': 'production',
        'DATABASE_URL': 'sqlite:///database/app.db'
    }, clear=True)
    def test_production_fails_fast_on_sqlite_database_url(self, caplog):
        """Production environment should not allow SQLite"""
        with caplog.at_level(logging.CRITICAL):
            with pytest.raises(SystemExit) as exc_info:
                from src.main import app
            
            assert exc_info.value.code == 1
            
            assert any('Production environment cannot use SQLite' in record.message for record in caplog.records)
    
    @patch.dict(os.environ, {
        'ENVIRONMENT': 'production',
        'DATABASE_URL': 'postgresql://user:pass@prod-db.example.com:5432/proddb',
        'DB_POOL_SIZE': '20',
        'DB_POOL_MAX_OVERFLOW': '15',
        'DB_POOL_RECYCLE': '7200',
        'DB_POOL_PRE_PING': 'true'
    }, clear=True)
    def test_production_uses_custom_pool_parameters(self, caplog):
        """Production environment should use custom connection pool parameters from env vars"""
        with caplog.at_level(logging.INFO):
            from src.main import app
            
            assert app.config['SQLALCHEMY_DATABASE_URI'] == 'postgresql://user:pass@prod-db.example.com:5432/proddb'
            
            pool_options = app.config['SQLALCHEMY_ENGINE_OPTIONS']
            assert pool_options['pool_size'] == 20
            assert pool_options['max_overflow'] == 15
            assert pool_options['pool_recycle'] == 7200
            assert pool_options['pool_pre_ping'] is True
            
            assert any('pool_size=20' in record.message for record in caplog.records)
            assert any('max_overflow=15' in record.message for record in caplog.records)
    
    @patch.dict(os.environ, {
        'ENVIRONMENT': 'staging',
        'DATABASE_URL': 'postgresql://user:pass@staging-db.example.com:5432/stagingdb'
    }, clear=True)
    def test_staging_uses_postgresql(self, caplog):
        """Staging environment should use PostgreSQL like production"""
        with caplog.at_level(logging.INFO):
            from src.main import app
            
            assert app.config['SQLALCHEMY_DATABASE_URI'] == 'postgresql://user:pass@staging-db.example.com:5432/stagingdb'
            
            assert 'pool_size' in app.config['SQLALCHEMY_ENGINE_OPTIONS']
            
            assert any('Using PostgreSQL' in record.message for record in caplog.records)
    
    def test_validate_database_url_function(self):
        """Test the validate_database_url helper function"""
        from src.main import validate_database_url
        
        is_valid, msg = validate_database_url('postgresql://user:pass@host:5432/db')
        assert is_valid is True
        
        is_valid, msg = validate_database_url('postgres://user:pass@host:5432/db')
        assert is_valid is True
        
        is_valid, msg = validate_database_url('sqlite:///path/to/db.db')
        assert is_valid is True
        
        is_valid, msg = validate_database_url('')
        assert is_valid is False
        assert 'empty' in msg.lower()
        
        is_valid, msg = validate_database_url('invalid://bad-url')
        assert is_valid is False
        assert 'scheme' in msg.lower()
        
        is_valid, msg = validate_database_url('postgresql://no-host')
        assert is_valid is False
        assert 'hostname' in msg.lower()
    
    @patch.dict(os.environ, {
        'ENVIRONMENT': 'production',
        'DATABASE_URL': 'postgresql://user:pass@prod-db.example.com:5432/proddb'
    }, clear=True)
    def test_logging_hides_credentials(self, caplog):
        """Verify that database credentials are not logged in plain text"""
        with caplog.at_level(logging.INFO):
            from src.main import app
            
            for record in caplog.records:
                assert 'pass' not in record.message or 'pass@' not in record.message
                
            assert any('prod-db.example.com' in record.message for record in caplog.records)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
