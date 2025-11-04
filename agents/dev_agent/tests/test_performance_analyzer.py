#!/usr/bin/env python3
"""
Tests for PerformanceAnalyzer
Priority 5: Performance Analysis
"""
import pytest
from performance import PerformanceAnalyzer, PerformanceIssue


class TestPerformanceAnalyzer:
    """Test suite for PerformanceAnalyzer functionality"""
    
    @pytest.fixture
    def analyzer(self):
        """Create PerformanceAnalyzer instance"""
        return PerformanceAnalyzer()
    
    def test_initialization(self, analyzer):
        """Test PerformanceAnalyzer initializes correctly"""
        assert analyzer is not None
    
    def test_analyze_simple_code(self, analyzer):
        """Test analysis of simple code without issues"""
        code = """
def simple_function():
    return 42
"""
        result = analyzer.analyze_code(code)
        
        assert result['success'] is True
        assert 'issues' in result
        assert isinstance(result['issues'], list)
    
    def test_detect_nested_loops_depth_2(self, analyzer):
        """Test detection of depth-2 nested loops"""
        code = """
def process_matrix(matrix):
    for row in matrix:
        for col in row:
            print(col)
"""
        result = analyzer.analyze_code(code)
        
        assert result['success'] is True
        assert len(result['issues']) == 0  # Depth 2 is acceptable
    
    def test_detect_nested_loops_depth_3(self, analyzer):
        """Test detection of depth-3 nested loops (should warn)"""
        code = """
def process_3d_array(arr):
    for x in arr:
        for y in x:
            for z in y:
                print(z)
"""
        result = analyzer.analyze_code(code)
        
        assert result['success'] is True
        assert 'issues' in result
        
        nested_loop_issues = [i for i in result['issues'] if i.issue_type == 'nested_loops']
        assert len(nested_loop_issues) > 0
        
        issue = nested_loop_issues[0]
        assert issue.severity == 'medium'
        assert '3' in issue.description or 'depth' in issue.description.lower()
    
    def test_detect_deeply_nested_loops(self, analyzer):
        """Test detection of deeply nested loops (depth > 3)"""
        code = """
def process_4d_array(arr):
    for w in arr:
        for x in w:
            for y in x:
                for z in y:
                    print(z)
"""
        result = analyzer.analyze_code(code)
        
        assert result['success'] is True
        nested_loop_issues = [i for i in result['issues'] if i.issue_type == 'nested_loops']
        assert len(nested_loop_issues) > 0
        
        issue = nested_loop_issues[0]
        assert 'depth' in issue.description.lower()
    
    def test_analyze_invalid_syntax(self, analyzer):
        """Test analysis of code with invalid syntax"""
        code = """
def broken_function(:
    return
"""
        result = analyzer.analyze_code(code)
        
        assert result['success'] is False
        assert 'error' in result
    
    def test_analyze_empty_code(self, analyzer):
        """Test analysis of empty code"""
        result = analyzer.analyze_code("")
        
        assert result['success'] is True
        assert result['issues'] == []
    
    def test_performance_issue_structure(self):
        """Test PerformanceIssue dataclass structure"""
        issue = PerformanceIssue(
            issue_type='test_issue',
            severity='high',
            description='Test description',
            location={'line': 10},
            suggestion='Test suggestion'
        )
        
        assert issue.issue_type == 'test_issue'
        assert issue.severity == 'high'
        assert issue.description == 'Test description'
        assert issue.location == {'line': 10}
        assert issue.suggestion == 'Test suggestion'
    
    def test_multiple_functions_with_loops(self, analyzer):
        """Test analysis of multiple functions with different loop patterns"""
        code = """
def simple_loop(items):
    for item in items:
        print(item)

def nested_loop(matrix):
    for row in matrix:
        for col in row:
            print(col)

def deep_nested(arr):
    for x in arr:
        for y in x:
            for z in y:
                for w in z:
                    print(w)
"""
        result = analyzer.analyze_code(code)
        
        assert result['success'] is True
        nested_issues = [i for i in result['issues'] if i.issue_type == 'nested_loops']
        assert len(nested_issues) > 0
    
    def test_loop_with_conditionals(self, analyzer):
        """Test that nested loops with conditionals are detected"""
        code = """
def process_with_conditions(data):
    for outer in data:
        if outer:
            for inner in outer:
                if inner:
                    for deep in inner:
                        print(deep)
"""
        result = analyzer.analyze_code(code)
        
        assert result['success'] is True
        nested_issues = [i for i in result['issues'] if i.issue_type == 'nested_loops']
        assert len(nested_issues) > 0
    
    def test_issue_location_information(self, analyzer):
        """Test that issues include location information"""
        code = """
def nested_function():
    for x in range(10):
        for y in range(10):
            for z in range(10):
                pass
"""
        result = analyzer.analyze_code(code)
        
        assert result['success'] is True
        if result['issues']:
            issue = result['issues'][0]
            assert 'location' in issue.__dict__
            assert isinstance(issue.location, dict)
            if 'line' in issue.location:
                assert isinstance(issue.location['line'], int)
    
    def test_severity_levels(self, analyzer):
        """Test that severity levels are appropriate"""
        code = """
def deep_nesting():
    for a in range(5):
        for b in range(5):
            for c in range(5):
                for d in range(5):
                    print(a, b, c, d)
"""
        result = analyzer.analyze_code(code)
        
        assert result['success'] is True
        if result['issues']:
            for issue in result['issues']:
                assert issue.severity in ['low', 'medium', 'high']
    
    def test_suggestions_provided(self, analyzer):
        """Test that issues include actionable suggestions"""
        code = """
def triple_nested():
    for i in range(10):
        for j in range(10):
            for k in range(10):
                print(i * j * k)
"""
        result = analyzer.analyze_code(code)
        
        assert result['success'] is True
        nested_issues = [i for i in result['issues'] if i.issue_type == 'nested_loops']
        
        if nested_issues:
            issue = nested_issues[0]
            assert issue.suggestion is not None
            assert len(issue.suggestion) > 0
            assert 'optimiz' in issue.suggestion.lower() or 'efficient' in issue.suggestion.lower()


