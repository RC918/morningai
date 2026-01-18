#!/usr/bin/env python3
"""
Tests for Test Agent v2 - EPIC D Phase 5 (P2-medium)

Blueprint Reference: Section 3.3 (Agent Catalog V2) - Test Agent
Issue: #4102 (EPIC D P2: Test Agent v2 Complete Implementation)

These tests verify:
1. TestAgentV2 initialization and configuration
2. Test quality validation (syntax, assertions, naming, structure)
3. Integration with TestGeneratorNode (D-7)
4. Integration with TestCoverageAnalyzer (B-11)
5. Edge cases and error handling
"""

from unittest.mock import Mock, patch

from test_agent.test_agent_v2 import (
    TestAgentV2,
    TestGenerationRequest,
    TestGenerationResponse,
    TestQualityResult,
    TestQualityLevel,
    TestQualityCategory,
    TestQualityAction,
    TestQualityFinding,
    get_test_agent,
    reset_test_agent,
    generate_tests,
    validate_test_quality,
    QUALITY_THRESHOLDS,
    CATEGORY_WEIGHTS,
)


class TestTestAgentV2Initialization:
    """Tests for TestAgentV2 initialization."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_test_agent()

    def test_default_initialization(self):
        """Test default initialization values."""
        agent = TestAgentV2()
        assert agent.enabled is True
        assert agent.enable_llm is True
        assert agent.validate_quality is True
        assert agent.max_tests_per_run == 5

    def test_custom_initialization(self):
        """Test custom initialization values."""
        agent = TestAgentV2(
            enabled=False,
            enable_llm=False,
            validate_quality=False,
            max_tests_per_run=10,
        )
        assert agent.enabled is False
        assert agent.enable_llm is False
        assert agent.validate_quality is False
        assert agent.max_tests_per_run == 10

    def test_singleton_pattern(self):
        """Test singleton pattern for get_test_agent."""
        agent1 = get_test_agent()
        agent2 = get_test_agent()
        assert agent1 is agent2

    def test_reset_singleton(self):
        """Test reset_test_agent clears singleton."""
        agent1 = get_test_agent()
        reset_test_agent()
        agent2 = get_test_agent()
        assert agent1 is not agent2


class TestTestQualityValidation:
    """Tests for test quality validation."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_test_agent()

    def test_validate_empty_code(self):
        """Test validation of empty code."""
        agent = TestAgentV2()
        result = agent.validate_test_quality("")
        assert result.overall_level == TestQualityLevel.INVALID
        assert result.action == TestQualityAction.REJECT
        assert result.overall_score == 0

    def test_validate_syntax_error(self):
        """Test validation of code with syntax errors."""
        agent = TestAgentV2()
        invalid_code = """
def test_something(
    # Missing closing parenthesis
    pass
"""
        result = agent.validate_test_quality(invalid_code)
        assert result.overall_level == TestQualityLevel.INVALID
        assert result.action == TestQualityAction.REJECT
        assert TestQualityCategory.SYNTAX in result.category_scores
        assert result.category_scores[TestQualityCategory.SYNTAX] == 0

    def test_validate_valid_test_code(self):
        """Test validation of valid test code."""
        agent = TestAgentV2()
        valid_code = '''
"""Test module for example."""
import pytest

def test_example_function():
    """Test example function."""
    result = 1 + 1
    assert result == 2
'''
        result = agent.validate_test_quality(valid_code)
        assert result.overall_level in [
            TestQualityLevel.EXCELLENT,
            TestQualityLevel.GOOD,
            TestQualityLevel.ACCEPTABLE,
        ]
        assert result.action in [
            TestQualityAction.APPROVE,
            TestQualityAction.SUGGEST_IMPROVEMENTS,
        ]
        assert result.test_count == 1
        assert result.assertion_count >= 1

    def test_validate_no_assertions(self):
        """Test validation of code without assertions."""
        agent = TestAgentV2()
        code_without_assertions = '''
def test_no_assertions():
    """Test without assertions."""
    result = 1 + 1
    print(result)
'''
        result = agent.validate_test_quality(code_without_assertions)
        assert result.assertion_count == 0
        assert TestQualityCategory.ASSERTIONS in result.category_scores
        # Score should be low due to no assertions
        assert result.category_scores[TestQualityCategory.ASSERTIONS] <= 50

    def test_validate_multiple_tests(self):
        """Test validation of code with multiple tests."""
        agent = TestAgentV2()
        multi_test_code = '''
"""Test module with multiple tests."""
import pytest

def test_first():
    """First test."""
    assert True

def test_second():
    """Second test."""
    assert 1 == 1

def test_third():
    """Third test."""
    assert "hello" == "hello"
'''
        result = agent.validate_test_quality(multi_test_code)
        assert result.test_count == 3
        assert result.assertion_count >= 3

    def test_validate_with_mocking(self):
        """Test validation of code with mocking."""
        agent = TestAgentV2()
        mock_code = '''
"""Test module with mocking."""
import pytest
from unittest.mock import Mock, patch

def test_with_mock():
    """Test with mock."""
    mock_obj = Mock()
    mock_obj.method.return_value = 42
    assert mock_obj.method() == 42

@patch('module.function')
def test_with_patch(mock_func):
    """Test with patch."""
    mock_func.return_value = "patched"
    assert mock_func() == "patched"
'''
        result = agent.validate_test_quality(mock_code)
        assert result.mock_count >= 2
        assert result.test_count == 2

    def test_validate_naming_conventions(self):
        """Test validation of naming conventions."""
        agent = TestAgentV2()
        # Good naming
        good_naming_code = '''
def test_valid_name():
    assert True

class TestValidClass:
    def test_method(self):
        assert True
'''
        result = agent.validate_test_quality(good_naming_code)
        assert TestQualityCategory.NAMING in result.category_scores
        assert result.category_scores[TestQualityCategory.NAMING] >= 80

    def test_validate_trivial_assertions(self):
        """Test detection of trivial assertions."""
        agent = TestAgentV2()
        trivial_code = '''
def test_trivial():
    """Test with trivial assertion."""
    assert True
'''
        result = agent.validate_test_quality(trivial_code)
        # Should have a finding about trivial assertion
        trivial_findings = [
            f for f in result.findings
            if "trivial" in f.title.lower() or "trivial" in f.description.lower()
        ]
        assert len(trivial_findings) >= 1


