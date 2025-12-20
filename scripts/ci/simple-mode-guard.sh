#!/bin/bash
# =============================================================================
# Simple Mode Guard - CI Script
# =============================================================================
#
# PURPOSE:
#   Prevents reintroduction of deprecated Simple Mode code after LangGraph
#   100% rollout. Scans git diff for forbidden symbols in Python files.
#
# USAGE:
#   ./scripts/ci/simple-mode-guard.sh <base_sha> <head_sha>
#
# ARGUMENTS:
#   base_sha  - Base commit SHA (PR base)
#   head_sha  - Head commit SHA (PR head)
#
# EXIT CODES:
#   0 - No violations found
#   1 - Violations detected
#   2 - Invalid arguments
#   3 - Git error
#
# FORBIDDEN SYMBOLS:
#   - record_simple_task (removed method)
#   - "Simple Mode" (deprecated terminology)
#   - USE_LANGGRAPH_PERCENT (obsolete env var)
#   - use_langgraph_percent (obsolete setting)
#
# EXCEPTIONS (not flagged as violations):
#   - Comments explaining removal (e.g., "NOTE: removed in Issue #2651")
#   - ADR/changelog entries documenting deprecation
#   - Test files that verify absence of Simple Mode
#
# RELATED:
#   - Issue #2651: Remove Simple Mode code after LangGraph 100% rollout
#   - ADR-005: Deprecate Simple Orchestrator Mode
#
# =============================================================================

set -euo pipefail

# Configuration
readonly SCRIPT_NAME="$(basename "$0")"
readonly MAX_FILES=100
readonly MAX_LINES_PER_FILE=10000

# Directories to scan (relative to repo root)
readonly SCAN_DIRS=(
    "handoff/20250928/40_App/orchestrator"
    "handoff/20250928/40_App/api-backend"
    "common"
)

# Forbidden symbols and their descriptions
declare -A FORBIDDEN_SYMBOLS=(
    ["record_simple_task"]="removed method"
    ["USE_LANGGRAPH_PERCENT"]="obsolete env var"
    ["use_langgraph_percent"]="obsolete setting"
)

# =============================================================================
# FUNCTIONS
# =============================================================================

usage() {
    echo "Usage: $SCRIPT_NAME <base_sha> <head_sha>"
    echo ""
    echo "Scans git diff for forbidden Simple Mode symbols in Python files."
    echo ""
    echo "Arguments:"
    echo "  base_sha  Base commit SHA (PR base)"
    echo "  head_sha  Head commit SHA (PR head)"
    echo ""
    echo "Exit codes:"
    echo "  0  No violations found"
    echo "  1  Violations detected"
    echo "  2  Invalid arguments"
    echo "  3  Git error"
}

log_info() {
    echo "[INFO] $*"
}

log_warn() {
    echo "[WARN] $*" >&2
}

log_error() {
    echo "[ERROR] $*" >&2
}

# Check if a line should be excluded from violation detection
is_excluded_line() {
    local line="$1"
    
    # Exclude comments explaining removal
    if [[ "$line" =~ "NOTE:" ]] || \
       [[ "$line" =~ "# NOTE" ]] || \
       [[ "$line" =~ "# TODO:" ]] || \
       [[ "$line" =~ "#.*removed" ]] || \
       [[ "$line" =~ "deprecated" ]] || \
       [[ "$line" =~ "removed" ]]; then
        return 0
    fi
    
    return 1
}

