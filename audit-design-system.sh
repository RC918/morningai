#!/bin/bash

# MorningAI Design System Audit Script

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

SHARED_COMPONENTS=0
if [ -d "packages/shared-ui/src/components/ui" ]; then
  SHARED_COMPONENTS=$(find packages/shared-ui/src/components/ui -name "*.tsx" 2>/dev/null | wc -l || echo 0)
fi
log_info "Shared UI components: $SHARED_COMPONENTS"

DASHBOARD_LOCAL=0
if [ -d "handoff/20250928/40_App/frontend-dashboard/src/components/ui" ]; then
  DASHBOARD_LOCAL=$(find handoff/20250928/40_App/frontend-dashboard/src/components/ui -name "*.tsx" 2>/dev/null | wc -l || echo 0)
fi
log_info "Frontend-dashboard local components: $DASHBOARD_LOCAL"

CONSOLE_LOCAL=0
if [ -d "handoff/20250928/40_App/owner-console/src/components/ui" ]; then
  CONSOLE_LOCAL=$(find handoff/20250928/40_App/owner-console/src/components/ui -name "*.tsx" 2>/dev/null | wc -l || echo 0)
fi
log_info "Owner-console local components: $CONSOLE_LOCAL"

DASHBOARD_SHARED_IMPORTS=0
if [ -d "handoff/20250928/40_App/frontend-dashboard/src" ]; then
  DASHBOARD_SHARED_IMPORTS=$(grep -r "from '@morningai/shared-ui'" handoff/20250928/40_App/frontend-dashboard/src --include="*.tsx" --include="*.ts" 2>/dev/null | wc -l || echo 0)
fi
log_info "Frontend-dashboard shared-ui imports: $DASHBOARD_SHARED_IMPORTS"

CONSOLE_SHARED_IMPORTS=0
if [ -d "handoff/20250928/40_App/owner-console/src" ]; then
  CONSOLE_SHARED_IMPORTS=$(grep -r "from '@morningai/shared-ui'" handoff/20250928/40_App/owner-console/src --include="*.tsx" --include="*.ts" 2>/dev/null | wc -l || echo 0)
fi
log_info "Owner-console shared-ui imports: $CONSOLE_SHARED_IMPORTS"

if [ $DASHBOARD_SHARED_IMPORTS -gt 0 ] || [ $CONSOLE_SHARED_IMPORTS -gt 0 ]; then
  log_pass "Apps are importing from @morningai/shared-ui ($((DASHBOARD_SHARED_IMPORTS + CONSOLE_SHARED_IMPORTS)) imports)"
else
  log_warn "No shared-ui imports detected in apps - migration may be incomplete"
fi

if [ $SHARED_COMPONENTS -gt 0 ] && [ $DASHBOARD_LOCAL -gt 0 ]; then
  log_warn "Frontend-dashboard has $DASHBOARD_LOCAL local components while shared-ui has $SHARED_COMPONENTS - review for duplicates"
elif [ $DASHBOARD_LOCAL -eq 0 ] && [ $SHARED_COMPONENTS -gt 0 ]; then
  log_pass "Frontend-dashboard has no local UI components - using shared-ui"
else
  log_pass "Component distribution looks reasonable"
fi

log_section "3. Design Tokens Enforcement"

HEX_VIOLATIONS=0
if [ -d "handoff/20250928/40_App/frontend-dashboard/src" ] || [ -d "handoff/20250928/40_App/owner-console/src" ] || [ -d "packages/shared-ui/src" ]; then
  HEX_VIOLATIONS=$(grep -r "#[0-9A-Fa-f]\{6\}" \
    handoff/20250928/40_App/frontend-dashboard/src \
    handoff/20250928/40_App/owner-console/src \
    packages/shared-ui/src \
    --include="*.tsx" --include="*.ts" \
    --exclude="tokens.json" --exclude="*.config.*" --exclude="*.stories.tsx" \
    2>/dev/null | wc -l || echo 0)
fi

if [ $HEX_VIOLATIONS -eq 0 ]; then
  log_pass "No hard-coded hex colors in component files (excluding stories)"
else
  log_warn "$HEX_VIOLATIONS instances of hard-coded hex colors found (excluding stories)"
fi

INLINE_STYLES=0
if [ -d "handoff/20250928/40_App/frontend-dashboard/src" ] || [ -d "handoff/20250928/40_App/owner-console/src" ] || [ -d "packages/shared-ui/src" ]; then
  INLINE_STYLES=$(grep -r "style={{" \
    handoff/20250928/40_App/frontend-dashboard/src \
    handoff/20250928/40_App/owner-console/src \
    packages/shared-ui/src \
    --include="*.tsx" \
    --exclude="*.stories.tsx" \
    --exclude="TokenExample.tsx" \
    2>/dev/null | \
    grep -v "style={{ y" | \
    grep -v "style={{ opacity" | \
    grep -v "style={{ transform" | \
    grep -v "style={{ width: \`" | \
    grep -v "style={{ height: \`" | \
    wc -l || echo 0)
