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

    // Filter out any remaining PWA plugin variants as a safety measure
    // The main PWA disabling is done via STORYBOOK env var in vite.config.js
    config.plugins = config.plugins?.filter(
      (plugin: any) => plugin && !plugin.name?.includes('vite-plugin-pwa')
    );

    return mergeConfig(config, {
      optimizeDeps: {
        include: [
          'react',
          'react-dom',
          '@storybook/react',
        ],
      },
      // NOTE: Do NOT use manualChunks for Storybook builds!
      // Storybook relies on __STORYBOOK_MODULE_PREVIEW_API__ being defined as a global
      // before other modules access it. Custom chunking breaks this module resolution.
    });
  },
};

export default config;
