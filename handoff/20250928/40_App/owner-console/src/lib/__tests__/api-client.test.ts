import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { apiClient, bootstrapCsrf } from '../api-client';

const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('apiClient', () => {
  const originalEnv = import.meta.env;

  beforeEach(() => {
    mockFetch.mockClear();
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
    vi.clearAllMocks();

    Object.defineProperty(import.meta, 'env', {
      value: originalEnv,
      writable: true,
      configurable: true,
    });
  });

  describe('Credentials Handling (P0)', () => {
    it('should always include credentials in requests', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ message: 'success' }),
      });

      await apiClient('/api/test', { method: 'GET' });

      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          credentials: 'include',
        })
      );
    });

    it('should include credentials for GET requests', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ data: 'test' }),
      });

      await apiClient('/api/data', { method: 'GET' });

      const callArgs = mockFetch.mock.calls[0][1];
      expect(callArgs.credentials).toBe('include');
    });

    it('should include credentials for POST requests', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 201,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ id: '123' }),
      });

      await apiClient('/api/create', { method: 'POST', body: JSON.stringify({ name: 'test' }) });

      const callArgs = mockFetch.mock.calls[0][1];
      expect(callArgs.credentials).toBe('include');
    });
  });

  describe('CSRF Token Injection (P0)', () => {
    it('should inject CSRF token for POST requests when token is in cookie', async () => {
      Object.defineProperty(document, 'cookie', {
        writable: true,
        value: 'csrf_token=test-csrf-token-123',
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 201,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ success: true }),
      });

      await apiClient('/api/create', { method: 'POST' });

      const callArgs = mockFetch.mock.calls[0][1];
      expect(callArgs.headers['X-CSRF-Token']).toBe('test-csrf-token-123');
    });

    it('should inject CSRF token for PUT requests', async () => {
      Object.defineProperty(document, 'cookie', {
        writable: true,
        value: 'csrf_token=put-token-456',
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ updated: true }),
      });

      await apiClient('/api/update', { method: 'PUT' });

      const callArgs = mockFetch.mock.calls[0][1];
      expect(callArgs.headers['X-CSRF-Token']).toBe('put-token-456');
    });

    it('should inject CSRF token for PATCH requests', async () => {
      Object.defineProperty(document, 'cookie', {
        writable: true,
        value: 'csrf_token=patch-token-789',
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ patched: true }),
      });

      await apiClient('/api/patch', { method: 'PATCH' });

      const callArgs = mockFetch.mock.calls[0][1];
      expect(callArgs.headers['X-CSRF-Token']).toBe('patch-token-789');
    });

    it('should inject CSRF token for DELETE requests', async () => {
      Object.defineProperty(document, 'cookie', {
        writable: true,
        value: 'csrf_token=delete-token-abc',
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 204,
        headers: new Headers({ 'content-type': 'text/plain' }),
        text: async () => '',
      });

      await apiClient('/api/delete', { method: 'DELETE' });

      const callArgs = mockFetch.mock.calls[0][1];
      expect(callArgs.headers['X-CSRF-Token']).toBe('delete-token-abc');
    });

    it('should NOT inject CSRF token for GET requests', async () => {
      Object.defineProperty(document, 'cookie', {
        writable: true,
        value: 'csrf_token=should-not-be-used',
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ data: 'test' }),
      });

      await apiClient('/api/data', { method: 'GET' });

      const callArgs = mockFetch.mock.calls[0][1];
      expect(callArgs.headers['X-CSRF-Token']).toBeUndefined();
    });

    it('should handle missing CSRF token gracefully for unsafe methods', async () => {
      Object.defineProperty(document, 'cookie', {
        writable: true,
        value: '',
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 201,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ success: true }),
      });

      await apiClient('/api/create', { method: 'POST' });

      const callArgs = mockFetch.mock.calls[0][1];
      expect(callArgs.headers['X-CSRF-Token']).toBeUndefined();
    });

    it('should parse CSRF token from cookie with multiple values', async () => {
      Object.defineProperty(document, 'cookie', {
        writable: true,
        value: 'session=abc123; csrf_token=correct-token; other=value',
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 201,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ success: true }),
      });

      await apiClient('/api/create', { method: 'POST' });

      const callArgs = mockFetch.mock.calls[0][1];
      expect(callArgs.headers['X-CSRF-Token']).toBe('correct-token');
    });
  });

  describe('Request Headers (P0)', () => {
    it('should set Content-Type to application/json by default', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ data: 'test' }),
      });

      await apiClient('/api/test', { method: 'GET' });

      const callArgs = mockFetch.mock.calls[0][1];
      expect(callArgs.headers['Content-Type']).toBe('application/json');
    });

    it('should allow custom headers to override defaults', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'text/plain' }),
        text: async () => 'plain text',
      });

      await apiClient('/api/test', {
        method: 'GET',
        headers: { 'Content-Type': 'text/plain' },
      });

      const callArgs = mockFetch.mock.calls[0][1];
      expect(callArgs.headers['Content-Type']).toBe('text/plain');
    });

    it('should merge custom headers with default headers', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ data: 'test' }),
      });

      await apiClient('/api/test', {
        method: 'GET',
        headers: { 'X-Custom-Header': 'custom-value' },
      });

      const callArgs = mockFetch.mock.calls[0][1];
      expect(callArgs.headers['Content-Type']).toBe('application/json');
      expect(callArgs.headers['X-Custom-Header']).toBe('custom-value');
    });
  });

  describe('Error Handling (P0)', () => {
    it('should throw error for 4xx responses', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        statusText: 'Bad Request',
        text: async () => 'Invalid input',
      });

      await expect(apiClient('/api/test', { method: 'POST' })).rejects.toThrow(
        'HTTP 400 Bad Request - Invalid input'
      );
    });

    it('should throw error for 401 Unauthorized', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        statusText: 'Unauthorized',
        text: async () => 'Not authenticated',
      });

      await expect(apiClient('/api/protected', { method: 'GET' })).rejects.toThrow(
        'HTTP 401 Unauthorized - Not authenticated'
      );
    });

    it('should throw error for 403 Forbidden', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 403,
        statusText: 'Forbidden',
        text: async () => 'Access denied',
      });

      await expect(apiClient('/api/admin', { method: 'GET' })).rejects.toThrow(
        'HTTP 403 Forbidden - Access denied'
      );
    });

    it('should throw error for 404 Not Found', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: 'Not Found',
        text: async () => 'Resource not found',
      });

      await expect(apiClient('/api/missing', { method: 'GET' })).rejects.toThrow(
        'HTTP 404 Not Found - Resource not found'
      );
    });

    it('should throw error for 5xx server errors', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        text: async () => 'Server error',
      });

      await expect(apiClient('/api/test', { method: 'GET' })).rejects.toThrow(
        'HTTP 500 Internal Server Error - Server error'
      );
    });

    it('should handle error when response text fails', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        text: async () => {
          throw new Error('Cannot read response');
        },
      });

      await expect(apiClient('/api/test', { method: 'GET' })).rejects.toThrow(
        'HTTP 500 Internal Server Error - '
      );
    });
  });

  describe('Response Handling (P0)', () => {
    it('should parse JSON responses correctly', async () => {
      const mockData = { id: '123', name: 'Test' };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => mockData,
      });

      const result = await apiClient<{ data: any; status: number }>('/api/test', { method: 'GET' });

      expect((result as any).data).toEqual(mockData);
      expect((result as any).status).toBe(200);
    });

    it('should parse text responses when content-type is not JSON', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'text/plain' }),
        text: async () => 'Plain text response',
      });

      const result = await apiClient<{ data: any }>('/api/test', { method: 'GET' });

      expect((result as any).data).toBe('Plain text response');
    });

    it('should include response status in result', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 201,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ created: true }),
      });

      const result = await apiClient<{ status: number }>('/api/create', { method: 'POST' });

      expect((result as any).status).toBe(201);
    });

    it('should include response headers in result', async () => {
      const headers = new Headers({
        'content-type': 'application/json',
        'x-custom-header': 'custom-value',
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers,
        json: async () => ({ data: 'test' }),
      });

      const result = await apiClient<{ headers: Headers }>('/api/test', { method: 'GET' });

      expect((result as any).headers).toBe(headers);
    });
  });

  describe('URL Construction (P0)', () => {
    it('should prepend API_BASE_URL to relative URLs', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ data: 'test' }),
      });

      await apiClient('/api/test', { method: 'GET' });

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/test'),
        expect.any(Object)
      );
    });
  });
});

