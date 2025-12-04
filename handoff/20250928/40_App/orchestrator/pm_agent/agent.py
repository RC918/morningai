#!/usr/bin/env python3
"""
PM Agent - Phase 3 PR-3 (#1815)

Product Manager Agent for task decomposition and planning.
Accepts high-level goals from humans and decomposes them into actionable sub-tasks.

Design Principles:
- Advisory role: Provides task decomposition and planning recommendations
- LLM-powered: Uses LLM for intelligent goal decomposition
- Confidence scoring: Provides confidence scores for generated plans
- Integration: Works with existing LLMPlannerAdapter and orchestrator components
"""
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)


class PMRisk(Enum):
    """PM planning risk levels"""
    HIGH = "high"          # Complex task, low confidence
    MEDIUM = "medium"      # Moderate complexity
    LOW = "low"            # Simple task, high confidence
    INFO = "info"          # Informational only


@dataclass
class SubTask:
    """Represents a decomposed sub-task"""
    task_id: str
    title: str
    description: str
    estimated_effort: str  # "small", "medium", "large"
    dependencies: List[str] = field(default_factory=list)
    affected_files: List[str] = field(default_factory=list)
    task_type: str = "unknown"
    priority: int = 0


@dataclass
class PMFinding:
    """Represents a PM planning finding"""
    category: str           # e.g., "complexity", "dependency", "risk"
    risk_level: PMRisk
    title: str
    description: str
    recommendation: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ImplementationPlan:
    """Represents a complete implementation plan"""
    plan_id: str
    goal: str
    sub_tasks: List[SubTask] = field(default_factory=list)
    total_effort: str = "unknown"
    estimated_duration: str = "unknown"
    affected_files: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)


@dataclass
class PMAdvisory:
    """PM advisory result from PMAgent analysis"""
    is_feasible: bool
    overall_risk: PMRisk
    confidence_score: float  # 0.0 to 1.0
    goal: str
    sub_tasks: List[SubTask] = field(default_factory=list)
    implementation_plan: Optional[ImplementationPlan] = None
    findings: List[PMFinding] = field(default_factory=list)
    summary: str = ""
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "is_feasible": self.is_feasible,
            "overall_risk": self.overall_risk.value,
            "confidence_score": self.confidence_score,
            "goal": self.goal,
            "sub_tasks": [
                {
                    "task_id": t.task_id,
                    "title": t.title,
                    "description": t.description,
                    "estimated_effort": t.estimated_effort,
                    "dependencies": t.dependencies,
                    "affected_files": t.affected_files,
                    "task_type": t.task_type,
                    "priority": t.priority,
                }
                for t in self.sub_tasks
            ],
            "implementation_plan": {
                "plan_id": self.implementation_plan.plan_id,
                "goal": self.implementation_plan.goal,
                "total_effort": self.implementation_plan.total_effort,
                "estimated_duration": self.implementation_plan.estimated_duration,
                "affected_files": self.implementation_plan.affected_files,
                "dependencies": self.implementation_plan.dependencies,
                "risks": self.implementation_plan.risks,
            } if self.implementation_plan else None,
            "findings": [
                {
                    "category": f.category,
                    "risk_level": f.risk_level.value,
                    "title": f.title,
                    "description": f.description,
                    "recommendation": f.recommendation,
                    "metadata": f.metadata,
                }
                for f in self.findings
            ],
            "summary": self.summary,
            "recommendations": self.recommendations,
            "metadata": self.metadata,
        }


