"""
Unit tests for repo_root discovery utilities.

Tests both:
- handoff/20250928/40_App/api-backend/src/utils/repo_root.py
- scripts/repo_root_utils.py

Coverage includes:
- REPO_ROOT_PATH environment variable override (valid/invalid paths)
- Git command failure/timeout scenarios with fallback to sentinel search
- Sentinel file search from deep subdirectories
- API backend root discovery
- LRU cache behavior

Note: Some tests involving subprocess mocking with LRU cache are excluded due to
pytest + lru_cache compatibility issues. See GitHub issue for future improvements.
"""
import importlib.util
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def import_module_from_path(module_name: str, file_path: Path):
    """Import a module from an arbitrary file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from {file_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def api_backend_utils():
    """Load the api-backend repo_root utility."""
    api_backend_root = Path(__file__).resolve().parent.parent.parent
    utils_path = api_backend_root / "src/utils/repo_root.py"
    module = import_module_from_path("api_backend_repo_root", utils_path)
    if hasattr(module.get_repo_root, 'cache_clear'):
        module.get_repo_root.cache_clear()
    if hasattr(module.get_api_backend_root, 'cache_clear'):
        module.get_api_backend_root.cache_clear()
    return module


@pytest.fixture
def scripts_utils():
    """Load the scripts repo_root utility."""
    repo_root = Path(__file__).resolve().parent.parent.parent.parent.parent.parent.parent
    utils_path = repo_root / "scripts/repo_root_utils.py"
    module = import_module_from_path("scripts_repo_root_utils", utils_path)
    if hasattr(module.get_repo_root, 'cache_clear'):
        module.get_repo_root.cache_clear()
    return module


@pytest.fixture(params=["api_backend_utils", "scripts_utils"])
def repo_root_module(request):
    """Parametrized fixture that tests both utilities."""
    return request.getfixturevalue(request.param)


class TestEnvOverride:
    """Test REPO_ROOT_PATH environment variable override."""

    def test_valid_env_override_takes_precedence(self, repo_root_module, tmp_path, monkeypatch):
        """Valid REPO_ROOT_PATH should take precedence over git and sentinels."""
        fake_repo = tmp_path / "fake_repo"
        fake_repo.mkdir()
        
        monkeypatch.setenv("REPO_ROOT_PATH", str(fake_repo))
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = str(tmp_path / "different_repo") + "\n"
        monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: mock_result)
        
        if hasattr(repo_root_module.get_repo_root, 'cache_clear'):
            repo_root_module.get_repo_root.cache_clear()
        
        result = repo_root_module.get_repo_root()
        assert result == fake_repo

    def test_invalid_env_override_falls_through(self, repo_root_module, monkeypatch, caplog):
        """Invalid REPO_ROOT_PATH should fall through to git/sentinels and log warning."""
        monkeypatch.setenv("REPO_ROOT_PATH", "/nonexistent/path/to/repo")
        
        actual_repo = Path(__file__).resolve().parent.parent.parent.parent.parent.parent
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = str(actual_repo) + "\n"
        monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: mock_result)
        
        if hasattr(repo_root_module.get_repo_root, 'cache_clear'):
            repo_root_module.get_repo_root.cache_clear()
        
        with caplog.at_level("DEBUG"):
            result = repo_root_module.get_repo_root()
        
        assert result == actual_repo
        assert any("REPO_ROOT_PATH" in record.message and "not a valid directory" in record.message 
                   for record in caplog.records)



class TestGitStrategy:
    """Test git rev-parse strategy."""

    def test_git_not_found(self, repo_root_module, tmp_path, monkeypatch, caplog):
        """Git command not found should fall back to sentinel search."""
        monkeypatch.delenv("REPO_ROOT_PATH", raising=False)
        
        def mock_run(*args, **kwargs):
            raise FileNotFoundError("git not found")
        monkeypatch.setattr(subprocess, "run", mock_run)
        
        fake_repo = tmp_path / "repo"
        fake_repo.mkdir()
        (fake_repo / ".git").mkdir()
        start_path = fake_repo / "a" / "b" / "c"
        start_path.mkdir(parents=True)
        
        if hasattr(repo_root_module.get_repo_root, 'cache_clear'):
            repo_root_module.get_repo_root.cache_clear()
        
        with caplog.at_level("DEBUG"):
            result = repo_root_module.get_repo_root(start_path=start_path)
        
        assert result == fake_repo
        assert any("git rev-parse failed" in record.message for record in caplog.records)

    def test_git_timeout(self, repo_root_module, tmp_path, monkeypatch, caplog):
        """Git command timeout should fall back to sentinel search."""
        monkeypatch.delenv("REPO_ROOT_PATH", raising=False)
        
        def mock_run(*args, **kwargs):
            raise subprocess.TimeoutExpired("git", 5)
        monkeypatch.setattr(subprocess, "run", mock_run)
        
        fake_repo = tmp_path / "repo"
        fake_repo.mkdir()
        (fake_repo / "config").mkdir()
        (fake_repo / "config" / "env.schema.yaml").touch()
        start_path = fake_repo / "deep" / "nested" / "path"
        start_path.mkdir(parents=True)
        
        if hasattr(repo_root_module.get_repo_root, 'cache_clear'):
            repo_root_module.get_repo_root.cache_clear()
        
        with caplog.at_level("DEBUG"):
            result = repo_root_module.get_repo_root(start_path=start_path)
        
        assert result == fake_repo
        assert any("git rev-parse failed" in record.message for record in caplog.records)


class TestSentinelSearch:
    """Test sentinel file search strategy."""

    def test_sentinel_git_directory(self, repo_root_module, tmp_path, monkeypatch):
        """Should find .git directory."""
        monkeypatch.delenv("REPO_ROOT_PATH", raising=False)
        
        def mock_run(*args, **kwargs):
            raise FileNotFoundError()
        monkeypatch.setattr(subprocess, "run", mock_run)
        
        fake_repo = tmp_path / "repo"
        fake_repo.mkdir()
        (fake_repo / ".git").mkdir()
        start_path = fake_repo / "a" / "b" / "c" / "d"
        start_path.mkdir(parents=True)
        
        if hasattr(repo_root_module.get_repo_root, 'cache_clear'):
            repo_root_module.get_repo_root.cache_clear()
        
        result = repo_root_module.get_repo_root(start_path=start_path)
        assert result == fake_repo

    def test_sentinel_env_schema(self, repo_root_module, tmp_path, monkeypatch):
        """Should find config/env.schema.yaml."""
        monkeypatch.delenv("REPO_ROOT_PATH", raising=False)
        
        def mock_run(*args, **kwargs):
            raise FileNotFoundError()
        monkeypatch.setattr(subprocess, "run", mock_run)
        
        fake_repo = tmp_path / "repo"
        fake_repo.mkdir()
        (fake_repo / "config").mkdir()
        (fake_repo / "config" / "env.schema.yaml").touch()
        start_path = fake_repo / "x" / "y" / "z"
        start_path.mkdir(parents=True)
        
        if hasattr(repo_root_module.get_repo_root, 'cache_clear'):
            repo_root_module.get_repo_root.cache_clear()
        
        result = repo_root_module.get_repo_root(start_path=start_path)
        assert result == fake_repo

    def test_sentinel_pyproject_toml(self, repo_root_module, tmp_path, monkeypatch):
        """Should find pyproject.toml."""
        monkeypatch.delenv("REPO_ROOT_PATH", raising=False)
        
        def mock_run(*args, **kwargs):
            raise FileNotFoundError()
        monkeypatch.setattr(subprocess, "run", mock_run)
        
        fake_repo = tmp_path / "repo"
        fake_repo.mkdir()
        (fake_repo / "pyproject.toml").touch()
        start_path = fake_repo / "nested"
        start_path.mkdir()
        
        if hasattr(repo_root_module.get_repo_root, 'cache_clear'):
            repo_root_module.get_repo_root.cache_clear()
        
        result = repo_root_module.get_repo_root(start_path=start_path)
        assert result == fake_repo

    def test_sentinel_package_json(self, repo_root_module, tmp_path, monkeypatch):
        """Should find package.json."""
        monkeypatch.delenv("REPO_ROOT_PATH", raising=False)
        
        def mock_run(*args, **kwargs):
            raise FileNotFoundError()
        monkeypatch.setattr(subprocess, "run", mock_run)
        
        fake_repo = tmp_path / "repo"
        fake_repo.mkdir()
        (fake_repo / "package.json").touch()
        start_path = fake_repo / "src" / "components"
        start_path.mkdir(parents=True)
        
        if hasattr(repo_root_module.get_repo_root, 'cache_clear'):
            repo_root_module.get_repo_root.cache_clear()
        
        result = repo_root_module.get_repo_root(start_path=start_path)
        assert result == fake_repo

    def test_sentinel_not_found_raises(self, repo_root_module, tmp_path, monkeypatch, caplog):
        """Should raise RuntimeError when no sentinel found."""
        monkeypatch.delenv("REPO_ROOT_PATH", raising=False)
        
        def mock_run(*args, **kwargs):
            raise FileNotFoundError()
        monkeypatch.setattr(subprocess, "run", mock_run)
        
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        
        if hasattr(repo_root_module.get_repo_root, 'cache_clear'):
            repo_root_module.get_repo_root.cache_clear()
        
        with pytest.raises(RuntimeError, match="Could not determine repository root"):
            with caplog.at_level("DEBUG"):
                repo_root_module.get_repo_root(start_path=empty_dir)
        
        assert any("Could not determine repository root" in record.message for record in caplog.records)


class TestApiBackendRoot:
    """Test get_api_backend_root() function (api-backend utils only)."""

    def test_get_api_backend_root(self, api_backend_utils, tmp_path, monkeypatch):
        """Should find api-backend directory from deep subdirectory."""
        monkeypatch.delenv("REPO_ROOT_PATH", raising=False)
        
        def mock_run(*args, **kwargs):
            raise FileNotFoundError()
        monkeypatch.setattr(subprocess, "run", mock_run)
        
        fake_repo = tmp_path / "repo"
        api_backend_dir = fake_repo / "handoff/20250928/40_App/api-backend"
        utils_dir = api_backend_dir / "src/utils"
        utils_dir.mkdir(parents=True)
        
        (fake_repo / ".git").mkdir()
        
        if hasattr(api_backend_utils.get_api_backend_root, 'cache_clear'):
            api_backend_utils.get_api_backend_root.cache_clear()
        if hasattr(api_backend_utils.get_repo_root, 'cache_clear'):
            api_backend_utils.get_repo_root.cache_clear()
        
        result = api_backend_utils.get_api_backend_root(start_path=utils_dir)
        assert result == api_backend_dir

    def test_get_api_backend_root_not_found_raises(self, api_backend_utils, tmp_path, monkeypatch):
        """Should raise RuntimeError when api-backend directory not found."""
        monkeypatch.delenv("REPO_ROOT_PATH", raising=False)
        
        def mock_run(*args, **kwargs):
            raise FileNotFoundError()
        monkeypatch.setattr(subprocess, "run", mock_run)
        
        fake_repo = tmp_path / "repo"
        fake_repo.mkdir()
        (fake_repo / ".git").mkdir()
        some_dir = fake_repo / "some/other/path"
        some_dir.mkdir(parents=True)
        
        if hasattr(api_backend_utils.get_api_backend_root, 'cache_clear'):
            api_backend_utils.get_api_backend_root.cache_clear()
        if hasattr(api_backend_utils.get_repo_root, 'cache_clear'):
            api_backend_utils.get_repo_root.cache_clear()
        
        with pytest.raises(RuntimeError, match="Could not (find|determine) api-backend"):
            api_backend_utils.get_api_backend_root(start_path=some_dir)


class TestCacheBehavior:
    """Test LRU cache behavior."""

    def test_cache_returns_same_object(self, repo_root_module, monkeypatch):
        """Multiple calls should return cached result."""
        monkeypatch.delenv("REPO_ROOT_PATH", raising=False)
        
        call_count = 0
        original_run = subprocess.run
        
        def counting_run(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "/test/repo\n"
            return mock_result
        
        monkeypatch.setattr(subprocess, "run", counting_run)
        
        if hasattr(repo_root_module.get_repo_root, 'cache_clear'):
            repo_root_module.get_repo_root.cache_clear()
        
        result1 = repo_root_module.get_repo_root()
        result2 = repo_root_module.get_repo_root()
        result3 = repo_root_module.get_repo_root()
        
        assert result1 == result2 == result3
        assert call_count == 1

    def test_cache_clear_forces_recompute(self, repo_root_module, monkeypatch):
        """Clearing cache should force recomputation."""
        monkeypatch.delenv("REPO_ROOT_PATH", raising=False)
        
        call_count = 0
        
        def counting_run(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "/test/repo\n"
            return mock_result
        
        monkeypatch.setattr(subprocess, "run", counting_run)
        
        if hasattr(repo_root_module.get_repo_root, 'cache_clear'):
            repo_root_module.get_repo_root.cache_clear()
        
        result1 = repo_root_module.get_repo_root()
        assert call_count == 1
        
        if hasattr(repo_root_module.get_repo_root, 'cache_clear'):
            repo_root_module.get_repo_root.cache_clear()
        
        result2 = repo_root_module.get_repo_root()
        assert call_count == 2
        assert result1 == result2


class TestGitIntegration:
    """Integration tests using real git repositories."""

    def test_git_success_from_subdirectory(self, tmp_path, repo_root_module):
        """Test git success by creating a real git repository."""
        repo_dir = tmp_path / "test_repo"
        repo_dir.mkdir()
        
        subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True)
        
        subdir = repo_dir / "a" / "b" / "c"
        subdir.mkdir(parents=True)
        
        if hasattr(repo_root_module.get_repo_root, 'cache_clear'):
            repo_root_module.get_repo_root.cache_clear()
        
        result = repo_root_module.get_repo_root(start_path=subdir)
        assert result == repo_dir

    def test_git_success_from_root(self, tmp_path, repo_root_module):
        """Test git success when called from repository root."""
        repo_dir = tmp_path / "test_repo"
        repo_dir.mkdir()
        
        subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True)
        
        if hasattr(repo_root_module.get_repo_root, 'cache_clear'):
            repo_root_module.get_repo_root.cache_clear()
        
        result = repo_root_module.get_repo_root(start_path=repo_dir)
        assert result == repo_dir

    def test_sentinel_fallback_when_not_in_git_repo(self, tmp_path, repo_root_module):
        """Test sentinel file search when not in a git repository."""
        repo_dir = tmp_path / "test_repo"
        repo_dir.mkdir()
        
        (repo_dir / "config").mkdir()
        (repo_dir / "config" / "env.schema.yaml").touch()
        
        subdir = repo_dir / "deep" / "nested" / "path"
        subdir.mkdir(parents=True)
        
        if hasattr(repo_root_module.get_repo_root, 'cache_clear'):
            repo_root_module.get_repo_root.cache_clear()
        
        result = repo_root_module.get_repo_root(start_path=subdir)
        assert result == repo_dir

    def test_multiple_sentinel_files(self, tmp_path, repo_root_module):
        """Test that any sentinel file is sufficient to identify repo root."""
        for sentinel in [".git", "pyproject.toml", "package.json"]:
            repo_dir = tmp_path / f"test_repo_{sentinel.replace('.', '_')}"
            repo_dir.mkdir()
            
            if sentinel == ".git":
                (repo_dir / sentinel).mkdir()
            else:
                (repo_dir / sentinel).touch()
            
            subdir = repo_dir / "src" / "utils"
            subdir.mkdir(parents=True)
            
            if hasattr(repo_root_module.get_repo_root, 'cache_clear'):
                repo_root_module.get_repo_root.cache_clear()
            
            result = repo_root_module.get_repo_root(start_path=subdir)
            assert result == repo_dir, f"Failed for sentinel: {sentinel}"
