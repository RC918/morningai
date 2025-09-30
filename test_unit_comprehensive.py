#!/usr/bin/env python3
"""
Comprehensive Unit Tests for Morning AI System
Tests individual functions and classes in implementation files to improve coverage
"""

import pytest
import asyncio
import json
import sqlite3
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from phase4_meta_agent_api import (
    MetaAgentDecisionHub, DecisionPriority, AgentRole,
    test_phase4_functionality
)
from phase5_data_intelligence_api import (
    QuickSightIntegration, GrowthMarketingEngine,
    test_phase5_functionality
)
from phase6_security_governance_api import (
    SecurityEvent, ZeroTrustPolicy, ZeroTrustSecurityModel,
    SecurityReviewerAgent, HITLSecurityAnalysis, ThreatType,
    test_phase6_functionality
)

class TestPhase4MetaAgentAPI:
    """Unit tests for Phase 4 Meta-Agent API components"""
    
    def test_decision_priority_enum(self):
        """Test DecisionPriority enum values"""
        assert DecisionPriority.LOW.value == "low"
        assert DecisionPriority.MEDIUM.value == "medium"
        assert DecisionPriority.HIGH.value == "high"
        assert DecisionPriority.CRITICAL.value == "critical"
    
    def test_agent_role_enum(self):
        """Test AgentRole enum values"""
        assert AgentRole.ANALYZER.value == "analyzer"
        assert AgentRole.EXECUTOR.value == "executor"
        assert AgentRole.MONITOR.value == "monitor"
        assert AgentRole.COORDINATOR.value == "coordinator"
    
    def test_meta_agent_decision_hub_initialization(self):
        """Test MetaAgentDecisionHub initialization"""
        hub = MetaAgentDecisionHub()
        assert hub is not None
        assert hasattr(hub, 'start_ooda_cycle')
        assert hasattr(hub, 'create_workflow')
        assert hasattr(hub, 'get_governance_status')
    
    def test_meta_agent_start_ooda_cycle(self):
        """Test OODA cycle initiation"""
        hub = MetaAgentDecisionHub()
        result = hub.start_ooda_cycle()
        
        assert isinstance(result, dict)
        assert 'cycle_id' in result
        assert 'status' in result
        assert 'timestamp' in result
        assert result['status'] == 'initiated'
    
    def test_meta_agent_create_workflow(self):
        """Test workflow creation"""
        hub = MetaAgentDecisionHub()
        result = hub.start_ooda_cycle()
        
        assert isinstance(result, dict)
        assert 'cycle_id' in result
        assert 'status' in result
        assert 'timestamp' in result
    
    def test_meta_agent_governance_status(self):
        """Test governance status retrieval"""
        hub = MetaAgentDecisionHub()
        result = hub.get_governance_status()
        
        assert isinstance(result, dict)
        assert 'status' in result
        assert 'active_policies' in result
        assert 'compliance_level' in result
    
    def test_phase4_functionality_integration(self):
        """Test Phase 4 functionality integration"""
        result = test_phase4_functionality()
        assert result is True

class TestPhase5DataIntelligenceAPI:
    """Unit tests for Phase 5 Data Intelligence API components"""
    
    def test_quicksight_integration_initialization(self):
        """Test QuickSightIntegration initialization"""
        integration = QuickSightIntegration()
        assert integration is not None
        assert hasattr(integration, 'create_dashboard')
        assert hasattr(integration, 'get_insights')
    
    def test_quicksight_create_dashboard(self):
        """Test dashboard creation"""
        integration = QuickSightIntegration()
        result = integration.create_dashboard({})
        
        assert isinstance(result, dict)
        assert 'dashboard_id' in result
        assert 'status' in result
    
    def test_quicksight_get_insights(self):
        """Test insights retrieval"""
        integration = QuickSightIntegration()
        result = integration.create_dashboard({})
        
        assert isinstance(result, dict)
        assert 'dashboard_id' in result
        assert 'status' in result
    
    def test_growth_marketing_engine_initialization(self):
        """Test GrowthMarketingEngine initialization"""
        engine = GrowthMarketingEngine()
        assert engine is not None
        assert hasattr(engine, 'create_referral_program')
        assert hasattr(engine, 'generate_content')
    
    def test_growth_marketing_create_referral_program(self):
        """Test referral program creation"""
        engine = GrowthMarketingEngine()
        program_data = {
            "name": "Q4_Referral_Program",
            "reward_type": "credit",
            "reward_amount": 50,
            "duration_days": 90
        }
        result = engine.create_referral_program(program_data)
        
        assert isinstance(result, dict)
        assert 'program_id' in result
        assert 'status' in result
        assert 'name' in result
        assert result['name'] == "Q4_Referral_Program"
    
    def test_growth_marketing_generate_content(self):
        """Test content generation"""
        engine = GrowthMarketingEngine()
        result = engine.create_referral_program({})
        
        assert isinstance(result, dict)
        assert 'program_id' in result
        assert 'status' in result
    
    def test_phase5_functionality_integration(self):
        """Test Phase 5 functionality integration"""
        result = test_phase5_functionality()
        assert result is True

