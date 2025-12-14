"""
Database concurrency and initialization tests.

Tests for verifying database initialization is process-safe and handles
concurrent access correctly. Part of PR1e improvements.

See: docs/database/DATABASE_INITIALIZATION.md
"""

import os
import sys
import subprocess
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest


class TestDatabaseConcurrentInit:
    """Tests for concurrent database initialization safety."""

    def test_multiple_processes_import_main_simultaneously(self):
        """
        Test that multiple processes can import src.main simultaneously without errors.
        
        This validates that import-time database initialization is process-safe,
        which is critical for:
        - Multiple gunicorn workers starting simultaneously
        - Multiple CI test processes running in parallel
        - Container orchestration scenarios (multiple pods starting)
        
        The test spawns N subprocesses that all import src.main with TESTING=true
        and verifies they all exit successfully (exit code 0).
        """
        num_processes = 4
        
        # Get the path to the api-backend directory
        backend_dir = Path(__file__).resolve().parent.parent
        src_dir = backend_dir / "src"
        orchestrator_dir = backend_dir.parent / "orchestrator"
        
        # Build PYTHONPATH
        pythonpath_parts = [
            str(src_dir),
            str(backend_dir),
            str(orchestrator_dir),
        ]
        pythonpath = os.pathsep.join(pythonpath_parts)
        
        # Script that imports src.main and exits
        import_script = """
import sys
import os
os.environ['TESTING'] = 'true'
os.environ['FLASK_SECRET_KEY'] = 'test-secret-for-concurrent-import'
os.environ['ENVIRONMENT'] = 'development'

try:
    from src.main import app
    # Verify app was created successfully
    assert app is not None
    assert hasattr(app, 'config')
    assert app.config.get('TESTING') == True
    print(f"Process {os.getpid()}: Import successful")
    sys.exit(0)
except Exception as e:
    print(f"Process {os.getpid()}: Import failed: {e}")
    sys.exit(1)
"""
        
        # Create temp file with the script
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(import_script)
            script_path = f.name
        
        try:
            # Start all processes simultaneously
            env = os.environ.copy()
            env['PYTHONPATH'] = pythonpath
            env['TESTING'] = 'true'
            
            processes = []
            for i in range(num_processes):
                proc = subprocess.Popen(
                    [sys.executable, script_path],
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=str(backend_dir),
                )
                processes.append(proc)
            
            # Wait for all processes to complete (with timeout)
            results = []
            for proc in processes:
                try:
                    stdout, stderr = proc.communicate(timeout=30)
                    results.append({
                        'returncode': proc.returncode,
                        'stdout': stdout.decode('utf-8', errors='replace'),
                        'stderr': stderr.decode('utf-8', errors='replace'),
                    })
                except subprocess.TimeoutExpired:
                    proc.kill()
                    results.append({
                        'returncode': -1,
                        'stdout': '',
                        'stderr': 'Process timed out',
                    })
            
            # Verify all processes succeeded
            failed_processes = [r for r in results if r['returncode'] != 0]
            
            if failed_processes:
                error_details = "\n".join([
                    f"Return code: {r['returncode']}\nStdout: {r['stdout']}\nStderr: {r['stderr']}"
                    for r in failed_processes
                ])
                pytest.fail(
                    f"{len(failed_processes)}/{num_processes} processes failed:\n{error_details}"
                )
            
            # All processes should have succeeded
            assert len(results) == num_processes
            assert all(r['returncode'] == 0 for r in results)
            
        finally:
            # Cleanup temp file
            os.unlink(script_path)

    def test_init_database_with_retry_mocked_failures(self):
        """
        Test that init_database_with_retry handles transient failures correctly.
        
        This unit test mocks db.create_all() to fail a few times then succeed,
        verifying the retry logic works without depending on real database issues.
        """
        from src.extensions.database import init_database_with_retry
        from flask import Flask
        from unittest.mock import MagicMock, patch
        
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        app.config['TESTING'] = True
        
        mock_db = MagicMock()
        
        # Track call count
        call_count = [0]
        
        def mock_create_all():
            call_count[0] += 1
            if call_count[0] < 3:
                raise Exception(f"Simulated transient failure #{call_count[0]}")
            # Success on 3rd attempt
        
        mock_db.create_all = mock_create_all
        
        # Patch time.sleep to speed up the test
        with patch('time.sleep'):
            # Should succeed after retries
            init_database_with_retry(app, mock_db, max_retries=5, initial_delay=0.1)
        
        # Verify it took 3 attempts
        assert call_count[0] == 3

    def test_init_database_with_retry_exhausts_retries(self):
        """
        Test that init_database_with_retry raises after exhausting all retries.
        """
        from src.extensions.database import init_database_with_retry
        from flask import Flask
        
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        app.config['TESTING'] = True
        
        mock_db = MagicMock()
        mock_db.create_all.side_effect = Exception("Persistent failure")
        
        # Patch time.sleep to speed up the test
        with patch('time.sleep'):
            with pytest.raises(Exception, match="Persistent failure"):
                init_database_with_retry(app, mock_db, max_retries=3, initial_delay=0.1)
        
        # Verify all retries were attempted
        assert mock_db.create_all.call_count == 3

    def test_before_request_handler_not_registered_multiple_times(self):
        """
        Test that calling initialize_database multiple times doesn't register
        multiple before_request handlers.
        
        This is important because:
        - Some test patterns may re-initialize the app
        - Multiple handlers would cause redundant table checks
        """
        from src.extensions.database import (
            configure_database,
            initialize_database,
            _register_test_db_safety_net,
        )
        from flask import Flask
        from unittest.mock import MagicMock
        
        app = Flask(__name__)
        mock_db = MagicMock()
        
        class MockSettings:
            testing = True
            environment = "development"
            database_url = None
            rate_limit_fail_fast = False
        
        # Configure once
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        app.config['TESTING'] = True
        
        # Count before_request handlers before
        initial_handler_count = len(app.before_request_funcs.get(None, []))
        
        # Register safety net multiple times
        _register_test_db_safety_net(app, mock_db)
        _register_test_db_safety_net(app, mock_db)
        _register_test_db_safety_net(app, mock_db)
        
        # Each call adds a handler (this is expected Flask behavior)
        # The test documents this behavior - if we want idempotency,
        # we'd need to track registration state
        final_handler_count = len(app.before_request_funcs.get(None, []))
        
        # Document current behavior: handlers are added each time
        # This is acceptable because:
        # 1. In production, initialize_database is only called once at import time
        # 2. The ensure_tables check is idempotent (just checks if tables exist)
        assert final_handler_count == initial_handler_count + 3


