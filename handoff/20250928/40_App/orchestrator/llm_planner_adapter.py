#!/usr/bin/env python3
"""
LLM Planner Adapter - Phase 1 Implementation
Integrates LLM-powered dynamic planning into LangGraph orchestrator

This module provides:
1. LLM-based plan generation using GPT-4
2. Task classification integration
3. Code context extraction
4. Plan validation and fallback logic
5. Planner accuracy metric recording
"""
import json
import logging
import time
from typing import Dict, List, Any, Optional
from openai import OpenAI

from common.config.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMPlannerAdapter:
    """
    Adapter for LLM-powered dynamic planning in LangGraph orchestrator

    Features:
    - GPT-4 based plan generation
    - Task classification integration
    - Code context extraction (<2000 tokens)
    - Plan validation (3-7 steps)
    - Fallback to static planning on failure
    - Planner accuracy metric recording
    """

    def __init__(self):
        """Initialize LLM planner adapter"""
        self.client = None
        if settings.openai_api_key:
            self.client = OpenAI(api_key=settings.openai_api_key)
        else:
            logger.warning("OpenAI API key not found, LLM planner will not be available")

    def generate_plan(
        self,
        goal: str,
        repo: str,
        trace_id: str,
        task_type: Optional[str] = None,
        code_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate dynamic plan using LLM

        Args:
            goal: User's goal/question
            repo: GitHub repository (owner/repo format)
            trace_id: Unique identifier for this task
            task_type: Optional task type from classifier
            code_context: Optional code context (<2000 tokens)

        Returns:
            Dict with plan, planner_type, and metadata
        """
        if not self.client:
            logger.warning("[LLM Planner] OpenAI client not available, using static plan")
            return self._get_static_plan(task_type)

        try:
            logger.info(f"[LLM Planner] Generating plan for goal: {goal[:50]}...", extra={
                "operation": "llm_planner",
                "trace_id": trace_id,
                "task_type": task_type
            })

            if not task_type:
                try:
                    from agents.dev_agent.workflows.task_classifier import classify_task
                    classification = classify_task(goal)
                    task_type = classification.get("task_type", "unknown")
                except ImportError:
                    try:
                        from agents.dev_agent.workflows.task_classifier import TaskClassifier
                        classifier = TaskClassifier()
                        task_type_enum = classifier.classify(goal)
                        task_type = task_type_enum.value if hasattr(task_type_enum, 'value') else str(task_type_enum)
                    except Exception as e:
                        logger.warning(f"[LLM Planner] Failed to classify task: {e}")
                        task_type = "unknown"
                except Exception as e:
                    logger.warning(f"[LLM Planner] Failed to classify task: {e}")
                    task_type = "unknown"

            if not code_context:
                code_context = self._get_code_context(repo, goal)

            plan_data = self._call_llm(goal, task_type, code_context, trace_id)

            if self._validate_plan(plan_data["plan"]):
                logger.info(f"[LLM Planner] Generated valid plan with {len(plan_data['plan'])} steps", extra={
                    "operation": "llm_planner",
                    "trace_id": trace_id,
                    "steps": len(plan_data["plan"]),
                    "planning_time_ms": plan_data["planning_time_ms"]
                })

                plan_steps = [step["step"] for step in plan_data["plan"]]

                self.record_planner_event(
                    trace_id=trace_id,
                    goal=goal,
                    planner_type="llm",
                    task_type=task_type,
                    actual_plan_steps=plan_steps,
                    planning_time_ms=plan_data["planning_time_ms"]
                )

                return {
                    "plan": plan_steps,
                    "plan_details": plan_data["plan"],
                    "planner_type": "llm",
                    "task_type": task_type,
                    "planning_time_ms": plan_data["planning_time_ms"]
                }
            else:
                logger.warning("[LLM Planner] Generated invalid plan, falling back to static")
                return self._get_static_plan(task_type)

        except Exception as e:
            logger.error(f"[LLM Planner] Failed to generate plan: {e}", extra={
                "operation": "llm_planner",
                "trace_id": trace_id,
                "error": str(e)
            })
            return self._get_static_plan(task_type)

    def _call_llm(
        self,
        goal: str,
        task_type: str,
        code_context: str,
        trace_id: str
    ) -> Dict[str, Any]:
        """
        Call GPT-4 to generate plan

        Args:
            goal: User's goal
            task_type: Task type from classifier
            code_context: Code context (<2000 tokens)
            trace_id: Trace ID for logging

        Returns:
            Dict with plan and planning_time_ms
        """
        system_prompt = """You are a senior software engineer creating executable plans for code tasks.

Generate a plan with 3-7 steps that are specific, actionable, and ordered correctly.

Output format (strict JSON):
[
  {"step": "Step description", "rationale": "Why this step", "risk": "low|medium|high"},
  ...
]

Requirements:
- 3-7 steps only
- Each step must have: step, rationale, risk
- Steps must be specific and actionable
- Risk must be one of: low, medium, high
"""

        user_prompt = f"""**Goal**: {goal}

**Task Type**: {task_type}

**Code Context** (relevant files/functions):
{code_context[:1000] if code_context else "No context available"}

Generate a 3-7 step plan to accomplish this goal."""

        start_time = time.time()

        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1000,
                timeout=25  # 25 second timeout (leave 5 sec buffer for 30 sec target)
            )

            planning_time_ms = (time.time() - start_time) * 1000

            content = response.choices[0].message.content
            plan = json.loads(content)

            self._record_planning_time(trace_id, planning_time_ms)

            return {
                "plan": plan,
                "planning_time_ms": planning_time_ms
            }

        except json.JSONDecodeError as e:
            logger.error(f"[LLM Planner] Failed to parse LLM response as JSON: {e}")
            raise
        except Exception as e:
            logger.error(f"[LLM Planner] LLM API call failed: {e}")
            raise

    def _validate_plan(self, plan: List[Dict[str, Any]]) -> bool:
        """
        Validate plan structure and constraints

        Args:
            plan: Plan from LLM

        Returns:
            True if valid, False otherwise
        """
        if not isinstance(plan, list):
            logger.warning("[LLM Planner] Plan is not a list")
            return False

        if not (3 <= len(plan) <= 7):
            logger.warning(f"[LLM Planner] Plan has {len(plan)} steps, expected 3-7")
            return False

        for i, step in enumerate(plan):
            if not isinstance(step, dict):
                logger.warning(f"[LLM Planner] Step {i} is not a dict")
                return False

            required_keys = ["step", "rationale", "risk"]
            if not all(k in step for k in required_keys):
                logger.warning(f"[LLM Planner] Step {i} missing required keys: {required_keys}")
                return False

            if step["risk"] not in ["low", "medium", "high"]:
                logger.warning(f"[LLM Planner] Step {i} has invalid risk: {step['risk']}")
                return False

        return True

    def _get_code_context(self, repo: str, goal: str, max_tokens: int = 2000) -> str:
        """
        Extract relevant code context for planning

        Args:
            repo: GitHub repository
            goal: User's goal
            max_tokens: Maximum tokens for context

        Returns:
            Code context string (<max_tokens)
        """
        try:
            from context_manager import get_code_context
            return get_code_context(repo, goal, max_files=5, max_tokens=max_tokens)
        except Exception as e:
            logger.warning(f"[LLM Planner] Failed to extract code context: {e}")
            context = f"Repository: {repo}\n"
            context += f"Goal: {goal}\n"
            context += "\nNote: Code context extraction failed"
            return context[:max_tokens]

    def _get_static_plan(self, task_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Get static fallback plan

        Args:
            task_type: Optional task type

        Returns:
            Dict with static plan and metadata
        """
        plan = [
            "Analyze requirements and identify impacted files",
            "Create a feature branch",
            "Implement changes with unit tests",
            "Run lint and unit tests locally",
            "Commit and push changes",
            "Open a pull request",
            "Monitor CI and address failures"
        ]

        logger.info(f"[LLM Planner] Using static plan with {len(plan)} steps", extra={
            "operation": "llm_planner",
            "planner_type": "static",
            "task_type": task_type
        })

        return {
            "plan": plan,
            "plan_details": [{"step": s, "rationale": "Static plan", "risk": "low"} for s in plan],
            "planner_type": "static",
            "task_type": task_type,
            "planning_time_ms": 0
        }

    def _record_planning_time(self, trace_id: str, planning_time_ms: float):
        """
        Record planning time metric

        Args:
            trace_id: Trace ID
            planning_time_ms: Planning time in milliseconds
        """
        logger.info(f"[LLM Planner] Planning time: {planning_time_ms:.2f}ms", extra={
            "operation": "llm_planner_metric",
            "trace_id": trace_id,
            "planning_time_ms": planning_time_ms
        })

    def record_planner_event(
        self,
        trace_id: str,
        goal: str,
        planner_type: str,
        task_type: str,
        actual_plan_steps: List[str],
        planning_time_ms: float
    ):
        """
        Record planner event to JSONL file for agent_eval

        Args:
            trace_id: Trace ID
            goal: User's goal
            planner_type: Type of planner used (llm/static)
            task_type: Task type from classifier
            actual_plan_steps: List of plan steps
            planning_time_ms: Planning time in milliseconds
        """
        import json
        import os
        from datetime import datetime

        events_file = os.environ.get('PLANNER_EVENTS_FILE', 'tools/agent_eval/data/planner_runs.jsonl')
        events_path = os.path.join(os.path.expanduser('~'), 'repos', 'morningai', events_file)

        os.makedirs(os.path.dirname(events_path), exist_ok=True)

        event = {
            "trace_id": trace_id,
            "goal": goal,
            "planner_type": planner_type,
            "task_type": task_type,
            "actual_plan_steps": actual_plan_steps,
            "num_steps": len(actual_plan_steps),
            "planning_time_ms": planning_time_ms,
            "timestamp": datetime.utcnow().isoformat()
        }

        try:
            with open(events_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(event) + '\n')
            logger.info(f"[LLM Planner] Recorded planner event to {events_file}")
        except Exception as e:
            logger.warning(f"[LLM Planner] Failed to record planner event: {e}")


def generate_llm_plan(
    goal: str,
    repo: str,
    trace_id: str,
    task_type: Optional[str] = None,
    code_context: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to generate LLM plan

    Args:
        goal: User's goal
        repo: GitHub repository
        trace_id: Trace ID
        task_type: Optional task type
        code_context: Optional code context

    Returns:
        Dict with plan and metadata
    """
    adapter = LLMPlannerAdapter()
    return adapter.generate_plan(goal, repo, trace_id, task_type, code_context)
