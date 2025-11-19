import type { StorybookConfig } from '@storybook/react-webpack5'
import type { Configuration } from 'webpack'

const config: StorybookConfig = {
  stories: ['../src/**/*.mdx', '../src/**/*.stories.@(js|jsx|mjs|ts|tsx)'],
  addons: [
    '@storybook/addon-links',
    '@storybook/addon-essentials',
    '@storybook/addon-interactions',
    '@storybook/addon-a11y',
  ],
  framework: {
    name: '@storybook/react-webpack5',
    options: {},
  },
  docs: {
    autodocs: 'tag',
  },
  async webpackFinal(config: Configuration) {
    config.module = config.module || {}
    config.module.rules = config.module.rules || []
    
    config.module.rules.push({
      test: /\.(ts|tsx)$/,
      exclude: /node_modules/,
      use: {
        loader: 'babel-loader',
        options: {
          presets: [
            '@babel/preset-env',
            ['@babel/preset-react', { runtime: 'automatic', importSource: 'react' }],
            '@babel/preset-typescript',
          ],
        },
      },
    })
    
    config.resolve = config.resolve || {}
    config.resolve.extensions = config.resolve.extensions || []
    if (!config.resolve.extensions.includes('.ts')) {
      config.resolve.extensions.push('.ts')
    }
    if (!config.resolve.extensions.includes('.tsx')) {
      config.resolve.extensions.push('.tsx')
    }
    
    return config
  },
}

export default config
