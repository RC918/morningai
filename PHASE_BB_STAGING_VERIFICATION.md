# Phase B-B Staging Verification

This PR is created to verify that the Phase B-B PR context passing fix works correctly in staging.

## Expected Behavior

After PR #2721 is deployed to staging:

1. Webhook receives `pull_request.opened` event
2. EventNormalizer extracts `resource_id` (PR number) and `resource_type` ("pull_request")
3. Worker passes `task.context` to `run_orchestrator`
4. Orchestrator logs show `pr_number > 0` (not 0)
5. `reviewer_node` executes (not skipped with "No PR to review")

## Verification Checklist

- [ ] Render logs show `Starting LangGraph orchestrator` with `pr_number=<this PR number>`
- [ ] `reviewer_node` executes successfully
- [ ] Telemetry fields (`pr_number`, `pr_url`, `trace_id`) are logged

## Test Date

$(date -u +"%Y-%m-%d %H:%M:%S UTC")
