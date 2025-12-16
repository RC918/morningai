#!/bin/bash
# =============================================================================
# Legacy Component Detection Script (Wrapper)
# =============================================================================
#
# PURPOSE:
#   Wrapper script that calls the AST-based Node.js detection script.
#   Detects imports of deprecated/legacy components in application code.
#   This helps enforce gradual migration away from legacy components.
#
# USAGE:
#   ./scripts/detect-legacy-components.sh [options]
#
# OPTIONS:
#   --dir <path>         Directory to scan (can be repeated)
#   --allowlist <path>   Path to allowlist JSON file
#   --components <list>  Comma-separated list of legacy components
#   --strict             Exit with error code 1 if violations found
#   --json               Output results as JSON
#   --use-grep           Use grep-based fallback instead of AST
#
# ENVIRONMENT VARIABLES:
#   LEGACY_COMPONENT_SCAN_DIRS    Colon-separated list of directories to scan
#   LEGACY_COMPONENT_ALLOWLIST    Path to allowlist JSON file
#   LEGACY_COMPONENTS             Comma-separated list of legacy components
#
# CONFIGURATION:
#   Allowlist: .github/legacy-component-allowlist.json
#
# DEPENDENCIES:
#   - Node.js >= 18 (for AST-based detection)
#   - TypeScript (available in repo node_modules)
#   - Bash 4+ (for grep fallback)
#
# RELATED:
#   - Issue #2513: Legacy component detection CI
#   - CONTRIBUTING_DESIGN_SYSTEM.md: Deprecated component list
#   - scripts/detect-legacy-components.mjs: AST-based detection implementation
#
# =============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Default configuration
DEFAULT_ALLOWLIST_FILE="$REPO_ROOT/.github/legacy-component-allowlist.json"
DEFAULT_SCAN_DIRS=(
  "$REPO_ROOT/handoff/20250928/40_App/owner-console/src"
  "$REPO_ROOT/handoff/20250928/40_App/frontend-dashboard/src"
)

# Parse arguments
STRICT_MODE=false
JSON_MODE=false
USE_GREP=false
CUSTOM_DIRS=()
ALLOWLIST_FILE=""
COMPONENTS=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --dir)
      if [[ -n "${2:-}" ]]; then
        CUSTOM_DIRS+=("$2")
        shift 2
      else
        echo "Error: --dir requires a path argument"
        exit 1
      fi
      ;;
    --allowlist)
      if [[ -n "${2:-}" ]]; then
        ALLOWLIST_FILE="$2"
        shift 2
      else
        echo "Error: --allowlist requires a path argument"
        exit 1
      fi
      ;;
    --components)
      if [[ -n "${2:-}" ]]; then
        COMPONENTS="$2"
        shift 2
      else
        echo "Error: --components requires a comma-separated list"
        exit 1
      fi
      ;;
    --strict)
      STRICT_MODE=true
      shift
      ;;
    --json)
      JSON_MODE=true
      shift
      ;;
    --use-grep)
      USE_GREP=true
      shift
      ;;
    --help|-h)
      head -50 "$0" | grep -E "^#" | sed 's/^# //' | sed 's/^#//'
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

