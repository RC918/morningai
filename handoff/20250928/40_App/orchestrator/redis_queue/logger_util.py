#!/usr/bin/env python3
"""
Structured logging utility for worker operations
"""
import json
import time
from datetime import datetime
from typing import Optional

def log_structured(
    level: str,
    message: str,
    operation: str,
    trace_id: Optional[str] = None,
    task_id: Optional[str] = None,
    elapsed_ms: Optional[float] = None,
    **extra
):
    """
    Log structured JSON message with consistent format
    
    Args:
        level: Log level (INFO, ERROR, WARNING)
        message: Log message
        operation: Operation name (enqueue, process, complete, fail, retry)
        trace_id: Optional trace ID
        task_id: Optional task ID
        elapsed_ms: Optional elapsed time in milliseconds
        **extra: Additional fields to include
    """
    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "level": level,
        "message": message,
        "operation": operation,
    }
    
    if trace_id:
        log_entry["trace_id"] = trace_id
    if task_id:
        log_entry["task_id"] = task_id
    if elapsed_ms is not None:
        log_entry["elapsed_ms"] = round(elapsed_ms, 2)
    
    log_entry.update(extra)
    
    print(json.dumps(log_entry))
