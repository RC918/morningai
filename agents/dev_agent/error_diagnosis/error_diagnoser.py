#!/usr/bin/env python3
"""
Error Diagnoser - Diagnose and Fix Common Errors
"""
import re
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from agents.dev_agent.error_handler import create_success, create_error, ErrorCode

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class FixSuggestion:
    """Represents a fix suggestion for an error"""
    error_type: str
    description: str
    suggested_fix: str
    confidence: float


class ErrorDiagnoser:
    """Diagnoses errors and suggests fixes"""

    def __init__(self):
        """Initialize ErrorDiagnoser"""
        self.common_patterns = self._load_common_patterns()

    def _load_common_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load common error patterns and their fixes"""
        return {
            'AttributeError': {
                'pattern': r"'(\w+)' object has no attribute '(\w+)'",
                'fix_template': 'Check if object has attribute using hasattr() or add the attribute'
            },
            'KeyError': {
                'pattern': r"KeyError: '(\w+)'",
                'fix_template': 'Use .get() method or check if key exists before accessing'
            },
            'IndexError': {
                'pattern': r'list index out of range',
                'fix_template': 'Check list length before accessing index'
            },
            'TypeError': {
                'pattern': r"unsupported operand type",
                'fix_template': 'Check operand types match expected types'
            }
        }

    def diagnose_error(
        self,
        error_message: str,
        code_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Diagnose an error and suggest fixes

        Args:
            error_message: The error message
            code_context: Optional code context where error occurred

        Returns:
            Dict with diagnosis and fix suggestions
        """
        suggestions: List[FixSuggestion] = []

        for error_type, pattern_info in self.common_patterns.items():
            if error_type in error_message:
                match = re.search(pattern_info['pattern'], error_message)
                if match:
                    suggestions.append(FixSuggestion(
                        error_type=error_type,
                        description=f"Common {error_type} error",
                        suggested_fix=pattern_info['fix_template'],
                        confidence=0.8
                    ))

        return create_success({
            'error_message': error_message,
            'total_suggestions': len(suggestions),
            'suggestions': [
                {
                    'error_type': s.error_type,
                    'description': s.description,
                    'suggested_fix': s.suggested_fix,
                    'confidence': s.confidence
                }
                for s in suggestions
            ]
        })


def create_error_diagnoser() -> ErrorDiagnoser:
    """Factory function to create ErrorDiagnoser instance"""
    return ErrorDiagnoser()
