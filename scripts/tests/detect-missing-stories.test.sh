#!/bin/bash
# =============================================================================
# Missing Storybook Stories Detection Script Tests
# =============================================================================
#
# PURPOSE:
#   Unit tests for the missing Storybook stories detection script.
#
# USAGE:
#   ./scripts/tests/detect-missing-stories.test.sh
#
# RELATED:
#   - Issue #2512: Storybook scanning CI
#   - scripts/detect-missing-stories.sh: Main detection script
#
# =============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DETECT_SCRIPT="$REPO_ROOT/scripts/detect-missing-stories.sh"

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Temporary directory for test fixtures
TEST_TMP_DIR=""

# =============================================================================
# Test Framework
# =============================================================================

setup() {
  TEST_TMP_DIR=$(mktemp -d)
  mkdir -p "$TEST_TMP_DIR/components"
}

teardown() {
  if [[ -n "$TEST_TMP_DIR" && -d "$TEST_TMP_DIR" ]]; then
    rm -rf "$TEST_TMP_DIR"
  fi
}

run_test() {
  local test_name="$1"
  local test_func="$2"
  
  TESTS_RUN=$((TESTS_RUN + 1))
  
  echo -n "  Testing: $test_name... "
  
  setup
  
  if $test_func; then
    echo -e "${GREEN}PASS${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
  else
    echo -e "${RED}FAIL${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
  fi
  
  teardown
}

assert_exit_code() {
  local expected="$1"
  local actual="$2"
  
  if [[ "$expected" != "$actual" ]]; then
    echo "Expected exit code $expected, got $actual" >&2
    return 1
  fi
  return 0
}

assert_output_contains() {
  local output="$1"
  local expected="$2"
  
  if [[ "$output" != *"$expected"* ]]; then
    echo "Expected output to contain: $expected" >&2
    return 1
  fi
  return 0
}

assert_output_not_contains() {
  local output="$1"
  local unexpected="$2"
  
  if [[ "$output" == *"$unexpected"* ]]; then
    echo "Expected output NOT to contain: $unexpected" >&2
    return 1
  fi
  return 0
}

# =============================================================================
# Test Fixtures
# =============================================================================

create_component_with_story() {
  local dir="$1"
  local name="$2"
  
  cat > "$dir/$name.tsx" << 'EOF'
import React from 'react';

export function Component() {
  return <div>Hello</div>;
}
EOF
  
  cat > "$dir/$name.stories.tsx" << 'EOF'
import type { Meta, StoryObj } from '@storybook/react';
import { Component } from './component';

const meta: Meta<typeof Component> = {
  title: 'UI/Component',
  component: Component,
};

export default meta;
type Story = StoryObj<typeof Component>;

export const Default: Story = {};
EOF
}

create_component_without_story() {
  local dir="$1"
  local name="$2"
  
  cat > "$dir/$name.tsx" << 'EOF'
import React from 'react';

export function Component() {
  return <div>Hello</div>;
}
EOF
}

create_test_file() {
  local dir="$1"
  local name="$2"
  
  cat > "$dir/$name.test.tsx" << 'EOF'
import { render } from '@testing-library/react';
import { Component } from './component';

test('renders', () => {
  render(<Component />);
});
EOF
}

create_index_file() {
  local dir="$1"
  
  cat > "$dir/index.tsx" << 'EOF'
export * from './component';
EOF
}

create_hook_file() {
  local dir="$1"
  local name="$2"
  
  cat > "$dir/$name.tsx" << 'EOF'
import { useState } from 'react';

export function useCustomHook() {
  const [state, setState] = useState(null);
  return { state, setState };
}
EOF
}

create_allowlist_file() {
  local file="$1"
  local allowed_file="${2:-}"
  
  if [[ -n "$allowed_file" ]]; then
    cat > "$file" << EOF
{
  "allowed_files": ["$allowed_file"],
  "expires": "2025-12-31"
}
EOF
  else
    cat > "$file" << 'EOF'
{
  "allowed_files": [],
  "expires": "2025-12-31"
}
EOF
  fi
}

# =============================================================================
# Test Cases - Basic Detection
# =============================================================================

test_full_coverage() {
  create_component_with_story "$TEST_TMP_DIR/components" "button"
  
  local output
  output=$(bash "$DETECT_SCRIPT" --dir "$TEST_TMP_DIR/components" 2>&1) || true
  local exit_code=$?
  
  assert_exit_code 0 "$exit_code" && \
  assert_output_contains "$output" "Components missing stories: 0" && \
  assert_output_contains "$output" "All components have Storybook stories"
}

