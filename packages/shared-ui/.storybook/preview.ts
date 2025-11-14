import type { Preview } from '@storybook/react'
import { applyDesignTokens } from '../src/design-tokens'

if (typeof window !== 'undefined') {
  applyDesignTokens()
}

const preview: Preview = {
  parameters: {
    actions: { argTypesRegex: '^on[A-Z].*' },
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/i,
      },
    },
  },
}

export default preview
