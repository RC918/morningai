# Tolgee Project Separation Architecture

## Overview

As of November 2025, the MorningAI platform uses **separate Tolgee projects** for each application to ensure complete isolation of translations and prevent cross-app contamination.

## Architecture

### Previous Setup (Deprecated)
```
❌ Single Shared Project
├─ Project #23882 (Demo "What to pack" app)
   ├─ Owner Console translations (mixed)
   └─ Frontend Dashboard translations (mixed)
```

**Problems**:
- Demo data contamination ("What to pack" packing list app)
- No isolation between apps
- Key collisions and confusion
- Difficult to manage independent release cycles

### Current Setup (Active)
```
✅ Separate Projects per App
├─ Project #24693 (Owner Console)
│  ├─ Languages: en, en-US, zh-TW
│  └─ Fully isolated from other apps
│
└─ Project #24702 (Frontend Dashboard)
   ├─ Languages: en-US, zh-TW
   └─ Fully isolated from other apps
```

**Benefits**:
- ✅ Complete isolation between apps
- ✅ Independent translation lifecycle management
- ✅ Smaller translation bundles (no cross-app bloat)
- ✅ Easier auditing and rollback per app
- ✅ Better CI validation (app-specific checks)
- ✅ No risk of cross-app contamination

## Configuration

### Owner Console

**Tolgee Project**: #24693  
**Location**: `handoff/20250928/40_App/owner-console/`

**CLI Configuration** (`.tolgeerc`):
```json
{
  "projectId": 24693,
  "apiUrl": "https://app.tolgee.io",
  "format": "JSON_I18NEXT",
  "pull": {
    "path": "./src/locales"
  }
}
```

**Runtime Configuration** (`src/tolgee.js`):
```javascript
projectId: import.meta.env.VITE_TOLGEE_PROJECT_ID  // Must be 24693
```

**Allowed Locales**:
- `en.json` - English (nested structure with 2FA keys)
- `en-US.json` - English US (main translation file)
- `zh-TW.json` - Traditional Chinese (Taiwan)

**Vercel Environment Variable**:
```
VITE_TOLGEE_PROJECT_ID=24693
```
(Set for both Production and Preview environments)

---

### Frontend Dashboard

**Tolgee Project**: #24702  
**Location**: `handoff/20250928/40_App/frontend-dashboard/`

**CLI Configuration** (`.tolgeerc`):
```json
{
  "projectId": 24702,
  "apiUrl": "https://app.tolgee.io",
  "format": "JSON_I18NEXT",
  "pull": {
    "path": "./src/i18n/locales"
  }
}
```

**Runtime Configuration** (`src/i18n/tolgee.js`):
```javascript
projectId: import.meta.env.VITE_TOLGEE_PROJECT_ID  // Must be 24702
```

**Allowed Locales**:
- `en-US.json` - English US (main translation file)
- `zh-TW.json` - Traditional Chinese (Taiwan)

**Vercel Environment Variable**:
```
VITE_TOLGEE_PROJECT_ID=24702
```
(Set for both Production and Preview environments)

---

## Important Notes

### CLI vs Runtime Configuration

⚠️ **Critical**: There are TWO separate configurations:

1. **CLI Configuration** (`.tolgeerc`):
   - Used by `tolgee pull` command during development and CI
   - Determines which Tolgee project to sync FROM
   - Location: `.tolgeerc` file in each app directory

2. **Runtime Configuration** (Environment Variables):
   - Used by the application at runtime (in browser)
   - Determines which Tolgee project the app connects to for in-context editing
   - Location: Vercel environment variables (`VITE_TOLGEE_PROJECT_ID`)

**Both must match!** If they don't match, you'll sync from one project but connect to another at runtime.

### Vercel Environment Variables Setup

For each app, you need to set `VITE_TOLGEE_PROJECT_ID` in **both environments**:

1. **Production Environment**:
   - Vercel Dashboard → Project → Settings → Environment Variables
   - Add: `VITE_TOLGEE_PROJECT_ID` = `24693` (Owner Console) or `24702` (Frontend Dashboard)
   - Environment: Production