test_detects_missing_story() {
  create_component_without_story "$TEST_TMP_DIR/components" "button"
  
  local output
  output=$(bash "$DETECT_SCRIPT" --dir "$TEST_TMP_DIR/components" 2>&1) || true
  local exit_code=$?
  
  assert_exit_code 0 "$exit_code" && \
  assert_output_contains "$output" "Components missing stories: 1"
}

test_multiple_components() {
  create_component_with_story "$TEST_TMP_DIR/components" "button"
  create_component_without_story "$TEST_TMP_DIR/components" "card"
  create_component_without_story "$TEST_TMP_DIR/components" "input"
  
  local output
  output=$(bash "$DETECT_SCRIPT" --dir "$TEST_TMP_DIR/components" 2>&1) || true
  local exit_code=$?
  
  assert_exit_code 0 "$exit_code" && \
  assert_output_contains "$output" "Components scanned: 3" && \
  assert_output_contains "$output" "Components missing stories: 2"
}

test_strict_mode_fails_on_missing() {
  create_component_without_story "$TEST_TMP_DIR/components" "button"
  
  local output
  local exit_code
  output=$(bash "$DETECT_SCRIPT" --dir "$TEST_TMP_DIR/components" --strict 2>&1) && exit_code=0 || exit_code=$?
  
  assert_exit_code 1 "$exit_code" && \
  assert_output_contains "$output" "STRICT MODE"
}

test_strict_mode_passes_on_full_coverage() {
  create_component_with_story "$TEST_TMP_DIR/components" "button"
  
  local output
  output=$(bash "$DETECT_SCRIPT" --dir "$TEST_TMP_DIR/components" --strict 2>&1) || true
  local exit_code=$?
  
  assert_exit_code 0 "$exit_code" && \
  assert_output_contains "$output" "All components have Storybook stories"
}

# =============================================================================
# Test Cases - File Exclusions
# =============================================================================

test_excludes_test_files() {
  create_component_without_story "$TEST_TMP_DIR/components" "button"
  create_test_file "$TEST_TMP_DIR/components" "button"
  
  local output
  output=$(bash "$DETECT_SCRIPT" --dir "$TEST_TMP_DIR/components" 2>&1) || true
  local exit_code=$?
  
  assert_exit_code 0 "$exit_code" && \
  assert_output_contains "$output" "Components scanned: 1" && \
  assert_output_not_contains "$output" "button.test.tsx"
}

test_excludes_index_files() {
  create_component_without_story "$TEST_TMP_DIR/components" "button"
  create_index_file "$TEST_TMP_DIR/components"
  
  local output
  output=$(bash "$DETECT_SCRIPT" --dir "$TEST_TMP_DIR/components" 2>&1) || true
  local exit_code=$?
  
  assert_exit_code 0 "$exit_code" && \
  assert_output_contains "$output" "Components scanned: 1" && \
  assert_output_not_contains "$output" "index.tsx"
}

test_excludes_hook_files() {
  create_hook_file "$TEST_TMP_DIR/components" "use-custom"
  
  local output
  output=$(bash "$DETECT_SCRIPT" --dir "$TEST_TMP_DIR/components" 2>&1) || true
  local exit_code=$?
  
  assert_exit_code 0 "$exit_code" && \
  assert_output_contains "$output" "Components scanned: 0"
}

test_excludes_story_files_from_scan() {
  create_component_with_story "$TEST_TMP_DIR/components" "button"
  
  local output
  output=$(bash "$DETECT_SCRIPT" --dir "$TEST_TMP_DIR/components" 2>&1) || true
  local exit_code=$?
  
  assert_exit_code 0 "$exit_code" && \
  assert_output_contains "$output" "Components scanned: 1"
}

# =============================================================================
# Test Cases - Allowlist
# =============================================================================

test_allowlist_skips_allowed_files() {
  create_component_without_story "$TEST_TMP_DIR/components" "legacy-button"
  create_allowlist_file "$TEST_TMP_DIR/allowlist.json" "legacy-button.tsx"
  
  local output
  output=$(bash "$DETECT_SCRIPT" --dir "$TEST_TMP_DIR/components" --allowlist "$TEST_TMP_DIR/allowlist.json" 2>&1) || true
  local exit_code=$?
  
  assert_exit_code 0 "$exit_code" && \
  assert_output_contains "$output" "Components missing stories: 0"
}

test_allowlist_still_detects_non_allowed_files() {
  create_component_without_story "$TEST_TMP_DIR/components" "button"
  create_component_without_story "$TEST_TMP_DIR/components" "legacy-button"
  create_allowlist_file "$TEST_TMP_DIR/allowlist.json" "legacy-button.tsx"
  
  local output
  output=$(bash "$DETECT_SCRIPT" --dir "$TEST_TMP_DIR/components" --allowlist "$TEST_TMP_DIR/allowlist.json" 2>&1) || true
  local exit_code=$?
  
  assert_exit_code 0 "$exit_code" && \
  assert_output_contains "$output" "Components missing stories: 1"
}

