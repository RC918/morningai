"""
Unit tests for type error handling and multi-threading safety in RoutingEngine

Issue #2687 - EPIC #2594: Qwen3 Provider Integration

Tests cover:
- Type error handling for context_size parameter (None, string, float)
- Multi-threading safety for concurrent select_model() calls
- Thread-safe access to _task_routing and TIER_CONTEXT_LIMITS
"""
import concurrent.futures
import threading
import pytest

from core.routing import RoutingEngine, Tier, TaskType


class TestContextSizeTypeErrors:
    """Tests for type error handling in context_size parameter"""

    def test_context_size_none_raises_type_error(self):
        """context_size=None should raise TypeError (comparison with int fails)"""
        engine = RoutingEngine(available_providers=["alicloud"])

        # None cannot be compared with int, so TypeError is expected
        with pytest.raises(TypeError):
            engine.select_model(TaskType.CODING, context_size=None)

    def test_context_size_string_raises_type_error(self):
        """context_size as string should raise TypeError"""
        engine = RoutingEngine(available_providers=["alicloud"])

        with pytest.raises(TypeError):
            engine.select_model(TaskType.CODING, context_size="1000")

    def test_context_size_float_handled_or_raises(self):
        """context_size as float should either work (truncated) or raise TypeError"""
        engine = RoutingEngine(available_providers=["alicloud"])

        # Float might be implicitly converted to int or raise TypeError
        # This test documents the actual behavior
        try:
            model = engine.select_model(TaskType.CODING, context_size=1000.5)
            # If it works, should return valid model
            assert model is not None
            assert model.tier == Tier.TIER_1
        except TypeError:
            # TypeError is also acceptable behavior
            pass

    def test_context_size_negative_float_handled(self):
        """context_size as negative float should be handled gracefully"""
        engine = RoutingEngine(available_providers=["alicloud"])

        try:
            model = engine.select_model(TaskType.CODING, context_size=-1000.5)
            # If it works, should return valid model with default tier
            assert model is not None
            assert model.tier == Tier.TIER_1
        except TypeError:
            # TypeError is also acceptable behavior
            pass

    def test_context_size_bool_true_handled(self):
        """context_size=True (bool) should be handled (bool is subclass of int)"""
        engine = RoutingEngine(available_providers=["alicloud"])

        # True == 1 in Python, so this should work
        model = engine.select_model(TaskType.CODING, context_size=True)

        assert model is not None
        # context_size=1 should not affect tier selection
        assert model.tier == Tier.TIER_1

    def test_context_size_bool_false_handled(self):
        """context_size=False (bool) should be handled (bool is subclass of int)"""
        engine = RoutingEngine(available_providers=["alicloud"])

        # False == 0 in Python, so this should work
        model = engine.select_model(TaskType.CODING, context_size=False)

        assert model is not None
        assert model.tier == Tier.TIER_1

    def test_context_size_list_raises_type_error(self):
        """context_size as list should raise TypeError"""
        engine = RoutingEngine(available_providers=["alicloud"])

        with pytest.raises(TypeError):
            engine.select_model(TaskType.CODING, context_size=[1000])

    def test_context_size_dict_raises_type_error(self):
        """context_size as dict should raise TypeError"""
        engine = RoutingEngine(available_providers=["alicloud"])

        with pytest.raises(TypeError):
            engine.select_model(TaskType.CODING, context_size={"size": 1000})


