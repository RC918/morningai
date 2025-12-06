"""
Tests for ConfidenceScorer

Issue: #1822 - 整合開發工具 (Integrate Development Tools)
Milestone: M5 - Meta Agent 優化
"""

import pytest

from ..confidence_scorer import (
    ConfidenceLevel,
    ConfidenceScore,
    ConfidenceScorer,
    Question,
    QuestionCategory,
    ScoredPlan,
)
from ..goal_parser import GoalParser
from ..task_planner import TaskPlanner


@pytest.fixture
def goal_parser():
    """Create a GoalParser instance for testing"""
    return GoalParser()


@pytest.fixture
def task_planner():
    """Create a TaskPlanner instance for testing"""
    return TaskPlanner()


@pytest.fixture
def confidence_scorer():
    """Create a ConfidenceScorer instance for testing"""
    return ConfidenceScorer()


@pytest.fixture
def simple_goal(goal_parser):
    """Create a simple, well-defined goal"""
    return goal_parser.parse(
        "Add a new button to the settings page that allows users to export their data",
        context={"repo": "RC918/morningai", "branch": "main"}
    )


@pytest.fixture
def complex_goal(goal_parser):
    """Create a complex goal with uncertainties"""
    return goal_parser.parse(
        "Maybe refactor the entire authentication system and possibly migrate to a new database",
        context={"repo": "RC918/morningai"}
    )


@pytest.fixture
def deployment_goal(goal_parser):
    """Create a deployment goal (high risk)"""
    return goal_parser.parse(
        "Deploy the new payment system to production",
        context={"repo": "RC918/morningai"}
    )


@pytest.fixture
def simple_plan(task_planner, simple_goal):
    """Create a plan for a simple goal"""
    return task_planner.create_plan(simple_goal)


@pytest.fixture
def complex_plan(task_planner, complex_goal):
    """Create a plan for a complex goal"""
    return task_planner.create_plan(complex_goal)


@pytest.fixture
def deployment_plan(task_planner, deployment_goal):
    """Create a plan for a deployment goal"""
    return task_planner.create_plan(deployment_goal)