2. **Preview Environment**:
   - Same location as above
   - Add: `VITE_TOLGEE_PROJECT_ID` = `24693` (Owner Console) or `24702` (Frontend Dashboard)
   - Environment: Preview

### API Key Requirements

The `TOLGEE_API_KEY` GitHub Secret must have access to **both** projects:
- Project #24693 (Owner Console)
- Project #24702 (Frontend Dashboard)

**Recommended**: Use a **Personal Access Token (PAT)** or **Organization-scoped token** instead of project-scoped keys.

To verify access:
1. Go to https://app.tolgee.io/account/apiKeys
2. Check that your API key has access to both projects
3. If not, create a new PAT with appropriate permissions

---

## Validation and Safety

### Automated Validation

The repository includes automated validation to prevent corrupted translations:

1. **Structured Validator** (`scripts/validate-tolgee-structure.js`):
   - Parses JSON and checks for demo data patterns
   - Validates structure (nested vs flat)
   - Checks for forbidden keys
   - Verifies only allowed locale files exist

2. **CI Integration** (`.github/workflows/frontend.yml`):
   - Runs validator on every PR
   - Blocks merge if demo data detected
   - Ensures locale files are clean

3. **Preflight Validation** (`.github/workflows/tolgee-sync.yml`):
   - Dry-pulls translations before creating PR
   - Validates structure before committing
   - Fails early if Tolgee project has bad data

### Manual Validation

To manually validate locale files:
```bash
node scripts/validate-tolgee-structure.js
```

Expected output:
```
✅ ALL VALIDATIONS PASSED - Locale files are clean!
```

---

## Migration History

### Timeline

1. **Before Nov 11, 2025**: Single shared project #23882 (demo data)
2. **Nov 11, 2025**: 
   - Created separate projects #24693 and #24702
   - Cleaned corrupted demo data from main branch (PR #1260)
   - Updated `.tolgeerc` configurations (PR #1265)
   - Added validation and CI fixes (PR #1259)

### Related PRs

- **PR #1256** (Closed): Tolgee sync with corrupted demo data
- **PR #1259** (Merged): CI fixes + Tolgee corruption guard
- **PR #1260** (Merged): Remove corrupted demo data from locale files
- **PR #1265** (Merged): Update Tolgee project IDs to separate projects

---

## Troubleshooting

### Problem: Tolgee sync pulls empty translations

**Cause**: New Tolgee project has no translations imported yet.

**Solution**:
1. Go to https://app.tolgee.io
2. Select the appropriate project (#24693 or #24702)
3. Import translations from existing locale files:
   - Owner Console: Import `en.json`, `en-US.json`, `zh-TW.json`
   - Frontend Dashboard: Import `en-US.json`, `zh-TW.json`

### Problem: Runtime shows wrong translations

**Cause**: Vercel environment variable `VITE_TOLGEE_PROJECT_ID` not updated.

**Solution**:
1. Vercel Dashboard → Project → Settings → Environment Variables
2. Update `VITE_TOLGEE_PROJECT_ID` to correct value
3. Redeploy the application

### Problem: Tolgee sync fails with "Access Denied"

**Cause**: `TOLGEE_API_KEY` doesn't have access to new projects.

**Solution**:
1. Go to https://app.tolgee.io/account/apiKeys
2. Create a new Personal Access Token (PAT)
3. Update GitHub Secret `TOLGEE_API_KEY` with new PAT

### Problem: Demo data detected in PR

**Cause**: Tolgee project contains corrupted/demo data.

**Solution**:
1. Check which project is being synced (`.tolgeerc` projectId)
2. Go to Tolgee UI and verify project data
3. Delete demo keys or reimport correct translations
4. Re-run Tolgee sync

---

## References

- Tolgee Documentation: https://tolgee.io/docs
- Tolgee CLI: https://github.com/tolgee/tolgee-cli
- Corruption Runbook: [TOLGEE_CORRUPTION_RUNBOOK.md](../runbooks/TOLGEE_CORRUPTION_RUNBOOK.md)
- Vercel Environment Variables: [VERCEL_ENVIRONMENT_VARIABLES.md](../deployment/VERCEL_ENVIRONMENT_VARIABLES.md)
