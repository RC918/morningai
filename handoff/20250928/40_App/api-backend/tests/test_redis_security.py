"""
Tests for Redis security check functionality (CVE-2025-49844)
"""
import pytest
import os
from unittest.mock import patch, MagicMock
from src.utils.redis_client import check_redis_security


class TestRedisSecurityCheck:
    """Test check_redis_security() function"""
    
    def test_check_redis_security_upstash(self):
        """Test security check with Upstash Redis (should be secure)"""
        mock_client = MagicMock()
        
        with patch.dict(os.environ, {'UPSTASH_REDIS_REST_URL': 'https://example.upstash.io'}, clear=True):
            with patch('src.utils.redis_client.get_redis_client', return_value=mock_client):
                result = check_redis_security()
                
                assert result['status'] == 'secure'
                assert result['type'] == 'upstash'
                assert result['cve_2025_49844_risk'] == 'low'
                assert len(result['recommendations']) == 0
                assert 'cloud-managed' in result['message'].lower()
    
    def test_check_redis_security_vulnerable_version(self):
        """Test security check with vulnerable Redis version (< 8.2.2)"""
        mock_client = MagicMock()
        mock_client.info.return_value = {
            'redis_version': '7.2.0'
        }
        
        with patch.dict(os.environ, {'REDIS_URL': 'rediss://example.com:6380/0'}, clear=True):
            with patch('src.utils.redis_client.get_redis_client', return_value=mock_client):
                result = check_redis_security()
                
                assert result['status'] == 'vulnerable'
                assert result['type'] == 'redis'
                assert result['version'] == '7.2.0'
                assert result['cve_2025_49844_risk'] == 'high'
                assert result['tls_enabled'] is True
                assert len(result['recommendations']) >= 1
                assert any('CVE-2025-49844' in rec for rec in result['recommendations'])
    
    def test_check_redis_security_secure_version(self):
        """Test security check with secure Redis version (>= 8.2.2)"""
        mock_client = MagicMock()
        mock_client.info.return_value = {
            'redis_version': '8.2.2'
        }
        
        with patch.dict(os.environ, {'REDIS_URL': 'rediss://example.com:6380/0'}, clear=True):
            with patch('src.utils.redis_client.get_redis_client', return_value=mock_client):
                result = check_redis_security()
                
                assert result['status'] == 'secure'
                assert result['type'] == 'redis'
                assert result['version'] == '8.2.2'
                assert result['cve_2025_49844_risk'] == 'low'
                assert result['tls_enabled'] is True
                assert len(result['recommendations']) == 0
    
    def test_check_redis_security_secure_version_higher(self):
        """Test security check with Redis version > 8.2.2"""
        mock_client = MagicMock()
        mock_client.info.return_value = {
            'redis_version': '8.3.0'
        }
        
        with patch.dict(os.environ, {'REDIS_URL': 'rediss://example.com:6380/0'}, clear=True):
            with patch('src.utils.redis_client.get_redis_client', return_value=mock_client):
                result = check_redis_security()
                
                assert result['status'] == 'secure'
                assert result['cve_2025_49844_risk'] == 'low'
    
    def test_check_redis_security_no_tls(self):
        """Test security check with Redis without TLS"""
        mock_client = MagicMock()
        mock_client.info.return_value = {
            'redis_version': '8.2.2'
        }
        
        with patch.dict(os.environ, {'REDIS_URL': 'redis://example.com:6379/0'}, clear=True):
            with patch('src.utils.redis_client.get_redis_client', return_value=mock_client):
                result = check_redis_security()
                
                assert result['status'] == 'secure'
                assert result['type'] == 'redis'
                assert result['tls_enabled'] is False
                assert len(result['recommendations']) >= 1
                assert any('TLS' in rec or 'rediss://' in rec for rec in result['recommendations'])
    
    def test_check_redis_security_vulnerable_no_tls(self):
        """Test security check with vulnerable Redis without TLS (worst case)"""
        mock_client = MagicMock()
        mock_client.info.return_value = {
            'redis_version': '7.0.0'
        }
        
        with patch.dict(os.environ, {'REDIS_URL': 'redis://example.com:6379/0'}, clear=True):
            with patch('src.utils.redis_client.get_redis_client', return_value=mock_client):
                result = check_redis_security()
                
                assert result['status'] == 'vulnerable'
                assert result['cve_2025_49844_risk'] == 'high'
                assert result['tls_enabled'] is False
                assert len(result['recommendations']) >= 2
    
    def test_check_redis_security_invalid_version_format(self):
        """Test security check with invalid version format"""
        mock_client = MagicMock()
        mock_client.info.return_value = {
            'redis_version': 'unknown'
        }
        
        with patch.dict(os.environ, {'REDIS_URL': 'rediss://example.com:6380/0'}, clear=True):
            with patch('src.utils.redis_client.get_redis_client', return_value=mock_client):
                result = check_redis_security()
                
                assert result['status'] == 'vulnerable'
                assert result['version'] == 'unknown'
    
    def test_check_redis_security_partial_version(self):
        """Test security check with partial version (e.g., '8.2')"""
        mock_client = MagicMock()
        mock_client.info.return_value = {
            'redis_version': '8.2'
        }
        
        with patch.dict(os.environ, {'REDIS_URL': 'rediss://example.com:6380/0'}, clear=True):
            with patch('src.utils.redis_client.get_redis_client', return_value=mock_client):
                result = check_redis_security()
                
                assert result['status'] == 'vulnerable'
                assert result['version'] == '8.2'
    
    def test_check_redis_security_no_config(self):
        """Test security check with no Redis configuration"""
        with patch.dict(os.environ, {}, clear=True):
            with patch('src.utils.redis_client.get_redis_client', side_effect=ValueError("No Redis config")):
                result = check_redis_security()
                
                assert result['status'] == 'error'
                assert result['type'] == 'unknown'
                assert result['cve_2025_49844_risk'] == 'unknown'
    
    def test_check_redis_security_connection_error(self):
        """Test security check with Redis connection error"""
        mock_client = MagicMock()
        mock_client.info.side_effect = Exception("Connection failed")
        
        with patch.dict(os.environ, {'REDIS_URL': 'rediss://example.com:6380/0'}, clear=True):
            with patch('src.utils.redis_client.get_redis_client', return_value=mock_client):
                result = check_redis_security()
                
                assert result['status'] == 'error'
                assert 'Connection failed' in result['message'] or 'Failed to check' in result['message']
    
    def test_check_redis_security_version_edge_case_8_2_1(self):
        """Test security check with Redis 8.2.1 (last vulnerable version)"""
        mock_client = MagicMock()
        mock_client.info.return_value = {
            'redis_version': '8.2.1'
        }
        
        with patch.dict(os.environ, {'REDIS_URL': 'rediss://example.com:6380/0'}, clear=True):
            with patch('src.utils.redis_client.get_redis_client', return_value=mock_client):
                result = check_redis_security()
                
                assert result['status'] == 'vulnerable'
                assert result['version'] == '8.2.1'
                assert result['cve_2025_49844_risk'] == 'high'
    
    def test_check_redis_security_version_edge_case_8_2_2(self):
        """Test security check with Redis 8.2.2 (first secure version)"""
        mock_client = MagicMock()
        mock_client.info.return_value = {
            'redis_version': '8.2.2'
        }
        
        with patch.dict(os.environ, {'REDIS_URL': 'rediss://example.com:6380/0'}, clear=True):
            with patch('src.utils.redis_client.get_redis_client', return_value=mock_client):
                result = check_redis_security()
                
                assert result['status'] == 'secure'
                assert result['version'] == '8.2.2'
                assert result['cve_2025_49844_risk'] == 'low'
    
    def test_check_redis_security_version_with_suffix(self):
        """Test security check with version containing suffix (e.g., '8.2.2-alpine')"""
        mock_client = MagicMock()
        mock_client.info.return_value = {
            'redis_version': '8.2.2-alpine'
        }
        
        with patch.dict(os.environ, {'REDIS_URL': 'rediss://example.com:6380/0'}, clear=True):
            with patch('src.utils.redis_client.get_redis_client', return_value=mock_client):
                result = check_redis_security()
                
                assert result['status'] == 'secure'
                assert result['version'] == '8.2.2-alpine'
