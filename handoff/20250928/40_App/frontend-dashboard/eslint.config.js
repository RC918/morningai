// For more info, see https://github.com/storybookjs/eslint-plugin-storybook#configuration-flat-config-format
import storybook from "eslint-plugin-storybook";

import js from '@eslint/js';
import globals from 'globals';
import react from 'eslint-plugin-react';
import reactHooks from 'eslint-plugin-react-hooks';
import reactRefresh from 'eslint-plugin-react-refresh';
import jsxA11y from 'eslint-plugin-jsx-a11y';
import tseslint from 'typescript-eslint';
import i18next from 'eslint-plugin-i18next';
import customRules from './eslint-rules/index.js';

export default [{ ignores: ['dist', 'src/lib/generated', 'storybook-static', '.storybook', '**/*.stories.tsx', 'playwright-report'] }, {
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
    'react': react,
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
      'warn',
      {
        patterns: [
          {
            group: ['**/owner-console/**'],
            message: 'frontend-dashboard must not import from owner-console. Extract shared code to packages/shared-ui instead.',
          },
          {
            group: ['@radix-ui/react-*', '@mui/*', '@headlessui/*', '@chakra-ui/*'],
            message: 'Direct import of UI component libraries is not allowed. Use @morningai/shared-ui instead. Allowed exceptions: lucide-react (icons), recharts (charts), date-fns (dates).',
          },
        ],
      },
    ],
    'no-unused-vars': 'off',
    'react/jsx-no-undef': 'error',
    'react/jsx-uses-react': 'error',
    'react/jsx-uses-vars': 'error',
    'react/jsx-closing-tag-location': 'error',
    'react/jsx-closing-bracket-location': 'error',
    'react/jsx-tag-spacing': 'error',
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
    'jsx-a11y/click-events-have-key-events': 'warn',
    'jsx-a11y/no-static-element-interactions': 'warn',
    'jsx-a11y/no-autofocus': 'warn',
    'jsx-a11y/no-redundant-roles': 'warn',
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
    'custom/no-hardcoded-colors': 'error',
  },
}, {
  files: ['**/*.{test,spec}.{ts,tsx,js,jsx}', '**/*.stories.{ts,tsx}', 'src/**/__tests__/**', 'scripts/**'],
  rules: {
    'i18next/no-literal-string': 'off',
  },
}, {
  files: [
    'src/components/ui/**/*.{ts,tsx}',
    'src/components/governance/**/*.{ts,tsx}',
    'src/components/usability/**/*.{ts,tsx}',
    'src/components/metrics/**/*.{ts,tsx}',
    'src/components/ab-testing/**/*.{ts,tsx}',
    'src/components/examples/**/*.{ts,tsx}',
    'src/components/AgentGovernance.tsx',
    'src/components/AppleHero.tsx',
    'src/components/CheckoutPage.tsx',
    'src/components/CostAnalysis.tsx',
    'src/components/Dashboard.tsx',
    'src/components/ErrorBoundary.tsx',
    'src/components/GlobalSearch.tsx',
    'src/components/HistoryAnalysis.tsx',
    'src/components/LiveRegion.tsx',
    'src/components/LoginPage.tsx',
    'src/components/ReportCenter.tsx',
    'src/components/SystemSettings.tsx',
    'src/components/TenantSettings.tsx',
    'src/components/WidgetLibrary.tsx',
    'src/pages/TenantSettings.tsx',
    'src/contexts/**/*.{ts,tsx}',
  ],
  rules: {
    'i18next/no-literal-string': 'off',
  },
},{
  files: [
    'src/pages/Settings2FA.tsx',
    'src/components/2fa/**/*.{ts,tsx}',
  ],
  rules: {
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
  },
}, ...storybook.configs["flat/recommended"]];
