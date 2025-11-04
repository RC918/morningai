#!/bin/bash

cd /home/ubuntu/repos/morningai

echo "============================================"
echo "GitHub Actions Workflow Security Audit"
echo "============================================"
echo ""

WORKFLOWS=$(find .github/workflows -name "*.yml" | sort)
RISK_COUNT=0
WARNING_COUNT=0
SAFE_COUNT=0

for workflow in $WORKFLOWS; do
    WORKFLOW_NAME=$(basename "$workflow")
    echo "=== $WORKFLOW_NAME ==="
    
    if grep -q "^  push:" "$workflow"; then
        if grep -A5 "^  push:" "$workflow" | grep -q "branches:"; then
            echo "  ✅ push: has branches filter"
        elif grep -A5 "^  push:" "$workflow" | grep -q "branches-ignore:"; then
            echo "  ✅ push: has branches-ignore filter"
        elif grep -A5 "^  push:" "$workflow" | grep -q "paths:"; then
            echo "  ⚠️  push: has paths filter (check if sufficient)"
            WARNING_COUNT=$((WARNING_COUNT + 1))
        else
            echo "  🔴 RISK: push triggers on ALL branches (no filter)"
            RISK_COUNT=$((RISK_COUNT + 1))
        fi
    fi
    
    if grep -q "^  pull_request:" "$workflow"; then
        if grep -A5 "^  pull_request:" "$workflow" | grep -q "branches:"; then
            echo "  ✅ pull_request: has branches filter"
        elif grep -A5 "^  pull_request:" "$workflow" | grep -q "branches-ignore:"; then
            echo "  ✅ pull_request: has branches-ignore filter"
        elif grep -A5 "^  pull_request:" "$workflow" | grep -q "paths:"; then
            echo "  ⚠️  pull_request: has paths filter (check if sufficient)"
            WARNING_COUNT=$((WARNING_COUNT + 1))
        else
            echo "  🔴 RISK: pull_request triggers on ALL PRs (no filter)"
            RISK_COUNT=$((RISK_COUNT + 1))
        fi
    fi
    
    if grep -q "workflow_dispatch:" "$workflow"; then
        echo "  ✅ workflow_dispatch: manual trigger available"
    fi
    
    if grep -q "schedule:" "$workflow"; then
        echo "  ✅ schedule: cron trigger (safe)"
    fi
    
    if grep -qi "create.*pull.*request\|gh pr create\|git_create_pr" "$workflow"; then
        echo "  ⚠️  WARNING: This workflow creates PRs!"
        echo "     - Could trigger infinite loop if not properly configured"
        WARNING_COUNT=$((WARNING_COUNT + 1))
    fi
    
    if grep -qi "git push" "$workflow"; then
        echo "  ⚠️  WARNING: This workflow pushes to branches!"
        echo "     - Could trigger other workflows"
        WARNING_COUNT=$((WARNING_COUNT + 1))
    fi
    
    echo ""
done

echo "============================================"
echo "AUDIT SUMMARY"
echo "============================================"
echo "🔴 High Risk Issues: $RISK_COUNT"
echo "⚠️  Warnings: $WARNING_COUNT"
echo ""

if [ $RISK_COUNT -gt 0 ]; then
    echo "RECOMMENDATION: Fix high risk issues immediately!"
    echo ""
    echo "Common fixes:"
    echo "1. Add branches filter:"
    echo "   on:"
    echo "     push:"
    echo "       branches: [main]"
    echo ""
    echo "2. Add branches-ignore for automated branches:"
    echo "   on:"
    echo "     push:"
    echo "       branches-ignore:"
    echo "         - 'automated/**'"
    echo "         - 'bot/**'"
    echo ""
fi

exit $RISK_COUNT
