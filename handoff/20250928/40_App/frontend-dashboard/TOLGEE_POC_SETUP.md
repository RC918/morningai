# Tolgee POC Setup Guide

## Overview

This project now includes **Tolgee** for in-context translation management. This is a **POC (Proof of Concept)** implementation that only covers the "shell" components (Navigation, Footer, Login page).

## What is Tolgee?

Tolgee is an open-source localization platform that provides:
- **In-Context Translation**: Click on text directly in your app to edit translations
- **Collaboration**: Non-technical team members can manage translations
- **Translation Memory**: Automatic suggestions based on previous translations
- **Machine Translation**: Integration with Google Translate, DeepL, etc.

## Current Implementation

### Scope (POC Phase)
✅ **Included**:
- Navigation/Header components
- Footer
- Login page labels and buttons
- Global UI strings

❌ **Not Included** (will be added after layout is stable):
- Dashboard content
- ReportCenter
- Settings pages content
- Other internal pages

### Architecture

```
App.jsx
└── TolgeeProvider (wraps entire app)
    └── i18next (existing setup, unchanged)
        └── Components use useTranslation() as before
```

**Key Points**:
- Tolgee wraps the existing i18next setup
- No changes needed to existing `t()` calls
- In development: Tolgee provides in-context editing
- In production: Falls back to static JSON files (no Tolgee dependency)

## Setup Instructions

### 1. Sign Up for Tolgee (Free)

1. Go to https://app.tolgee.io
2. Create a free account
3. Create a new project called "Morning AI"
4. Select languages: `zh-TW` and `en-US`

### 2. Get API Credentials

1. In your Tolgee project, go to **Integrations** > **API Keys**
2. Create a new API key with **Edit** permissions
3. Copy the API key and Project ID

### 3. Configure Environment Variables

Create a `.env.local` file in the project root:

```bash
# Tolgee Configuration (Development Only)
VITE_TOLGEE_API_URL=https://app.tolgee.io
VITE_TOLGEE_API_KEY=your_api_key_here
VITE_TOLGEE_PROJECT_ID=your_project_id_here
```

**Important**: 
- `.env.local` is gitignored (never commit API keys!)
- These variables are only used in development
- Production builds use static JSON files

### 4. Upload Existing Translations

You can upload the existing translation files to Tolgee:

#### Option A: Manual Upload (Recommended for POC)
1. Go to your Tolgee project
2. Click **Import** > **Upload files**
3. Upload `src/i18n/locales/zh-TW.json` for Chinese
4. Upload `src/i18n/locales/en-US.json` for English

#### Option B: Using Tolgee CLI
```bash
# Install Tolgee CLI
npm install -g @tolgee/cli

# Push translations to Tolgee
tolgee push \
  --api-url https://app.tolgee.io \
  --api-key YOUR_API_KEY \
  --project-id YOUR_PROJECT_ID \
  --path src/i18n/locales
```

### 5. Start Development Server

```bash
npm run dev
```

### 6. Enable In-Context Translation

1. Open the app in your browser
2. Press **Alt + T** (or **Option + T** on Mac) to toggle Tolgee DevTools
3. Click on any text to edit translations directly
4. Changes are saved to Tolgee cloud immediately

## Usage

### For Developers

**No changes needed!** Continue using `useTranslation()` and `t()` as before:

```jsx
import { useTranslation } from 'react-i18next'

function MyComponent() {
  const { t } = useTranslation()
  return <h1>{t('landing.hero.title')}</h1>
}
```

### For Translators/Content Managers

1. Open the app in development mode
2. Press **Alt + T** to enable in-context editing
3. Click on any text to edit
4. Changes are saved automatically
5. Refresh to see changes

### Syncing Translations

To pull translations from Tolgee back to local JSON files:

```bash
tolgee pull \
  --api-url https://app.tolgee.io \
  --api-key YOUR_API_KEY \
  --project-id YOUR_PROJECT_ID \
  --path src/i18n/locales
```

## POC Validation Criteria

### ✅ Success Criteria

- [ ] In-context translation works (can click and edit text)
- [ ] No hardcoded Chinese strings in shell components (`rg '[\p{Han}]'` returns 0)
- [ ] No performance regression (Lighthouse Performance ≥85)
- [ ] No accessibility regression (Lighthouse A11y ≥95)
- [ ] Production build works without Tolgee credentials
- [ ] Bundle size increase < 50KB gzipped

### 🔍 Testing Checklist

1. **In-Context Editing**:
   - [ ] Press Alt+T to toggle DevTools
   - [ ] Click on navigation items to edit
   - [ ] Click on login form labels to edit
   - [ ] Changes save to Tolgee cloud

2. **Production Build**:
   - [ ] Build without .env.local (should work)
   - [ ] Translations load from static JSON
   - [ ] No Tolgee API calls in production

3. **Performance**:
   - [ ] Run Lighthouse audit
   - [ ] Check bundle size
   - [ ] Verify no infinite loops or memory leaks

## Next Steps (After POC)

If POC is successful:

1. **Expand Coverage**: Add Dashboard, Settings, and other pages
2. **Team Onboarding**: Train team members on in-context editing
3. **CI/CD Integration**: Auto-sync translations in deployment pipeline
4. **Translation Workflow**: Set up review/approval process
5. **Machine Translation**: Enable auto-translation for new keys

## Troubleshooting

### In-Context Editing Not Working

1. Check that `.env.local` exists with correct credentials
2. Verify you're in development mode (`npm run dev`)
3. Check browser console for errors
4. Try pressing Alt+T multiple times

### Translations Not Loading

1. Check that JSON files exist in `src/i18n/locales/`
2. Verify import paths in `tolgee.js`
3. Check browser console for import errors

### Build Fails

1. Remove `.env.local` temporarily
2. Verify Tolgee packages are installed
3. Check for TypeScript errors

## Resources

- **Tolgee Documentation**: https://tolgee.io/docs
- **React Integration**: https://tolgee.io/integrations/react
- **i18next Plugin**: https://tolgee.io/integrations/i18next
- **Tolgee GitHub**: https://github.com/tolgee/tolgee-platform

## Support

For issues or questions:
1. Check Tolgee documentation
2. Join Tolgee Discord: https://discord.gg/tolgee
3. Open an issue on GitHub

---

**Last Updated**: 2025-10-22  
**Status**: POC Phase - Shell Components Only
