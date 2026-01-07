"""
Tests for Auto-Fix Policy Module

Issue #2251: Safety mechanisms for auto-fix executor
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest  # noqa: E402
from dataclasses import dataclass, field  # noqa: E402
from enum import Enum  # noqa: E402
from typing import Any, Dict, List  # noqa: E402
from unittest.mock import MagicMock, patch  # noqa: E402

from utils.auto_fix_policy import (  # noqa: E402
    AutoFixLoopProtection,
    AutoFixPolicy,
    AutoFixRateLimiter,
    CISignatureDeduplication,
    check_auto_fix_safety,
    get_allowed_categories,
    get_allowed_repos,
    is_auto_fix_commit,
    is_auto_fix_actor,
    is_auto_fix_enabled,
)


class CommentCategory(Enum):
    """Comment category enum for testing"""
    BUG_FIX = "bug_fix"
    STYLE = "style"
    REFACTOR = "refactor"
    SECURITY = "security"
    PERFORMANCE = "performance"
    DOCUMENTATION = "documentation"


class RiskLevel(Enum):
    """Risk level enum for testing"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class CommentTriageResult:
    """Mock CommentTriageResult for testing"""
    comment_id: str
    source: str
    category: CommentCategory
    risk_level: RiskLevel
    files_affected: List[str] = field(default_factory=list)
    lines_affected: int = 0
    should_auto_fix: bool = False
    confidence: float = 0.0
    reason: str = ""
    keywords_matched: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@pytest.fixture
def mock_settings():
    """Create mock settings for testing"""
    settings = MagicMock()
    settings.auto_fix_enabled = True
    settings.auto_fix_categories = "style,documentation"
    settings.auto_fix_repos_allowlist = ""
    settings.auto_fix_max_retries = 3
    settings.auto_fix_per_repo_per_hour = 10
    settings.auto_fix_per_pr_per_hour = 3
    settings.auto_fix_global_per_hour = 100
    settings.redis_url = None
    return settings


@pytest.fixture
def mock_triage_result():
    """Create mock triage result for testing"""
    return CommentTriageResult(
        comment_id="test-comment-123",
        source="codex",
        category=CommentCategory.STYLE,
        risk_level=RiskLevel.LOW,
        files_affected=["src/main.py"],
        lines_affected=5,
        should_auto_fix=True,
        confidence=0.85,
        reason="Low-risk style fix with high confidence",
    )


class TestHelperFunctions:
    """Tests for helper functions"""

    def test_get_allowed_categories_default(self, mock_settings):
        """Test getting allowed categories from settings"""
        categories = get_allowed_categories(mock_settings)
        assert categories == {"style", "documentation"}

    def test_get_allowed_categories_empty(self, mock_settings):
        """Test getting allowed categories when empty"""
        mock_settings.auto_fix_categories = ""
        categories = get_allowed_categories(mock_settings)
        assert categories == set()

    def test_get_allowed_categories_with_spaces(self, mock_settings):
        """Test getting allowed categories with extra spaces"""
        mock_settings.auto_fix_categories = " style , documentation , bug_fix "
        categories = get_allowed_categories(mock_settings)
        assert categories == {"style", "documentation", "bug_fix"}

    def test_get_allowed_repos_empty(self, mock_settings):
        """Test getting allowed repos when empty (all repos allowed)"""
        repos = get_allowed_repos(mock_settings)
        assert repos == set()

    def test_get_allowed_repos_with_values(self, mock_settings):
        """Test getting allowed repos with values"""
        mock_settings.auto_fix_repos_allowlist = "owner/repo1,owner/repo2"
        repos = get_allowed_repos(mock_settings)
        assert repos == {"owner/repo1", "owner/repo2"}

    def test_is_auto_fix_enabled_true(self, mock_settings):
        """Test auto-fix enabled check when true"""
        assert is_auto_fix_enabled(mock_settings) is True

    def test_is_auto_fix_enabled_false(self, mock_settings):
        """Test auto-fix enabled check when false"""
        mock_settings.auto_fix_enabled = False
        assert is_auto_fix_enabled(mock_settings) is False

    def test_is_auto_fix_commit_with_marker(self):
        """Test detecting auto-fix commit with marker"""
        assert is_auto_fix_commit("[auto-fix] Fix style issue") is True
        assert is_auto_fix_commit("Auto-fix: Update documentation") is True

    def test_is_auto_fix_commit_without_marker(self):
        """Test detecting regular commit without marker"""
        assert is_auto_fix_commit("Fix style issue") is False
        assert is_auto_fix_commit("Update documentation") is False

    def test_is_auto_fix_commit_empty(self):
        """Test detecting auto-fix commit with empty message"""
        assert is_auto_fix_commit("") is False
        assert is_auto_fix_commit(None) is False

    def test_is_auto_fix_actor_bot(self):
        """Test detecting auto-fix bot actor"""
        assert is_auto_fix_actor("morningai-bot") is True
        assert is_auto_fix_actor("auto-fix-bot") is True
        assert is_auto_fix_actor("github-actions[bot]") is True

    def test_is_auto_fix_actor_human(self):
        """Test detecting human actor"""
        assert is_auto_fix_actor("john-doe") is False
        assert is_auto_fix_actor("developer") is False

    def test_is_auto_fix_actor_empty(self):
        """Test detecting actor with empty name"""
        assert is_auto_fix_actor("") is False
        assert is_auto_fix_actor(None) is False


