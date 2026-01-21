"""
Comprehensive tests for Phase 4/5/6 API modules to achieve 80%+ coverage.

This module tests the core functionality of:
- phase4_meta_agent_api.py: Meta-Agent Decision Hub, LangGraph, Governance
- phase5_data_intelligence_api.py: QuickSight, Growth Marketing, Data Intelligence
- phase6_security_governance_api.py: Zero Trust, Security Reviewer, HITL, Audit
"""
import pytest
from datetime import datetime
from unittest.mock import patch


class TestPhase4MetaAgentDecisionHub:
    """Test MetaAgentDecisionHub class"""

    @pytest.fixture
    def decision_hub(self):
        from src.phases.phase4_meta_agent_api import MetaAgentDecisionHub
        return MetaAgentDecisionHub()

    @pytest.mark.asyncio
    async def test_start_ooda_cycle_success(self, decision_hub):
        """Test successful OODA cycle execution"""
        result = await decision_hub.start_ooda_cycle()

        assert result['status'] == 'completed'
        assert 'cycle_id' in result
        assert 'observation' in result
        assert 'orientation' in result
        assert result['observation']['system_metrics']['system_health_score'] == 85.3

    @pytest.mark.asyncio
    async def test_start_ooda_cycle_with_critical_issues(self, decision_hub):
        """Test OODA cycle when system health is below threshold"""
        with patch.object(decision_hub, '_collect_system_metrics') as mock_metrics:
            mock_metrics.return_value = {
                'cpu_usage': 95.0,
                'memory_usage': 90.0,
                'api_latency_p95': 250.0,
                'error_rate': 0.08,
                'active_users': 1000,
                'system_health_score': 65.0,
                'timestamp': datetime.now().isoformat()
            }

            result = await decision_hub.start_ooda_cycle()

            assert result['status'] == 'completed'
            assert result['orientation']['requires_action'] is True
            assert len(result['orientation']['critical_issues']) > 0

    @pytest.mark.asyncio
    async def test_start_ooda_cycle_error_handling(self, decision_hub):
        """Test OODA cycle error handling"""
        with patch.object(decision_hub, '_collect_system_metrics', side_effect=Exception('Test error')):
            result = await decision_hub.start_ooda_cycle()

            assert result['status'] == 'error'
            assert 'error' in result

    @pytest.mark.asyncio
    async def test_collect_system_metrics(self, decision_hub):
        """Test system metrics collection"""
        metrics = await decision_hub._collect_system_metrics()

        assert 'cpu_usage' in metrics
        assert 'memory_usage' in metrics
        assert 'api_latency_p95' in metrics
        assert 'error_rate' in metrics
        assert 'system_health_score' in metrics

    @pytest.mark.asyncio
    async def test_collect_business_metrics(self, decision_hub):
        """Test business metrics collection"""
        metrics = await decision_hub._collect_business_metrics()

        assert 'daily_active_users' in metrics
        assert 'conversion_rate' in metrics
        assert 'revenue_today' in metrics
        assert 'customer_satisfaction' in metrics

    @pytest.mark.asyncio
    async def test_analyze_situation_requires_action(self, decision_hub):
        """Test situation analysis when action is required"""
        system_metrics = {
            'system_health_score': 70.0,
            'error_rate': 0.06,
            'cpu_usage': 85.0,
            'api_latency_p95': 250.0
        }
        business_metrics = {'conversion_rate': 0.02}

        result = await decision_hub._analyze_situation(system_metrics, business_metrics)

        assert result['requires_action'] is True
        assert len(result['critical_issues']) > 0
        assert result['risk_level'] == 'high'

    @pytest.mark.asyncio
    async def test_analyze_situation_no_action_needed(self, decision_hub):
        """Test situation analysis when no action is needed"""
        system_metrics = {
            'system_health_score': 95.0,
            'error_rate': 0.01,
            'cpu_usage': 40.0,
            'api_latency_p95': 100.0
        }
        business_metrics = {'conversion_rate': 0.05}

        result = await decision_hub._analyze_situation(system_metrics, business_metrics)

        assert result['risk_level'] == 'low'

    def test_generate_recommendations_high_cpu(self, decision_hub):
        """Test recommendations when CPU is high"""
        system_metrics = {'cpu_usage': 85.0, 'api_latency_p95': 100.0}
        business_metrics = {'conversion_rate': 0.05}

        recommendations = decision_hub._generate_recommendations(system_metrics, business_metrics)

        assert 'Scale up compute resources' in recommendations

    def test_generate_recommendations_high_latency(self, decision_hub):
        """Test recommendations when latency is high"""
        system_metrics = {'cpu_usage': 40.0, 'api_latency_p95': 250.0}
        business_metrics = {'conversion_rate': 0.05}

        recommendations = decision_hub._generate_recommendations(system_metrics, business_metrics)

        assert 'Optimize API performance' in recommendations

    def test_generate_recommendations_low_conversion(self, decision_hub):
        """Test recommendations when conversion rate is low"""
        system_metrics = {'cpu_usage': 40.0, 'api_latency_p95': 100.0}
        business_metrics = {'conversion_rate': 0.02}

        recommendations = decision_hub._generate_recommendations(system_metrics, business_metrics)

        assert 'Improve conversion funnel' in recommendations

    @pytest.mark.asyncio
    async def test_make_decision_high_risk(self, decision_hub):
        """Test decision making for high risk situation"""
        situation = {
            'risk_level': 'high',
            'critical_issues': ['System health below threshold'],
            'requires_action': True
        }

        decision = await decision_hub._make_decision(situation)

        assert decision.strategy == 'immediate_intervention'
        assert decision.requires_approval is True
        assert len(decision.actions) > 0

    @pytest.mark.asyncio
    async def test_make_decision_low_risk(self, decision_hub):
        """Test decision making for low risk situation"""
        situation = {
            'risk_level': 'low',
            'critical_issues': [],
            'requires_action': True
        }

        decision = await decision_hub._make_decision(situation)

        assert decision.strategy == 'optimization_routine'
        assert decision.requires_approval is False

    @pytest.mark.asyncio
    async def test_execute_decision(self, decision_hub):
        """Test decision execution"""
        from src.phases.phase4_meta_agent_api import DecisionResult

        decision = DecisionResult(
            decision_id='test-123',
            strategy='optimization_routine',
            actions=[
                {'type': 'performance_tuning', 'parameters': {'target': 'api_latency'}},
                {'type': 'cache_optimization', 'parameters': {'ttl': 3600}}
            ],
            confidence=0.92,
            risk_assessment=0.08,
            execution_timeline='immediate',
            requires_approval=False
        )

        result = await decision_hub._execute_decision(decision)

        assert result['execution_status'] == 'completed'
        assert result['actions_executed'] == 2
        assert result['success_rate'] == 1.0

    @pytest.mark.asyncio
    async def test_execute_action(self, decision_hub):
        """Test single action execution"""
        action = {'type': 'scale_resources', 'parameters': {'replicas': 3}}

        result = await decision_hub._execute_action(action)

        assert result['success'] is True
        assert result['action_type'] == 'scale_resources'


