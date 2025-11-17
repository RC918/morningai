/**
 * Puppeteer script for Lighthouse CI - Dark Mode
 * 
 * This script creates and prepares a page in dark mode, then returns it to Lighthouse for auditing.
 * 
 * Approach:
 * 1. Create a new page ourselves (not relying on Lighthouse's page creation)
 * 2. Apply dark mode configuration BEFORE navigating:
 *    - Set evaluateOnNewDocument to configure localStorage, dark class, and data-theme
 *    - Use CDP to emulate prefers-color-scheme: dark
 * 3. Navigate to the URL Lighthouse wants to audit
 * 4. Verify dark mode is active
 * 5. Return the prepared page to Lighthouse for auditing
 * 
 * This ensures Lighthouse audits the page in dark mode, catching color contrast issues
 * specific to dark themes.
 */

module.exports = async (browser, context) => {
  console.log('🌙 Dark mode: Creating and preparing page for', context.url);
  
  try {
    // Create a new page that we will prepare and return to Lighthouse
    const page = await browser.newPage();
    console.log('🌙 Created new page');
    
    // Set up evaluateOnNewDocument to configure dark mode BEFORE any navigation
    // This ensures localStorage and DOM are set up before the app initializes
    await page.evaluateOnNewDocument(() => {
      try {
        // Set theme in localStorage (for ThemeProvider)
        localStorage.setItem('morningai-theme', 'dark');
        
        // Add dark class and data-theme attribute (for Tailwind and app logic)
        document.documentElement.classList.add('dark');
        document.documentElement.setAttribute('data-theme', 'dark');
        
        // Set color-scheme CSS property for browser default styles
        document.documentElement.style.colorScheme = 'dark';
        
        console.log('🌙 evaluateOnNewDocument: Dark mode configured');
      } catch (error) {
        console.warn('⚠️ evaluateOnNewDocument error:', error?.message);
      }
    });
    console.log('🌙 Installed evaluateOnNewDocument handler');
    
    // Emulate prefers-color-scheme: dark using CDP
    // This makes window.matchMedia('(prefers-color-scheme: dark)').matches return true
    try {
      if (typeof page.emulateMediaFeatures === 'function') {
        await page.emulateMediaFeatures([
          { name: 'prefers-color-scheme', value: 'dark' }
        ]);
        console.log('✨ Used page.emulateMediaFeatures for prefers-color-scheme: dark');
      } else {
        // Use Chrome DevTools Protocol as fallback
        const client = await page.target().createCDPSession();
        await client.send('Emulation.setEmulatedMedia', {
          features: [{ name: 'prefers-color-scheme', value: 'dark' }]
        });
        console.log('✨ Used CDP Emulation.setEmulatedMedia for prefers-color-scheme: dark');
      }
    } catch (error) {
      console.warn('⚠️ Failed to emulate prefers-color-scheme, continuing with class/localStorage only:', error?.message);
    }
    
    // Navigate to the URL Lighthouse wants to audit
    console.log('🌙 Navigating to', context.url);
    await page.goto(context.url, { waitUntil: 'networkidle0', timeout: 30000 });
    console.log('🌙 Navigation complete');
    
    // Verify dark mode is active
    const darkModeStatus = await page.evaluate(() => {
      return {
        theme: localStorage.getItem('morningai-theme'),
        hasDarkClass: document.documentElement.classList.contains('dark'),
        dataTheme: document.documentElement.getAttribute('data-theme'),
        prefersDark: window.matchMedia('(prefers-color-scheme: dark)').matches,
        colorScheme: document.documentElement.style.colorScheme
      };
    });
    
    console.log('🌙 Dark mode status:', JSON.stringify(darkModeStatus));
    
    if (darkModeStatus.hasDarkClass && darkModeStatus.prefersDark) {
      console.log('✅ Dark mode verified: Page is ready for Lighthouse audit');
    } else {
      console.warn('⚠️ Dark mode verification incomplete:', darkModeStatus);
    }
    
    // Return the prepared page to Lighthouse for auditing
    console.log('🌙 Returning prepared page to Lighthouse');
    return page;
    
  } catch (error) {
    console.error('❌ Error preparing dark mode page:', error.message);
    console.error('   Stack:', error.stack);
    // Don't throw - allow LHCI to continue even if dark mode setup fails
    console.warn('⚠️ Returning undefined - Lighthouse will create its own page');
    return undefined;
  }
};
