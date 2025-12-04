#!/usr/bin/env bash
# Unified Migration Runner for MorningAI
# ======================================
# Phase 4: Engineering Optimization (#1819)
#
# Discovers and runs all SQL migrations in numerical order.
# Supports dry-run mode, specific migration selection, filtering,
# and agent-specific migrations.
#
# Usage:
#   ./scripts/run_migrations.sh                    # Run all main migrations
#   ./scripts/run_migrations.sh --dry-run          # Show what would be run
#   ./scripts/run_migrations.sh --from 010         # Run migrations from 010 onwards
#   ./scripts/run_migrations.sh --only 015         # Run only migration 015
#   ./scripts/run_migrations.sh --list             # List all available migrations
#   ./scripts/run_migrations.sh --agents           # Include agent-specific migrations
#   ./scripts/run_migrations.sh --all              # Run all migrations (main + agents)
#   ./scripts/run_migrations.sh --verify           # Verify no duplicate migration numbers
#
# Migration Directories:
#   - migrations/                           Main migrations (001-999)
#   - agents/dev_agent/migrations/          Dev Agent migrations
#   - agents/faq_agent/migrations/          FAQ Agent migrations
#
# Environment:
#   DATABASE_URL - Required. PostgreSQL connection string.
#
# Exit codes:
#   0 - All migrations applied successfully
#   1 - Migration error
#   2 - Configuration error
#   3 - Duplicate migration numbers detected

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory and repo root
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$DIR/.." && pwd)"
MIG_DIR="$REPO_ROOT/migrations"

# Agent migration directories
DEV_AGENT_MIG_DIR="$REPO_ROOT/agents/dev_agent/migrations"
FAQ_AGENT_MIG_DIR="$REPO_ROOT/agents/faq_agent/migrations"

# Migration directory configuration (directory:label pairs)
# Used by for_each_migration_dir() helper for DRY iteration
declare -a MIGRATION_DIR_CONFIG=(
    "$MIG_DIR:main migrations"
    "$DEV_AGENT_MIG_DIR:dev_agent migrations"
    "$FAQ_AGENT_MIG_DIR:faq_agent migrations"
)

# Default options
DRY_RUN=false
FROM_MIGRATION=""
ONLY_MIGRATION=""
LIST_ONLY=false
VERBOSE=false
INCLUDE_AGENTS=false
RUN_ALL=false
VERIFY_ONLY=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --from)
            if [[ -z "${2:-}" ]]; then
                echo -e "${RED}ERROR: --from requires a migration number${NC}" >&2
                exit 2
            fi
            FROM_MIGRATION="$2"
            shift 2
            ;;
        --only)
            if [[ -z "${2:-}" ]]; then
                echo -e "${RED}ERROR: --only requires a migration number${NC}" >&2
                exit 2
            fi
            ONLY_MIGRATION="$2"
            shift 2
            ;;
        --list)
            LIST_ONLY=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --agents)
            INCLUDE_AGENTS=true
            shift
            ;;
        --all)
            RUN_ALL=true
            INCLUDE_AGENTS=true
            shift
            ;;
        --verify)
            VERIFY_ONLY=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --dry-run     Show what would be run without executing"
            echo "  --from NUM    Run migrations from NUM onwards (e.g., --from 010)"
            echo "  --only NUM    Run only migration NUM (e.g., --only 015)"
            echo "  --list        List all available migrations"
            echo "  --agents      Include agent-specific migrations"
            echo "  --all         Run all migrations (main + agents)"
            echo "  --verify      Verify no duplicate migration numbers"
            echo "  --verbose,-v  Show detailed output"
            echo "  --help,-h     Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}ERROR: Unknown option: $1${NC}" >&2
            exit 2
            ;;
    esac
done

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1" >&2
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $1" >&2
}

# Get list of migration files (numbered .sql files only)
get_migrations() {
    find "$MIG_DIR" -maxdepth 1 -name '[0-9][0-9][0-9]_*.sql' -type f | sort
}

# Get list of agent migration files
get_agent_migrations() {
    local dir="$1"
    if [[ -d "$dir" ]]; then
        find "$dir" -maxdepth 1 -name '[0-9][0-9][0-9]_*.sql' -type f | sort
    fi
}

# Extract migration number from filename
get_migration_number() {
    basename "$1" | grep -oE '^[0-9]+' || echo "000"
}

