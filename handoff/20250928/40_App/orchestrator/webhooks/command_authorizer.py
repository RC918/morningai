"""
Command Authorizer - Permission gating for /morningai commands

This module provides authorization checks for PR comment commands,
ensuring only authorized users can trigger MorningAI flows.

Issue: #3388 - Add authorization/permission gating for /morningai commands
Blueprint Alignment:
    - Self-Governed: Authorization is part of the governance mechanism
    - Security: Prevents unauthorized command execution

Authorization Flow:
    1. Check if actor is in explicit allowlist (break-glass)
    2. Check GitHub permission level (admin/maintain/write required)
    3. Fail-closed on API errors (deny if can't verify)

Permission Levels (from GitHub API):
    - admin: Full repository access
    - maintain: Manage repository without destructive actions
    - write: Push to non-protected branches
    - triage: Manage issues and PRs without write access
    - read: Read-only access
    - none: No access

Only admin, maintain, and write are authorized to trigger commands.
"""

import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, Set, Tuple

from github import Github, GithubException

logger = logging.getLogger(__name__)


def _get_github_token() -> Optional[str]:
    """Get GitHub token from settings with lazy import to avoid import errors in tests."""
    try:
        from common.config.settings import settings
        return settings.agent_github_token or settings.github_token
    except ImportError:
        logger.warning("[CommandAuthorizer] Could not import settings, no default token available")
        return None


class PermissionLevel(Enum):
    """GitHub repository permission levels"""
    ADMIN = "admin"
    MAINTAIN = "maintain"
    WRITE = "write"
    TRIAGE = "triage"
    READ = "read"
    NONE = "none"
    UNKNOWN = "unknown"


# Permission levels that are authorized to trigger commands
AUTHORIZED_PERMISSION_LEVELS: Set[PermissionLevel] = {
    PermissionLevel.ADMIN,
    PermissionLevel.MAINTAIN,
    PermissionLevel.WRITE,
}


@dataclass
class AuthorizationResult:
    """Result of an authorization check"""
    authorized: bool
    reason: str
    permission_level: Optional[PermissionLevel] = None
    cached: bool = False

    def to_dict(self) -> Dict:
        return {
            "authorized": self.authorized,
            "reason": self.reason,
            "permission_level": self.permission_level.value if self.permission_level else None,
            "cached": self.cached,
        }


