"""
Centralized sys.path bootstrap for MorningAI API Backend.

This module ensures that the orchestrator package and its submodules
(governance, webhooks, persistence, etc.) are importable as:
    from orchestrator.governance.ai_policy import ...
    from orchestrator.webhooks.handlers import ...

The orchestrator directory structure requires the parent directory (40_App)
to be on sys.path for these imports to work correctly.

This module should be imported early in:
- gunicorn.conf.py (production)
- src/__init__.py or conftest.py (tests)
"""
import os
import sys
import logging
from pathlib import Path

_logger = logging.getLogger(__name__)


def _normalize_path(path: str) -> str:
    """Normalize path to avoid duplicates from different representations."""
    return os.path.realpath(os.path.abspath(path))


def _ensure_path_at_front(path: str, description: str) -> bool:
    """
    Ensure normalized path is at position 0 of sys.path.
    
    If the path already exists elsewhere in sys.path, remove it first
    then insert at position 0. This ensures this path wins any import races.
    """
    normalized = _normalize_path(path)
    
    # Remove any existing occurrences of this path
    sys.path[:] = [p for p in sys.path if p and _normalize_path(p) != normalized]
    
    # Insert at position 0 to ensure it's searched first
    sys.path.insert(0, normalized)
    _logger.debug(f"bootstrap_paths: ensured {description}={normalized} at sys.path[0]")
    return True


def _clear_conflicting_orchestrator_modules():
    """
    Remove any existing orchestrator module that might be from the wrong location.

    This is needed because there may be a conflicting 'orchestrator' package
    installed via pip or at a different location. We need to ensure that
    'import orchestrator' resolves to our repo's orchestrator package.
    """
    modules_to_remove = [
        mod_name for mod_name in list(sys.modules.keys())
        if mod_name == 'orchestrator' or mod_name.startswith('orchestrator.')
    ]
    for mod_name in modules_to_remove:
        del sys.modules[mod_name]
        _logger.debug(f"bootstrap_paths: cleared conflicting module {mod_name}")


def bootstrap_orchestrator_paths():
    """
    Set up sys.path to enable orchestrator imports.

    This function:
    1. Clears any conflicting orchestrator modules from sys.modules
    2. Adds the 40_App directory to sys.path so that:
       - 'import orchestrator' works
       - 'from orchestrator.governance.ai_policy import ...' works
       - 'from orchestrator.webhooks.handlers import ...' works
    """
    # Find the 40_App directory relative to this file
    # Path: src/bootstrap_paths.py -> src -> api-backend -> 40_App
    this_file = Path(__file__).resolve()
    src_dir = this_file.parent
    api_backend_dir = src_dir.parent
    app_dir = api_backend_dir.parent  # This is 40_App

    # Verify we found the right directory
    orchestrator_dir = app_dir / 'orchestrator'
    if not orchestrator_dir.is_dir():
        _logger.warning(
            f"bootstrap_paths: orchestrator directory not found at {orchestrator_dir}. "
            "Orchestrator features may not work."
        )
        return False

    # Clear any conflicting orchestrator modules from sys.modules
    # This is needed in case orchestrator was already imported from the wrong location
    _clear_conflicting_orchestrator_modules()

    # Ensure 40_App is at position 0 in sys.path so it wins the import race
    # for 'import orchestrator'. We don't remove other paths (like repo root)
    # because they may be needed for other imports (e.g., 'import common').
    _ensure_path_at_front(str(app_dir), "40_App (orchestrator parent)")

    _logger.debug(f"bootstrap_paths: orchestrator imports enabled from {orchestrator_dir}")

    return True


# Auto-bootstrap when this module is imported
_bootstrapped = False


def ensure_bootstrapped():
    """Ensure paths are bootstrapped (idempotent)."""
    global _bootstrapped
    if not _bootstrapped:
        bootstrap_orchestrator_paths()
        _bootstrapped = True


# Bootstrap immediately on import
ensure_bootstrapped()
