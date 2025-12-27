"""
Tests for Docs Digest Strategy (Layer 2 Value Gate)

Issue #3087: Implement Docs Digest Strategy
"""

import json
import time
from unittest.mock import MagicMock, patch

from governance.docs_digest import (
    BlockedDocChange,
    record_blocked_doc_change,
    maybe_flush_docs_digest,
    get_pending_count,
    _should_flush,
    _acquire_flush_lock,
    _release_flush_lock,
    _move_pending_to_processing,
    _clear_processing,
    _restore_processing_to_pending,
    _merge_changes_by_path,
)


class TestBlockedDocChange:
    """Tests for BlockedDocChange dataclass"""

    def test_to_dict(self):
        """Test serialization to dict"""
        change = BlockedDocChange(
            trace_id="test-trace-123",
            repo="RC918/morningai",
            doc_file_path="docs/test.md",
            content="# Test Content",
            goal="Add test documentation",
            score=20,
            downgrade_reason="value_gate_blocked",
            created_at=1234567890.0,
            changeset_hash="abc123",
            branch="",
        )

        result = change.to_dict()

        assert result["trace_id"] == "test-trace-123"
        assert result["repo"] == "RC918/morningai"
        assert result["doc_file_path"] == "docs/test.md"
        assert result["content"] == "# Test Content"
        assert result["goal"] == "Add test documentation"
        assert result["score"] == 20
        assert result["downgrade_reason"] == "value_gate_blocked"
        assert result["created_at"] == 1234567890.0
        assert result["changeset_hash"] == "abc123"

    def test_from_dict(self):
        """Test deserialization from dict"""
        data = {
            "trace_id": "test-trace-456",
            "repo": "RC918/morningai",
            "doc_file_path": "docs/another.md",
            "content": "# Another Content",
            "goal": "Add another doc",
            "score": 15,
            "downgrade_reason": "duplicate_blocked",
            "created_at": 9876543210.0,
            "changeset_hash": "def456",
            "branch": "test-branch",
        }

        change = BlockedDocChange.from_dict(data)

        assert change.trace_id == "test-trace-456"
        assert change.repo == "RC918/morningai"
        assert change.doc_file_path == "docs/another.md"
        assert change.score == 15
        assert change.changeset_hash == "def456"

    def test_from_dict_with_missing_fields(self):
        """Test deserialization handles missing fields gracefully"""
        data = {"trace_id": "minimal"}

        change = BlockedDocChange.from_dict(data)

        assert change.trace_id == "minimal"
        assert change.repo == ""
        assert change.score == 0


class TestRedisKeyGeneration:
    """Tests for Redis key generation"""

    def test_get_key_format(self):
        """Test key generation format"""
        from governance.docs_digest import _get_key
        key = _get_key("pending", "RC918/morningai")
        assert "pending" in key
        assert "RC918/morningai" in key
        assert "docs_digest" in key


