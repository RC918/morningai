import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import './i18n'
import App from './App.jsx'
import { bootstrapCsrf } from './lib/api-client.ts'

bootstrapCsrf().catch(err => {
  console.warn('CSRF bootstrap failed:', err);
});

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
