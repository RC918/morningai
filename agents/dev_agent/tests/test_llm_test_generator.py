#!/usr/bin/env python3
"""
Unit tests for LLM-Enhanced Test Generator
Phase 2 Day 1-2: LLM Test Generator Tests
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from agents.dev_agent.testing.llm_test_generator import LLMTestGenerator, create_llm_test_generator
from agents.dev_agent.testing.test_generator import GeneratedTest


class TestLLMTestGenerator:
    """Test suite for LLMTestGenerator"""

    def test_initialization_with_api_key(self):
        """Test LLMTestGenerator initializes with API key"""
        generator = LLMTestGenerator(
            framework="pytest",
            openai_api_key="test-key",
            enable_llm=True
        )
        
        assert generator.framework == "pytest"
        assert generator.enable_llm is True
        assert generator.model == "gpt-4"
        assert generator.openai_client is not None

    def test_initialization_without_api_key_falls_back(self):
        """Test LLMTestGenerator falls back to heuristic mode without API key"""
        with patch('agents.dev_agent.testing.llm_test_generator.settings') as mock_settings:
            mock_settings.openai_api_key = None
            
            generator = LLMTestGenerator(
                framework="pytest",
                openai_api_key=None,
                enable_llm=True
            )
            
            assert generator.enable_llm is False
            assert generator.openai_client is None

    def test_initialization_with_llm_disabled(self):
        """Test LLMTestGenerator with LLM explicitly disabled"""
        generator = LLMTestGenerator(
            framework="pytest",
            enable_llm=False
        )
        
        assert generator.enable_llm is False
        assert generator.openai_client is None

    def test_generate_tests_with_syntax_error(self):
        """Test generate_tests handles syntax errors"""
        generator = LLMTestGenerator(enable_llm=False)
        
        invalid_code = "def invalid syntax here"
        result = generator.generate_tests(invalid_code, "test.py")
        
        assert result['success'] is False
        assert result['error']['error_code'] == 'DEV_015'
        assert result['error']['error_name'] == 'INVALID_INPUT'

    def test_generate_tests_heuristic_mode(self):
        """Test generate_tests works in heuristic mode"""
        generator = LLMTestGenerator(enable_llm=False)
        
        code = """
def calculate_sum(a, b):
    \"\"\"Calculate sum of two numbers\"\"\"
    return a + b

def get_user_name(user_id):
    \"\"\"Get user name by ID\"\"\"
    return "test_user"
"""
        
        result = generator.generate_tests(code, "calculator.py")
        
        assert result['success'] is True
        assert result['total_tests'] == 2
        assert result['llm_used'] is False
        assert 'test_calculate_sum' in result['test_code']
        assert 'test_get_user_name' in result['test_code']

    def test_generate_tests_skips_private_functions(self):
        """Test generate_tests skips private functions"""
        generator = LLMTestGenerator(enable_llm=False)
        
        code = """
def public_function():
    return True

def _private_function():
    return False

def __init__(self):
    pass
"""
        
        result = generator.generate_tests(code, "test.py")
        
        assert result['success'] is True
        assert result['total_tests'] == 1
        assert 'test_public_function' in result['test_code']
        assert 'test__private_function' not in result['test_code']
        assert 'test___init__' not in result['test_code']

    @patch('agents.dev_agent.testing.llm_test_generator.OpenAI')
    def test_generate_tests_with_llm_success(self, mock_openai_class):
        """Test generate_tests with successful LLM call"""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = """
```python
def test_calculate_sum():
    \"\"\"Test calculate_sum with positive numbers\"\"\"
    result = calculate_sum(2, 3)
    assert result == 5
    assert isinstance(result, int)
```
"""
        mock_client.chat.completions.create.return_value = mock_response
        
        generator = LLMTestGenerator(
            openai_api_key="test-key",
            enable_llm=True
        )
        
        code = """
def calculate_sum(a, b):
    \"\"\"Calculate sum of two numbers\"\"\"
    return a + b
"""
        
        result = generator.generate_tests(code, "calculator.py")
        
        assert result['success'] is True
        assert result['total_tests'] == 1
        assert result['llm_used'] is True
        assert 'test_calculate_sum' in result['test_code']
        assert 'assert result == 5' in result['test_code']

    @patch('agents.dev_agent.testing.llm_test_generator.OpenAI')
    def test_generate_tests_llm_fallback_on_error(self, mock_openai_class):
        """Test generate_tests falls back to heuristic when LLM fails"""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        
        generator = LLMTestGenerator(
            openai_api_key="test-key",
            enable_llm=True,
            max_retries=1
        )
        
        code = """
def calculate_sum(a, b):
    return a + b
"""
        
        result = generator.generate_tests(code, "calculator.py")
        
        assert result['success'] is True
        assert result['total_tests'] == 1
        assert 'test_calculate_sum' in result['test_code']

    @patch('agents.dev_agent.testing.llm_test_generator.OpenAI')
    def test_generate_tests_llm_invalid_output_fallback(self, mock_openai_class):
        """Test generate_tests falls back when LLM returns invalid output"""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "This is not valid Python code"
        mock_client.chat.completions.create.return_value = mock_response
        
        generator = LLMTestGenerator(
            openai_api_key="test-key",
            enable_llm=True,
            max_retries=1
        )
        
        code = """
