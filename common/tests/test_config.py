"""
Centralized configuration for lint tests across the codebase.

This module defines deprecated module lists that are shared across
api-backend, orchestrator, and agents. Each domain can extend the base
list with domain-specific deprecated modules.
"""

BASE_DEPRECATED_MODULES = [
    "utils.preauth_token",
    "src.utils.preauth_token",
]


API_BACKEND_DEPRECATED_MODULES = BASE_DEPRECATED_MODULES + [
]

ORCHESTRATOR_DEPRECATED_MODULES = BASE_DEPRECATED_MODULES + [
]

AGENTS_DEPRECATED_MODULES = BASE_DEPRECATED_MODULES + [
]

DEV_AGENT_DEPRECATED_MODULES = AGENTS_DEPRECATED_MODULES + []
FAQ_AGENT_DEPRECATED_MODULES = AGENTS_DEPRECATED_MODULES + []
OPS_AGENT_DEPRECATED_MODULES = AGENTS_DEPRECATED_MODULES + []

PREAUTH_TOKEN_MIGRATION_GUIDE = [
    "🔧 Migration Guide:",
    "  - Replace 'utils.preauth_token' with 'utils.pre_auth_token'",
    "  - Use PreAuthTokenManager class instead of standalone functions:",
    "    • generate_preauth_token() → PreAuthTokenManager.generate_token()",
    "    • validate_and_consume_preauth_token() → PreAuthTokenManager.verify_token() + consume_token_atomic()",
    "    • revoke_preauth_tokens_for_user() → PreAuthTokenManager.revoke_token()",
    "\n",
    "📚 See: handoff/20250928/40_App/api-backend/src/utils/pre_auth_token.py",
]
