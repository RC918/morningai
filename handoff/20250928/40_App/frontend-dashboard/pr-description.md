## Comprehensive Frontend Engineering Improvements (A-H)

This PR implements 8 comprehensive frontend enhancement tasks as requested:

### A. Feature Flags (隱藏 WIP)
- ✅ Added `VITE_FEATURES` environment variable (default: dashboard,checkout,settings)
- ✅ Dynamic sidebar rendering based on enabled features
- ✅ WIP route redirects automatically to Dashboard
- ✅ Vercel-ready configuration for external visibility control

### B. Global State Management (輕量)
- ✅ Enhanced Zustand store with `useAppStore`: user/tenant/billing/status/toast
- ✅ SystemSettings integrated with global store
- ✅ Cross-page state persistence and consistency
- ✅ localStorage integration for settings persistence

### C. API Contract Automation
- ✅ Implemented `openapi-typescript` + `orval` for type generation
- ✅ Created centralized API client with type safety
- ✅ CheckoutPage updated to use generated SDK
- ✅ PR compilation guards against type breaking changes

### D. Accessibility Enhancements
- ✅ Enhanced `eslint-plugin-jsx-a11y` configuration
- ✅ Full Tab/Enter keyboard navigation for Checkout flow
- ✅ Added focus styles and ARIA attributes to shadcn components
- ✅ Lint passes with zero a11y errors

### E. Error Presentation & Observability
- ✅ **Frontend**: Error Boundary + global fetch interceptor → Toast notifications
- ✅ **Frontend**: Sentry integration with DSN configuration
- ✅ **Backend**: Structured JSON logging with request_id
- ✅ **Backend**: Consistent error format: {"error":{code,message}}
- ✅ **Verification**: Random API errors show consistent UI with trace IDs

### F. Documentation & Environment
- ✅ Created `docs/ENV_VARS.md` with comprehensive setup guide
- ✅ Added `.env.sample` with unified Render/Vercel variable names
- ✅ 10-minute local setup workflow documented
- ✅ New developer onboarding streamlined

### G. Post-Deploy Smoke Test Expansion
- ✅ Extended existing health assertions with billing API checks
- ✅ Added 200/201 status assertions for `/api/billing/plans` and `/api/billing/checkout/session`
- ✅ Automated CI pipeline integration
- ✅ Main branch PR merge protection with health verification

### H. WIP Page UX (選配)
- ✅ Created friendly "即將推出" (Coming Soon) pages
- ✅ 3-second auto-redirect to Dashboard
- ✅ Milestone progress display
- ✅ User-friendly experience with manual navigation option

## Technical Implementation

### Key Files Added/Modified:
- `src/App.jsx` - Feature flags integration, Error Boundary, Sentry setup
- `src/components/Sidebar.jsx` - Dynamic feature-based menu rendering
- `src/lib/feature-flags.js` - Feature flag management system
- `src/stores/appStore.js` - Enhanced Zustand global state
- `src/components/ErrorBoundary.jsx` - React error boundary implementation
- `src/components/WIPPage.jsx` - User-friendly WIP page component
- `src/lib/api.js` - Centralized API client with error handling
- `docs/ENV_VARS.md` - Comprehensive environment setup guide
- `scripts/smoke-tests.js` - Extended billing API health checks
- `orval.config.js` - API contract automation configuration

### Environment Variables:
```bash
# Feature Flags
VITE_FEATURES=dashboard,checkout,settings

# API Configuration  
VITE_API_BASE_URL=http://localhost:5001
VITE_USE_MOCK=false

# Error Tracking
VITE_SENTRY_DSN=your-sentry-dsn

# Payment Integration (for future Stripe/TapPay)
STRIPE_SECRET_KEY=your-stripe-key
STRIPE_WEBHOOK_SECRET=your-webhook-secret
```

## Verification Completed

### ✅ Local Testing:
- Feature flags working: sidebar shows only enabled features
- Global state: Settings persist across navigation and reload
- API integration: CheckoutPage uses centralized API client
- Accessibility: Full keyboard navigation, zero lint errors
- Error handling: API errors show consistent toast notifications
- WIP pages: Friendly redirect experience

### ✅ Build & Lint:
- `pnpm run build` - ✅ Passes
- `pnpm run lint` - ✅ Zero errors
- `pnpm typecheck` - ✅ Type safety verified

### ✅ Browser Testing:
- Dashboard navigation ✅
- Settings page with global state ✅  
- Checkout page with API integration ✅
- Feature flag dynamic rendering ✅
- Error boundary and toast notifications ✅

## Preserves Existing Functionality
- ✅ All billing integration from PR #49 maintained
- ✅ Mock data toggle functionality preserved
- ✅ Authentication flow unchanged
- ✅ Design system and UI components intact
- ✅ Backend API endpoints fully compatible

## CI/CD Integration
- Extended post-deploy health assertions
- Billing API smoke tests automated
- Type checking in build pipeline
- Accessibility linting enforced

---

**Link to Devin run**: https://app.devin.ai/sessions/5536dd1cc32144ef86804f80be4f4a24
**Requested by**: @RC918

Ready for review and deployment! 🚀
