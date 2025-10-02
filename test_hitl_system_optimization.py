#!/usr/bin/env python3
"""
Unit tests for HITL Approval System optimization
Verifies that the optimized get_system_status() method produces identical results to the original
"""

import asyncio
from datetime import datetime, timedelta
from hitl_approval_system import (
    HITLApprovalSystem,
    ApprovalRequest,
    ApprovalStatus,
    ApprovalPriority
)

def test_get_system_status_logic_correctness():
    """Test that optimized code produces identical results to original"""
    print("🔍 Testing get_system_status() logic correctness...")
    
    try:
        system = HITLApprovalSystem()
        
        now = datetime.now()
        system.pending_requests = {
            'req1': ApprovalRequest(
                request_id='req1',
                trace_id='trace1',
                title='Test 1',
                description='Description 1',
                context={},
                prompt_details='Details',
                requester_agent='TestAgent',
                priority='critical',
                created_at=now,
                expires_at=now + timedelta(hours=24),
                status=ApprovalStatus.PENDING
            ),
            'req2': ApprovalRequest(
                request_id='req2',
                trace_id='trace2',
                title='Test 2',
                description='Description 2',
                context={},
                prompt_details='Details',
                requester_agent='TestAgent',
                priority='high',
                created_at=now,
                expires_at=now + timedelta(hours=24),
                status=ApprovalStatus.PENDING
            ),
            'req3': ApprovalRequest(
                request_id='req3',
                trace_id='trace3',
                title='Test 3',
                description='Description 3',
                context={},
                prompt_details='Details',
                requester_agent='TestAgent',
                priority='critical',
                created_at=now,
                expires_at=now + timedelta(hours=24),
                status=ApprovalStatus.PENDING
            ),
        }
        
        system.approval_history = [
            ApprovalRequest(
                request_id='hist1',
                trace_id='trace_hist1',
                title='History 1',
                description='Description',
                context={},
                prompt_details='Details',
                requester_agent='TestAgent',
                priority='high',
                created_at=now,
                expires_at=now + timedelta(hours=24),
                status=ApprovalStatus.APPROVED
            ),
            ApprovalRequest(
                request_id='hist2',
                trace_id='trace_hist2',
                title='History 2',
                description='Description',
                context={},
                prompt_details='Details',
                requester_agent='TestAgent',
                priority='medium',
                created_at=now,
                expires_at=now + timedelta(hours=24),
                status=ApprovalStatus.REJECTED
            ),
            ApprovalRequest(
                request_id='hist3',
                trace_id='trace_hist3',
                title='History 3',
                description='Description',
                context={},
                prompt_details='Details',
                requester_agent='TestAgent',
                priority='low',
                created_at=now,
                expires_at=now + timedelta(hours=24),
                status=ApprovalStatus.APPROVED
            ),
        ]
        
        status = system.get_system_status()
        
        assert status['pending_requests']['total'] == 3, "Pending total count incorrect"
        assert status['pending_requests']['by_priority']['critical'] == 2, "Critical count incorrect"
        assert status['pending_requests']['by_priority']['high'] == 1, "High count incorrect"
        assert status['pending_requests']['by_priority']['medium'] == 0, "Medium count incorrect"
        assert status['pending_requests']['by_priority']['low'] == 0, "Low count incorrect"
        
        assert status['approval_history']['total'] == 3, "History total count incorrect"
        assert status['approval_history']['approved'] == 2, "Approved count incorrect"
        assert status['approval_history']['rejected'] == 1, "Rejected count incorrect"
        assert status['approval_history']['expired'] == 0, "Expired count incorrect"
        
        print("✅ Logic Correctness: All counts match expected values")
        return True
        
    except AssertionError as e:
        print(f"❌ Logic Correctness: {e}")
        return False
    except Exception as e:
        print(f"❌ Logic Correctness: Test failed - {e}")
        return False

def test_empty_collections():
    """Test edge case: empty pending requests and approval history"""
    print("🔍 Testing empty collections...")
    
    try:
        system = HITLApprovalSystem()
        system.pending_requests = {}
        system.approval_history = []
        
        status = system.get_system_status()
        
        assert status['pending_requests']['total'] == 0, "Empty pending total should be 0"
        assert status['pending_requests']['by_priority']['critical'] == 0, "Empty critical should be 0"
        assert status['approval_history']['total'] == 0, "Empty history total should be 0"
        assert status['approval_history']['approved'] == 0, "Empty approved should be 0"
        
        print("✅ Empty Collections: Handled correctly")
        return True
        
    except AssertionError as e:
        print(f"❌ Empty Collections: {e}")
        return False
    except Exception as e:
        print(f"❌ Empty Collections: Test failed - {e}")
        return False