class TestRecordBlockedDocChange:
    """Tests for record_blocked_doc_change function"""

    @patch('governance.docs_digest._get_settings')
    @patch('governance.docs_digest._get_redis_client')
    def test_record_when_disabled(self, mock_redis, mock_settings):
        """Test that recording is skipped when feature is disabled"""
        mock_settings.return_value = {"enabled": False}

        change = BlockedDocChange(
            trace_id="test",
            repo="test/repo",
            doc_file_path="docs/test.md",
            content="content",
            goal="goal",
            score=20,
            downgrade_reason="blocked",
            created_at=time.time(),
            changeset_hash="hash123",
        )

        result = record_blocked_doc_change(change)

        assert result is False
        mock_redis.assert_not_called()

    @patch('governance.docs_digest._get_settings')
    @patch('governance.docs_digest._get_redis_client')
    def test_record_duplicate_skipped(self, mock_redis, mock_settings):
        """Test that duplicate changes are skipped"""
        mock_settings.return_value = {
            "enabled": True,
            "count_threshold": 5,
            "max_items": 50,
        }

        mock_client = MagicMock()
        mock_client.sismember.return_value = True  # Already seen
        mock_redis.return_value = mock_client

        change = BlockedDocChange(
            trace_id="test",
            repo="test/repo",
            doc_file_path="docs/test.md",
            content="content",
            goal="goal",
            score=20,
            downgrade_reason="blocked",
            created_at=time.time(),
            changeset_hash="duplicate-hash",
        )

        result = record_blocked_doc_change(change)

        assert result is False
        mock_client.lpush.assert_not_called()

    @patch('governance.docs_digest._get_settings')
    @patch('governance.docs_digest._get_redis_client')
    def test_record_max_items_reached(self, mock_redis, mock_settings):
        """Test that recording is skipped when max items reached"""
        mock_settings.return_value = {
            "enabled": True,
            "count_threshold": 5,
            "max_items": 50,
        }

        mock_client = MagicMock()
        mock_client.sismember.return_value = False
        mock_client.llen.return_value = 50  # At max
        mock_redis.return_value = mock_client

        change = BlockedDocChange(
            trace_id="test",
            repo="test/repo",
            doc_file_path="docs/test.md",
            content="content",
            goal="goal",
            score=20,
            downgrade_reason="blocked",
            created_at=time.time(),
            changeset_hash="new-hash",
        )

        result = record_blocked_doc_change(change)

        assert result is False
        mock_client.lpush.assert_not_called()

    @patch('governance.docs_digest._get_settings')
    @patch('governance.docs_digest._get_redis_client')
    def test_record_success(self, mock_redis, mock_settings):
        """Test successful recording of blocked change"""
        mock_settings.return_value = {
            "enabled": True,
            "count_threshold": 5,
            "max_items": 50,
        }

        mock_client = MagicMock()
        mock_client.sismember.return_value = False
        mock_client.llen.return_value = 3  # Below max
        mock_redis.return_value = mock_client

        change = BlockedDocChange(
            trace_id="test-trace",
            repo="test/repo",
            doc_file_path="docs/test.md",
            content="content",
            goal="goal",
            score=20,
            downgrade_reason="blocked",
            created_at=time.time(),
            changeset_hash="new-hash",
        )

        result = record_blocked_doc_change(change)

        assert result is True
        mock_client.lpush.assert_called_once()
        mock_client.sadd.assert_called_once()


class TestShouldFlush:
    """Tests for _should_flush function"""

    @patch('governance.docs_digest._get_settings')
    def test_should_flush_disabled(self, mock_settings):
        """Test flush check when feature is disabled"""
        mock_settings.return_value = {"enabled": False}

        should, reason, count = _should_flush("test/repo")

        assert should is False
        assert reason == "disabled"

    @patch('governance.docs_digest._get_settings')
    @patch('governance.docs_digest._get_redis_client')
    def test_should_flush_empty(self, mock_redis, mock_settings):
        """Test flush check when pending list is empty"""
        mock_settings.return_value = {
            "enabled": True,
            "count_threshold": 5,
            "flush_hour_utc": 0,
        }

        mock_client = MagicMock()
        mock_client.llen.return_value = 0
        mock_redis.return_value = mock_client

        should, reason, count = _should_flush("test/repo")

        assert should is False
        assert reason == "empty"
        assert count == 0

    @patch('governance.docs_digest._get_settings')
    @patch('governance.docs_digest._get_redis_client')
    def test_should_flush_count_threshold(self, mock_redis, mock_settings):
        """Test flush triggered by count threshold"""
        mock_settings.return_value = {
            "enabled": True,
            "count_threshold": 5,
            "flush_hour_utc": 0,
        }

        mock_client = MagicMock()
        mock_client.llen.return_value = 5  # At threshold
        mock_redis.return_value = mock_client

        should, reason, count = _should_flush("test/repo")

        assert should is True
        assert reason == "count_threshold"
        assert count == 5


