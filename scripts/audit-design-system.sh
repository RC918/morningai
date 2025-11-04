#!/bin/bash

set -euo pipefail

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0
INFO=0

REPORT_FILE="audit-design-system-report.md"

init_report() {
    cat > "$REPORT_FILE" << EOF

**Generated**: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
**Branch**: $(git branch --show-current)
**Commit**: $(git rev-parse --short HEAD)

---


This report provides a comprehensive audit of the MorningAI design system, covering:
- Token usage and scoping
- Component consistency
- Accessibility compliance (WCAG 2.1 AA)
- Dependency management
- CI/CD integration

---


EOF
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    echo "### ❌ ERROR: $1" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    ((ERRORS++))
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
    echo "### ⚠️  WARNING: $1" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    ((WARNINGS++))
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
    echo "### ℹ️  INFO: $1" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    ((INFO++))
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
    echo "### ✅ SUCCESS: $1" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
}

log_section() {
    echo ""
    echo -e "${BLUE}=== $1 ===${NC}"
    echo "" >> "$REPORT_FILE"
    echo "## $1" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
}

check_hardcoded_colors() {
    log_section "1. Hardcoded Color Check"
    
    SCAN_DIRS=(
        "handoff/20250928/40_App/frontend-dashboard/src"
        "handoff/20250928/40_App/owner-console/src"
    )
    
    EXCLUDE_PATTERN="tokens\.json|tailwind\.config\.(js|ts)|\.test\.(tsx?|jsx?)$|\.stories\.(tsx?|jsx?)$|__tests__|design-tokens\.(ts|js)|/lib/"
    
    echo "Scanning for hardcoded hex colors in source files..."
    
    local found_violations=0
    
    for dir in "${SCAN_DIRS[@]}"; do
        if [ -d "$dir" ]; then
            echo "Checking $dir..."
            
            while IFS= read -r file; do
                if echo "$file" | grep -Eq "$EXCLUDE_PATTERN"; then
                    continue
                fi
                
                local matches=$(grep -nE '(#[0-9a-fA-F]{3}([^0-9a-fA-F]|$)|#[0-9a-fA-F]{6}([^0-9a-fA-F]|$))' "$file" 2>/dev/null | grep -v 'var(--' | grep -v 'Issue #' || true)
                
                if [ -n "$matches" ]; then
                    log_error "Hardcoded hex colors found in: $file"
                    echo '```' >> "$REPORT_FILE"
                    echo "$matches" >> "$REPORT_FILE"
                    echo '```' >> "$REPORT_FILE"
                    echo "" >> "$REPORT_FILE"
                    ((found_violations++))
                fi
            done < <(find "$dir" -type f \( -name "*.tsx" -o -name "*.jsx" -o -name "*.ts" -o -name "*.js" \) 2>/dev/null)
        fi
    done
    
    if [ $found_violations -eq 0 ]; then
        log_success "No hardcoded hex colors found in source files"
    else
        log_error "Found $found_violations file(s) with hardcoded hex colors. Use design tokens instead."
    fi
}

check_theme_container() {
    log_section "2. Theme Container Check"
    
    echo "Checking for .theme-morning-ai container usage..."
    
    local app_files=(
        "handoff/20250928/40_App/frontend-dashboard/src/App.tsx"
        "handoff/20250928/40_App/owner-console/src/App.tsx"
    )
    
    local found_container=0
    
    for app_file in "${app_files[@]}"; do
        if [ -f "$app_file" ]; then
            if grep -q "theme-morning-ai" "$app_file"; then
                log_success "Theme container found in: $app_file"
                ((found_container++))
            else
                log_error "Theme container NOT found in: $app_file"
                echo "**Expected**: Root element should have \`.theme-morning-ai\` class" >> "$REPORT_FILE"
                echo "" >> "$REPORT_FILE"
            fi
        fi
    done
    
    if [ $found_container -eq 0 ]; then
        log_error "No theme containers found. Tokens may pollute global scope."
    fi
}

check_tailwind_css_vars() {
    log_section "3. Tailwind CSS Variable Integration"
    
    echo "Checking Tailwind config for CSS variable mapping..."
    
    local tailwind_config="handoff/20250928/40_App/frontend-dashboard/tailwind.config.js"
    
    if [ -f "$tailwind_config" ]; then
        if grep -q "var(--" "$tailwind_config"; then
            log_success "Tailwind config uses CSS variables"
        else
            log_warning "Tailwind config does NOT use CSS variables. Consider mapping tokens to CSS vars."
            echo "**Recommendation**: Map design tokens to CSS variables in \`theme.extend.colors\`" >> "$REPORT_FILE"
            echo '```javascript' >> "$REPORT_FILE"
            echo "colors: {" >> "$REPORT_FILE"
            echo "  primary: 'var(--color-primary-500)'," >> "$REPORT_FILE"
            echo "  'primary-foreground': 'var(--color-primary-50)'," >> "$REPORT_FILE"
            echo "  // ..." >> "$REPORT_FILE"
            echo "}" >> "$REPORT_FILE"
            echo '```' >> "$REPORT_FILE"
            echo "" >> "$REPORT_FILE"
        fi
    else
        log_error "Tailwind config not found: $tailwind_config"
    fi
}

