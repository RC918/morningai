"""
Unit tests for scripts/apply_phase3_migrations.py

Tests migration execution with mocked database connections.
"""

import pytest
from pathlib import Path
import sys
import os
from unittest.mock import Mock, MagicMock, patch, mock_open
import importlib.util

pytestmark = pytest.mark.unit
os.environ['IDEMPOTENCY_TESTS_ALLOWED'] = 'true'

mock_psycopg2 = MagicMock()
mock_conn = MagicMock()
mock_cursor = MagicMock()
mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
mock_psycopg2.connect.return_value = mock_conn
sys.modules['psycopg2'] = mock_psycopg2

mock_repo_root = Mock()
mock_repo_root.get_repo_root.return_value = Path('/tmp/test_repo')
sys.modules['repo_root_utils'] = mock_repo_root

sys.modules['common'] = MagicMock()
sys.modules['common.config'] = MagicMock()
sys.modules['common.config.settings'] = MagicMock()
mock_settings = MagicMock()
mock_settings.database_url = 'postgresql://test:test@localhost/testdb'
sys.modules['common.config.settings'].settings = mock_settings

script_path = Path(__file__).parent.parent / 'scripts' / 'apply_phase3_migrations.py'
spec = importlib.util.spec_from_file_location("migrations_mod", script_path)
migrations_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(migrations_mod)


class TestReadSqlFile:
    """Test SQL file reading."""
    
    def test_read_sql_file(self, tmp_path):
        """Test reading SQL file content."""
        sql_file = tmp_path / 'test.sql'
        sql_content = 'SELECT * FROM users;'
        sql_file.write_text(sql_content)
        
        result = migrations_mod.read_sql_file(sql_file)
        
        assert result == sql_content
    
    def test_read_sql_file_with_utf8(self, tmp_path):
        """Test reading SQL file with UTF-8 content."""
        sql_file = tmp_path / 'test.sql'
        sql_content = '-- 中文註解\nSELECT * FROM users;'
        sql_file.write_text(sql_content, encoding='utf-8')
        
        result = migrations_mod.read_sql_file(sql_file)
        
        assert '中文註解' in result
        assert 'SELECT * FROM users;' in result
    
    def test_read_sql_file_multiline(self, tmp_path):
        """Test reading multiline SQL file."""
        sql_file = tmp_path / 'test.sql'
        sql_content = '''CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100)
);'''
        sql_file.write_text(sql_content)
        
        result = migrations_mod.read_sql_file(sql_file)
        
        assert 'CREATE TABLE users' in result
        assert 'id SERIAL PRIMARY KEY' in result


class TestExecuteSqlFile:
    """Test SQL file execution."""
    
    def test_execute_sql_file_success(self, tmp_path):
        """Test successful SQL file execution."""
        sql_file = tmp_path / 'test.sql'
        sql_file.write_text('SELECT 1;')
        
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.statusmessage = 'SELECT 1'
        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
        mock_conn.notices = []
        
        result = migrations_mod.execute_sql_file(mock_conn, sql_file, 'Test migration')
        
        assert result is True
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
        mock_conn.rollback.assert_not_called()
    
    def test_execute_sql_file_failure(self, tmp_path):
        """Test SQL file execution failure."""
        sql_file = tmp_path / 'test.sql'
        sql_file.write_text('INVALID SQL;')
        
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = Exception('SQL syntax error')
        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
        
        result = migrations_mod.execute_sql_file(mock_conn, sql_file, 'Test migration')
        
        assert result is False
        mock_conn.rollback.assert_called_once()
        mock_conn.commit.assert_not_called()
    
    def test_execute_sql_file_with_notices(self, tmp_path):
        """Test SQL file execution with database notices."""
        sql_file = tmp_path / 'test.sql'
        sql_file.write_text('CREATE TABLE test (id INT);')
        
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.statusmessage = 'CREATE TABLE'
        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
        mock_conn.notices = ['NOTICE: table created']
        
        result = migrations_mod.execute_sql_file(mock_conn, sql_file, 'Create table')
        
        assert result is True
        mock_conn.commit.assert_called_once()
    
    def test_execute_sql_file_rollback_on_error(self, tmp_path):
        """Test that rollback is called on error."""
        sql_file = tmp_path / 'test.sql'
        sql_file.write_text('DROP TABLE nonexistent;')
        
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = Exception('Table does not exist')
        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
        
        result = migrations_mod.execute_sql_file(mock_conn, sql_file, 'Drop table')
        
        assert result is False
        mock_conn.rollback.assert_called_once()
