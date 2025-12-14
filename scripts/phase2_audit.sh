#!/bin/bash
# ============================================================================
# Phase 2 Audit Script - Design System Card Migration Tracking
# ============================================================================
#
# This script measures shared-ui card adoption and tracks migration progress
# for Epic #2304 Phase 2 work.
#
# REQUIREMENTS:
#   - Bash 4.0+ (uses arrays, pipefail, associative arrays)
#   - GNU grep (for -o, -E, -P options)
#   - Must be run from repository root
#
# USAGE:
#   ./scripts/phase2_audit.sh                    # Audit all target directories
#   ./scripts/phase2_audit.sh --file <path>      # Audit single file
#   ./scripts/phase2_audit.sh --dir <path>       # Audit specific directory
#   ./scripts/phase2_audit.sh --json             # Output JSON format
#   ./scripts/phase2_audit.sh --compare <file>   # Compare with baseline
#   ./scripts/phase2_audit.sh --update-baseline  # Update baseline file
#   ./scripts/phase2_audit.sh --help             # Show help
#
# ============================================================================

set -euo pipefail

# ============================================================================
# CONFIGURATION
# ============================================================================

# Scan paths (relative to repo root)
SCAN_DIRS=(
  "handoff/20250928/40_App/owner-console/src/pages"
  "handoff/20250928/40_App/owner-console/src/components"
  "handoff/20250928/40_App/frontend-dashboard/src/pages"
  "handoff/20250928/40_App/frontend-dashboard/src/components"
)

# Exclude patterns
EXCLUDE_PATTERNS=(
  "*.stories.*"
  "*.test.*"
  "*.spec.*"
  "__tests__"
  "__mocks__"
  "node_modules"
)

# File types to scan
FILE_EXTENSIONS=("tsx" "jsx" "ts" "js")

# Shared-UI Card Allowlist (Phase 1 archetypes)
SHARED_UI_CARDS=(
  "StatCard"
  "StatusCard"
  "MetricCard"
  "SettingsCard"
  "SectionCard"
)

# Legacy Card Allowlist (to be migrated in Phase 2)
LEGACY_CARDS=(
  # Owner Console
  "SessionStatusCard"
  "TwoFAStatusCard"
  "TenantCard"
  "ApprovalCard"
  "PolicyCard"
  "GovernanceCard"
  "MonitoringCard"
  "EvaluationCard"
  "ExperimentCard"
  # Frontend Dashboard
  "DashboardCard"
  "CostCard"
  "AgentCard"
  "DecisionCard"
  "ReportCard"
)

# Baseline file
BASELINE_FILE=".phase2-baseline.json"

# Output format
OUTPUT_FORMAT="text"
SINGLE_FILE=""
SINGLE_DIR=""
COMPARE_FILE=""
UPDATE_BASELINE=false

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

print_help() {
  cat << 'EOF'
Phase 2 Audit Script - Design System Card Migration Tracking

USAGE:
  ./scripts/phase2_audit.sh [OPTIONS]

OPTIONS:
  --file <path>       Audit a single file
  --dir <path>        Audit a specific directory
  --json              Output in JSON format
  --compare <file>    Compare results with baseline file
  --update-baseline   Update the baseline file with current results
  --help              Show this help message

EXAMPLES:
  # Audit all target directories
  ./scripts/phase2_audit.sh

  # Audit a single file
  ./scripts/phase2_audit.sh --file src/pages/Settings2FA.jsx

  # Output JSON for CI integration
  ./scripts/phase2_audit.sh --json > audit-result.json

  # Compare with baseline
  ./scripts/phase2_audit.sh --compare .phase2-baseline.json

SCAN PATHS:
  - handoff/20250928/40_App/owner-console/src/pages
  - handoff/20250928/40_App/owner-console/src/components
  - handoff/20250928/40_App/frontend-dashboard/src/pages
  - handoff/20250928/40_App/frontend-dashboard/src/components

EXCLUDES:
  - *.stories.*, *.test.*, *.spec.*
  - __tests__, __mocks__, node_modules

SHARED-UI CARD ALLOWLIST:
  StatCard, StatusCard, MetricCard, SettingsCard, SectionCard

LEGACY CARD ALLOWLIST:
  SessionStatusCard, TwoFAStatusCard, TenantCard, ApprovalCard,
  PolicyCard, GovernanceCard, MonitoringCard, EvaluationCard,
  ExperimentCard, DashboardCard, CostCard, AgentCard, DecisionCard, ReportCard
EOF
}

