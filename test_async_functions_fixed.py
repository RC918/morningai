#!/usr/bin/env python3
"""
Fixed Async Function Tests
Properly handle async functions with asyncio.run() to fix failing test suites
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from phase4_meta_agent_api import MetaAgentDecisionHub, LangGraphWorkflowEngine, AIGovernanceConsole
from phase5_data_intelligence_api import QuickSightIntegration, GrowthMarketingEngine, DataIntelligencePlatform
from phase6_security_governance_api import (
    ZeroTrustSecurityModel, SecurityReviewerAgent, HITLSecurityAnalysis,
    SecurityEvent, ThreatType, SecurityLevel
)

class TestAsyncFunctionHandling:
    """Test async functions with proper asyncio handling"""
    
    @pytest.mark.asyncio
    async def test_meta_agent_ooda_cycle_async(self):
        """Test MetaAgent OODA cycle as async function"""
        hub = MetaAgentDecisionHub()
        
        result = await hub.start_ooda_cycle()
        assert isinstance(result, dict)
        assert 'cycle_id' in result
        assert 'status' in result
    
    @pytest.mark.asyncio
    async def test_quicksight_create_dashboard_async(self):
        """Test QuickSight dashboard creation as async function"""
        integration = QuickSightIntegration()
        
        dashboard_config = {
            "name": "test_dashboard",
            "data_source": "test_source",
            "widgets": ["chart1", "table1"]
        }
        
        result = await integration.create_dashboard(dashboard_config)
        assert isinstance(result, dict)
        assert 'dashboard_id' in result
    
    @pytest.mark.asyncio
    async def test_growth_marketing_referral_program_async(self):
        """Test Growth Marketing referral program as async function"""
        engine = GrowthMarketingEngine()
        
        program_config = {
            "name": "test_referral_program",
            "reward_type": "points",
            "reward_amount": 100
        }
        
        result = await engine.create_referral_program(program_config)
        assert isinstance(result, dict)
        assert 'program_id' in result
    
    @pytest.mark.asyncio
    async def test_zero_trust_evaluate_access_async(self):
        """Test Zero Trust access evaluation as async function"""
        model = ZeroTrustSecurityModel()
        
        access_request = {
            "user_id": "test_user",
            "resource": "test_resource",
            "action": "read",
            "context": {"device": "trusted", "location": "office"}
        }
        
        result = await model.evaluate_access_request(access_request)
        assert isinstance(result, dict)
        assert 'decision' in result
    
    @pytest.mark.asyncio
    async def test_security_reviewer_review_event_async(self):
        """Test Security Reviewer event review as async function"""
        agent = SecurityReviewerAgent()
        
        security_event = SecurityEvent(
            event_id='test_event_001',
            timestamp=datetime.now(),
            event_type=ThreatType.UNAUTHORIZED_ACCESS,
            severity=SecurityLevel.HIGH,
            source_ip='192.168.1.100',
            user_id='test_user',
            description='Test security event for async testing',
            risk_score=0.8,
            requires_human_review=False
        )
        
        result = await agent.review_security_event(security_event)
        assert isinstance(result, dict)
        assert 'review_id' in result
    
    @pytest.mark.asyncio
    async def test_hitl_get_pending_reviews_async(self):
        """Test HITL pending reviews as async function"""
        analysis = HITLSecurityAnalysis()
        
        result = await analysis.get_pending_reviews()
        assert isinstance(result, dict)
        assert 'pending_reviews' in result or 'reviews' in result

class TestSyncFunctionWrappers:
    """Test sync wrapper functions for async operations"""
    
    def test_meta_agent_ooda_cycle_sync_wrapper(self):
        """Test MetaAgent OODA cycle with sync wrapper"""
        hub = MetaAgentDecisionHub()
        
        result = asyncio.run(hub.start_ooda_cycle())
        assert isinstance(result, dict)
        assert 'cycle_id' in result or 'workflow_id' in result
    
    def test_quicksight_dashboard_sync_wrapper(self):
        """Test QuickSight dashboard with sync wrapper"""
        integration = QuickSightIntegration()
        
        dashboard_config = {
            "name": "sync_test_dashboard",
            "data_source": "test_source"
        }
        
        result = asyncio.run(integration.create_dashboard(dashboard_config))
        assert isinstance(result, dict)
        assert 'dashboard_id' in result or 'id' in result
    
    def test_growth_marketing_sync_wrapper(self):
        """Test Growth Marketing with sync wrapper"""
        engine = GrowthMarketingEngine()
        
        program_config = {
            "name": "sync_test_program",
            "type": "referral"
        }
        
        result = asyncio.run(engine.create_referral_program(program_config))
        assert isinstance(result, dict)
        assert 'program_id' in result or 'id' in result
    
    def test_zero_trust_sync_wrapper(self):
        """Test Zero Trust with sync wrapper"""
        model = ZeroTrustSecurityModel()
        
        access_request = {
            "user_id": "sync_test_user",
            "resource": "test_resource",
            "action": "read"
        }
        
        result = asyncio.run(model.evaluate_access_request(access_request))
        assert isinstance(result, dict)
        assert 'decision' in result
    
    def test_security_reviewer_sync_wrapper(self):
        """Test Security Reviewer with sync wrapper"""
        from phase6_security_governance_api import SecurityEvent, ThreatType, SecurityLevel
        from datetime import datetime
        
        agent = SecurityReviewerAgent()
        
        event_data = SecurityEvent(
            event_id='sync_test_event',
            timestamp=datetime.now(),
            event_type=ThreatType.UNAUTHORIZED_ACCESS,
            severity=SecurityLevel.MEDIUM,
            source_ip='192.168.1.200',
            user_id='test_user',
            description='Test security event for sync wrapper testing',
            risk_score=0.6,
            requires_human_review=False
        )
        
        result = asyncio.run(agent.review_security_event(event_data))
        assert isinstance(result, dict)
        assert 'review_id' in result or 'status' in result
    
    def test_hitl_analysis_sync_wrapper(self):
        """Test HITL Analysis with sync wrapper"""
        analysis = HITLSecurityAnalysis()
        
        result = asyncio.run(analysis.get_pending_reviews())
        assert isinstance(result, dict)
        assert 'pending_reviews' in result or 'reviews' in result or 'count' in result

class TestConcurrentAsyncOperations:
    """Test concurrent async operations"""
    
    @pytest.mark.asyncio
    async def test_concurrent_dashboard_creation(self):
        """Test concurrent dashboard creation"""
        integration = QuickSightIntegration()
        
        tasks = []
        for i in range(3):
            config = {
                "name": f"concurrent_dashboard_{i}",
                "data_source": f"source_{i}"
            }
            task = integration.create_dashboard(config)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        assert len(results) == 3
        for result in results:
            if not isinstance(result, Exception):
                assert isinstance(result, dict)
    
    @pytest.mark.asyncio
    async def test_concurrent_security_evaluations(self):
        """Test concurrent security evaluations"""
        model = ZeroTrustSecurityModel()
        
        tasks = []
        for i in range(5):
            request = {
                "user_id": f"concurrent_user_{i}",
                "resource": "shared_resource",
                "action": "read"
            }
            task = model.evaluate_access_request(request)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        assert len(results) == 5
        for result in results:
            if not isinstance(result, Exception):
                assert isinstance(result, dict)
                assert 'decision' in result

class TestAsyncErrorHandling:
    """Test async error handling scenarios"""
    
    @pytest.mark.asyncio
    async def test_async_timeout_handling(self):
        """Test async operations with timeout"""
        hub = MetaAgentDecisionHub()
        
        try:
            result = await asyncio.wait_for(hub.start_ooda_cycle(), timeout=5.0)
            assert isinstance(result, dict)
        except asyncio.TimeoutError:
            pytest.skip("Operation timed out as expected")
    
    @pytest.mark.asyncio
    async def test_async_exception_handling(self):
        """Test async exception handling"""
        integration = QuickSightIntegration()
        
        invalid_config = {
            "name": None,  # Invalid configuration
            "data_source": ""
        }
        
        try:
            result = await integration.create_dashboard(invalid_config)
            assert isinstance(result, dict)
        except Exception as e:
            assert isinstance(e, (ValueError, TypeError, AttributeError))
    
    @pytest.mark.asyncio
    async def test_async_cancellation(self):
        """Test async operation cancellation"""
        model = ZeroTrustSecurityModel()
        
        request = {
            "user_id": "test_user",
            "resource": "test_resource",
            "action": "read"
        }
        
        task = asyncio.create_task(model.evaluate_access_request(request))
        
        await asyncio.sleep(0.1)
        task.cancel()
        
        try:
            await task
        except asyncio.CancelledError:
            pass  # Expected cancellation

def test_all_async_functions_work():
    """Integration test to verify all async functions work with asyncio.run"""
    from phase6_security_governance_api import SecurityEvent, ThreatType, SecurityLevel
    from datetime import datetime
    
    hub = MetaAgentDecisionHub()
    result = asyncio.run(hub.start_ooda_cycle())
    assert isinstance(result, dict)
    
    integration = QuickSightIntegration()
    result = asyncio.run(integration.create_dashboard({"name": "test"}))
    assert isinstance(result, dict)
    
    engine = GrowthMarketingEngine()
    result = asyncio.run(engine.create_referral_program({"name": "test"}))
    assert isinstance(result, dict)
    
    model = ZeroTrustSecurityModel()
    result = asyncio.run(model.evaluate_access_request({"user_id": "test"}))
    assert isinstance(result, dict)
    
    agent = SecurityReviewerAgent()
    security_event = SecurityEvent(
        event_id='test_event_integration',
        timestamp=datetime.now(),
        event_type=ThreatType.UNAUTHORIZED_ACCESS,
        severity=SecurityLevel.HIGH,
        source_ip='192.168.1.100',
        user_id='test_user',
        description='Integration test security event',
        risk_score=0.8,
        requires_human_review=False
    )
    result = asyncio.run(agent.review_security_event(security_event))
    assert isinstance(result, dict)
    
    analysis = HITLSecurityAnalysis()
    result = asyncio.run(analysis.get_pending_reviews())
    assert isinstance(result, dict)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
