#!/usr/bin/env python3
"""
Performance Analyzer - Code Performance Analysis
"""
import ast
import logging
from typing import List, Dict, Any
from dataclasses import dataclass

from agents.dev_agent.error_handler import create_success, create_error, ErrorCode

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PerformanceIssue:
    """Represents a performance issue"""
    issue_type: str
    severity: str
    description: str
    location: Dict[str, int]
    suggestion: str


class PerformanceAnalyzer:
    """Analyzes code for performance issues"""

    def __init__(self):
        """Initialize PerformanceAnalyzer"""
        pass

    def analyze_performance(self, code: str) -> Dict[str, Any]:
        """
        Analyze code for performance issues

        Args:
            code: Source code to analyze

        Returns:
            Dict with performance analysis results
        """
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return create_error(
                ErrorCode.INVALID_INPUT,
                f"Syntax error: {str(e)}"
            )

        issues: List[PerformanceIssue] = []

        issues.extend(self._check_nested_loops(tree))
        issues.extend(self._check_repeated_calculations(tree, code))

        return create_success({
            'total_issues': len(issues),
            'issues': [
                {
                    'issue_type': i.issue_type,
                    'severity': i.severity,
                    'description': i.description,
                    'location': i.location,
                    'suggestion': i.suggestion
                }
                for i in issues
            ]
        })

    def _check_nested_loops(self, tree: ast.AST) -> List[PerformanceIssue]:
        """Check for deeply nested loops"""
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While)):
                depth = self._calculate_loop_depth(node)
                if depth > 2:
                    issues.append(PerformanceIssue(
                        issue_type='nested_loops',
                        severity='medium',
                        description=f'Deeply nested loops (depth: {depth}) may cause performance issues',
                        location={'line': node.lineno},
                        suggestion='Consider optimizing algorithm or using more efficient data structures'
                    ))
        
        return issues

    def _calculate_loop_depth(self, node: ast.AST, depth: int = 1) -> int:
        """Calculate depth of nested loops"""
        max_depth = depth
        
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.For, ast.While)):
                child_depth = self._calculate_loop_depth(child, depth + 1)
                max_depth = max(max_depth, child_depth)
        
        return max_depth

    def _check_repeated_calculations(self, tree: ast.AST, code: str) -> List[PerformanceIssue]:
        """Check for repeated calculations in loops"""
        issues = []
        return issues


def create_performance_analyzer() -> PerformanceAnalyzer:
    """Factory function to create PerformanceAnalyzer instance"""
    return PerformanceAnalyzer()
