#!/bin/bash
# ============================================================================
# Bundle Size Measurement Script - Phase 2 Design System Migration
# ============================================================================
#
# This script measures bundle sizes for frontend applications to track
# performance impact during Phase 2 migration work.
#
# REQUIREMENTS:
#   - Bash 4.0+
#   - pnpm (for building)
#   - Node.js 20+
#
# USAGE:
#   ./scripts/measure-bundle-size.sh                    # Measure all apps
#   ./scripts/measure-bundle-size.sh owner-console      # Measure specific app
#   ./scripts/measure-bundle-size.sh --compare <file>   # Compare with baseline
#   ./scripts/measure-bundle-size.sh --save-baseline    # Save current as baseline
#   ./scripts/measure-bundle-size.sh --json             # Output JSON format
#   ./scripts/measure-bundle-size.sh --help             # Show help
#
# METRICS:
#   - Total JS (gzip): Sum of all .js files after gzip compression
#   - Total CSS (gzip): Sum of all .css files after gzip compression
#   - Largest Chunk: Size of the largest JS chunk after gzip
#
# THRESHOLDS:
#   - Total JS: +50KB
#   - Total CSS: +10KB
#   - Largest Chunk: +30KB
#
# ============================================================================

set -euo pipefail

# ============================================================================
# CONFIGURATION
# ============================================================================

# Apps to measure
APPS=(
  "owner-console"
  "frontend-dashboard"
)

# App paths (relative to repo root)
declare -A APP_PATHS
APP_PATHS["owner-console"]="handoff/20250928/40_App/owner-console"
APP_PATHS["frontend-dashboard"]="handoff/20250928/40_App/frontend-dashboard"

# Thresholds (in KB)
THRESHOLD_JS=50
THRESHOLD_CSS=10
THRESHOLD_CHUNK=30

# Baseline file
BASELINE_FILE=".bundle-size-baseline.json"

# Output format
OUTPUT_FORMAT="text"
COMPARE_FILE=""
SAVE_BASELINE=false
SINGLE_APP=""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

print_help() {
  cat << 'EOF'
Bundle Size Measurement Script - Phase 2 Design System Migration

USAGE:
  ./scripts/measure-bundle-size.sh [OPTIONS] [APP]

OPTIONS:
  --compare <file>    Compare results with baseline file
  --save-baseline     Save current results as baseline
  --json              Output in JSON format
  --help              Show this help message

APPS:
  owner-console       Owner Console application
  frontend-dashboard  Frontend Dashboard application

EXAMPLES:
  # Measure all apps
  ./scripts/measure-bundle-size.sh

  # Measure specific app
  ./scripts/measure-bundle-size.sh owner-console

  # Save baseline
  ./scripts/measure-bundle-size.sh --save-baseline

  # Compare with baseline
  ./scripts/measure-bundle-size.sh --compare .bundle-size-baseline.json

THRESHOLDS:
  - Total JS (gzip): +50KB
  - Total CSS (gzip): +10KB
  - Largest Chunk (gzip): +30KB
EOF
}

# Parse Vite build output to extract bundle sizes
# Vite output format: dist/assets/index-abc123.js   245.67 kB │ gzip:  78.23 kB
parse_vite_output() {
  local build_output="$1"
  local file_type="$2"  # "js" or "css"
  
  local total=0
  local largest=0
  
  while IFS= read -r line; do
    if [[ "$line" =~ \.$file_type[[:space:]] ]] && [[ "$line" =~ gzip:[[:space:]]*([0-9.]+)[[:space:]]*kB ]]; then
      local size="${BASH_REMATCH[1]}"
      # Convert to integer (multiply by 100 for precision, then divide later)
      local size_int
      size_int=$(echo "$size * 100" | bc | cut -d. -f1)
      total=$((total + size_int))
      if [[ "$size_int" -gt "$largest" ]]; then
        largest="$size_int"
      fi
    fi
  done <<< "$build_output"
  
  # Convert back to KB with one decimal
  local total_kb
  local largest_kb
  if command -v bc &> /dev/null; then
    total_kb=$(echo "scale=1; $total / 100" | bc)
    largest_kb=$(echo "scale=1; $largest / 100" | bc)
  else
    total_kb=$(awk "BEGIN {printf \"%.1f\", $total / 100}")
    largest_kb=$(awk "BEGIN {printf \"%.1f\", $largest / 100}")
  fi
  
  echo "$total_kb $largest_kb"
}