class TestTestQualityDataclasses:
    """Tests for test quality dataclasses."""

    def test_test_quality_finding_to_dict(self):
        """Test TestQualityFinding serialization."""
        finding = TestQualityFinding(
            category=TestQualityCategory.SYNTAX,
            level=TestQualityLevel.GOOD,
            finding_id="TEST-001",
            title="Test Finding",
            description="Test description",
            file_path="test.py",
            line_number=10,
            test_name="test_example",
            recommendation="Fix this",
            metadata={"key": "value"},
        )
        result = finding.to_dict()
        assert result["category"] == "syntax"
        assert result["level"] == "good"
        assert result["finding_id"] == "TEST-001"
        assert result["file_path"] == "test.py"
        assert result["line_number"] == 10

    def test_test_quality_result_to_dict(self):
        """Test TestQualityResult serialization."""
        result = TestQualityResult(
            overall_score=85,
            overall_level=TestQualityLevel.GOOD,
            action=TestQualityAction.APPROVE,
            test_count=5,
            assertion_count=10,
            mock_count=2,
            summary="Test summary",
        )
        data = result.to_dict()
        assert data["overall_score"] == 85
        assert data["overall_level"] == "good"
        assert data["action"] == "approve"
        assert data["test_count"] == 5
        assert data["assertion_count"] == 10

    def test_test_generation_request_to_dict(self):
        """Test TestGenerationRequest serialization."""
        request = TestGenerationRequest(
            coverage_gaps=[{"function_name": "test_func"}],
            repo_path="/path/to/repo",
            trace_id="trace-123",
            max_tests_per_run=10,
            enable_llm=False,
        )
        data = request.to_dict()
        assert data["repo_path"] == "/path/to/repo"
        assert data["trace_id"] == "trace-123"
        assert data["max_tests_per_run"] == 10
        assert data["enable_llm"] is False

    def test_test_generation_response_to_dict(self):
        """Test TestGenerationResponse serialization."""
        response = TestGenerationResponse(
            success=True,
            generated_tests=[{"test_file_path": "test.py"}],
            summary="Generated 1 test",
            total_generated=1,
            trace_id="trace-123",
        )
        data = response.to_dict()
        assert data["success"] is True
        assert data["total_generated"] == 1
        assert data["trace_id"] == "trace-123"


