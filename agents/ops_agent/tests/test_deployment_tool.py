#!/usr/bin/env python3
"""
Tests for Deployment Tool
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.deployment_tool import DeploymentTool, DeploymentState, create_deployment_tool


class TestDeploymentTool:
    """Tests for DeploymentTool"""
    
    @pytest.fixture
    def deployment_tool(self):
        """Create deployment tool for testing"""
        return DeploymentTool(token="test_token", team_id="test_team")
    
    def test_initialization(self, deployment_tool):
        """Test DeploymentTool initialization"""
        assert deployment_tool.token == "test_token"
        assert deployment_tool.team_id == "test_team"
        assert "Authorization" in deployment_tool.headers
        assert deployment_tool.headers["Authorization"] == "Bearer test_token"
    
    @pytest.mark.asyncio
    async def test_deploy_success(self, deployment_tool):
        """Test successful deployment"""
        mock_response = {
            'id': 'dep_123',
            'url': 'morningai-xyz.vercel.app',
            'readyState': 'BUILDING',
            'inspectorUrl': 'https://vercel.com/inspect/dep_123',
            'createdAt': 1234567890
        }
        
        with patch.object(deployment_tool, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {'success': True, 'data': mock_response}
            
            result = await deployment_tool.deploy(
                project="morningai",
                environment="production"
            )
            
            assert result['success'] is True
            assert result['deployment_id'] == 'dep_123'
            assert result['url'] == 'morningai-xyz.vercel.app'
            assert result['state'] == 'BUILDING'
    
    @pytest.mark.asyncio
    async def test_deploy_with_git_source(self, deployment_tool):
        """Test deployment with git source"""
        git_source = {
            'type': 'github',
            'repo': 'RC918/morningai',
            'ref': 'main'
        }
        
        with patch.object(deployment_tool, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                'success': True,
                'data': {
                    'id': 'dep_456',
                    'url': 'test.vercel.app',
                    'readyState': 'INITIALIZING'
                }
            }
            
            result = await deployment_tool.deploy(
                project="morningai",
                git_source=git_source,
                environment="preview"
            )
            
            assert result['success'] is True
            assert result['deployment_id'] == 'dep_456'
    
    @pytest.mark.asyncio
    async def test_get_deployment(self, deployment_tool):
        """Test getting deployment information"""
        mock_response = {
            'id': 'dep_123',
            'url': 'test.vercel.app',
            'readyState': 'READY',
            'createdAt': 1234567890,
            'ready': True,
            'meta': {
                'githubCommitRef': 'main',
                'githubCommitSha': 'abc123'
            }
        }
        
        with patch.object(deployment_tool, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {'success': True, 'data': mock_response}
            
            result = await deployment_tool.get_deployment('dep_123')
            
            assert result['success'] is True
            assert result['deployment']['id'] == 'dep_123'
            assert result['deployment']['state'] == 'READY'
            assert result['deployment']['git_branch'] == 'main'
    
    @pytest.mark.asyncio
    async def test_list_deployments(self, deployment_tool):
        """Test listing deployments"""
        mock_response = {
            'deployments': [
                {
                    'uid': 'dep_1',
                    'name': 'morningai',
                    'url': 'test1.vercel.app',
                    'state': 'READY',
                    'created': 1234567890,
                    'target': 'production'
                },
                {
                    'uid': 'dep_2',
                    'name': 'morningai',
                    'url': 'test2.vercel.app',
                    'state': 'BUILDING',
                    'created': 1234567800,
                    'target': 'preview'
                }
            ]
        }
        
        with patch.object(deployment_tool, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {'success': True, 'data': mock_response}
            
            result = await deployment_tool.list_deployments(project="morningai", limit=10)
            
            assert result['success'] is True
            assert result['total'] == 2
            assert len(result['deployments']) == 2
            assert result['deployments'][0]['id'] == 'dep_1'
            assert result['deployments'][0]['state'] == 'READY'
    
    @pytest.mark.asyncio
    async def test_cancel_deployment(self, deployment_tool):
        """Test canceling a deployment"""
        with patch.object(deployment_tool, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {'success': True, 'data': {}}
            
            result = await deployment_tool.cancel_deployment('dep_123')
            
            assert result['success'] is True
            assert result['deployment_id'] == 'dep_123'
            assert result['state'] == 'CANCELED'
    
    @pytest.mark.asyncio
    async def test_get_deployment_events(self, deployment_tool):
        """Test getting deployment events"""
        mock_events = [
            {'type': 'stdout', 'payload': 'Building...'},
            {'type': 'stdout', 'payload': 'Build completed'}
        ]
        
        with patch.object(deployment_tool, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {'success': True, 'data': mock_events}
            
            result = await deployment_tool.get_deployment_events('dep_123')
            
            assert result['success'] is True
            assert len(result['events']) == 2
    
    @pytest.mark.asyncio
    async def test_wait_for_deployment_ready(self, deployment_tool):
        """Test waiting for deployment to be ready"""
        mock_deployment = {
            'id': 'dep_123',
            'state': 'READY',
            'url': 'test.vercel.app'
        }
        
        with patch.object(deployment_tool, 'get_deployment', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {
                'success': True,
                'deployment': mock_deployment
            }
            
            result = await deployment_tool.wait_for_deployment('dep_123', timeout=10)
            
            assert result['success'] is True
            assert result['state'] == 'READY'
            assert result['deployment']['id'] == 'dep_123'
    
    @pytest.mark.asyncio
    async def test_wait_for_deployment_error(self, deployment_tool):
        """Test waiting for deployment that fails"""
        mock_deployment = {
            'id': 'dep_123',
            'state': 'ERROR',
            'url': 'test.vercel.app'
        }
        
        with patch.object(deployment_tool, 'get_deployment', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {
                'success': True,
                'deployment': mock_deployment
            }
            
            result = await deployment_tool.wait_for_deployment('dep_123', timeout=10)
            
            assert result['success'] is False
            assert result['state'] == 'ERROR'
    
    @pytest.mark.asyncio
    async def test_wait_for_deployment_timeout(self, deployment_tool):
        """Test deployment timeout"""
        mock_deployment = {
            'id': 'dep_123',
            'state': 'BUILDING',
            'url': 'test.vercel.app'
        }
        
        with patch.object(deployment_tool, 'get_deployment', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {
                'success': True,
                'deployment': mock_deployment
            }
            
            result = await deployment_tool.wait_for_deployment('dep_123', timeout=1, poll_interval=0.5)
            
            assert result['success'] is False
            assert 'timeout' in result['error'].lower()
    
    @pytest.mark.asyncio
    async def test_redeploy(self, deployment_tool):
        """Test redeploying an existing deployment"""
        original_deployment = {
            'id': 'dep_123',
            'url': 'test.vercel.app',
            'state': 'READY'
        }
        
        new_deployment = {
            'id': 'dep_456',
            'url': 'test-new.vercel.app',
            'readyState': 'BUILDING'
        }
        
        with patch.object(deployment_tool, 'get_deployment', new_callable=AsyncMock) as mock_get, \
             patch.object(deployment_tool, '_make_request', new_callable=AsyncMock) as mock_request:
            
            mock_get.return_value = {'success': True, 'deployment': original_deployment}
            mock_request.return_value = {'success': True, 'data': new_deployment}
            
            result = await deployment_tool.redeploy('dep_123')
            
            assert result['success'] is True
            assert result['original_deployment_id'] == 'dep_123'
            assert result['new_deployment_id'] == 'dep_456'
    
    @pytest.mark.asyncio
    async def test_promote_to_production(self, deployment_tool):
        """Test promoting preview to production"""
        with patch.object(deployment_tool, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {'success': True, 'data': {}}
            
            result = await deployment_tool.promote_to_production('dep_123')
            
            assert result['success'] is True
    
    @pytest.mark.asyncio
    async def test_api_error_handling(self, deployment_tool):
        """Test API error handling"""
        with patch.object(deployment_tool, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                'success': False,
                'error': 'API rate limit exceeded',
                'status_code': 429
            }
            
            result = await deployment_tool.deploy(project="test")
            
            assert result['success'] is False
            assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_network_error_handling(self, deployment_tool):
        """Test network error handling"""
        with patch.object(deployment_tool, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = Exception("Network error")
            
            result = await deployment_tool.deploy(project="test")
            
            assert result['success'] is False
            assert 'error' in result


class TestDeploymentToolFactory:
    """Tests for deployment tool factory function"""
    
    def test_create_deployment_tool(self):
        """Test factory function"""
        tool = create_deployment_tool(token="test_token", team_id="test_team")
        
        assert isinstance(tool, DeploymentTool)
        assert tool.token == "test_token"
        assert tool.team_id == "test_team"
    
    def test_create_deployment_tool_no_params(self):
        """Test factory function without parameters"""
        tool = create_deployment_tool()
        
        assert isinstance(tool, DeploymentTool)
        assert tool.token is None


class TestDeploymentToolEdgeCases:
    """Edge case tests for DeploymentTool"""
    
    @pytest.fixture
    def deployment_tool(self):
        return DeploymentTool(token="test_token")
    
    @pytest.mark.asyncio
    async def test_empty_project_name(self, deployment_tool):
        """Test deployment with empty project name"""
        with patch.object(deployment_tool, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {'success': True, 'data': {'id': 'dep_123', 'url': 'test.vercel.app'}}
            
            result = await deployment_tool.deploy(project="")
            
            assert result['success'] is True
    
    @pytest.mark.asyncio
    async def test_list_deployments_empty(self, deployment_tool):
        """Test listing deployments when none exist"""
        with patch.object(deployment_tool, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {'success': True, 'data': {'deployments': []}}
            
            result = await deployment_tool.list_deployments()
            
            assert result['success'] is True
            assert result['total'] == 0
            assert len(result['deployments']) == 0
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_deployment(self, deployment_tool):
        """Test getting a deployment that doesn't exist"""
        with patch.object(deployment_tool, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                'success': False,
                'error': 'Deployment not found',
                'status_code': 404
            }
            
            result = await deployment_tool.get_deployment('nonexistent')
            
            assert result['success'] is False
            assert 'error' in result


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
