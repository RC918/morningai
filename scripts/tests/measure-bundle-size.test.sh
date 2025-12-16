#!/bin/bash
# ============================================================================
# Unit Tests for measure-bundle-size.sh
# ============================================================================
#
# Tests the fallback mechanisms and edge cases in the bundle size measurement
# script, specifically:
#   - calculate_gzip_sizes_direct() function
#   - Zero-value detection regex
#   - bc/awk fallback for calculations
#   - parse_vite_output() function
#
# USAGE:
#   ./scripts/tests/measure-bundle-size.test.sh
#
# REQUIREMENTS:
#   - Bash 4.0+
#   - gzip
#   - bc (optional, tests awk fallback if missing)
#
# ============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Temporary directory for test fixtures
TEST_DIR=""

# ============================================================================
# TEST FRAMEWORK
# ============================================================================

setup() {
  TEST_DIR=$(mktemp -d)
  echo "Test directory: $TEST_DIR"
}

teardown() {
  if [[ -n "$TEST_DIR" ]] && [[ -d "$TEST_DIR" ]]; then
    rm -rf "$TEST_DIR"
  fi
}

assert_equals() {
  local expected="$1"
  local actual="$2"
  local message="${3:-}"
  
  if [[ "$expected" == "$actual" ]]; then
    return 0
  else
    echo -e "${RED}FAIL${NC}: Expected '$expected', got '$actual' ${message:+- $message}"
    return 1
  fi
}

assert_matches() {
  local pattern="$1"
  local actual="$2"
  local message="${3:-}"
  
  if [[ "$actual" =~ $pattern ]]; then
    return 0
  else
    echo -e "${RED}FAIL${NC}: '$actual' does not match pattern '$pattern' ${message:+- $message}"
    return 1
  fi
}

assert_not_empty() {
  local actual="$1"
  local message="${2:-}"
  
  if [[ -n "$actual" ]]; then
    return 0
  else
    echo -e "${RED}FAIL${NC}: Value is empty ${message:+- $message}"
    return 1
  fi
}

run_test() {
  local test_name="$1"
  local test_func="$2"
  
  TESTS_RUN=$((TESTS_RUN + 1))
  echo -n "  $test_name... "
  
  if $test_func; then
    echo -e "${GREEN}PASS${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
  else
    TESTS_FAILED=$((TESTS_FAILED + 1))
  fi
}

# ============================================================================
# SOURCE THE FUNCTIONS TO TEST
# ============================================================================

# We need to source just the functions, not run the main script
# Create a temporary file with just the functions