class TestAutoFixPolicy:
    """Tests for AutoFixPolicy class"""

    def test_policy_allows_valid_request(self, mock_settings, mock_triage_result):
        """Test policy allows valid auto-fix request"""
        policy = AutoFixPolicy(mock_settings)
        result = policy.check(
            triage_result=mock_triage_result,
            repo="owner/repo",
            pr_id="owner/repo#123",
        )
        assert result.allowed is True
        assert result.blocked_by is None

    def test_policy_blocks_when_disabled(self, mock_settings, mock_triage_result):
        """Test policy blocks when auto-fix is disabled"""
        mock_settings.auto_fix_enabled = False
        policy = AutoFixPolicy(mock_settings)
        result = policy.check(
            triage_result=mock_triage_result,
            repo="owner/repo",
            pr_id="owner/repo#123",
        )
        assert result.allowed is False
        assert result.blocked_by == "feature_flag"

    def test_policy_blocks_when_triage_not_recommended(self, mock_settings, mock_triage_result):
        """Test policy blocks when triage does not recommend auto-fix"""
        mock_triage_result.should_auto_fix = False
        policy = AutoFixPolicy(mock_settings)
        result = policy.check(
            triage_result=mock_triage_result,
            repo="owner/repo",
            pr_id="owner/repo#123",
        )
        assert result.allowed is False
        assert result.blocked_by == "triage_result"

    def test_policy_blocks_auto_fix_actor(self, mock_settings, mock_triage_result):
        """Test policy blocks auto-fix bot actor (loop protection)"""
        policy = AutoFixPolicy(mock_settings)
        result = policy.check(
            triage_result=mock_triage_result,
            repo="owner/repo",
            pr_id="owner/repo#123",
            actor_name="morningai-bot",
        )
        assert result.allowed is False
        assert result.blocked_by == "loop_protection_actor"

    def test_policy_blocks_auto_fix_commit(self, mock_settings, mock_triage_result):
        """Test policy blocks auto-fix commit (loop protection)"""
        policy = AutoFixPolicy(mock_settings)
        result = policy.check(
            triage_result=mock_triage_result,
            repo="owner/repo",
            pr_id="owner/repo#123",
            commit_message="[auto-fix] Previous fix",
        )
        assert result.allowed is False
        assert result.blocked_by == "loop_protection_commit"

    def test_policy_blocks_category_not_allowed(self, mock_settings, mock_triage_result):
        """Test policy blocks category not in allowlist"""
        mock_triage_result.category = CommentCategory.SECURITY
        policy = AutoFixPolicy(mock_settings)
        result = policy.check(
            triage_result=mock_triage_result,
            repo="owner/repo",
            pr_id="owner/repo#123",
        )
        assert result.allowed is False
        assert result.blocked_by == "category_allowlist"

    def test_policy_blocks_repo_not_allowed(self, mock_settings, mock_triage_result):
        """Test policy blocks repo not in allowlist"""
        mock_settings.auto_fix_repos_allowlist = "allowed/repo1,allowed/repo2"
        policy = AutoFixPolicy(mock_settings)
        result = policy.check(
            triage_result=mock_triage_result,
            repo="other/repo",
            pr_id="other/repo#123",
        )
        assert result.allowed is False
        assert result.blocked_by == "repo_allowlist"

    def test_policy_allows_repo_in_allowlist(self, mock_settings, mock_triage_result):
        """Test policy allows repo in allowlist"""
        mock_settings.auto_fix_repos_allowlist = "owner/repo,other/repo"
        policy = AutoFixPolicy(mock_settings)
        result = policy.check(
            triage_result=mock_triage_result,
            repo="owner/repo",
            pr_id="owner/repo#123",
        )
        assert result.allowed is True


