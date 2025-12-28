"""
Resource Telemetry Module for P1 瘦身計畫 (Issue #3197)

Provides per-workflow resource measurement and telemetry events:
- [RESOURCE_PEAK]: RSS measurement after each major node
- [DIFF_FETCH_BYTES]: Diff fetch payload size
- [PROMPT_BUILD_BYTES]: LLM prompt size before call
- [CHECKPOINT_PUT_BYTES]: Checkpoint payload size
- [LLM_RESPONSE_BYTES]: LLM response size

All events include trace_id for correlation.
"""

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


def get_current_rss_mb() -> float:
    """
    Get current RSS (Resident Set Size) memory usage in MB.

    Uses /proc/self/statm on Linux for accurate measurement.
    Falls back to psutil if available, otherwise returns 0.

    Returns:
        Current RSS in MB, or 0 if measurement fails
    """
    try:
        # Linux: Read from /proc/self/statm (most accurate, no dependencies)
        # Format: size resident shared text lib data dt
        # resident is in pages, multiply by page size
        with open('/proc/self/statm', 'r') as f:
            parts = f.read().split()
            if len(parts) >= 2:
                resident_pages = int(parts[1])
                page_size = os.sysconf('SC_PAGE_SIZE')
                return (resident_pages * page_size) / (1024 * 1024)
    except (FileNotFoundError, OSError, ValueError):
        pass

    # Fallback: Try psutil if available
    try:
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / (1024 * 1024)
    except ImportError:
        pass
    except Exception:
        pass

    return 0.0


def log_resource_peak(
    node_name: str,
    trace_id: str,
    operation: str = "langgraph_orchestrator"
) -> float:
    """
    Log [RESOURCE_PEAK] event after a node completes.

    Args:
        node_name: Name of the completed node
        trace_id: Trace ID for correlation
        operation: Operation name for log filtering

    Returns:
        Current RSS in MB
    """
    rss_mb = get_current_rss_mb()

    logger.info(
        f"[RESOURCE_PEAK] Node {node_name} completed",
        extra={
            "operation": operation,
            "trace_id": trace_id,
            "event_code": "RESOURCE_PEAK",
            "node_name": node_name,
            "current_rss_mb": round(rss_mb, 2)
        }
    )

    return rss_mb


def log_diff_fetch_bytes(
    trace_id: str,
    diff_bytes: int,
    file_count: int,
    truncated: bool,
    pr_number: Optional[int] = None,
    operation: str = "github_api"
) -> None:
    """
    Log [DIFF_FETCH_BYTES] event after diff fetch.

    Args:
        trace_id: Trace ID for correlation
        diff_bytes: Size of diff content in bytes
        file_count: Number of files in diff
        truncated: Whether diff was truncated
        pr_number: PR number (optional)
        operation: Operation name for log filtering
    """
    rss_mb = get_current_rss_mb()

    logger.info(
        f"[DIFF_FETCH_BYTES] Diff fetched: {diff_bytes} bytes, {file_count} files",
        extra={
            "operation": operation,
            "trace_id": trace_id,
            "event_code": "DIFF_FETCH_BYTES",
            "diff_bytes": diff_bytes,
            "file_count": file_count,
            "truncated": truncated,
            "pr_number": pr_number,
            "current_rss_mb": round(rss_mb, 2)
        }
    )


def log_prompt_build_bytes(
    trace_id: str,
    prompt_bytes: int,
    system_prompt_bytes: int,
    user_prompt_bytes: int,
    diff_included: bool,
    operation: str = "llm_reviewer"
) -> None:
    """
    Log [PROMPT_BUILD_BYTES] event before LLM call.

    Args:
        trace_id: Trace ID for correlation
        prompt_bytes: Total prompt size in bytes
        system_prompt_bytes: System prompt size in bytes
        user_prompt_bytes: User prompt size in bytes
        diff_included: Whether diff was included in prompt
        operation: Operation name for log filtering
    """
    rss_mb = get_current_rss_mb()

    logger.info(
        f"[PROMPT_BUILD_BYTES] Prompt built: {prompt_bytes} bytes total",
        extra={
            "operation": operation,
            "trace_id": trace_id,
            "event_code": "PROMPT_BUILD_BYTES",
            "prompt_bytes": prompt_bytes,
            "system_prompt_bytes": system_prompt_bytes,
            "user_prompt_bytes": user_prompt_bytes,
            "diff_included": diff_included,
            "current_rss_mb": round(rss_mb, 2)
        }
    )


def log_llm_response_bytes(
    trace_id: str,
    response_bytes: int,
    token_count: Optional[int] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    operation: str = "llm_reviewer"
) -> None:
    """
    Log [LLM_RESPONSE_BYTES] event after LLM call.

    Args:
        trace_id: Trace ID for correlation
        response_bytes: Size of LLM response in bytes
        token_count: Number of tokens in response (if available)
        provider: LLM provider name
        model: LLM model name
        operation: Operation name for log filtering
    """
    rss_mb = get_current_rss_mb()

    logger.info(
        f"[LLM_RESPONSE_BYTES] Response received: {response_bytes} bytes",
        extra={
            "operation": operation,
            "trace_id": trace_id,
            "event_code": "LLM_RESPONSE_BYTES",
            "response_bytes": response_bytes,
            "token_count": token_count,
            "provider": provider,
            "model": model,
            "current_rss_mb": round(rss_mb, 2)
        }
    )


def log_checkpoint_put_bytes(
    trace_id: str,
    payload_bytes: int,
    checkpoint_count: int,
    thread_id: Optional[str] = None,
    is_degraded: bool = False,
    operation: str = "langgraph_orchestrator"
) -> None:
    """
    Log [CHECKPOINT_PUT_BYTES] event during checkpoint put.

    Args:
        trace_id: Trace ID for correlation
        payload_bytes: Size of checkpoint payload in bytes
        checkpoint_count: Current number of checkpoints
        thread_id: Thread ID for the checkpoint
        is_degraded: Whether using degraded (MemorySaver) mode
        operation: Operation name for log filtering
    """
    rss_mb = get_current_rss_mb()

    logger.info(
        f"[CHECKPOINT_PUT_BYTES] Checkpoint put: {payload_bytes} bytes",
        extra={
            "operation": operation,
            "trace_id": trace_id,
            "event_code": "CHECKPOINT_PUT_BYTES",
            "payload_bytes": payload_bytes,
            "checkpoint_count": checkpoint_count,
            "thread_id": thread_id,
            "is_degraded": is_degraded,
            "current_rss_mb": round(rss_mb, 2)
        }
    )
