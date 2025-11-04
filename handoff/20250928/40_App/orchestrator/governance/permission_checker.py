"""Permission Checker - Reputation-based access control"""
from typing import Optional
from .reputation_engine import get_reputation_engine


class PermissionDenied(Exception):
    """Raised when permission is denied"""
    pass


class PermissionChecker:
    """Check agent permissions based on reputation"""
    
    def __init__(self, reputation_engine=None):
        self.reputation_engine = reputation_engine or get_reputation_engine()
    
    def check_permission(self, agent_id: str, operation: str) -> bool:
        """
        Check if agent has permission to perform operation
        
        Args:
            agent_id: Agent UUID
            operation: Operation name (e.g., 'create_pr', 'deploy_prod')
        
        Returns:
            True if allowed
        
        Raises:
            PermissionDenied if not allowed
        """
        permission_level = self.reputation_engine.get_permission_level(agent_id)
        
        allowed_operations = self.reputation_engine.get_allowed_operations(agent_id)
        
        if operation not in allowed_operations:
            score = self.reputation_engine.get_reputation_score(agent_id)
            raise PermissionDenied(
                f"Operation '{operation}' denied for agent {agent_id}. "
                f"Current level: {permission_level} (score: {score}). "
                f"Allowed operations: {', '.join(allowed_operations)}"
            )
        
        return True
    
    def can_access_environment(self, agent_id: str, environment: str) -> bool:
        """Check if agent can access specific environment"""
        permission_level = self.reputation_engine.get_permission_level(agent_id)
        
        env_requirements = {
            'sandbox': 'sandbox_only',
            'staging': 'staging_access',
            'production': 'prod_low_risk'
        }
        
        required_level = env_requirements.get(environment, 'prod_full_access')
        
        levels = ['sandbox_only', 'staging_access', 'prod_low_risk', 'prod_full_access']
        
        try:
            current_idx = levels.index(permission_level)
            required_idx = levels.index(required_level)
            return current_idx >= required_idx
        except ValueError:
            return False
    
    def require_permission(self, agent_id: str, operation: str) -> None:
        """Require permission, raise exception if denied"""
        self.check_permission(agent_id, operation)
    
    def get_permission_summary(self, agent_id: str) -> dict:
        """Get comprehensive permission summary for agent"""
        permission_level = self.reputation_engine.get_permission_level(agent_id)
        score = self.reputation_engine.get_reputation_score(agent_id)
        allowed_operations = self.reputation_engine.get_allowed_operations(agent_id)
        
        levels_thresholds = {
            'sandbox_only': (0, 89),
            'staging_access': (90, 129),
            'prod_low_risk': (130, 159),
            'prod_full_access': (160, 999)
        }
        
        current_min, current_max = levels_thresholds.get(permission_level, (0, 89))
        
        next_level = None
        points_to_next = None
        
        levels_order = ['sandbox_only', 'staging_access', 'prod_low_risk', 'prod_full_access']
        current_idx = levels_order.index(permission_level) if permission_level in levels_order else 0
        
        if current_idx < len(levels_order) - 1:
            next_level = levels_order[current_idx + 1]
            next_min, _ = levels_thresholds[next_level]
            points_to_next = max(0, next_min - score)
        
        return {
            'agent_id': agent_id,
            'permission_level': permission_level,
            'reputation_score': score,
            'score_range': {
                'min': current_min,
                'max': current_max,
                'current': score
            },
            'allowed_operations': allowed_operations,
            'next_level': {
                'level': next_level,
                'points_needed': points_to_next
            } if next_level else None,
            'environment_access': {
                'sandbox': self.can_access_environment(agent_id, 'sandbox'),
                'staging': self.can_access_environment(agent_id, 'staging'),
                'production': self.can_access_environment(agent_id, 'production')
            }
        }


_permission_checker = None


def get_permission_checker() -> PermissionChecker:
    """Get or create global PermissionChecker instance"""
    global _permission_checker
    if _permission_checker is None:
        _permission_checker = PermissionChecker()
    return _permission_checker