class TestAutoFixRateLimiter:
    """Tests for AutoFixRateLimiter class"""

    def test_rate_limiter_allows_when_redis_unavailable(self, mock_settings):
        """Test rate limiter allows request when Redis is unavailable"""
        with patch('utils.auto_fix_policy.redis.Redis') as mock_redis:
            mock_redis.side_effect = Exception("Connection failed")
            rate_limiter = AutoFixRateLimiter(mock_settings)
            result = rate_limiter.check("owner/repo", "owner/repo#123")
            assert result.allowed is True

    def test_rate_limiter_allows_under_limit(self, mock_settings):
        """Test rate limiter allows request under limit"""
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_pipe.execute.return_value = [None, 0]
        mock_redis.pipeline.return_value = mock_pipe

        with patch('utils.auto_fix_policy.redis.Redis') as redis_class:
            redis_class.return_value = mock_redis
            rate_limiter = AutoFixRateLimiter(mock_settings)
            result = rate_limiter.check("owner/repo", "owner/repo#123")
            assert result.allowed is True

    def test_rate_limiter_blocks_over_pr_limit(self, mock_settings):
        """Test rate limiter blocks when PR limit exceeded"""
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_pipe.execute.return_value = [None, 5]
        mock_redis.pipeline.return_value = mock_pipe

        with patch('utils.auto_fix_policy.redis.Redis') as redis_class:
            redis_class.return_value = mock_redis
            rate_limiter = AutoFixRateLimiter(mock_settings)
            result = rate_limiter.check("owner/repo", "owner/repo#123")
            assert result.allowed is False
            assert result.exceeded_dimension == "pr"


class TestAutoFixLoopProtection:
    """Tests for AutoFixLoopProtection class"""

    def test_loop_protection_allows_first_attempt(self, mock_settings):
        """Test loop protection allows first attempt"""
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        mock_redis.incr.return_value = 1

        with patch('utils.auto_fix_policy.redis.Redis') as redis_class:
            redis_class.return_value = mock_redis
            loop_protection = AutoFixLoopProtection(mock_settings)
            allowed, attempts = loop_protection.check_and_increment("owner/repo#123")
            assert allowed is True
            assert attempts == 1

    def test_loop_protection_blocks_max_retries(self, mock_settings):
        """Test loop protection blocks when max retries exceeded"""
        mock_redis = MagicMock()
        mock_redis.get.return_value = "3"

        with patch('utils.auto_fix_policy.redis.Redis') as redis_class:
            redis_class.return_value = mock_redis
            loop_protection = AutoFixLoopProtection(mock_settings)
            allowed, attempts = loop_protection.check_and_increment("owner/repo#123")
            assert allowed is False
            assert attempts == 3

    def test_loop_protection_allows_when_redis_unavailable(self, mock_settings):
        """Test loop protection allows when Redis is unavailable"""
        with patch('utils.auto_fix_policy.redis.Redis') as mock_redis:
            mock_redis.side_effect = Exception("Connection failed")
            loop_protection = AutoFixLoopProtection(mock_settings)
            allowed, attempts = loop_protection.check_and_increment("owner/repo#123")
            assert allowed is True
            assert attempts == 0

    def test_get_attempts(self, mock_settings):
        """Test getting current attempts"""
        mock_redis = MagicMock()
        mock_redis.get.return_value = "2"

        with patch('utils.auto_fix_policy.redis.Redis') as redis_class:
            redis_class.return_value = mock_redis
            loop_protection = AutoFixLoopProtection(mock_settings)
            attempts = loop_protection.get_attempts("owner/repo#123")
            assert attempts == 2

    def test_reset_attempts(self, mock_settings):
        """Test resetting attempts"""
        mock_redis = MagicMock()

        with patch('utils.auto_fix_policy.redis.Redis') as redis_class:
            redis_class.return_value = mock_redis
            loop_protection = AutoFixLoopProtection(mock_settings)
            result = loop_protection.reset_attempts("owner/repo#123")
            assert result is True
            mock_redis.delete.assert_called_once()


