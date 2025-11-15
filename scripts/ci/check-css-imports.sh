#!/bin/bash

set -e

echo "🔍 Checking for react-resizable-panels CSS imports..."

USES_RESIZABLE=false
ERROR_FOUND=false

for app in "handoff/20250928/40_App/frontend-dashboard" "handoff/20250928/40_App/owner-console"; do
  APP_NAME=$(basename "$app")
  
  if grep -r "from.*resizable" "$app/src" --include="*.jsx" --include="*.tsx" --include="*.js" --include="*.ts" 2>/dev/null | grep -q "@morningai/shared-ui"; then
    echo "  ✓ $APP_NAME uses resizable components from shared-ui"
    USES_RESIZABLE=true
    
    MAIN_FILES=(
      "$app/src/main.jsx"
      "$app/src/main.tsx"
      "$app/src/index.jsx"
      "$app/src/index.tsx"
      "$app/src/App.jsx"
      "$app/src/App.tsx"
    )
    
    CSS_IMPORTED=false
    for main_file in "${MAIN_FILES[@]}"; do
      if [ -f "$main_file" ]; then
        if grep -q "react-resizable-panels/styles" "$main_file" 2>/dev/null; then
          echo "    ✓ CSS import found in $(basename "$main_file")"
          CSS_IMPORTED=true
          break
        fi
      fi
    done
    
    CSS_FALLBACK=false
    INDEX_CSS_FILES=(
      "$app/src/index.css"
      "$app/src/styles/index.css"
    )
    
    for index_css in "${INDEX_CSS_FILES[@]}"; do
      if [ -f "$index_css" ]; then
        if grep -q "\[UX-SENTINEL\].*Resizable Panels" "$index_css" 2>/dev/null; then
          echo "    ✓ CSS fallback found in $(basename "$index_css")"
          CSS_FALLBACK=true
          break
        fi
      fi
    done
    
    if [ "$CSS_IMPORTED" = false ] && [ "$CSS_FALLBACK" = false ]; then
      echo "    ❌ ERROR: react-resizable-panels styles not configured!"
      echo "    Either:"
      echo "    1. Import library CSS in main.jsx/tsx:"
      echo "       import 'react-resizable-panels/styles.css';"
      echo "    OR"
      echo "    2. Add CSS fallback in index.css with [UX-SENTINEL] marker"
      ERROR_FOUND=true
    fi
  fi
done

if grep -r "from.*react-resizable-panels" "packages/shared-ui/src" --include="*.tsx" --include="*.ts" 2>/dev/null | grep -q "react-resizable-panels"; then
  echo "  ✓ shared-ui uses react-resizable-panels"
  echo "    ⚠️  Apps using shared-ui resizable components must import react-resizable-panels/styles.css"
fi

if [ "$USES_RESIZABLE" = false ]; then
  echo "  ℹ️  No resizable components found in apps, skipping CSS check"
fi

if [ "$ERROR_FOUND" = true ]; then
  echo ""
  echo "❌ CSS import check FAILED"
  echo "Missing react-resizable-panels CSS imports will cause accessibility labels to be visible."
  exit 1
fi

echo ""
echo "✅ CSS import check complete"
