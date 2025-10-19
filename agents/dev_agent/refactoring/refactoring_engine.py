#!/usr/bin/env python3
"""
Refactoring Engine - Smart Code Refactoring
Analyzes code and provides intelligent refactoring suggestions
"""
import ast
import re
import logging
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum

from agents.dev_agent.error_handler import create_success, create_error, ErrorCode

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RefactoringType(Enum):
    """Types of refactoring suggestions"""
    EXTRACT_METHOD = "extract_method"
    EXTRACT_CLASS = "extract_class"
    SIMPLIFY_CONDITIONAL = "simplify_conditional"
    REMOVE_DUPLICATION = "remove_duplication"
    RENAME = "rename"
    REDUCE_COMPLEXITY = "reduce_complexity"
    IMPROVE_NAMING = "improve_naming"
    ADD_TYPE_HINTS = "add_type_hints"


@dataclass
class RefactoringSuggestion:
    """Represents a single refactoring suggestion"""
    type: RefactoringType
    severity: str
    description: str
    location: Dict[str, int]
    code_snippet: str
    suggested_code: Optional[str] = None
    confidence: float = 0.8
    impact: str = "medium"


class RefactoringEngine:
    """
    Smart Refactoring Engine
    Analyzes code and provides intelligent refactoring suggestions
    """

    def __init__(
        self,
        max_function_lines: int = 50,
        max_complexity: int = 10,
        min_duplication_length: int = 5
    ):
        """
        Initialize RefactoringEngine

        Args:
            max_function_lines: Maximum lines before suggesting extraction
            max_complexity: Maximum cyclomatic complexity
            min_duplication_length: Minimum lines for duplication detection
        """
        self.max_function_lines = max_function_lines
        self.max_complexity = max_complexity
        self.min_duplication_length = min_duplication_length

    def analyze_code(self, code: str, file_path: str = "unknown") -> Dict[str, Any]:
        """
        Analyze code and provide refactoring suggestions

        Args:
            code: Source code to analyze
            file_path: Path to the file being analyzed

        Returns:
            Dict with success status and suggestions
        """
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return create_error(
                ErrorCode.INVALID_INPUT,
                f"Syntax error in code: {str(e)}",
                line=e.lineno
            )

        suggestions: List[RefactoringSuggestion] = []

        suggestions.extend(self._check_long_functions(tree, code))
        suggestions.extend(self._check_complexity(tree, code))
        suggestions.extend(self._check_code_duplication(code))
        suggestions.extend(self._check_naming_conventions(tree, code))
        suggestions.extend(self._check_type_hints(tree, code))

        suggestions.sort(key=lambda x: (
            {'high': 0, 'medium': 1, 'low': 2}[x.severity],
            -x.confidence
        ))

        return create_success({
            'file_path': file_path,
            'total_suggestions': len(suggestions),
            'suggestions': [self._suggestion_to_dict(s) for s in suggestions],
            'metrics': {
                'total_functions': len([n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]),
                'total_classes': len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]),
                'lines_of_code': len(code.split('\n'))
            }
        })

    def _check_long_functions(self, tree: ast.AST, code: str) -> List[RefactoringSuggestion]:
        """Identify functions that are too long"""
        suggestions = []
        lines = code.split('\n')

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if hasattr(node, 'lineno') and hasattr(node, 'end_lineno'):
                    func_lines = node.end_lineno - node.lineno + 1

                    if func_lines > self.max_function_lines:
                        code_snippet = '\n'.join(lines[node.lineno-1:node.end_lineno])

                        suggestions.append(RefactoringSuggestion(
                            type=RefactoringType.EXTRACT_METHOD,
                            severity='medium' if func_lines < self.max_function_lines * 1.5 else 'high',
                            description=f"Function '{node.name}' is {func_lines} lines long (recommended: <{self.max_function_lines}). Consider breaking it into smaller functions.",
                            location={
                                'start_line': node.lineno,
                                'end_line': node.end_lineno
                            },
                            code_snippet=code_snippet[:200] + '...' if len(code_snippet) > 200 else code_snippet,
                            confidence=0.9,
                            impact='medium'
                        ))

        return suggestions

    def _calculate_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity of a function"""
        complexity = 1

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1

        return complexity

    def _check_complexity(self, tree: ast.AST, code: str) -> List[RefactoringSuggestion]:
        """Check for overly complex functions"""
        suggestions = []
        lines = code.split('\n')

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                complexity = self._calculate_complexity(node)

                if complexity > self.max_complexity:
                    code_snippet = '\n'.join(lines[node.lineno-1:min(node.end_lineno, node.lineno+10)])

                    suggestions.append(RefactoringSuggestion(
                        type=RefactoringType.REDUCE_COMPLEXITY,
                        severity='high' if complexity > self.max_complexity * 1.5 else 'medium',
                        description=f"Function '{node.name}' has cyclomatic complexity of {complexity} (recommended: <{self.max_complexity}). Consider simplifying logic or extracting methods.",
                        location={
                            'start_line': node.lineno,
                            'end_line': node.end_lineno
                        },
                        code_snippet=code_snippet,
                        confidence=0.85,
                        impact='high'
                    ))

        return suggestions

    def _check_code_duplication(self, code: str) -> List[RefactoringSuggestion]:
        """Detect code duplication"""
        suggestions = []
        lines = code.split('\n')
        significant_lines = [
            (i, line.strip()) for i, line in enumerate(lines)
            if line.strip() and not line.strip().startswith('#')
        ]

        seen_sequences: Dict[str, List[int]] = {}

        for i in range(len(significant_lines) - self.min_duplication_length):
            sequence = tuple(
                line for _, line in significant_lines[i:i+self.min_duplication_length]
            )
            sequence_key = '|'.join(sequence)

            if sequence_key in seen_sequences:
                seen_sequences[sequence_key].append(significant_lines[i][0])
            else:
                seen_sequences[sequence_key] = [significant_lines[i][0]]

        for sequence, locations in seen_sequences.items():
            if len(locations) > 1:
                first_line = locations[0]
                code_snippet = '\n'.join(lines[first_line:first_line+self.min_duplication_length])

                suggestions.append(RefactoringSuggestion(
                    type=RefactoringType.REMOVE_DUPLICATION,
                    severity='medium',
                    description=f"Code duplication detected at {len(locations)} locations (lines: {', '.join(map(str, locations))}). Consider extracting to a function.",
                    location={
                        'start_line': first_line + 1,
                        'end_line': first_line + self.min_duplication_length + 1
                    },
                    code_snippet=code_snippet,
                    confidence=0.7,
                    impact='medium'
                ))

        return suggestions

    def _check_naming_conventions(self, tree: ast.AST, code: str) -> List[RefactoringSuggestion]:
        """Check naming conventions"""
        suggestions = []
        lines = code.split('\n')

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if not re.match(r'^[a-z_][a-z0-9_]*$', node.name):
                    original_line = lines[node.lineno - 1] if node.lineno <= len(lines) else f"def {node.name}():"
                    new_name = self._to_snake_case(node.name)
                    suggested_line = original_line.replace(node.name, new_name, 1)
                    
                    suggestions.append(RefactoringSuggestion(
                        type=RefactoringType.IMPROVE_NAMING,
                        severity='low',
                        description=f"Function '{node.name}' should use snake_case naming convention.",
                        location={'start_line': node.lineno, 'end_line': node.lineno},
                        code_snippet=f"def {node.name}(...)",
                        suggested_code=suggested_line,
                        confidence=0.95,
                        impact='low'
                    ))

            elif isinstance(node, ast.ClassDef):
                if not re.match(r'^[A-Z][a-zA-Z0-9]*$', node.name):
                    original_line = lines[node.lineno - 1] if node.lineno <= len(lines) else f"class {node.name}:"
                    new_name = self._to_pascal_case(node.name)
                    suggested_line = original_line.replace(node.name, new_name, 1)
                    
                    suggestions.append(RefactoringSuggestion(
                        type=RefactoringType.IMPROVE_NAMING,
                        severity='low',
                        description=f"Class '{node.name}' should use PascalCase naming convention.",
                        location={'start_line': node.lineno, 'end_line': node.lineno},
                        code_snippet=f"class {node.name}:",
                        suggested_code=suggested_line,
                        confidence=0.95,
                        impact='low'
                    ))

        return suggestions

    def _check_type_hints(self, tree: ast.AST, code: str) -> List[RefactoringSuggestion]:
        """Check for missing type hints"""
        suggestions = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                missing_hints = []

                if node.args.args:
                    for arg in node.args.args:
                        if arg.annotation is None and arg.arg != 'self' and arg.arg != 'cls':
                            missing_hints.append(arg.arg)

                if node.returns is None and node.name != '__init__':
                    missing_hints.append('return type')

                if missing_hints:
                    suggestions.append(RefactoringSuggestion(
                        type=RefactoringType.ADD_TYPE_HINTS,
                        severity='low',
                        description=f"Function '{node.name}' missing type hints for: {', '.join(missing_hints)}.",
                        location={'start_line': node.lineno, 'end_line': node.lineno},
                        code_snippet=f"def {node.name}(...)",
                        confidence=0.8,
                        impact='low'
                    ))

        return suggestions

    def _to_snake_case(self, name: str) -> str:
        """Convert name to snake_case"""
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    def _to_pascal_case(self, name: str) -> str:
        """Convert name to PascalCase"""
        return ''.join(word.capitalize() for word in name.split('_'))

    def _suggestion_to_dict(self, suggestion: RefactoringSuggestion) -> Dict[str, Any]:
        """Convert RefactoringSuggestion to dictionary"""
        return {
            'type': suggestion.type.value,
            'severity': suggestion.severity,
            'description': suggestion.description,
            'location': suggestion.location,
            'code_snippet': suggestion.code_snippet,
            'suggested_code': suggestion.suggested_code,
            'confidence': suggestion.confidence,
            'impact': suggestion.impact
        }

    def apply_refactoring(
        self,
        code: str,
        suggestion: RefactoringSuggestion
    ) -> Dict[str, Any]:
        """
        Apply a refactoring suggestion to code

        Args:
            code: Original source code
            suggestion: Refactoring suggestion to apply

        Returns:
            Dict with success status and refactored code
        """
        if suggestion.suggested_code is None:
            return create_error(
                ErrorCode.INVALID_INPUT,
                "Suggestion does not include suggested code",
                suggestion_type=suggestion.type.value
            )

        try:
            lines = code.split('\n')
            start_line = suggestion.location['start_line'] - 1
            end_line = suggestion.location.get('end_line', start_line + 1) - 1

            refactored_lines = lines[:start_line] + \
                [suggestion.suggested_code] + \
                lines[end_line+1:]

            refactored_code = '\n'.join(refactored_lines)

            try:
                ast.parse(refactored_code)
            except SyntaxError as e:
                return create_error(
                    ErrorCode.INVALID_OUTPUT,
                    f"Refactored code has syntax error: {str(e)}",
                    line=e.lineno
                )

            return create_success({
                'refactored_code': refactored_code,
                'changes_applied': 1
            })

        except Exception as e:
            logger.error(f"Failed to apply refactoring: {e}")
            return create_error(
                ErrorCode.TOOL_EXECUTION_FAILED,
                f"Failed to apply refactoring: {str(e)}"
            )

    def verify_refactoring(
        self,
        original: str,
        refactored: str
    ) -> Dict[str, Any]:
        """
        Verify that refactoring preserves functionality

        Args:
            original: Original code
            refactored: Refactored code

        Returns:
            Dict with verification results
        """
        try:
            original_ast = ast.parse(original)
            refactored_ast = ast.parse(refactored)
        except SyntaxError as e:
            return create_error(
                ErrorCode.INVALID_INPUT,
                f"Code has syntax error: {str(e)}"
            )

        original_functions = set()
        refactored_functions = set()

        for node in ast.walk(original_ast):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                original_functions.add(node.name)

        for node in ast.walk(refactored_ast):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                refactored_functions.add(node.name)

        added = refactored_functions - original_functions
        removed = original_functions - refactored_functions

        return create_success({
            'syntax_valid': True,
            'functions_preserved': len(removed) == 0 or len(added) > 0,
            'added_symbols': list(added),
            'removed_symbols': list(removed),
            'recommendation': 'Run tests to verify behavior' if (added or removed) else 'Structure preserved'
        })


def create_refactoring_engine(
    max_function_lines: int = 50,
    max_complexity: int = 10,
    min_duplication_length: int = 5
) -> RefactoringEngine:
    """Factory function to create RefactoringEngine instance"""
    return RefactoringEngine(
        max_function_lines=max_function_lines,
        max_complexity=max_complexity,
        min_duplication_length=min_duplication_length
    )