class TestCheckAutoFixSafety:
    """Tests for check_auto_fix_safety function"""

    def test_safety_check_passes_all(self, mock_settings, mock_triage_result):
        """Test safety check passes when all checks pass"""
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_pipe.execute.return_value = [None, 0]
        mock_redis.pipeline.return_value = mock_pipe
        mock_redis.get.return_value = None
        mock_redis.incr.return_value = 1

        with patch('utils.auto_fix_policy.redis.Redis') as redis_class:
            redis_class.return_value = mock_redis
            result = check_auto_fix_safety(
                triage_result=mock_triage_result,
                repo="owner/repo",
                pr_id="owner/repo#123",
                settings=mock_settings,
            )
            assert result.allowed is True
            assert result.policy_result.allowed is True

    def test_safety_check_fails_policy(self, mock_settings, mock_triage_result):
        """Test safety check fails when policy check fails"""
        mock_settings.auto_fix_enabled = False
        result = check_auto_fix_safety(
            triage_result=mock_triage_result,
            repo="owner/repo",
            pr_id="owner/repo#123",
            settings=mock_settings,
        )
        assert result.allowed is False
        assert "disabled" in result.reason.lower()

    def test_safety_check_fails_rate_limit(self, mock_settings, mock_triage_result):
        """Test safety check fails when rate limit exceeded"""
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_pipe.execute.return_value = [None, 100]
        mock_redis.pipeline.return_value = mock_pipe

        with patch('utils.auto_fix_policy.redis.Redis') as redis_class:
            redis_class.return_value = mock_redis
            result = check_auto_fix_safety(
                triage_result=mock_triage_result,
                repo="owner/repo",
                pr_id="owner/repo#123",
                settings=mock_settings,
            )
            assert result.allowed is False
            assert "rate limit" in result.reason.lower()

    def test_safety_check_fails_max_retries(self, mock_settings, mock_triage_result):
        """Test safety check fails when max retries exceeded"""
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_pipe.execute.return_value = [None, 0]
        mock_redis.pipeline.return_value = mock_pipe
        mock_redis.get.return_value = "5"

        with patch('utils.auto_fix_policy.redis.Redis') as redis_class:
            redis_class.return_value = mock_redis
            result = check_auto_fix_safety(
                triage_result=mock_triage_result,
                repo="owner/repo",
                pr_id="owner/repo#123",
                settings=mock_settings,
            )
            assert result.allowed is False
            assert "max retries" in result.reason.lower()