fi

if [ $INLINE_STYLES -eq 0 ]; then
  log_pass "No inline styles found (excluding animations and stories)"
elif [ $INLINE_STYLES -lt 50 ]; then
  log_warn "$INLINE_STYLES instances of inline styles (acceptable if < 50, excluding animations)"
else
  log_fail "$INLINE_STYLES instances of inline styles (should be < 50, excluding animations)"
fi

RGB_VIOLATIONS=0
if [ -d "handoff/20250928/40_App/frontend-dashboard/src" ] || [ -d "handoff/20250928/40_App/owner-console/src" ] || [ -d "packages/shared-ui/src" ]; then
  RGB_VIOLATIONS=$(grep -rE "rgb\(|rgba\(" \
    handoff/20250928/40_App/frontend-dashboard/src \
    handoff/20250928/40_App/owner-console/src \
    packages/shared-ui/src \
    --include="*.tsx" --include="*.ts" \
    --exclude="*.stories.tsx" \
    2>/dev/null | wc -l || echo 0)
fi

if [ $RGB_VIOLATIONS -eq 0 ]; then
  log_pass "No rgb/rgba color values in component files (excluding stories)"
else
  log_warn "$RGB_VIOLATIONS instances of rgb/rgba colors found (excluding stories)"
fi

log_section "4. Accessibility Compliance"

if [ -f "handoff/20250928/40_App/frontend-dashboard/package.json" ] && grep -q "eslint-plugin-jsx-a11y" handoff/20250928/40_App/frontend-dashboard/package.json 2>/dev/null; then
  log_pass "eslint-plugin-jsx-a11y installed in frontend-dashboard"
else
  log_fail "eslint-plugin-jsx-a11y missing in frontend-dashboard"
fi

A11Y_TOOLS=0
if [ -f "handoff/20250928/40_App/frontend-dashboard/package.json" ]; then
  A11Y_TOOLS=$(grep -E "vitest-axe|jest-axe|@axe-core" handoff/20250928/40_App/frontend-dashboard/package.json 2>/dev/null | wc -l || echo 0)
fi

if [ $A11Y_TOOLS -gt 0 ]; then
  log_pass "Accessibility testing tools installed (axe-core, jest-axe, or vitest-axe)"
else
  log_warn "No accessibility testing tools found"
fi

A11Y_TESTS=0
if [ -d "handoff/20250928/40_App/frontend-dashboard/src" ]; then
  A11Y_TESTS=$(find handoff/20250928/40_App/frontend-dashboard/src -name "*.a11y.test.*" -o -name "*.axe.test.*" 2>/dev/null | wc -l || echo 0)
fi
log_info "Accessibility test files: $A11Y_TESTS"

if [ $A11Y_TESTS -gt 0 ]; then
  log_pass "$A11Y_TESTS accessibility test files found"
else
  log_warn "No dedicated accessibility test files found"
fi

IMG_NO_ALT=0
if [ -d "handoff/20250928/40_App/frontend-dashboard/src" ]; then
  IMG_NO_ALT=$(grep -r "<img" handoff/20250928/40_App/frontend-dashboard/src --include="*.tsx" 2>/dev/null | grep -v "alt=" | grep -v "\.stories\.tsx" | wc -l || echo 0)
fi

if [ "$IMG_NO_ALT" -eq 0 ]; then
  log_pass "No <img> tags without alt attributes detected"
else
  log_warn "$IMG_NO_ALT <img> tag(s) potentially missing alt attributes"
fi

log_section "5. Motion & Animation Governance"

REDUCED_MOTION_CSS=0
REDUCED_MOTION_JS=0
if [ -d "handoff/20250928/40_App/frontend-dashboard/src" ]; then
  REDUCED_MOTION_CSS=$(grep -r "prefers-reduced-motion" handoff/20250928/40_App/frontend-dashboard/src --include="*.css" 2>/dev/null | wc -l || echo 0)
  REDUCED_MOTION_JS=$(grep -r "prefers-reduced-motion" handoff/20250928/40_App/frontend-dashboard/src --include="*.tsx" --include="*.ts" 2>/dev/null | wc -l || echo 0)
fi

if [ $REDUCED_MOTION_CSS -gt 0 ] || [ $REDUCED_MOTION_JS -gt 0 ]; then
  log_pass "prefers-reduced-motion support detected (CSS: $REDUCED_MOTION_CSS, JS: $REDUCED_MOTION_JS)"
else
  log_fail "No prefers-reduced-motion support found"
fi

FRAMER_USAGE=0
if [ -d "handoff/20250928/40_App/frontend-dashboard/src" ] || [ -d "packages/shared-ui/src" ]; then
  FRAMER_USAGE=$(grep -r "from 'framer-motion'" handoff/20250928/40_App/frontend-dashboard/src packages/shared-ui/src --include="*.tsx" --include="*.ts" 2>/dev/null | wc -l || echo 0)
