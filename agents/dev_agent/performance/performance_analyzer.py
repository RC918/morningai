#!/usr/bin/env python3
"""
Performance Analyzer - Code Performance Analysis
"""
import ast
import logging
from typing import List, Dict, Any
from dataclasses import dataclass

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from error_handler import create_success, create_error, ErrorCode

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

    def analyze_code(self, code: str) -> Dict[str, Any]:
        """
        Analyze code for performance issues

        Args:
            code: Source code to analyze

        Returns:
            Dict with performance analysis results
        """
        if code is None:
            return create_error(
                ErrorCode.INVALID_INPUT,
                "Code input cannot be None"
            )
        
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
        issues.extend(self._check_global_lookups(tree))
        issues.extend(self._check_inefficient_operations(tree))
        issues.extend(self._check_memory_issues(tree))

        return create_success(
            total_issues=len(issues),
            issues=issues
        )

    def _check_nested_loops(self, tree: ast.AST) -> List[PerformanceIssue]:
        """Check for deeply nested loops"""
        issues = []
        visited = set()
        
        def analyze_node(node, current_depth=0):
            if id(node) in visited:
                return
            visited.add(id(node))
            
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
            
            for child in ast.iter_child_nodes(node):
                analyze_node(child, current_depth)
        
        analyze_node(tree)
        return issues

    def _calculate_loop_depth(self, node: ast.AST, depth: int = 1) -> int:
        """Calculate depth of nested loops, accounting for loops inside conditionals"""
        max_depth = depth
        
        for child in ast.walk(node):
            if child is node:
                continue
            if isinstance(child, (ast.For, ast.While)):
                child_depth = self._calculate_loop_depth(child, depth + 1)
                max_depth = max(max_depth, child_depth)
                break
        
        return max_depth

    def _check_repeated_calculations(self, tree: ast.AST, code: str) -> List[PerformanceIssue]:
        """Check for repeated calculations in loops"""
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While)):
                loop_calls = []
                
                for child in ast.walk(node):
                    if isinstance(child, ast.Call) and hasattr(child.func, 'id'):
                        func_name = child.func.id
                        if func_name not in ('print', 'len', 'range', 'enumerate', 'zip'):
                            loop_calls.append((func_name, child.lineno))
                
                call_counts = {}
                for func_name, lineno in loop_calls:
                    if func_name not in call_counts:
                        call_counts[func_name] = []
                    call_counts[func_name].append(lineno)
                
                for func_name, lines in call_counts.items():
                    if len(lines) > 1:
                        issues.append(PerformanceIssue(
                            issue_type='repeated_calculation',
                            severity='low',
                            description=f'Function "{func_name}" called multiple times ({len(lines)}) in loop',
                            location={'line': node.lineno, 'calls': lines},
                            suggestion=f'Consider caching result of "{func_name}" before loop if value doesn\'t change'
                        ))
        
        return issues
    
    def _check_global_lookups(self, tree: ast.AST) -> List[PerformanceIssue]:
        """Check for excessive global variable lookups in loops"""
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While)):
                global_accesses = []
                
                for child in ast.walk(node):
                    if isinstance(child, ast.Global):
                        for name in child.names:
                            global_accesses.append((name, child.lineno))
                
                if global_accesses:
                    issues.append(PerformanceIssue(
                        issue_type='global_lookup',
                        severity='low',
                        description=f'Global variable accesses in loop (count: {len(global_accesses)})',
                        location={'line': node.lineno},
                        suggestion='Consider using local variable to cache global value'
                    ))
        
        return issues
    
    def _check_inefficient_operations(self, tree: ast.AST) -> List[PerformanceIssue]:
        """Check for inefficient operations"""
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
                if isinstance(node.left, ast.Str) or isinstance(node.right, ast.Str):
                    parent_loop = self._find_parent_loop(tree, node)
                    if parent_loop:
                        issues.append(PerformanceIssue(
                            issue_type='inefficient_operation',
                            severity='medium',
                            description='String concatenation in loop (use list + join instead)',
                            location={'line': getattr(node, 'lineno', 0)},
                            suggestion='Use list.append() and "".join(list) instead of += for strings in loops'
                        ))
            
            if isinstance(node, ast.ListComp):
                for generator in node.generators:
                    if len(generator.ifs) > 1:
                        issues.append(PerformanceIssue(
                            issue_type='inefficient_operation',
                            severity='low',
                            description='Multiple filters in list comprehension',
                            location={'line': node.lineno},
                            suggestion='Consider combining filters with "and" or using generator expression for large datasets'
                        ))
        
        return issues
    
    def _check_memory_issues(self, tree: ast.AST) -> List[PerformanceIssue]:
        """Check for potential memory issues"""
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if hasattr(node.func, 'id'):
                    if node.func.id in ('list', 'dict', 'set'):
                        if len(node.args) > 0:
                            if isinstance(node.args[0], ast.ListComp):
                                issues.append(PerformanceIssue(
                                    issue_type='memory_issue',
                                    severity='low',
                                    description=f'Unnecessary {node.func.id}() wrapper around comprehension',
                                    location={'line': node.lineno},
                                    suggestion=f'Remove {node.func.id}() wrapper - comprehensions already create the collection'
                                ))
            
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        if isinstance(node.value, ast.List):
                            if len(node.value.elts) > 100:
                                issues.append(PerformanceIssue(
                                    issue_type='memory_issue',
                                    severity='low',
                                    description='Large list literal - consider generator or lazy loading',
                                    location={'line': node.lineno},
                                    suggestion='Use generator expressions for large datasets to reduce memory usage'
                                ))
        
        return issues
    
    def _find_parent_loop(self, tree: ast.AST, target_node: ast.AST) -> bool:
        """Check if a node is inside a loop"""
        class LoopChecker(ast.NodeVisitor):
            def __init__(self):
                self.in_loop = False
                self.target = target_node
                self.found = False
            
            def visit_For(self, node):
                old_in_loop = self.in_loop
                self.in_loop = True
                self.generic_visit(node)
                self.in_loop = old_in_loop
            
            def visit_While(self, node):
                old_in_loop = self.in_loop
                self.in_loop = True
                self.generic_visit(node)
                self.in_loop = old_in_loop
            
            def generic_visit(self, node):
                if node is self.target and self.in_loop:
                    self.found = True
                super().generic_visit(node)
        
        checker = LoopChecker()
        checker.visit(tree)
        return checker.found


def create_performance_analyzer() -> PerformanceAnalyzer:
    """Factory function to create PerformanceAnalyzer instance"""
    return PerformanceAnalyzer()
