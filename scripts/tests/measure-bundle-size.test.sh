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

# Floating point comparison helper
# Uses bc if available, falls back to awk (consistent with production code)
# Arguments:
#   $1 - first value (a)
#   $2 - operator: "gt" (>), "ge" (>=), "lt" (<), "le" (<=), "eq" (==)
#   $3 - second value (b)
# Returns:
#   0 if comparison is true, 1 if false
float_compare() {
  local a="$1"
  local op="$2"
  local b="$3"
  
  # Normalize values (handle bc returning .X format)
  a=$(echo "$a" | sed 's/^\./0./')
  b=$(echo "$b" | sed 's/^\./0./')
  
  local expr
  case "$op" in
    gt) expr="$a > $b" ;;
    ge) expr="$a >= $b" ;;
    lt) expr="$a < $b" ;;
    le) expr="$a <= $b" ;;
    eq) expr="$a == $b" ;;
    *) echo "Unknown operator: $op" >&2; return 1 ;;
  esac
  
  local result
  if command -v bc &> /dev/null && echo "1+1" | bc &> /dev/null; then
    # Use bc for comparison
    result=$(echo "$expr" | bc -l 2>/dev/null | tr -d '[:space:]')
  else
    # Fallback to awk
    result=$(awk -v a="$a" -v b="$b" "BEGIN {print ($expr)}")
  fi
  
  if [[ "$result" == "1" ]]; then
    return 0
  else
    return 1
  fi
}

# Floating point range check helper
# Uses bc if available, falls back to awk (consistent with production code)
# Arguments:
#   $1 - value to check
#   $2 - minimum (inclusive)
#   $3 - maximum (inclusive)
# Returns:
#   0 if value is in range [min, max], 1 if not
float_in_range() {
  local val="$1"
  local min="$2"
  local max="$3"
  
  # Normalize values (handle bc returning .X format)
  val=$(echo "$val" | sed 's/^\./0./')
  min=$(echo "$min" | sed 's/^\./0./')
  max=$(echo "$max" | sed 's/^\./0./')
  
  local result
  if command -v bc &> /dev/null && echo "1+1" | bc &> /dev/null; then
    # Use bc for comparison
    result=$(echo "$val >= $min && $val <= $max" | bc -l 2>/dev/null | tr -d '[:space:]')
  else
    # Fallback to awk
    result=$(awk -v v="$val" -v mn="$min" -v mx="$max" "BEGIN {print (v >= mn && v <= mx)}")
  fi
  
  if [[ "$result" == "1" ]]; then
    return 0
  else
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
# SOURCE THE SHARED LIBRARY
# ============================================================================

# Determine script directory for sourcing library
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB_DIR="$(cd "$SCRIPT_DIR/../lib" && pwd)"

# Source the shared library directly - this is the same library used by
# measure-bundle-size.sh, ensuring test consistency with production code.
# See scripts/tests/BUNDLE_SIZE_TESTING.md for architecture details.
source_library() {
  source "$LIB_DIR/bundle-size-lib.sh"
}

# ============================================================================
# TEST: calculate_gzip_sizes_direct()
# ============================================================================

test_gzip_direct_valid_directory() {
  source_library
  
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
  
  # Total should be greater than 0
  if float_compare "$total" gt 0; then
    return 0
  else
    echo "Expected total > 0, got $total"
    return 1
  fi
}

test_gzip_direct_missing_directory() {
  source_library
  
  local result
  result=$(calculate_gzip_sizes_direct "$TEST_DIR/nonexistent" "js")
  
  assert_equals "0 0" "$result" "Missing directory should return 0 0"
}

test_gzip_direct_empty_directory() {
  source_library
  
  # Create empty assets directory
  mkdir -p "$TEST_DIR/empty/assets"
  
  local result
  result=$(calculate_gzip_sizes_direct "$TEST_DIR/empty" "js")
  
  assert_equals "0 0" "$result" "Empty directory should return 0 0"
}

test_gzip_direct_no_matching_files() {
  source_library
  
  # Create assets directory with only CSS files
  mkdir -p "$TEST_DIR/css-only/assets"
  echo "body { color: red; }" > "$TEST_DIR/css-only/assets/style.css"
  
  local result
  result=$(calculate_gzip_sizes_direct "$TEST_DIR/css-only" "js")
  
  assert_equals "0 0" "$result" "No matching files should return 0 0"
}

test_gzip_direct_multiple_files() {
  source_library
  
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
  
  # Total should be greater than largest (multiple files)
  # largest > 0 ensures we're testing meaningful values
  if float_compare "$largest" gt 0 && float_compare "$total" gt "$largest"; then
    return 0
  else
    echo "Expected largest > 0 and total > largest, got total=$total, largest=$largest"
    return 1
  fi
}

test_gzip_direct_css_files() {
  source_library
  
  # Create CSS files
  mkdir -p "$TEST_DIR/css/assets"
  echo "body { color: red; margin: 0; padding: 0; }" > "$TEST_DIR/css/assets/style.css"
  echo ".header { background: blue; }" > "$TEST_DIR/css/assets/header.css"
  
  local result
  result=$(calculate_gzip_sizes_direct "$TEST_DIR/css" "css")
  
  local total
  total=$(echo "$result" | cut -d' ' -f1)
  
  if float_compare "$total" gt 0; then
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
  source_library
  
  local vite_output="dist/assets/index-abc123.js   245.67 kB │ gzip:  78.23 kB"
  
  local result
  result=$(parse_vite_output "$vite_output" "js")
  
  local total
  total=$(echo "$result" | cut -d' ' -f1)
  
  # Should be approximately 78.2
  if float_in_range "$total" 78 79; then
    return 0
  else
    echo "Expected ~78.2, got $total"
    return 1
  fi
}

test_parse_vite_multiple_js() {
  source_library
  
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
  if float_in_range "$total" 123 124 && float_in_range "$largest" 78 79; then
    return 0
  else
    echo "Expected total ~123.7 and largest ~78.2, got total=$total, largest=$largest"
    return 1
  fi
}

test_parse_vite_css() {
  source_library
  
  local vite_output="dist/assets/style-abc123.css   45.00 kB │ gzip:  12.50 kB"
  
  local result
  result=$(parse_vite_output "$vite_output" "css")
  
  local total
  total=$(echo "$result" | cut -d' ' -f1)
  
  if float_in_range "$total" 12 13; then
    return 0
  else
    echo "Expected ~12.5, got $total"
    return 1
  fi
}

test_parse_vite_no_gzip_info() {
  source_library
  
  local vite_output="dist/assets/index-abc123.js   245.67 kB"
  
  local result
  result=$(parse_vite_output "$vite_output" "js")
  
  assert_equals "0 0" "$result" "No gzip info should return 0 0"
}

test_parse_vite_empty_output() {
  source_library
  
  local vite_output=""
  
  local result
  result=$(parse_vite_output "$vite_output" "js")
  
  assert_equals "0 0" "$result" "Empty output should return 0 0"
}

test_parse_vite_mixed_content() {
  source_library
  
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
  
  if float_in_range "$js_total" 78 79 && float_in_range "$css_total" 12 13; then
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