class TestCISignatureDeduplication:
    """Tests for CISignatureDeduplication class (Cost Optimization)"""

    def test_compute_signature_deterministic(self, mock_settings):
        """Test signature computation is deterministic"""
        with patch('utils.auto_fix_policy.redis.Redis') as redis_class:
            redis_class.return_value = MagicMock()
            dedup = CISignatureDeduplication(mock_settings)

            sig1 = dedup._compute_signature("owner/repo#123", "lint", "error msg")
            sig2 = dedup._compute_signature("owner/repo#123", "lint", "error msg")
            assert sig1 == sig2
            assert len(sig1) == 16  # SHA256 truncated to 16 chars

    def test_compute_signature_different_inputs(self, mock_settings):
        """Test different inputs produce different signatures"""
        with patch('utils.auto_fix_policy.redis.Redis') as redis_class:
            redis_class.return_value = MagicMock()
            dedup = CISignatureDeduplication(mock_settings)

            sig1 = dedup._compute_signature("owner/repo#123", "lint", "error A")
            sig2 = dedup._compute_signature("owner/repo#123", "lint", "error B")
            sig3 = dedup._compute_signature("owner/repo#123", "test", "error A")
            sig4 = dedup._compute_signature("owner/repo#456", "lint", "error A")

            assert sig1 != sig2  # Different error
            assert sig1 != sig3  # Different check name
            assert sig1 != sig4  # Different PR

    def test_check_and_mark_new_failure(self, mock_settings):
        """Test check_and_mark returns True for new failure"""
        mock_redis = MagicMock()
        mock_redis.get.return_value = None  # Not seen before

        with patch('utils.auto_fix_policy.redis.Redis') as redis_class:
            redis_class.return_value = mock_redis
            dedup = CISignatureDeduplication(mock_settings)
            is_new, signature = dedup.check_and_mark(
                pr_id="owner/repo#123",
                failed_check_name="lint",
                error_summary="Error: unused variable"
            )
            assert is_new is True
            assert len(signature) == 16
            mock_redis.setex.assert_called_once()

    def test_check_and_mark_duplicate_failure(self, mock_settings):
        """Test check_and_mark returns False for duplicate failure"""
        mock_redis = MagicMock()
        mock_redis.get.return_value = "2026-01-06T12:00:00Z"  # Already seen

        with patch('utils.auto_fix_policy.redis.Redis') as redis_class:
            redis_class.return_value = mock_redis
            dedup = CISignatureDeduplication(mock_settings)
            is_new, signature = dedup.check_and_mark(
                pr_id="owner/repo#123",
                failed_check_name="lint",
                error_summary="Error: unused variable"
            )
            assert is_new is False
            assert len(signature) == 16
            mock_redis.setex.assert_not_called()

    def test_check_and_mark_redis_unavailable_fail_open(self, mock_settings):
        """Test check_and_mark returns True (fail-open) when Redis unavailable"""
        with patch('utils.auto_fix_policy.redis.Redis') as redis_class:
            redis_class.side_effect = Exception("Connection failed")
            dedup = CISignatureDeduplication(mock_settings)
            is_new, signature = dedup.check_and_mark(
                pr_id="owner/repo#123",
                failed_check_name="lint",
                error_summary="Error: unused variable"
            )
            assert is_new is True  # Fail-open behavior
            assert len(signature) == 16

    def test_check_and_mark_redis_connection_error_fail_open(self, mock_settings):
        """Test check_and_mark returns True (fail-open) on Redis connection error"""
        import redis as redis_lib
        mock_redis = MagicMock()
        mock_redis.get.side_effect = redis_lib.ConnectionError("Connection lost")

        with patch('utils.auto_fix_policy.redis.Redis') as redis_class:
            redis_class.return_value = mock_redis
            dedup = CISignatureDeduplication(mock_settings)
            is_new, signature = dedup.check_and_mark(
                pr_id="owner/repo#123",
                failed_check_name="lint",
                error_summary="Error: unused variable"
            )
            assert is_new is True  # Fail-open behavior

    def test_check_and_mark_uses_correct_ttl(self, mock_settings):
        """Test check_and_mark uses correct TTL (24 hours default)"""
        mock_redis = MagicMock()
        mock_redis.get.return_value = None

        with patch('utils.auto_fix_policy.redis.Redis') as redis_class:
            redis_class.return_value = mock_redis
            dedup = CISignatureDeduplication(mock_settings)
            dedup.check_and_mark(
                pr_id="owner/repo#123",
                failed_check_name="lint",
                error_summary="Error: unused variable",
                ttl=3600  # Custom TTL
            )
            # Verify setex was called with correct TTL
            call_args = mock_redis.setex.call_args
            assert call_args[0][1] == 3600  # TTL is second positional arg

    def test_error_digest_truncation(self, mock_settings):
        """Test error summary is truncated to 500 chars for digest"""
        mock_redis = MagicMock()
        mock_redis.get.return_value = None

        with patch('utils.auto_fix_policy.redis.Redis') as redis_class:
            redis_class.return_value = mock_redis
            dedup = CISignatureDeduplication(mock_settings)

            # Long error message
            long_error = "x" * 1000
            short_error = "x" * 500

            sig_long = dedup._compute_signature("pr#1", "lint", long_error[:500])
            sig_short = dedup._compute_signature("pr#1", "lint", short_error)

            # Both should produce same signature (truncated to 500)
            assert sig_long == sig_short
