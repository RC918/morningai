"""
Unit tests for services.sentry_integration module

Issue #1915 - sentry_integration.py tests

Tests Sentry integration functionality including:
- Sensitive data scrubbing
- User context management
- Custom context setting
- Breadcrumb functionality
- Exception and message capture
- Performance monitoring decorators
- Transaction and span management
- SentryMetrics class methods
"""
from unittest.mock import patch, MagicMock


class TestScrubSensitiveData:
    """Test sensitive data scrubbing functionality"""

    def test_scrub_sensitive_data_with_none_event(self):
        """Should return None when event is None"""
        from services.sentry_integration import scrub_sensitive_data

        result = scrub_sensitive_data(None, {})

        assert result is None

    def test_scrub_sensitive_data_with_empty_event(self):
        """Should return None when event is empty dict (falsy)"""
        from services.sentry_integration import scrub_sensitive_data

        event = {}
        result = scrub_sensitive_data(event, {})

        assert result is None

    def test_scrub_sensitive_data_headers_authorization(self):
        """Should redact authorization header"""
        from services.sentry_integration import scrub_sensitive_data

        event = {
            'request': {
                'headers': {
                    'authorization': 'Bearer secret-token',
                    'content-type': 'application/json'
                }
            }
        }

        result = scrub_sensitive_data(event, {})

        assert result['request']['headers']['authorization'] == '[REDACTED]'
        assert result['request']['headers']['content-type'] == 'application/json'

    def test_scrub_sensitive_data_headers_api_key(self):
        """Should redact api_key header"""
        from services.sentry_integration import scrub_sensitive_data

        event = {
            'request': {
                'headers': {
                    'api_key': 'my-api-key',
                    'x-request-id': '12345'
                }
            }
        }

        result = scrub_sensitive_data(event, {})

        assert result['request']['headers']['api_key'] == '[REDACTED]'
        assert result['request']['headers']['x-request-id'] == '12345'

    def test_scrub_sensitive_data_headers_token(self):
        """Should redact token header"""
        from services.sentry_integration import scrub_sensitive_data

        event = {
            'request': {
                'headers': {
                    'token': 'secret-token-value'
                }
            }
        }

        result = scrub_sensitive_data(event, {})

        assert result['request']['headers']['token'] == '[REDACTED]'

    def test_scrub_sensitive_data_headers_secret(self):
        """Should redact secret header"""
        from services.sentry_integration import scrub_sensitive_data

        event = {
            'request': {
                'headers': {
                    'secret': 'my-secret'
                }
            }
        }

        result = scrub_sensitive_data(event, {})

        assert result['request']['headers']['secret'] == '[REDACTED]'

    def test_scrub_sensitive_data_query_string_with_api_key(self):
        """Should redact query string containing api_key"""
        from services.sentry_integration import scrub_sensitive_data

        event = {
            'request': {
                'query_string': 'api_key=secret123&user=john'
            }
        }

        result = scrub_sensitive_data(event, {})

        assert result['request']['query_string'] == '[REDACTED]'

    def test_scrub_sensitive_data_query_string_with_token(self):
        """Should redact query string containing token"""
        from services.sentry_integration import scrub_sensitive_data

        event = {
            'request': {
                'query_string': 'token=abc123&page=1'
            }
        }

        result = scrub_sensitive_data(event, {})

        assert result['request']['query_string'] == '[REDACTED]'

    def test_scrub_sensitive_data_query_string_safe(self):
        """Should not redact safe query strings"""
        from services.sentry_integration import scrub_sensitive_data

        event = {
            'request': {
                'query_string': 'page=1&limit=10'
            }
        }

        result = scrub_sensitive_data(event, {})

        assert result['request']['query_string'] == 'page=1&limit=10'

    def test_scrub_sensitive_data_request_body_password(self):
        """Should redact password in request body"""
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

    def test_scrub_sensitive_data_request_body_access_token(self):
        """Should redact access_token in request body"""
        from services.sentry_integration import scrub_sensitive_data

        event = {
            'request': {
                'data': {
                    'access_token': 'token123',
                    'user_id': '456'
                }
            }
        }

        result = scrub_sensitive_data(event, {})

        assert result['request']['data']['access_token'] == '[REDACTED]'
        assert result['request']['data']['user_id'] == '456'

    def test_scrub_sensitive_data_request_body_non_dict(self):
        """Should handle non-dict request data gracefully"""
        from services.sentry_integration import scrub_sensitive_data

        event = {
            'request': {
                'data': 'raw string data'
            }
        }

        result = scrub_sensitive_data(event, {})

        assert result['request']['data'] == 'raw string data'

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

    def test_scrub_sensitive_data_extra_jwt(self):
        """Should redact jwt in extra context"""
        from services.sentry_integration import scrub_sensitive_data

        event = {
            'extra': {
                'jwt': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
                'request_id': 'req-123'
            }
        }

        result = scrub_sensitive_data(event, {})

        assert result['extra']['jwt'] == '[REDACTED]'
        assert result['extra']['request_id'] == 'req-123'

    def test_scrub_sensitive_data_extra_refresh_token(self):
        """Should redact refresh_token in extra context"""
        from services.sentry_integration import scrub_sensitive_data

        event = {
            'extra': {
                'refresh_token': 'refresh-token-value'
            }
        }

        result = scrub_sensitive_data(event, {})

        assert result['extra']['refresh_token'] == '[REDACTED]'

    def test_scrub_sensitive_data_extra_bearer(self):
        """Should redact bearer in extra context"""
        from services.sentry_integration import scrub_sensitive_data

        event = {
            'extra': {
                'bearer': 'bearer-token-value'
            }
        }

        result = scrub_sensitive_data(event, {})

        assert result['extra']['bearer'] == '[REDACTED]'

    def test_scrub_sensitive_data_multiple_sections(self):
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

    def test_scrub_sensitive_data_no_request_section(self):
        """Should handle event without request section"""
        from services.sentry_integration import scrub_sensitive_data

        event = {
            'extra': {
                'user_id': '123'
            }
        }

        result = scrub_sensitive_data(event, {})

        assert result['extra']['user_id'] == '123'
        assert 'request' not in result