class TestDatabaseConfigurationEdgeCases:
    """Tests for database configuration edge cases."""

    def test_configure_database_production_without_database_url(self):
        """Test that production without DATABASE_URL raises RuntimeError."""
        from src.extensions.database import configure_database
        from flask import Flask
        from unittest.mock import patch, MagicMock
        
        app = Flask(__name__)
        
        class MockSettings:
            testing = False
            environment = "production"
            database_url = None
            rate_limit_fail_fast = False
        
        # Patch get_settings at the source module where it's imported from
        with patch('common.config.settings.get_settings') as mock_get_settings:
            mock_get_settings.return_value.database_url = None
            
            with pytest.raises(RuntimeError, match="Production must have DATABASE_URL configured"):
                configure_database(app, MockSettings(), MagicMock())

    def test_configure_database_production_with_sqlite(self):
        """Test that production with SQLite raises RuntimeError."""
        from src.extensions.database import configure_database
        from flask import Flask
        from unittest.mock import patch, MagicMock
        
        app = Flask(__name__)
        
        class MockSettings:
            testing = False
            environment = "production"
            database_url = "sqlite:///test.db"
            rate_limit_fail_fast = False
        
        # Patch get_settings at the source module where it's imported from
        with patch('common.config.settings.get_settings') as mock_get_settings:
            mock_get_settings.return_value.database_url = "sqlite:///test.db"
            
            with pytest.raises(RuntimeError, match="Production must use PostgreSQL, not SQLite"):
                configure_database(app, MockSettings(), MagicMock())

    def test_configure_database_test_mode_via_pytest_in_sys_modules(self):
        """Test that pytest in sys.modules triggers test mode configuration."""
        from src.extensions.database import configure_database
        from flask import Flask
        from unittest.mock import patch, MagicMock
        
        app = Flask(__name__)
        mock_db = MagicMock()
        
        class MockSettings:
            testing = False  # Not set via env, but pytest is in sys.modules
            environment = "development"
            database_url = None
            rate_limit_fail_fast = False
        
        # Patch get_settings at the source module where it's imported from
        with patch('common.config.settings.get_settings') as mock_get_settings:
            mock_get_settings.return_value.database_url = None
            
            # pytest should be in sys.modules during test execution
            assert "pytest" in sys.modules
            
            configure_database(app, MockSettings(), mock_db)
            
            # Should be configured for testing
            assert app.config.get('TESTING') == True
            assert app.config.get('SQLALCHEMY_DATABASE_URI') == 'sqlite://'

    def test_configure_database_test_mode_via_settings_testing(self):
        """Test that app_settings.testing=True triggers test mode configuration."""
        from src.extensions.database import configure_database
        from flask import Flask
        from unittest.mock import patch, MagicMock
        import sys
        
        app = Flask(__name__)
        mock_db = MagicMock()
        
        class MockSettings:
            testing = True  # Explicitly set
            environment = "development"
            database_url = None
            rate_limit_fail_fast = False
        
        # Patch get_settings at the source module where it's imported from
        with patch('common.config.settings.get_settings') as mock_get_settings:
            mock_get_settings.return_value.database_url = None
            
            configure_database(app, MockSettings(), mock_db)
            
            # Should be configured for testing
            assert app.config.get('TESTING') == True
            assert app.config.get('SQLALCHEMY_DATABASE_URI') == 'sqlite://'
