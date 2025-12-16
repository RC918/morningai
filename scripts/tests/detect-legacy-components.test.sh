#!/bin/bash
# =============================================================================
# Legacy Component Detection Script Tests
# =============================================================================
#
# PURPOSE:
#   Unit tests for the legacy component detection script.
#   Tests both AST-based (Node.js) and grep-based fallback detection.
#
# USAGE:
#   ./scripts/tests/detect-legacy-components.test.sh
#
# RELATED:
#   - Issue #2513: Legacy component detection CI
#   - scripts/detect-legacy-components.sh: Main detection script
#   - scripts/detect-legacy-components.mjs: AST-based detection implementation
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
DETECT_SCRIPT="$REPO_ROOT/scripts/detect-legacy-components.sh"

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
  mkdir -p "$TEST_TMP_DIR/src"
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
    echo "Actual output: $output" >&2
    return 1
  fi
  return 0
}

assert_output_not_contains() {
  local output="$1"
  local unexpected="$2"
  
  if [[ "$output" == *"$unexpected"* ]]; then
    echo "Expected output NOT to contain: $unexpected" >&2
    echo "Actual output: $output" >&2
    return 1
  fi
  return 0
}

# =============================================================================
# Test Fixtures
# =============================================================================

create_file_with_legacy_import() {
  local file="$1"
  cat > "$file" << 'EOF'
import React from 'react';
import { LegacyCard } from '../components/LegacyCard';

export function MyComponent() {
  return <LegacyCard>Hello</LegacyCard>;
}
EOF
}

create_file_with_legacy_import_named() {
  local file="$1"
  cat > "$file" << 'EOF'
import React from 'react';
import { LegacyCard, LegacyStatCard } from '../components';

export function MyComponent() {
  return (
    <div>
      <LegacyCard>Hello</LegacyCard>
      <LegacyStatCard value={42} />
    </div>
  );
}
EOF
}

create_file_without_legacy_import() {
  local file="$1"
  cat > "$file" << 'EOF'
import React from 'react';
import { Card } from '@shared-ui/components';

export function MyComponent() {
  return <Card>Hello</Card>;
}
EOF
}

create_file_with_commented_import() {
  local file="$1"
  cat > "$file" << 'EOF'
import React from 'react';
// import { LegacyCard } from '../components/LegacyCard';
import { Card } from '@shared-ui/components';

export function MyComponent() {
  return <Card>Hello</Card>;
}
EOF
}

create_file_with_string_mention() {
  local file="$1"
  cat > "$file" << 'EOF'
import React from 'react';
import { Card } from '@shared-ui/components';

export function MyComponent() {
  const message = "Replace LegacyCard with Card";
  return <Card>{message}</Card>;
}
EOF
}

create_file_with_multiline_import() {
  local file="$1"
  cat > "$file" << 'EOF'
import React from 'react';
import {
  LegacyCard,
  SomeOtherComponent
} from '../components';

export function MyComponent() {
  return <LegacyCard>Hello</LegacyCard>;
}
EOF
}

create_allowlist_file() {
  local file="$1"
  local allowed_file="${2:-}"
  
  if [[ -n "$allowed_file" ]]; then
    cat > "$file" << EOF
{
  "legacy_components": ["LegacyCard", "LegacyStatCard"],
  "allowed_files": ["$allowed_file"],
  "expires": "2025-12-31"
}
EOF
  else
    cat > "$file" << 'EOF'
{
  "legacy_components": ["LegacyCard", "LegacyStatCard"],
  "allowed_files": [],
  "expires": "2025-12-31"
}
EOF
  fi
}

# =============================================================================
# Test Cases - Basic Detection
# =============================================================================

test_no_violations_in_clean_directory() {
  create_file_without_legacy_import "$TEST_TMP_DIR/src/Component.tsx"
  
  local output
  output=$(bash "$DETECT_SCRIPT" --dir "$TEST_TMP_DIR/src" 2>&1) || true
  local exit_code=$?
  
  assert_exit_code 0 "$exit_code" && \
  assert_output_contains "$output" "Violations found: 0" && \
  assert_output_contains "$output" "No legacy component imports detected"
}

test_detects_legacy_import() {
  create_file_with_legacy_import "$TEST_TMP_DIR/src/Component.tsx"
  
  local output
  output=$(bash "$DETECT_SCRIPT" --dir "$TEST_TMP_DIR/src" 2>&1) || true
  local exit_code=$?
  
  assert_exit_code 0 "$exit_code" && \
  assert_output_contains "$output" "Violations found: 1"
}

test_detects_multiple_legacy_imports() {
  create_file_with_legacy_import_named "$TEST_TMP_DIR/src/Component.tsx"
  
  local output
  output=$(bash "$DETECT_SCRIPT" --dir "$TEST_TMP_DIR/src" 2>&1) || true
  local exit_code=$?
  
  assert_exit_code 0 "$exit_code" && \
  assert_output_contains "$output" "Violations found:"
}

