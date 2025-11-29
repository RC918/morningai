"""
Security Agent - Phase 4 PR-2

Advisory agent for security analysis in the 5-Agent Advisory Pipeline.
Provides security recommendations for code changes and task execution.
"""
from .agent import SecurityAgent, SecurityAdvisory, SecurityRisk

__all__ = ['SecurityAgent', 'SecurityAdvisory', 'SecurityRisk']
