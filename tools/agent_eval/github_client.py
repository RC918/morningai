#!/usr/bin/env python3
"""
GitHub Client for Agent Evaluation

Provides interface to check PR CI status via GitHub API.
"""

import os
import logging
from typing import Optional, Dict, List
from github import Github, GithubException

logger = logging.getLogger(__name__)


class GitHubClient:
    """Client for interacting with GitHub API."""
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize GitHub client.
        
        Args:
            token: GitHub personal access token (optional, uses GITHUB_TOKEN env if not provided)
        """
        self.token = token or os.getenv('GITHUB_TOKEN')
        
        if not self.token:
            logger.warning("No GitHub token provided. API rate limits will be restrictive.")
            self.github = Github()
        else:
            self.github = Github(self.token)
        
        logger.info("GitHub client initialized")
    
    def get_pr_from_url(self, pr_url: str) -> Optional[Dict]:
        """
        Extract PR information from URL.
        
        Args:
            pr_url: GitHub PR URL (e.g., https://github.com/owner/repo/pull/123)
        
        Returns:
            dict: {"owner": str, "repo": str, "pr_number": int} or None if invalid
        """
        try:
            parts = pr_url.rstrip('/').split('/')
            
            if len(parts) < 7 or parts[-2] != 'pull':
                logger.error(f"Invalid PR URL format: {pr_url}")
                return None
            
            owner = parts[-4]
            repo = parts[-3]
            pr_number = int(parts[-1])
            
            return {
                "owner": owner,
                "repo": repo,
                "pr_number": pr_number
            }
        except (ValueError, IndexError) as e:
            logger.error(f"Failed to parse PR URL: {pr_url}, error: {e}")
            return None
    
    def check_pr_ci_status(self, pr_url: str) -> Dict:
        """
        Check CI status for a GitHub PR.
        
        Args:
            pr_url: GitHub PR URL
        
        Returns:
            dict: {
                "ci_passed": bool,
                "total_checks": int,
                "passed_checks": int,
                "failed_checks": int,
                "pending_checks": int,
                "check_details": List[Dict],
                "error": str or None
            }
        """
        result = {
            "ci_passed": False,
            "total_checks": 0,
            "passed_checks": 0,
            "failed_checks": 0,
            "pending_checks": 0,
            "check_details": [],
            "error": None
        }
        
        try:
            pr_info = self.get_pr_from_url(pr_url)
            if not pr_info:
                result["error"] = "Invalid PR URL"
                return result
            
            repo = self.github.get_repo(f"{pr_info['owner']}/{pr_info['repo']}")
            pr = repo.get_pull(pr_info['pr_number'])
            
            commits = list(pr.get_commits())
            if not commits:
                result["error"] = "No commits found in PR"
                return result
            
            latest_commit = commits[-1]
            
            check_runs = latest_commit.get_check_runs()
            statuses = latest_commit.get_statuses()
            
            for check_run in check_runs:
                result["total_checks"] += 1
                
                check_detail = {
                    "name": check_run.name,
                    "status": check_run.status,
                    "conclusion": check_run.conclusion,
                    "type": "check_run"
                }
                result["check_details"].append(check_detail)
                
                if check_run.status == "completed":
                    if check_run.conclusion == "success":
                        result["passed_checks"] += 1
                    elif check_run.conclusion in ["failure", "cancelled", "timed_out"]:
                        result["failed_checks"] += 1
                else:
                    result["pending_checks"] += 1
            
            for status in statuses:
                result["total_checks"] += 1
                
                check_detail = {
                    "name": status.context,
                    "status": status.state,
                    "conclusion": status.state,
                    "type": "status"
                }
                result["check_details"].append(check_detail)
                
                if status.state == "success":
                    result["passed_checks"] += 1
                elif status.state == "failure":
                    result["failed_checks"] += 1
                elif status.state == "pending":
                    result["pending_checks"] += 1
            
            if result["total_checks"] == 0:
                result["ci_passed"] = False
                result["error"] = "No CI checks found"
            elif result["pending_checks"] > 0:
                result["ci_passed"] = False
                result["error"] = f"{result['pending_checks']} checks still pending"
            elif result["failed_checks"] > 0:
                result["ci_passed"] = False
            else:
                result["ci_passed"] = True
            
            logger.info(f"CI status checked for PR {pr_url}", extra={
                "pr_url": pr_url,
                "ci_passed": result["ci_passed"],
                "total_checks": result["total_checks"],
                "passed": result["passed_checks"],
                "failed": result["failed_checks"],
                "pending": result["pending_checks"]
            })
            
        except GithubException as e:
            logger.error(f"GitHub API error: {e}", extra={"pr_url": pr_url})
            result["error"] = f"GitHub API error: {e.status} - {e.data.get('message', 'Unknown error')}"
        except Exception as e:
            logger.error(f"Unexpected error checking CI status: {e}", extra={"pr_url": pr_url})
            result["error"] = f"Unexpected error: {str(e)}"
        
        return result
    
    def get_pr_details(self, pr_url: str) -> Optional[Dict]:
        """
        Get detailed PR information.
        
        Args:
            pr_url: GitHub PR URL
        
        Returns:
            dict: PR details or None if error
        """
        try:
            pr_info = self.get_pr_from_url(pr_url)
            if not pr_info:
                return None
            
            repo = self.github.get_repo(f"{pr_info['owner']}/{pr_info['repo']}")
            pr = repo.get_pull(pr_info['pr_number'])
            
            return {
                "number": pr.number,
                "title": pr.title,
                "state": pr.state,
                "merged": pr.merged,
                "mergeable": pr.mergeable,
                "created_at": pr.created_at.isoformat() if pr.created_at else None,
                "updated_at": pr.updated_at.isoformat() if pr.updated_at else None,
                "merged_at": pr.merged_at.isoformat() if pr.merged_at else None,
                "user": pr.user.login if pr.user else None,
                "head_sha": pr.head.sha,
                "base_ref": pr.base.ref,
                "head_ref": pr.head.ref
            }
        except Exception as e:
            logger.error(f"Failed to get PR details: {e}", extra={"pr_url": pr_url})
            return None


class MockGitHubClient(GitHubClient):
    """Mock GitHub client for testing without API access."""
    
    def __init__(self):
        """Initialize mock client without GitHub token."""
        self.token = None
        logger.info("Mock GitHub client initialized")
    
    def check_pr_ci_status(self, pr_url: str) -> Dict:
        """Mock CI status check."""
        logger.info(f"Mock CI status check for {pr_url}")
        
        return {
            "ci_passed": True,
            "total_checks": 3,
            "passed_checks": 3,
            "failed_checks": 0,
            "pending_checks": 0,
            "check_details": [
                {"name": "build", "status": "completed", "conclusion": "success", "type": "check_run"},
                {"name": "test", "status": "completed", "conclusion": "success", "type": "check_run"},
                {"name": "lint", "status": "completed", "conclusion": "success", "type": "check_run"}
            ],
            "error": None
        }
    
    def get_pr_details(self, pr_url: str) -> Optional[Dict]:
        """Mock PR details retrieval."""
        pr_info = self.get_pr_from_url(pr_url)
        if not pr_info:
            return None
        
        return {
            "number": pr_info["pr_number"],
            "title": "Mock PR Title",
            "state": "open",
            "merged": False,
            "mergeable": True,
            "created_at": "2025-11-17T00:00:00Z",
            "updated_at": "2025-11-17T12:00:00Z",
            "merged_at": None,
            "user": "mock-user",
            "head_sha": "abc123def456",
            "base_ref": "main",
            "head_ref": "feature-branch"
        }
