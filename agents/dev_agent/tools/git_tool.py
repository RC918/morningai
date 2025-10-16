#!/usr/bin/env python3
"""
Git Tool - Enhanced Git operations for Dev Agent
Provides comprehensive Git functionality including clone, commit, push, PR creation
"""
import os
import logging
from typing import Dict, Any, Optional, List
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GitTool:
    """Enhanced Git tool for development operations"""
    
    def __init__(self, sandbox_endpoint: str, github_token: Optional[str] = None):
        self.sandbox_endpoint = sandbox_endpoint
        self.github_token = github_token or os.getenv('GITHUB_TOKEN')
        
    async def clone(self, repo_url: str, destination: Optional[str] = None) -> Dict[str, Any]:
        """
        Clone a git repository
        
        Args:
            repo_url: Repository URL (https or git)
            destination: Optional destination path in workspace
            
        Returns:
            Dict with success status and result
        """
        try:
            response = requests.post(
                f"{self.sandbox_endpoint}/api/git/clone",
                json={
                    'repo_url': repo_url,
                    'destination': destination
                }
            )
            return response.json()
        except Exception as e:
            logger.error(f"Git clone failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def commit(self, message: str, files: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Commit changes to repository
        
        Args:
            message: Commit message
            files: Optional list of specific files to commit
            
        Returns:
            Dict with success status and result
        """
        try:
            response = requests.post(
                f"{self.sandbox_endpoint}/api/git/commit",
                json={
                    'message': message,
                    'files': files
                }
            )
            return response.json()
        except Exception as e:
            logger.error(f"Git commit failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def push(self, remote: str = 'origin', branch: Optional[str] = None) -> Dict[str, Any]:
        """
        Push commits to remote repository
        
        Args:
            remote: Remote name (default: origin)
            branch: Branch name (default: current branch)
            
        Returns:
            Dict with success status and result
        """
        try:
            branch_flag = f" {branch}" if branch else ""
            command = f"git push {remote}{branch_flag}"
            
            response = requests.post(
                f"{self.sandbox_endpoint}/api/shell",
                json={'command': command}
            )
            return response.json()
        except Exception as e:
            logger.error(f"Git push failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def create_branch(self, branch_name: str, base: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new branch
        
        Args:
            branch_name: Name of the new branch
            base: Optional base branch (default: current branch)
            
        Returns:
            Dict with success status and result
        """
        try:
            base_flag = f" {base}" if base else ""
            command = f"git checkout -b {branch_name}{base_flag}"
            
            response = requests.post(
                f"{self.sandbox_endpoint}/api/shell",
                json={'command': command}
            )
            return response.json()
        except Exception as e:
            logger.error(f"Git create branch failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def status(self) -> Dict[str, Any]:
        """
        Get repository status
        
        Returns:
            Dict with success status and git status output
        """
        try:
            response = requests.post(
                f"{self.sandbox_endpoint}/api/shell",
                json={'command': 'git status'}
            )
            return response.json()
        except Exception as e:
            logger.error(f"Git status failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def diff(self, file_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Get diff of changes
        
        Args:
            file_path: Optional specific file to diff
            
        Returns:
            Dict with success status and diff output
        """
        try:
            file_flag = f" {file_path}" if file_path else ""
            command = f"git diff{file_flag}"
            
            response = requests.post(
                f"{self.sandbox_endpoint}/api/shell",
                json={'command': command}
            )
            return response.json()
        except Exception as e:
            logger.error(f"Git diff failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def create_pr(
        self, 
        repo: str, 
        title: str, 
        body: str, 
        head: str, 
        base: str = 'main'
    ) -> Dict[str, Any]:
        """
        Create a pull request on GitHub
        
        Args:
            repo: Repository in format 'owner/repo'
            title: PR title
            body: PR description
            head: Head branch
            base: Base branch (default: main)
            
        Returns:
            Dict with success status and PR URL
        """
        try:
            if not self.github_token:
                return {'success': False, 'error': 'GitHub token not configured'}
            
            headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            data = {
                'title': title,
                'body': body,
                'head': head,
                'base': base
            }
            
            response = requests.post(
                f"https://api.github.com/repos/{repo}/pulls",
                headers=headers,
                json=data
            )
            
            if response.status_code == 201:
                pr_data = response.json()
                return {
                    'success': True,
                    'pr_url': pr_data['html_url'],
                    'pr_number': pr_data['number']
                }
            else:
                return {
                    'success': False,
                    'error': f"GitHub API error: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            logger.error(f"Create PR failed: {e}")
            return {'success': False, 'error': str(e)}


def get_git_tool(sandbox_endpoint: str) -> GitTool:
    """Factory function to create GitTool instance"""
    return GitTool(sandbox_endpoint)
