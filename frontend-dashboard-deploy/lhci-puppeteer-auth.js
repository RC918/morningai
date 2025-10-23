/**
 * Puppeteer script for Lighthouse CI authentication
 * 
 * This script runs before each Lighthouse test and injects
 * Supabase authentication data into localStorage.
 * 
 * The authentication data is extracted from Playwright's
 * storageState.json by the make-lhci-cookie.js script.
 */

const fs = require('fs');
const path = require('path');

const STATE_FILE = path.join(__dirname, 'playwright/.auth/storageState.json');

module.exports = async (browser, context) => {
  if (!fs.existsSync(STATE_FILE)) {
    console.log('⚠️  No authentication state found, skipping auth injection');
    return;
  }

  try {
    const state = JSON.parse(fs.readFileSync(STATE_FILE, 'utf8'));
    
    if (!state.origins || state.origins.length === 0) {
      console.log('⚠️  No localStorage data in state file');
      return;
    }

    const page = context.newPage ? await context.newPage() : context;
    
    await page.goto('http://localhost:4173/', { waitUntil: 'domcontentloaded' });
    
    for (const origin of state.origins) {
      if (origin.localStorage && origin.localStorage.length > 0) {
        console.log(`🔐 Injecting ${origin.localStorage.length} localStorage items for ${origin.origin}`);
        
        for (const item of origin.localStorage) {
          await page.evaluate(
            (name, value) => {
              localStorage.setItem(name, value);
            },
            item.name,
            item.value
          );
        }
      }
    }
    
    console.log('✅ Authentication injected successfully');
  } catch (error) {
    console.error('❌ Error injecting authentication:', error.message);
  }
};
