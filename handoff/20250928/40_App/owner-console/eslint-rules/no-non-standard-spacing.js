/**
 * ESLint rule: no-non-standard-spacing
 * 
 * Enforces the use of standardized Tailwind spacing utilities.
 * Prevents non-standard padding, margin, gap, and space values.
 * 
 * @see https://eslint.org/docs/latest/extend/custom-rules
 */

/**
 * Allowed spacing values based on MorningAI design system
 * @see docs/ui-ux/standard.md
 */
const ALLOWED_SPACING = {
  // Padding utilities
  padding: [
    'p-0', 'p-1', 'p-2', 'p-3', 'p-4', 'p-5', 'p-6', 'p-8',
    'px-0', 'px-1', 'px-2', 'px-3', 'px-4', 'px-5', 'px-6', 'px-8',
    'py-0', 'py-1', 'py-2', 'py-3', 'py-4', 'py-5', 'py-6', 'py-8',
    'pt-0', 'pt-1', 'pt-2', 'pt-3', 'pt-4', 'pt-5', 'pt-6', 'pt-8',
    'pb-0', 'pb-1', 'pb-2', 'pb-3', 'pb-4', 'pb-5', 'pb-6', 'pb-8',
    'pl-0', 'pl-1', 'pl-2', 'pl-3', 'pl-4', 'pl-5', 'pl-6', 'pl-8',
    'pr-0', 'pr-1', 'pr-2', 'pr-3', 'pr-4', 'pr-5', 'pr-6', 'pr-8',
  ],
  // Margin utilities
  margin: [
    'm-0', 'm-1', 'm-2', 'm-3', 'm-4', 'm-5', 'm-6', 'm-8', 'm-auto',
    'mx-0', 'mx-1', 'mx-2', 'mx-3', 'mx-4', 'mx-5', 'mx-6', 'mx-8', 'mx-auto',
    'my-0', 'my-1', 'my-2', 'my-3', 'my-4', 'my-5', 'my-6', 'my-8', 'my-auto',
    'mt-0', 'mt-1', 'mt-2', 'mt-3', 'mt-4', 'mt-5', 'mt-6', 'mt-8', 'mt-auto',
    'mb-0', 'mb-1', 'mb-2', 'mb-3', 'mb-4', 'mb-5', 'mb-6', 'mb-8', 'mb-auto',
    'ml-0', 'ml-1', 'ml-2', 'ml-3', 'ml-4', 'ml-5', 'ml-6', 'ml-8', 'ml-auto',
    'mr-0', 'mr-1', 'mr-2', 'mr-3', 'mr-4', 'mr-5', 'mr-6', 'mr-8', 'mr-auto',
    // Negative margins (commonly used)
    '-m-1', '-m-2', '-m-3', '-m-4',
    '-mx-1', '-mx-2', '-mx-3', '-mx-4',
    '-my-1', '-my-2', '-my-3', '-my-4',
    '-mt-1', '-mt-2', '-mt-3', '-mt-4',
    '-mb-1', '-mb-2', '-mb-3', '-mb-4',
    '-ml-1', '-ml-2', '-ml-3', '-ml-4',
    '-mr-1', '-mr-2', '-mr-3', '-mr-4',
  ],
  // Gap utilities (for flex/grid)
  gap: [
    'gap-0', 'gap-1', 'gap-2', 'gap-3', 'gap-4', 'gap-5', 'gap-6', 'gap-8',
    'gap-x-0', 'gap-x-1', 'gap-x-2', 'gap-x-3', 'gap-x-4', 'gap-x-5', 'gap-x-6', 'gap-x-8',
    'gap-y-0', 'gap-y-1', 'gap-y-2', 'gap-y-3', 'gap-y-4', 'gap-y-5', 'gap-y-6', 'gap-y-8',
  ],
  // Space utilities (for child spacing)
  space: [
    'space-x-0', 'space-x-1', 'space-x-2', 'space-x-3', 'space-x-4', 'space-x-5', 'space-x-6', 'space-x-8',
    'space-y-0', 'space-y-1', 'space-y-2', 'space-y-3', 'space-y-4', 'space-y-5', 'space-y-6', 'space-y-8',
  ],
};

// Flatten all allowed values into a Set for fast lookup
const ALLOWED_SET = new Set([
  ...ALLOWED_SPACING.padding,
  ...ALLOWED_SPACING.margin,
  ...ALLOWED_SPACING.gap,
  ...ALLOWED_SPACING.space,
]);

/**
 * Patterns to detect spacing utilities
 * These match Tailwind's spacing utilities with numeric values
 */
const SPACING_PATTERNS = [
  // Padding: p-{n}, px-{n}, py-{n}, pt-{n}, pb-{n}, pl-{n}, pr-{n}
  /^p[xytblr]?-(\d+\.?\d*|\[.+\])$/,
  // Margin: m-{n}, mx-{n}, my-{n}, mt-{n}, mb-{n}, ml-{n}, mr-{n} (including negative)
  /^-?m[xytblr]?-(\d+\.?\d*|\[.+\]|auto)$/,
  // Gap: gap-{n}, gap-x-{n}, gap-y-{n}
  /^gap(-[xy])?-(\d+\.?\d*|\[.+\])$/,
  // Space: space-x-{n}, space-y-{n}
  /^-?space-[xy]-(\d+\.?\d*|\[.+\]|reverse)$/,
];