test_strict_mode_exits_with_error() {
  create_file_with_legacy_import "$TEST_TMP_DIR/src/Component.tsx"
  
  local output
  local exit_code
  output=$(bash "$DETECT_SCRIPT" --dir "$TEST_TMP_DIR/src" --strict 2>&1) && exit_code=0 || exit_code=$?
  
  assert_exit_code 1 "$exit_code" && \
  assert_output_contains "$output" "STRICT MODE"
}

test_strict_mode_passes_with_no_violations() {
  create_file_without_legacy_import "$TEST_TMP_DIR/src/Component.tsx"
  
  local output
  output=$(bash "$DETECT_SCRIPT" --dir "$TEST_TMP_DIR/src" --strict 2>&1) || true
  local exit_code=$?
  
  assert_exit_code 0 "$exit_code" && \
  assert_output_contains "$output" "No legacy component imports detected"
}

# =============================================================================
# Test Cases - AST Accuracy (False Positive Prevention)
# =============================================================================

test_ignores_commented_imports() {
  create_file_with_commented_import "$TEST_TMP_DIR/src/Component.tsx"
  
  local output
  output=$(bash "$DETECT_SCRIPT" --dir "$TEST_TMP_DIR/src" 2>&1) || true
  local exit_code=$?
  
  assert_exit_code 0 "$exit_code" && \
  assert_output_contains "$output" "Violations found: 0"
}

test_ignores_string_mentions() {
  create_file_with_string_mention "$TEST_TMP_DIR/src/Component.tsx"
  
  local output
  output=$(bash "$DETECT_SCRIPT" --dir "$TEST_TMP_DIR/src" 2>&1) || true
  local exit_code=$?
  
  assert_exit_code 0 "$exit_code" && \
  assert_output_contains "$output" "Violations found: 0"
}

test_detects_multiline_imports() {
  create_file_with_multiline_import "$TEST_TMP_DIR/src/Component.tsx"
  
  local output
  output=$(bash "$DETECT_SCRIPT" --dir "$TEST_TMP_DIR/src" 2>&1) || true
  local exit_code=$?
  
  assert_exit_code 0 "$exit_code" && \
  assert_output_contains "$output" "Violations found: 1"
}

# =============================================================================
# Test Cases - Allowlist
# =============================================================================

test_allowlist_skips_allowed_files() {
  create_file_with_legacy_import "$TEST_TMP_DIR/src/AllowedComponent.tsx"
  create_allowlist_file "$TEST_TMP_DIR/allowlist.json" "AllowedComponent.tsx"
  
  local output
  output=$(bash "$DETECT_SCRIPT" --dir "$TEST_TMP_DIR/src" --allowlist "$TEST_TMP_DIR/allowlist.json" 2>&1) || true
  local exit_code=$?
  
  assert_exit_code 0 "$exit_code" && \
  assert_output_contains "$output" "Violations found: 0"
}

test_allowlist_still_detects_non_allowed_files() {
  create_file_with_legacy_import "$TEST_TMP_DIR/src/Component.tsx"
  create_file_with_legacy_import "$TEST_TMP_DIR/src/AllowedComponent.tsx"
  create_allowlist_file "$TEST_TMP_DIR/allowlist.json" "AllowedComponent.tsx"
  
  local output
  output=$(bash "$DETECT_SCRIPT" --dir "$TEST_TMP_DIR/src" --allowlist "$TEST_TMP_DIR/allowlist.json" 2>&1) || true
  local exit_code=$?
  
  assert_exit_code 0 "$exit_code" && \
  assert_output_contains "$output" "Violations found: 1"
}

# =============================================================================
# Test Cases - Custom Components
# =============================================================================

test_custom_components_list() {
  cat > "$TEST_TMP_DIR/src/Component.tsx" << 'EOF'
import React from 'react';
import { CustomLegacy } from '../components';

export function MyComponent() {
  return <CustomLegacy>Hello</CustomLegacy>;
}
EOF
  
  local output
  output=$(bash "$DETECT_SCRIPT" --dir "$TEST_TMP_DIR/src" --components "CustomLegacy" 2>&1) || true
  local exit_code=$?
  
  assert_exit_code 0 "$exit_code" && \
  assert_output_contains "$output" "Violations found: 1"
}

# =============================================================================
# Test Cases - Multiple Directories
# =============================================================================

test_multiple_directories() {
  mkdir -p "$TEST_TMP_DIR/src1" "$TEST_TMP_DIR/src2"
  create_file_with_legacy_import "$TEST_TMP_DIR/src1/Component1.tsx"
  create_file_with_legacy_import "$TEST_TMP_DIR/src2/Component2.tsx"
  
  local output
  output=$(bash "$DETECT_SCRIPT" --dir "$TEST_TMP_DIR/src1" --dir "$TEST_TMP_DIR/src2" 2>&1) || true
  local exit_code=$?
  
  assert_exit_code 0 "$exit_code" && \
  assert_output_contains "$output" "Violations found: 2"
}