# Build grep exclude arguments
build_exclude_args() {
  local args=""
  for pattern in "${EXCLUDE_PATTERNS[@]}"; do
    if [[ "$pattern" == *"*"* ]]; then
      args="$args --exclude=$pattern"
    else
      args="$args --exclude-dir=$pattern"
    fi
  done
  echo "$args"
}

# Build file include arguments
build_include_args() {
  local args=""
  for ext in "${FILE_EXTENSIONS[@]}"; do
    args="$args --include=*.$ext"
  done
  echo "$args"
}

# Count occurrences of a pattern in a file (match-based, not line-based)
# Returns 0 if no matches (handles grep exit 1 gracefully)
count_pattern() {
  local pattern="$1"
  local file="$2"
  local count
  count=$({ grep -Eo "$pattern" "$file" 2>/dev/null || true; } | wc -l)
  echo "${count:-0}"
}

# Count occurrences of a pattern in a directory
count_pattern_in_dir() {
  local pattern="$1"
  local dir="$2"
  local exclude_args
  local include_args
  exclude_args=$(build_exclude_args)
  include_args=$(build_include_args)
  
  local count
  # shellcheck disable=SC2086
  count=$({ grep -rEo $include_args $exclude_args "$pattern" "$dir" 2>/dev/null || true; } | wc -l)
  echo "${count:-0}"
}

# ============================================================================
# CARD COUNTING FUNCTIONS
# ============================================================================

# Count shared-ui card JSX usage
# Handles both direct JSX (<StatCard>) and namespace JSX (<SharedUI.StatCard>)
count_shared_ui_cards() {
  local target="$1"
  local total=0
  
  for card in "${SHARED_UI_CARDS[@]}"; do
    local count
    if [[ -f "$target" ]]; then
      # Direct JSX: <StatCard followed by space, newline, >, or /
      local direct
      direct=$(count_pattern "<${card}([^a-zA-Z0-9]|$)" "$target")
      # Namespace JSX: <SharedUI.StatCard or similar patterns
      local namespace
      namespace=$(count_pattern "\\.${card}([^a-zA-Z0-9]|$)" "$target")
      count=$((direct + namespace))
    else
      # Direct JSX
      local direct
      direct=$(count_pattern_in_dir "<${card}([^a-zA-Z0-9]|$)" "$target")
      # Namespace JSX
      local namespace
      namespace=$(count_pattern_in_dir "\\.${card}([^a-zA-Z0-9]|$)" "$target")
      count=$((direct + namespace))
    fi
    total=$((total + count))
  done
  
  echo "$total"
}

# Count individual shared-ui card types (returns JSON-like string)
count_shared_ui_cards_breakdown() {
  local target="$1"
  local result=""
  
  for card in "${SHARED_UI_CARDS[@]}"; do
    local count
    if [[ -f "$target" ]]; then
      local direct
      direct=$(count_pattern "<${card}([^a-zA-Z0-9]|$)" "$target")
      local namespace
      namespace=$(count_pattern "\\.${card}([^a-zA-Z0-9]|$)" "$target")
      count=$((direct + namespace))
    else
      local direct
      direct=$(count_pattern_in_dir "<${card}([^a-zA-Z0-9]|$)" "$target")
      local namespace
      namespace=$(count_pattern_in_dir "\\.${card}([^a-zA-Z0-9]|$)" "$target")
      count=$((direct + namespace))
    fi
    if [[ -n "$result" ]]; then
      result="$result, "
    fi
    result="$result$card: $count"
  done
  
  echo "$result"
}