class TestLoopDepthCalculation:
    """Test loop depth calculation logic"""
    
    def test_single_loop_depth(self):
        """Test calculation for single loop"""
        analyzer = PerformanceAnalyzer()
        code = """
for i in range(10):
    print(i)
"""
        result = analyzer.analyze_code(code)
        assert result['success'] is True
    
    def test_parallel_loops_not_nested(self):
        """Test that parallel loops are not considered nested"""
        analyzer = PerformanceAnalyzer()
        code = """
def parallel_loops():
    for i in range(10):
        print(i)
    
    for j in range(10):
        print(j)
"""
        result = analyzer.analyze_code(code)
        assert result['success'] is True
        nested_issues = [i for i in result['issues'] if i.issue_type == 'nested_loops']
        assert len(nested_issues) == 0
    
    def test_loop_in_different_scopes(self):
        """Test loops in different function scopes"""
        analyzer = PerformanceAnalyzer()
        code = """
def outer_function():
    for i in range(10):
        print(i)
    
    def inner_function():
        for j in range(10):
            print(j)
"""
        result = analyzer.analyze_code(code)
        assert result['success'] is True


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_none_code_input(self):
        """Test handling of None as code input"""
        analyzer = PerformanceAnalyzer()
        result = analyzer.analyze_code(None)
        
        assert result['success'] is False
        assert 'error' in result
    
    def test_very_large_code(self):
        """Test analysis of large code file"""
        analyzer = PerformanceAnalyzer()
        
        code = "def large_function():\n"
        code += "    x = 1\n" * 1000
        code += "    return x\n"
        
        result = analyzer.analyze_code(code)
        assert result['success'] is True
    
    def test_unicode_in_code(self):
        """Test handling of unicode characters in code"""
        analyzer = PerformanceAnalyzer()
        code = """
def unicode_function():
    message = "你好世界"  # Chinese characters
    for char in message:
        print(char)
"""
        result = analyzer.analyze_code(code)
        assert result['success'] is True
