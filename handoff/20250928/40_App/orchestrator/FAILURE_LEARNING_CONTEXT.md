# Planner Failure Learning Context

This document describes the Failure Learning system that enables the Planner to learn from past failures and improve its planning decisions.

## Overview

The Failure Learning system implements a "post-mortem" flow for failed workflows. When a workflow fails, the Observer Node captures the failure context, generates a summary, and stores the error-fix pair to pgvector for future learning. This enables the Planner to query past failures and learn from previous mistakes.

## Architecture

The system consists of the following components:

1. **Observer Node** (`observer_node.py`): Captures failure context and stores error-fix pairs
2. **Error-Fix Pairs** (`memory/error_fix_pairs.py`): pgvector-based storage for semantic similarity search
3. **Knowledge Graph** (optional): Provides additional context from bug/fix patterns
4. **Orchestrator Metrics** (`orchestrator_metrics.py`): Tracks latency and performance metrics

## Feature Flags

The following feature flags control the Failure Learning system:

| Flag | Description | Default |
|------|-------------|---------|
| `ENABLE_FAILURE_LEARNING_CONTEXT` | Gates the learning context functionality in the Planner | `false` |
| `ENABLE_KNOWLEDGE_GRAPH_LEARNING` | Enables Knowledge Graph pattern queries | `false` |

## Core Functions

### observe_failure()

Records a failure observation to pgvector for future learning.

```python
from observer_node import observe_failure

result = observe_failure(
    trace_id="trace-123",
    error_log="TypeError: Cannot read property 'x' of undefined",
    last_attempt="Attempted to fix by adding null check",
    workflow_context={"goal": "Fix login bug", "task_type": "bug_fix"}
)
```

**Parameters:**
- `trace_id`: Unique identifier for the workflow
- `error_log`: The error message or stack trace
- `last_attempt`: Description of the last fix attempt
- `workflow_context`: Optional context about the workflow

**Returns:**
- `trace_id`: The trace ID
- `error_type`: Categorized error type (e.g., "ci_failure", "timeout", "syntax_error")
- `summary`: Human-readable failure summary
- `saved_to_pgvector`: Whether the failure was saved to pgvector
- `latency_ms`: Operation latency in milliseconds

### query_past_failures()

Queries past failures similar to the given error.

```python
from observer_node import query_past_failures

results = query_past_failures(
    error_text="TypeError: Cannot read property",
    limit=5,
    threshold=0.7,
    error_type_filter="runtime_error",
    trace_id="trace-123"  # Optional, for metrics
)
```

**Parameters:**
- `error_text`: Error text to search for similar failures
- `limit`: Maximum number of results (default: 5)
- `threshold`: Minimum similarity score 0.0-1.0 (default: 0.7)
- `error_type_filter`: Optional filter by error type
- `trace_id`: Optional trace ID for metrics tracking

**Returns:**
List of similar past failures with:
- `id`: Pair ID
- `error_text`: Original error text
- `fix_text`: The fix that resolved the error
- `error_type`: Categorized error type
- `similarity`: Similarity score
- `confidence_score`: Confidence in the fix
- `success_count`: Number of successful applications
- `failure_count`: Number of failed applications

### get_learning_context()

Gets learning context from past failures for the Planner.

```python
from observer_node import get_learning_context

context = get_learning_context(
    goal="Fix the login page bug",
    task_type="bug_fix",
    limit=3,
    trace_id="trace-123"  # Optional, for metrics
)
```

**Parameters:**
- `goal`: The current task goal
- `task_type`: Optional task type for filtering
- `limit`: Maximum number of past failures to include (default: 5)
- `trace_id`: Optional trace ID for metrics tracking

**Returns:**
Formatted context string containing:
- Past Experience (Similar Failures) section
- Knowledge Graph Patterns section (if enabled)

### update_fix_for_failure()

Updates the fix for a previously recorded failure.

```python
from observer_node import update_fix_for_failure

success = update_fix_for_failure(
    trace_id="trace-123",
    fix_text="Added null check before accessing property",
    was_successful=True
)
```

**Parameters:**
- `trace_id`: Trace ID of the original failure
- `fix_text`: The fix that resolved the error
- `was_successful`: Whether the fix was successful

**Returns:**
- `True` if updated successfully, `False` otherwise

## Latency Metrics (Issue #2124)

The system tracks latency metrics for all failure learning operations:

### Metrics Recorded

