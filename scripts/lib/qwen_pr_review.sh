#!/usr/bin/env bash
# scripts/lib/qwen_pr_review.sh
#
# Shared library for Qwen AI Code Review workflow
# Used by both production workflow and test workflow to ensure consistency
#
# Usage:
#   source scripts/lib/qwen_pr_review.sh
#
# This file contains shared constants and functions to avoid drift between
# the production workflow (.github/workflows/qwen-pr-review.yml) and
# the test workflow (.github/workflows/qwen-review-tests.yml).
#
# MAINTENANCE NOTE:
# When modifying this file, both workflows will automatically use the updated logic.
# Run the test workflow to verify changes before merging.

set -euo pipefail

# =============================================================================
# CONSTANTS
# =============================================================================

# Sensitive file detection pattern (case-insensitive)
# Matches: .env, .env.*, .pem, .key, .secret, .credential
# Note: .env.* includes backup files like .env.example.bak (intentional)
# Note: .pem.bak, .key.old do NOT match (anchored to $)
readonly QWEN_SENSITIVE_FILE_PATTERN='\.(env(\..+)?|pem|key|secret|credential)$'

# API retry configuration
# Transient errors worth retrying (rate limit, server errors)
readonly QWEN_RETRY_CODES="429 500 502 503 504"
# Non-transient errors (bad request, auth, not found) - don't retry
readonly QWEN_NO_RETRY_CODES="400 401 403 404"
# Maximum retry attempts
readonly QWEN_MAX_ATTEMPTS=3
# Maximum backoff seconds (cap for exponential backoff)
readonly QWEN_MAX_BACKOFF=30

# Markdown truncation limits
readonly QWEN_MAX_COMMENT_LENGTH=60000
readonly QWEN_MIN_TRUNCATE_POSITION=50000

# =============================================================================
# FUNCTIONS
# =============================================================================

# Check if a file path matches sensitive file patterns
# Usage: qwen_is_sensitive_file "path/to/file"
# Returns: 0 if sensitive, 1 if not
qwen_is_sensitive_file() {
    local file="$1"
    echo "$file" | grep -Eiq "$QWEN_SENSITIVE_FILE_PATTERN"
}

# Check if an HTTP code should trigger a retry
# Usage: qwen_should_retry "429"
# Returns: 0 if should retry, 1 if not
qwen_should_retry() {
    local http_code="$1"
    echo "$QWEN_RETRY_CODES" | grep -qw "$http_code"
}

# Check if an HTTP code is a non-transient error (should not retry)
# Usage: qwen_is_non_transient_error "401"
# Returns: 0 if non-transient, 1 if not
qwen_is_non_transient_error() {
    local http_code="$1"
    echo "$QWEN_NO_RETRY_CODES" | grep -qw "$http_code"
}

# Calculate exponential backoff with cap
# Usage: qwen_calculate_backoff 3  # returns 8 (2^3, capped at 30)
# Output: backoff seconds to stdout
qwen_calculate_backoff() {
    local attempt="$1"
    local backoff=$((2 ** attempt))
    if [ "$backoff" -gt "$QWEN_MAX_BACKOFF" ]; then
        backoff=$QWEN_MAX_BACKOFF
    fi
    echo "$backoff"
}

# Remove @mentions from text by inserting zero-width space
# This prevents notification spam while preserving readability
# Email addresses (foo@bar.com) are NOT modified
# Usage: qwen_remove_mentions "Hello @user"
# Output: sanitized text to stdout
qwen_remove_mentions() {
    local text="$1"
    # Use perl for reliable Unicode handling
    # Negative lookbehind ensures we don't modify email addresses
    printf '%s' "$text" | perl -CSD -pe 's/(?<![a-zA-Z0-9])@([a-zA-Z0-9_-]+)/@\x{200B}$1/g' 2>/dev/null || printf '%s' "$text"
}

# Count code fence markers (```) in text
# Usage: qwen_count_code_fences "text with ```code```"
# Output: count to stdout
qwen_count_code_fences() {
    local text="$1"
    printf '%s' "$text" | grep -c '```' || echo "0"
}

# Check if code fences are balanced (even count)
# Usage: qwen_has_balanced_fences "text"
# Returns: 0 if balanced, 1 if unbalanced
qwen_has_balanced_fences() {
    local text="$1"
    local count
    count=$(qwen_count_code_fences "$text")
    [ $((count % 2)) -eq 0 ]
}

# Write multiline content to GITHUB_ENV safely
# Usage: qwen_write_env "VAR_NAME" "multiline content"
qwen_write_env() {
    local var_name="$1"
    local content="$2"
    local delimiter
    delimiter=$(openssl rand -hex 16)
    {
        printf '%s\n' "${var_name}<<${delimiter}"
        printf '%s\n' "$content"
        printf '%s\n' "$delimiter"
    } >> "$GITHUB_ENV"
}

# =============================================================================
# EXPORT CHECK
# =============================================================================

# Marker to verify the library was sourced
QWEN_LIB_LOADED=true
