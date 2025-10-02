#!/usr/bin/env python3
"""
Unit tests for additional efficiency optimizations (Issues #2, #5, #6)
Verifies that optimized code produces identical results to original
"""

import statistics
from datetime import datetime, timedelta
from monitoring_system import MonitoringSystem, HealthCheckResult
from growth_strategist import GrowthStrategist, GamificationRule, RewardType
from saga_orchestrator import SagaOrchestrator, SagaTransaction, SagaStatus


def test_p95_latency_optimization():
    """Test Issue #2: P95 latency calculation optimization"""
    print("🔍 Testing P95 latency calculation optimization (Issue #2)...")
    
    try:
        monitor = MonitoringSystem("http://test.com", "token")
        
        now = datetime.now()
        for i in range(150):
            result = HealthCheckResult(
                endpoint="/test",
                status_code=200,
                latency_ms=float(i),
                timestamp=now,
                success=True
            )
            monitor.health_results.append(result)
        
        p95 = monitor.calculate_p95_latency(window_minutes=10)
        
        latencies = [r.latency_ms for r in monitor.health_results if r.latency_ms > 0]
        expected_p95 = statistics.quantiles(latencies, n=100)[94]
        
        assert abs(p95 - expected_p95) < 0.01, f"P95 mismatch: {p95} vs {expected_p95}"
        
        print(f"✅ P95 Latency Optimization: Calculated P95={p95:.2f}ms correctly")
        return True
        
    except AssertionError as e:
        print(f"❌ P95 Latency Optimization: {e}")
        return False
    except Exception as e:
        print(f"❌ P95 Latency Optimization: Test failed - {e}")
        return False


def test_p95_edge_cases():
    """Test Issue #2: Edge cases for P95 calculation"""
    print("🔍 Testing P95 edge cases...")
    
    try:
        monitor = MonitoringSystem("http://test.com", "token")
        
        p95_empty = monitor.calculate_p95_latency(window_minutes=10)
        assert p95_empty == 0.0, "Empty collection should return 0"
        
        now = datetime.now()
        for i in range(10):
            result = HealthCheckResult(
                endpoint="/test",
                status_code=200,
                latency_ms=float(i * 10),
                timestamp=now,
                success=True
            )
            monitor.health_results.append(result)
        
        p95_small = monitor.calculate_p95_latency(window_minutes=10)
        assert p95_small == 90.0, f"Small dataset should use max: {p95_small}"
        
        print("✅ P95 Edge Cases: Empty and small datasets handled correctly")
        return True
        
    except AssertionError as e:
        print(f"❌ P95 Edge Cases: {e}")
        return False
    except Exception as e:
        print(f"❌ P95 Edge Cases: Test failed - {e}")
        return False


def test_average_effectiveness_optimization():
    """Test Issue #5: Average effectiveness calculation optimization"""
    print("🔍 Testing average effectiveness optimization (Issue #5)...")
    
    try:
        strategist = GrowthStrategist()
        
        strategist.gamification_rules = {
            'rule1': GamificationRule(
                rule_id='rule1',
                name='Test Rule 1',
                trigger_condition='test',
                reward_type=RewardType.POINTS.value,
                reward_amount=100,
                effectiveness_score=0.75,
                last_updated=datetime.now()
            ),
            'rule2': GamificationRule(
                rule_id='rule2',
                name='Test Rule 2',
                trigger_condition='test',
                reward_type=RewardType.POINTS.value,
                reward_amount=200,
                effectiveness_score=0.85,
                last_updated=datetime.now()
            ),
            'rule3': GamificationRule(
                rule_id='rule3',
                name='Test Rule 3',
                trigger_condition='test',
                reward_type=RewardType.POINTS.value,
                reward_amount=150,
                effectiveness_score=0.65,
                last_updated=datetime.now()
            ),
        }
        
        report = strategist.get_growth_report()
        avg_effectiveness = report['average_effectiveness']
        
        expected_avg = statistics.mean([0.75, 0.85, 0.65])
        assert abs(avg_effectiveness - expected_avg) < 0.0001, \
            f"Average mismatch: {avg_effectiveness} vs {expected_avg}"
        
        print(f"✅ Average Effectiveness: Calculated average={avg_effectiveness:.4f} correctly")
        return True
        
    except AssertionError as e:
        print(f"❌ Average Effectiveness: {e}")
        return False
    except Exception as e:
        print(f"❌ Average Effectiveness: Test failed - {e}")
        return False


