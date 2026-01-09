"""
Resource Telemetry Module for P1 瘦身計畫 (Issue #3197)

Provides per-workflow resource measurement and telemetry events:
- [RESOURCE_PEAK]: RSS measurement after each major node
- [DIFF_FETCH_BYTES]: Diff fetch payload size
- [PROMPT_BUILD_BYTES]: LLM prompt size before call
- [CHECKPOINT_PUT_BYTES]: Checkpoint payload size
- [LLM_RESPONSE_BYTES]: LLM response size
- [CONTEXT_FILE_SCAN]: Files scanned during context extraction
- [CONTEXT_FILE_SELECT]: Files selected for context (with scores)
- [CONTEXT_TOKEN_BUDGET]: Token budget usage during context building
- [GENERAL_CODER_MULTI_FILE_HITL_ESCALATION]: HITL escalation when 6+ files detected

All events include trace_id for correlation.

Controllability (Issue #3205):
- RESOURCE_TELEMETRY_ENABLED: Set to "false" to disable all telemetry logging.
  Default is "true" (enabled). This provides a kill-switch for production
  if log volume becomes problematic.
"""

import logging
import os
import time
from typing import Optional

logger = logging.getLogger(__name__)


def _is_telemetry_enabled() -> bool:
    """
    Check if resource telemetry is enabled via environment variable.

    Accepts common falsey values: "false", "0", "no", "off", "" (empty string).
    Default is enabled (true).

    Returns:
        True if telemetry is enabled (default), False if explicitly disabled.
    """
    value = os.environ.get("RESOURCE_TELEMETRY_ENABLED", "true").strip().lower()
    return value not in ("false", "0", "no", "off", "")


def _get_timestamp_ms() -> int:
    """Get current timestamp in milliseconds (UTC) for cross-service correlation."""
    return time.time_ns() // 1_000_000


_rss_warning_logged = False


def get_current_rss_mb() -> tuple[float, bool]:
    """
    Get current RSS (Resident Set Size) memory usage in MB.

    Uses /proc/self/statm on Linux for accurate measurement.
    Falls back to psutil if available, otherwise returns 0.

    Returns:
        Tuple of (RSS in MB, success flag). Returns (0.0, False) if measurement fails.
    """
    global _rss_warning_logged

    try:
        # Linux: Read from /proc/self/statm (most accurate, no dependencies)
        # Format: size resident shared text lib data dt
        # resident is in pages, multiply by page size
        with open('/proc/self/statm', 'r') as f:
            parts = f.read().split()
            if len(parts) >= 2:
                resident_pages = int(parts[1])
                page_size = os.sysconf('SC_PAGE_SIZE')
                return ((resident_pages * page_size) / (1024 * 1024), True)
    except (FileNotFoundError, OSError, ValueError):
        pass

    # Fallback: Try psutil if available
    try:
        import psutil
        process = psutil.Process()
        return (process.memory_info().rss / (1024 * 1024), True)
    except ImportError:
        pass
    except Exception:
        pass

    # Log warning once if RSS measurement is unavailable
    if not _rss_warning_logged:
        logger.warning(
            "[RESOURCE_TELEMETRY] RSS measurement unavailable on this platform",
            extra={"operation": "resource_telemetry", "event_code": "RSS_UNAVAILABLE"}
        )
        _rss_warning_logged = True

    return (0.0, False)


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
        Current RSS in MB (0.0 if telemetry disabled)
    """
    if not _is_telemetry_enabled():
        return 0.0

    rss_mb, rss_available = get_current_rss_mb()

    logger.info(
        f"[RESOURCE_PEAK] Node {node_name} completed",
        extra={
            "operation": operation,
            "trace_id": trace_id,
            "event_code": "RESOURCE_PEAK",
            "node_name": node_name,
            "current_rss_mb": round(rss_mb, 2),
            "rss_available": rss_available,
            "timestamp_ms": _get_timestamp_ms()
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
    if not _is_telemetry_enabled():
        return

    rss_mb, rss_available = get_current_rss_mb()

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
            "current_rss_mb": round(rss_mb, 2),
            "rss_available": rss_available,
            "timestamp_ms": _get_timestamp_ms()
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
    if not _is_telemetry_enabled():
        return

    rss_mb, rss_available = get_current_rss_mb()

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
            "current_rss_mb": round(rss_mb, 2),
            "rss_available": rss_available,
            "timestamp_ms": _get_timestamp_ms()
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
    if not _is_telemetry_enabled():
        return

    rss_mb, rss_available = get_current_rss_mb()

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
            "current_rss_mb": round(rss_mb, 2),
            "rss_available": rss_available,
            "timestamp_ms": _get_timestamp_ms()
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

    Note: payload_bytes uses sys.getsizeof() which only measures shallow object
    size. The actual memory footprint of nested structures may be larger.
    The size_method field indicates this is an estimate.

    Args:
        trace_id: Trace ID for correlation
        payload_bytes: Shallow size estimate of checkpoint payload in bytes
        checkpoint_count: Current number of checkpoints
        thread_id: Thread ID for the checkpoint
        is_degraded: Whether using degraded (MemorySaver) mode
        operation: Operation name for log filtering
    """
    if not _is_telemetry_enabled():
        return

    rss_mb, rss_available = get_current_rss_mb()

    logger.info(
        f"[CHECKPOINT_PUT_BYTES] Checkpoint put: {payload_bytes} bytes (shallow)",
        extra={
            "operation": operation,
            "trace_id": trace_id,
            "event_code": "CHECKPOINT_PUT_BYTES",
            "payload_shallow_bytes": payload_bytes,
            "size_method": "shallow_getsizeof",
            "checkpoint_count": checkpoint_count,
            "thread_id": thread_id,
            "is_degraded": is_degraded,
            "current_rss_mb": round(rss_mb, 2),
            "rss_available": rss_available,
            "timestamp_ms": _get_timestamp_ms()
        }
    )


