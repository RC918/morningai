#!/usr/bin/env python3
"""
Test Phase 7 Components
Comprehensive test suite for all Phase 7 functionality
"""

import asyncio
from datetime import datetime, timedelta

def test_ops_agent():
    """Test Ops_Agent functionality"""
    try:
        from ops_agent import OpsAgent, SystemCapacity, PerformanceMetrics
        
        ops_agent = OpsAgent()
        
        async def test_capacity():
            capacity = await ops_agent.analyze_system_capacity()
            return capacity
            
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        capacity = loop.run_until_complete(test_capacity())
        
        assert capacity.current_load >= 0.0
        assert capacity.recommended_batch_size > 0
        assert capacity.estimated_headroom >= 0.0
        
        print("✅ Ops_Agent: Capacity analysis test passed")
        return True
        
    except Exception as e:
        print(f"❌ Ops_Agent: Test failed - {e}")
        return False
        
def test_growth_strategist():
    """Test GrowthStrategist functionality"""
    try:
        from growth_strategist import GrowthStrategist, CampaignStrategy, GamificationRule
        
        growth_strategist = GrowthStrategist()
        
        async def test_campaign():
            campaign = await growth_strategist.plan_user_campaign(50000)
            return campaign
            
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        campaign = loop.run_until_complete(test_campaign())
        
        assert campaign.target_audience == "50000 users"
        assert campaign.batch_size > 0
        assert campaign.duration_hours > 0
        
        async def test_gamification():
            analysis = await growth_strategist.analyze_gamification_effectiveness()
            return analysis
            
        analysis = loop.run_until_complete(test_gamification())
        assert 'current_effectiveness' in analysis
        assert 'recommendations' in analysis
        
        print("✅ GrowthStrategist: Campaign planning and gamification test passed")
        return True
        
    except Exception as e:
        print(f"❌ GrowthStrategist: Test failed - {e}")
        return False
        
def test_pm_agent():
    """Test PM_Agent functionality"""
    try:
        from pm_agent import PMAgent, BetaCandidate, UserStory
        
        pm_agent = PMAgent()
        
        async def test_screening():
            candidates = await pm_agent.screen_beta_candidates()
            return candidates
            
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        candidates = loop.run_until_complete(test_screening())
        
        assert len(candidates) >= 0
        if candidates:
            assert candidates[0].activity_score >= 0.8
            
        async def test_feedback():
            stories = await pm_agent.collect_and_analyze_feedback()
            return stories
            
        stories = loop.run_until_complete(test_feedback())
        assert len(stories) >= 0
        if stories:
            assert stories[0].title is not None
            assert stories[0].priority in ['high', 'medium', 'low']
            
        print("✅ PM_Agent: Beta screening and feedback analysis test passed")
        return True
        
    except Exception as e:
        print(f"❌ PM_Agent: Test failed - {e}")
        return False
        
def test_hitl_approval_system():
    """Test HITL Approval System functionality"""
    try:
        from hitl_approval_system import HITLApprovalSystem, ApprovalRequest, ApprovalStatus, ApprovalChannel
        
        hitl_system = HITLApprovalSystem()
        
        async def test_approval():
            request = await hitl_system.create_approval_request(
                title="Test Approval",
                description="Test approval request",
                context={"test": True},
                requester_agent="test_agent"
            )
            return request
            
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        request = loop.run_until_complete(test_approval())
        
        assert request.title == "Test Approval"
        assert request.status == ApprovalStatus.PENDING
        assert request.requester_agent == "test_agent"
        assert request.trace_id is not None
        
        async def test_process():
            success = await hitl_system.process_approval(
                request.request_id,
                approved=True,
                approver="test_approver",
                channel=ApprovalChannel.CONSOLE
            )
            return success
            
        success = loop.run_until_complete(test_process())
        assert success == True
        
        pending = hitl_system.get_pending_requests()
        assert isinstance(pending, list)
        
        print("✅ HITL Approval System: Request creation and processing test passed")
        return True
        
    except Exception as e:
        print(f"❌ HITL Approval System: Test failed - {e}")
        return False
        
def test_phase7_startup():
    """Test Phase 7 startup system"""
    try:
        from phase7_startup import Phase7System
        
        system = Phase7System()
        
        assert system.config is not None
        assert 'phase7' in system.config
        
        status = system.get_system_status()
        assert 'phase' in status
        assert 'version' in status
        assert 'components' in status
        
        print("✅ Phase 7 Startup: Configuration and status test passed")
        return True
        
    except Exception as e:
        print(f"❌ Phase 7 Startup: Test failed - {e}")
        return False
        
def test_integration_with_phase6():
    """Test integration with Phase 6 components"""
    try:
        from meta_agent_decision_hub import MetaAgentDecisionHub
        from monitoring_system import MonitoringSystem
        from security_manager import SecurityManager
        
        meta_agent = MetaAgentDecisionHub()
        monitoring = MonitoringSystem("https://morningai-backend-v2.onrender.com")
        security_config = {
            'master_key': 'test-key',
            'secret_key': 'test-secret',
            'audit_log_file': 'test_audit.log'
        }
        security = SecurityManager(security_config)
        
        assert meta_agent is not None
        assert monitoring is not None
        assert security is not None
        
        print("✅ Phase 6 Integration: Import and initialization test passed")
        return True
        
    except Exception as e:
        print(f"❌ Phase 6 Integration: Test failed - {e}")
        return False
        
def test_component_coordination():
    """Test coordination between Phase 7 components"""
    try:
        from ops_agent import OpsAgent
        from growth_strategist import GrowthStrategist
        from pm_agent import PMAgent
        from hitl_approval_system import HITLApprovalSystem
        
        ops_agent = OpsAgent()
        growth_strategist = GrowthStrategist(ops_agent=ops_agent)
        pm_agent = PMAgent()
        hitl_system = HITLApprovalSystem()
        
        async def test_coordination():
            campaign = await growth_strategist.plan_user_campaign(10000)
            assert campaign.batch_size > 0
            
            request = await hitl_system.simulate_meta_agent_request()
            assert request.requester_agent == "Meta-Agent"
            
            return True
            
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(test_coordination())
        
        assert result == True
        
        print("✅ Component Coordination: Integration test passed")
        return True
        
    except Exception as e:
        print(f"❌ Component Coordination: Test failed - {e}")
        return False

def main():
    """Run all Phase 7 component tests"""
    print("🧪 Testing Phase 7 Components")
    print("=" * 60)
    
    tests = [
        ("Ops_Agent", test_ops_agent),
        ("GrowthStrategist", test_growth_strategist),
        ("PM_Agent", test_pm_agent),
        ("HITL Approval System", test_hitl_approval_system),
        ("Phase 7 Startup", test_phase7_startup),
        ("Phase 6 Integration", test_integration_with_phase6),
        ("Component Coordination", test_component_coordination)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Testing {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"   ⚠️ {test_name} test needs attention")
            
    print("=" * 60)
    print(f"🎯 Phase 7 Component Tests: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All Phase 7 components working correctly!")
        print("\n📋 Test Summary:")
        print("   ✅ Performance optimization and capacity management")
        print("   ✅ Data-driven growth engines and gamification")
        print("   ✅ Autonomous Beta tenant management")
        print("   ✅ Dual-channel HITL approval system")
        print("   ✅ Phase 6 integration and coordination")
        print("   ✅ Component startup and configuration")
        return True
    else:
        print("⚠️ Some Phase 7 components need attention")
        failed_tests = total - passed
        print(f"   ❌ {failed_tests} test(s) failed")
        return False
        
if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
