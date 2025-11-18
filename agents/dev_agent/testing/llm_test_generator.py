#!/usr/bin/env python3
"""
LLM-Enhanced Test Generator - Intelligent Test Generation using GPT-4
Phase 2 Day 1-2: LLM-Enhanced Test Generator
"""
import ast
import logging
import os
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from openai import OpenAI

import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from agents.dev_agent.testing.test_generator import TestGenerator, GeneratedTest
from agents.dev_agent.error_handler import create_success, create_error, ErrorCode
from common.config.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMTestGenerator(TestGenerator):
    """
    LLM-Enhanced Test Generator
    Uses GPT-4 to generate intelligent, context-aware unit tests
    Falls back to heuristic mode if LLM fails
    """

    def __init__(
        self,
        framework: str = "pytest",
        openai_api_key: Optional[str] = None,
        model: str = "gpt-4",
        enable_llm: bool = True,
        max_retries: int = 2
    ):
        """
        Initialize LLM Test Generator

        Args:
            framework: Test framework to use (pytest, unittest)
            openai_api_key: OpenAI API key (defaults to settings)
            model: OpenAI model to use (gpt-4, gpt-4-turbo-preview)
            enable_llm: Whether to use LLM (False = heuristic only)
            max_retries: Maximum retries for LLM calls
        """
        super().__init__(framework=framework)
        
        self.enable_llm = enable_llm
        self.model = model
        self.max_retries = max_retries
        self.openai_client = None
        
        if enable_llm:
            api_key = openai_api_key or settings.openai_api_key
            if api_key:
                self.openai_client = OpenAI(api_key=api_key)
                logger.info(f"LLM Test Generator initialized with {model}")
            else:
                logger.warning(
                    "OpenAI API key not configured, falling back to heuristic mode"
                )
                self.enable_llm = False

    def generate_tests(self, code: str, file_path: str = "unknown") -> Dict[str, Any]:
        """
        Generate tests for a source file using LLM or heuristics

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
                    test = self._generate_test_for_function_with_llm(
                        node, code, file_path
                    )
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
            ],
            'llm_used': self.enable_llm and self.openai_client is not None
        })

    def _generate_test_for_function_with_llm(
        self,
        func: ast.FunctionDef,
        source_code: str,
        file_path: str
    ) -> Optional[GeneratedTest]:
        """
        Generate test for a function using LLM with fallback to heuristic

        Args:
            func: AST function definition
            source_code: Full source code
            file_path: Path to source file

        Returns:
            GeneratedTest or None
        """
        if not self.enable_llm or not self.openai_client:
            return super()._generate_test_for_function(func, source_code)

        try:
            func_source = self._extract_function_source(func, source_code)
            
            llm_test = self._call_llm_for_test_generation(
                func.name, func_source, file_path
            )
            
            if llm_test:
                return llm_test
            else:
                logger.info(
                    f"LLM failed for {func.name}, using heuristic fallback"
                )
                return super()._generate_test_for_function(func, source_code)

        except Exception as e:
            logger.warning(
                f"LLM test generation failed for {func.name}: {e}, "
                "using heuristic fallback"
            )
            return super()._generate_test_for_function(func, source_code)

    def _extract_function_source(
        self, func: ast.FunctionDef, source_code: str
    ) -> str:
        """
        Extract function source code from full source

        Args:
            func: AST function definition
            source_code: Full source code

        Returns:
            Function source code as string
        """
        try:
            lines = source_code.split('\n')
            start_line = func.lineno - 1
            end_line = func.end_lineno if hasattr(func, 'end_lineno') else start_line + 10
            
            func_lines = lines[start_line:end_line]
            return '\n'.join(func_lines)
        except Exception as e:
            logger.warning(f"Could not extract function source: {e}")
            return f"def {func.name}(...): pass"

    def _call_llm_for_test_generation(
        self,
        func_name: str,
        func_source: str,
        file_path: str
    ) -> Optional[GeneratedTest]:
        """
        Call LLM to generate test for a function

        Args:
            func_name: Function name
            func_source: Function source code
            file_path: Path to source file

        Returns:
            GeneratedTest or None if LLM fails
        """
        prompt = self._build_test_generation_prompt(
            func_name, func_source, file_path
        )

        for attempt in range(self.max_retries):
            try:
                response = self.openai_client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are an expert Python test engineer. "
                                "Generate comprehensive, meaningful unit tests "
                                "that cover edge cases and validate behavior."
                            )
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.3,
                    max_tokens=1000
                )

                llm_output = response.choices[0].message.content.strip()
                
                test = self._parse_llm_test_output(
                    llm_output, func_name
                )
                
                if test:
                    logger.info(
                        f"LLM successfully generated test for {func_name}"
                    )
                    return test
                else:
                    logger.warning(
                        f"Could not parse LLM output for {func_name}, "
                        f"attempt {attempt + 1}/{self.max_retries}"
                    )

            except Exception as e:
                logger.warning(
                    f"LLM call failed for {func_name}, "
                    f"attempt {attempt + 1}/{self.max_retries}: {e}"
                )

        return None

    def _build_test_generation_prompt(
        self,
        func_name: str,
        func_source: str,
        file_path: str
    ) -> str:
        """
        Build prompt for LLM test generation

        Args:
            func_name: Function name
            func_source: Function source code
            file_path: Path to source file

        Returns:
            Prompt string
        """
        framework_example = ""
        if self.framework == "pytest":
            framework_example = """
