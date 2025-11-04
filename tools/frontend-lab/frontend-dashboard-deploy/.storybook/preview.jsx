import '../src/index.css';
import { applyDesignTokens } from '../src/lib/design-tokens';

if (typeof window !== 'undefined') {
  applyDesignTokens('morning-ai', '.theme-morning-ai');
}

/** @type { import('@storybook/react').Preview } */
const preview = {
  parameters: {
    controls: {
      matchers: {
       color: /(background|color)$/i,
       date: /Date$/i,
      },
    },
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
    actions: { argTypesRegex: '^on[A-Z].*' },
    a11y: {
      config: {
        rules: [
          {
            id: 'color-contrast',
            enabled: true,
          },
          {
            id: 'label',
            enabled: true,
          },
        ],
      },
    },
  },
  decorators: [
    (Story) => (
      <div className="theme-morning-ai" style={{ padding: '2rem' }}>
        <Story />
      </div>
    ),
  ],
};

export default preview;
