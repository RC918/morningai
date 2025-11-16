const { injectAxe, checkA11y } = require('axe-playwright');

module.exports = {
  async preVisit(page) {
    await injectAxe(page);
  },
  async postVisit(page) {
    await checkA11y(page, '#storybook-root', {
      includedImpacts: ['critical'],
      detailedReport: true,
      detailedReportOptions: {
        html: true,
      },
    });
  },
};
