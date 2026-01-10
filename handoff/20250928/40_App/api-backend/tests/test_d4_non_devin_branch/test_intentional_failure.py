"""
D-4 Self-Correction Loop Verification Test (Non-Devin Branch)

This test intentionally fails to verify that the D-4 Self-Correction Loop
is triggered correctly after the race condition fix in PR #3793.

IMPORTANT: This test uses a `test/*` branch instead of `devin/*` because
the normalizer skips CI failures from `devin/*` and `orchestrator/*` branches
to prevent self-trigger loops. See normalizer.py _handle_ci_check_completed():

    if branch_lower.startswith("orchestrator/") or branch_lower.startswith("devin/"):
        return False  # Skip to prevent self-trigger loops

Expected behavior after fix:
1. PR_OPENED webhook should NOT exhaust loop protection counter
2. CI_FAILURE webhook should trigger D-4 with [SELF_CORRECTION_INTEGRATION_START]
3. Loop protection counter should only increment AFTER actual fix attempt

Issue: #3792, #3793
"""


def test_d4_verification_intentional_failure():
    """This test intentionally fails to trigger D-4 Self-Correction Loop."""
    # Intentional failure to trigger CI failure and D-4
    assert 1 == 2, "Intentional failure to verify D-4 fix from PR #3793 (non-devin branch)"
