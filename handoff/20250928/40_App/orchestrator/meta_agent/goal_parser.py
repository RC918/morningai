"""
Goal Parser - Natural Language Goal Parsing for Meta Agent

This module implements natural language goal parsing, converting high-level
user goals into structured objectives that can be decomposed into subtasks.

Issue: #1821 - Meta Agent 自主任務規劃與執行
Milestone: M5 - Meta Agent 優化
"""

import logging
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class GoalType(Enum):
    """Types of goals the Meta Agent can handle"""
    FEATURE_DEVELOPMENT = "feature_development"
    BUG_FIX = "bug_fix"
    REFACTORING = "refactoring"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    OPTIMIZATION = "optimization"
    INVESTIGATION = "investigation"
    MAINTENANCE = "maintenance"
    UNKNOWN = "unknown"


class GoalPriority(Enum):
    """Priority levels for goals"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ParsedGoal:
    """Structured representation of a parsed goal"""
    goal_id: str
    original_text: str
    goal_type: GoalType
    priority: GoalPriority
    summary: str
    objectives: List[str]
    constraints: List[str]
    success_criteria: List[str]
    estimated_complexity: str  # "simple", "moderate", "complex"
    requires_approval: bool
    metadata: Dict[str, Any] = field(default_factory=dict)
    parsed_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "goal_id": self.goal_id,
            "original_text": self.original_text,
            "goal_type": self.goal_type.value,
            "priority": self.priority.value,
            "summary": self.summary,
            "objectives": self.objectives,
            "constraints": self.constraints,
            "success_criteria": self.success_criteria,
            "estimated_complexity": self.estimated_complexity,
            "requires_approval": self.requires_approval,
            "metadata": self.metadata,
            "parsed_at": self.parsed_at.isoformat(),
        }


class GoalParser:
    """
    Parses natural language goals into structured objectives.

    This parser uses a combination of pattern matching and LLM-based
    understanding to extract structured information from user goals.
    """

    # Keywords for goal type detection
    GOAL_TYPE_KEYWORDS = {
        GoalType.FEATURE_DEVELOPMENT: [
            "add", "create", "implement", "build", "develop", "新增", "建立",
            "實現", "開發", "feature", "功能", "new"
        ],
        GoalType.BUG_FIX: [
            "fix", "repair", "resolve", "debug", "修復", "修正", "解決",
            "bug", "error", "issue", "problem", "錯誤", "問題"
        ],
        GoalType.REFACTORING: [
            "refactor", "restructure", "reorganize", "clean", "重構",
            "整理", "優化結構", "improve code"
        ],
        GoalType.DOCUMENTATION: [
            "document", "docs", "readme", "guide", "文檔", "說明",
            "documentation", "write docs"
        ],
        GoalType.TESTING: [
            "test", "testing", "coverage", "unit test", "e2e", "測試",
            "覆蓋率", "integration test"
        ],
        GoalType.DEPLOYMENT: [
            "deploy", "release", "publish", "ship", "部署", "發布",
            "上線", "production"
        ],
        GoalType.OPTIMIZATION: [
            "optimize", "improve", "performance", "speed", "優化",
            "效能", "加速", "faster"
        ],
        GoalType.INVESTIGATION: [
            "investigate", "analyze", "research", "explore", "調查",
            "分析", "研究", "understand"
        ],
        GoalType.MAINTENANCE: [
            "maintain", "update", "upgrade", "維護", "更新", "升級",
            "dependency", "version"
        ],
    }

    # Keywords for priority detection
    PRIORITY_KEYWORDS = {
        GoalPriority.CRITICAL: [
            "critical", "urgent", "emergency", "asap", "緊急", "立即",
            "immediately", "blocking"
        ],
        GoalPriority.HIGH: [
            "high priority", "important", "soon", "重要", "高優先",
            "priority", "需要盡快"
        ],
        GoalPriority.LOW: [
            "low priority", "when possible", "nice to have", "低優先",
            "有空時", "optional"
        ],
    }

    # High-risk patterns that require approval (English and Chinese)
    HIGH_RISK_PATTERNS = [
        # English patterns
        r"deploy.*prod",
        r"production",
        r"database.*migration",
        r"delete.*data",
        r"remove.*user",
        r"payment",
        r"billing",
        r"security",
        r"authentication",
        r"authorization",
        r"drop.*table",
        r"truncate",
        r"rollback",
        r"revert.*prod",
        r"secret",
        r"credential",
        r"api.*key",
        r"password",
        r"token",
        # Chinese patterns (中文高風險模式)
        r"部署.*生產",
        r"部署.*正式",
        r"生產環境",
        r"正式環境",
        r"資料庫.*遷移",
        r"數據庫.*遷移",
        r"刪除.*資料",
        r"刪除.*數據",
        r"移除.*用戶",
        r"移除.*使用者",
        r"付款",
        r"支付",
        r"帳單",
        r"賬單",
        r"安全",
        r"認證",
        r"授權",
        r"密碼",
        r"金鑰",
        r"密鑰",
        r"憑證",
        r"憑據",
        r"回滾",
        r"還原.*生產",
    ]

    def __init__(self, llm_client: Optional[Any] = None):
        """
        Initialize the GoalParser.

        Args:
            llm_client: Optional LLM client for advanced parsing.
                       If not provided, uses pattern-based parsing only.
        """
        self.llm_client = llm_client
        logger.info("[GoalParser] Initialized (LLM: %s)", "enabled" if llm_client else "disabled")

    def parse(self, goal_text: str, context: Optional[Dict[str, Any]] = None) -> ParsedGoal:
        """
        Parse a natural language goal into a structured ParsedGoal.

        Args:
            goal_text: The natural language goal description
            context: Optional context information (repo, user, etc.)

        Returns:
            ParsedGoal with structured information

        Raises:
            ValueError: If goal_text is empty or invalid
        """
        if not goal_text or not goal_text.strip():
            raise ValueError("Goal text cannot be empty")

        goal_text = goal_text.strip()
        goal_id = str(uuid.uuid4())
        context = context or {}

        logger.info("[GoalParser] Parsing goal: %s...", goal_text[:50])

        # Detect goal type
        goal_type = self._detect_goal_type(goal_text)

        # Detect priority
        priority = self._detect_priority(goal_text)

        # Generate summary
        summary = self._generate_summary(goal_text)

        # Extract objectives
        objectives = self._extract_objectives(goal_text, goal_type)

        # Extract constraints
        constraints = self._extract_constraints(goal_text, context)

        # Generate success criteria
        success_criteria = self._generate_success_criteria(goal_text, goal_type, objectives)

        # Estimate complexity
        complexity = self._estimate_complexity(goal_text, objectives)

        # Check if approval required
        requires_approval = self._check_requires_approval(goal_text, goal_type)

        parsed_goal = ParsedGoal(
            goal_id=goal_id,
            original_text=goal_text,
            goal_type=goal_type,
            priority=priority,
            summary=summary,
            objectives=objectives,
            constraints=constraints,
            success_criteria=success_criteria,
            estimated_complexity=complexity,
            requires_approval=requires_approval,
            metadata={
                "context": context,
                "parser_version": "1.0.0",
                "llm_enhanced": self.llm_client is not None,
            },
        )

        logger.info(
            "[GoalParser] Parsed goal %s: type=%s, priority=%s, complexity=%s, "
            "objectives=%d, requires_approval=%s",
            goal_id[:8],
            goal_type.value,
            priority.value,
            complexity,
            len(objectives),
            requires_approval,
        )

        return parsed_goal

    def _detect_goal_type(self, goal_text: str) -> GoalType:
        """Detect the type of goal from the text"""
        goal_lower = goal_text.lower()

        # Count keyword matches for each type
        type_scores: Dict[GoalType, int] = {}
        for goal_type, keywords in self.GOAL_TYPE_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in goal_lower)
            if score > 0:
                type_scores[goal_type] = score

        if not type_scores:
            return GoalType.UNKNOWN

        # Return the type with highest score
        return max(type_scores, key=type_scores.get)

    def _detect_priority(self, goal_text: str) -> GoalPriority:
        """Detect the priority level from the text"""
        goal_lower = goal_text.lower()

        for priority, keywords in self.PRIORITY_KEYWORDS.items():
            if any(kw in goal_lower for kw in keywords):
                return priority

        # Default to medium priority
        return GoalPriority.MEDIUM

    def _generate_summary(self, goal_text: str) -> str:
        """Generate a concise summary of the goal"""
        # Take first sentence or first 100 chars
        sentences = re.split(r'[.!?。！？]', goal_text)
        first_sentence = sentences[0].strip() if sentences else goal_text

        if len(first_sentence) > 100:
            return first_sentence[:97] + "..."
        return first_sentence

    def _extract_objectives(self, goal_text: str, goal_type: GoalType) -> List[str]:
        """Extract specific objectives from the goal text"""
        objectives = []

        # Split by common delimiters
        parts = re.split(r'[,;，；]|\band\b|\bor\b|以及|和|或', goal_text)

        for part in parts:
            part = part.strip()
            if len(part) > 10:  # Filter out very short fragments
                objectives.append(part)

        # If no objectives found, use the whole text as one objective
        if not objectives:
            objectives = [goal_text]

        # Add type-specific default objectives
        type_objectives = {
            GoalType.FEATURE_DEVELOPMENT: ["Implement the feature", "Add tests", "Update documentation"],
            GoalType.BUG_FIX: ["Identify root cause", "Implement fix", "Add regression test"],
            GoalType.TESTING: ["Write test cases", "Achieve coverage target", "Verify all tests pass"],
            GoalType.DOCUMENTATION: ["Write documentation", "Add examples", "Review for clarity"],
            GoalType.DEPLOYMENT: ["Prepare deployment", "Run pre-deployment checks", "Deploy and verify"],
        }

        if goal_type in type_objectives and len(objectives) == 1:
            # Enhance with type-specific objectives
            base_objective = objectives[0]
            objectives = [f"{base_objective}: {obj}" for obj in type_objectives[goal_type][:2]]

        return objectives[:5]  # Limit to 5 objectives

    def _extract_constraints(self, goal_text: str, context: Dict[str, Any]) -> List[str]:
        """Extract constraints from the goal text and context"""
        constraints = []

        # Check for explicit constraints in text
        constraint_patterns = [
            (r"without\s+(.+?)(?:\.|,|$)", "Must not: {}"),
            (r"must\s+(.+?)(?:\.|,|$)", "Must: {}"),
            (r"should\s+not\s+(.+?)(?:\.|,|$)", "Should not: {}"),
            (r"不能(.+?)(?:\.|,|。|$)", "Must not: {}"),
            (r"必須(.+?)(?:\.|,|。|$)", "Must: {}"),
        ]

        for pattern, template in constraint_patterns:
            matches = re.findall(pattern, goal_text, re.IGNORECASE)
            for match in matches:
                constraints.append(template.format(match.strip()))

        # Add context-based constraints
        if context.get("repo"):
            constraints.append(f"Target repository: {context['repo']}")

        if context.get("branch"):
            constraints.append(f"Target branch: {context['branch']}")

        return constraints

    def _generate_success_criteria(
        self, goal_text: str, goal_type: GoalType, objectives: List[str]
    ) -> List[str]:
        """Generate success criteria based on goal type and objectives"""
        criteria = []

        # Type-specific criteria
        type_criteria = {
            GoalType.FEATURE_DEVELOPMENT: [
                "Feature is implemented and functional",
                "All tests pass",
                "Code review approved",
            ],
            GoalType.BUG_FIX: [
                "Bug is fixed and verified",
                "Regression test added",
                "No new issues introduced",
            ],
            GoalType.TESTING: [
                "Test coverage meets target",
                "All tests pass",
                "Edge cases covered",
            ],
            GoalType.DOCUMENTATION: [
                "Documentation is complete",
                "Examples are working",
                "Reviewed for accuracy",
            ],
            GoalType.DEPLOYMENT: [
                "Deployment successful",
                "Health checks pass",
                "Rollback plan verified",
            ],
            GoalType.REFACTORING: [
                "Code quality improved",
                "All existing tests pass",
                "No functionality changes",
            ],
        }

        if goal_type in type_criteria:
            criteria.extend(type_criteria[goal_type])
        else:
            # Generic criteria
            criteria = [
                "Task completed successfully",
                "No errors or regressions",
                "Changes verified",
            ]

        return criteria

    def _estimate_complexity(self, goal_text: str, objectives: List[str]) -> str:
        """Estimate the complexity of the goal"""
        # Simple heuristics for complexity estimation
        complexity_score = 0

        # More objectives = more complex
        complexity_score += len(objectives) * 2

        # Longer description = potentially more complex
        if len(goal_text) > 200:
            complexity_score += 2
        elif len(goal_text) > 100:
            complexity_score += 1

        # Check for complexity indicators
        complex_keywords = [
            "multiple", "several", "all", "entire", "complete",
            "integration", "migration", "refactor", "redesign",
            "多個", "所有", "整個", "完整", "整合", "遷移"
        ]

        goal_lower = goal_text.lower()
        complexity_score += sum(2 for kw in complex_keywords if kw in goal_lower)

        # Determine complexity level
        if complexity_score >= 8:
            return "complex"
        elif complexity_score >= 4:
            return "moderate"
        else:
            return "simple"

    def _check_requires_approval(self, goal_text: str, goal_type: GoalType) -> bool:
        """Check if the goal requires human approval"""
        goal_lower = goal_text.lower()

        # Check high-risk patterns
        for pattern in self.HIGH_RISK_PATTERNS:
            if re.search(pattern, goal_lower):
                logger.info("[GoalParser] High-risk pattern detected: %s", pattern)
                return True

        # Deployment always requires approval
        if goal_type == GoalType.DEPLOYMENT:
            return True

        return False

    async def parse_with_llm(
        self, goal_text: str, context: Optional[Dict[str, Any]] = None
    ) -> ParsedGoal:
        """
        Parse a goal using LLM for enhanced understanding.

        This method uses the LLM client to provide more accurate parsing
        for complex or ambiguous goals.

        Args:
            goal_text: The natural language goal description
            context: Optional context information

        Returns:
            ParsedGoal with LLM-enhanced parsing
        """
        if not self.llm_client:
            logger.warning("[GoalParser] LLM client not available, falling back to pattern parsing")
            return self.parse(goal_text, context)

        # First, do pattern-based parsing as baseline
        base_goal = self.parse(goal_text, context)

        try:
            # Enhance with LLM
            prompt = self._build_llm_prompt(goal_text, context)
            llm_response = await self.llm_client.generate(prompt)

            # Parse LLM response and merge with base goal
            enhanced_goal = self._merge_llm_response(base_goal, llm_response)
            enhanced_goal.metadata["llm_enhanced"] = True

            return enhanced_goal

        except Exception as e:
            logger.error("[GoalParser] LLM parsing failed: %s, using base parsing", e)
            return base_goal

    def _build_llm_prompt(self, goal_text: str, context: Optional[Dict[str, Any]]) -> str:
        """Build prompt for LLM-based parsing"""
        return f"""Analyze the following goal and extract structured information:

Goal: {goal_text}

Context: {context or 'None provided'}

Please identify:
1. Goal type (feature_development, bug_fix, refactoring, documentation, testing, deployment, optimization, investigation, maintenance)
2. Priority (critical, high, medium, low)
3. Main objectives (list of specific tasks)
4. Constraints (any limitations or requirements)
5. Success criteria (how to verify completion)
6. Complexity estimate (simple, moderate, complex)
7. Whether human approval is required

Respond in JSON format."""

    def _merge_llm_response(self, base_goal: ParsedGoal, llm_response: str) -> ParsedGoal:
        """Merge LLM response with base goal parsing"""
        # For now, return base goal - LLM integration to be implemented
        # when LLM client is properly configured
        return base_goal