class TestPhase4LangGraphWorkflowEngine:
    """Test LangGraphWorkflowEngine class"""

    @pytest.fixture
    def workflow_engine(self):
        from src.phases.phase4_meta_agent_api import LangGraphWorkflowEngine
        return LangGraphWorkflowEngine()

    @pytest.mark.asyncio
    async def test_create_workflow_with_name(self, workflow_engine):
        """Test workflow creation with name"""
        workflow_def = {
            'name': 'Test Workflow',
            'description': 'A test workflow'
        }

        result = await workflow_engine.create_workflow(workflow_def)

        assert result['status'] == 'created'
        assert 'workflow_id' in result
        assert result['node_count'] == 3  # default nodes

    @pytest.mark.asyncio
    async def test_create_workflow_with_custom_nodes(self, workflow_engine):
        """Test workflow creation with custom nodes"""
        workflow_def = {
            'name': 'Custom Workflow',
            'nodes': [
                {'id': 'start', 'type': 'input'},
                {'id': 'process1', 'type': 'processing'},
                {'id': 'process2', 'type': 'processing'},
                {'id': 'end', 'type': 'output'}
            ],
            'edges': [
                {'from': 'start', 'to': 'process1'},
                {'from': 'process1', 'to': 'process2'},
                {'from': 'process2', 'to': 'end'}
            ]
        }

        result = await workflow_engine.create_workflow(workflow_def)

        assert result['node_count'] == 4
        assert result['edge_count'] == 3

    @pytest.mark.asyncio
    async def test_create_workflow_with_workflow_type(self, workflow_engine):
        """Test workflow creation with workflow_type instead of name"""
        workflow_def = {
            'workflow_type': 'data_processing'
        }

        result = await workflow_engine.create_workflow(workflow_def)

        assert result['status'] == 'created'

    @pytest.mark.asyncio
    async def test_execute_workflow_success(self, workflow_engine):
        """Test successful workflow execution"""
        workflow_def = {'name': 'Test Workflow'}
        create_result = await workflow_engine.create_workflow(workflow_def)
        workflow_id = create_result['workflow_id']

        result = await workflow_engine.execute_workflow(workflow_id, {'input': 'test'})

        assert result['status'] == 'completed'
        assert result['workflow_id'] == workflow_id
        assert 'execution_id' in result

    @pytest.mark.asyncio
    async def test_execute_workflow_not_found(self, workflow_engine):
        """Test workflow execution with non-existent workflow"""
        result = await workflow_engine.execute_workflow('non-existent-id', {})

        assert 'error' in result
        assert result['error'] == 'Workflow not found'


class TestPhase4AIGovernanceConsole:
    """Test AIGovernanceConsole class"""

    @pytest.fixture
    def governance_console(self):
        from src.phases.phase4_meta_agent_api import AIGovernanceConsole
        return AIGovernanceConsole()

    @pytest.mark.asyncio
    async def test_get_governance_status(self, governance_console):
        """Test governance status retrieval"""
        result = await governance_console.get_governance_status()

        assert 'governance_score' in result
        assert 'compliance_status' in result
        assert 'risk_assessment' in result
        assert result['compliance_status'] == 'compliant'

    @pytest.mark.asyncio
    async def test_create_governance_policy(self, governance_console):
        """Test governance policy creation"""
        policy_data = {
            'name': 'Data Retention Policy',
            'description': 'Policy for data retention',
            'rules': ['rule1', 'rule2'],
            'enforcement_level': 'strict'
        }

        result = await governance_console.create_governance_policy(policy_data)

        assert result['status'] == 'created'
        assert 'policy_id' in result
        assert result['enforcement_level'] == 'strict'

    @pytest.mark.asyncio
    async def test_create_governance_policy_default_enforcement(self, governance_console):
        """Test governance policy creation with default enforcement"""
        policy_data = {
            'name': 'Basic Policy',
            'rules': ['rule1']
        }

        result = await governance_console.create_governance_policy(policy_data)

        assert result['enforcement_level'] == 'warning'


