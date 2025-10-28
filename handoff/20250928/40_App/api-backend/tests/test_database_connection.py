"""
Unit tests for database connection logic in main.py

Tests cover:
- validate_database_url helper function
- Database configuration parameters
"""

import os
import sys
import pytest


class TestDatabaseValidation:
    """Test database URL validation logic"""
    
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
        
        is_valid, msg = validate_database_url('postgresql://')
        assert is_valid is False
        assert 'hostname' in msg.lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
