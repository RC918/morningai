#!/bin/bash
# Count TypeScript strict mode errors for all packages
# Usage: ./scripts/count-strict-errors.sh [--update-baseline]
#
# This script counts TypeScript strict mode errors and compares against baselines.
# Use --update-baseline to update .strict-baseline.json with current counts.

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BASELINE_FILE="$REPO_ROOT/.strict-baseline.json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Package paths
declare -A PACKAGES=(
  ["frontend-dashboard"]="handoff/20250928/40_App/frontend-dashboard"
  ["owner-console"]="handoff/20250928/40_App/owner-console"
  ["shared-ui"]="packages/shared-ui"
)

count_errors() {
  local package_path="$1"
  local full_path="$REPO_ROOT/$package_path"
  
  if [ ! -d "$full_path" ]; then
    echo "0"
    return
  fi
  
  cd "$full_path"
  
  # Run typecheck:strict and count errors
  local output
  output=$(pnpm run typecheck:strict 2>&1 || true)
  local count
  count=$(echo "$output" | grep -c 'error TS' || true)
  
  # Handle case where grep returns empty or non-numeric
  if [ -z "$count" ] || ! [[ "$count" =~ ^[0-9]+$ ]]; then
    count=0
  fi
  
  echo "$count"
}

get_baseline() {
  local package="$1"
  if [ -f "$BASELINE_FILE" ]; then
    jq -r ".packages.\"$package\".error_count // 0" "$BASELINE_FILE"
  else
    echo "0"
  fi
}

update_baseline() {
  local package="$1"
  local count="$2"
  local today
  today=$(date +%Y-%m-%d)
  
  if [ -f "$BASELINE_FILE" ]; then
    # Update existing baseline
    jq ".packages.\"$package\".error_count = $count | .last_updated = \"$today\"" "$BASELINE_FILE" > "$BASELINE_FILE.tmp"
    mv "$BASELINE_FILE.tmp" "$BASELINE_FILE"
  fi
}

main() {
  local update_mode=false
  if [ "$1" = "--update-baseline" ]; then
    update_mode=true
  fi

  echo "TypeScript Strict Mode Error Count"
  echo "==================================="
  echo ""
  
  local total_errors=0
  local total_baseline=0
  local has_regression=false
  
  for package in "${!PACKAGES[@]}"; do
    local path="${PACKAGES[$package]}"
    local count
    count=$(count_errors "$path")
    local baseline
    baseline=$(get_baseline "$package")
    
    total_errors=$((total_errors + count))
    total_baseline=$((total_baseline + baseline))
    
    # Determine status
    local status
    if [ "$count" -gt "$baseline" ]; then
      status="${RED}REGRESSION (+$((count - baseline)))${NC}"
      has_regression=true
    elif [ "$count" -lt "$baseline" ]; then
      status="${GREEN}IMPROVED (-$((baseline - count)))${NC}"
    else
      status="${GREEN}OK${NC}"
    fi
    
    printf "%-20s: %3d errors (baseline: %3d) %b\n" "$package" "$count" "$baseline" "$status"
    
    if [ "$update_mode" = true ]; then
      update_baseline "$package" "$count"
    fi
  done
  
  echo ""
  echo "-----------------------------------"
  printf "%-20s: %3d errors (baseline: %3d)\n" "TOTAL" "$total_errors" "$total_baseline"
  
  if [ "$update_mode" = true ]; then
    echo ""
    echo -e "${YELLOW}Baseline updated in $BASELINE_FILE${NC}"
  fi
  
  if [ "$has_regression" = true ]; then
    echo ""
    echo -e "${RED}ERROR: Strict mode errors have increased!${NC}"
    echo "Fix the new errors or update the baseline with: $0 --update-baseline"
    exit 1
  fi
  
  echo ""
  echo -e "${GREEN}All packages within baseline.${NC}"
}

main "$@"
