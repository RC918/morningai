"""
Unit tests for F-5 Debate Engine v2 - Adversarial Collaboration

Tests the DebateEngine, DebateAgent, JudgeAgent, and related functions
that implement the adversarial collaboration pattern from Blueprint Section 7.
"""

from unittest.mock import patch, MagicMock
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core', 'planner'))

from debate_engine import (
    DebateRole,
    DebateOutcome,
    DebateCategory,
    DebateTopic,
    DebateArgument,
    JudgeDecision,
    DebateResult,
    DebateAgent,
    JudgeAgent,
    DebateEngine,
    should_trigger_debate,
    create_debate_topic_from_plan,
)


class TestDebateRole:
    """Tests for DebateRole enum."""

    def test_left_role(self):
        """Test LEFT role value."""
        assert DebateRole.LEFT.value == "left"

    def test_right_role(self):
        """Test RIGHT role value."""
        assert DebateRole.RIGHT.value == "right"

    def test_judge_role(self):
        """Test JUDGE role value."""
        assert DebateRole.JUDGE.value == "judge"


class TestDebateOutcome:
    """Tests for DebateOutcome enum."""

    def test_left_wins(self):
        """Test LEFT_WINS outcome value."""
        assert DebateOutcome.LEFT_WINS.value == "left_wins"

    def test_right_wins(self):
        """Test RIGHT_WINS outcome value."""
        assert DebateOutcome.RIGHT_WINS.value == "right_wins"

    def test_synthesis(self):
        """Test SYNTHESIS outcome value."""
        assert DebateOutcome.SYNTHESIS.value == "synthesis"

    def test_inconclusive(self):
        """Test INCONCLUSIVE outcome value."""
        assert DebateOutcome.INCONCLUSIVE.value == "inconclusive"


class TestDebateCategory:
    """Tests for DebateCategory enum."""

    def test_architecture_category(self):
        """Test ARCHITECTURE category value."""
        assert DebateCategory.ARCHITECTURE.value == "architecture"

    def test_security_category(self):
        """Test SECURITY category value."""
        assert DebateCategory.SECURITY.value == "security"

    def test_performance_category(self):
        """Test PERFORMANCE category value."""
        assert DebateCategory.PERFORMANCE.value == "performance"

    def test_cost_category(self):
        """Test COST category value."""
        assert DebateCategory.COST.value == "cost"

    def test_privacy_category(self):
        """Test PRIVACY category value."""
        assert DebateCategory.PRIVACY.value == "privacy"

    def test_strategy_category(self):
        """Test STRATEGY category value."""
        assert DebateCategory.STRATEGY.value == "strategy"

    def test_implementation_category(self):
        """Test IMPLEMENTATION category value."""
        assert DebateCategory.IMPLEMENTATION.value == "implementation"


class TestDebateTopic:
    """Tests for DebateTopic dataclass."""

    def test_basic_creation(self):
        """Test basic topic creation."""
        topic = DebateTopic(question="Should we use microservices?")

        assert topic.question == "Should we use microservices?"
        assert topic.context == {}
        assert topic.risk_level == "medium"
        assert topic.category == DebateCategory.STRATEGY
        assert topic.constraints == []
        assert topic.success_criteria == []

    def test_full_creation(self):
        """Test topic creation with all fields."""
        topic = DebateTopic(
            question="Should we use microservices?",
            context={"team_size": 10, "project_size": "large"},
            risk_level="high",
            category=DebateCategory.ARCHITECTURE,
            constraints=["Must support 1000 RPS", "Budget < $10k/month"],
            success_criteria=["Scalability", "Maintainability"],
        )

        assert topic.question == "Should we use microservices?"
        assert topic.context["team_size"] == 10
        assert topic.risk_level == "high"
        assert topic.category == DebateCategory.ARCHITECTURE
        assert len(topic.constraints) == 2
        assert len(topic.success_criteria) == 2

    def test_to_dict(self):
        """Test conversion to dictionary."""
        topic = DebateTopic(
            question="Test question",
            context={"key": "value"},
            risk_level="high",
            category=DebateCategory.SECURITY,
            constraints=["constraint1"],
            success_criteria=["criteria1"],
        )

        result = topic.to_dict()

        assert result["question"] == "Test question"
        assert result["context"] == {"key": "value"}
        assert result["risk_level"] == "high"
        assert result["category"] == "security"
        assert result["constraints"] == ["constraint1"]
        assert result["success_criteria"] == ["criteria1"]