def calculate_sum(a, b):
    return a + b
"""
        
        result = generator.generate_tests(code, "calculator.py")
        
        assert result['success'] is True
        assert result['total_tests'] == 1

    def test_extract_function_source(self):
        """Test _extract_function_source extracts function code"""
        generator = LLMTestGenerator(enable_llm=False)
        
        code = """
def first_function():
    return 1

def second_function():
    return 2
"""
        
        import ast
        tree = ast.parse(code)
        func_node = None
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "second_function":
                func_node = node
                break
        
        assert func_node is not None
        
        extracted = generator._extract_function_source(func_node, code)
        
        assert "def second_function():" in extracted
        assert "return 2" in extracted

    def test_parse_llm_test_output_with_code_blocks(self):
        """Test _parse_llm_test_output parses markdown code blocks"""
        generator = LLMTestGenerator(enable_llm=False)
        
        llm_output = """
Here's the test:

```python
def test_my_function():
    \"\"\"Test my_function with valid input\"\"\"
    result = my_function(42)
    assert result == 42
```

This test covers the basic case.
"""
        
        test = generator._parse_llm_test_output(llm_output, "my_function")
        
        assert test is not None
        assert test.test_name == "test_my_function"
        assert test.target_function == "my_function"
        assert "assert result == 42" in test.test_code

    def test_parse_llm_test_output_without_code_blocks(self):
        """Test _parse_llm_test_output parses plain code"""
        generator = LLMTestGenerator(enable_llm=False)
        
        llm_output = """
def test_my_function():
    \"\"\"Test my_function\"\"\"
    result = my_function(42)
    assert result == 42
"""
        
        test = generator._parse_llm_test_output(llm_output, "my_function")
        
        assert test is not None
        assert test.test_name == "test_my_function"
        assert "assert result == 42" in test.test_code

    def test_parse_llm_test_output_invalid_syntax(self):
        """Test _parse_llm_test_output returns None for invalid syntax"""
        generator = LLMTestGenerator(enable_llm=False)
        
        llm_output = """
def test_my_function():
    invalid syntax here
"""
        
        test = generator._parse_llm_test_output(llm_output, "my_function")
        
        assert test is None

    def test_build_test_generation_prompt_pytest(self):
        """Test _build_test_generation_prompt for pytest"""
        generator = LLMTestGenerator(framework="pytest", enable_llm=False)
        
        prompt = generator._build_test_generation_prompt(
            "calculate_sum",
            "def calculate_sum(a, b):\n    return a + b",
            "calculator.py"
        )
        
        assert "calculate_sum" in prompt
        assert "pytest" in prompt
        assert "calculator.py" in prompt
        assert "test_calculate_sum" in prompt

    def test_build_test_generation_prompt_unittest(self):
        """Test _build_test_generation_prompt for unittest"""
        generator = LLMTestGenerator(framework="unittest", enable_llm=False)
        
        prompt = generator._build_test_generation_prompt(
            "calculate_sum",
            "def calculate_sum(a, b):\n    return a + b",
            "calculator.py"
        )
        
        assert "calculate_sum" in prompt
        assert "unittest" in prompt
        assert "self.assertEqual" in prompt

    def test_factory_function(self):
        """Test create_llm_test_generator factory function"""
        generator = create_llm_test_generator(framework="pytest", enable_llm=False)
        
        assert isinstance(generator, LLMTestGenerator)
        assert generator.framework == "pytest"
        assert generator.enable_llm is False

    @patch('agents.dev_agent.testing.llm_test_generator.OpenAI')
    def test_llm_retry_mechanism(self, mock_openai_class):
        """Test LLM retries on failure"""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = """
```python
def test_my_func():
    \"\"\"Test my_func\"\"\"
    assert my_func() is not None
```
"""
        
        mock_client.chat.completions.create.side_effect = [
            Exception("First attempt fails"),
            mock_response
        ]
        
        generator = LLMTestGenerator(
            openai_api_key="test-key",
            enable_llm=True,
            max_retries=2
        )
        
        code = "def my_func():\n    return True"
        result = generator.generate_tests(code, "test.py")
        
        assert result['success'] is True
        assert mock_client.chat.completions.create.call_count == 2

    def test_generate_tests_multiple_functions(self):
        """Test generate_tests handles multiple functions"""
        generator = LLMTestGenerator(enable_llm=False)
        
        code = """
def func_one():
    return 1

def func_two():
    return 2

def func_three():
    return 3
"""
        
        result = generator.generate_tests(code, "multi.py")
        
        assert result['success'] is True
        assert result['total_tests'] == 3
        assert 'test_func_one' in result['test_code']
        assert 'test_func_two' in result['test_code']
        assert 'test_func_three' in result['test_code']

    def test_generate_tests_async_functions(self):
        """Test generate_tests handles async functions"""
        generator = LLMTestGenerator(enable_llm=False)
        
        code = """
async def async_fetch_data():
    return {"data": "value"}
"""
        
        result = generator.generate_tests(code, "async_test.py")
        
        assert result['success'] is True
        assert result['total_tests'] == 1
        assert 'test_async_fetch_data' in result['test_code']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