# Build Node.js script arguments
build_node_args() {
  local args=()
  
  # Add custom directories
  if [[ ${#CUSTOM_DIRS[@]} -gt 0 ]]; then
    for dir in "${CUSTOM_DIRS[@]}"; do
      args+=("--dir" "$dir")
    done
  fi
  
  # Add allowlist
  if [[ -n "$ALLOWLIST_FILE" ]]; then
    args+=("--allowlist" "$ALLOWLIST_FILE")
  fi
  
  # Add components
  if [[ -n "$COMPONENTS" ]]; then
    args+=("--components" "$COMPONENTS")
  fi
  
  # Add strict mode
  if [[ "$STRICT_MODE" == "true" ]]; then
    args+=("--strict")
  fi
  
  # Add JSON mode
  if [[ "$JSON_MODE" == "true" ]]; then
    args+=("--json")
  fi
  
  echo "${args[@]:-}"
}

# Grep-based fallback detection (for environments without Node.js)
grep_fallback() {
  echo "=============================================================================="
  echo "Legacy Component Detection (grep fallback)"
  echo "=============================================================================="
  echo ""
  echo -e "${YELLOW}Note: Using grep-based fallback. For accurate detection, use Node.js.${NC}"
  echo ""
  
  # Determine directories to scan
  local scan_dirs=()
  if [[ ${#CUSTOM_DIRS[@]} -gt 0 ]]; then
    scan_dirs=("${CUSTOM_DIRS[@]}")
  elif [[ -n "${LEGACY_COMPONENT_SCAN_DIRS:-}" ]]; then
    IFS=':' read -ra scan_dirs <<< "$LEGACY_COMPONENT_SCAN_DIRS"
  else
    scan_dirs=("${DEFAULT_SCAN_DIRS[@]}")
  fi
  
  # Determine allowlist file
  local allowlist="${ALLOWLIST_FILE:-${LEGACY_COMPONENT_ALLOWLIST:-$DEFAULT_ALLOWLIST_FILE}}"
  
  # Read legacy components
  local legacy_components
  if [[ -n "$COMPONENTS" ]]; then
    legacy_components="$COMPONENTS"
  elif [[ -n "${LEGACY_COMPONENTS:-}" ]]; then
    legacy_components="$LEGACY_COMPONENTS"
  elif [[ -f "$allowlist" ]] && command -v node &> /dev/null; then
    legacy_components=$(node -e "
      const fs = require('fs');
      const config = JSON.parse(fs.readFileSync('$allowlist', 'utf8'));
      console.log(config.legacy_components.join(','));
    " 2>/dev/null || echo "LegacyCard,LegacyStatCard")
  else
    legacy_components="LegacyCard,LegacyStatCard"
  fi
  
  # Read allowed files
  local allowed_files=""
  if [[ -f "$allowlist" ]] && command -v node &> /dev/null; then
    allowed_files=$(node -e "
      const fs = require('fs');
      const config = JSON.parse(fs.readFileSync('$allowlist', 'utf8'));
      console.log(config.allowed_files.join('\n'));
    " 2>/dev/null || echo "")
  fi
  
  # Build grep pattern
  local pattern
  pattern=$(echo "$legacy_components" | tr ',' '|')
  
  echo "Legacy components to detect:"
  echo "$legacy_components" | tr ',' '\n' | while read -r comp; do
    echo "  - $comp"
  done
  echo ""
  
  echo "Scanning directories:"
  for dir in "${scan_dirs[@]}"; do
    if [[ -d "$dir" ]]; then
      echo "  - ${dir#$REPO_ROOT/}"
    fi
  done
  echo ""
  
  # Find violations
  local violations=0
  local violations_list=""
  local files_scanned=0
  
  for dir in "${scan_dirs[@]}"; do
    if [[ ! -d "$dir" ]]; then
      continue
    fi
    
    while IFS= read -r -d '' file; do
      files_scanned=$((files_scanned + 1))
      
      # Skip if file is in allowlist
      local relative_file="${file#$REPO_ROOT/}"
      local skip=false
      while IFS= read -r allowed; do
        if [[ -n "$allowed" && "$relative_file" == *"$allowed"* ]]; then
          skip=true
          break
        fi
      done <<< "$allowed_files"
      
      if [[ "$skip" == "true" ]]; then
        continue
      fi
      
      # Check for legacy component imports (excluding comments)
      local matches
      matches=$(grep -nE "^[^/]*import.*($pattern)|^[^/]*from.*($pattern)" "$file" 2>/dev/null | grep -v "^\s*//" || true)
      
      if [[ -n "$matches" ]]; then
        violations=$((violations + 1))
        violations_list="${violations_list}\n${relative_file}:\n${matches}\n"
      fi
    done < <(find "$dir" -type f \( -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" \) -print0 2>/dev/null)
  done
  
  # Output results
  echo "=============================================================================="
  echo "Results"
  echo "=============================================================================="
  echo ""
  echo "Files scanned: $files_scanned"
  echo "Violations found: $violations"
  echo ""
  
  if [[ $violations -gt 0 ]]; then
    echo -e "${YELLOW}Violations:${NC}"
    echo -e "$violations_list"
    echo ""
    echo "=============================================================================="
    echo "Migration Guide"
    echo "=============================================================================="
    echo ""
    echo "Replace legacy components with shared-ui alternatives:"
    echo ""
    echo "  LegacyCard -> Card, StatCard, StatusCard, SettingsCard, or SectionCard"
    echo "  LegacyStatCard -> StatCard"
    echo ""
    echo "See CONTRIBUTING_DESIGN_SYSTEM.md for the LegacyCard replacement decision flow."
    echo ""
    echo "If you need to temporarily allow a file, add it to:"
    echo "  .github/legacy-component-allowlist.json"
    echo ""
    
    if [[ "$STRICT_MODE" == "true" ]]; then
      echo -e "${RED}STRICT MODE: Failing due to legacy component violations.${NC}"
      exit 1
    else
      echo -e "${YELLOW}WARNING MODE: Violations detected but not blocking.${NC}"
      exit 0
    fi
  else
    echo -e "${GREEN}No legacy component imports detected!${NC}"
    exit 0
  fi
}

# Main function
main() {
  # Check if we should use grep fallback
  if [[ "$USE_GREP" == "true" ]]; then
    grep_fallback
    return
  fi
  
  # Check if Node.js is available
  if ! command -v node &> /dev/null; then
    echo -e "${YELLOW}Warning: Node.js not found. Using grep-based fallback.${NC}"
    grep_fallback
    return
  fi
  
  # Check if the Node.js script exists
  local node_script="$SCRIPT_DIR/detect-legacy-components.mjs"
  if [[ ! -f "$node_script" ]]; then
    echo -e "${YELLOW}Warning: Node.js script not found. Using grep-based fallback.${NC}"
    grep_fallback
    return
  fi
  
  # Run the Node.js script
  local args
  args=$(build_node_args)
  
  # shellcheck disable=SC2086
  node "$node_script" $args
}

main "$@"
