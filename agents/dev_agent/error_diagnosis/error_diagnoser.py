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
        self.error_patterns = self._load_common_patterns()

    def _load_common_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load common error patterns and their fixes"""
        return {
            'AttributeError': {
                'pattern': r"'(\w+)' object has no attribute '(\w+)'",
                'fix_template': 'Check if object has attribute using hasattr() or add the attribute'
            },
            'KeyError': {
                'pattern': r"KeyError: ['\"](\w+)['\"]",
                'fix_template': 'Use .get() method: dict.get("key", default_value) or check if key exists'
            },
            'IndexError': {
                'pattern': r'(list|tuple) index out of range',
                'fix_template': 'Check list/tuple length before accessing: if len(items) > index: ...'
            },
            'TypeError': {
                'pattern': r"unsupported operand type|can't multiply sequence|argument must be",
                'fix_template': 'Verify data types are compatible and convert if needed using int(), str(), etc.'
            },
            'ValueError': {
                'pattern': r'ValueError:|invalid literal|could not convert',
                'fix_template': 'Validate input before conversion or use try-except to handle invalid values'
            },
            'ImportError': {
                'pattern': r'(ImportError|ModuleNotFoundError):.*No module named',
                'fix_template': 'Install missing package using pip install or verify import path'
            },
            'FileNotFoundError': {
                'pattern': r'FileNotFoundError|No such file or directory',
                'fix_template': 'Check file path exists using os.path.exists() before opening'
            },
            'ZeroDivisionError': {
                'pattern': r'ZeroDivisionError:|division by zero',
                'fix_template': 'Check denominator is not zero before division: if divisor != 0: ...'
            },
            'NameError': {
                'pattern': r"NameError:.*name '(\w+)' is not defined",
                'fix_template': 'Define the variable before using it or check for typos in variable name'
            },
            'IndentationError': {
                'pattern': r'IndentationError:|unexpected indent|expected an indented block',
                'fix_template': 'Fix indentation to match Python syntax (4 spaces per level)'
            },
            'SyntaxError': {
                'pattern': r'SyntaxError:|invalid syntax',
                'fix_template': 'Review code for syntax errors (missing colons, parentheses, quotes, etc.)'
            },
            'RecursionError': {
                'pattern': r'RecursionError:|maximum recursion depth exceeded',
                'fix_template': 'Add base case to recursive function or convert to iterative approach'
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
        if not error_message:
            return create_success(
                error_type='Unknown',
                error_message='',
                suggestions=[],
                total_suggestions=0
            )
        
        suggestions: List[FixSuggestion] = []
        detected_error_type = 'Unknown'

        for error_type, pattern_info in self.error_patterns.items():
            if re.search(pattern_info['pattern'], error_message, re.IGNORECASE):
                detected_error_type = error_type
                suggestions.append(FixSuggestion(
                    error_type=error_type,
                    description=f"Common {error_type} error",
                    suggested_fix=pattern_info['fix_template'],
                    confidence=0.8
                ))

        return create_success(
            error_type=detected_error_type,
            error_message=error_message,
            suggestions=suggestions,
            total_suggestions=len(suggestions)
        )


def create_error_diagnoser() -> ErrorDiagnoser:
    """Factory function to create ErrorDiagnoser instance"""
    return ErrorDiagnoser()