class TestTestGeneration:
    """Tests for test generation functionality."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_test_agent()

    def test_generate_tests_disabled(self):
        """Test generation when disabled."""
        agent = TestAgentV2(enabled=False)
        request = TestGenerationRequest(
            coverage_gaps=[{"function_name": "test_func"}],
            repo_path="/path/to/repo",
            trace_id="trace-123",
        )
        response = agent.generate_tests(request)
        assert response.success is False
        assert "disabled" in response.summary.lower()

    def test_generate_tests_no_gaps(self):
        """Test generation with no coverage gaps."""
        agent = TestAgentV2()
        request = TestGenerationRequest(
            coverage_gaps=[],
            repo_path="/path/to/repo",
            trace_id="trace-123",
        )
        response = agent.generate_tests(request)
        assert response.success is True
        assert "no coverage gaps" in response.summary.lower()

    @patch('test_agent.test_agent_v2.TestAgentV2._get_test_generator')
    def test_generate_tests_with_generator(self, mock_get_generator):
        """Test generation with mocked generator."""
        # Create mock generator
        mock_generator = Mock()
        mock_result = Mock()
        mock_result.generated_tests = []
        mock_result.failed_generations = []
        mock_generator.generate.return_value = mock_result
        mock_get_generator.return_value = mock_generator

        agent = TestAgentV2()
        request = TestGenerationRequest(
            coverage_gaps=[{"function_name": "test_func", "file_path": "src/module.py"}],
            repo_path="/path/to/repo",
            trace_id="trace-123",
            validate_quality=False,
        )
        agent.generate_tests(request)
        assert mock_generator.generate.called

    def test_generate_tests_generator_not_available(self):
        """Test generation when generator is not available."""
        agent = TestAgentV2()
        agent._test_generator = None
        # Force generator to be None
        with patch.object(agent, '_get_test_generator', return_value=None):
            request = TestGenerationRequest(
                coverage_gaps=[{"function_name": "test_func"}],
                repo_path="/path/to/repo",
                trace_id="trace-123",
            )
            response = agent.generate_tests(request)
            assert response.success is False
            assert "not available" in response.summary.lower()


class TestCoverageGapAnalysis:
    """Tests for coverage gap analysis."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_test_agent()

    @patch('test_agent.test_agent_v2.TestAgentV2._get_coverage_analyzer')
    def test_analyze_coverage_gaps(self, mock_get_analyzer):
        """Test coverage gap analysis."""
        mock_analyzer = Mock()
        mock_analysis = Mock()
        mock_analysis.to_dict.return_value = {
            "coverage_gaps": [{"function_name": "func1"}],
            "summary": "Found 1 gap",
        }
        mock_analyzer.analyze.return_value = mock_analysis
        mock_get_analyzer.return_value = mock_analyzer

        agent = TestAgentV2()
        result = agent.analyze_coverage_gaps(
            diff_content="diff content",
            trace_id="trace-123",
        )
        assert "coverage_gaps" in result
        assert mock_analyzer.analyze.called

    def test_analyze_coverage_gaps_analyzer_not_available(self):
        """Test analysis when analyzer is not available."""
        agent = TestAgentV2()
        with patch.object(agent, '_get_coverage_analyzer', return_value=None):
            result = agent.analyze_coverage_gaps(
                diff_content="diff content",
                trace_id="trace-123",
            )
            assert result["coverage_gaps"] == []
            assert "not available" in result["summary"].lower()


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_test_agent()

    def test_generate_tests_function(self):
        """Test generate_tests convenience function."""
        with patch.object(TestAgentV2, 'generate_tests') as mock_generate:
            mock_response = TestGenerationResponse(
                success=True,
                summary="Test summary",
                trace_id="trace-123",
            )
            mock_generate.return_value = mock_response

            result = generate_tests(
                coverage_gaps=[],
                repo_path="/path",
                trace_id="trace-123",
            )
            assert result["success"] is True

    def test_validate_test_quality_function(self):
        """Test validate_test_quality convenience function."""
        result = validate_test_quality(
            test_code='''
def test_example():
    assert True
''',
            file_path="test.py",
        )
        assert "overall_score" in result
        assert "overall_level" in result


