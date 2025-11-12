# Tolgee Corruption Response Runbook

## Overview

This runbook provides step-by-step instructions for detecting, responding to, and fixing Tolgee translation corruption issues.

## Symptoms

### How to Detect Corruption

1. **CI Failure**: PR has failing "Validate Locale Files (Tolgee Corruption Guard)" check
2. **Demo Data in Files**: Locale files contain strings like:
   - "What to pack"
   - "add-item-add-button"
   - "delete-item-button"
   - "Quoi emballer" (French)
   - "Was mitnehmen" (German)
3. **Flat Structure**: Locale files have flat key structure instead of nested
4. **Wrong Keys**: Files contain unexpected keys not related to MorningAI

### Example of Corrupted File

```json
{
  "add-item-add-button": "Add",
  "add-item-input-placeholder": "New list item",
  "app-title": "What to pack",
  "delete-item-button": "Delete"
}
```

This is Tolgee's demo "packing list" application data, NOT MorningAI translations.

---

## Immediate Response (P0)

### Step 1: Close the Corrupted PR

**DO NOT MERGE** any PR with corrupted translations.

```bash
# Close the PR via GitHub UI or CLI
gh pr close <PR_NUMBER> --comment "Closing due to corrupted Tolgee data. See [Corruption Runbook](docs/runbooks/TOLGEE_CORRUPTION_RUNBOOK.md) for remediation steps."
```

### Step 2: Stop Any Running Tolgee Syncs

```bash
# Cancel any running Tolgee sync workflows
gh run list --workflow=tolgee-sync.yml --status=in_progress
gh run cancel <RUN_ID>
```

### Step 3: Verify Main Branch Status

Check if main branch is already corrupted:

```bash
# Check for demo data on main
cd ~/repos/morningai
git checkout main
git pull origin main

# Run validator
node scripts/validate-tolgee-structure.js
```

If main is corrupted, proceed to **Emergency Cleanup** section below.

---

## Root Cause Analysis

### Step 1: Identify the Source Project

Check which Tolgee project was synced:

```bash
# Check .tolgeerc files
cat handoff/20250928/40_App/owner-console/.tolgeerc | grep projectId
cat handoff/20250928/40_App/frontend-dashboard/.tolgeerc | grep projectId
```

### Step 2: Verify Tolgee Project Data

1. Go to https://app.tolgee.io
2. Log in with your credentials
3. Navigate to the project ID from Step 1
4. Check the translations:
   - Do they contain "What to pack" or similar demo strings?
   - Are they the correct MorningAI translations?
   - Is this a demo project?

### Step 3: Document Findings

Create an issue documenting:
- Which PR introduced the corruption
- Which Tolgee project ID was used
- What data was found in the Tolgee project
- Timeline of when corruption occurred

---

## Fix Tolgee Project Data

### Option A: Clean Existing Project

If you want to keep the same project ID:

1. **Go to Tolgee UI**: https://app.tolgee.io
2. **Select the corrupted project**
3. **Delete all demo keys**:
   - Go to Translations
   - Select all keys containing demo data
   - Delete them
4. **Import correct translations**:
   - Go to Import
   - Upload the correct locale files from your repository
   - Verify import preview
   - Confirm import

### Option B: Create New Separate Projects (Recommended)

For better isolation, create separate projects per app:

1. **Create Owner Console Project**:
   - Go to https://app.tolgee.io
   - Click "Create Project"
   - Name: "MorningAI Owner Console"
   - Note the Project ID (e.g., 24693)

2. **Create Frontend Dashboard Project**:
   - Click "Create Project"
   - Name: "MorningAI Frontend Dashboard"
   - Note the Project ID (e.g., 24702)

