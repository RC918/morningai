# Morning AI Frontend Dashboard

React-based dashboard for the Morning AI intelligent decision system.

## Features

- **Real-time Monitoring**: System metrics and performance monitoring
- **Cloud Resource Status**: Live status of integrated cloud services
- **Decision Management**: AI decision approval and management interface
- **Authentication**: Secure user authentication with JWT tokens
- **Responsive Design**: Mobile-friendly interface with modern UI components

## Quick Start

### Development

1. Install dependencies:
```bash
pnpm install
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Start the development server:
```bash
pnpm dev
```

The application will be available at `http://localhost:5173`

### Production

The application is configured for deployment on Vercel using the `vercel.json` configuration in the project root.

## Environment Variables

- `VITE_API_BASE_URL` - Backend API base URL
- `VITE_APP_NAME` - Application name
- `VITE_APP_VERSION` - Application version

## Components

### Core Components
- `Dashboard` - Main system monitoring dashboard
- `LoginPage` - User authentication interface
- `CloudStatus` - Cloud resource status monitoring
- `DecisionApproval` - AI decision management interface

### UI Components
Built with shadcn/ui components for consistent design and accessibility.

## Integration

The frontend integrates with the Morning AI API backend for:
- User authentication
- Real-time system metrics
- Cloud resource status monitoring
- AI decision management

## Deployment

Configured for deployment on Vercel with automatic builds from the main branch.
