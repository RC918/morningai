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

JSON_OUTPUT_DIR=".github/artifacts"
JSON_OUTPUT_FILE="$JSON_OUTPUT_DIR/design-system-violations.json"

DIFF_ONLY="${DIFF_ONLY:-false}"
CHANGED_FILES="${CHANGED_FILES:-}"

if [ "$DIFF_ONLY" = "true" ] && [ -n "$CHANGED_FILES" ]; then
  echo -e "${BLUE}🔍 Auditing shared-ui import compliance (Stage 2: diff-only mode)...${NC}"
  echo -e "${BLUE}📝 Only checking changed files in this PR${NC}"
else
  echo -e "${BLUE}🔍 Auditing shared-ui import compliance...${NC}"
fi
echo ""

VIOLATIONS_FOUND=0
TOTAL_FILES_SCANNED=0
VIOLATIONS_JSON="[]"

CHANGED_FILES_LIST=$(mktemp)

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
VIOLATIONS_DETAILS=$(mktemp)

json_escape() {
  echo "$1" | sed 's/\\/\\\\/g; s/"/\\"/g; s/$/\\n/g' | tr -d '\n' | sed 's/\\n$//'
}

extract_package() {
  local import_line="$1"
  echo "$import_line" | grep -oP "from ['\"](\K[^'\"]+)" || echo "unknown"
}

suggest_fix() {
  local package="$1"
  local file="$2"
  
  if [[ "$package" == *"@radix-ui/react-"* ]]; then
    local component=$(echo "$package" | sed 's/@radix-ui\/react-//')
    echo "Replace with: import { ... } from '@morningai/shared-ui'. If component doesn't exist, add it to shared-ui first."
  elif [[ "$package" == *"@mui/"* ]]; then
    echo "Replace with equivalent @morningai/shared-ui component. MUI is not allowed due to design inconsistency."
  elif [[ "$package" == *"@headlessui/"* ]]; then
    echo "Replace with @morningai/shared-ui (based on Radix UI). Headless UI overlaps with our Radix-based components."
  elif [[ "$package" == *"@chakra-ui/"* ]]; then
    echo "Replace with @morningai/shared-ui component. Chakra UI is not allowed due to design inconsistency."
  else
    echo "Replace with @morningai/shared-ui equivalent component."
  fi
}

should_scan_file() {
  local file=$1
  
  if [ "$DIFF_ONLY" != "true" ]; then
    return 0
  fi
  
  if [ -z "$CHANGED_FILES" ]; then
    return 1
  fi
  
  grep -Fxq "$file" "$CHANGED_FILES_LIST" 2>/dev/null
  return $?
}

if [ "$DIFF_ONLY" = "true" ] && [ -n "$CHANGED_FILES" ]; then
  echo "$CHANGED_FILES" > "$CHANGED_FILES_LIST"
  CHANGED_COUNT=$(echo "$CHANGED_FILES" | grep -c '^' || echo "0")
  echo -e "${BLUE}📋 Changed files to audit: $CHANGED_COUNT${NC}"
  echo ""
fi

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
    
    if ! should_scan_file "$file"; then
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
            
            line_num=$(echo "$line" | cut -d: -f1)
            import_statement=$(echo "$line" | cut -d: -f2-)
            package=$(extract_package "$import_statement")
            suggested_fix=$(suggest_fix "$package" "$file")
            
            code_snippet=$(sed -n "$((line_num-1)),$((line_num+1))p" "$file" 2>/dev/null | sed 's/"/\\"/g' | sed ':a;N;$!ba;s/\n/\\n/g')
            
            cat >> "$VIOLATIONS_DETAILS" <<EOF
{
  "file": "$(json_escape "$file")",
  "line": $line_num,
  "import": "$(json_escape "$import_statement")",
  "package": "$(json_escape "$package")",
  "rule": "no-direct-ui-library-imports",
  "severity": "warning",
  "suggestedFix": "$(json_escape "$suggested_fix")",
  "componentMapping": "See docs/DESIGN_SYSTEM_ENFORCEMENT.md",
  "autofixable": false,
  "confidence": "high",
  "codeSnippet": "$(json_escape "$code_snippet")"
},
EOF
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

mkdir -p "$JSON_OUTPUT_DIR"

if [ -f "$VIOLATIONS_DETAILS" ] && [ -s "$VIOLATIONS_DETAILS" ]; then
  VIOLATIONS_JSON=$(cat "$VIOLATIONS_DETAILS" | sed '$ s/,$//')
  VIOLATIONS_JSON="[$VIOLATIONS_JSON]"
else
  VIOLATIONS_JSON="[]"
fi

GIT_REPO="${GIT_REPO:-${GITHUB_REPOSITORY:-RC918/morningai}}"
GIT_PR="${GIT_PR:-${GITHUB_PR_NUMBER:-unknown}}"
GIT_COMMIT="${GIT_COMMIT:-${GITHUB_SHA:-$(git rev-parse HEAD 2>/dev/null || echo 'unknown')}}"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

