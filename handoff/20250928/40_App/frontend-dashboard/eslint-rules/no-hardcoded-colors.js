/**
 * ESLint rule: no-hardcoded-colors
 * 
 * Prevents usage of hardcoded Tailwind color utilities in className attributes.
 * Enforces use of semantic design tokens instead.
 * 
 * @see https://eslint.org/docs/latest/extend/custom-rules
 */

const HARDCODED_COLOR_PATTERNS = [
  /\btext-(red|green|blue|yellow|amber|purple|pink|indigo|cyan|teal|lime|emerald|sky|violet|fuchsia|rose|orange|slate|zinc|stone)(-\d+)?\b/,
  /\bbg-(red|green|blue|yellow|amber|purple|pink|indigo|cyan|teal|lime|emerald|sky|violet|fuchsia|rose|orange|slate|zinc|stone)(-\d+)?\b/,
  /\bborder-(red|green|blue|yellow|amber|purple|pink|indigo|cyan|teal|lime|emerald|sky|violet|fuchsia|rose|orange|slate|zinc|stone)(-\d+)?\b/,
  /\bring-(red|green|blue|yellow|amber|purple|pink|indigo|cyan|teal|lime|emerald|sky|violet|fuchsia|rose|orange|slate|zinc|stone)(-\d+)?\b/,
  /\boutline-(red|green|blue|yellow|amber|purple|pink|indigo|cyan|teal|lime|emerald|sky|violet|fuchsia|rose|orange|slate|zinc|stone)(-\d+)?\b/,
  /\bplaceholder-(red|green|blue|yellow|amber|purple|pink|indigo|cyan|teal|lime|emerald|sky|violet|fuchsia|rose|orange|slate|zinc|stone)(-\d+)?\b/,
  /\bdivide-(red|green|blue|yellow|amber|purple|pink|indigo|cyan|teal|lime|emerald|sky|violet|fuchsia|rose|orange|slate|zinc|stone)(-\d+)?\b/,
  /\bshadow-(red|green|blue|yellow|amber|purple|pink|indigo|cyan|teal|lime|emerald|sky|violet|fuchsia|rose|orange|slate|zinc|stone)(-\d+)?\b/,
  /\bdecoration-(red|green|blue|yellow|amber|purple|pink|indigo|cyan|teal|lime|emerald|sky|violet|fuchsia|rose|orange|slate|zinc|stone)(-\d+)?\b/,
  /\bcaret-(red|green|blue|yellow|amber|purple|pink|indigo|cyan|teal|lime|emerald|sky|violet|fuchsia|rose|orange|slate|zinc|stone)(-\d+)?\b/,
  /\baccent-(red|green|blue|yellow|amber|purple|pink|indigo|cyan|teal|lime|emerald|sky|violet|fuchsia|rose|orange|slate|zinc|stone)(-\d+)?\b/,
];

const SEMANTIC_TOKENS = [
  'error', 'success', 'warning', 'info', 'neutral', 'primary', 'secondary', 'accent',
  'muted', 'foreground', 'background', 'border', 'input', 'ring', 'card', 'popover',
  'destructive', 'chart'
];

const ALLOWED_PATTERNS = [
  /\b(text|bg|border|ring|outline|placeholder|divide|shadow|decoration|caret|accent)-(error|success|warning|info|neutral|primary|secondary|accent|muted|foreground|background|border|input|ring|card|popover|destructive|chart)(-\d+)?\b/,
  /\b(text|bg|border|ring|outline|placeholder|divide|shadow|decoration|caret|accent)-gray(-\d+)?\b/,
  /\b(text|bg|border|ring|outline|placeholder|divide|shadow|decoration|caret|accent)-(white|black|transparent|current|inherit)\b/,
];

/**
 * Check if a className string contains hardcoded colors
 */
function containsHardcodedColor(classNameValue) {
  if (!classNameValue || typeof classNameValue !== 'string') {
    return null;
  }

  const classes = classNameValue.split(/\s+/);

  for (const cls of classes) {
    for (const pattern of HARDCODED_COLOR_PATTERNS) {
      if (pattern.test(cls)) {
        const isAllowed = ALLOWED_PATTERNS.some(allowedPattern => allowedPattern.test(cls));
        if (!isAllowed) {
          return cls;
        }
      }
    }
  }

  return null;
}

/**
 * Get semantic token suggestion for a hardcoded color
 */
function getSuggestion(hardcodedClass) {
  const match = hardcodedClass.match(/^(text|bg|border|ring|outline|placeholder|divide|shadow|decoration|caret|accent)-(red|green|blue|yellow|amber|purple|pink|indigo|cyan|teal|lime|emerald|sky|violet|fuchsia|rose|orange|slate|zinc|stone)(-\d+)?$/);
  
  if (!match) return null;

  const [, prefix, color, shade] = match;
  
  const suggestions = {
    red: `${prefix}-error${shade || '-600'}`,
    green: `${prefix}-success${shade || '-600'}`,
    yellow: `${prefix}-warning${shade || '-600'}`,
    amber: `${prefix}-warning${shade || '-600'}`,
    blue: `${prefix}-primary${shade || '-600'} or ${prefix}-info${shade || '-600'}`,
    purple: `${prefix}-accent${shade || '-600'}`,
    gray: `${prefix}-neutral${shade || '-600'}`,
    slate: `${prefix}-neutral${shade || '-600'}`,
    zinc: `${prefix}-neutral${shade || '-600'}`,
    stone: `${prefix}-neutral${shade || '-600'}`,
  };

  return suggestions[color] || `${prefix}-<semantic-token>${shade || ''}`;
}

export default {
  meta: {
    type: 'problem',
    docs: {
      description: 'Disallow hardcoded Tailwind color utilities in favor of semantic design tokens',
      category: 'Best Practices',
      recommended: true,
    },
    messages: {
      hardcodedColor: 'Hardcoded color class "{{hardcodedClass}}" detected. Use semantic design tokens instead: {{suggestion}}',
    },
    fixable: null, // Not auto-fixable due to context-dependent semantic mapping
    schema: [
      {
        type: 'object',
        properties: {
          allowedColors: {
            type: 'array',
            items: { type: 'string' },
            description: 'Additional color names to allow (e.g., ["gray"] for neutral colors)',
          },
        },
        additionalProperties: false,
      },
    ],
  },

  create(context) {
    const options = context.options[0] || {};
    const allowedColors = options.allowedColors || [];

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

        const hardcodedClass = containsHardcodedColor(classNameValue);
        if (hardcodedClass) {
          const suggestion = getSuggestion(hardcodedClass);
          context.report({
            node,
            messageId: 'hardcodedColor',
            data: {
              hardcodedClass,
              suggestion: suggestion || 'Use semantic design tokens (error, success, warning, info, neutral, primary, accent)',
            },
          });
        }
      },
    };
  },
};