class TestDebateArgument:
    """Tests for DebateArgument dataclass."""

    def test_basic_creation(self):
        """Test basic argument creation."""
        arg = DebateArgument(
            role=DebateRole.LEFT,
            position="Use monolith",
            reasoning="Simpler to deploy",
        )

        assert arg.role == DebateRole.LEFT
        assert arg.position == "Use monolith"
        assert arg.reasoning == "Simpler to deploy"
        assert arg.evidence == []
        assert arg.counterpoints == []
        assert arg.confidence == 0.8
        assert arg.round_number == 1

    def test_full_creation(self):
        """Test argument creation with all fields."""
        arg = DebateArgument(
            role=DebateRole.RIGHT,
            position="Use microservices",
            reasoning="Better scalability",
            evidence=["Netflix uses microservices", "Amazon uses microservices"],
            counterpoints=["Complexity is manageable with good tooling"],
            confidence=0.9,
            round_number=2,
        )

        assert arg.role == DebateRole.RIGHT
        assert arg.confidence == 0.9
        assert arg.round_number == 2
        assert len(arg.evidence) == 2
        assert len(arg.counterpoints) == 1

    def test_to_dict(self):
        """Test conversion to dictionary."""
        arg = DebateArgument(
            role=DebateRole.LEFT,
            position="Test position",
            reasoning="Test reasoning",
            evidence=["evidence1"],
            counterpoints=["counterpoint1"],
            confidence=0.75,
            round_number=3,
        )

        result = arg.to_dict()

        assert result["role"] == "left"
        assert result["position"] == "Test position"
        assert result["reasoning"] == "Test reasoning"
        assert result["evidence"] == ["evidence1"]
        assert result["counterpoints"] == ["counterpoint1"]
        assert result["confidence"] == 0.75
        assert result["round_number"] == 3


class TestJudgeDecision:
    """Tests for JudgeDecision dataclass."""

    def test_basic_creation(self):
        """Test basic decision creation."""
        decision = JudgeDecision(
            outcome=DebateOutcome.LEFT_WINS,
            winning_position="Use monolith",
            rationale="Simpler for current team size",
        )

        assert decision.outcome == DebateOutcome.LEFT_WINS
        assert decision.winning_position == "Use monolith"
        assert decision.rationale == "Simpler for current team size"
        assert decision.strengths_left == []
        assert decision.strengths_right == []
        assert decision.weaknesses_left == []
        assert decision.weaknesses_right == []
        assert decision.confidence == 0.8
        assert decision.requires_human_review is False
        assert decision.action_items == []

    def test_full_creation(self):
        """Test decision creation with all fields."""
        decision = JudgeDecision(
            outcome=DebateOutcome.SYNTHESIS,
            winning_position="Modular monolith with service boundaries",
            rationale="Combines benefits of both approaches",
            strengths_left=["Simplicity", "Easy deployment"],
            strengths_right=["Scalability", "Team autonomy"],
            weaknesses_left=["Limited scalability"],
            weaknesses_right=["Operational complexity"],
            confidence=0.85,
            requires_human_review=True,
            action_items=["Define service boundaries", "Set up monitoring"],
        )

        assert decision.outcome == DebateOutcome.SYNTHESIS
        assert decision.confidence == 0.85
        assert decision.requires_human_review is True
        assert len(decision.strengths_left) == 2
        assert len(decision.action_items) == 2

    def test_to_dict(self):
        """Test conversion to dictionary."""
        decision = JudgeDecision(
            outcome=DebateOutcome.RIGHT_WINS,
            winning_position="Test position",
            rationale="Test rationale",
            strengths_left=["s1"],
            strengths_right=["s2"],
            weaknesses_left=["w1"],
            weaknesses_right=["w2"],
            confidence=0.9,
            requires_human_review=True,
            action_items=["action1"],
        )

        result = decision.to_dict()

        assert result["outcome"] == "right_wins"
        assert result["winning_position"] == "Test position"
        assert result["rationale"] == "Test rationale"
        assert result["strengths_left"] == ["s1"]
        assert result["strengths_right"] == ["s2"]
        assert result["weaknesses_left"] == ["w1"]
        assert result["weaknesses_right"] == ["w2"]
        assert result["confidence"] == 0.9
        assert result["requires_human_review"] is True
        assert result["action_items"] == ["action1"]


