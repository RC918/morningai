import requests
import os
import asyncio
from typing import Dict, List, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class CloudResourceHealthChecker:
    """Cloud resource health checker for user's specific services"""
    
    def __init__(self):
        self.services = {
            'sentry': self._check_sentry,
            'cloudflare': self._check_cloudflare,
            'upstash': self._check_upstash,
            'vercel': self._check_vercel,
            'render': self._check_render,
            'supabase': self._check_supabase
        }
    
    async def check_all_services(self) -> Dict[str, Any]:
        """Check all cloud services health"""
        results = {}
        for service_name, check_func in self.services.items():
            try:
                results[service_name] = await check_func()
            except Exception as e:
                results[service_name] = {
                    'status': 'error',
                    'message': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                }
        return results
    
    async def _check_sentry(self) -> Dict[str, Any]:
        """Check Sentry service health"""
        sentry_dsn = os.getenv('SENTRY_DSN')
        if not sentry_dsn:
            return {'status': 'not_configured', 'message': 'Sentry DSN not configured'}
        
        try:
            import re
            match = re.search(r'https://(.+)@(.+)/(\d+)', sentry_dsn)
            if match:
                auth_token = os.getenv('SENTRY_AUTH_TOKEN')
                if auth_token:
                    headers = {'Authorization': f'Bearer {auth_token}'}
                    response = requests.get(
                        'https://sentry.io/api/0/projects/',
                        headers=headers,
                        timeout=10
                    )
                    if response.status_code == 200:
                        return {
                            'status': 'healthy', 
                            'response_time': response.elapsed.total_seconds(),
                            'timestamp': datetime.utcnow().isoformat()
                        }
            
            return {
                'status': 'healthy', 
                'message': 'DSN configured',
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'status': 'unhealthy', 
                'message': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def _check_cloudflare(self) -> Dict[str, Any]:
        """Check Cloudflare service health"""
        cf_token = os.getenv('CLOUDFLARE_API_TOKEN')
        cf_zone_id = os.getenv('CLOUDFLARE_ZONE_ID')
        
        if not cf_token:
            return {
                'status': 'not_configured', 
                'message': 'Cloudflare API token not configured',
                'timestamp': datetime.utcnow().isoformat()
            }
        
        try:
            headers = {'Authorization': f'Bearer {cf_token}'}
            response = requests.get(
                'https://api.cloudflare.com/client/v4/user/tokens/verify',
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    return {
                        'status': 'healthy', 
                        'response_time': response.elapsed.total_seconds(),
                        'timestamp': datetime.utcnow().isoformat()
                    }
            
            return {
                'status': 'unhealthy', 
                'message': 'Token verification failed',
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'status': 'unhealthy', 
                'message': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def _check_upstash(self) -> Dict[str, Any]:
        """Check Upstash Redis health"""
        redis_url = os.getenv('UPSTASH_REDIS_REST_URL')
        redis_token = os.getenv('UPSTASH_REDIS_REST_TOKEN')
        
        if not redis_url or not redis_token:
            return {
                'status': 'not_configured', 
                'message': 'Upstash Redis credentials not configured',
                'timestamp': datetime.utcnow().isoformat()
            }
        
        try:
            headers = {'Authorization': f'Bearer {redis_token}'}
            response = requests.post(
                f'{redis_url}/ping',
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                return {
                    'status': 'healthy', 
                    'response_time': response.elapsed.total_seconds(),
                    'timestamp': datetime.utcnow().isoformat()
                }
            
            return {
                'status': 'unhealthy', 
                'message': f'HTTP {response.status_code}',
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'status': 'unhealthy', 
                'message': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def _check_vercel(self) -> Dict[str, Any]:
        """Check Vercel service health"""
        vercel_token = os.getenv('VERCEL_TOKEN')
        
        if not vercel_token:
            return {
                'status': 'not_configured', 
                'message': 'Vercel token not configured',
                'timestamp': datetime.utcnow().isoformat()
            }
        
        try:
            headers = {'Authorization': f'Bearer {vercel_token}'}
            response = requests.get(
                'https://api.vercel.com/v2/user',
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                return {
                    'status': 'healthy', 
                    'response_time': response.elapsed.total_seconds(),
                    'timestamp': datetime.utcnow().isoformat()
                }
            
            return {
                'status': 'unhealthy', 
                'message': f'HTTP {response.status_code}',
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'status': 'unhealthy', 
                'message': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def _check_render(self) -> Dict[str, Any]:
        """Check Render service health"""
        render_api_key = os.getenv('RENDER_API_KEY')
        
        if not render_api_key:
            return {
                'status': 'not_configured', 
                'message': 'Render API key not configured',
                'timestamp': datetime.utcnow().isoformat()
            }
        
        try:
            headers = {'Authorization': f'Bearer {render_api_key}'}
            response = requests.get(
                'https://api.render.com/v1/services',
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                return {
                    'status': 'healthy', 
                    'response_time': response.elapsed.total_seconds(),
                    'timestamp': datetime.utcnow().isoformat()
                }
            
            return {
                'status': 'unhealthy', 
                'message': f'HTTP {response.status_code}',
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'status': 'unhealthy', 
                'message': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def _check_supabase(self) -> Dict[str, Any]:
        """Check Supabase service health"""
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        if not supabase_url or not supabase_key:
            return {
                'status': 'not_configured', 
                'message': 'Supabase credentials not configured',
                'timestamp': datetime.utcnow().isoformat()
            }
        
        try:
            headers = {
                'apikey': supabase_key,
                'Authorization': f'Bearer {supabase_key}'
            }
            response = requests.get(
                f'{supabase_url}/rest/v1/',
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                return {
                    'status': 'healthy', 
                    'response_time': response.elapsed.total_seconds(),
                    'timestamp': datetime.utcnow().isoformat()
                }
            
            return {
                'status': 'unhealthy', 
                'message': f'HTTP {response.status_code}',
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'status': 'unhealthy', 
                'message': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
