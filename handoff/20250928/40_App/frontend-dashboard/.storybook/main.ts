import type { StorybookConfig } from '@storybook/react-vite';
import { mergeConfig } from 'vite';

const config: StorybookConfig = {
  stories: [
    "../src/**/*.mdx",
    "../src/**/*.stories.@(js|jsx|mjs|ts|tsx)"
  ],
  addons: [
    '@storybook/addon-essentials',
    '@storybook/addon-interactions',
    '@storybook/addon-links',
    '@storybook/addon-a11y'
  ],
  framework: {
    name: '@storybook/react-vite',
    options: {}
  },
  docs: {
    autodocs: 'tag'
  },
  features: {
    storyStoreV7: true,
    buildStoriesJson: true,
  },
  async viteFinal(config) {
    return mergeConfig(config, {
      plugins: config.plugins?.filter(
        (plugin: any) => plugin && plugin.name !== 'vite-plugin-pwa'
      ),
      optimizeDeps: {
        include: [
          'react',
          'react-dom',
          '@storybook/react',
        ],
      },
      build: {
        rollupOptions: {
          output: {
            manualChunks: {
              'react-vendor': ['react', 'react-dom'],
              'storybook-vendor': ['@storybook/react'],
            },
          },
        },
      },
    });
  },
};

export default config;
