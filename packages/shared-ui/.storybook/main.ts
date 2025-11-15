import type { StorybookConfig } from '@storybook/react-vite'
import type { InlineConfig } from 'vite'

const config: StorybookConfig = {
  stories: ['../src/**/*.mdx', '../src/**/*.stories.@(js|jsx|mjs|ts|tsx)'],
  addons: [
    '@storybook/addon-links',
    '@storybook/addon-essentials',
    '@storybook/addon-interactions',
    '@storybook/addon-a11y',
  ],
  framework: {
    name: '@storybook/react-vite',
    options: {},
  },
  docs: {
    autodocs: 'tag',
  },
  async viteFinal(config: InlineConfig) {
    return {
      ...config,
      build: {
        ...(config.build || {}),
        sourcemap: false,
      },
      ssr: {
        ...(config.ssr || {}),
        noExternal: [
          /^@radix-ui/,
          'react-remove-scroll',
          'aria-hidden',
          'react-style-singleton',
        ],
      },
    }
  },
}

export default config
