#!/bin/bash

set -e

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

RESTRICTED_PATTERNS=(
  "@radix-ui/react-"
  "@mui/"
  "@headlessui/"
  "@chakra-ui/"
)

ALLOWED_PATTERNS=(
  "lucide-react"
  "recharts"
  "date-fns"
  "@morningai/shared-ui"
)

SCAN_DIRS=(
  "handoff/20250928/40_App/frontend-dashboard/src"
  "handoff/20250928/40_App/owner-console/src"
)

EXCLUDE_PATTERNS=(
  "*.test.tsx"
  "*.test.ts"
  "*.spec.tsx"
  "*.spec.ts"
  "*.stories.tsx"
  "*.stories.ts"
  "__tests__"
  "scripts"
  "examples"
)

echo -e "${BLUE}🔍 Auditing shared-ui import compliance...${NC}"
echo ""

VIOLATIONS_FOUND=0
TOTAL_FILES_SCANNED=0

should_exclude() {
  local file=$1
  for pattern in "${EXCLUDE_PATTERNS[@]}"; do
    if [[ "$file" == *"$pattern"* ]]; then
      return 0
    fi
  done
  return 1
}

is_allowed() {
  local import=$1
  for allowed in "${ALLOWED_PATTERNS[@]}"; do
    if [[ "$import" == *"$allowed"* ]]; then
      return 0
    fi
  done
  return 1
}

VIOLATIONS_FILE=$(mktemp)

for dir in "${SCAN_DIRS[@]}"; do
  if [ ! -d "$dir" ]; then
    echo -e "${YELLOW}⚠️  Directory not found: $dir${NC}"
    continue
  fi
  
  echo -e "${BLUE}📂 Scanning: $dir${NC}"
  
  while IFS= read -r -d '' file; do
    if should_exclude "$file"; then
      continue
    fi
    
    TOTAL_FILES_SCANNED=$((TOTAL_FILES_SCANNED + 1))
    
    for pattern in "${RESTRICTED_PATTERNS[@]}"; do
      matches=$(grep -n "import.*from.*['\"]${pattern}" "$file" 2>/dev/null || true)
      
      if [ -n "$matches" ]; then
        if ! is_allowed "$matches"; then
          VIOLATIONS_FOUND=$((VIOLATIONS_FOUND + 1))
          echo "$file" >> "$VIOLATIONS_FILE"
          echo -e "${YELLOW}⚠️  $file${NC}"
          echo "$matches" | while IFS= read -r line; do
            echo -e "   ${RED}→${NC} $line"
          done
          echo ""
        fi
      fi
    done
  done < <(find "$dir" -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \) -print0)
done

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📊 Audit Summary${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "Files scanned: ${TOTAL_FILES_SCANNED}"
echo -e "Violations found: ${VIOLATIONS_FOUND}"
echo ""

if [ $VIOLATIONS_FOUND -gt 0 ]; then
  echo -e "${YELLOW}⚠️  Stage 1 (Warn Mode): Violations detected but not blocking${NC}"
  echo ""
  echo -e "${BLUE}📝 Recommended Actions:${NC}"
  echo "1. Replace direct UI library imports with @morningai/shared-ui components"
  echo "2. If component doesn't exist in shared-ui, consider adding it"
  echo "3. Allowed exceptions: lucide-react (icons), recharts (charts), date-fns (dates)"
  echo ""
  echo -e "${BLUE}📚 Documentation:${NC}"
  echo "See docs/DESIGN_SYSTEM_ENFORCEMENT.md for details"
  echo ""
  echo -e "${YELLOW}⏰ Timeline: Stage 1 (warn) runs for 1 week, then Stage 2 (diff-only block)${NC}"
  
  if [ -n "$GITHUB_OUTPUT" ]; then
    echo "violations_count=$VIOLATIONS_FOUND" >> "$GITHUB_OUTPUT"
    echo "files_scanned=$TOTAL_FILES_SCANNED" >> "$GITHUB_OUTPUT"
  fi
  
  exit 0
else
  echo -e "${GREEN}✅ No violations found - all imports comply with shared-ui policy${NC}"
  
  if [ -n "$GITHUB_OUTPUT" ]; then
    echo "violations_count=0" >> "$GITHUB_OUTPUT"
    echo "files_scanned=$TOTAL_FILES_SCANNED" >> "$GITHUB_OUTPUT"
  fi
  
  exit 0
fi

rm -f "$VIOLATIONS_FILE"
