#!/usr/bin/env python3
"""
Phase 6-8 Comprehensive Deep Testing Suite
Tests Phase 6 (Security & Governance), Phase 7 (Performance & Growth), and Phase 8 (Dashboard & Reporting)
"""

import asyncio
import requests
import time
import json
from datetime import datetime
import traceback

class Phase6_8TestSuite:
    def __init__(self):
        self.base_url = "http://127.0.0.1:5001"
        self.results = []
        self.start_time = None
        
    def log_result(self, test_name, success, response_time=None, details=None):
        """Log test result with timing and details"""
        result = {
            'test': test_name,
            'success': success,
            'response_time': response_time,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.results.append(result)
        
        status = "✅ PASSED" if success else "❌ FAILED"
        timing = f" ({response_time:.2f}ms)" if response_time else ""
        print(f"{status}: {test_name}{timing}")
        if details and not success:
            print(f"   Details: {details}")
    
    def test_api_endpoint(self, endpoint, method="GET", data=None, test_name=None):
        """Test a single API endpoint"""
        if not test_name:
            test_name = f"{method} {endpoint}"
            
        try:
            start_time = time.time()
            
            if method == "GET":
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
            elif method == "POST":
                response = requests.post(f"{self.base_url}{endpoint}", json=data, timeout=10)
            elif method == "PUT":
                response = requests.put(f"{self.base_url}{endpoint}", json=data, timeout=10)
            
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    self.log_result(test_name, True, response_time, f"Status: {response.status_code}")
                    return True, response_data
                except:
                    self.log_result(test_name, True, response_time, f"Status: {response.status_code} (non-JSON)")
                    return True, response.text
            else:
                self.log_result(test_name, False, response_time, f"HTTP {response.status_code}: {response.text[:200]}")
                return False, None
                
        except Exception as e:
            self.log_result(test_name, False, None, str(e))
            return False, None
    
    def test_phase6_security_governance(self):
        """Test Phase 6: Security & Governance components"""
        print("\n🧪 Testing Phase 6: Security & Governance")
        print("=" * 70)
        
        phase6_tests = [
            {
                'endpoint': '/api/security/access/evaluate',
                'method': 'POST',
                'data': {
                    'user_id': 'test_user_123',
                    'resource': 'sensitive_data',
                    'action': 'read',
                    'context': {
                        'ip_address': '192.168.1.100',
                        'device_id': 'device_456',
                        'time_of_day': 'business_hours'
                    }
                },
                'name': 'Phase 6 - Zero Trust Access Evaluation'
            },
            
            {
                'endpoint': '/api/security/events/review',
                'method': 'POST',
                'data': {
                    'event_type': 'suspicious_login',
                    'user': 'test_user',
                    'severity': 'high',
                    'details': {
                        'failed_attempts': 3,
                        'unusual_location': True,
                        'device_fingerprint': 'unknown'
                    }
                },
                'name': 'Phase 6 - Security Event Review'
            },
            
            {
                'endpoint': '/api/security/hitl/submit',
                'method': 'POST',
                'data': {
                    'event_data': {
                        'event_type': 'data_access_anomaly',
                        'user_id': 'user_789',
                        'severity': 'critical',
                        'affected_resources': ['database', 'api_keys']
                    },
                    'ai_analysis': {
                        'risk_score': 0.85,
                        'threat_indicators': ['unusual_access_pattern', 'privilege_escalation', 'data_exfiltration']
                    }
                },
                'name': 'Phase 6 - HITL Security Analysis'
            },
            
            {
                'endpoint': '/api/security/audit',
                'method': 'POST',
                'data': {
                    'audit_type': 'comprehensive',
                    'scope': ['access_logs', 'security_events', 'compliance_status'],
                    'time_range': '24h'
                },
                'name': 'Phase 6 - Security Audit'
            },
            
            {
                'endpoint': '/api/security/reviews/pending',
                'method': 'GET',
                'name': 'Phase 6 - Pending Security Reviews'
            }
        ]
        
        phase6_passed = 0
        for test in phase6_tests:
            success, _ = self.test_api_endpoint(
                test['endpoint'], 
                test['method'], 
                test.get('data'), 
                test['name']
            )
            if success:
                phase6_passed += 1
        
        return phase6_passed, len(phase6_tests)
    
    def test_phase7_performance_growth(self):
        """Test Phase 7: Performance, Growth & Beta Introduction"""
        print("\n🧪 Testing Phase 7: Performance, Growth & Beta Introduction")
        print("=" * 70)
        
        phase7_tests = [
            {
                'endpoint': '/api/phase7/status',
                'method': 'GET',
                'name': 'Phase 7 - System Status'
            },
            
            {
                'endpoint': '/api/phase7/approvals/pending',
                'method': 'GET',
                'name': 'Phase 7 - Pending Approvals'
            },
            
            {
                'endpoint': '/api/phase7/beta/candidates',
                'method': 'GET',
                'name': 'Phase 7 - Beta Candidates'
            },
            
            {
                'endpoint': '/api/phase7/growth/metrics',
                'method': 'GET',
                'name': 'Phase 7 - Growth Metrics'
            },
            
            {
                'endpoint': '/api/phase7/ops/metrics',
                'method': 'GET',
                'name': 'Phase 7 - Operations Metrics'
            },
            
            {
                'endpoint': '/api/phase7/monitoring/dashboard',
                'method': 'GET',
                'name': 'Phase 7 - Monitoring Dashboard'
            },
            
            {
                'endpoint': '/api/phase7/resilience/metrics',
                'method': 'GET',
                'name': 'Phase 7 - Resilience Metrics'
            },
            
            {
                'endpoint': '/api/phase7/environment/validate',
                'method': 'POST',
                'data': {
                    'environment': 'production',
                    'checks': ['database', 'redis', 'external_apis']
                },
                'name': 'Phase 7 - Environment Validation'
            }
        ]
        
        phase7_passed = 0
        for test in phase7_tests:
            success, _ = self.test_api_endpoint(
                test['endpoint'], 
                test['method'], 
                test.get('data'), 
                test['name']
            )
            if success:
                phase7_passed += 1
        
        return phase7_passed, len(phase7_tests)
    
    def test_phase8_dashboard_reporting(self):
        """Test Phase 8: Self-service Dashboard & Reporting Center"""
        print("\n🧪 Testing Phase 8: Self-service Dashboard & Reporting Center")
        print("=" * 70)
        
        phase8_tests = [
            {
                'endpoint': '/api/dashboard/layouts',
                'method': 'GET',
                'name': 'Phase 8 - Dashboard Layouts'
            },
            
            {
                'endpoint': '/api/dashboard/widgets/available',
                'method': 'GET',
                'name': 'Phase 8 - Available Widgets'
            },
            
            {
                'endpoint': '/api/dashboard/data',
                'method': 'POST',
                'data': {
                    'dashboard_id': 'main_dashboard',
                    'widgets': ['performance_metrics', 'user_analytics', 'revenue_chart'],
                    'time_range': '7d'
                },
                'name': 'Phase 8 - Dashboard Data'
            },
            
            {
                'endpoint': '/api/reports/generate',
                'method': 'POST',
                'data': {
                    'report_type': 'performance_summary',
                    'format': 'pdf',
                    'parameters': {
                        'date_range': '30d',
                        'include_charts': True,
                        'sections': ['overview', 'metrics', 'recommendations']
                    }
                },
                'name': 'Phase 8 - Report Generation'
            },
            
            {
                'endpoint': '/api/reports/templates',
                'method': 'GET',
                'name': 'Phase 8 - Report Templates'
            },
            
            {
                'endpoint': '/api/reports/history',
                'method': 'GET',
                'name': 'Phase 8 - Report History'
            },
            
            {
                'endpoint': '/api/dashboard/layouts',
                'method': 'POST',
                'data': {
                    'name': 'Custom Performance Dashboard',
                    'layout': {
                        'widgets': [
                            {'type': 'metric_card', 'position': {'x': 0, 'y': 0, 'w': 4, 'h': 2}},
                            {'type': 'line_chart', 'position': {'x': 4, 'y': 0, 'w': 8, 'h': 4}}
                        ]
                    },
                    'permissions': ['read', 'write']
                },
                'name': 'Phase 8 - Custom Dashboard Creation'
            }
        ]
        
        phase8_passed = 0
        for test in phase8_tests:
            success, _ = self.test_api_endpoint(
                test['endpoint'], 
                test['method'], 
                test.get('data'), 
                test['name']
            )
            if success:
                phase8_passed += 1
        
        return phase8_passed, len(phase8_tests)
    
    def test_integration_scenarios(self):
        """Test integration scenarios across Phase 6-8"""
        print("\n🧪 Testing Phase 6-8 Integration Scenarios")
        print("=" * 70)
        
        integration_tests = [
            {
                'endpoint': '/api/security/events/review',
                'method': 'POST',
                'data': {
                    'event_type': 'performance_anomaly',
                    'severity': 'medium',
                    'details': {
                        'response_time_spike': True,
                        'resource_usage': 'high',
                        'affected_services': ['api', 'dashboard']
                    }
                },
                'name': 'Integration - Security + Performance Monitoring'
            },
            
            {
                'endpoint': '/api/dashboard/data',
                'method': 'POST',
                'data': {
                    'dashboard_id': 'security_dashboard',
                    'widgets': ['security_alerts', 'threat_metrics', 'compliance_status'],
                    'time_range': '24h'
                },
                'name': 'Integration - Security Dashboard Data'
            },
            
            {
                'endpoint': '/api/reports/generate',
                'method': 'POST',
                'data': {
                    'report_type': 'growth_security_analysis',
                    'format': 'json',
                    'parameters': {
                        'include_security_metrics': True,
                        'include_growth_metrics': True,
                        'correlation_analysis': True
                    }
                },
                'name': 'Integration - Growth + Security Report'
            }
        ]
        
        integration_passed = 0
        for test in integration_tests:
            success, _ = self.test_api_endpoint(
                test['endpoint'], 
                test['method'], 
                test.get('data'), 
                test['name']
            )
            if success:
                integration_passed += 1
        
        return integration_passed, len(integration_tests)
    
    def run_comprehensive_tests(self):
        """Run all Phase 6-8 tests and generate comprehensive report"""
        print("🧪 Phase 6-8 Comprehensive Deep Testing Suite")
        print("=" * 80)
        print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        self.start_time = time.time()
        
        phase6_passed, phase6_total = self.test_phase6_security_governance()
        phase7_passed, phase7_total = self.test_phase7_performance_growth()
        phase8_passed, phase8_total = self.test_phase8_dashboard_reporting()
        integration_passed, integration_total = self.test_integration_scenarios()
        
        total_passed = phase6_passed + phase7_passed + phase8_passed + integration_passed
        total_tests = phase6_total + phase7_total + phase8_total + integration_total
        success_rate = (total_passed / total_tests) * 100 if total_tests > 0 else 0
        
        test_duration = time.time() - self.start_time
        
        print("\n" + "=" * 80)
        print("🎯 PHASE 6-8 COMPREHENSIVE TESTING REPORT")
        print("=" * 80)
        print(f"📊 Overall Results: {total_passed}/{total_tests} tests passed ({success_rate:.1f}%)")
        print(f"🕐 Test Duration: {test_duration:.2f} seconds")
        print()
        
        phases = [
            ("Phase 6: Security & Governance", phase6_passed, phase6_total),
            ("Phase 7: Performance & Growth", phase7_passed, phase7_total),
            ("Phase 8: Dashboard & Reporting", phase8_passed, phase8_total),
            ("Integration Scenarios", integration_passed, integration_total)
        ]
        
        for phase_name, passed, total in phases:
            rate = (passed / total) * 100 if total > 0 else 0
            status = "✅" if rate == 100 else "⚠️" if rate >= 70 else "❌"
            print(f"{status} {phase_name}: {passed}/{total} ({rate:.1f}%)")
        
        print("\n" + "=" * 80)
        print("🔍 DETAILED ANALYSIS & RECOMMENDATIONS")
        print("=" * 80)
        
        response_times = [r['response_time'] for r in self.results if r['response_time']]
        if response_times:
            avg_response = sum(response_times) / len(response_times)
            min_response = min(response_times)
            max_response = max(response_times)
            
            print(f"\n📈 PERFORMANCE METRICS:")
            print(f"• Average Response Time: {avg_response:.2f}ms")
            print(f"• Fastest Response: {min_response:.2f}ms")
            print(f"• Slowest Response: {max_response:.2f}ms")
        
        if success_rate >= 90:
            print(f"\n🟢 EXCELLENT SUCCESS RATE:")
            print(f"• Phase 6-8 integration highly successful")
            print(f"• All major components operational")
            print(f"• System ready for production deployment")
        elif success_rate >= 70:
            print(f"\n🟡 GOOD SUCCESS RATE:")
            print(f"• Most Phase 6-8 components working")
            print(f"• Some optimization opportunities identified")
            print(f"• Focus on failing components for improvement")
        else:
            print(f"\n🔴 LOW SUCCESS RATE:")
            print(f"• Significant Phase 6-8 implementation gaps")
            print(f"• Major components need attention")
            print(f"• System requires substantial fixes")
        
        failed_tests = [r for r in self.results if not r['success']]
        if failed_tests:
            print(f"\n❌ FAILED TESTS ({len(failed_tests)} total):")
            for test in failed_tests[:10]:  # Show first 10 failures
                print(f"• {test['test']}: {test['details']}")
            if len(failed_tests) > 10:
                print(f"• ... and {len(failed_tests) - 10} more failures")
        
        self.generate_optimization_recommendations(success_rate, phases)
        
        return success_rate, total_passed, total_tests
    
    def generate_optimization_recommendations(self, success_rate, phases):
        """Generate specific optimization recommendations"""
        print(f"\n🚀 OPTIMIZATION RECOMMENDATIONS:")
        
        for phase_name, passed, total in phases:
            rate = (passed / total) * 100 if total > 0 else 0
            if rate < 100:
                if "Phase 6" in phase_name:
                    print(f"• **Phase 6**: Strengthen security event processing and HITL analysis")
                elif "Phase 7" in phase_name:
                    print(f"• **Phase 7**: Optimize performance monitoring and growth tracking")
                elif "Phase 8" in phase_name:
                    print(f"• **Phase 8**: Enhance dashboard customization and report generation")
                elif "Integration" in phase_name:
                    print(f"• **Integration**: Improve cross-phase communication and data flow")
        
        if success_rate < 90:
            print(f"• **API Endpoints**: Review and fix failing endpoint implementations")
            print(f"• **Error Handling**: Improve error responses and validation")
            print(f"• **Data Models**: Ensure consistent data structures across phases")
            print(f"• **Authentication**: Verify security and access control mechanisms")
        
        print(f"• **Monitoring**: Implement comprehensive health checks for all phases")
        print(f"• **Logging**: Add detailed logging for debugging and optimization")
        print(f"• **Testing**: Expand test coverage for edge cases and error scenarios")
        print(f"• **Documentation**: Update API documentation with latest endpoints")

def main():
    """Run Phase 6-8 comprehensive testing"""
    suite = Phase6_8TestSuite()
    
    try:
        success_rate, passed, total = suite.run_comprehensive_tests()
        
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'success_rate': success_rate,
            'total_passed': passed,
            'total_tests': total,
            'detailed_results': suite.results
        }
        
        with open('/home/ubuntu/repos/morningai/PHASE_6_8_DEEP_TEST_REPORT.json', 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: /home/ubuntu/repos/morningai/PHASE_6_8_DEEP_TEST_REPORT.json")
        
        return success_rate >= 70
        
    except Exception as e:
        print(f"❌ Testing suite failed: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()