# Count legacy card JSX usage
count_legacy_cards() {
  local target="$1"
  local total=0
  
  for card in "${LEGACY_CARDS[@]}"; do
    local count
    if [[ -f "$target" ]]; then
      count=$(count_pattern "<${card}([^a-zA-Z0-9]|$)" "$target")
    else
      count=$(count_pattern_in_dir "<${card}([^a-zA-Z0-9]|$)" "$target")
    fi
    total=$((total + count))
  done
  
  echo "$total"
}

# Count individual legacy card types (returns JSON-like string)
count_legacy_cards_breakdown() {
  local target="$1"
  local result=""
  
  for card in "${LEGACY_CARDS[@]}"; do
    local count
    if [[ -f "$target" ]]; then
      count=$(count_pattern "<${card}([^a-zA-Z0-9]|$)" "$target")
    else
      count=$(count_pattern_in_dir "<${card}([^a-zA-Z0-9]|$)" "$target")
    fi
    if [[ "$count" -gt 0 ]]; then
      if [[ -n "$result" ]]; then
        result="$result, "
      fi
      result="$result$card: $count"
    fi
  done
  
  echo "${result:-none}"
}

# Count unknown card-like components (heuristic)
# These are components ending in "Card" that are not in allowlists
count_unknown_cards() {
  local target="$1"
  local count
  
  # Build exclusion pattern for known cards
  local known_cards=("${SHARED_UI_CARDS[@]}" "${LEGACY_CARDS[@]}")
  local exclude_pattern=""
  for card in "${known_cards[@]}"; do
    if [[ -n "$exclude_pattern" ]]; then
      exclude_pattern="$exclude_pattern|"
    fi
    exclude_pattern="$exclude_pattern$card"
  done
  
  if [[ -f "$target" ]]; then
    # Find all <*Card patterns, then exclude known ones
    local all_cards
    all_cards=$({ grep -Eo "<[A-Z][a-zA-Z]*Card([^a-zA-Z0-9]|$)" "$target" 2>/dev/null || true; } | wc -l)
    local known
    known=$({ grep -Eo "<($exclude_pattern)([^a-zA-Z0-9]|$)" "$target" 2>/dev/null || true; } | wc -l)
    count=$((all_cards - known))
  else
    local exclude_args
    local include_args
    exclude_args=$(build_exclude_args)
    include_args=$(build_include_args)
    
    # shellcheck disable=SC2086
    local all_cards
    all_cards=$({ grep -rEo $include_args $exclude_args "<[A-Z][a-zA-Z]*Card([^a-zA-Z0-9]|$)" "$target" 2>/dev/null || true; } | wc -l)
    # shellcheck disable=SC2086
    local known
    known=$({ grep -rEo $include_args $exclude_args "<($exclude_pattern)([^a-zA-Z0-9]|$)" "$target" 2>/dev/null || true; } | wc -l)
    count=$((all_cards - known))
  fi
  
  # Ensure non-negative
  if [[ "$count" -lt 0 ]]; then
    count=0
  fi
  
  echo "$count"
}

# List unknown card-like components
list_unknown_cards() {
  local target="$1"
  
  # Build exclusion pattern for known cards
  local known_cards=("${SHARED_UI_CARDS[@]}" "${LEGACY_CARDS[@]}")
  local exclude_pattern=""
  for card in "${known_cards[@]}"; do
    if [[ -n "$exclude_pattern" ]]; then
      exclude_pattern="$exclude_pattern|"
    fi
    exclude_pattern="$exclude_pattern$card"
  done
  
  local exclude_args
  local include_args
  exclude_args=$(build_exclude_args)
  include_args=$(build_include_args)
  
  if [[ -f "$target" ]]; then
    { grep -Eo "<[A-Z][a-zA-Z]*Card" "$target" 2>/dev/null || true; } | \
      { grep -Ev "^<($exclude_pattern)$" || true; } | \
      sort -u | \
      sed 's/^<//'
  else
    # shellcheck disable=SC2086
    { grep -rEoh $include_args $exclude_args "<[A-Z][a-zA-Z]*Card" "$target" 2>/dev/null || true; } | \
      { grep -Ev "^<($exclude_pattern)$" || true; } | \
      sort -u | \
      sed 's/^<//'
  fi
}