def log_context_file_scan(
    goal: str,
    files_scanned: int,
    search_dirs: list[str],
    max_scan: int,
    trace_id: Optional[str] = None,
    operation: str = "context_manager"
) -> None:
    """
    Log [CONTEXT_FILE_SCAN] event during context extraction file scanning.

    Args:
        goal: User's goal (truncated for logging)
        files_scanned: Number of files scanned
        search_dirs: Directories searched
        max_scan: Maximum files to scan limit
        trace_id: Trace ID for correlation (optional)
        operation: Operation name for log filtering
    """
    if not _is_telemetry_enabled():
        return

    rss_mb, rss_available = get_current_rss_mb()

    logger.info(
        f"[CONTEXT_FILE_SCAN] Scanned {files_scanned} files for context",
        extra={
            "operation": operation,
            "trace_id": trace_id,
            "event_code": "CONTEXT_FILE_SCAN",
            "goal_preview": goal[:100] if goal else "",
            "files_scanned": files_scanned,
            "search_dirs": search_dirs,
            "max_scan_limit": max_scan,
            "current_rss_mb": round(rss_mb, 2),
            "rss_available": rss_available,
            "timestamp_ms": _get_timestamp_ms()
        }
    )


def log_context_file_select(
    selected_files: list[tuple[str, float]],
    max_files: int,
    trace_id: Optional[str] = None,
    operation: str = "context_manager"
) -> None:
    """
    Log [CONTEXT_FILE_SELECT] event when files are selected for context.

    Args:
        selected_files: List of (file_path, score) tuples
        max_files: Maximum files limit
        trace_id: Trace ID for correlation (optional)
        operation: Operation name for log filtering
    """
    if not _is_telemetry_enabled():
        return

    rss_mb, rss_available = get_current_rss_mb()

    file_details = [
        {"path": path, "score": round(score, 4)}
        for path, score in selected_files
    ]

    logger.info(
        f"[CONTEXT_FILE_SELECT] Selected {len(selected_files)} files for context",
        extra={
            "operation": operation,
            "trace_id": trace_id,
            "event_code": "CONTEXT_FILE_SELECT",
            "selected_count": len(selected_files),
            "max_files_limit": max_files,
            "selected_files": file_details,
            "current_rss_mb": round(rss_mb, 2),
            "rss_available": rss_available,
            "timestamp_ms": _get_timestamp_ms()
        }
    )


