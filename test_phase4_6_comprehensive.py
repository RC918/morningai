#!/usr/bin/env python3
"""
Phase 4-6 Comprehensive Testing Suite
Tests AI Orchestration, Data Intelligence, and Security components
"""

import requests
import json
import time
import sqlite3
import os
import sys
from datetime import datetime
from pathlib import Path

class Phase456TestSuite:
    def __init__(self):
        self.base_url = "http://127.0.0.1:10001"
        self.results = []
        self.start_time = datetime.now()
        
    def log_test_result(self, phase, test_name, success, details=None, response_time=None):
        """Log test result with details"""
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
        """Test Phase 4: AI 自治系統核心"""
        print("\n🧪 Testing Phase 4: AI Orchestration & Meta-Agent System")
        print("=" * 70)
        
        print("Testing AI Orchestrator availability...")
        result = self.test_api_endpoint(f"{self.base_url}/api/orchestrator/health")
        self.log_test_result(
            "Phase 4", "AI Orchestrator Health Check", 
            result['success'], 
            {'error': result.get('error', 'Service unavailable')} if not result['success'] else result.get('response_data'),
            result.get('response_time_ms')
        )
        
        print("Testing Meta-Agent decision capabilities...")
        decision_data = {
            'scenario': 'resource_allocation',
            'context': {
                'available_agents': ['DataAnalyst', 'SecurityReviewer', 'GrowthStrategist'],
                'task_priority': 'high',
                'resource_constraints': {'cpu': 80, 'memory': 70}
            }
        }
        
        result = self.test_api_endpoint(f"{self.base_url}/api/meta-agent/decide", method='POST', data=decision_data)
        self.log_test_result(
            "Phase 4", "Meta-Agent Decision Making", 
            result['success'], 
            {'error': result.get('error', 'Decision engine unavailable')} if not result['success'] else {
                'decision_time': result.get('response_data', {}).get('decision_time_ms', 'N/A'),
                'selected_agents': result.get('response_data', {}).get('selected_agents', []),
                'confidence_score': result.get('response_data', {}).get('confidence_score', 0)
            },
            result.get('response_time_ms')
        )
        
        print("Testing agent orchestration workflow...")
        workflow_data = {
            'workflow_type': 'multi_agent_collaboration',
            'agents': ['DataAnalyst', 'SecurityReviewer'],
            'task': 'security_audit_with_data_analysis'
        }
        
        result = self.test_api_endpoint(f"{self.base_url}/api/orchestrator/workflow", method='POST', data=workflow_data)
        self.log_test_result(
            "Phase 4", "Agent Orchestration Workflow", 
            result['success'], 
            {'error': result.get('error', 'Workflow orchestration failed')} if not result['success'] else {
                'workflow_id': result.get('response_data', {}).get('workflow_id', 'N/A'),
                'status': result.get('response_data', {}).get('status', 'unknown'),
                'estimated_duration': result.get('response_data', {}).get('estimated_duration_minutes', 'N/A')
            },
            result.get('response_time_ms')
        )
        
        print("Testing LangGraph workflow integration...")
        result = self.test_api_endpoint(f"{self.base_url}/api/orchestrator/langgraph/status")
        self.log_test_result(
            "Phase 4", "LangGraph Integration", 
            result['success'], 
            {'error': result.get('error', 'LangGraph not available')} if not result['success'] else {
                'graph_status': result.get('response_data', {}).get('status', 'unknown'),
                'active_workflows': result.get('response_data', {}).get('active_workflows', 0),
                'version': result.get('response_data', {}).get('version', 'N/A')
            },
            result.get('response_time_ms')
        )

    def test_phase5_data_intelligence(self):
        """Test Phase 5: 數據智能與成長"""
        print("\n🧪 Testing Phase 5: Data Intelligence & Growth")
        print("=" * 70)
        
        print("Testing data dashboard functionality...")
        result = self.test_api_endpoint(f"{self.base_url}/api/dashboard/data-intelligence")
        self.log_test_result(
            "Phase 5", "Data Dashboard Integration", 
            result['success'], 
            {'error': result.get('error', 'Dashboard service unavailable')} if not result['success'] else {
                'widgets_count': len(result.get('response_data', {}).get('widgets', [])),
                'data_sources': result.get('response_data', {}).get('data_sources', []),
                'last_updated': result.get('response_data', {}).get('last_updated', 'N/A')
            },
            result.get('response_time_ms')
        )
        
        print("Testing QuickSight integration...")
        result = self.test_api_endpoint(f"{self.base_url}/api/analytics/quicksight/status")
        self.log_test_result(
            "Phase 5", "QuickSight Integration", 
            result['success'], 
            {'error': result.get('error', 'QuickSight integration not configured')} if not result['success'] else {
                'connection_status': result.get('response_data', {}).get('status', 'unknown'),
                'dashboards_count': result.get('response_data', {}).get('dashboards_count', 0),
                'data_sets': result.get('response_data', {}).get('data_sets', [])
            },
            result.get('response_time_ms')
        )
        
        print("Testing growth marketing automation...")
        growth_data = {
            'campaign_type': 'referral_program',
            'target_metrics': {
                'conversion_rate': 0.15,
                'viral_coefficient': 1.2
            }
        }
        
        result = self.test_api_endpoint(f"{self.base_url}/api/growth/campaign", method='POST', data=growth_data)
        self.log_test_result(
            "Phase 5", "Growth Marketing Module", 
            result['success'], 
            {'error': result.get('error', 'Growth module unavailable')} if not result['success'] else {
                'campaign_id': result.get('response_data', {}).get('campaign_id', 'N/A'),
                'predicted_reach': result.get('response_data', {}).get('predicted_reach', 0),
                'automation_status': result.get('response_data', {}).get('automation_status', 'unknown')
            },
            result.get('response_time_ms')
        )
        
        print("Testing automated content generation...")
        content_data = {
            'content_type': 'social_media_post',
            'target_audience': 'tech_entrepreneurs',
            'brand_voice': 'professional_friendly'
        }
        
        result = self.test_api_endpoint(f"{self.base_url}/api/content/generate", method='POST', data=content_data)
        self.log_test_result(
            "Phase 5", "Content Generation Automation", 
            result['success'], 
            {'error': result.get('error', 'Content generation service unavailable')} if not result['success'] else {
                'content_id': result.get('response_data', {}).get('content_id', 'N/A'),
                'generation_time': result.get('response_data', {}).get('generation_time_ms', 'N/A'),
                'quality_score': result.get('response_data', {}).get('quality_score', 0)
            },
            result.get('response_time_ms')
        )

    def test_phase6_security_governance(self):
        """Test Phase 6: 安全與審計強化"""
        print("\n🧪 Testing Phase 6: Security & Governance")
        print("=" * 70)
        
        print("Testing zero trust security implementation...")
        result = self.test_api_endpoint(f"{self.base_url}/api/security/zero-trust/status")
        self.log_test_result(
            "Phase 6", "Zero Trust Security Model", 
            result['success'], 
            {'error': result.get('error', 'Zero trust security not configured')} if not result['success'] else {
                'security_level': result.get('response_data', {}).get('security_level', 'unknown'),
                'active_policies': result.get('response_data', {}).get('active_policies', 0),
                'threat_detection': result.get('response_data', {}).get('threat_detection_enabled', False)
            },
            result.get('response_time_ms')
        )
        
        print("Testing SecurityReviewer agent capabilities...")
        security_review_data = {
            'review_type': 'code_security_audit',
            'target': 'api_endpoints',
            'severity_threshold': 'medium'
        }
        
        result = self.test_api_endpoint(f"{self.base_url}/api/security/review", method='POST', data=security_review_data)
        self.log_test_result(
            "Phase 6", "SecurityReviewer Agent", 
            result['success'], 
            {'error': result.get('error', 'SecurityReviewer agent unavailable')} if not result['success'] else {
                'review_id': result.get('response_data', {}).get('review_id', 'N/A'),
                'findings_count': result.get('response_data', {}).get('findings_count', 0),
                'risk_score': result.get('response_data', {}).get('risk_score', 'N/A')
            },
            result.get('response_time_ms')
        )
        
        print("Testing Human-in-the-Loop security analysis...")
        hitl_data = {
            'incident_type': 'suspicious_activity',
            'severity': 'high',
            'requires_human_review': True
        }
        
        result = self.test_api_endpoint(f"{self.base_url}/api/security/hitl/analyze", method='POST', data=hitl_data)
        self.log_test_result(
            "Phase 6", "HITL Security Analysis", 
            result['success'], 
            {'error': result.get('error', 'HITL security analysis unavailable')} if not result['success'] else {
                'analysis_id': result.get('response_data', {}).get('analysis_id', 'N/A'),
                'escalation_status': result.get('response_data', {}).get('escalation_status', 'unknown'),
                'estimated_review_time': result.get('response_data', {}).get('estimated_review_time_hours', 'N/A')
            },
            result.get('response_time_ms')
        )
        
        print("Testing audit trail and compliance features...")
        result = self.test_api_endpoint(f"{self.base_url}/api/security/audit/compliance-status")
        self.log_test_result(
            "Phase 6", "Audit Trail & Compliance", 
            result['success'], 
            {'error': result.get('error', 'Audit system unavailable')} if not result['success'] else {
                'compliance_score': result.get('response_data', {}).get('compliance_score', 0),
                'audit_events_count': result.get('response_data', {}).get('audit_events_count', 0),
                'last_audit_date': result.get('response_data', {}).get('last_audit_date', 'N/A')
            },
            result.get('response_time_ms')
        )

    def test_integration_points(self):
        """Test integration between Phase 4-6 components"""
        print("\n🧪 Testing Phase 4-6 Integration Points")
        print("=" * 70)
        
        print("Testing AI Orchestrator security integration...")
        integration_data = {
            'workflow_type': 'secure_data_processing',
            'security_level': 'high',
            'agents': ['DataAnalyst', 'SecurityReviewer']
        }
        
        result = self.test_api_endpoint(f"{self.base_url}/api/orchestrator/secure-workflow", method='POST', data=integration_data)
        self.log_test_result(
            "Integration", "AI Orchestrator + Security", 
            result['success'], 
            {'error': result.get('error', 'Secure workflow integration failed')} if not result['success'] else {
                'workflow_id': result.get('response_data', {}).get('workflow_id', 'N/A'),
                'security_clearance': result.get('response_data', {}).get('security_clearance', 'unknown'),
                'monitoring_enabled': result.get('response_data', {}).get('monitoring_enabled', False)
            },
            result.get('response_time_ms')
        )
        
        print("Testing data intelligence and growth integration...")
        result = self.test_api_endpoint(f"{self.base_url}/api/analytics/growth-insights")
        self.log_test_result(
            "Integration", "Data Intelligence + Growth", 
            result['success'], 
            {'error': result.get('error', 'Growth analytics integration failed')} if not result['success'] else {
                'insights_count': len(result.get('response_data', {}).get('insights', [])),
                'growth_predictions': result.get('response_data', {}).get('growth_predictions', {}),
                'recommendation_score': result.get('response_data', {}).get('recommendation_score', 0)
            },
            result.get('response_time_ms')
        )

    def generate_optimization_report(self):
        """Generate comprehensive optimization report for Phase 4-6"""
        print("\n" + "=" * 80)
        print("🎯 PHASE 4-6 OPTIMIZATION REPORT")
        print("=" * 80)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r['success'])
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        phase_results = {}
        for result in self.results:
            phase = result['phase']
            if phase not in phase_results:
                phase_results[phase] = {'passed': 0, 'total': 0, 'tests': []}
            phase_results[phase]['total'] += 1
            if result['success']:
                phase_results[phase]['passed'] += 1
            phase_results[phase]['tests'].append(result)
        
        print(f"📊 Overall Results: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}%)")
        print(f"🕐 Test Duration: {(datetime.now() - self.start_time).total_seconds():.2f} seconds")
        print()
        
        for phase, data in phase_results.items():
            phase_success_rate = (data['passed'] / data['total']) * 100
            status_emoji = "✅" if phase_success_rate >= 75 else "⚠️" if phase_success_rate >= 50 else "❌"
            print(f"{status_emoji} {phase}: {data['passed']}/{data['total']} ({phase_success_rate:.1f}%)")
            
            failed_tests = [t for t in data['tests'] if not t['success']]
            if failed_tests:
                for test in failed_tests:
                    print(f"   ❌ {test['test_name']}: {test['details'].get('error', 'Unknown error')}")
        
        print("\n" + "=" * 80)
        print("🔍 DETAILED ANALYSIS & RECOMMENDATIONS")
        print("=" * 80)
        
        recommendations = self.generate_recommendations(phase_results)
        
        for priority, recs in recommendations.items():
            if recs:
                print(f"\n🔴 {priority.upper()} PRIORITY:")
                for rec in recs:
                    print(f"• {rec}")
        
        print(f"\n📈 TECHNICAL METRICS:")
        response_times = [r.get('response_time_ms', 0) for r in self.results if r.get('response_time_ms')]
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            print(f"• Average Response Time: {avg_response_time:.2f}ms")
            print(f"• Fastest Response: {min(response_times):.2f}ms")
            print(f"• Slowest Response: {max(response_times):.2f}ms")
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'success_rate': success_rate,
            'phase_results': phase_results,
            'recommendations': recommendations,
            'test_duration': (datetime.now() - self.start_time).total_seconds()
        }

    def generate_recommendations(self, phase_results):
        """Generate optimization recommendations based on test results"""
        recommendations = {
            'high': [],
            'medium': [],
            'low': []
        }
        
        if 'Phase 4' in phase_results:
            phase4_success = (phase_results['Phase 4']['passed'] / phase_results['Phase 4']['total']) * 100
            if phase4_success < 50:
                recommendations['high'].append("Phase 4 AI Orchestration: Critical infrastructure missing - implement Meta-Agent decision hub and LangGraph integration")
            elif phase4_success < 75:
                recommendations['medium'].append("Phase 4 AI Orchestration: Enhance agent workflow orchestration and improve decision-making algorithms")
        
        if 'Phase 5' in phase_results:
            phase5_success = (phase_results['Phase 5']['passed'] / phase_results['Phase 5']['total']) * 100
            if phase5_success < 50:
                recommendations['high'].append("Phase 5 Data Intelligence: Implement QuickSight integration and growth marketing automation")
            elif phase5_success < 75:
                recommendations['medium'].append("Phase 5 Data Intelligence: Optimize content generation and improve analytics dashboard performance")
        
        if 'Phase 6' in phase_results:
            phase6_success = (phase_results['Phase 6']['passed'] / phase_results['Phase 6']['total']) * 100
            if phase6_success < 50:
                recommendations['high'].append("Phase 6 Security: Critical security gaps - implement zero trust model and HITL security analysis")
            elif phase6_success < 75:
                recommendations['medium'].append("Phase 6 Security: Enhance SecurityReviewer agent capabilities and audit trail compliance")
        
        if 'Integration' in phase_results:
            integration_success = (phase_results['Integration']['passed'] / phase_results['Integration']['total']) * 100
            if integration_success < 75:
                recommendations['medium'].append("Cross-Phase Integration: Improve integration between AI orchestration, data intelligence, and security components")
        
        overall_success = sum(data['passed'] for data in phase_results.values()) / sum(data['total'] for data in phase_results.values()) * 100
        
        if overall_success < 60:
            recommendations['high'].append("System Architecture: Fundamental gaps in Phase 4-6 implementation require immediate attention")
        elif overall_success < 80:
            recommendations['medium'].append("System Optimization: Focus on improving API endpoint availability and response times")
        else:
            recommendations['low'].append("System Monitoring: Implement comprehensive monitoring and alerting for Phase 4-6 components")
        
        return recommendations

    def save_report_to_file(self, report_data):
        """Save detailed report to markdown file"""
        report_path = "/home/ubuntu/repos/morningai/PHASE_4_6_OPTIMIZATION_REPORT.md"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# Phase 4-6 優化建議報告\n\n")
            f.write(f"**測試執行時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**測試持續時間**: {report_data['test_duration']:.2f} 秒\n\n")
            
            f.write("## 📊 執行摘要\n\n")
            f.write(f"- **總測試數**: {report_data['total_tests']} 項測試\n")
            f.write(f"- **通過測試**: {report_data['passed_tests']} 項 ({report_data['success_rate']:.1f}% 成功率)\n")
            f.write(f"- **整體評估**: {'優秀' if report_data['success_rate'] >= 80 else '良好' if report_data['success_rate'] >= 60 else '需要改進'}\n\n")
            
            f.write("## 🔍 各階段詳細結果\n\n")
            for phase, data in report_data['phase_results'].items():
                phase_success_rate = (data['passed'] / data['total']) * 100
                status = "✅" if phase_success_rate >= 75 else "⚠️" if phase_success_rate >= 50 else "❌"
                f.write(f"### {phase} {status} {phase_success_rate:.1f}% ({data['passed']}/{data['total']})\n\n")
                
                for test in data['tests']:
                    status_icon = "✅" if test['success'] else "❌"
                    f.write(f"- {status_icon} {test['test_name']}")
                    if test.get('response_time_ms'):
                        f.write(f": {test['response_time_ms']:.2f}ms")
                    f.write("\n")
                    if not test['success'] and test['details'].get('error'):
                        f.write(f"  - 錯誤: {test['details']['error']}\n")
                f.write("\n")
            
            f.write("## 🎯 優化建議\n\n")
            for priority, recs in report_data['recommendations'].items():
                if recs:
                    priority_emoji = "🔴" if priority == 'high' else "🟡" if priority == 'medium' else "🟢"
                    f.write(f"### {priority_emoji} {priority.upper()} 優先級\n\n")
                    for rec in recs:
                        f.write(f"- {rec}\n")
                    f.write("\n")
        
        return report_path

def run_phase456_comprehensive_testing():
    """Run comprehensive testing for Phase 4-6"""
    print("🧪 Phase 4-6 Comprehensive Testing Suite")
    print("=" * 80)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    suite = Phase456TestSuite()
    
    suite.test_phase4_ai_orchestration()
    suite.test_phase5_data_intelligence()
    suite.test_phase6_security_governance()
    suite.test_integration_points()
    
    report_data = suite.generate_optimization_report()
    report_path = suite.save_report_to_file(report_data)
    
    print(f"\n📄 Detailed report saved to: {report_path}")
    
    return report_data['success_rate'] >= 60

if __name__ == "__main__":
    success = run_phase456_comprehensive_testing()
    exit(0 if success else 1)
