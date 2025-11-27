import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { VitePWA } from 'vite-plugin-pwa'
import { sentryVitePlugin } from '@sentry/vite-plugin'
import path from 'path'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // Disable PWA for Storybook builds to prevent interference with iframe communication
  const isStorybook = Boolean(process.env.STORYBOOK)
  
  const enableSentry = Boolean(
    process.env.SENTRY_ORG && 
    process.env.SENTRY_PROJECT && 
    process.env.SENTRY_AUTH_TOKEN
  )

  const sentryPlugin = enableSentry
    ? Object.assign(
        sentryVitePlugin({
          org: process.env.SENTRY_ORG,
          project: process.env.SENTRY_PROJECT,
          authToken: process.env.SENTRY_AUTH_TOKEN,
          release: {
            name: process.env.VERCEL_GIT_COMMIT_SHA || process.env.SENTRY_RELEASE
          },
          sourcemaps: {
            assets: './dist/**',
            filesToDeleteAfterUpload: './dist/**/*.map'
          },
          telemetry: false
        }),
        { apply: 'build' }
      )
    : null

  // PWA plugin configuration - disabled for Storybook builds
  const pwaPlugin = !isStorybook ? VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.ico', 'apple-touch-icon.png', 'icon-192.png', 'icon-512.png'],
      manifest: {
        name: 'Morning AI - Intelligent Decision Support',
        short_name: 'Morning AI',
        description: 'AI-powered decision support platform with real-time analytics and insights',
        theme_color: '#000000',
        background_color: '#ffffff',
        display: 'standalone',
        icons: [
          {
            src: '/icon-192.png',
            sizes: '192x192',
            type: 'image/png',
            purpose: 'any maskable'
          },
          {
            src: '/icon-512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'any maskable'
          }
        ]
      },
      workbox: {
        skipWaiting: true,
        clientsClaim: true,
        cleanupOutdatedCaches: true,
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff,woff2}'],
        navigateFallback: '/index.html',
        navigateFallbackAllowlist: [/^\/(?!api).*/],
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/fonts\.googleapis\.com\/.*/i,
            handler: 'CacheFirst',
            options: {
              cacheName: 'google-fonts-cache',
              expiration: {
                maxEntries: 10,
                maxAgeSeconds: 60 * 60 * 24 * 365 // 1 year
              },
              cacheableResponse: {
                statuses: [0, 200]
              }
            }
          },
          {
            urlPattern: /^https:\/\/fonts\.gstatic\.com\/.*/i,
            handler: 'CacheFirst',
            options: {
              cacheName: 'gstatic-fonts-cache',
              expiration: {
                maxEntries: 10,
                maxAgeSeconds: 60 * 60 * 24 * 365 // 1 year
              },
              cacheableResponse: {
                statuses: [0, 200]
              }
            }
          },
          {
            urlPattern: /\/api\/.*/i,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'api-cache',
              expiration: {
                maxEntries: 50,
                maxAgeSeconds: 60 * 5 // 5 minutes
              },
              networkTimeoutSeconds: 10
            }
          }
        ]
      },
      devOptions: {
        enabled: false
      }
    }) : null

  return {
    plugins: [
      react(),
      tailwindcss(),
      ...(sentryPlugin ? [sentryPlugin] : []),
      ...(pwaPlugin ? [pwaPlugin] : []),
    ],
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
      },
    },
    build: {
      sourcemap: true,
      rollupOptions: {
        output: {
          manualChunks: (id) => {
            // Only split clearly independent, heavy libraries
            // Let React/Radix follow Vite's default behavior to avoid bundling issues
            
            // Charts library - heavy, clearly independent
            if (id.includes('node_modules/recharts')) {
              return 'charts-vendor';
            }
            
            // Supabase - heavy library, clearly independent
            if (id.includes('node_modules/@supabase')) {
              return 'supabase-vendor';
            }
            
            // Sentry - monitoring library, clearly independent
            if (id.includes('node_modules/@sentry')) {
              return 'sentry-vendor';
            }
            
            // Animation library - heavy, clearly independent
            if (id.includes('node_modules/framer-motion')) {
              return 'motion-vendor';
            }
            
            // i18n libraries - clearly independent
            if (id.includes('node_modules/i18next') || 
                id.includes('node_modules/react-i18next') ||
                id.includes('node_modules/@tolgee')) {
              return 'i18n-vendor';
            }
            
            // Icons library - clearly independent
            if (id.includes('node_modules/lucide-react')) {
              return 'icons-vendor';
            }
          },
        },
      },
      chunkSizeWarningLimit: 600,
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
  }
})
