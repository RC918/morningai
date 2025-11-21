import js from '@eslint/js';
import globals from 'globals';
import react from 'eslint-plugin-react';
import reactHooks from 'eslint-plugin-react-hooks';
import tseslint from 'typescript-eslint';

export default [
  {
    ignores: [
      'dist',
      'storybook-static',
      '.storybook',
      'coverage',
      '**/*.stories.tsx',
      'scripts/**',
    ],
  },
  {
    files: ['**/*.{js,jsx,ts,tsx}'],
    languageOptions: {
      ecmaVersion: 2020,
      sourceType: 'module',
      globals: {
        ...globals.browser,
        ...globals.node,
      },
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
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      'no-unused-vars': 'off',
      'react/jsx-no-undef': 'error',
      'react/jsx-uses-react': 'error',
      'react/jsx-uses-vars': 'error',
      'react/jsx-closing-tag-location': 'warn',
      'react/jsx-closing-bracket-location': 'warn',
      'react/jsx-tag-spacing': 'warn',
    },
  },
  {
    files: ['**/*.{test,spec}.{ts,tsx,js,jsx}', 'src/**/__tests__/**'],
    rules: {
      'no-unused-vars': 'off',
    },
  },
];