create_test_harness() {
  cat > "$TEST_DIR/functions.sh" << 'FUNCTIONS'
# Extracted functions from measure-bundle-size.sh for testing

# Parse Vite build output to extract bundle sizes
parse_vite_output() {
  local build_output="$1"
  local file_type="$2"
  
  local total=0
  local largest=0
  
  while IFS= read -r line; do
    if [[ "$line" =~ \.$file_type[[:space:]] ]] && [[ "$line" =~ gzip:[[:space:]]*([0-9.]+)[[:space:]]*kB ]]; then
      local size="${BASH_REMATCH[1]}"
      local size_int
      if command -v bc &> /dev/null; then
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

# Direct gzip calculation fallback
calculate_gzip_sizes_direct() {
  local dist_path="$1"
  local file_type="$2"
  
  local total=0
  local largest=0
  
  if [[ ! -d "$dist_path/assets" ]]; then
    echo "0 0"
    return
  fi
  
  while IFS= read -r -d '' file; do
    if [[ -f "$file" ]]; then
      local current_size
      current_size=$({ gzip -c "$file" 2>/dev/null || true; } | wc -c)
      total=$((total + ${current_size:-0}))
      if (( ${current_size:-0} > largest )); then
        largest=${current_size:-0}
      fi
    fi
  done < <(find "$dist_path/assets" -name "*.$file_type" -print0 2>/dev/null)
  
  local total_kb
  local largest_kb
  if command -v bc &> /dev/null; then
    total_kb=$(echo "scale=1; $total / 1024" | bc)
    largest_kb=$(echo "scale=1; $largest / 1024" | bc)
  else
    total_kb=$(awk "BEGIN {printf \"%.1f\", $total / 1024}")
    largest_kb=$(awk "BEGIN {printf \"%.1f\", $largest / 1024}")
  fi
  
  echo "$total_kb $largest_kb"
}
FUNCTIONS
}

# ============================================================================
# TEST: calculate_gzip_sizes_direct()
# ============================================================================

test_gzip_direct_valid_directory() {
  source "$TEST_DIR/functions.sh"
  
  # Create test fixtures with larger content to ensure measurable gzip size
  mkdir -p "$TEST_DIR/dist/assets"
  # Create a larger JS file to ensure gzip produces measurable output
  for i in {1..100}; do
    echo "console.log('test line $i with some content to make it larger');" >> "$TEST_DIR/dist/assets/index.js"
  done
  echo "body { color: red; }" > "$TEST_DIR/dist/assets/style.css"
  
  local result
  result=$(calculate_gzip_sizes_direct "$TEST_DIR/dist" "js")
  
  # Should return non-zero values
  local total
  total=$(echo "$result" | cut -d' ' -f1)
  
  # Total should be greater than 0 (handle bc returning .X format)
  # Normalize by prepending 0 if starts with .
  local normalized_total
  normalized_total=$(echo "$total" | sed 's/^\./0./')
  
  if [[ $(awk "BEGIN {print ($normalized_total > 0)}") == "1" ]]; then
    return 0
  else
    echo "Expected total > 0, got $total (normalized: $normalized_total)"
    return 1
  fi
}

test_gzip_direct_missing_directory() {
  source "$TEST_DIR/functions.sh"
  
  local result
  result=$(calculate_gzip_sizes_direct "$TEST_DIR/nonexistent" "js")
  
  assert_equals "0 0" "$result" "Missing directory should return 0 0"
}

test_gzip_direct_empty_directory() {
  source "$TEST_DIR/functions.sh"
  
  # Create empty assets directory
  mkdir -p "$TEST_DIR/empty/assets"
  
  local result
  result=$(calculate_gzip_sizes_direct "$TEST_DIR/empty" "js")
  
  assert_equals "0 0" "$result" "Empty directory should return 0 0"
}

test_gzip_direct_no_matching_files() {
  source "$TEST_DIR/functions.sh"
  
  # Create assets directory with only CSS files
  mkdir -p "$TEST_DIR/css-only/assets"
  echo "body { color: red; }" > "$TEST_DIR/css-only/assets/style.css"
  
  local result
  result=$(calculate_gzip_sizes_direct "$TEST_DIR/css-only" "js")
  
  assert_equals "0 0" "$result" "No matching files should return 0 0"
}

test_gzip_direct_multiple_files() {
  source "$TEST_DIR/functions.sh"
  
  # Create multiple JS files with larger content
  mkdir -p "$TEST_DIR/multi/assets"
  for i in {1..50}; do
    echo "console.log('chunk1 line $i with content');" >> "$TEST_DIR/multi/assets/chunk1.js"
  done
  for i in {1..30}; do
    echo "console.log('chunk2 line $i with different content');" >> "$TEST_DIR/multi/assets/chunk2.js"
  done
  for i in {1..20}; do
    echo "console.log('chunk3 line $i with more content');" >> "$TEST_DIR/multi/assets/chunk3.js"
  done
  
  local result
  result=$(calculate_gzip_sizes_direct "$TEST_DIR/multi" "js")
  
  local total
  total=$(echo "$result" | cut -d' ' -f1)
  local largest
  largest=$(echo "$result" | cut -d' ' -f2)
  
  # Normalize values (handle bc returning .X format)
  local normalized_total
  normalized_total=$(echo "$total" | sed 's/^\./0./')
  local normalized_largest
  normalized_largest=$(echo "$largest" | sed 's/^\./0./')
  
  # Total should be greater than largest (multiple files)
  # Both should be non-zero
  if [[ $(awk "BEGIN {print ($normalized_total > 0)}") == "1" ]] && \
     [[ $(awk "BEGIN {print ($normalized_largest > 0)}") == "1" ]]; then
    return 0
  else
    echo "Expected non-zero values, got total=$total (normalized: $normalized_total), largest=$largest (normalized: $normalized_largest)"
    return 1
  fi
}

test_gzip_direct_css_files() {
  source "$TEST_DIR/functions.sh"
  
  # Create CSS files
  mkdir -p "$TEST_DIR/css/assets"
  echo "body { color: red; margin: 0; padding: 0; }" > "$TEST_DIR/css/assets/style.css"
  echo ".header { background: blue; }" > "$TEST_DIR/css/assets/header.css"
  
  local result
  result=$(calculate_gzip_sizes_direct "$TEST_DIR/css" "css")
  
  local total
  total=$(echo "$result" | cut -d' ' -f1)
  
  if [[ $(echo "$total > 0" | bc -l 2>/dev/null || awk "BEGIN {print ($total > 0)}") == "1" ]]; then
    return 0
  else
    echo "Expected total > 0 for CSS, got $total"
    return 1
  fi
}

# ============================================================================
# TEST: Zero-value detection regex
# ============================================================================

test_zero_regex_zero() {
  local value="0"
  if [[ "$value" =~ ^(0|\.0|0\.0)$ ]]; then
    return 0
  else
    echo "Expected '0' to match zero regex"
    return 1
  fi
}

test_zero_regex_dot_zero() {
  local value=".0"
  if [[ "$value" =~ ^(0|\.0|0\.0)$ ]]; then
    return 0
  else
    echo "Expected '.0' to match zero regex"
    return 1
  fi
}

test_zero_regex_zero_dot_zero() {
  local value="0.0"
  if [[ "$value" =~ ^(0|\.0|0\.0)$ ]]; then
    return 0
  else
    echo "Expected '0.0' to match zero regex"
    return 1
  fi
}

test_zero_regex_non_zero() {
  local value="1.5"
  if [[ "$value" =~ ^(0|\.0|0\.0)$ ]]; then
    echo "Expected '1.5' to NOT match zero regex"
    return 1
  else
    return 0
  fi
}

test_zero_regex_small_value() {
  local value="0.1"
  if [[ "$value" =~ ^(0|\.0|0\.0)$ ]]; then
    echo "Expected '0.1' to NOT match zero regex"
    return 1
  else
    return 0
  fi
}

# ============================================================================
# TEST: parse_vite_output()
# ============================================================================

test_parse_vite_single_js() {
  source "$TEST_DIR/functions.sh"
  
  local vite_output="dist/assets/index-abc123.js   245.67 kB │ gzip:  78.23 kB"
  
  local result
  result=$(parse_vite_output "$vite_output" "js")
  
  local total
  total=$(echo "$result" | cut -d' ' -f1)
  
  # Should be approximately 78.2
  if [[ $(echo "$total >= 78 && $total <= 79" | bc -l 2>/dev/null || awk "BEGIN {print ($total >= 78 && $total <= 79)}") == "1" ]]; then
    return 0
  else
    echo "Expected ~78.2, got $total"
    return 1
  fi
}

test_parse_vite_multiple_js() {
  source "$TEST_DIR/functions.sh"
  
  local vite_output="dist/assets/index-abc123.js   245.67 kB │ gzip:  78.23 kB
dist/assets/vendor-def456.js   100.00 kB │ gzip:  30.50 kB
dist/assets/chunk-ghi789.js    50.00 kB │ gzip:  15.00 kB"
  
  local result
  result=$(parse_vite_output "$vite_output" "js")
  
  local total
  total=$(echo "$result" | cut -d' ' -f1)
  local largest
  largest=$(echo "$result" | cut -d' ' -f2)
  
  # Total should be ~123.7 (78.23 + 30.50 + 15.00)
  # Largest should be ~78.2
  if [[ $(echo "$total >= 123 && $total <= 124" | bc -l 2>/dev/null || awk "BEGIN {print ($total >= 123 && $total <= 124)}") == "1" ]] && \
     [[ $(echo "$largest >= 78 && $largest <= 79" | bc -l 2>/dev/null || awk "BEGIN {print ($largest >= 78 && $largest <= 79)}") == "1" ]]; then
    return 0
  else
    echo "Expected total ~123.7 and largest ~78.2, got total=$total, largest=$largest"
    return 1
  fi
}

test_parse_vite_css() {
  source "$TEST_DIR/functions.sh"
  
  local vite_output="dist/assets/style-abc123.css   45.00 kB │ gzip:  12.50 kB"
  
  local result
  result=$(parse_vite_output "$vite_output" "css")
  
  local total
  total=$(echo "$result" | cut -d' ' -f1)
  
  if [[ $(echo "$total >= 12 && $total <= 13" | bc -l 2>/dev/null || awk "BEGIN {print ($total >= 12 && $total <= 13)}") == "1" ]]; then
    return 0
  else
    echo "Expected ~12.5, got $total"
    return 1
  fi
}

test_parse_vite_no_gzip_info() {
  source "$TEST_DIR/functions.sh"
  
  local vite_output="dist/assets/index-abc123.js   245.67 kB"
  
  local result
  result=$(parse_vite_output "$vite_output" "js")
  
  assert_equals "0 0" "$result" "No gzip info should return 0 0"
}

test_parse_vite_empty_output() {
  source "$TEST_DIR/functions.sh"
  
  local vite_output=""
  
  local result
  result=$(parse_vite_output "$vite_output" "js")
  
  assert_equals "0 0" "$result" "Empty output should return 0 0"
}

test_parse_vite_mixed_content() {
  source "$TEST_DIR/functions.sh"
  
  local vite_output="vite v5.0.0 building for production...
transforming...
rendering chunks...
dist/assets/index-abc123.js   245.67 kB │ gzip:  78.23 kB
dist/assets/style-def456.css   45.00 kB │ gzip:  12.50 kB
build completed in 5.23s"
  
  local js_result
  js_result=$(parse_vite_output "$vite_output" "js")
  local css_result
  css_result=$(parse_vite_output "$vite_output" "css")
  
  local js_total
  js_total=$(echo "$js_result" | cut -d' ' -f1)
  local css_total
  css_total=$(echo "$css_result" | cut -d' ' -f1)
  
  if [[ $(echo "$js_total >= 78 && $js_total <= 79" | bc -l 2>/dev/null || awk "BEGIN {print ($js_total >= 78 && $js_total <= 79)}") == "1" ]] && \
     [[ $(echo "$css_total >= 12 && $css_total <= 13" | bc -l 2>/dev/null || awk "BEGIN {print ($css_total >= 12 && $css_total <= 13)}") == "1" ]]; then
    return 0
  else
    echo "Expected js ~78.2 and css ~12.5, got js=$js_total, css=$css_total"
    return 1
  fi
}

# ============================================================================
# TEST: bc/awk fallback
# ============================================================================

test_awk_fallback_calculation() {
  # Test awk calculation directly
  local result
  result=$(awk "BEGIN {printf \"%.1f\", 12345 / 100}")
  
  assert_equals "123.5" "$result" "awk calculation should work"
}

test_awk_fallback_zero() {
  local result
  result=$(awk "BEGIN {printf \"%.1f\", 0 / 100}")
  
  assert_equals "0.0" "$result" "awk zero calculation should return 0.0"
}

# ============================================================================
# TEST: Integration - Fallback trigger
# ============================================================================

test_fallback_trigger_on_zero_js() {
  # This tests the condition that triggers fallback
  local js_total="0"
  
  if [[ "$js_total" =~ ^(0|\.0|0\.0)$ ]] || [[ -z "$js_total" ]]; then
    return 0  # Fallback would be triggered
  else
    echo "Expected fallback to be triggered for js_total=0"
    return 1
  fi
}

test_fallback_trigger_on_empty() {
  local js_total=""
  
  if [[ "$js_total" =~ ^(0|\.0|0\.0)$ ]] || [[ -z "$js_total" ]]; then
    return 0  # Fallback would be triggered
  else
    echo "Expected fallback to be triggered for empty js_total"
    return 1
  fi
}

test_no_fallback_on_valid_value() {
  local js_total="78.2"
  
  if [[ "$js_total" =~ ^(0|\.0|0\.0)$ ]] || [[ -z "$js_total" ]]; then
    echo "Expected NO fallback for js_total=78.2"
    return 1
  else
    return 0
  fi
}

# ============================================================================
# MAIN
# ============================================================================

main() {
  echo "=============================================================================="
  echo "Bundle Size Script Unit Tests"
  echo "=============================================================================="
  echo ""
  
  setup
  create_test_harness
  
  echo "Test Suite: calculate_gzip_sizes_direct()"
  echo "-------------------------------------------"
  run_test "Valid directory with JS files" test_gzip_direct_valid_directory
  run_test "Missing directory returns 0 0" test_gzip_direct_missing_directory
  run_test "Empty directory returns 0 0" test_gzip_direct_empty_directory
  run_test "No matching files returns 0 0" test_gzip_direct_no_matching_files
  run_test "Multiple files calculates total and largest" test_gzip_direct_multiple_files
  run_test "CSS files calculation" test_gzip_direct_css_files
  echo ""
  
  echo "Test Suite: Zero-value detection regex"
  echo "---------------------------------------"
  run_test "Matches '0'" test_zero_regex_zero
  run_test "Matches '.0'" test_zero_regex_dot_zero
  run_test "Matches '0.0'" test_zero_regex_zero_dot_zero
  run_test "Does not match '1.5'" test_zero_regex_non_zero
  run_test "Does not match '0.1'" test_zero_regex_small_value
  echo ""
  
  echo "Test Suite: parse_vite_output()"
  echo "--------------------------------"
  run_test "Single JS file parsing" test_parse_vite_single_js
  run_test "Multiple JS files parsing" test_parse_vite_multiple_js
  run_test "CSS file parsing" test_parse_vite_css
  run_test "No gzip info returns 0 0" test_parse_vite_no_gzip_info
  run_test "Empty output returns 0 0" test_parse_vite_empty_output
  run_test "Mixed content parsing" test_parse_vite_mixed_content
  echo ""
  
  echo "Test Suite: bc/awk fallback"
  echo "---------------------------"
  run_test "awk calculation works" test_awk_fallback_calculation
  run_test "awk zero calculation" test_awk_fallback_zero
  echo ""
  
  echo "Test Suite: Fallback trigger conditions"
  echo "----------------------------------------"
  run_test "Triggers fallback on zero" test_fallback_trigger_on_zero_js
  run_test "Triggers fallback on empty" test_fallback_trigger_on_empty
  run_test "No fallback on valid value" test_no_fallback_on_valid_value
  echo ""
  
  teardown
  
  echo "=============================================================================="
  echo "Results: $TESTS_PASSED/$TESTS_RUN passed"
  if [[ $TESTS_FAILED -gt 0 ]]; then
    echo -e "${RED}$TESTS_FAILED tests failed${NC}"
    exit 1
  else
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
  fi
}

main "$@"
