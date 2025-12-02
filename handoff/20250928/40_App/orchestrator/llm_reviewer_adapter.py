#!/usr/bin/env python3
"""
LLM Reviewer Adapter - Phase 6 PR-3 Implementation
Integrates LLM-powered code review into LangGraph orchestrator

This module provides:
1. LLM-based code review using multiple providers (OpenAI, Gemini)
2. A/B testing support via ExperimentManager
3. JSON response parsing with retry logic
4. Graceful fallback to CI-only review on failure

Usage:
    from llm_reviewer_adapter import generate_llm_review

    review = generate_llm_review(
        pr_number=123,
        pr_url="https://github.com/owner/repo/pull/123",
        ci_state="success",
        goal="Add new feature",
        repo="owner/repo",
        trace_id="abc123"
    )
"""
import json
import logging
import time
from typing import Dict, Any, Optional

from common.config.settings import settings
from llm.client import get_client_for_component

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SEVERITY_ORDER = {
    "none": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}


def combine_severity(ci_severity: str, llm_severity: str) -> str:
    """
    Combine CI and LLM severities, taking the worse (higher) severity.

    Args:
        ci_severity: Severity from CI-based review
        llm_severity: Severity from LLM review

    Returns:
        Combined severity (the worse of the two)
    """
    ci_val = SEVERITY_ORDER.get(ci_severity, 0)
    llm_val = SEVERITY_ORDER.get(llm_severity, 0)
    final_val = max(ci_val, llm_val)

    for name, val in SEVERITY_ORDER.items():
        if val == final_val:
            return name
    return llm_severity or ci_severity


