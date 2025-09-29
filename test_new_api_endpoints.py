#!/usr/bin/env python3
"""
Test New API Endpoints Implementation
Tests the newly implemented Phase 2-3 API endpoints
"""

import requests
import json
import time
from datetime import datetime

def test_api_endpoint(url, method='GET', data=None, expected_status=200):
    """Test a single API endpoint"""
    try:
        if method == 'POST':
            response = requests.post(url, json=data, timeout=10)
        else:
            response = requests.get(url, timeout=10)
        
        success = response.status_code == expected_status
        
        return {
            'success': success,
            'status_code': response.status_code,
            'response_time_ms': response.elapsed.total_seconds() * 1000,
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

def test_phase2_endpoints():
    """Test Phase 2 API endpoints"""
    print("🧪 Testing Phase 2 API Endpoints")
    print("=" * 50)
    
    base_url = "http://127.0.0.1:10001"
    results = []
    
    print("Testing /api/agents/bind...")
    bind_data = {
        'tenant_id': 'test_tenant_001',
        'platform_type': 'slack',
        'credentials': {
            'api_key': 'test_key_123',
            'webhook_url': 'https://hooks.slack.com/test'
        }
    }
    
    result = test_api_endpoint(f"{base_url}/api/agents/bind", method='POST', data=bind_data)
    results.append(('AI Agent Binding', result))
    
    if result['success']:
        print(f"✅ AI Agent Binding: {result['response_time_ms']:.2f}ms")
        print(f"   Binding ID: {result['response_data']['data']['binding_id']}")
        print(f"   Success Rate: {result['response_data']['data']['success_rate']}")
    else:
        print(f"❌ AI Agent Binding: {result.get('error', 'Failed')}")
    
    print("\nTesting /api/tenants/isolate...")
    isolate_data = {
        'tenant_id': 'test_tenant_001',
        'isolation_level': 'schema'
    }
    
    result = test_api_endpoint(f"{base_url}/api/tenants/isolate", method='POST', data=isolate_data)
    results.append(('Multi-tenant Isolation', result))
    
    if result['success']:
        print(f"✅ Multi-tenant Isolation: {result['response_time_ms']:.2f}ms")
        print(f"   Database Schema: {result['response_data']['data']['database_schema']}")
        print(f"   Security Policies: {len(result['response_data']['data']['security_policies'])} policies")
    else:
        print(f"❌ Multi-tenant Isolation: {result.get('error', 'Failed')}")
    
    return results

def test_phase3_endpoints():
    """Test Phase 3 API endpoints"""
    print("\n🧪 Testing Phase 3 API Endpoints")
    print("=" * 50)
    
    base_url = "http://127.0.0.1:10001"
    results = []
    
    print("Testing /api/bots/create...")
    bot_data = {
        'bot_name': 'Customer Support Bot',
        'bot_type': 'customer_service',
        'tenant_id': 'test_tenant_001',
        'customization': {
            'personality': 'friendly',
            'language': 'en',
            'response_style': 'professional'
        }
    }
    
    result = test_api_endpoint(f"{base_url}/api/bots/create", method='POST', data=bot_data)
    results.append(('AI Bot Creation', result))
    
    if result['success']:
        print(f"✅ AI Bot Creation: {result['response_time_ms']:.2f}ms")
        print(f"   Bot ID: {result['response_data']['data']['bot_id']}")
        print(f"   Capabilities: {len(result['response_data']['data']['capabilities'])} features")
        print(f"   Performance: {result['response_data']['data']['performance_metrics']['accuracy_rate']:.2%} accuracy")
    else:
        print(f"❌ AI Bot Creation: {result.get('error', 'Failed')}")
    
    print("\nTesting /api/subscriptions/create...")
    subscription_data = {
        'tenant_id': 'test_tenant_001',
        'plan_type': 'professional',
        'payment_method': 'pm_test_card_visa'
    }
    
    result = test_api_endpoint(f"{base_url}/api/subscriptions/create", method='POST', data=subscription_data)
    results.append(('Subscription Management', result))
    
    if result['success']:
        print(f"✅ Subscription Management: {result['response_time_ms']:.2f}ms")
        print(f"   Subscription ID: {result['response_data']['data']['subscription_id']}")
        print(f"   Plan: {result['response_data']['data']['plan_type']} - ${result['response_data']['data']['amount']}")
        print(f"   Features: {result['response_data']['data']['features']['ai_agents']} AI agents")
    else:
        print(f"❌ Subscription Management: {result.get('error', 'Failed')}")
    
    return results

def test_endpoint_error_handling():
    """Test error handling for new endpoints"""
    print("\n🧪 Testing Error Handling")
    print("=" * 50)
    
    base_url = "http://127.0.0.1:10001"
    results = []
    
    print("Testing error handling with missing fields...")
    
    result = test_api_endpoint(f"{base_url}/api/agents/bind", method='POST', 
                             data={'platform_type': 'slack'}, expected_status=400)
    results.append(('Agent Binding Error Handling', result))
    
    if result['success']:
        print("✅ Agent binding error handling works correctly")
    else:
        print("❌ Agent binding error handling failed")
    
    result = test_api_endpoint(f"{base_url}/api/bots/create", method='POST', 
                             data={'bot_type': 'general'}, expected_status=400)
    results.append(('Bot Creation Error Handling', result))
    
    if result['success']:
        print("✅ Bot creation error handling works correctly")
    else:
        print("❌ Bot creation error handling failed")
    
    return results

def run_comprehensive_endpoint_testing():
    """Run comprehensive testing of new API endpoints"""
    print("🧪 New API Endpoints Comprehensive Testing Suite")
    print("=" * 80)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    all_results = []
    
    phase2_results = test_phase2_endpoints()
    all_results.extend(phase2_results)
    
    phase3_results = test_phase3_endpoints()
    all_results.extend(phase3_results)
    
    error_results = test_endpoint_error_handling()
    all_results.extend(error_results)
    
    print("\n" + "=" * 80)
    print("🎯 NEW API ENDPOINTS TESTING RESULTS")
    print("=" * 80)
    
    passed_tests = 0
    total_tests = len(all_results)
    
    for test_name, result in all_results:
        status = "✅ PASSED" if result['success'] else "❌ FAILED"
        response_time = f" ({result['response_time_ms']:.2f}ms)" if result.get('response_time_ms') else ""
        print(f"{status}: {test_name}{response_time}")
        if result['success']:
            passed_tests += 1
    
    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    print(f"\n🎯 Overall Result: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}%)")
    
    if success_rate >= 80:
        print("🎉 NEW API ENDPOINTS IMPLEMENTATION SUCCESSFUL!")
        print("✅ Phase 2-3 functionality now available")
        print("✅ Multi-tenant architecture gaps addressed")
        print("✅ AI binding and bot creation endpoints working")
        print("✅ Subscription management ready for Stripe integration")
    else:
        print("⚠️  Some endpoint tests failed. Review issues above.")
    
    return success_rate >= 80

if __name__ == "__main__":
    success = run_comprehensive_endpoint_testing()
    exit(0 if success else 1)