class TestFlushLock:
    """Tests for distributed lock functions"""

    @patch('governance.docs_digest._get_settings')
    @patch('governance.docs_digest._get_redis_client')
    def test_acquire_lock_success(self, mock_redis, mock_settings):
        """Test successful lock acquisition"""
        mock_settings.return_value = {"lock_ttl": 600}

        mock_client = MagicMock()
        mock_client.set.return_value = True
        mock_redis.return_value = mock_client

        acquired, token = _acquire_flush_lock("test/repo")

        assert acquired is True
        assert len(token) > 0
        mock_client.set.assert_called_once()

    @patch('governance.docs_digest._get_settings')
    @patch('governance.docs_digest._get_redis_client')
    def test_acquire_lock_busy(self, mock_redis, mock_settings):
        """Test lock acquisition when already held"""
        mock_settings.return_value = {"lock_ttl": 600}

        mock_client = MagicMock()
        mock_client.set.return_value = False  # Lock already held
        mock_redis.return_value = mock_client

        acquired, token = _acquire_flush_lock("test/repo")

        assert acquired is False
        assert token == ""

    @patch('governance.docs_digest._get_redis_client')
    def test_release_lock_success(self, mock_redis):
        """Test successful lock release"""
        mock_client = MagicMock()
        mock_client.get.return_value = "test-token"
        mock_redis.return_value = mock_client

        result = _release_flush_lock("test/repo", "test-token")

        assert result is True
        mock_client.delete.assert_called_once()

    @patch('governance.docs_digest._get_redis_client')
    def test_release_lock_mismatch(self, mock_redis):
        """Test lock release with mismatched token"""
        mock_client = MagicMock()
        mock_client.get.return_value = "different-token"
        mock_redis.return_value = mock_client

        result = _release_flush_lock("test/repo", "test-token")

        assert result is False
        mock_client.delete.assert_not_called()


class TestTwoStageMovement:
    """Tests for two-stage movement pattern"""

    @patch('governance.docs_digest._get_redis_client')
    def test_move_pending_to_processing(self, mock_redis):
        """Test moving items from pending to processing"""
        mock_client = MagicMock()

        # Simulate two items in pending
        item1 = json.dumps({
            "trace_id": "trace1",
            "repo": "test/repo",
            "doc_file_path": "docs/a.md",
            "content": "content1",
            "goal": "goal1",
            "score": 20,
            "downgrade_reason": "blocked",
            "created_at": 1234567890.0,
            "changeset_hash": "hash1",
            "branch": "",
        })
        item2 = json.dumps({
            "trace_id": "trace2",
            "repo": "test/repo",
            "doc_file_path": "docs/b.md",
            "content": "content2",
            "goal": "goal2",
            "score": 15,
            "downgrade_reason": "blocked",
            "created_at": 1234567891.0,
            "changeset_hash": "hash2",
            "branch": "",
        })

        mock_client.rpoplpush.side_effect = [item1, item2, None]
        mock_redis.return_value = mock_client

        items = _move_pending_to_processing("test/repo")

        assert len(items) == 2
        assert items[0].trace_id == "trace1"
        assert items[1].trace_id == "trace2"

    @patch('governance.docs_digest._get_redis_client')
    def test_clear_processing(self, mock_redis):
        """Test clearing processing list"""
        mock_client = MagicMock()
        mock_redis.return_value = mock_client

        result = _clear_processing("test/repo")

        assert result is True
        mock_client.delete.assert_called_once()

    @patch('governance.docs_digest._get_redis_client')
    def test_restore_processing_to_pending(self, mock_redis):
        """Test restoring items from processing to pending"""
        mock_client = MagicMock()

        # Simulate one item in processing
        item = json.dumps({"trace_id": "trace1"})
        mock_client.rpoplpush.side_effect = [item, None]
        mock_redis.return_value = mock_client

        result = _restore_processing_to_pending("test/repo")

        assert result is True