class TestConfidenceScorer:
    """Tests for ConfidenceScorer class"""

    def test_init(self, confidence_scorer):
        """Test ConfidenceScorer initialization"""
        assert confidence_scorer is not None
        assert confidence_scorer.llm_client is None

    def test_init_with_llm(self):
        """Test ConfidenceScorer initialization with LLM client"""
        mock_llm = object()
        scorer = ConfidenceScorer(llm_client=mock_llm)
        assert scorer.llm_client is mock_llm

    def test_score_simple_plan(self, confidence_scorer, simple_plan):
        """Test scoring a simple, well-defined plan"""
        scored = confidence_scorer.score_plan(simple_plan)

        assert isinstance(scored, ScoredPlan)
        assert scored.plan == simple_plan
        assert isinstance(scored.confidence, ConfidenceScore)
        assert 0.0 <= scored.confidence.overall_score <= 1.0
        assert scored.confidence.level in ConfidenceLevel
        assert isinstance(scored.questions, list)
        assert isinstance(scored.recommendations, list)

    def test_score_complex_plan(self, confidence_scorer, complex_plan):
        """Test scoring a complex plan with uncertainties"""
        scored = confidence_scorer.score_plan(complex_plan)

        assert isinstance(scored, ScoredPlan)
        # Complex plans should have lower confidence
        assert scored.confidence.overall_score < 0.8
        # Should have more questions
        assert len(scored.questions) > 0

    def test_score_deployment_plan(self, confidence_scorer, deployment_plan):
        """Test scoring a deployment plan (high risk)"""
        scored = confidence_scorer.score_plan(deployment_plan)

        assert isinstance(scored, ScoredPlan)
        # Deployment plans require approval
        assert any(q.category == QuestionCategory.APPROVAL for q in scored.questions)
        # Should have blocking questions
        assert any(q.blocking for q in scored.questions)

    def test_confidence_score_breakdown(self, confidence_scorer, simple_plan):
        """Test that confidence score has proper breakdown"""
        scored = confidence_scorer.score_plan(simple_plan)
        confidence = scored.confidence

        assert "scope_clarity" in confidence.breakdown
        assert "technical_feasibility" in confidence.breakdown
        assert "dependency_completeness" in confidence.breakdown
        assert "risk_assessment" in confidence.breakdown
        assert "resource_availability" in confidence.breakdown

        # All breakdown scores should be between 0 and 1
        for key, value in confidence.breakdown.items():
            assert 0.0 <= value <= 1.0, f"{key} score out of range: {value}"

    def test_confidence_level_determination(self, confidence_scorer):
        """Test confidence level determination"""
        assert confidence_scorer._determine_level(0.9) == ConfidenceLevel.HIGH
        assert confidence_scorer._determine_level(0.8) == ConfidenceLevel.HIGH
        assert confidence_scorer._determine_level(0.6) == ConfidenceLevel.MEDIUM
        assert confidence_scorer._determine_level(0.5) == ConfidenceLevel.MEDIUM
        assert confidence_scorer._determine_level(0.3) == ConfidenceLevel.LOW
        assert confidence_scorer._determine_level(0.1) == ConfidenceLevel.VERY_LOW

    def test_ready_to_execute_high_confidence(self, confidence_scorer, simple_plan):
        """Test ready_to_execute for high confidence plans"""
        scored = confidence_scorer.score_plan(simple_plan)

        # Simple plans with high confidence should be ready
        if scored.confidence.overall_score >= 0.5:
            blocking = [q for q in scored.questions if q.blocking]
            if len(blocking) == 0:
                assert scored.ready_to_execute is True

    def test_ready_to_execute_blocking_questions(self, confidence_scorer, deployment_plan):
        """Test ready_to_execute with blocking questions"""
        scored = confidence_scorer.score_plan(deployment_plan)

        # Deployment plans have blocking questions
        blocking = [q for q in scored.questions if q.blocking]
        if len(blocking) > 0:
            assert scored.ready_to_execute is False

    def test_questions_have_required_fields(self, confidence_scorer, complex_plan):
        """Test that generated questions have all required fields"""
        scored = confidence_scorer.score_plan(complex_plan)

        for question in scored.questions:
            assert question.question_id is not None
            assert question.category in QuestionCategory
            assert question.question is not None
            assert len(question.question) > 0
            assert question.priority in ["critical", "high", "medium", "low"]
            assert isinstance(question.blocking, bool)

    def test_recommendations_generated(self, confidence_scorer, simple_plan):
        """Test that recommendations are generated"""
        scored = confidence_scorer.score_plan(simple_plan)

        assert len(scored.recommendations) > 0
        for rec in scored.recommendations:
            assert isinstance(rec, str)
            assert len(rec) > 0

    def test_factors_collected(self, confidence_scorer, simple_plan):
        """Test that factors affecting score are collected"""
        scored = confidence_scorer.score_plan(simple_plan)

        assert len(scored.confidence.factors) > 0
        for factor in scored.confidence.factors:
            assert isinstance(factor, str)


class TestConfidenceScoreDataclass:
    """Tests for ConfidenceScore dataclass"""

    def test_to_dict(self):
        """Test ConfidenceScore to_dict method"""
        score = ConfidenceScore(
            overall_score=0.75,
            level=ConfidenceLevel.MEDIUM,
            scope_clarity=0.8,
            technical_feasibility=0.7,
            dependency_completeness=0.6,
            risk_assessment=0.8,
            resource_availability=0.7,
            breakdown={"test": 0.5},
            factors=["Factor 1", "Factor 2"],
        )

        d = score.to_dict()

        assert d["overall_score"] == 0.75
        assert d["overall_percent"] == 75
        assert d["level"] == "medium"
        assert d["scope_clarity"] == 0.8
        assert d["technical_feasibility"] == 0.7
        assert d["factors"] == ["Factor 1", "Factor 2"]


class TestQuestionDataclass:
    """Tests for Question dataclass"""

    def test_to_dict(self):
        """Test Question to_dict method"""
        question = Question(
            question_id="Q001",
            category=QuestionCategory.SCOPE,
            question="What is the scope?",
            context="Testing context",
            priority="high",
            blocking=True,
            suggested_answer="Answer here",
            metadata={"key": "value"},
        )

        d = question.to_dict()

        assert d["question_id"] == "Q001"
        assert d["category"] == "scope"
        assert d["question"] == "What is the scope?"
        assert d["context"] == "Testing context"
        assert d["priority"] == "high"
        assert d["blocking"] is True
        assert d["suggested_answer"] == "Answer here"
        assert d["metadata"] == {"key": "value"}


