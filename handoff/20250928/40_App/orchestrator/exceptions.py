#!/usr/bin/env python3
"""
Custom exceptions for Orchestrator system

Provides specific exception types for better error handling and debugging.
"""


class OrchestratorException(Exception):
    """Base exception for all orchestrator errors"""
    pass


class DatabaseException(OrchestratorException):
    """Base exception for database-related errors"""
    pass


class DatabaseConnectionError(DatabaseException):
    """Failed to connect to database"""
    pass


class DatabaseWriteError(DatabaseException):
    """Failed to write to database"""
    pass


class DatabaseReadError(DatabaseException):
    """Failed to read from database"""
    pass


class TenantResolutionError(DatabaseException):
    """Failed to resolve tenant_id for user"""
    pass


class MCPException(OrchestratorException):
    """Base exception for MCP client errors"""
    pass


class MCPConnectionError(MCPException):
    """Failed to connect to MCP server"""
    pass


class MCPToolError(MCPException):
    """MCP tool execution failed"""
    pass


class MCPTimeoutError(MCPException):
    """MCP operation timed out"""
    pass


class GitHubException(OrchestratorException):
    """Base exception for GitHub API errors"""
    pass


class GitHubAuthenticationError(GitHubException):
    """GitHub authentication failed (invalid token)"""
    pass


class GitHubRateLimitError(GitHubException):
    """GitHub API rate limit exceeded"""
    pass


class GitHubResourceNotFoundError(GitHubException):
    """GitHub resource not found (repo, PR, branch)"""
    pass


class GitHubPermissionError(GitHubException):
    """Insufficient permissions for GitHub operation"""
    pass


class WorkflowException(OrchestratorException):
    """Base exception for workflow errors"""
    pass


class WorkflowStepError(WorkflowException):
    """Workflow step execution failed"""
    pass


class WorkflowTimeoutError(WorkflowException):
    """Workflow exceeded maximum execution time"""
    pass


class WorkflowCIError(WorkflowException):
    """CI checks failed and could not be fixed"""
    pass


class ValidationException(OrchestratorException):
    """Base exception for validation errors"""
    pass


class InvalidConfigurationError(ValidationException):
    """Configuration is invalid or missing"""
    pass


class InvalidInputError(ValidationException):
    """Input validation failed"""
    pass
