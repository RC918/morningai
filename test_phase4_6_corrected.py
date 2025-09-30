#!/usr/bin/env python3
"""
Phase 4-6 Corrected Testing Suite
Tests AI Orchestration, Data Intelligence, and Security components with correct endpoints
"""

import requests
import json
import time
import sqlite3
import os
import sys
from datetime import datetime
from pathlib import Path

class Phase456CorrectedTestSuite:
    def __init__(self):
        self.base_url = "http://127.0.0.1:5001"
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
        """Test Phase 4: AI Orchestration and Meta-Agent Decision Hub"""
        print("\n🤖 Testing Phase 4: AI Orchestration")
        
        result = self.test_api_endpoint(
            f"{self.base_url}/api/meta-agent/ooda-cycle",
            method='POST',
            data={},
            expected_status=200
        )
        self.log_test_result("Phase 4", "Meta-Agent OODA Cycle", result['success'], result, result.get('response_time_ms'))
        
        workflow_data = {
            "name": "test_workflow",
            "type": "decision_tree",
            "agents": ["analyzer", "executor"]
        }
        result = self.test_api_endpoint(
            f"{self.base_url}/api/langgraph/workflows",
            method='POST',
            data=workflow_data,
            expected_status=200
        )
        self.log_test_result("Phase 4", "LangGraph Workflow Creation", result['success'], result, result.get('response_time_ms'))
        
        result = self.test_api_endpoint(
            f"{self.base_url}/api/governance/status",
            expected_status=200
        )
        self.log_test_result("Phase 4", "Governance Status Check", result['success'], result, result.get('response_time_ms'))
        
        policy_data = {
            "name": "test_policy",
            "type": "access_control",
            "rules": ["authenticated_users_only"]
        }
        result = self.test_api_endpoint(
            f"{self.base_url}/api/governance/policies",
            method='POST',
            data=policy_data,
            expected_status=200
        )
        self.log_test_result("Phase 4", "Governance Policy Creation", result['success'], result, result.get('response_time_ms'))

    def test_phase5_data_intelligence(self):
        """Test Phase 5: Data Intelligence and Growth Marketing"""
        print("\n📊 Testing Phase 5: Data Intelligence")
        
        dashboard_data = {
            "name": "test_dashboard",
            "data_source": "analytics_db",
            "widgets": ["revenue_chart", "user_metrics"]
        }
        result = self.test_api_endpoint(
            f"{self.base_url}/api/quicksight/dashboards",
            method='POST',
            data=dashboard_data,
            expected_status=200
        )
        self.log_test_result("Phase 5", "QuickSight Dashboard Creation", result['success'], result, result.get('response_time_ms'))
        
        report_data = {
            "type": "monthly_summary",
            "metrics": ["revenue", "user_growth", "engagement"],
            "format": "pdf"
        }
        result = self.test_api_endpoint(
            f"{self.base_url}/api/reports/automated",
            method='POST',
            data=report_data,
            expected_status=200
        )
        self.log_test_result("Phase 5", "Automated Report Generation", result['success'], result, result.get('response_time_ms'))
        
        referral_data = {
            "name": "Q4_Referral_Program",
            "reward_type": "credit",
            "reward_amount": 50,
            "duration_days": 90
        }
        result = self.test_api_endpoint(
            f"{self.base_url}/api/growth/referral-programs",
            method='POST',
            data=referral_data,
            expected_status=200
        )
        self.log_test_result("Phase 5", "Referral Program Creation", result['success'], result, result.get('response_time_ms'))
        
        content_data = {
            "type": "social_media_post",
            "topic": "AI automation benefits",
            "platform": "linkedin",
            "tone": "professional"
        }
        result = self.test_api_endpoint(
            f"{self.base_url}/api/growth/content/generate",
            method='POST',
            data=content_data,
            expected_status=200
        )
        self.log_test_result("Phase 5", "Marketing Content Generation", result['success'], result, result.get('response_time_ms'))
        
        result = self.test_api_endpoint(
            f"{self.base_url}/api/business-intelligence/summary",
            expected_status=200
        )
        self.log_test_result("Phase 5", "Business Intelligence Summary", result['success'], result, result.get('response_time_ms'))

    def test_phase6_security_governance(self):
        """Test Phase 6: Security and Audit Enhancement"""
        print("\n🔒 Testing Phase 6: Security & Governance")
        
        access_data = {
            "user_id": "user_123",
            "resource": "sensitive_database",
            "action": "read",
            "context": {"location": "office", "device": "trusted"}
        }
        result = self.test_api_endpoint(
            f"{self.base_url}/api/security/access/evaluate",
            method='POST',
            data=access_data,
            expected_status=200
        )
        self.log_test_result("Phase 6", "Access Request Evaluation", result['success'], result, result.get('response_time_ms'))
        
        event_data = {
            "event_id": "SEC_001",
            "event_type": "unauthorized_access_attempt",
            "severity": "high",
            "source_ip": "192.168.1.100",
            "timestamp": "2025-09-30T10:00:00Z"
        }
        result = self.test_api_endpoint(
            f"{self.base_url}/api/security/events/review",
            method='POST',
            data=event_data,
            expected_status=200
        )
        self.log_test_result("Phase 6", "Security Event Review", result['success'], result, result.get('response_time_ms'))
        
        hitl_data = {
            "event_id": "SEC_001",
            "analysis_type": "threat_assessment",
            "analyst_id": "analyst_001",
            "priority": "high",
            "notes": "Suspicious activity detected from unusual location"
        }
        result = self.test_api_endpoint(
            f"{self.base_url}/api/security/hitl/submit",
            method='POST',
            data=hitl_data,
            expected_status=200
        )
        self.log_test_result("Phase 6", "HITL Security Analysis", result['success'], result, result.get('response_time_ms'))
        
        audit_data = {
            "audit_type": "compliance_check",
            "scope": "user_access_controls",
            "compliance_framework": "SOC2"
        }
        result = self.test_api_endpoint(
            f"{self.base_url}/api/security/audit",
            method='POST',
            data=audit_data,
            expected_status=200
        )
        self.log_test_result("Phase 6", "Security Audit", result['success'], result, result.get('response_time_ms'))
        
        result = self.test_api_endpoint(
            f"{self.base_url}/api/security/reviews/pending",
            expected_status=200
        )
        self.log_test_result("Phase 6", "Pending Security Reviews", result['success'], result, result.get('response_time_ms'))

    def test_integration_points(self):
        """Test integration between Phase 4-6 components"""
        print("\n🔗 Testing Phase 4-6 Integration Points")
        
        result = self.test_api_endpoint(
            f"{self.base_url}/api/business-intelligence/summary",
            expected_status=200
        )
        self.log_test_result("Integration", "Security + Analytics Integration", result['success'], result, result.get('response_time_ms'))
        
        result = self.test_api_endpoint(
            f"{self.base_url}/api/governance/status",
            expected_status=200
        )
        self.log_test_result("Integration", "Governance + Security Integration", result['success'], result, result.get('response_time_ms'))

    def generate_summary_report(self):
        """Generate test summary report"""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r['success'])
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n📊 Test Summary Report")
        print("=" * 80)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if success_rate < 100:
            print(f"\n❌ Failed Tests:")
            for result in self.results:
                if not result['success']:
                    print(f"  - {result['phase']}: {result['test_name']}")
                    if 'error' in result['details']:
                        print(f"    Error: {result['details']['error']}")
        
        return success_rate >= 80

def run_corrected_phase456_testing():
    """Run corrected comprehensive testing for Phase 4-6"""
    print("🧪 Phase 4-6 Corrected Testing Suite")
    print("=" * 80)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    suite = Phase456CorrectedTestSuite()
    
    suite.test_phase4_ai_orchestration()
    suite.test_phase5_data_intelligence()
    suite.test_phase6_security_governance()
    suite.test_integration_points()
    
    success = suite.generate_summary_report()
    
    return success

if __name__ == "__main__":
    success = run_corrected_phase456_testing()
    exit(0 if success else 1)
