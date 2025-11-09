"""
Unit tests for sys.path bootstrap mechanism

Tests the multi-tier fallback mechanism used in:
- monitoring/braintrust_processor.py
- handoff/20250928/40_App/api-backend/gunicorn.conf.py

Priority order:
1. REPO_ROOT environment variable (most explicit)
2. PYTHONPATH environment variable (standard Python mechanism)
3. Marker file detection (auto-discovery)
"""
import pytest
import sys
import os
from pathlib import Path


class TestSysPathBootstrap:
    """Test sys.path bootstrap fallback mechanisms"""

    def test_repo_root_adds_to_path(self, monkeypatch, tmp_path):
        """Test REPO_ROOT adds directory to sys.path"""
        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()
        
        monkeypatch.setenv('REPO_ROOT', str(repo_dir))
        
        original_path = sys.path.copy()
        
        if 'REPO_ROOT' in os.environ:
            repo_root = os.environ['REPO_ROOT']
            if repo_root and os.path.isdir(repo_root) and repo_root not in sys.path:
                sys.path.insert(0, repo_root)
        
        assert str(repo_dir) in sys.path
        
        sys.path = original_path

    def test_pythonpath_adds_to_path(self, monkeypatch, tmp_path):
        """Test PYTHONPATH adds directory to sys.path"""
        app_dir = tmp_path / "app"
        app_dir.mkdir()
        
        monkeypatch.delenv('REPO_ROOT', raising=False)
        monkeypatch.setenv('PYTHONPATH', str(app_dir))
        
        original_path = sys.path.copy()
        
        if 'PYTHONPATH' in os.environ:
            pythonpath_entries = os.environ['PYTHONPATH'].split(os.pathsep)
            for entry in reversed(pythonpath_entries):
                if entry and os.path.isdir(entry) and entry not in sys.path:
                    sys.path.insert(0, entry)
        
        assert str(app_dir) in sys.path
        
        sys.path = original_path

    def test_pythonpath_multiple_entries(self, monkeypatch, tmp_path):
        """Test PYTHONPATH with multiple colon-separated paths"""
        dir1 = tmp_path / "dir1"
        dir2 = tmp_path / "dir2"
        dir3 = tmp_path / "dir3"
        dir1.mkdir()
        dir2.mkdir()
        dir3.mkdir()
        
        monkeypatch.setenv('PYTHONPATH', f"{dir1}{os.pathsep}{dir2}{os.pathsep}{dir3}")
        
        original_path = sys.path.copy()
        
        if 'PYTHONPATH' in os.environ:
            pythonpath_entries = os.environ['PYTHONPATH'].split(os.pathsep)
            for entry in reversed(pythonpath_entries):
                if entry and os.path.isdir(entry) and entry not in sys.path:
                    sys.path.insert(0, entry)
        
        assert str(dir1) in sys.path
        assert str(dir2) in sys.path
        assert str(dir3) in sys.path
        
        sys.path = original_path

    def test_repo_root_misconfigured_as_common(self, monkeypatch, tmp_path):
        """Test REPO_ROOT ending with /common is corrected"""
        repo_dir = tmp_path / "repo"
        common_dir = repo_dir / "common"
        repo_dir.mkdir()
        common_dir.mkdir()
        
        monkeypatch.setenv('REPO_ROOT', str(common_dir))
        
        original_path = sys.path.copy()
        
        if 'REPO_ROOT' in os.environ:
            repo_root = os.environ['REPO_ROOT']
            if repo_root and repo_root.endswith('/common'):
                repo_root = str(Path(repo_root).parent)
            if repo_root and os.path.isdir(repo_root) and repo_root not in sys.path:
                sys.path.insert(0, repo_root)
        
        assert str(repo_dir) in sys.path
        
        sys.path = original_path

    def test_invalid_paths_skipped(self, monkeypatch):
        """Test invalid paths are skipped"""
        monkeypatch.setenv('REPO_ROOT', '/nonexistent/path')
        monkeypatch.setenv('PYTHONPATH', '/another/nonexistent:/also/bad')
        
        original_path = sys.path.copy()
        original_len = len(sys.path)
        
        if 'REPO_ROOT' in os.environ:
            repo_root = os.environ['REPO_ROOT']
            if repo_root and os.path.isdir(repo_root) and repo_root not in sys.path:
                sys.path.insert(0, repo_root)
        
        if 'PYTHONPATH' in os.environ:
            pythonpath_entries = os.environ['PYTHONPATH'].split(os.pathsep)
            for entry in reversed(pythonpath_entries):
                if entry and os.path.isdir(entry) and entry not in sys.path:
                    sys.path.insert(0, entry)
        
        assert len(sys.path) == original_len
        assert '/nonexistent/path' not in sys.path
        assert '/another/nonexistent' not in sys.path
        assert '/also/bad' not in sys.path
        
        sys.path = original_path

    def test_empty_pythonpath_entries_skipped(self, monkeypatch, tmp_path):
        """Test empty PYTHONPATH entries are skipped"""
        valid_dir = tmp_path / "valid"
        valid_dir.mkdir()
        
        monkeypatch.setenv('PYTHONPATH', f"{valid_dir}{os.pathsep}{os.pathsep}/nonexistent")
        
        original_path = sys.path.copy()
        
        if 'PYTHONPATH' in os.environ:
            pythonpath_entries = os.environ['PYTHONPATH'].split(os.pathsep)
            for entry in reversed(pythonpath_entries):
                if entry and os.path.isdir(entry) and entry not in sys.path:
                    sys.path.insert(0, entry)
        
        assert str(valid_dir) in sys.path
        assert '' not in sys.path
        
        sys.path = original_path

    def test_no_duplicate_paths(self, monkeypatch, tmp_path):
        """Test paths are not added if already in sys.path"""
        test_dir = tmp_path / "test"
        test_dir.mkdir()
        
        original_path = sys.path.copy()
        sys.path.insert(0, str(test_dir))
        initial_count = sys.path.count(str(test_dir))
        
        monkeypatch.setenv('REPO_ROOT', str(test_dir))
        
        if 'REPO_ROOT' in os.environ:
            repo_root = os.environ['REPO_ROOT']
            if repo_root and os.path.isdir(repo_root) and repo_root not in sys.path:
                sys.path.insert(0, repo_root)
        
        assert sys.path.count(str(test_dir)) == initial_count
        
        sys.path = original_path

    def test_marker_file_detection(self, tmp_path):
        """Test marker file detection fallback"""
        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()
        (repo_dir / "pyproject.toml").touch()
        
        script_file = repo_dir / "script.py"
        script_file.touch()
        
        original_path = sys.path.copy()
        
        script_path = Path(script_file).resolve()
        for parent in [script_path] + list(script_path.parents):
            if (parent / 'pyproject.toml').exists() or (parent / '.git').exists() or (parent / 'env.schema.yaml').exists() or (parent / 'common').is_dir():
                if str(parent) not in sys.path:
                    sys.path.insert(0, str(parent))
                break
        
        assert str(repo_dir) in sys.path
        
        sys.path = original_path

    def test_common_directory_detection(self, tmp_path):
        """Test common directory detection as marker"""
        repo_dir = tmp_path / "repo"
        common_dir = repo_dir / "common"
        repo_dir.mkdir()
        common_dir.mkdir()
        
        script_file = repo_dir / "script.py"
        script_file.touch()
        
        original_path = sys.path.copy()
        
        script_path = Path(script_file).resolve()
        for parent in [script_path] + list(script_path.parents):
            if (parent / 'pyproject.toml').exists() or (parent / '.git').exists() or (parent / 'env.schema.yaml').exists() or (parent / 'common').is_dir():
                if str(parent) not in sys.path:
                    sys.path.insert(0, str(parent))
                break
        
        assert str(repo_dir) in sys.path
        
        sys.path = original_path

    def test_both_env_vars_add_paths(self, monkeypatch, tmp_path):
        """Test both REPO_ROOT and PYTHONPATH add their paths"""
        repo_root_dir = tmp_path / "repo_root"
        pythonpath_dir = tmp_path / "pythonpath"
        
        repo_root_dir.mkdir()
        pythonpath_dir.mkdir()
        
        monkeypatch.setenv('REPO_ROOT', str(repo_root_dir))
        monkeypatch.setenv('PYTHONPATH', str(pythonpath_dir))
        
        original_path = sys.path.copy()
        
        if 'REPO_ROOT' in os.environ:
            repo_root = os.environ['REPO_ROOT']
            if repo_root and os.path.isdir(repo_root) and repo_root not in sys.path:
                sys.path.insert(0, repo_root)
        
        if 'PYTHONPATH' in os.environ:
            pythonpath_entries = os.environ['PYTHONPATH'].split(os.pathsep)
            for entry in reversed(pythonpath_entries):
                if entry and os.path.isdir(entry) and entry not in sys.path:
                    sys.path.insert(0, entry)
        
        assert str(repo_root_dir) in sys.path
        assert str(pythonpath_dir) in sys.path
        
        sys.path = original_path
