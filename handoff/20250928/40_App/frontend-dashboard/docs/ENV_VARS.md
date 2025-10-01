# Environment Variables Guide

This document provides a comprehensive guide to all environment variables used in the Morning AI Frontend Dashboard.

## Quick Start (10-minute setup)

1. **Clone and navigate to the project:**
   ```bash
   git clone https://github.com/RC918/morningai.git
   cd morningai/handoff/20250928/40_App/frontend-dashboard
   ```

2. **Copy environment template:**
   ```bash
   cp .env.sample .env.local
   ```

3. **Install dependencies:**
   ```bash
   pnpm install
   ```

4. **Start development server:**
   ```bash
   pnpm run dev
   ```

5. **Open browser:**
   Navigate to `http://localhost:5173`

## Environment Variables Reference

### Core Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `VITE_API_BASE_URL` | Backend API base URL | `http://localhost:5001` | Yes |
| `VITE_USE_MOCK` | Enable/disable mock data | `true` | Yes |
| `VITE_ENABLE_MOCK_DATA` | Legacy mock data flag | `true` | No |

### Feature Flags

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `VITE_FEATURES` | Comma-separated list of enabled features | `dashboard,checkout,settings` | Yes |

**Available Features:**
- `dashboard` - Main dashboard page
- `strategies` - Strategy management page  
- `approvals` - Decision approval page
- `history` - History analysis page
- `costs` - Cost analysis page
- `settings` - System settings page
- `checkout` - Billing checkout page

### Payment Integration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `VITE_STRIPE_PUBLISHABLE_KEY` | Stripe publishable key | `pk_test_...` | Yes |

### Error Tracking

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `VITE_SENTRY_DSN` | Sentry error tracking DSN | - | No |

## Environment-Specific Configuration

### Local Development (.env.local)
```bash
# API Configuration
VITE_API_BASE_URL=http://localhost:5001
VITE_USE_MOCK=true

# Feature Flags
VITE_FEATURES=dashboard,checkout,settings

# Payment (Test Keys)
VITE_STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_test_publishable_key_here

# Error Tracking
VITE_SENTRY_DSN=your_sentry_dsn_here
```

### Production (.env.production)
```bash
# API Configuration
VITE_API_BASE_URL=https://morningai-backend-v2.onrender.com
VITE_USE_MOCK=false

# Feature Flags
VITE_FEATURES=dashboard,checkout,settings

# Payment (Live Keys)
VITE_STRIPE_PUBLISHABLE_KEY=pk_live_your_stripe_publishable_key_here

# Error Tracking
VITE_SENTRY_DSN=${SENTRY_DSN}
```

## Deployment Platform Configuration

### Vercel Environment Variables

Set these in your Vercel project dashboard:

```bash
# Core
VITE_API_BASE_URL=https://morningai-backend-v2.onrender.com
VITE_USE_MOCK=false
VITE_FEATURES=dashboard,checkout,settings

# Payment
VITE_STRIPE_PUBLISHABLE_KEY=pk_live_your_stripe_publishable_key_here

# Error Tracking
VITE_SENTRY_DSN=your_sentry_dsn_here
```

### Render Environment Variables

Set these in your Render service dashboard:

```bash
# Backend Variables (for reference)
STRIPE_SECRET_KEY=sk_live_your_stripe_secret_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here
SENTRY_DSN=your_sentry_dsn_here
SENTRY_AUTH_TOKEN=your_sentry_auth_token_here
```

## Backend Environment Variables (Reference)

The frontend connects to a Flask backend that requires these environment variables:

| Variable | Description | Required |
|----------|-------------|----------|
| `STRIPE_SECRET_KEY` | Stripe secret key | Yes |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook secret | Yes |
| `SENTRY_DSN` | Sentry error tracking DSN | No |
| `SENTRY_AUTH_TOKEN` | Sentry authentication token | No |
| `DATABASE_URL` | Database connection string | Yes |
| `JWT_SECRET_KEY` | JWT signing secret | Yes |

## Feature Flag Usage Examples

### Enable only Dashboard and Settings
```bash
VITE_FEATURES=dashboard,settings
```

### Enable all features
```bash
VITE_FEATURES=dashboard,strategies,approvals,history,costs,settings,checkout
```

### Minimal configuration (Dashboard only)
```bash
VITE_FEATURES=dashboard
```

## Troubleshooting

### Common Issues

1. **"Feature not available" errors**
   - Check `VITE_FEATURES` includes the required feature
   - Verify environment file is loaded correctly

2. **API connection failures**
   - Verify `VITE_API_BASE_URL` is correct
   - Check backend service is running
   - Ensure CORS is configured properly

3. **Payment integration issues**
   - Verify Stripe keys are correct for environment
   - Check key format (pk_test_/pk_live_ prefix)

4. **Build failures**
   - Ensure all required environment variables are set
   - Check for typos in variable names
   - Verify .env files are in correct location

### Debug Commands

```bash
# Check environment variables are loaded
pnpm run dev --debug

# Verify build with environment
pnpm run build

# Run type checking
pnpm run typecheck

# Run linting
pnpm run lint

# Run smoke tests
pnpm run test:smoke
```

## Security Notes

- Never commit `.env.local` or `.env.production` files
- Use different Stripe keys for development and production
- Rotate secrets regularly
- Use Sentry for error tracking in production
- Enable HTTPS in production environments

## Support

For additional help:
1. Check the main README.md
2. Review the project documentation
3. Contact the development team
4. Check GitHub issues for known problems