check_skip_navigation() {
    log_section "4. Accessibility - Skip Navigation"
    
    echo "Checking for skip navigation link..."
    
    local app_files=(
        "handoff/20250928/40_App/frontend-dashboard/src/App.tsx"
        "handoff/20250928/40_App/owner-console/src/App.tsx"
    )
    
    local found_skip_link=0
    
    for app_file in "${app_files[@]}"; do
        if [ -f "$app_file" ]; then
            if grep -qE "(SkipToContent|skip.*content|href=\"#main-content\")" "$app_file"; then
                log_success "Skip navigation found in: $app_file"
                ((found_skip_link++))
            else
                log_warning "Skip navigation NOT found in: $app_file"
                echo "**WCAG 2.1 AA Requirement**: Provide skip link for keyboard users" >> "$REPORT_FILE"
                echo "" >> "$REPORT_FILE"
            fi
        fi
    done
    
    if [ $found_skip_link -eq 0 ]; then
        log_error "No skip navigation links found. Required for WCAG 2.1 AA compliance."
    fi
}

check_aria_live_regions() {
    log_section "5. Accessibility - ARIA Live Regions"
    
    echo "Checking for ARIA live regions usage..."
    
    local src_dirs=(
        "handoff/20250928/40_App/frontend-dashboard/src"
        "handoff/20250928/40_App/owner-console/src"
    )
    
    local live_region_count=0
    
    for dir in "${src_dirs[@]}"; do
        if [ -d "$dir" ]; then
            live_region_count=$(grep -rE 'aria-live=|role="(alert|status)"' "$dir" 2>/dev/null | wc -l)
        fi
    done
    
    echo "Found $live_region_count ARIA live region usage(s)"
    
    if [ $live_region_count -lt 5 ]; then
        log_warning "Low ARIA live region usage ($live_region_count instances). Consider adding for dynamic content updates."
        echo "**Recommendation**: Use \`aria-live\`, \`role=\"alert\"\`, or \`role=\"status\"\` for:" >> "$REPORT_FILE"
        echo "- Save status indicators" >> "$REPORT_FILE"
        echo "- Error messages" >> "$REPORT_FILE"
        echo "- Toast notifications" >> "$REPORT_FILE"
        echo "- Form validation feedback" >> "$REPORT_FILE"
        echo "" >> "$REPORT_FILE"
    else
        log_success "Adequate ARIA live region usage found ($live_region_count instances)"
    fi
}

check_focus_management() {
    log_section "6. Accessibility - Focus Management"
    
    echo "Checking for focus management patterns..."
    
    local src_dirs=(
        "handoff/20250928/40_App/frontend-dashboard/src"
        "handoff/20250928/40_App/owner-console/src"
    )
    
    local focus_patterns=0
    
    for dir in "${src_dirs[@]}"; do
        if [ -d "$dir" ]; then
            focus_patterns=$(grep -rE '(focus-visible|focus-within|focus:|tabIndex|autoFocus)' "$dir" 2>/dev/null | wc -l)
        fi
    done
    
    echo "Found $focus_patterns focus management pattern(s)"
    
    if [ $focus_patterns -lt 10 ]; then
        log_warning "Limited focus management patterns found ($focus_patterns instances)"
        echo "**Recommendation**: Ensure proper focus management for:" >> "$REPORT_FILE"
        echo "- Modal dialogs (trap focus)" >> "$REPORT_FILE"
        echo "- Dropdown menus (keyboard navigation)" >> "$REPORT_FILE"
        echo "- Form validation (focus on first error)" >> "$REPORT_FILE"
        echo "" >> "$REPORT_FILE"
    else
        log_success "Good focus management patterns found ($focus_patterns instances)"
    fi
}

check_dependency_management() {
    log_section "7. Dependency Management"
    
    echo "Checking for forbidden lock files..."
    
    local forbidden_files=(
        "package-lock.json"
        "yarn.lock"
    )
    
    local found_forbidden=0
    
    for file in "${forbidden_files[@]}"; do
        if find . -name "$file" -not -path "*/node_modules/*" 2>/dev/null | grep -q .; then
            log_error "Forbidden lock file found: $file"
            echo "**Policy**: Only \`pnpm-lock.yaml\` is allowed" >> "$REPORT_FILE"
            echo "" >> "$REPORT_FILE"
            ((found_forbidden++))
        fi
    done
    
    if [ $found_forbidden -eq 0 ]; then
        log_success "No forbidden lock files found (pnpm-only policy enforced)"
    fi
    
    if [ -f "pnpm-lock.yaml" ]; then
        log_success "pnpm-lock.yaml found"
    else
        log_error "pnpm-lock.yaml NOT found"
    fi
}

