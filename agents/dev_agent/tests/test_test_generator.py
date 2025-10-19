#!/usr/bin/env python3
"""
Tests for Test Generator
"""
import pytest
from testing import create_test_generator


class TestTestGenerator:
    """Test Test Generator functionality"""

    @pytest.fixture
    def generator(self):
        """Create test generator instance"""
        return create_test_generator(framework="pytest")

    def test_generator_initialization(self, generator):
        """Test generator initializes correctly"""
        assert generator is not None
        assert generator.framework == "pytest"

        print("✓ Test generator initialized")

    def test_generate_tests_for_simple_function(self, generator):
        """Test generating tests for a simple function"""
        code = """
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b
"""
        result = generator.generate_tests(code)

        assert result['success'] is True
        assert result['total_tests'] == 2
        assert 'test_code' in result
        assert 'test_add' in result['test_code']
        assert 'test_subtract' in result['test_code']

        print("✓ Tests generated for simple functions")

    def test_generate_tests_for_class_methods(self, generator):
        """Test generating tests for class methods"""
        code = """
class Calculator:
    def add(self, a, b):
        return a + b
    
    def multiply(self, a, b):
        return a * b
"""
        result = generator.generate_tests(code)

        assert result['success'] is True
        assert result['total_tests'] == 2

        print("✓ Tests generated for class methods")

    def test_skip_private_functions(self, generator):
        """Test that private functions are skipped"""
        code = """
def _private_function():
    pass

def public_function():
    pass
"""
        result = generator.generate_tests(code)

        assert result['success'] is True
        assert result['total_tests'] == 1
        assert 'test_public_function' in result['test_code']
        assert 'test__private_function' not in result['test_code']

        print("✓ Private functions skipped")

    def test_handle_syntax_error(self, generator):
        """Test handling of syntax errors"""
        invalid_code = "def bad syntax"

        result = generator.generate_tests(invalid_code)

        assert result['success'] is False
        assert 'error' in result

        print("✓ Syntax errors handled gracefully")


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("Test Generator Tests")
    print("=" * 70 + "\n")

    pytest.main([__file__, '-v', '--tb=short', '-s'])