# Helper: Iterate over migration directories and execute a callback
# Usage: for_each_migration_dir callback_function [include_agents]
# The callback receives: directory, label, is_main (true/false)
# If include_agents is "false", only main migrations are processed
for_each_migration_dir() {
    local callback="$1"
    local include_agents="${2:-true}"
    local is_first=true
    
    for config in "${MIGRATION_DIR_CONFIG[@]}"; do
        local dir="${config%%:*}"
        local label="${config##*:}"
        local is_main="false"
        
        # Check if this is the main migrations directory
        if [[ "$dir" == "$MIG_DIR" ]]; then
            is_main="true"
        fi
        
        # Skip agent directories if not included
        if [[ "$is_main" == "false" ]] && [[ "$include_agents" == "false" ]]; then
            continue
        fi
        
        # Execute callback with directory info
        "$callback" "$dir" "$label" "$is_main" "$is_first"
        is_first=false
    done
}

# Verify no duplicate migration numbers in a directory
verify_no_duplicates() {
    local dir="$1"
    local label="$2"
    local has_duplicates=false
    
    if [[ ! -d "$dir" ]]; then
        return 0
    fi
    
    local numbers
    numbers=$(find "$dir" -maxdepth 1 -name '[0-9][0-9][0-9]_*.sql' -type f -exec basename {} \; 2>/dev/null | grep -oE '^[0-9]+' | sort)
    
    if [[ -z "$numbers" ]]; then
        return 0
    fi
    
    local duplicates
    duplicates=$(echo "$numbers" | uniq -d)
    
    if [[ -n "$duplicates" ]]; then
        log_error "Duplicate migration numbers found in $label:"
        for num in $duplicates; do
            echo "  - $num:"
            find "$dir" -maxdepth 1 -name "${num}_*.sql" -type f -exec basename {} \; | sed 's/^/      /'
        done
        has_duplicates=true
    fi
    
    if [[ "$has_duplicates" == "true" ]]; then
        return 1
    fi
    return 0
}

# Callback for verify_all_migrations: verify a single directory
# Sets VERIFY_HAS_ERRORS=true if duplicates found
_verify_dir_callback() {
    local dir="$1"
    local label="$2"
    local is_main="$3"
    local is_first="$4"
    
    # Capitalize first letter of label for display
    local display_label
    display_label=$(echo "$label" | sed 's/\b\(.\)/\u\1/g')
    
    if ! verify_no_duplicates "$dir" "$label"; then
        VERIFY_HAS_ERRORS=true
    else
        log_success "$display_label: No duplicates"
    fi
}

# Verify all migration directories (DRY refactored)
verify_all_migrations() {
    log_info "Verifying migration directories for duplicate numbers..."
    echo ""
    
    VERIFY_HAS_ERRORS=false
    for_each_migration_dir _verify_dir_callback "true"
    
    echo ""
    if [[ "$VERIFY_HAS_ERRORS" == "true" ]]; then
        log_error "Duplicate migration numbers detected. Please fix before running migrations."
        return 1
    else
        log_success "All migration directories verified - no duplicates found"
        return 0
    fi
}

# Helper: List migrations in a single directory
# Usage: _list_dir_migrations directory label
_list_dir_migrations() {
    local dir="$1"
    local label="$2"
    
    # Capitalize first letter of label for display
    local display_label
    display_label=$(echo "$label" | sed 's/\b\(.\)/\u\1/g')
    
    echo ""
    echo "$display_label in $dir:"
    echo "=================================="
    
    local count=0
    local get_func="get_migrations"
    
    # Use get_agent_migrations for non-main directories
    if [[ "$dir" != "$MIG_DIR" ]]; then
        get_func="get_agent_migrations"
    fi
    
    while IFS= read -r migration; do
        if [[ -n "$migration" ]]; then
            local num
            num=$(get_migration_number "$migration")
            local name
            name=$(basename "$migration")
            echo "  $num: $name"
            ((count++)) || true
        fi
    done < <(if [[ "$get_func" == "get_migrations" ]]; then get_migrations; else get_agent_migrations "$dir"; fi)
    
    echo ""
    echo "Total: $count $label"
}

# Callback for list_migrations: list a single directory
_list_dir_callback() {
    local dir="$1"
    local label="$2"
    local is_main="$3"
    local is_first="$4"
    
    _list_dir_migrations "$dir" "$label"
}

