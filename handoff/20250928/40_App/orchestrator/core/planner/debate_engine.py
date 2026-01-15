"""
F-5: Debate Engine v2 - Adversarial Collaboration for High-Risk Decisions

EPIC F Phase F-5: Debate Engine v2 Implementation

This module implements the Debate Engine v2 as described in Blueprint Section 7
"Adversarial Collaboration". It provides a structured debate mechanism where:
- Left Agent proposes one approach/solution
- Right Agent proposes an alternative approach (adversarial)
- Judge Agent evaluates both proposals and makes the final decision

Blueprint Alignment:
- Section 7 "Adversarial Collaboration" - Left vs Right -> Judge
- Section 3.3 "Agent Catalog V2" - Judge Agent, Debate Agent (Left/Right)

Use Cases:
- High-risk tasks (architecture decisions, security choices)
- Cost optimization strategies
- Privacy-sensitive decisions
- Complex reasoning tasks with multiple valid approaches

Usage:
    from core.planner.debate_engine import DebateEngine, DebateTopic

    engine = DebateEngine(trace_id="abc123")
    result = await engine.debate(
        topic=DebateTopic(
            question="Should we use microservices or monolith?",
            context={"project_size": "large", "team_size": 10},
            risk_level="high"
        )
    )
"""

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from common.config.settings import settings
from memory.memory_integration import save_debate_result

logger = logging.getLogger(__name__)


# Feature flags for Debate Engine (from centralized settings)
USE_DEBATE_ENGINE = settings.use_debate_engine
DEBATE_ENGINE_ENABLE_LLM = settings.debate_engine_enable_llm
DEBATE_ENGINE_MAX_ROUNDS = settings.debate_engine_max_rounds


class DebateRole(Enum):
    """
    Roles in the debate process.

    - LEFT: Proposes the primary/conventional approach
    - RIGHT: Proposes an alternative/adversarial approach
    - JUDGE: Evaluates both sides and makes the final decision
    """
    LEFT = "left"
    RIGHT = "right"
    JUDGE = "judge"


class DebateOutcome(Enum):
    """
    Possible outcomes of a debate.

    - LEFT_WINS: Judge favors the Left Agent's proposal
    - RIGHT_WINS: Judge favors the Right Agent's proposal
    - SYNTHESIS: Judge combines elements from both proposals
    - INCONCLUSIVE: No clear winner, requires human intervention
    """
    LEFT_WINS = "left_wins"
    RIGHT_WINS = "right_wins"
    SYNTHESIS = "synthesis"
    INCONCLUSIVE = "inconclusive"


class DebateCategory(Enum):
    """
    Categories of debate topics.

    These categories help determine the appropriate debate strategy
    and evaluation criteria.
    """
    ARCHITECTURE = "architecture"
    SECURITY = "security"
    PERFORMANCE = "performance"
    COST = "cost"
    PRIVACY = "privacy"
    STRATEGY = "strategy"
    IMPLEMENTATION = "implementation"


@dataclass
class DebateTopic:
    """
    A topic for debate.

    Attributes:
        question: The main question to debate
        context: Additional context for the debate
        risk_level: Risk level of the decision (low, medium, high, critical)
        category: Category of the debate topic
        constraints: Any constraints that must be respected
        success_criteria: Criteria for evaluating proposals
    """
    question: str
    context: Dict[str, Any] = field(default_factory=dict)
    risk_level: str = "medium"
    category: DebateCategory = DebateCategory.STRATEGY
    constraints: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "question": self.question,
            "context": self.context,
            "risk_level": self.risk_level,
            "category": self.category.value,
            "constraints": self.constraints,
            "success_criteria": self.success_criteria,
        }


