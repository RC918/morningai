# Phase B-B Context Diagnosis Test

This PR is created to trigger the webhook and collect diagnostic logs for the `pr_number=0` issue.

## Purpose

After merging PR #2732, the orchestrator now logs detailed context information:
- `resource_type`: Expected to be `pull_request`
- `context_keys`: All keys in the context dict
- `payload_keys`: Keys in the payload dict
- `payload_len`: Size of the payload
- `raw_pr_number`: Raw value before extraction
- `raw_pr_url`: Raw value before extraction

## Expected Outcome

Search Render logs for `resource_type=` to diagnose why `pr_number=0` and `pr_url=''` appear in staging logs.

## Cleanup

This file should be deleted after verification is complete.
