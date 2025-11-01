import type { Config } from 'tailwindcss'

export default {
  content: [
    './index.html',
    './src/**/*.{js,jsx,ts,tsx,mdx}',
    '../../packages/shared-ui/src/**/*.{js,jsx,ts,tsx,mdx}',
    '../../packages/shared-ui/dist/**/*.{js,jsx,ts,tsx}',
    '../../node_modules/@morningai/shared-ui/**/*.{js,jsx,ts,tsx,mdx}'
  ],
  safelist: [
    'animate-spring-in',
    'animate-spring-out',
    'animate-bounce-gentle',
    'animate-pulse-subtle',
    'hover-lift',
    'press-effect',
    'scale-smooth',
    'focus-ring-spring',
    {
      pattern: /^(bg|text|border|ring)-(primary|accent|success|warning|error|joy|calm|energy|growth|wisdom)-(50|100|200|300|400|500|600|700|800|900|text|foreground)$/
    },
    {
      pattern: /^(p|m|gap|space)-(xs|sm|md|lg|xl|2xl|3xl|4xl)$/
    },
    {
      pattern: /^rounded-(sm|md|lg|xl|2xl|full)$/
    },
    {
      pattern: /^col-span-(1|2|3|4|5|6|7|8|9|10|11|12)$/
    },
    {
      pattern: /^(flex|grid)-(1|2|3|4|5|6|7|8|9|10|11|12)$/
    }
  ]
} satisfies Config
