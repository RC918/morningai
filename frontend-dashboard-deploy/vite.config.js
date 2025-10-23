import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'
import criticalCSSPlugin from './vite-plugin-critical-css.js'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    criticalCSSPlugin({
      criticalCSS: `
        *,::before,::after{box-sizing:border-box;border-width:0;border-style:solid;border-color:#e5e7eb}
        html{line-height:1.5;-webkit-text-size-adjust:100%;-moz-tab-size:4;tab-size:4;font-family:Inter,system-ui,sans-serif;font-feature-settings:normal;font-variation-settings:normal}
        body{margin:0;line-height:inherit}
        #root{min-height:100vh;display:flex;flex-direction:column}
        .container{width:100%;margin-left:auto;margin-right:auto;padding-left:1rem;padding-right:1rem}
        @media(min-width:640px){.container{max-width:640px}}
        @media(min-width:768px){.container{max-width:768px}}
        @media(min-width:1024px){.container{max-width:1024px}}
        @media(min-width:1280px){.container{max-width:1280px}}
      `,
    }),
  ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  build: {
    sourcemap: true,
    cssCodeSplit: true,
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'ui-vendor': ['lucide-react', 'recharts', 'framer-motion'],
          'form-vendor': ['react-hook-form', '@hookform/resolvers', 'zod'],
          'i18n-vendor': ['i18next', 'react-i18next'],
        },
        assetFileNames: (assetInfo) => {
          const info = assetInfo.name.split('.');
          const ext = info[info.length - 1];
          if (/png|jpe?g|svg|gif|tiff|bmp|ico|webp|avif/i.test(ext)) {
            return `assets/images/[name]-[hash][extname]`;
          } else if (/woff2?|ttf|eot|otf/i.test(ext)) {
            return `assets/fonts/[name]-[hash][extname]`;
          }
          return `assets/[name]-[hash][extname]`;
        },
      },
    },
    chunkSizeWarningLimit: 600,
    minify: 'esbuild',
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:5001',
        changeOrigin: true,
        secure: false,
      },
    },
  },
})
