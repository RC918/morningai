#!/bin/bash
# Count TypeScript strict mode errors for all packages
# Usage: ./scripts/count-strict-errors.sh [--update-baseline] [--validate]
#
# This script counts TypeScript strict mode errors and compares against baselines.
# Use --update-baseline to update .strict-baseline.json with current counts.
# Use --validate to run a quick validation check (for CI smoke testing).

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BASELINE_FILE="$REPO_ROOT/.strict-baseline.json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

validate_baseline_file() {
  local errors=0
  
  echo "Validating baseline file..."
  
  # Check file exists
  if [ ! -f "$BASELINE_FILE" ]; then
    echo -e "${RED}ERROR: $BASELINE_FILE not found${NC}"
    echo "This file is required for TypeScript strict mode checks."
    echo "See docs/typescript/STRICT_MODE_BASELINE.md for setup instructions."
    return 1
  fi
  
  # Check JSON is valid
  if ! jq -e '.' "$BASELINE_FILE" > /dev/null 2>&1; then
    echo -e "${RED}ERROR: $BASELINE_FILE is not valid JSON${NC}"
    return 1
  fi
  
  # Check required structure
  if ! jq -e '.packages' "$BASELINE_FILE" > /dev/null 2>&1; then
    echo -e "${RED}ERROR: Missing 'packages' key in baseline file${NC}"
    return 1
  fi
  
  # Validate each package entry
  for package in $(jq -r '.packages | keys[]' "$BASELINE_FILE"); do
    local path
    path=$(jq -r ".packages.\"$package\".path // empty" "$BASELINE_FILE")
    local error_count
    error_count=$(jq -r ".packages.\"$package\".error_count // empty" "$BASELINE_FILE")
    
    # Check for invalid characters in package name (colon is used as delimiter in batch updates)
    if [[ "$package" == *":"* ]]; then
      echo -e "${RED}ERROR: Package name '$package' contains ':' which is not allowed${NC}"
      errors=$((errors + 1))
    fi
    
    if [ -z "$path" ]; then
      echo -e "${RED}ERROR: Package '$package' missing 'path' field${NC}"
      errors=$((errors + 1))
    elif [ ! -d "$REPO_ROOT/$path" ]; then
      echo -e "${YELLOW}WARNING: Package '$package' path does not exist: $path${NC}"
    fi
    
    if [ -z "$error_count" ]; then
      echo -e "${RED}ERROR: Package '$package' missing 'error_count' field${NC}"
      errors=$((errors + 1))
    elif ! [[ "$error_count" =~ ^[0-9]+$ ]]; then
      echo -e "${RED}ERROR: Package '$package' error_count is not a number: $error_count${NC}"
      errors=$((errors + 1))
    fi
  done
  
  if [ "$errors" -gt 0 ]; then
    echo -e "${RED}Validation failed with $errors error(s)${NC}"
    return 1
  fi
  
  echo -e "${GREEN}Baseline file validation passed${NC}"
  return 0
}

count_errors() {
  local package_path="$1"
  local full_path="$REPO_ROOT/$package_path"
  
  if [ ! -d "$full_path" ]; then
    echo "0"
    return
  fi
  
  # Run typecheck:strict in a subshell to avoid changing working directory
  # Count errors matching "src/" and "error TS" to match CI behavior
  local output
  output=$( (cd "$full_path" && pnpm run typecheck:strict) 2>&1 || true)
  local count
  count=$(echo "$output" | grep "src/" | grep -c 'error TS' || true)
  
  # Handle case where grep returns empty or non-numeric
  if [ -z "$count" ] || ! [[ "$count" =~ ^[0-9]+$ ]]; then
    count=0
  fi
  
  echo "$count"
}

get_baseline() {
  local package="$1"
  jq -r ".packages.\"$package\".error_count // 0" "$BASELINE_FILE"
}

get_package_path() {
  local package="$1"
  jq -r ".packages.\"$package\".path // empty" "$BASELINE_FILE"
}

# Batch update baseline - more efficient and safer for updating multiple packages at once
# Usage: update_baseline_batch "pkg1:count1" "pkg2:count2" ...
# Uses --argjson to safely pass data to jq, avoiding string interpolation vulnerabilities
update_baseline_batch() {
  local today
  today=$(date +%Y-%m-%d)
  
  # Build JSON array of updates for safe passing to jq
  local updates_json="["
  local first=true
  for entry in "$@"; do
    if [ "$first" = true ]; then
      first=false
    else
      updates_json+=","
    fi
    updates_json+="\"$entry\""
  done
  updates_json+="]"
  
  # Use --argjson to safely pass data to jq (avoids string interpolation vulnerabilities)
  # The reduce function iterates over updates and applies each one
  jq --arg today "$today" \
     --argjson updates "$updates_json" \
     '.last_updated = $today | reduce ($updates[] | split(":")) as $p (.; .packages[$p[0]].error_count = ($p[1] | tonumber))' \
     "$BASELINE_FILE" > "$BASELINE_FILE.tmp"
  mv "$BASELINE_FILE.tmp" "$BASELINE_FILE"
}

main() {
  local update_mode=false
  local validate_mode=false
  
  for arg in "$@"; do
    case "$arg" in
      --update-baseline)
        update_mode=true
        ;;
      --validate)
        validate_mode=true
        ;;
    esac
  done

  # Validate mode: just check baseline file structure
  if [ "$validate_mode" = true ]; then
    validate_baseline_file
    exit $?
  fi

  # Normal mode: require baseline file
  if [ ! -f "$BASELINE_FILE" ]; then
    echo -e "${RED}ERROR: $BASELINE_FILE not found${NC}"
    echo "This file is required. See docs/typescript/STRICT_MODE_BASELINE.md"
    exit 1
  fi

  echo "TypeScript Strict Mode Error Count"
  echo "==================================="
  echo ""
  
  local total_errors=0
  local total_baseline=0
  local has_regression=false
  local updates=()  # Collect updates for batch processing
  
  # Read packages dynamically from baseline file
  for package in $(jq -r '.packages | keys[]' "$BASELINE_FILE"); do
    local path
    path=$(get_package_path "$package")
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
      # Collect updates for batch processing (more efficient than individual file writes)
      updates+=("$package:$count")
    fi
  done
  
  # Batch update all baselines in a single file write (if in update mode)
  if [ "$update_mode" = true ] && [ ${#updates[@]} -gt 0 ]; then
    update_baseline_batch "${updates[@]}"
  fi
  
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
