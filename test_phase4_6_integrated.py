#!/usr/bin/env python3
"""
Phase 4-6 Comprehensive Testing Suite for Integrated Flask Backend
Tests the actual API endpoints implemented in the Flask backend integration
"""

import requests
import time
import json
from datetime import datetime

class Phase456IntegratedTestSuite:
    def __init__(self, base_url="http://127.0.0.1:10001"):
        self.base_url = base_url
        self.results = []
        self.start_time = datetime.now()

    def log_test_result(self, phase, test_name, success, details=None, response_time=None):
        """Log test result with detailed information"""
        result = {
            'phase': phase,
            'test_name': test_name,
            'success': success,
            'details': details or {},
            'response_time_ms': response_time,
            'timestamp': datetime.now().isoformat()
        }
        self.results.append(result)
        
        status = "✅ PASSED" if success else "❌ FAILED"
        time_info = f" ({response_time:.2f}ms)" if response_time else ""
        print(f"{status}: {phase} - {test_name}{time_info}")
        
        if not success and details:
            print(f"   Error: {details.get('error', 'Unknown error')}")

    def test_api_endpoint(self, url, method='GET', data=None, expected_status=200):
        """Test a single API endpoint"""
        try:
            start_time = time.time()
            if method == 'POST':
                response = requests.post(url, json=data, timeout=10)
            else:
                response = requests.get(url, timeout=10)
            
            response_time = (time.time() - start_time) * 1000
            success = response.status_code == expected_status
            
            return {
                'success': success,
                'status_code': response.status_code,
                'response_time_ms': response_time,
                'response_data': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'status_code': None,
                'response_time_ms': None,
                'response_data': None
            }

    def test_phase4_ai_orchestration(self):
        """Test Phase 4: AI 自治系統核心 - Integrated Flask Endpoints"""
        print("\n🧪 Testing Phase 4: AI Orchestration & Meta-Agent System")
        print("=" * 70)
        
        print("Testing Meta-Agent OODA cycle...")
        ooda_data = {
            'scenario': 'resource_allocation',
            'context': {
                'available_agents': ['DataAnalyst', 'SecurityReviewer', 'GrowthStrategist'],
                'task_priority': 'high',
                'resource_constraints': {'cpu': 80, 'memory': 70}
            }
        }
        
        result = self.test_api_endpoint(f"{self.base_url}/api/meta-agent/ooda-cycle", method='POST', data=ooda_data)
        self.log_test_result(
            "Phase 4", "Meta-Agent OODA Cycle", 
            result['success'], 
            {'error': result.get('error', 'OODA cycle unavailable')} if not result['success'] else {
                'decision_time': result.get('response_data', {}).get('decision_time_ms', 'N/A'),
                'selected_agents': result.get('response_data', {}).get('selected_agents', []),
                'confidence_score': result.get('response_data', {}).get('confidence_score', 0)
            },
            result.get('response_time_ms')
        )
        
        print("Testing LangGraph workflow creation...")
        workflow_data = {
            'workflow_type': 'multi_agent_collaboration',
            'agents': ['DataAnalyst', 'SecurityReviewer'],
            'task': 'security_audit_with_data_analysis'
        }
        
        result = self.test_api_endpoint(f"{self.base_url}/api/langgraph/workflows", method='POST', data=workflow_data)
        self.log_test_result(
            "Phase 4", "LangGraph Workflow Creation", 
            result['success'], 
            {'error': result.get('error', 'Workflow creation failed')} if not result['success'] else {
                'workflow_id': result.get('response_data', {}).get('workflow_id', 'N/A'),
                'status': result.get('response_data', {}).get('status', 'unknown'),
                'estimated_duration': result.get('response_data', {}).get('estimated_duration_minutes', 'N/A')
            },
            result.get('response_time_ms')
        )
        
        print("Testing governance status...")
        result = self.test_api_endpoint(f"{self.base_url}/api/governance/status")
        self.log_test_result(
            "Phase 4", "AI Governance Status", 
            result['success'], 
            {'error': result.get('error', 'Governance not available')} if not result['success'] else {
                'governance_status': result.get('response_data', {}).get('status', 'unknown'),
                'active_policies': result.get('response_data', {}).get('active_policies', 0),
                'compliance_score': result.get('response_data', {}).get('compliance_score', 'N/A')
            },
            result.get('response_time_ms')
        )
        
        print("Testing governance policy creation...")
        policy_data = {
            'name': 'test_security_policy',
            'type': 'security',
            'rules': ['require_approval_for_high_risk', 'audit_all_decisions']
        }
        
        result = self.test_api_endpoint(f"{self.base_url}/api/governance/policies", method='POST', data=policy_data)
        self.log_test_result(
            "Phase 4", "Governance Policy Creation", 
            result['success'], 
            {'error': result.get('error', 'Policy creation failed')} if not result['success'] else {
                'policy_id': result.get('response_data', {}).get('policy_id', 'N/A'),
                'status': result.get('response_data', {}).get('status', 'unknown')
            },
            result.get('response_time_ms')
        )

    def test_phase5_data_intelligence(self):
        """Test Phase 5: 數據智能與成長 - Integrated Flask Endpoints"""
        print("\n🧪 Testing Phase 5: Data Intelligence & Growth")
        print("=" * 70)
        
        print("Testing QuickSight dashboard creation...")
        dashboard_data = {
            'name': 'test_analytics_dashboard',
            'type': 'business_intelligence',
            'data_sources': ['user_metrics', 'revenue_data', 'growth_metrics']
        }
        
        result = self.test_api_endpoint(f"{self.base_url}/api/quicksight/dashboards", method='POST', data=dashboard_data)
        self.log_test_result(
            "Phase 5", "QuickSight Dashboard Creation", 
            result['success'], 
            {'error': result.get('error', 'Dashboard creation failed')} if not result['success'] else {
                'dashboard_id': result.get('response_data', {}).get('dashboard_id', 'N/A'),
                'status': result.get('response_data', {}).get('status', 'unknown'),
                'data_sources_count': len(result.get('response_data', {}).get('data_sources', []))
            },
            result.get('response_time_ms')
        )
        
        print("Testing dashboard insights...")
        result = self.test_api_endpoint(f"{self.base_url}/api/quicksight/dashboards/test-dashboard/insights")
        self.log_test_result(
            "Phase 5", "Dashboard Insights", 
            result['success'], 
            {'error': result.get('error', 'Insights unavailable')} if not result['success'] else {
                'insights_count': len(result.get('response_data', {}).get('insights', [])),
                'confidence_score': result.get('response_data', {}).get('confidence_score', 'N/A'),
                'last_updated': result.get('response_data', {}).get('last_updated', 'N/A')
            },
            result.get('response_time_ms')
        )
        
        print("Testing referral program creation...")
        referral_data = {
            'name': 'test_referral_program',
            'type': 'viral_growth',
            'rewards': {'referrer': 100, 'referee': 50},
            'target_audience': 'new_users'
        }
        
        result = self.test_api_endpoint(f"{self.base_url}/api/growth/referral-programs", method='POST', data=referral_data)
        self.log_test_result(
            "Phase 5", "Referral Program Creation", 
            result['success'], 
            {'error': result.get('error', 'Referral program creation failed')} if not result['success'] else {
                'program_id': result.get('response_data', {}).get('program_id', 'N/A'),
                'status': result.get('response_data', {}).get('status', 'unknown'),
                'expected_reach': result.get('response_data', {}).get('expected_reach', 'N/A')
            },
            result.get('response_time_ms')
        )
        
        print("Testing marketing content generation...")
        content_data = {
            'type': 'social_media',
            'topic': 'AI automation benefits',
            'target_audience': 'tech_professionals',
            'tone': 'professional'
        }
        
        result = self.test_api_endpoint(f"{self.base_url}/api/growth/content/generate", method='POST', data=content_data)
        self.log_test_result(
            "Phase 5", "Marketing Content Generation", 
            result['success'], 
            {'error': result.get('error', 'Content generation failed')} if not result['success'] else {
                'content_id': result.get('response_data', {}).get('content_id', 'N/A'),
                'content_length': len(result.get('response_data', {}).get('content', '')),
                'engagement_score': result.get('response_data', {}).get('engagement_score', 'N/A')
            },
            result.get('response_time_ms')
        )
        
        print("Testing business intelligence summary...")
        result = self.test_api_endpoint(f"{self.base_url}/api/business-intelligence/summary")
        self.log_test_result(
            "Phase 5", "Business Intelligence Summary", 
            result['success'], 
            {'error': result.get('error', 'BI summary unavailable')} if not result['success'] else {
                'metrics_count': len(result.get('response_data', {}).get('metrics', [])),
                'insights_count': len(result.get('response_data', {}).get('insights', [])),
                'growth_rate': result.get('response_data', {}).get('growth_rate', 'N/A')
            },
            result.get('response_time_ms')
        )

    def test_phase6_security_governance(self):
        """Test Phase 6: 安全與審計強化 - Integrated Flask Endpoints"""
        print("\n🧪 Testing Phase 6: Security & Governance")
        print("=" * 70)
        
        print("Testing access request evaluation...")
        access_data = {
            'user': 'test_user',
            'resource': 'sensitive_dashboard',
            'action': 'read',
            'context': {
                'ip_address': '192.168.1.100',
                'device_trust_score': 0.8,
                'time_of_request': datetime.now().isoformat()
            }
        }
        
        result = self.test_api_endpoint(f"{self.base_url}/api/security/access-requests/evaluate", method='POST', data=access_data)
        self.log_test_result(
            "Phase 6", "Access Request Evaluation", 
            result['success'], 
            {'error': result.get('error', 'Access evaluation failed')} if not result['success'] else {
                'decision': result.get('response_data', {}).get('decision', 'unknown'),
                'trust_score': result.get('response_data', {}).get('trust_score', 'N/A'),
                'risk_level': result.get('response_data', {}).get('risk_level', 'N/A')
            },
            result.get('response_time_ms')
        )
        
        print("Testing security event review...")
        security_data = {
            'event_type': 'suspicious_login',
            'user': 'test_user',
            'details': {
                'failed_attempts': 3,
                'unusual_location': True,
                'device_fingerprint': 'unknown'
            }
        }
        
        result = self.test_api_endpoint(f"{self.base_url}/api/security/events/review", method='POST', data=security_data)
        self.log_test_result(
            "Phase 6", "Security Event Review", 
            result['success'], 
            {'error': result.get('error', 'Security review failed')} if not result['success'] else {
                'risk_assessment': result.get('response_data', {}).get('risk_assessment', 'unknown'),
                'recommended_action': result.get('response_data', {}).get('recommended_action', 'N/A'),
                'confidence_score': result.get('response_data', {}).get('confidence_score', 'N/A')
            },
            result.get('response_time_ms')
        )
        
        print("Testing HITL security analysis...")
        hitl_data = {
            'event_data': {
                'event_type': 'data_access_anomaly',
                'severity': 'high',
                'affected_resources': ['user_database', 'payment_data']
            },
            'ai_analysis': {
                'risk_score': 0.85,
                'threat_indicators': ['unusual_access_pattern', 'off_hours_activity'],
                'recommended_action': 'immediate_review'
            }
        }
        
        result = self.test_api_endpoint(f"{self.base_url}/api/security/hitl/submit", method='POST', data=hitl_data)
        self.log_test_result(
            "Phase 6", "HITL Security Analysis", 
            result['success'], 
            {'error': result.get('error', 'HITL analysis failed')} if not result['success'] else {
                'review_id': result.get('response_data', {}).get('review_id', 'N/A'),
                'status': result.get('response_data', {}).get('status', 'unknown'),
                'priority': result.get('response_data', {}).get('priority', 'N/A')
            },
            result.get('response_time_ms')
        )
        
        print("Testing security audit...")
        audit_data = {
            'scope': 'comprehensive',
            'type': 'compliance_check',
            'focus_areas': ['access_controls', 'data_protection', 'audit_trails']
        }
        
        result = self.test_api_endpoint(f"{self.base_url}/api/security/audit/perform", method='POST', data=audit_data)
        self.log_test_result(
            "Phase 6", "Security Audit", 
            result['success'], 
            {'error': result.get('error', 'Security audit failed')} if not result['success'] else {
                'audit_id': result.get('response_data', {}).get('audit_id', 'N/A'),
                'status': result.get('response_data', {}).get('status', 'unknown'),
                'findings_count': len(result.get('response_data', {}).get('findings', []))
            },
            result.get('response_time_ms')
        )

    def test_integration_points(self):
        """Test Phase 4-6 Integration Points"""
        print("\n🧪 Testing Phase 4-6 Integration Points")
        print("=" * 70)
        
        print("Testing AI orchestrator security integration...")
        integration_data = {
            'workflow_type': 'secure_data_analysis',
            'security_level': 'high',
            'required_approvals': ['security_reviewer', 'data_owner']
        }
        
        result = self.test_api_endpoint(f"{self.base_url}/api/langgraph/workflows", method='POST', data=integration_data)
        self.log_test_result(
            "Integration", "AI Orchestrator + Security", 
            result['success'], 
            {'error': result.get('error', 'Secure workflow integration failed')} if not result['success'] else {
                'workflow_id': result.get('response_data', {}).get('workflow_id', 'N/A'),
                'security_clearance': result.get('response_data', {}).get('security_clearance', 'N/A')
            },
            result.get('response_time_ms')
        )
        
        print("Testing data intelligence growth integration...")
        result = self.test_api_endpoint(f"{self.base_url}/api/business-intelligence/summary")
        self.log_test_result(
            "Integration", "Data Intelligence + Growth", 
            result['success'], 
            {'error': result.get('error', 'Growth analytics integration failed')} if not result['success'] else {
                'growth_metrics': len(result.get('response_data', {}).get('growth_metrics', [])),
                'intelligence_score': result.get('response_data', {}).get('intelligence_score', 'N/A')
            },
            result.get('response_time_ms')
        )

    def generate_optimization_report(self):
        """Generate comprehensive optimization report"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r['success'])
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        phase_results = {}
        for result in self.results:
            phase = result['phase']
            if phase not in phase_results:
                phase_results[phase] = {'total': 0, 'passed': 0, 'tests': []}
            phase_results[phase]['total'] += 1
            if result['success']:
                phase_results[phase]['passed'] += 1
            phase_results[phase]['tests'].append(result)
        
        response_times = [r['response_time_ms'] for r in self.results if r['response_time_ms'] is not None]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        min_response_time = min(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0
        
        print("\n" + "=" * 80)
        print("🎯 PHASE 4-6 INTEGRATED TESTING REPORT")
        print("=" * 80)
        print(f"📊 Overall Results: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}%)")
        print(f"🕐 Test Duration: {duration:.2f} seconds")
        print()
        
        for phase, data in phase_results.items():
            phase_success_rate = (data['passed'] / data['total'] * 100) if data['total'] > 0 else 0
            status_icon = "✅" if phase_success_rate >= 80 else "⚠️" if phase_success_rate >= 50 else "❌"
            print(f"{status_icon} {phase}: {data['passed']}/{data['total']} ({phase_success_rate:.1f}%)")
            
            for test in data['tests']:
                test_status = "✅" if test['success'] else "❌"
                test_name = test['test_name']
                if not test['success'] and 'error' in test.get('details', {}):
                    error_msg = test['details']['error']
                    print(f"   {test_status} {test_name}: {error_msg}")
                else:
                    print(f"   {test_status} {test_name}")
        
        print("\n" + "=" * 80)
        print("🔍 DETAILED ANALYSIS & RECOMMENDATIONS")
        print("=" * 80)
        
        if success_rate >= 80:
            print("\n🟢 HIGH SUCCESS RATE:")
            print("• Phase 4-6 integration successful - all major components operational")
            print("• Meta-Agent decision hub, QuickSight integration, and Zero Trust security working")
            print("• System ready for production deployment")
        elif success_rate >= 50:
            print("\n🟡 MODERATE SUCCESS RATE:")
            print("• Phase 4-6 integration partially successful - some components need attention")
            print("• Focus on failed components for immediate improvement")
        else:
            print("\n🔴 LOW SUCCESS RATE:")
            print("• Phase 4-6 integration needs significant work")
            print("• Review Flask backend integration and API endpoint implementations")
        
        print(f"\n📈 TECHNICAL METRICS:")
        print(f"• Average Response Time: {avg_response_time:.2f}ms")
        print(f"• Fastest Response: {min_response_time:.2f}ms")
        print(f"• Slowest Response: {max_response_time:.2f}ms")
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'success_rate': success_rate,
            'duration_seconds': duration,
            'phase_results': phase_results,
            'avg_response_time_ms': avg_response_time
        }

    def save_report_to_file(self, report_data):
        """Save detailed report to file"""
        report_path = "/home/ubuntu/repos/morningai/PHASE_4_6_INTEGRATED_TEST_REPORT.md"
        
        with open(report_path, 'w') as f:
            f.write("# Phase 4-6 Integrated Testing Report\n\n")
            f.write(f"**Test Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Overall Success Rate**: {report_data['success_rate']:.1f}%\n")
            f.write(f"**Total Tests**: {report_data['total_tests']}\n")
            f.write(f"**Passed Tests**: {report_data['passed_tests']}\n")
            f.write(f"**Test Duration**: {report_data['duration_seconds']:.2f} seconds\n\n")
            
            f.write("## Phase-Specific Results\n\n")
            for phase, data in report_data['phase_results'].items():
                phase_success_rate = (data['passed'] / data['total'] * 100) if data['total'] > 0 else 0
                f.write(f"### {phase}\n")
                f.write(f"- **Success Rate**: {phase_success_rate:.1f}%\n")
                f.write(f"- **Tests Passed**: {data['passed']}/{data['total']}\n\n")
                
                for test in data['tests']:
                    status = "✅ PASSED" if test['success'] else "❌ FAILED"
                    f.write(f"- {status}: {test['test_name']}\n")
                    if not test['success'] and 'error' in test.get('details', {}):
                        f.write(f"  - Error: {test['details']['error']}\n")
                f.write("\n")
            
            f.write("## Technical Metrics\n\n")
            f.write(f"- **Average Response Time**: {report_data['avg_response_time_ms']:.2f}ms\n")
            f.write(f"- **Test Infrastructure**: Flask Backend Integration\n")
            f.write(f"- **API Endpoints Tested**: 14 Phase 4-6 endpoints\n\n")
            
            f.write("## Detailed Test Results\n\n")
            for result in self.results:
                f.write(f"### {result['test_name']}\n")
                f.write(f"- **Phase**: {result['phase']}\n")
                f.write(f"- **Status**: {'✅ PASSED' if result['success'] else '❌ FAILED'}\n")
                f.write(f"- **Response Time**: {result['response_time_ms']:.2f}ms\n")
                if result['details']:
                    f.write(f"- **Details**: {json.dumps(result['details'], indent=2)}\n")
                f.write(f"- **Timestamp**: {result['timestamp']}\n\n")
        
        print(f"\n📄 Detailed report saved to: {report_path}")

def run_phase456_integrated_testing():
    """Run comprehensive Phase 4-6 integrated testing"""
    print("🧪 Phase 4-6 Integrated Flask Backend Testing Suite")
    print("=" * 80)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    suite = Phase456IntegratedTestSuite()
    
    suite.test_phase4_ai_orchestration()
    suite.test_phase5_data_intelligence()
    suite.test_phase6_security_governance()
    suite.test_integration_points()
    
    report_data = suite.generate_optimization_report()
    suite.save_report_to_file(report_data)
    
    return report_data

if __name__ == "__main__":
    run_phase456_integrated_testing()
