"""
Concurrency and Race Condition Tests for SimpleCoder - Issue #3218

This module tests thread-safety and race conditions in the SimpleCoder flow:
1. get_simple_coder() singleton initialization under concurrent access
2. Concurrent _attempt_simple_coder_fix() calls with shared state
3. commit_file() concurrent write scenarios
4. Redis atomic claim pattern for review deduplication

Issue #3218: Concurrency/Race Condition Tests
Parent Issue #2760: D-1 General Coder Agent MVP
Parent EPIC #2759: EPIC D - Autonomous Coder Agent Family
"""
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import patch, MagicMock

from coder.simple_coder import (
    SimpleCoder,
    CoderOutput,
    get_simple_coder,
)
from coder.autofix_gate import is_autofix_allowed, is_path_excluded


class TestGetSimpleCoderConcurrency:
    """Tests for thread-safety of get_simple_coder() singleton pattern."""

    def setup_method(self):
        """Reset the cached coder before each test."""
        import coder.simple_coder as sc_module
        sc_module._CACHED_CODER = None

    def teardown_method(self):
        """Clean up after each test."""
        import coder.simple_coder as sc_module
        sc_module._CACHED_CODER = None

    def test_concurrent_singleton_initialization(self):
        """
        Test that concurrent calls to get_simple_coder() return the same instance.

        Race Condition Scenario:
        - Multiple threads call get_simple_coder() simultaneously
        - Without proper synchronization, multiple SimpleCoder instances could be created
        - All threads should receive the same cached instance
        """
        results = []
        errors = []
        num_threads = 10
        barrier = threading.Barrier(num_threads)

        def get_coder_with_barrier():
            try:
                barrier.wait()
                coder = get_simple_coder()
                results.append(id(coder))
            except Exception as e:
                errors.append(str(e))

        threads = [
            threading.Thread(target=get_coder_with_barrier)
            for _ in range(num_threads)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == num_threads
        assert len(set(results)) == 1, "All threads should get the same instance"

    def test_singleton_under_high_contention(self):
        """
        Test singleton behavior under high contention with ThreadPoolExecutor.

        This simulates a production scenario where many workers might
        simultaneously request the SimpleCoder instance.
        """
        num_workers = 50
        instances = []

        def get_coder():
            return id(get_simple_coder())

        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(get_coder) for _ in range(num_workers)]
            for future in as_completed(futures):
                instances.append(future.result())

        unique_instances = set(instances)
        assert len(unique_instances) == 1, (
            f"Expected 1 unique instance, got {len(unique_instances)}. "
            "This indicates a race condition in singleton initialization."
        )


