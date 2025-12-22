"""
Tests for orchestrator import failure fallback behavior.

This module tests that endpoints gracefully handle orchestrator import failures
by returning 503 Service Unavailable responses instead of 500 Internal Server
Errors or AttributeError exceptions.

These tests verify:
1. The MissingOptionalDependency proxy raises descriptive errors on attribute access
2. Endpoints return 503 when orchestrator is unavailable
3. Helper functions handle unavailable state correctly
"""
import pytest
from unittest.mock import patch, MagicMock
import sys


class TestMissingOptionalDependencyProxy:
    """Tests for the MissingOptionalDependency proxy class."""
    
    def test_proxy_raises_on_attribute_access(self):
        """Proxy should raise RuntimeError on attribute access."""
        from src.utils.optional_imports import MissingOptionalDependency
        
        proxy = MissingOptionalDependency(
            "test.module.SomeClass",
            hint="Install test-package"
        )
        
        with pytest.raises(RuntimeError) as exc_info:
            _ = proxy.some_attribute
        
        assert "test.module.SomeClass" in str(exc_info.value)
        assert "some_attribute" in str(exc_info.value)
        assert "Install test-package" in str(exc_info.value)
    
    def test_proxy_raises_on_call(self):
        """Proxy should raise RuntimeError when called as a function."""
        from src.utils.optional_imports import MissingOptionalDependency
        
        proxy = MissingOptionalDependency("test.module.SomeClass")
        
        with pytest.raises(RuntimeError) as exc_info:
            proxy()
        
        assert "test.module.SomeClass" in str(exc_info.value)
    
    def test_proxy_is_falsy(self):
        """Proxy should be falsy for truthiness checks."""
        from src.utils.optional_imports import MissingOptionalDependency
        
        proxy = MissingOptionalDependency("test.module.SomeClass")
        
        assert not proxy
        assert bool(proxy) is False
    
    def test_proxy_equals_none(self):
        """Proxy should compare equal to None for backward compatibility."""
        from src.utils.optional_imports import MissingOptionalDependency
        
        proxy = MissingOptionalDependency("test.module.SomeClass")
        
        assert proxy == None  # noqa: E711
        assert not (proxy != None)  # noqa: E711
    
    def test_proxy_repr(self):
        """Proxy should have a clear repr."""
        from src.utils.optional_imports import MissingOptionalDependency
        
        proxy = MissingOptionalDependency("test.module.SomeClass")
        
        assert "MissingOptionalDependency" in repr(proxy)
        assert "test.module.SomeClass" in repr(proxy)
    
    def test_missing_factory_function(self):
        """The missing() factory should create a proxy."""
        from src.utils.optional_imports import missing
        
        proxy = missing("test.module.SomeClass", hint="Install test-package")
        
        assert not proxy
        with pytest.raises(RuntimeError) as exc_info:
            _ = proxy.attr
        assert "Install test-package" in str(exc_info.value)


class TestAIPoliciesEndpointFallback:
    """Tests for AI Policies endpoint fallback behavior."""
    
    @pytest.fixture
    def client(self):
        """Create a test client with mocked auth."""
        from src.main import create_app
        app = create_app()
        app.config['TESTING'] = True
        return app.test_client()
    
    @pytest.fixture
    def mock_jwt(self):
        """Mock JWT authentication to allow requests."""
        with patch('src.middleware.auth_middleware.verify_jwt_token') as mock:
            mock.return_value = {'sub': 'test-user-id', 'role': 'admin'}
            with patch('src.middleware.auth_middleware.get_jwt_identity') as mock_identity:
                mock_identity.return_value = 'test-user-id'
                yield mock
    
    def test_list_policies_returns_503_when_unavailable(self, client, mock_jwt):
        """GET /api/ai-policies should return 503 when orchestrator unavailable."""
        with patch('src.routes.ai_policies.AI_POLICY_AVAILABLE', False):
            response = client.get(
                '/api/ai-policies',
                headers={'Authorization': 'Bearer test-token'}
            )
            
            assert response.status_code == 503
            data = response.get_json()
            assert 'error' in data
            assert 'not available' in data['error'].lower()
    
    def test_get_policy_returns_503_when_unavailable(self, client, mock_jwt):
        """GET /api/ai-policies/<id> should return 503 when orchestrator unavailable."""
        with patch('src.routes.ai_policies.AI_POLICY_AVAILABLE', False):
            response = client.get(
                '/api/ai-policies/test-policy-id',
                headers={'Authorization': 'Bearer test-token'}
            )
            
            assert response.status_code == 503
            data = response.get_json()
            assert 'error' in data
            assert 'not available' in data['error'].lower()
    
    def test_create_policy_returns_503_when_unavailable(self, client, mock_jwt):
        """POST /api/ai-policies should return 503 when orchestrator unavailable."""
        with patch('src.routes.ai_policies.AI_POLICY_AVAILABLE', False):
            response = client.post(
                '/api/ai-policies',
                json={'name': 'test', 'policy_type': 'test', 'rules': {}},
                headers={'Authorization': 'Bearer test-token'}
            )
            
            assert response.status_code == 503
            data = response.get_json()
            assert 'error' in data
            assert 'not available' in data['error'].lower()
    
    def test_templates_returns_503_when_unavailable(self, client, mock_jwt):
        """GET /api/ai-policies/templates should return 503 when orchestrator unavailable."""
        with patch('src.routes.ai_policies.AI_POLICY_AVAILABLE', False):
            response = client.get(
                '/api/ai-policies/templates',
                headers={'Authorization': 'Bearer test-token'}
            )
            
            assert response.status_code == 503
            data = response.get_json()
            assert 'error' in data
            assert 'not available' in data['error'].lower()
    
    def test_evaluate_returns_503_when_unavailable(self, client, mock_jwt):
        """POST /api/ai-policies/evaluate should return 503 when orchestrator unavailable."""
        with patch('src.routes.ai_policies.AI_POLICY_AVAILABLE', False):
            response = client.post(
                '/api/ai-policies/evaluate',
                json={'capability': 'test'},
                headers={'Authorization': 'Bearer test-token'}
            )
            
            assert response.status_code == 503
            data = response.get_json()
            assert 'error' in data
            assert 'not available' in data['error'].lower()


