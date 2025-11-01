import { describe, it, expect, beforeEach, vi } from 'vitest';
import {
  storeTokenExpiry,
  getStoredTokenExpiry,
  clearTokens,
  storeUser,
  getStoredUser,
  isTokenExpired,
  isAuthenticated,
} from '../auth';

describe('Auth Module', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
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
});