class TestDebateResult:
    """Tests for DebateResult dataclass."""

    def test_basic_creation(self):
        """Test basic result creation."""
        topic = DebateTopic(question="Test question")
        decision = JudgeDecision(
            outcome=DebateOutcome.LEFT_WINS,
            winning_position="Test",
            rationale="Test",
        )
        result = DebateResult(
            topic=topic,
            arguments=[],
            decision=decision,
            rounds_completed=3,
            debate_time_ms=1500.0,
            trace_id="test-123",
        )

        assert result.topic == topic
        assert result.decision == decision
        assert result.rounds_completed == 3
        assert result.debate_time_ms == 1500.0
        assert result.trace_id == "test-123"

    def test_to_dict(self):
        """Test conversion to dictionary."""
        topic = DebateTopic(question="Test question")
        arg = DebateArgument(
            role=DebateRole.LEFT,
            position="Test",
            reasoning="Test",
        )
        decision = JudgeDecision(
            outcome=DebateOutcome.LEFT_WINS,
            winning_position="Test",
            rationale="Test",
        )
        result = DebateResult(
            topic=topic,
            arguments=[arg],
            decision=decision,
            rounds_completed=2,
            debate_time_ms=1000.0,
            trace_id="test-456",
        )

        dict_result = result.to_dict()

        assert dict_result["topic"]["question"] == "Test question"
        assert len(dict_result["arguments"]) == 1
        assert dict_result["decision"]["outcome"] == "left_wins"
        assert dict_result["rounds_completed"] == 2
        assert dict_result["debate_time_ms"] == 1000.0
        assert dict_result["trace_id"] == "test-456"


