#!/usr/bin/env python3
"""
Test Generator - Automatic Test Generation
Analyzes code and generates unit tests
"""
import ast
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from agents.dev_agent.error_handler import create_success, create_error, ErrorCode

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class GeneratedTest:
    """Represents a generated test case"""
    test_name: str
    test_code: str
    target_function: str
    description: str


class TestGenerator:
    """
    Automatic Test Generator
    Generates unit tests for Python code
    """

    def __init__(self, framework: str = "pytest"):
        """
        Initialize TestGenerator

        Args:
            framework: Test framework to use (pytest, unittest)
        """
        self.framework = framework

    def generate_tests(self, code: str, file_path: str = "unknown") -> Dict[str, Any]:
        """
        Generate tests for a source file

        Args:
            code: Source code to generate tests for
            file_path: Path to the source file

        Returns:
            Dict with success status and generated tests
        """
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return create_error(
                ErrorCode.INVALID_INPUT,
                f"Syntax error in code: {str(e)}",
                line=e.lineno
            )

        generated_tests: List[GeneratedTest] = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not node.name.startswith('_') and node.name != '__init__':
                    test = self._generate_test_for_function(node, code)
                    if test:
                        generated_tests.append(test)

        test_code = self._format_test_file(generated_tests, file_path)

        return create_success({
            'file_path': file_path,
            'total_tests': len(generated_tests),
            'test_code': test_code,
            'tests': [
                {
                    'test_name': t.test_name,
                    'target_function': t.target_function,
                    'description': t.description
                }
                for t in generated_tests
            ]
        })

    def _generate_test_for_function(
        self,
        func: ast.FunctionDef,
        source_code: str
    ) -> Optional[GeneratedTest]:
        """Generate test for a single function"""
        func_name = func.name
        test_name = f"test_{func_name}"

        args = [arg.arg for arg in func.args.args if arg.arg not in ('self', 'cls')]

        test_code_lines = []
        test_code_lines.append(f"def {test_name}():")
        test_code_lines.append(f'    """{f"Test {func_name} function"}"""')

        if args:
            test_inputs = self._generate_test_inputs(args)
            test_code_lines.append(f"    result = {func_name}({', '.join(test_inputs.values())})")
        else:
            test_code_lines.append(f"    result = {func_name}()")
        
        assertions = self._generate_assertions(func, func_name, args)
        for assertion in assertions:
            test_code_lines.append(f"    {assertion}")

        return GeneratedTest(
            test_name=test_name,
            test_code='\n'.join(test_code_lines),
            target_function=func_name,
            description=f"Test {func_name} function"
        )

    def _generate_test_inputs(self, args: List[str]) -> Dict[str, str]:
        """Generate test input values for function arguments"""
        test_inputs = {}
        
        for arg in args:
            if 'count' in arg.lower() or 'num' in arg.lower() or 'id' in arg.lower():
                test_inputs[arg] = '1'
            elif 'name' in arg.lower() or 'text' in arg.lower() or 'str' in arg.lower():
                test_inputs[arg] = '"test"'
            elif 'list' in arg.lower() or 'items' in arg.lower():
                test_inputs[arg] = '[]'
            elif 'dict' in arg.lower() or 'data' in arg.lower():
                test_inputs[arg] = '{}'
            elif 'bool' in arg.lower() or 'flag' in arg.lower():
                test_inputs[arg] = 'True'
            else:
                test_inputs[arg] = 'None'
        
        return test_inputs
    
    def _generate_assertions(self, func: ast.FunctionDef, func_name: str, args: List[str]) -> List[str]:
        """Generate meaningful assertions based on function characteristics"""
        assertions = []
        
        has_return_hint = func.returns is not None
        
        if 'get' in func_name.lower() or 'fetch' in func_name.lower() or 'retrieve' in func_name.lower():
            assertions.append("assert result is not None")
            if 'list' in func_name.lower() or 'all' in func_name.lower():
                assertions.append("assert isinstance(result, list)")
            elif 'dict' in func_name.lower():
                assertions.append("assert isinstance(result, dict)")
        
        elif 'is_' in func_name.lower() or 'has_' in func_name.lower() or 'can_' in func_name.lower():
            assertions.append("assert isinstance(result, bool)")
        
        elif 'count' in func_name.lower() or 'len' in func_name.lower() or 'size' in func_name.lower():
            assertions.append("assert isinstance(result, int)")
            assertions.append("assert result >= 0")
        
        elif 'calculate' in func_name.lower() or 'compute' in func_name.lower():
            assertions.append("assert result is not None")
            assertions.append("assert isinstance(result, (int, float))")
        
        elif 'create' in func_name.lower() or 'build' in func_name.lower():
            assertions.append("assert result is not None")
        
        elif 'delete' in func_name.lower() or 'remove' in func_name.lower():
            assertions.append("assert result is not None")
            if has_return_hint:
                if func.returns and hasattr(func.returns, 'id') and func.returns.id == 'bool':
                    assertions.append("assert isinstance(result, bool)")
        
        elif 'validate' in func_name.lower() or 'check' in func_name.lower():
            assertions.append("assert isinstance(result, bool)")
        
        elif 'find' in func_name.lower() or 'search' in func_name.lower():
            assertions.append("assert result is not None")
        
        elif has_return_hint:
            if hasattr(func.returns, 'id'):
                return_type = func.returns.id
                if return_type == 'bool':
                    assertions.append("assert isinstance(result, bool)")
                elif return_type == 'str':
                    assertions.append("assert isinstance(result, str)")
                    assertions.append("assert len(result) >= 0")
                elif return_type == 'int':
                    assertions.append("assert isinstance(result, int)")
                elif return_type == 'float':
                    assertions.append("assert isinstance(result, float)")
                elif return_type == 'list':
                    assertions.append("assert isinstance(result, list)")
                elif return_type == 'dict':
                    assertions.append("assert isinstance(result, dict)")
                else:
                    assertions.append("assert result is not None")
            else:
                assertions.append("assert result is not None")
        
        if not assertions:
            assertions.append("assert result is not None")
        
        return assertions

    def _format_test_file(self, tests: List[GeneratedTest], source_file: str) -> str:
        """Format generated tests into a complete test file"""
        lines = []
        
        lines.append('#!/usr/bin/env python3')
        lines.append(f'"""Auto-generated tests for {source_file}"""')
        
        if self.framework == "pytest":
            lines.append('import pytest')
        else:
            lines.append('import unittest')
        
        lines.append('')
        lines.append('')
        
        for test in tests:
            lines.append(test.test_code)
            lines.append('')
            lines.append('')
        
        if self.framework == "unittest":
            lines.append("if __name__ == '__main__':")
            lines.append("    unittest.main()")
        
        return '\n'.join(lines)


def create_test_generator(framework: str = "pytest") -> TestGenerator:
    """Factory function to create TestGenerator instance"""
    return TestGenerator(framework=framework)