/**
 * Check if a class is a spacing utility
 */
function isSpacingUtility(cls) {
  return SPACING_PATTERNS.some(pattern => pattern.test(cls));
}

/**
 * Check if a class is allowed by the additionalAllowed option
 */
function isAllowedByOption(cls, additionalAllowed) {
  if (!additionalAllowed || additionalAllowed.length === 0) {
    return false;
  }
  return additionalAllowed.includes(cls);
}

/**
 * Check if a className string contains non-standard spacing
 * @param {string} classNameValue - The className attribute value
 * @param {string[]} additionalAllowed - Additional spacing values to allow
 * @returns {string|null} - The first non-standard spacing class found, or null
 */
function containsNonStandardSpacing(classNameValue, additionalAllowed = []) {
  if (!classNameValue || typeof classNameValue !== 'string') {
    return null;
  }

  const classes = classNameValue.split(/\s+/);

  for (const cls of classes) {
    // Skip if not a spacing utility
    if (!isSpacingUtility(cls)) {
      continue;
    }

    // Skip if in the allowed set
    if (ALLOWED_SET.has(cls)) {
      continue;
    }

    // Skip if explicitly allowed by options
    if (isAllowedByOption(cls, additionalAllowed)) {
      continue;
    }

    // Skip special values that are always allowed
    if (cls.endsWith('-auto') || cls.endsWith('-reverse')) {
      continue;
    }

    // Skip arbitrary values (e.g., p-[20px]) - these are intentional overrides
    if (cls.includes('[') && cls.includes(']')) {
      continue;
    }

    // This is a non-standard spacing value
    return cls;
  }

  return null;
}

/**
 * Get suggestion for a non-standard spacing class
 */
function getSuggestion(nonStandardClass) {
  // Extract the prefix and value
  const match = nonStandardClass.match(/^(-?)(p|m|gap|space)([xytblr]?|-[xy])?-(\d+\.?\d*)$/);
  
  if (!match) return null;

  const [, negative, prefix, direction, value] = match;
  const numValue = parseFloat(value);
  
  // Find the closest allowed value
  const allowedValues = [0, 1, 2, 3, 4, 5, 6, 8];
  const closest = allowedValues.reduce((prev, curr) => 
    Math.abs(curr - numValue) < Math.abs(prev - numValue) ? curr : prev
  );

  const suggestion = `${negative}${prefix}${direction || ''}-${closest}`;
  
  // Verify the suggestion is in our allowed set
  if (ALLOWED_SET.has(suggestion) || (negative && ALLOWED_SET.has(suggestion))) {
    return suggestion;
  }

  // Fallback to recommending standard values
  if (prefix === 'p') {
    return 'p-4, p-5, p-6, or p-8';
  } else if (prefix === 'm') {
    return 'mt-4, mt-8, mb-4, or mb-8';
  } else if (prefix === 'gap') {
    return 'gap-2, gap-4, gap-6, or gap-8';
  } else if (prefix === 'space') {
    return 'space-y-4, space-y-6, or space-y-8';
  }

  return 'Use standard spacing values (0, 1, 2, 3, 4, 5, 6, 8)';
}

export default {
  meta: {
    type: 'suggestion',
    docs: {
      description: 'Enforce standardized Tailwind spacing utilities from the design system',
      category: 'Best Practices',
      recommended: true,
    },
    messages: {
      nonStandardSpacing: 'Non-standard spacing "{{nonStandardClass}}" detected. Use design system spacing instead: {{suggestion}}',
    },
    fixable: null, // Not auto-fixable to encourage intentional decisions
    schema: [
      {
        type: 'object',
        properties: {
          additionalAllowed: {
            type: 'array',
            items: { type: 'string' },
            description: 'Additional spacing values to allow beyond the standard set',
          },
        },
        additionalProperties: false,
      },
    ],
  },

  create(context) {
    const options = context.options[0] || {};
    const additionalAllowed = options.additionalAllowed || [];

    return {
      JSXAttribute(node) {
        if (node.name.name !== 'className' && node.name.name !== 'class') {
          return;
        }

        let classNameValue = null;

        if (node.value && node.value.type === 'Literal') {
          classNameValue = node.value.value;
        } else if (node.value && node.value.type === 'JSXExpressionContainer') {
          const expression = node.value.expression;
          
          if (expression.type === 'TemplateLiteral') {
            classNameValue = expression.quasis.map(q => q.value.cooked).join(' ');
          }
          else if (expression.type === 'Literal' && typeof expression.value === 'string') {
            classNameValue = expression.value;
          }
        }

        if (!classNameValue) {
          return;
        }

        const nonStandardClass = containsNonStandardSpacing(classNameValue, additionalAllowed);
        if (nonStandardClass) {
          const suggestion = getSuggestion(nonStandardClass);
          context.report({
            node,
            messageId: 'nonStandardSpacing',
            data: {
              nonStandardClass,
              suggestion: suggestion || 'Use standard spacing values (0, 1, 2, 3, 4, 5, 6, 8)',
            },
          });
        }
      },
    };
  },
};
