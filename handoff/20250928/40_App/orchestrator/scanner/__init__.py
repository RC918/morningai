"""
Scanner module for MorningAI Orchestrator.

This module provides periodic scanning capabilities to complement webhook-based
event processing, serving as a backup mechanism for missed webhooks.

Issue: #3519 - CI failure polling scanner as webhook backup
"""

from .ci_failure_scanner import CIFailureScanner, run_scanner

__all__ = ["CIFailureScanner", "run_scanner"]