class TestDebateAgent:
    """Tests for DebateAgent class."""

    def test_init_left_agent(self):
        """Test initialization of LEFT agent."""
        agent = DebateAgent(
            role=DebateRole.LEFT,
            trace_id="test-123",
            enable_llm=False,
        )

        assert agent.role == DebateRole.LEFT
        assert agent.trace_id == "test-123"
        assert agent.enable_llm is False

    def test_init_right_agent(self):
        """Test initialization of RIGHT agent."""
        agent = DebateAgent(
            role=DebateRole.RIGHT,
            trace_id="test-456",
            enable_llm=False,
        )

        assert agent.role == DebateRole.RIGHT
        assert agent.trace_id == "test-456"

    def test_init_judge_role_raises_error(self):
        """Test that JUDGE role raises ValueError."""
        try:
            DebateAgent(
                role=DebateRole.JUDGE,
                trace_id="test-789",
            )
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "JUDGE" in str(e)

    def test_generate_template_argument_left(self):
        """Test template argument generation for LEFT agent."""
        agent = DebateAgent(
            role=DebateRole.LEFT,
            trace_id="test-123",
            enable_llm=False,
        )
        topic = DebateTopic(
            question="Should we use microservices?",
            risk_level="high",
        )

        arg = agent.generate_argument(topic, [], round_number=1)

        assert arg.role == DebateRole.LEFT
        assert "conventional" in arg.position.lower()
        assert arg.round_number == 1
        assert arg.confidence == 0.6

    def test_generate_template_argument_right(self):
        """Test template argument generation for RIGHT agent."""
        agent = DebateAgent(
            role=DebateRole.RIGHT,
            trace_id="test-123",
            enable_llm=False,
        )
        topic = DebateTopic(
            question="Should we use microservices?",
            risk_level="high",
        )

        arg = agent.generate_argument(topic, [], round_number=2)

        assert arg.role == DebateRole.RIGHT
        assert "alternative" in arg.position.lower()
        assert arg.round_number == 2

    def test_build_user_prompt_basic(self):
        """Test user prompt building with basic topic."""
        agent = DebateAgent(
            role=DebateRole.LEFT,
            trace_id="test-123",
            enable_llm=False,
        )
        topic = DebateTopic(
            question="Test question",
            context={"key": "value"},
            risk_level="high",
            category=DebateCategory.ARCHITECTURE,
        )

        prompt = agent._build_user_prompt(topic, [], round_number=1)

        assert "Test question" in prompt
        assert "high" in prompt
        assert "architecture" in prompt

    def test_build_user_prompt_with_constraints(self):
        """Test user prompt building with constraints."""
        agent = DebateAgent(
            role=DebateRole.LEFT,
            trace_id="test-123",
            enable_llm=False,
        )
        topic = DebateTopic(
            question="Test question",
            constraints=["constraint1", "constraint2"],
            success_criteria=["criteria1"],
        )

        prompt = agent._build_user_prompt(topic, [], round_number=1)

        assert "constraint1" in prompt
        assert "constraint2" in prompt
        assert "criteria1" in prompt

    def test_build_user_prompt_with_opponent_arguments(self):
        """Test user prompt building with opponent arguments."""
        agent = DebateAgent(
            role=DebateRole.LEFT,
            trace_id="test-123",
            enable_llm=False,
        )
        topic = DebateTopic(question="Test question")
        opponent_arg = DebateArgument(
            role=DebateRole.RIGHT,
            position="Opponent position",
            reasoning="Opponent reasoning",
            round_number=1,
        )

        prompt = agent._build_user_prompt(topic, [opponent_arg], round_number=2)

        assert "Opponent position" in prompt
        assert "Opponent reasoning" in prompt

    def test_parse_argument_response_valid_json(self):
        """Test parsing valid JSON response."""
        agent = DebateAgent(
            role=DebateRole.LEFT,
            trace_id="test-123",
            enable_llm=False,
        )
        response = '''
        {
            "position": "Test position",
            "reasoning": "Test reasoning",
            "evidence": ["evidence1"],
            "counterpoints": ["counterpoint1"],
            "confidence": 0.85
        }
        '''

        arg = agent._parse_argument_response(response, round_number=1)

        assert arg.position == "Test position"
        assert arg.reasoning == "Test reasoning"
        assert arg.evidence == ["evidence1"]
        assert arg.counterpoints == ["counterpoint1"]
        assert arg.confidence == 0.85

    def test_parse_argument_response_invalid_json(self):
        """Test parsing invalid JSON response falls back gracefully."""
        agent = DebateAgent(
            role=DebateRole.LEFT,
            trace_id="test-123",
            enable_llm=False,
        )
        response = "This is not valid JSON"

        arg = agent._parse_argument_response(response, round_number=1)

        assert arg.role == DebateRole.LEFT
        assert arg.confidence == 0.5
        assert arg.round_number == 1


