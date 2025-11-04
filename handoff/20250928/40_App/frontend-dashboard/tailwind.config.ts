/**
 * Tailwind CSS v4 Configuration
 * 
 * This config ensures Tailwind scans the shared-ui package for classes.
 * Tailwind v4 uses @theme in CSS for configuration, but we still need
 * to specify content paths for proper class detection.
 * 
 * Note: Tailwind v4 doesn't support safelist in config. Instead, use
 * the @theme directive in CSS to define custom utilities and ensure
 * all classes are included in the final build.
 */
export default {
  content: [
    './index.html',
    './src/**/*.{js,jsx,ts,tsx,mdx}',
    '../../packages/shared-ui/src/**/*.{js,jsx,ts,tsx,mdx}',
    '../../packages/shared-ui/dist/**/*.{js,jsx,ts,tsx}',
    '../../node_modules/@morningai/shared-ui/**/*.{js,jsx,ts,tsx,mdx}'
  ]
}
