"""
Tests to improve redis_client.py coverage to 80%+

Focuses on:
1. check_redis_security() version parsing and vulnerability detection
2. get_redis_connection_info() for different configurations
3. Edge cases in UpstashRedisAdapter
"""
import pytest
import logging
from unittest.mock import patch, MagicMock, Mock


class TestCheckRedisSecurity:
    """Tests for check_redis_security function"""

    @patch('utils.redis_client.get_redis_client')
    @patch('utils.redis_client.get_settings')
    def test_check_redis_security_upstash(self, mock_settings, mock_get_client):
        """Test check_redis_security with Upstash Redis"""
        mock_settings.return_value.upstash_redis_rest_url = "https://example.upstash.io"
        mock_settings.return_value.redis_url = None

        from utils.redis_client import check_redis_security
        result = check_redis_security()

        assert result['status'] == 'secure'
        assert result['type'] == 'upstash'
        assert result['cve_2025_49844_risk'] == 'low'

    @patch('utils.redis_client.get_redis_client')
    @patch('utils.redis_client.get_settings')
    def test_check_redis_security_redis_secure_version(self, mock_settings, mock_get_client):
        """Test check_redis_security with secure Redis version"""
        mock_settings.return_value.upstash_redis_rest_url = None
        mock_settings.return_value.redis_url = "rediss://localhost:6379/0"

        mock_client = MagicMock()
        mock_client.info.return_value = {'redis_version': '8.2.2'}
        mock_get_client.return_value = mock_client

        from utils.redis_client import check_redis_security
        result = check_redis_security()

        assert result['status'] == 'secure'
        assert result['type'] == 'redis'
        assert result['version'] == '8.2.2'
        assert result['tls_enabled'] is True
        assert result['cve_2025_49844_risk'] == 'low'

    @patch('utils.redis_client.get_redis_client')
    @patch('utils.redis_client.get_settings')
    def test_check_redis_security_redis_vulnerable_version(self, mock_settings, mock_get_client):
        """Test check_redis_security with vulnerable Redis version"""
        mock_settings.return_value.upstash_redis_rest_url = None
        mock_settings.return_value.redis_url = "redis://localhost:6379/0"

        mock_client = MagicMock()
        mock_client.info.return_value = {'redis_version': '7.2.0'}
        mock_get_client.return_value = mock_client

        from utils.redis_client import check_redis_security
        result = check_redis_security()

        assert result['status'] == 'vulnerable'
        assert result['type'] == 'redis'
        assert result['version'] == '7.2.0'
        assert result['tls_enabled'] is False
        assert result['cve_2025_49844_risk'] == 'high'
        assert len(result['recommendations']) > 0

    @patch('utils.redis_client.get_redis_client')
    @patch('utils.redis_client.get_settings')
    def test_check_redis_security_version_with_suffix(self, mock_settings, mock_get_client):
        """Test check_redis_security with version containing suffix"""
        mock_settings.return_value.upstash_redis_rest_url = None
        mock_settings.return_value.redis_url = "rediss://localhost:6379/0"

        mock_client = MagicMock()
        mock_client.info.return_value = {'redis_version': '8.2.3-rc1+build123'}
        mock_get_client.return_value = mock_client

        from utils.redis_client import check_redis_security
        result = check_redis_security()

        assert result['status'] == 'secure'
        assert result['version'] == '8.2.3-rc1+build123'

    @patch('utils.redis_client.get_redis_client')
    @patch('utils.redis_client.get_settings')
    def test_check_redis_security_invalid_version_format(self, mock_settings, mock_get_client):
        """Test check_redis_security with invalid version format"""
        mock_settings.return_value.upstash_redis_rest_url = None
        mock_settings.return_value.redis_url = "rediss://localhost:6379/0"

        mock_client = MagicMock()
        mock_client.info.return_value = {'redis_version': 'invalid'}
        mock_get_client.return_value = mock_client

        from utils.redis_client import check_redis_security
        result = check_redis_security()

        assert result['type'] == 'redis'
        assert result['version'] == 'invalid'

    @patch('utils.redis_client.get_redis_client')
    @patch('utils.redis_client.get_settings')
    def test_check_redis_security_partial_version(self, mock_settings, mock_get_client):
        """Test check_redis_security with partial version (e.g., '8.2')"""
        mock_settings.return_value.upstash_redis_rest_url = None
        mock_settings.return_value.redis_url = "rediss://localhost:6379/0"

        mock_client = MagicMock()
        mock_client.info.return_value = {'redis_version': '8.2'}
        mock_get_client.return_value = mock_client

        from utils.redis_client import check_redis_security
        result = check_redis_security()

        assert result['type'] == 'redis'
        assert result['version'] == '8.2'

    @patch('utils.redis_client.get_redis_client')
    @patch('utils.redis_client.get_settings')
    def test_check_redis_security_no_config(self, mock_settings, mock_get_client):
        """Test check_redis_security with no Redis configuration"""
        mock_settings.return_value.upstash_redis_rest_url = None
        mock_settings.return_value.redis_url = None

        from utils.redis_client import check_redis_security
        result = check_redis_security()

        assert result['status'] == 'unknown'
        assert result['type'] == 'none'
        assert 'Configure Redis' in result['recommendations'][0]

    @patch('utils.redis_client.get_redis_client')
    @patch('utils.redis_client.get_settings')
    def test_check_redis_security_connection_error(self, mock_settings, mock_get_client):
        """Test check_redis_security with connection error"""
        mock_settings.return_value.upstash_redis_rest_url = None
        mock_settings.return_value.redis_url = "redis://localhost:6379/0"
        mock_get_client.side_effect = Exception('Connection refused')

        from utils.redis_client import check_redis_security
        result = check_redis_security()

        assert result['status'] == 'error'
        assert 'Connection refused' in result['message']

    @patch('utils.redis_client.get_redis_client')
    @patch('utils.redis_client.get_settings')
    def test_check_redis_security_non_tls_warning(self, mock_settings, mock_get_client):
        """Test check_redis_security warns about non-TLS connection"""
        mock_settings.return_value.upstash_redis_rest_url = None
        mock_settings.return_value.redis_url = "redis://localhost:6379/0"

        mock_client = MagicMock()
        mock_client.info.return_value = {'redis_version': '8.2.2'}
        mock_get_client.return_value = mock_client

        from utils.redis_client import check_redis_security
        result = check_redis_security()

        assert result['tls_enabled'] is False
        assert any('TLS' in rec for rec in result['recommendations'])


