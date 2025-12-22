"""
Pytest configuration for API Backend tests.

This conftest.py ensures that the repository root is on sys.path
so that the 'common' module can be imported during test collection.

IMPORTANT: We also add 40_App to sys.path at position 0 AFTER repo root,
so that 'import orchestrator' resolves to 40_App/orchestrator (which has
the governance submodule) instead of repo-root/orchestrator (which doesn't).

Note: The PYTHONPATH in CI is set to prioritize 40_App for orchestrator imports.
"""
import os
import sys

REPO_ROOT = os.path.abspath(os.path.realpath(os.path.join(os.path.dirname(__file__), "../../../..")))
APP_DIR = os.path.abspath(os.path.realpath(os.path.join(os.path.dirname(__file__), "..")))  # 40_App directory


def _normalize_path(p: str) -> str:
    """Normalize a path for comparison."""
    if not p:
        return p
    return os.path.normcase(os.path.normpath(os.path.abspath(p)))


def _ensure_path_at_front(path: str) -> None:
    """Ensure path is at position 0 of sys.path, removing any existing occurrences first."""
    normalized = _normalize_path(path)
    # Remove any existing occurrences of this path (with normalized comparison)
    sys.path[:] = [p for p in sys.path if p and _normalize_path(p) != normalized]
    # Insert at position 0
    sys.path.insert(0, path)


def _clear_orchestrator_modules() -> None:
    """Clear any cached orchestrator modules so they can be re-imported from the correct location."""
    modules_to_remove = [
        mod_name for mod_name in list(sys.modules.keys())
        if mod_name == 'orchestrator' or mod_name.startswith('orchestrator.')
    ]
    for mod_name in modules_to_remove:
        del sys.modules[mod_name]


# Step 1: Clear any previously imported orchestrator modules
_clear_orchestrator_modules()

# Step 2: Ensure repo root is in sys.path (for 'common' module)
# Use append to avoid shadowing 40_App
if _normalize_path(REPO_ROOT) not in [_normalize_path(p) for p in sys.path if p]:
    sys.path.append(REPO_ROOT)

# Step 3: Ensure 40_App is at position 0 so it wins the import race for 'orchestrator'
_ensure_path_at_front(APP_DIR)
