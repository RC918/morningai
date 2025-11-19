"""
Agent Evaluation Harness

Provides tools for measuring AI agent performance metrics including:
- Task completion rate
- Correctness rate
- CI pass rate
- Time efficiency
- Overall success rate
"""

__version__ = "0.1.0"

from .runner import run_evaluation
from .metrics import calculate_metrics

__all__ = ["run_evaluation", "calculate_metrics"]
