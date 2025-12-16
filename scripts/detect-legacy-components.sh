#!/bin/bash
# =============================================================================
# Legacy Component Detection Script
# =============================================================================
#
# PURPOSE:
#   Detects imports of deprecated/legacy components in application code.
#   This helps enforce gradual migration away from legacy components.
#
# USAGE:
#   ./scripts/detect-legacy-components.sh [--strict]
#
# OPTIONS:
#   --strict    Exit with error code 1 if violations found (default: warning only)
#
# CONFIGURATION:
#   Allowlist: .github/legacy-component-allowlist.json
#
# RELATED:
#   - Issue #2513: Legacy component detection CI
#   - CONTRIBUTING_DESIGN_SYSTEM.md: Deprecated component list
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

# Configuration
ALLOWLIST_FILE="$REPO_ROOT/.github/legacy-component-allowlist.json"
STRICT_MODE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --strict)
      STRICT_MODE=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Directories to scan
SCAN_DIRS=(
  "$REPO_ROOT/handoff/20250928/40_App/owner-console/src"
  "$REPO_ROOT/handoff/20250928/40_App/frontend-dashboard/src"
)

# Read legacy components from allowlist
read_legacy_components() {
  if [[ -f "$ALLOWLIST_FILE" ]]; then
    # Use node to parse JSON (more reliable than jq which may not be installed)
    node -e "
      const fs = require('fs');
      const config = JSON.parse(fs.readFileSync('$ALLOWLIST_FILE', 'utf8'));
      console.log(config.legacy_components.join('\n'));
    " 2>/dev/null || echo "LegacyCard"
  else
    # Default legacy components if no allowlist
    echo "LegacyCard"
    echo "LegacyStatCard"
  fi
}

# Read allowed files from allowlist
read_allowed_files() {
  if [[ -f "$ALLOWLIST_FILE" ]]; then
    node -e "
      const fs = require('fs');
      const config = JSON.parse(fs.readFileSync('$ALLOWLIST_FILE', 'utf8'));
      console.log(config.allowed_files.join('\n'));
    " 2>/dev/null || echo ""
  fi
}

# Check if file is in allowlist
is_file_allowed() {
  local file="$1"
  local relative_file="${file#$REPO_ROOT/}"
  
  while IFS= read -r allowed; do
    if [[ -n "$allowed" && "$relative_file" == *"$allowed"* ]]; then
      return 0
    fi
  done < <(read_allowed_files)
  
  return 1
}

# Main detection logic
main() {
  echo "=============================================================================="
  echo "Legacy Component Detection"
  echo "=============================================================================="
  echo ""
  
  # Read configuration
  local legacy_components
  legacy_components=$(read_legacy_components)
  
  if [[ -z "$legacy_components" ]]; then
    echo -e "${GREEN}No legacy components configured. Skipping detection.${NC}"
    exit 0
  fi
  
  echo "Legacy components to detect:"
  echo "$legacy_components" | while read -r comp; do
    echo "  - $comp"
  done
  echo ""
  
  # Build grep pattern
  local pattern=""
  while IFS= read -r comp; do
    if [[ -n "$comp" ]]; then
      if [[ -n "$pattern" ]]; then
        pattern="$pattern|$comp"
      else
        pattern="$comp"
      fi
    fi
  done <<< "$legacy_components"
  
  if [[ -z "$pattern" ]]; then
    echo -e "${GREEN}No pattern to search. Exiting.${NC}"
    exit 0
  fi
  
  echo "Scanning directories:"
  for dir in "${SCAN_DIRS[@]}"; do
    if [[ -d "$dir" ]]; then
      echo "  - ${dir#$REPO_ROOT/}"
    fi
  done
  echo ""
  
  # Find violations
  local violations=0
  local violations_list=""
  local files_scanned=0
  
  for dir in "${SCAN_DIRS[@]}"; do
    if [[ ! -d "$dir" ]]; then
      continue
    fi
    
    while IFS= read -r -d '' file; do
      files_scanned=$((files_scanned + 1))
      
      # Skip if file is in allowlist
      if is_file_allowed "$file"; then
        continue
      fi
      
      # Check for legacy component imports
      local matches
      matches=$(grep -nE "import.*($pattern)|from.*($pattern)" "$file" 2>/dev/null || true)
      
      if [[ -n "$matches" ]]; then
        local relative_file="${file#$REPO_ROOT/}"
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
    echo "  LegacyCard → Card, StatCard, StatusCard, SettingsCard, or SectionCard"
    echo "  LegacyStatCard → StatCard"
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

main "$@"
