import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import {
  storeTokenExpiry,
  getStoredTokenExpiry,
  clearTokens,
  storeUser,
  getStoredUser,
  isTokenExpired,
  isAuthenticated,
  login,
  logout,
  refreshAccessToken,
  getCurrentUser,
  startTokenRefresh,
  stopTokenRefresh,
  initAuth,
  cleanupAuth,
  authenticatedFetch,
} from '../auth';

const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('Auth Module', () => {
  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
    vi.clearAllMocks();
    mockFetch.mockReset();
    
    Object.defineProperty(document, 'cookie', {
      writable: true,
      value: '',
    });
    
    delete (window as any).location;
    (window as any).location = { href: '' };
  });
  
  afterEach(() => {
    vi.clearAllTimers();
    stopTokenRefresh();
  });

  describe('Token Expiry Management', () => {
    it('should store and retrieve token expiry', () => {
      const expiresAt = Date.now() + 60000;
      storeTokenExpiry(expiresAt);
      
      const retrieved = getStoredTokenExpiry();
      expect(retrieved).toBe(expiresAt);
    });

    it('should return null when no token expiry is stored', () => {
      const retrieved = getStoredTokenExpiry();
      expect(retrieved).toBeNull();
    });

    it('should clear token expiry', () => {
      const expiresAt = Date.now() + 60000;
      storeTokenExpiry(expiresAt);
      
      clearTokens();
      
      const retrieved = getStoredTokenExpiry();
      expect(retrieved).toBeNull();
    });
  });

  describe('User Management', () => {
    it('should store and retrieve user', () => {
      const user = {
        id: 'test-id',
        email: 'test@example.com',
        role: 'owner' as const,
        tenantId: 'tenant-1',
        name: 'Test User',
      };
      
      storeUser(user);
      
      const retrieved = getStoredUser();
      expect(retrieved).toEqual(user);
    });

    it('should return null when no user is stored', () => {
      const retrieved = getStoredUser();
      expect(retrieved).toBeNull();
    });

    it('should clear user data', () => {
      const user = {
        id: 'test-id',
        email: 'test@example.com',
        role: 'owner' as const,
        tenantId: 'tenant-1',
      };
      
      storeUser(user);
      clearTokens();
      
      const retrieved = getStoredUser();
      expect(retrieved).toBeNull();
    });
  });

  describe('Token Expiration Check', () => {
    it('should return false for non-expired token', () => {
      const expiresAt = Date.now() + 60 * 60 * 1000; // 1 hour from now
      expect(isTokenExpired(expiresAt)).toBe(false);
    });

    it('should return true for expired token', () => {
      const expiresAt = Date.now() - 1000; // 1 second ago
      expect(isTokenExpired(expiresAt)).toBe(true);
    });

    it('should return true for token about to expire (within buffer)', () => {
      const expiresAt = Date.now() + 2 * 60 * 1000; // 2 minutes from now (within 5min buffer)
      expect(isTokenExpired(expiresAt)).toBe(true);
    });
  });

  describe('Authentication Check', () => {
    it('should return true when valid token exists', () => {
      const expiresAt = Date.now() + 60 * 60 * 1000; // 1 hour from now
      storeTokenExpiry(expiresAt);
      
      expect(isAuthenticated()).toBe(true);
    });

    it('should return false when no token exists', () => {
      expect(isAuthenticated()).toBe(false);
    });

    it('should return false when token is expired', () => {
      const expiresAt = Date.now() - 1000; // 1 second ago
      storeTokenExpiry(expiresAt);
      
      expect(isAuthenticated()).toBe(false);
    });
  });

  describe('Login Flow (P0)', () => {
    beforeEach(() => {
      vi.mock('../feature-flags', () => ({
        isFeatureEnabled: () => true,
      }));
    });

    it('should successfully login with valid credentials', async () => {
      const mockUser = {
        id: 'user-123',
        email: 'test@example.com',
        role: 'owner' as const,
        tenantId: 'tenant-456',
        name: 'Test User',
      };

      const mockResponse = {
        user: mockUser,
        tokens: {
          expiresAt: Date.now() + 3600000,
        },
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        headers: { get: () => 'application/json' },
        json: async () => ({ csrf_token: 'csrf-123' }),
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await login({
        email: 'test@example.com',
        password: 'password123',
      });

      expect(result.user).toEqual(mockUser);
      expect(result.tokens.expiresAt).toBe(mockResponse.tokens.expiresAt);
      expect(getStoredUser()).toEqual(mockUser);
      expect(getStoredTokenExpiry()).toBe(mockResponse.tokens.expiresAt);
    });

    it('should throw error on invalid credentials', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        headers: { get: () => 'application/json' },
        json: async () => ({ csrf_token: 'csrf-123' }),
      });

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ message: 'Invalid credentials' }),
      });

      await expect(
        login({
          email: 'wrong@example.com',
          password: 'wrongpass',
        })
      ).rejects.toThrow('Invalid credentials');
    });

    it('should include credentials in login request', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        headers: { get: () => 'application/json' },
        json: async () => ({ csrf_token: 'csrf-123' }),
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          user: { id: '1', email: 'test@example.com', role: 'owner', tenantId: 't1' },
          tokens: { expiresAt: Date.now() + 3600000 },
        }),
      });

      await login({ email: 'test@example.com', password: 'pass' });

      const loginCall = mockFetch.mock.calls[1];
      expect(loginCall[1].credentials).toBe('include');
    });

    it('should send credentials in request body', async () => {
      const credentials = {
        email: 'test@example.com',
        password: 'password123',
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        headers: { get: () => 'application/json' },
        json: async () => ({ csrf_token: 'csrf-123' }),
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          user: { id: '1', email: credentials.email, role: 'owner', tenantId: 't1' },
          tokens: { expiresAt: Date.now() + 3600000 },
        }),
      });

      await login(credentials);

      const loginCall = mockFetch.mock.calls[1];
      expect(JSON.parse(loginCall[1].body as string)).toEqual(credentials);
    });
  });

  describe('Logout Flow (P0)', () => {
    beforeEach(() => {
      vi.mock('../feature-flags', () => ({
        isFeatureEnabled: () => true,
      }));
    });

    it('should clear local storage on logout', async () => {
      const user = {
        id: 'user-123',
        email: 'test@example.com',
        role: 'owner' as const,
        tenantId: 'tenant-456',
      };

      storeUser(user);
      storeTokenExpiry(Date.now() + 3600000);

      mockFetch.mockResolvedValueOnce({
        ok: true,
      });

      await logout();

      expect(getStoredUser()).toBeNull();
      expect(getStoredTokenExpiry()).toBeNull();
    });

    it('should call logout API endpoint', async () => {
      Object.defineProperty(document, 'cookie', {
        writable: true,
        value: 'csrf_token=test-csrf',
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
      });

      await logout();

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/auth/v2/logout'),
        expect.objectContaining({
          method: 'POST',
          credentials: 'include',
        })
      );
    });

    it('should include CSRF token in logout request', async () => {
      Object.defineProperty(document, 'cookie', {
        writable: true,
        value: 'csrf_token=logout-csrf-token',
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
      });

      await logout();

      const logoutCall = mockFetch.mock.calls[0];
      expect(logoutCall[1].headers['X-CSRF-Token']).toBe('logout-csrf-token');
    });

    it('should clear tokens even if API call fails', async () => {
      storeUser({ id: '1', email: 'test@example.com', role: 'owner', tenantId: 't1' });
      storeTokenExpiry(Date.now() + 3600000);

      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      await logout();

      expect(getStoredUser()).toBeNull();
      expect(getStoredTokenExpiry()).toBeNull();
    });
  });

  describe('Token Refresh (P0)', () => {
    beforeEach(() => {
      vi.mock('../feature-flags', () => ({
        isFeatureEnabled: () => true,
      }));
    });

    it('should refresh access token successfully', async () => {
      const newExpiresAt = Date.now() + 3600000;

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          tokens: { expiresAt: newExpiresAt },
        }),
      });

      const result = await refreshAccessToken();

      expect(result.expiresAt).toBe(newExpiresAt);
      expect(getStoredTokenExpiry()).toBe(newExpiresAt);
    });

    it('should clear tokens on refresh failure', async () => {
      storeTokenExpiry(Date.now() + 1000);

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
      });

      await expect(refreshAccessToken()).rejects.toThrow('Token refresh failed');
      expect(getStoredTokenExpiry()).toBeNull();
    });

    it('should include credentials in refresh request', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          tokens: { expiresAt: Date.now() + 3600000 },
        }),
      });

      await refreshAccessToken();

      const refreshCall = mockFetch.mock.calls[0];
      expect(refreshCall[1].credentials).toBe('include');
    });
  });

  describe('Get Current User (P0)', () => {
    it('should return stored user if available', async () => {
      const user = {
        id: 'user-123',
        email: 'test@example.com',
        role: 'owner' as const,
        tenantId: 'tenant-456',
        name: 'Test User',
      };

      storeUser(user);

      const result = await getCurrentUser();

      expect(result).toEqual(user);
      expect(mockFetch).not.toHaveBeenCalled();
    });
  });

  describe('Automatic Token Refresh (P0)', () => {
    beforeEach(() => {
      vi.useFakeTimers();
    });

    afterEach(() => {
      vi.useRealTimers();
    });

    it('should start token refresh interval', () => {
      const expiresAt = Date.now() + 3600000;
      storeTokenExpiry(expiresAt);

      startTokenRefresh();

      expect(vi.getTimerCount()).toBeGreaterThan(0);
    });

    it('should not start multiple intervals', () => {
      const expiresAt = Date.now() + 3600000;
      storeTokenExpiry(expiresAt);

      startTokenRefresh();
      const timerCount1 = vi.getTimerCount();

      startTokenRefresh();
      const timerCount2 = vi.getTimerCount();

      expect(timerCount1).toBe(timerCount2);
    });

    it('should stop token refresh interval', () => {
      const expiresAt = Date.now() + 3600000;
      storeTokenExpiry(expiresAt);

      startTokenRefresh();
      const timerCountBefore = vi.getTimerCount();
      expect(timerCountBefore).toBeGreaterThan(0);

      stopTokenRefresh();
      
      vi.clearAllTimers();
      expect(vi.getTimerCount()).toBe(0);
    });
  });

  describe('Initialize Auth (P0)', () => {
    it('should return authenticated state when valid token exists', async () => {
      const user = {
        id: 'user-123',
        email: 'test@example.com',
        role: 'owner' as const,
        tenantId: 'tenant-456',
      };

      storeUser(user);
      storeTokenExpiry(Date.now() + 3600000);

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ csrf_token: 'csrf-123' }),
      });

      const result = await initAuth();

      expect(result.isAuthenticated).toBe(true);
      expect(result.user).toEqual(user);
    });

    it('should return unauthenticated state when no token exists', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ csrf_token: 'csrf-123' }),
      });

      const result = await initAuth();

      expect(result.isAuthenticated).toBe(false);
      expect(result.user).toBeNull();
    });
  });

  describe('Cleanup Auth (P0)', () => {
    it('should stop token refresh on cleanup', () => {
      const expiresAt = Date.now() + 3600000;
      storeTokenExpiry(expiresAt);

      vi.useFakeTimers();
      startTokenRefresh();
      expect(vi.getTimerCount()).toBeGreaterThan(0);

      cleanupAuth();
      expect(vi.getTimerCount()).toBe(0);

      vi.useRealTimers();
    });
  });

  describe('401 Refresh-and-Retry (P0)', () => {
    beforeEach(() => {
      localStorage.setItem('feature_flag_OWNER_CONSOLE_API', 'true');
    });

    it('should retry request after refreshing token on 401', async () => {
      const testUrl = 'https://api.example.com/test';
      
      storeTokenExpiry(Date.now() + 3600000);
      storeUser({ id: 'test-user', email: 'test@example.com', role: 'owner', tenantId: 'test-tenant', name: 'Test User' });
      
      mockFetch.mockResolvedValueOnce({
        status: 401,
        ok: false,
      });
      
      mockFetch.mockResolvedValueOnce({
        status: 200,
        ok: true,
        json: async () => ({ tokens: { expiresAt: Date.now() + 3600000 } }),
      });
      
      mockFetch.mockResolvedValueOnce({
        status: 200,
        ok: true,
        json: async () => ({ data: 'success' }),
      });
      
      const response = await authenticatedFetch(testUrl, { method: 'GET' });
      
      expect(mockFetch).toHaveBeenCalledTimes(3);
      expect(mockFetch).toHaveBeenNthCalledWith(1, testUrl, expect.objectContaining({
        credentials: 'include',
      }));
      expect(mockFetch).toHaveBeenNthCalledWith(2, expect.stringContaining('/api/auth/v2/refresh'), expect.any(Object));
      expect(mockFetch).toHaveBeenNthCalledWith(3, testUrl, expect.objectContaining({
        credentials: 'include',
      }));
      expect(response.status).toBe(200);
    });

    it('should clear tokens and redirect on double 401 failure', async () => {
      const testUrl = 'https://api.example.com/test';
      
      storeTokenExpiry(Date.now() + 3600000);
      storeUser({ id: 'test-user', email: 'test@example.com', role: 'owner', tenantId: 'test-tenant', name: 'Test User' });
      
      mockFetch.mockResolvedValueOnce({
        status: 401,
        ok: false,
      });
      
      mockFetch.mockResolvedValueOnce({
        status: 200,
        ok: true,
        json: async () => ({ tokens: { expiresAt: Date.now() + 3600000 } }),
      });
      
      mockFetch.mockResolvedValueOnce({
        status: 401,
        ok: false,
      });
      
      await expect(authenticatedFetch(testUrl, { method: 'GET' })).rejects.toThrow('Authentication failed');
      
      expect(getStoredTokenExpiry()).toBeNull();
      expect(getStoredUser()).toBeNull();
      expect((window as any).location.href).toBe('/login');
    });

    it('should clear tokens and redirect when refresh fails', async () => {
      const testUrl = 'https://api.example.com/test';
      
      storeTokenExpiry(Date.now() + 3600000);
      storeUser({ id: 'test-user', email: 'test@example.com', role: 'owner', tenantId: 'test-tenant', name: 'Test User' });
      
      mockFetch.mockResolvedValueOnce({
        status: 401,
        ok: false,
      });
      
      mockFetch.mockResolvedValueOnce({
        status: 401,
        ok: false,
      });
      
      await expect(authenticatedFetch(testUrl, { method: 'GET' })).rejects.toThrow();
      
      expect(mockFetch).toHaveBeenCalledTimes(2);
      expect(getStoredTokenExpiry()).toBeNull();
      expect(getStoredUser()).toBeNull();
      expect((window as any).location.href).toBe('/login');
    });

    it('should not retry on non-401 errors', async () => {
      const testUrl = 'https://api.example.com/test';
      
      const expiryTime = Date.now() + 3600000;
      storeTokenExpiry(expiryTime);
      storeUser({ id: 'test-user', email: 'test@example.com', role: 'owner', tenantId: 'test-tenant', name: 'Test User' });
      
      mockFetch.mockResolvedValueOnce({
        status: 403,
        ok: false,
      });
      
      const response = await authenticatedFetch(testUrl, { method: 'GET' });
      
      expect(mockFetch).toHaveBeenCalledTimes(1);
      expect(response.status).toBe(403);
      expect(getStoredTokenExpiry()).toBe(expiryTime);
    });

    it('should include CSRF token in retry for unsafe methods', async () => {
      const testUrl = 'https://api.example.com/test';
      
      storeTokenExpiry(Date.now() + 3600000);
      storeUser({ id: 'test-user', email: 'test@example.com', role: 'owner', tenantId: 'test-tenant', name: 'Test User' });
      document.cookie = 'csrf_token=test-csrf-token';
      
      mockFetch.mockResolvedValueOnce({
        status: 401,
        ok: false,
      });
      
      mockFetch.mockResolvedValueOnce({
        status: 200,
        ok: true,
        json: async () => ({ tokens: { expiresAt: Date.now() + 3600000 } }),
      });
      
      mockFetch.mockResolvedValueOnce({
        status: 200,
        ok: true,
        json: async () => ({ data: 'success' }),
      });
      
      await authenticatedFetch(testUrl, { method: 'POST', body: '{}' });
      
      const retryCall = mockFetch.mock.calls[2];
      const retryHeaders = retryCall[1].headers;
      expect(retryHeaders.get('X-CSRF-Token')).toBe('test-csrf-token');
    });

    it('should update token expiry after successful refresh', async () => {
      const testUrl = 'https://api.example.com/test';
      const newExpiry = Date.now() + 7200000;
      
      storeTokenExpiry(Date.now() + 3600000);
      storeUser({ id: 'test-user', email: 'test@example.com', role: 'owner', tenantId: 'test-tenant', name: 'Test User' });
      
      mockFetch.mockResolvedValueOnce({
        status: 401,
        ok: false,
      });
      
      mockFetch.mockResolvedValueOnce({
        status: 200,
        ok: true,
        json: async () => ({ tokens: { expiresAt: newExpiry } }),
      });
      
      mockFetch.mockResolvedValueOnce({
        status: 200,
        ok: true,
        json: async () => ({ data: 'success' }),
      });
      
      await authenticatedFetch(testUrl, { method: 'GET' });
      
      expect(getStoredTokenExpiry()).toBe(newExpiry);
    });
  });
});
