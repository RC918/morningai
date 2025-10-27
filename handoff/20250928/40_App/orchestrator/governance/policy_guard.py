"""Policy Guard - Constraint-based autonomy enforcement"""
import os
import yaml
import re
from functools import wraps
from typing import Any, Callable, Dict, List, Optional
from pathlib import Path


class PolicyViolation(Exception):
    """Raised when a policy is violated"""
    pass


class PolicyGuard:
    """Enforces governance policies from policies.yaml"""
    
    def __init__(self, policies_path: Optional[str] = None):
        if policies_path is None:
            policies_path = os.getenv('POLICIES_PATH')
            if policies_path is None:
                policies_path = os.path.join(
                    os.path.dirname(__file__),
                    '../../../../config/policies.yaml'
                )
        
        self.policies_path = policies_path
        self.policies = self._load_policies()
    
    def _load_policies(self) -> Dict:
        """Load policies from YAML file"""
        try:
            with open(self.policies_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"[PolicyGuard] Warning: policies.yaml not found at {self.policies_path}")
            return {}
        except Exception as e:
            print(f"[PolicyGuard] Error loading policies: {e}")
            return {}
    
    def check_file_access(self, file_path: str) -> bool:
        """Check if file access is allowed"""
        if not self.policies:
            return True
        
        sandbox = self.policies.get('resource_sandbox', {})
        file_access = sandbox.get('file_access', {})
        
        deny_patterns = file_access.get('deny', [])
        for pattern in deny_patterns:
            if self._match_pattern(file_path, pattern):
                raise PolicyViolation(f"File access denied: {file_path} (matches deny pattern: {pattern})")
        
        allow_patterns = file_access.get('allow', [])
        if allow_patterns:
            for pattern in allow_patterns:
                if self._match_pattern(file_path, pattern):
                    return True
            raise PolicyViolation(f"File access denied: {file_path} (not in allow list)")
        
        return True
    
    def check_network_access(self, domain: str) -> bool:
        """Check if network access to domain is allowed"""
        if not self.policies:
            return True
        
        sandbox = self.policies.get('resource_sandbox', {})
        network = sandbox.get('network', {})
        allow_domains = network.get('allow_domains', [])
        
        if not allow_domains:
            return True
        
        for allowed in allow_domains:
            if self._match_domain(domain, allowed):
                return True
        
        raise PolicyViolation(f"Network access denied: {domain} (not in allow list)")
    
    def check_tool_permission(self, tool_name: str, operation: str, agent_permission_level: str) -> bool:
        """Check if agent has permission to use tool"""
        if not self.policies:
            return True
        
        constraints = self.policies.get('capability_constraints', {})
        restricted_tools = constraints.get('restricted_tools', [])
        
        for tool_config in restricted_tools:
            if tool_config['name'] == tool_name:
                required_level = tool_config.get('permission_level', 'sandbox_only')
                
                if not self._has_permission_level(agent_permission_level, required_level):
                    raise PolicyViolation(
                        f"Tool access denied: {tool_name} requires {required_level}, "
                        f"agent has {agent_permission_level}"
                    )
                
                denied_ops = tool_config.get('denied_operations', [])
                if operation in denied_ops:
                    raise PolicyViolation(
                        f"Operation denied: {tool_name}.{operation} is in denied list"
                    )
                
                allowed_ops = tool_config.get('allowed_operations', [])
                if allowed_ops and operation not in allowed_ops:
                    raise PolicyViolation(
                        f"Operation denied: {tool_name}.{operation} not in allowed list"
                    )
        
        return True
    
    def check_risk_level(self, file_paths: List[str]) -> str:
        """Determine risk level based on file patterns"""
        if not self.policies:
            return "low_risk"
        
        risk_routing = self.policies.get('risk_routing', {})
        risk_scoring = risk_routing.get('risk_scoring', {})
        file_patterns = risk_scoring.get('file_patterns', {})
        
        high_risk_patterns = file_patterns.get('high_risk', [])
        for file_path in file_paths:
            for pattern in high_risk_patterns:
                if self._match_pattern(file_path, pattern):
                    return "high_risk"
        
        medium_risk_patterns = file_patterns.get('medium_risk', [])
        for file_path in file_paths:
            for pattern in medium_risk_patterns:
                if self._match_pattern(file_path, pattern):
                    return "medium_risk"
        
        return "low_risk"
    
    def requires_human_approval(self, labels: List[str], risk_level: str) -> bool:
        """Check if human approval is required"""
        if not self.policies:
            return False
        
        risk_routing = self.policies.get('risk_routing', {})
        
        auto_approve = risk_routing.get('auto_approve_labels', [])
        if any(label in auto_approve for label in labels):
            return False
        
        high_risk_labels = risk_routing.get('high_risk_labels', [])
        if any(label in high_risk_labels for label in labels):
            return True
        
        if risk_level == "high_risk":
            return risk_routing.get('require_human_signoff', True)
        
        return False
    
    def _match_pattern(self, path: str, pattern: str) -> bool:
        """Match file path against glob-like pattern"""
        regex_pattern = pattern.replace('**', '.*').replace('*', '[^/]*')
        regex_pattern = f"^{regex_pattern}$"
        return bool(re.match(regex_pattern, path))
    
    def _match_domain(self, domain: str, pattern: str) -> bool:
        """Match domain against pattern (supports wildcards)"""
        if pattern.startswith('*.'):
            base_domain = pattern[2:]
            return domain.endswith(base_domain) or domain == base_domain
        return domain == pattern
    
    def _has_permission_level(self, current_level: str, required_level: str) -> bool:
        """Check if current permission level meets requirement"""
        levels = ['sandbox_only', 'staging_access', 'prod_low_risk', 'prod_full_access']
        
        try:
            current_idx = levels.index(current_level)
            required_idx = levels.index(required_level)
            return current_idx >= required_idx
        except ValueError:
            return False


_policy_guard = None


def get_policy_guard() -> PolicyGuard:
    """Get or create global PolicyGuard instance"""
    global _policy_guard
    if _policy_guard is None:
        _policy_guard = PolicyGuard()
    return _policy_guard


def guarded(func: Callable) -> Callable:
    """Decorator to enforce policy checks on tool functions"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        ctx = kwargs.get('ctx', {})
        
        guard = get_policy_guard()
        
        if 'file_path' in ctx:
            guard.check_file_access(ctx['file_path'])
        
        if 'domain' in ctx:
            guard.check_network_access(ctx['domain'])
        
        tool_name = ctx.get('tool_name', func.__name__)
        operation = ctx.get('operation', 'execute')
        agent_permission_level = ctx.get('permission_level', 'sandbox_only')
        
        guard.check_tool_permission(tool_name, operation, agent_permission_level)
        
        return func(*args, **kwargs)
    
    return wrapper
