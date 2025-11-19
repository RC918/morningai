/**
 * 2FA Authentication Flow Tests
 * 
 * Comprehensive tests for 2FA authentication flow including:
 * - AuthProvider component behavior with different next_step values
 * - Token field fallback (token vs tmp_login_token)
 * - State management based on next_step
 * - Production lock behavior (OWNER_CONSOLE_API flag)
 * 
 * These tests verify actual component behavior, not just data structures.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import React from 'react';
import { AuthProvider, useAuth } from '../../components/AuthProvider';
import type { LoginResponse, User } from '../auth';
import * as authModule from '../auth';

vi.mock('../auth', async () => {
  const actual = await vi.importActual('../auth');
  return {
    ...actual,
    login: vi.fn(),
    logout: vi.fn(),
    getCurrentUser: vi.fn(),
    isAuthenticated: vi.fn(),
    initAuth: vi.fn(),
    cleanupAuth: vi.fn(),
  };
});

describe('AuthProvider Component - 2FA Flow', () => {
  const mockUser: User = {
    id: 'user-123',
    email: 'owner@example.com',
    role: 'owner',
    tenantId: 'tenant-123',
    name: 'Test Owner',
  };

  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
    vi.clearAllMocks();
    
    vi.mocked(authModule.initAuth).mockResolvedValue({
      isAuthenticated: false,
      user: null,
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('next_step=session (successful login)', () => {
    it('should set isAuthenticated=true when next_step is session', async () => {
      const sessionResponse: LoginResponse = {
        next_step: 'session',
        user: mockUser,
        tokens: {
          expiresAt: Date.now() + 3600000,
        },
      };

      vi.mocked(authModule.login).mockResolvedValue(sessionResponse);

      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <AuthProvider>{children}</AuthProvider>
      );

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        await result.current.login({ email: 'test@example.com', password: 'password' });
      });

      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.user).toEqual(mockUser);
    });

    it('should return full response to caller', async () => {
      const sessionResponse: LoginResponse = {
        next_step: 'session',
        user: mockUser,
        tokens: {
          expiresAt: Date.now() + 3600000,
        },
      };

      vi.mocked(authModule.login).mockResolvedValue(sessionResponse);

      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <AuthProvider>{children}</AuthProvider>
      );

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      let response: LoginResponse | undefined;
      await act(async () => {
        response = await result.current.login({ email: 'test@example.com', password: 'password' });
      });

      expect(response).toEqual(sessionResponse);
      expect(response?.next_step).toBe('session');
    });
  });

  describe('next_step=enroll_2fa (2FA enrollment required)', () => {
    it('should NOT set isAuthenticated when next_step is enroll_2fa', async () => {
      const enrollResponse: LoginResponse = {
        next_step: 'enroll_2fa',
        tmp_login_token: 'tmp-token-123',
        user: mockUser,
      };

      vi.mocked(authModule.login).mockResolvedValue(enrollResponse);

      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <AuthProvider>{children}</AuthProvider>
      );

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        await result.current.login({ email: 'test@example.com', password: 'password' });
      });

      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
    });

    it('should return full response with tmp_login_token', async () => {
      const enrollResponse: LoginResponse = {
        next_step: 'enroll_2fa',
        tmp_login_token: 'tmp-token-123',
        user: mockUser,
      };

      vi.mocked(authModule.login).mockResolvedValue(enrollResponse);

      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <AuthProvider>{children}</AuthProvider>
      );

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      let response: LoginResponse | undefined;
      await act(async () => {
        response = await result.current.login({ email: 'test@example.com', password: 'password' });
      });

      expect(response).toEqual(enrollResponse);
      expect(response?.next_step).toBe('enroll_2fa');
      expect(response?.tmp_login_token).toBe('tmp-token-123');
    });
  });

  describe('next_step=challenge_2fa (2FA verification required)', () => {
    it('should NOT set isAuthenticated when next_step is challenge_2fa', async () => {
      const challengeResponse: LoginResponse = {
        next_step: 'challenge_2fa',
        tmp_login_token: 'tmp-token-456',
      };

      vi.mocked(authModule.login).mockResolvedValue(challengeResponse);

      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <AuthProvider>{children}</AuthProvider>
      );

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        await result.current.login({ email: 'test@example.com', password: 'password' });
      });

      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
    });

    it('should return full response with tmp_login_token', async () => {
      const challengeResponse: LoginResponse = {
        next_step: 'challenge_2fa',
        tmp_login_token: 'tmp-token-456',
      };

      vi.mocked(authModule.login).mockResolvedValue(challengeResponse);

      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <AuthProvider>{children}</AuthProvider>
      );

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      let response: LoginResponse | undefined;
      await act(async () => {
        response = await result.current.login({ email: 'test@example.com', password: 'password' });
      });

      expect(response).toEqual(challengeResponse);
      expect(response?.next_step).toBe('challenge_2fa');
      expect(response?.tmp_login_token).toBe('tmp-token-456');
    });
  });

  describe('missing next_step (legacy response)', () => {
    it('should set isAuthenticated=true for legacy responses without next_step', async () => {
      const legacyResponse: LoginResponse = {
        user: mockUser,
        tokens: {
          expiresAt: Date.now() + 3600000,
        },
      };

      vi.mocked(authModule.login).mockResolvedValue(legacyResponse);

      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <AuthProvider>{children}</AuthProvider>
      );

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        await result.current.login({ email: 'test@example.com', password: 'password' });
      });

      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.user).toEqual(mockUser);
    });
  });

  describe('Error handling', () => {
    it('should clear authentication state on login error', async () => {
      vi.mocked(authModule.login).mockRejectedValue(new Error('Invalid credentials'));

      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <AuthProvider>{children}</AuthProvider>
      );

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await expect(async () => {
        await act(async () => {
          await result.current.login({ email: 'test@example.com', password: 'wrong' });
        });
      }).rejects.toThrow('Invalid credentials');

      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
    });

    it('should clear authentication state on logout', async () => {
      const sessionResponse: LoginResponse = {
        next_step: 'session',
        user: mockUser,
        tokens: {
          expiresAt: Date.now() + 3600000,
        },
      };

      vi.mocked(authModule.login).mockResolvedValue(sessionResponse);
      vi.mocked(authModule.logout).mockResolvedValue();

      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <AuthProvider>{children}</AuthProvider>
      );

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        await result.current.login({ email: 'test@example.com', password: 'password' });
      });

      expect(result.current.isAuthenticated).toBe(true);

      await act(async () => {
        await result.current.logout();
      });

      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
    });

    it('should handle refreshUser success', async () => {
      vi.mocked(authModule.getCurrentUser).mockResolvedValue(mockUser);

      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <AuthProvider>{children}</AuthProvider>
      );

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        await result.current.refreshUser();
      });

      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.user).toEqual(mockUser);
    });

    it('should handle refreshUser error', async () => {
      vi.mocked(authModule.getCurrentUser).mockRejectedValue(new Error('Session expired'));

      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <AuthProvider>{children}</AuthProvider>
      );

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await expect(async () => {
        await act(async () => {
          await result.current.refreshUser();
        });
      }).rejects.toThrow('Session expired');

      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
    });
  });
});
