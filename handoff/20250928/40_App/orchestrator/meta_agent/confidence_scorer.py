"""
Confidence Scorer - Implementation Plan Confidence Assessment

This module implements confidence scoring for implementation plans,
providing a quantitative assessment of plan feasibility and identifying
potential issues or questions that need clarification.

Issue: #1822 - 整合開發工具 (Integrate Development Tools)
Milestone: M5 - Meta Agent 優化

Flow:
    ParsedGoal → TaskPlan → ConfidenceScorer → ScoredPlan (with confidence & questions)
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from .goal_parser import GoalType
from .task_planner import TaskPlan

logger = logging.getLogger(__name__)


class ConfidenceLevel(Enum):
    """Confidence level categories"""
    HIGH = "high"  # 80-100%: Ready to execute
    MEDIUM = "medium"  # 50-79%: Needs some clarification
    LOW = "low"  # 20-49%: Significant uncertainties
    VERY_LOW = "very_low"  # 0-19%: Major blockers


class QuestionCategory(Enum):
    """Categories of questions/issues identified"""
    SCOPE = "scope"  # Unclear scope or boundaries
    TECHNICAL = "technical"  # Technical uncertainties
    DEPENDENCY = "dependency"  # Missing dependencies or prerequisites
    RISK = "risk"  # Potential risks identified
    RESOURCE = "resource"  # Resource or time concerns
    APPROVAL = "approval"  # Needs human approval
    CLARIFICATION = "clarification"  # General clarification needed


@dataclass
class Question:
    """A question or issue that needs clarification"""
    question_id: str
    category: QuestionCategory
    question: str
    context: str
    priority: str  # "critical", "high", "medium", "low"
    blocking: bool = False  # If True, blocks execution until resolved
    suggested_answer: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "question_id": self.question_id,
            "category": self.category.value,
            "question": self.question,
            "context": self.context,
            "priority": self.priority,
            "blocking": self.blocking,
            "suggested_answer": self.suggested_answer,
            "metadata": self.metadata,
        }


@dataclass
class ConfidenceScore:
    """Detailed confidence score breakdown"""
    overall_score: float  # 0.0 to 1.0
    level: ConfidenceLevel
    scope_clarity: float  # How clear is the scope?
    technical_feasibility: float  # How technically feasible?
    dependency_completeness: float  # Are all dependencies identified?
    risk_assessment: float  # How well are risks understood?
    resource_availability: float  # Are resources available?
    breakdown: Dict[str, float] = field(default_factory=dict)
    factors: List[str] = field(default_factory=list)  # Factors affecting score

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "overall_score": self.overall_score,
            "overall_percent": int(self.overall_score * 100),
            "level": self.level.value,
            "scope_clarity": self.scope_clarity,
            "technical_feasibility": self.technical_feasibility,
            "dependency_completeness": self.dependency_completeness,
            "risk_assessment": self.risk_assessment,
            "resource_availability": self.resource_availability,
            "breakdown": self.breakdown,
            "factors": self.factors,
        }


@dataclass
class ScoredPlan:
    """A TaskPlan with confidence scoring and questions"""
    plan: TaskPlan
    confidence: ConfidenceScore
    questions: List[Question]
    recommendations: List[str]
    ready_to_execute: bool
    scored_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "plan": self.plan.to_dict(),
            "confidence": self.confidence.to_dict(),
            "questions": [q.to_dict() for q in self.questions],
            "recommendations": self.recommendations,
            "ready_to_execute": self.ready_to_execute,
            "scored_at": self.scored_at.isoformat(),
            "blocking_questions": len([q for q in self.questions if q.blocking]),
            "total_questions": len(self.questions),
        }


class ConfidenceScorer:
    """
    Scores implementation plans for confidence and identifies questions.

    This scorer analyzes TaskPlans and their underlying ParsedGoals to:
    1. Calculate a confidence score (0-100%)
    2. Identify questions that need clarification
    3. Provide recommendations for improving plan quality
    """

    # Weights for different scoring factors
    SCORE_WEIGHTS = {
        "scope_clarity": 0.25,
        "technical_feasibility": 0.25,
        "dependency_completeness": 0.20,
        "risk_assessment": 0.15,
        "resource_availability": 0.15,
    }

    # Keywords indicating uncertainty
    UNCERTAINTY_KEYWORDS = [
        "maybe", "perhaps", "possibly", "might", "could",
        "unclear", "unknown", "tbd", "todo", "fixme",
        "可能", "也許", "或許", "不確定", "待定",
    ]

    # Keywords indicating well-defined scope
    CLARITY_KEYWORDS = [
        "specific", "exactly", "precisely", "must", "shall",
        "required", "mandatory", "concrete",
        "具體", "明確", "必須", "需要", "確定",
    ]

    # Technical complexity indicators
    COMPLEXITY_INDICATORS = [
        "integration", "migration", "refactor", "redesign",
        "distributed", "concurrent", "async", "real-time",
        "整合", "遷移", "重構", "分散式", "並發", "即時",
    ]

    # Risk indicators
    RISK_INDICATORS = [
        "production", "database", "security", "payment",
        "authentication", "critical", "sensitive",
        "生產", "資料庫", "安全", "付款", "認證", "關鍵",
    ]

    def __init__(self, llm_client: Optional[Any] = None):
        """
        Initialize the ConfidenceScorer.

        Args:
            llm_client: Optional LLM client for advanced analysis.
                       If not provided, uses pattern-based scoring only.
        """
        self.llm_client = llm_client
        logger.info(
            "[ConfidenceScorer] Initialized (LLM: %s)",
            "enabled" if llm_client else "disabled"
        )

    def score_plan(self, plan: TaskPlan) -> ScoredPlan:
        """
        Score a TaskPlan and generate questions.

        Args:
            plan: The TaskPlan to score

        Returns:
            ScoredPlan with confidence score and questions
        """
        logger.info(
            "[ConfidenceScorer] Scoring plan %s for goal: %s",
            plan.plan_id[:8],
            plan.goal.summary[:50],
        )

        # Calculate individual scores
        scope_score = self._score_scope_clarity(plan)
        tech_score = self._score_technical_feasibility(plan)
        dep_score = self._score_dependency_completeness(plan)
        risk_score = self._score_risk_assessment(plan)
        resource_score = self._score_resource_availability(plan)

        # Calculate weighted overall score
        overall_score = (
            scope_score * self.SCORE_WEIGHTS["scope_clarity"] +
            tech_score * self.SCORE_WEIGHTS["technical_feasibility"] +
            dep_score * self.SCORE_WEIGHTS["dependency_completeness"] +
            risk_score * self.SCORE_WEIGHTS["risk_assessment"] +
            resource_score * self.SCORE_WEIGHTS["resource_availability"]
        )

        # Determine confidence level
        level = self._determine_level(overall_score)

        # Collect factors affecting score
        factors = self._collect_factors(plan, scope_score, tech_score, dep_score, risk_score)

        confidence = ConfidenceScore(
            overall_score=overall_score,
            level=level,
            scope_clarity=scope_score,
            technical_feasibility=tech_score,
            dependency_completeness=dep_score,
            risk_assessment=risk_score,
            resource_availability=resource_score,
            breakdown={
                "scope_clarity": scope_score,
                "technical_feasibility": tech_score,
                "dependency_completeness": dep_score,
                "risk_assessment": risk_score,
                "resource_availability": resource_score,
            },
            factors=factors,
        )

        # Generate questions
        questions = self._generate_questions(plan, confidence)

        # Generate recommendations
        recommendations = self._generate_recommendations(plan, confidence, questions)

        # Determine if ready to execute
        blocking_questions = [q for q in questions if q.blocking]
        ready_to_execute = (
            overall_score >= 0.5 and
            len(blocking_questions) == 0 and
            level in [ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM]
        )

        scored_plan = ScoredPlan(
            plan=plan,
            confidence=confidence,
            questions=questions,
            recommendations=recommendations,
            ready_to_execute=ready_to_execute,
        )

        logger.info(
            "[ConfidenceScorer] Plan %s scored: %.0f%% (%s), %d questions, ready=%s",
            plan.plan_id[:8],
            overall_score * 100,
            level.value,
            len(questions),
            ready_to_execute,
        )

        return scored_plan

    def _score_scope_clarity(self, plan: TaskPlan) -> float:
        """Score how clear and well-defined the scope is"""
        goal = plan.goal
        score = 0.5  # Start at neutral

        # Check objectives clarity
        if goal.objectives:
            # More specific objectives = higher score
            avg_obj_length = sum(len(obj) for obj in goal.objectives) / len(goal.objectives)
            if avg_obj_length > 50:
                score += 0.15
            elif avg_obj_length > 30:
                score += 0.1

            # Multiple objectives suggest clearer breakdown
            if len(goal.objectives) >= 2:
                score += 0.1

        # Check for clarity keywords
        text = f"{goal.original_text} {goal.summary}".lower()
        clarity_count = sum(1 for kw in self.CLARITY_KEYWORDS if kw in text)
        score += min(clarity_count * 0.05, 0.15)

        # Check for uncertainty keywords (negative)
        uncertainty_count = sum(1 for kw in self.UNCERTAINTY_KEYWORDS if kw in text)
        score -= min(uncertainty_count * 0.1, 0.3)

        # Check success criteria
        if goal.success_criteria and len(goal.success_criteria) >= 2:
            score += 0.1

        return max(0.0, min(1.0, score))

    def _score_technical_feasibility(self, plan: TaskPlan) -> float:
        """Score technical feasibility of the plan"""
        goal = plan.goal
        score = 0.7  # Start optimistic

        text = goal.original_text.lower()

        # Check complexity
        if goal.estimated_complexity == "complex":
            score -= 0.2
        elif goal.estimated_complexity == "simple":
            score += 0.1

        # Check for complexity indicators
        complexity_count = sum(1 for kw in self.COMPLEXITY_INDICATORS if kw in text)
        score -= min(complexity_count * 0.05, 0.2)

        # Check goal type feasibility
        high_feasibility_types = [
            GoalType.DOCUMENTATION,
            GoalType.TESTING,
            GoalType.MAINTENANCE,
        ]
        medium_feasibility_types = [
            GoalType.BUG_FIX,
            GoalType.REFACTORING,
            GoalType.INVESTIGATION,
        ]

        if goal.goal_type in high_feasibility_types:
            score += 0.1
        elif goal.goal_type in medium_feasibility_types:
            score += 0.05
        elif goal.goal_type == GoalType.DEPLOYMENT:
            score -= 0.1

        # Check subtask count (too many = more complex)
        if len(plan.subtasks) > 10:
            score -= 0.1
        elif len(plan.subtasks) <= 5:
            score += 0.05

        return max(0.0, min(1.0, score))

    def _score_dependency_completeness(self, plan: TaskPlan) -> float:
        """Score how complete the dependency identification is"""
        goal = plan.goal
        score = 0.6  # Start slightly optimistic

        # Check constraints (more constraints = better understanding)
        if goal.constraints:
            score += min(len(goal.constraints) * 0.05, 0.15)

        # Check if context is provided
        context = goal.metadata.get("context", {})
        if context.get("repo"):
            score += 0.1
        if context.get("branch"):
            score += 0.05

        # Check subtask dependencies
        tasks_with_deps = sum(1 for t in plan.subtasks if t.dependencies)
        if tasks_with_deps > 0:
            score += 0.1

        # Check for external dependency mentions
        text = goal.original_text.lower()
        dep_keywords = ["depends on", "requires", "needs", "依賴", "需要", "前提"]
        if any(kw in text for kw in dep_keywords):
            score += 0.05  # Explicit dependency awareness

        return max(0.0, min(1.0, score))

    def _score_risk_assessment(self, plan: TaskPlan) -> float:
        """Score how well risks are understood and mitigated"""
        goal = plan.goal
        score = 0.7  # Start optimistic

        text = goal.original_text.lower()

        # Check for risk indicators
        risk_count = sum(1 for kw in self.RISK_INDICATORS if kw in text)
        if risk_count > 0:
            # Risks identified but may not be mitigated
            score -= min(risk_count * 0.1, 0.3)

        # Check if approval is required (good risk awareness)
        if goal.requires_approval:
            score += 0.1  # Acknowledging need for approval is good

        # Check for approval-required subtasks
        approval_tasks = sum(1 for t in plan.subtasks if t.requires_approval)
        if approval_tasks > 0:
            score += 0.05

        # Check goal type risk
        high_risk_types = [GoalType.DEPLOYMENT, GoalType.OPTIMIZATION]
        if goal.goal_type in high_risk_types:
            score -= 0.1

        return max(0.0, min(1.0, score))

    def _score_resource_availability(self, plan: TaskPlan) -> float:
        """Score resource availability and time estimates"""
        score = 0.7  # Start optimistic

        # Check time estimates
        total_minutes = plan.total_estimated_minutes
        if total_minutes > 240:  # > 4 hours
            score -= 0.15
        elif total_minutes > 120:  # > 2 hours
            score -= 0.05
        elif total_minutes <= 60:  # <= 1 hour
            score += 0.1

        # Check subtask estimates
        for task in plan.subtasks:
            if task.estimated_duration_minutes > 60:
                score -= 0.05  # Long individual tasks are risky

        # Check agent availability (all tasks have assigned agents)
        if all(t.agent_type for t in plan.subtasks):
            score += 0.1

        return max(0.0, min(1.0, score))

    def _determine_level(self, score: float) -> ConfidenceLevel:
        """Determine confidence level from score"""
        if score >= 0.8:
            return ConfidenceLevel.HIGH
        elif score >= 0.5:
            return ConfidenceLevel.MEDIUM
        elif score >= 0.2:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW

    def _collect_factors(
        self,
        plan: TaskPlan,
        scope_score: float,
        tech_score: float,
        dep_score: float,
        risk_score: float,
    ) -> List[str]:
        """Collect factors affecting the confidence score"""
        factors = []

        # Scope factors
        if scope_score >= 0.7:
            factors.append("Clear and well-defined scope")
        elif scope_score < 0.5:
            factors.append("Scope needs clarification")

        # Technical factors
        if tech_score >= 0.7:
            factors.append("Technically straightforward")
        elif tech_score < 0.5:
            factors.append("Technical complexity concerns")

        # Dependency factors
        if dep_score >= 0.7:
            factors.append("Dependencies well understood")
        elif dep_score < 0.5:
            factors.append("Missing dependency information")

        # Risk factors
        if risk_score >= 0.7:
            factors.append("Risks well managed")
        elif risk_score < 0.5:
            factors.append("Risk mitigation needed")

        # Goal type factor
        goal = plan.goal
        if goal.goal_type == GoalType.DEPLOYMENT:
            factors.append("Deployment requires extra caution")
        elif goal.goal_type == GoalType.DOCUMENTATION:
            factors.append("Documentation task - lower risk")

        # Approval factor
        if goal.requires_approval:
            factors.append("Human approval required")

        return factors

    def _generate_questions(
        self, plan: TaskPlan, confidence: ConfidenceScore
    ) -> List[Question]:
        """Generate questions based on plan analysis"""
        questions = []
        goal = plan.goal
        q_id = 0

        # Scope questions
        if confidence.scope_clarity < 0.6:
            q_id += 1
            questions.append(Question(
                question_id=f"{plan.plan_id[:8]}-Q{q_id:02d}",
                category=QuestionCategory.SCOPE,
                question="What are the exact boundaries of this task?",
                context=f"Goal: {goal.summary}",
                priority="high" if confidence.scope_clarity < 0.4 else "medium",
                blocking=confidence.scope_clarity < 0.3,
            ))

        # Check for vague objectives
        if goal.objectives:
            for i, obj in enumerate(goal.objectives):
                if len(obj) < 20 or any(kw in obj.lower() for kw in self.UNCERTAINTY_KEYWORDS):
                    q_id += 1
                    questions.append(Question(
                        question_id=f"{plan.plan_id[:8]}-Q{q_id:02d}",
                        category=QuestionCategory.CLARIFICATION,
                        question=f"Can you clarify objective: '{obj}'?",
                        context="Objective seems vague or uncertain",
                        priority="medium",
                        blocking=False,
                    ))

        # Technical questions
        if confidence.technical_feasibility < 0.6:
            q_id += 1
            questions.append(Question(
                question_id=f"{plan.plan_id[:8]}-Q{q_id:02d}",
                category=QuestionCategory.TECHNICAL,
                question="Are there any technical constraints or requirements not mentioned?",
                context=f"Complexity: {goal.estimated_complexity}",
                priority="high" if confidence.technical_feasibility < 0.4 else "medium",
                blocking=confidence.technical_feasibility < 0.3,
            ))

        # Dependency questions
        if confidence.dependency_completeness < 0.6:
            q_id += 1
            questions.append(Question(
                question_id=f"{plan.plan_id[:8]}-Q{q_id:02d}",
                category=QuestionCategory.DEPENDENCY,
                question="Are there any external dependencies or prerequisites?",
                context="Dependencies may not be fully identified",
                priority="medium",
                blocking=False,
            ))

        # Risk questions
        if goal.requires_approval:
            q_id += 1
            questions.append(Question(
                question_id=f"{plan.plan_id[:8]}-Q{q_id:02d}",
                category=QuestionCategory.APPROVAL,
                question="This task requires human approval before execution. Who should approve?",
                context="High-risk operation detected",
                priority="critical",
                blocking=True,
            ))

        # Resource questions for long tasks
        if plan.total_estimated_minutes > 180:
            q_id += 1
            questions.append(Question(
                question_id=f"{plan.plan_id[:8]}-Q{q_id:02d}",
                category=QuestionCategory.RESOURCE,
                question=f"This task is estimated to take {plan.total_estimated_minutes} minutes. Is this timeline acceptable?",
                context="Long-running task",
                priority="medium",
                blocking=False,
            ))

        # Goal type specific questions
        if goal.goal_type == GoalType.DEPLOYMENT:
            q_id += 1
            questions.append(Question(
                question_id=f"{plan.plan_id[:8]}-Q{q_id:02d}",
                category=QuestionCategory.RISK,
                question="What is the rollback plan if deployment fails?",
                context="Deployment task detected",
                priority="critical",
                blocking=True,
                suggested_answer="Revert to previous version",
            ))

        if goal.goal_type == GoalType.UNKNOWN:
            q_id += 1
            questions.append(Question(
                question_id=f"{plan.plan_id[:8]}-Q{q_id:02d}",
                category=QuestionCategory.SCOPE,
                question="Could not determine the type of task. What kind of work is this?",
                context="Goal type unclear",
                priority="high",
                blocking=True,
            ))

        return questions

    def _generate_recommendations(
        self,
        plan: TaskPlan,
        confidence: ConfidenceScore,
        questions: List[Question],
    ) -> List[str]:
        """Generate recommendations for improving the plan"""
        recommendations = []

        # Based on confidence level
        if confidence.level == ConfidenceLevel.HIGH:
            recommendations.append("Plan is ready for execution")
        elif confidence.level == ConfidenceLevel.MEDIUM:
            recommendations.append("Consider addressing open questions before execution")
        elif confidence.level == ConfidenceLevel.LOW:
            recommendations.append("Significant clarification needed before proceeding")
        else:
            recommendations.append("Plan needs major revision - too many uncertainties")

        # Based on individual scores
        if confidence.scope_clarity < 0.5:
            recommendations.append("Clarify scope boundaries and success criteria")

        if confidence.technical_feasibility < 0.5:
            recommendations.append("Break down complex technical tasks into smaller steps")

        if confidence.dependency_completeness < 0.5:
            recommendations.append("Identify and document all dependencies")

        if confidence.risk_assessment < 0.5:
            recommendations.append("Develop risk mitigation strategies")

        # Based on questions
        blocking_count = len([q for q in questions if q.blocking])
        if blocking_count > 0:
            recommendations.append(f"Resolve {blocking_count} blocking question(s) before execution")

        # Based on plan characteristics
        if plan.total_estimated_minutes > 240:
            recommendations.append("Consider breaking this into multiple smaller tasks")

        if len(plan.subtasks) > 8:
            recommendations.append("Large number of subtasks - consider phased execution")

        return recommendations

    async def score_plan_with_llm(self, plan: TaskPlan) -> ScoredPlan:
        """
        Score a plan using LLM for enhanced analysis.

        Args:
            plan: The TaskPlan to score

        Returns:
            ScoredPlan with LLM-enhanced scoring
        """
        if not self.llm_client:
            logger.warning(
                "[ConfidenceScorer] LLM client not available, using pattern-based scoring"
            )
            return self.score_plan(plan)

        # First, do pattern-based scoring as baseline
        base_scored = self.score_plan(plan)

        try:
            # Enhance with LLM analysis
            prompt = self._build_llm_prompt(plan, base_scored)
            llm_response = await self.llm_client.generate(prompt)

            # Parse LLM response and merge
            enhanced_scored = self._merge_llm_response(base_scored, llm_response)
            enhanced_scored.plan.metadata["llm_confidence_enhanced"] = True

            return enhanced_scored

        except Exception as e:
            logger.error(
                "[ConfidenceScorer] LLM scoring failed: %s, using base scoring",
                e
            )
            return base_scored

    def _build_llm_prompt(self, plan: TaskPlan, base_scored: ScoredPlan) -> str:
        """Build prompt for LLM-based scoring enhancement"""
        return f"""Analyze this implementation plan and identify additional questions or concerns:

Goal: {plan.goal.original_text}
Type: {plan.goal.goal_type.value}
Complexity: {plan.goal.estimated_complexity}
Current Confidence: {base_scored.confidence.overall_score * 100:.0f}%

Subtasks:
{chr(10).join(f"- {t.description}" for t in plan.subtasks)}

Current Questions:
{chr(10).join(f"- {q.question}" for q in base_scored.questions)}

Please identify:
1. Any additional questions that should be asked
2. Potential risks not yet identified
3. Suggestions for improving plan confidence

Format your response as JSON with keys: additional_questions, risks, suggestions
"""

    def _merge_llm_response(
        self, base_scored: ScoredPlan, llm_response: str
    ) -> ScoredPlan:
        """Merge LLM response with base scoring"""
        # For now, return base scored - LLM parsing to be implemented
        return base_scored
