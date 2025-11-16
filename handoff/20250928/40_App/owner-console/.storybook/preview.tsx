import type { Preview } from '@storybook/react';
import React from 'react';
import { I18nextProvider } from 'react-i18next';
import { ThemeProvider } from 'next-themes';
import { initialize, mswDecorator } from 'msw-storybook-addon';
import { useDarkMode } from 'storybook-dark-mode';
import i18n from '../src/i18n.js';
import '../src/index.css';

initialize({
  onUnhandledRequest: 'bypass',
});

const WithTheme = (Story: any) => {
  const isDark = useDarkMode();
  
  return (
    <I18nextProvider i18n={i18n}>
      <ThemeProvider 
        attribute="class" 
        enableSystem={false} 
        forcedTheme={isDark ? 'dark' : 'light'}
      >
        <div className="min-h-screen bg-white dark:bg-neutral-900">
          <Story />
        </div>
      </ThemeProvider>
    </I18nextProvider>
  );
};

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
      default: 'transparent',
      values: [
        {
          name: 'transparent',
          value: 'transparent',
        },
      ],
    },
    darkMode: {
      classTarget: 'html',
      darkClass: 'dark',
      lightClass: 'light',
      stylePreview: true,
    },
  },
  decorators: [
    mswDecorator,
    WithTheme,
  ],
};

export default preview;
