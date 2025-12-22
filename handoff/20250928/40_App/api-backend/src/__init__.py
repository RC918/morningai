# Bootstrap orchestrator paths before any other imports
# This ensures 'from orchestrator.governance...' imports work correctly
from src.bootstrap_paths import ensure_bootstrapped
ensure_bootstrapped()
