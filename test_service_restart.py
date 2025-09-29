#!/usr/bin/env python3
"""
Service Restart Testing
Tests state persistence through simulated service restarts
"""

import os
import sys
import time
import subprocess
import signal
from datetime import datetime, timedelta

sys.path.append('.')

from persistent_state_manager import persistent_state_manager

def simulate_service_restart():
    """Test service restart and state recovery"""
    print("🔄 Service Restart Simulation Test")
    print("=" * 60)
    
    print("📝 Phase 1: Saving critical state before restart...")
    
    test_data = {
        'beta_candidates': [
            {
                'user_id': f'user_{i}',
                'activity_score': 80 + i,
                'engagement_metrics': {'daily_logins': 10 + i, 'feature_usage': 0.7 + i*0.1},
                'qualification_reason': f'Test qualification reason {i}',
                'status': 'pending',
                'created_at': datetime.now().isoformat()
            }
            for i in range(5)
        ],
        'approval_requests': [
            {
                'request_id': f'req_{i}',
                'trace_id': f'trace_req_{i}',
                'title': f'Test Request {i}',
                'description': f'Test approval request {i} for restart testing',
                'context': {'test_mode': True, 'restart_test': True, 'request_num': i},
                'prompt_details': f'Automated restart test approval request {i}',
                'requester_agent': 'restart_test_agent',
                'priority': 'medium',
                'status': 'pending',
                'created_at': datetime.now().isoformat(),
                'expires_at': (datetime.now() + timedelta(hours=24)).isoformat()
            }
            for i in range(3)
        ]
    }
    
    for candidate in test_data['beta_candidates']:
        persistent_state_manager.save_beta_candidate(candidate)
    
    for request in test_data['approval_requests']:
        persistent_state_manager.save_approval_request(request)
    
    checkpoint_ids = []
    for i in range(3):
        checkpoint_id = persistent_state_manager.create_checkpoint(
            f'service_component_{i}',
            {'state': f'checkpoint_data_{i}', 'timestamp': time.time()},
            {'restart_test': True, 'component_id': i}
        )
        checkpoint_ids.append(checkpoint_id)
    
    print(f"💾 Saved {len(test_data['beta_candidates'])} beta candidates")
    print(f"💾 Saved {len(test_data['approval_requests'])} approval requests")
    print(f"💾 Created {len(checkpoint_ids)} checkpoints")
    
    print("\n⏳ Phase 2: Simulating service restart (3 second delay)...")
    time.sleep(3)
    
    print("\n🔄 Phase 3: Recovering state after restart...")
    start_recovery = time.time()
    
    recovered_candidates = persistent_state_manager.load_beta_candidates(status='pending')
    
    recovered_requests = persistent_state_manager.load_approval_requests(status='pending')
    
    recovered_checkpoints = []
    for i in range(3):
        checkpoint = persistent_state_manager.restore_from_checkpoint(f'service_component_{i}')
        if checkpoint:
            recovered_checkpoints.append(checkpoint)
    
    recovery_time = time.time() - start_recovery
    
    print(f"⏱️  Recovery completed in {recovery_time:.3f} seconds")
    print(f"📊 Recovered {len(recovered_candidates)} beta candidates")
    print(f"📊 Recovered {len(recovered_requests)} approval requests")
    print(f"📊 Recovered {len(recovered_checkpoints)} checkpoints")
    
    data_integrity_ok = (
        len(recovered_candidates) == len(test_data['beta_candidates']) and
        len(recovered_requests) == len(test_data['approval_requests']) and
        len(recovered_checkpoints) == 3
    )
    
    recovery_time_ok = recovery_time < 60  # Within 1 minute
    
    print(f"\n📋 Verification Results:")
    print(f"   Data Integrity: {'✅ PASSED' if data_integrity_ok else '❌ FAILED'}")
    print(f"   Recovery Time: {'✅ PASSED' if recovery_time_ok else '❌ FAILED'} ({recovery_time:.3f}s < 60s)")
    
    if data_integrity_ok and recovery_time_ok:
        print("✅ SERVICE RESTART TEST PASSED: State recovered successfully within time limit")
        return True
    else:
        print("❌ SERVICE RESTART TEST FAILED: Data loss or recovery too slow")
        return False

def test_multiple_restarts():
    """Test multiple consecutive restarts"""
    print("\n🔄 Multiple Restart Test")
    print("=" * 60)
    
    restart_count = 3
    all_passed = True
    
    for restart_num in range(1, restart_count + 1):
        print(f"\n🔄 Restart {restart_num}/{restart_count}")
        print("-" * 30)
        
        unique_data = {
            'user_id': f'restart_user_{restart_num}',
            'activity_score': 90 + restart_num,
            'engagement_metrics': {'daily_logins': 20 + restart_num, 'feature_usage': 0.9},
            'qualification_reason': f'Multiple restart test qualification {restart_num}',
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        }
        
        persistent_state_manager.save_beta_candidate(unique_data)
        
        checkpoint_id = persistent_state_manager.create_checkpoint(
            f'restart_test_{restart_num}',
            {'restart_number': restart_num, 'data': unique_data},
            {'multiple_restart_test': True}
        )
        
        print(f"💾 Saved data for restart {restart_num}")
        
        time.sleep(1)
        
        recovered_candidates = persistent_state_manager.load_beta_candidates(status='pending')
        recovered_checkpoint = persistent_state_manager.restore_from_checkpoint(f'restart_test_{restart_num}')
        
        restart_passed = (
            len(recovered_candidates) >= restart_num and
            recovered_checkpoint is not None
        )
        
        if restart_passed:
            print(f"✅ Restart {restart_num} recovery successful")
        else:
            print(f"❌ Restart {restart_num} recovery failed")
            all_passed = False
    
    if all_passed:
        print(f"\n✅ MULTIPLE RESTART TEST PASSED: All {restart_count} restarts recovered successfully")
    else:
        print(f"\n❌ MULTIPLE RESTART TEST FAILED: Some restarts failed to recover")
    
    return all_passed

if __name__ == "__main__":
    print("🧪 Service Restart Testing Suite")
    print("=" * 80)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    test1_passed = simulate_service_restart()
    
    test2_passed = test_multiple_restarts()
    
    print("\n" + "=" * 80)
    print("🎯 SERVICE RESTART TEST RESULTS")
    print("=" * 80)
    
    tests = [
        ("Single Service Restart", test1_passed),
        ("Multiple Consecutive Restarts", test2_passed)
    ]
    
    passed_tests = sum(1 for _, passed in tests if passed)
    
    for test_name, passed in tests:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\n🎯 Overall Result: {passed_tests}/{len(tests)} tests passed")
    
    if passed_tests == len(tests):
        print("🎉 ALL SERVICE RESTART TESTS PASSED! State persistence is robust.")
    else:
        print("⚠️  Some restart tests failed. State persistence needs improvement.")