describe('bootstrapCsrf', () => {
  beforeEach(() => {
    mockFetch.mockClear();
    vi.spyOn(console, 'debug').mockImplementation(() => {});
    vi.spyOn(console, 'warn').mockImplementation(() => {});
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should fetch CSRF token from /api/auth/v2/csrf endpoint', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      headers: { get: () => 'application/json' },
      json: async () => ({ csrf_token: 'bootstrap-token-123' }),
    });

    await bootstrapCsrf();

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/auth/v2/csrf'),
      expect.objectContaining({
        credentials: 'include',
      })
    );
  });

  it('should cache CSRF token from response body', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      headers: { get: () => 'application/json' },
      json: async () => ({ csrf_token: 'cached-token-456' }),
    });

    await bootstrapCsrf();

    expect(console.debug).toHaveBeenCalledWith('CSRF token cached from response body');
  });

  it('should handle failed CSRF bootstrap gracefully', async () => {
    mockFetch.mockRejectedValueOnce(new Error('Network error'));

    await bootstrapCsrf();

    expect(console.warn).toHaveBeenCalledWith(
      'Failed to bootstrap CSRF token:',
      expect.any(Error)
    );
  });

  it('should handle non-ok response gracefully', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      headers: { get: () => 'application/json' },
      text: async () => 'Server error',
    });

    await bootstrapCsrf();

    expect(console.error).toHaveBeenCalledWith(
      'CSRF bootstrap failed with status:',
      500
    );
  });

  it('should handle response without csrf_token field', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      headers: { get: () => 'application/json' },
      json: async () => ({ message: 'No token' }),
    });

    await bootstrapCsrf();

    expect(console.debug).toHaveBeenCalledWith(
      'Bootstrapping CSRF token from:',
      'http://test.local/api/auth/v2/csrf'
    );
  });
});

