#!/usr/bin/env python3
"""
MCP Client for Dev Agent Sandbox
Exposes sandbox capabilities through MCP protocol
"""
import asyncio
import logging
from aiohttp import web
from dev_agent_sandbox import DevAgentSandbox

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sandbox = DevAgentSandbox()

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

async def handle_git_clone(request):
    """Handle git clone requests"""
    try:
        data = await request.json()
        repo_url = data.get('repo_url')
        destination = data.get('destination')
        
        result = await sandbox.git_clone(repo_url, destination)
        return web.json_response(result)
    except Exception as e:
        logger.error(f"Git clone handler error: {e}")
        return web.json_response({'success': False, 'error': str(e)}, status=500)

async def handle_git_commit(request):
    """Handle git commit requests"""
    try:
        data = await request.json()
        message = data.get('message')
        files = data.get('files')
        
        result = await sandbox.git_commit(message, files)
        return web.json_response(result)
    except Exception as e:
        logger.error(f"Git commit handler error: {e}")
        return web.json_response({'success': False, 'error': str(e)}, status=500)

async def handle_read_file(request):
    """Handle file read requests"""
    try:
        data = await request.json()
        file_path = data.get('file_path')
        
        result = await sandbox.read_file(file_path)
        return web.json_response(result)
    except Exception as e:
        logger.error(f"Read file handler error: {e}")
        return web.json_response({'success': False, 'error': str(e)}, status=500)

async def handle_write_file(request):
    """Handle file write requests"""
    try:
        data = await request.json()
        file_path = data.get('file_path')
        content = data.get('content')
        
        result = await sandbox.write_file(file_path, content)
        return web.json_response(result)
    except Exception as e:
        logger.error(f"Write file handler error: {e}")
        return web.json_response({'success': False, 'error': str(e)}, status=500)

async def handle_lsp_start(request):
    """Handle LSP server start requests"""
    try:
        data = await request.json()
        language = data.get('language')
        
        result = await sandbox.start_lsp_server(language)
        return web.json_response(result)
    except Exception as e:
        logger.error(f"LSP start handler error: {e}")
        return web.json_response({'success': False, 'error': str(e)}, status=500)

async def handle_health(request):
    """Health check endpoint"""
    result = await sandbox.health_check()
    return web.json_response(result)

def create_app():
    """Create aiohttp application with routes"""
    app = web.Application()
    
    app.router.add_post('/api/shell', handle_shell)
    app.router.add_post('/api/git/clone', handle_git_clone)
    app.router.add_post('/api/git/commit', handle_git_commit)
    app.router.add_post('/api/file/read', handle_read_file)
    app.router.add_post('/api/file/write', handle_write_file)
    app.router.add_post('/api/lsp/start', handle_lsp_start)
    app.router.add_get('/health', handle_health)
    
    return app

if __name__ == '__main__':
    logger.info("Starting Dev Agent MCP Server on port 8080")
    app = create_app()
    web.run_app(app, host='0.0.0.0', port=8080)