class TestPhase4APIFunctions:
    """Test Phase 4 API functions"""

    @pytest.mark.asyncio
    async def test_api_meta_agent_ooda_cycle(self):
        """Test api_meta_agent_ooda_cycle function"""
        from src.phases.phase4_meta_agent_api import api_meta_agent_ooda_cycle

        result = await api_meta_agent_ooda_cycle()

        assert result['status'] == 'completed'

    @pytest.mark.asyncio
    async def test_api_create_langgraph_workflow(self):
        """Test api_create_langgraph_workflow function"""
        from src.phases.phase4_meta_agent_api import api_create_langgraph_workflow

        result = await api_create_langgraph_workflow({'name': 'Test'})

        assert result['status'] == 'created'

    @pytest.mark.asyncio
    async def test_api_governance_status(self):
        """Test api_governance_status function"""
        from src.phases.phase4_meta_agent_api import api_governance_status

        result = await api_governance_status()

        assert 'governance_score' in result

    @pytest.mark.asyncio
    async def test_api_create_governance_policy(self):
        """Test api_create_governance_policy function"""
        from src.phases.phase4_meta_agent_api import api_create_governance_policy

        result = await api_create_governance_policy({
            'name': 'Test Policy',
            'rules': ['rule1']
        })

        assert result['status'] == 'created'


class TestPhase5QuickSightIntegration:
    """Test QuickSightIntegration class"""

    @pytest.fixture
    def quicksight(self):
        from src.phases.phase5_data_intelligence_api import QuickSightIntegration
        return QuickSightIntegration()

    @pytest.mark.asyncio
    async def test_create_dashboard(self, quicksight):
        """Test dashboard creation"""
        config = {
            'name': 'Test Dashboard',
            'type': 'analytics',
            'description': 'Test description'
        }

        result = await quicksight.create_dashboard(config)

        assert result['status'] == 'created'
        assert 'dashboard_id' in result
        assert 'url' in result

    @pytest.mark.asyncio
    async def test_create_dashboard_with_custom_sources(self, quicksight):
        """Test dashboard creation with custom data sources"""
        config = {
            'name': 'Custom Dashboard',
            'data_sources': ['source1', 'source2'],
            'visualizations': [
                {'type': 'line_chart', 'title': 'Chart 1'}
            ]
        }

        result = await quicksight.create_dashboard(config)

        assert result['data_source_count'] == 2
        assert result['visualization_count'] == 1

    @pytest.mark.asyncio
    async def test_get_dashboard_insights_success(self, quicksight):
        """Test getting dashboard insights"""
        create_result = await quicksight.create_dashboard({'name': 'Test'})
        dashboard_id = create_result['dashboard_id']

        result = await quicksight.get_dashboard_insights(dashboard_id)

        assert 'insights' in result
        assert result['insights_count'] == 2
        assert 'confidence_avg' in result

    @pytest.mark.asyncio
    async def test_get_dashboard_insights_not_found(self, quicksight):
        """Test getting insights for non-existent dashboard"""
        result = await quicksight.get_dashboard_insights('non-existent')

        assert 'error' in result
        assert result['error'] == 'Dashboard not found'

    @pytest.mark.asyncio
    async def test_generate_automated_report(self, quicksight):
        """Test automated report generation"""
        config = {
            'type': 'monthly_business_review'
        }

        result = await quicksight.generate_automated_report(config)

        assert result['status'] == 'generated'
        assert 'report_id' in result
        assert 'data' in result
        assert 'executive_summary' in result['data']


class TestPhase5GrowthMarketingEngine:
    """Test GrowthMarketingEngine class"""

    @pytest.fixture
    def growth_engine(self):
        from src.phases.phase5_data_intelligence_api import GrowthMarketingEngine
        return GrowthMarketingEngine()

    @pytest.mark.asyncio
    async def test_create_referral_program(self, growth_engine):
        """Test referral program creation"""
        config = {
            'name': 'Test Referral',
            'type': 'referral',
            'referrer_reward': 100,
            'referee_reward': 50
        }

        result = await growth_engine.create_referral_program(config)

        assert result['status'] == 'created'
        assert 'program_id' in result
        assert 'tracking_code' in result

    @pytest.mark.asyncio
    async def test_create_referral_program_with_rewards_dict(self, growth_engine):
        """Test referral program creation with rewards dict"""
        config = {
            'name': 'Test Referral',
            'rewards': {
                'referrer': 200,
                'referee': 100
            }
        }

        result = await growth_engine.create_referral_program(config)

        assert result['referrer_reward'] == 200
        assert result['referee_reward'] == 100

    @pytest.mark.asyncio
    async def test_create_referral_program_with_target(self, growth_engine):
        """Test referral program creation with target audience"""
        config = {
            'name': 'Test Referral',
            'target': 'premium_users'
        }

        result = await growth_engine.create_referral_program(config)

        assert result['status'] == 'created'

    @pytest.mark.asyncio
    async def test_get_referral_analytics_success(self, growth_engine):
        """Test getting referral analytics"""
        create_result = await growth_engine.create_referral_program({'name': 'Test'})
        program_id = create_result['program_id']

        result = await growth_engine.get_referral_analytics(program_id)

        assert 'total_referrals' in result
        assert 'conversion_rate' in result
        assert 'roi' in result

    @pytest.mark.asyncio
    async def test_get_referral_analytics_not_found(self, growth_engine):
        """Test getting analytics for non-existent program"""
        result = await growth_engine.get_referral_analytics('non-existent')

        assert 'error' in result

    @pytest.mark.asyncio
    async def test_generate_marketing_content_email(self, growth_engine):
        """Test email marketing content generation"""
        request = {
            'type': 'email',
            'target_audience': 'enterprise'
        }

        result = await growth_engine.generate_marketing_content(request)

        assert result['type'] == 'email'
        assert 'content' in result
        assert 'subject' in result['content']

    @pytest.mark.asyncio
    async def test_generate_marketing_content_social_media(self, growth_engine):
        """Test social media content generation"""
        request = {
            'type': 'social_media',
            'target_audience': 'startups'
        }

        result = await growth_engine.generate_marketing_content(request)

        assert result['type'] == 'social_media'
        assert 'content' in result

    @pytest.mark.asyncio
    async def test_generate_marketing_content_blog_post(self, growth_engine):
        """Test blog post content generation"""
        request = {
            'type': 'blog_post',
            'target_audience': 'developers'
        }

        result = await growth_engine.generate_marketing_content(request)

        assert result['type'] == 'blog_post'
        assert 'title' in result['content']


