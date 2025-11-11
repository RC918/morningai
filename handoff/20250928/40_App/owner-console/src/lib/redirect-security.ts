/**
 * Sanitize redirect URL to prevent open redirect attacks
 * Only allows relative paths starting with /
 * 
 * @param url - The redirect URL to sanitize
 * @returns A safe redirect URL (defaults to '/' if invalid)
 */
export function sanitizeRedirect(url: string | null | undefined): string {
  if (!url || typeof url !== 'string') {
    return '/';
  }

  const trimmed = url.trim();

  if (trimmed.match(/^(javascript|data):/i)) {
    console.warn('[Security] Rejected dangerous protocol redirect:', url);
    return '/';
  }

  if (!trimmed.startsWith('/')) {
    console.warn('[Security] Rejected non-relative redirect:', url);
    return '/';
  }

  if (trimmed.startsWith('//')) {
    console.warn('[Security] Rejected protocol-relative redirect:', url);
    return '/';
  }

  return trimmed;
}
