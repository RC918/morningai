#!/usr/bin/env python3
"""
Planner Events Store - Shared database operations for planner metrics

This module provides a unified interface for storing and querying planner events
in the database. Used by both the orchestrator (for writing) and monitoring tools
(for reading).

Phase 1 Monitoring: Replaces ephemeral JSONL files with persistent database storage.
"""
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
from .db_client import get_client

logger = logging.getLogger(__name__)


def insert_planner_event(
    trace_id: str,
    goal: str,
    planner_type: str,
    task_type: str,
    actual_plan_steps: List[str],
    planning_time_ms: float,
    timestamp: Optional[datetime] = None,
    provider: Optional[str] = None
) -> bool:
    """
    Insert a planner event into the database.

    Args:
        trace_id: Unique identifier for the task/trace
        goal: Task goal/description
        planner_type: Type of planner used (e.g., "llm", "simple")
        task_type: Classification of the task
        actual_plan_steps: List of plan steps generated
        planning_time_ms: Time taken to generate plan in milliseconds
        timestamp: When the plan was generated (defaults to now)
        provider: LLM provider used (e.g., "openai", "gemini"). None for static plans.

    Returns:
        True if successful, False otherwise
    """
    try:
        client = get_client()

        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        # Convert datetime to ISO format string for Supabase
        timestamp_str = timestamp.isoformat() if isinstance(timestamp, datetime) else timestamp

        data = {
            "trace_id": trace_id,
            "goal": goal,
            "planner_type": planner_type,
            "task_type": task_type,
            "actual_plan_steps": actual_plan_steps,  # Supabase handles JSONB automatically
            "num_steps": len(actual_plan_steps),
            "planning_time_ms": planning_time_ms,
            "timestamp": timestamp_str,
            "provider": provider
        }

        client.table("planner_events").insert(data).execute()

        logger.info(
            f"[Planner Events Store] Inserted event: trace_id={trace_id}, "
            f"planner_type={planner_type}, provider={provider}, num_steps={len(actual_plan_steps)}"
        )
        return True

    except Exception as e:
        logger.error(
            f"[Planner Events Store] Failed to insert event for trace_id={trace_id}: {e}",
            exc_info=True
        )
        return False