class CommandAuthorizer:
    """
    Authorization checker for /morningai commands.

    Checks if a user has sufficient permissions to trigger commands on a repository.
    Uses GitHub API to verify permission levels with caching to reduce API calls.

    Issue: #3388 - Add authorization/permission gating for /morningai commands
    """

    # Cache TTL in seconds (5 minutes)
    CACHE_TTL_SECONDS = 300

    def __init__(
        self,
        github_token: Optional[str] = None,
        allowlist: Optional[Set[str]] = None,
    ):
        """
        Initialize the Command Authorizer.

        Args:
            github_token: GitHub API token (defaults to settings.agent_github_token)
            allowlist: Optional set of usernames that are always authorized
        """
        self._github_token = github_token or _get_github_token()
        self._allowlist = allowlist or set()
        # Cache: {(repo, username): (permission_level, timestamp)}
        self._permission_cache: Dict[Tuple[str, str], Tuple[PermissionLevel, float]] = {}
        # Reuse Github client for performance (avoid creating new client per API call)
        self._gh: Optional[Github] = Github(self._github_token) if self._github_token else None

        logger.info(
            "[CommandAuthorizer] Initialized",
            extra={
                "operation": "authorizer_init",
                "allowlist_size": len(self._allowlist),
                "has_token": bool(self._github_token),
            }
        )

    def authorize(
        self,
        repo: str,
        username: str,
        skip_cache: bool = False,
    ) -> AuthorizationResult:
        """
        Check if a user is authorized to trigger commands on a repository.

        Authorization logic:
        1. If username is in allowlist, authorize immediately
        2. Check GitHub permission level (cached if available)
        3. Authorize if permission level is admin, maintain, or write
        4. Deny on API errors (fail-closed)

        Args:
            repo: Repository in owner/repo format
            username: GitHub username to check
            skip_cache: If True, bypass cache and fetch fresh permission

        Returns:
            AuthorizationResult with authorization decision and reason
        """
        # P0: Check allowlist first (break-glass)
        if username in self._allowlist:
            logger.info(
                "[CommandAuthorizer] User authorized via allowlist",
                extra={
                    "operation": "auth_allowlist",
                    "repo": repo,
                    "username": username,
                }
            )
            return AuthorizationResult(
                authorized=True,
                reason="User in allowlist",
                permission_level=None,
                cached=False,
            )

        # P1: Check cache
        if not skip_cache:
            cached_result = self._get_cached_permission(repo, username)
            if cached_result is not None:
                permission_level, _ = cached_result
                authorized = permission_level in AUTHORIZED_PERMISSION_LEVELS
                logger.debug(
                    "[CommandAuthorizer] Using cached permission",
                    extra={
                        "operation": "auth_cache_hit",
                        "repo": repo,
                        "username": username,
                        "permission_level": permission_level.value,
                        "authorized": authorized,
                    }
                )
                return AuthorizationResult(
                    authorized=authorized,
                    reason=f"Permission level: {permission_level.value}" if authorized
                           else f"Insufficient permission: {permission_level.value}",
                    permission_level=permission_level,
                    cached=True,
                )

        # P2: Fetch permission from GitHub API
        permission_level = self._fetch_permission_level(repo, username)

        if permission_level == PermissionLevel.UNKNOWN:
            # API error - fail closed
            logger.warning(
                "[CommandAuthorizer] Failed to verify permission, denying (fail-closed)",
                extra={
                    "operation": "auth_api_error",
                    "repo": repo,
                    "username": username,
                }
            )
            return AuthorizationResult(
                authorized=False,
                reason="Failed to verify permission (API error)",
                permission_level=PermissionLevel.UNKNOWN,
                cached=False,
            )

        # P3: Cache the result
        self._cache_permission(repo, username, permission_level)

        # P4: Check if authorized
        authorized = permission_level in AUTHORIZED_PERMISSION_LEVELS

        log_level = logging.INFO if authorized else logging.WARNING
        logger.log(
            log_level,
            "[CommandAuthorizer] Authorization decision",
            extra={
                "operation": "auth_decision",
                "repo": repo,
                "username": username,
                "permission_level": permission_level.value,
                "authorized": authorized,
            }
        )

        return AuthorizationResult(
            authorized=authorized,
            reason=f"Permission level: {permission_level.value}" if authorized
                   else f"Insufficient permission: {permission_level.value} (requires write or higher)",
            permission_level=permission_level,
            cached=False,
        )

    def _fetch_permission_level(self, repo: str, username: str) -> PermissionLevel:
        """
        Fetch user's permission level from GitHub API.

        Args:
            repo: Repository in owner/repo format
            username: GitHub username

        Returns:
            PermissionLevel (UNKNOWN on API error)
        """
        if not self._gh:
            logger.error(
                "[CommandAuthorizer] No GitHub client configured (missing token)",
                extra={
                    "operation": "auth_no_token",
                    "repo": repo,
                    "username": username,
                }
            )
            return PermissionLevel.UNKNOWN

        try:
            repository = self._gh.get_repo(repo)

            # Get collaborator permission level
            # This returns: admin, maintain, write, triage, read, or none
            permission = repository.get_collaborator_permission(username)

            # Map to PermissionLevel enum
            permission_map = {
                "admin": PermissionLevel.ADMIN,
                "maintain": PermissionLevel.MAINTAIN,
                "write": PermissionLevel.WRITE,
                "triage": PermissionLevel.TRIAGE,
                "read": PermissionLevel.READ,
                "none": PermissionLevel.NONE,
            }

            return permission_map.get(permission.lower(), PermissionLevel.UNKNOWN)

        except GithubException as e:
            logger.error(
                "[CommandAuthorizer] GitHub API error",
                extra={
                    "operation": "auth_github_error",
                    "repo": repo,
                    "username": username,
                    "error": str(e),
                    "status": getattr(e, 'status', None),
                }
            )
            return PermissionLevel.UNKNOWN

        except Exception as e:
            logger.error(
                "[CommandAuthorizer] Unexpected error fetching permission",
                extra={
                    "operation": "auth_unexpected_error",
                    "repo": repo,
                    "username": username,
                    "error": str(e),
                    "error_type": type(e).__name__,
                }
            )
            return PermissionLevel.UNKNOWN

    def _get_cached_permission(
        self,
        repo: str,
        username: str,
    ) -> Optional[Tuple[PermissionLevel, float]]:
        """Get cached permission if not expired"""
        cache_key = (repo, username)
        cached = self._permission_cache.get(cache_key)

        if cached is None:
            return None

        permission_level, timestamp = cached
        if time.time() - timestamp > self.CACHE_TTL_SECONDS:
            # Cache expired
            del self._permission_cache[cache_key]
            return None

        return cached

    def _cache_permission(
        self,
        repo: str,
        username: str,
        permission_level: PermissionLevel,
    ) -> None:
        """Cache permission level with timestamp"""
        cache_key = (repo, username)
        self._permission_cache[cache_key] = (permission_level, time.time())

    def clear_cache(self) -> None:
        """Clear the permission cache"""
        self._permission_cache.clear()
        logger.info("[CommandAuthorizer] Cache cleared")

    def add_to_allowlist(self, username: str) -> None:
        """Add a username to the allowlist"""
        self._allowlist.add(username)
        logger.info(
            "[CommandAuthorizer] Added to allowlist",
            extra={"username": username}
        )

    def remove_from_allowlist(self, username: str) -> None:
        """Remove a username from the allowlist"""
        self._allowlist.discard(username)
        logger.info(
            "[CommandAuthorizer] Removed from allowlist",
            extra={"username": username}
        )


# Global instance for convenience
_command_authorizer: Optional[CommandAuthorizer] = None


def get_command_authorizer() -> CommandAuthorizer:
    """Get or create global CommandAuthorizer instance"""
    global _command_authorizer
    if _command_authorizer is None:
        _command_authorizer = CommandAuthorizer()
    return _command_authorizer