class TestScoredPlanDataclass:
    """Tests for ScoredPlan dataclass"""

    def test_to_dict(self, task_planner, goal_parser, confidence_scorer):
        """Test ScoredPlan to_dict method"""
        goal = goal_parser.parse("Add a new feature")
        plan = task_planner.create_plan(goal)
        scored = confidence_scorer.score_plan(plan)

        d = scored.to_dict()

        assert "plan" in d
        assert "confidence" in d
        assert "questions" in d
        assert "recommendations" in d
        assert "ready_to_execute" in d
        assert "scored_at" in d
        assert "blocking_questions" in d
        assert "total_questions" in d


class TestScoringFactors:
    """Tests for individual scoring factors"""

    def test_scope_clarity_with_clear_objectives(self, confidence_scorer, goal_parser, task_planner):
        """Test scope clarity scoring with clear objectives"""
        goal = goal_parser.parse(
            "Implement a specific user authentication feature with OAuth2 support. "
            "Must handle login, logout, and token refresh. "
            "Success criteria: all tests pass, documentation updated."
        )
        plan = task_planner.create_plan(goal)
        scored = confidence_scorer.score_plan(plan)

        # Clear objectives should result in higher scope clarity
        assert scored.confidence.scope_clarity >= 0.5

    def test_scope_clarity_with_vague_objectives(self, confidence_scorer, goal_parser, task_planner):
        """Test scope clarity scoring with vague objectives"""
        goal = goal_parser.parse("Maybe do something with the code, possibly fix stuff")
        plan = task_planner.create_plan(goal)
        scored = confidence_scorer.score_plan(plan)

        # Vague objectives should result in lower scope clarity
        assert scored.confidence.scope_clarity < 0.7

    def test_technical_feasibility_simple_task(self, confidence_scorer, goal_parser, task_planner):
        """Test technical feasibility for simple tasks"""
        goal = goal_parser.parse("Write documentation for the API endpoints")
        plan = task_planner.create_plan(goal)
        scored = confidence_scorer.score_plan(plan)

        # Documentation is technically straightforward
        assert scored.confidence.technical_feasibility >= 0.6

    def test_technical_feasibility_complex_task(self, confidence_scorer, goal_parser, task_planner):
        """Test technical feasibility for complex tasks"""
        goal = goal_parser.parse(
            "Refactor the entire distributed system architecture with concurrent processing"
        )
        plan = task_planner.create_plan(goal)
        scored = confidence_scorer.score_plan(plan)

        # Complex tasks should have lower technical feasibility
        assert scored.confidence.technical_feasibility < 0.8

    def test_risk_assessment_deployment(self, confidence_scorer, goal_parser, task_planner):
        """Test risk assessment for deployment tasks"""
        goal = goal_parser.parse("Deploy to production environment")
        plan = task_planner.create_plan(goal)
        scored = confidence_scorer.score_plan(plan)

        # Deployment has higher risk
        assert scored.confidence.risk_assessment < 0.8

    def test_resource_availability_long_task(self, confidence_scorer, goal_parser, task_planner):
        """Test resource availability for long tasks"""
        goal = goal_parser.parse(
            "Complete refactoring of multiple modules including testing and documentation"
        )
        plan = task_planner.create_plan(goal)
        scored = confidence_scorer.score_plan(plan)

        # Long tasks may have resource concerns
        if plan.total_estimated_minutes > 180:
            assert scored.confidence.resource_availability < 0.8