class TestJudgeAgent:
    """Tests for JudgeAgent class."""

    def test_init(self):
        """Test initialization."""
        judge = JudgeAgent(trace_id="test-123", enable_llm=False)

        assert judge.trace_id == "test-123"
        assert judge.enable_llm is False

    def test_evaluate_template_left_wins(self):
        """Test template evaluation where LEFT wins."""
        judge = JudgeAgent(trace_id="test-123", enable_llm=False)
        topic = DebateTopic(question="Test question")
        arguments = [
            DebateArgument(
                role=DebateRole.LEFT,
                position="Left position",
                reasoning="Left reasoning",
                confidence=0.9,
            ),
            DebateArgument(
                role=DebateRole.RIGHT,
                position="Right position",
                reasoning="Right reasoning",
                confidence=0.6,
            ),
        ]

        decision = judge.evaluate(topic, arguments)

        assert decision.outcome == DebateOutcome.LEFT_WINS
        assert decision.requires_human_review is True

    def test_evaluate_template_right_wins(self):
        """Test template evaluation where RIGHT wins."""
        judge = JudgeAgent(trace_id="test-123", enable_llm=False)
        topic = DebateTopic(question="Test question")
        arguments = [
            DebateArgument(
                role=DebateRole.LEFT,
                position="Left position",
                reasoning="Left reasoning",
                confidence=0.5,
            ),
            DebateArgument(
                role=DebateRole.RIGHT,
                position="Right position",
                reasoning="Right reasoning",
                confidence=0.9,
            ),
        ]

        decision = judge.evaluate(topic, arguments)

        assert decision.outcome == DebateOutcome.RIGHT_WINS

    def test_evaluate_template_synthesis(self):
        """Test template evaluation resulting in SYNTHESIS."""
        judge = JudgeAgent(trace_id="test-123", enable_llm=False)
        topic = DebateTopic(question="Test question")
        arguments = [
            DebateArgument(
                role=DebateRole.LEFT,
                position="Left position",
                reasoning="Left reasoning",
                confidence=0.75,
            ),
            DebateArgument(
                role=DebateRole.RIGHT,
                position="Right position",
                reasoning="Right reasoning",
                confidence=0.78,
            ),
        ]

        decision = judge.evaluate(topic, arguments)

        assert decision.outcome == DebateOutcome.SYNTHESIS

    def test_build_evaluation_prompt(self):
        """Test evaluation prompt building."""
        judge = JudgeAgent(trace_id="test-123", enable_llm=False)
        topic = DebateTopic(
            question="Test question",
            context={"key": "value"},
            risk_level="high",
            category=DebateCategory.SECURITY,
        )
        arguments = [
            DebateArgument(
                role=DebateRole.LEFT,
                position="Left position",
                reasoning="Left reasoning",
                round_number=1,
            ),
            DebateArgument(
                role=DebateRole.RIGHT,
                position="Right position",
                reasoning="Right reasoning",
                round_number=1,
            ),
        ]

        prompt = judge._build_evaluation_prompt(topic, arguments)

        assert "Test question" in prompt
        assert "high" in prompt
        assert "security" in prompt
        assert "Left position" in prompt
        assert "Right position" in prompt

    def test_parse_decision_response_valid_json(self):
        """Test parsing valid JSON decision response."""
        judge = JudgeAgent(trace_id="test-123", enable_llm=False)
        response = '''
        {
            "outcome": "left_wins",
            "winning_position": "Test position",
            "rationale": "Test rationale",
            "strengths_left": ["s1"],
            "strengths_right": ["s2"],
            "weaknesses_left": ["w1"],
            "weaknesses_right": ["w2"],
            "confidence": 0.85,
            "requires_human_review": false,
            "action_items": ["action1"]
        }
        '''

        decision = judge._parse_decision_response(response)

        assert decision.outcome == DebateOutcome.LEFT_WINS
        assert decision.winning_position == "Test position"
        assert decision.confidence == 0.85
        assert decision.requires_human_review is False

    def test_parse_decision_response_invalid_json(self):
        """Test parsing invalid JSON falls back to INCONCLUSIVE."""
        judge = JudgeAgent(trace_id="test-123", enable_llm=False)
        response = "This is not valid JSON"

        decision = judge._parse_decision_response(response)

        assert decision.outcome == DebateOutcome.INCONCLUSIVE
        assert decision.requires_human_review is True
        assert decision.confidence == 0.3


class TestDebateEngine:
    """Tests for DebateEngine class."""

    def test_init(self):
        """Test initialization."""
        engine = DebateEngine(
            trace_id="test-123",
            max_rounds=2,
            enable_llm=False,
        )

        assert engine.trace_id == "test-123"
        assert engine.max_rounds == 2
        assert engine.enable_llm is False
        assert engine.left_agent.role == DebateRole.LEFT
        assert engine.right_agent.role == DebateRole.RIGHT

    def test_debate_basic(self):
        """Test basic debate execution."""
        engine = DebateEngine(
            trace_id="test-123",
            max_rounds=1,
            enable_llm=False,
        )
        topic = DebateTopic(
            question="Should we use microservices?",
            risk_level="high",
        )

        result = engine.debate(topic)

        assert result.topic == topic
        assert result.rounds_completed == 1
        assert len(result.arguments) == 2
        assert result.decision is not None
        assert result.trace_id == "test-123"
        assert result.debate_time_ms > 0

    def test_debate_multiple_rounds(self):
        """Test debate with multiple rounds."""
        engine = DebateEngine(
            trace_id="test-123",
            max_rounds=3,
            enable_llm=False,
        )
        topic = DebateTopic(question="Test question")

        result = engine.debate(topic)

        assert result.rounds_completed == 3
        assert len(result.arguments) == 6

    def test_debate_arguments_alternate(self):
        """Test that arguments alternate between LEFT and RIGHT."""
        engine = DebateEngine(
            trace_id="test-123",
            max_rounds=2,
            enable_llm=False,
        )
        topic = DebateTopic(question="Test question")

        result = engine.debate(topic)

        assert result.arguments[0].role == DebateRole.LEFT
        assert result.arguments[1].role == DebateRole.RIGHT
        assert result.arguments[2].role == DebateRole.LEFT
        assert result.arguments[3].role == DebateRole.RIGHT


