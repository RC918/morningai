"""Error Handler Tests for Phase 1 refactoring (PR1d).

These tests verify that the error handler extracted to src/middleware/error_handlers.py
behaves correctly for various exception types and configurations.

Part of Phase 1 refactoring for main.py.
See: docs/PHASE1_MAIN_PY_REFACTORING_PLAN.md
"""

import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
from werkzeug.exceptions import BadRequest, NotFound, Forbidden, InternalServerError


class TestErrorHandlerBasic:
    """Test basic error handler functionality."""
    
    def test_generic_exception_returns_500(self):
        """Verify generic Exception returns 500 with correct JSON format."""
        from src.middleware.error_handlers import register_error_handlers
        
        app = Flask(__name__)
        register_error_handlers(app)
        
        @app.route('/test-error')
        def raise_error():
            raise Exception("Test error message")
        
        with app.test_client() as client:
            response = client.get('/test-error')
            assert response.status_code == 500
            data = response.get_json()
            assert 'error' in data
            assert data['error']['code'] == 'internal_server_error'
            assert data['error']['message'] == 'An unexpected error occurred'
    
    def test_http_exception_bad_request_returns_400(self):
        """Verify BadRequest HTTPException returns 400."""
        from src.middleware.error_handlers import register_error_handlers
        
        app = Flask(__name__)
        register_error_handlers(app)
        
        @app.route('/test-bad-request')
        def raise_bad_request():
            raise BadRequest("Invalid input")
        
        with app.test_client() as client:
            response = client.get('/test-bad-request')
            assert response.status_code == 400
            data = response.get_json()
            assert 'error' in data
    
    def test_http_exception_not_found_returns_404(self):
        """Verify NotFound HTTPException returns 404."""
        from src.middleware.error_handlers import register_error_handlers
        
        app = Flask(__name__)
        register_error_handlers(app)
        
        @app.route('/test-not-found')
        def raise_not_found():
            raise NotFound("Resource not found")
        
        with app.test_client() as client:
            response = client.get('/test-not-found')
            assert response.status_code == 404
            data = response.get_json()
            assert 'error' in data
    
    def test_http_exception_forbidden_returns_403(self):
        """Verify Forbidden HTTPException returns 403."""
        from src.middleware.error_handlers import register_error_handlers
        
        app = Flask(__name__)
        register_error_handlers(app)
        
        @app.route('/test-forbidden')
        def raise_forbidden():
            raise Forbidden("Access denied")
        
        with app.test_client() as client:
            response = client.get('/test-forbidden')
            assert response.status_code == 403
            data = response.get_json()
            assert 'error' in data


class TestErrorHandlerExceptionTypes:
    """Test error handler with various Python exception types."""
    
    def test_key_error_returns_500(self):
        """Verify KeyError returns 500."""
        from src.middleware.error_handlers import register_error_handlers
        
        app = Flask(__name__)
        register_error_handlers(app)
        
        @app.route('/test-key-error')
        def raise_key_error():
            d = {}
            return d['nonexistent']
        
        with app.test_client() as client:
            response = client.get('/test-key-error')
            assert response.status_code == 500
            data = response.get_json()
            assert data['error']['code'] == 'internal_server_error'
    
    def test_type_error_returns_500(self):
        """Verify TypeError returns 500."""
        from src.middleware.error_handlers import register_error_handlers
        
        app = Flask(__name__)
        register_error_handlers(app)
        
        @app.route('/test-type-error')
        def raise_type_error():
            return None + 1  # TypeError
        
        with app.test_client() as client:
            response = client.get('/test-type-error')
            assert response.status_code == 500
            data = response.get_json()
            assert data['error']['code'] == 'internal_server_error'
    
    def test_value_error_returns_500(self):
        """Verify ValueError returns 500."""
        from src.middleware.error_handlers import register_error_handlers
        
        app = Flask(__name__)
        register_error_handlers(app)
        
        @app.route('/test-value-error')
        def raise_value_error():
            raise ValueError("Invalid value")
        
        with app.test_client() as client:
            response = client.get('/test-value-error')
            assert response.status_code == 500
            data = response.get_json()
            assert data['error']['code'] == 'internal_server_error'
    
    def test_attribute_error_returns_500(self):
        """Verify AttributeError returns 500."""
        from src.middleware.error_handlers import register_error_handlers
        
        app = Flask(__name__)
        register_error_handlers(app)
        
        @app.route('/test-attr-error')
        def raise_attr_error():
            obj = None
            return obj.nonexistent_method()
        
        with app.test_client() as client:
            response = client.get('/test-attr-error')
            assert response.status_code == 500
            data = response.get_json()
            assert data['error']['code'] == 'internal_server_error'


