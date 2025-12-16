#!/bin/bash
# =============================================================================
# Bundle Size Measurement Library
# =============================================================================
#
# PURPOSE:
#   Shared library containing helper functions for bundle size measurement.
#   This file is sourced by both the main script and unit tests to ensure
#   consistency and reduce maintenance cost.
#
# USAGE:
#   source scripts/lib/bundle-size-lib.sh
#
# FUNCTIONS:
#   - parse_vite_output(): Parse Vite build output to extract gzip sizes
#   - calculate_gzip_sizes_direct(): Direct gzip calculation fallback
#
# TESTING:
#   Unit tests: scripts/tests/measure-bundle-size.test.sh
#   CI workflow: .github/workflows/bundle-size-script-tests.yml
#   Documentation: scripts/tests/BUNDLE_SIZE_TESTING.md
#
# MAINTENANCE:
#   When modifying these functions, ensure corresponding unit tests are updated.
#   See scripts/tests/BUNDLE_SIZE_TESTING.md for testing guidelines.
#
# =============================================================================

# Prevent direct execution - this file should only be sourced
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  echo "Error: This script should be sourced, not executed directly." >&2
  echo "Usage: source ${BASH_SOURCE[0]}" >&2
  exit 1
fi

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

# Parse Vite build output to extract bundle sizes
# Vite output format: dist/assets/index-abc123.js   245.67 kB │ gzip:  78.23 kB
#
# Arguments:
#   $1 - build_output: The captured output from pnpm build
#   $2 - file_type: "js" or "css"
#
# Output:
#   Two space-separated values: "total_kb largest_kb"
#   Example: "123.5 78.2"
#
# Notes:
#   - Uses bc for calculations if available, falls back to awk
#   - Returns "0 0" if no matching files found in output
#   - Multiplies by 100 for integer math, then divides for decimal result
#
parse_vite_output() {
  local build_output="$1"
  local file_type="$2"  # "js" or "css"
  
  local total=0
  local largest=0
  
  while IFS= read -r line; do
    if [[ "$line" =~ \.$file_type[[:space:]] ]] && [[ "$line" =~ gzip:[[:space:]]*([0-9.]+)[[:space:]]*kB ]]; then
      local size="${BASH_REMATCH[1]}"
      # Convert to integer (multiply by 100 for precision, then divide later)
      # Use bc if available, otherwise use awk as fallback
      local size_int
      if command -v bc &> /dev/null && bc --version &> /dev/null; then
        size_int=$(echo "$size * 100" | bc | cut -d. -f1)
      else
        size_int=$(awk "BEGIN {printf \"%.0f\", $size * 100}")
      fi
      total=$((total + ${size_int:-0}))
      if (( ${size_int:-0} > largest )); then
        largest=${size_int:-0}
      fi
    fi
  done <<< "$build_output"
  
  # Convert back to KB with one decimal
  local total_kb
  local largest_kb
  if command -v bc &> /dev/null && bc --version &> /dev/null; then
    total_kb=$(echo "scale=1; $total / 100" | bc)
    largest_kb=$(echo "scale=1; $largest / 100" | bc)
  else
    total_kb=$(awk "BEGIN {printf \"%.1f\", $total / 100}")
    largest_kb=$(awk "BEGIN {printf \"%.1f\", $largest / 100}")
  fi
  
  echo "$total_kb $largest_kb"
}

# Direct gzip calculation fallback
# Used when Vite output parsing fails or returns 0
# This directly measures gzip size of files in dist/assets
#
# Arguments:
#   $1 - dist_path: Path to the dist directory (e.g., "app/dist")
#   $2 - file_type: "js" or "css"
#
# Output:
#   Two space-separated values: "total_kb largest_kb"
#   Example: "123.5 78.2"
#
# Notes:
#   - Returns "0 0" if dist/assets directory doesn't exist
#   - Uses gzip -c to calculate compressed size without modifying files
#   - Handles gzip failures gracefully with { gzip || true; }
#   - Uses bc for calculations if available, falls back to awk
#
calculate_gzip_sizes_direct() {
  local dist_path="$1"
  local file_type="$2"  # "js" or "css"
  
  local total=0
  local largest=0
  
  if [[ ! -d "$dist_path/assets" ]]; then
    echo "0 0"
    return
  fi
  
  # Find all files of the specified type and calculate gzip size
  while IFS= read -r -d '' file; do
    if [[ -f "$file" ]]; then
      # Calculate gzip size in bytes
      # Use { gzip || true; } to prevent pipefail from terminating script on gzip failure
      local current_size
      current_size=$({ gzip -c "$file" 2>/dev/null || true; } | wc -c)
      # Use default value 0 if current_size is empty (gzip failed completely)
      total=$((total + ${current_size:-0}))
      if (( ${current_size:-0} > largest )); then
        largest=${current_size:-0}
      fi
    fi
  done < <(find "$dist_path/assets" -name "*.$file_type" -print0 2>/dev/null)
  
  # Convert bytes to KB with one decimal
  local total_kb
  local largest_kb
  if command -v bc &> /dev/null && bc --version &> /dev/null; then
    total_kb=$(echo "scale=1; $total / 1024" | bc)
    largest_kb=$(echo "scale=1; $largest / 1024" | bc)
  else
    total_kb=$(awk "BEGIN {printf \"%.1f\", $total / 1024}")
    largest_kb=$(awk "BEGIN {printf \"%.1f\", $largest / 1024}")
  fi
  
  echo "$total_kb $largest_kb"
}

# Check if bc is available and functional
# This is more robust than just `command -v bc` because some systems
# may have bc installed but not functional
#
# Returns:
#   0 if bc is available and functional
#   1 if bc is not available or not functional
#
is_bc_available() {
  if command -v bc &> /dev/null && echo "1+1" | bc &> /dev/null; then
    return 0
  else
    return 1
  fi
}
