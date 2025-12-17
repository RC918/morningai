#!/bin/bash
#
# sync-react-versions.sh - Automated React version synchronization tool
#
# This script ensures all workspace package.json files have React versions
# aligned with the root package.json pnpm overrides (single source of truth).
#
# Requirements:
#   - Node.js >= 18.0.0 (for JSON parsing)
#   - pnpm (for lockfile updates with --install flag)
#
# Usage:
#   ./scripts/sync-react-versions.sh              # Sync from pnpm overrides
#   ./scripts/sync-react-versions.sh --version 19.2.0  # Specify version directly
#   ./scripts/sync-react-versions.sh --dry-run    # Preview changes without applying
#   ./scripts/sync-react-versions.sh --check      # Check alignment only (CI mode)
#   ./scripts/sync-react-versions.sh --install    # Auto-run pnpm install after sync
#   ./scripts/sync-react-versions.sh --workspace path/to/workspace  # Override workspace
#
# Exit Codes:
#   0 - Success (all versions aligned or updated successfully)
#   1 - Version misalignment detected (in --check mode)
#   2 - Invalid arguments or missing required tools
#   3 - File not found or permission error
#   4 - JSON parse error
#   5 - pnpm install failed
#
# Related:
#   - PR #2578: React version alignment (single source of truth)
#   - Issue #2576: React version mismatch tracking
#   - Issue #2579: CI lockfile sync check
#

set -eo pipefail

# Exit codes
EXIT_SUCCESS=0
EXIT_MISALIGNED=1
EXIT_INVALID_ARGS=2
EXIT_FILE_ERROR=3
EXIT_JSON_ERROR=4
EXIT_PNPM_ERROR=5

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
AUTO_INSTALL=false
SPECIFIED_VERSION=""
CUSTOM_WORKSPACES=()

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
    echo "Workspaces are automatically discovered from pnpm-workspace.yaml."
    echo ""
    echo "Requirements:"
    echo "  - Node.js >= 18.0.0 (for JSON parsing)"
    echo "  - pnpm (optional, for --install flag)"
    echo ""
    echo "Options:"
    echo "  --version VERSION    Specify React version directly (e.g., 19.2.0)"
    echo "  --dry-run            Preview changes without applying them"
    echo "  --check              Check alignment only, exit 1 if misaligned (CI mode)"
    echo "  --install            Auto-run 'pnpm install' after syncing versions"
    echo "  --workspace PATH     Override workspace path (can be used multiple times)"
    echo "  --verbose            Show detailed output"
    echo "  -h, --help           Show this help message"
    echo ""
    echo "Exit Codes:"
    echo "  0 - Success"
    echo "  1 - Version misalignment (--check mode)"
    echo "  2 - Invalid arguments or missing tools"
    echo "  3 - File not found"
    echo "  4 - JSON parse error"
    echo "  5 - pnpm install failed"
    echo ""
    echo "Examples:"
    echo "  $0                      # Sync from pnpm overrides"
    echo "  $0 --version 19.2.0     # Update all to React 19.2.0"
    echo "  $0 --dry-run            # Preview what would change"
    echo "  $0 --check              # CI check for version alignment"
    echo "  $0 --install            # Sync and update lockfile"
    echo "  $0 --workspace packages/my-app  # Sync specific workspace"
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
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

log_verbose() {
    if [[ "$VERBOSE" == true ]]; then
        echo -e "  ${BLUE}→${NC} $1"
    fi
}

check_requirements() {
    local missing=false
    
    if ! command -v node >/dev/null 2>&1; then
        log_error "Node.js is required but not found in PATH"
        log_error "Please install Node.js >= 18.0.0"
        missing=true
    else
        local node_version
        node_version=$(node -v | sed 's/v//' | cut -d. -f1)
        if [[ "$node_version" -lt 18 ]]; then
            log_error "Node.js >= 18.0.0 required, found: $(node -v)"
            missing=true
        fi
    fi
    
    if [[ "$AUTO_INSTALL" == true ]] && ! command -v pnpm >/dev/null 2>&1; then
        log_error "pnpm is required for --install flag but not found in PATH"
        missing=true
    fi
    
    if [[ "$missing" == true ]]; then
        exit $EXIT_INVALID_ARGS
    fi
}

