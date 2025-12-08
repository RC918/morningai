import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import {
  getCsrfToken,
  storeCsrfToken,
  clearCsrfToken,
  ensureCsrfToken,
  getCookie,
  shouldIncludeCsrf,
  updateCsrfFromResponse,
  _resetCsrfState,
} from '../csrf-token';

const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('CSRF Token Module', () => {
  const originalEnv = import.meta.env;

  beforeEach(() => {
    sessionStorage.clear();
    vi.clearAllMocks();
    mockFetch.mockReset();
    _resetCsrfState();

    Object.defineProperty(document, 'cookie', {
      writable: true,
      value: '',
    });

    Object.defineProperty(import.meta, 'env', {
      value: { ...originalEnv, VITE_API_BASE_URL: 'http://test.local' },
      writable: true,
      configurable: true,
    });
  });

  afterEach(() => {
    Object.defineProperty(import.meta, 'env', {
      value: originalEnv,
      writable: true,
      configurable: true,
    });
  });

  describe('getCookie', () => {
    it('should return null when no cookies exist', () => {
      expect(getCookie('csrf_token')).toBeNull();
    });

    it('should return cookie value when it exists', () => {
      Object.defineProperty(document, 'cookie', {
        writable: true,
        value: 'csrf_token=test-token-123',
      });

      expect(getCookie('csrf_token')).toBe('test-token-123');
    });

    it('should return correct cookie when multiple cookies exist', () => {
      Object.defineProperty(document, 'cookie', {
        writable: true,
        value: 'other=value; csrf_token=my-csrf-token; another=data',
      });

      expect(getCookie('csrf_token')).toBe('my-csrf-token');
    });
  });

  describe('getCsrfToken', () => {
    it('should return null when no token exists', () => {
      expect(getCsrfToken()).toBeNull();
    });

    it('should return token from cookie (highest priority)', () => {
      Object.defineProperty(document, 'cookie', {
        writable: true,
        value: 'csrf_token=cookie-token',
      });
      sessionStorage.setItem('csrf_token', 'session-token');

      expect(getCsrfToken()).toBe('cookie-token');
    });

    it('should sync sessionStorage when cookie differs', () => {
      Object.defineProperty(document, 'cookie', {
        writable: true,
        value: 'csrf_token=new-cookie-token',
      });
      sessionStorage.setItem('csrf_token', 'old-session-token');

      getCsrfToken();

      expect(sessionStorage.getItem('csrf_token')).toBe('new-cookie-token');
    });

    it('should return token from sessionStorage when no cookie', () => {
      sessionStorage.setItem('csrf_token', 'session-only-token');

      expect(getCsrfToken()).toBe('session-only-token');
    });
  });

  describe('storeCsrfToken', () => {
    it('should store token in sessionStorage', () => {
      storeCsrfToken('new-token');

      expect(sessionStorage.getItem('csrf_token')).toBe('new-token');
    });

    it('should update in-memory cache', () => {
      storeCsrfToken('memory-token');

      // Clear sessionStorage to verify in-memory fallback
      sessionStorage.clear();
      Object.defineProperty(document, 'cookie', {
        writable: true,
        value: '',
      });

      // The in-memory token should still be accessible
      expect(getCsrfToken()).toBe('memory-token');
    });
  });

  describe('clearCsrfToken', () => {
    it('should clear token from sessionStorage', () => {
      sessionStorage.setItem('csrf_token', 'to-be-cleared');

      clearCsrfToken();

      expect(sessionStorage.getItem('csrf_token')).toBeNull();
    });

    it('should clear in-memory cache', () => {
      storeCsrfToken('to-be-cleared');
      clearCsrfToken();

      expect(getCsrfToken()).toBeNull();
    });
  });

  describe('shouldIncludeCsrf', () => {
    it('should return true for POST', () => {
      expect(shouldIncludeCsrf('POST')).toBe(true);
    });

    it('should return true for PUT', () => {
      expect(shouldIncludeCsrf('PUT')).toBe(true);
    });

    it('should return true for PATCH', () => {
      expect(shouldIncludeCsrf('PATCH')).toBe(true);
    });

    it('should return true for DELETE', () => {
      expect(shouldIncludeCsrf('DELETE')).toBe(true);
    });

    it('should return false for GET', () => {
      expect(shouldIncludeCsrf('GET')).toBe(false);
    });

    it('should return false for HEAD', () => {
      expect(shouldIncludeCsrf('HEAD')).toBe(false);
    });

    it('should be case-insensitive', () => {
      expect(shouldIncludeCsrf('post')).toBe(true);
      expect(shouldIncludeCsrf('Post')).toBe(true);
    });
  });

  describe('updateCsrfFromResponse', () => {
    it('should update token from X-CSRF-Token header', () => {
      const headers = new Headers();
      headers.set('X-CSRF-Token', 'response-token');

      updateCsrfFromResponse(headers);

      expect(sessionStorage.getItem('csrf_token')).toBe('response-token');
    });

    it('should not update when header is missing', () => {
      storeCsrfToken('existing-token');
      const headers = new Headers();

      updateCsrfFromResponse(headers);

      expect(sessionStorage.getItem('csrf_token')).toBe('existing-token');
    });
  });

  describe('ensureCsrfToken', () => {
    it('should not fetch when cookie token exists', async () => {
      Object.defineProperty(document, 'cookie', {
        writable: true,
        value: 'csrf_token=existing-cookie-token',
      });

      await ensureCsrfToken();

      expect(mockFetch).not.toHaveBeenCalled();
    });

    it('should not fetch when sessionStorage token exists', async () => {
      sessionStorage.setItem('csrf_token', 'existing-session-token');

      await ensureCsrfToken();

      expect(mockFetch).not.toHaveBeenCalled();
    });

    it('should fetch token when none exists', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        headers: { get: () => 'application/json' },
        json: async () => ({ csrf_token: 'fetched-token' }),
      });

      await ensureCsrfToken();

      expect(mockFetch).toHaveBeenCalledWith(
        'http://test.local/api/auth/v2/csrf',
        expect.objectContaining({
          method: 'GET',
          credentials: 'include',
        })
      );
      expect(sessionStorage.getItem('csrf_token')).toBe('fetched-token');
    });

    it('should use single-flight pattern for concurrent calls', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        headers: { get: () => 'application/json' },
        json: async () => ({ csrf_token: 'single-flight-token' }),
      });

      // Make concurrent calls
      const promise1 = ensureCsrfToken();
      const promise2 = ensureCsrfToken();
      const promise3 = ensureCsrfToken();

      await Promise.all([promise1, promise2, promise3]);

      // Should only fetch once
      expect(mockFetch).toHaveBeenCalledTimes(1);
    });
  });

  describe('Token Rotation Scenarios', () => {
    it('should sync all storage layers when backend rotates token via cookie', () => {
      // Initial state: old token in sessionStorage
      sessionStorage.setItem('csrf_token', 'old-token');

      // Backend rotates token (sets new cookie)
      Object.defineProperty(document, 'cookie', {
        writable: true,
        value: 'csrf_token=rotated-token',
      });

      // getCsrfToken should detect the rotation and sync
      const token = getCsrfToken();

      expect(token).toBe('rotated-token');
      expect(sessionStorage.getItem('csrf_token')).toBe('rotated-token');
    });

    it('should handle token rotation during login flow', async () => {
      // Step 1: Initial CSRF token fetch
      mockFetch.mockResolvedValueOnce({
        ok: true,
        headers: { get: () => 'application/json' },
        json: async () => ({ csrf_token: 'initial-token' }),
      });

      await ensureCsrfToken();
      expect(sessionStorage.getItem('csrf_token')).toBe('initial-token');

      // Step 2: Login succeeds, backend rotates token via cookie
      Object.defineProperty(document, 'cookie', {
        writable: true,
        value: 'csrf_token=post-login-token',
      });

      // Step 3: Next getCsrfToken call should return the rotated token
      const token = getCsrfToken();
      expect(token).toBe('post-login-token');
      expect(sessionStorage.getItem('csrf_token')).toBe('post-login-token');
    });

    it('should handle token rotation via response header', () => {
      // Initial token
      storeCsrfToken('original-token');

      // Response contains new token in header
      const headers = new Headers();
      headers.set('X-CSRF-Token', 'header-rotated-token');

      updateCsrfFromResponse(headers);

      expect(getCsrfToken()).toBe('header-rotated-token');
      expect(sessionStorage.getItem('csrf_token')).toBe('header-rotated-token');
    });

    it('should prefer cookie over sessionStorage after rotation', () => {
      // Scenario: sessionStorage has old token, cookie has new token
      sessionStorage.setItem('csrf_token', 'stale-session-token');
      Object.defineProperty(document, 'cookie', {
        writable: true,
        value: 'csrf_token=fresh-cookie-token',
      });

      // getCsrfToken should return cookie value and sync sessionStorage
      const token = getCsrfToken();

      expect(token).toBe('fresh-cookie-token');
      expect(sessionStorage.getItem('csrf_token')).toBe('fresh-cookie-token');
    });

    it('should clear stale in-memory token before fetching new one', async () => {
      // Set up stale in-memory token
      storeCsrfToken('stale-memory-token');

      // Clear sessionStorage and cookie to simulate cleared state
      sessionStorage.clear();
      Object.defineProperty(document, 'cookie', {
        writable: true,
        value: '',
      });

      // Reset state to simulate fresh start
      _resetCsrfState();

      mockFetch.mockResolvedValueOnce({
        ok: true,
        headers: { get: () => 'application/json' },
        json: async () => ({ csrf_token: 'fresh-token' }),
      });

      await ensureCsrfToken();

      expect(sessionStorage.getItem('csrf_token')).toBe('fresh-token');
    });

    it('should maintain consistency across multiple getCsrfToken calls', () => {
      // Set cookie token
      Object.defineProperty(document, 'cookie', {
        writable: true,
        value: 'csrf_token=consistent-token',
      });

      // Multiple calls should return same value
      const token1 = getCsrfToken();
      const token2 = getCsrfToken();
      const token3 = getCsrfToken();

      expect(token1).toBe('consistent-token');
      expect(token2).toBe('consistent-token');
      expect(token3).toBe('consistent-token');
    });
  });
});