class TestPhase5DataIntelligencePlatform:
    """Test DataIntelligencePlatform class"""

    @pytest.fixture
    def data_platform(self):
        from src.phases.phase5_data_intelligence_api import DataIntelligencePlatform
        return DataIntelligencePlatform()

    @pytest.mark.asyncio
    async def test_get_business_intelligence_summary(self, data_platform):
        """Test business intelligence summary"""
        result = await data_platform.get_business_intelligence_summary()

        assert 'summary' in result
        assert 'key_metrics' in result
        assert 'insights' in result
        assert 'recommendations' in result

    @pytest.mark.asyncio
    async def test_collect_user_metrics(self, data_platform):
        """Test user metrics collection"""
        result = await data_platform._collect_user_metrics()

        assert 'total_users' in result
        assert 'daily_active_users' in result
        assert 'user_retention_7d' in result

    @pytest.mark.asyncio
    async def test_collect_revenue_metrics(self, data_platform):
        """Test revenue metrics collection"""
        result = await data_platform._collect_revenue_metrics()

        assert 'monthly_revenue' in result
        assert 'average_revenue_per_user' in result
        assert 'customer_lifetime_value' in result

    @pytest.mark.asyncio
    async def test_collect_growth_metrics(self, data_platform):
        """Test growth metrics collection"""
        result = await data_platform._collect_growth_metrics()

        assert 'user_growth_rate' in result
        assert 'revenue_growth_rate' in result
        assert 'viral_coefficient' in result

    @pytest.mark.asyncio
    async def test_generate_business_insights(self, data_platform):
        """Test business insights generation"""
        user_metrics = {'total_users': 15000}
        revenue_metrics = {'churn_rate': 0.02}
        growth_metrics = {
            'user_growth_rate': 0.20,
            'customer_acquisition_cost': 25.0
        }

        result = await data_platform._generate_business_insights(
            user_metrics, revenue_metrics, growth_metrics
        )

        assert len(result) > 0
        assert result[0]['type'] == 'growth_opportunity'


class TestPhase5APIFunctions:
    """Test Phase 5 API functions"""

    @pytest.mark.asyncio
    async def test_api_create_quicksight_dashboard(self):
        """Test api_create_quicksight_dashboard function"""
        from src.phases.phase5_data_intelligence_api import api_create_quicksight_dashboard

        result = await api_create_quicksight_dashboard({'name': 'Test'})

        assert result['status'] == 'created'

    @pytest.mark.asyncio
    async def test_api_generate_automated_report(self):
        """Test api_generate_automated_report function"""
        from src.phases.phase5_data_intelligence_api import api_generate_automated_report

        result = await api_generate_automated_report({'type': 'monthly'})

        assert result['status'] == 'generated'

    @pytest.mark.asyncio
    async def test_api_create_referral_program(self):
        """Test api_create_referral_program function"""
        from src.phases.phase5_data_intelligence_api import api_create_referral_program

        result = await api_create_referral_program({'name': 'Test'})

        assert result['status'] == 'created'

    @pytest.mark.asyncio
    async def test_api_generate_marketing_content(self):
        """Test api_generate_marketing_content function"""
        from src.phases.phase5_data_intelligence_api import api_generate_marketing_content

        result = await api_generate_marketing_content({'type': 'email'})

        assert 'content' in result

    @pytest.mark.asyncio
    async def test_api_get_business_intelligence(self):
        """Test api_get_business_intelligence function"""
        from src.phases.phase5_data_intelligence_api import api_get_business_intelligence

        result = await api_get_business_intelligence()

        assert 'summary' in result