class TestAIPoliciesHelperFunctions:
    """Tests for AI Policies helper function fallback behavior."""
    
    def test_parse_policy_type_returns_error_when_unavailable(self):
        """_parse_policy_type should return error when AI_POLICY_AVAILABLE is False."""
        with patch('src.routes.ai_policies.AI_POLICY_AVAILABLE', False):
            from src.routes.ai_policies import _parse_policy_type
            
            result, error = _parse_policy_type('some_type')
            
            assert result is None
            assert error is not None
            assert 'not available' in error.lower()
    
    def test_parse_policy_scope_returns_error_when_unavailable(self):
        """_parse_policy_scope should return error when AI_POLICY_AVAILABLE is False."""
        with patch('src.routes.ai_policies.AI_POLICY_AVAILABLE', False):
            from src.routes.ai_policies import _parse_policy_scope
            
            result, error = _parse_policy_scope('tenant')
            
            assert result is None
            assert error is not None
            assert 'not available' in error.lower()
    
    def test_parse_policy_status_returns_error_when_unavailable(self):
        """_parse_policy_status should return error when AI_POLICY_AVAILABLE is False."""
        with patch('src.routes.ai_policies.AI_POLICY_AVAILABLE', False):
            from src.routes.ai_policies import _parse_policy_status
            
            result, error = _parse_policy_status('draft')
            
            assert result is None
            assert error is not None
            assert 'not available' in error.lower()


class TestGovernanceEndpointFallback:
    """Tests for Governance endpoint fallback behavior."""
    
    @pytest.fixture
    def client(self):
        """Create a test client with mocked auth."""
        from src.main import create_app
        app = create_app()
        app.config['TESTING'] = True
        return app.test_client()
    
    @pytest.fixture
    def mock_jwt(self):
        """Mock JWT authentication to allow requests."""
        with patch('src.middleware.auth_middleware.verify_jwt_token') as mock:
            mock.return_value = {'sub': 'test-user-id', 'role': 'admin'}
            with patch('src.middleware.auth_middleware.get_jwt_identity') as mock_identity:
                mock_identity.return_value = 'test-user-id'
                yield mock
    
    def test_get_agents_returns_503_when_unavailable(self, client, mock_jwt):
        """GET /api/governance/agents should return 503 when governance unavailable."""
        with patch('src.routes.governance.GOVERNANCE_AVAILABLE', False):
            response = client.get(
                '/api/governance/agents',
                headers={'Authorization': 'Bearer test-token'}
            )
            
            assert response.status_code == 503
            data = response.get_json()
            assert 'error' in data
            assert 'not available' in data['error'].lower()
    
    def test_get_costs_returns_503_when_unavailable(self, client, mock_jwt):
        """GET /api/governance/costs should return 503 when governance unavailable."""
        with patch('src.routes.governance.GOVERNANCE_AVAILABLE', False):
            response = client.get(
                '/api/governance/costs',
                headers={'Authorization': 'Bearer test-token'}
            )
            
            assert response.status_code == 503
            data = response.get_json()
            assert 'error' in data
            assert 'not available' in data['error'].lower()
    
    def test_get_violations_returns_503_when_unavailable(self, client, mock_jwt):
        """GET /api/governance/violations should return 503 when governance unavailable."""
        with patch('src.routes.governance.GOVERNANCE_AVAILABLE', False):
            response = client.get(
                '/api/governance/violations',
                headers={'Authorization': 'Bearer test-token'}
            )
            
            assert response.status_code == 503
            data = response.get_json()
            assert 'error' in data
            assert 'not available' in data['error'].lower()


class TestBootstrapPathsDebugLogging:
    """Tests for bootstrap_paths.py debug logging functionality."""
    
    def test_debug_logging_disabled_by_default(self, monkeypatch):
        """Debug logging should be disabled by default."""
        monkeypatch.delenv('BOOTSTRAP_PATHS_DEBUG', raising=False)
        
        # Force reimport to pick up env change
        import importlib
        import src.bootstrap_paths as bp
        importlib.reload(bp)
        
        assert bp._DEBUG is False
    
    def test_debug_logging_enabled_with_env_var(self, monkeypatch):
        """Debug logging should be enabled with BOOTSTRAP_PATHS_DEBUG=1."""
        monkeypatch.setenv('BOOTSTRAP_PATHS_DEBUG', '1')
        
        # Force reimport to pick up env change
        import importlib
        import src.bootstrap_paths as bp
        importlib.reload(bp)
        
        assert bp._DEBUG is True
    
    def test_debug_logging_enabled_with_true(self, monkeypatch):
        """Debug logging should be enabled with BOOTSTRAP_PATHS_DEBUG=true."""
        monkeypatch.setenv('BOOTSTRAP_PATHS_DEBUG', 'true')
        
        # Force reimport to pick up env change
        import importlib
        import src.bootstrap_paths as bp
        importlib.reload(bp)
        
        assert bp._DEBUG is True
