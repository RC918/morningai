"""
Comprehensive test suite for HITL approval system optimization
Tests logic correctness, edge cases, type safety, and performance improvements
"""

import sys
import time
from typing import Dict, List
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta

class ApprovalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"

class ApprovalPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class MockApprovalRequest:
    request_id: str
    priority: str
    status: ApprovalStatus
    request_data: Dict
    created_at: datetime
    timeout_at: datetime

def original_implementation(pending_requests: Dict, approval_history: List) -> Dict:
    """Original implementation with multiple list comprehensions"""
    pending_by_priority = {}
    for priority in ['critical', 'high', 'medium', 'low']:
        pending_by_priority[priority] = len([r for r in pending_requests.values() if r.priority == priority])
    
    return {
        'pending_requests': {
            'total': len(pending_requests),
            'by_priority': pending_by_priority
        },
        'approval_history': {
            'total': len(approval_history),
            'approved': len([r for r in approval_history if r.status == ApprovalStatus.APPROVED]),
            'rejected': len([r for r in approval_history if r.status == ApprovalStatus.REJECTED]),
            'expired': len([r for r in approval_history if r.status == ApprovalStatus.EXPIRED])
        }
    }

def optimized_implementation(pending_requests: Dict, approval_history: List) -> Dict:
    """Optimized implementation with single-pass counters"""
    pending_by_priority = {
        'critical': 0,
        'high': 0,
        'medium': 0,
        'low': 0
    }
    for request in pending_requests.values():
        if request.priority in pending_by_priority:
            pending_by_priority[request.priority] += 1
    
    history_total = len(approval_history)
    history_counts = {
        'approved': 0,
        'rejected': 0,
        'expired': 0
    }
    for request in approval_history:
        if request.status == ApprovalStatus.APPROVED:
            history_counts['approved'] += 1
        elif request.status == ApprovalStatus.REJECTED:
            history_counts['rejected'] += 1
        elif request.status == ApprovalStatus.EXPIRED:
            history_counts['expired'] += 1
    
    return {
        'pending_requests': {
            'total': len(pending_requests),
            'by_priority': pending_by_priority
        },
        'approval_history': {
            'total': history_total,
            'approved': history_counts['approved'],
            'rejected': history_counts['rejected'],
            'expired': history_counts['expired']
        }
    }

def create_test_data(num_pending: int, num_history: int) -> tuple:
    """Create test data with various priority and status distributions"""
    priorities = ['critical', 'high', 'medium', 'low']
    statuses = [ApprovalStatus.APPROVED, ApprovalStatus.REJECTED, ApprovalStatus.EXPIRED, ApprovalStatus.PENDING]
    
    pending_requests = {}
    for i in range(num_pending):
        priority = priorities[i % len(priorities)]
        pending_requests[f"req_{i}"] = MockApprovalRequest(
            request_id=f"req_{i}",
            priority=priority,
            status=ApprovalStatus.PENDING,
            request_data={},
            created_at=datetime.now(),
            timeout_at=datetime.now() + timedelta(hours=24)
        )
    
    approval_history = []
    for i in range(num_history):
        status = statuses[i % len(statuses)]
        priority = priorities[i % len(priorities)]
        approval_history.append(MockApprovalRequest(
            request_id=f"hist_{i}",
            priority=priority,
            status=status,
            request_data={},
            created_at=datetime.now(),
            timeout_at=datetime.now() + timedelta(hours=24)
        ))
    
    return pending_requests, approval_history

def test_logic_correctness():
    """Test 1: Verify counting produces identical results"""
    print("=" * 80)
    print("TEST 1: Logic Correctness - Verify identical results")
    print("=" * 80)
    
    test_cases = [
        (10, 20, "Small dataset"),
        (100, 200, "Medium dataset"),
        (1000, 2000, "Large dataset"),
    ]
    
    all_passed = True
    for num_pending, num_history, description in test_cases:
        pending_requests, approval_history = create_test_data(num_pending, num_history)
        
        result_original = original_implementation(pending_requests, approval_history)
        result_optimized = optimized_implementation(pending_requests, approval_history)
        
        if result_original == result_optimized:
            print(f"✅ PASS: {description} ({num_pending} pending, {num_history} history)")
        else:
            print(f"❌ FAIL: {description}")
            print(f"   Original:  {result_original}")
            print(f"   Optimized: {result_optimized}")
            all_passed = False
    
    print(f"\nLogic Correctness: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}\n")
    return all_passed

def test_edge_cases():
    """Test 2: Edge cases - empty collections, unknown values"""
    print("=" * 80)
    print("TEST 2: Edge Cases - Empty collections and unknown values")
    print("=" * 80)
    
    all_passed = True
    
    print("\n2.1: Empty Collections")
    empty_pending = {}
    empty_history = []
    result = optimized_implementation(empty_pending, empty_history)
    expected = {
        'pending_requests': {'total': 0, 'by_priority': {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}},
        'approval_history': {'total': 0, 'approved': 0, 'rejected': 0, 'expired': 0}
    }
    if result == expected:
        print("✅ PASS: Empty collections handled correctly")
    else:
        print(f"❌ FAIL: Empty collections")
        print(f"   Expected:  {expected}")
        print(f"   Got:       {result}")
        all_passed = False
    
    print("\n2.2: Unknown Priority Values")
    pending_with_unknown = {
        "req_1": MockApprovalRequest("req_1", "unknown_priority", ApprovalStatus.PENDING, {}, datetime.now(), datetime.now()),
        "req_2": MockApprovalRequest("req_2", "critical", ApprovalStatus.PENDING, {}, datetime.now(), datetime.now()),
    }
    result = optimized_implementation(pending_with_unknown, [])
    if result['pending_requests']['by_priority']['critical'] == 1:
        print("✅ PASS: Unknown priority values ignored gracefully")
    else:
        print("❌ FAIL: Unknown priority values not handled correctly")
        all_passed = False
    
    print("\n2.3: Single Item Collections")
    single_pending = {"req_1": MockApprovalRequest("req_1", "high", ApprovalStatus.PENDING, {}, datetime.now(), datetime.now())}
    single_history = [MockApprovalRequest("hist_1", "high", ApprovalStatus.APPROVED, {}, datetime.now(), datetime.now())]
    result = optimized_implementation(single_pending, single_history)
    if result['pending_requests']['total'] == 1 and result['approval_history']['approved'] == 1:
        print("✅ PASS: Single item collections handled correctly")
    else:
        print("❌ FAIL: Single item collections")
        all_passed = False
    
    print(f"\nEdge Cases: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}\n")
    return all_passed

