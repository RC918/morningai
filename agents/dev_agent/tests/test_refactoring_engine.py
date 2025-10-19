#!/usr/bin/env python3
"""
Tests for Refactoring Engine
"""
import pytest
from agents.dev_agent.refactoring import (
    create_refactoring_engine,
    RefactoringType
)


class TestRefactoringEngine:
    """Test Refactoring Engine functionality"""

    @pytest.fixture
    def engine(self):
        """Create refactoring engine instance"""
        return create_refactoring_engine(
            max_function_lines=20,
            max_complexity=5,
            min_duplication_length=3
        )

    def test_engine_initialization(self, engine):
        """Test engine initializes correctly"""
        assert engine is not None
        assert engine.max_function_lines == 20
        assert engine.max_complexity == 5
        assert engine.min_duplication_length == 3

        print("✓ Refactoring engine initialized")

    def test_detect_long_function(self, engine):
        """Test detection of long functions"""
        long_code = """
def long_function():
    line1 = 1
    line2 = 2
    line3 = 3
    line4 = 4
    line5 = 5
    line6 = 6
    line7 = 7
    line8 = 8
    line9 = 9
    line10 = 10
    line11 = 11
    line12 = 12
    line13 = 13
    line14 = 14
    line15 = 15
    line16 = 16
    line17 = 17
    line18 = 18
    line19 = 19
    line20 = 20
    line21 = 21
    line22 = 22
    return line22
"""
        result = engine.analyze_code(long_code)

        assert result['success'] is True
        assert result['total_suggestions'] > 0

        extract_suggestions = [
            s for s in result['suggestions']
            if s['type'] == RefactoringType.EXTRACT_METHOD.value
        ]

        assert len(extract_suggestions) > 0
        assert 'long_function' in extract_suggestions[0]['description']

        print("✓ Long function detected")

    def test_detect_high_complexity(self, engine):
        """Test detection of high complexity functions"""
        complex_code = """
def complex_function(x, y, z):
    if x > 0:
        if y > 0:
            if z > 0:
                if x > y:
                    if y > z:
                        if z > 1:
                            return x + y + z
    return 0
"""
        result = engine.analyze_code(complex_code)

        assert result['success'] is True

        complexity_suggestions = [
            s for s in result['suggestions']
            if s['type'] == RefactoringType.REDUCE_COMPLEXITY.value
        ]

        assert len(complexity_suggestions) > 0
        assert 'complexity' in complexity_suggestions[0]['description'].lower()

        print("✓ High complexity detected")

    def test_detect_code_duplication(self, engine):
        """Test detection of code duplication"""
        duplicated_code = """
def function1():
    x = 1
    y = 2
    z = x + y
    return z

def function2():
    x = 1
    y = 2
    z = x + y
    return z * 2
"""
        result = engine.analyze_code(duplicated_code)

        assert result['success'] is True

        duplication_suggestions = [
            s for s in result['suggestions']
            if s['type'] == RefactoringType.REMOVE_DUPLICATION.value
        ]

        assert len(duplication_suggestions) > 0

        print("✓ Code duplication detected")

    def test_detect_naming_violations(self, engine):
        """Test detection of naming convention violations"""
        bad_naming_code = """
def BadFunctionName():
    pass

class bad_class_name:
    pass
"""
        result = engine.analyze_code(bad_naming_code)

        assert result['success'] is True

        naming_suggestions = [
            s for s in result['suggestions']
            if s['type'] == RefactoringType.IMPROVE_NAMING.value
        ]

        assert len(naming_suggestions) > 0

        print("✓ Naming violations detected")

    def test_detect_missing_type_hints(self, engine):
        """Test detection of missing type hints"""
        no_hints_code = """
def add(a, b):
    return a + b

def greet(name):
    print(f"Hello {name}")
"""
        result = engine.analyze_code(no_hints_code)

        assert result['success'] is True

        hint_suggestions = [
            s for s in result['suggestions']
            if s['type'] == RefactoringType.ADD_TYPE_HINTS.value
        ]

        assert len(hint_suggestions) > 0

        print("✓ Missing type hints detected")

    def test_analyze_clean_code(self, engine):
        """Test analyzing clean, well-structured code"""
        clean_code = """
def calculate_sum(numbers: list[int]) -> int:
    '''Calculate sum of numbers.'''
    return sum(numbers)

class Calculator:
    '''Simple calculator class.'''
    
    def add(self, a: int, b: int) -> int:
        '''Add two numbers.'''
        return a + b
"""
        result = engine.analyze_code(clean_code)

        assert result['success'] is True

        print(f"✓ Clean code analyzed: {result['total_suggestions']} minor suggestions")

    def test_apply_naming_refactoring(self, engine):
        """Test applying a naming refactoring"""
        code = "def BadName():\n    pass"

        result = engine.analyze_code(code)
        assert result['success'] is True

        suggestions = [
            s for s in result['suggestions']
            if s['type'] == RefactoringType.IMPROVE_NAMING.value
        ]

        if suggestions:
            suggestion_dict = suggestions[0]

            from agents.dev_agent.refactoring import RefactoringSuggestion
            suggestion = RefactoringSuggestion(
                type=RefactoringType.IMPROVE_NAMING,
                severity=suggestion_dict['severity'],
                description=suggestion_dict['description'],
                location=suggestion_dict['location'],
                code_snippet=suggestion_dict['code_snippet'],
                suggested_code=suggestion_dict.get('suggested_code')
            )

            if suggestion.suggested_code:
                refactor_result = engine.apply_refactoring(code, suggestion)
                assert refactor_result['success'] is True

                print("✓ Naming refactoring applied")

    def test_verify_refactoring(self, engine):
        """Test refactoring verification"""
        original = """
def calculate(x, y):
    return x + y
"""

        refactored = """
def calculate(x, y):
    result = x + y
    return result
"""

        result = engine.verify_refactoring(original, refactored)

        assert result['success'] is True
        assert result['syntax_valid'] is True
        assert result['functions_preserved'] is True

        print("✓ Refactoring verified")

    def test_syntax_error_handling(self, engine):
        """Test handling of syntax errors"""
        invalid_code = "def bad syntax here"

        result = engine.analyze_code(invalid_code)

        assert result['success'] is False
        assert 'error' in result

        print("✓ Syntax error handled gracefully")

    def test_metrics_reporting(self, engine):
        """Test that metrics are reported correctly"""
        code = """
class MyClass:
    def method1(self):
        pass
    
    def method2(self):
        pass

def standalone_function():
    pass
"""

        result = engine.analyze_code(code)

        assert result['success'] is True
        assert 'metrics' in result
        assert result['metrics']['total_functions'] == 3
        assert result['metrics']['total_classes'] == 1
        assert result['metrics']['lines_of_code'] > 0

        print("✓ Metrics reported correctly")


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("Refactoring Engine Tests")
    print("=" * 70 + "\n")

    pytest.main([__file__, '-v', '--tb=short', '-s'])
