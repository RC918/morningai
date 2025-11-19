# Agent Evaluation Result Schema

This document describes the structure of evaluation results produced by the agent evaluation framework.

## Result Object Structure

Each evaluation result contains the following fields:

### Core Fields

| Field | Type | Description |
|-------|------|-------------|
| `task_id` | string | Unique identifier for the task (e.g., "task-001") |
| `task_type` | string | Type of task: "bug_fix", "feature", "refactor", "test" |
| `description` | string | Human-readable task description |
| `difficulty` | string | Task difficulty: "easy", "medium", "hard" |
| `estimated_time_minutes` | integer | Estimated time to complete (minutes) |

### Execution Metadata

| Field | Type | Description |
|-------|------|-------------|
| `start_time` | string (ISO 8601) | Task start timestamp |
| `end_time` | string (ISO 8601) | Task completion timestamp |
| `duration_seconds` | float | Actual execution time in seconds |
| `status` | string | Execution status: "completed", "failed", "error" |
| `orchestrator_mode` | string | Execution mode: "real" or "mock" |

### PR and CI Status

| Field | Type | Description |
|-------|------|-------------|
| `pr_created` | boolean | Whether a PR was created |
| `pr_url` | string \| null | GitHub PR URL if created |
| `ci_passed` | boolean | Whether all CI checks passed |
| `ci_checks_total` | integer | Total number of CI checks |
| `ci_checks_passed` | integer | Number of passed CI checks |
| `ci_checks_failed` | integer | Number of failed CI checks |
| `ci_checks_pending` | integer | Number of pending CI checks |
| `ci_check_details` | array | Detailed CI check information (see below) |

### CI Check Detail Object

Each entry in `ci_check_details` contains:

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Check name (e.g., "build", "test", "lint") |
| `status` | string | Check status: "completed", "pending", "queued" |
| `conclusion` | string | Check conclusion: "success", "failure", "cancelled", "timed_out" |
| `type` | string | Check type: "check_run" (GitHub Actions) or "status" (legacy CI) |

### Correctness Evaluation

| Field | Type | Description |
|-------|------|-------------|
| `correctness_score` | float | Overall correctness score (0.0 - 1.0) |
| `correctness_criteria_met` | array | List of met criteria (e.g., ["pr_created", "ci_passed"]) |

### Error Tracking

| Field | Type | Description |
|-------|------|-------------|
| `errors` | array | List of error messages encountered |
| `notes` | string | Additional notes or warnings |

## Future Fields (Phase 1+)

The following fields will be added in future phases:

### Planner Accuracy (Phase 1)

| Field | Type | Description |
|-------|------|-------------|
| `expected_plan_steps` | array | Expected plan steps from dataset |
| `actual_plan_steps` | array | Actual plan steps executed |
| `planner_accuracy` | float | Accuracy score (0.0 - 1.0) |

### Self-Healing (Phase 1)

| Field | Type | Description |
|-------|------|-------------|
| `retry_attempts` | integer | Number of retry attempts |
| `self_healed` | boolean | Whether the agent self-healed from errors |
| `self_healing_rate` | float | Self-healing success rate |

### Multi-Agent Coordination (Phase 3)

| Field | Type | Description |
|-------|------|-------------|
| `agent_handoffs` | integer | Number of agent handoffs |
| `coordination_latency_ms` | float | Average coordination latency |

### Cost Tracking (Phase 5-6)

| Field | Type | Description |
|-------|------|-------------|
| `tokens_used` | integer | Total tokens consumed |
| `api_cost_usd` | float | Estimated API cost in USD |
| `cost_per_task` | float | Cost per task metric |

## Example Result

```json
{
  "task_id": "task-001",
  "task_type": "bug_fix",
  "description": "Fix authentication timeout issue",
  "difficulty": "easy",
  "estimated_time_minutes": 20,
  "start_time": "2025-11-17T18:11:09.540404",
  "end_time": "2025-11-17T18:11:11.540876",
  "duration_seconds": 2.0,
  "status": "completed",
  "orchestrator_mode": "mock",
  "pr_created": true,
  "pr_url": "https://github.com/RC918/morningai/pull/1234",
  "ci_passed": true,
  "ci_checks_total": 3,
  "ci_checks_passed": 3,
  "ci_checks_failed": 0,
  "ci_checks_pending": 0,
  "ci_check_details": [
    {
      "name": "build",
      "status": "completed",
      "conclusion": "success",
      "type": "check_run"
    },
    {
      "name": "test",
      "status": "completed",
      "conclusion": "success",
      "type": "check_run"
    },
    {
      "name": "lint",
      "status": "completed",
      "conclusion": "success",
      "type": "check_run"
    }
  ],
  "correctness_score": 0.9,
  "correctness_criteria_met": ["pr_created", "ci_passed"],
  "errors": [],
  "notes": "Task executed via mock orchestrator"
}
```

## Output File Structure

The complete output file contains:

```json
{
  "evaluation_date": "2025-11-17T18:11:11.541100",
  "dataset": "dataset.jsonl",
  "total_tasks": 10,
  "results": [
    // Array of result objects as described above
  ]
}
```
