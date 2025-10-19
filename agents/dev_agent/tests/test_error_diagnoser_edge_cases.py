#!/usr/bin/env python3
"""
Edge Case Tests for ErrorDiagnoser
Comprehensive boundary and edge case testing
"""
import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from error_diagnosis import ErrorDiagnoser, FixSuggestion


class TestErrorDiagnoserEdgeCases:
    """Edge case tests for ErrorDiagnoser"""
    
    @pytest.fixture
    def diagnoser(self):
        return ErrorDiagnoser()
    
    def test_null_input(self, diagnoser):
        """Test handling of None error message"""
        result = diagnoser.diagnose_error(None)
        
        assert result['success'] is True
        assert result['error_type'] == 'Unknown'
        assert result['total_suggestions'] == 0
    
    def test_empty_string(self, diagnoser):
        """Test handling of empty string error message"""
        result = diagnoser.diagnose_error("")
        
        assert result['success'] is True
        assert result['error_type'] == 'Unknown'
        assert result['total_suggestions'] == 0
    
    def test_whitespace_only(self, diagnoser):
        """Test handling of whitespace-only error message"""
        result = diagnoser.diagnose_error("   \t\n   ")
        
        assert result['success'] is True
    
    def test_very_long_error_message(self, diagnoser):
        """Test handling of extremely long error message"""
        long_error = "KeyError: " + "a" * 10000
        
        result = diagnoser.diagnose_error(long_error)
        
        assert result['success'] is True
        assert result['error_type'] == 'KeyError'
    
    def test_malformed_error_message(self, diagnoser):
        """Test handling of malformed error messages"""
        malformed_errors = [
            "Error without type information",
            "!!!Invalid!!!",
            "123456789",
            "Error: but no type",
            "@#$%^&*()",
        ]
        
        for error_msg in malformed_errors:
            result = diagnoser.diagnose_error(error_msg)
            assert result['success'] is True
    
    def test_multiple_error_types_in_message(self, diagnoser):
        """Test error message containing multiple error types"""
        error_msg = "KeyError: 'missing_key' caused by AttributeError: 'NoneType' object has no attribute 'get'"
        
        result = diagnoser.diagnose_error(error_msg)
        
        assert result['success'] is True
        assert result['error_type'] in ['KeyError', 'AttributeError']
    
    def test_unicode_in_error_message(self, diagnoser):
        """Test handling of unicode characters in error message"""
        unicode_errors = [
            "KeyError: '用戶名'",
            "ValueError: 無効な値",
            "TypeError: Тип не поддерживается",
            "AttributeError: '对象' has no attribute 'método'",
        ]
        
        for error_msg in unicode_errors:
            result = diagnoser.diagnose_error(error_msg)
            assert result['success'] is True
    
    def test_error_with_code_context(self, diagnoser):
        """Test error diagnosis with code context provided"""
        error_msg = "KeyError: 'user_id'"
        code_context = """
def get_user(data):
    return data['user_id']
"""
        
        result = diagnoser.diagnose_error(error_msg, code_context)
        
        assert result['success'] is True
        assert result['error_type'] == 'KeyError'
        assert len(result['suggestions']) > 0
    
    def test_error_with_very_long_code_context(self, diagnoser):
        """Test error diagnosis with extremely long code context"""
        error_msg = "AttributeError: 'NoneType' object has no attribute 'value'"
        long_context = "def func():\n" + "    x = 1\n" * 1000
        
        result = diagnoser.diagnose_error(error_msg, long_context)
        
        assert result['success'] is True
        assert result['error_type'] == 'AttributeError'
    
    def test_case_sensitivity(self, diagnoser):
        """Test that error matching is case-insensitive"""
        variations = [
            "keyerror: 'test'",
            "KEYERROR: 'test'",
            "KeyError: 'test'",
            "kEyErRoR: 'test'",
        ]
        
        for error_msg in variations:
            result = diagnoser.diagnose_error(error_msg)
            assert result['success'] is True
            assert result['error_type'] == 'KeyError'
    
    def test_special_characters_in_key_names(self, diagnoser):
        """Test handling of special characters in error messages"""
        special_char_errors = [
            "KeyError: 'user-id'",
            "KeyError: 'user_name'",
            "KeyError: 'user.email'",
            "KeyError: 'user[0]'",
            "AttributeError: '__init__'",
        ]
        
        for error_msg in special_char_errors:
            result = diagnoser.diagnose_error(error_msg)
            assert result['success'] is True
    
    def test_nested_error_traces(self, diagnoser):
        """Test handling of nested error traces"""
        nested_error = """
Traceback (most recent call last):
  File "test.py", line 10, in process
    result = data['user_id']
KeyError: 'user_id'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "test.py", line 15, in main
    process(None)
AttributeError: 'NoneType' object has no attribute 'keys'
"""
        
        result = diagnoser.diagnose_error(nested_error)
        
        assert result['success'] is True
        assert result['error_type'] in ['KeyError', 'AttributeError']
    
    def test_concurrent_diagnoses(self, diagnoser):
        """Test that multiple diagnoses don't interfere with each other"""
        errors = [
            "KeyError: 'key1'",
            "ValueError: invalid value",
            "TypeError: unsupported type",
            "IndexError: list index out of range",
        ]
        
        results = [diagnoser.diagnose_error(err) for err in errors]
        
        assert all(r['success'] for r in results)
        assert len(set(r['error_type'] for r in results)) == 4
    
    def test_suggestion_structure_integrity(self, diagnoser):
        """Test that all suggestions maintain proper structure"""
        error_msg = "KeyError: 'missing_key'"
        
        result = diagnoser.diagnose_error(error_msg)
        
        assert result['success'] is True
        for suggestion in result['suggestions']:
            assert isinstance(suggestion, FixSuggestion)
            assert hasattr(suggestion, 'error_type')
            assert hasattr(suggestion, 'description')
            assert hasattr(suggestion, 'suggested_fix')
            assert hasattr(suggestion, 'confidence')
            assert 0 <= suggestion.confidence <= 1
    
    def test_all_error_patterns_have_examples(self, diagnoser):
        """Test that all error patterns have code examples"""
        for error_type, pattern_info in diagnoser.error_patterns.items():
            assert 'code_examples' in pattern_info
            assert isinstance(pattern_info['code_examples'], list)
            assert len(pattern_info['code_examples']) > 0
    
    def test_error_pattern_regex_validity(self, diagnoser):
        """Test that all error patterns have valid regex"""
        import re
        
        for error_type, pattern_info in diagnoser.error_patterns.items():
            try:
                re.compile(pattern_info['pattern'])
            except re.error:
                pytest.fail(f"Invalid regex pattern for {error_type}")
    
    def test_json_serializable_output(self, diagnoser):
        """Test that output is JSON serializable"""
        import json
        
        error_msg = "KeyError: 'test'"
        result = diagnoser.diagnose_error(error_msg)
        
        result_copy = result.copy()
        result_copy['suggestions'] = [
            {
                'error_type': s.error_type,
                'description': s.description,
                'suggested_fix': s.suggested_fix,
                'confidence': s.confidence
            }
            for s in result['suggestions']
        ]
        
        try:
            json.dumps(result_copy)
        except (TypeError, ValueError) as e:
            pytest.fail(f"Result is not JSON serializable: {e}")
    
    def test_error_with_numeric_values(self, diagnoser):
        """Test handling of errors with numeric values"""
        numeric_errors = [
            "IndexError: list index 999 out of range",
            "ValueError: invalid literal for int() with base 10: '999999999999'",
            "ZeroDivisionError: division by zero (denominator: 0)",
        ]
        
        for error_msg in numeric_errors:
            result = diagnoser.diagnose_error(error_msg)
            assert result['success'] is True
    
    def test_error_with_file_paths(self, diagnoser):
        """Test handling of errors with file paths"""
        path_errors = [
            "FileNotFoundError: /very/long/path/to/missing/file.txt",
            "FileNotFoundError: C:\\Users\\Test\\Documents\\file.txt",
            "PermissionError: /etc/protected/file.conf",
        ]
        
        for error_msg in path_errors:
            result = diagnoser.diagnose_error(error_msg)
            assert result['success'] is True
    
    def test_memory_efficiency_large_batch(self, diagnoser):
        """Test memory efficiency with large batch of diagnoses"""
        errors = [f"KeyError: 'key_{i}'" for i in range(1000)]
        
        results = []
        for error in errors:
            result = diagnoser.diagnose_error(error)
            results.append(result)
        
        assert len(results) == 1000
        assert all(r['success'] for r in results)
    
    def test_error_type_consistency(self, diagnoser):
        """Test that same error type always returns consistent results"""
        error_msg = "KeyError: 'test_key'"
        
        results = [diagnoser.diagnose_error(error_msg) for _ in range(10)]
        
        assert all(r['error_type'] == results[0]['error_type'] for r in results)
        assert all(len(r['suggestions']) == len(results[0]['suggestions']) for r in results)


