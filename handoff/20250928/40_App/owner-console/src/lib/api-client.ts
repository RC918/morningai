const API_BASE_URL =
  (typeof window !== 'undefined' && (window as any).__VITE_API_BASE_URL__) ||
  (typeof process !== 'undefined' ? process.env.VITE_API_BASE_URL : '') ||
  '';

/**
 * Get CSRF token from cookie
 */
function getCsrfToken(): string | null {
  if (typeof document === 'undefined') return null;
  
  const match = document.cookie.match(/csrf_token=([^;]+)/);
  return match ? match[1] : null;
}

/**
 * API client with automatic credentials and CSRF token injection
 * 
 * P0-3 Security Fix:
 * - Adds credentials: 'include' to send HttpOnly cookies
 * - Injects X-CSRF-Token header for POST/PUT/PATCH/DELETE requests
 */
export async function apiClient<T>(
  url: string,
  options: RequestInit = {}
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  };
  
  const unsafeMethods = ['POST', 'PUT', 'PATCH', 'DELETE'];
  if (options.method && unsafeMethods.includes(options.method.toUpperCase())) {
    const csrfToken = getCsrfToken();
    if (csrfToken) {
      headers['X-CSRF-Token'] = csrfToken;
    }
  }
  
  const res = await fetch(`${API_BASE_URL}${url}`, {
    ...options,
    credentials: 'include',  // P0-3: Always include credentials for HttpOnly cookies
    headers,
  });

  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`HTTP ${res.status} ${res.statusText} - ${text}`);
  }
  const ct = res.headers.get('content-type') || '';
  const data = ct.includes('application/json') ? await res.json() : await res.text();
  
  return {
    data,
    status: res.status,
    headers: res.headers,
  } as T;
}

/**
 * Bootstrap CSRF token before making authenticated requests
 * Call this on app initialization if using SameSite=None cookies
 */
export async function bootstrapCsrf(): Promise<void> {
  try {
    await fetch(`${API_BASE_URL}/api/auth/v2/csrf`, {
      credentials: 'include',
    });
  } catch (error) {
    console.warn('Failed to bootstrap CSRF token:', error);
  }
}
