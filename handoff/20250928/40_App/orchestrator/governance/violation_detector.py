"""Violation Detector - Detect and prevent policy violations"""
import re
from typing import Dict, List, Optional


class ViolationError(Exception):
    """Raised when a violation is detected"""
    pass


class ViolationDetector:
    """Detect policy violations in agent operations"""
    
    def __init__(self, policies=None):
        self.policies = policies or self._load_default_policies()
        self.violation_patterns = self.policies.get('violation_detection', {}).get('patterns', {})
    
    def _load_default_policies(self) -> Dict:
        """Load default violation patterns"""
        import os
        import yaml
        
        policies_path = os.path.join(
            os.path.dirname(__file__),
            '../../../../config/policies.yaml'
        )
        
        try:
            with open(policies_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"[ViolationDetector] Error loading policies: {e}")
            return {}
    
    def check_secrets_access(self, content: str) -> None:
        """Check for attempts to access secrets"""
        patterns = self.violation_patterns.get('secrets_access', [])
        
        for pattern_config in patterns:
            pattern = pattern_config.get('pattern', '')
            severity = pattern_config.get('severity', 'warning')
            action = pattern_config.get('action', 'warn')
            
            if re.search(pattern, content, re.IGNORECASE):
                message = f"Secrets access violation detected: pattern '{pattern}' matched"
                
                if action == 'block':
                    raise ViolationError(message)
                else:
                    print(f"[ViolationDetector] Warning: {message}")
    
    def check_dangerous_operations(self, command: str) -> None:
        """Check for dangerous shell operations"""
        patterns = self.violation_patterns.get('dangerous_operations', [])
        
        for pattern_config in patterns:
            pattern = pattern_config.get('pattern', '')
            severity = pattern_config.get('severity', 'warning')
            action = pattern_config.get('action', 'warn')
            
            if re.search(pattern, command, re.IGNORECASE):
                message = f"Dangerous operation detected: pattern '{pattern}' matched in command '{command}'"
                
                if action == 'block':
                    raise ViolationError(message)
                else:
                    print(f"[ViolationDetector] Warning: {message}")
    
    def check_unauthorized_api(self, api_call: str, args: Dict) -> None:
        """Check for unauthorized API access"""
        patterns = self.violation_patterns.get('unauthorized_api', [])
        
        args_str = str(args)
        full_call = f"{api_call} {args_str}"
        
        for pattern_config in patterns:
            pattern = pattern_config.get('pattern', '')
            severity = pattern_config.get('severity', 'warning')
            action = pattern_config.get('action', 'warn')
            
            if re.search(pattern, full_call, re.IGNORECASE):
                message = f"Unauthorized API access detected: pattern '{pattern}' matched"
                
                if action == 'block':
                    raise ViolationError(message)
                else:
                    print(f"[ViolationDetector] Warning: {message}")
    
    def check_file_access(self, file_path: str) -> None:
        """Check if file access violates policies"""
        secrets_patterns = [
            r'\.env',
            r'secrets',
            r'credentials',
            r'\.key$',
            r'\.pem$',
            r'\.p12$'
        ]
        
        for pattern in secrets_patterns:
            if re.search(pattern, file_path, re.IGNORECASE):
                raise ViolationError(f"Attempted access to secrets file: {file_path}")
    
    def check_all(self, operation: str, content: str, metadata: Optional[Dict] = None) -> None:
        """Run all violation checks"""
        metadata = metadata or {}
        
        if operation == 'file_access':
            self.check_file_access(content)
        elif operation == 'shell_command':
            self.check_dangerous_operations(content)
        elif operation == 'api_call':
            self.check_unauthorized_api(content, metadata.get('args', {}))
        
        self.check_secrets_access(content)
    
    def sanitize_content(self, content: str) -> str:
        """Sanitize content by removing potential secrets"""
        redact_patterns = [
            (r'(SECRET|PASSWORD|TOKEN|KEY)[\s=:]+[^\s]+', r'\1=<REDACTED>'),
            (r'Bearer\s+[^\s]+', 'Bearer <REDACTED>'),
            (r'[A-Za-z0-9]{32,}', '<REDACTED_TOKEN>'),
        ]
        
        sanitized = content
        for pattern, replacement in redact_patterns:
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
        
        return sanitized


_violation_detector = None


def get_violation_detector() -> ViolationDetector:
    """Get or create global ViolationDetector instance"""
    global _violation_detector
    if _violation_detector is None:
        _violation_detector = ViolationDetector()
    return _violation_detector
