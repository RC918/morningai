#!/usr/bin/env python3
"""
Deployment Tool - Vercel Integration
Manages deployments to Vercel platform
"""
import logging
import asyncio
import aiohttp
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DeploymentState(Enum):
    """Deployment states"""
    BUILDING = "BUILDING"
    ERROR = "ERROR"
    INITIALIZING = "INITIALIZING"
    QUEUED = "QUEUED"
    READY = "READY"
    CANCELED = "CANCELED"


class DeploymentEnvironment(Enum):
    """Deployment environments"""
    PRODUCTION = "production"
    PREVIEW = "preview"
    DEVELOPMENT = "development"


@dataclass
class DeploymentInfo:
    """Deployment information"""
    id: str
    url: str
    state: str
    created_at: datetime
    environment: str
    git_branch: Optional[str] = None
    git_commit: Optional[str] = None
    build_duration: Optional[int] = None
    error_message: Optional[str] = None


class DeploymentTool:
    """Tool for managing Vercel deployments"""
    
    VERCEL_API_BASE = "https://api.vercel.com"
    
    def __init__(self, token: Optional[str] = None, team_id: Optional[str] = None):
        """
        Initialize Deployment Tool
        
        Args:
            token: Vercel API token
            team_id: Vercel team ID (optional)
        """
        self.token = token
        self.team_id = team_id
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to Vercel API"""
        url = f"{self.VERCEL_API_BASE}{endpoint}"
        
        if self.team_id and params:
            params["teamId"] = self.team_id
        elif self.team_id:
            params = {"teamId": self.team_id}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method,
                    url,
                    headers=self.headers,
                    json=data,
                    params=params
                ) as response:
                    response_data = await response.json()
                    
                    if response.status >= 400:
                        logger.error(f"API request failed: {response.status} - {response_data}")
                        return {
                            'success': False,
                            'error': response_data.get('error', {}).get('message', 'Unknown error'),
                            'status_code': response.status
                        }
                    
                    return {
                        'success': True,
                        'data': response_data
                    }
        
        except Exception as e:
            logger.error(f"Request exception: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def deploy(
        self,
        project: str,
        git_source: Optional[Dict[str, str]] = None,
        environment: str = "production",
        target: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Trigger a new deployment
        
        Args:
            project: Project name
            git_source: Git source info (branch, repo)
            environment: production, preview, or development
            target: Target environment (production/staging)
        
        Returns:
            Dict with deployment information
        """
        try:
            payload = {
                "name": project,
                "gitSource": git_source or {},
                "target": target or environment
            }
            
            result = await self._make_request(
                "POST",
                "/v13/deployments",
                data=payload
            )
            
            if not result['success']:
                return result
            
            deployment_data = result['data']
            
            return {
                'success': True,
                'deployment_id': deployment_data.get('id'),
                'url': deployment_data.get('url'),
                'state': deployment_data.get('readyState', 'INITIALIZING'),
                'inspector_url': deployment_data.get('inspectorUrl'),
                'created_at': deployment_data.get('createdAt')
            }
        
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_deployment(self, deployment_id: str) -> Dict[str, Any]:
        """
        Get deployment information
        
        Args:
            deployment_id: Deployment ID
        
        Returns:
            Dict with deployment details
        """
        try:
            result = await self._make_request(
                "GET",
                f"/v13/deployments/{deployment_id}"
            )
            
            if not result['success']:
                return result
            
            deployment = result['data']
            
            return {
                'success': True,
                'deployment': {
                    'id': deployment.get('id'),
                    'url': deployment.get('url'),
                    'state': deployment.get('readyState'),
                    'created_at': deployment.get('createdAt'),
                    'ready': deployment.get('ready'),
                    'git_branch': deployment.get('meta', {}).get('githubCommitRef'),
                    'git_commit': deployment.get('meta', {}).get('githubCommitSha'),
                    'build_duration': deployment.get('buildingAt')
                }
            }
        
        except Exception as e:
            logger.error(f"Failed to get deployment: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def list_deployments(
        self,
        project: Optional[str] = None,
        limit: int = 20,
        state: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List deployments
        
        Args:
            project: Filter by project name
            limit: Maximum number of results
            state: Filter by state (READY, ERROR, etc.)
        
        Returns:
            Dict with list of deployments
        """
        try:
            params = {"limit": limit}
            if project:
                params["app"] = project
            if state:
                params["state"] = state
            
            result = await self._make_request(
                "GET",
                "/v6/deployments",
                params=params
            )
            
            if not result['success']:
                return result
            
            deployments = result['data'].get('deployments', [])
            
            deployment_list = [
                {
                    'id': d.get('uid'),
                    'name': d.get('name'),
                    'url': d.get('url'),
                    'state': d.get('state'),
                    'created_at': d.get('created'),
                    'environment': d.get('target')
                }
                for d in deployments
            ]
            
            return {
                'success': True,
                'deployments': deployment_list,
                'total': len(deployment_list)
            }
        
        except Exception as e:
            logger.error(f"Failed to list deployments: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def cancel_deployment(self, deployment_id: str) -> Dict[str, Any]:
        """
        Cancel a deployment
        
        Args:
            deployment_id: Deployment ID to cancel
        
        Returns:
            Dict with cancellation result
        """
        try:
            result = await self._make_request(
                "PATCH",
                f"/v12/deployments/{deployment_id}/cancel"
            )
            
            if not result['success']:
                return result
            
            return {
                'success': True,
                'deployment_id': deployment_id,
                'state': 'CANCELED'
            }
        
        except Exception as e:
            logger.error(f"Failed to cancel deployment: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_deployment_events(self, deployment_id: str) -> Dict[str, Any]:
        """
        Get deployment build events/logs
        
        Args:
            deployment_id: Deployment ID
        
        Returns:
            Dict with deployment events
        """
        try:
            result = await self._make_request(
                "GET",
                f"/v2/deployments/{deployment_id}/events"
            )
            
            if not result['success']:
                return result
            
            return {
                'success': True,
                'events': result['data']
            }
        
        except Exception as e:
            logger.error(f"Failed to get deployment events: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def wait_for_deployment(
        self,
        deployment_id: str,
        timeout: int = 600,
        poll_interval: int = 5
    ) -> Dict[str, Any]:
        """
        Wait for deployment to complete
        
        Args:
            deployment_id: Deployment ID
            timeout: Maximum wait time in seconds
            poll_interval: Polling interval in seconds
        
        Returns:
            Dict with final deployment status
        """
        try:
            start_time = asyncio.get_event_loop().time()
            
            while True:
                result = await self.get_deployment(deployment_id)
                
                if not result['success']:
                    return result
                
                deployment = result['deployment']
                state = deployment['state']
                
                if state in [DeploymentState.READY.value, DeploymentState.ERROR.value, DeploymentState.CANCELED.value]:
                    return {
                        'success': state == DeploymentState.READY.value,
                        'deployment': deployment,
                        'state': state
                    }
                
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed > timeout:
                    return {
                        'success': False,
                        'error': 'Deployment timeout',
                        'deployment': deployment
                    }
                
                await asyncio.sleep(poll_interval)
        
        except Exception as e:
            logger.error(f"Failed to wait for deployment: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def redeploy(
        self,
        deployment_id: str,
        target: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Redeploy an existing deployment
        
        Args:
            deployment_id: Original deployment ID
            target: Target environment
        
        Returns:
            Dict with new deployment information
        """
        try:
            get_result = await self.get_deployment(deployment_id)
            
            if not get_result['success']:
                return get_result
            
            original = get_result['deployment']
            
            payload = {
                "deploymentId": deployment_id,
                "meta": {
                    "action": "redeploy"
                }
            }
            
            if target:
                payload["target"] = target
            
            result = await self._make_request(
                "POST",
                "/v13/deployments",
                data=payload
            )
            
            if not result['success']:
                return result
            
            deployment_data = result['data']
            
            return {
                'success': True,
                'original_deployment_id': deployment_id,
                'new_deployment_id': deployment_data.get('id'),
                'url': deployment_data.get('url'),
                'state': deployment_data.get('readyState')
            }
        
        except Exception as e:
            logger.error(f"Redeployment failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_project_deployments(
        self,
        project_id: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get deployments for a specific project
        
        Args:
            project_id: Project ID or name
            limit: Maximum number of deployments
        
        Returns:
            Dict with project deployments
        """
        return await self.list_deployments(
            project=project_id,
            limit=limit
        )
    
    async def promote_to_production(self, deployment_id: str) -> Dict[str, Any]:
        """
        Promote a preview deployment to production
        
        Args:
            deployment_id: Preview deployment ID
        
        Returns:
            Dict with promotion result
        """
        try:
            payload = {
                "target": "production"
            }
            
            result = await self._make_request(
                "PATCH",
                f"/v9/projects/deployments/{deployment_id}/promote",
                data=payload
            )
            
            return result
        
        except Exception as e:
            logger.error(f"Promotion failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }


def create_deployment_tool(
    token: Optional[str] = None,
    team_id: Optional[str] = None
) -> DeploymentTool:
    """Factory function to create DeploymentTool instance"""
    return DeploymentTool(token=token, team_id=team_id)
