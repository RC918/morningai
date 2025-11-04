#!/usr/bin/env python3
"""
Sentry monitoring tool for MCP
"""
import aiohttp
import os
from typing import Dict, Any, Optional

class SentryTool:
    """Sentry API integration for error monitoring"""
    
    def __init__(self):
        self.auth_token = os.getenv('SENTRY_AUTH_TOKEN')
        self.organization = os.getenv('SENTRY_ORG', 'morningai')
        self.base_url = 'https://sentry.io/api/0'
        
    async def call_api(self, endpoint: str, method: str = 'GET', data: Optional[Dict] = None) -> Dict[str, Any]:
        """Call Sentry API"""
        if not self.auth_token:
            return {
                'success': False,
                'error': 'SENTRY_AUTH_TOKEN not configured'
            }
            
        headers = {
            'Authorization': f'Bearer {self.auth_token}',
            'Content-Type': 'application/json'
        }
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        async with aiohttp.ClientSession() as session:
            if method == 'GET':
                async with session.get(url, headers=headers) as resp:
                    result = await resp.json()
                    return {
                        'success': resp.status == 200,
                        'status_code': resp.status,
                        'data': result
                    }
            else:
                return {
                    'success': False,
                    'error': f'Unsupported method: {method}'
                }
                
    async def get_issues(self, project: str) -> Dict[str, Any]:
        """Get recent issues"""
        return await self.call_api(f'projects/{self.organization}/{project}/issues/')
