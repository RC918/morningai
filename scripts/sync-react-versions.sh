#!/bin/bash
#
# sync-react-versions.sh - Automated React version synchronization tool
#
# This script ensures all workspace package.json files have React versions
# aligned with the root package.json pnpm overrides (single source of truth).
#
# Usage:
#   ./scripts/sync-react-versions.sh              # Sync from pnpm overrides
#   ./scripts/sync-react-versions.sh --version 19.2.0  # Specify version directly
#   ./scripts/sync-react-versions.sh --dry-run    # Preview changes without applying
#   ./scripts/sync-react-versions.sh --check      # Check alignment only (CI mode)
#
# Related:
#   - PR #2578: React version alignment (single source of truth)
#   - Issue #2576: React version mismatch tracking
#   - Issue #2579: CI lockfile sync check
#

set -eo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script options
DRY_RUN=false
CHECK_ONLY=false
VERBOSE=false
SPECIFIED_VERSION=""

# Workspace paths (relative to repo root)
# Note: shared-ui is excluded because it's a library with peerDependencies
# that intentionally supports multiple React versions (^18.0.0 || ^19.0.0)
WORKSPACES=(
    "handoff/20250928/40_App/frontend-dashboard"
    "handoff/20250928/40_App/owner-console"
)

# Library workspaces (only sync devDependencies, not peerDependencies)
LIBRARY_WORKSPACES=(
    "packages/shared-ui"
)

# Packages to sync
REACT_PACKAGES=(
    "react"
    "react-dom"
)

TYPES_PACKAGES=(
    "@types/react"
    "@types/react-dom"
)

usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Synchronize React versions across all workspaces in the monorepo."
    echo ""
    echo "Options:"
    echo "  --version VERSION  Specify React version directly (e.g., 19.2.0)"
    echo "  --dry-run          Preview changes without applying them"
    echo "  --check            Check alignment only, exit 1 if misaligned (CI mode)"
    echo "  --verbose          Show detailed output"
    echo "  -h, --help         Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                      # Sync from pnpm overrides"
    echo "  $0 --version 19.2.0     # Update all to React 19.2.0"
    echo "  $0 --dry-run            # Preview what would change"
    echo "  $0 --check              # CI check for version alignment"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_verbose() {
    if [[ "$VERBOSE" == true ]]; then
        echo -e "  ${BLUE}→${NC} $1"
    fi
}

