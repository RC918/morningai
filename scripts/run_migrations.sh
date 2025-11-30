#!/usr/bin/env bash
# Unified Migration Runner for MorningAI
# ======================================
# Discovers and runs all SQL migrations in numerical order.
# Supports dry-run mode, specific migration selection, and filtering.
#
# Usage:
#   ./scripts/run_migrations.sh                    # Run all migrations
#   ./scripts/run_migrations.sh --dry-run          # Show what would be run
#   ./scripts/run_migrations.sh --from 010         # Run migrations from 010 onwards
#   ./scripts/run_migrations.sh --only 015         # Run only migration 015
#   ./scripts/run_migrations.sh --list             # List all available migrations
#
# Environment:
#   DATABASE_URL - Required. PostgreSQL connection string.
#
# Exit codes:
#   0 - All migrations applied successfully
#   1 - Migration error
#   2 - Configuration error

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

# Default options
DRY_RUN=false
FROM_MIGRATION=""
ONLY_MIGRATION=""
LIST_ONLY=false
VERBOSE=false

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
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --dry-run     Show what would be run without executing"
            echo "  --from NUM    Run migrations from NUM onwards (e.g., --from 010)"
            echo "  --only NUM    Run only migration NUM (e.g., --only 015)"
            echo "  --list        List all available migrations"
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

# Extract migration number from filename
get_migration_number() {
    basename "$1" | grep -oE '^[0-9]+' || echo "000"
}

# List all migrations
list_migrations() {
    echo ""
    echo "Available Migrations in $MIG_DIR:"
    echo "=================================="

    local count=0
    while IFS= read -r migration; do
        if [[ -n "$migration" ]]; then
            local num
            num=$(get_migration_number "$migration")
            local name
            name=$(basename "$migration")
            echo "  $num: $name"
            ((count++)) || true
        fi
    done < <(get_migrations)

    echo ""
    echo "Total: $count migrations"
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