check_vercel_config() {
    log_section "8. Vercel Configuration"
    
    echo "Checking Vercel config for pnpm usage..."
    
    if [ -f "vercel.json" ]; then
        if grep -q "pnpm install" "vercel.json"; then
            log_success "Vercel config uses pnpm install"
        else
            log_error "Vercel config does NOT use pnpm install"
            echo "**Required**: \`installCommand\` must use \`pnpm install\`" >> "$REPORT_FILE"
            echo "" >> "$REPORT_FILE"
        fi
        
        if grep -q '"rootDirectory"' "vercel.json"; then
            log_warning "Vercel config has rootDirectory set. May cause issues with monorepo."
        fi
    else
        log_info "vercel.json not found (may be optional)"
    fi
}

check_design_tokens_files() {
    log_section "9. Design Tokens Files"
    
    echo "Checking for design tokens files..."
    
    local required_files=(
        "handoff/20250928/40_App/frontend-dashboard/public/tokens.json"
        "handoff/20250928/40_App/frontend-dashboard/src/lib/design-tokens.ts"
        "packages/shared-ui/src/tokens.json"
    )
    
    local missing_files=0
    
    for file in "${required_files[@]}"; do
        if [ -f "$file" ]; then
            log_success "Found: $file"
        else
            log_error "Missing: $file"
            ((missing_files++))
        fi
    done
    
    if [ $missing_files -eq 0 ]; then
        log_success "All design token files present"
    fi
}

check_storybook_config() {
    log_section "10. Storybook Configuration"
    
    echo "Checking Storybook setup..."
    
    local storybook_config="handoff/20250928/40_App/frontend-dashboard/.storybook/main.ts"
    
    if [ -f "$storybook_config" ]; then
        log_success "Storybook config found"
        
        if grep -q "addon-a11y" "$storybook_config"; then
            log_success "Storybook a11y addon configured"
        else
            log_warning "Storybook a11y addon NOT found. Recommended for accessibility testing."
        fi
        
        local story_count=$(find handoff/20250928/40_App/frontend-dashboard/src -name "*.stories.tsx" -o -name "*.stories.ts" 2>/dev/null | wc -l)
        echo "Found $story_count Storybook stories"
        
        if [ $story_count -lt 10 ]; then
            log_warning "Low story count ($story_count). Consider documenting more components."
        else
            log_success "Good story coverage ($story_count stories)"
        fi
    else
        log_warning "Storybook config not found. Consider setting up for component documentation."
    fi
}

check_existing_lint() {
    log_section "11. Existing Lint Checks"
    
    echo "Running existing lint checks..."
    
    if grep -q '"lint"' package.json; then
        echo "Running: pnpm lint"
        if pnpm lint 2>&1 | tee -a "$REPORT_FILE"; then
            log_success "Lint checks passed"
        else
            log_error "Lint checks failed. See output above."
        fi
    else
        log_info "No lint script found in package.json"
    fi
}

generate_summary() {
    log_section "Summary"
    
    echo "Audit completed!"
    echo ""
    echo "Results:"
    echo "  Errors:   $ERRORS"
    echo "  Warnings: $WARNINGS"
    echo "  Info:     $INFO"
    echo ""
    
    cat >> "$REPORT_FILE" << EOF

---


- **Errors**: $ERRORS
- **Warnings**: $WARNINGS
- **Info**: $INFO


EOF

    if [ $ERRORS -gt 0 ]; then
        echo "**Priority**: Fix all errors before merging." >> "$REPORT_FILE"
        echo "" >> "$REPORT_FILE"
    fi
    
    if [ $WARNINGS -gt 0 ]; then
        echo "**Recommended**: Address warnings to improve design system quality." >> "$REPORT_FILE"
        echo "" >> "$REPORT_FILE"
    fi
    
    cat >> "$REPORT_FILE" << EOF


1. Review this report and address all errors
2. Consult \`DEEP_INVESTIGATION_CHECKLIST.md\` for detailed investigation flow
3. Refer to \`DESIGN_SYSTEM_INVARIANTS.md\` for non-negotiable rules
4. Update components to use design tokens consistently
5. Ensure WCAG 2.1 AA compliance for all interactive elements

---

**Report generated by**: \`scripts/audit-design-system.sh\`
**CTO Responsibility**: Technical Strategy & Architecture
EOF

    echo "Report saved to: $REPORT_FILE"
    
    if [ $ERRORS -gt 0 ]; then
        exit 1
    fi
}

main() {
    echo "==================================="
    echo "  Design System Audit"
    echo "  MorningAI - CTO Level"
    echo "==================================="
    echo ""
    
    init_report
    
    check_hardcoded_colors
    check_theme_container
    check_tailwind_css_vars
    check_skip_navigation
    check_aria_live_regions
    check_focus_management
    check_dependency_management
    check_vercel_config
    check_design_tokens_files
    check_storybook_config
    check_existing_lint
    
    generate_summary
}

main "$@"