class TestPhase6ZeroTrustSecurityModel:
    """Test ZeroTrustSecurityModel class"""

    @pytest.fixture
    def zero_trust(self):
        from src.phases.phase6_security_governance_api import ZeroTrustSecurityModel
        return ZeroTrustSecurityModel()

    @pytest.mark.asyncio
    async def test_evaluate_access_request_allow(self, zero_trust):
        """Test access request evaluation - allow"""
        request = {
            'user_id': 'user_001',
            'resource': 'public_data',
            'action': 'read',
            'context': {
                'device_known': True,
                'location_trusted': True,
                'time_normal_hours': True
            }
        }

        zero_trust.trust_scores['user_001'] = 0.9

        result = await zero_trust.evaluate_access_request(request)

        assert 'decision' in result
        assert 'trust_score' in result
        assert 'risk_assessment' in result

    @pytest.mark.asyncio
    async def test_evaluate_access_request_deny(self, zero_trust):
        """Test access request evaluation - deny"""
        request = {
            'user': 'unknown_user',
            'resource': 'sensitive_admin_data',
            'action': 'delete',
            'context': {
                'device_known': False,
                'location_trusted': False,
                'time_normal_hours': False
            }
        }

        result = await zero_trust.evaluate_access_request(request)

        assert result['decision'] == 'deny'

    @pytest.mark.asyncio
    async def test_calculate_trust_score_with_history(self, zero_trust):
        """Test trust score calculation with historical data"""
        zero_trust.trust_scores['user_001'] = 0.8

        context = {
            'device_known': True,
            'location_trusted': True,
            'time_normal_hours': True
        }

        score = await zero_trust._calculate_trust_score('user_001', context)

        assert 0.0 <= score <= 1.0

    @pytest.mark.asyncio
    async def test_calculate_trust_score_off_hours(self, zero_trust):
        """Test trust score calculation during off hours"""
        context = {
            'device_known': False,
            'location_trusted': False,
            'time_normal_hours': False
        }

        score = await zero_trust._calculate_trust_score('new_user', context)

        assert score < 0.5

    @pytest.mark.asyncio
    async def test_assess_risk_sensitive_resource(self, zero_trust):
        """Test risk assessment for sensitive resource"""
        result = await zero_trust._assess_risk(
            'user_001', 'sensitive_database', 'delete', {}
        )

        assert result['risk_score'] > 0.3
        assert 'High-sensitivity resource' in result['risk_factors']
        assert 'High-risk action' in result['risk_factors']

    @pytest.mark.asyncio
    async def test_assess_risk_admin_resource(self, zero_trust):
        """Test risk assessment for admin resource"""
        result = await zero_trust._assess_risk(
            'user_001', 'admin_panel', 'modify', {}
        )

        assert 'High-sensitivity resource' in result['risk_factors']

    @pytest.mark.asyncio
    async def test_assess_risk_untrusted_context(self, zero_trust):
        """Test risk assessment with untrusted context"""
        context = {
            'location_trusted': False,
            'device_known': False
        }

        result = await zero_trust._assess_risk(
            'user_001', 'data', 'read', context
        )

        assert 'Untrusted location' in result['risk_factors']
        assert 'Unknown device' in result['risk_factors']

    def test_get_risk_level_critical(self, zero_trust):
        """Test risk level - critical"""
        assert zero_trust._get_risk_level(0.9) == 'critical'

    def test_get_risk_level_high(self, zero_trust):
        """Test risk level - high"""
        assert zero_trust._get_risk_level(0.7) == 'high'

    def test_get_risk_level_medium(self, zero_trust):
        """Test risk level - medium"""
        assert zero_trust._get_risk_level(0.4) == 'medium'

    def test_get_risk_level_low(self, zero_trust):
        """Test risk level - low"""
        assert zero_trust._get_risk_level(0.2) == 'low'

    @pytest.mark.asyncio
    async def test_make_access_decision_high_trust_low_risk(self, zero_trust):
        """Test access decision - high trust, low risk"""
        result = await zero_trust._make_access_decision(
            0.9, {'risk_score': 0.1}
        )

        assert result['decision'] == 'allow'
        assert 'additional_verification' not in result or not result.get('additional_verification')

    @pytest.mark.asyncio
    async def test_make_access_decision_medium_trust(self, zero_trust):
        """Test access decision - medium trust"""
        result = await zero_trust._make_access_decision(
            0.7, {'risk_score': 0.3}
        )

        assert result['decision'] == 'allow'
        assert result['additional_verification'] is True
        assert 'mfa_required' in result['conditions']

    @pytest.mark.asyncio
    async def test_make_access_decision_conditional(self, zero_trust):
        """Test access decision - conditional allow"""
        result = await zero_trust._make_access_decision(
            0.5, {'risk_score': 0.5}
        )

        assert result['decision'] == 'conditional_allow'
        assert 'manager_approval' in result['conditions']


class TestPhase6SecurityReviewerAgent:
    """Test SecurityReviewerAgent class"""

    @pytest.fixture
    def security_reviewer(self):
        from src.phases.phase6_security_governance_api import SecurityReviewerAgent
        return SecurityReviewerAgent()

    @pytest.fixture
    def security_event(self):
        from src.phases.phase6_security_governance_api import (
            SecurityEvent, SecurityLevel, ThreatType
        )
        return SecurityEvent(
            event_id='evt_001',
            timestamp=datetime.now(),
            event_type=ThreatType.UNAUTHORIZED_ACCESS,
            severity=SecurityLevel.HIGH,
            source_ip='192.168.1.100',
            user_id='user_001',
            description='Multiple failed login attempts',
            risk_score=0.85,
            requires_human_review=False
        )

    @pytest.mark.asyncio
    async def test_review_security_event(self, security_reviewer, security_event):
        """Test security event review"""
        result = await security_reviewer.review_security_event(security_event)

        assert 'review_id' in result
        assert 'initial_analysis' in result
        assert 'recommendations' in result

    @pytest.mark.asyncio
    async def test_review_security_event_critical(self, security_reviewer):
        """Test critical security event review"""
        from src.phases.phase6_security_governance_api import (
            SecurityEvent, SecurityLevel, ThreatType
        )

        event = SecurityEvent(
            event_id='evt_002',
            timestamp=datetime.now(),
            event_type=ThreatType.DATA_BREACH,
            severity=SecurityLevel.CRITICAL,
            source_ip='10.0.0.1',
            user_id=None,
            description='Data exfiltration detected',
            risk_score=0.95,
            requires_human_review=True
        )

        result = await security_reviewer.review_security_event(event)

        assert result['requires_human_intervention'] is True

    @pytest.mark.asyncio
    async def test_perform_initial_analysis(self, security_reviewer, security_event):
        """Test initial analysis"""
        result = await security_reviewer._perform_initial_analysis(security_event)

        assert 'threat_classification' in result
        assert 'severity_assessment' in result
        assert 'confidence' in result

    @pytest.mark.asyncio
    async def test_is_known_attack_pattern_true(self, security_reviewer):
        """Test known attack pattern detection - true"""
        from src.phases.phase6_security_governance_api import (
            SecurityEvent, SecurityLevel, ThreatType
        )

        event = SecurityEvent(
            event_id='evt_003',
            timestamp=datetime.now(),
            event_type=ThreatType.MALICIOUS_ACTIVITY,
            severity=SecurityLevel.HIGH,
            source_ip='10.0.0.1',
            user_id=None,
            description='sql_injection_attempt detected in request',
            risk_score=0.9,
            requires_human_review=False
        )

        result = await security_reviewer._is_known_attack_pattern(event)

        assert result is True

    @pytest.mark.asyncio
    async def test_is_known_attack_pattern_false(self, security_reviewer, security_event):
        """Test known attack pattern detection - false"""
        result = await security_reviewer._is_known_attack_pattern(security_event)

        assert result is False

    @pytest.mark.asyncio
    async def test_requires_human_intervention_critical(self, security_reviewer):
        """Test human intervention required for critical events"""
        from src.phases.phase6_security_governance_api import (
            SecurityEvent, SecurityLevel, ThreatType
        )

        event = SecurityEvent(
            event_id='evt_004',
            timestamp=datetime.now(),
            event_type=ThreatType.DATA_BREACH,
            severity=SecurityLevel.CRITICAL,
            source_ip='10.0.0.1',
            user_id=None,
            description='Critical breach',
            risk_score=0.95,
            requires_human_review=True
        )

        analysis = {'confidence': 0.9, 'false_positive_probability': 0.1}

        result = await security_reviewer._requires_human_intervention(event, analysis)

        assert result is True

    @pytest.mark.asyncio
    async def test_requires_human_intervention_low_confidence(self, security_reviewer, security_event):
        """Test human intervention required for low confidence"""
        analysis = {'confidence': 0.5, 'false_positive_probability': 0.1}

        result = await security_reviewer._requires_human_intervention(security_event, analysis)

        assert result is True

    @pytest.mark.asyncio
    async def test_requires_human_intervention_high_false_positive(self, security_reviewer, security_event):
        """Test human intervention required for high false positive probability"""
        analysis = {'confidence': 0.9, 'false_positive_probability': 0.4}

        result = await security_reviewer._requires_human_intervention(security_event, analysis)

        assert result is True

    @pytest.mark.asyncio
    async def test_execute_automated_response_unauthorized_access(self, security_reviewer, security_event):
        """Test automated response for unauthorized access"""
        analysis = {'confidence': 0.9}

        result = await security_reviewer._execute_automated_response(security_event, analysis)

        assert len(result) > 0
        assert any(a['action'] == 'block_ip' for a in result)
        assert any(a['action'] == 'suspend_user_session' for a in result)

    @pytest.mark.asyncio
    async def test_execute_automated_response_malicious_activity(self, security_reviewer):
        """Test automated response for malicious activity"""
        from src.phases.phase6_security_governance_api import (
            SecurityEvent, SecurityLevel, ThreatType
        )

        event = SecurityEvent(
            event_id='evt_005',
            timestamp=datetime.now(),
            event_type=ThreatType.MALICIOUS_ACTIVITY,
            severity=SecurityLevel.HIGH,
            source_ip='10.0.0.1',
            user_id=None,
            description='Malicious activity',
            risk_score=0.85,
            requires_human_review=False
        )

        result = await security_reviewer._execute_automated_response(event, {})

        assert any(a['action'] == 'quarantine_resource' for a in result)

    @pytest.mark.asyncio
    async def test_generate_recommendations(self, security_reviewer, security_event):
        """Test recommendations generation"""
        analysis = {'false_positive_probability': 0.3}

        result = await security_reviewer._generate_recommendations(security_event, analysis)

        assert len(result) > 0
        assert 'Monitor for similar events' in result[-1]


