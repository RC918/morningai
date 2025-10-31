
interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  readonly VITE_FEATURES: string
  readonly VITE_FEATURE_OWNER_CONSOLE_API: string
  readonly VITE_FEATURE_OWNER_CONSOLE_GOVERNANCE: string
  readonly VITE_FEATURE_OWNER_CONSOLE_TENANTS: string
  readonly VITE_FEATURE_OWNER_CONSOLE_MONITORING: string
  readonly VITE_FEATURE_OWNER_CONSOLE_SETTINGS: string
  readonly VITE_FEATURE_OWNER_CONSOLE_SECURITY: string
  readonly VITE_FEATURE_OWNER_CONSOLE_PWA: string
  readonly VITE_SUPABASE_URL?: string
  readonly VITE_SUPABASE_ANON_KEY?: string
  readonly [key: `VITE_FEATURE_${string}`]: string | undefined
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
