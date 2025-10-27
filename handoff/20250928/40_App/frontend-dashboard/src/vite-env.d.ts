
interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  readonly VITE_SENTRY_DSN: string
  readonly VITE_SENTRY_ENVIRONMENT: string
  readonly VITE_GA_MEASUREMENT_ID: string
  readonly VITE_STRIPE_PUBLISHABLE_KEY: string
  readonly VITE_ENABLE_ANALYTICS: string
  readonly VITE_ENABLE_SENTRY: string
  readonly MODE: string
  readonly DEV: boolean
  readonly PROD: boolean
  readonly SSR: boolean
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

interface Window {
  Sentry?: {
    captureException: (error: Error, context?: any) => void
    captureMessage: (message: string, level?: string) => void
    setUser: (user: any) => void
    setContext: (name: string, context: any) => void
  }
  gtag?: (
    command: 'config' | 'event' | 'set',
    targetId: string,
    config?: Record<string, any>
  ) => void
}
