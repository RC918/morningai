"""
D-4 Self-Correction Loop Final Verification Test

This test intentionally fails to verify that D-4 Self-Correction Loop
is working correctly after PR #3817 fix (Loop Protection counter only
increments for CI failure events, not PR_OPENED events).

Expected behavior:
1. This test fails in CI
2. D-4 detects the CI failure
3. D-4 attempts to fix the test automatically
4. Loop Protection counter should only increment for CI failure events

Branch: test/d4-final-verify-* (non-devin/* branch to trigger D-4)
"""


def test_intentional_failure_for_d4_verification():
    """
    This test intentionally fails to trigger D-4 Self-Correction Loop.
    
    D-4 should detect this failure and attempt to fix it by changing
    the assertion from `assert False` to `assert True`.
    """
    assert False, "Intentional failure to verify D-4 Self-Correction Loop after PR #3820 orchestrator diagnostic logs"
