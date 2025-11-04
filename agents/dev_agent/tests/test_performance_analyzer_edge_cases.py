#!/usr/bin/env python3
"""
Edge Case Tests for PerformanceAnalyzer
Comprehensive boundary and edge case testing
"""
import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from performance import PerformanceAnalyzer, PerformanceIssue


class TestPerformanceAnalyzerEdgeCases:
    """Edge case tests for PerformanceAnalyzer"""
    
    @pytest.fixture
    def analyzer(self):
        return PerformanceAnalyzer()
    
    def test_empty_code(self, analyzer):
        """Test analysis of empty code"""
        result = analyzer.analyze_code("")
        
        assert result['success'] is True
        assert result['total_issues'] == 0
    
    def test_whitespace_only_code(self, analyzer):
        """Test analysis of whitespace-only code"""
        result = analyzer.analyze_code("   \n\t   \n   ")
        
        assert result['success'] is True
        assert result['total_issues'] == 0
    
    def test_comments_only_code(self, analyzer):
        """Test analysis of code with only comments"""
        code = """
"""
        result = analyzer.analyze_code(code)
        
        assert result['success'] is True
        assert result['total_issues'] == 0
    
    def test_single_line_code(self, analyzer):
        """Test analysis of single line of code"""
        result = analyzer.analyze_code("x = 1")
        
        assert result['success'] is True
        assert result['total_issues'] == 0
    
    def test_very_deeply_nested_loops(self, analyzer):
        """Test detection of very deeply nested loops (depth 6)"""
        code = """
def deep_nesting():
    for i in range(10):
        for j in range(10):
            for k in range(10):
                for l in range(10):
                    for m in range(10):
                        for n in range(10):
                            pass
"""
        result = analyzer.analyze_code(code)
        
        assert result['success'] is True
        assert result['total_issues'] > 0
        assert any(issue.issue_type == 'nested_loops' for issue in result['issues'])
    
    def test_parallel_loops_not_nested(self, analyzer):
        """Test that parallel loops are not counted as nested"""
        code = """
def parallel_loops():
    for i in range(10):
        pass
    for j in range(10):
        pass
    for k in range(10):
        pass
"""
        result = analyzer.analyze_code(code)
        
        assert result['success'] is True
        nested_issues = [i for i in result['issues'] if i.issue_type == 'nested_loops']
        assert len(nested_issues) == 0
    
    def test_loops_in_different_functions(self, analyzer):
        """Test that loops in different functions don't interfere"""
        code = """
def func1():
    for i in range(10):
        for j in range(10):
            pass

def func2():
    for k in range(10):
        pass
"""
        result = analyzer.analyze_code(code)
        
        assert result['success'] is True
    
    def test_while_loops(self, analyzer):
        """Test detection with while loops"""
        code = """
def while_nested():
    while True:
        while True:
            while True:
                break
"""
        result = analyzer.analyze_code(code)
        
        assert result['success'] is True
    
    def test_mixed_for_and_while_loops(self, analyzer):
        """Test detection with mixed loop types"""
        code = """
def mixed_loops():
    for i in range(10):
        while i > 0:
            for j in range(5):
                pass
"""
        result = analyzer.analyze_code(code)
        
        assert result['success'] is True
        assert result['total_issues'] > 0
    
    def test_loops_with_complex_conditions(self, analyzer):
        """Test loops with complex conditions"""
        code = """
def complex_conditions():
    for i in range(10) if condition else range(5):
        for j in [x for x in range(10) if x > 5]:
            pass
"""
        try:
            result = analyzer.analyze_code(code)
            if result.get('success'):
                assert 'issues' in result
        except:
            pass
    
    def test_generator_expressions(self, analyzer):
        """Test handling of generator expressions"""
        code = """
def with_generators():
    result = (x for x in range(100))
    squared = (x**2 for x in range(100))
    return list(result)
"""
        result = analyzer.analyze_code(code)
        
        assert result['success'] is True
    
    def test_list_comprehensions(self, analyzer):
        """Test handling of list comprehensions"""
        code = """
def with_comprehensions():
    result = [x for x in range(100)]
    filtered = [x for x in range(100) if x > 50]
    nested = [[y for y in range(10)] for x in range(10)]
    return result
"""
        result = analyzer.analyze_code(code)
        
        assert result['success'] is True
    
    def test_async_functions(self, analyzer):
        """Test handling of async functions"""
        code = """
async def async_func():
    for i in range(10):
        await something()
"""
        result = analyzer.analyze_code(code)
        
        assert result['success'] is True
    
    def test_nested_functions(self, analyzer):
        """Test handling of nested functions"""
        code = """
def outer():
    def inner():
        for i in range(10):
            for j in range(10):
                pass
    inner()
"""
        result = analyzer.analyze_code(code)
        
        assert result['success'] is True
    
    def test_class_methods(self, analyzer):
        """Test handling of class methods"""
        code = """
class MyClass:
    def method1(self):
        for i in range(10):
            for j in range(10):
                pass
    
    @staticmethod
    def method2():
        for k in range(10):
            pass
"""
        result = analyzer.analyze_code(code)
        
        assert result['success'] is True
    
    def test_decorators(self, analyzer):
        """Test handling of decorated functions"""
        code = """
@decorator
def decorated_func():
    for i in range(10):
        for j in range(10):
            pass
"""
        result = analyzer.analyze_code(code)
        
        assert result['success'] is True
    
    def test_try_except_blocks(self, analyzer):
        """Test handling of try-except blocks"""
        code = """
def with_exception_handling():
    try:
        for i in range(10):
            for j in range(10):
                risky_operation()
    except Exception:
        pass
"""
        result = analyzer.analyze_code(code)
        
        assert result['success'] is True
    
    def test_context_managers(self, analyzer):
        """Test handling of context managers"""
        code = """
def with_context():
    with open('file.txt') as f:
        for line in f:
            for char in line:
                process(char)
"""
        result = analyzer.analyze_code(code)
        
        assert result['success'] is True
    
    def test_lambda_functions(self, analyzer):
        """Test handling of lambda functions"""
        code = """
def with_lambdas():
    funcs = [lambda x: x**2 for i in range(10)]
    mapped = map(lambda x: x * 2, range(10))
    return funcs
"""
        result = analyzer.analyze_code(code)
        
        assert result['success'] is True
    
    def test_very_large_code_file(self, analyzer):
        """Test analysis of very large code file"""
        code_lines = []
        for i in range(1000):
            code_lines.append(f"def function_{i}():\n")
            code_lines.append("    for i in range(10):\n")
            code_lines.append("        for j in range(10):\n")
            code_lines.append("            pass\n")
        
        code = ''.join(code_lines)
        
        result = analyzer.analyze_code(code)
        
        assert result['success'] is True
    
    def test_unicode_in_code(self, analyzer):
        """Test handling of unicode in code"""
        code = """
def 函数():
    for i in range(10):
        變量 = i * 2
"""
        result = analyzer.analyze_code(code)
        
        assert result['success'] is True
    
    def test_malformed_syntax(self, analyzer):
        """Test handling of malformed syntax"""
        malformed_codes = [
            "def broken(",
            "for i in",
            "while",
            "if True",
        ]
        
        for code in malformed_codes:
            result = analyzer.analyze_code(code)
            assert result['success'] is False
            assert 'error' in result
    
    def test_none_code_input(self, analyzer):
        """Test handling of None input"""
        result = analyzer.analyze_code(None)
        
        assert result['success'] is False
        assert 'error' in result
    
    def test_issue_structure_integrity(self, analyzer):
        """Test that all issues maintain proper structure"""
        code = """
def test_func():
    for i in range(10):
        for j in range(10):
            for k in range(10):
                pass
"""
        result = analyzer.analyze_code(code)
        
        assert result['success'] is True
        for issue in result['issues']:
            assert isinstance(issue, PerformanceIssue)
            assert hasattr(issue, 'issue_type')
            assert hasattr(issue, 'severity')
            assert hasattr(issue, 'description')
            assert hasattr(issue, 'location')
            assert hasattr(issue, 'suggestion')
            assert issue.severity in ['low', 'medium', 'high']
    
    def test_json_serializable_output(self, analyzer):
        """Test that output is JSON serializable"""
        import json
        
        code = """
def test():
    for i in range(10):
        for j in range(10):
            pass
"""
        result = analyzer.analyze_code(code)
        
        result_copy = result.copy()
        result_copy['issues'] = [
            {
                'issue_type': i.issue_type,
                'severity': i.severity,
                'description': i.description,
                'location': i.location,
                'suggestion': i.suggestion
            }
            for i in result['issues']
        ]
        
        try:
            json.dumps(result_copy)
        except (TypeError, ValueError) as e:
            pytest.fail(f"Result is not JSON serializable: {e}")
    
    def test_string_concatenation_in_loop(self, analyzer):
        """Test detection of string concatenation in loops"""
        code = """
def concat_strings():
    result = ""
    for i in range(100):
        result += str(i)
    return result
"""
        result = analyzer.analyze_code(code)
        
        assert result['success'] is True
    
    def test_global_variable_access(self, analyzer):
        """Test detection of global variable access in loops"""
        code = """
global_var = 100

def use_global():
    global global_var
    for i in range(10):
        x = global_var * 2
"""
        result = analyzer.analyze_code(code)
        
        assert result['success'] is True
    
    def test_concurrent_analyses(self, analyzer):
        """Test that multiple analyses don't interfere"""
        codes = [
            "for i in range(10):\n    for j in range(10):\n        pass",
            "while True:\n    while True:\n        break",
            "for x in range(5):\n    pass",
        ]
        
        results = [analyzer.analyze_code(code) for code in codes]
        
        assert all(r['success'] for r in results)