fi
log_info "Framer Motion usage: $FRAMER_USAGE files"

REDUCED_MOTION_WRAPPER=0
if [ -d "handoff/20250928/40_App/frontend-dashboard/src" ] || [ -d "packages/shared-ui/src" ]; then
  REDUCED_MOTION_WRAPPER=$(grep -r "withReducedMotion" handoff/20250928/40_App/frontend-dashboard/src packages/shared-ui/src --include="*.tsx" --include="*.ts" 2>/dev/null | wc -l || echo 0)
fi

if [ $REDUCED_MOTION_WRAPPER -gt 0 ]; then
  log_pass "withReducedMotion wrapper usage detected"
else
  log_warn "No withReducedMotion wrapper usage found (verify manual implementation)"
fi

log_section "6. Internationalization (i18n)"

if [ -f "handoff/20250928/40_App/frontend-dashboard/package.json" ] && grep -qE "react-i18next|i18next" handoff/20250928/40_App/frontend-dashboard/package.json 2>/dev/null; then
  log_pass "i18n library (react-i18next/i18next) installed"
else
  log_warn "No i18n library detected"
fi

I18N_USAGE=0
if [ -d "handoff/20250928/40_App/frontend-dashboard/src" ]; then
  I18N_USAGE=$(grep -rE "useTranslation|t\(" handoff/20250928/40_App/frontend-dashboard/src --include="*.tsx" --include="*.ts" 2>/dev/null | wc -l || echo 0)
fi
log_info "i18n usage instances: $I18N_USAGE"

if [ $I18N_USAGE -gt 100 ]; then
  log_pass "Extensive i18n usage detected ($I18N_USAGE instances)"
elif [ $I18N_USAGE -gt 0 ]; then
  log_warn "Limited i18n usage ($I18N_USAGE instances) - consider expanding coverage"
else
  log_warn "No i18n usage detected"
fi

log_section "7. Storybook & Documentation"

if [ -d "handoff/20250928/40_App/frontend-dashboard/.storybook" ]; then
  log_pass "Storybook configuration found in frontend-dashboard"
else
  log_warn "No Storybook configuration in frontend-dashboard"
fi

STORY_FILES=0
if [ -d "handoff/20250928/40_App/frontend-dashboard/src" ]; then
  STORY_FILES=$(find handoff/20250928/40_App/frontend-dashboard/src -name "*.stories.*" 2>/dev/null | wc -l || echo 0)
fi
log_info "Storybook story files: $STORY_FILES"

if [ $STORY_FILES -gt 20 ]; then
  log_pass "$STORY_FILES story files found"
elif [ $STORY_FILES -gt 0 ]; then
  log_warn "Only $STORY_FILES story files found - consider adding more"
else
  log_warn "No Storybook stories found"
fi

VRT_TESTS=0
if [ -d "handoff/20250928/40_App/frontend-dashboard" ]; then
  VRT_TESTS=$(grep -r "@vrt" handoff/20250928/40_App/frontend-dashboard --include="*.spec.*" --include="*.test.*" 2>/dev/null | wc -l || echo 0)
fi

if [ $VRT_TESTS -gt 0 ]; then
  log_pass "$VRT_TESTS visual regression tests (@vrt) found"
else
  log_warn "No visual regression tests (@vrt) found"
fi

DOCS_MISSING=0
for doc in "DESIGN_SYSTEM_GUIDELINES.md" "CODE_DUPLICATION_ANALYSIS.md" "SHARED_COMPONENT_MIGRATION_PLAN.md"; do
  if [ ! -f "$doc" ]; then
    DOCS_MISSING=$((DOCS_MISSING + 1))
    log_info "Missing: $doc"
  fi
done

if [ $DOCS_MISSING -eq 0 ]; then
  log_pass "All key design system documentation files present"
else
  log_warn "$DOCS_MISSING key documentation file(s) missing"
fi

log_section "8. React Version Alignment"

REACT_VERSIONS=0
if [ -f "package.json" ]; then
  REACT_VERSIONS=$(grep -h '"react":' package.json packages/*/package.json handoff/20250928/40_App/*/package.json 2>/dev/null | sort -u | wc -l || echo 0)
fi

if [ $REACT_VERSIONS -eq 1 ]; then
  log_pass "React version consistent across all packages"
else
  log_warn "Multiple React versions detected ($REACT_VERSIONS different versions)"
fi

if [ -f "package.json" ] && grep -q '"react": "\^19' package.json 2>/dev/null; then
  log_pass "Using React 19 (latest)"
else
  log_warn "Not using React 19 - consider upgrading"
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
NOTES=All 8 audit sections enabled. Running in $MODE_LABEL mode.
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
