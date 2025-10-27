"""
Root conftest.py for monorepo test collection

This file configures pytest to properly handle tests from multiple sub-projects
that have their own module structures.

IMPORTANT: This file is executed BEFORE test collection, so sys.path modifications
here will affect all test imports.
"""
import sys
from pathlib import Path

# Get the root directory
ROOT_DIR = Path(__file__).parent.resolve()

# List of sub-projects that need to be added to sys.path
# These are directories that contain their own 'tools' or 'persistence' modules
SUBPROJECTS = [
    "agents/faq_agent",
    "agents/ops_agent",
    "agents/dev_agent",
    "handoff/20250928/40_App/api-backend/src",
    "handoff/20250928/40_App/orchestrator",
    "handoff/20250928/99_Original_Bundle",
    "orchestrator",
]

# Add each subproject to sys.path if it exists
added_paths = []
for subproject in SUBPROJECTS:
    subproject_path = ROOT_DIR / subproject
    if subproject_path.exists():
        path_str = str(subproject_path)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)
            added_paths.append(subproject)

# Also add the root directory itself
root_str = str(ROOT_DIR)
if root_str not in sys.path:
    sys.path.insert(0, root_str)

# This will be printed during pytest collection
# print(f"✓ Configured pytest for monorepo: added {len(added_paths)} subprojects to sys.path")
