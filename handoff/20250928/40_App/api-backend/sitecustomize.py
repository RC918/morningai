"""
Customize Python's sys.path to include the repository root.

This ensures that the 'common' module can be imported from anywhere
within the api-backend directory, particularly during test collection.

IMPORTANT: We also add 40_App to sys.path at position 0 AFTER repo root,
so that 'import orchestrator' resolves to 40_App/orchestrator (which has
the governance submodule) instead of repo-root/orchestrator (which doesn't).
"""
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))  # 40_App directory

# Add repo root first (for 'common' module)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

# Add 40_App at position 0 so it wins the import race for 'orchestrator'
# This ensures 'from orchestrator.governance import ...' works correctly
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)
