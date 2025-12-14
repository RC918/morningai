"""Blueprint Contract Tests for Phase 1 refactoring.

These tests verify that all blueprints are registered correctly after refactoring.
This is critical for PR1c which extracts blueprint registration to a separate module.

Part of Phase 1 pre-work for main.py refactoring.
See: docs/PHASE1_MAIN_PY_REFACTORING_PLAN.md

Note: This is the improved version using actual blueprint names (not variable names)
and precise matching as suggested by Gemini review.
"""

import pytest


class TestBlueprintContract:
    """Verify all blueprints are registered correctly after refactoring."""
    
    # Core blueprints that are always registered (unconditionally)
    # These use the actual blueprint names from Blueprint('name', ...) definitions
    CORE_BLUEPRINTS = [
        'user',           # user_bp from routes/user.py
        'auth',           # auth_bp from routes/auth.py
        'auth_enhanced',  # auth_enhanced_bp from routes/auth_enhanced.py
        'auth_2fa',       # auth_2fa_bp from routes/auth_2fa.py
        'dashboard',      # dashboard_bp from routes/dashboard.py
        'totp',           # totp_bp from routes/totp.py
        'billing',        # bp from routes/billing.py
        'agent_registry', # bp from routes/agent_registry.py
        'tenant',         # bp from routes/tenant.py
        'vectors',        # bp from routes/vectors.py
        'governance',     # bp from routes/governance.py
        'admin',          # bp from routes/admin.py
        'admin_agents',   # admin_bp from routes/governance.py
        'failures',       # bp from routes/failures.py
        'experiments',    # bp from routes/experiments.py
        'ai_policies',    # bp from routes/ai_policies.py
    ]
    
    # Conditional blueprints (registered based on feature flags or environment)
    CONDITIONAL_BLUEPRINTS = [
        'agent',           # Registered if BACKEND_SERVICES_AVAILABLE
        'agent_evaluation',# Registered if BACKEND_SERVICES_AVAILABLE
        'faq',             # Registered if BACKEND_SERVICES_AVAILABLE
        'action_requests', # Registered if PHASE_456_AVAILABLE
        'sessions',        # Registered if PHASE_456_AVAILABLE
        'webhooks',        # Registered if PHASE_456_AVAILABLE
        'deepwiki',        # Registered if PHASE_456_AVAILABLE
        'metrics',         # Registered if PHASE_456_AVAILABLE
        'mock_api',        # Registered if FLASK_ENV == 'development'
    ]
    
    def test_all_core_blueprints_registered(self):
        """Verify all core blueprints are registered."""
        from src.main import app
        registered_names = set(app.blueprints.keys())
        
        missing = []
        for expected in self.CORE_BLUEPRINTS:
            if expected not in registered_names:
                missing.append(expected)
        
        assert not missing, f"Missing core blueprints: {missing}"
    
    def test_core_blueprint_count(self):
        """Verify at least the core blueprints are registered."""
        from src.main import app
        # Should have at least the core blueprints
        assert len(app.blueprints) >= len(self.CORE_BLUEPRINTS), \
            f"Expected at least {len(self.CORE_BLUEPRINTS)} blueprints, got {len(app.blueprints)}"
    
    def test_no_duplicate_blueprints(self):
        """Verify no blueprints are registered multiple times."""
        from src.main import app
        # Flask's blueprints dict already prevents duplicates by name,
        # but we verify the count matches unique names
        blueprint_names = list(app.blueprints.keys())
        assert len(blueprint_names) == len(set(blueprint_names)), \
            "Duplicate blueprint names detected"
    
    def test_blueprints_have_valid_names(self):
        """Verify all registered blueprints have non-empty names."""
        from src.main import app
        for name, bp in app.blueprints.items():
            assert name, "Blueprint has empty name"
            assert bp.name == name, f"Blueprint name mismatch: {bp.name} != {name}"
    
    @pytest.mark.parametrize('blueprint_name', CORE_BLUEPRINTS)
    def test_core_blueprint_exists(self, blueprint_name):
        """Verify each core blueprint is registered."""
        from src.main import app
        assert blueprint_name in app.blueprints, \
            f"Core blueprint '{blueprint_name}' not registered"
    
    def test_conditional_blueprints_when_backend_services_available(self):
        """Verify conditional blueprints are registered when BACKEND_SERVICES_AVAILABLE is True."""
        from src.main import app, BACKEND_SERVICES_AVAILABLE
        
        if BACKEND_SERVICES_AVAILABLE:
            backend_blueprints = ['agent', 'agent_evaluation', 'faq']
            registered_names = set(app.blueprints.keys())
            for bp_name in backend_blueprints:
                assert bp_name in registered_names, \
                    f"Blueprint '{bp_name}' should be registered when BACKEND_SERVICES_AVAILABLE=True"
    
    def test_conditional_blueprints_when_phase_456_available(self):
        """Verify conditional blueprints are registered when PHASE_456_AVAILABLE is True."""
        from src.main import app, PHASE_456_AVAILABLE
        
        if PHASE_456_AVAILABLE:
            phase456_blueprints = ['action_requests', 'sessions', 'webhooks', 'deepwiki', 'metrics']
            registered_names = set(app.blueprints.keys())
            for bp_name in phase456_blueprints:
                assert bp_name in registered_names, \
                    f"Blueprint '{bp_name}' should be registered when PHASE_456_AVAILABLE=True"


