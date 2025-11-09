"""Agent Governance Framework"""
from pathlib import Path
import sys

repo_root = Path(__file__).resolve().parent
for _ in range(8):  # Limit search depth to avoid infinite loop
    if (repo_root / 'common').exists():
        break
    repo_root = repo_root.parent

if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from .policy_guard import PolicyGuard, guarded
from .cost_tracker import CostTracker, CostBudgetExceeded, get_cost_tracker
from .reputation_engine import ReputationEngine, get_reputation_engine
from .permission_checker import PermissionChecker, PermissionDenied, get_permission_checker
from .violation_detector import ViolationDetector, ViolationError, get_violation_detector

__all__ = [
    'PolicyGuard',
    'guarded',
    'CostTracker',
    'CostBudgetExceeded',
    'get_cost_tracker',
    'ReputationEngine',
    'get_reputation_engine',
    'PermissionChecker',
    'PermissionDenied',
    'get_permission_checker',
    'ViolationDetector',
    'ViolationError',
    'get_violation_detector',
]
