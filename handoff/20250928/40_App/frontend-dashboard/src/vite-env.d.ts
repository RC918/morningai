
interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  readonly VITE_SENTRY_DSN: string
  readonly VITE_SENTRY_ENVIRONMENT: string
  readonly VITE_GA_MEASUREMENT_ID: string
  readonly VITE_STRIPE_PUBLISHABLE_KEY: string
  readonly VITE_ENABLE_ANALYTICS: string
  readonly VITE_ENABLE_SENTRY: string
  readonly VITE_USE_MOCK: string
  readonly VITE_PHASE3_DEPLOYMENT_DATE: string
  readonly VITE_FEATURES: string
  readonly VITE_PHASE: string
  readonly VITE_SUPABASE_URL: string
  readonly VITE_SUPABASE_ANON_KEY: string
  readonly VITE_TOLGEE_API_URL: string
  readonly VITE_TOLGEE_API_KEY: string
  readonly VITE_TOLGEE_PROJECT_ID: string
  readonly MODE: string
  readonly DEV: boolean
  readonly PROD: boolean
  readonly SSR: boolean
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

interface Window {
  Sentry?: typeof import('@sentry/react')
  gtag?: (
    command: 'config' | 'event' | 'set',
    targetId: string,
    config?: Record<string, any>
  ) => void
}
