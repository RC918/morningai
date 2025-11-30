#!/usr/bin/env python3
"""
LLM Planner Adapter - Phase 1 Implementation
Integrates LLM-powered dynamic planning into LangGraph orchestrator

This module provides:
1. LLM-based plan generation using multiple providers (OpenAI, Gemini)
2. Task classification integration
3. Code context extraction
4. Plan validation and fallback logic
5. Planner accuracy metric recording

Updated in Phase 2 Extra to use LLMClient abstraction layer.
"""
import json
import logging
import time
from typing import Dict, List, Any, Optional

from common.config.settings import settings
from llm.client import LLMClient

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMPlannerAdapter:
    """
    Adapter for LLM-powered dynamic planning in LangGraph orchestrator

    Features:
    - Multi-provider LLM support via LLMClient (OpenAI, Gemini)
    - Task classification integration
    - Code context extraction (<2000 tokens)
    - Plan validation (3-7 steps)
    - Fallback to static planning on failure
    - Planner accuracy metric recording
    """

    def __init__(self, provider: Optional[str] = None):
        """
        Initialize LLM planner adapter

        Args:
            provider: LLM provider to use (openai, gemini, auto)
                     If None, uses LLM_PROVIDER env var or defaults to openai
        """
        self.llm_client = None
        self._openai_client = None
        try:
            self.llm_client = LLMClient(provider=provider)
            logger.info(
                f"[LLM Planner] Initialized with provider={self.llm_client.provider_name}"
            )
            if self.llm_client.provider_name == "openai" and OpenAI and settings.openai_api_key:
                self._openai_client = OpenAI(api_key=settings.openai_api_key)
        except ValueError as e:
            logger.warning(f"LLM client not available: {e}")

    @property
    def client(self):
        """
        Backward compatibility: Return OpenAI client for tests that expect it

        Returns:
            OpenAI client instance or None if not available
        """
        return self._openai_client

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
        if not self.llm_client or not self.llm_client.is_available():
            logger.warning("[LLM Planner] LLM client not available, using static plan")
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
                provider = plan_data.get("provider")

                self.record_planner_event(
                    trace_id=trace_id,
                    goal=goal,
                    planner_type="llm",
                    task_type=task_type,
                    actual_plan_steps=plan_steps,
                    planning_time_ms=plan_data["planning_time_ms"],
                    provider=provider
                )

                return {
                    "plan": plan_steps,
                    "plan_details": plan_data["plan"],
                    "planner_type": "llm",
                    "task_type": task_type,
                    "planning_time_ms": plan_data["planning_time_ms"],
                    "provider": provider
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

    def _clean_json_response(self, content: str) -> str:
        """
        Clean and repair JSON response from LLM

        Handles common issues:
        - Markdown code blocks (```json ... ```)
        - Explanatory text before/after JSON
        - Extra whitespace

        Args:
            content: Raw LLM response

        Returns:
            Cleaned JSON string
        """
        import re

        content = re.sub(r'^```json\s*', '', content, flags=re.MULTILINE)
        content = re.sub(r'^```\s*$', '', content, flags=re.MULTILINE)
        content = re.sub(r'```$', '', content)

        match = re.search(r'\[.*\]', content, flags=re.DOTALL)
        if match:
            content = match.group(0)

        content = content.strip()

        return content

    def _call_llm(
        self,
        goal: str,
        task_type: str,
        code_context: str,
        trace_id: str
    ) -> Dict[str, Any]:
        """
        Call LLM to generate plan using LLMClient abstraction

        Args:
            goal: User's goal
            task_type: Task type from classifier
            code_context: Code context (<2000 tokens)
            trace_id: Trace ID for logging

        Returns:
            Dict with plan and planning_time_ms
        """
        use_json_mode = settings.planner_json_mode

        if use_json_mode:
            system_prompt = """You are a senior software engineer creating executable plans for code tasks.

Generate a plan with 3-7 steps that are specific, actionable, and ordered correctly.

Return a JSON object with a "plan" key containing an array of steps.

Output format (strict JSON):
{
  "plan": [
    {"step": "Step description", "rationale": "Why this step", "risk": "low|medium|high"},
    ...
  ]
}

Requirements:
- 3-7 steps only
- Each step must have: step, rationale, risk
- Steps must be specific and actionable
- Risk must be one of: low, medium, high
"""
        else:
            system_prompt = """You are a senior software engineer creating executable plans for code tasks.

Generate a plan with 3-7 steps that are specific, actionable, and ordered correctly.

IMPORTANT: Return ONLY a valid JSON array. Do not include any explanatory text, markdown formatting, or code blocks.

Output format (strict JSON array):
[
  {"step": "Step description", "rationale": "Why this step", "risk": "low|medium|high"},
  ...
]

Requirements:
- 3-7 steps only
- Each step must have: step, rationale, risk
- Steps must be specific and actionable
- Risk must be one of: low, medium, high
- Return ONLY the JSON array, nothing else
"""

        user_prompt = f"""**Goal**: {goal}

**Task Type**: {task_type}

**Code Context** (relevant files/functions):
{code_context[:1000] if code_context else "No context available"}

Generate a 3-7 step plan to accomplish this goal. Return ONLY the JSON array."""

        start_time = time.time()

        try:
            if use_json_mode:
                logger.info(f"[LLM Planner] Using JSON mode for trace_id={trace_id}")

            # Build kwargs for provider-specific parameters
            generate_kwargs = {
                "prompt": user_prompt,
                "system_prompt": system_prompt,
                "temperature": 0.7,
                "max_tokens": 1000,
                "json_mode": use_json_mode,
                "timeout": 25
            }

            # Add thinking_level for Gemini 3 models (complex planning benefits from deep reasoning)
            if self.llm_client.provider_name == "gemini":
                generate_kwargs["thinking_level"] = "high"
                logger.info(
                    "[LLM Planner] Using thinking_level=high for Gemini provider",
                    extra={
                        "operation": "llm_planner",
                        "trace_id": trace_id,
                        "thinking_level": "high"
                    }
                )

            response = self.llm_client.generate(**generate_kwargs)

            planning_time_ms = (time.time() - start_time) * 1000

            content = response.content

            plan = self._parse_json_with_retry(content, use_json_mode, trace_id)

            self._record_planning_time(trace_id, planning_time_ms)

            logger.info(
                f"[LLM Planner] Generated plan using {response.provider}/{response.model}",
                extra={
                    "operation": "llm_planner",
                    "trace_id": trace_id,
                    "provider": response.provider,
                    "model": response.model,
                    "usage": response.usage
                }
            )

            return {
                "plan": plan,
                "planning_time_ms": planning_time_ms,
                "provider": response.provider
            }

        except json.JSONDecodeError as e:
            logger.error(f"[LLM Planner] Failed to parse LLM response as JSON: {e}")
            raise
        except Exception as e:
            logger.error(f"[LLM Planner] LLM API call failed: {e}")
            raise

    def _parse_json_with_retry(self, content: str, use_json_mode: bool, trace_id: str) -> List[Dict[str, Any]]:
        """
        Parse JSON with retry and repair logic

        Args:
            content: Raw LLM response
            use_json_mode: Whether JSON mode was used
            trace_id: Trace ID for logging

        Returns:
            Parsed plan array

        Raises:
            json.JSONDecodeError: If parsing fails after retry
        """
        try:
            if use_json_mode:
                parsed = json.loads(content)
                if isinstance(parsed, dict) and "plan" in parsed:
                    return parsed["plan"]
                elif isinstance(parsed, list):
                    return parsed
                else:
                    raise json.JSONDecodeError(f"Unexpected JSON structure: {type(parsed)}", content, 0)
            else:
                return json.loads(content)
        except json.JSONDecodeError as e:
            logger.warning(f"[LLM Planner] First parse attempt failed: {e}, attempting repair")

            try:
                cleaned_content = self._clean_json_response(content)
                logger.info(f"[LLM Planner] Cleaned content for trace_id={trace_id}")

                if use_json_mode:
                    parsed = json.loads(cleaned_content)
                    if isinstance(parsed, dict) and "plan" in parsed:
                        logger.info("[LLM Planner] Successfully parsed after cleaning (JSON mode)")
                        return parsed["plan"]
                    elif isinstance(parsed, list):
                        logger.info("[LLM Planner] Successfully parsed after cleaning (array fallback)")
                        return parsed
                    else:
                        raise json.JSONDecodeError(f"Unexpected JSON structure after cleaning: {type(parsed)}", cleaned_content, 0)
                else:
                    plan = json.loads(cleaned_content)
                    logger.info("[LLM Planner] Successfully parsed after cleaning")
                    return plan
            except json.JSONDecodeError as e2:
                logger.error(f"[LLM Planner] Failed to parse even after cleaning: {e2}")
                logger.error(f"[LLM Planner] Original content: {content[:200]}...")
                logger.error(f"[LLM Planner] Cleaned content: {cleaned_content[:200]}...")
                raise e2

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
        planning_time_ms: float,
        provider: Optional[str] = None
    ):
        """
        Record planner event to both JSONL file and database

        Dual-write strategy:
        1. Write to JSONL file (backward compatibility, local dev)
        2. Write to database (persistent storage, production)

        Args:
            trace_id: Trace ID
            goal: User's goal
            planner_type: Type of planner used (llm/static)
            task_type: Task type from classifier
            actual_plan_steps: List of plan steps
            planning_time_ms: Planning time in milliseconds
            provider: LLM provider used (e.g., "openai", "gemini"). None for static plans.
        """
        import json
        import os
        from datetime import datetime, timezone

        from common.utils.path_utils import resolve_planner_events_path
        from common.config.settings import settings

        timestamp = datetime.now(timezone.utc)

        # Write to JSONL file (backward compatibility)
        try:
            events_path = resolve_planner_events_path()
            os.makedirs(os.path.dirname(events_path), exist_ok=True)

            event = {
                "trace_id": trace_id,
                "goal": goal,
                "planner_type": planner_type,
                "task_type": task_type,
                "actual_plan_steps": actual_plan_steps,
                "num_steps": len(actual_plan_steps),
                "planning_time_ms": planning_time_ms,
                "timestamp": timestamp.isoformat(),
                "provider": provider
            }

            with open(events_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(event) + '\n')
            logger.info(f"[LLM Planner] Recorded planner event to {events_path}")
        except Exception as e:
            logger.warning(f"[LLM Planner] Failed to record planner event to JSONL at {events_path}: {e}")

        # Write to database (persistent storage)
        storage_mode = getattr(settings, 'planner_events_storage', 'db')
        if storage_mode == 'db':
            try:
                from persistence.planner_events_store import insert_planner_event

                success = insert_planner_event(
                    trace_id=trace_id,
                    goal=goal,
                    planner_type=planner_type,
                    task_type=task_type,
                    actual_plan_steps=actual_plan_steps,
                    planning_time_ms=planning_time_ms,
                    timestamp=timestamp,
                    provider=provider
                )

                if success:
                    logger.info(f"[LLM Planner] Recorded planner event to database (trace_id={trace_id})")
                else:
                    logger.warning(f"[LLM Planner] Failed to record planner event to database (trace_id={trace_id})")
            except Exception as e:
                logger.warning(
                    f"[LLM Planner] Failed to record planner event to database: {e}",
                    exc_info=True
                )


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
