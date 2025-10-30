#!/usr/bin/env python3
"""
Comprehensive tests for fix_cloud_auth.py module
Tests cloud service authentication validation and repair guidance
"""
import pytest
import os
from unittest.mock import patch, Mock
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import fix_cloud_auth


class TestSupabaseAuth:
    """Test Supabase authentication validation"""
    
    def test_validate_supabase_auth_missing_env_vars(self, capsys):
        """Test Supabase validation with missing environment variables"""
        with patch.dict(os.environ, {}, clear=True):
            result = fix_cloud_auth.validate_supabase_auth()
            assert result is False
            
            captured = capsys.readouterr()
            assert "Missing environment variables" in captured.out
            assert "REPAIR STEPS" in captured.out
    
    def test_validate_supabase_auth_invalid_key(self, capsys):
        """Test Supabase validation with invalid API key"""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_SERVICE_ROLE_KEY': 'invalid_key'
        }):
            mock_response = Mock()
            mock_response.status_code = 401
            
            with patch('requests.get', return_value=mock_response):
                result = fix_cloud_auth.validate_supabase_auth()
                assert result is False
                
                captured = capsys.readouterr()
                assert "Invalid API key detected" in captured.out
                assert "Regenerate service_role key" in captured.out
    
    def test_validate_supabase_auth_success(self, capsys):
        """Test successful Supabase authentication"""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_SERVICE_ROLE_KEY': 'valid_key'
        }):
            mock_response = Mock()
            mock_response.status_code = 200
            
            with patch('requests.get', return_value=mock_response):
                result = fix_cloud_auth.validate_supabase_auth()
                assert result is True
                
                captured = capsys.readouterr()
                assert "Supabase authentication successful" in captured.out
    
    def test_validate_supabase_auth_unexpected_response(self, capsys):
        """Test Supabase validation with unexpected response"""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_SERVICE_ROLE_KEY': 'valid_key'
        }):
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.text = 'Internal Server Error'
            
            with patch('requests.get', return_value=mock_response):
                result = fix_cloud_auth.validate_supabase_auth()
                assert result is False
                
                captured = capsys.readouterr()
                assert "Unexpected response: HTTP 500" in captured.out
    
    def test_validate_supabase_auth_connection_error(self, capsys):
        """Test Supabase validation with connection error"""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_SERVICE_ROLE_KEY': 'valid_key'
        }):
            with patch('requests.get', side_effect=Exception('Connection timeout')):
                result = fix_cloud_auth.validate_supabase_auth()
                assert result is False
                
                captured = capsys.readouterr()
                assert "Connection error" in captured.out


class TestCloudflareAuth:
    """Test Cloudflare authentication validation"""
    
    def test_validate_cloudflare_auth_missing_env_vars(self, capsys):
        """Test Cloudflare validation with missing environment variables"""
        with patch.dict(os.environ, {}, clear=True):
            result = fix_cloud_auth.validate_cloudflare_auth()
            assert result is False
            
            captured = capsys.readouterr()
            assert "Missing environment variables" in captured.out
            assert "REPAIR STEPS" in captured.out
    
    def test_validate_cloudflare_auth_invalid_token(self, capsys):
        """Test Cloudflare validation with invalid token"""
        with patch.dict(os.environ, {
            'CLOUDFLARE_API_TOKEN': 'invalid_token',
            'CLOUDFLARE_ZONE_ID': 'test_zone_id'
        }):
            mock_response = Mock()
            mock_response.status_code = 401
            
            with patch('requests.get', return_value=mock_response):
                result = fix_cloud_auth.validate_cloudflare_auth()
                assert result is False
                
                captured = capsys.readouterr()
                assert "Invalid API token" in captured.out
    
    def test_validate_cloudflare_auth_no_zone_access(self, capsys):
        """Test Cloudflare validation with no zone access"""
        with patch.dict(os.environ, {
            'CLOUDFLARE_API_TOKEN': 'valid_token',
            'CLOUDFLARE_ZONE_ID': 'test_zone_id'
        }):
            mock_verify_response = Mock()
            mock_verify_response.status_code = 200
            
            mock_zone_response = Mock()
            mock_zone_response.status_code = 403
            
            with patch('requests.get', side_effect=[mock_verify_response, mock_zone_response]):
                result = fix_cloud_auth.validate_cloudflare_auth()
                assert result is False
                
                captured = capsys.readouterr()
                assert "Token lacks zone access permissions" in captured.out
    
    def test_validate_cloudflare_auth_invalid_zone_id(self, capsys):
        """Test Cloudflare validation with invalid zone ID"""
        with patch.dict(os.environ, {
            'CLOUDFLARE_API_TOKEN': 'valid_token',
            'CLOUDFLARE_ZONE_ID': 'invalid_zone_id'
        }):
            mock_verify_response = Mock()
            mock_verify_response.status_code = 200
            
            mock_zone_response = Mock()
            mock_zone_response.status_code = 404
            
            with patch('requests.get', side_effect=[mock_verify_response, mock_zone_response]):
                result = fix_cloud_auth.validate_cloudflare_auth()
                assert result is False
                
                captured = capsys.readouterr()
                assert "Invalid Zone ID" in captured.out
    
    def test_validate_cloudflare_auth_success(self, capsys):
        """Test successful Cloudflare authentication"""
        with patch.dict(os.environ, {
            'CLOUDFLARE_API_TOKEN': 'valid_token',
            'CLOUDFLARE_ZONE_ID': 'valid_zone_id'
        }):
            mock_verify_response = Mock()
            mock_verify_response.status_code = 200
            
            mock_zone_response = Mock()
            mock_zone_response.status_code = 200
            
            with patch('requests.get', side_effect=[mock_verify_response, mock_zone_response]):
                result = fix_cloud_auth.validate_cloudflare_auth()
                assert result is True
                
                captured = capsys.readouterr()
                assert "Cloudflare authentication successful" in captured.out
    
    def test_validate_cloudflare_auth_connection_error(self, capsys):
        """Test Cloudflare validation with connection error"""
        with patch.dict(os.environ, {
            'CLOUDFLARE_API_TOKEN': 'valid_token',
            'CLOUDFLARE_ZONE_ID': 'valid_zone_id'
        }):
            with patch('requests.get', side_effect=Exception('Network error')):
                result = fix_cloud_auth.validate_cloudflare_auth()
                assert result is False
                
                captured = capsys.readouterr()
                assert "Connection error" in captured.out