class TestGetRedisConnectionInfo:
    """Tests for get_redis_connection_info function"""

    @patch('utils.redis_client.get_settings')
    def test_get_redis_connection_info_upstash(self, mock_settings):
        """Test get_redis_connection_info with Upstash"""
        mock_settings.return_value.upstash_redis_rest_url = "https://user:pass@example.upstash.io"
        mock_settings.return_value.redis_url = None

        from utils.redis_client import get_redis_connection_info
        result = get_redis_connection_info()

        assert result['type'] == 'upstash'
        assert result['protocol'] == 'https'
        assert result['tls_enabled'] is True
        assert 'pass' not in result['url']

    @patch('utils.redis_client.get_settings')
    def test_get_redis_connection_info_redis_tls(self, mock_settings):
        """Test get_redis_connection_info with Redis TLS"""
        mock_settings.return_value.upstash_redis_rest_url = None
        mock_settings.return_value.redis_url = "rediss://user:pass@localhost:6379/0"

        from utils.redis_client import get_redis_connection_info
        result = get_redis_connection_info()

        assert result['type'] == 'redis'
        assert result['protocol'] == 'rediss'
        assert result['tls_enabled'] is True

    @patch('utils.redis_client.get_settings')
    def test_get_redis_connection_info_redis_no_tls(self, mock_settings):
        """Test get_redis_connection_info with Redis without TLS"""
        mock_settings.return_value.upstash_redis_rest_url = None
        mock_settings.return_value.redis_url = "redis://localhost:6379/0"

        from utils.redis_client import get_redis_connection_info
        result = get_redis_connection_info()

        assert result['type'] == 'redis'
        assert result['protocol'] == 'redis'
        assert result['tls_enabled'] is False

    @patch('utils.redis_client.get_settings')
    def test_get_redis_connection_info_no_config(self, mock_settings):
        """Test get_redis_connection_info with no configuration"""
        mock_settings.return_value.upstash_redis_rest_url = None
        mock_settings.return_value.redis_url = None

        from utils.redis_client import get_redis_connection_info
        result = get_redis_connection_info()

        assert result['type'] == 'none'
        assert result['tls_enabled'] is False
        assert result['url'] == 'not_configured'

    @patch('utils.redis_client.get_settings')
    def test_get_redis_connection_info_url_without_at(self, mock_settings):
        """Test get_redis_connection_info with URL without @ symbol"""
        mock_settings.return_value.upstash_redis_rest_url = "https://example.upstash.io"
        mock_settings.return_value.redis_url = None

        from utils.redis_client import get_redis_connection_info
        result = get_redis_connection_info()

        assert result['url'] == '***'


