#!/bin/bash
# =============================================================================
# Missing Storybook Stories Detection Script
# =============================================================================
#
# PURPOSE:
#   Detects React components in shared-ui that are missing corresponding
#   Storybook stories (.stories.tsx files). This helps ensure all components
#   are properly documented and visually testable.
#
# USAGE:
#   ./scripts/detect-missing-stories.sh [options]
#
# OPTIONS:
#   --dir <path>         Directory to scan (default: packages/shared-ui/src/components)
#   --allowlist <path>   Path to allowlist JSON file
#   --strict             Exit with error code 1 if missing stories found
#   --json               Output results as JSON
#
# ENVIRONMENT VARIABLES:
#   STORYBOOK_SCAN_DIR       Directory to scan
#   STORYBOOK_ALLOWLIST      Path to allowlist JSON file
#
# CONFIGURATION:
#   Allowlist: .github/storybook-coverage-allowlist.json
#
# DEPENDENCIES:
#   - Bash 4+
#   - Node.js (for JSON parsing, optional)
#
# RELATED:
#   - Issue #2512: Storybook scanning CI
#   - Issue #2303: Design system governance rules
#
# =============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Default configuration
DEFAULT_SCAN_DIR="$REPO_ROOT/packages/shared-ui/src/components"
DEFAULT_ALLOWLIST_FILE="$REPO_ROOT/.github/storybook-coverage-allowlist.json"

# Parse arguments
STRICT_MODE=false
JSON_MODE=false
SCAN_DIR=""
ALLOWLIST_FILE=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --dir)
      if [[ -n "${2:-}" ]]; then
        SCAN_DIR="$2"
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
    --strict)
      STRICT_MODE=true
      shift
      ;;
    --json)
      JSON_MODE=true
      shift
      ;;
    --help|-h)
      sed '/^set -euo pipefail/q' "$0" | grep '^#' | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

# Determine scan directory
SCAN_DIR="${SCAN_DIR:-${STORYBOOK_SCAN_DIR:-$DEFAULT_SCAN_DIR}}"

# Determine allowlist file
ALLOWLIST_FILE="${ALLOWLIST_FILE:-${STORYBOOK_ALLOWLIST:-$DEFAULT_ALLOWLIST_FILE}}"

# Read allowlist
read_allowlist() {
  local allowlist_file="$1"
  
  if [[ ! -f "$allowlist_file" ]]; then
    echo ""
    return
  fi
  
  if command -v node &> /dev/null; then
    node -e "
      const fs = require('fs');
      try {
        const config = JSON.parse(fs.readFileSync('$allowlist_file', 'utf8'));
        console.log((config.allowed_files || []).join('\n'));
      } catch (e) {
        console.error('Warning: Could not parse allowlist:', e.message);
      }
    " 2>/dev/null || echo ""
  else
    # Fallback: simple grep-based extraction
    grep -oE '"[^"]+\.tsx"' "$allowlist_file" 2>/dev/null | tr -d '"' || echo ""
  fi
}

# Check if a file should be excluded
should_exclude() {
  local file="$1"
  local basename
  basename=$(basename "$file")
  
  # Exclude test files
  if [[ "$basename" == *.test.tsx ]]; then
    return 0
  fi
  
  # Exclude story files
  if [[ "$basename" == *.stories.tsx ]]; then
    return 0
  fi
  
  # Exclude index files
  if [[ "$basename" == "index.tsx" ]]; then
    return 0
  fi
  
  # Exclude type definition files
  if [[ "$basename" == *.types.tsx ]] || [[ "$basename" == types.tsx ]]; then
    return 0
  fi
  
  # Exclude hook files (usually don't need stories)
  if [[ "$basename" == use*.tsx ]]; then
    return 0
  fi
  
  # Exclude context files
  if [[ "$basename" == *-context.tsx ]] || [[ "$basename" == *Context.tsx ]]; then
    return 0
  fi
  
  # Exclude provider files
  if [[ "$basename" == *-provider.tsx ]] || [[ "$basename" == *Provider.tsx ]]; then
    return 0
  fi
  
  return 1
}

# Check if file is in allowlist
is_in_allowlist() {
  local file="$1"
  local allowlist="$2"
  local relative_file
  
  relative_file="${file#$REPO_ROOT/}"
  
  while IFS= read -r allowed; do
    if [[ -n "$allowed" ]]; then
      # Check if the file path contains the allowed pattern
      if [[ "$relative_file" == *"$allowed"* ]] || [[ "$file" == *"$allowed"* ]]; then
        return 0
      fi
    fi
  done <<< "$allowlist"
  
  return 1
}

# Get corresponding story file path
get_story_path() {
  local component_file="$1"
  local dir
  local basename
  local name_without_ext
  
  dir=$(dirname "$component_file")
  basename=$(basename "$component_file")
  name_without_ext="${basename%.tsx}"
  
  echo "$dir/$name_without_ext.stories.tsx"
}

