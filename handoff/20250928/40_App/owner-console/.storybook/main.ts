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
    '@storybook/addon-a11y',
    'storybook-dark-mode'
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
    const filteredPlugins = (config.plugins || []).filter((plugin: any) => {
      if (!plugin) return false;
      const name = typeof plugin === 'object' && plugin.name ? plugin.name : '';
      return !name.toLowerCase().includes('pwa');
    });

    return mergeConfig(config, {
      plugins: filteredPlugins,
      // optimizeDeps: {
      //   include: [
      //     'react',
      //     'react-dom',
      //     '@storybook/react',
      //   ],
      // },
      build: {
        minify: false,
      },
      esbuild: {
        target: 'es2020', // More conservative target
      },
    });
  },
};

export default config;