class TestSetUserContext:
    """Test user context setting functionality"""

    def test_set_user_context_when_sentry_disabled(self):
        """Should do nothing when Sentry is disabled"""
        with patch('services.sentry_integration.sentry_sdk', None):
            from services.sentry_integration import set_user_context

            set_user_context(user_id='user123', tenant_id='tenant456')

    def test_set_user_context_with_user_id_only(self):
        """Should set user context with user_id only"""
        mock_sentry = MagicMock()

        with patch('services.sentry_integration.sentry_sdk', mock_sentry):
            from services.sentry_integration import set_user_context

            set_user_context(user_id='user123')

            mock_sentry.set_user.assert_called_once_with({'id': 'user123'})

    def test_set_user_context_with_tenant_id_only(self):
        """Should set user context with tenant_id only"""
        mock_sentry = MagicMock()

        with patch('services.sentry_integration.sentry_sdk', mock_sentry):
            from services.sentry_integration import set_user_context

            set_user_context(tenant_id='tenant456')

            mock_sentry.set_user.assert_called_once_with({'tenant_id': 'tenant456'})

    def test_set_user_context_with_both_ids(self):
        """Should set user context with both user_id and tenant_id"""
        mock_sentry = MagicMock()

        with patch('services.sentry_integration.sentry_sdk', mock_sentry):
            from services.sentry_integration import set_user_context

            set_user_context(user_id='user123', tenant_id='tenant456')

            mock_sentry.set_user.assert_called_once_with({
                'id': 'user123',
                'tenant_id': 'tenant456'
            })

    def test_set_user_context_with_extra_kwargs(self):
        """Should set user context with additional kwargs"""
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

    def test_set_user_context_with_no_params(self):
        """Should set empty user context when no params provided"""
        mock_sentry = MagicMock()

        with patch('services.sentry_integration.sentry_sdk', mock_sentry):
            from services.sentry_integration import set_user_context

            set_user_context()

            mock_sentry.set_user.assert_called_once_with({})


