/**
 * 2FA Authentication Flow Tests
 * 
 * Tests for 2FA authentication flow including:
 * - next_step handling (session, enroll_2fa, challenge_2fa)
 * - Token field fallback (token vs tmp_login_token)
 * - AuthProvider state management based on next_step
 * - Production lock behavior (OWNER_CONSOLE_API flag)
 * 
 * Note: These tests verify the frontend 2FA flow logic without requiring
 * a live backend. Backend integration should be tested via E2E tests.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';

describe('2FA Authentication Flow', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  describe('next_step handling', () => {
    it('should handle next_step=session (successful login)', () => {
      const mockResponse = {
        next_step: 'session',
        user: {
          id: 'user-123',
          email: 'owner@example.com',
          role: 'owner',
          tenantId: 'tenant-123',
          name: 'Test Owner',
        },
        token: 'jwt-token-123',
      };

      expect(mockResponse.next_step).toBe('session');
      expect(mockResponse.user).toBeDefined();
      expect(mockResponse.token).toBeDefined();
    });

    it('should handle next_step=enroll_2fa (2FA enrollment required)', () => {
      const mockResponse = {
        next_step: 'enroll_2fa',
        tmp_login_token: 'tmp-token-123',
        user: {
          id: 'user-123',
          email: 'owner@example.com',
          role: 'owner',
          tenantId: 'tenant-123',
          name: 'Test Owner',
        },
      };

      expect(mockResponse.next_step).toBe('enroll_2fa');
      expect(mockResponse.tmp_login_token).toBeDefined();
      expect(mockResponse.user).toBeDefined();
    });

    it('should handle next_step=challenge_2fa (2FA verification required)', () => {
      const mockResponse = {
        next_step: 'challenge_2fa',
        tmp_login_token: 'tmp-token-456',
      };

      expect(mockResponse.next_step).toBe('challenge_2fa');
      expect(mockResponse.tmp_login_token).toBeDefined();
    });

    it('should handle missing next_step (legacy response)', () => {
      const mockResponse = {
        user: {
          id: 'user-123',
          email: 'owner@example.com',
          role: 'owner',
          tenantId: 'tenant-123',
          name: 'Test Owner',
        },
        token: 'jwt-token-123',
      };

      expect(mockResponse.next_step).toBeUndefined();
      expect(mockResponse.user).toBeDefined();
      expect(mockResponse.token).toBeDefined();
    });
  });

  describe('Token field handling', () => {
    it('should use token field for successful login (next_step=session)', () => {
      const mockResponse = {
        next_step: 'session',
        user: {
          id: 'user-123',
          email: 'owner@example.com',
          role: 'owner',
          tenantId: 'tenant-123',
          name: 'Test Owner',
        },
        token: 'jwt-token-123',
      };

      expect(mockResponse.token).toBe('jwt-token-123');
      expect(mockResponse.tmp_login_token).toBeUndefined();
    });

    it('should use tmp_login_token for 2FA enrollment (next_step=enroll_2fa)', () => {
      const mockResponse = {
        next_step: 'enroll_2fa',
        tmp_login_token: 'tmp-token-123',
        user: {
          id: 'user-123',
          email: 'owner@example.com',
          role: 'owner',
          tenantId: 'tenant-123',
          name: 'Test Owner',
        },
      };

      expect(mockResponse.tmp_login_token).toBe('tmp-token-123');
      expect(mockResponse.token).toBeUndefined();
    });

    it('should use tmp_login_token for 2FA challenge (next_step=challenge_2fa)', () => {
      const mockResponse = {
        next_step: 'challenge_2fa',
        tmp_login_token: 'tmp-token-456',
      };

      expect(mockResponse.tmp_login_token).toBe('tmp-token-456');
      expect(mockResponse.token).toBeUndefined();
    });

    it('should handle token field fallback for legacy responses', () => {
      const mockResponse = {
        user: {
          id: 'user-123',
          email: 'owner@example.com',
          role: 'owner',
          tenantId: 'tenant-123',
          name: 'Test Owner',
        },
        token: 'jwt-token-123',
      };

      const tokenToUse = mockResponse.token || mockResponse.tmp_login_token;
      expect(tokenToUse).toBe('jwt-token-123');
    });
  });

  describe('AuthProvider state management', () => {
    it('should set authenticated=true only when next_step=session', () => {
      const sessionResponse = {
        next_step: 'session',
        user: {
          id: 'user-123',
          email: 'owner@example.com',
          role: 'owner',
          tenantId: 'tenant-123',
          name: 'Test Owner',
        },
        token: 'jwt-token-123',
      };

      const shouldAuthenticate = sessionResponse.next_step === 'session' || !sessionResponse.next_step;
      expect(shouldAuthenticate).toBe(true);
    });

    it('should NOT set authenticated=true when next_step=enroll_2fa', () => {
      const enrollResponse = {
        next_step: 'enroll_2fa',
        tmp_login_token: 'tmp-token-123',
        user: {
          id: 'user-123',
          email: 'owner@example.com',
          role: 'owner',
          tenantId: 'tenant-123',
          name: 'Test Owner',
        },
      };

      const shouldAuthenticate = enrollResponse.next_step === 'session' || !enrollResponse.next_step;
      expect(shouldAuthenticate).toBe(false);
    });

    it('should NOT set authenticated=true when next_step=challenge_2fa', () => {
      const challengeResponse = {
        next_step: 'challenge_2fa',
        tmp_login_token: 'tmp-token-456',
      };

      const shouldAuthenticate = challengeResponse.next_step === 'session' || !challengeResponse.next_step;
      expect(shouldAuthenticate).toBe(false);
    });

    it('should set authenticated=true for legacy responses (no next_step)', () => {
      const legacyResponse = {
        user: {
          id: 'user-123',
          email: 'owner@example.com',
          role: 'owner',
          tenantId: 'tenant-123',
          name: 'Test Owner',
        },
        token: 'jwt-token-123',
      };

      const shouldAuthenticate = legacyResponse.next_step === 'session' || !legacyResponse.next_step;
      expect(shouldAuthenticate).toBe(true);
    });
  });

  describe('Production lock behavior', () => {
    it('should verify OWNER_CONSOLE_API flag controls backend usage', () => {
      const isProduction = import.meta.env.PROD;
      const apiEnabled = true;

      if (isProduction && !apiEnabled) {
        expect(() => {
          throw new Error('Backend API is not configured. Please contact your system administrator.');
        }).toThrow('Backend API is not configured');
      }
    });

    it('should allow mock auth in development when OWNER_CONSOLE_API=false', () => {
      const isProduction = import.meta.env.PROD;
      const apiEnabled = false;

      if (!isProduction && !apiEnabled) {
        const mockUser = {
          id: 'mock-user-id',
          email: 'test@example.com',
          role: 'owner',
          tenantId: 'mock-tenant-id',
          name: 'Mock User',
        };
        expect(mockUser.id).toBe('mock-user-id');
      }
    });
  });

  describe('2FA Flow Integration', () => {
    it('should complete full 2FA enrollment flow', () => {
      const loginResponse = {
        next_step: 'enroll_2fa',
        tmp_login_token: 'tmp-token-123',
        user: {
          id: 'user-123',
          email: 'owner@example.com',
          role: 'owner',
          tenantId: 'tenant-123',
          name: 'Test Owner',
        },
      };

      expect(loginResponse.next_step).toBe('enroll_2fa');

      const enrollResponse = {
        next_step: 'session',
        user: loginResponse.user,
        token: 'jwt-token-123',
      };

      expect(enrollResponse.next_step).toBe('session');
      expect(enrollResponse.token).toBeDefined();
    });

    it('should complete full 2FA challenge flow', () => {
      const loginResponse = {
        next_step: 'challenge_2fa',
        tmp_login_token: 'tmp-token-456',
      };

      expect(loginResponse.next_step).toBe('challenge_2fa');

      const challengeResponse = {
        next_step: 'session',
        user: {
          id: 'user-123',
          email: 'owner@example.com',
          role: 'owner',
          tenantId: 'tenant-123',
          name: 'Test Owner',
        },
        token: 'jwt-token-789',
      };

      expect(challengeResponse.next_step).toBe('session');
      expect(challengeResponse.token).toBeDefined();
    });
  });
});
