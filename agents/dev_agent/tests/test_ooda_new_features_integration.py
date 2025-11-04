#!/usr/bin/env python3
"""
Integration Tests for New Features in OODA Loop
Tests: Refactoring, TestGen, ErrorDiag, PerfAnalyzer integration
"""
import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dev_agent_ooda import DevAgentOODA


class TestOODANewFeaturesIntegration:
    """Integration tests for new features integrated into OODA Loop"""
    
    @pytest.fixture
    def ooda_agent(self):
        """Create OODA agent for testing"""
        return DevAgentOODA(
            sandbox_endpoint="http://localhost:8080",
            enable_persistence=False
        )
    
    def test_refactoring_engine_initialization(self, ooda_agent):
        """Test that refactoring engine is initialized"""
        assert ooda_agent.refactoring_engine is not None
        assert hasattr(ooda_agent.refactoring_engine, 'analyze_code')
        assert hasattr(ooda_agent.refactoring_engine, 'apply_refactoring')
        assert hasattr(ooda_agent.refactoring_engine, 'verify_refactoring')
    
    def test_test_generator_initialization(self, ooda_agent):
        """Test that test generator is initialized"""
        assert ooda_agent.test_generator is not None
        assert hasattr(ooda_agent.test_generator, 'generate_tests')
        assert ooda_agent.test_generator.framework == 'pytest'
    
    def test_error_diagnoser_initialization(self, ooda_agent):
        """Test that error diagnoser is initialized"""
        assert ooda_agent.error_diagnoser is not None
        assert hasattr(ooda_agent.error_diagnoser, 'diagnose_error')
        assert len(ooda_agent.error_diagnoser.error_patterns) >= 12
    
    def test_performance_analyzer_initialization(self, ooda_agent):
        """Test that performance analyzer is initialized"""
        assert ooda_agent.performance_analyzer is not None
        assert hasattr(ooda_agent.performance_analyzer, 'analyze_code')
    
    async def test_analyze_code_quality_action(self, ooda_agent):
        """Test analyze_code_quality action execution"""
        test_code = """
def long_function():
    x = 1
    x = 2
    x = 3
""" + "    x += 1\n" * 60
        
        action = {
            'type': 'analyze_code_quality',
            'code': test_code
        }
        
        result = await ooda_agent._execute_action(action)
        
        assert result.get('success') is True
        assert 'suggestions' in result
        assert 'metrics' in result
    
    async def test_generate_tests_action(self, ooda_agent):
        """Test generate_tests action execution"""
        test_code = """
def calculate_sum(a, b):
    return a + b

def is_valid(value):
    return value > 0
"""
        
        action = {
            'type': 'generate_tests',
            'code': test_code,
            'file_path': 'test_module.py'
        }
        
        result = await ooda_agent._execute_action(action)
        
        assert result.get('success') is True
        assert 'test_code' in result
        assert 'total_tests' in result
        assert result['total_tests'] >= 2
    
    async def test_diagnose_error_action(self, ooda_agent):
        """Test diagnose_error action execution"""
        action = {
            'type': 'diagnose_error',
            'error_message': "KeyError: 'missing_key'",
            'code_context': "result = data['missing_key']"
        }
        
        result = await ooda_agent._execute_action(action)
        
        assert result.get('success') is True
        assert 'error_type' in result
        assert result['error_type'] == 'KeyError'
        assert 'suggestions' in result
        assert len(result['suggestions']) > 0
    
    async def test_analyze_performance_action(self, ooda_agent):
        """Test analyze_performance action execution"""
        test_code = """
def nested_loops(data):
    for i in data:
        for j in i:
            for k in j:
                for m in k:
                    print(m)
"""
        
        action = {
            'type': 'analyze_performance',
            'code': test_code
        }
        
        result = await ooda_agent._execute_action(action)
        
        assert result.get('success') is True
        assert 'issues' in result
        assert 'total_issues' in result
    
    async def test_apply_refactoring_action(self, ooda_agent):
        """Test apply_refactoring action execution"""
        original_code = """
def MyFunction():
    return 42
"""
        
        suggestion = {
            'type': 'improve_naming',
            'description': 'Function name should use snake_case',
            'original_code': original_code,
            'suggested_code': 'def my_function():\n    return 42\n',
            'line': 1
        }
        
        action = {
            'type': 'apply_refactoring',
            'code': original_code,
            'suggestion': suggestion
        }
        
        result = await ooda_agent._execute_action(action)
        
        assert result.get('success') is True
        assert 'refactored_code' in result
    
    async def test_verify_refactoring_action(self, ooda_agent):
        """Test verify_refactoring action execution"""
        original_code = "def MyFunction():\n    return 42\n"
        refactored_code = "def my_function():\n    return 42\n"
        
        action = {
            'type': 'verify_refactoring',
            'original_code': original_code,
            'refactored_code': refactored_code
        }
        
        result = await ooda_agent._execute_action(action)
        
        assert result.get('success') is True
        assert 'syntax_valid' in result
        assert 'functions_preserved' in result
        assert 'added_symbols' in result
        assert 'removed_symbols' in result
    
    async def test_invalid_action_type(self, ooda_agent):
        """Test handling of invalid action type"""
        action = {
            'type': 'nonexistent_action',
            'data': 'test'
        }
        
        result = await ooda_agent._execute_action(action)
        
        assert result.get('success') is False
        assert 'error' in result
    
    async def test_action_error_handling(self, ooda_agent):
        """Test error handling in actions"""
        action = {
            'type': 'analyze_code_quality',
            'code': 'def broken syntax('
        }
        
        result = await ooda_agent._execute_action(action)
        
        assert result.get('success') is False
        assert 'error' in result


