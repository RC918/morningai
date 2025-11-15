import type { Preview } from '@storybook/react';
import React from 'react';
import { I18nextProvider } from 'react-i18next';
import { ThemeProvider } from 'next-themes';
import i18n from '../src/i18n.js';
import '../src/index.css';

const preview: Preview = {
  parameters: {
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/i,
      },
    },
    actions: { argTypesRegex: '^on[A-Z].*' },
    backgrounds: {
      default: 'light',
      values: [
        {
          name: 'light',
          value: '#ffffff',
        },
        {
          name: 'dark',
          value: '#1a1a1a',
        },
      ],
    },
  },
  decorators: [
    (Story) => (
      <I18nextProvider i18n={i18n}>
        <ThemeProvider attribute="class" defaultTheme="light">
          <div className="min-h-screen bg-white dark:bg-neutral-900">
            <Story />
          </div>
        </ThemeProvider>
      </I18nextProvider>
    ),
  ],
};

export default preview;
