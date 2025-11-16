"""
Unit tests for scripts/apply_phase3_migrations.py main() function

Tests the main entry point and full migration workflow.
"""

import pytest
from pathlib import Path
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import importlib.util

pytestmark = pytest.mark.unit
os.environ['IDEMPOTENCY_TESTS_ALLOWED'] = 'true'

mock_psycopg2 = MagicMock()
sys.modules['psycopg2'] = mock_psycopg2

mock_repo_root = Mock()
test_root = Path('/tmp/test_migrations')
mock_repo_root.get_repo_root.return_value = test_root
sys.modules['repo_root_utils'] = mock_repo_root

mock_settings_module = MagicMock()
mock_settings = MagicMock()
mock_settings.database_url = 'postgresql://localhost/test'
mock_settings_module.settings = mock_settings
sys.modules['common'] = MagicMock()
sys.modules['common.config'] = MagicMock()
sys.modules['common.config.settings'] = mock_settings_module

script_path = Path(__file__).parent.parent / 'scripts' / 'apply_phase3_migrations.py'
spec = importlib.util.spec_from_file_location("apply_migrations_main_mod", script_path)
apply_migrations_main_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(apply_migrations_main_mod)


class TestMainFunction:
    """Test main() function."""
    
    def test_main_no_database_url(self, capsys):
        """Test main when DATABASE_URL is not set."""
        mock_settings.database_url = None
        
        with pytest.raises(SystemExit) as exc_info:
            apply_migrations_main_mod.main()
        
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert '❌ Error: DATABASE_URL must be set' in captured.out
        
        mock_settings.database_url = 'postgresql://localhost/test'
    
    def test_main_connection_failure(self, capsys):
        """Test main when database connection fails."""
        mock_settings.database_url = 'postgresql://localhost/test'
        mock_psycopg2.connect.side_effect = Exception('Connection failed')
        
        with pytest.raises(SystemExit) as exc_info:
            apply_migrations_main_mod.main()
        
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert '❌ Failed to connect to database' in captured.out
        
        mock_psycopg2.connect.side_effect = None
    
    def test_main_successful_migrations(self, tmp_path, capsys, monkeypatch):
        """Test main with successful migrations."""
        mock_settings.database_url = 'postgresql://localhost/test'
        
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.statusmessage = 'CREATE TABLE'
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.notices = []
        mock_psycopg2.connect.return_value = mock_conn
        
        migrations_dir = tmp_path / 'migrations'
        migrations_dir.mkdir(parents=True)
        
        (migrations_dir / '005_create_user_profiles_table.sql').write_text('CREATE TABLE user_profiles (id INT);')
        (migrations_dir / '006_update_rls_policies_true_tenant_isolation.sql').write_text('ALTER TABLE users ENABLE ROW LEVEL SECURITY;')
        (migrations_dir / 'backfill_user_profiles.sql').write_text('INSERT INTO user_profiles SELECT * FROM users;')
        
        monkeypatch.setattr('os.path.dirname', lambda x: str(tmp_path))
        monkeypatch.setattr('os.path.abspath', lambda x: str(tmp_path / 'scripts' / 'apply_phase3_migrations.py'))
        
        apply_migrations_main_mod.main()
        
        captured = capsys.readouterr()
        assert 'Connecting to database...' in captured.out
        assert '✅ Connected successfully' in captured.out
        assert 'Migration Summary' in captured.out
        assert '✅ Success: 3' in captured.out
        assert '❌ Failed:  0' in captured.out
        assert '🎉 All migrations completed successfully!' in captured.out
    
    def test_main_with_missing_migration_files(self, tmp_path, capsys, monkeypatch):
        """Test main when some migration files are missing."""
        mock_settings.database_url = 'postgresql://localhost/test'
        
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.statusmessage = 'CREATE TABLE'
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.notices = []
        mock_psycopg2.connect.return_value = mock_conn
        
        migrations_dir = tmp_path / 'migrations'
        migrations_dir.mkdir(parents=True)
        
        (migrations_dir / '005_create_user_profiles_table.sql').write_text('CREATE TABLE user_profiles (id INT);')
        
        monkeypatch.setattr('os.path.dirname', lambda x: str(tmp_path))
        monkeypatch.setattr('os.path.abspath', lambda x: str(tmp_path / 'scripts' / 'apply_phase3_migrations.py'))
        
        apply_migrations_main_mod.main()
        
        captured = capsys.readouterr()
        assert '⚠️  Skipping' in captured.out
        assert 'file not found' in captured.out
        assert '✅ Success: 1' in captured.out
    
    def test_main_with_failed_migration(self, tmp_path, capsys, monkeypatch):
        """Test main when a migration fails."""
        mock_settings.database_url = 'postgresql://localhost/test'
        
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = [
            None,
            Exception('SQL error'),
            None
        ]
        mock_cursor.statusmessage = 'CREATE TABLE'
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.notices = []
        mock_psycopg2.connect.return_value = mock_conn
        
        migrations_dir = tmp_path / 'migrations'
        migrations_dir.mkdir(parents=True)
        
        (migrations_dir / '005_create_user_profiles_table.sql').write_text('CREATE TABLE user_profiles (id INT);')
        (migrations_dir / '006_update_rls_policies_true_tenant_isolation.sql').write_text('INVALID SQL;')
        (migrations_dir / 'backfill_user_profiles.sql').write_text('INSERT INTO user_profiles SELECT * FROM users;')
        
        monkeypatch.setattr('os.path.dirname', lambda x: str(tmp_path))
        monkeypatch.setattr('os.path.abspath', lambda x: str(tmp_path / 'scripts' / 'apply_phase3_migrations.py'))
        
        with pytest.raises(SystemExit) as exc_info:
            apply_migrations_main_mod.main()
        
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert '❌ Failed:  1' in captured.out
        assert '⚠️  Some migrations failed' in captured.out
    
    def test_main_prints_migration_progress(self, tmp_path, capsys, monkeypatch):
        """Test that main prints migration progress."""
        mock_settings.database_url = 'postgresql://localhost/test'
        
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.statusmessage = 'CREATE TABLE'
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.notices = []
        mock_psycopg2.connect.return_value = mock_conn
        
        migrations_dir = tmp_path / 'migrations'
        migrations_dir.mkdir(parents=True)
        
        (migrations_dir / '005_create_user_profiles_table.sql').write_text('CREATE TABLE user_profiles (id INT);')
        
        monkeypatch.setattr('os.path.dirname', lambda x: str(tmp_path))
        monkeypatch.setattr('os.path.abspath', lambda x: str(tmp_path / 'scripts' / 'apply_phase3_migrations.py'))
        
        apply_migrations_main_mod.main()
        
        captured = capsys.readouterr()
        assert 'Executing: Migration 005: Create user_profiles table' in captured.out
        assert 'File:' in captured.out
        assert '005_create_user_profiles_table.sql' in captured.out
        assert '✅ Migration 005: Create user_profiles table - SUCCESS' in captured.out