class LLMReviewerAdapter:
    """
    Adapter for LLM-powered code review in LangGraph orchestrator

    Features:
    - Multi-provider LLM support via get_client_for_component (OpenAI, Gemini)
    - A/B testing integration via ExperimentManager
    - JSON response parsing with retry/repair logic
    - Graceful fallback on failure
    """

    def __init__(self, trace_id: str):
        """
        Initialize LLM reviewer adapter

        Args:
            trace_id: Trace ID for experiment assignment and logging
        """
        self.trace_id = trace_id
        self.llm_client = None
        try:
            self.llm_client = get_client_for_component(
                component="reviewer",
                trace_id=trace_id,
                default_provider="openai"
            )
            logger.info(
                f"[LLM Reviewer] Initialized with provider={self.llm_client.provider_name}",
                extra={
                    "operation": "llm_reviewer_init",
                    "trace_id": trace_id,
                    "provider": self.llm_client.provider_name
                }
            )
        except Exception as e:
            logger.warning(f"[LLM Reviewer] LLM client not available: {e}")

    def generate_review(
        self,
        pr_number: Optional[int],
        pr_url: Optional[str],
        ci_state: str,
        goal: str,
        repo: str,
        base_quality_score: int,
        base_severity: str
    ) -> Dict[str, Any]:
        """
        Generate LLM-powered code review

        Args:
            pr_number: Pull request number
            pr_url: Pull request URL
            ci_state: CI check state (success, failure, pending, unknown)
            goal: Original user goal/task description
            repo: GitHub repository (owner/repo format)
            base_quality_score: Base quality score from CI-only review
            base_severity: Base severity from CI-only review

        Returns:
            Dict with review results:
            - quality_score: Combined quality score (0-100)
            - severity: Combined severity level
            - summary: Review summary
            - decision: Review decision (approve, needs_changes, block)
            - comments: List of review comments
            - llm_used: Whether LLM was used
            - provider: LLM provider used (if any)
        """
        if not self.llm_client or not self.llm_client.is_available():
            logger.warning("[LLM Reviewer] LLM client not available, skipping LLM review")
            return self._get_fallback_result(base_quality_score, base_severity)

        try:
            logger.info(
                f"[LLM Reviewer] Generating review for PR #{pr_number}",
                extra={
                    "operation": "llm_reviewer",
                    "trace_id": self.trace_id,
                    "pr_number": pr_number,
                    "ci_state": ci_state
                }
            )

            review_data = self._call_llm(
                pr_number=pr_number,
                pr_url=pr_url,
                ci_state=ci_state,
                goal=goal,
                repo=repo
            )

            llm_score = review_data.get("quality_score", base_quality_score)
            llm_severity = review_data.get("severity", "none")

            final_score = max(0, min(int(llm_score), base_quality_score, 100))
            final_severity = combine_severity(base_severity, llm_severity)

            logger.info(
                f"[LLM Reviewer] Review completed: score={final_score}, severity={final_severity}",
                extra={
                    "operation": "llm_reviewer",
                    "trace_id": self.trace_id,
                    "llm_score": llm_score,
                    "base_score": base_quality_score,
                    "final_score": final_score,
                    "llm_severity": llm_severity,
                    "base_severity": base_severity,
                    "final_severity": final_severity,
                    "review_time_ms": review_data.get("review_time_ms", 0)
                }
            )

            return {
                "quality_score": final_score,
                "severity": final_severity,
                "summary": review_data.get("summary", ""),
                "decision": review_data.get("decision", "needs_changes"),
                "comments": review_data.get("comments", []),
                "llm_used": True,
                "provider": self.llm_client.provider_name,
                "review_time_ms": review_data.get("review_time_ms", 0)
            }

        except Exception as e:
            logger.error(
                f"[LLM Reviewer] Review failed: {e}",
                extra={
                    "operation": "llm_reviewer",
                    "trace_id": self.trace_id,
                    "error": str(e)
                },
                exc_info=True
            )
            return self._get_fallback_result(base_quality_score, base_severity)

    def _call_llm(
        self,
        pr_number: Optional[int],
        pr_url: Optional[str],
        ci_state: str,
        goal: str,
        repo: str
    ) -> Dict[str, Any]:
        """
        Call LLM to generate review

        Args:
            pr_number: Pull request number
            pr_url: Pull request URL
            ci_state: CI check state
            goal: User's goal
            repo: GitHub repository

        Returns:
            Dict with review data and timing
        """
        use_json_mode = getattr(settings, 'reviewer_json_mode', True)

        system_prompt = """You are a senior software engineer performing code review for a pull request.

You receive:
1. The CI status for this PR (success, failure, pending, or unknown)
2. The task goal/description
3. Repository and PR metadata

IMPORTANT: You do NOT see the actual code diff. You are providing a high-level risk assessment based on the available metadata and CI status. Be conservative in your assessment.

Your job is to:
1. Assess overall code quality risk based on CI status and task complexity
2. Identify potential concerns based on the task description
3. Produce a JSON object that summarizes your assessment

Rules:
- Be conservative: if CI failed, severity should be at least "high"
- If CI passed, you can still flag concerns based on task complexity
- If information is limited, default to moderate scores and "needs_changes" decision
- Always respond with valid JSON only, no extra commentary

Output format (strict JSON):
{
  "summary": "Brief assessment of the PR based on available information",
  "quality_score": 0-100,
  "severity": "none" | "low" | "medium" | "high" | "critical",
  "decision": "approve" | "needs_changes" | "block",
  "comments": [
    {
      "severity": "nit" | "suggestion" | "warning" | "error",
      "category": "style" | "bug" | "performance" | "security" | "maintainability" | "other",
      "message": "Description of concern or suggestion"
    }
  ]
}

Guidelines for scoring:
- CI success + simple task: quality_score 70-85, severity "none" or "low"
- CI success + complex task: quality_score 60-75, severity "low" or "medium"
- CI pending: quality_score 50-65, severity "medium"
- CI failure: quality_score 30-50, severity "high" or "critical"
"""

        user_prompt = f"""**Pull Request Information**
- Repository: {repo}
- PR Number: {pr_number or "Unknown"}
- PR URL: {pr_url or "Not available"}
- CI Status: {ci_state}

**Task Goal/Description**:
{goal}

Based on this information, provide your code review assessment as JSON.
Remember: You cannot see the actual code changes, so focus on risk assessment based on CI status and task complexity."""

        start_time = time.time()

        try:
            if use_json_mode:
                logger.info(f"[LLM Reviewer] Using JSON mode for trace_id={self.trace_id}")

            # Build kwargs for provider-specific parameters
            generate_kwargs = {
                "prompt": user_prompt,
                "system_prompt": system_prompt,
                "temperature": 0.5,
                "max_tokens": 1000,
                "json_mode": use_json_mode,
                "timeout": 20
            }

            # Add thinking_level for Gemini 3 models based on reasoning_mode_enabled setting
            if self.llm_client.provider_name == "gemini":
                reasoning_mode_enabled = getattr(settings, 'reasoning_mode_enabled', False)
                thinking_level = "high" if reasoning_mode_enabled else "low"
                generate_kwargs["thinking_level"] = thinking_level
                logger.info(
                    f"[LLM Reviewer] Using thinking_level={thinking_level} for Gemini provider",
                    extra={
                        "operation": "llm_reviewer",
                        "trace_id": self.trace_id,
                        "thinking_level": thinking_level,
                        "reasoning_mode_enabled": reasoning_mode_enabled
                    }
                )

            response = self.llm_client.generate(**generate_kwargs)

            review_time_ms = (time.time() - start_time) * 1000

            content = response.content
            review = self._parse_json_with_retry(content, use_json_mode)

            logger.info(
                f"[LLM Reviewer] Generated review using {response.provider}/{response.model}",
                extra={
                    "operation": "llm_reviewer",
                    "trace_id": self.trace_id,
                    "provider": response.provider,
                    "model": response.model,
                    "usage": response.usage,
                    "review_time_ms": review_time_ms
                }
            )

            review["review_time_ms"] = review_time_ms
            return review

        except json.JSONDecodeError as e:
            logger.error(f"[LLM Reviewer] Failed to parse LLM response as JSON: {e}")
            raise
        except Exception as e:
            logger.error(f"[LLM Reviewer] LLM API call failed: {e}")
            raise

    def _parse_json_with_retry(self, content: str, use_json_mode: bool) -> Dict[str, Any]:
        """
        Parse JSON with retry and repair logic

        Args:
            content: Raw LLM response
            use_json_mode: Whether JSON mode was used

        Returns:
            Parsed review dict

        Raises:
            json.JSONDecodeError: If parsing fails after retry
        """
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.warning(f"[LLM Reviewer] First parse attempt failed: {e}, attempting repair")

            try:
                cleaned_content = self._clean_json_response(content)
                logger.info(f"[LLM Reviewer] Cleaned content for trace_id={self.trace_id}")
                return json.loads(cleaned_content)
            except json.JSONDecodeError as e2:
                logger.error(f"[LLM Reviewer] Failed to parse even after cleaning: {e2}")
                raise e2

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
        content = content.strip()

        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]

        if content.endswith("```"):
            content = content[:-3]

        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1 and end > start:
            content = content[start:end + 1]

        return content.strip()

    def _get_fallback_result(
        self,
        base_quality_score: int,
        base_severity: str
    ) -> Dict[str, Any]:
        """
        Get fallback result when LLM is unavailable

        Args:
            base_quality_score: Base quality score from CI-only review
            base_severity: Base severity from CI-only review

        Returns:
            Dict with fallback review results
        """
        if base_severity == "none":
            decision = "approve"
        else:
            decision = "needs_changes"

        return {
            "quality_score": base_quality_score,
            "severity": base_severity,
            "summary": "LLM review unavailable, using CI-based assessment",
            "decision": decision,
            "comments": [],
            "llm_used": False,
            "provider": None,
            "review_time_ms": 0
        }


def generate_llm_review(
    pr_number: Optional[int],
    pr_url: Optional[str],
    ci_state: str,
    goal: str,
    repo: str,
    trace_id: str,
    base_quality_score: int,
    base_severity: str
) -> Dict[str, Any]:
    """
    Convenience function to generate LLM-powered code review

    Args:
        pr_number: Pull request number
        pr_url: Pull request URL
        ci_state: CI check state (success, failure, pending, unknown)
        goal: Original user goal/task description
        repo: GitHub repository (owner/repo format)
        trace_id: Unique trace identifier
        base_quality_score: Base quality score from CI-only review
        base_severity: Base severity from CI-only review

    Returns:
        Dict with review results
    """
    adapter = LLMReviewerAdapter(trace_id=trace_id)
    return adapter.generate_review(
        pr_number=pr_number,
        pr_url=pr_url,
        ci_state=ci_state,
        goal=goal,
        repo=repo,
        base_quality_score=base_quality_score,
        base_severity=base_severity
    )