def query_planner_events(
    limit: Optional[int] = None,
    planner_type_filter: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    trace_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Query planner events from the database.

    Args:
        limit: Maximum number of events to return (most recent first)
        planner_type_filter: Filter by planner type (e.g., "llm")
        start_time: Filter events after this time
        end_time: Filter events before this time
        trace_id: Filter by specific trace_id

    Returns:
        List of planner event dictionaries, ordered by timestamp DESC
    """
    try:
        client = get_client()

        # Start with base query
        query = client.table("planner_events").select("*")

        # Apply filters
        if trace_id:
            query = query.eq("trace_id", trace_id)

        if planner_type_filter:
            query = query.eq("planner_type", planner_type_filter)

        if start_time:
            start_str = start_time.isoformat() if isinstance(start_time, datetime) else start_time
            query = query.gte("timestamp", start_str)

        if end_time:
            end_str = end_time.isoformat() if isinstance(end_time, datetime) else end_time
            query = query.lte("timestamp", end_str)

        # Order by timestamp descending (most recent first)
        query = query.order("timestamp", desc=True)

        # Apply limit
        if limit:
            query = query.limit(limit)

        response = query.execute()

        events = response.data if response.data else []

        logger.info(
            f"[Planner Events Store] Queried {len(events)} events "
            f"(limit={limit}, planner_type={planner_type_filter})"
        )

        return events

    except Exception as e:
        logger.error(
            f"[Planner Events Store] Failed to query events: {e}",
            exc_info=True
        )
        return []


def get_planner_stats_summary(
    limit: Optional[int] = None,
    planner_type_filter: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get summary statistics for planner events.

    Args:
        limit: Maximum number of recent events to analyze
        planner_type_filter: Filter by planner type

    Returns:
        Dictionary with summary statistics (count, avg_time, median_time, etc.)
    """
    events = query_planner_events(
        limit=limit,
        planner_type_filter=planner_type_filter
    )

    if not events:
        return {
            "count": 0,
            "avg_planning_time_ms": 0,
            "median_planning_time_ms": 0,
            "avg_num_steps": 0,
            "median_num_steps": 0
        }

    # Calculate statistics
    planning_times = [e["planning_time_ms"] for e in events]
    num_steps = [e["num_steps"] for e in events]

    planning_times_sorted = sorted(planning_times)
    num_steps_sorted = sorted(num_steps)

    count = len(events)

    # Calculate medians
    if count % 2 == 0:
        median_planning_time = (
            planning_times_sorted[count // 2 - 1] + planning_times_sorted[count // 2]
        ) / 2
        median_num_steps = (
            num_steps_sorted[count // 2 - 1] + num_steps_sorted[count // 2]
        ) / 2
    else:
        median_planning_time = planning_times_sorted[count // 2]
        median_num_steps = num_steps_sorted[count // 2]

    return {
        "count": count,
        "avg_planning_time_ms": sum(planning_times) / count,
        "median_planning_time_ms": median_planning_time,
        "avg_num_steps": sum(num_steps) / count,
        "median_num_steps": median_num_steps,
        "planner_type_filter": planner_type_filter,
        "limit": limit
    }


def get_metrics_by_provider(
    days: int = 7,
    planner_type_filter: Optional[str] = "llm"
) -> Dict[str, Dict[str, Any]]:
    """
    Get aggregated metrics grouped by provider for experiment comparison.

    This function queries planner_events and aggregates statistics by provider,
    which is used to compare control (e.g., openai) vs treatment (e.g., gemini)
    performance in A/B experiments.

    Args:
        days: Number of days to look back (default: 7)
        planner_type_filter: Filter by planner type (default: "llm")

    Returns:
        Dictionary with provider as key and metrics as value:
        {
            "openai": {
                "total_requests": 100,
                "avg_latency_ms": 1250.5,
                "success_rate": 0.95,
                "error_rate": 0.05
            },
            "gemini": {...}
        }
    """
    try:
        from datetime import timedelta
        client = get_client()

        # Calculate start time
        start_time = datetime.now(timezone.utc) - timedelta(days=days)
        start_str = start_time.isoformat()

        # Query events with provider not null
        query = client.table("planner_events").select("*")

        if planner_type_filter:
            query = query.eq("planner_type", planner_type_filter)

        query = query.gte("timestamp", start_str)
        query = query.not_.is_("provider", "null")

        response = query.execute()
        events = response.data if response.data else []

        if not events:
            logger.info("[Planner Events Store] No events found for metrics aggregation")
            return {}

        # Group by provider and calculate metrics
        provider_stats: Dict[str, Dict[str, Any]] = {}

        for event in events:
            provider = event.get("provider")
            if not provider:
                continue

            if provider not in provider_stats:
                provider_stats[provider] = {
                    "total_requests": 0,
                    "total_latency_ms": 0.0,
                    "success_count": 0,
                    "error_count": 0
                }

            stats = provider_stats[provider]
            stats["total_requests"] += 1

            # Add latency
            latency = event.get("planning_time_ms", 0)
            stats["total_latency_ms"] += latency

            # Count success/error based on whether plan steps were generated
            plan_steps = event.get("actual_plan_steps", [])
            if plan_steps and len(plan_steps) > 0:
                stats["success_count"] += 1
            else:
                stats["error_count"] += 1

        # Calculate final metrics
        result: Dict[str, Dict[str, Any]] = {}
        for provider, stats in provider_stats.items():
            total = stats["total_requests"]
            if total > 0:
                result[provider] = {
                    "total_requests": total,
                    "avg_latency_ms": round(stats["total_latency_ms"] / total, 2),
                    "success_rate": round(stats["success_count"] / total, 4),
                    "error_rate": round(stats["error_count"] / total, 4)
                }

        logger.info(
            f"[Planner Events Store] Aggregated metrics for {len(result)} providers: "
            f"{list(result.keys())}"
        )

        return result

    except Exception as e:
        logger.error(
            f"[Planner Events Store] Failed to get metrics by provider: {e}",
            exc_info=True
        )
        return {}
