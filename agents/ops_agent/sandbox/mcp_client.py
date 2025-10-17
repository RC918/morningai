#!/usr/bin/env python3
"""
MCP Client for Ops Agent Sandbox
Exposes sandbox capabilities through MCP protocol
"""
import asyncio
import logging
from aiohttp import web
from ops_agent_sandbox import OpsAgentSandbox

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sandbox = OpsAgentSandbox()

async def handle_shell(request):
    """Handle shell execution requests"""
    try:
        data = await request.json()
        command = data.get('command')
        cwd = data.get('cwd')
        
        result = await sandbox.execute_shell(command, cwd)
        return web.json_response(result)
    except Exception as e:
        logger.error(f"Shell handler error: {e}")
        return web.json_response({'success': False, 'error': str(e)}, status=500)

async def handle_performance(request):
    """Handle performance monitoring requests"""
    try:
        result = await sandbox.monitor_performance()
        return web.json_response(result)
    except Exception as e:
        logger.error(f"Performance handler error: {e}")
        return web.json_response({'success': False, 'error': str(e)}, status=500)

async def handle_capacity(request):
    """Handle capacity check requests"""
    try:
        result = await sandbox.check_capacity()
        return web.json_response(result)
    except Exception as e:
        logger.error(f"Capacity handler error: {e}")
        return web.json_response({'success': False, 'error': str(e)}, status=500)

async def handle_health(request):
    """Handle health check requests"""
    try:
        result = await sandbox.health_check()
        return web.json_response(result)
    except Exception as e:
        logger.error(f"Health handler error: {e}")
        return web.json_response({'success': False, 'error': str(e)}, status=500)

app = web.Application()
app.router.add_post('/api/shell', handle_shell)
app.router.add_get('/api/performance', handle_performance)
app.router.add_get('/api/capacity', handle_capacity)
app.router.add_get('/health', handle_health)

if __name__ == '__main__':
    logger.info("Starting Ops Agent MCP Server on port 8000")
    web.run_app(app, host='0.0.0.0', port=8000)