# Count raw hex colors (using audit-design-system.sh pattern)
count_raw_hex() {
  local target="$1"
  local exclude_args
  local include_args
  exclude_args=$(build_exclude_args)
  include_args=$(build_include_args)
  
  # Pattern: #RGB or #RRGGBB (strict 3 or 6 digits)
  local hex_pattern="#[0-9A-Fa-f]{3}([0-9A-Fa-f]{3})?"
  # Fallback pattern: hex inside var() fallback
  local fallback_pattern="var\([^)]*,[[:space:]]*#[0-9A-Fa-f]{3}([0-9A-Fa-f]{3})?"
  
  local total_hex
  local fallback_hex
  
  if [[ -f "$target" ]]; then
    total_hex=$(count_pattern "$hex_pattern" "$target")
    fallback_hex=$({ grep -Eo "$fallback_pattern" "$target" 2>/dev/null || true; } | \
      { grep -Eo "$hex_pattern" || true; } | wc -l)
  else
    total_hex=$(count_pattern_in_dir "$hex_pattern" "$target")
    # shellcheck disable=SC2086
    fallback_hex=$({ grep -rEo $include_args $exclude_args "$fallback_pattern" "$target" 2>/dev/null || true; } | \
      { grep -Eo "$hex_pattern" || true; } | wc -l)
  fi
  
  local raw_hex=$((total_hex - fallback_hex))
  if [[ "$raw_hex" -lt 0 ]]; then
    raw_hex=0
  fi
  
  echo "$raw_hex"
}

# Count inline styles
count_inline_styles() {
  local target="$1"
  local pattern="style=\{"
  
  if [[ -f "$target" ]]; then
    count_pattern "$pattern" "$target"
  else
    count_pattern_in_dir "$pattern" "$target"
  fi
}

# Calculate adoption percentage
calc_adoption() {
  local shared="$1"
  local legacy="$2"
  local unknown="$3"
  
  local total=$((shared + legacy + unknown))
  if [[ "$total" -eq 0 ]]; then
    echo "N/A"
    return
  fi
  
  # Use bc for floating point, or awk if bc not available
  if command -v bc &> /dev/null; then
    local pct
    pct=$(echo "scale=1; $shared * 100 / $total" | bc)
    echo "${pct}%"
  else
    awk "BEGIN {printf \"%.1f%%\", $shared * 100 / $total}"
  fi
}

# ============================================================================
# AUDIT FUNCTIONS
# ============================================================================

