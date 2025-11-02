/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
    '../../packages/shared-ui/src/**/*.{js,ts,jsx,tsx}',
  ],
  safelist: [
    'flex', 'grid', 'inline-flex', 'inline-grid',
    'w-full', 'h-full', 'min-h-screen',
    { pattern: /grid-cols-(1|2|3|4|6|12)/ },
    { pattern: /gap-(1|2|3|4|6|8)/ },
    { pattern: /p(x|y|t|b|l|r)?-(0|1|2|3|4|6|8|12|16)/ },
    { pattern: /m(x|y|t|b|l|r)?-(0|1|2|3|4|6|8|12|16|auto)/ },
    { pattern: /bg-(primary|secondary|accent|success|warning|error|info)-(50|100|200|300|400|500|600|700|800|900)/ },
    { pattern: /text-(primary|secondary|accent|success|warning|error|info)-(50|100|200|300|400|500|600|700|800|900)/ },
    { pattern: /border-(primary|secondary|accent|success|warning|error|info)-(50|100|200|300|400|500|600|700|800|900)/ },
    { pattern: /text-(xs|sm|base|lg|xl|2xl|3xl|4xl|5xl|6xl)/ },
    { pattern: /font-(light|normal|medium|semibold|bold)/ },
    'data-[state=open]', 'data-[state=closed]',
    'data-[side=top]', 'data-[side=right]', 'data-[side=bottom]', 'data-[side=left]',
    'animate-in', 'animate-out',
    'fade-in', 'fade-out',
    'zoom-in', 'zoom-out',
    'slide-in-from-top', 'slide-in-from-bottom', 'slide-in-from-left', 'slide-in-from-right',
  ],
  theme: {
    extend: {
      maxWidth: {
        'xs': '20rem',    // 320px
        'sm': '24rem',    // 384px
        'md': '28rem',    // 448px
        'lg': '32rem',    // 512px
        'xl': '36rem',    // 576px
        '2xl': '42rem',   // 672px
        '3xl': '48rem',   // 768px
        '4xl': '56rem',   // 896px
        '5xl': '64rem',   // 1024px
        '6xl': '72rem',   // 1152px
        '7xl': '80rem',   // 1280px
      },
    },
  },
  plugins: [],
}
