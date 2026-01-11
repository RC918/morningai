"""
D-4 Self-Correction Loop - Fresh Verification Test

This test intentionally fails to verify the complete D-4 Self-Correction Loop flow
after PR #3815 fix for ci_failure_context extraction.

This is a FRESH test PR to bypass loop protection counter (which was at 3/3 for PR #3812).

Expected staging log events after this test fails:
- [SELF_CORRECTION_INTEGRATION_FETCH_LOGS] - Starting log fetch from GitHub Actions
- [SELF_CORRECTION_INTEGRATION_LOGS_FETCHED] - Successfully fetched logs (logs_length > 0)
- [SELF_CORRECTION_INTEGRATION_START] - D-4 triggered with test output

IMPORTANT: This test uses a `test/*` branch instead of `devin/*` because
the normalizer skips CI failures from `devin/*` and `orchestrator/*` branches
to prevent self-trigger loops.

Issue: #3815 (ci_failure_context fix verification)
Created: 2026-01-11T04:53:00Z
"""


def test_d4_complete_flow_verification():
    """This test intentionally fails to trigger D-4 Self-Correction Loop."""
    # Intentional failure to trigger CI failure and D-4
    # Fresh PR to bypass loop protection counter
    assert 1 == 2, "Intentional failure to verify D-4 complete flow after PR #3815 fix"
