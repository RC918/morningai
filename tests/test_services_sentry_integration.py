"""
Unit tests for services.sentry_integration module

Tests Sentry integration functionality including:
- Sensitive data scrubbing
- User context management
- Exception and message capture
- Performance monitoring
- Metrics tracking
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime


class TestScrubSensitiveData:
    """Test sensitive data scrubbing functionality"""
    
    def test_scrub_sensitive_data_with_none_event(self):
        """Should return None when event is None"""
        from services.sentry_integration import scrub_sensitive_data
        
        result = scrub_sensitive_data(None, {})
        
        assert result is None
    
    def test_scrub_sensitive_data_with_empty_event(self):
        """Should return event when empty (not None)"""
        from services.sentry_integration import scrub_sensitive_data
        
        event = {}
        result = scrub_sensitive_data(event, {})
        
        assert result is None
    
    def test_scrub_sensitive_data_headers(self):
        """Should redact sensitive headers"""
        from services.sentry_integration import scrub_sensitive_data
        
        event = {
            'request': {
                'headers': {
                    'authorization': 'Bearer secret-token',
                    'api_key': 'my-api-key',
                    'content-type': 'application/json'
                }
            }
        }
        
        result = scrub_sensitive_data(event, {})
        
        assert result['request']['headers']['authorization'] == '[REDACTED]'
        assert result['request']['headers']['api_key'] == '[REDACTED]'
        assert result['request']['headers']['content-type'] == 'application/json'
    
    def test_scrub_sensitive_data_query_string(self):
        """Should redact sensitive query parameters"""
        from services.sentry_integration import scrub_sensitive_data
        
        event = {
            'request': {
                'query_string': 'api_key=secret123&user=john'
            }
        }
        
        result = scrub_sensitive_data(event, {})
        
        assert result['request']['query_string'] == '[REDACTED]'
    
    def test_scrub_sensitive_data_request_body(self):
        """Should redact sensitive data in request body"""
        from services.sentry_integration import scrub_sensitive_data
        
        event = {
            'request': {
                'data': {
                    'username': 'john',
                    'password': 'secret123',
                    'email': 'john@example.com'
                }
            }
        }
        
        result = scrub_sensitive_data(event, {})
        
        assert result['request']['data']['password'] == '[REDACTED]'
        assert result['request']['data']['username'] == 'john'
        assert result['request']['data']['email'] == 'john@example.com'
    
    def test_scrub_sensitive_data_extra_context(self):
        """Should redact sensitive data in extra context"""
        from services.sentry_integration import scrub_sensitive_data
        
        event = {
            'extra': {
                'user_id': '123',
                'access_token': 'secret-token',
                'metadata': 'some-data'
            }
        }
        
        result = scrub_sensitive_data(event, {})
        
        assert result['extra']['access_token'] == '[REDACTED]'
        assert result['extra']['user_id'] == '123'
        assert result['extra']['metadata'] == 'some-data'
    
    def test_scrub_sensitive_data_multiple_fields(self):
        """Should redact all sensitive fields across different sections"""
        from services.sentry_integration import scrub_sensitive_data
        
        event = {
            'request': {
                'headers': {'authorization': 'Bearer token'},
                'data': {'password': 'pass123', 'username': 'john'}
            },
            'extra': {
                'jwt': 'eyJhbGc...',
                'user_id': '123'
            }
        }
        
        result = scrub_sensitive_data(event, {})
        
        assert result['request']['headers']['authorization'] == '[REDACTED]'
        assert result['request']['data']['password'] == '[REDACTED]'
        assert result['extra']['jwt'] == '[REDACTED]'
        assert result['request']['data']['username'] == 'john'
        assert result['extra']['user_id'] == '123'


class TestSetUserContext:
    """Test user context setting functionality"""
    
    def test_set_user_context_when_sentry_disabled(self, monkeypatch):
        """Should do nothing when Sentry is disabled"""
        with patch('services.sentry_integration.sentry_sdk', None):
            from services.sentry_integration import set_user_context
            
            set_user_context(user_id='user123', tenant_id='tenant456')
    
    def test_set_user_context_with_user_id(self):
        """Should set user context with user_id"""
        mock_sentry = MagicMock()
        
        with patch('services.sentry_integration.sentry_sdk', mock_sentry):
            from services.sentry_integration import set_user_context
            
            set_user_context(user_id='user123')
            
            mock_sentry.set_user.assert_called_once_with({'id': 'user123'})
    
    def test_set_user_context_with_tenant_id(self):
        """Should set user context with tenant_id"""
        mock_sentry = MagicMock()
        
        with patch('services.sentry_integration.sentry_sdk', mock_sentry):
            from services.sentry_integration import set_user_context
            
            set_user_context(tenant_id='tenant456')
            
            mock_sentry.set_user.assert_called_once_with({'tenant_id': 'tenant456'})
    
    def test_set_user_context_with_all_params(self):
        """Should set user context with all parameters"""
        mock_sentry = MagicMock()
        
        with patch('services.sentry_integration.sentry_sdk', mock_sentry):
            from services.sentry_integration import set_user_context
            
            set_user_context(
                user_id='user123',
                tenant_id='tenant456',
                email='user@example.com',
                role='admin'
            )
            
            mock_sentry.set_user.assert_called_once_with({
                'id': 'user123',
                'tenant_id': 'tenant456',
                'email': 'user@example.com',
                'role': 'admin'
            })


class TestSetContext:
    """Test custom context setting functionality"""
    
    def test_set_context_when_sentry_disabled(self):
        """Should do nothing when Sentry is disabled"""
        with patch('services.sentry_integration.sentry_sdk', None):
            from services.sentry_integration import set_context
            
            set_context('agent', {'agent_id': 'agent123'})
    
    def test_set_context_with_data(self):
        """Should set custom context with data"""
        mock_sentry = MagicMock()
        
        with patch('services.sentry_integration.sentry_sdk', mock_sentry):
            from services.sentry_integration import set_context
            
            context_data = {'agent_id': 'agent123', 'task_id': 'task456'}
            set_context('agent', context_data)
            
            mock_sentry.set_context.assert_called_once_with('agent', context_data)


class TestAddBreadcrumb:
    """Test breadcrumb functionality"""
    
    def test_add_breadcrumb_when_sentry_disabled(self):
        """Should do nothing when Sentry is disabled"""
        with patch('services.sentry_integration.sentry_sdk', None):
            from services.sentry_integration import add_breadcrumb
            
            add_breadcrumb('api_call', 'GET /api/users')
    
    def test_add_breadcrumb_basic(self):
        """Should add breadcrumb with basic parameters"""
        mock_sentry = MagicMock()
        
        with patch('services.sentry_integration.sentry_sdk', mock_sentry):
            from services.sentry_integration import add_breadcrumb
            
            add_breadcrumb('api_call', 'GET /api/users')
            
            mock_sentry.add_breadcrumb.assert_called_once_with(
                category='api_call',
                message='GET /api/users',
                level='info',
                data={}
            )
    
    def test_add_breadcrumb_with_level_and_data(self):
        """Should add breadcrumb with custom level and data"""
        mock_sentry = MagicMock()
        
        with patch('services.sentry_integration.sentry_sdk', mock_sentry):
            from services.sentry_integration import add_breadcrumb
            
            data = {'user_id': '123', 'endpoint': '/api/users'}
            add_breadcrumb('api_call', 'GET /api/users', level='warning', data=data)
            
            mock_sentry.add_breadcrumb.assert_called_once_with(
                category='api_call',
                message='GET /api/users',
                level='warning',
                data=data
            )


class TestCaptureException:
    """Test exception capture functionality"""
    
    def test_capture_exception_when_sentry_disabled(self, caplog):
        """Should log error when Sentry is disabled"""
        with patch('services.sentry_integration.sentry_sdk', None):
            from services.sentry_integration import capture_exception
            
            exception = ValueError("Test error")
            capture_exception(exception)
            
            assert "Exception (Sentry disabled)" in caplog.text
    
    def test_capture_exception_basic(self):
        """Should capture exception"""
        mock_sentry = MagicMock()
        
        with patch('services.sentry_integration.sentry_sdk', mock_sentry):
            from services.sentry_integration import capture_exception
            
            exception = ValueError("Test error")
            capture_exception(exception)
            
            mock_sentry.capture_exception.assert_called_once_with(exception)
    
    def test_capture_exception_with_tags(self):
        """Should capture exception with tags"""
        mock_sentry = MagicMock()
        
        with patch('services.sentry_integration.sentry_sdk', mock_sentry):
            from services.sentry_integration import capture_exception
            
            exception = ValueError("Test error")
            capture_exception(exception, user_id='user123', tenant_id='tenant456')
            
            assert mock_sentry.set_tag.call_count == 2
            mock_sentry.set_tag.assert_any_call('user_id', 'user123')
            mock_sentry.set_tag.assert_any_call('tenant_id', 'tenant456')
            mock_sentry.capture_exception.assert_called_once_with(exception)


class TestCaptureMessage:
    """Test message capture functionality"""
    
    def test_capture_message_when_sentry_disabled(self):
        """Should log message when Sentry is disabled"""
        with patch('services.sentry_integration.sentry_sdk', None):
            with patch('services.sentry_integration.logger') as mock_logger:
                from services.sentry_integration import capture_message
                
                capture_message("Test message", level='info')
                
                mock_logger.log.assert_called_once()
    
    def test_capture_message_basic(self):
        """Should capture message with default level"""
        mock_sentry = MagicMock()
        
        with patch('services.sentry_integration.sentry_sdk', mock_sentry):
            from services.sentry_integration import capture_message
            
            capture_message("Test message")
            
            mock_sentry.capture_message.assert_called_once_with("Test message", level='info')
    
    def test_capture_message_with_level(self):
        """Should capture message with custom level"""
        mock_sentry = MagicMock()
        
        with patch('services.sentry_integration.sentry_sdk', mock_sentry):
            from services.sentry_integration import capture_message
            
            capture_message("Warning message", level='warning')
            
            mock_sentry.capture_message.assert_called_once_with("Warning message", level='warning')
    
    def test_capture_message_with_tags(self):
        """Should capture message with tags"""
        mock_sentry = MagicMock()
        
        with patch('services.sentry_integration.sentry_sdk', mock_sentry):
            from services.sentry_integration import capture_message
            
            capture_message("Test message", level='error', component='api', action='request')
            
            assert mock_sentry.set_tag.call_count == 2
            mock_sentry.set_tag.assert_any_call('component', 'api')
            mock_sentry.set_tag.assert_any_call('action', 'request')
            mock_sentry.capture_message.assert_called_once()


class TestMonitorPerformance:
    """Test performance monitoring decorator"""
    
    def test_monitor_performance_when_sentry_disabled(self):
        """Should execute function normally when Sentry is disabled"""
        with patch('services.sentry_integration.sentry_sdk', None):
            from services.sentry_integration import monitor_performance
            
            @monitor_performance("test_transaction")
            def test_func(x, y):
                return x + y
            
            result = test_func(2, 3)
            assert result == 5
    
    def test_monitor_performance_with_sentry_enabled(self):
        """Should wrap function in transaction when Sentry is enabled"""
        mock_sentry = MagicMock()
        mock_transaction = MagicMock()
        mock_sentry.start_transaction.return_value.__enter__.return_value = mock_transaction
        
        with patch('services.sentry_integration.sentry_sdk', mock_sentry):
            from services.sentry_integration import monitor_performance
            
            @monitor_performance("test_transaction")
            def test_func(x, y):
                return x + y
            
            result = test_func(2, 3)
            
            assert result == 5
            mock_sentry.start_transaction.assert_called_once_with(
                op="function",
                name="test_transaction"
            )


class TestStartTransaction:
    """Test transaction start functionality"""
    
    def test_start_transaction_when_sentry_disabled(self):
        """Should return None when Sentry is disabled"""
        with patch('services.sentry_integration.sentry_sdk', None):
            from services.sentry_integration import start_transaction
            
            result = start_transaction("http.server", "GET /api/users")
            
            assert result is None
    
    def test_start_transaction_with_sentry_enabled(self):
        """Should start transaction when Sentry is enabled"""
        mock_sentry = MagicMock()
        mock_transaction = MagicMock()
        mock_sentry.start_transaction.return_value = mock_transaction
        
        with patch('services.sentry_integration.sentry_sdk', mock_sentry):
            from services.sentry_integration import start_transaction
            
            result = start_transaction("http.server", "GET /api/users")
            
            assert result == mock_transaction
            mock_sentry.start_transaction.assert_called_once_with(
                op="http.server",
                name="GET /api/users"
            )


class TestStartSpan:
    """Test span start functionality"""
    
    def test_start_span_when_sentry_disabled(self):
        """Should return None when Sentry is disabled"""
        with patch('services.sentry_integration.sentry_sdk', None):
            from services.sentry_integration import start_span
            
            result = start_span("db.query", "SELECT * FROM users")
            
            assert result is None
    
    def test_start_span_with_sentry_enabled(self):
        """Should start span when Sentry is enabled"""
        mock_sentry = MagicMock()
        mock_span = MagicMock()
        mock_sentry.start_span.return_value = mock_span
        
        with patch('services.sentry_integration.sentry_sdk', mock_sentry):
            from services.sentry_integration import start_span
            
            result = start_span("db.query", "SELECT * FROM users")
            
            assert result == mock_span
            mock_sentry.start_span.assert_called_once_with(
                op="db.query",
                description="SELECT * FROM users"
            )


class TestSentryMetrics:
    """Test SentryMetrics class"""
    
    def test_increment_when_sentry_disabled(self):
        """Should do nothing when Sentry is disabled"""
        with patch('services.sentry_integration.sentry_sdk', None):
            from services.sentry_integration import SentryMetrics
            
            SentryMetrics.increment("test_metric", value=1.0)
    
    def test_increment_with_sentry_enabled(self):
        """Should increment metric when Sentry is enabled"""
        mock_sentry = MagicMock()
        
        with patch('services.sentry_integration.sentry_sdk', mock_sentry):
            from services.sentry_integration import SentryMetrics
            
            SentryMetrics.increment("test_metric", value=2.0, tags={'env': 'test'})
            
            mock_sentry.metrics.incr.assert_called_once_with(
                key="test_metric",
                value=2.0,
                tags={'env': 'test'}
            )
    
    def test_increment_with_attribute_error(self):
        """Should handle AttributeError gracefully"""
        mock_sentry = MagicMock()
        mock_sentry.metrics.incr.side_effect = AttributeError("metrics not available")
        
        with patch('services.sentry_integration.sentry_sdk', mock_sentry):
            from services.sentry_integration import SentryMetrics
            
            SentryMetrics.increment("test_metric")
    
    def test_gauge_when_sentry_disabled(self):
        """Should do nothing when Sentry is disabled"""
        with patch('services.sentry_integration.sentry_sdk', None):
            from services.sentry_integration import SentryMetrics
            
            SentryMetrics.gauge("test_gauge", value=42.0)
    
    def test_gauge_with_sentry_enabled(self):
        """Should set gauge metric when Sentry is enabled"""
        mock_sentry = MagicMock()
        
        with patch('services.sentry_integration.sentry_sdk', mock_sentry):
            from services.sentry_integration import SentryMetrics
            
            SentryMetrics.gauge("test_gauge", value=42.0, tags={'env': 'test'})
            
            mock_sentry.metrics.gauge.assert_called_once_with(
                key="test_gauge",
                value=42.0,
                tags={'env': 'test'}
            )
    
    def test_distribution_when_sentry_disabled(self):
        """Should do nothing when Sentry is disabled"""
        with patch('services.sentry_integration.sentry_sdk', None):
            from services.sentry_integration import SentryMetrics
            
            SentryMetrics.distribution("test_dist", value=123.45)
    
    def test_distribution_with_sentry_enabled(self):
        """Should record distribution metric when Sentry is enabled"""
        mock_sentry = MagicMock()
        
        with patch('services.sentry_integration.sentry_sdk', mock_sentry):
            from services.sentry_integration import SentryMetrics
            
            SentryMetrics.distribution("test_dist", value=123.45, tags={'env': 'test'})
            
            mock_sentry.metrics.distribution.assert_called_once_with(
                key="test_dist",
                value=123.45,
                tags={'env': 'test'}
            )
