#!/usr/bin/env python3
"""
Render.com API tool for MCP
"""
import aiohttp
import os
from typing import Dict, Any, Optional

class RenderTool:
    """Render.com API integration"""
    
    def __init__(self):
        self.api_key = os.getenv('RENDER_API_KEY')
        self.base_url = 'https://api.render.com/v1'
        
    async def call_api(self, endpoint: str, method: str = 'GET', data: Optional[Dict] = None) -> Dict[str, Any]:
        """Call Render API"""
        if not self.api_key:
            return {
                'success': False,
                'error': 'RENDER_API_KEY not configured'
            }
            
        headers = {
            'Authorization': f'Bearer {self.api_key}',
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
            elif method == 'POST':
                async with session.post(url, headers=headers, json=data) as resp:
                    result = await resp.json()
                    return {
                        'success': resp.status in [200, 201],
                        'status_code': resp.status,
                        'data': result
                    }
            else:
                return {
                    'success': False,
                    'error': f'Unsupported method: {method}'
                }
                
    async def list_services(self) -> Dict[str, Any]:
        """List all services"""
        return await self.call_api('services')
        
    async def get_service(self, service_id: str) -> Dict[str, Any]:
        """Get service details"""
        return await self.call_api(f'services/{service_id}')