# Main detection function
detect_missing_stories() {
  local scan_dir="$1"
  local allowlist="$2"
  
  local components_scanned=0
  local missing_count=0
  local missing_files=()
  local covered_count=0
  
  # Note: Directory existence is checked in main() before calling this function
  
  # Find all .tsx files
  while IFS= read -r -d '' file; do
    # Skip excluded files
    if should_exclude "$file"; then
      continue
    fi
    
    components_scanned=$((components_scanned + 1))
    
    # Check if in allowlist
    if is_in_allowlist "$file" "$allowlist"; then
      continue
    fi
    
    # Check if story file exists
    local story_path
    story_path=$(get_story_path "$file")
    
    if [[ -f "$story_path" ]]; then
      covered_count=$((covered_count + 1))
    else
      missing_count=$((missing_count + 1))
      missing_files+=("$file")
    fi
  done < <(find "$scan_dir" -type f -name "*.tsx" -print0 2>/dev/null)
  
  # Calculate coverage
  local coverage=0
  if [[ $components_scanned -gt 0 ]]; then
    coverage=$((covered_count * 100 / components_scanned))
  fi
  
  # Output results
  if [[ "$JSON_MODE" == "true" ]]; then
    output_json "$components_scanned" "$covered_count" "$missing_count" "$coverage" "${missing_files[@]}"
  else
    output_text "$components_scanned" "$covered_count" "$missing_count" "$coverage" "${missing_files[@]}"
  fi
  
  # Return exit code based on mode
  if [[ "$STRICT_MODE" == "true" && $missing_count -gt 0 ]]; then
    return 1
  fi
  
  return 0
}

# Output results as JSON
output_json() {
  local components_scanned="$1"
  local covered_count="$2"
  local missing_count="$3"
  local coverage="$4"
  shift 4
  local missing_files=("$@")
  
  local missing_json
  if command -v node &> /dev/null; then
    local relative_missing_files=()
    for file in "${missing_files[@]}"; do
      relative_missing_files+=("${file#$REPO_ROOT/}")
    done
    if [[ ${#relative_missing_files[@]} -gt 0 ]]; then
      missing_json=$(node -p 'JSON.stringify(process.argv.slice(1))' -- "${relative_missing_files[@]}")
    else
      missing_json="[]"
    fi
  else
    echo "Warning: 'node' command not found. Using basic JSON output which may be unreliable for paths with special characters." >&2
    missing_json="[]"
    if [[ ${#missing_files[@]} -gt 0 ]]; then
      missing_json=$(printf '%s\n' "${missing_files[@]}" | while read -r f; do
        echo "\"${f#$REPO_ROOT/}\""
      done | paste -sd, | sed 's/^/[/' | sed 's/$/]/')
    fi
  fi
  
  cat << EOF
{
  "componentsScanned": $components_scanned,
  "componentsCovered": $covered_count,
  "componentsMissing": $missing_count,
  "coveragePercent": $coverage,
  "missingStories": $missing_json
}
EOF
}

# Output results as text
output_text() {
  local components_scanned="$1"
  local covered_count="$2"
  local missing_count="$3"
  local coverage="$4"
  shift 4
  local missing_files=("$@")
  
  echo "=============================================================================="
  echo "Storybook Coverage Detection"
  echo "=============================================================================="
  echo ""
  echo "Scanning directory:"
  echo "  ${SCAN_DIR#$REPO_ROOT/}"
  echo ""
  echo "=============================================================================="
  echo "Results"
  echo "=============================================================================="
  echo ""
  echo "Components scanned: $components_scanned"
  echo "Components with stories: $covered_count"
  echo "Components missing stories: $missing_count"
  echo "Coverage: ${coverage}%"
  echo ""
  
  if [[ $missing_count -gt 0 ]]; then
    echo -e "${YELLOW}Components Missing Stories:${NC}"
    echo ""
    for file in "${missing_files[@]}"; do
      local relative_file="${file#$REPO_ROOT/}"
      local story_path
      story_path=$(get_story_path "$file")
      local relative_story="${story_path#$REPO_ROOT/}"
      echo "  - $relative_file"
      echo -e "    ${CYAN}Expected: $relative_story${NC}"
    done
    echo ""
    echo "=============================================================================="
    echo "How to Fix"
    echo "=============================================================================="
    echo ""
    echo "Create a .stories.tsx file for each component listed above."
    echo ""
    echo "Example story structure:"
    echo ""
    echo "  import type { Meta, StoryObj } from '@storybook/react';"
    echo "  import { ComponentName } from './component-name';"
    echo ""
    echo "  const meta: Meta<typeof ComponentName> = {"
    echo "    title: 'UI/ComponentName',"
    echo "    component: ComponentName,"
    echo "  };"
    echo ""
    echo "  export default meta;"
    echo "  type Story = StoryObj<typeof ComponentName>;"
    echo ""
    echo "  export const Default: Story = {};"
    echo ""
    echo "If a component should not have a story, add it to:"
    echo "  .github/storybook-coverage-allowlist.json"
    echo ""
    
    if [[ "$STRICT_MODE" == "true" ]]; then
      echo -e "${RED}STRICT MODE: Failing due to missing stories.${NC}"
    else
      echo -e "${YELLOW}WARNING MODE: Missing stories detected but not blocking.${NC}"
    fi
  else
    echo -e "${GREEN}All components have Storybook stories!${NC}"
  fi
}

# Main
main() {
  local allowlist
  allowlist=$(read_allowlist "$ALLOWLIST_FILE")
  
  # Check if directory exists before proceeding
  if [[ ! -d "$SCAN_DIR" ]]; then
    echo "Error: Scan directory does not exist: $SCAN_DIR" >&2
    exit 1
  fi
  
  detect_missing_stories "$SCAN_DIR" "$allowlist"
}

main "$@"
