"""
Unit tests for type error handling and multi-threading safety in RoutingEngine

Issue #2687 - EPIC #2594: Qwen3 Provider Integration

Type Contract for context_size parameter:
- int: Supported (including negative values, which are treated as within limit)
- float: Supported (implicit comparison works in Python)
- bool: Supported (bool is subclass of int in Python)
- None: Raises TypeError (cannot compare with int)
- str/list/dict: Raises TypeError

Threading Behavior:
- Concurrent read operations (select_model, get_tier_for_task) are safe
- Concurrent write operations (set_available_providers) during reads may have
  race conditions but will not crash or produce invalid results
- These tests verify basic invariants, not strict thread-safety guarantees
"""
import concurrent.futures
import queue
import threading
import pytest

from core.routing import RoutingEngine, Tier, TaskType


class TestContextSizeTypeContract:
    """Tests documenting the type contract for context_size parameter.

    These tests define the expected API behavior for different input types.
    The contract is based on the current implementation where context_size
    is compared with int using `context_size > 0`.
    """

    def test_context_size_none_raises_type_error(self):
        """context_size=None raises TypeError (cannot compare None > int)"""
        engine = RoutingEngine(available_providers=["alicloud"])

        with pytest.raises(TypeError):
            engine.select_model(TaskType.CODING, context_size=None)

    def test_context_size_string_raises_type_error(self):
        """context_size as string raises TypeError (cannot compare str > int)"""
        engine = RoutingEngine(available_providers=["alicloud"])

        with pytest.raises(TypeError):
            engine.select_model(TaskType.CODING, context_size="1000")

    def test_context_size_float_is_supported(self):
        """context_size as float is supported (implicit comparison works).

        Float values are accepted because Python allows float > int comparison.
        This is documented behavior, not a bug.
        """
        engine = RoutingEngine(available_providers=["alicloud"])

        model = engine.select_model(TaskType.CODING, context_size=1000.5)

        assert model is not None
        assert model.tier == Tier.TIER_1
        assert model.provider == "alicloud"

    def test_context_size_negative_float_is_supported(self):
        """context_size as negative float is supported (treated as within limit)"""
        engine = RoutingEngine(available_providers=["alicloud"])

        model = engine.select_model(TaskType.CODING, context_size=-1000.5)

        assert model is not None
        assert model.tier == Tier.TIER_1

    def test_context_size_bool_true_is_supported(self):
        """context_size=True is supported (bool is subclass of int, True==1)"""
        engine = RoutingEngine(available_providers=["alicloud"])

        model = engine.select_model(TaskType.CODING, context_size=True)

        assert model is not None
        assert model.tier == Tier.TIER_1

    def test_context_size_bool_false_is_supported(self):
        """context_size=False is supported (bool is subclass of int, False==0)"""
        engine = RoutingEngine(available_providers=["alicloud"])

        model = engine.select_model(TaskType.CODING, context_size=False)

        assert model is not None
        assert model.tier == Tier.TIER_1

    def test_context_size_list_raises_type_error(self):
        """context_size as list raises TypeError"""
        engine = RoutingEngine(available_providers=["alicloud"])

        with pytest.raises(TypeError):
            engine.select_model(TaskType.CODING, context_size=[1000])

    def test_context_size_dict_raises_type_error(self):
        """context_size as dict raises TypeError"""
        engine = RoutingEngine(available_providers=["alicloud"])

        with pytest.raises(TypeError):
            engine.select_model(TaskType.CODING, context_size={"size": 1000})


