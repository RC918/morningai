/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly MODE: string
  readonly BASE_URL: string
  readonly PROD: boolean
  readonly DEV: boolean
  readonly SSR: boolean
  readonly VITE_API_BASE_URL: string
  readonly VITE_PREVIEW_PUBLIC_METRICS?: string
  readonly VITE_FEATURES: string
  readonly VITE_FEATURE_OWNER_CONSOLE_API: string
  readonly VITE_FEATURE_OWNER_CONSOLE_GOVERNANCE: string
  readonly VITE_FEATURE_OWNER_CONSOLE_TENANTS: string
  readonly VITE_FEATURE_OWNER_CONSOLE_MONITORING: string
  readonly VITE_FEATURE_OWNER_CONSOLE_SETTINGS: string
  readonly VITE_FEATURE_OWNER_CONSOLE_SECURITY: string
  readonly VITE_FEATURE_OWNER_CONSOLE_PWA: string
  readonly [key: `VITE_FEATURE_${string}`]: string | undefined
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
