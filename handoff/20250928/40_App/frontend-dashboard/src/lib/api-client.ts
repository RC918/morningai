const API_BASE_URL =
  (typeof window !== 'undefined' && (window as any).__VITE_API_BASE_URL__) ||
  (typeof process !== 'undefined' ? process.env.VITE_API_BASE_URL : '') ||
  'https://morningai-backend-v2.onrender.com';

export async function apiClient({
  url,
  method,
  params,
  data,
  headers,
}: {
  url: string;
  method: string;
  params?: Record<string, any>;
  data?: any;
  headers?: Record<string, string>;
}) {
  const qs = params
    ? '?' +
      new URLSearchParams(
        Object.fromEntries(
          Object.entries(params).map(([k, v]) => [k, String(v)])
        )
      ).toString()
    : '';

  const res = await fetch(`${API_BASE_URL}${url}${qs}`, {
    method,
    headers: { 'Content-Type': 'application/json', ...(headers || {}) },
    body: data != null ? JSON.stringify(data) : undefined,
  });

  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`HTTP ${res.status} ${res.statusText} - ${text}`);
  }
  const ct = res.headers.get('content-type') || '';
  return ct.includes('application/json') ? res.json() : res.text();
}