# Build an app and capture output
build_app() {
  local app="$1"
  local app_path="${APP_PATHS[$app]}"
  
  if [[ ! -d "$app_path" ]]; then
    echo "Error: App path not found: $app_path" >&2
    return 1
  fi
  
  # Build the app
  local build_output
  build_output=$(pnpm --filter "$app" build 2>&1) || {
    echo "Error: Build failed for $app" >&2
    echo "$build_output" >&2
    return 1
  }
  
  echo "$build_output"
}

# Measure bundle size for an app
measure_app() {
  local app="$1"
  
  echo "Building $app..." >&2
  
  local build_output
  build_output=$(build_app "$app") || return 1
  
  # Parse JS sizes
  local js_result
  js_result=$(parse_vite_output "$build_output" "js")
  local js_total
  js_total=$(echo "$js_result" | cut -d' ' -f1)
  local js_largest
  js_largest=$(echo "$js_result" | cut -d' ' -f2)
  
  # Parse CSS sizes
  local css_result
  css_result=$(parse_vite_output "$build_output" "css")
  local css_total
  css_total=$(echo "$css_result" | cut -d' ' -f1)
  
  echo "$js_total $css_total $js_largest"
}

# ============================================================================
# MAIN FUNCTIONS
# ============================================================================

# Measure all apps or a single app
measure_all() {
  local apps_to_measure=("${APPS[@]}")
  
  if [[ -n "$SINGLE_APP" ]]; then
    apps_to_measure=("$SINGLE_APP")
  fi
  
  local timestamp
  timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  local commit
  commit=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
  
  if [[ "$OUTPUT_FORMAT" != "json" ]]; then
    echo "================================================================================"
    echo "Bundle Size Report"
    echo "Generated: $timestamp"
    echo "Commit: $commit"
    echo "================================================================================"
  fi
  
  local json_apps=""
  local all_results=()
  
  for app in "${apps_to_measure[@]}"; do
    local result
    result=$(measure_app "$app") || continue
    
    local js_total
    js_total=$(echo "$result" | cut -d' ' -f1)
    local css_total
    css_total=$(echo "$result" | cut -d' ' -f2)
    local js_largest
    js_largest=$(echo "$result" | cut -d' ' -f3)
    
    all_results+=("$app:$js_total:$css_total:$js_largest")
    
    if [[ "$OUTPUT_FORMAT" == "json" ]]; then
      if [[ -n "$json_apps" ]]; then
        json_apps="$json_apps,"
      fi
      json_apps="$json_apps
    {
      \"app\": \"$app\",
      \"js_total_gzip_kb\": $js_total,
      \"css_total_gzip_kb\": $css_total,
      \"largest_chunk_gzip_kb\": $js_largest
    }"
    else
      echo ""
      echo "### $app"
      echo ""
      echo "| Metric | Value |"
      echo "|--------|-------|"
      echo "| Total JS (gzip) | ${js_total} kB |"
      echo "| Total CSS (gzip) | ${css_total} kB |"
      echo "| Largest Chunk (gzip) | ${js_largest} kB |"
    fi
  done
  
  if [[ "$OUTPUT_FORMAT" == "json" ]]; then
    cat << EOF
{
  "timestamp": "$timestamp",
  "commit": "$commit",
  "apps": [$json_apps
  ]
}
EOF
  fi
  
  # Compare with baseline if exists
  if [[ -f "$BASELINE_FILE" ]] && [[ "$OUTPUT_FORMAT" != "json" ]]; then
    echo ""
    echo "=== Baseline Comparison ==="
    echo ""
    
    for result in "${all_results[@]}"; do
      local app
      app=$(echo "$result" | cut -d: -f1)
      local js_total
      js_total=$(echo "$result" | cut -d: -f2)
      local css_total
      css_total=$(echo "$result" | cut -d: -f3)
      local js_largest
      js_largest=$(echo "$result" | cut -d: -f4)
      
      # Get baseline values
      local baseline_js baseline_css baseline_chunk
      if command -v jq &> /dev/null; then
        baseline_js=$(jq -r ".apps[] | select(.app == \"$app\") | .js_total_gzip_kb // 0" "$BASELINE_FILE" 2>/dev/null || echo "0")
        baseline_css=$(jq -r ".apps[] | select(.app == \"$app\") | .css_total_gzip_kb // 0" "$BASELINE_FILE" 2>/dev/null || echo "0")
        baseline_chunk=$(jq -r ".apps[] | select(.app == \"$app\") | .largest_chunk_gzip_kb // 0" "$BASELINE_FILE" 2>/dev/null || echo "0")
      else
        baseline_js="0"
        baseline_css="0"
        baseline_chunk="0"
      fi
      
      # Calculate deltas
      local js_delta css_delta chunk_delta
      if command -v bc &> /dev/null; then
        js_delta=$(echo "$js_total - $baseline_js" | bc)
        css_delta=$(echo "$css_total - $baseline_css" | bc)
        chunk_delta=$(echo "$js_largest - $baseline_chunk" | bc)
      else
        js_delta=$(awk "BEGIN {printf \"%.1f\", $js_total - $baseline_js}")
        css_delta=$(awk "BEGIN {printf \"%.1f\", $css_total - $baseline_css}")
        chunk_delta=$(awk "BEGIN {printf \"%.1f\", $js_largest - $baseline_chunk}")
      fi
      
      echo "### $app"
      echo ""
      echo "| Metric | Baseline | Current | Delta | Status |"
      echo "|--------|----------|---------|-------|--------|"
      
      # JS status
      local js_status="PASS"
      local js_delta_num
      js_delta_num=$(echo "$js_delta" | sed 's/[^0-9.-]//g')
      if (( $(echo "$js_delta_num > $THRESHOLD_JS" | bc -l) )); then
        js_status="FAIL"
      fi
      printf "| Total JS (gzip) | %s kB | %s kB | %+.1f kB | %s |\n" "$baseline_js" "$js_total" "$js_delta" "$js_status"
      
      # CSS status
      local css_status="PASS"
      local css_delta_num
      css_delta_num=$(echo "$css_delta" | sed 's/[^0-9.-]//g')
      if (( $(echo "$css_delta_num > $THRESHOLD_CSS" | bc -l) )); then
        css_status="FAIL"
      fi
      printf "| Total CSS (gzip) | %s kB | %s kB | %+.1f kB | %s |\n" "$baseline_css" "$css_total" "$css_delta" "$css_status"
      
      # Chunk status
      local chunk_status="PASS"
      local chunk_delta_num
      chunk_delta_num=$(echo "$chunk_delta" | sed 's/[^0-9.-]//g')
      if (( $(echo "$chunk_delta_num > $THRESHOLD_CHUNK" | bc -l) )); then
        chunk_status="FAIL"
      fi
      printf "| Largest Chunk | %s kB | %s kB | %+.1f kB | %s |\n" "$baseline_chunk" "$js_largest" "$chunk_delta" "$chunk_status"
      
      echo ""
    done
  fi
  
  # Save baseline if requested
  if [[ "$SAVE_BASELINE" == true ]]; then
    OUTPUT_FORMAT="json"
    measure_all > "$BASELINE_FILE"
    OUTPUT_FORMAT="text"
    echo ""
    echo "Baseline saved to: $BASELINE_FILE"
  fi
}

# ============================================================================
# MAIN
# ============================================================================

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --compare)
      COMPARE_FILE="$2"
      BASELINE_FILE="$2"
      shift 2
      ;;
    --save-baseline)
      SAVE_BASELINE=true
      shift
      ;;
    --json)
      OUTPUT_FORMAT="json"
      shift
      ;;
    --help|-h)
      print_help
      exit 0
      ;;
    owner-console|frontend-dashboard)
      SINGLE_APP="$1"
      shift
      ;;
    *)
      echo "Unknown option: $1" >&2
      print_help
      exit 1
      ;;
  esac
done

# Check we're in repo root
if [[ ! -f "package.json" ]] || [[ ! -f "pnpm-workspace.yaml" ]]; then
  echo "Error: Must be run from repository root" >&2
  exit 1
fi

# Check dependencies
if ! command -v pnpm &> /dev/null; then
  echo "Error: pnpm is required but not installed" >&2
  exit 1
fi

if ! command -v bc &> /dev/null; then
  echo "Warning: bc not found, using awk for calculations" >&2
fi

# Run measurement
measure_all