# =============================================================================
# Test Cases - JSON Output
# =============================================================================

test_json_output_format() {
  create_component_with_story "$TEST_TMP_DIR/components" "button"
  
  local output
  output=$(bash "$DETECT_SCRIPT" --dir "$TEST_TMP_DIR/components" --json 2>&1) || true
  local exit_code=$?
  
  assert_exit_code 0 "$exit_code" && \
  assert_output_contains "$output" '"componentsScanned"' && \
  assert_output_contains "$output" '"componentsMissing"' && \
  assert_output_contains "$output" '"coveragePercent"'
}

# =============================================================================
# Test Cases - Edge Cases
# =============================================================================

test_empty_directory() {
  local output
  output=$(bash "$DETECT_SCRIPT" --dir "$TEST_TMP_DIR/components" 2>&1) || true
  local exit_code=$?
  
  assert_exit_code 0 "$exit_code" && \
  assert_output_contains "$output" "Components scanned: 0"
}

test_nonexistent_directory() {
  local output
  local exit_code
  output=$(bash "$DETECT_SCRIPT" --dir "$TEST_TMP_DIR/nonexistent" 2>&1) && exit_code=0 || exit_code=$?
  
  # Should fail with error
  assert_exit_code 1 "$exit_code"
}

test_help_option() {
  local output
  output=$(bash "$DETECT_SCRIPT" --help 2>&1) || true
  local exit_code=$?
  
  assert_exit_code 0 "$exit_code" && \
  assert_output_contains "$output" "USAGE" && \
  assert_output_contains "$output" "OPTIONS"
}

# =============================================================================
# Test Cases - Subdirectories
# =============================================================================

test_scans_subdirectories() {
  mkdir -p "$TEST_TMP_DIR/components/ui"
  mkdir -p "$TEST_TMP_DIR/components/dashboard"
  
  create_component_without_story "$TEST_TMP_DIR/components/ui" "button"
  create_component_without_story "$TEST_TMP_DIR/components/dashboard" "stat-card"
  
  local output
  output=$(bash "$DETECT_SCRIPT" --dir "$TEST_TMP_DIR/components" 2>&1) || true
  local exit_code=$?
  
  assert_exit_code 0 "$exit_code" && \
  assert_output_contains "$output" "Components scanned: 2" && \
  assert_output_contains "$output" "Components missing stories: 2"
}

# =============================================================================
# Main Test Runner
# =============================================================================

main() {
  echo "=============================================================================="
  echo "Missing Storybook Stories Detection Script Tests"
  echo "=============================================================================="
  echo ""
  
  # Basic Detection Tests
  echo "Basic Detection Tests:"
  run_test "full coverage" test_full_coverage
  run_test "detects missing story" test_detects_missing_story
  run_test "multiple components" test_multiple_components
  run_test "strict mode fails on missing" test_strict_mode_fails_on_missing
  run_test "strict mode passes on full coverage" test_strict_mode_passes_on_full_coverage
  echo ""
  
  # File Exclusion Tests
  echo "File Exclusion Tests:"
  run_test "excludes test files" test_excludes_test_files
  run_test "excludes index files" test_excludes_index_files
  run_test "excludes hook files" test_excludes_hook_files
  run_test "excludes story files from scan" test_excludes_story_files_from_scan
  echo ""
  
  # Allowlist Tests
  echo "Allowlist Tests:"
  run_test "allowlist skips allowed files" test_allowlist_skips_allowed_files
  run_test "allowlist still detects non-allowed files" test_allowlist_still_detects_non_allowed_files
  echo ""
  
  # JSON Output Tests
  echo "JSON Output Tests:"
  run_test "json output format" test_json_output_format
  echo ""
  
  # Edge Case Tests
  echo "Edge Case Tests:"
  run_test "empty directory" test_empty_directory
  run_test "nonexistent directory" test_nonexistent_directory
  run_test "help option" test_help_option
  echo ""
  
  # Subdirectory Tests
  echo "Subdirectory Tests:"
  run_test "scans subdirectories" test_scans_subdirectories
  echo ""
  
  # Summary
  echo "=============================================================================="
  echo "Test Summary"
  echo "=============================================================================="
  echo "Tests run: $TESTS_RUN"
  echo "Tests passed: $TESTS_PASSED"
  echo "Tests failed: $TESTS_FAILED"
  echo ""
  
  if [[ $TESTS_FAILED -gt 0 ]]; then
    echo -e "${RED}SOME TESTS FAILED${NC}"
    exit 1
  else
    echo -e "${GREEN}ALL TESTS PASSED${NC}"
    exit 0
  fi
}

main "$@"