# Audit a single file
audit_file() {
  local file="$1"
  
  if [[ ! -f "$file" ]]; then
    echo "Error: File not found: $file" >&2
    return 1
  fi
  
  local shared_ui
  shared_ui=$(count_shared_ui_cards "$file")
  local shared_ui_breakdown
  shared_ui_breakdown=$(count_shared_ui_cards_breakdown "$file")
  local legacy
  legacy=$(count_legacy_cards "$file")
  local legacy_breakdown
  legacy_breakdown=$(count_legacy_cards_breakdown "$file")
  local unknown
  unknown=$(count_unknown_cards "$file")
  local unknown_list
  unknown_list=$(list_unknown_cards "$file" | tr '\n' ', ' | sed 's/,$//')
  local raw_hex
  raw_hex=$(count_raw_hex "$file")
  local inline_styles
  inline_styles=$(count_inline_styles "$file")
  local adoption
  adoption=$(calc_adoption "$shared_ui" "$legacy" "$unknown")
  
  if [[ "$OUTPUT_FORMAT" == "json" ]]; then
    cat << EOF
{
  "file": "$file",
  "shared_ui_cards": $shared_ui,
  "shared_ui_breakdown": {$(echo "$shared_ui_breakdown" | sed 's/: /": /g; s/, /", "/g; s/^/"/')"},
  "legacy_cards": $legacy,
  "legacy_breakdown": "$legacy_breakdown",
  "unknown_cards": $unknown,
  "unknown_list": "$unknown_list",
  "raw_hex": $raw_hex,
  "inline_styles": $inline_styles,
  "adoption": "$adoption"
}
EOF
  else
    echo ""
    echo "File: $file"
    echo "  Shared-UI Cards: $shared_ui ($shared_ui_breakdown)"
    echo "  Legacy Cards: $legacy ($legacy_breakdown)"
    echo "  Unknown Cards: $unknown${unknown_list:+ ($unknown_list)}"
    echo "  Adoption: $adoption"
    echo "  Raw Hex: $raw_hex"
    echo "  Inline Styles: $inline_styles"
  fi
}

# Audit a directory
audit_directory() {
  local dir="$1"
  
  if [[ ! -d "$dir" ]]; then
    echo "Error: Directory not found: $dir" >&2
    return 1
  fi
  
  local shared_ui
  shared_ui=$(count_shared_ui_cards "$dir")
  local shared_ui_breakdown
  shared_ui_breakdown=$(count_shared_ui_cards_breakdown "$dir")
  local legacy
  legacy=$(count_legacy_cards "$dir")
  local legacy_breakdown
  legacy_breakdown=$(count_legacy_cards_breakdown "$dir")
  local unknown
  unknown=$(count_unknown_cards "$dir")
  local unknown_list
  unknown_list=$(list_unknown_cards "$dir" | tr '\n' ', ' | sed 's/,$//')
  local raw_hex
  raw_hex=$(count_raw_hex "$dir")
  local inline_styles
  inline_styles=$(count_inline_styles "$dir")
  local adoption
  adoption=$(calc_adoption "$shared_ui" "$legacy" "$unknown")
  
  if [[ "$OUTPUT_FORMAT" == "json" ]]; then
    cat << EOF
{
  "directory": "$dir",
  "shared_ui_cards": $shared_ui,
  "legacy_cards": $legacy,
  "unknown_cards": $unknown,
  "raw_hex": $raw_hex,
  "inline_styles": $inline_styles,
  "adoption": "$adoption"
}
EOF
  else
    echo ""
    echo "Directory: $dir"
    echo "  Shared-UI Cards: $shared_ui ($shared_ui_breakdown)"
    echo "  Legacy Cards: $legacy ($legacy_breakdown)"
    echo "  Unknown Cards: $unknown${unknown_list:+ ($unknown_list)}"
    echo "  Adoption: $adoption"
    echo "  Raw Hex: $raw_hex"
    echo "  Inline Styles: $inline_styles"
  fi
}

# Full audit of all target directories
audit_all() {
  local total_shared_ui=0
  local total_legacy=0
  local total_unknown=0
  local total_raw_hex=0
  local total_inline_styles=0
  local files_scanned=0
  
  if [[ "$OUTPUT_FORMAT" != "json" ]]; then
    echo "================================================================================"
    echo "Phase 2 Audit Report"
    echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "Commit: $(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"
    echo "================================================================================"
    echo ""
    echo "=== Per-Directory Analysis ==="
  fi
  
  local json_dirs=""
  
  for dir in "${SCAN_DIRS[@]}"; do
    if [[ -d "$dir" ]]; then
      local shared_ui
      shared_ui=$(count_shared_ui_cards "$dir")
      local legacy
      legacy=$(count_legacy_cards "$dir")
      local unknown
      unknown=$(count_unknown_cards "$dir")
      local raw_hex
      raw_hex=$(count_raw_hex "$dir")
      local inline_styles
      inline_styles=$(count_inline_styles "$dir")
      local adoption
      adoption=$(calc_adoption "$shared_ui" "$legacy" "$unknown")
      
      total_shared_ui=$((total_shared_ui + shared_ui))
      total_legacy=$((total_legacy + legacy))
      total_unknown=$((total_unknown + unknown))
      total_raw_hex=$((total_raw_hex + raw_hex))
      total_inline_styles=$((total_inline_styles + inline_styles))
      
      # Count files
      local exclude_args
      local include_args
      exclude_args=$(build_exclude_args)
      include_args=$(build_include_args)
      # shellcheck disable=SC2086
      local dir_files
      dir_files=$({ find "$dir" -type f \( -name "*.tsx" -o -name "*.jsx" -o -name "*.ts" -o -name "*.js" \) \
        ! -name "*.stories.*" ! -name "*.test.*" ! -name "*.spec.*" \
        ! -path "*/__tests__/*" ! -path "*/__mocks__/*" ! -path "*/node_modules/*" 2>/dev/null || true; } | wc -l)
      files_scanned=$((files_scanned + dir_files))
      
      if [[ "$OUTPUT_FORMAT" == "json" ]]; then
        if [[ -n "$json_dirs" ]]; then
          json_dirs="$json_dirs,"
        fi
        json_dirs="$json_dirs
    {
      \"directory\": \"$dir\",
      \"shared_ui_cards\": $shared_ui,
      \"legacy_cards\": $legacy,
      \"unknown_cards\": $unknown,
      \"raw_hex\": $raw_hex,
      \"inline_styles\": $inline_styles,
      \"adoption\": \"$adoption\",
      \"files\": $dir_files
    }"
      else
        echo ""
        echo "Directory: $dir"
        echo "  Files: $dir_files"
        echo "  Shared-UI Cards: $shared_ui"
        echo "  Legacy Cards: $legacy"
        echo "  Unknown Cards: $unknown"
        echo "  Adoption: $adoption"
        echo "  Raw Hex: $raw_hex"
        echo "  Inline Styles: $inline_styles"
      fi
    else
      if [[ "$OUTPUT_FORMAT" != "json" ]]; then
        echo ""
        echo "Directory: $dir (NOT FOUND)"
      fi
    fi
  done
  
  # Calculate overall adoption
  local overall_adoption
  overall_adoption=$(calc_adoption "$total_shared_ui" "$total_legacy" "$total_unknown")
  
  # List all unknown cards
  local all_unknown_list=""
  for dir in "${SCAN_DIRS[@]}"; do
    if [[ -d "$dir" ]]; then
      local dir_unknown
      dir_unknown=$(list_unknown_cards "$dir")
      if [[ -n "$dir_unknown" ]]; then
        if [[ -n "$all_unknown_list" ]]; then
          all_unknown_list="$all_unknown_list"$'\n'"$dir_unknown"
        else
          all_unknown_list="$dir_unknown"
        fi
      fi
    fi
  done
  all_unknown_list=$(echo "$all_unknown_list" | sort -u | tr '\n' ', ' | sed 's/,$//')
  
  if [[ "$OUTPUT_FORMAT" == "json" ]]; then
    cat << EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "commit": "$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')",
  "directories": [$json_dirs
  ],
  "summary": {
    "total_files_scanned": $files_scanned,
    "total_shared_ui_cards": $total_shared_ui,
    "total_legacy_cards": $total_legacy,
    "total_unknown_cards": $total_unknown,
    "unknown_card_list": "$all_unknown_list",
    "overall_adoption": "$overall_adoption",
    "total_raw_hex": $total_raw_hex,
    "total_inline_styles": $total_inline_styles
  }
}
EOF
  else
    echo ""
    echo "=== Summary ==="
    echo ""
    echo "Total Files Scanned: $files_scanned"
    echo "Total Shared-UI Cards: $total_shared_ui"
    echo "Total Legacy Cards: $total_legacy"
    echo "Total Unknown Cards: $total_unknown${all_unknown_list:+ ($all_unknown_list)}"
    echo "Overall Adoption: $overall_adoption"
    echo "Total Raw Hex: $total_raw_hex"
    echo "Total Inline Styles: $total_inline_styles"
    
    # Compare with baseline if exists
    if [[ -f "$BASELINE_FILE" ]]; then
      echo ""
      echo "=== Baseline Comparison ==="
      echo ""
      
      local baseline_raw_hex
      local baseline_inline_styles
      local baseline_shared_ui
      local baseline_legacy
      
      if command -v jq &> /dev/null; then
        baseline_raw_hex=$(jq -r '.summary.total_raw_hex // 0' "$BASELINE_FILE" 2>/dev/null || echo "0")
        baseline_inline_styles=$(jq -r '.summary.total_inline_styles // 0' "$BASELINE_FILE" 2>/dev/null || echo "0")
        baseline_shared_ui=$(jq -r '.summary.total_shared_ui_cards // 0' "$BASELINE_FILE" 2>/dev/null || echo "0")
        baseline_legacy=$(jq -r '.summary.total_legacy_cards // 0' "$BASELINE_FILE" 2>/dev/null || echo "0")
      else
        baseline_raw_hex=$({ grep -o '"total_raw_hex": *[0-9]*' "$BASELINE_FILE" 2>/dev/null || true; } | grep -o '[0-9]*' || echo "0")
        baseline_inline_styles=$({ grep -o '"total_inline_styles": *[0-9]*' "$BASELINE_FILE" 2>/dev/null || true; } | grep -o '[0-9]*' || echo "0")
        baseline_shared_ui=$({ grep -o '"total_shared_ui_cards": *[0-9]*' "$BASELINE_FILE" 2>/dev/null || true; } | grep -o '[0-9]*' || echo "0")
        baseline_legacy=$({ grep -o '"total_legacy_cards": *[0-9]*' "$BASELINE_FILE" 2>/dev/null || true; } | grep -o '[0-9]*' || echo "0")
      fi
      
      local raw_hex_delta=$((total_raw_hex - baseline_raw_hex))
      local inline_styles_delta=$((total_inline_styles - baseline_inline_styles))
      local shared_ui_delta=$((total_shared_ui - baseline_shared_ui))
      local legacy_delta=$((total_legacy - baseline_legacy))
      
      printf "| %-20s | %-10s | %-10s | %-10s | %-6s |\n" "Metric" "Baseline" "Current" "Delta" "Status"
      printf "|%-22s|%-12s|%-12s|%-12s|%-8s|\n" "----------------------" "------------" "------------" "------------" "--------"
      
      local raw_hex_status="PASS"
      if [[ "$raw_hex_delta" -gt 0 ]]; then raw_hex_status="FAIL"; fi
      printf "| %-20s | %-10s | %-10s | %+10d | %-6s |\n" "Raw Hex" "$baseline_raw_hex" "$total_raw_hex" "$raw_hex_delta" "$raw_hex_status"
      
      local inline_styles_status="PASS"
      if [[ "$inline_styles_delta" -gt 0 ]]; then inline_styles_status="FAIL"; fi
      printf "| %-20s | %-10s | %-10s | %+10d | %-6s |\n" "Inline Styles" "$baseline_inline_styles" "$total_inline_styles" "$inline_styles_delta" "$inline_styles_status"
      
      local shared_ui_status="PASS"
      if [[ "$shared_ui_delta" -lt 0 ]]; then shared_ui_status="WARN"; fi
      printf "| %-20s | %-10s | %-10s | %+10d | %-6s |\n" "Shared-UI Cards" "$baseline_shared_ui" "$total_shared_ui" "$shared_ui_delta" "$shared_ui_status"
      
      local legacy_status="PASS"
      if [[ "$legacy_delta" -gt 0 ]]; then legacy_status="WARN"; fi
      printf "| %-20s | %-10s | %-10s | %+10d | %-6s |\n" "Legacy Cards" "$baseline_legacy" "$total_legacy" "$legacy_delta" "$legacy_status"
    fi
  fi
  
  # Update baseline if requested
  if [[ "$UPDATE_BASELINE" == true ]]; then
    # Re-run with JSON output to save baseline
    OUTPUT_FORMAT="json"
    audit_all > "$BASELINE_FILE"
    OUTPUT_FORMAT="text"
    echo ""
    echo "Baseline updated: $BASELINE_FILE"
  fi
}

# ============================================================================
# MAIN
# ============================================================================

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --file)
      SINGLE_FILE="$2"
      shift 2
      ;;
    --dir)
      SINGLE_DIR="$2"
      shift 2
      ;;
    --json)
      OUTPUT_FORMAT="json"
      shift
      ;;
    --compare)
      COMPARE_FILE="$2"
      BASELINE_FILE="$2"
      shift 2
      ;;
    --update-baseline)
      UPDATE_BASELINE=true
      shift
      ;;
    --help|-h)
      print_help
      exit 0
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

# Run appropriate audit
if [[ -n "$SINGLE_FILE" ]]; then
  audit_file "$SINGLE_FILE"
elif [[ -n "$SINGLE_DIR" ]]; then
  audit_directory "$SINGLE_DIR"
else
  audit_all
fi
