/**
 * Storybook Test Runner Configuration
 * 
 * IMPORTANT: This file MUST use CommonJS format (module.exports, require)
 * because @storybook/test-runner loads it via require(), which doesn't
 * support ES modules (.ts or import/export syntax).
 * 
 * DO NOT convert this to:
 * - TypeScript (.ts extension)
 * - ES modules (import/export syntax)
 * - Set "type": "module" in package.json
 * 
 * Doing so will cause CI failures with:
 * "Must use import to load ES Module"
 * 
 * This configuration automatically runs accessibility checks on every story
 * using axe-core via axe-playwright.
 */

const { injectAxe, checkA11y } = require('axe-playwright');

module.exports = {
  async preVisit(page) {
    await injectAxe(page);
  },
  async postVisit(page) {
    await checkA11y(page, '#storybook-root', {
      detailedReport: true,
      detailedReportOptions: {
        html: true,
      },
    });
  },
};