class TestMultiThreadingSafety:
    """Tests for multi-threading safety in RoutingEngine"""

    def test_concurrent_select_model_calls(self):
        """Multiple threads calling select_model() should not cause race conditions"""
        engine = RoutingEngine(available_providers=["alicloud", "siliconflow"])
        results = []
        errors = []

        def call_select_model(task_type, context_size):
            try:
                model = engine.select_model(task_type, context_size=context_size)
                results.append((task_type, model.tier, model.model_name))
            except Exception as e:
                errors.append((task_type, str(e)))

        # Create multiple threads with different task types and context sizes
        threads = []
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

        for task_type, context_size in test_cases:
            t = threading.Thread(target=call_select_model, args=(task_type, context_size))
            threads.append(t)

        # Start all threads
        for t in threads:
            t.start()

        # Wait for all threads to complete
        for t in threads:
            t.join()

        # Verify no errors occurred
        assert len(errors) == 0, f"Errors occurred: {errors}"

        # Verify all calls returned results
        assert len(results) == len(test_cases)

    def test_concurrent_select_model_with_thread_pool(self):
        """ThreadPoolExecutor should handle concurrent select_model() calls"""
        engine = RoutingEngine(available_providers=["alicloud", "siliconflow"])

        def select_model_task(args):
            task_type, context_size = args
            return engine.select_model(task_type, context_size=context_size)

        test_cases = [
            (TaskType.PLANNING, 1000),
            (TaskType.CODING, 50000),
            (TaskType.REVIEW, 100),
            (TaskType.UX_COPY, 5000),
            (TaskType.TRANSLATION, 20000),
            (TaskType.SUMMARIZATION, 30000),
            (TaskType.ANALYSIS, 80000),
            (TaskType.CHAT, 10000),
        ] * 10  # Run each case 10 times

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(select_model_task, case) for case in test_cases]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All calls should succeed
        assert len(results) == len(test_cases)
        for model in results:
            assert model is not None
            assert model.tier in list(Tier)

    def test_concurrent_access_to_task_routing(self):
        """Concurrent reads of _task_routing should be safe"""
        engine = RoutingEngine(available_providers=["alicloud"])
        results = []

        def read_task_routing():
            for _ in range(100):
                tier = engine.get_tier_for_task(TaskType.CODING)
                results.append(tier)

        threads = [threading.Thread(target=read_task_routing) for _ in range(4)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All reads should return consistent results
        assert len(results) == 400
        assert all(tier == Tier.TIER_1 for tier in results)

    def test_concurrent_select_model_same_task_type(self):
        """Multiple threads selecting model for same task type should be consistent"""
        engine = RoutingEngine(available_providers=["alicloud"])
        results = []
        lock = threading.Lock()

        def select_same_task():
            for _ in range(50):
                model = engine.select_model(TaskType.PLANNING, context_size=1000)
                with lock:
                    results.append(model.model_name)

        threads = [threading.Thread(target=select_same_task) for _ in range(4)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All results should be the same model
        assert len(results) == 200
        assert len(set(results)) == 1  # All same model name

    def test_concurrent_select_model_with_large_context(self):
        """Concurrent calls with large context should all upgrade tier correctly"""
        engine = RoutingEngine(available_providers=["alicloud"])
        results = []

        def select_with_large_context():
            for _ in range(25):
                # UX_COPY defaults to Tier 3, but 50000 tokens should upgrade
                model = engine.select_model(TaskType.UX_COPY, context_size=50000)
                results.append(model.tier)

        threads = [threading.Thread(target=select_with_large_context) for _ in range(4)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All results should be upgraded tier (Tier 0 or 1)
        assert len(results) == 100
        for tier in results:
            assert tier.value <= Tier.TIER_1.value


class TestThreadSafeProviderAccess:
    """Tests for thread-safe access to provider configurations"""

    def test_concurrent_provider_availability_check(self):
        """Concurrent checks of provider availability should be safe"""
        engine = RoutingEngine(available_providers=["alicloud", "siliconflow"])
        results = []

        def check_providers():
            for _ in range(100):
                model = engine.select_model(TaskType.CODING)
                results.append(model.provider)

        threads = [threading.Thread(target=check_providers) for _ in range(4)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All results should be valid providers
        assert len(results) == 400
        assert all(p in ["alicloud", "siliconflow"] for p in results)

    def test_concurrent_set_available_providers(self):
        """Concurrent updates to available_providers should not crash"""
        engine = RoutingEngine(available_providers=["alicloud"])
        errors = []

        def update_providers():
            try:
                for i in range(50):
                    if i % 2 == 0:
                        engine.set_available_providers(["alicloud"])
                    else:
                        engine.set_available_providers(["alicloud", "siliconflow"])
            except Exception as e:
                errors.append(str(e))

        def select_models():
            try:
                for _ in range(50):
                    engine.select_model(TaskType.CODING)
            except Exception as e:
                errors.append(str(e))

        threads = [
            threading.Thread(target=update_providers),
            threading.Thread(target=select_models),
            threading.Thread(target=select_models),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should not have any errors (or only expected ones)
        # Note: This test may reveal race conditions if they exist
        assert len(errors) == 0, f"Errors occurred: {errors}"


class TestEdgeCasesWithTypeCoercion:
    """Tests for edge cases involving type coercion"""

    def test_context_size_numpy_int_if_available(self):
        """context_size as numpy int should work if numpy is available"""
        try:
            import numpy as np
            engine = RoutingEngine(available_providers=["alicloud"])

            model = engine.select_model(TaskType.CODING, context_size=np.int64(1000))

            assert model is not None
            assert model.tier == Tier.TIER_1
        except ImportError:
            pytest.skip("numpy not available")

    def test_context_size_large_int(self):
        """Very large int context_size should be handled"""
        engine = RoutingEngine(available_providers=["alicloud"])

        # Python can handle arbitrarily large integers
        model = engine.select_model(TaskType.CODING, context_size=10**18)

        # Should use Tier 0 (highest capability)
        assert model.tier == Tier.TIER_0

    def test_context_size_zero_vs_default(self):
        """context_size=0 should behave same as not specifying context_size"""
        engine = RoutingEngine(available_providers=["alicloud"])

        model_zero = engine.select_model(TaskType.CODING, context_size=0)
        model_default = engine.select_model(TaskType.CODING)

        # Both should return same tier (context_size=0 doesn't trigger adjustment)
        assert model_zero.tier == model_default.tier
        assert model_zero.model_name == model_default.model_name