@dataclass
class DebateArgument:
    """
    An argument made by a debate agent.

    Attributes:
        role: The role of the agent making the argument
        position: The main position/proposal
        reasoning: Detailed reasoning supporting the position
        evidence: Evidence or examples supporting the argument
        counterpoints: Anticipated counterarguments and rebuttals
        confidence: Confidence score (0.0 to 1.0)
        round_number: Which round this argument was made in
    """
    role: DebateRole
    position: str
    reasoning: str
    evidence: List[str] = field(default_factory=list)
    counterpoints: List[str] = field(default_factory=list)
    confidence: float = 0.8
    round_number: int = 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "role": self.role.value,
            "position": self.position,
            "reasoning": self.reasoning,
            "evidence": self.evidence,
            "counterpoints": self.counterpoints,
            "confidence": self.confidence,
            "round_number": self.round_number,
        }


@dataclass
class JudgeDecision:
    """
    The Judge Agent's final decision.

    Attributes:
        outcome: The debate outcome
        winning_position: The winning position (or synthesized position)
        rationale: Detailed rationale for the decision
        strengths_left: Strengths of the Left Agent's argument
        strengths_right: Strengths of the Right Agent's argument
        weaknesses_left: Weaknesses of the Left Agent's argument
        weaknesses_right: Weaknesses of the Right Agent's argument
        confidence: Confidence in the decision (0.0 to 1.0)
        requires_human_review: Whether human review is recommended
        action_items: Recommended next steps
    """
    outcome: DebateOutcome
    winning_position: str
    rationale: str
    strengths_left: List[str] = field(default_factory=list)
    strengths_right: List[str] = field(default_factory=list)
    weaknesses_left: List[str] = field(default_factory=list)
    weaknesses_right: List[str] = field(default_factory=list)
    confidence: float = 0.8
    requires_human_review: bool = False
    action_items: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "outcome": self.outcome.value,
            "winning_position": self.winning_position,
            "rationale": self.rationale,
            "strengths_left": self.strengths_left,
            "strengths_right": self.strengths_right,
            "weaknesses_left": self.weaknesses_left,
            "weaknesses_right": self.weaknesses_right,
            "confidence": self.confidence,
            "requires_human_review": self.requires_human_review,
            "action_items": self.action_items,
        }


@dataclass
class DebateResult:
    """
    Complete result of a debate session.

    Attributes:
        topic: The original debate topic
        arguments: All arguments made during the debate
        decision: The Judge's final decision
        rounds_completed: Number of debate rounds completed
        debate_time_ms: Total time taken for the debate
        trace_id: Trace ID for telemetry
    """
    topic: DebateTopic
    arguments: List[DebateArgument]
    decision: JudgeDecision
    rounds_completed: int
    debate_time_ms: float
    trace_id: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "topic": self.topic.to_dict(),
            "arguments": [arg.to_dict() for arg in self.arguments],
            "decision": self.decision.to_dict(),
            "rounds_completed": self.rounds_completed,
            "debate_time_ms": self.debate_time_ms,
            "trace_id": self.trace_id,
        }


