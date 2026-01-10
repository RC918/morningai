"""
D-4 Self-Correction Loop CI Logs Verification Test

This test intentionally fails to verify that PR #3803 fix is working:
- D-4 should now fetch CI logs from GitHub Actions when error_summary is empty
- Expected staging log events:
  - [SELF_CORRECTION_INTEGRATION_FETCH_LOGS] - Starting log fetch
  - [SELF_CORRECTION_INTEGRATION_LOGS_FETCHED] - Successfully fetched logs
  - [SELF_CORRECTION_INTEGRATION_START] - D-4 triggered with test output

IMPORTANT: This test uses a `test/*` branch instead of `devin/*` because
the normalizer skips CI failures from `devin/*` and `orchestrator/*` branches
to prevent self-trigger loops.

Issue: #3803
"""


def test_d4_logs_verification_intentional_failure():
    """This test intentionally fails to trigger D-4 Self-Correction Loop."""
    # Intentional failure to trigger CI failure and D-4
    assert 1 == 2, "Intentional failure to verify D-4 CI logs fetch from PR #3803"
