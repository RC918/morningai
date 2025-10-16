#!/usr/bin/env python3
"""
Shell execution tool for MCP
"""
import asyncio
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ShellTool:
    """Execute shell commands in sandbox"""
    
    def __init__(self, workspace: str = '/workspace'):
        self.workspace = workspace
        
    async def execute(self, command: str, cwd: Optional[str] = None) -> Dict[str, Any]:
        """Execute shell command"""
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
        """Clone git repository"""
        dest = destination or 'repo'
        command = f"git clone {repo_url} {dest}"
        return await self.execute(command)
        
    async def git_commit(self, message: str, files: Optional[list] = None) -> Dict[str, Any]:
        """Commit changes"""
        if files:
            add_cmd = f"git add {' '.join(files)}"
            await self.execute(add_cmd)
        else:
            await self.execute("git add .")
            
        commit_cmd = f"git commit -m '{message}'"
        return await self.execute(commit_cmd)