if [ "$DIFF_ONLY" = "true" ]; then
  STAGE_NUM=2
  STAGE_NAME="diff-only-enforcement"
  IS_BLOCKING=true
else
  STAGE_NUM=1
  STAGE_NAME="warn"
  IS_BLOCKING=false
fi

cat > "$JSON_OUTPUT_FILE" <<EOF
{
  "version": "1.0",
  "gateId": "design-system-enforcement",
  "repo": "$GIT_REPO",
  "pr": "$GIT_PR",
  "commit": "$GIT_COMMIT",
  "stage": $STAGE_NUM,
  "stageName": "$STAGE_NAME",
  "timestamp": "$TIMESTAMP",
  "summary": {
    "filesScanned": $TOTAL_FILES_SCANNED,
    "violationsFound": $VIOLATIONS_FOUND,
    "blocking": $IS_BLOCKING,
    "diffOnly": $([ "$DIFF_ONLY" = "true" ] && echo "true" || echo "false")
  },
  "violations": $VIOLATIONS_JSON,
  "quickFixGuide": "docs/DESIGN_SYSTEM_QUICKSTART.md",
  "documentation": "docs/DESIGN_SYSTEM_ENFORCEMENT.md",
  "allowedExceptions": [
    "lucide-react (icons)",
    "recharts (charts)",
    "date-fns (date utilities)"
  ],
  "restrictedPackages": [
    "@radix-ui/react-*",
    "@mui/*",
    "@headlessui/*",
    "@chakra-ui/*"
  ]
}
EOF

echo -e "${GREEN}📄 JSON artifact generated: $JSON_OUTPUT_FILE${NC}"
echo ""

if [ $VIOLATIONS_FOUND -gt 0 ]; then
  if [ "$DIFF_ONLY" = "true" ]; then
    echo -e "${RED}❌ Stage 2 (Diff-Only Enforcement): Violations detected - BLOCKING${NC}"
    echo ""
    echo -e "${BLUE}📝 Required Actions:${NC}"
    echo "1. Replace direct UI library imports with @morningai/shared-ui components"
    echo "2. If component doesn't exist in shared-ui, add it to shared-ui first"
    echo "3. Allowed exceptions: lucide-react (icons), recharts (charts), date-fns (dates)"
    echo ""
    echo -e "${BLUE}📚 Documentation:${NC}"
    echo "See docs/DESIGN_SYSTEM_ENFORCEMENT.md for details"
    echo "See docs/DESIGN_SYSTEM_QUICKSTART.md for quick fixes (2-minute guide)"
    echo ""
    echo -e "${RED}🚨 This PR cannot be merged until violations are resolved${NC}"
    echo -e "${YELLOW}Emergency override: Contact @RC918 for admin approval${NC}"
  else
    echo -e "${YELLOW}⚠️  Stage 1 (Warn Mode): Violations detected but not blocking${NC}"
    echo ""
    echo -e "${BLUE}📝 Recommended Actions:${NC}"
    echo "1. Replace direct UI library imports with @morningai/shared-ui components"
    echo "2. If component doesn't exist in shared-ui, consider adding it"
    echo "3. Allowed exceptions: lucide-react (icons), recharts (charts), date-fns (dates)"
    echo ""
    echo -e "${BLUE}📚 Documentation:${NC}"
    echo "See docs/DESIGN_SYSTEM_ENFORCEMENT.md for details"
    echo "See docs/DESIGN_SYSTEM_QUICKSTART.md for quick fixes (2-minute guide)"
  fi
  
  if [ -n "$GITHUB_OUTPUT" ]; then
    echo "violations_count=$VIOLATIONS_FOUND" >> "$GITHUB_OUTPUT"
    echo "files_scanned=$TOTAL_FILES_SCANNED" >> "$GITHUB_OUTPUT"
    echo "json_artifact=$JSON_OUTPUT_FILE" >> "$GITHUB_OUTPUT"
  fi
  
  if [ "$DIFF_ONLY" = "true" ]; then
    rm -f "$VIOLATIONS_FILE" "$VIOLATIONS_DETAILS" "$CHANGED_FILES_LIST"
    exit 1
  else
    rm -f "$VIOLATIONS_FILE" "$VIOLATIONS_DETAILS" "$CHANGED_FILES_LIST"
    exit 0
  fi
else
  if [ "$DIFF_ONLY" = "true" ]; then
    echo -e "${GREEN}✅ Stage 2: No violations found in changed files - all imports comply${NC}"
  else
    echo -e "${GREEN}✅ No violations found - all imports comply with shared-ui policy${NC}"
  fi
  
  if [ -n "$GITHUB_OUTPUT" ]; then
    echo "violations_count=0" >> "$GITHUB_OUTPUT"
    echo "files_scanned=$TOTAL_FILES_SCANNED" >> "$GITHUB_OUTPUT"
    echo "json_artifact=$JSON_OUTPUT_FILE" >> "$GITHUB_OUTPUT"
  fi
  
  rm -f "$VIOLATIONS_FILE" "$VIOLATIONS_DETAILS" "$CHANGED_FILES_LIST"
  exit 0
fi
