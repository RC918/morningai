#!/usr/bin/env node

/**
 * Extract Supabase cookies from Playwright auth state and convert to LHCI format
 * 
 * This script:
 * 1. Reads Playwright's storageState.json (contains cookies from authenticated session)
 * 2. Extracts cookies and formats them as a Cookie header
 * 3. Writes to LHCI_EXTRA_HEADERS.json for Lighthouse to use
 * 
 * This allows Lighthouse to test authenticated pages by reusing the session
 * from Playwright's login test.
 */

const fs = require('fs');
const path = require('path');

const PLAYWRIGHT_STATE_FILE = path.join(__dirname, '../frontend-dashboard-deploy/playwright/.auth/storageState.json');
const OUTPUT_FILE = path.join(__dirname, '../frontend-dashboard-deploy/LHCI_EXTRA_HEADERS.json');

function extractCookies() {
  try {
    if (!fs.existsSync(PLAYWRIGHT_STATE_FILE)) {
      console.error(`❌ Playwright state file not found: ${PLAYWRIGHT_STATE_FILE}`);
      console.error('   Make sure to run Playwright auth setup first:');
      console.error('   pnpm dlx playwright test tests/auth.setup.spec.ts');
      process.exit(1);
    }

    const state = JSON.parse(fs.readFileSync(PLAYWRIGHT_STATE_FILE, 'utf8'));
    
    if (!state.cookies || state.cookies.length === 0) {
      console.error('❌ No cookies found in Playwright state');
      process.exit(1);
    }

    const cookieString = state.cookies
      .map(cookie => `${cookie.name}=${cookie.value}`)
      .join('; ');

    console.log(`✅ Extracted ${state.cookies.length} cookie(s) from Playwright state`);
    console.log('   Cookies:', state.cookies.map(c => c.name).join(', '));

    return cookieString;
  } catch (error) {
    console.error('❌ Error reading Playwright state:', error.message);
    process.exit(1);
  }
}

function writeExtraHeaders(cookieString) {
  try {
    const headers = {
      Cookie: cookieString
    };

    fs.writeFileSync(OUTPUT_FILE, JSON.stringify(headers, null, 2), 'utf8');
    console.log(`✅ Extra headers written to: ${OUTPUT_FILE}`);
  } catch (error) {
    console.error('❌ Error writing extra headers:', error.message);
    process.exit(1);
  }
}

function main() {
  console.log('Converting Playwright cookies to LHCI format...\n');
  
  const cookieString = extractCookies();
  writeExtraHeaders(cookieString);
  
  console.log('\n✅ Cookie conversion complete!');
  console.log('   Lighthouse CI can now test authenticated pages.');
}

main();