class TestShouldTriggerDebate:
    """Tests for should_trigger_debate function."""

    @patch.dict(os.environ, {"USE_DEBATE_ENGINE": "false"})
    def test_disabled_returns_false(self):
        """Test that disabled engine returns False."""
        import debate_engine
        debate_engine.USE_DEBATE_ENGINE = False

        result = should_trigger_debate(risk_level="critical")

        assert result is False

    @patch.dict(os.environ, {"USE_DEBATE_ENGINE": "true"})
    def test_high_risk_triggers_debate(self):
        """Test that high risk triggers debate."""
        import debate_engine
        debate_engine.USE_DEBATE_ENGINE = True

        result = should_trigger_debate(risk_level="high")

        assert result is True

    @patch.dict(os.environ, {"USE_DEBATE_ENGINE": "true"})
    def test_critical_risk_triggers_debate(self):
        """Test that critical risk triggers debate."""
        import debate_engine
        debate_engine.USE_DEBATE_ENGINE = True

        result = should_trigger_debate(risk_level="critical")

        assert result is True

    @patch.dict(os.environ, {"USE_DEBATE_ENGINE": "true"})
    def test_architecture_category_triggers_debate(self):
        """Test that architecture category triggers debate."""
        import debate_engine
        debate_engine.USE_DEBATE_ENGINE = True

        result = should_trigger_debate(
            risk_level="low",
            category="architecture",
        )

        assert result is True

    @patch.dict(os.environ, {"USE_DEBATE_ENGINE": "true"})
    def test_security_category_triggers_debate(self):
        """Test that security category triggers debate."""
        import debate_engine
        debate_engine.USE_DEBATE_ENGINE = True

        result = should_trigger_debate(
            risk_level="low",
            category="security",
        )

        assert result is True

    @patch.dict(os.environ, {"USE_DEBATE_ENGINE": "true"})
    def test_privacy_category_triggers_debate(self):
        """Test that privacy category triggers debate."""
        import debate_engine
        debate_engine.USE_DEBATE_ENGINE = True

        result = should_trigger_debate(
            risk_level="low",
            category="privacy",
        )

        assert result is True

    @patch.dict(os.environ, {"USE_DEBATE_ENGINE": "true"})
    def test_force_debate_triggers(self):
        """Test that force_debate=True triggers debate."""
        import debate_engine
        debate_engine.USE_DEBATE_ENGINE = True

        result = should_trigger_debate(
            risk_level="low",
            force_debate=True,
        )

        assert result is True

    @patch.dict(os.environ, {"USE_DEBATE_ENGINE": "true"})
    def test_low_risk_no_category_no_trigger(self):
        """Test that low risk without special category doesn't trigger."""
        import debate_engine
        debate_engine.USE_DEBATE_ENGINE = True

        result = should_trigger_debate(
            risk_level="low",
            category="implementation",
        )

        assert result is False


class TestCreateDebateTopicFromPlan:
    """Tests for create_debate_topic_from_plan function."""

    def test_basic_creation(self):
        """Test basic topic creation from plan."""
        topic = create_debate_topic_from_plan(
            goal="Implement user authentication",
            risk_level="high",
            context={"team_size": 5},
        )

        assert "Implement user authentication" in topic.question
        assert topic.risk_level == "high"
        assert topic.context["team_size"] == 5
        assert topic.category == DebateCategory.STRATEGY

    def test_architecture_category(self):
        """Test topic creation with architecture category."""
        topic = create_debate_topic_from_plan(
            goal="Design API",
            risk_level="medium",
            context={},
            category="architecture",
        )

        assert topic.category == DebateCategory.ARCHITECTURE

    def test_security_category(self):
        """Test topic creation with security category."""
        topic = create_debate_topic_from_plan(
            goal="Implement auth",
            risk_level="high",
            context={},
            category="security",
        )

        assert topic.category == DebateCategory.SECURITY

    def test_unknown_category_defaults_to_strategy(self):
        """Test that unknown category defaults to STRATEGY."""
        topic = create_debate_topic_from_plan(
            goal="Test goal",
            risk_level="low",
            context={},
            category="unknown_category",
        )

        assert topic.category == DebateCategory.STRATEGY

    def test_all_categories(self):
        """Test all valid categories."""
        categories = [
            ("architecture", DebateCategory.ARCHITECTURE),
            ("security", DebateCategory.SECURITY),
            ("performance", DebateCategory.PERFORMANCE),
            ("cost", DebateCategory.COST),
            ("privacy", DebateCategory.PRIVACY),
            ("strategy", DebateCategory.STRATEGY),
            ("implementation", DebateCategory.IMPLEMENTATION),
        ]

        for cat_str, cat_enum in categories:
            topic = create_debate_topic_from_plan(
                goal="Test",
                risk_level="low",
                context={},
                category=cat_str,
            )
            assert topic.category == cat_enum, f"Failed for {cat_str}"


