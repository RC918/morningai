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
      colors: {
        primary: {
          50: 'var(--color-primary-lightest, #eff6ff)',
          100: 'var(--color-primary-lighter, #dbeafe)',
          200: 'var(--color-primary-light, #bfdbfe)',
          300: 'var(--color-primary-light, #93c5fd)',
          400: 'var(--color-primary-light, #60a5fa)',
          500: 'var(--color-primary, #007AFF)',
          600: 'var(--color-primary-hover, #0051D0)',
          700: 'var(--color-primary-active, #1d4ed8)',
          800: '#1e40af',
          900: '#1e3a8a',
        },
        success: {
          50: '#f0fdf4',
          100: '#dcfce7',
          200: '#bbf7d0',
          300: '#86efac',
          400: '#4ade80',
          500: 'var(--color-success, #22c55e)',
          600: '#16a34a',
          700: '#15803d',
          800: '#166534',
          900: '#14532d',
        },
        warning: {
          50: '#fffbeb',
          100: 'var(--color-warning-light, #fef3c7)',
          200: '#fde68a',
          300: '#fcd34d',
          400: '#fbbf24',
          500: 'var(--color-warning, #f59e0b)',
          600: '#d97706',
          700: '#b45309',
          800: '#92400e',
          900: '#78350f',
        },
        error: {
          50: '#fef2f2',
          100: 'var(--color-error-light, #fee2e2)',
          200: '#fecaca',
          300: '#fca5a5',
          400: '#f87171',
          500: 'var(--color-error, #ef4444)',
          600: '#dc2626',
          700: '#b91c1c',
          800: '#991b1b',
          900: '#7f1d1d',
        },
      },
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
