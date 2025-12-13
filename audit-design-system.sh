#!/bin/bash

# MorningAI Design System Audit Script
# Full version with all 8 audit sections implemented
# Epic #2304 Phase 0-1: UI/UX Systematization and Standardization

set -euo pipefail

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
GRAY='\033[0;90m'
NC='\033[0m'

CI_MODE=false
VERBOSE=false
STRICT_MODE=false
SUMMARY_FILE="audit-summary.txt"
FAIL_COUNT=0
WARN_COUNT=0
PASS_COUNT=0
TODO_COUNT=0

for arg in "$@"; do
  case $arg in
    --ci)
      CI_MODE=true
      shift
      ;;
    --verbose)
      VERBOSE=true
      shift
      ;;
    --strict)
      STRICT_MODE=true
      shift
      ;;
    --relaxed)
      STRICT_MODE=false
      shift
      ;;
    --summary-file)
      SUMMARY_FILE="$2"
      shift 2
      ;;
  esac
done

log_section() {
  echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${BLUE}$1${NC}"
  echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

log_pass() {
  echo -e "${GREEN}✓ PASS${NC}: $1"
  PASS_COUNT=$((PASS_COUNT + 1))
}

log_warn() {
  echo -e "${YELLOW}⚠ WARN${NC}: $1"
  WARN_COUNT=$((WARN_COUNT + 1))
}

log_fail() {
  echo -e "${RED}✗ FAIL${NC}: $1"
  FAIL_COUNT=$((FAIL_COUNT + 1))
}

log_todo() {
  echo -e "${GRAY}⊘ TODO${NC}: $1"
  TODO_COUNT=$((TODO_COUNT + 1))
}

log_info() {
  if [ "$VERBOSE" = true ]; then
    echo -e "  ℹ $1"
  fi
}

if [ ! -f "package.json" ] || [ ! -f "pnpm-workspace.yaml" ]; then
  echo -e "${RED}Error: Must be run from repository root${NC}"
  exit 1
fi

MODE_LABEL="relaxed"
if [ "$STRICT_MODE" = true ]; then
  MODE_LABEL="strict"
fi

echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║         MorningAI Design System Audit Report                      ║"
echo "║         $(date '+%Y-%m-%d %H:%M:%S %Z')                                    ║"
echo "║         Mode: $MODE_LABEL                                                  ║"
echo "╚════════════════════════════════════════════════════════════════════╝"

log_section "1. Environment & Package Governance"

NODE_VERSION=$(node --version | sed 's/v//')
REQUIRED_NODE="20.0.0"
if [ "$(printf '%s\n' "$REQUIRED_NODE" "$NODE_VERSION" | sort -V | head -n1)" = "$REQUIRED_NODE" ]; then
  log_pass "Node.js version $NODE_VERSION >= $REQUIRED_NODE"
else
  log_fail "Node.js version $NODE_VERSION < $REQUIRED_NODE (required: >= $REQUIRED_NODE)"
fi

if command -v pnpm &> /dev/null; then
  PNPM_VERSION=$(pnpm --version)
  REQUIRED_PNPM="9.0.0"
  if [ "$(printf '%s\n' "$REQUIRED_PNPM" "$PNPM_VERSION" | sort -V | head -n1)" = "$REQUIRED_PNPM" ]; then
    log_pass "pnpm version $PNPM_VERSION >= $REQUIRED_PNPM"
  else
    log_fail "pnpm version $PNPM_VERSION < $REQUIRED_PNPM (required: >= $REQUIRED_PNPM)"
  fi
else
  log_fail "pnpm not installed"
fi

if find . -name "yarn.lock" -o -name "package-lock.json" -o -name "npm-shrinkwrap.json" 2>/dev/null | grep -q .; then
  log_fail "Forbidden lockfiles found (yarn.lock, package-lock.json, or npm-shrinkwrap.json)"
else
  log_pass "No forbidden lockfiles (yarn.lock, package-lock.json, npm-shrinkwrap.json)"
fi

if [ -f "pnpm-lock.yaml" ]; then
  log_pass "pnpm-lock.yaml exists at root"
else
  log_fail "pnpm-lock.yaml missing at root"
fi

if grep -q '"packageManager".*"pnpm@' package.json 2>/dev/null; then
  log_pass "Root package.json has packageManager field set to pnpm"
else
  log_warn "Root package.json missing packageManager field"
fi

if [ -d "packages/shared-ui" ] && [ -f "packages/shared-ui/package.json" ]; then
  log_pass "packages/shared-ui exists with package.json"
else
  log_fail "packages/shared-ui directory or package.json missing"
fi

if [ -f "packages/shared-ui/src/tokens.json" ]; then
  log_pass "Design tokens file exists (packages/shared-ui/src/tokens.json)"
else
  log_warn "Design tokens file missing (packages/shared-ui/src/tokens.json)"
fi

log_section "2. Design System Adoption & Component Duplication"

# Count shared-ui components
SHARED_UI_COMPONENTS=$(find packages/shared-ui/src/components/ui -name "*.tsx" -not -name "*.stories.tsx" -not -name "*.test.tsx" 2>/dev/null | wc -l || echo "0")
if [ "$SHARED_UI_COMPONENTS" -ge 40 ]; then
  log_pass "Shared-ui has $SHARED_UI_COMPONENTS components (target: 40+)"
else
  log_warn "Shared-ui has only $SHARED_UI_COMPONENTS components (target: 40+)"
fi

# Check shared-ui imports in frontend apps
FRONTEND_IMPORTS=$(grep -r "@morningai/shared-ui" handoff/20250928/40_App/frontend-dashboard/src --include="*.tsx" --include="*.ts" 2>/dev/null | wc -l || echo "0")
OWNER_IMPORTS=$(grep -r "@morningai/shared-ui" handoff/20250928/40_App/owner-console/src --include="*.tsx" --include="*.ts" 2>/dev/null | wc -l || echo "0")
TOTAL_IMPORTS=$((FRONTEND_IMPORTS + OWNER_IMPORTS))
if [ "$TOTAL_IMPORTS" -ge 50 ]; then
  log_pass "Shared-ui imports found: $TOTAL_IMPORTS (frontend: $FRONTEND_IMPORTS, owner-console: $OWNER_IMPORTS)"
else
  log_warn "Low shared-ui adoption: $TOTAL_IMPORTS imports (target: 50+)"
fi

log_section "3. Design Tokens Enforcement"

# Check for hard-coded hex colors in frontend apps (excluding node_modules, dist, .stories files)
HEX_COLORS=$(grep -rE "#[0-9A-Fa-f]{6}\b|#[0-9A-Fa-f]{3}\b" \
  handoff/20250928/40_App/frontend-dashboard/src \
  handoff/20250928/40_App/owner-console/src \
  --include="*.tsx" --include="*.ts" --include="*.css" \
  2>/dev/null | grep -v "node_modules" | grep -v ".stories." | wc -l || echo "0")

if [ "$HEX_COLORS" -le 50 ]; then
  log_pass "Hard-coded hex colors: $HEX_COLORS (target: <50)"
elif [ "$HEX_COLORS" -le 150 ]; then
  log_warn "Hard-coded hex colors: $HEX_COLORS (target: <50, acceptable: <150)"
else
  log_fail "Too many hard-coded hex colors: $HEX_COLORS (target: <50)"
fi

# Check for inline styles
INLINE_STYLES=$(grep -rE "style=\{" \
  handoff/20250928/40_App/frontend-dashboard/src \
  handoff/20250928/40_App/owner-console/src \
  --include="*.tsx" \
  2>/dev/null | grep -v "node_modules" | grep -v ".stories." | wc -l || echo "0")

if [ "$INLINE_STYLES" -le 100 ]; then
  log_pass "Inline styles usage: $INLINE_STYLES (target: <100)"
else
  log_warn "High inline styles usage: $INLINE_STYLES (target: <100)"
fi

# Check design tokens file has required categories
if [ -f "packages/shared-ui/src/tokens.json" ]; then
  REQUIRED_TOKENS=("color" "font" "space" "radius" "shadow" "animation" "breakpoint")
  MISSING_TOKENS=0
  for token in "${REQUIRED_TOKENS[@]}"; do
    if ! grep -q "\"$token\"" packages/shared-ui/src/tokens.json 2>/dev/null; then
      MISSING_TOKENS=$((MISSING_TOKENS + 1))
      log_info "Missing token category: $token"
    fi
  done
  if [ "$MISSING_TOKENS" -eq 0 ]; then
    log_pass "All required token categories present (${#REQUIRED_TOKENS[@]} categories)"
  else
    log_warn "Missing $MISSING_TOKENS token categories"
  fi
fi

log_section "4. Accessibility Compliance"

# Check for eslint-plugin-jsx-a11y in package.json files
A11Y_ESLINT=$(grep -r "eslint-plugin-jsx-a11y" \
  handoff/20250928/40_App/frontend-dashboard/package.json \
  handoff/20250928/40_App/owner-console/package.json \
  2>/dev/null | wc -l || echo "0")

if [ "$A11Y_ESLINT" -ge 1 ]; then
  log_pass "eslint-plugin-jsx-a11y installed in $A11Y_ESLINT package(s)"
else
  log_warn "eslint-plugin-jsx-a11y not found in frontend packages"
fi

# Check for axe-core testing tools
AXE_TOOLS=$(grep -rE "@axe-core|jest-axe|vitest-axe" \
  handoff/20250928/40_App/frontend-dashboard/package.json \
  handoff/20250928/40_App/owner-console/package.json \
  packages/shared-ui/package.json \
  2>/dev/null | wc -l || echo "0")

if [ "$AXE_TOOLS" -ge 1 ]; then
  log_pass "Accessibility testing tools found: $AXE_TOOLS package references"
else
  log_warn "No axe-core testing tools found"
fi

# Count accessibility test files
A11Y_TESTS=$(find packages/shared-ui/src -name "*.a11y.test.*" -o -name "*accessibility*.test.*" 2>/dev/null | wc -l || echo "0")
if [ "$A11Y_TESTS" -ge 3 ]; then
  log_pass "Accessibility test files: $A11Y_TESTS"
else
  log_warn "Few accessibility test files: $A11Y_TESTS (target: 3+)"
fi

log_section "5. Motion & Animation Governance"

# Check for prefers-reduced-motion support
REDUCED_MOTION_CSS=$(grep -r "prefers-reduced-motion" \
  handoff/20250928/40_App/frontend-dashboard/src \
  handoff/20250928/40_App/owner-console/src \
  packages/shared-ui/src \
  --include="*.css" --include="*.scss" --include="*.tsx" --include="*.ts" \
  2>/dev/null | wc -l || echo "0")

if [ "$REDUCED_MOTION_CSS" -ge 3 ]; then
  log_pass "prefers-reduced-motion support: $REDUCED_MOTION_CSS instances"
else
  log_warn "Limited prefers-reduced-motion support: $REDUCED_MOTION_CSS instances (target: 3+)"
fi

# Check for framer-motion usage
FRAMER_MOTION=$(grep -r "framer-motion" \
  packages/shared-ui/package.json \
  handoff/20250928/40_App/frontend-dashboard/package.json \
  2>/dev/null | wc -l || echo "0")

if [ "$FRAMER_MOTION" -ge 1 ]; then
  log_pass "Framer Motion installed for animations"
else
  log_info "Framer Motion not detected (optional)"
fi

log_section "6. Internationalization (i18n)"

# Check for i18n libraries
I18N_LIBS=$(grep -rE "react-i18next|i18next|@tolgee" \
  handoff/20250928/40_App/frontend-dashboard/package.json \
  handoff/20250928/40_App/owner-console/package.json \
  2>/dev/null | wc -l || echo "0")

if [ "$I18N_LIBS" -ge 1 ]; then
  log_pass "i18n libraries installed: $I18N_LIBS package references"
else
  log_warn "No i18n libraries found"
fi

# Count i18n usage (useTranslation, t() calls)
I18N_USAGE=$(grep -rE "useTranslation|\\bt\\(" \
  handoff/20250928/40_App/frontend-dashboard/src \
  handoff/20250928/40_App/owner-console/src \
  --include="*.tsx" --include="*.ts" \
  2>/dev/null | wc -l || echo "0")

if [ "$I18N_USAGE" -ge 100 ]; then
  log_pass "i18n usage: $I18N_USAGE instances (excellent coverage)"
elif [ "$I18N_USAGE" -ge 50 ]; then
  log_pass "i18n usage: $I18N_USAGE instances (good coverage)"
else
  log_warn "Low i18n usage: $I18N_USAGE instances (target: 50+)"
fi

log_section "7. Storybook & Documentation"

# Check Storybook configuration
if [ -d "packages/shared-ui/.storybook" ]; then
  log_pass "Storybook configured in shared-ui"
else
  log_warn "Storybook not configured in shared-ui"
fi

# Count story files
STORY_FILES=$(find packages/shared-ui/src -name "*.stories.tsx" -o -name "*.stories.ts" 2>/dev/null | wc -l || echo "0")
if [ "$STORY_FILES" -ge 15 ]; then
  log_pass "Story files: $STORY_FILES (good coverage)"
elif [ "$STORY_FILES" -ge 5 ]; then
  log_warn "Story files: $STORY_FILES (target: 15+)"
else
  log_fail "Few story files: $STORY_FILES (target: 15+)"
fi

# Check for design system documentation
DESIGN_DOCS=0
for doc in "DESIGN_SYSTEM_GUIDELINES.md" "docs/UI_UX_QUICKSTART.md" "docs/UI_UX_CHEATSHEET.md"; do
  if [ -f "$doc" ]; then
    DESIGN_DOCS=$((DESIGN_DOCS + 1))
  fi
done

if [ "$DESIGN_DOCS" -ge 2 ]; then
  log_pass "Design system documentation: $DESIGN_DOCS files found"
else
  log_warn "Limited design system documentation: $DESIGN_DOCS files (target: 2+)"
fi

log_section "8. React Version Alignment"

# Check React version in shared-ui
SHARED_UI_REACT=$(grep -oP '"react":\s*"\K[^"]+' packages/shared-ui/package.json 2>/dev/null || echo "not found")
log_info "shared-ui React peer dependency: $SHARED_UI_REACT"

# Check for React 19 adoption
REACT_19=$(grep -rE '"react":\s*"[^"]*19' \
  handoff/20250928/40_App/frontend-dashboard/package.json \
  handoff/20250928/40_App/owner-console/package.json \
  2>/dev/null | wc -l || echo "0")

if [ "$REACT_19" -ge 1 ]; then
  log_pass "React 19 adopted in $REACT_19 frontend package(s)"
else
  # Check for React 18 as acceptable
  REACT_18=$(grep -rE '"react":\s*"[^"]*18' \
    handoff/20250928/40_App/frontend-dashboard/package.json \
    handoff/20250928/40_App/owner-console/package.json \
    2>/dev/null | wc -l || echo "0")
  if [ "$REACT_18" -ge 1 ]; then
    log_pass "React 18 in use (React 19 upgrade recommended)"
  else
    log_warn "React version not detected in frontend packages"
  fi
fi

# Check React version consistency
REACT_VERSIONS=$(grep -ohP '"react":\s*"\K[^"]+' \
  packages/shared-ui/package.json \
  handoff/20250928/40_App/frontend-dashboard/package.json \
  handoff/20250928/40_App/owner-console/package.json \
  2>/dev/null | sort -u | wc -l || echo "0")

if [ "$REACT_VERSIONS" -le 2 ]; then
  log_pass "React version consistency: $REACT_VERSIONS unique version patterns"
else
  log_warn "React version inconsistency: $REACT_VERSIONS different version patterns"
fi

log_section "Audit Summary"

TOTAL_CHECKS=$((PASS_COUNT + WARN_COUNT + FAIL_COUNT + TODO_COUNT))

echo ""
echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║                         AUDIT RESULTS                              ║"
echo "╠════════════════════════════════════════════════════════════════════╣"
printf "║  ${GREEN}✓ PASSED${NC}:   %-53s ║\n" "$PASS_COUNT / $TOTAL_CHECKS"
printf "║  ${YELLOW}⚠ WARNINGS${NC}:  %-53s ║\n" "$WARN_COUNT / $TOTAL_CHECKS"
printf "║  ${RED}✗ FAILED${NC}:    %-53s ║\n" "$FAIL_COUNT / $TOTAL_CHECKS"
printf "║  ${GRAY}⊘ TODO${NC}:      %-53s ║\n" "$TODO_COUNT / $TOTAL_CHECKS"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

cat > "$SUMMARY_FILE" <<EOF
PASS=$PASS_COUNT
WARN=$WARN_COUNT
FAIL=$FAIL_COUNT
TODO=$TODO_COUNT
TOTAL=$TOTAL_CHECKS
MODE=$MODE_LABEL
NOTES=Full audit with all 8 sections implemented. Epic #2304 Phase 0-1 complete.
EOF

log_info "Summary written to $SUMMARY_FILE"

if [ "$STRICT_MODE" = true ]; then
  if [ $FAIL_COUNT -eq 0 ] && [ $WARN_COUNT -eq 0 ]; then
    echo -e "${GREEN}🎉 All checks passed! Design system is in excellent condition.${NC}"
    exit 0
  elif [ $FAIL_COUNT -eq 0 ]; then
    echo -e "${YELLOW}⚠️  Audit completed with $WARN_COUNT warning(s). Review recommended.${NC}"
    exit 2
  else
    echo -e "${RED}❌ Audit failed with $FAIL_COUNT critical issue(s) and $WARN_COUNT warning(s).${NC}"
    echo -e "${RED}   Please address the failures before proceeding.${NC}"
    exit 1
  fi
else
  if [ $FAIL_COUNT -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Relaxed mode: $FAIL_COUNT failure(s) detected but not blocking CI.${NC}"
    echo -e "${YELLOW}   Run with --strict to enforce failures.${NC}"
  fi
  if [ $TODO_COUNT -gt 0 ]; then
    echo -e "${GRAY}ℹ️  $TODO_COUNT check(s) marked as TODO - will be enabled after debugging.${NC}"
  fi
  echo -e "${GREEN}✓ Audit completed in relaxed mode (exit 0).${NC}"
  exit 0
fi