import pytest

# Check if llm module is available for integration tests
try:
    from llm.client import get_client_for_task
    HAS_LLM_MODULE = True
except ImportError:
    HAS_LLM_MODULE = False


@pytest.mark.skipif(not HAS_LLM_MODULE, reason="llm module not available")
class TestLLMIntegration:
    """Tests for LLM integration (mocked). Requires llm module in path."""

    @patch("llm.client.get_client_for_task")
    def test_debate_agent_llm_success(self, mock_get_client):
        """Test successful LLM-based argument generation."""
        mock_client = MagicMock()
        mock_client.generate.return_value = '''
        {
            "position": "LLM position",
            "reasoning": "LLM reasoning",
            "evidence": ["evidence1"],
            "counterpoints": [],
            "confidence": 0.9
        }
        '''
        mock_get_client.return_value = mock_client

        import debate_engine
        debate_engine.DEBATE_ENGINE_ENABLE_LLM = True

        agent = DebateAgent(
            role=DebateRole.LEFT,
            trace_id="test-123",
            enable_llm=True,
        )
        agent.enable_llm = True
        topic = DebateTopic(question="Test question")

        arg = agent._generate_llm_argument(topic, [], round_number=1)

        assert arg.position == "LLM position"
        assert arg.reasoning == "LLM reasoning"
        assert arg.confidence == 0.9

    @patch("llm.client.get_client_for_task")
    def test_debate_agent_llm_failure_fallback(self, mock_get_client):
        """Test fallback to template when LLM fails."""
        mock_get_client.side_effect = Exception("LLM error")

        import debate_engine
        debate_engine.DEBATE_ENGINE_ENABLE_LLM = True

        agent = DebateAgent(
            role=DebateRole.LEFT,
            trace_id="test-123",
            enable_llm=True,
        )
        agent.enable_llm = True
        topic = DebateTopic(question="Test question")

        arg = agent.generate_argument(topic, [], round_number=1)

        assert arg.role == DebateRole.LEFT
        assert "conventional" in arg.position.lower()

    @patch("llm.client.get_client_for_task")
    def test_judge_agent_llm_success(self, mock_get_client):
        """Test successful LLM-based judge decision."""
        mock_client = MagicMock()
        mock_client.generate.return_value = '''
        {
            "outcome": "synthesis",
            "winning_position": "Combined approach",
            "rationale": "Both have merits",
            "strengths_left": ["s1"],
            "strengths_right": ["s2"],
            "weaknesses_left": [],
            "weaknesses_right": [],
            "confidence": 0.85,
            "requires_human_review": false,
            "action_items": []
        }
        '''
        mock_get_client.return_value = mock_client

        import debate_engine
        debate_engine.DEBATE_ENGINE_ENABLE_LLM = True

        judge = JudgeAgent(trace_id="test-123", enable_llm=True)
        judge.enable_llm = True
        topic = DebateTopic(question="Test question")
        arguments = [
            DebateArgument(
                role=DebateRole.LEFT,
                position="Left",
                reasoning="Left reasoning",
            ),
            DebateArgument(
                role=DebateRole.RIGHT,
                position="Right",
                reasoning="Right reasoning",
            ),
        ]

        decision = judge._generate_llm_decision(topic, arguments)

        assert decision.outcome == DebateOutcome.SYNTHESIS
        assert decision.winning_position == "Combined approach"
        assert decision.confidence == 0.85