# Check a single line for forbidden symbols
check_line_for_violations() {
    local line="$1"
    local file="$2"
    local violations=()
    
    # Skip excluded lines
    if is_excluded_line "$line"; then
        return 0
    fi
    
    # Check for record_simple_task
    if [[ "$line" =~ record_simple_task ]]; then
        violations+=("record_simple_task")
    fi
    
    # Check for USE_LANGGRAPH_PERCENT
    if [[ "$line" =~ USE_LANGGRAPH_PERCENT ]]; then
        violations+=("USE_LANGGRAPH_PERCENT")
    fi
    
    # Check for use_langgraph_percent
    if [[ "$line" =~ use_langgraph_percent ]]; then
        violations+=("use_langgraph_percent")
    fi
    
    # Check for "Simple Mode" string (case insensitive)
    if [[ "${line,,}" =~ \"simple\ mode\" ]]; then
        violations+=("\"Simple Mode\"")
    fi
    
    # Return violations
    if [[ ${#violations[@]} -gt 0 ]]; then
        for v in "${violations[@]}"; do
            echo "$v"
        done
        return 1
    fi
    
    return 0
}

# Get list of changed Python files in relevant directories
get_changed_files() {
    local base_sha="$1"
    local head_sha="$2"
    local files=()
    
    for dir in "${SCAN_DIRS[@]}"; do
        # Use git pathspec glob magic for reliable matching
        while IFS= read -r file; do
            if [[ -n "$file" ]]; then
                files+=("$file")
            fi
        done < <(git diff --name-only --diff-filter=AM "$base_sha".."$head_sha" -- ":(glob)$dir/**/*.py" 2>/dev/null || true)
    done
    
    printf '%s\n' "${files[@]}"
}

# Scan a single file for violations
scan_file() {
    local base_sha="$1"
    local head_sha="$2"
    local file="$3"
    local file_violations=0
    local line_count=0
    
    # Get added lines for this file
    while IFS= read -r line; do
        # Skip diff headers
        if [[ "$line" =~ ^\+\+\+ ]]; then
            continue
        fi
        
        # Only process added lines (starting with +)
        if [[ "$line" =~ ^\+ ]]; then
            line_count=$((line_count + 1))
            
            # Safety limit
            if [[ $line_count -gt $MAX_LINES_PER_FILE ]]; then
                log_warn "File $file exceeds $MAX_LINES_PER_FILE added lines, truncating scan"
                break
            fi
            
            # Remove leading + for checking
            local content="${line:1}"
            
            # Check for violations
            local found_violations
            if found_violations=$(check_line_for_violations "$content" "$file"); then
                : # No violations
            else
                while IFS= read -r violation; do
                    if [[ -n "$violation" ]]; then
                        echo "VIOLATION:$file:$violation"
                        file_violations=$((file_violations + 1))
                    fi
                done <<< "$found_violations"
            fi
        fi
    done < <(git diff "$base_sha".."$head_sha" -U0 -- "$file" 2>/dev/null || true)
    
    return $file_violations
}

# Main scanning function
scan_for_violations() {
    local base_sha="$1"
    local head_sha="$2"
    local total_violations=0
    local files_scanned=0
    local violation_details=()
    
    log_info "Scanning for forbidden Simple Mode symbols..."
    log_info "Base SHA: $base_sha"
    log_info "Head SHA: $head_sha"
    
    # Get changed files
    local changed_files
    changed_files=$(get_changed_files "$base_sha" "$head_sha")
    
    if [[ -z "$changed_files" ]]; then
        log_info "No Python files changed in relevant directories"
        return 0
    fi
    
    # Count files
    local file_count
    file_count=$(echo "$changed_files" | wc -l)
    
    if [[ $file_count -gt $MAX_FILES ]]; then
        log_warn "Too many files changed ($file_count > $MAX_FILES), scanning first $MAX_FILES only"
    fi
    
    # Scan each file
    while IFS= read -r file; do
        if [[ -z "$file" ]]; then
            continue
        fi
        
        files_scanned=$((files_scanned + 1))
        
        if [[ $files_scanned -gt $MAX_FILES ]]; then
            break
        fi
        
        # Scan file and collect violations
        local file_output
        file_output=$(scan_file "$base_sha" "$head_sha" "$file" 2>&1) || true
        
        while IFS= read -r violation_line; do
            if [[ "$violation_line" =~ ^VIOLATION: ]]; then
                violation_details+=("$violation_line")
                total_violations=$((total_violations + 1))
            fi
        done <<< "$file_output"
        
    done <<< "$changed_files"
    
    # Report results
    echo ""
    log_info "Scan complete: $files_scanned files scanned"
    
    if [[ $total_violations -gt 0 ]]; then
        echo ""
        log_error "Found $total_violations violation(s):"
        echo ""
        
        # Group violations by file
        declare -A file_violations
        for v in "${violation_details[@]}"; do
            local file="${v#VIOLATION:}"
            file="${file%%:*}"
            local symbol="${v##*:}"
            if [[ -n "${file_violations[$file]:-}" ]]; then
                file_violations[$file]="${file_violations[$file]}, $symbol"
            else
                file_violations[$file]="$symbol"
            fi
        done
        
        for file in "${!file_violations[@]}"; do
            echo "  - $file: ${file_violations[$file]}"
        done
        
        echo ""
        echo "Action Required: Remove deprecated Simple Mode references."
        echo "See docs/adr/005-deprecate-simple-orchestrator-mode.md for context."
        
        return 1
    else
        log_info "No violations found"
        return 0
    fi
}

# =============================================================================
# MAIN
# =============================================================================

main() {
    # Validate arguments
    if [[ $# -lt 2 ]]; then
        log_error "Missing required arguments"
        usage
        exit 2
    fi
    
    local base_sha="$1"
    local head_sha="$2"
    
    # Validate SHAs
    if ! git rev-parse --verify "$base_sha" >/dev/null 2>&1; then
        log_error "Invalid base SHA: $base_sha"
        exit 3
    fi
    
    if ! git rev-parse --verify "$head_sha" >/dev/null 2>&1; then
        log_error "Invalid head SHA: $head_sha"
        exit 3
    fi
    
    # Run scan
    if scan_for_violations "$base_sha" "$head_sha"; then
        exit 0
    else
        exit 1
    fi
}

# Run main if not sourced
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
