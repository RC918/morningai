"""
Utility for reliably discovering the repository root directory.

This module provides a robust way to find the repository root that works across
different execution contexts (pytest, scripts, CI, containers, etc.) without
relying on fragile .parent.parent... chains.

Usage:
    from src.utils.repo_root import get_repo_root
    
    repo_root = get_repo_root()
    config_path = repo_root / 'config' / 'env.schema.yaml'
"""

import logging
import os
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


REPO_SENTINELS = [
    '.git',
    'config/env.schema.yaml',
    'pyproject.toml',
    'package.json',
]


@lru_cache(maxsize=1)
def get_repo_root(start_path: Optional[Path] = None) -> Path:
    """
    Find the repository root directory using multiple strategies.
    
    Resolution order:
    1. REPO_ROOT_PATH environment variable (if set and exists) - TESTING/CI ONLY
    2. git rev-parse --show-toplevel (if in a git repository)
    3. Ascend from start_path to find sentinel files
    
    WARNING: REPO_ROOT_PATH should only be set in testing/CI environments.
    Do not set this in production as it can override auto-detection and cause
    incorrect path resolution
    
    Args:
        start_path: Starting path for search. Defaults to this file's directory.
    
    Returns:
        Path to repository root
    
    Raises:
        RuntimeError: If repository root cannot be determined
    
    Examples:
        >>> repo_root = get_repo_root()
        >>> config_path = repo_root / 'config' / 'env.schema.yaml'
        >>> assert config_path.exists()
    """
    env_root = os.environ.get('REPO_ROOT_PATH')
    if env_root:
        env_path = Path(env_root).resolve()
        if env_path.exists() and env_path.is_dir():
            return env_path
        else:
            logger.debug(
                "REPO_ROOT_PATH=%r is not a valid directory; ignoring and falling back to git/sentinels",
                env_root
            )
    
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'],
            capture_output=True,
            text=True,
            timeout=2,
            check=False
        )
        if result.returncode == 0:
            git_root = Path(result.stdout.strip()).resolve()
            if git_root.exists():
                return git_root
        else:
            logger.debug("git rev-parse returned non-zero exit code %d; falling back to sentinel search", result.returncode)
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        logger.debug("git rev-parse failed (%s); falling back to sentinel search", e)
    
    if start_path is None:
        start_path = Path(__file__).resolve().parent
    else:
        start_path = Path(start_path).resolve()
    
    current = start_path
    max_ascent = 10  # Prevent infinite loops
    
    for _ in range(max_ascent):
        for sentinel in REPO_SENTINELS:
            sentinel_path = current / sentinel
            if sentinel_path.exists():
                return current
        
        parent = current.parent
        if parent == current:
            break
        current = parent
    
    logger.debug(
        "Could not determine repository root from %s using env/git/sentinels",
        start_path
    )
    raise RuntimeError(
        f"Could not determine repository root. Tried:\n"
        f"  1. REPO_ROOT_PATH env var: {env_root or '(not set)'}\n"
        f"  2. git rev-parse: (failed or not in git repo)\n"
        f"  3. Sentinel search from: {start_path}\n"
        f"     Looking for: {', '.join(REPO_SENTINELS)}\n"
        f"\n"
        f"To fix: Set REPO_ROOT_PATH environment variable or run from within git repo."
    )


def get_api_backend_root(start_path: Optional[Path] = None) -> Path:
    """
    Get the api-backend root directory.
    
    This is a convenience function for code in the api-backend directory.
    
    Args:
        start_path: Starting path for search. Defaults to this file's directory.
    
    Returns:
        Path to handoff/20250928/40_App/api-backend directory
    
    Examples:
        >>> backend_root = get_api_backend_root()
        >>> src_dir = backend_root / 'src'
        >>> assert src_dir.exists()
    """
    if start_path is None:
        return Path(__file__).resolve().parent.parent.parent
    
    current = Path(start_path).resolve()
    max_ascent = 10
    
    for _ in range(max_ascent):
        if current.name == 'api-backend' and (current / 'src').exists():
            return current
        
        parent = current.parent
        if parent == current:
            break
        current = parent
    
    repo_root = get_repo_root(start_path)
    backend_root = repo_root / 'handoff' / '20250928' / '40_App' / 'api-backend'
    
    if backend_root.exists():
        return backend_root
    
    raise RuntimeError(
        f"Could not determine api-backend root from {start_path}. "
        f"Expected: {backend_root}"
    )


if __name__ == '__main__':
    try:
        repo_root = get_repo_root()
        print(f"✓ Repository root: {repo_root}")
        
        config_path = repo_root / 'config' / 'env.schema.yaml'
        if config_path.exists():
            print(f"✓ Found config/env.schema.yaml")
        else:
            print(f"⚠ config/env.schema.yaml not found at {config_path}")
        
        backend_root = get_api_backend_root()
        print(f"✓ API backend root: {backend_root}")
        
        src_dir = backend_root / 'src'
        if src_dir.exists():
            print(f"✓ Found src/ directory")
        else:
            print(f"⚠ src/ directory not found at {src_dir}")
        
    except RuntimeError as e:
        print(f"✗ Error: {e}")
        exit(1)