# List all migrations (DRY refactored)
list_migrations() {
    local include_agents="false"
    if [[ "$INCLUDE_AGENTS" == "true" ]] || [[ "$RUN_ALL" == "true" ]]; then
        include_agents="true"
    fi
    
    for_each_migration_dir _list_dir_callback "$include_agents"
    echo ""
}

# Check if migration should be run based on filters
should_run_migration() {
    local migration="$1"
    local num
    num=$(get_migration_number "$migration")

    # If --only is specified, only run that migration
    if [[ -n "$ONLY_MIGRATION" ]]; then
        [[ "$num" == "$ONLY_MIGRATION" ]] && return 0 || return 1
    fi

    # If --from is specified, skip migrations before that number
    # Use 10# prefix to force base-10 interpretation (avoid octal issues with 008, 009)
    if [[ -n "$FROM_MIGRATION" ]]; then
        [[ "10#$num" -ge "10#$FROM_MIGRATION" ]] && return 0 || return 1
    fi

    return 0
}

# Run a single migration
run_migration() {
    local migration="$1"
    local name
    name=$(basename "$migration")

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY-RUN] Would run: $name"
        return 0
    fi

    log_info "Running: $name"

    local output
    local exit_code
    
    if [[ "$VERBOSE" == "true" ]]; then
        if psql "$DATABASE_URL" -f "$migration" 2>&1; then
            log_success "$name"
            return 0
        else
            log_error "$name"
            return 1
        fi
    else
        output=$(psql "$DATABASE_URL" -f "$migration" -q 2>&1) && exit_code=0 || exit_code=$?
        if [[ $exit_code -eq 0 ]]; then
            log_success "$name"
            return 0
        else
            log_error "$name"
            echo "$output" >&2
            return 1
        fi
    fi
}

# Main execution
main() {
    # Verify mode
    if [[ "$VERIFY_ONLY" == "true" ]]; then
        if verify_all_migrations; then
            exit 0
        else
            exit 3
        fi
    fi

    # List mode
    if [[ "$LIST_ONLY" == "true" ]]; then
        list_migrations
        exit 0
    fi

    # Check DATABASE_URL (not required for dry-run mode)
    if [[ -z "${DATABASE_URL:-}" ]] && [[ "$DRY_RUN" != "true" ]]; then
        log_error "DATABASE_URL is not set"
        echo "  Set DATABASE_URL environment variable to your PostgreSQL connection string"
        exit 2
    fi

    # Check migrations directory
    if [[ ! -d "$MIG_DIR" ]]; then
        log_error "Migrations directory not found: $MIG_DIR"
        exit 2
    fi

    echo ""
    echo "========================================"
    echo "  MorningAI Unified Migration Runner"
    echo "========================================"
    echo ""

    if [[ "$DRY_RUN" == "true" ]]; then
        log_warning "DRY-RUN MODE - No changes will be made"
        echo ""
    fi

    # Get migrations to run
    local migrations_to_run=()
    while IFS= read -r migration; do
        if [[ -n "$migration" ]] && should_run_migration "$migration"; then
            migrations_to_run+=("$migration")
        fi
    done < <(get_migrations)

    if [[ ${#migrations_to_run[@]} -eq 0 ]]; then
        log_warning "No migrations to run"
        exit 0
    fi

    log_info "Found ${#migrations_to_run[@]} migration(s) to run"
    echo ""

    # Run migrations
    local success_count=0
    local failed_count=0
    local failed_migrations=()

    for migration in "${migrations_to_run[@]}"; do
        if run_migration "$migration"; then
            ((success_count++)) || true
        else
            ((failed_count++)) || true
            failed_migrations+=("$(basename "$migration")")
        fi
    done

    # Summary
    echo ""
    echo "========================================"
    echo "  Migration Summary"
    echo "========================================"
    echo ""
    log_info "Total:   ${#migrations_to_run[@]}"
    log_success "Success: $success_count"

    if [[ $failed_count -gt 0 ]]; then
        log_error "Failed:  $failed_count"
        echo ""
        log_error "Failed migrations:"
        for failed in "${failed_migrations[@]}"; do
            echo "  - $failed"
        done
        echo ""
        exit 1
    fi

    echo ""
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "Dry-run complete. No changes were made."
    else
        log_success "All migrations applied successfully!"
    fi
    echo ""
}

main "$@"
