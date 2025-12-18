#!/usr/bin/env python3
"""
Refactor Agent V2 - Migration to BaseAgent with RoutingEngine

EPIC #2594 - Issue #2676: Agent Migration Validation

This module demonstrates the migration of RefactorAgent to use the new
BaseAgent class with RoutingEngine integration. It serves as a reference
implementation for migrating other agents.

Migration Changes:
- Inherits from BaseAgent instead of standalone class
- Uses self.call_llm() instead of direct LLMClient calls
- Leverages RoutingEngine for dynamic model selection
- Emits Telemetry v2 events automatically

Original: refactor_agent/agent.py (RefactorAgent)
Migrated: refactor_agent/agent_v2.py (RefactorAgentV2)
"""
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any

from core.agents import BaseAgent, AgentInput, AgentOutput

logger = logging.getLogger(__name__)


class RefactorRisk(Enum):
    """Refactor risk levels"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class TSError:
    """Represents a TypeScript error"""
    file_path: str
    line: int
    column: int
    error_code: str
    message: str
    severity: str = "error"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "file_path": self.file_path,
            "line": self.line,
            "column": self.column,
            "error_code": self.error_code,
            "message": self.message,
            "severity": self.severity,
        }


@dataclass
class RefactorTask:
    """Represents a refactor task for a single TS error"""
    task_id: str
    error: TSError
    fix_strategy: str
    estimated_risk: RefactorRisk
    status: str = "pending"
    fix_applied: Optional[str] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "task_id": self.task_id,
            "error": self.error.to_dict(),
            "fix_strategy": self.fix_strategy,
            "estimated_risk": self.estimated_risk.value,
            "status": self.status,
            "fix_applied": self.fix_applied,
            "error_message": self.error_message,
        }


@dataclass
class RefactorResultV2:
    """Result of a refactor run using BaseAgent"""
    run_id: str
    started_at: float
    completed_at: Optional[float] = None
    total_errors_found: int = 0
    errors_fixed: int = 0
    errors_failed: int = 0
    tasks: List[RefactorTask] = field(default_factory=list)
    summary: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "run_id": self.run_id,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "total_errors_found": self.total_errors_found,
            "errors_fixed": self.errors_fixed,
            "errors_failed": self.errors_failed,
            "tasks": [t.to_dict() for t in self.tasks],
            "summary": self.summary,
            "metadata": self.metadata,
        }


TS_FIX_STRATEGIES = {
    "TS2322": "type_mismatch",
    "TS2339": "property_missing",
    "TS2345": "argument_type",
    "TS2531": "null_check",
    "TS2532": "undefined_check",
    "TS2554": "argument_count",
    "TS2571": "unknown_type",
    "TS7006": "implicit_any",
    "TS7031": "binding_any",
    "TS18046": "unknown_type_use",
    "TS18047": "possibly_null",
    "TS18048": "possibly_undefined",
}

TS_FIX_PROMPT_TEMPLATES: Dict[str, str] = {
    "null_check": """Fix the TypeScript error where an object is possibly 'null'.

Error: {error_message}
File: {file_path}
Line {line}, Column {column}

Code context:
```typescript
{code_context}
```

Generate a fix that adds proper null checking. Options include:
1. Optional chaining (?.)
2. Nullish coalescing (??)
3. Type guard (if statement)
4. Non-null assertion (!) - only if you're certain the value is never null

Return ONLY the fixed code snippet that should replace the problematic line(s).
Do not include explanations, just the code.""",

    "generic": """Fix the following TypeScript error.

Error: {error_message}
Error Code: {error_code}
File: {file_path}
Line {line}, Column {column}

Code context:
```typescript
{code_context}
```

Analyze the error and generate an appropriate fix.
Consider TypeScript best practices and type safety.