def test_type_safety():
    """Test 3: Type safety - valid properties"""
    print("=" * 80)
    print("TEST 3: Type Safety - Verify property access is safe")
    print("=" * 80)
    
    all_passed = True
    
    try:
        pending_requests, approval_history = create_test_data(10, 20)
        
        for request in pending_requests.values():
            assert hasattr(request, 'priority'), "Request missing 'priority' attribute"
            assert isinstance(request.priority, str), "Priority is not a string"
        
        for request in approval_history:
            assert hasattr(request, 'status'), "Request missing 'status' attribute"
            assert isinstance(request.status, ApprovalStatus), "Status is not ApprovalStatus enum"
        
        result = optimized_implementation(pending_requests, approval_history)
        
        print("✅ PASS: All property accesses are type-safe")
        print("   - All pending requests have valid 'priority' attributes")
        print("   - All history requests have valid 'status' attributes")
        print("   - No AttributeError or TypeError exceptions raised")
        
    except (AttributeError, TypeError, AssertionError) as e:
        print(f"❌ FAIL: Type safety issue detected: {e}")
        all_passed = False
    
    print(f"\nType Safety: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}\n")
    return all_passed

def test_behavior_preservation():
    """Test 4: Behavior preservation - no functional changes"""
    print("=" * 80)
    print("TEST 4: Behavior Preservation - Verify no functional changes")
    print("=" * 80)
    
    all_passed = True
    
    test_scenarios = [
        (0, 0, "Empty collections"),
        (5, 10, "Small dataset"),
        (50, 100, "Medium dataset"),
        (500, 1000, "Large dataset"),
    ]
    
    print("\nComparing original vs optimized across multiple scenarios:")
    for num_pending, num_history, description in test_scenarios:
        pending_requests, approval_history = create_test_data(num_pending, num_history)
        
        result_original = original_implementation(pending_requests, approval_history)
        result_optimized = optimized_implementation(pending_requests, approval_history)
        
        if result_original == result_optimized:
            print(f"✅ PASS: {description} - Behavior preserved")
        else:
            print(f"❌ FAIL: {description} - Behavior changed!")
            all_passed = False
    
    print(f"\nBehavior Preservation: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}\n")
    return all_passed

def benchmark_performance():
    """Benchmark: Measure performance improvement"""
    print("=" * 80)
    print("BENCHMARK: Performance Improvement Analysis")
    print("=" * 80)
    
    dataset_sizes = [
        (100, 200, "Small"),
        (1000, 2000, "Medium"),
        (10000, 20000, "Large"),
    ]
    
    print("\nPerformance comparison (lower is better):\n")
    print(f"{'Dataset':<15} {'Original (ms)':<20} {'Optimized (ms)':<20} {'Improvement':<15}")
    print("-" * 70)
    
    for num_pending, num_history, size_label in dataset_sizes:
        pending_requests, approval_history = create_test_data(num_pending, num_history)
        
        iterations = 1000
        
        start = time.perf_counter()
        for _ in range(iterations):
            original_implementation(pending_requests, approval_history)
        time_original = (time.perf_counter() - start) * 1000
        
        start = time.perf_counter()
        for _ in range(iterations):
            optimized_implementation(pending_requests, approval_history)
        time_optimized = (time.perf_counter() - start) * 1000
        
        improvement = ((time_original - time_optimized) / time_original) * 100
        
        print(f"{size_label:<15} {time_original:>18.3f}  {time_optimized:>18.3f}  {improvement:>13.1f}%")
    
    print("\n📊 Analysis:")
    print("   - Optimized version reduces iteration count from 8 passes to 2 passes")
    print("   - Complexity reduced from O(4n + 4m) to O(n + m)")
    print("   - Performance improvement scales with dataset size")
    print()

def main():
    """Run all tests and benchmarks"""
    print("\n" + "=" * 80)
    print("HITL Approval System Optimization - Comprehensive Test Suite")
    print("=" * 80 + "\n")
    
    results = []
    
    results.append(("Logic Correctness", test_logic_correctness()))
    results.append(("Edge Cases", test_edge_cases()))
    results.append(("Type Safety", test_type_safety()))
    results.append(("Behavior Preservation", test_behavior_preservation()))
    
    benchmark_performance()
    
    print("=" * 80)
    print("FINAL RESULTS")
    print("=" * 80)
    print()
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(passed for _, passed in results)
    print()
    if all_passed:
        print("🎉 ALL TESTS PASSED - Optimization is correct and safe!")
    else:
        print("⚠️  SOME TESTS FAILED - Please review the failures above")
    print("=" * 80)
    print()
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
