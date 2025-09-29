# Morning AI API Backend

Flask-based API backend for the Morning AI intelligent decision system.

## Features

- **Authentication**: JWT-based user authentication
- **Cloud Resource Monitoring**: Health checks for Sentry, Cloudflare, Upstash, Vercel, Render, and Supabase
- **System Metrics**: Real-time system performance monitoring
- **Health Checks**: Comprehensive health monitoring endpoints
- **CORS Support**: Cross-origin resource sharing for frontend integration

## Quick Start

### Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Run the development server:
```bash
python run.py
```

The API will be available at `http://localhost:8000`

### Production

The application is configured for deployment on Render.com using the `render.yaml` configuration.

## API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `GET /api/auth/verify` - Token verification

### Health Monitoring
- `GET /health` - Basic health check
- `GET /healthz` - Detailed health check with cloud resources
- `GET /api/cloud/status` - Cloud resource status

### System
- `GET /api/system/metrics` - System performance metrics
- `GET /openapi.json` - OpenAPI specification

## Environment Variables

See `.env.example` for all required environment variables.

### Required for Cloud Resource Monitoring:
- `SENTRY_DSN` - Sentry error tracking DSN
- `CLOUDFLARE_API_TOKEN` - Cloudflare API token
- `UPSTASH_REDIS_REST_URL` - Upstash Redis REST URL
- `VERCEL_TOKEN` - Vercel API token
- `RENDER_API_KEY` - Render API key
- `SUPABASE_URL` - Supabase project URL

## Testing

Run the test script to verify all endpoints:
```bash
python src/test_api.py
```

## Deployment

The application is configured for deployment on Render.com. See `render.yaml` for deployment configuration.
