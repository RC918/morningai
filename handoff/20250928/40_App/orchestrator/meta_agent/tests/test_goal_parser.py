"""
Tests for GoalParser - Natural Language Goal Parsing

Issue: #1821 - Meta Agent 自主任務規劃與執行
"""

import pytest
from ..goal_parser import GoalParser, GoalType, GoalPriority, ParsedGoal


class TestGoalParser:
    """Test cases for GoalParser"""

    @pytest.fixture
    def parser(self):
        """Create a GoalParser instance"""
        return GoalParser()

    def test_parse_empty_goal_raises_error(self, parser):
        """Test that empty goal raises ValueError"""
        with pytest.raises(ValueError, match="Goal text cannot be empty"):
            parser.parse("")

        with pytest.raises(ValueError, match="Goal text cannot be empty"):
            parser.parse("   ")

    def test_parse_feature_development_goal(self, parser):
        """Test parsing a feature development goal"""
        goal_text = "Add a new user authentication feature with OAuth support"
        result = parser.parse(goal_text)

        assert isinstance(result, ParsedGoal)
        assert result.goal_type == GoalType.FEATURE_DEVELOPMENT
        assert result.original_text == goal_text
        assert len(result.goal_id) > 0
        assert len(result.objectives) > 0
        assert len(result.success_criteria) > 0

    def test_parse_bug_fix_goal(self, parser):
        """Test parsing a bug fix goal"""
        goal_text = "Fix the login error that occurs when users enter special characters"
        result = parser.parse(goal_text)

        assert result.goal_type == GoalType.BUG_FIX
        assert "error" in goal_text.lower() or "fix" in goal_text.lower()

    def test_parse_refactoring_goal(self, parser):
        """Test parsing a refactoring goal"""
        goal_text = "Refactor the authentication module to improve code quality"
        result = parser.parse(goal_text)

        assert result.goal_type == GoalType.REFACTORING

    def test_parse_documentation_goal(self, parser):
        """Test parsing a documentation goal"""
        goal_text = "Write documentation for the API endpoints"
        result = parser.parse(goal_text)

        assert result.goal_type == GoalType.DOCUMENTATION

    def test_parse_testing_goal(self, parser):
        """Test parsing a testing goal"""
        goal_text = "Add unit tests to increase coverage to 80%"
        result = parser.parse(goal_text)

        assert result.goal_type == GoalType.TESTING

    def test_parse_deployment_goal(self, parser):
        """Test parsing a deployment goal"""
        goal_text = "Deploy the new version to production"
        result = parser.parse(goal_text)

        assert result.goal_type == GoalType.DEPLOYMENT
        assert result.requires_approval is True  # Deployment always requires approval

    def test_detect_critical_priority(self, parser):
        """Test detection of critical priority"""
        goal_text = "URGENT: Fix the critical security vulnerability immediately"
        result = parser.parse(goal_text)

        assert result.priority == GoalPriority.CRITICAL

    def test_detect_high_priority(self, parser):
        """Test detection of high priority"""
        goal_text = "Important: Update the payment processing module soon"
        result = parser.parse(goal_text)

        assert result.priority == GoalPriority.HIGH

    def test_detect_low_priority(self, parser):
        """Test detection of low priority"""
        goal_text = "When possible, clean up the old log files"
        result = parser.parse(goal_text)

        assert result.priority == GoalPriority.LOW

    def test_default_medium_priority(self, parser):
        """Test default medium priority"""
        goal_text = "Update the README file"
        result = parser.parse(goal_text)

        assert result.priority == GoalPriority.MEDIUM

    def test_complexity_estimation_simple(self, parser):
        """Test simple complexity estimation"""
        goal_text = "Update the version number"
        result = parser.parse(goal_text)

        assert result.estimated_complexity == "simple"

    def test_complexity_estimation_complex(self, parser):
        """Test complex complexity estimation"""
        goal_text = (
            "Implement a complete integration with multiple external services, "
            "including database migration, API refactoring, and comprehensive testing "
            "across all modules in the entire system"
        )
        result = parser.parse(goal_text)

        assert result.estimated_complexity == "complex"

    def test_high_risk_pattern_detection(self, parser):
        """Test detection of high-risk patterns requiring approval"""
        high_risk_goals = [
            "Deploy to production environment",
            "Run database migration on production",
            "Update payment processing logic",
            "Modify authentication system",
        ]

        for goal_text in high_risk_goals:
            result = parser.parse(goal_text)
            assert result.requires_approval is True, f"Expected approval for: {goal_text}"

    def test_context_in_constraints(self, parser):
        """Test that context is included in constraints"""
        context = {"repo": "RC918/morningai", "branch": "feature/test"}
        result = parser.parse("Add a new feature", context)

        constraint_text = " ".join(result.constraints)
        assert "RC918/morningai" in constraint_text
        assert "feature/test" in constraint_text

    def test_chinese_goal_parsing(self, parser):
        """Test parsing Chinese language goals"""
        goal_text = "新增用戶認證功能，支援 OAuth 登入"
        result = parser.parse(goal_text)

        assert result.goal_type == GoalType.FEATURE_DEVELOPMENT
        assert len(result.objectives) > 0

    def test_chinese_priority_detection(self, parser):
        """Test Chinese priority keywords"""
        goal_text = "緊急修復登入錯誤問題"
        result = parser.parse(goal_text)

        assert result.priority == GoalPriority.CRITICAL

    def test_to_dict_serialization(self, parser):
        """Test ParsedGoal serialization to dict"""
        result = parser.parse("Add a new feature")
        result_dict = result.to_dict()

        assert "goal_id" in result_dict
        assert "goal_type" in result_dict
        assert "priority" in result_dict
        assert "objectives" in result_dict
        assert "success_criteria" in result_dict
        assert result_dict["goal_type"] == "feature_development"

    def test_summary_generation(self, parser):
        """Test summary generation for long goals"""
        long_goal = "A" * 200
        result = parser.parse(long_goal)

        assert len(result.summary) <= 103  # 100 chars + "..."

    def test_objective_extraction_with_delimiters(self, parser):
        """Test objective extraction with various delimiters"""
        goal_text = "Add feature A, implement feature B, and update feature C"
        result = parser.parse(goal_text)

        assert len(result.objectives) >= 2

    def test_metadata_includes_parser_version(self, parser):
        """Test that metadata includes parser version"""
        result = parser.parse("Add a feature")

        assert "parser_version" in result.metadata
        assert result.metadata["parser_version"] == "1.0.0"


class TestGoalType:
    """Test cases for GoalType enum"""

    def test_all_goal_types_have_keywords(self):
        """Test that all goal types have associated keywords"""
        parser = GoalParser()

        for goal_type in GoalType:
            if goal_type != GoalType.UNKNOWN:
                assert goal_type in parser.GOAL_TYPE_KEYWORDS


class TestParsedGoal:
    """Test cases for ParsedGoal dataclass"""

    def test_parsed_goal_creation(self):
        """Test ParsedGoal creation with all fields"""
        goal = ParsedGoal(
            goal_id="test-123",
            original_text="Test goal",
            goal_type=GoalType.FEATURE_DEVELOPMENT,
            priority=GoalPriority.HIGH,
            summary="Test",
            objectives=["Objective 1"],
            constraints=["Constraint 1"],
            success_criteria=["Criteria 1"],
            estimated_complexity="simple",
            requires_approval=False,
        )

        assert goal.goal_id == "test-123"
        assert goal.goal_type == GoalType.FEATURE_DEVELOPMENT
        assert goal.priority == GoalPriority.HIGH