class DebateAgent:
    """
    A debate agent that can argue for a position.

    This agent can take either the LEFT or RIGHT role and will
    generate arguments supporting its assigned position.
    """

    # System prompts for each role
    SYSTEM_PROMPTS = {
        DebateRole.LEFT: """You are the Left Agent in a structured debate.
Your role is to propose and defend the PRIMARY or CONVENTIONAL approach.
You should:
1. Present a clear, well-reasoned position
2. Provide evidence and examples supporting your approach
3. Anticipate and address potential counterarguments
4. Be objective but advocate strongly for your position
5. Acknowledge limitations honestly

Format your response as JSON with these fields:
- position: Your main proposal (1-2 sentences)
- reasoning: Detailed reasoning (2-3 paragraphs)
- evidence: List of supporting evidence/examples
- counterpoints: Anticipated counterarguments and your rebuttals
- confidence: Your confidence score (0.0 to 1.0)""",

        DebateRole.RIGHT: """You are the Right Agent in a structured debate.
Your role is to propose and defend an ALTERNATIVE or ADVERSARIAL approach.
You should:
1. Challenge the conventional wisdom
2. Present a creative or unconventional solution
3. Highlight risks or blind spots in the primary approach
4. Provide evidence for why your alternative is viable
5. Be constructively adversarial, not contrarian for its own sake

Format your response as JSON with these fields:
- position: Your alternative proposal (1-2 sentences)
- reasoning: Detailed reasoning (2-3 paragraphs)
- evidence: List of supporting evidence/examples
- counterpoints: Anticipated counterarguments and your rebuttals
- confidence: Your confidence score (0.0 to 1.0)""",
    }

    def __init__(
        self,
        role: DebateRole,
        trace_id: str,
        enable_llm: bool = True,
    ):
        """
        Initialize a debate agent.

        Args:
            role: The role of this agent (LEFT or RIGHT)
            trace_id: Trace ID for telemetry
            enable_llm: Whether to use LLM for argument generation
        """
        if role == DebateRole.JUDGE:
            raise ValueError("DebateAgent cannot have JUDGE role")

        self.role = role
        self.trace_id = trace_id
        self.enable_llm = enable_llm and DEBATE_ENGINE_ENABLE_LLM
        self._executor = ThreadPoolExecutor(max_workers=1)

    def generate_argument(
        self,
        topic: DebateTopic,
        opponent_arguments: List[DebateArgument],
        round_number: int = 1,
    ) -> DebateArgument:
        """
        Generate an argument for the given topic.

        Args:
            topic: The debate topic
            opponent_arguments: Arguments made by the opponent
            round_number: Current round number

        Returns:
            DebateArgument with the agent's position
        """
        if not self.enable_llm:
            return self._generate_template_argument(topic, round_number)

        try:
            return self._generate_llm_argument(
                topic, opponent_arguments, round_number
            )
        except Exception as e:
            logger.warning(
                f"[DebateAgent] LLM argument generation failed: {e}, "
                f"falling back to template"
            )
            return self._generate_template_argument(topic, round_number)

    def _generate_llm_argument(
        self,
        topic: DebateTopic,
        opponent_arguments: List[DebateArgument],
        round_number: int,
    ) -> DebateArgument:
        """Generate argument using LLM."""
        from llm.client import get_client_for_task
        from core.routing import TaskType

        client = get_client_for_task(TaskType.ANALYSIS)

        system_prompt = self.SYSTEM_PROMPTS[self.role]
        user_prompt = self._build_user_prompt(
            topic, opponent_arguments, round_number
        )

        response = client.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            trace_id=self.trace_id,
        )

        return self._parse_argument_response(response, round_number)

    def _build_user_prompt(
        self,
        topic: DebateTopic,
        opponent_arguments: List[DebateArgument],
        round_number: int,
    ) -> str:
        """Build the user prompt for argument generation."""
        prompt_parts = [
            f"## Debate Topic\n{topic.question}",
            f"\n## Context\n{topic.context}",
            f"\n## Risk Level: {topic.risk_level}",
            f"\n## Category: {topic.category.value}",
        ]

        if topic.constraints:
            prompt_parts.append(
                "\n## Constraints\n" +
                "\n".join(f"- {c}" for c in topic.constraints)
            )

        if topic.success_criteria:
            prompt_parts.append(
                "\n## Success Criteria\n" +
                "\n".join(f"- {c}" for c in topic.success_criteria)
            )

        if opponent_arguments:
            prompt_parts.append("\n## Opponent's Arguments")
            for arg in opponent_arguments:
                prompt_parts.append(
                    f"\n### Round {arg.round_number} ({arg.role.value})\n"
                    f"Position: {arg.position}\n"
                    f"Reasoning: {arg.reasoning}"
                )

        prompt_parts.append(
            f"\n## Your Task\n"
            f"This is round {round_number}. Generate your argument."
        )

        return "\n".join(prompt_parts)

    def _parse_argument_response(
        self,
        response: str,
        round_number: int,
    ) -> DebateArgument:
        """Parse LLM response into DebateArgument."""
        import json

        try:
            # Try to extract JSON from response
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                data = json.loads(response[json_start:json_end])
            else:
                data = json.loads(response)

            return DebateArgument(
                role=self.role,
                position=data.get("position", ""),
                reasoning=data.get("reasoning", ""),
                evidence=data.get("evidence", []),
                counterpoints=data.get("counterpoints", []),
                confidence=float(data.get("confidence", 0.8)),
                round_number=round_number,
            )
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"[DebateAgent] Failed to parse response: {e}")
            # Fallback: treat entire response as reasoning
            return DebateArgument(
                role=self.role,
                position=f"{self.role.value.title()} position",
                reasoning=response[:1000] if response else "No reasoning",
                evidence=[],
                counterpoints=[],
                confidence=0.5,
                round_number=round_number,
            )

    def _generate_template_argument(
        self,
        topic: DebateTopic,
        round_number: int,
    ) -> DebateArgument:
        """Generate a template-based argument when LLM is disabled."""
        if self.role == DebateRole.LEFT:
            position = "Recommend the conventional, well-established approach"
            reasoning = (
                f"For the question '{topic.question}', the conventional "
                f"approach offers proven reliability and lower risk. "
                f"Given the {topic.risk_level} risk level, stability "
                f"should be prioritized."
            )
        else:
            position = "Recommend an innovative, alternative approach"
            reasoning = (
                f"For the question '{topic.question}', an alternative "
                f"approach may offer better long-term benefits. "
                f"The conventional approach may have hidden costs or "
                f"limitations that should be considered."
            )

        return DebateArgument(
            role=self.role,
            position=position,
            reasoning=reasoning,
            evidence=["Template-based argument - LLM disabled"],
            counterpoints=[],
            confidence=0.6,
            round_number=round_number,
        )


