/**
 * Puppeteer script for Lighthouse CI - Dark Mode
 * 
 * This script runs before each Lighthouse test and:
 * 1. Enables dark mode via prefers-color-scheme media query (using CDP fallback)
 * 2. Sets the theme to 'dark' in localStorage (for our app's theme system)
 * 3. Adds 'dark' class to document root (for Tailwind dark mode)
 * 
 * This ensures Lighthouse tests run in dark mode to catch
 * color contrast issues specific to dark themes.
 */

module.exports = async (browser, context) => {
  console.log('🌙 Dark mode: start');
  
  try {
    // Resolve the page object - LHCI can pass either a Page or BrowserContext
    const isPage = context && typeof context.goto === 'function';
    let page;
    
    if (isPage) {
      // LHCI gave us the Page it will audit - use it directly
      page = context;
      console.log('🌙 Using provided Page object');
    } else if (context?.pages) {
      // BrowserContext case - get existing pages
      const pages = await context.pages();
      page = pages[0] || await context.newPage();
      console.log('🌙 Resolved Page from BrowserContext');
    } else if (browser?.newPage) {
      // Last resort - create new page
      page = await browser.newPage();
      console.log('⚠️ Created new Page (may not be audited by LHCI)');
    } else {
      console.warn('⚠️ Could not resolve Page from context; aborting dark-mode setup');
      return;
    }
    
    // Set theme very early, before any app code runs
    await page.evaluateOnNewDocument(() => {
      try {
        localStorage.setItem('morningai-theme', 'dark');
        const root = document.documentElement;
        root.classList.add('dark');
        root.setAttribute('data-theme', 'dark');
      } catch (_) {
        // Ignore errors in case localStorage is not available
      }
    });
    
    // Emulate dark mode media feature using CDP fallback
    // (page.emulateMediaFeatures may not exist in LHCI's Puppeteer version)
    try {
      if (typeof page.emulateMediaFeatures === 'function') {
        await page.emulateMediaFeatures([
          { name: 'prefers-color-scheme', value: 'dark' }
        ]);
        console.log('✨ Used page.emulateMediaFeatures');
      } else {
        // Use Chrome DevTools Protocol as fallback
        const client = await page.target().createCDPSession();
        await client.send('Emulation.setEmulatedMedia', {
          features: [{ name: 'prefers-color-scheme', value: 'dark' }]
        });
        console.log('✨ Used CDP fallback for prefers-color-scheme');
      }
    } catch (e) {
      console.warn('⚠️ Dark mode emulation failed, continuing with class/storage only:', e?.message);
      // Don't throw - continue with class/localStorage fallback
    }
    
    // Sanity check - verify dark mode is active
    await page.evaluate(() => {
      const hasDark = document.documentElement.classList.contains('dark');
      console.log('🌗 dark class present?', hasDark);
    });
    
    console.log('✅ Dark mode: done');
  } catch (error) {
    console.error('❌ Error configuring dark mode:', error.message);
    // Don't throw - allow LHCI to continue even if dark mode setup fails
    console.warn('⚠️ Continuing without dark mode configuration');
  }
};
