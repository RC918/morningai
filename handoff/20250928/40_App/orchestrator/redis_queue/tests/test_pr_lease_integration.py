"""
PR Lease Integration Tests for Concurrent Worker Scenarios.

This module implements integration tests to verify the atomic SETNX lease mechanism
for PR deduplication works correctly under concurrent access patterns.

Issue: #2917 (Add concurrent worker integration tests for PR lease mechanism)

Test Scenarios:
1. Concurrent Acquisition: Multiple workers attempt to acquire same lease simultaneously
2. TTL Expiry: Lease can be re-acquired after TTL expires
3. Complete Blocks: Completed lease blocks subsequent acquisitions with PR metadata
4. Release Allows Re-acquire: Released lease can be acquired by another worker

Test Markers:
- @pytest.mark.concurrency: Tests involving multi-threading (potential flakiness)
- @pytest.mark.integration: Tests requiring real Redis connection

Blueprint Alignment:
- Memory v2 (Layer 1): Atomic short-term reservation
- Safety Governor v2: Prevents race condition duplicates
- Telemetry v2: Structured logging for lease decisions
"""

import pytest
import threading
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple

import redis


class TestPRLeaseIntegration:
    """Integration tests for PR lease mechanism with real Redis.

    These tests verify the atomic SETNX lease mechanism works correctly
    under concurrent access patterns.
    """

    @pytest.fixture
    def redis_client(self):
        """Create a real Redis client for integration tests."""
        redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        try:
            client = redis.from_url(redis_url, decode_responses=True)
            client.ping()
            yield client
            # Clean up test keys only (safer than flushdb)
            for key in client.keys("orchestrator:pr_lease:*"):
                client.delete(key)
            for key in client.keys("test:pr_lease:*"):
                client.delete(key)
        except redis.ConnectionError:
            pytest.skip("Redis not available for integration tests")

    @pytest.fixture
    def unique_dedup_key(self):
        """Generate a unique dedup key for each test to avoid cross-test interference."""
        return f"test-repo/test:{int(time.time() * 1000000)}"

    @pytest.mark.integration
    @pytest.mark.concurrency
    def test_concurrent_lease_acquisition_only_one_winner(self, redis_client, unique_dedup_key):
        """Test that only one worker wins the lease under concurrent acquisition.

        Uses barrier-style synchronization to ensure all threads start simultaneously.
        Verifies exactly one winner and N-1 losers.
        """
        from governance.pr_deduplication import acquire_pr_lease, release_pr_lease

        num_workers = 10
        barrier = threading.Barrier(num_workers)
        results: List[Tuple[str, bool]] = []
        lock = threading.Lock()

        def attempt_acquire(worker_id: str):
            # Wait for all threads to be ready
            barrier.wait()

            result = acquire_pr_lease(
                dedup_key=unique_dedup_key,
                worker_id=worker_id,
                trace_id=f"trace-{worker_id}",
                redis_url=os.environ.get("REDIS_URL", "redis://localhost:6379/0")
            )

            with lock:
                results.append((worker_id, result.acquired))

        # Start all workers
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [
                executor.submit(attempt_acquire, f"worker-{i}")
                for i in range(num_workers)
            ]
            for future in as_completed(futures):
                future.result()

        # Verify exactly one winner
        winners = [r for r in results if r[1] is True]
        losers = [r for r in results if r[1] is False]

        assert len(winners) == 1, f"Expected exactly 1 winner, got {len(winners)}: {winners}"
        assert len(losers) == num_workers - 1, f"Expected {num_workers - 1} losers, got {len(losers)}"

        # Clean up
        release_pr_lease(
            dedup_key=unique_dedup_key,
            trace_id="cleanup",
            redis_url=os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        )

    @pytest.mark.integration
    def test_ttl_expiry_allows_reacquire(self, redis_client, unique_dedup_key):
        """Test that lease can be re-acquired after TTL expires.

        Uses a short TTL (1 second) to verify expiry behavior.
        """
        from governance.pr_deduplication import (
            acquire_pr_lease,
            _get_lease_key,
        )

        redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

        # Manually set a lease with short TTL (1 second)
        lease_key = _get_lease_key(unique_dedup_key)
        redis_client.set(
            lease_key,
            '{"worker_id": "worker-1", "trace_id": "trace-1", "status": "in_progress"}',
            ex=1  # 1 second TTL
        )

        # First attempt should fail (lease held)
        result1 = acquire_pr_lease(
            dedup_key=unique_dedup_key,
            worker_id="worker-2",
            trace_id="trace-2",
            redis_url=redis_url
        )
        assert result1.acquired is False, "Should not acquire lease while held"
        assert result1.holder == "worker-1", "Should report correct holder"

        # Wait for TTL to expire
        time.sleep(1.5)

        # Second attempt should succeed (lease expired)
        result2 = acquire_pr_lease(
            dedup_key=unique_dedup_key,
            worker_id="worker-2",
            trace_id="trace-2",
            redis_url=redis_url
        )
        assert result2.acquired is True, "Should acquire lease after TTL expiry"
        assert result2.holder == "worker-2", "Should report new holder"

    @pytest.mark.integration
    def test_complete_blocks_with_pr_metadata(self, redis_client, unique_dedup_key):
        """Test that completed lease blocks subsequent acquisitions and returns PR metadata.

        Verifies that after complete_pr_lease(), subsequent acquire attempts:
        1. Fail to acquire
        2. Return the existing PR URL and number
        """
        from governance.pr_deduplication import (
            acquire_pr_lease,
            complete_pr_lease,
        )

        redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

        # First worker acquires lease
        result1 = acquire_pr_lease(
            dedup_key=unique_dedup_key,
            worker_id="worker-1",
            trace_id="trace-1",
            redis_url=redis_url
        )
        assert result1.acquired is True, "First worker should acquire lease"

        # First worker completes with PR info
        complete_pr_lease(
            dedup_key=unique_dedup_key,
            trace_id="trace-1",
            pr_url="https://github.com/test/repo/pull/123",
            pr_number=123,
            redis_url=redis_url
        )

        # Second worker attempts to acquire
        result2 = acquire_pr_lease(
            dedup_key=unique_dedup_key,
            worker_id="worker-2",
            trace_id="trace-2",
            redis_url=redis_url
        )

        assert result2.acquired is False, "Second worker should not acquire completed lease"
        assert result2.existing_pr_url == "https://github.com/test/repo/pull/123", \
            "Should return existing PR URL"
        assert result2.existing_pr_number == 123, "Should return existing PR number"

    @pytest.mark.integration
    def test_release_allows_reacquire(self, redis_client, unique_dedup_key):
        """Test that released lease can be acquired by another worker.

        Verifies the release_pr_lease() function properly clears the lease.
        """
        from governance.pr_deduplication import acquire_pr_lease, release_pr_lease

        redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

        # First worker acquires lease
        result1 = acquire_pr_lease(
            dedup_key=unique_dedup_key,
            worker_id="worker-1",
            trace_id="trace-1",
            redis_url=redis_url
        )
        assert result1.acquired is True, "First worker should acquire lease"

        # Second worker fails to acquire
        result2 = acquire_pr_lease(
            dedup_key=unique_dedup_key,
            worker_id="worker-2",
            trace_id="trace-2",
            redis_url=redis_url
        )
        assert result2.acquired is False, "Second worker should not acquire held lease"

        # First worker releases lease
        released = release_pr_lease(
            dedup_key=unique_dedup_key,
            trace_id="trace-1",
            redis_url=redis_url
        )
        assert released is True, "Release should succeed"

        # Second worker can now acquire
        result3 = acquire_pr_lease(
            dedup_key=unique_dedup_key,
            worker_id="worker-2",
            trace_id="trace-2",
            redis_url=redis_url
        )
        assert result3.acquired is True, "Second worker should acquire after release"

    @pytest.mark.integration
    @pytest.mark.concurrency
    def test_concurrent_acquire_release_cycles(self, redis_client, unique_dedup_key):
        """Test multiple acquire-release cycles under concurrent access.

        Simulates realistic scenario where workers acquire, do work, and release.
        Verifies no deadlocks or race conditions over multiple cycles.
        """
        from governance.pr_deduplication import acquire_pr_lease, release_pr_lease

        redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        num_workers = 5
        cycles_per_worker = 3

        successful_acquisitions = [0]
        errors: List[str] = []
        lock = threading.Lock()

        def worker_cycle(worker_id: str):
            for cycle in range(cycles_per_worker):
                try:
                    result = acquire_pr_lease(
                        dedup_key=unique_dedup_key,
                        worker_id=worker_id,
                        trace_id=f"trace-{worker_id}-{cycle}",
                        redis_url=redis_url
                    )

                    if result.acquired:
                        with lock:
                            successful_acquisitions[0] += 1

                        # Simulate work
                        time.sleep(0.01)

                        # Release lease
                        release_pr_lease(
                            dedup_key=unique_dedup_key,
                            trace_id=f"trace-{worker_id}-{cycle}",
                            redis_url=redis_url
                        )
                    else:
                        # Wait a bit before retrying
                        time.sleep(0.05)

                except Exception as e:
                    with lock:
                        errors.append(f"{worker_id}-{cycle}: {str(e)}")

        # Start all workers
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [
                executor.submit(worker_cycle, f"worker-{i}")
                for i in range(num_workers)
            ]
            for future in as_completed(futures):
                future.result()

        assert len(errors) == 0, f"Errors during concurrent cycles: {errors}"
        assert successful_acquisitions[0] > 0, "Should have at least some successful acquisitions"

    @pytest.mark.integration
    def test_deterministic_dedup_key_generation(self, redis_client):
        """Test that generate_dedup_key produces deterministic keys.

        Same inputs should always produce the same key.
        """
        from governance.pr_deduplication import generate_dedup_key

        # Same inputs should produce same key
        key1 = generate_dedup_key(
            repo="test/repo",
            doc_file_path="docs/test.md",
            source_pr_number=123,
            event_action="opened"
        )
        key2 = generate_dedup_key(
            repo="test/repo",
            doc_file_path="docs/test.md",
            source_pr_number=123,
            event_action="opened"
        )

        assert key1 == key2, "Same inputs should produce same dedup key"

        # Different inputs should produce different keys
        key3 = generate_dedup_key(
            repo="test/repo",
            doc_file_path="docs/test.md",
            source_pr_number=124,  # Different PR number
            event_action="opened"
        )

        assert key1 != key3, "Different inputs should produce different dedup keys"

    @pytest.mark.integration
    def test_deterministic_branch_generation(self, redis_client):
        """Test that generate_deterministic_branch produces deterministic names.

        Same inputs should always produce the same branch name.
        """
        from governance.pr_deduplication import generate_deterministic_branch

        # Same inputs should produce same branch
        branch1 = generate_deterministic_branch(
            repo="test/repo",
            doc_file_path="docs/test-file.md",
            source_pr_number=123
        )
        branch2 = generate_deterministic_branch(
            repo="test/repo",
            doc_file_path="docs/test-file.md",
            source_pr_number=123
        )

        assert branch1 == branch2, "Same inputs should produce same branch name"
        assert branch1.startswith("orchestrator/docs-"), "Branch should have correct prefix"

        # Different inputs should produce different branches
        branch3 = generate_deterministic_branch(
            repo="test/repo",
            doc_file_path="docs/other-file.md",
            source_pr_number=123
        )

        assert branch1 != branch3, "Different inputs should produce different branch names"


