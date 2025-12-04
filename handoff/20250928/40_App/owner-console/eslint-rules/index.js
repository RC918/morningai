/**
 * Custom ESLint rules for MorningAI owner-console
 */

import noHardcodedColors from './no-hardcoded-colors.js';
import noNonStandardSpacing from './no-non-standard-spacing.js';

export default {
  rules: {
    'no-hardcoded-colors': noHardcodedColors,
    'no-non-standard-spacing': noNonStandardSpacing,
  },
};
