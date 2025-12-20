"""
Tests for is_internal_repo_allowed() helper function

Phase B-B: Internal Repo Dogfooding
Issue: #2763 - Enable internal repo dogfooding in Staging

This tests the preconditions for allowing internal repos to be reviewed:
1. settings object is available
2. allow_internal_repos_in_staging is True
3. is_staging environment is True
4. repo is in internal_repos_whitelist
"""

from unittest.mock import MagicMock, patch

from .. import normalizer as normalizer_module
from ..normalizer import is_internal_repo_allowed


class MockSettings:
    """Mock settings object for testing"""

    def __init__(
        self,
        is_staging: bool = False,
        allow_internal: bool = False,
        whitelist: str = "",
    ):
        self.is_staging = is_staging
        self.allow_internal_repos_in_staging = allow_internal
        self.internal_repos_whitelist = whitelist


class TestIsInternalRepoAllowed:
    """Tests for is_internal_repo_allowed() function"""

    def test_returns_false_when_settings_is_none(self):
        """Test that function returns False when settings is None"""
        with patch.object(normalizer_module, "settings", None):
            assert is_internal_repo_allowed("RC918/morningai") is False

    def test_returns_false_when_allow_internal_is_false(self):
        """Test that function returns False when allow_internal_repos_in_staging is False"""
        mock_settings = MockSettings(
            is_staging=True,
            allow_internal=False,
            whitelist="RC918/morningai",
        )
        with patch.object(normalizer_module, "settings", mock_settings):
            assert is_internal_repo_allowed("RC918/morningai") is False

    def test_returns_false_when_not_staging(self):
        """Test that function returns False when not in staging environment"""
        mock_settings = MockSettings(
            is_staging=False,
            allow_internal=True,
            whitelist="RC918/morningai",
        )
        with patch.object(normalizer_module, "settings", mock_settings):
            assert is_internal_repo_allowed("RC918/morningai") is False

    def test_returns_false_when_whitelist_empty(self):
        """Test that function returns False when whitelist is empty"""
        mock_settings = MockSettings(
            is_staging=True,
            allow_internal=True,
            whitelist="",
        )
        with patch.object(normalizer_module, "settings", mock_settings):
            assert is_internal_repo_allowed("RC918/morningai") is False

    def test_returns_false_when_repo_not_in_whitelist(self):
        """Test that function returns False when repo is not in whitelist"""
        mock_settings = MockSettings(
            is_staging=True,
            allow_internal=True,
            whitelist="other/repo",
        )
        with patch.object(normalizer_module, "settings", mock_settings):
            assert is_internal_repo_allowed("RC918/morningai") is False

    def test_returns_true_when_all_conditions_met(self):
        """Test that function returns True when all preconditions are met"""
        mock_settings = MockSettings(
            is_staging=True,
            allow_internal=True,
            whitelist="RC918/morningai",
        )
        with patch.object(normalizer_module, "settings", mock_settings):
            assert is_internal_repo_allowed("RC918/morningai") is True

    def test_whitelist_with_multiple_repos(self):
        """Test that whitelist parsing works with multiple repos"""
        mock_settings = MockSettings(
            is_staging=True,
            allow_internal=True,
            whitelist="other/repo, RC918/morningai, another/repo",
        )
        with patch.object(normalizer_module, "settings", mock_settings):
            assert is_internal_repo_allowed("RC918/morningai") is True
            assert is_internal_repo_allowed("other/repo") is True
            assert is_internal_repo_allowed("another/repo") is True
            assert is_internal_repo_allowed("not/in/list") is False

    def test_whitelist_handles_whitespace(self):
        """Test that whitelist parsing handles extra whitespace"""
        mock_settings = MockSettings(
            is_staging=True,
            allow_internal=True,
            whitelist="  RC918/morningai  ,  other/repo  ",
        )
        with patch.object(normalizer_module, "settings", mock_settings):
            assert is_internal_repo_allowed("RC918/morningai") is True
            assert is_internal_repo_allowed("other/repo") is True

    def test_uses_getattr_for_missing_attributes(self):
        """Test that function uses getattr safely for missing attributes"""
        # Create a minimal mock that only has is_staging
        mock_settings = MagicMock()
        mock_settings.is_staging = True
        # Simulate missing attributes by having getattr return defaults
        del mock_settings.allow_internal_repos_in_staging
        del mock_settings.internal_repos_whitelist

        with patch.object(normalizer_module, "settings", mock_settings):
            # Should return False because allow_internal defaults to False
            result = is_internal_repo_allowed("RC918/morningai")
            assert result is False
