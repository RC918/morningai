import js from '@eslint/js';
import globals from 'globals';
import reactHooks from 'eslint-plugin-react-hooks';
import reactRefresh from 'eslint-plugin-react-refresh';
import jsxA11y from 'eslint-plugin-jsx-a11y';
import i18next from 'eslint-plugin-i18next';
import tseslint from 'typescript-eslint';
import customRules from './eslint-rules/index.js';

export default [
  { ignores: ['dist', 'src/lib/generated'] },
  {
    files: ['**/*.{js,jsx,ts,tsx}'],
    languageOptions: {
      ecmaVersion: 2020,
      sourceType: 'module',
      globals: globals.browser,
      parser: tseslint.parser,
      parserOptions: {
        ecmaFeatures: {
          jsx: true,
        },
      },
    },
    plugins: {
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
      'jsx-a11y': jsxA11y,
      'i18next': i18next,
      'custom': customRules,
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      ...jsxA11y.configs.recommended.rules,
      'react-refresh/only-export-components': [
        'warn',
        { allowConstantExport: true },
      ],
      'no-restricted-imports': [
        'error',
        {
          patterns: [
            {
              group: ['**/frontend-dashboard/**'],
              message: 'owner-console must not import from frontend-dashboard. Extract shared code to packages/shared-ui instead.',
            },
          ],
        },
      ],
      'no-unused-vars': 'off',
      'no-undef': 'off',
      'jsx-a11y/aria-props': 'error',
      'jsx-a11y/aria-proptypes': 'error',
      'jsx-a11y/aria-unsupported-elements': 'error',
      'jsx-a11y/role-has-required-aria-props': 'error',
      'jsx-a11y/role-supports-aria-props': 'error',
      'jsx-a11y/tabindex-no-positive': 'error',
      'jsx-a11y/heading-has-content': 'error',
      'jsx-a11y/html-has-lang': 'error',
      'jsx-a11y/lang': 'error',
      'jsx-a11y/no-distracting-elements': 'error',
      'jsx-a11y/scope': 'error',
      'jsx-a11y/click-events-have-key-events': 'error',
      'jsx-a11y/no-static-element-interactions': 'error',
      'jsx-a11y/anchor-is-valid': 'error',
      'jsx-a11y/img-redundant-alt': 'error',
      'jsx-a11y/label-has-associated-control': 'error',
      'i18next/no-literal-string': ['error', {
        markupOnly: true,
        onlyAttribute: ['alt', 'title', 'placeholder', 'aria-label', 'aria-description'],
        ignoreAttribute: ['className', 'data-testid', 'href', 'to', 'id', 'name', 'type', 'role', 'tabIndex', 'aria-labelledby', 'aria-describedby', 'data-devinid'],
        ignoreCallee: ['t', 'Trans', 'clsx', 'cn', 'tw', 'cva'],
        ignore: [
          '^\\s*$',
          '^[0-9 .,:+\\-/%()]*$',
          '^(true|false)$',
        ],
      }],
      // Design system enforcement: prevent hardcoded Tailwind colors
      // Use semantic tokens instead (error, success, warning, info, neutral, primary, accent)
      'custom/no-hardcoded-colors': 'warn',
      // Design system enforcement: prevent non-standard spacing utilities
      // Use standardized spacing values (0, 1, 2, 4, 5, 6, 8)
      'custom/no-non-standard-spacing': 'warn',
    },
  },
  {
    files: ['**/*.{test,spec}.{js,jsx,ts,tsx}', 'scripts/**'],
    rules: {
      'i18next/no-literal-string': 'off',
    },
  },
  {
    files: ['**/*.{js,jsx}'],
    rules: {
      'no-undef': 'off',
    },
  },
];
