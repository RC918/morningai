#!/usr/bin/env python3
"""
Render Tool - Interact with Render API
"""
import logging
import os
from typing import Dict, Any
import aiohttp

class RenderTool:
    """Render API interaction tool"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.api_key = os.getenv('RENDER_API_KEY')
        self.base_url = 'https://api.render.com/v1'
        
        self.approval_required_ops = [
            'delete_service',
            'suspend_service',
            'scale_to_zero'
        ]
    
    def requires_approval(self, arguments: Dict[str, Any]) -> bool:
        """Check if operation requires approval"""
        operation = arguments.get('operation', '')
        return operation in self.approval_required_ops
    
    def get_approval_description(self, arguments: Dict[str, Any]) -> str:
        """Get human-readable description for approval"""
        operation = arguments.get('operation', '')
        return f"Render API operation: {operation} with params {arguments}"
    
    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Render API call"""
        endpoint = arguments.get('endpoint', '')
        method = arguments.get('method', 'GET')
        data = arguments.get('data')
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    'Authorization': f'Bearer {self.api_key}',
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
            self.logger.error(f"Render API call failed: {e}")
            return {'error': str(e)}
