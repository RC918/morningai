"""
Probe 0: CI Validation File for AutoFixer Testing

This file contains an intentional lint error to validate the
CI failure -> AutoFixer -> SimpleCoder pipeline.

DO NOT MERGE this file with the error - it should be fixed by AutoFixer.

Expected:
- CI fails with F821 (undefined name)
- AutoFixer detects the failure and triggers SimpleCoder
- SimpleCoder fixes the typo and commits

Log keywords to search in Render logs:
- [Fixer]
- [CODER_PATCH]
"""


def validate_ci_pipeline(value: int) -> int:
    """Validate the CI pipeline is working.

    Args:
        value: Input value to process.

    Returns:
        Processed value.
    """
    result = value * 2
    return reuslt  # Intentional typo: should be 'result'
# Trigger CI re-run after FIXER_PERCENT=100 update
