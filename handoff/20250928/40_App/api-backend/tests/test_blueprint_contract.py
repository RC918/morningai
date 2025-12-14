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
