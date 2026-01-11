"""
D-4 Self-Correction Loop - Azure Blob Storage Auth Verification Test

This test intentionally fails to verify that PR #3805 and PR #3807 fixes are working:
- PR #3805: Fixed HTTP 403 error by skipping auth header for Azure Blob Storage URLs
- PR #3807: Fixed CI signature deduplication by adding commit_sha to signature

Expected staging log events after this test fails:
- [SELF_CORRECTION_INTEGRATION_FETCH_LOGS] - Starting log fetch from GitHub Actions
- [SELF_CORRECTION_INTEGRATION_LOGS_FETCHED] - Successfully fetched logs (logs_length > 0)
- [SELF_CORRECTION_INTEGRATION_START] - D-4 triggered with test output

IMPORTANT: This test uses a `test/*` branch instead of `devin/*` because
the normalizer skips CI failures from `devin/*` and `orchestrator/*` branches
to prevent self-trigger loops.

Issue: #3805, #3807
Created: 2026-01-11T03:20:00Z
"""


def test_d4_azure_blob_auth_verification():
    """This test intentionally fails to trigger D-4 Self-Correction Loop."""
    # Intentional failure to trigger CI failure and D-4
    # This is a fresh test file to bypass CI signature deduplication
    assert 1 == 2, "Intentional failure to verify PR #3805 Azure Blob Storage auth fix"
