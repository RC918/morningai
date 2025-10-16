#!/usr/bin/env python3
"""
Dev Agent Sandbox - Provides development tools and environment
"""
import asyncio
import logging
import os
import subprocess
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DevAgentSandbox:
    """Development Agent Sandbox with IDE and LSP capabilities"""
    
    def __init__(self):
        self.workspace = os.getenv('WORKSPACE_PATH', '/workspace')
        self.agent_id = os.getenv('AGENT_ID', 'dev-agent')
        
    async def execute_shell(self, command: str, cwd: Optional[str] = None) -> Dict[str, Any]:
        """Execute shell command in sandbox"""
        try:
            working_dir = cwd or self.workspace
            logger.info(f"Executing: {command} in {working_dir}")
            
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir
            )
            
            stdout, stderr = await process.communicate()
            
            return {
                'success': process.returncode == 0,
                'return_code': process.returncode,
                'stdout': stdout.decode('utf-8'),
                'stderr': stderr.decode('utf-8')
            }
            
        except Exception as e:
            logger.error(f"Shell execution failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def git_clone(self, repo_url: str, destination: Optional[str] = None) -> Dict[str, Any]:
        """Clone a git repository"""
        try:
            dest = destination or os.path.join(self.workspace, 'repo')
            command = f"git clone {repo_url} {dest}"
            return await self.execute_shell(command)
        except Exception as e:
            logger.error(f"Git clone failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def git_commit(self, message: str, files: list = None) -> Dict[str, Any]:
        """Commit changes to git"""
        try:
            if files:
                add_cmd = f"git add {' '.join(files)}"
                await self.execute_shell(add_cmd)
            else:
                await self.execute_shell("git add .")
            
            commit_cmd = f"git commit -m '{message}'"
            return await self.execute_shell(commit_cmd)
        except Exception as e:
            logger.error(f"Git commit failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def read_file(self, file_path: str) -> Dict[str, Any]:
        """Read file contents"""
        try:
            full_path = os.path.join(self.workspace, file_path)
            with open(full_path, 'r') as f:
                content = f.read()
            return {'success': True, 'content': content}
        except Exception as e:
            logger.error(f"Read file failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def write_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """Write content to file"""
        try:
            full_path = os.path.join(self.workspace, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w') as f:
                f.write(content)
            return {'success': True}
        except Exception as e:
            logger.error(f"Write file failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def start_lsp_server(self, language: str) -> Dict[str, Any]:
        """Start Language Server Protocol server for given language"""
        try:
            if language == 'python':
                command = "pylsp"
            elif language in ['typescript', 'javascript']:
                command = "typescript-language-server --stdio"
            else:
                return {'success': False, 'error': f'Unsupported language: {language}'}
            
            logger.info(f"Starting LSP server for {language}")
            return {'success': True, 'command': command}
            
        except Exception as e:
            logger.error(f"LSP server start failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check endpoint"""
        return {
            'status': 'healthy',
            'agent_id': self.agent_id,
            'workspace': self.workspace
        }

if __name__ == '__main__':
    sandbox = DevAgentSandbox()
    logger.info(f"Dev Agent Sandbox initialized for {sandbox.agent_id}")
    logger.info(f"Workspace: {sandbox.workspace}")