Return ONLY the fixed code snippet.
Do not include explanations, just the code.""",
}

STRATEGY_TO_TEMPLATE: Dict[str, str] = {
    "null_check": "null_check",
    "undefined_check": "null_check",
    "implicit_any": "generic",
    "type_mismatch": "generic",
    "property_missing": "generic",
    "argument_type": "generic",
    "unknown_type": "generic",
    "unknown_type_use": "generic",
    "binding_any": "generic",
    "argument_count": "generic",
    "possibly_null": "null_check",
    "possibly_undefined": "null_check",
}


class RefactorAgentV2(BaseAgent):
    """
    Refactor Agent V2 - Migrated to BaseAgent with RoutingEngine

    This class demonstrates the migration pattern from the original
    RefactorAgent to use BaseAgent's call_llm() method with dynamic routing.

    Key Migration Changes:
    1. Inherits from BaseAgent instead of standalone class
    2. Uses self.call_llm() instead of direct LLMClient instantiation
    3. Task type is set to "coding" for TypeScript fixes
    4. Risk level is determined by the error type
    5. Telemetry v2 events are emitted automatically

    Usage:
        agent = RefactorAgentV2()
        input = AgentInput(
            task_id="refactor-001",
            prompt="Fix TS2531 null check error",
            task_type="coding",
            risk_level="low",
            context={"error": error.to_dict(), "code_context": "..."}
        )
        output = agent.run(input)
    """

    def __init__(self, repo_path: Optional[str] = None):
        """
        Initialize RefactorAgentV2

        Args:
            repo_path: Optional path to repository root
        """
        super().__init__(agent_id="refactor_agent_v2")
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()
        self._load_settings()
        logger.info("[RefactorAgentV2] Initialized with BaseAgent integration")

    def _load_settings(self):
        """Load settings from environment"""
        try:
            from common.config.settings import settings
            self.enabled = getattr(settings, 'refactor_agent_enabled', True)
            self.errors_per_run = getattr(
                settings, 'refactor_agent_errors_per_run', 10
            )
        except (ImportError, AttributeError):
            self.enabled = True
            self.errors_per_run = 10

    def execute(self, input: AgentInput) -> AgentOutput:
        """
        Execute the refactor agent's main task

        This method implements the abstract execute() from BaseAgent.
        It processes a single TypeScript error fix request.

        Args:
            input: AgentInput containing:
                - task_id: Unique task identifier
                - prompt: The fix prompt (can be auto-generated)
                - task_type: Should be "coding" for TS fixes
                - risk_level: Based on error type
                - context: Dict with "error" and "code_context"

        Returns:
            AgentOutput with fix result
        """
        error_dict = input.context.get("error", {})
        code_context = input.context.get("code_context", "")

        if not error_dict:
            return AgentOutput(
                task_id=input.task_id,
                success=False,
                error="No error provided in context"
            )

        error = TSError(**error_dict)
        strategy = TS_FIX_STRATEGIES.get(error.error_code, "generic")
        template_key = STRATEGY_TO_TEMPLATE.get(strategy, "generic")
        template = TS_FIX_PROMPT_TEMPLATES.get(template_key, TS_FIX_PROMPT_TEMPLATES["generic"])

        prompt = template.format(
            error_message=error.message,
            error_code=error.error_code,
            file_path=error.file_path,
            line=error.line,
            column=error.column,
            code_context=code_context
        )

        try:
            result = self.call_llm(
                prompt=prompt,
                task_type="coding",
                risk_level=input.risk_level,
                system_prompt="You are an expert TypeScript developer. Fix the error with minimal changes.",
                temperature=0.3,
                max_tokens=500
            )

            fix_content = result.get("content", "")

            if len(fix_content.strip()) < 5:
                return AgentOutput(
                    task_id=input.task_id,
                    success=False,
                    error="Generated fix is too short or empty",
                    model_used=result.get("model"),
                    provider_used=result.get("provider"),
                    tokens_in=result.get("tokens_in"),
                    tokens_out=result.get("tokens_out")
                )

            return AgentOutput(
                task_id=input.task_id,
                success=True,
                data={
                    "fix": fix_content,
                    "strategy": strategy,
                    "error": error.to_dict()
                },
                model_used=result.get("model"),
                provider_used=result.get("provider"),
                tokens_in=result.get("tokens_in"),
                tokens_out=result.get("tokens_out")
            )

        except Exception as e:
            logger.error(f"[RefactorAgentV2] Fix generation failed: {e}")
            return AgentOutput(
                task_id=input.task_id,
                success=False,
                error=str(e)
            )

    def generate_fix(self, error: TSError, code_context: str) -> AgentOutput:
        """
        Generate a fix for a TypeScript error

        This is a convenience method that wraps execute() with proper
        AgentInput construction.

        Args:
            error: TSError to fix
            code_context: Code context around the error

        Returns:
            AgentOutput with fix result
        """
        risk_level = self._determine_risk_level(error)

        input = AgentInput(
            task_id=f"fix-{error.error_code}-{error.line}",
            prompt=f"Fix {error.error_code}: {error.message}",
            task_type="coding",
            risk_level=risk_level,
            context={
                "error": error.to_dict(),
                "code_context": code_context
            }
        )

        return self.run(input)

    def _determine_risk_level(self, error: TSError) -> str:
        """
        Determine risk level based on error type

        Args:
            error: TSError to analyze

        Returns:
            Risk level string: "high", "medium", or "low"
        """
        high_risk_codes = {"TS2322", "TS2345"}
        medium_risk_codes = {"TS2339", "TS2554", "TS7006", "TS7031"}

        if error.error_code in high_risk_codes:
            return "high"
        elif error.error_code in medium_risk_codes:
            return "medium"
        else:
            return "low"

    def analyze_error(self, error: TSError) -> RefactorTask:
        """
        Analyze a TS error and create a refactor task

        Args:
            error: TSError to analyze

        Returns:
            RefactorTask with analysis
        """
        strategy = TS_FIX_STRATEGIES.get(error.error_code, "generic")
        risk_level = self._determine_risk_level(error)

        risk_enum = {
            "high": RefactorRisk.HIGH,
            "medium": RefactorRisk.MEDIUM,
            "low": RefactorRisk.LOW
        }.get(risk_level, RefactorRisk.MEDIUM)

        return RefactorTask(
            task_id=f"task-{error.error_code}-{error.line}",
            error=error,
            fix_strategy=strategy,
            estimated_risk=risk_enum
        )


def get_refactor_agent_v2(repo_path: Optional[str] = None) -> RefactorAgentV2:
    """
    Factory function to get RefactorAgentV2 instance

    Args:
        repo_path: Optional path to repository root

    Returns:
        RefactorAgentV2 instance
    """
    return RefactorAgentV2(repo_path=repo_path)