Example pytest test:
```python
def test_calculate_sum():
    \"\"\"Test calculate_sum with positive numbers\"\"\"
    result = calculate_sum(2, 3)
    assert result == 5
    assert isinstance(result, int)
```
"""
        else:
            framework_example = """
Example unittest test:
```python
def test_calculate_sum(self):
    \"\"\"Test calculate_sum with positive numbers\"\"\"
    result = calculate_sum(2, 3)
    self.assertEqual(result, 5)
    self.assertIsInstance(result, int)
```
"""

        prompt = f"""Generate a comprehensive unit test for the following Python function.

File: {file_path}
Function to test:
```python
{func_source}
```

Requirements:
1. Use {self.framework} framework
2. Test name should be: test_{func_name}
3. Include a descriptive docstring
4. Test edge cases and normal cases
5. Use meaningful assertions
6. Generate realistic test inputs based on function purpose
7. Return ONLY the test function code, no explanations

{framework_example}

Generate the test function:"""

        return prompt

    def _parse_llm_test_output(
        self,
        llm_output: str,
        func_name: str
    ) -> Optional[GeneratedTest]:
        """
        Parse LLM output to extract test code

        Args:
            llm_output: Raw LLM output
            func_name: Target function name

        Returns:
            GeneratedTest or None if parsing fails
        """
        try:
            code_blocks = []
            in_code_block = False
            current_block = []

            for line in llm_output.split('\n'):
                if line.strip().startswith('```'):
                    if in_code_block:
                        code_blocks.append('\n'.join(current_block))
                        current_block = []
                    in_code_block = not in_code_block
                elif in_code_block:
                    current_block.append(line)

            if not code_blocks:
                code_blocks = [llm_output]

            for block in code_blocks:
                if f'def test_{func_name}' in block:
                    try:
                        ast.parse(block)
                        
                        description = f"Test {func_name} function"
                        if '"""' in block or "'''" in block:
                            doc_match = block.split('"""')[1] if '"""' in block else block.split("'''")[1]
                            description = doc_match.strip()

                        return GeneratedTest(
                            test_name=f"test_{func_name}",
                            test_code=block.strip(),
                            target_function=func_name,
                            description=description
                        )
                    except SyntaxError:
                        logger.warning(
                            f"LLM generated invalid Python for {func_name}"
                        )
                        continue

            return None

        except Exception as e:
            logger.warning(f"Failed to parse LLM output: {e}")
            return None


def create_llm_test_generator(
    framework: str = "pytest",
    enable_llm: bool = True
) -> LLMTestGenerator:
    """
    Factory function to create LLMTestGenerator instance

    Args:
        framework: Test framework (pytest, unittest)
        enable_llm: Whether to enable LLM (False = heuristic only)

    Returns:
        LLMTestGenerator instance
    """
    return LLMTestGenerator(framework=framework, enable_llm=enable_llm)