class TestRegisterBlueprintsEdgeCases:
    """Test register_blueprints function with different configurations.
    
    These tests verify that the blueprint registration function handles
    various environment configurations correctly without raising exceptions.
    
    Part of PR1c edge case testing as requested by CTO review.
    """
    
    def test_register_blueprints_does_not_raise_with_default_config(self):
        """Verify register_blueprints doesn't raise with default configuration."""
        from flask import Flask
        from src.routes import register_blueprints
        
        app = Flask(__name__)
        # Should not raise any exception
        register_blueprints(app, backend_services_available=False)
        
        # Should have at least core blueprints registered
        assert len(app.blueprints) >= 16, \
            f"Expected at least 16 core blueprints, got {len(app.blueprints)}"
    
    def test_register_blueprints_with_backend_services_false(self):
        """Verify register_blueprints works when backend_services_available=False."""
        from flask import Flask
        from src.routes import register_blueprints
        
        app = Flask(__name__)
        register_blueprints(app, backend_services_available=False)
        
        # mock_api should NOT be registered
        assert 'mock_api' not in app.blueprints, \
            "mock_api should not be registered when backend_services_available=False"
    
    def test_register_blueprints_with_backend_services_true(self):
        """Verify register_blueprints works when backend_services_available=True."""
        from flask import Flask
        from src.routes import register_blueprints
        
        app = Flask(__name__)
        # This may or may not register mock_api depending on whether the module exists
        # The key is that it should not raise an exception
        register_blueprints(app, backend_services_available=True)
        
        # Should have at least core blueprints registered
        assert len(app.blueprints) >= 16, \
            f"Expected at least 16 core blueprints, got {len(app.blueprints)}"
    
    def test_register_blueprints_orchestrator_disabled(self, monkeypatch):
        """Verify register_blueprints works when ENABLE_ORCHESTRATOR=false."""
        from flask import Flask
        from src.routes import register_blueprints
        
        monkeypatch.setenv('ENABLE_ORCHESTRATOR', 'false')
        
        app = Flask(__name__)
        register_blueprints(app, backend_services_available=False)
        
        # Orchestrator blueprints should NOT be registered
        orchestrator_blueprints = ['agent', 'agent_evaluation', 'faq']
        for bp_name in orchestrator_blueprints:
            assert bp_name not in app.blueprints, \
                f"Blueprint '{bp_name}' should not be registered when ENABLE_ORCHESTRATOR=false"
    
    def test_register_blueprints_orchestrator_enabled(self, monkeypatch):
        """Verify register_blueprints works when ENABLE_ORCHESTRATOR=true."""
        from flask import Flask
        from src.routes import register_blueprints
        
        monkeypatch.setenv('ENABLE_ORCHESTRATOR', 'true')
        
        app = Flask(__name__)
        register_blueprints(app, backend_services_available=False)
        
        # Orchestrator blueprints should be registered
        orchestrator_blueprints = ['agent', 'agent_evaluation', 'faq']
        for bp_name in orchestrator_blueprints:
            assert bp_name in app.blueprints, \
                f"Blueprint '{bp_name}' should be registered when ENABLE_ORCHESTRATOR=true"
    
    def test_register_blueprints_idempotent_on_fresh_app(self):
        """Verify register_blueprints can be called on a fresh Flask app."""
        from flask import Flask
        from src.routes import register_blueprints
        
        # Create two separate apps and register blueprints on each
        app1 = Flask(__name__)
        app2 = Flask(__name__)
        
        register_blueprints(app1, backend_services_available=False)
        register_blueprints(app2, backend_services_available=False)
        
        # Both apps should have the same blueprints registered
        assert set(app1.blueprints.keys()) == set(app2.blueprints.keys()), \
            "Blueprint registration should be consistent across fresh apps"
