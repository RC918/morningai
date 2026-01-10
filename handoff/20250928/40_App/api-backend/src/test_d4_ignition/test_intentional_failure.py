"""D-4 Self-Correction Loop Ignition Test.

This test intentionally fails to trigger the D-4 Self-Correction Loop.
The test failure should cause the following telemetry events:
- [SELF_CORRECTION_INTEGRATION_START]
- [SELF_CORRECTION_ATTEMPT]
- [SELF_CORRECTION_INTEGRATION_SUCCESS] or [SELF_CORRECTION_INTEGRATION_ESCALATE]

Issue #2764: D-4 Self-Correction Loop
"""


def test_intentional_failure_for_d4_ignition():
    """This test intentionally fails to trigger D-4 Self-Correction Loop."""
    # Intentional failure: expected value is wrong
    result = 1 + 1
    assert result == 3, "Intentional failure: 1 + 1 should equal 2, not 3"
