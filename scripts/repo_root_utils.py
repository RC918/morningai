"""
Scripts utilities for repository root discovery.

This module re-exports get_repo_root from the common module for use in scripts.

Usage:
    from scripts.repo_root_utils import get_repo_root
    
    repo_root = get_repo_root()
    config_path = repo_root / 'config' / 'env.schema.yaml'
"""

import sys
from pathlib import Path

_repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_repo_root))

from common.utils.repo_root import get_repo_root  # noqa: E402

__all__ = ['get_repo_root']


if __name__ == '__main__':
    try:
        repo_root = get_repo_root()
        print(f"✓ Repository root: {repo_root}")
        
        config_path = repo_root / 'config' / 'env.schema.yaml'
        if config_path.exists():
            print(f"✓ Found config/env.schema.yaml")
        else:
            print(f"⚠ config/env.schema.yaml not found at {config_path}")
        
    except RuntimeError as e:
        print(f"✗ Error: {e}")
        exit(1)