class TestQuestionGeneration:
    """Tests for question generation"""

    def test_generates_scope_questions_for_unclear_scope(
        self, confidence_scorer, goal_parser, task_planner
    ):
        """Test that scope questions are generated for unclear scope"""
        goal = goal_parser.parse("Do something")
        plan = task_planner.create_plan(goal)
        scored = confidence_scorer.score_plan(plan)

        # Should generate scope-related questions
        scope_questions = [q for q in scored.questions if q.category == QuestionCategory.SCOPE]
        assert len(scope_questions) > 0

    def test_generates_approval_questions_for_high_risk(
        self, confidence_scorer, goal_parser, task_planner
    ):
        """Test that approval questions are generated for high-risk tasks"""
        goal = goal_parser.parse("Deploy payment system to production")
        plan = task_planner.create_plan(goal)
        scored = confidence_scorer.score_plan(plan)

        # Should generate approval questions
        approval_questions = [q for q in scored.questions if q.category == QuestionCategory.APPROVAL]
        assert len(approval_questions) > 0

    def test_generates_risk_questions_for_deployment(
        self, confidence_scorer, goal_parser, task_planner
    ):
        """Test that risk questions are generated for deployment"""
        goal = goal_parser.parse("Deploy to production")
        plan = task_planner.create_plan(goal)
        scored = confidence_scorer.score_plan(plan)

        # Should generate risk questions about rollback
        risk_questions = [q for q in scored.questions if q.category == QuestionCategory.RISK]
        assert len(risk_questions) > 0

    def test_generates_resource_questions_for_long_tasks(
        self, confidence_scorer, goal_parser, task_planner
    ):
        """Test that resource questions are generated for long tasks"""
        # Create a goal that will result in a long plan
        goal = goal_parser.parse(
            "Complete full system redesign with multiple integration points, "
            "comprehensive testing, and detailed documentation"
        )
        plan = task_planner.create_plan(goal)

        # Manually increase estimated time to trigger resource questions
        for task in plan.subtasks:
            task.estimated_duration_minutes = 60
        plan.total_estimated_minutes = sum(t.estimated_duration_minutes for t in plan.subtasks)

        scored = confidence_scorer.score_plan(plan)

        if plan.total_estimated_minutes > 180:
            resource_questions = [
                q for q in scored.questions if q.category == QuestionCategory.RESOURCE
            ]
            assert len(resource_questions) > 0


class TestRecommendationGeneration:
    """Tests for recommendation generation"""

    def test_high_confidence_recommendation(self, confidence_scorer, goal_parser, task_planner):
        """Test recommendations for high confidence plans"""
        goal = goal_parser.parse(
            "Write unit tests for the user service module",
            context={"repo": "RC918/morningai", "branch": "main"}
        )
        plan = task_planner.create_plan(goal)
        scored = confidence_scorer.score_plan(plan)

        if scored.confidence.level == ConfidenceLevel.HIGH:
            assert any("ready" in rec.lower() for rec in scored.recommendations)

    def test_low_confidence_recommendation(self, confidence_scorer, goal_parser, task_planner):
        """Test recommendations for low confidence plans"""
        goal = goal_parser.parse("Maybe do something unclear")
        plan = task_planner.create_plan(goal)
        scored = confidence_scorer.score_plan(plan)

        if scored.confidence.level in [ConfidenceLevel.LOW, ConfidenceLevel.VERY_LOW]:
            assert any(
                "clarification" in rec.lower() or "revision" in rec.lower()
                for rec in scored.recommendations
            )

    def test_blocking_questions_recommendation(self, confidence_scorer, goal_parser, task_planner):
        """Test recommendations when there are blocking questions"""
        goal = goal_parser.parse("Deploy to production")
        plan = task_planner.create_plan(goal)
        scored = confidence_scorer.score_plan(plan)

        blocking = [q for q in scored.questions if q.blocking]
        if len(blocking) > 0:
            assert any("blocking" in rec.lower() for rec in scored.recommendations)


class TestConfidenceLevelEnum:
    """Tests for ConfidenceLevel enum"""

    def test_confidence_levels(self):
        """Test all confidence levels exist"""
        assert ConfidenceLevel.HIGH.value == "high"
        assert ConfidenceLevel.MEDIUM.value == "medium"
        assert ConfidenceLevel.LOW.value == "low"
        assert ConfidenceLevel.VERY_LOW.value == "very_low"


class TestQuestionCategoryEnum:
    """Tests for QuestionCategory enum"""

    def test_question_categories(self):
        """Test all question categories exist"""
        assert QuestionCategory.SCOPE.value == "scope"
        assert QuestionCategory.TECHNICAL.value == "technical"
        assert QuestionCategory.DEPENDENCY.value == "dependency"
        assert QuestionCategory.RISK.value == "risk"
        assert QuestionCategory.RESOURCE.value == "resource"
        assert QuestionCategory.APPROVAL.value == "approval"
        assert QuestionCategory.CLARIFICATION.value == "clarification"