class TestOODAWorkflowWithNewFeatures:
    """E2E workflow tests using new features"""
    
    @pytest.fixture
    def ooda_agent(self):
        """Create OODA agent for testing"""
        return DevAgentOODA(
            sandbox_endpoint="http://localhost:8080",
            enable_persistence=False
        )
    
    async def test_code_quality_workflow(self, ooda_agent):
        """Test complete code quality analysis workflow"""
        test_code = """
def VeryLongFunctionName():
    result = 0
    for i in range(100):
        for j in range(100):
            for k in range(100):
                result += i + j + k
    return result
"""
        
        analyze_action = {
            'type': 'analyze_code_quality',
            'code': test_code
        }
        
        analyze_result = await ooda_agent._execute_action(analyze_action)
        
        assert analyze_result.get('success') is True
        assert len(analyze_result.get('suggestions', [])) > 0
        
        if analyze_result.get('suggestions'):
            suggestion = analyze_result['suggestions'][0]
            
            if suggestion['type'] in ['improve_naming', 'rename']:
                apply_action = {
                    'type': 'apply_refactoring',
                    'code': test_code,
                    'suggestion': suggestion
                }
                
                apply_result = await ooda_agent._execute_action(apply_action)
                assert apply_result.get('success') is True
    
    async def test_error_diagnosis_workflow(self, ooda_agent):
        """Test complete error diagnosis workflow"""
        error_messages = [
            "KeyError: 'config'",
            "AttributeError: 'NoneType' object has no attribute 'value'",
            "IndexError: list index out of range",
            "TypeError: unsupported operand type(s) for +: 'int' and 'str'"
        ]
        
        for error_msg in error_messages:
            action = {
                'type': 'diagnose_error',
                'error_message': error_msg
            }
            
            result = await ooda_agent._execute_action(action)
            
            assert result.get('success') is True
            assert result.get('error_type') != 'Unknown'
            assert len(result.get('suggestions', [])) > 0
    
    async def test_test_generation_workflow(self, ooda_agent):
        """Test complete test generation workflow"""
        source_code = """
def get_user_name(user_id):
    return f"user_{user_id}"

def is_admin(user):
    return user.get('role') == 'admin'

def count_items(items):
    return len(items)
"""
        
        action = {
            'type': 'generate_tests',
            'code': source_code,
            'file_path': 'user_utils.py'
        }
        
        result = await ooda_agent._execute_action(action)
        
        assert result.get('success') is True
        assert result['total_tests'] == 3
        assert 'test_code' in result
        assert 'def test_get_user_name' in result['test_code']
        assert 'def test_is_admin' in result['test_code']
        assert 'def test_count_items' in result['test_code']
    
    async def test_performance_analysis_workflow(self, ooda_agent):
        """Test complete performance analysis workflow"""
        slow_code = """
def process_data(data):
    results = []
    for item in data:
        for subitem in item:
            for value in subitem:
                expensive_operation()
                expensive_operation()
                results.append(value)
    return results

def expensive_operation():
    pass
"""
        
        action = {
            'type': 'analyze_performance',
            'code': slow_code
        }
        
        result = await ooda_agent._execute_action(action)
        
        assert result.get('success') is True
        assert result['total_issues'] > 0
        
        issues = result['issues']
        issue_types = [issue.issue_type for issue in issues]
        
        assert 'nested_loops' in issue_types or 'repeated_calculation' in issue_types


class TestOODAFeatureDiscovery:
    """Tests for feature discovery and capability reporting"""
    
    @pytest.fixture
    def ooda_agent(self):
        """Create OODA agent for testing"""
        return DevAgentOODA(
            sandbox_endpoint="http://localhost:8080",
            enable_persistence=False
        )
    
    def test_all_new_features_available(self, ooda_agent):
        """Test that all new features are available in OODA agent"""
        required_modules = [
            'refactoring_engine',
            'test_generator',
            'error_diagnoser',
            'performance_analyzer'
        ]
        
        for module_name in required_modules:
            assert hasattr(ooda_agent, module_name), f"Missing module: {module_name}"
            assert getattr(ooda_agent, module_name) is not None
    
    def test_feature_integration_completeness(self, ooda_agent):
        """Test that all features are properly initialized"""
        assert ooda_agent.refactoring_engine is not None
        assert ooda_agent.test_generator is not None
        assert ooda_agent.error_diagnoser is not None
        assert ooda_agent.performance_analyzer is not None
        
        assert ooda_agent.test_generator.framework == 'pytest'
        assert len(ooda_agent.error_diagnoser.error_patterns) >= 12