class TestQualityThresholds:
    """Tests for quality thresholds and weights."""

    def test_quality_thresholds_defined(self):
        """Test that quality thresholds are properly defined."""
        assert TestQualityLevel.EXCELLENT in QUALITY_THRESHOLDS
        assert TestQualityLevel.GOOD in QUALITY_THRESHOLDS
        assert TestQualityLevel.ACCEPTABLE in QUALITY_THRESHOLDS
        assert TestQualityLevel.POOR in QUALITY_THRESHOLDS
        assert TestQualityLevel.INVALID in QUALITY_THRESHOLDS

    def test_category_weights_sum_to_one(self):
        """Test that category weights sum to approximately 1."""
        total_weight = sum(CATEGORY_WEIGHTS.values())
        assert 0.99 <= total_weight <= 1.01

    def test_all_categories_have_weights(self):
        """Test that all categories have weights defined."""
        for category in TestQualityCategory:
            assert category in CATEGORY_WEIGHTS


class TestQualityLevelDetermination:
    """Tests for quality level determination."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_test_agent()

    def test_excellent_level(self):
        """Test excellent quality level determination."""
        agent = TestAgentV2()
        level = agent._determine_level(95)
        assert level == TestQualityLevel.EXCELLENT

    def test_good_level(self):
        """Test good quality level determination."""
        agent = TestAgentV2()
        level = agent._determine_level(80)
        assert level == TestQualityLevel.GOOD

    def test_acceptable_level(self):
        """Test acceptable quality level determination."""
        agent = TestAgentV2()
        level = agent._determine_level(65)
        assert level == TestQualityLevel.ACCEPTABLE

    def test_poor_level(self):
        """Test poor quality level determination."""
        agent = TestAgentV2()
        level = agent._determine_level(45)
        assert level == TestQualityLevel.POOR

    def test_invalid_level(self):
        """Test invalid quality level determination."""
        agent = TestAgentV2()
        level = agent._determine_level(30)
        assert level == TestQualityLevel.INVALID


class TestActionDetermination:
    """Tests for action determination."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_test_agent()

    def test_approve_action(self):
        """Test approve action for excellent/good quality."""
        agent = TestAgentV2()
        action = agent._determine_action(TestQualityLevel.EXCELLENT, [])
        assert action == TestQualityAction.APPROVE

        action = agent._determine_action(TestQualityLevel.GOOD, [])
        assert action == TestQualityAction.APPROVE

    def test_suggest_improvements_action(self):
        """Test suggest improvements action for acceptable quality."""
        agent = TestAgentV2()
        action = agent._determine_action(TestQualityLevel.ACCEPTABLE, [])
        assert action == TestQualityAction.SUGGEST_IMPROVEMENTS

    def test_require_changes_action(self):
        """Test require changes action for poor quality."""
        agent = TestAgentV2()
        action = agent._determine_action(TestQualityLevel.POOR, [])
        assert action == TestQualityAction.REQUIRE_CHANGES

    def test_reject_action(self):
        """Test reject action for invalid quality."""
        agent = TestAgentV2()
        action = agent._determine_action(TestQualityLevel.INVALID, [])
        assert action == TestQualityAction.REJECT


class TestEvidenceHash:
    """Tests for evidence hash computation."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_test_agent()

    def test_evidence_hash_computed(self):
        """Test that evidence hash is computed."""
        agent = TestAgentV2()
        result = agent.validate_test_quality('''
def test_example():
    assert True
''')
        assert result.evidence_hash is not None
        assert len(result.evidence_hash) == 16

    def test_evidence_hash_deterministic(self):
        """Test that evidence hash is deterministic."""
        agent = TestAgentV2()
        code = '''
def test_example():
    assert True
'''
        result1 = agent.validate_test_quality(code)
        result2 = agent.validate_test_quality(code)
        assert result1.evidence_hash == result2.evidence_hash

    def test_evidence_hash_changes_with_code(self):
        """Test that evidence hash changes with different code."""
        agent = TestAgentV2()
        result1 = agent.validate_test_quality('''
def test_one():
    assert True
''')
        result2 = agent.validate_test_quality('''
def test_two():
    assert False
''')
        assert result1.evidence_hash != result2.evidence_hash
