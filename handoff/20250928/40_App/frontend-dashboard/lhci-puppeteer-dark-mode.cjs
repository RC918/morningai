/**
 * Puppeteer script for Lighthouse CI - Dark Mode
 * 
 * This script runs before each Lighthouse test and:
 * 1. Enables dark mode via prefers-color-scheme media query
 * 2. Sets the theme to 'dark' in localStorage (for our app's theme system)
 * 
 * This ensures Lighthouse tests run in dark mode to catch
 * color contrast issues specific to dark themes.
 */

module.exports = async (browser, context) => {
  console.log('🌙 Dark mode: start');
  
  try {
    const page = context.newPage ? await context.newPage() : context;
    
    console.log('🌙 Emulating dark mode preference...');
    
    await page.emulateMediaFeatures([
      { name: 'prefers-color-scheme', value: 'dark' }
    ]);
    
    await page.evaluateOnNewDocument(() => {
      localStorage.setItem('morningai-theme', 'dark');
    });
    
    console.log('✅ Dark mode: done');
  } catch (error) {
    console.error('❌ Error configuring dark mode:', error.message);
    throw error;
  }
};