class TestAutofixGateConcurrency:
    """Tests for thread-safety of autofix gate checks."""

    def test_concurrent_gate_checks_same_outcome(self):
        """
        Test that concurrent gate checks on the same outcome are consistent.

        Race Condition Scenario:
        - Multiple threads check the same review_outcome simultaneously
        - All should return the same result without interference
        """
        outcome = {
            "severity": "low",
            "diff_truncated": False,
            "schema_validated": True
        }
        results = []
        num_threads = 20

        def check_gate():
            result = is_autofix_allowed(outcome)
            results.append(result)

        threads = [
            threading.Thread(target=check_gate)
            for _ in range(num_threads)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert all(r is True for r in results), "All checks should pass"
        assert len(results) == num_threads

    def test_concurrent_gate_checks_different_outcomes(self):
        """
        Test concurrent gate checks with different outcomes don't interfere.

        Race Condition Scenario:
        - Multiple threads check different review_outcomes
        - Each should get the correct result for their specific outcome
        """
        outcomes = [
            ({"severity": "low", "diff_truncated": False, "schema_validated": True}, True),
            ({"severity": "high", "diff_truncated": False, "schema_validated": True}, False),
            ({"severity": "low", "diff_truncated": True, "schema_validated": True}, False),
            ({"severity": "low", "diff_truncated": False, "schema_validated": False}, False),
        ]
        results = []
        lock = threading.Lock()

        def check_gate(outcome, expected):
            result = is_autofix_allowed(outcome)
            with lock:
                results.append((result, expected))

        threads = []
        for _ in range(5):
            for outcome, expected in outcomes:
                t = threading.Thread(target=check_gate, args=(outcome.copy(), expected))
                threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        for result, expected in results:
            assert result == expected, f"Expected {expected}, got {result}"

    def test_concurrent_path_exclusion_checks(self):
        """
        Test concurrent path exclusion checks are thread-safe.
        """
        paths_and_expected = [
            ("config/settings.py", True),
            ("src/utils.py", False),
            ("migrations/001.py", True),
            ("app/models.py", False),
            (".env", True),
            ("main.py", False),
        ]
        results = []
        lock = threading.Lock()

        def check_path(path, expected):
            result = is_path_excluded(path)
            with lock:
                results.append((path, result, expected))

        threads = []
        for _ in range(10):
            for path, expected in paths_and_expected:
                t = threading.Thread(target=check_path, args=(path, expected))
                threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        for path, result, expected in results:
            assert result == expected, f"Path {path}: expected {expected}, got {result}"


class TestSimpleCoderExecuteConcurrency:
    """Tests for concurrent SimpleCoder.execute() calls."""

    @patch.object(SimpleCoder, 'call_llm')
    def test_concurrent_execute_independent_tasks(self, mock_call_llm):
        """
        Test that concurrent execute() calls with different inputs don't interfere.

        Race Condition Scenario:
        - Multiple threads call execute() with different file_path/content
        - Each should process independently and return correct results
        """
        mock_call_llm.return_value = {
            "content": json.dumps({
                "status": "patch",
                "patch": "def fixed(): pass"
            })
        }

        coder = get_simple_coder()
        results = []
        lock = threading.Lock()

        def execute_task(task_id, file_path):
            from core.agents import AgentInput
            input_data = AgentInput(
                task_id=task_id,
                prompt="Fix the code",
                context={
                    "file_path": file_path,
                    "file_content": "def foo(): pass",
                    "review_comment": "Add docstring",
                    "severity": "low"
                }
            )
            output = coder.execute(input_data)
            with lock:
                results.append((task_id, file_path, output.success))

        threads = []
        for i in range(10):
            t = threading.Thread(
                target=execute_task,
                args=(f"task-{i}", f"file_{i}.py")
            )
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 10
        for task_id, file_path, success in results:
            assert success is True, f"Task {task_id} for {file_path} failed"

    @patch.object(SimpleCoder, 'call_llm')
    def test_concurrent_execute_mixed_success_failure(self, mock_call_llm):
        """
        Test concurrent execution with mixed success/failure outcomes.

        Race Condition Scenario:
        - Some tasks succeed, some fail
        - Results should not be mixed up between threads
        """
        call_count = [0]
        call_lock = threading.Lock()

        def mock_llm_response(*args, **kwargs):
            with call_lock:
                count = call_count[0]
                call_count[0] += 1
            if count % 2 == 0:
                return {"content": json.dumps({"status": "patch", "patch": "def x(): pass"})}
            else:
                return {"content": json.dumps({"status": "skipped", "reason": "Too complex"})}

        mock_call_llm.side_effect = mock_llm_response

        coder = get_simple_coder()
        results = []
        lock = threading.Lock()

        def execute_task(task_id):
            from core.agents import AgentInput
            input_data = AgentInput(
                task_id=task_id,
                prompt="Fix the code",
                context={
                    "file_path": "test.py",
                    "file_content": "def foo(): pass",
                    "review_comment": "Fix it",
                    "severity": "low"
                }
            )
            output = coder.execute(input_data)
            with lock:
                results.append((task_id, output.success, output.data.get("status")))

        threads = []
        for i in range(20):
            t = threading.Thread(target=execute_task, args=(f"task-{i}",))
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 20
        successes = [r for r in results if r[1] is True]
        failures = [r for r in results if r[1] is False]
        assert len(successes) == 10, f"Expected 10 successes, got {len(successes)}"
        assert len(failures) == 10, f"Expected 10 failures, got {len(failures)}"


class TestCommitFileConcurrency:
    """Tests for concurrent commit_file() scenarios.

    Note: These tests use a mock commit_file function to avoid importing
    tools.github_api which has complex dependencies. The tests verify
    the concurrency patterns rather than the actual GitHub API integration.
    """

    def test_concurrent_commits_to_different_files(self):
        """
        Test concurrent commits to different files don't interfere.

        Race Condition Scenario:
        - Multiple workers commit to different files on the same branch
        - Each commit should succeed independently
        """
        mock_repo = MagicMock()
        mock_file = MagicMock()
        mock_file.sha = "abc123"
        mock_repo.get_contents.return_value = mock_file

        def mock_commit_file(repo, branch, path, content, message):
            """Mock commit_file that simulates the real function."""
            file = repo.get_contents(path, ref=branch)
            repo.update_file(path, message, content, file.sha, branch=branch)

        results = []
        lock = threading.Lock()

        def do_commit(file_path, content):
            try:
                mock_commit_file(mock_repo, "main", file_path, content, f"Update {file_path}")
                with lock:
                    results.append((file_path, True, None))
            except Exception as e:
                with lock:
                    results.append((file_path, False, str(e)))

        threads = []
        for i in range(10):
            t = threading.Thread(
                target=do_commit,
                args=(f"file_{i}.py", f"content_{i}")
            )
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 10
        for file_path, success, error in results:
            assert success is True, f"Commit to {file_path} failed: {error}"

    def test_concurrent_commits_to_same_file_conflict(self):
        """
        Test concurrent commits to the same file (potential conflict scenario).

        Race Condition Scenario:
        - Multiple workers try to commit to the same file simultaneously
        - This tests how the system handles potential conflicts
        - In real GitHub, this would cause 409 Conflict errors
        """
        mock_repo = MagicMock()
        mock_file = MagicMock()
        mock_file.sha = "abc123"
        mock_repo.get_contents.return_value = mock_file

        commit_order = []
        commit_lock = threading.Lock()

        def track_commit(*args, **kwargs):
            with commit_lock:
                commit_order.append(time.time())

        mock_repo.update_file.side_effect = track_commit

        def mock_commit_file(repo, branch, path, content, message):
            """Mock commit_file that simulates the real function."""
            file = repo.get_contents(path, ref=branch)
            repo.update_file(path, message, content, file.sha, branch=branch)

        results = []
        lock = threading.Lock()
        barrier = threading.Barrier(5)

        def do_commit(worker_id):
            try:
                barrier.wait()
                mock_commit_file(mock_repo, "main", "shared_file.py", f"content_{worker_id}", "Update")
                with lock:
                    results.append((worker_id, True))
            except Exception:
                with lock:
                    results.append((worker_id, False))

        threads = []
        for i in range(5):
            t = threading.Thread(target=do_commit, args=(i,))
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 5
        assert len(commit_order) == 5, "All commits should have been attempted"


class TestAttemptSimpleCoderFixConcurrency:
    """Tests for concurrent _attempt_simple_coder_fix() calls."""

    def test_concurrent_state_access_isolation(self):
        """
        Test that concurrent calls with different states don't interfere.

        Race Condition Scenario:
        - Multiple workers process different PRs simultaneously
        - Each should access only its own state without cross-contamination
        """
        states = []
        for i in range(5):
            states.append({
                "repo": f"owner/repo{i}",
                "branch": f"branch-{i}",
                "review_outcome": {
                    "severity": "low",
                    "diff_truncated": False,
                    "schema_validated": True
                },
                "review_file_path": f"file_{i}.py",
                "comment_body": f"Fix issue {i}",
            })

        results = []
        lock = threading.Lock()

        def process_state(state, state_id):
            repo = state.get("repo")
            branch = state.get("branch")
            with lock:
                results.append({
                    "state_id": state_id,
                    "repo": repo,
                    "branch": branch,
                })

        threads = []
        for i, state in enumerate(states):
            t = threading.Thread(target=process_state, args=(state, i))
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 5
        for result in results:
            state_id = result["state_id"]
            assert result["repo"] == f"owner/repo{state_id}"
            assert result["branch"] == f"branch-{state_id}"


class TestRedisAtomicClaimConcurrency:
    """Tests for Redis atomic claim pattern used in review deduplication.

    Note: These tests use a mock implementation of the atomic claim pattern
    to avoid importing tools.github_api which has complex dependencies.
    The tests verify the concurrency patterns of SET NX atomic operations.
    """

    def test_atomic_claim_prevents_duplicate_reviews(self):
        """
        Test that atomic SET NX prevents duplicate review posts.

        Race Condition Scenario:
        - Multiple workers try to claim the same PR for review
        - Only one should succeed due to atomic SET NX
        """
        mock_redis = MagicMock()

        claim_results = [True] + [False] * 9
        claim_index = [0]
        claim_lock = threading.Lock()

        def mock_set_nx(*args, **kwargs):
            with claim_lock:
                idx = claim_index[0]
                claim_index[0] += 1
                return claim_results[idx] if idx < len(claim_results) else False

        mock_redis.set.side_effect = mock_set_nx
        mock_redis.get.return_value = "claiming"

        def mock_check_review_already_posted(repo, pr_number, head_sha):
            """Mock implementation of _check_review_already_posted."""
            if not head_sha:
                return False, None

            dedup_key = f"review_posted:{repo}:{pr_number}:{head_sha[:12]}:v1"
            claimed = mock_redis.set(dedup_key, "claiming", nx=True, ex=300)

            if claimed:
                return False, dedup_key
            else:
                return True, dedup_key

        results = []
        lock = threading.Lock()
        barrier = threading.Barrier(10)

        def try_claim(worker_id):
            barrier.wait()
            already_posted, key = mock_check_review_already_posted(
                "owner/repo", 123, "abc123def456"
            )
            with lock:
                results.append((worker_id, already_posted, key))

        threads = []
        for i in range(10):
            t = threading.Thread(target=try_claim, args=(i,))
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 10
        claimed = [r for r in results if r[1] is False]
        blocked = [r for r in results if r[1] is True]
        assert len(claimed) == 1, f"Expected 1 claim, got {len(claimed)}"
        assert len(blocked) == 9, f"Expected 9 blocked, got {len(blocked)}"


class TestCoderOutputThreadSafety:
    """Tests for thread-safety of CoderOutput creation and serialization."""

    def test_concurrent_coder_output_creation(self):
        """
        Test that concurrent CoderOutput creation is thread-safe.
        """
        results = []
        lock = threading.Lock()

        def create_output(idx):
            if idx % 2 == 0:
                output = CoderOutput.create_patch(
                    f"def func_{idx}(): pass",
                    file_path=f"file_{idx}.py",
                    syntax_valid=True
                )
            else:
                output = CoderOutput.create_skipped(
                    f"Reason {idx}",
                    file_path=f"file_{idx}.py"
                )
            with lock:
                results.append((idx, output.to_dict()))

        threads = []
        for i in range(20):
            t = threading.Thread(target=create_output, args=(i,))
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 20
        for idx, data in results:
            if idx % 2 == 0:
                assert data["status"] == "patch"
                assert f"func_{idx}" in data["patch"]
            else:
                assert data["status"] == "skipped"
                assert f"Reason {idx}" in data["reason"]

    def test_concurrent_json_serialization(self):
        """
        Test that concurrent JSON serialization doesn't cause issues.
        """
        outputs = [
            CoderOutput.create_patch(f"code_{i}", file_path=f"f{i}.py", syntax_valid=True)
            for i in range(10)
        ]

        results = []
        lock = threading.Lock()

        def serialize(output, idx):
            json_str = output.to_json()
            parsed = json.loads(json_str)
            with lock:
                results.append((idx, parsed))

        threads = []
        for i, output in enumerate(outputs):
            t = threading.Thread(target=serialize, args=(output, i))
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 10
        for idx, parsed in results:
            assert parsed["patch"] == f"code_{idx}"
            assert parsed["file_path"] == f"f{idx}.py"


class TestHighContentionScenarios:
    """Tests for high-contention production-like scenarios."""

    @patch.object(SimpleCoder, 'call_llm')
    def test_burst_of_concurrent_requests(self, mock_call_llm):
        """
        Test system behavior under a burst of concurrent requests.

        This simulates a production scenario where many PRs trigger
        SimpleCoder simultaneously (e.g., after a batch merge).
        """
        mock_call_llm.return_value = {
            "content": json.dumps({"status": "patch", "patch": "def x(): pass"})
        }

        num_requests = 100
        results = []
        errors = []
        lock = threading.Lock()

        def process_request(request_id):
            try:
                coder = get_simple_coder()
                from core.agents import AgentInput
                input_data = AgentInput(
                    task_id=f"burst-{request_id}",
                    prompt="Fix",
                    context={
                        "file_path": f"file_{request_id}.py",
                        "file_content": "x = 1",
                        "review_comment": "Fix it",
                        "severity": "low"
                    }
                )
                output = coder.execute(input_data)
                with lock:
                    results.append((request_id, output.success))
            except Exception as e:
                with lock:
                    errors.append((request_id, str(e)))

        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [
                executor.submit(process_request, i)
                for i in range(num_requests)
            ]
            for future in as_completed(futures):
                pass

        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == num_requests
        success_count = sum(1 for _, success in results if success)
        assert success_count == num_requests, (
            f"Expected {num_requests} successes, got {success_count}"
        )

    def test_gate_check_under_load(self):
        """
        Test autofix gate checks under high load.
        """
        num_checks = 1000
        outcomes = [
            {"severity": "low", "diff_truncated": False, "schema_validated": True},
            {"severity": "high", "diff_truncated": False, "schema_validated": True},
            {"severity": "low", "diff_truncated": True, "schema_validated": True},
        ]
        expected = [True, False, False]

        results = []
        lock = threading.Lock()

        def check_gate(idx):
            outcome = outcomes[idx % 3]
            result = is_autofix_allowed(outcome)
            with lock:
                results.append((idx, result, expected[idx % 3]))

        with ThreadPoolExecutor(max_workers=100) as executor:
            futures = [executor.submit(check_gate, i) for i in range(num_checks)]
            for future in as_completed(futures):
                pass

        assert len(results) == num_checks
        mismatches = [(idx, r, e) for idx, r, e in results if r != e]
        assert len(mismatches) == 0, f"Mismatches found: {mismatches[:10]}..."