# =============================================================================
# Test Cases - Grep Fallback
# =============================================================================

test_grep_fallback_detects_imports() {
  create_file_with_legacy_import "$TEST_TMP_DIR/src/Component.tsx"
  
  local output
  output=$(bash "$DETECT_SCRIPT" --dir "$TEST_TMP_DIR/src" --use-grep 2>&1) || true
  local exit_code=$?
  
  assert_exit_code 0 "$exit_code" && \
  assert_output_contains "$output" "grep fallback" && \
  assert_output_contains "$output" "Violations found: 1"
}

test_grep_fallback_no_violations() {
  create_file_without_legacy_import "$TEST_TMP_DIR/src/Component.tsx"
  
  local output
  output=$(bash "$DETECT_SCRIPT" --dir "$TEST_TMP_DIR/src" --use-grep 2>&1) || true
  local exit_code=$?
  
  assert_exit_code 0 "$exit_code" && \
  assert_output_contains "$output" "grep fallback" && \
  assert_output_contains "$output" "Violations found: 0"
}

# =============================================================================
# Test Cases - JSON Output
# =============================================================================

test_json_output_format() {
  create_file_without_legacy_import "$TEST_TMP_DIR/src/Component.tsx"
  
  local output
  output=$(bash "$DETECT_SCRIPT" --dir "$TEST_TMP_DIR/src" --json 2>&1) || true
  local exit_code=$?
  
  assert_exit_code 0 "$exit_code" && \
  assert_output_contains "$output" '"filesScanned"' && \
  assert_output_contains "$output" '"violations"'
}

# =============================================================================
# Test Cases - Empty Directory
# =============================================================================

test_empty_directory() {
  local output
  output=$(bash "$DETECT_SCRIPT" --dir "$TEST_TMP_DIR/src" 2>&1) || true
  local exit_code=$?
  
  assert_exit_code 0 "$exit_code" && \
  assert_output_contains "$output" "Files scanned: 0" && \
  assert_output_contains "$output" "Violations found: 0"
}

# =============================================================================
# Test Cases - Non-existent Directory
# =============================================================================

test_nonexistent_directory() {
  local output
  output=$(bash "$DETECT_SCRIPT" --dir "$TEST_TMP_DIR/nonexistent" 2>&1) || true
  local exit_code=$?
  
  assert_exit_code 0 "$exit_code" && \
  assert_output_contains "$output" "Files scanned: 0"
}

# =============================================================================
# Test Cases - Help Option
# =============================================================================

test_help_option() {
  local output
  output=$(bash "$DETECT_SCRIPT" --help 2>&1) || true
  local exit_code=$?
  
  assert_exit_code 0 "$exit_code" && \
  assert_output_contains "$output" "USAGE" && \
  assert_output_contains "$output" "OPTIONS"
}

# =============================================================================
# Main Test Runner
# =============================================================================

main() {
  echo "=============================================================================="
  echo "Legacy Component Detection Script Tests"
  echo "=============================================================================="
  echo ""
  
  # Basic Detection Tests
  echo "Basic Detection Tests:"
  run_test "no violations in clean directory" test_no_violations_in_clean_directory
  run_test "detects legacy import" test_detects_legacy_import
  run_test "detects multiple legacy imports" test_detects_multiple_legacy_imports
  run_test "strict mode exits with error" test_strict_mode_exits_with_error
  run_test "strict mode passes with no violations" test_strict_mode_passes_with_no_violations
  echo ""
  
  # AST Accuracy Tests
  echo "AST Accuracy Tests (False Positive Prevention):"
  run_test "ignores commented imports" test_ignores_commented_imports
  run_test "ignores string mentions" test_ignores_string_mentions
  run_test "detects multiline imports" test_detects_multiline_imports
  echo ""
  
  # Allowlist Tests
  echo "Allowlist Tests:"
  run_test "allowlist skips allowed files" test_allowlist_skips_allowed_files
  run_test "allowlist still detects non-allowed files" test_allowlist_still_detects_non_allowed_files
  echo ""
  
  # Custom Components Tests
  echo "Custom Components Tests:"
  run_test "custom components list" test_custom_components_list
  echo ""
  
  # Multiple Directories Tests
  echo "Multiple Directories Tests:"
  run_test "multiple directories" test_multiple_directories
  echo ""
  
  # Grep Fallback Tests
  echo "Grep Fallback Tests:"
  run_test "grep fallback detects imports" test_grep_fallback_detects_imports
  run_test "grep fallback no violations" test_grep_fallback_no_violations
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