class JudgeAgent:
    """
    The Judge Agent that evaluates debate arguments and makes decisions.

    The Judge Agent is responsible for:
    1. Evaluating arguments from both Left and Right agents
    2. Identifying strengths and weaknesses of each position
    3. Making a final decision (LEFT_WINS, RIGHT_WINS, SYNTHESIS, INCONCLUSIVE)
    4. Providing detailed rationale for the decision
    """

    SYSTEM_PROMPT = """You are the Judge Agent in a structured debate.
Your role is to evaluate arguments from both sides and make a fair decision.
You should:
1. Objectively analyze the strengths and weaknesses of each position
2. Consider the context, constraints, and success criteria
3. Make a clear decision: LEFT_WINS, RIGHT_WINS, SYNTHESIS, or INCONCLUSIVE
4. Provide detailed rationale for your decision
5. Recommend action items based on the winning position

Format your response as JSON with these fields:
- outcome: One of "left_wins", "right_wins", "synthesis", "inconclusive"
- winning_position: The winning position or synthesized position
- rationale: Detailed rationale for your decision (2-3 paragraphs)
- strengths_left: List of strengths in Left's argument
- strengths_right: List of strengths in Right's argument
- weaknesses_left: List of weaknesses in Left's argument
- weaknesses_right: List of weaknesses in Right's argument
- confidence: Your confidence in this decision (0.0 to 1.0)
- requires_human_review: Boolean - true if human review is recommended
- action_items: List of recommended next steps"""

    def __init__(
        self,
        trace_id: str,
        enable_llm: bool = True,
    ):
        """
        Initialize the Judge Agent.

        Args:
            trace_id: Trace ID for telemetry
            enable_llm: Whether to use LLM for decision making
        """
        self.trace_id = trace_id
        self.enable_llm = enable_llm and DEBATE_ENGINE_ENABLE_LLM

    def evaluate(
        self,
        topic: DebateTopic,
        arguments: List[DebateArgument],
    ) -> JudgeDecision:
        """
        Evaluate the debate and make a decision.

        Args:
            topic: The debate topic
            arguments: All arguments from both sides

        Returns:
            JudgeDecision with the final verdict
        """
        if not self.enable_llm:
            return self._generate_template_decision(topic, arguments)

        try:
            return self._generate_llm_decision(topic, arguments)
        except Exception as e:
            logger.warning(
                f"[JudgeAgent] LLM decision failed: {e}, "
                f"falling back to template"
            )
            return self._generate_template_decision(topic, arguments)

    def _generate_llm_decision(
        self,
        topic: DebateTopic,
        arguments: List[DebateArgument],
    ) -> JudgeDecision:
        """Generate decision using LLM."""
        from llm.client import get_client_for_task
        from core.routing import TaskType

        client = get_client_for_task(TaskType.ANALYSIS)

        user_prompt = self._build_evaluation_prompt(topic, arguments)

        response = client.generate(
            system_prompt=self.SYSTEM_PROMPT,
            user_prompt=user_prompt,
            trace_id=self.trace_id,
        )

        return self._parse_decision_response(response)

    def _build_evaluation_prompt(
        self,
        topic: DebateTopic,
        arguments: List[DebateArgument],
    ) -> str:
        """Build the evaluation prompt for the Judge."""
        prompt_parts = [
            f"## Debate Topic\n{topic.question}",
            f"\n## Context\n{topic.context}",
            f"\n## Risk Level: {topic.risk_level}",
            f"\n## Category: {topic.category.value}",
        ]

        if topic.constraints:
            prompt_parts.append(
                "\n## Constraints\n" +
                "\n".join(f"- {c}" for c in topic.constraints)
            )

        if topic.success_criteria:
            prompt_parts.append(
                "\n## Success Criteria\n" +
                "\n".join(f"- {c}" for c in topic.success_criteria)
            )

        # Group arguments by role
        left_args = [a for a in arguments if a.role == DebateRole.LEFT]
        right_args = [a for a in arguments if a.role == DebateRole.RIGHT]

        prompt_parts.append("\n## Left Agent's Arguments")
        for arg in left_args:
            prompt_parts.append(
                f"\n### Round {arg.round_number}\n"
                f"Position: {arg.position}\n"
                f"Reasoning: {arg.reasoning}\n"
                f"Evidence: {arg.evidence}\n"
                f"Confidence: {arg.confidence}"
            )

        prompt_parts.append("\n## Right Agent's Arguments")
        for arg in right_args:
            prompt_parts.append(
                f"\n### Round {arg.round_number}\n"
                f"Position: {arg.position}\n"
                f"Reasoning: {arg.reasoning}\n"
                f"Evidence: {arg.evidence}\n"
                f"Confidence: {arg.confidence}"
            )

        prompt_parts.append(
            "\n## Your Task\n"
            "Evaluate both sides and make your decision."
        )

        return "\n".join(prompt_parts)

    def _parse_decision_response(self, response: str) -> JudgeDecision:
        """Parse LLM response into JudgeDecision."""
        import json

        try:
            # Try to extract JSON from response
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                data = json.loads(response[json_start:json_end])
            else:
                data = json.loads(response)

            outcome_str = data.get("outcome", "inconclusive").lower()
            outcome_map = {
                "left_wins": DebateOutcome.LEFT_WINS,
                "right_wins": DebateOutcome.RIGHT_WINS,
                "synthesis": DebateOutcome.SYNTHESIS,
                "inconclusive": DebateOutcome.INCONCLUSIVE,
            }
            outcome = outcome_map.get(outcome_str, DebateOutcome.INCONCLUSIVE)

            return JudgeDecision(
                outcome=outcome,
                winning_position=data.get("winning_position", ""),
                rationale=data.get("rationale", ""),
                strengths_left=data.get("strengths_left", []),
                strengths_right=data.get("strengths_right", []),
                weaknesses_left=data.get("weaknesses_left", []),
                weaknesses_right=data.get("weaknesses_right", []),
                confidence=float(data.get("confidence", 0.5)),
                requires_human_review=data.get("requires_human_review", False),
                action_items=data.get("action_items", []),
            )
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"[JudgeAgent] Failed to parse response: {e}")
            return JudgeDecision(
                outcome=DebateOutcome.INCONCLUSIVE,
                winning_position="Unable to determine",
                rationale=response[:500] if response else "Parse error",
                confidence=0.3,
                requires_human_review=True,
            )

    def _generate_template_decision(
        self,
        topic: DebateTopic,
        arguments: List[DebateArgument],
    ) -> JudgeDecision:
        """Generate a template-based decision when LLM is disabled."""
        left_args = [a for a in arguments if a.role == DebateRole.LEFT]
        right_args = [a for a in arguments if a.role == DebateRole.RIGHT]

        # Simple heuristic: compare confidence scores
        left_confidence = (
            sum(a.confidence for a in left_args) / len(left_args)
            if left_args else 0.5
        )
        right_confidence = (
            sum(a.confidence for a in right_args) / len(right_args)
            if right_args else 0.5
        )

        if abs(left_confidence - right_confidence) < 0.1:
            outcome = DebateOutcome.SYNTHESIS
            winning_position = "Combine elements from both approaches"
        elif left_confidence > right_confidence:
            outcome = DebateOutcome.LEFT_WINS
            winning_position = (
                left_args[0].position if left_args else "Left position"
            )
        else:
            outcome = DebateOutcome.RIGHT_WINS
            winning_position = (
                right_args[0].position if right_args else "Right position"
            )

        return JudgeDecision(
            outcome=outcome,
            winning_position=winning_position,
            rationale=(
                f"Template-based decision. Left confidence: {left_confidence:.2f}, "
                f"Right confidence: {right_confidence:.2f}. "
                f"LLM evaluation was disabled."
            ),
            strengths_left=["Template evaluation - details unavailable"],
            strengths_right=["Template evaluation - details unavailable"],
            confidence=0.5,
            requires_human_review=True,
            action_items=["Review this decision manually"],
        )