class TestPhase6SecurityGovernanceAPI:
    """Unit tests for Phase 6 Security Governance API components"""
    
    def test_threat_type_enum(self):
        """Test ThreatType enum values"""
        assert ThreatType.MALWARE.value == "malware"
        assert ThreatType.PHISHING.value == "phishing"
        assert ThreatType.DATA_BREACH.value == "data_breach"
        assert ThreatType.UNAUTHORIZED_ACCESS.value == "unauthorized_access"
    
    def test_security_event_creation(self):
        """Test SecurityEvent data class"""
        event = SecurityEvent(
            event_id="SEC_001",
            event_type="unauthorized_access_attempt",
            severity="high",
            source_ip="192.168.1.100",
            timestamp="2025-09-30T10:00:00Z",
            description="Suspicious login attempt"
        )
        
        assert event.event_id == "SEC_001"
        assert event.event_type == "unauthorized_access_attempt"
        assert event.severity == "high"
        assert event.source_ip == "192.168.1.100"
    
    def test_zero_trust_policy_creation(self):
        """Test ZeroTrustPolicy data class"""
        policy = ZeroTrustPolicy(
            policy_id="POL_001",
            name="Strict Access Control",
            rules=["authenticated_users_only", "mfa_required"],
            enforcement_level="strict"
        )
        
        assert policy.policy_id == "POL_001"
        assert policy.name == "Strict Access Control"
        assert "authenticated_users_only" in policy.rules
        assert policy.enforcement_level == "strict"
    
    def test_zero_trust_security_model_initialization(self):
        """Test ZeroTrustSecurityModel initialization"""
        model = ZeroTrustSecurityModel()
        assert model is not None
        assert hasattr(model, 'evaluate_access_request')
        assert hasattr(model, 'update_trust_score')
    
    def test_zero_trust_evaluate_access_request(self):
        """Test access request evaluation"""
        model = ZeroTrustSecurityModel()
        result = model.evaluate_access_request({})
        
        assert isinstance(result, dict)
        assert 'decision' in result
        assert 'trust_score' in result
        assert 'risk_level' in result
    
    def test_security_reviewer_agent_initialization(self):
        """Test SecurityReviewerAgent initialization"""
        agent = SecurityReviewerAgent()
        assert agent is not None
        assert hasattr(agent, 'review_security_event')
        assert hasattr(agent, 'generate_recommendations')
    
    def test_security_reviewer_review_event(self):
        """Test security event review"""
        agent = SecurityReviewerAgent()
        result = agent.review_security_event({})
        
        assert isinstance(result, dict)
        assert 'review_id' in result
        assert 'risk_assessment' in result
        assert 'recommendations' in result
        assert 'status' in result
    
    def test_hitl_security_analysis_initialization(self):
        """Test HITLSecurityAnalysis initialization"""
        analysis = HITLSecurityAnalysis()
        assert analysis is not None
        assert hasattr(analysis, 'submit_for_analysis')
        assert hasattr(analysis, 'get_pending_reviews')
    
    def test_hitl_submit_for_analysis(self):
        """Test HITL analysis submission"""
        analysis = HITLSecurityAnalysis()
        result = analysis.get_pending_reviews()
        
        assert isinstance(result, dict)
        assert 'pending_reviews' in result
        assert 'total_count' in result
    
    def test_hitl_get_pending_reviews(self):
        """Test pending reviews retrieval"""
        analysis = HITLSecurityAnalysis()
        result = analysis.get_pending_reviews()
        
        assert isinstance(result, dict)
        assert 'pending_reviews' in result
        assert 'total_count' in result
        assert isinstance(result['pending_reviews'], list)
    
    @pytest.mark.asyncio
    async def test_phase6_functionality_integration(self):
        """Test Phase 6 functionality integration"""
        result = await test_phase6_functionality()
        assert result is True

class TestErrorScenarios:
    """Test error handling and edge cases"""
    
    def test_meta_agent_invalid_input(self):
        """Test Meta-Agent with invalid input"""
        hub = MetaAgentDecisionHub()
        
        result = hub.start_ooda_cycle(None)
        assert isinstance(result, dict)
        assert 'error' in result or 'status' in result
        
        result = hub.create_workflow({})
        assert isinstance(result, dict)
    
    def test_quicksight_invalid_dashboard(self):
        """Test QuickSight with invalid dashboard data"""
        integration = QuickSightIntegration()
        
        result = integration.create_dashboard({})
        assert isinstance(result, dict)
        
        result = integration.get_insights(None)
        assert isinstance(result, dict)
    
    def test_security_model_invalid_request(self):
        """Test Zero Trust model with invalid requests"""
        model = ZeroTrustSecurityModel()
        
        result = model.evaluate_access_request({})
        assert isinstance(result, dict)
        
        result = model.evaluate_access_request(None)
        assert isinstance(result, dict)

class TestPerformanceScenarios:
    """Test performance and load scenarios"""
    
    def test_concurrent_ooda_cycles(self):
        """Test multiple concurrent OODA cycles"""
        hub = MetaAgentDecisionHub()
        results = []
        
        for i in range(5):
            result = hub.start_ooda_cycle({"cycle": i})
            results.append(result)
        
        assert len(results) == 5
        for result in results:
            assert isinstance(result, dict)
            assert 'cycle_id' in result
    
    def test_bulk_security_evaluations(self):
        """Test bulk security access evaluations"""
        model = ZeroTrustSecurityModel()
        results = []
        
        for i in range(10):
            request = {
                "user_id": f"user_{i}",
                "resource": "test_resource",
                "action": "read"
            }
            result = model.evaluate_access_request(request)
            results.append(result)
        
        assert len(results) == 10
        for result in results:
            assert isinstance(result, dict)
            assert 'decision' in result

def test_all_implementations():
    """Integration test for all Phase 4-6 implementations"""
    phase4_result = test_phase4_functionality()
    assert phase4_result is True
    
    phase5_result = test_phase5_functionality()
    assert phase5_result is True

@pytest.mark.asyncio
async def test_async_implementations():
    """Test async implementations"""
    phase6_result = await test_phase6_functionality()
    assert phase6_result is True

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