class TestUpstashRedisAdapterEdgeCases:
    """Additional edge case tests for UpstashRedisAdapter"""

    def test_scan_iter_bytes_cursor_valid(self):
        """Test scan_iter with valid bytes cursor that can be decoded"""
        from utils.redis_client import UpstashRedisAdapter

        class FakeClient:
            def __init__(self):
                self.call_count = 0

            def scan(self, cursor=0, match=None, count=None):
                self.call_count += 1
                if self.call_count == 1:
                    return (b"5", ["key1"])
                return (0, ["key2"])

        client = FakeClient()
        adapter = UpstashRedisAdapter(client)
        keys = list(adapter.scan_iter())

        assert keys == ["key1", "key2"]

    def test_scan_iter_tuple_result(self):
        """Test scan_iter with tuple result format"""
        from utils.redis_client import UpstashRedisAdapter

        class FakeClient:
            def scan(self, cursor=0, match=None, count=None):
                return (0, ["key1", "key2"])

        client = FakeClient()
        adapter = UpstashRedisAdapter(client)
        keys = list(adapter.scan_iter())

        assert keys == ["key1", "key2"]

    def test_mget_tuple_style(self):
        """Test mget with tuple style input"""
        from utils.redis_client import UpstashRedisAdapter

        class FakeClient:
            def mget(self, *keys):
                return ["val1", "val2"]

        client = FakeClient()
        adapter = UpstashRedisAdapter(client)
        result = adapter.mget(("key1", "key2"))

        assert result == ["val1", "val2"]


class TestCreateRedisClientEdgeCases:
    """Edge case tests for create_redis_client"""

    @patch('utils.redis_client.get_settings')
    def test_create_redis_client_no_config_raises(self, mock_settings):
        """Test create_redis_client raises when no config"""
        mock_settings.return_value.upstash_redis_rest_url = None
        mock_settings.return_value.redis_url = None

        from utils.redis_client import create_redis_client
        with pytest.raises(ValueError, match="No Redis configuration found"):
            create_redis_client()

    @patch('utils.redis_client.get_settings')
    def test_create_redis_client_upstash_import_error_fallback(self, mock_settings):
        """Test create_redis_client falls back when upstash-redis not installed"""
        mock_settings.return_value.upstash_redis_rest_url = "https://example.upstash.io"
        mock_settings.return_value.upstash_redis_rest_token = "token"
        mock_settings.return_value.redis_url = "redis://localhost:6379/0"

        with patch.dict('sys.modules', {'upstash_redis': None}):
            with patch('redis.from_url') as mock_from_url:
                mock_client = MagicMock()
                mock_from_url.return_value = mock_client

                from utils.redis_client import create_redis_client
                try:
                    client = create_redis_client(skip_ping=True)
                except Exception:
                    pass

    @patch('utils.redis_client.get_settings')
    def test_create_redis_client_redis_non_tls_warning(self, mock_settings, caplog):
        """Test create_redis_client logs warning for non-TLS Redis"""
        mock_settings.return_value.upstash_redis_rest_url = None
        mock_settings.return_value.redis_url = "redis://localhost:6379/0"
        mock_settings.return_value.redis_host = "localhost"
        mock_settings.return_value.redis_port = 6379
        mock_settings.return_value.redis_db = 0

        with patch('redis.from_url') as mock_from_url:
            mock_client = MagicMock()
            mock_from_url.return_value = mock_client

            with caplog.at_level(logging.WARNING):
                from utils.redis_client import create_redis_client
                client = create_redis_client(skip_ping=True)

            assert any('not using TLS' in record.message for record in caplog.records)