class TestErrorHandlerCustomCodeAttribute:
    """Test error handler with custom exceptions that have .code attribute."""
    
    def test_custom_exception_with_code_attribute(self):
        """Verify exception with .code attribute returns that code."""
        from src.middleware.error_handlers import register_error_handlers
        
        class CustomException(Exception):
            def __init__(self, message, code):
                super().__init__(message)
                self.code = code
        
        app = Flask(__name__)
        register_error_handlers(app)
        
        @app.route('/test-custom-code')
        def raise_custom():
            raise CustomException("Custom error", 418)
        
        with app.test_client() as client:
            response = client.get('/test-custom-code')
            assert response.status_code == 418
            data = response.get_json()
            assert 'error' in data


class TestErrorHandlerSentryIntegration:
    """Test error handler Sentry integration."""
    
    def test_sentry_capture_called_when_dsn_set(self):
        """Verify sentry_sdk.capture_exception is called when SENTRY_DSN is set."""
        with patch('src.middleware.error_handlers.SENTRY_DSN', 'https://fake@sentry.io/123'):
            with patch('sentry_sdk.capture_exception') as mock_capture:
                from src.middleware.error_handlers import handle_exception
                from flask import Flask
                
                app = Flask(__name__)
                
                with app.app_context():
                    # Call handle_exception directly with a test exception
                    test_exception = Exception("Test error")
                    response, status_code = handle_exception(test_exception)
                    
                    # Verify Sentry was called
                    mock_capture.assert_called_once_with(test_exception)
                    assert status_code == 500
    
    def test_sentry_not_called_when_dsn_not_set(self):
        """Verify sentry_sdk.capture_exception is NOT called when SENTRY_DSN is not set."""
        with patch('src.middleware.error_handlers.SENTRY_DSN', None):
            with patch('sentry_sdk.capture_exception') as mock_capture:
                from src.middleware.error_handlers import handle_exception
                from flask import Flask
                
                app = Flask(__name__)
                
                with app.app_context():
                    test_exception = Exception("Test error")
                    response, status_code = handle_exception(test_exception)
                    
                    # Verify Sentry was NOT called
                    mock_capture.assert_not_called()
                    assert status_code == 500
    
    def test_sentry_not_called_for_http_exceptions(self):
        """Verify sentry_sdk.capture_exception is NOT called for HTTPExceptions with .code."""
        with patch('src.middleware.error_handlers.SENTRY_DSN', 'https://fake@sentry.io/123'):
            with patch('sentry_sdk.capture_exception') as mock_capture:
                from src.middleware.error_handlers import handle_exception
                from flask import Flask
                
                app = Flask(__name__)
                
                with app.app_context():
                    # HTTPException has .code attribute, should return early
                    http_exception = BadRequest("Bad request")
                    response, status_code = handle_exception(http_exception)
                    
                    # Verify Sentry was NOT called (early return for .code exceptions)
                    mock_capture.assert_not_called()
                    assert status_code == 400


class TestErrorHandlerResponseFormat:
    """Test error handler response format consistency."""
    
    def test_500_response_json_structure(self):
        """Verify 500 response has correct JSON structure."""
        from src.middleware.error_handlers import register_error_handlers
        
        app = Flask(__name__)
        register_error_handlers(app)
        
        @app.route('/test-structure')
        def raise_error():
            raise Exception("Test")
        
        with app.test_client() as client:
            response = client.get('/test-structure')
            data = response.get_json()
            
            # Verify structure
            assert isinstance(data, dict)
            assert 'error' in data
            assert isinstance(data['error'], dict)
            assert 'code' in data['error']
            assert 'message' in data['error']
            assert data['error']['code'] == 'internal_server_error'
            assert data['error']['message'] == 'An unexpected error occurred'
    
    def test_response_content_type_is_json(self):
        """Verify response Content-Type is application/json."""
        from src.middleware.error_handlers import register_error_handlers
        
        app = Flask(__name__)
        register_error_handlers(app)
        
        @app.route('/test-content-type')
        def raise_error():
            raise Exception("Test")
        
        with app.test_client() as client:
            response = client.get('/test-content-type')
            assert response.content_type == 'application/json'


class TestErrorHandlerRegistration:
    """Test error handler registration."""
    
    def test_register_error_handlers_registers_exception_handler(self):
        """Verify register_error_handlers registers the Exception handler."""
        from src.middleware.error_handlers import register_error_handlers
        
        app = Flask(__name__)
        
        register_error_handlers(app)
        
        # After registration, Exception handler should be registered
        # Flask's error_handler_spec is nested: {blueprint_name: {code_or_exception: handler}}
        # For app-level handlers, blueprint_name is None
        error_handlers = app.error_handler_spec.get(None, {})
        # The inner dict may also be nested with None key
        if None in error_handlers:
            error_handlers = error_handlers[None]
        assert Exception in error_handlers
    
    def test_handle_exception_importable_from_main(self):
        """Verify handle_exception can be imported from src.main (backward compatibility)."""
        from src.main import handle_exception
        assert callable(handle_exception)
    
    def test_register_error_handlers_importable_from_middleware(self):
        """Verify register_error_handlers can be imported from middleware module."""
        from src.middleware.error_handlers import register_error_handlers
        assert callable(register_error_handlers)
