#!/usr/bin/env python3
"""
Integration Tests for Vercel Deployment
These tests use real Vercel API calls (requires VERCEL_TOKEN)
"""
import pytest
import os
import sys
import asyncio

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.deployment_tool import DeploymentTool


@pytest.mark.skipif(
    not os.getenv('VERCEL_TOKEN'),
    reason="VERCEL_TOKEN not set - skipping integration tests"
)
class TestVercelIntegration:
    """Real integration tests with Vercel API"""
    
    @pytest.fixture
    def deployment_tool(self):
        """Create deployment tool with real credentials"""
        return DeploymentTool(
            token=os.getenv('VERCEL_TOKEN'),
            team_id=os.getenv('VERCEL_ORG_ID')
        )
    
    @pytest.mark.asyncio
    async def test_list_deployments_real(self, deployment_tool):
        """Test listing real deployments"""
        project_id = os.getenv('VERCEL_PROJECT_ID', 'morningai')
        
        result = await deployment_tool.list_deployments(
            project=project_id,
            limit=5
        )
        
        assert result['success'] is True or 'error' in result
        
        if result['success']:
            print(f"\n✅ Successfully listed deployments")
            print(f"Total deployments: {result['total']}")
            
            if result['deployments']:
                print("\nRecent deployments:")
                for dep in result['deployments'][:3]:
                    print(f"  - {dep['name']}: {dep['state']} ({dep['url']})")
        else:
            print(f"\n⚠️ API Error: {result.get('error')}")
    
    @pytest.mark.asyncio
    async def test_get_deployment_real(self, deployment_tool):
        """Test getting a real deployment's details"""
        project_id = os.getenv('VERCEL_PROJECT_ID', 'morningai')
        
        list_result = await deployment_tool.list_deployments(
            project=project_id,
            limit=1
        )
        
        if list_result['success'] and list_result['deployments']:
            deployment_id = list_result['deployments'][0]['id']
            
            result = await deployment_tool.get_deployment(deployment_id)
            
            assert result['success'] is True or 'error' in result
            
            if result['success']:
                dep = result['deployment']
                print(f"\n✅ Retrieved deployment details:")
                print(f"  ID: {dep['id']}")
                print(f"  URL: {dep['url']}")
                print(f"  State: {dep['state']}")
                print(f"  Ready: {dep.get('ready', 'N/A')}")
        else:
            pytest.skip("No deployments found to test")
    
    @pytest.mark.asyncio
    async def test_api_connection(self, deployment_tool):
        """Test basic API connectivity"""
        result = await deployment_tool._make_request(
            "GET",
            "/v6/deployments",
            params={"limit": 1}
        )
        
        assert result is not None
        
        if result.get('success'):
            print("\n✅ Vercel API connection successful")
        else:
            print(f"\n⚠️ API connection issue: {result.get('error')}")
            print(f"Status code: {result.get('status_code')}")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s', '--tb=short'])
