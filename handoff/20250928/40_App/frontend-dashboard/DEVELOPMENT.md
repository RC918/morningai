# Development Guide

## Running the Preview Server Locally

When running the preview server locally for testing (e.g., for UX QA capture scripts), you may encounter issues with the default IPv6 binding. To ensure reliable connectivity:

```bash
# Build the app
pnpm run build

# Start preview server with explicit IPv4 binding
pnpm run preview --host 127.0.0.1 --port 4173
```

### Why `--host 127.0.0.1`?

By default, Vite preview binds to IPv6 `[::1]`, which can cause connection issues with tools like Playwright, curl, and Node.js fetch when they attempt to connect via IPv4 `127.0.0.1`. Explicitly binding to `127.0.0.1` ensures compatibility with all tools.

### Background Process

If you need to run the server in the background:

```bash
nohup pnpm run preview --host 127.0.0.1 --port 4173 </dev/null >/tmp/preview.log 2>&1 &
```

This prevents the process from being stopped by job control signals (SIGTTIN) when it tries to read from stdin.

## Supabase Configuration

The app uses Supabase for authentication. If Supabase credentials are not configured, the app will:

1. Display a warning in the console: `Supabase not configured - Auth features will be disabled`
2. Load successfully without crashing
3. Return errors for all auth operations instead of throwing exceptions

This graceful degradation allows the app to be previewed and tested even without Supabase credentials.

### Required Environment Variables

For full authentication functionality, set these in your `.env` file:

```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
```

**Note**: The `.env` file is gitignored and should never be committed to the repository.
