"""
API Backend utilities for repository root discovery.

This module re-exports get_repo_root from the common module and provides
api-backend specific helpers like get_api_backend_root.

Usage:
    from src.utils.repo_root import get_repo_root, get_api_backend_root
    
    repo_root = get_repo_root()
    backend_root = get_api_backend_root()
"""

import sys
from pathlib import Path
from typing import Optional

_repo_root = Path(__file__).resolve().parent.parent.parent.parent.parent.parent
if not (_repo_root / 'common' / 'utils' / 'repo_root.py').exists():
    import subprocess
    result = subprocess.run(['git', 'rev-parse', '--show-toplevel'], 
                          capture_output=True, text=True, check=False)
    if result.returncode == 0:
        _repo_root = Path(result.stdout.strip())

sys.path.insert(0, str(_repo_root))

from common.utils.repo_root import get_repo_root  # noqa: E402

__all__ = ['get_repo_root', 'get_api_backend_root']


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