class TestVercelAuth:
    """Test Vercel authentication validation"""
    
    def test_validate_vercel_auth_missing_token(self, capsys):
        """Test Vercel validation with missing token"""
        with patch.dict(os.environ, {}, clear=True):
            result = fix_cloud_auth.validate_vercel_auth()
            assert result is False
            
            captured = capsys.readouterr()
            assert "Missing VERCEL_TOKEN" in captured.out
            assert "REPAIR STEPS" in captured.out
    
    def test_validate_vercel_auth_invalid_token(self, capsys):
        """Test Vercel validation with invalid token"""
        with patch.dict(os.environ, {'VERCEL_TOKEN': 'invalid_token'}):
            mock_response = Mock()
            mock_response.status_code = 403
            mock_response.json.return_value = {
                'error': {'invalidToken': True}
            }
            
            with patch('requests.get', return_value=mock_response):
                result = fix_cloud_auth.validate_vercel_auth()
                assert result is False
                
                captured = capsys.readouterr()
                assert "Invalid or expired token" in captured.out
    
    def test_validate_vercel_auth_insufficient_permissions(self, capsys):
        """Test Vercel validation with insufficient permissions"""
        with patch.dict(os.environ, {'VERCEL_TOKEN': 'valid_token'}):
            mock_response = Mock()
            mock_response.status_code = 403
            mock_response.json.return_value = {
                'error': {'code': 'insufficient_permissions'}
            }
            
            with patch('requests.get', return_value=mock_response):
                result = fix_cloud_auth.validate_vercel_auth()
                assert result is False
                
                captured = capsys.readouterr()
                assert "Token lacks required permissions" in captured.out
    
    def test_validate_vercel_auth_success(self, capsys):
        """Test successful Vercel authentication"""
        with patch.dict(os.environ, {'VERCEL_TOKEN': 'valid_token'}):
            mock_response = Mock()
            mock_response.status_code = 200
            
            with patch('requests.get', return_value=mock_response):
                result = fix_cloud_auth.validate_vercel_auth()
                assert result is True
                
                captured = capsys.readouterr()
                assert "Vercel authentication successful" in captured.out
    
    def test_validate_vercel_auth_connection_error(self, capsys):
        """Test Vercel validation with connection error"""
        with patch.dict(os.environ, {'VERCEL_TOKEN': 'valid_token'}):
            with patch('requests.get', side_effect=Exception('Timeout')):
                result = fix_cloud_auth.validate_vercel_auth()
                assert result is False
                
                captured = capsys.readouterr()
                assert "Connection error" in captured.out


class TestMain:
    """Test main function"""
    
    def test_main_all_services_working(self, capsys):
        """Test main function with all services working"""
        with patch('fix_cloud_auth.validate_supabase_auth', return_value=True), \
             patch('fix_cloud_auth.validate_cloudflare_auth', return_value=True), \
             patch('fix_cloud_auth.validate_vercel_auth', return_value=True):
            
            fix_cloud_auth.main()
            
            captured = capsys.readouterr()
            assert "Authentication Status: 3/3 services working" in captured.out
            assert "All authentication issues resolved!" in captured.out
    
    def test_main_some_services_failing(self, capsys):
        """Test main function with some services failing"""
        with patch('fix_cloud_auth.validate_supabase_auth', return_value=True), \
             patch('fix_cloud_auth.validate_cloudflare_auth', return_value=False), \
             patch('fix_cloud_auth.validate_vercel_auth', return_value=True):
            
            fix_cloud_auth.main()
            
            captured = capsys.readouterr()
            assert "Authentication Status: 2/3 services working" in captured.out
            assert "Follow the repair steps above" in captured.out
    
    def test_main_all_services_failing(self, capsys):
        """Test main function with all services failing"""
        with patch('fix_cloud_auth.validate_supabase_auth', return_value=False), \
             patch('fix_cloud_auth.validate_cloudflare_auth', return_value=False), \
             patch('fix_cloud_auth.validate_vercel_auth', return_value=False):
            
            fix_cloud_auth.main()
            
            captured = capsys.readouterr()
            assert "Authentication Status: 0/3 services working" in captured.out
            assert "Follow the repair steps above" in captured.out