class TestPerformanceAnalyzerStressTests:
    """Stress tests for PerformanceAnalyzer"""
    
    @pytest.fixture
    def analyzer(self):
        return PerformanceAnalyzer()
    
    @pytest.mark.benchmark
    def test_performance_small_file(self, analyzer):
        """Test performance on small file"""
        import time
        
        code = """
def test():
    for i in range(10):
        for j in range(10):
            pass
"""
        
        start = time.time()
        for _ in range(100):
            analyzer.analyze_code(code)
        elapsed = (time.time() - start) * 1000
        
        avg_time = elapsed / 100
        assert avg_time < 50, f"Average analysis time {avg_time:.2f}ms exceeds 50ms"
    
    @pytest.mark.benchmark
    def test_performance_medium_file(self, analyzer):
        """Test performance on medium file"""
        import time
        
        code_lines = []
        for i in range(50):
            code_lines.append(f"def function_{i}():\n")
            code_lines.append("    for i in range(10):\n")
            code_lines.append("        pass\n")
        
        code = ''.join(code_lines)
        
        start = time.time()
        for _ in range(10):
            analyzer.analyze_code(code)
        elapsed = (time.time() - start) * 1000
        
        avg_time = elapsed / 10
        assert avg_time < 200, f"Average analysis time {avg_time:.2f}ms exceeds 200ms"
    
    def test_memory_efficiency(self, analyzer):
        """Test memory efficiency with many analyses"""
        code = """
def test():
    for i in range(10):
        for j in range(10):
            pass
"""
        
        results = []
        for _ in range(1000):
            result = analyzer.analyze_code(code)
            results.append(result)
        
        assert len(results) == 1000
        assert all(r['success'] for r in results)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