class TestErrorDiagnoserStressTests:
    """Stress tests for ErrorDiagnoser"""
    
    @pytest.fixture
    def diagnoser(self):
        return ErrorDiagnoser()
    
    @pytest.mark.benchmark
    def test_performance_single_diagnosis(self, diagnoser):
        """Test performance of single error diagnosis"""
        import time
        
        error_msg = "KeyError: 'test'"
        
        start = time.time()
        for _ in range(100):
            diagnoser.diagnose_error(error_msg)
        elapsed = (time.time() - start) * 1000
        
        avg_time = elapsed / 100
        assert avg_time < 10, f"Average diagnosis time {avg_time:.2f}ms exceeds 10ms"
    
    @pytest.mark.benchmark
    def test_performance_different_error_types(self, diagnoser):
        """Test performance across different error types"""
        import time
        
        errors = [
            "KeyError: 'key'",
            "ValueError: invalid value",
            "TypeError: wrong type",
            "AttributeError: no attribute",
            "IndexError: out of range",
        ]
        
        start = time.time()
        for _ in range(20):
            for error in errors:
                diagnoser.diagnose_error(error)
        elapsed = (time.time() - start) * 1000
        
        total_diagnoses = 20 * len(errors)
        avg_time = elapsed / total_diagnoses
        assert avg_time < 10, f"Average diagnosis time {avg_time:.2f}ms exceeds 10ms"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
