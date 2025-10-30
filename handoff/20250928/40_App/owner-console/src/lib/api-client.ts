const API_BASE_URL =
  (typeof window !== 'undefined' && (window as any).__VITE_API_BASE_URL__) ||
  (typeof process !== 'undefined' ? process.env.VITE_API_BASE_URL : '') ||
  '';

export async function apiClient<T>(
  url: string,
  options: RequestInit
): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${url}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...options.headers },
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