class TestSetContext:
    """Test custom context setting functionality"""

    def test_set_context_when_sentry_disabled(self):
        """Should do nothing when Sentry is disabled"""
        with patch('services.sentry_integration.sentry_sdk', None):
            from services.sentry_integration import set_context

            set_context('agent', {'agent_id': 'agent123'})

    def test_set_context_with_agent_data(self):
        """Should set custom context with agent data"""
        mock_sentry = MagicMock()

        with patch('services.sentry_integration.sentry_sdk', mock_sentry):
            from services.sentry_integration import set_context

            context_data = {'agent_id': 'agent123', 'task_id': 'task456'}
            set_context('agent', context_data)

            mock_sentry.set_context.assert_called_once_with('agent', context_data)

    def test_set_context_with_task_data(self):
        """Should set custom context with task data"""
        mock_sentry = MagicMock()

        with patch('services.sentry_integration.sentry_sdk', mock_sentry):
            from services.sentry_integration import set_context

            context_data = {'task_id': 'task123', 'status': 'running'}
            set_context('task', context_data)

            mock_sentry.set_context.assert_called_once_with('task', context_data)

    def test_set_context_with_empty_data(self):
        """Should set custom context with empty data"""
        mock_sentry = MagicMock()

        with patch('services.sentry_integration.sentry_sdk', mock_sentry):
            from services.sentry_integration import set_context

            set_context('empty', {})

            mock_sentry.set_context.assert_called_once_with('empty', {})


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

    def test_add_breadcrumb_with_warning_level(self):
        """Should add breadcrumb with warning level"""
        mock_sentry = MagicMock()

        with patch('services.sentry_integration.sentry_sdk', mock_sentry):
            from services.sentry_integration import add_breadcrumb

            add_breadcrumb('api_call', 'Rate limit warning', level='warning')

            mock_sentry.add_breadcrumb.assert_called_once_with(
                category='api_call',
                message='Rate limit warning',
                level='warning',
                data={}
            )

    def test_add_breadcrumb_with_error_level(self):
        """Should add breadcrumb with error level"""
        mock_sentry = MagicMock()

        with patch('services.sentry_integration.sentry_sdk', mock_sentry):
            from services.sentry_integration import add_breadcrumb

            add_breadcrumb('db_query', 'Query failed', level='error')

            mock_sentry.add_breadcrumb.assert_called_once_with(
                category='db_query',
                message='Query failed',
                level='error',
                data={}
            )

    def test_add_breadcrumb_with_data(self):
        """Should add breadcrumb with custom data"""
        mock_sentry = MagicMock()

        with patch('services.sentry_integration.sentry_sdk', mock_sentry):
            from services.sentry_integration import add_breadcrumb

            data = {'user_id': '123', 'endpoint': '/api/users'}
            add_breadcrumb('api_call', 'GET /api/users', data=data)

            mock_sentry.add_breadcrumb.assert_called_once_with(
                category='api_call',
                message='GET /api/users',
                level='info',
                data=data
            )

    def test_add_breadcrumb_with_all_params(self):
        """Should add breadcrumb with all parameters"""
        mock_sentry = MagicMock()

        with patch('services.sentry_integration.sentry_sdk', mock_sentry):
            from services.sentry_integration import add_breadcrumb

            data = {'query': 'SELECT * FROM users', 'duration_ms': 150}
            add_breadcrumb('db_query', 'User lookup', level='debug', data=data)

            mock_sentry.add_breadcrumb.assert_called_once_with(
                category='db_query',
                message='User lookup',
                level='debug',
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

    def test_capture_exception_with_single_tag(self):
        """Should capture exception with single tag"""
        mock_sentry = MagicMock()

        with patch('services.sentry_integration.sentry_sdk', mock_sentry):
            from services.sentry_integration import capture_exception

            exception = ValueError("Test error")
            capture_exception(exception, user_id='user123')

            mock_sentry.set_tag.assert_called_once_with('user_id', 'user123')
            mock_sentry.capture_exception.assert_called_once_with(exception)

    def test_capture_exception_with_multiple_tags(self):
        """Should capture exception with multiple tags"""
        mock_sentry = MagicMock()

        with patch('services.sentry_integration.sentry_sdk', mock_sentry):
            from services.sentry_integration import capture_exception

            exception = ValueError("Test error")
            capture_exception(exception, user_id='user123', tenant_id='tenant456')

            assert mock_sentry.set_tag.call_count == 2
            mock_sentry.set_tag.assert_any_call('user_id', 'user123')
            mock_sentry.set_tag.assert_any_call('tenant_id', 'tenant456')
            mock_sentry.capture_exception.assert_called_once_with(exception)

    def test_capture_exception_with_custom_tags(self):
        """Should capture exception with custom tags"""
        mock_sentry = MagicMock()

        with patch('services.sentry_integration.sentry_sdk', mock_sentry):
            from services.sentry_integration import capture_exception

            exception = RuntimeError("Connection failed")
            capture_exception(exception, component='redis', action='connect')

            assert mock_sentry.set_tag.call_count == 2
            mock_sentry.set_tag.assert_any_call('component', 'redis')
            mock_sentry.set_tag.assert_any_call('action', 'connect')


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

    def test_capture_message_with_warning_level(self):
        """Should capture message with warning level"""
        mock_sentry = MagicMock()

        with patch('services.sentry_integration.sentry_sdk', mock_sentry):
            from services.sentry_integration import capture_message

            capture_message("Warning message", level='warning')

            mock_sentry.capture_message.assert_called_once_with("Warning message", level='warning')

    def test_capture_message_with_error_level(self):
        """Should capture message with error level"""
        mock_sentry = MagicMock()

        with patch('services.sentry_integration.sentry_sdk', mock_sentry):
            from services.sentry_integration import capture_message

            capture_message("Error message", level='error')

            mock_sentry.capture_message.assert_called_once_with("Error message", level='error')

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

    def test_monitor_performance_preserves_function_name(self):
        """Should preserve decorated function name"""
        with patch('services.sentry_integration.sentry_sdk', None):
            from services.sentry_integration import monitor_performance

            @monitor_performance("test_transaction")
            def my_function():
                pass

            assert my_function.__name__ == 'my_function'

    def test_monitor_performance_with_kwargs(self):
        """Should handle function with kwargs"""
        with patch('services.sentry_integration.sentry_sdk', None):
            from services.sentry_integration import monitor_performance

            @monitor_performance("test_transaction")
            def test_func(a, b=10):
                return a + b

            result = test_func(5, b=20)
            assert result == 25


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

    def test_start_transaction_with_kwargs(self):
        """Should pass additional kwargs to transaction"""
        mock_sentry = MagicMock()
        mock_transaction = MagicMock()
        mock_sentry.start_transaction.return_value = mock_transaction

        with patch('services.sentry_integration.sentry_sdk', mock_sentry):
            from services.sentry_integration import start_transaction

            start_transaction("http.server", "GET /api/users", sampled=True)

            mock_sentry.start_transaction.assert_called_once_with(
                op="http.server",
                name="GET /api/users",
                sampled=True
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

    def test_start_span_with_different_ops(self):
        """Should start span with different operation types"""
        mock_sentry = MagicMock()
        mock_span = MagicMock()
        mock_sentry.start_span.return_value = mock_span

        with patch('services.sentry_integration.sentry_sdk', mock_sentry):
            from services.sentry_integration import start_span

            start_span("http.client", "POST /external/api")

            mock_sentry.start_span.assert_called_once_with(
                op="http.client",
                description="POST /external/api"
            )


class TestSentryMetricsIncrement:
    """Test SentryMetrics.increment method"""

    def test_increment_when_sentry_disabled(self):
        """Should do nothing when Sentry is disabled"""
        with patch('services.sentry_integration.sentry_sdk', None):
            from services.sentry_integration import SentryMetrics

            SentryMetrics.increment("test_metric", value=1.0)

    def test_increment_with_default_value(self):
        """Should increment metric with default value"""
        mock_sentry = MagicMock()

        with patch('services.sentry_integration.sentry_sdk', mock_sentry):
            from services.sentry_integration import SentryMetrics

            SentryMetrics.increment("test_metric")

            mock_sentry.metrics.incr.assert_called_once_with(
                key="test_metric",
                value=1.0,
                tags={}
            )

    def test_increment_with_custom_value(self):
        """Should increment metric with custom value"""
        mock_sentry = MagicMock()

        with patch('services.sentry_integration.sentry_sdk', mock_sentry):
            from services.sentry_integration import SentryMetrics

            SentryMetrics.increment("test_metric", value=5.0)

            mock_sentry.metrics.incr.assert_called_once_with(
                key="test_metric",
                value=5.0,
                tags={}
            )

    def test_increment_with_tags(self):
        """Should increment metric with tags"""
        mock_sentry = MagicMock()

        with patch('services.sentry_integration.sentry_sdk', mock_sentry):
            from services.sentry_integration import SentryMetrics

            SentryMetrics.increment("test_metric", value=2.0, tags={'env': 'test', 'region': 'us-east'})

            mock_sentry.metrics.incr.assert_called_once_with(
                key="test_metric",
                value=2.0,
                tags={'env': 'test', 'region': 'us-east'}
            )

    def test_increment_handles_attribute_error(self):
        """Should handle AttributeError gracefully"""
        mock_sentry = MagicMock()
        mock_sentry.metrics.incr.side_effect = AttributeError("metrics not available")

        with patch('services.sentry_integration.sentry_sdk', mock_sentry):
            from services.sentry_integration import SentryMetrics

            SentryMetrics.increment("test_metric")


class TestSentryMetricsGauge:
    """Test SentryMetrics.gauge method"""

    def test_gauge_when_sentry_disabled(self):
        """Should do nothing when Sentry is disabled"""
        with patch('services.sentry_integration.sentry_sdk', None):
            from services.sentry_integration import SentryMetrics

            SentryMetrics.gauge("test_gauge", value=42.0)

    def test_gauge_with_value(self):
        """Should set gauge metric with value"""
        mock_sentry = MagicMock()

        with patch('services.sentry_integration.sentry_sdk', mock_sentry):
            from services.sentry_integration import SentryMetrics

            SentryMetrics.gauge("test_gauge", value=42.0)

            mock_sentry.metrics.gauge.assert_called_once_with(
                key="test_gauge",
                value=42.0,
                tags={}
            )

    def test_gauge_with_tags(self):
        """Should set gauge metric with tags"""
        mock_sentry = MagicMock()

        with patch('services.sentry_integration.sentry_sdk', mock_sentry):
            from services.sentry_integration import SentryMetrics

            SentryMetrics.gauge("test_gauge", value=100.0, tags={'env': 'production'})

            mock_sentry.metrics.gauge.assert_called_once_with(
                key="test_gauge",
                value=100.0,
                tags={'env': 'production'}
            )

    def test_gauge_handles_attribute_error(self):
        """Should handle AttributeError gracefully"""
        mock_sentry = MagicMock()
        mock_sentry.metrics.gauge.side_effect = AttributeError("metrics not available")

        with patch('services.sentry_integration.sentry_sdk', mock_sentry):
            from services.sentry_integration import SentryMetrics

            SentryMetrics.gauge("test_gauge", value=42.0)


class TestSentryMetricsDistribution:
    """Test SentryMetrics.distribution method"""

    def test_distribution_when_sentry_disabled(self):
        """Should do nothing when Sentry is disabled"""
        with patch('services.sentry_integration.sentry_sdk', None):
            from services.sentry_integration import SentryMetrics

            SentryMetrics.distribution("test_dist", value=123.45)

    def test_distribution_with_value(self):
        """Should record distribution metric with value"""
        mock_sentry = MagicMock()

        with patch('services.sentry_integration.sentry_sdk', mock_sentry):
            from services.sentry_integration import SentryMetrics

            SentryMetrics.distribution("test_dist", value=123.45)

            mock_sentry.metrics.distribution.assert_called_once_with(
                key="test_dist",
                value=123.45,
                tags={}
            )

    def test_distribution_with_tags(self):
        """Should record distribution metric with tags"""
        mock_sentry = MagicMock()

        with patch('services.sentry_integration.sentry_sdk', mock_sentry):
            from services.sentry_integration import SentryMetrics

            SentryMetrics.distribution("response_time", value=250.5, tags={'endpoint': '/api/users'})

            mock_sentry.metrics.distribution.assert_called_once_with(
                key="response_time",
                value=250.5,
                tags={'endpoint': '/api/users'}
            )

    def test_distribution_handles_attribute_error(self):
        """Should handle AttributeError gracefully"""
        mock_sentry = MagicMock()
        mock_sentry.metrics.distribution.side_effect = AttributeError("metrics not available")

        with patch('services.sentry_integration.sentry_sdk', mock_sentry):
            from services.sentry_integration import SentryMetrics

            SentryMetrics.distribution("test_dist", value=123.45)


class TestModuleExports:
    """Test module exports"""

    def test_all_exports_defined(self):
        """Should have all expected exports in __all__"""
        from services import sentry_integration

        expected_exports = [
            'sentry_sdk',
            'set_user_context',
            'set_context',
            'add_breadcrumb',
            'capture_exception',
            'capture_message',
            'monitor_performance',
            'start_transaction',
            'start_span',
            'SentryMetrics'
        ]

        for export in expected_exports:
            assert export in sentry_integration.__all__, f"{export} not in __all__"

    def test_scrub_sensitive_data_importable(self):
        """Should be able to import scrub_sensitive_data"""
        from services.sentry_integration import scrub_sensitive_data
        assert callable(scrub_sensitive_data)

    def test_sentry_metrics_class_importable(self):
        """Should be able to import SentryMetrics class"""
        from services.sentry_integration import SentryMetrics
        assert hasattr(SentryMetrics, 'increment')
        assert hasattr(SentryMetrics, 'gauge')
        assert hasattr(SentryMetrics, 'distribution')
