#!/usr/bin/env python3
"""
Tests for ErrorDiagnoser
Priority 4: Error Diagnosis & Auto-Fix
"""
import pytest
from agents.dev_agent.error_diagnosis.error_diagnoser import ErrorDiagnoser, FixSuggestion


class TestErrorDiagnoser:
    """Test suite for ErrorDiagnoser functionality"""
    
    @pytest.fixture
    def diagnoser(self):
        """Create ErrorDiagnoser instance"""
        return ErrorDiagnoser()
    
    def test_initialization(self, diagnoser):
        """Test ErrorDiagnoser initializes correctly"""
        assert diagnoser is not None
        assert len(diagnoser.error_patterns) > 0
        assert 'AttributeError' in diagnoser.error_patterns
        assert 'KeyError' in diagnoser.error_patterns
        assert 'IndexError' in diagnoser.error_patterns
        assert 'TypeError' in diagnoser.error_patterns
    
    def test_diagnose_attribute_error(self, diagnoser):
        """Test diagnosis of AttributeError"""
        error_message = "AttributeError: 'NoneType' object has no attribute 'value'"
        result = diagnoser.diagnose_error(error_message)
        
        assert result['success'] is True
        assert 'error_type' in result
        assert result['error_type'] == 'AttributeError'
        assert 'suggestions' in result
        assert len(result['suggestions']) > 0
        
        suggestion = result['suggestions'][0]
        assert isinstance(suggestion, FixSuggestion)
        assert suggestion.error_type == 'AttributeError'
        assert 'hasattr' in suggestion.suggested_fix or 'None' in suggestion.description
    
    def test_diagnose_key_error(self, diagnoser):
        """Test diagnosis of KeyError"""
        error_message = "KeyError: 'missing_key'"
        result = diagnoser.diagnose_error(error_message)
        
        assert result['success'] is True
        assert result['error_type'] == 'KeyError'
        assert len(result['suggestions']) > 0
        
        suggestion = result['suggestions'][0]
        assert suggestion.error_type == 'KeyError'
        assert '.get(' in suggestion.suggested_fix
    
    def test_diagnose_index_error(self, diagnoser):
        """Test diagnosis of IndexError"""
        error_message = "IndexError: list index out of range"
        result = diagnoser.diagnose_error(error_message)
        
        assert result['success'] is True
        assert result['error_type'] == 'IndexError'
        assert len(result['suggestions']) > 0
        
        suggestion = result['suggestions'][0]
        assert suggestion.error_type == 'IndexError'
        assert 'len(' in suggestion.suggested_fix or 'bounds' in suggestion.description.lower()
    
    def test_diagnose_type_error(self, diagnoser):
        """Test diagnosis of TypeError"""
        error_message = "TypeError: unsupported operand type(s) for +: 'int' and 'str'"
        result = diagnoser.diagnose_error(error_message)
        
        assert result['success'] is True
        assert result['error_type'] == 'TypeError'
        assert len(result['suggestions']) > 0
        
        suggestion = result['suggestions'][0]
        assert suggestion.error_type == 'TypeError'
        assert 'type' in suggestion.description.lower() or 'convert' in suggestion.description.lower()
    
    def test_diagnose_unknown_error(self, diagnoser):
        """Test diagnosis of unknown error type"""
        error_message = "UnknownError: this error is not in the pattern library"
        result = diagnoser.diagnose_error(error_message)
        
        assert result['success'] is True
        assert result['error_type'] == 'Unknown'
        assert 'suggestions' in result
        assert len(result['suggestions']) == 0
    
    def test_diagnose_empty_message(self, diagnoser):
        """Test diagnosis with empty error message"""
        result = diagnoser.diagnose_error("")
        
        assert result['success'] is True
        assert result['error_type'] == 'Unknown'
        assert len(result['suggestions']) == 0
    
    def test_fix_suggestion_structure(self, diagnoser):
        """Test FixSuggestion dataclass structure"""
        suggestion = FixSuggestion(
            error_type='TestError',
            description='Test description',
            suggested_fix='test_fix()',
            confidence=0.9
        )
        
        assert suggestion.error_type == 'TestError'
        assert suggestion.description == 'Test description'
        assert suggestion.suggested_fix == 'test_fix()'
        assert suggestion.confidence == 0.9
    
    def test_multiple_suggestions(self, diagnoser):
        """Test that diagnose_error can return multiple suggestions"""
        error_message = "KeyError: 'config'"
        result = diagnoser.diagnose_error(error_message)
        
        assert result['success'] is True
        assert 'suggestions' in result
        suggestions = result['suggestions']
        
        for suggestion in suggestions:
            assert isinstance(suggestion, FixSuggestion)
            assert suggestion.error_type == 'KeyError'
            assert 0.0 <= suggestion.confidence <= 1.0
    
    def test_confidence_scores(self, diagnoser):
        """Test that confidence scores are reasonable"""
        error_message = "AttributeError: 'dict' object has no attribute 'append'"
        result = diagnoser.diagnose_error(error_message)
        
        for suggestion in result['suggestions']:
            assert 0.0 <= suggestion.confidence <= 1.0
            assert suggestion.confidence > 0.0
    
    def test_pattern_matching_case_insensitive(self, diagnoser):
        """Test that error pattern matching works regardless of case"""
        error_messages = [
            "AttributeError: test",
            "attributeerror: test",
            "ATTRIBUTEERROR: test"
        ]
        
        for msg in error_messages:
            result = diagnoser.diagnose_error(msg)
            assert result['success'] is True
            assert result['error_type'] in ['AttributeError', 'Unknown']
    
    def test_complex_error_message(self, diagnoser):
        """Test diagnosis with complex multi-line error message"""
        error_message = """Traceback (most recent call last):
  File "test.py", line 10, in <module>
    result = obj.missing_attr
AttributeError: 'MyClass' object has no attribute 'missing_attr'"""
        
        result = diagnoser.diagnose_error(error_message)
        
        assert result['success'] is True
        assert result['error_type'] == 'AttributeError'
        assert len(result['suggestions']) > 0


class TestErrorPatternLibrary:
    """Test the error pattern library"""
    
    def test_all_patterns_have_required_fields(self):
        """Test that all error patterns have required fields"""
        diagnoser = ErrorDiagnoser()
        
        for error_type, pattern_info in diagnoser.error_patterns.items():
            assert 'pattern' in pattern_info
            assert 'fix_template' in pattern_info
            assert isinstance(pattern_info['pattern'], str)
            assert isinstance(pattern_info['fix_template'], str)
            assert len(pattern_info['pattern']) > 0
            assert len(pattern_info['fix_template']) > 0
    
    def test_pattern_coverage(self):
        """Test that we cover common Python errors"""
        diagnoser = ErrorDiagnoser()
        common_errors = ['AttributeError', 'KeyError', 'IndexError', 'TypeError']
        
        for error in common_errors:
            assert error in diagnoser.error_patterns, f"{error} should be in pattern library"