class TestConcurrentReadOperations:
    """Tests for concurrent read operations on RoutingEngine.

    These tests verify that concurrent calls to read-only methods
    (select_model, get_tier_for_task) maintain basic invariants:
    - No exceptions raised
    - Results are valid (provider in allowed set, tier is valid enum)
    - Consistent results for identical inputs
    """

    def test_concurrent_select_model_maintains_invariants(self):
        """Concurrent select_model() calls maintain basic invariants.

        Uses threading.Barrier to synchronize thread start for maximum contention.
        Verifies that all results have valid provider, tier, and model_name.
        """
        allowed_providers = ["alicloud", "siliconflow"]
        engine = RoutingEngine(available_providers=allowed_providers)
        results = queue.Queue()
        errors = queue.Queue()
        num_threads = 8
        iterations_per_thread = 50
        barrier = threading.Barrier(num_threads)

        def worker(task_type, context_size):
            barrier.wait()  # Synchronize start for maximum contention
            for _ in range(iterations_per_thread):
                try:
                    model = engine.select_model(task_type, context_size=context_size)
                    # Verify invariants
                    assert model.provider in allowed_providers
                    assert model.tier in list(Tier)
                    assert model.model_name
                    results.put((task_type, model.tier, model.model_name, model.provider))
                except Exception as e:
                    errors.put((task_type, str(e)))

        test_cases = [
            (TaskType.PLANNING, 1000),
            (TaskType.CODING, 50000),
            (TaskType.REVIEW, 100),
            (TaskType.UX_COPY, 5000),
            (TaskType.TRANSLATION, 20000),
            (TaskType.SUMMARIZATION, 30000),
            (TaskType.ANALYSIS, 80000),
            (TaskType.CHAT, 10000),
        ]

        threads = [
            threading.Thread(target=worker, args=test_cases[i % len(test_cases)])
            for i in range(num_threads)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Verify no errors occurred
        error_list = []
        while not errors.empty():
            error_list.append(errors.get())
        assert len(error_list) == 0, f"Errors occurred: {error_list}"

        # Verify expected number of results
        assert results.qsize() == num_threads * iterations_per_thread

    def test_concurrent_select_model_with_thread_pool(self):
        """ThreadPoolExecutor handles concurrent select_model() with invariant checks"""
        allowed_providers = ["alicloud", "siliconflow"]
        engine = RoutingEngine(available_providers=allowed_providers)

        def select_and_verify(args):
            task_type, context_size = args
            model = engine.select_model(task_type, context_size=context_size)
            # Verify invariants
            assert model.provider in allowed_providers
            assert model.tier in list(Tier)
            assert model.model_name
            return model

        test_cases = [
            (TaskType.PLANNING, 1000),
            (TaskType.CODING, 50000),
            (TaskType.REVIEW, 100),
            (TaskType.UX_COPY, 5000),
            (TaskType.TRANSLATION, 20000),
            (TaskType.SUMMARIZATION, 30000),
            (TaskType.ANALYSIS, 80000),
            (TaskType.CHAT, 10000),
        ] * 20  # Run each case 20 times

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(select_and_verify, case) for case in test_cases]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        assert len(results) == len(test_cases)

    def test_concurrent_get_tier_for_task_is_consistent(self):
        """Concurrent get_tier_for_task() returns consistent results"""
        engine = RoutingEngine(available_providers=["alicloud"])
        results = queue.Queue()
        num_threads = 4
        iterations = 100
        barrier = threading.Barrier(num_threads)

        def worker():
            barrier.wait()
            for _ in range(iterations):
                tier = engine.get_tier_for_task(TaskType.CODING)
                results.put(tier)

        threads = [threading.Thread(target=worker) for _ in range(num_threads)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All reads should return consistent results
        result_list = []
        while not results.empty():
            result_list.append(results.get())

        assert len(result_list) == num_threads * iterations
        assert all(tier == Tier.TIER_1 for tier in result_list)

    def test_concurrent_select_model_same_input_is_consistent(self):
        """Concurrent select_model() with same input returns consistent results"""
        engine = RoutingEngine(available_providers=["alicloud"])
        results = queue.Queue()
        num_threads = 4
        iterations = 50
        barrier = threading.Barrier(num_threads)

        def worker():
            barrier.wait()
            for _ in range(iterations):
                model = engine.select_model(TaskType.PLANNING, context_size=1000)
                results.put(model.model_name)

        threads = [threading.Thread(target=worker) for _ in range(num_threads)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        result_list = []
        while not results.empty():
            result_list.append(results.get())

        assert len(result_list) == num_threads * iterations
        assert len(set(result_list)) == 1  # All same model name

    def test_concurrent_select_model_tier_upgrade_is_consistent(self):
        """Concurrent calls with large context consistently upgrade tier"""
        engine = RoutingEngine(available_providers=["alicloud"])
        results = queue.Queue()
        num_threads = 4
        iterations = 25
        barrier = threading.Barrier(num_threads)

        def worker():
            barrier.wait()
            for _ in range(iterations):
                # UX_COPY defaults to Tier 3, but 50000 tokens should upgrade
                model = engine.select_model(TaskType.UX_COPY, context_size=50000)
                results.put(model.tier)

        threads = [threading.Thread(target=worker) for _ in range(num_threads)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        result_list = []
        while not results.empty():
            result_list.append(results.get())

        assert len(result_list) == num_threads * iterations
        for tier in result_list:
            assert tier.value <= Tier.TIER_1.value


class TestConcurrentMixedOperations:
    """Tests for concurrent read and write operations.

    These tests verify that concurrent reads and writes do not crash
    and maintain basic invariants. They do NOT guarantee strict
    thread-safety or atomicity - that would require design-level
    synchronization in RoutingEngine.

    Purpose: Regression guard to catch obvious shared-state corruption.
    """

    def test_concurrent_provider_reads_maintain_invariants(self):
        """Concurrent provider availability checks maintain invariants"""
        allowed_providers = ["alicloud", "siliconflow"]
        engine = RoutingEngine(available_providers=allowed_providers)
        results = queue.Queue()
        num_threads = 4
        iterations = 100
        barrier = threading.Barrier(num_threads)

        def worker():
            barrier.wait()
            for _ in range(iterations):
                model = engine.select_model(TaskType.CODING)
                results.put(model.provider)

        threads = [threading.Thread(target=worker) for _ in range(num_threads)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        result_list = []
        while not results.empty():
            result_list.append(results.get())

        assert len(result_list) == num_threads * iterations
        assert all(p in allowed_providers for p in result_list)

    def test_concurrent_read_write_no_crash(self):
        """Concurrent reads and writes do not crash (best-effort regression guard).

        This test verifies that concurrent set_available_providers() calls
        during select_model() calls do not cause crashes or produce invalid
        results (provider not in any valid set, invalid tier, empty model_name).

        NOTE: This does NOT guarantee strict thread-safety. The test catches
        obvious corruption but cannot detect all race conditions.
        """
        all_valid_providers = {"alicloud", "siliconflow"}
        engine = RoutingEngine(available_providers=["alicloud"])
        errors = queue.Queue()
        num_iterations = 50
        barrier = threading.Barrier(3)

        def update_providers():
            barrier.wait()
            for i in range(num_iterations):
                providers = ["alicloud"] if i % 2 == 0 else ["alicloud", "siliconflow"]
                engine.set_available_providers(providers)

        def select_and_verify():
            barrier.wait()
            for _ in range(num_iterations):
                try:
                    model = engine.select_model(TaskType.CODING)
                    self._verify_model_invariants(model, all_valid_providers, errors)
                except ValueError:
                    pass  # Acceptable if no provider available briefly

        threads = [
            threading.Thread(target=update_providers),
            threading.Thread(target=select_and_verify),
            threading.Thread(target=select_and_verify),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        error_list = list(errors.queue)
        assert len(error_list) == 0, f"Errors occurred: {error_list}"

    def _verify_model_invariants(self, model, valid_providers, errors):
        """Helper to verify model invariants and report errors."""
        if model.provider not in valid_providers:
            errors.put(f"Invalid provider: {model.provider}")
        if model.tier not in list(Tier):
            errors.put(f"Invalid tier: {model.tier}")
        if not model.model_name:
            errors.put("Empty model_name")


class TestEdgeCasesWithTypeCoercion:
    """Tests for edge cases involving type coercion"""

    def test_context_size_numpy_int_is_supported(self):
        """context_size as numpy int is supported if numpy is available"""
        try:
            import numpy as np
        except ImportError:
            pytest.skip("numpy not available")

        engine = RoutingEngine(available_providers=["alicloud"])

        model = engine.select_model(TaskType.CODING, context_size=np.int64(1000))

        assert model is not None
        assert model.tier == Tier.TIER_1

    def test_context_size_large_int_uses_tier_0(self):
        """Very large int context_size uses Tier 0 (highest capability).

        Python handles arbitrarily large integers without overflow.
        This test documents that extremely large values are handled gracefully.
        """
        engine = RoutingEngine(available_providers=["alicloud"])

        model = engine.select_model(TaskType.CODING, context_size=10**18)

        assert model.tier == Tier.TIER_0

    def test_context_size_zero_same_as_default(self):
        """context_size=0 behaves same as not specifying context_size"""
        engine = RoutingEngine(available_providers=["alicloud"])

        model_zero = engine.select_model(TaskType.CODING, context_size=0)
        model_default = engine.select_model(TaskType.CODING)

        assert model_zero.tier == model_default.tier
        assert model_zero.model_name == model_default.model_name