class TestPhase6HITLSecurityAnalysis:
    """Test HITLSecurityAnalysis class"""

    @pytest.fixture
    def hitl_analysis(self):
        from src.phases.phase6_security_governance_api import HITLSecurityAnalysis
        return HITLSecurityAnalysis()

    @pytest.fixture
    def security_event(self):
        from src.phases.phase6_security_governance_api import (
            SecurityEvent, SecurityLevel, ThreatType
        )
        return SecurityEvent(
            event_id='evt_001',
            timestamp=datetime.now(),
            event_type=ThreatType.DATA_BREACH,
            severity=SecurityLevel.CRITICAL,
            source_ip='10.0.0.1',
            user_id='user_001',
            description='Data breach detected',
            risk_score=0.95,
            requires_human_review=True
        )

    @pytest.mark.asyncio
    async def test_submit_for_human_review(self, hitl_analysis, security_event):
        """Test submitting event for human review"""
        ai_analysis = {'confidence': 0.8}

        result = await hitl_analysis.submit_for_human_review(security_event, ai_analysis)

        assert result['status'] == 'submitted'
        assert 'request_id' in result
        assert 'queue_position' in result
        assert result['priority'] == 'urgent'

    def test_calculate_review_priority_critical(self, hitl_analysis):
        """Test review priority calculation - critical"""
        from src.phases.phase6_security_governance_api import (
            SecurityEvent, SecurityLevel, ThreatType
        )

        event = SecurityEvent(
            event_id='evt_001',
            timestamp=datetime.now(),
            event_type=ThreatType.DATA_BREACH,
            severity=SecurityLevel.CRITICAL,
            source_ip='10.0.0.1',
            user_id=None,
            description='Critical',
            risk_score=0.95,
            requires_human_review=True
        )

        result = hitl_analysis._calculate_review_priority(event)

        assert result == 'urgent'

    def test_calculate_review_priority_high(self, hitl_analysis):
        """Test review priority calculation - high"""
        from src.phases.phase6_security_governance_api import (
            SecurityEvent, SecurityLevel, ThreatType
        )

        event = SecurityEvent(
            event_id='evt_002',
            timestamp=datetime.now(),
            event_type=ThreatType.UNAUTHORIZED_ACCESS,
            severity=SecurityLevel.HIGH,
            source_ip='10.0.0.1',
            user_id=None,
            description='High',
            risk_score=0.8,
            requires_human_review=True
        )

        result = hitl_analysis._calculate_review_priority(event)

        assert result == 'high'

    def test_calculate_review_priority_medium(self, hitl_analysis):
        """Test review priority calculation - medium"""
        from src.phases.phase6_security_governance_api import (
            SecurityEvent, SecurityLevel, ThreatType
        )

        event = SecurityEvent(
            event_id='evt_003',
            timestamp=datetime.now(),
            event_type=ThreatType.ANOMALOUS_BEHAVIOR,
            severity=SecurityLevel.MEDIUM,
            source_ip='10.0.0.1',
            user_id=None,
            description='Medium',
            risk_score=0.5,
            requires_human_review=True
        )

        result = hitl_analysis._calculate_review_priority(event)

        assert result == 'medium'

    def test_estimate_review_time_critical(self, hitl_analysis):
        """Test review time estimation - critical"""
        from src.phases.phase6_security_governance_api import (
            SecurityEvent, SecurityLevel, ThreatType
        )

        event = SecurityEvent(
            event_id='evt_001',
            timestamp=datetime.now(),
            event_type=ThreatType.DATA_BREACH,
            severity=SecurityLevel.CRITICAL,
            source_ip='10.0.0.1',
            user_id=None,
            description='Critical',
            risk_score=0.95,
            requires_human_review=True
        )

        result = hitl_analysis._estimate_review_time(event)

        assert result == '15 minutes'

    def test_estimate_review_time_high(self, hitl_analysis):
        """Test review time estimation - high"""
        from src.phases.phase6_security_governance_api import (
            SecurityEvent, SecurityLevel, ThreatType
        )

        event = SecurityEvent(
            event_id='evt_002',
            timestamp=datetime.now(),
            event_type=ThreatType.UNAUTHORIZED_ACCESS,
            severity=SecurityLevel.HIGH,
            source_ip='10.0.0.1',
            user_id=None,
            description='High',
            risk_score=0.8,
            requires_human_review=True
        )

        result = hitl_analysis._estimate_review_time(event)

        assert result == '1 hour'

    @pytest.mark.asyncio
    async def test_get_pending_reviews(self, hitl_analysis, security_event):
        """Test getting pending reviews"""
        ai_analysis = {'confidence': 0.8}
        await hitl_analysis.submit_for_human_review(security_event, ai_analysis)

        result = await hitl_analysis.get_pending_reviews()

        assert 'total_pending' in result
        assert 'urgent_count' in result
        assert 'pending_reviews' in result