class TestMergeChangesByPath:
    """Tests for _merge_changes_by_path function"""

    def test_merge_single_change(self):
        """Test merging with single change"""
        changes = [
            BlockedDocChange(
                trace_id="trace1",
                repo="test/repo",
                doc_file_path="docs/test.md",
                content="content1",
                goal="goal1",
                score=20,
                downgrade_reason="blocked",
                created_at=1000.0,
                changeset_hash="hash1",
            )
        ]

        merged = _merge_changes_by_path(changes)

        assert len(merged) == 1
        assert "docs/test.md" in merged
        assert merged["docs/test.md"].trace_id == "trace1"

    def test_merge_multiple_same_path_latest_wins(self):
        """Test that latest change wins for same path"""
        changes = [
            BlockedDocChange(
                trace_id="trace1",
                repo="test/repo",
                doc_file_path="docs/test.md",
                content="old content",
                goal="old goal",
                score=20,
                downgrade_reason="blocked",
                created_at=1000.0,
                changeset_hash="hash1",
            ),
            BlockedDocChange(
                trace_id="trace2",
                repo="test/repo",
                doc_file_path="docs/test.md",
                content="new content",
                goal="new goal",
                score=25,
                downgrade_reason="blocked",
                created_at=2000.0,  # Later timestamp
                changeset_hash="hash2",
            ),
        ]

        merged = _merge_changes_by_path(changes)

        assert len(merged) == 1
        assert merged["docs/test.md"].trace_id == "trace2"
        assert merged["docs/test.md"].content == "new content"

    def test_merge_different_paths(self):
        """Test merging changes to different paths"""
        changes = [
            BlockedDocChange(
                trace_id="trace1",
                repo="test/repo",
                doc_file_path="docs/a.md",
                content="content a",
                goal="goal a",
                score=20,
                downgrade_reason="blocked",
                created_at=1000.0,
                changeset_hash="hash1",
            ),
            BlockedDocChange(
                trace_id="trace2",
                repo="test/repo",
                doc_file_path="docs/b.md",
                content="content b",
                goal="goal b",
                score=25,
                downgrade_reason="blocked",
                created_at=2000.0,
                changeset_hash="hash2",
            ),
        ]

        merged = _merge_changes_by_path(changes)

        assert len(merged) == 2
        assert "docs/a.md" in merged
        assert "docs/b.md" in merged


class TestMaybeFlushDocsDigest:
    """Tests for maybe_flush_docs_digest function"""

    @patch('governance.docs_digest._get_settings')
    def test_flush_disabled(self, mock_settings):
        """Test flush when feature is disabled"""
        mock_settings.return_value = {"enabled": False}

        result = maybe_flush_docs_digest("test/repo")

        assert result is None

    @patch('governance.docs_digest._should_flush')
    @patch('governance.docs_digest._get_settings')
    def test_flush_not_needed(self, mock_settings, mock_should_flush):
        """Test flush when conditions not met"""
        mock_settings.return_value = {"enabled": True}
        mock_should_flush.return_value = (False, "not_triggered", 3)

        result = maybe_flush_docs_digest("test/repo")

        assert result is None

    @patch('governance.docs_digest._release_flush_lock')
    @patch('governance.docs_digest._acquire_flush_lock')
    @patch('governance.docs_digest._should_flush')
    @patch('governance.docs_digest._get_settings')
    def test_flush_lock_busy(self, mock_settings, mock_should_flush, mock_acquire, mock_release):
        """Test flush when lock is already held"""
        mock_settings.return_value = {"enabled": True}
        mock_should_flush.return_value = (True, "count_threshold", 5)
        mock_acquire.return_value = (False, "")

        result = maybe_flush_docs_digest("test/repo")

        assert result is None
        mock_release.assert_not_called()


class TestGetPendingCount:
    """Tests for get_pending_count function"""

    @patch('governance.docs_digest._get_redis_client')
    def test_get_pending_count_success(self, mock_redis):
        """Test getting pending count"""
        mock_client = MagicMock()
        mock_client.llen.return_value = 7
        mock_redis.return_value = mock_client

        count = get_pending_count("test/repo")

        assert count == 7

    @patch('governance.docs_digest._get_redis_client')
    def test_get_pending_count_no_redis(self, mock_redis):
        """Test getting pending count when Redis unavailable"""
        mock_redis.return_value = None

        count = get_pending_count("test/repo")

        assert count == 0

    @patch('governance.docs_digest._get_redis_client')
    def test_get_pending_count_error(self, mock_redis):
        """Test getting pending count on error"""
        mock_client = MagicMock()
        mock_client.llen.side_effect = Exception("Redis error")
        mock_redis.return_value = mock_client

        count = get_pending_count("test/repo")

        assert count == 0
