/**
 * Puppeteer script for Lighthouse CI - Dark Mode
 * 
 * This script runs before each Lighthouse test and:
 * 1. Hooks into Browser's targetcreated event to intercept pages LHCI creates
 * 2. Applies dark mode configuration to those pages before app code runs:
 *    - Enables dark mode via prefers-color-scheme media query (using CDP fallback)
 *    - Sets the theme to 'dark' in localStorage (for our app's theme system)
 *    - Adds 'dark' class to document root (for Tailwind dark mode)
 * 
 * This ensures Lighthouse tests run in dark mode to catch
 * color contrast issues specific to dark themes.
 */

// Module-scope guard to prevent duplicate listener registration
let installed = false;

module.exports = async (browser, context) => {
  console.log('🌙 Dark mode: start');
  
  // Prevent duplicate listener registration across multiple runs
  if (installed) {
    console.log('🌙 Dark mode already installed, skipping');
    return;
  }
  installed = true;
  
  try {
    // Helper function to apply dark mode configuration to a page
    const applyDarkMode = async (page) => {
      try {
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
        
        console.log('🌙 Applied dark mode to page');
      } catch (error) {
        console.warn('⚠️ Failed to apply dark mode to page:', error?.message);
      }
    };
    
    // Apply dark mode to any existing pages
    try {
      const pages = await browser.pages();
      console.log(`🌙 Found ${pages.length} existing page(s)`);
      for (const page of pages) {
        await applyDarkMode(page);
      }
    } catch (error) {
      console.warn('⚠️ Failed to apply dark mode to existing pages:', error?.message);
    }
    
    // Hook into targetcreated event to intercept pages LHCI creates for auditing
    browser.on('targetcreated', async (target) => {
      try {
        if (target.type() !== 'page') {
          return;
        }
        
        const page = await target.page();
        if (!page) {
          return;
        }
        
        console.log('🌙 New page target created, applying dark mode');
        await applyDarkMode(page);
        console.log('✅ Dark mode applied to newly created target page');
      } catch (error) {
        console.warn('⚠️ targetcreated handler error:', error?.message);
      }
    });
    
    console.log('✅ Dark mode: setup complete');
  } catch (error) {
    console.error('❌ Error setting up dark mode:', error.message);
    // Don't throw - allow LHCI to continue even if dark mode setup fails
    console.warn('⚠️ Continuing without dark mode configuration');
  }
};