class TestPhase6SecurityAuditSystem:
    """Test SecurityAuditSystem class"""

    @pytest.fixture
    def audit_system(self):
        from src.phases.phase6_security_governance_api import SecurityAuditSystem
        return SecurityAuditSystem()

    @pytest.mark.asyncio
    async def test_perform_security_audit(self, audit_system):
        """Test security audit execution"""
        scope = {
            'scope': 'comprehensive',
            'systems': ['web', 'database']
        }

        result = await audit_system.perform_security_audit(scope)

        assert 'audit_id' in result
        assert 'findings' in result
        assert 'overall_score' in result
        assert 'recommendations' in result

    @pytest.mark.asyncio
    async def test_audit_access_controls(self, audit_system):
        """Test access controls audit"""
        result = await audit_system._audit_access_controls()

        assert 'score' in result
        assert 'checks_performed' in result
        assert 'passed' in result
        assert 'failed' in result

    @pytest.mark.asyncio
    async def test_audit_data_protection(self, audit_system):
        """Test data protection audit"""
        result = await audit_system._audit_data_protection()

        assert 'score' in result
        assert result['score'] == 92.0

    @pytest.mark.asyncio
    async def test_audit_policy_compliance(self, audit_system):
        """Test policy compliance audit"""
        result = await audit_system._audit_policy_compliance()

        assert 'score' in result
        assert 'issues' in result

    def test_calculate_overall_score(self, audit_system):
        """Test overall score calculation"""
        scores = [85.0, 90.0, 95.0]

        result = audit_system._calculate_overall_score(scores)

        assert result == 90.0

    @pytest.mark.asyncio
    async def test_generate_audit_recommendations(self, audit_system):
        """Test audit recommendations generation"""
        findings = {
            'access_control': {
                'score': 85.0,
                'recommendations': ['Review permissions']
            },
            'data_protection': {
                'score': 95.0,
                'recommendations': []
            }
        }

        result = await audit_system._generate_audit_recommendations(findings)

        assert len(result) > 0
        assert 'Review permissions' in result


class TestPhase6APIFunctions:
    """Test Phase 6 API functions"""

    @pytest.mark.asyncio
    async def test_api_evaluate_access_request(self):
        """Test api_evaluate_access_request function"""
        from src.phases.phase6_security_governance_api import api_evaluate_access_request

        result = await api_evaluate_access_request({
            'user_id': 'user_001',
            'resource': 'data',
            'action': 'read'
        })

        assert 'decision' in result

    @pytest.mark.asyncio
    async def test_api_review_security_event_dict(self):
        """Test api_review_security_event with dict input"""
        from src.phases.phase6_security_governance_api import api_review_security_event

        event_data = {
            'event_id': 'evt_001',
            'event_type': 'unauthorized_access',
            'severity': 'high',
            'source_ip': '10.0.0.1',
            'user_id': 'user_001',
            'description': 'Test event',
            'risk_score': 0.7
        }

        result = await api_review_security_event(event_data)

        assert 'review_id' in result

    @pytest.mark.asyncio
    async def test_api_review_security_event_with_details(self):
        """Test api_review_security_event with details"""
        from src.phases.phase6_security_governance_api import api_review_security_event

        event_data = {
            'event_type': 'suspicious_login',
            'severity': 'medium',
            'details': {
                'failed_attempts': 5,
                'unusual_location': True,
                'device_fingerprint': 'unknown'
            }
        }

        result = await api_review_security_event(event_data)

        assert 'review_id' in result

    @pytest.mark.asyncio
    async def test_api_submit_hitl_review(self):
        """Test api_submit_hitl_review function"""
        from src.phases.phase6_security_governance_api import api_submit_hitl_review

        request_data = {
            'event_data': {
                'event_id': 'evt_001',
                'event_type': 'data_breach',
                'severity': 'critical',
                'description': 'Test breach'
            },
            'ai_analysis': {
                'risk_score': 0.9,
                'threat_indicators': ['indicator1', 'indicator2', 'indicator3']
            }
        }

        result = await api_submit_hitl_review(request_data)

        assert result['status'] == 'submitted'

    @pytest.mark.asyncio
    async def test_api_submit_hitl_review_with_affected_resources(self):
        """Test api_submit_hitl_review with affected resources"""
        from src.phases.phase6_security_governance_api import api_submit_hitl_review

        request_data = {
            'event_id': 'evt_002',
            'event_type': 'data_breach',
            'severity': 'high',
            'affected_resources': ['database1', 'database2']
        }

        result = await api_submit_hitl_review(request_data)

        assert result['status'] == 'submitted'

    @pytest.mark.asyncio
    async def test_api_get_pending_reviews(self):
        """Test api_get_pending_reviews function"""
        from src.phases.phase6_security_governance_api import api_get_pending_reviews

        result = await api_get_pending_reviews()

        assert 'total_pending' in result

    @pytest.mark.asyncio
    async def test_api_perform_security_audit(self):
        """Test api_perform_security_audit function"""
        from src.phases.phase6_security_governance_api import api_perform_security_audit

        result = await api_perform_security_audit({'scope': 'full'})

        assert 'audit_id' in result


