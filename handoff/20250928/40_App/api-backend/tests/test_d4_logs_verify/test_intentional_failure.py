"""
D-4 Self-Correction Loop CI Logs Verification Test

This test intentionally fails to verify that PR #3803 and PR #3805 fixes are working:
- PR #3803: D-4 should now fetch CI logs from GitHub Actions when error_summary is empty
- PR #3805: Fixed HTTP 403 error by skipping auth header for Azure Blob Storage URLs
- Expected staging log events:
  - [SELF_CORRECTION_INTEGRATION_FETCH_LOGS] - Starting log fetch
  - [SELF_CORRECTION_INTEGRATION_LOGS_FETCHED] - Successfully fetched logs (logs_length > 0)
  - [SELF_CORRECTION_INTEGRATION_START] - D-4 triggered with test output

IMPORTANT: This test uses a `test/*` branch instead of `devin/*` because
the normalizer skips CI failures from `devin/*` and `orchestrator/*` branches
to prevent self-trigger loops.

Issue: #3803, #3805
Re-trigger: 2026-01-10T17:57:00Z
"""


def test_d4_logs_verification_intentional_failure():
    """This test intentionally fails to trigger D-4 Self-Correction Loop."""
    # Intentional failure to trigger CI failure and D-4
    # Using unique timestamp to bypass CI signature deduplication
    import time
    unique_id = int(time.time())
    assert 1 == 2, f"Intentional failure #{unique_id} to verify PR #3805 Azure Blob auth fix"