describe('Bootstrap CSRF Token Integration (P0)', () => {
  beforeEach(() => {
    mockFetch.mockClear();
    vi.clearAllMocks();
    document.cookie = '';
  });

  afterEach(() => {
    vi.resetModules();
  });

  it('should use cached CSRF token when cookies are unavailable (cross-origin)', async () => {
    const { bootstrapCsrf, apiClient } = await import('../api-client');
    
    document.cookie = '';
    
    mockFetch.mockResolvedValueOnce({
      ok: true,
      headers: { get: () => 'application/json' },
      json: async () => ({ csrf_token: 'CACHED_TOKEN_123' }),
    });
    
    await bootstrapCsrf();
    
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ data: 'success' }),
      headers: new Headers({ 'content-type': 'application/json' }),
    });
    
    await apiClient('/api/test', { method: 'POST', body: JSON.stringify({ test: true }) });
    
    const postCall = mockFetch.mock.calls[1];
    expect(postCall[1].headers['X-CSRF-Token']).toBe('CACHED_TOKEN_123');
  });

  it('should fallback to cookie when cache is empty', async () => {
    const { apiClient } = await import('../api-client');
    
    document.cookie = 'csrf_token=COOKIE_TOKEN_456';
    
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ data: 'success' }),
      headers: new Headers({ 'content-type': 'application/json' }),
    });
    
    await apiClient('/api/test', { method: 'DELETE' });
    
    const deleteCall = mockFetch.mock.calls[0];
    expect(deleteCall[1].headers['X-CSRF-Token']).toBe('COOKIE_TOKEN_456');
  });

  it('should not add CSRF header for safe methods even with cached token', async () => {
    const { bootstrapCsrf, apiClient } = await import('../api-client');
    
    mockFetch.mockResolvedValueOnce({
      ok: true,
      headers: { get: () => 'application/json' },
      json: async () => ({ csrf_token: 'CACHED_TOKEN_789' }),
    });
    
    await bootstrapCsrf();
    
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ data: 'success' }),
      headers: new Headers({ 'content-type': 'application/json' }),
    });
    
    await apiClient('/api/test', { method: 'GET' });
    
    const getCall = mockFetch.mock.calls[1];
    expect(getCall[1].headers['X-CSRF-Token']).toBeUndefined();
  });

  it('should prioritize cached token over cookie', async () => {
    const { bootstrapCsrf, apiClient } = await import('../api-client');
    
    document.cookie = 'csrf_token=COOKIE_TOKEN';
    
    mockFetch.mockResolvedValueOnce({
      ok: true,
      headers: { get: () => 'application/json' },
      json: async () => ({ csrf_token: 'CACHED_TOKEN_PRIORITY' }),
    });
    
    await bootstrapCsrf();
    
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ data: 'success' }),
      headers: new Headers({ 'content-type': 'application/json' }),
    });
    
    await apiClient('/api/test', { method: 'PUT', body: JSON.stringify({ test: true }) });
    
    const putCall = mockFetch.mock.calls[1];
    expect(putCall[1].headers['X-CSRF-Token']).toBe('CACHED_TOKEN_PRIORITY');
  });

  it('should persist cached token across multiple requests', async () => {
    const { bootstrapCsrf, apiClient } = await import('../api-client');
    
    document.cookie = '';
    
    mockFetch.mockResolvedValueOnce({
      ok: true,
      headers: { get: () => 'application/json' },
      json: async () => ({ csrf_token: 'PERSISTENT_TOKEN' }),
    });
    
    await bootstrapCsrf();
    
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ data: 'success1' }),
      headers: new Headers({ 'content-type': 'application/json' }),
    });
    
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ data: 'success2' }),
      headers: new Headers({ 'content-type': 'application/json' }),
    });
    
    await apiClient('/api/test1', { method: 'POST', body: '{}' });
    await apiClient('/api/test2', { method: 'PATCH', body: '{}' });
    
    const firstCall = mockFetch.mock.calls[1];
    const secondCall = mockFetch.mock.calls[2];
    
    expect(firstCall[1].headers['X-CSRF-Token']).toBe('PERSISTENT_TOKEN');
    expect(secondCall[1].headers['X-CSRF-Token']).toBe('PERSISTENT_TOKEN');
  });

  it('should handle missing CSRF token gracefully', async () => {
    const { apiClient } = await import('../api-client');
    
    document.cookie = '';
    
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ data: 'success' }),
      headers: new Headers({ 'content-type': 'application/json' }),
    });
    
    await apiClient('/api/test', { method: 'POST', body: '{}' });
    
    const postCall = mockFetch.mock.calls[0];
    expect(postCall[1].headers['X-CSRF-Token']).toBeUndefined();
  });
});