discover_workspaces() {
    local workspace_file="pnpm-workspace.yaml"
    
    if [[ ! -f "$workspace_file" ]]; then
        log_error "pnpm-workspace.yaml not found in current directory"
        log_error "Please run this script from the repository root"
        exit $EXIT_FILE_ERROR
    fi
    
    local workspaces=()
    local library_workspaces=()
    
    while IFS= read -r line; do
        line=$(echo "$line" | sed "s/^[[:space:]]*-[[:space:]]*['\"]*//" | sed "s/['\"].*//")
        
        if [[ -z "$line" || "$line" == "packages:" ]]; then
            continue
        fi
        
        if [[ "$line" == *"/*" ]]; then
            local base_path="${line%/*}"
            if [[ -d "$base_path" ]]; then
                for dir in "$base_path"/*/; do
                    if [[ -f "${dir}package.json" ]]; then
                        local ws_path="${dir%/}"
                        if is_library_workspace "$ws_path"; then
                            library_workspaces+=("$ws_path")
                        else
                            workspaces+=("$ws_path")
                        fi
                    fi
                done
            fi
        else
            if [[ -d "$line" && -f "$line/package.json" ]]; then
                if is_library_workspace "$line"; then
                    library_workspaces+=("$line")
                else
                    workspaces+=("$line")
                fi
            fi
        fi
    done < "$workspace_file"
    
    WORKSPACES=("${workspaces[@]}")
    LIBRARY_WORKSPACES=("${library_workspaces[@]}")
    
    log_verbose "Discovered ${#WORKSPACES[@]} application workspace(s)"
    log_verbose "Discovered ${#LIBRARY_WORKSPACES[@]} library workspace(s)"
}

is_library_workspace() {
    local workspace="$1"
    local pkg_json="$workspace/package.json"
    
    if [[ ! -f "$pkg_json" ]]; then
        return 1
    fi
    
    local has_peer
    has_peer=$(node -p "
        try {
            const pkg = require('./$pkg_json');
            const peer = pkg.peerDependencies || {};
            !!(peer['react'] || peer['react-dom']);
        } catch(e) { false; }
    " 2>/dev/null)
    
    [[ "$has_peer" == "true" ]]
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
    
    if [[ ! -f "package.json" ]]; then
        log_error "package.json not found in current directory"
        exit $EXIT_FILE_ERROR
    fi
    
    version=$(node -p "
        try {
            const pkg = require('./package.json');
            const override = pkg.pnpm?.overrides?.['$package'] || '';
            override.replace(/^\\^/, '');
        } catch(e) {
            console.error('JSON parse error:', e.message);
            process.exit(1);
        }
    " 2>/dev/null)
    
    if [[ $? -ne 0 ]]; then
        log_error "Failed to parse package.json"
        exit $EXIT_JSON_ERROR
    fi
    
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
# Usage: update_workspace_version <workspace> <package> <new_version> [section]
# Parameters:
#   workspace   - Path to the workspace directory
#   package     - Package name to update (e.g., "react", "@types/react")
#   new_version - New version to set (without ^ prefix)
#   section     - Optional: specific section to update (dependencies|devDependencies|peerDependencies)
#                 If not provided, updates all sections where the package exists
update_workspace_version() {
    local workspace="$1"
    local package="$2"
    local new_version="$3"
    local section="${4:-}"  # Optional: specific section to update
    local pkg_json="$workspace/package.json"
    
    if [[ ! -f "$pkg_json" ]]; then
        log_error "Package.json not found: $pkg_json"
        return 1
    fi
    
    # Validate section parameter if provided
    if [[ -n "$section" ]]; then
        case "$section" in
            dependencies|devDependencies|peerDependencies)
                ;;
            *)
                log_error "Invalid section: $section (must be dependencies, devDependencies, or peerDependencies)"
                return 1
                ;;
        esac
    fi
    
    # Use node to update the version while preserving formatting
    node -e "
        const fs = require('fs');
        const path = './$pkg_json';
        const content = fs.readFileSync(path, 'utf8');
        const pkg = JSON.parse(content);
        
        const targetSection = '$section';
        const sections = targetSection 
            ? [targetSection] 
            : ['dependencies', 'devDependencies', 'peerDependencies'];
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
            if [[ -z "$2" || "$2" == --* ]]; then
                log_error "--version requires a VERSION argument"
                exit $EXIT_INVALID_ARGS
            fi
            SPECIFIED_VERSION="$2"
            shift 2
            ;;
        --workspace)
            if [[ -z "$2" || "$2" == --* ]]; then
                log_error "--workspace requires a PATH argument"
                exit $EXIT_INVALID_ARGS
            fi
            CUSTOM_WORKSPACES+=("$2")
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
        --install)
            AUTO_INSTALL=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            usage
            exit $EXIT_SUCCESS
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            exit $EXIT_INVALID_ARGS
            ;;
    esac
done

# Main execution
check_requirements

echo "========================================="
echo "React Version Sync Tool"
echo "========================================="
echo ""

# Discover or use custom workspaces
if [[ ${#CUSTOM_WORKSPACES[@]} -gt 0 ]]; then
    log_info "Using custom workspace(s):"
    WORKSPACES=()
    LIBRARY_WORKSPACES=()
    for ws in "${CUSTOM_WORKSPACES[@]}"; do
        if [[ ! -d "$ws" ]]; then
            log_error "Workspace not found: $ws"
            exit $EXIT_FILE_ERROR
        fi
        if [[ ! -f "$ws/package.json" ]]; then
            log_error "No package.json in workspace: $ws"
            exit $EXIT_FILE_ERROR
        fi
        if is_library_workspace "$ws"; then
            LIBRARY_WORKSPACES+=("$ws")
            log_info "  $ws (library)"
        else
            WORKSPACES+=("$ws")
            log_info "  $ws (application)"
        fi
    done
else
    discover_workspaces
    log_info "Discovered workspaces from pnpm-workspace.yaml:"
    for ws in "${WORKSPACES[@]}"; do
        log_info "  $ws (application)"
    done
    for ws in "${LIBRARY_WORKSPACES[@]}"; do
        log_info "  $ws (library)"
    done
fi

echo ""

# Determine target versions
if [[ -n "$SPECIFIED_VERSION" ]]; then
    if ! validate_version "$SPECIFIED_VERSION"; then
        exit $EXIT_INVALID_ARGS
    fi
    REACT_VERSION="$SPECIFIED_VERSION"
    TYPES_VERSION="$SPECIFIED_VERSION"
    log_info "Using specified version: $REACT_VERSION"
else
    REACT_VERSION=$(get_override_version "react")
    if [[ -z "$REACT_VERSION" ]]; then
        log_error "Could not read React version from pnpm overrides"
        exit $EXIT_JSON_ERROR
    fi
    
    TYPES_VERSION=$(get_override_version "@types/react")
    if [[ -z "$TYPES_VERSION" ]]; then
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
                log_warning "[DRY-RUN] Would update $package: $current_version -> $TYPES_VERSION (devDependencies only)"
                CHANGES=$((CHANGES + 1))
            else
                # Use parameterized update to only update devDependencies for libraries
                if update_workspace_version "$workspace" "$package" "$TYPES_VERSION" "devDependencies"; then
                    log_success "Updated $package: $current_version -> $TYPES_VERSION (devDependencies)"
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
        echo "Or run './scripts/sync-react-versions.sh --install' to fix and update lockfile"
        exit $EXIT_MISALIGNED
    else
        log_success "All React versions aligned with pnpm overrides"
        exit $EXIT_SUCCESS
    fi
elif [[ "$DRY_RUN" == true ]]; then
    if [[ $CHANGES -gt 0 ]]; then
        log_warning "[DRY-RUN] $CHANGES package(s) would be updated"
        echo ""
        echo "Run without --dry-run to apply changes"
        echo "Run with --install to also update lockfile"
    else
        log_success "All React versions already aligned"
    fi
    exit $EXIT_SUCCESS
else
    if [[ $CHANGES -gt 0 ]]; then
        log_success "$CHANGES package(s) updated"
        echo ""
        
        if [[ "$AUTO_INSTALL" == true ]]; then
            echo "Running 'pnpm install' to update lockfile..."
            if pnpm install --frozen-lockfile=false 2>&1; then
                log_success "Lockfile updated successfully"
            else
                log_error "pnpm install failed"
                echo ""
                echo "Please run 'pnpm install' manually to update lockfile"
                exit $EXIT_PNPM_ERROR
            fi
            echo ""
            echo "Next steps:"
            echo "  1. Verify changes with 'git diff'"
            echo "  2. Commit changes"
        else
            echo "Next steps:"
            echo "  1. Run 'pnpm install' to update lockfile"
            echo "  2. Verify changes with 'git diff'"
            echo "  3. Commit changes"
        fi
    else
        log_success "All React versions already aligned"
    fi
    exit $EXIT_SUCCESS
fi
