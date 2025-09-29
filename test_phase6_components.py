#!/usr/bin/env python3
"""
Test Phase 6 Components
Simple test to verify all Phase 6 components can be imported and work
"""

def test_security_manager():
    """Test security manager import and basic functionality"""
    try:
        from security_manager import SecurityManager
        
        config = {
            'master_key': 'test-master-key',
            'secret_key': 'test-secret-key',
            'audit_log_file': 'test_audit.log'
        }
        
        security_manager = SecurityManager(config)
        
        test_secret = "test-secret-data"
        encrypted = security_manager.kms.encrypt_secret(test_secret, "test_key")
        decrypted = security_manager.kms.decrypt_secret(encrypted, "test_key")
        
        if decrypted == test_secret:
            print("✅ Security Manager: Import and encryption test passed")
            return True
        else:
            print("❌ Security Manager: Encryption/decryption failed")
            return False
            
    except Exception as e:
        print(f"❌ Security Manager: Test failed - {e}")
        return False

def test_monitoring_system():
    """Test monitoring system import and basic functionality"""
    try:
        from monitoring_system import MonitoringSystem
        
        monitor = MonitoringSystem("https://morningai-backend-v2.onrender.com")
        
        result = monitor.check_endpoint('/health', dry_run=True)
        
        if result.success:
            print("✅ Monitoring System: Import and dry run test passed")
            return True
        else:
            print("❌ Monitoring System: Dry run test failed")
            return False
            
    except Exception as e:
        print(f"❌ Monitoring System: Test failed - {e}")
        return False

def test_meta_agent_hub():
    """Test Meta-Agent decision hub import"""
    try:
        from meta_agent_decision_hub import MetaAgentDecisionHub
        
        hub = MetaAgentDecisionHub()
        
        status = hub.get_system_status()
        
        if 'ooda_loop_status' in status:
            print("✅ Meta-Agent Hub: Import and status test passed")
            return True
        else:
            print("❌ Meta-Agent Hub: Status test failed")
            return False
            
    except Exception as e:
        print(f"❌ Meta-Agent Hub: Test failed - {e}")
        return False

def test_governance_module():
    """Test AI governance module import"""
    try:
        from ai_governance_module import AIGovernanceModule, UserRole, GovernanceRuleType
        
        governance = AIGovernanceModule()
        
        user = governance.permission_manager.create_user(
            username="test_user",
            email="test@example.com",
            role=UserRole.TENANT_USER,
            tenant_id="test_tenant"
        )
        
        if user.username == "test_user":
            print("✅ Governance Module: Import and user creation test passed")
            return True
        else:
            print("❌ Governance Module: User creation test failed")
            return False
            
    except Exception as e:
        print(f"❌ Governance Module: Test failed - {e}")
        return False

def main():
    """Run all Phase 6 component tests"""
    print("🧪 Testing Phase 6 Components")
    print("=" * 40)
    
    tests = [
        ("Security Manager", test_security_manager),
        ("Monitoring System", test_monitoring_system),
        ("Meta-Agent Hub", test_meta_agent_hub),
        ("Governance Module", test_governance_module)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        if test_func():
            passed += 1
    
    print("=" * 40)
    print(f"🎯 Phase 6 Component Tests: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All Phase 6 components working correctly!")
        return True
    else:
        print("⚠️ Some Phase 6 components need attention")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