class TestPRLeaseFailOpen:
    """Tests for fail-open behavior when Redis is unavailable.

    These tests verify that the lease mechanism fails open (allows PR creation)
    when Redis is unavailable, rather than blocking all PR creation.
    """

    def test_acquire_fails_open_when_redis_unavailable(self, caplog):
        """Test that acquire_pr_lease returns acquired=True when Redis is unavailable.

        This is the fail-open behavior to prevent Redis outages from blocking
        all PR creation.
        """
        import logging
        from governance.pr_deduplication import acquire_pr_lease

        # Use invalid Redis URL to simulate unavailability
        with caplog.at_level(logging.WARNING):
            result = acquire_pr_lease(
                dedup_key="test-key",
                worker_id="worker-1",
                trace_id="trace-1",
                redis_url="redis://invalid-host:6379/0"
            )

        # Should fail open
        assert result.acquired is True, "Should fail open when Redis unavailable"
        assert "fail-open" in result.reason.lower() or "unavailable" in result.reason.lower(), \
            f"Reason should indicate fail-open: {result.reason}"

    def test_release_handles_redis_unavailable(self):
        """Test that release_pr_lease handles Redis unavailability gracefully."""
        from governance.pr_deduplication import release_pr_lease

        # Use invalid Redis URL
        result = release_pr_lease(
            dedup_key="test-key",
            trace_id="trace-1",
            redis_url="redis://invalid-host:6379/0"
        )

        # Should return False but not raise
        assert result is False, "Should return False when Redis unavailable"

    def test_complete_handles_redis_unavailable(self):
        """Test that complete_pr_lease handles Redis unavailability gracefully."""
        from governance.pr_deduplication import complete_pr_lease

        # Use invalid Redis URL
        result = complete_pr_lease(
            dedup_key="test-key",
            trace_id="trace-1",
            pr_url="https://github.com/test/repo/pull/123",
            pr_number=123,
            redis_url="redis://invalid-host:6379/0"
        )

        # Should return False but not raise
        assert result is False, "Should return False when Redis unavailable"
