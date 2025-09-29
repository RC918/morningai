#!/usr/bin/env python3
"""
Phase 8 Backend Component Testing
Tests dashboard customization and report generation functionality
"""

import sys
import os
from datetime import datetime

def test_report_generator():
    """Test report generation functionality"""
    print("🧪 Testing Report Generator")
    print("=" * 50)
    
    try:
        sys.path.append('.')
        from report_generator import report_generator
        
        report_types = ['performance', 'task_tracking', 'resilience', 'financial']
        
        for report_type in report_types:
            print(f"   Testing {report_type} report...")
            
            report_data = report_generator.generate_report(report_type, '24h')
            
            if report_data and report_data.title:
                print(f"   ✅ {report_type} report generated: {report_data.title}")
                
                csv_data = report_generator.export_csv(report_data)
                if len(csv_data) > 100:  # Basic validation
                    print(f"   ✅ CSV export successful: {len(csv_data)} characters")
                else:
                    print(f"   ❌ CSV export too short: {len(csv_data)} characters")
                    return False
                    
                try:
                    pdf_path = report_generator.export_pdf(report_data, report_type)
                    if os.path.exists(pdf_path):
                        print(f"   ✅ PDF export successful: {pdf_path}")
                        os.remove(pdf_path)  # Cleanup
                    else:
                        print(f"   ❌ PDF file not created")
                        return False
                except Exception as e:
                    print(f"   ❌ PDF export failed: {e}")
                    return False
            else:
                print(f"   ❌ {report_type} report generation failed")
                return False
        
        print("✅ All report types generated successfully")
        return True
        
    except Exception as e:
        print(f"❌ Report generation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_persistent_state_manager():
    """Test dashboard layout persistence"""
    print("\n🧪 Testing Persistent State Manager")
    print("=" * 50)
    
    try:
        from persistent_state_manager import persistent_state_manager
        
        test_layout = {
            'widgets': [
                {'id': 'cpu_usage', 'position': {'x': 0, 'y': 0, 'w': 6, 'h': 4}},
                {'id': 'memory_usage', 'position': {'x': 6, 'y': 0, 'w': 6, 'h': 4}},
                {'id': 'task_execution', 'position': {'x': 0, 'y': 4, 'w': 12, 'h': 6}}
            ]
        }
        
        persistent_state_manager.save_dashboard_layout('test_user', test_layout)
        print("✅ Dashboard layout saved successfully")
        
        loaded_layout = persistent_state_manager.load_dashboard_layout('test_user')
        print(f"✅ Dashboard layout loaded: {len(loaded_layout['widgets'])} widgets")
        
        if loaded_layout == test_layout:
            print("✅ Layout data integrity verified")
            return True
        else:
            print("❌ Layout data mismatch")
            return False
            
    except Exception as e:
        print(f"❌ Dashboard layout test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_flask_api_endpoints():
    """Test Phase 8 Flask API endpoints"""
    print("\n🧪 Testing Flask API Endpoints")
    print("=" * 50)
    
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'handoff/20250928/40_App/api-backend'))
        
        from src.main import app
        
        with app.test_client() as client:
            response = client.get('/api/dashboard/layouts?user_id=test')
            if response.status_code == 200:
                print("✅ Dashboard layouts GET endpoint working")
            else:
                print(f"❌ Dashboard layouts GET failed: {response.status_code}")
                return False
            
            response = client.get('/api/dashboard/widgets/available')
            if response.status_code == 200:
                widgets = response.get_json()
                print(f"✅ Available widgets endpoint: {len(widgets)} widgets")
            else:
                print(f"❌ Available widgets endpoint failed: {response.status_code}")
                return False
            
            response = client.get('/api/dashboard/data')
            if response.status_code == 200:
                data = response.get_json()
                print(f"✅ Dashboard data endpoint: {len(data)} data keys")
            else:
                print(f"❌ Dashboard data endpoint failed: {response.status_code}")
                return False
            
            response = client.get('/api/reports/templates')
            if response.status_code == 200:
                templates = response.get_json()
                print(f"✅ Report templates endpoint: {len(templates)} templates")
            else:
                print(f"❌ Report templates endpoint failed: {response.status_code}")
                return False
        
        print("✅ All API endpoints working correctly")
        return True
        
    except Exception as e:
        print(f"❌ API endpoints test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_phase8_backend_tests():
    """Run all Phase 8 backend component tests"""
    print("🧪 Phase 8 Backend Component Testing Suite")
    print("=" * 80)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    test_results = []
    
    result1 = test_report_generator()
    test_results.append(("Report Generator", result1))
    
    result2 = test_persistent_state_manager()
    test_results.append(("Persistent State Manager", result2))
    
    result3 = test_flask_api_endpoints()
    test_results.append(("Flask API Endpoints", result3))
    
    print("\n" + "=" * 80)
    print("🎯 PHASE 8 BACKEND TEST RESULTS")
    print("=" * 80)
    
    passed_tests = 0
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
        if result:
            passed_tests += 1
    
    print(f"\n🎯 Overall Result: {passed_tests}/{len(test_results)} tests passed")
    
    if passed_tests == len(test_results):
        print("🎉 ALL PHASE 8 BACKEND TESTS PASSED! Backend components ready.")
    else:
        print("⚠️  Some backend tests failed. Need to fix issues.")
    
    return passed_tests == len(test_results)

if __name__ == "__main__":
    success = run_phase8_backend_tests()
    exit(0 if success else 1)