class TestPhase6Enums:
    """Test Phase 6 enums"""

    def test_security_level_values(self):
        """Test SecurityLevel enum values"""
        from src.phases.phase6_security_governance_api import SecurityLevel

        assert SecurityLevel.LOW.value == 'low'
        assert SecurityLevel.MEDIUM.value == 'medium'
        assert SecurityLevel.HIGH.value == 'high'
        assert SecurityLevel.CRITICAL.value == 'critical'

    def test_threat_type_values(self):
        """Test ThreatType enum values"""
        from src.phases.phase6_security_governance_api import ThreatType

        assert ThreatType.UNAUTHORIZED_ACCESS.value == 'unauthorized_access'
        assert ThreatType.DATA_BREACH.value == 'data_breach'
        assert ThreatType.MALICIOUS_ACTIVITY.value == 'malicious_activity'


class TestPhase4Enums:
    """Test Phase 4 enums"""

    def test_decision_priority_values(self):
        """Test DecisionPriority enum values"""
        from src.phases.phase4_meta_agent_api import DecisionPriority

        assert DecisionPriority.CRITICAL.value == 'critical'
        assert DecisionPriority.HIGH.value == 'high'
        assert DecisionPriority.MEDIUM.value == 'medium'
        assert DecisionPriority.LOW.value == 'low'

    def test_agent_role_values(self):
        """Test AgentRole enum values"""
        from src.phases.phase4_meta_agent_api import AgentRole

        assert AgentRole.META_AGENT.value == 'meta_agent'
        assert AgentRole.OPS_AGENT.value == 'ops_agent'
        assert AgentRole.DEV_AGENT.value == 'dev_agent'


class TestPhase5Dataclasses:
    """Test Phase 5 dataclasses"""

    def test_data_insight_creation(self):
        """Test DataInsight dataclass"""
        from src.phases.phase5_data_intelligence_api import DataInsight

        insight = DataInsight(
            insight_id='ins_001',
            category='user_behavior',
            title='Test Insight',
            description='Test description',
            confidence=0.9,
            impact_score=8.5,
            recommended_actions=['action1', 'action2']
        )

        assert insight.insight_id == 'ins_001'
        assert insight.confidence == 0.9

    def test_growth_metric_creation(self):
        """Test GrowthMetric dataclass"""
        from src.phases.phase5_data_intelligence_api import GrowthMetric

        metric = GrowthMetric(
            metric_name='user_growth',
            current_value=1000,
            previous_value=800,
            growth_rate=0.25,
            trend='up',
            target_value=1200
        )

        assert metric.metric_name == 'user_growth'
        assert metric.growth_rate == 0.25


class TestPhase4Dataclasses:
    """Test Phase 4 dataclasses"""

    def test_ooda_context_creation(self):
        """Test OODAContext dataclass"""
        from src.phases.phase4_meta_agent_api import OODAContext

        context = OODAContext(
            observation_id='obs_001',
            timestamp=datetime.now(),
            system_metrics={'cpu': 50},
            business_metrics={'revenue': 1000},
            situation_assessment={'status': 'ok'},
            decision_required=False
        )

        assert context.observation_id == 'obs_001'
        assert context.decision_required is False

    def test_decision_result_creation(self):
        """Test DecisionResult dataclass"""
        from src.phases.phase4_meta_agent_api import DecisionResult

        result = DecisionResult(
            decision_id='dec_001',
            strategy='optimization',
            actions=[{'type': 'scale'}],
            confidence=0.9,
            risk_assessment=0.1,
            execution_timeline='immediate',
            requires_approval=False
        )

        assert result.decision_id == 'dec_001'
        assert result.requires_approval is False


class TestPhase6Dataclasses:
    """Test Phase 6 dataclasses"""

    def test_security_event_creation(self):
        """Test SecurityEvent dataclass"""
        from src.phases.phase6_security_governance_api import (
            SecurityEvent, SecurityLevel, ThreatType
        )

        event = SecurityEvent(
            event_id='evt_001',
            timestamp=datetime.now(),
            event_type=ThreatType.UNAUTHORIZED_ACCESS,
            severity=SecurityLevel.HIGH,
            source_ip='10.0.0.1',
            user_id='user_001',
            description='Test event',
            risk_score=0.8,
            requires_human_review=True
        )

        assert event.event_id == 'evt_001'
        assert event.severity == SecurityLevel.HIGH

    def test_zero_trust_policy_creation(self):
        """Test ZeroTrustPolicy dataclass"""
        from src.phases.phase6_security_governance_api import ZeroTrustPolicy

        policy = ZeroTrustPolicy(
            policy_id='pol_001',
            name='Test Policy',
            description='Test description',
            rules=[{'rule': 'test'}],
            enforcement_level='strict',
            created_at=datetime.now(),
            status='active'
        )

        assert policy.policy_id == 'pol_001'
        assert policy.enforcement_level == 'strict'