class DebateEngine:
    """
    The main Debate Engine that orchestrates the debate process.

    This engine coordinates:
    1. Creating Left and Right agents
    2. Running multiple debate rounds
    3. Having the Judge evaluate and decide
    4. Producing the final DebateResult
    """

    def __init__(
        self,
        trace_id: str,
        max_rounds: int = DEBATE_ENGINE_MAX_ROUNDS,
        enable_llm: bool = True,
    ):
        """
        Initialize the Debate Engine.

        Args:
            trace_id: Trace ID for telemetry
            max_rounds: Maximum number of debate rounds
            enable_llm: Whether to use LLM for agents
        """
        self.trace_id = trace_id
        self.max_rounds = max_rounds
        self.enable_llm = enable_llm and DEBATE_ENGINE_ENABLE_LLM

        self.left_agent = DebateAgent(
            role=DebateRole.LEFT,
            trace_id=trace_id,
            enable_llm=self.enable_llm,
        )
        self.right_agent = DebateAgent(
            role=DebateRole.RIGHT,
            trace_id=trace_id,
            enable_llm=self.enable_llm,
        )
        self.judge = JudgeAgent(
            trace_id=trace_id,
            enable_llm=self.enable_llm,
        )

    def debate(self, topic: DebateTopic) -> DebateResult:
        """
        Run a complete debate on the given topic.

        Args:
            topic: The topic to debate

        Returns:
            DebateResult with all arguments and the final decision
        """
        start_time = time.time()
        arguments: List[DebateArgument] = []

        logger.info(
            f"[DebateEngine] Starting debate on: {topic.question[:50]}... "
            f"(trace_id={self.trace_id})"
        )

        # Run debate rounds
        for round_num in range(1, self.max_rounds + 1):
            logger.info(f"[DebateEngine] Round {round_num}/{self.max_rounds}")

            # Left agent argues first
            left_opponent_args = [
                a for a in arguments if a.role == DebateRole.RIGHT
            ]
            left_arg = self.left_agent.generate_argument(
                topic, left_opponent_args, round_num
            )
            arguments.append(left_arg)
            logger.debug(
                f"[DebateEngine] Left position: {left_arg.position[:50]}..."
            )

            # Right agent responds
            right_opponent_args = [
                a for a in arguments if a.role == DebateRole.LEFT
            ]
            right_arg = self.right_agent.generate_argument(
                topic, right_opponent_args, round_num
            )
            arguments.append(right_arg)
            logger.debug(
                f"[DebateEngine] Right position: {right_arg.position[:50]}..."
            )

        # Judge evaluates
        logger.info("[DebateEngine] Judge evaluating arguments...")
        decision = self.judge.evaluate(topic, arguments)
        logger.info(
            f"[DebateEngine] Decision: {decision.outcome.value} "
            f"(confidence={decision.confidence:.2f})"
        )

        elapsed_ms = (time.time() - start_time) * 1000

        # EPIC G: Save debate result to Agent Interaction Memory
        # This is controlled by ENABLE_MEMORY_V2_DEBATE feature flag (checked internally)
        debate_id = f"debate_{self.trace_id}_{int(time.time())}"
        save_debate_result(
            debate_id=debate_id,
            trace_id=self.trace_id,
            topic=topic.question,
            left_agent="left_agent",
            right_agent="right_agent",
            arguments=[arg.to_dict() for arg in arguments],
            decision=decision.to_dict(),
            outcome=decision.outcome.value,
            rounds_completed=self.max_rounds,
            debate_time_ms=elapsed_ms,
        )

        return DebateResult(
            topic=topic,
            arguments=arguments,
            decision=decision,
            rounds_completed=self.max_rounds,
            debate_time_ms=elapsed_ms,
            trace_id=self.trace_id,
        )

    async def debate_async(self, topic: DebateTopic) -> DebateResult:
        """
        Run a debate asynchronously.

        Args:
            topic: The topic to debate

        Returns:
            DebateResult with all arguments and the final decision
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.debate, topic)


def should_trigger_debate(
    risk_level: str,
    category: Optional[str] = None,
    force_debate: bool = False,
) -> bool:
    """
    Determine if a debate should be triggered for a decision.

    Args:
        risk_level: Risk level of the decision
        category: Category of the decision
        force_debate: Force debate regardless of other factors

    Returns:
        True if debate should be triggered
    """
    if not USE_DEBATE_ENGINE:
        return False

    if force_debate:
        return True

    # High-risk and critical decisions always trigger debate
    if risk_level in ("high", "critical"):
        return True

    # Certain categories always trigger debate
    debate_categories = {"architecture", "security", "privacy"}
    if category and category.lower() in debate_categories:
        return True

    return False


def create_debate_topic_from_plan(
    goal: str,
    risk_level: str,
    context: Dict[str, Any],
    category: str = "strategy",
) -> DebateTopic:
    """
    Create a DebateTopic from planning context.

    Args:
        goal: The planning goal
        risk_level: Risk level of the plan
        context: Additional context
        category: Category of the decision

    Returns:
        DebateTopic ready for debate
    """
    category_map = {
        "architecture": DebateCategory.ARCHITECTURE,
        "security": DebateCategory.SECURITY,
        "performance": DebateCategory.PERFORMANCE,
        "cost": DebateCategory.COST,
        "privacy": DebateCategory.PRIVACY,
        "strategy": DebateCategory.STRATEGY,
        "implementation": DebateCategory.IMPLEMENTATION,
    }

    return DebateTopic(
        question=f"What is the best approach to: {goal}",
        context=context,
        risk_level=risk_level,
        category=category_map.get(category.lower(), DebateCategory.STRATEGY),
        constraints=[],
        success_criteria=[],
    )