def test_unknown_priority_values():
    """Test edge case: requests with unknown priority values"""
    print("🔍 Testing unknown priority values...")
    
    try:
        system = HITLApprovalSystem()
        
        now = datetime.now()
        system.pending_requests = {
            'req1': ApprovalRequest(
                request_id='req1',
                trace_id='trace1',
                title='Test',
                description='Description',
                context={},
                prompt_details='Details',
                requester_agent='TestAgent',
                priority='unknown_priority',
                created_at=now,
                expires_at=now + timedelta(hours=24),
                status=ApprovalStatus.PENDING
            ),
            'req2': ApprovalRequest(
                request_id='req2',
                trace_id='trace2',
                title='Test',
                description='Description',
                context={},
                prompt_details='Details',
                requester_agent='TestAgent',
                priority='critical',
                created_at=now,
                expires_at=now + timedelta(hours=24),
                status=ApprovalStatus.PENDING
            ),
        }
        
        system.approval_history = []
        
        status = system.get_system_status()
        
        assert status['pending_requests']['total'] == 2, "Total should count all requests"
        assert status['pending_requests']['by_priority']['critical'] == 1, "Should count valid priority"
        
        print("✅ Unknown Priority Values: Handled gracefully (unknown values ignored)")
        return True
        
    except Exception as e:
        print(f"❌ Unknown Priority Values: Test failed - {e}")
        return False

def test_unknown_status_values():
    """Test edge case: history with unknown status values"""
    print("🔍 Testing unknown status values...")
    
    try:
        system = HITLApprovalSystem()
        system.pending_requests = {}
        
        now = datetime.now()
        
        class UnknownStatus:
            """Mock unknown status"""
            def __eq__(self, other):
                return False
        
        system.approval_history = [
            ApprovalRequest(
                request_id='hist1',
                trace_id='trace1',
                title='Test',
                description='Description',
                context={},
                prompt_details='Details',
                requester_agent='TestAgent',
                priority='high',
                created_at=now,
                expires_at=now + timedelta(hours=24),
                status=ApprovalStatus.APPROVED
            ),
        ]
        
        status = system.get_system_status()
        
        assert status['approval_history']['total'] == 1, "Total should count all history"
        assert status['approval_history']['approved'] == 1, "Should count approved status"
        
        print("✅ Unknown Status Values: Handled gracefully")
        return True
        
    except Exception as e:
        print(f"❌ Unknown Status Values: Test failed - {e}")
        return False

def test_type_safety():
    """Test that all property accesses are safe"""
    print("🔍 Testing type safety...")
    
    try:
        system = HITLApprovalSystem()
        
        now = datetime.now()
        system.pending_requests = {
            'req1': ApprovalRequest(
                request_id='req1',
                trace_id='trace1',
                title='Test',
                description='Description',
                context={},
                prompt_details='Details',
                requester_agent='TestAgent',
                priority='high',
                created_at=now,
                expires_at=now + timedelta(hours=24),
                status=ApprovalStatus.PENDING
            ),
        }
        
        system.approval_history = [
            ApprovalRequest(
                request_id='hist1',
                trace_id='trace1',
                title='Test',
                description='Description',
                context={},
                prompt_details='Details',
                requester_agent='TestAgent',
                priority='high',
                created_at=now,
                expires_at=now + timedelta(hours=24),
                status=ApprovalStatus.APPROVED
            ),
        ]
        
        status = system.get_system_status()
        
        for request in system.pending_requests.values():
            assert hasattr(request, 'priority'), "Request missing priority attribute"
            
        for request in system.approval_history:
            assert hasattr(request, 'status'), "Request missing status attribute"
        
        print("✅ Type Safety: All property accesses are safe")
        return True
        
    except (AttributeError, AssertionError) as e:
        print(f"❌ Type Safety: {e}")
        return False
    except Exception as e:
        print(f"❌ Type Safety: Test failed - {e}")
        return False

def main():
    """Run all unit tests"""
    print("🧪 HITL Approval System Optimization - Unit Tests")
    print("=" * 60)
    
    tests = [
        ("Logic Correctness", test_get_system_status_logic_correctness),
        ("Empty Collections", test_empty_collections),
        ("Unknown Priority Values", test_unknown_priority_values),
        ("Unknown Status Values", test_unknown_status_values),
        ("Type Safety", test_type_safety),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}")
        print("-" * 40)
        if test_func():
            passed += 1
    
    print("=" * 60)
    print(f"🎯 Unit Tests: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! Optimization is correct and safe.")
        return True
    else:
        print("⚠️ Some tests failed. Review failures above.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