def test_average_effectiveness_edge_cases():
    """Test Issue #5: Edge cases for average calculation"""
    print("🔍 Testing average effectiveness edge cases...")
    
    try:
        strategist = GrowthStrategist()
        strategist.gamification_rules = {}
        
        report = strategist.get_growth_report()
        avg_effectiveness = report['average_effectiveness']
        
        assert avg_effectiveness == 0, "Empty rules should return 0"
        
        strategist.gamification_rules = {
            'rule1': GamificationRule(
                rule_id='rule1',
                name='Single Rule',
                trigger_condition='test',
                reward_type=RewardType.POINTS.value,
                reward_amount=100,
                effectiveness_score=0.75,
                last_updated=datetime.now()
            )
        }
        
        report = strategist.get_growth_report()
        avg_effectiveness = report['average_effectiveness']
        
        assert abs(avg_effectiveness - 0.75) < 0.0001, "Single rule average incorrect"
        
        print("✅ Average Effectiveness Edge Cases: Empty and single rule handled correctly")
        return True
        
    except AssertionError as e:
        print(f"❌ Average Effectiveness Edge Cases: {e}")
        return False
    except Exception as e:
        print(f"❌ Average Effectiveness Edge Cases: Test failed - {e}")
        return False


def test_saga_status_counting_optimization():
    """Test Issue #6: Saga status counting optimization"""
    print("🔍 Testing saga status counting optimization (Issue #6)...")
    
    try:
        orchestrator = SagaOrchestrator()
        
        saga1 = SagaTransaction(
            saga_id='saga1',
            name='Test Saga 1',
            status=SagaStatus.RUNNING
        )
        saga2 = SagaTransaction(
            saga_id='saga2',
            name='Test Saga 2',
            status=SagaStatus.RUNNING
        )
        saga3 = SagaTransaction(
            saga_id='saga3',
            name='Test Saga 3',
            status=SagaStatus.COMPLETED
        )
        saga4 = SagaTransaction(
            saga_id='saga4',
            name='Test Saga 4',
            status=SagaStatus.FAILED
        )
        
        orchestrator.active_sagas = {
            'saga1': saga1,
            'saga2': saga2,
            'saga3': saga3,
            'saga4': saga4
        }
        
        metrics = orchestrator.get_orchestrator_metrics()
        status_counts = metrics['saga_statuses']
        
        assert status_counts['running'] == 2, f"Running count incorrect: {status_counts['running']}"
        assert status_counts['completed'] == 1, f"Completed count incorrect: {status_counts['completed']}"
        assert status_counts['failed'] == 1, f"Failed count incorrect: {status_counts['failed']}"
        assert status_counts['created'] == 0, f"Created count should be 0: {status_counts['created']}"
        
        print("✅ Saga Status Counting: All counts match expected values")
        return True
        
    except AssertionError as e:
        print(f"❌ Saga Status Counting: {e}")
        return False
    except Exception as e:
        print(f"❌ Saga Status Counting: Test failed - {e}")
        return False


def test_saga_status_edge_cases():
    """Test Issue #6: Edge cases for saga status counting"""
    print("🔍 Testing saga status counting edge cases...")
    
    try:
        orchestrator = SagaOrchestrator()
        orchestrator.active_sagas = {}
        
        metrics = orchestrator.get_orchestrator_metrics()
        status_counts = metrics['saga_statuses']
        
        for status in SagaStatus:
            assert status_counts[status.value] == 0, f"Empty should have 0 for {status.value}"
        
        saga1 = SagaTransaction(
            saga_id='saga1',
            name='Single Saga',
            status=SagaStatus.RUNNING
        )
        orchestrator.active_sagas = {'saga1': saga1}
        
        metrics = orchestrator.get_orchestrator_metrics()
        status_counts = metrics['saga_statuses']
        
        assert status_counts['running'] == 1, "Single saga count incorrect"
        assert metrics['active_sagas'] == 1, "Active sagas count incorrect"
        
        print("✅ Saga Status Edge Cases: Empty and single saga handled correctly")
        return True
        
    except AssertionError as e:
        print(f"❌ Saga Status Edge Cases: {e}")
        return False
    except Exception as e:
        print(f"❌ Saga Status Edge Cases: Test failed - {e}")
        return False


def main():
    """Run all efficiency optimization tests"""
    print("🧪 Additional Efficiency Optimizations - Unit Tests (Issues #2, #5, #6)")
    print("=" * 70)
    
    tests = [
        ("Issue #2: P95 Latency Calculation", test_p95_latency_optimization),
        ("Issue #2: P95 Edge Cases", test_p95_edge_cases),
        ("Issue #5: Average Effectiveness", test_average_effectiveness_optimization),
        ("Issue #5: Average Edge Cases", test_average_effectiveness_edge_cases),
        ("Issue #6: Saga Status Counting", test_saga_status_counting_optimization),
        ("Issue #6: Saga Status Edge Cases", test_saga_status_edge_cases),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}")
        print("-" * 50)
        if test_func():
            passed += 1
    
    print("=" * 70)
    print(f"🎯 Unit Tests: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! Optimizations are correct and safe.")
        return True
    else:
        print("⚠️ Some tests failed. Review failures above.")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