def log_context_token_budget(
    files_included: int,
    files_excluded: int,
    tokens_used: int,
    max_tokens: int,
    budget_exceeded: bool,
    excluded_files: Optional[list[str]] = None,
    trace_id: Optional[str] = None,
    operation: str = "context_manager"
) -> None:
    """
    Log [CONTEXT_TOKEN_BUDGET] event showing token budget usage.

    Args:
        files_included: Number of files included in context
        files_excluded: Number of files excluded due to budget
        tokens_used: Estimated tokens used
        max_tokens: Maximum token budget
        budget_exceeded: Whether budget was exceeded
        excluded_files: List of file paths excluded (optional)
        trace_id: Trace ID for correlation (optional)
        operation: Operation name for log filtering
    """
    if not _is_telemetry_enabled():
        return

    rss_mb, rss_available = get_current_rss_mb()

    log_level = logging.WARNING if budget_exceeded else logging.INFO
    msg = f"[CONTEXT_TOKEN_BUDGET] Used {tokens_used}/{max_tokens} tokens"
    if budget_exceeded:
        msg += f" (exceeded, {files_excluded} files excluded)"

    logger.log(
        log_level,
        msg,
        extra={
            "operation": operation,
            "trace_id": trace_id,
            "event_code": "CONTEXT_TOKEN_BUDGET",
            "files_included": files_included,
            "files_excluded": files_excluded,
            "tokens_used": tokens_used,
            "max_tokens": max_tokens,
            "budget_exceeded": budget_exceeded,
            "excluded_files": excluded_files or [],
            "utilization_pct": round((tokens_used / max_tokens) * 100, 1) if max_tokens > 0 else 0,
            "current_rss_mb": round(rss_mb, 2),
            "rss_available": rss_available,
            "timestamp_ms": _get_timestamp_ms()
        }
    )


def log_multi_file_hitl_escalation(
    file_count: int,
    max_files: int,
    skip_reason: str,
    trace_id: Optional[str] = None,
    pr_number: Optional[int] = None,
    operation: str = "langgraph_orchestrator"
) -> None:
    """
    Log [GENERAL_CODER_MULTI_FILE_HITL_ESCALATION] event when 6+ files trigger HITL.

    This event is logged when GeneralCoder skips due to too many files (> MAX_FILES_PER_OPERATION)
    and HITL escalation is triggered to request human review instead of silently falling back
    to SimpleCoder/AutoFixer.

    Args:
        file_count: Number of files that triggered the escalation
        max_files: Maximum files limit (typically 5)
        skip_reason: Original skip reason from GeneralCoder
        trace_id: Trace ID for correlation (optional)
        pr_number: PR number being processed (optional)
        operation: Operation name for log filtering
    """
    if not _is_telemetry_enabled():
        return

    rss_mb, rss_available = get_current_rss_mb()

    logger.warning(
        f"[GENERAL_CODER_MULTI_FILE_HITL_ESCALATION] "
        f"HITL escalation triggered: {file_count} files > {max_files} limit",
        extra={
            "operation": operation,
            "trace_id": trace_id,
            "event_code": "GENERAL_CODER_MULTI_FILE_HITL_ESCALATION",
            "file_count": file_count,
            "max_files_limit": max_files,
            "skip_reason": skip_reason,
            "pr_number": pr_number,
            "escalation_type": "multi_file_limit_exceeded",
            "current_rss_mb": round(rss_mb, 2),
            "rss_available": rss_available,
            "timestamp_ms": _get_timestamp_ms()
        }
    )