class PMAgent:
    """
    Product Manager Agent for the orchestrator pipeline.

    Phase 3 PR-3 Features (#1815):
    - Goal decomposition: Break down high-level goals into sub-tasks
    - Implementation planning: Generate detailed implementation plans
    - Confidence scoring: Provide confidence scores for plans
    - Risk assessment: Identify planning risks and dependencies
    - File impact analysis: Identify affected files and directories
    """

    # Task type patterns for classification
    TASK_TYPE_PATTERNS = {
        "documentation": ["readme", "doc", "comment", "説明", "文檔"],
        "bug_fix": ["fix", "bug", "error", "issue", "修正", "修復"],
        "feature": ["add", "implement", "create", "new", "新增", "實作"],
        "refactor": ["refactor", "clean", "improve", "optimize", "重構", "優化"],
        "test": ["test", "spec", "coverage", "測試"],
        "config": ["config", "setting", "env", "設定", "配置"],
        "security": ["security", "auth", "permission", "安全", "權限"],
        "performance": ["performance", "speed", "cache", "效能", "快取"],
    }

    # Effort estimation keywords
    EFFORT_KEYWORDS = {
        "small": ["simple", "minor", "small", "quick", "簡單", "小"],
        "medium": ["moderate", "medium", "standard", "中等"],
        "large": ["complex", "large", "major", "significant", "複雜", "大"],
    }

    def __init__(self):
        """Initialize PMAgent with configuration"""
        self._load_settings()
        self._init_llm_integration()
        logger.info("[PMAgent] Initialized - Phase 3 PR-3 (#1815)")

    def _load_settings(self):
        """Load settings from environment"""
        try:
            from common.config.settings import settings
            self.enabled = getattr(settings, 'pm_agent_enabled', True)
            self.use_llm = getattr(settings, 'pm_agent_use_llm', True)
            self.max_sub_tasks = getattr(settings, 'pm_agent_max_sub_tasks', 10)
            logger.info(
                "[PMAgent] Settings loaded: enabled=%s, use_llm=%s",
                self.enabled, self.use_llm
            )
        except (ImportError, AttributeError) as e:
            logger.warning("[PMAgent] Failed to load settings: %s, using defaults", e)
            self.enabled = True
            self.use_llm = True
            self.max_sub_tasks = 10

    def _init_llm_integration(self):
        """Initialize LLM integration for intelligent decomposition"""
        self.llm_planner = None

        try:
            from llm_planner_adapter import LLMPlannerAdapter
            self.llm_planner = LLMPlannerAdapter()
            logger.info("[PMAgent] LLMPlannerAdapter integration enabled")
        except ImportError as e:
            logger.warning("[PMAgent] LLMPlannerAdapter not available: %s", e)

    def decompose_goal(
        self,
        goal: str,
        repo: str = "RC918/morningai",
        context: Optional[Dict[str, Any]] = None
    ) -> PMAdvisory:
        """
        Decompose a high-level goal into actionable sub-tasks.

        Args:
            goal: High-level goal description (natural language)
            repo: Repository name for context
            context: Optional additional context

        Returns:
            PMAdvisory with decomposed sub-tasks and confidence score
        """
        if not self.enabled:
            return PMAdvisory(
                is_feasible=True,
                overall_risk=PMRisk.INFO,
                confidence_score=0.0,
                goal=goal,
                summary="PM Agent disabled"
            )

        start_time = time.time()
        trace_id = str(uuid.uuid4())

        logger.info("[PMAgent] Decomposing goal", extra={
            "operation": "decompose_goal",
            "trace_id": trace_id,
            "goal": goal[:100],
            "repo": repo
        })

        findings: List[PMFinding] = []
        sub_tasks: List[SubTask] = []

        # Try LLM-powered decomposition first
        if self.use_llm and self.llm_planner:
            try:
                llm_result = self._llm_decompose(goal, repo, trace_id)
                if llm_result:
                    sub_tasks = llm_result.get("sub_tasks", [])
                    findings.extend(llm_result.get("findings", []))
            except Exception as e:
                logger.warning("[PMAgent] LLM decomposition failed: %s", e)
                findings.append(PMFinding(
                    category="llm_error",
                    risk_level=PMRisk.MEDIUM,
                    title="LLM decomposition failed",
                    description=str(e),
                    recommendation="Falling back to rule-based decomposition"
                ))

        # Fallback to rule-based decomposition
        if not sub_tasks:
            sub_tasks = self._rule_based_decompose(goal, trace_id)

        # Analyze complexity and risks
        complexity_findings = self._analyze_complexity(goal, sub_tasks)
        findings.extend(complexity_findings)

        # Calculate confidence score
        confidence_score = self._calculate_confidence(goal, sub_tasks, findings)

        # Determine overall risk
        overall_risk = self._calculate_overall_risk(findings, confidence_score)

        # Generate summary and recommendations
        summary = self._generate_summary(goal, sub_tasks, findings)
        recommendations = self._generate_recommendations(findings, sub_tasks)

        latency_ms = (time.time() - start_time) * 1000

        advisory = PMAdvisory(
            is_feasible=len(sub_tasks) > 0,
            overall_risk=overall_risk,
            confidence_score=confidence_score,
            goal=goal,
            sub_tasks=sub_tasks,
            findings=findings,
            summary=summary,
            recommendations=recommendations,
            metadata={
                "trace_id": trace_id,
                "repo": repo,
                "latency_ms": latency_ms,
                "sub_task_count": len(sub_tasks),
                "decomposition_method": "llm" if self.use_llm and self.llm_planner else "rule_based"
            }
        )

        logger.info("[PMAgent] Goal decomposition complete", extra={
            "operation": "decompose_goal",
            "trace_id": trace_id,
            "sub_task_count": len(sub_tasks),
            "confidence_score": confidence_score,
            "overall_risk": overall_risk.value,
            "latency_ms": latency_ms
        })

        return advisory

    def plan_implementation(
        self,
        goal: str,
        repo: str = "RC918/morningai",
        sub_tasks: Optional[List[SubTask]] = None
    ) -> PMAdvisory:
        """
        Generate a detailed implementation plan for a goal.

        Args:
            goal: High-level goal description
            repo: Repository name
            sub_tasks: Optional pre-decomposed sub-tasks

        Returns:
            PMAdvisory with implementation plan
        """
        if not self.enabled:
            return PMAdvisory(
                is_feasible=True,
                overall_risk=PMRisk.INFO,
                confidence_score=0.0,
                goal=goal,
                summary="PM Agent disabled"
            )

        start_time = time.time()
        trace_id = str(uuid.uuid4())

        logger.info("[PMAgent] Planning implementation", extra={
            "operation": "plan_implementation",
            "trace_id": trace_id,
            "goal": goal[:100]
        })

        # Decompose if sub_tasks not provided
        if not sub_tasks:
            advisory = self.decompose_goal(goal, repo)
            sub_tasks = advisory.sub_tasks

        # Collect all affected files
        all_affected_files = []
        all_dependencies = []
        for task in sub_tasks:
            all_affected_files.extend(task.affected_files)
            all_dependencies.extend(task.dependencies)

        # Remove duplicates
        all_affected_files = list(set(all_affected_files))
        all_dependencies = list(set(all_dependencies))

        # Estimate total effort
        total_effort = self._estimate_total_effort(sub_tasks)

        # Estimate duration
        estimated_duration = self._estimate_duration(sub_tasks, total_effort)

        # Identify risks
        risks = self._identify_risks(goal, sub_tasks, all_affected_files)

        # Create implementation plan
        plan = ImplementationPlan(
            plan_id=trace_id,
            goal=goal,
            sub_tasks=sub_tasks,
            total_effort=total_effort,
            estimated_duration=estimated_duration,
            affected_files=all_affected_files,
            dependencies=all_dependencies,
            risks=risks
        )

        # Calculate confidence
        confidence_score = self._calculate_plan_confidence(plan)

        # Determine risk level
        overall_risk = PMRisk.LOW
        if len(risks) > 3 or confidence_score < 0.5:
            overall_risk = PMRisk.HIGH
        elif len(risks) > 1 or confidence_score < 0.7:
            overall_risk = PMRisk.MEDIUM

        latency_ms = (time.time() - start_time) * 1000

        advisory = PMAdvisory(
            is_feasible=True,
            overall_risk=overall_risk,
            confidence_score=confidence_score,
            goal=goal,
            sub_tasks=sub_tasks,
            implementation_plan=plan,
            summary=f"Implementation plan with {len(sub_tasks)} tasks, {total_effort} effort",
            recommendations=self._generate_plan_recommendations(plan),
            metadata={
                "trace_id": trace_id,
                "repo": repo,
                "latency_ms": latency_ms,
                "total_effort": total_effort,
                "estimated_duration": estimated_duration,
                "risk_count": len(risks)
            }
        )

        logger.info("[PMAgent] Implementation planning complete", extra={
            "operation": "plan_implementation",
            "trace_id": trace_id,
            "sub_task_count": len(sub_tasks),
            "total_effort": total_effort,
            "confidence_score": confidence_score,
            "latency_ms": latency_ms
        })

        return advisory

    def _llm_decompose(
        self,
        goal: str,
        repo: str,
        trace_id: str
    ) -> Optional[Dict[str, Any]]:
        """Use LLM to decompose goal into sub-tasks"""
        if not self.llm_planner:
            return None

        try:
            plan_result = self.llm_planner.generate_plan(
                goal=goal,
                repo=repo,
                trace_id=trace_id
            )

            plan_steps = plan_result.get("plan", [])
            sub_tasks = []

            for i, step in enumerate(plan_steps[:self.max_sub_tasks]):
                step_text = step if isinstance(step, str) else step.get("step", str(step))

                task_type = self._classify_task_type(step_text)
                effort = self._estimate_effort(step_text)

                sub_task = SubTask(
                    task_id=f"{trace_id}-{i}",
                    title=step_text[:100],
                    description=step_text,
                    estimated_effort=effort,
                    task_type=task_type,
                    priority=i
                )
                sub_tasks.append(sub_task)

            return {
                "sub_tasks": sub_tasks,
                "findings": [],
                "planner_type": plan_result.get("planner_type", "llm")
            }

        except Exception as e:
            logger.warning("[PMAgent] LLM decomposition error: %s", e)
            return None

    def _rule_based_decompose(self, goal: str, trace_id: str) -> List[SubTask]:
        """Rule-based fallback for goal decomposition"""
        sub_tasks = []

        # Split by common delimiters
        parts = []
        for delimiter in ["\n", "，", ",", "；", ";", "、"]:
            if delimiter in goal:
                parts = [p.strip() for p in goal.split(delimiter) if p.strip()]
                break

        if not parts:
            parts = [goal]

        for i, part in enumerate(parts[:self.max_sub_tasks]):
            task_type = self._classify_task_type(part)
            effort = self._estimate_effort(part)

            sub_task = SubTask(
                task_id=f"{trace_id}-{i}",
                title=part[:100],
                description=part,
                estimated_effort=effort,
                task_type=task_type,
                priority=i
            )
            sub_tasks.append(sub_task)

        return sub_tasks

    def _classify_task_type(self, text: str) -> str:
        """Classify task type based on text content"""
        text_lower = text.lower()

        for task_type, keywords in self.TASK_TYPE_PATTERNS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return task_type

        return "unknown"

    def _estimate_effort(self, text: str) -> str:
        """Estimate effort based on text content"""
        text_lower = text.lower()

        for effort, keywords in self.EFFORT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return effort

        # Default based on text length
        if len(text) < 50:
            return "small"
        elif len(text) < 150:
            return "medium"
        else:
            return "large"

    def _analyze_complexity(
        self,
        goal: str,
        sub_tasks: List[SubTask]
    ) -> List[PMFinding]:
        """Analyze complexity and generate findings"""
        findings = []

        # Check number of sub-tasks
        if len(sub_tasks) > 5:
            findings.append(PMFinding(
                category="complexity",
                risk_level=PMRisk.MEDIUM,
                title="High task count",
                description=f"Goal decomposed into {len(sub_tasks)} sub-tasks",
                recommendation="Consider breaking into multiple phases"
            ))

        # Check for large effort tasks
        large_tasks = [t for t in sub_tasks if t.estimated_effort == "large"]
        if large_tasks:
            findings.append(PMFinding(
                category="complexity",
                risk_level=PMRisk.MEDIUM,
                title="Large effort tasks detected",
                description=f"{len(large_tasks)} tasks estimated as large effort",
                recommendation="Consider further decomposition of large tasks"
            ))

        # Check for security-related tasks
        security_tasks = [t for t in sub_tasks if t.task_type == "security"]
        if security_tasks:
            findings.append(PMFinding(
                category="risk",
                risk_level=PMRisk.HIGH,
                title="Security-related tasks",
                description=f"{len(security_tasks)} security-related tasks identified",
                recommendation="Ensure security review before implementation"
            ))

        return findings

    def _calculate_confidence(
        self,
        goal: str,
        sub_tasks: List[SubTask],
        findings: List[PMFinding]
    ) -> float:
        """Calculate confidence score for the decomposition"""
        if not sub_tasks:
            return 0.0

        base_confidence = 0.8

        # Reduce confidence for high-risk findings
        high_risk_count = len([f for f in findings if f.risk_level == PMRisk.HIGH])
        medium_risk_count = len([f for f in findings if f.risk_level == PMRisk.MEDIUM])

        confidence = base_confidence - (high_risk_count * 0.15) - (medium_risk_count * 0.05)

        # Reduce confidence for many sub-tasks
        if len(sub_tasks) > 7:
            confidence -= 0.1
        elif len(sub_tasks) > 5:
            confidence -= 0.05

        # Reduce confidence for unknown task types
        unknown_count = len([t for t in sub_tasks if t.task_type == "unknown"])
        confidence -= unknown_count * 0.05

        return max(0.0, min(1.0, confidence))

    def _calculate_overall_risk(
        self,
        findings: List[PMFinding],
        confidence_score: float
    ) -> PMRisk:
        """Calculate overall risk level"""
        high_risk_count = len([f for f in findings if f.risk_level == PMRisk.HIGH])

        if high_risk_count > 0 or confidence_score < 0.5:
            return PMRisk.HIGH
        elif confidence_score < 0.7:
            return PMRisk.MEDIUM
        else:
            return PMRisk.LOW

    def _generate_summary(
        self,
        goal: str,
        sub_tasks: List[SubTask],
        findings: List[PMFinding]
    ) -> str:
        """Generate summary of the decomposition"""
        task_types = set(t.task_type for t in sub_tasks)
        efforts = [t.estimated_effort for t in sub_tasks]

        summary_parts = [
            f"Decomposed into {len(sub_tasks)} sub-tasks",
            f"Task types: {', '.join(task_types)}",
            f"Effort distribution: {efforts.count('small')} small, {efforts.count('medium')} medium, {efforts.count('large')} large"
        ]

        if findings:
            summary_parts.append(f"Findings: {len(findings)} issues identified")

        return ". ".join(summary_parts)

    def _generate_recommendations(
        self,
        findings: List[PMFinding],
        sub_tasks: List[SubTask]
    ) -> List[str]:
        """Generate recommendations based on findings"""
        recommendations = []

        # Add finding recommendations
        for finding in findings:
            if finding.recommendation:
                recommendations.append(finding.recommendation)

        # Add general recommendations
        if len(sub_tasks) > 5:
            recommendations.append("Consider implementing in phases")

        large_tasks = [t for t in sub_tasks if t.estimated_effort == "large"]
        if large_tasks:
            recommendations.append("Break down large tasks before implementation")

        return list(set(recommendations))  # Remove duplicates

    def _estimate_total_effort(self, sub_tasks: List[SubTask]) -> str:
        """Estimate total effort from sub-tasks"""
        effort_scores = {"small": 1, "medium": 2, "large": 4}
        total_score = sum(effort_scores.get(t.estimated_effort, 2) for t in sub_tasks)

        if total_score <= 3:
            return "small"
        elif total_score <= 8:
            return "medium"
        else:
            return "large"

    def _estimate_duration(self, sub_tasks: List[SubTask], total_effort: str) -> str:
        """Estimate duration based on effort"""
        duration_map = {
            "small": "1-2 hours",
            "medium": "1-2 days",
            "large": "3-5 days"
        }
        return duration_map.get(total_effort, "unknown")

    def _identify_risks(
        self,
        goal: str,
        sub_tasks: List[SubTask],
        affected_files: List[str]
    ) -> List[str]:
        """Identify implementation risks"""
        risks = []

        # Check for security-related changes
        security_keywords = ["auth", "permission", "secret", "credential", "token"]
        if any(kw in goal.lower() for kw in security_keywords):
            risks.append("Security-sensitive changes require careful review")

        # Check for database changes
        db_keywords = ["migration", "database", "schema", "table"]
        if any(kw in goal.lower() for kw in db_keywords):
            risks.append("Database changes may require migration coordination")

        # Check for many affected files
        if len(affected_files) > 10:
            risks.append("Large number of affected files increases merge conflict risk")

        # Check for large tasks
        large_tasks = [t for t in sub_tasks if t.estimated_effort == "large"]
        if len(large_tasks) > 2:
            risks.append("Multiple large tasks may cause timeline delays")

        return risks

    def _calculate_plan_confidence(self, plan: ImplementationPlan) -> float:
        """Calculate confidence score for implementation plan"""
        base_confidence = 0.85

        # Reduce for risks
        confidence = base_confidence - (len(plan.risks) * 0.1)

        # Reduce for many dependencies
        if len(plan.dependencies) > 5:
            confidence -= 0.1

        # Reduce for large effort
        if plan.total_effort == "large":
            confidence -= 0.1

        return max(0.0, min(1.0, confidence))

    def _generate_plan_recommendations(self, plan: ImplementationPlan) -> List[str]:
        """Generate recommendations for implementation plan"""
        recommendations = []

        if plan.total_effort == "large":
            recommendations.append("Consider implementing in multiple PRs")

        if len(plan.risks) > 0:
            recommendations.append("Address identified risks before starting")

        if len(plan.dependencies) > 3:
            recommendations.append("Verify all dependencies are available")

        if len(plan.affected_files) > 5:
            recommendations.append("Coordinate with team to avoid merge conflicts")

        return recommendations


# Singleton instance
_pm_agent: Optional[PMAgent] = None


def get_pm_agent() -> PMAgent:
    """Get or create the singleton PMAgent instance"""
    global _pm_agent
    if _pm_agent is None:
        _pm_agent = PMAgent()
    return _pm_agent


def decompose_goal(
    goal: str,
    repo: str = "RC918/morningai",
    context: Optional[Dict[str, Any]] = None
) -> PMAdvisory:
    """Convenience function to decompose a goal"""
    agent = get_pm_agent()
    return agent.decompose_goal(goal, repo, context)


def plan_implementation(
    goal: str,
    repo: str = "RC918/morningai",
    sub_tasks: Optional[List[SubTask]] = None
) -> PMAdvisory:
    """Convenience function to plan implementation"""
    agent = get_pm_agent()
    return agent.plan_implementation(goal, repo, sub_tasks)