| Metric | Description |
|--------|-------------|
| `failure_learning.observe` | Failure observation latency |
| `failure_learning.query.similar_errors` | Query latency for similar errors |
| `failure_learning.context_generation` | Learning context generation latency |
| `failure_learning.fix_update` | Fix update latency |
| `failure_learning.error_type.{type}` | Count by error type |
| `failure_learning.pgvector.saved` | Count of saved observations |
| `failure_learning.pgvector.skipped` | Count of skipped observations |
| `failure_learning.query.results.{bucket}` | Query results distribution (empty/few/many) |
| `failure_learning.context.has_past_failures` | Context with past failures |
| `failure_learning.context.has_kg_patterns` | Context with Knowledge Graph patterns |
| `failure_learning.fix_update.success` | Successful fix updates |
| `failure_learning.fix_update.failure` | Failed fix updates |

### Using the Metrics

```python
from orchestrator_metrics import get_orchestrator_metrics

metrics = get_orchestrator_metrics()

# Record failure observation
metrics.record_failure_observation(
    trace_id="trace-123",
    error_type="ci_failure",
    saved_to_pgvector=True,
    latency_ms=150.5
)

# Record failure query
metrics.record_failure_query(
    trace_id="trace-123",
    results_count=3,
    latency_ms=200.0,
    query_type="similar_errors"
)

# Record learning context generation
metrics.record_learning_context_generation(
    trace_id="trace-123",
    has_past_failures=True,
    has_kg_patterns=False,
    latency_ms=250.0
)

# Record fix update
metrics.record_fix_update(
    trace_id="trace-123",
    was_successful=True,
    latency_ms=100.0
)

# Use context manager for automatic latency tracking
with metrics.track_failure_learning_operation("custom_op", "trace-123"):
    # Your operation here
    pass

# Get summary
summary = metrics.get_failure_learning_summary(window_minutes=15)
```

### Summary Output

The `get_failure_learning_summary()` method returns:

```python
{
    "observations": 10,
    "pgvector_saved": 8,
    "pgvector_skipped": 2,
    "save_rate": 80.0,
    "queries": 25,
    "context_generations": 15,
    "fix_updates": 5,
    "fix_success_rate": 80.0,
    "context_with_past_failures": 12,
    "context_with_kg_patterns": 3
}
```

## Error Types

The system categorizes errors into the following types:

| Error Type | Description |
|------------|-------------|
| `ci_failure` | CI/CD pipeline failures |
| `timeout` | Operation timeouts |
| `syntax_error` | Code syntax errors |
| `runtime_error` | Runtime exceptions |
| `type_error` | Type-related errors |
| `import_error` | Module import failures |
| `permission_error` | Permission/access denied |
| `network_error` | Network-related failures |
| `unknown` | Uncategorized errors |

## Integration with Planner

The Planner integrates with the Failure Learning system through the `get_learning_context()` function:

```python
from observer_node import get_learning_context
from common.config.settings import settings

def plan_task(goal: str, task_type: str, trace_id: str):
    context = ""
    
    # Get learning context if feature flag is enabled
    if settings.enable_failure_learning_context:
        context = get_learning_context(
            goal=goal,
            task_type=task_type,
            trace_id=trace_id
        )
    
    # Include context in planner prompt
    prompt = f"""
    Goal: {goal}
    
    {context}
    
    Please create a plan to achieve this goal.
    """
    
    return generate_plan(prompt)
```

## Best Practices

1. **Always provide trace_id**: Include the trace_id parameter for proper metrics tracking and debugging.

2. **Set appropriate thresholds**: Use a similarity threshold of 0.7 or higher to ensure relevant results.

3. **Limit results**: Keep the limit parameter reasonable (3-5) to avoid overwhelming the Planner with too much context.

4. **Update fixes**: Always call `update_fix_for_failure()` when a fix is found to improve future recommendations.

5. **Monitor metrics**: Regularly check the failure learning summary to identify patterns and optimize performance.

## Troubleshooting

### No past failures returned

- Check if pgvector is properly configured
- Verify the similarity threshold is not too high
- Ensure there are recorded failures in the database

### High latency

- Check pgvector index configuration
- Consider reducing the limit parameter
- Monitor the `failure_learning.*` metrics for bottlenecks

### Feature flag not working

- Verify `ENABLE_FAILURE_LEARNING_CONTEXT` is set in environment
- Check settings configuration loading
- Review logs for feature flag evaluation

## Related Issues

- Issue #2124: Latency metrics for failure learning observability
- Issue #2126: Test quality improvement
- Issue #2123: Documentation update (this document)
