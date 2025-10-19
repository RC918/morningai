#!/usr/bin/env python3
"""
Error Diagnoser - Diagnose and Fix Common Errors
"""
import re
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from error_handler import create_success, create_error, ErrorCode

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
                'fix_template': 'Check if object has attribute using hasattr() or add the attribute',
                'code_examples': [
                    'if hasattr(obj, "attr"): obj.attr',
                    'getattr(obj, "attr", default_value)'
                ]
            },
            'KeyError': {
                'pattern': r"KeyError: ['\"](\w+)['\"]",
                'fix_template': 'Use .get() method: dict.get("key", default_value) or check if key exists',
                'code_examples': [
                    'value = my_dict.get("key", None)',
                    'if "key" in my_dict: value = my_dict["key"]'
                ]
            },
            'IndexError': {
                'pattern': r'(list|tuple) index out of range',
                'fix_template': 'Check list/tuple length before accessing: if len(items) > index: ...',
                'code_examples': [
                    'if len(items) > index: value = items[index]',
                    'value = items[index] if index < len(items) else None'
                ]
            },
            'TypeError': {
                'pattern': r"unsupported operand type|can't multiply sequence|argument must be",
                'fix_template': 'Verify data types are compatible and convert if needed using int(), str(), etc.',
                'code_examples': [
                    'result = int(value1) + int(value2)',
                    'if isinstance(obj, expected_type): ...'
                ]
            },
            'ValueError': {
                'pattern': r'ValueError:|invalid literal|could not convert',
                'fix_template': 'Validate input before conversion or use try-except to handle invalid values',
                'code_examples': [
                    'try: num = int(value) \nexcept ValueError: num = 0',
                    'if value.isdigit(): num = int(value)'
                ]
            },
            'ImportError': {
                'pattern': r'(ImportError|ModuleNotFoundError):.*No module named',
                'fix_template': 'Install missing package using pip install or verify import path',
                'code_examples': [
                    'pip install package_name',
                    'poetry add package_name'
                ]
            },
            'FileNotFoundError': {
                'pattern': r'FileNotFoundError|No such file or directory',
                'fix_template': 'Check file path exists using os.path.exists() before opening',
                'code_examples': [
                    'if os.path.exists(filepath): with open(filepath) as f: ...',
                    'from pathlib import Path\nif Path(filepath).exists(): ...'
                ]
            },
            'ZeroDivisionError': {
                'pattern': r'ZeroDivisionError:|division by zero',
                'fix_template': 'Check denominator is not zero before division: if divisor != 0: ...',
                'code_examples': [
                    'result = numerator / divisor if divisor != 0 else 0',
                    'if divisor: result = numerator / divisor'
                ]
            },
            'NameError': {
                'pattern': r"NameError:.*name '(\w+)' is not defined",
                'fix_template': 'Define the variable before using it or check for typos in variable name',
                'code_examples': [
                    'variable_name = initial_value',
                    'Check spelling and scope of variable'
                ]
            },
            'IndentationError': {
                'pattern': r'IndentationError:|unexpected indent|expected an indented block',
                'fix_template': 'Fix indentation to match Python syntax (4 spaces per level)',
                'code_examples': [
                    'Use consistent indentation (4 spaces)',
                    'Ensure blocks after : are indented'
                ]
            },
            'SyntaxError': {
                'pattern': r'SyntaxError:|invalid syntax',
                'fix_template': 'Review code for syntax errors (missing colons, parentheses, quotes, etc.)',
                'code_examples': [
                    'Check for missing colons after if/for/def',
                    'Match opening and closing brackets/parentheses'
                ]
            },
            'RecursionError': {
                'pattern': r'RecursionError:|maximum recursion depth exceeded',
                'fix_template': 'Add base case to recursive function or convert to iterative approach',
                'code_examples': [
                    'def recursive_fn(n): if n <= 0: return base_case',
                    'Use iteration with for/while loops instead'
                ]
            },
            'AssertionError': {
                'pattern': r'AssertionError',
                'fix_template': 'Check assertion condition or remove/fix the assertion',
                'code_examples': [
                    'Add meaningful assertion messages: assert condition, "message"',
                    'Verify assertion logic is correct'
                ]
            },
            'StopIteration': {
                'pattern': r'StopIteration',
                'fix_template': 'Handle iterator exhaustion or use for loops instead of manual next()',
                'code_examples': [
                    'try: value = next(iterator) \nexcept StopIteration: ...',
                    'for item in iterator: ...'
                ]
            },
            'UnicodeDecodeError': {
                'pattern': r'UnicodeDecodeError|codec can\'t decode',
                'fix_template': 'Specify correct encoding or use error handling',
                'code_examples': [
                    'with open(file, encoding="utf-8") as f: ...',
                    'text.decode("utf-8", errors="ignore")'
                ]
            },
            'ConnectionError': {
                'pattern': r'ConnectionError|Connection refused|Connection reset',
                'fix_template': 'Check network connectivity and retry with exponential backoff',
                'code_examples': [
                    'import time\nfor i in range(retries): try: response = request() \nexcept ConnectionError: time.sleep(2**i)',
                    'Verify service is running and accessible'
                ]
            },
            'TimeoutError': {
                'pattern': r'TimeoutError|timed out',
                'fix_template': 'Increase timeout value or optimize slow operation',
                'code_examples': [
                    'response = requests.get(url, timeout=30)',
                    'Check for performance bottlenecks'
                ]
            },
            'PermissionError': {
                'pattern': r'PermissionError|Permission denied',
                'fix_template': 'Check file/directory permissions or run with appropriate privileges',
                'code_examples': [
                    'os.chmod(filepath, 0o644)',
                    'Verify user has read/write permissions'
                ]
            },
            'MemoryError': {
                'pattern': r'MemoryError|Out of memory',
                'fix_template': 'Optimize memory usage by processing data in chunks or using generators',
                'code_examples': [
                    'def process_large_file(): for line in file: yield process(line)',
                    'Use generators instead of loading all data into memory'
                ]
            },
            'JSONDecodeError': {
                'pattern': r'JSONDecodeError|Expecting value|Invalid.*JSON',
                'fix_template': 'Validate JSON format or use try-except to handle malformed JSON',
                'code_examples': [
                    'try: data = json.loads(text) \nexcept json.JSONDecodeError: ...',
                    'Verify JSON syntax with online validator'
                ]
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