# Validate semver format (basic validation)
validate_version() {
    local version="$1"
    if [[ ! "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        log_error "Invalid version format: $version (expected: X.Y.Z)"
        return 1
    fi
    return 0
}

# Get version from root package.json pnpm overrides
get_override_version() {
    local package="$1"
    local version
    
    if ! command -v node >/dev/null 2>&1; then
        log_error "Node.js is required but not found in PATH"
        exit 1
    fi
    
    version=$(node -p "
        const pkg = require('./package.json');
        const override = pkg.pnpm?.overrides?.['$package'] || '';
        override.replace(/^\\^/, '');
    " 2>/dev/null)
    
    if [[ -z "$version" || "$version" == "undefined" ]]; then
        return 1
    fi
    
    echo "$version"
}

# Get current version from a workspace package.json
get_workspace_version() {
    local workspace="$1"
    local package="$2"
    local pkg_json="$workspace/package.json"
    
    if [[ ! -f "$pkg_json" ]]; then
        return 1
    fi
    
    local version
    version=$(node -p "
        const pkg = require('./$pkg_json');
        const deps = pkg.dependencies || {};
        const devDeps = pkg.devDependencies || {};
        const peerDeps = pkg.peerDependencies || {};
        const ver = deps['$package'] || devDeps['$package'] || peerDeps['$package'] || '';
        ver.replace(/^\\^/, '');
    " 2>/dev/null)
    
    if [[ -z "$version" || "$version" == "undefined" ]]; then
        return 1
    fi
    
    echo "$version"
}

# Update version in a workspace package.json using node
update_workspace_version() {
    local workspace="$1"
    local package="$2"
    local new_version="$3"
    local pkg_json="$workspace/package.json"
    
    if [[ ! -f "$pkg_json" ]]; then
        log_error "Package.json not found: $pkg_json"
        return 1
    fi
    
    # Use node to update the version while preserving formatting
    node -e "
        const fs = require('fs');
        const path = './$pkg_json';
        const content = fs.readFileSync(path, 'utf8');
        const pkg = JSON.parse(content);
        
        const sections = ['dependencies', 'devDependencies', 'peerDependencies'];
        let updated = false;
        
        for (const section of sections) {
            if (pkg[section] && pkg[section]['$package']) {
                pkg[section]['$package'] = '^$new_version';
                updated = true;
            }
        }
        
        if (updated) {
            fs.writeFileSync(path, JSON.stringify(pkg, null, 2) + '\n');
        }
    " 2>/dev/null
    
    return $?
}

# Check if package exists in workspace
package_exists_in_workspace() {
    local workspace="$1"
    local package="$2"
    local pkg_json="$workspace/package.json"
    
    if [[ ! -f "$pkg_json" ]]; then
        return 1
    fi
    
    node -p "
        const pkg = require('./$pkg_json');
        const deps = pkg.dependencies || {};
        const devDeps = pkg.devDependencies || {};
        const peerDeps = pkg.peerDependencies || {};
        !!(deps['$package'] || devDeps['$package'] || peerDeps['$package']);
    " 2>/dev/null | grep -q "true"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --version)
            SPECIFIED_VERSION="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --check)
            CHECK_ONLY=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Main execution
echo "========================================="
echo "React Version Sync Tool"
echo "========================================="
echo ""

# Determine target versions
if [[ -n "$SPECIFIED_VERSION" ]]; then
    if ! validate_version "$SPECIFIED_VERSION"; then
        exit 1
    fi
    REACT_VERSION="$SPECIFIED_VERSION"
    TYPES_VERSION="$SPECIFIED_VERSION"
    log_info "Using specified version: $REACT_VERSION"
else
    REACT_VERSION=$(get_override_version "react")
    if [[ -z "$REACT_VERSION" ]]; then
        log_error "Could not read React version from pnpm overrides"
        exit 1
    fi
    
    TYPES_VERSION=$(get_override_version "@types/react")
    if [[ -z "$TYPES_VERSION" ]]; then
        # Fall back to React version for types
        TYPES_VERSION="$REACT_VERSION"
    fi
    
    log_info "Target versions from pnpm overrides:"
    log_info "  react/react-dom: $REACT_VERSION"
    log_info "  @types/react/@types/react-dom: $TYPES_VERSION"
fi

echo ""

# Track changes
CHANGES=0
MISALIGNED=0

# Process each workspace
for workspace in "${WORKSPACES[@]}"; do
    if [[ ! -d "$workspace" ]]; then
        log_warning "Workspace not found: $workspace"
        continue
    fi
    
    workspace_name=$(basename "$workspace")
    echo "Checking $workspace_name..."
    
    # Check React packages
    for package in "${REACT_PACKAGES[@]}"; do
        if ! package_exists_in_workspace "$workspace" "$package"; then
            log_verbose "$package not in $workspace_name (skipping)"
            continue
        fi
        
        current_version=$(get_workspace_version "$workspace" "$package")
        
        if [[ "$current_version" != "$REACT_VERSION" ]]; then
            MISALIGNED=$((MISALIGNED + 1))
            
            if [[ "$CHECK_ONLY" == true ]]; then
                log_error "$workspace_name: $package $current_version != $REACT_VERSION"
            elif [[ "$DRY_RUN" == true ]]; then
                log_warning "[DRY-RUN] Would update $package: $current_version -> $REACT_VERSION"
                CHANGES=$((CHANGES + 1))
            else
                if update_workspace_version "$workspace" "$package" "$REACT_VERSION"; then
                    log_success "Updated $package: $current_version -> $REACT_VERSION"
                    CHANGES=$((CHANGES + 1))
                else
                    log_error "Failed to update $package in $workspace_name"
                fi
            fi
        else
            log_verbose "$package: $current_version (aligned)"
        fi
    done
    
    # Check @types packages
    for package in "${TYPES_PACKAGES[@]}"; do
        if ! package_exists_in_workspace "$workspace" "$package"; then
            log_verbose "$package not in $workspace_name (skipping)"
            continue
        fi
        
        current_version=$(get_workspace_version "$workspace" "$package")
        
        if [[ "$current_version" != "$TYPES_VERSION" ]]; then
            MISALIGNED=$((MISALIGNED + 1))
            
            if [[ "$CHECK_ONLY" == true ]]; then
                log_error "$workspace_name: $package $current_version != $TYPES_VERSION"
            elif [[ "$DRY_RUN" == true ]]; then
                log_warning "[DRY-RUN] Would update $package: $current_version -> $TYPES_VERSION"
                CHANGES=$((CHANGES + 1))
            else
                if update_workspace_version "$workspace" "$package" "$TYPES_VERSION"; then
                    log_success "Updated $package: $current_version -> $TYPES_VERSION"
                    CHANGES=$((CHANGES + 1))
                else
                    log_error "Failed to update $package in $workspace_name"
                fi
            fi
        else
            log_verbose "$package: $current_version (aligned)"
        fi
    done
    
    echo ""
done

# Process library workspaces (only devDependencies, skip peerDependencies)
for workspace in "${LIBRARY_WORKSPACES[@]}"; do
    if [[ ! -d "$workspace" ]]; then
        log_warning "Library workspace not found: $workspace"
        continue
    fi
    
    workspace_name=$(basename "$workspace")
    echo "Checking $workspace_name (library - devDependencies only)..."
    log_verbose "Skipping peerDependencies (libraries need version ranges for compatibility)"
    
    # Only check @types packages in devDependencies for libraries
    for package in "${TYPES_PACKAGES[@]}"; do
        if ! package_exists_in_workspace "$workspace" "$package"; then
            log_verbose "$package not in $workspace_name (skipping)"
            continue
        fi
        
        current_version=$(get_workspace_version "$workspace" "$package")
        
        # Skip if it's a peerDependency range (contains ||)
        if [[ "$current_version" == *"||"* ]]; then
            log_verbose "$package: $current_version (peerDependency range, skipping)"
            continue
        fi
        
        if [[ "$current_version" != "$TYPES_VERSION" ]]; then
            MISALIGNED=$((MISALIGNED + 1))
            
            if [[ "$CHECK_ONLY" == true ]]; then
                log_error "$workspace_name: $package $current_version != $TYPES_VERSION"
            elif [[ "$DRY_RUN" == true ]]; then
                log_warning "[DRY-RUN] Would update $package: $current_version -> $TYPES_VERSION"
                CHANGES=$((CHANGES + 1))
            else
                if update_workspace_version "$workspace" "$package" "$TYPES_VERSION"; then
                    log_success "Updated $package: $current_version -> $TYPES_VERSION"
                    CHANGES=$((CHANGES + 1))
                else
                    log_error "Failed to update $package in $workspace_name"
                fi
            fi
        else
            log_verbose "$package: $current_version (aligned)"
        fi
    done
    
    echo ""
done

# Summary
echo "========================================="
echo "Summary"
echo "========================================="

if [[ "$CHECK_ONLY" == true ]]; then
    if [[ $MISALIGNED -gt 0 ]]; then
        log_error "$MISALIGNED package(s) misaligned with pnpm overrides"
        echo ""
        echo "Run './scripts/sync-react-versions.sh' to fix alignment"
        exit 1
    else
        log_success "All React versions aligned with pnpm overrides"
        exit 0
    fi
elif [[ "$DRY_RUN" == true ]]; then
    if [[ $CHANGES -gt 0 ]]; then
        log_warning "[DRY-RUN] $CHANGES package(s) would be updated"
        echo ""
        echo "Run without --dry-run to apply changes"
    else
        log_success "All React versions already aligned"
    fi
    exit 0
else
    if [[ $CHANGES -gt 0 ]]; then
        log_success "$CHANGES package(s) updated"
        echo ""
        echo "Next steps:"
        echo "  1. Run 'pnpm install' to update lockfile"
        echo "  2. Verify changes with 'git diff'"
        echo "  3. Commit changes"
    else
        log_success "All React versions already aligned"
    fi
    exit 0
fi
