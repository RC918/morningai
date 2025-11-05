import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { TolgeeProvider } from '@tolgee/react'
import { I18nextProvider } from 'react-i18next'
import './index.css'
import i18n, { tolgee } from './i18n'
import App from './App.jsx'
import { bootstrapCsrf } from './lib/api-client.ts'
import { isFeatureEnabled } from './lib/feature-flags.ts'

console.log('[DEBUG] Feature Flag Debug:', {
  urlParam: new URLSearchParams(location.search).get('feature_OWNER_CONSOLE_API'),
  localStorage: localStorage.getItem('feature_flag_OWNER_CONSOLE_API'),
  env: import.meta.env.VITE_FEATURE_OWNER_CONSOLE_API,
  computed: isFeatureEnabled('OWNER_CONSOLE_API'),
  allEnv: import.meta.env
});

if (import.meta.env.VITE_SENTRY_DSN) {
  import('@sentry/react').then((Sentry) => {
    Sentry.init({
      dsn: import.meta.env.VITE_SENTRY_DSN,
      environment: import.meta.env.MODE,
      integrations: [
        Sentry.browserTracingIntegration(),
        Sentry.replayIntegration(),
      ],
      tracesSampleRate: Number(import.meta.env.VITE_SENTRY_TRACES_SAMPLE_RATE ?? 0.1),
      replaysSessionSampleRate: Number(import.meta.env.VITE_SENTRY_REPLAYS_SESSION_SAMPLE_RATE ?? 0.01),
      replaysOnErrorSampleRate: 1.0,
    })
  })
}

bootstrapCsrf().catch(err => {
  console.warn('CSRF bootstrap failed:', err);
});

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <TolgeeProvider tolgee={tolgee}>
      <I18nextProvider i18n={i18n}>
        <App />
      </I18nextProvider>
    </TolgeeProvider>
  </StrictMode>,
)
