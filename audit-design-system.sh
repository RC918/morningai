#!/bin/bash

#
#
#

set -euo pipefail

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

CI_MODE=false
VERBOSE=false
FAIL_COUNT=0
WARN_COUNT=0
PASS_COUNT=0

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
  esac
done

log_section() {
  echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${BLUE}$1${NC}"
  echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

log_pass() {
  echo -e "${GREEN}✓ PASS${NC}: $1"
  ((PASS_COUNT++))
}

log_warn() {
  echo -e "${YELLOW}⚠ WARN${NC}: $1"
  ((WARN_COUNT++))
}

log_fail() {
  echo -e "${RED}✗ FAIL${NC}: $1"
  ((FAIL_COUNT++))
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

echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║         MorningAI Design System Audit Report                      ║"
echo "║         $(date '+%Y-%m-%d %H:%M:%S %Z')                                    ║"
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

FORBIDDEN_LOCKS=$(find . -name "yarn.lock" -o -name "package-lock.json" -o -name "npm-shrinkwrap.json" 2>/dev/null)
if [ -z "$FORBIDDEN_LOCKS" ]; then
  log_pass "No forbidden lockfiles (yarn.lock, package-lock.json, npm-shrinkwrap.json)"
else
  log_fail "Forbidden lockfiles found:"
  echo "$FORBIDDEN_LOCKS" | while read -r file; do
    echo "    - $file"
  done
fi

if [ -f "pnpm-lock.yaml" ]; then
  log_pass "pnpm-lock.yaml exists at root"
else
  log_fail "pnpm-lock.yaml missing at root"
fi

if grep -q '"packageManager".*"pnpm@' package.json; then
  log_pass "Root package.json has packageManager field set to pnpm"
else
  log_warn "Root package.json missing packageManager field"
fi

PACKAGES_WITHOUT_ENGINES=0
for pkg in packages/*/package.json handoff/20250928/40_App/*/package.json; do
  if [ -f "$pkg" ]; then
    if ! grep -q '"engines"' "$pkg"; then
      ((PACKAGES_WITHOUT_ENGINES++))
      log_info "Missing engines: $pkg"
    fi
  fi
done

if [ $PACKAGES_WITHOUT_ENGINES -eq 0 ]; then
  log_pass "All workspace packages have engines field"
else
  log_warn "$PACKAGES_WITHOUT_ENGINES workspace package(s) missing engines field"
fi

log_section "2. Design System Adoption & Component Duplication"

SHARED_COMPONENTS=$(find packages/shared-ui/src/components/ui -name "*.tsx" 2>/dev/null | wc -l)
log_info "Shared UI components: $SHARED_COMPONENTS"

DASHBOARD_LOCAL=$(find handoff/20250928/40_App/frontend-dashboard/src/components/ui -name "*.tsx" 2>/dev/null | wc -l)
log_info "Frontend-dashboard local components: $DASHBOARD_LOCAL"

CONSOLE_LOCAL=$(find handoff/20250928/40_App/owner-console/src/components/ui -name "*.tsx" 2>/dev/null | wc -l)
log_info "Owner-console local components: $CONSOLE_LOCAL"

DUPLICATES=$(comm -12 \
  <(find packages/shared-ui/src/components/ui -name "*.tsx" -exec basename {} \; 2>/dev/null | sort) \
  <(find handoff/20250928/40_App/frontend-dashboard/src/components/ui -name "*.tsx" -exec basename {} \; 2>/dev/null | sort))

if [ -z "$DUPLICATES" ]; then
  log_pass "No duplicate component names between shared-ui and frontend-dashboard"
else
  log_warn "Duplicate component names found:"
  echo "$DUPLICATES" | while read -r dup; do
    echo "    - $dup"
  done
fi

DASHBOARD_SHARED_IMPORTS=$(grep -r "from '@morningai/shared-ui'" handoff/20250928/40_App/frontend-dashboard/src --include="*.tsx" --include="*.ts" 2>/dev/null | wc -l)
CONSOLE_SHARED_IMPORTS=$(grep -r "from '@morningai/shared-ui'" handoff/20250928/40_App/owner-console/src --include="*.tsx" --include="*.ts" 2>/dev/null | wc -l)

log_info "Frontend-dashboard shared-ui imports: $DASHBOARD_SHARED_IMPORTS"
log_info "Owner-console shared-ui imports: $CONSOLE_SHARED_IMPORTS"

if [ $DASHBOARD_SHARED_IMPORTS -gt 0 ] || [ $CONSOLE_SHARED_IMPORTS -gt 0 ]; then
  log_pass "Apps are importing from @morningai/shared-ui"
else
  log_warn "No shared-ui imports detected in apps - migration may be incomplete"
fi

log_section "3. Design Tokens Enforcement"

HEX_VIOLATIONS=$(grep -r "#[0-9A-Fa-f]\{6\}" \
  handoff/20250928/40_App/frontend-dashboard/src \
  handoff/20250928/40_App/owner-console/src \
  packages/shared-ui/src \
  --include="*.tsx" --include="*.ts" \
  --exclude="tokens.json" --exclude="*.config.*" \
  2>/dev/null | wc -l)

if [ $HEX_VIOLATIONS -eq 0 ]; then
  log_pass "No hard-coded hex colors in component files"
else
  log_warn "$HEX_VIOLATIONS instances of hard-coded hex colors found"
  if [ "$VERBOSE" = true ]; then
    grep -r "#[0-9A-Fa-f]\{6\}" \
      handoff/20250928/40_App/frontend-dashboard/src \
      handoff/20250928/40_App/owner-console/src \
      packages/shared-ui/src \
      --include="*.tsx" --include="*.ts" \
      --exclude="tokens.json" --exclude="*.config.*" \
      2>/dev/null | head -10
  fi
fi

INLINE_STYLES=$(grep -r "style={{" \
  handoff/20250928/40_App/frontend-dashboard/src \
  handoff/20250928/40_App/owner-console/src \
  packages/shared-ui/src \
  --include="*.tsx" \
  2>/dev/null | wc -l)

if [ $INLINE_STYLES -eq 0 ]; then
  log_pass "No inline styles found"
elif [ $INLINE_STYLES -lt 50 ]; then
  log_warn "$INLINE_STYLES instances of inline styles (acceptable if < 50)"
else
  log_fail "$INLINE_STYLES instances of inline styles (should be < 50)"
fi

if [ -f "packages/shared-ui/src/tokens.json" ]; then
  log_pass "Design tokens file exists (packages/shared-ui/src/tokens.json)"
else
  log_fail "Design tokens file missing (packages/shared-ui/src/tokens.json)"
fi

log_section "4. Accessibility Compliance"

if grep -q "eslint-plugin-jsx-a11y" handoff/20250928/40_App/frontend-dashboard/package.json; then
  log_pass "eslint-plugin-jsx-a11y installed in frontend-dashboard"
else
  log_fail "eslint-plugin-jsx-a11y missing in frontend-dashboard"
fi

A11Y_TOOLS=$(grep -E "vitest-axe|jest-axe|@axe-core" handoff/20250928/40_App/frontend-dashboard/package.json | wc -l)
if [ $A11Y_TOOLS -gt 0 ]; then
  log_pass "Accessibility testing tools installed (axe-core, jest-axe, or vitest-axe)"
else
  log_warn "No accessibility testing tools found"
fi

A11Y_TESTS=$(find handoff/20250928/40_App/frontend-dashboard/src -name "*.a11y.test.*" -o -name "*.axe.test.*" 2>/dev/null | wc -l)
log_info "Accessibility test files: $A11Y_TESTS"

if [ $A11Y_TESTS -gt 0 ]; then
  log_pass "$A11Y_TESTS accessibility test files found"
else
  log_warn "No dedicated accessibility test files found"
fi

IMG_NO_ALT=$(grep -r "<img" handoff/20250928/40_App/frontend-dashboard/src --include="*.tsx" 2>/dev/null | grep -v "alt=" | wc -l)
if [ $IMG_NO_ALT -eq 0 ]; then
  log_pass "No <img> tags without alt attributes detected"
else
  log_warn "$IMG_NO_ALT <img> tag(s) potentially missing alt attributes"
fi

log_section "5. Motion & Animation Governance"

REDUCED_MOTION_CSS=$(grep -r "prefers-reduced-motion" handoff/20250928/40_App/frontend-dashboard/src --include="*.css" 2>/dev/null | wc -l)
REDUCED_MOTION_JS=$(grep -r "prefers-reduced-motion" handoff/20250928/40_App/frontend-dashboard/src --include="*.tsx" --include="*.ts" 2>/dev/null | wc -l)

if [ $REDUCED_MOTION_CSS -gt 0 ] || [ $REDUCED_MOTION_JS -gt 0 ]; then
  log_pass "prefers-reduced-motion support detected (CSS: $REDUCED_MOTION_CSS, JS: $REDUCED_MOTION_JS)"
else
  log_fail "No prefers-reduced-motion support found"
fi

FRAMER_USAGE=$(grep -r "from 'framer-motion'" handoff/20250928/40_App/frontend-dashboard/src packages/shared-ui/src --include="*.tsx" --include="*.ts" 2>/dev/null | wc -l)
log_info "Framer Motion usage: $FRAMER_USAGE files"

REDUCED_MOTION_WRAPPER=$(grep -r "withReducedMotion" handoff/20250928/40_App/frontend-dashboard/src packages/shared-ui/src --include="*.tsx" --include="*.ts" 2>/dev/null | wc -l)
if [ $REDUCED_MOTION_WRAPPER -gt 0 ]; then
  log_pass "withReducedMotion wrapper usage detected"
else
  log_warn "No withReducedMotion wrapper usage found (verify manual implementation)"
fi

log_section "6. Internationalization (i18n)"

if grep -q "react-i18next\|i18next" handoff/20250928/40_App/frontend-dashboard/package.json; then
  log_pass "i18n library (react-i18next/i18next) installed"
else
  log_warn "No i18n library detected"
fi

I18N_USAGE=$(grep -rE "useTranslation|t\(" handoff/20250928/40_App/frontend-dashboard/src --include="*.tsx" --include="*.ts" 2>/dev/null | wc -l)
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

STORY_FILES=$(find handoff/20250928/40_App/frontend-dashboard/src -name "*.stories.*" 2>/dev/null | wc -l)
log_info "Storybook story files: $STORY_FILES"

if [ $STORY_FILES -gt 20 ]; then
  log_pass "$STORY_FILES story files found"
elif [ $STORY_FILES -gt 0 ]; then
  log_warn "Only $STORY_FILES story files found - consider adding more"
else
  log_warn "No Storybook stories found"
fi

VRT_TESTS=$(grep -r "@vrt" handoff/20250928/40_App/frontend-dashboard --include="*.spec.*" --include="*.test.*" 2>/dev/null | wc -l)
if [ $VRT_TESTS -gt 0 ]; then
  log_pass "$VRT_TESTS visual regression tests (@vrt) found"
else
  log_warn "No visual regression tests (@vrt) found"
fi

DOCS_MISSING=0
for doc in "DESIGN_SYSTEM_GUIDELINES.md" "CODE_DUPLICATION_ANALYSIS.md" "SHARED_COMPONENT_MIGRATION_PLAN.md"; do
  if [ ! -f "$doc" ]; then
    ((DOCS_MISSING++))
    log_info "Missing: $doc"
  fi
done

if [ $DOCS_MISSING -eq 0 ]; then
  log_pass "All key design system documentation files present"
else
  log_warn "$DOCS_MISSING key documentation file(s) missing"
fi

log_section "8. React Version Alignment"

REACT_VERSIONS=$(grep -h '"react":' package.json packages/*/package.json handoff/20250928/40_App/*/package.json 2>/dev/null | sort -u | wc -l)

if [ $REACT_VERSIONS -eq 1 ]; then
  log_pass "React version consistent across all packages"
else
  log_warn "Multiple React versions detected ($REACT_VERSIONS different versions)"
  if [ "$VERBOSE" = true ]; then
    grep -h '"react":' package.json packages/*/package.json handoff/20250928/40_App/*/package.json 2>/dev/null | sort -u
  fi
fi

if grep -q '"react": "\^19' package.json; then
  log_pass "Using React 19 (latest)"
else
  log_warn "Not using React 19 - consider upgrading"
fi

log_section "Audit Summary"

TOTAL_CHECKS=$((PASS_COUNT + WARN_COUNT + FAIL_COUNT))

echo ""
echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║                         AUDIT RESULTS                              ║"
echo "╠════════════════════════════════════════════════════════════════════╣"
printf "║  ${GREEN}✓ PASSED${NC}:  %-54s ║\n" "$PASS_COUNT / $TOTAL_CHECKS"
printf "║  ${YELLOW}⚠ WARNINGS${NC}: %-54s ║\n" "$WARN_COUNT / $TOTAL_CHECKS"
printf "║  ${RED}✗ FAILED${NC}:  %-54s ║\n" "$FAIL_COUNT / $TOTAL_CHECKS"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

if [ $FAIL_COUNT -eq 0 ] && [ $WARN_COUNT -eq 0 ]; then
  echo -e "${GREEN}🎉 All checks passed! Design system is in excellent condition.${NC}"
  exit 0
elif [ $FAIL_COUNT -eq 0 ]; then
  echo -e "${YELLOW}⚠️  Audit completed with $WARN_COUNT warning(s). Review recommended.${NC}"
  if [ "$CI_MODE" = true ]; then
    exit 2
  else
    exit 0
  fi
else
  echo -e "${RED}❌ Audit failed with $FAIL_COUNT critical issue(s) and $WARN_COUNT warning(s).${NC}"
  echo -e "${RED}   Please address the failures before proceeding.${NC}"
  exit 1
fi