3. **Import Translations**:
   
   **Owner Console** (Project #24693):
   ```bash
   # Files to import:
   handoff/20250928/40_App/owner-console/src/locales/en.json
   handoff/20250928/40_App/owner-console/src/locales/en-US.json
   handoff/20250928/40_App/owner-console/src/locales/zh-TW.json
   ```
   
   **Frontend Dashboard** (Project #24702):
   ```bash
   # Files to import:
   handoff/20250928/40_App/frontend-dashboard/src/i18n/locales/en-US.json
   handoff/20250928/40_App/frontend-dashboard/src/i18n/locales/zh-TW.json
   ```

4. **Update `.tolgeerc` Files**:
   ```bash
   # Update owner-console/.tolgeerc
   {
     "projectId": 24693,  # ← New project ID
     ...
   }
   
   # Update frontend-dashboard/.tolgeerc
   {
     "projectId": 24702,  # ← New project ID
     ...
   }
   ```

5. **Update Vercel Environment Variables**:
   - Vercel Dashboard → Owner Console → Settings → Environment Variables
   - Set `VITE_TOLGEE_PROJECT_ID=24693` (Production + Preview)
   - Vercel Dashboard → Frontend Dashboard → Settings → Environment Variables
   - Set `VITE_TOLGEE_PROJECT_ID=24702` (Production + Preview)

6. **Verify API Key Access**:
   - Go to https://app.tolgee.io/account/apiKeys
   - Ensure your API key has access to both new projects
   - Update GitHub Secret `TOLGEE_API_KEY` if needed (use PAT)

---

## Emergency Cleanup (If Main is Corrupted)

### Step 1: Create Cleanup Branch

```bash
cd ~/repos/morningai
git checkout main
git pull origin main
git checkout -b fix/remove-corrupted-tolgee-data
```

### Step 2: Remove Corrupted Files

```bash
# Remove corrupted locale files
rm handoff/20250928/40_App/owner-console/src/locales/fr.json
rm handoff/20250928/40_App/owner-console/src/locales/de.json
rm handoff/20250928/40_App/frontend-dashboard/src/i18n/locales/en.json
rm handoff/20250928/40_App/frontend-dashboard/src/i18n/locales/fr.json
rm handoff/20250928/40_App/frontend-dashboard/src/i18n/locales/de.json
```

### Step 3: Verify Good Files Remain

```bash
# These files should still exist and contain correct data
ls -la handoff/20250928/40_App/owner-console/src/locales/
# Should show: en.json, en-US.json, zh-TW.json

ls -la handoff/20250928/40_App/frontend-dashboard/src/i18n/locales/
# Should show: en-US.json, zh-TW.json
```

### Step 4: Run Validator

```bash
node scripts/validate-tolgee-structure.js
# Should show: ✅ ALL VALIDATIONS PASSED
```

### Step 5: Create PR

```bash
git add -A
git commit -m "fix: Remove corrupted Tolgee demo data from locale files"
git push origin fix/remove-corrupted-tolgee-data

# Create PR
gh pr create --title "fix: Remove corrupted Tolgee demo data" \
  --body "Emergency cleanup of corrupted translations. See [Corruption Runbook](docs/runbooks/TOLGEE_CORRUPTION_RUNBOOK.md)."
```

### Step 6: Fast-Track Merge

- Get immediate review and approval
- Merge as soon as CI passes
- This is a P0 fix to restore main branch integrity

---

## Prevention

### Automated Safeguards

The repository now includes multiple layers of protection:

1. **Structured Validator** (`scripts/validate-tolgee-structure.js`):
   - Detects demo data patterns
   - Validates JSON structure
   - Checks for forbidden keys

2. **CI Validation** (`.github/workflows/frontend.yml`):
   - Runs on every PR
   - Blocks merge if corruption detected

3. **Preflight Validation** (`.github/workflows/tolgee-sync.yml`):
   - Dry-pulls before creating PR
   - Validates before committing
   - Fails early if bad data

### Manual Checks

Before merging any Tolgee sync PR:

1. **Review the diff**:
   ```bash
   gh pr diff <PR_NUMBER>
   ```
   
2. **Look for red flags**:
   - Flat structure (all keys at root level)
   - Demo-related strings
   - Unexpected language files (de.json, fr.json)
   - Large deletions of existing translations

3. **Run validator locally**:
   ```bash
   gh pr checkout <PR_NUMBER>
   node scripts/validate-tolgee-structure.js
   ```

4. **Check Tolgee project**:
   - Verify project ID in `.tolgeerc`
   - Check project data in Tolgee UI
   - Ensure it's the correct project

---

## Post-Incident Review

After resolving a corruption incident:

1. **Document the incident**:
   - Create a post-mortem issue
   - Include timeline, root cause, and resolution
   - Tag with `incident` and `tolgee`

2. **Update runbook**:
   - Add any new learnings
   - Update detection methods
   - Improve prevention steps

3. **Verify safeguards**:
   - Ensure all validation is working
   - Test preflight validation
   - Confirm CI blocks bad PRs

4. **Team communication**:
   - Share learnings with team
   - Update onboarding docs
   - Add to team knowledge base

---

## Escalation

If you cannot resolve the issue:

1. **Check GitHub Discussions**: Search for similar issues
2. **Contact Tolgee Support**: support@tolgee.io
3. **Escalate to CTO**: For critical production issues

---

## Quick Reference

### Validation Commands

```bash
# Validate locale files
node scripts/validate-tolgee-structure.js

# Check .tolgeerc project IDs
grep -r "projectId" handoff/20250928/40_App/*/.tolgeerc

# Check for demo data
grep -r "What to pack" handoff/20250928/40_App/*/src/

# List locale files
find handoff/20250928/40_App -name "*.json" -path "*/locales/*"
```

### Tolgee URLs

- **Tolgee Dashboard**: https://app.tolgee.io
- **API Keys**: https://app.tolgee.io/account/apiKeys
- **Owner Console Project**: https://app.tolgee.io/projects/24693
- **Frontend Dashboard Project**: https://app.tolgee.io/projects/24702

### Related Documentation

- [Tolgee Separation Architecture](../i18n/TOLGEE_SEPARATION.md)
- [Vercel Environment Variables](../deployment/VERCEL_ENVIRONMENT_VARIABLES.md)
- [CI/CD Documentation](../ci-cd/README.md)
