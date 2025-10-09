#!/usr/bin/env python3
"""
Sentry Tool - Interact with Sentry API
"""
import logging
import os
from typing import Dict, Any
import aiohttp

class SentryTool:
    """Sentry API interaction tool"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.auth_token = os.getenv('SENTRY_AUTH_TOKEN')
        self.base_url = 'https://sentry.io/api/0'
    
    def requires_approval(self, arguments: Dict[str, Any]) -> bool:
        """Sentry read operations don't require approval"""
        method = arguments.get('method', 'GET')
        return method in ['DELETE', 'PUT', 'PATCH']
    
    def get_approval_description(self, arguments: Dict[str, Any]) -> str:
        """Get human-readable description for approval"""
        return f"Sentry API operation: {arguments}"
    
    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Sentry API call"""
        endpoint = arguments.get('endpoint', '')
        method = arguments.get('method', 'GET')
        data = arguments.get('data')
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    'Authorization': f'Bearer {self.auth_token}',
                    'Content-Type': 'application/json'
                }
                
                url = f"{self.base_url}{endpoint}"
                
                async with session.request(
                    method,
                    url,
                    json=data,
                    headers=headers
                ) as response:
                    result = await response.json()
                    return {
                        'status_code': response.status,
                        'result': result
                    }
                    
        except Exception as e:
            self.logger.error(f"Sentry API call failed: {e}")
            return {'error': str(e)}
