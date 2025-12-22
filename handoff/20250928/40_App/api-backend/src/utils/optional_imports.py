"""
Utilities for handling optional dependencies gracefully.

This module provides a proxy class that raises descriptive errors when
optional dependencies are not available, preventing silent AttributeError
failures that can be confusing to debug.

Usage:
    try:
        from orchestrator.governance.ai_policy import PolicyStatus
        AI_POLICY_AVAILABLE = True
    except ImportError:
        AI_POLICY_AVAILABLE = False
        PolicyStatus = MissingOptionalDependency(
            "orchestrator.governance.ai_policy.PolicyStatus",
            hint="Check PYTHONPATH and orchestrator package installation"
        )
"""
import logging

_logger = logging.getLogger(__name__)


class MissingOptionalDependency:
    """
    A proxy object that raises RuntimeError on any attribute access.
    
    This replaces the pattern of setting `SomeClass = None` when an import
    fails, which can lead to confusing AttributeError exceptions like
    `'NoneType' object has no attribute 'DRAFT'`.
    
    Instead, this proxy raises a clear RuntimeError explaining which
    dependency is missing and how to fix it.
    
    Attributes:
        _name: The fully qualified name of the missing dependency
        _hint: Optional hint for how to resolve the issue
    """
    
    __slots__ = ('_name', '_hint')
    
    def __init__(self, name: str, *, hint: str = None):
        """
        Initialize the proxy.
        
        Args:
            name: Fully qualified name of the missing dependency
                  (e.g., "orchestrator.governance.ai_policy.PolicyStatus")
            hint: Optional hint for resolving the issue
        """
        object.__setattr__(self, '_name', name)
        object.__setattr__(self, '_hint', hint)
    
    def _raise_error(self, attr_name: str = None) -> None:
        """Raise a descriptive RuntimeError."""
        msg = f"Optional dependency '{self._name}' is not available"
        if attr_name:
            msg += f" (attempted to access '.{attr_name}')"
        if self._hint:
            msg += f". {self._hint}"
        raise RuntimeError(msg)
    
    def __getattr__(self, name: str):
        """Raise error on any attribute access."""
        self._raise_error(name)
    
    def __setattr__(self, name: str, value):
        """Raise error on any attribute assignment."""
        if name in ('_name', '_hint'):
            object.__setattr__(self, name, value)
        else:
            self._raise_error(name)
    
    def __call__(self, *args, **kwargs):
        """Raise error if called as a function/constructor."""
        self._raise_error("__call__")
    
    def __repr__(self) -> str:
        """Return a clear representation showing this is a missing dependency."""
        return f"<MissingOptionalDependency: {self._name}>"
    
    def __str__(self) -> str:
        """Return a clear string showing this is a missing dependency."""
        return f"<MissingOptionalDependency: {self._name}>"
    
    def __bool__(self) -> bool:
        """
        Return False to allow truthiness checks without raising.
        
        This allows patterns like:
            if PolicyStatus:
                # use PolicyStatus
        """
        return False
    
    def __eq__(self, other) -> bool:
        """
        Compare equal to None for backward compatibility.
        
        This allows existing code that checks `if X is None` or `if X == None`
        to continue working, though `if not X` is preferred.
        """
        return other is None
    
    def __ne__(self, other) -> bool:
        """Inverse of __eq__."""
        return other is not None
    
    def __hash__(self) -> int:
        """Return a consistent hash based on the name."""
        return hash(self._name)


def missing(name: str, *, hint: str = None) -> MissingOptionalDependency:
    """
    Factory function to create a MissingOptionalDependency proxy.
    
    This is a convenience function that makes call sites cleaner:
    
        PolicyStatus = missing(
            "orchestrator.governance.ai_policy.PolicyStatus",
            hint="Ensure orchestrator package is installed"
        )
    
    Args:
        name: Fully qualified name of the missing dependency
        hint: Optional hint for resolving the issue
        
    Returns:
        MissingOptionalDependency proxy instance
    """
    return MissingOptionalDependency(name, hint=hint)
