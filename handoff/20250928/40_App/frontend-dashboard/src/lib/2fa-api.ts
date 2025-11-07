/**
 * 2FA API Client
 * 
 * API client functions for Two-Factor Authentication endpoints
 * Uses the existing apiClient for consistent auth and CSRF handling
 */

import { apiClient } from './api-client';
import type {
  TwoFASetupRequest,
  TwoFASetupResponse,
  TwoFAVerifySetupRequest,
  TwoFAVerifySetupResponse,
  TwoFADisableRequest,
  TwoFADisableResponse,
  TwoFARegenerateBackupCodesRequest,
  TwoFARegenerateBackupCodesResponse,
  TwoFAStatusResponse,
  TwoFALoginRequest,
  TwoFALoginResponse,
  TwoFAChallengeRequest,
  TwoFAChallengeResponse,
  TwoFAEnrollResponse,
  TwoFAVerifyEnrollRequest,
  TwoFAVerifyEnrollResponse,
} from '../types/2fa';

/**
 * Get 2FA status for the authenticated user
 */
export async function getTwoFAStatus(): Promise<TwoFAStatusResponse> {
  return apiClient<TwoFAStatusResponse>('/api/auth/v2/totp/status', {
    method: 'GET',
  });
}

/**
 * Setup TOTP for the authenticated user
 * Returns secret, QR code, and backup codes
 */
export async function setupTwoFA(
  request: TwoFASetupRequest
): Promise<TwoFASetupResponse> {
  return apiClient<TwoFASetupResponse>('/api/auth/v2/totp/setup', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

/**
 * Verify TOTP code and enable 2FA
 */
export async function verifyTwoFASetup(
  request: TwoFAVerifySetupRequest
): Promise<TwoFAVerifySetupResponse> {
  return apiClient<TwoFAVerifySetupResponse>('/api/auth/v2/totp/verify-setup', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

/**
 * Disable TOTP for the authenticated user
 * Requires password and current TOTP code
 */
export async function disableTwoFA(
  request: TwoFADisableRequest
): Promise<TwoFADisableResponse> {
  return apiClient<TwoFADisableResponse>('/api/auth/v2/totp/disable', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

/**
 * Regenerate backup codes
 * Requires password confirmation
 */
export async function regenerateBackupCodes(
  request: TwoFARegenerateBackupCodesRequest
): Promise<TwoFARegenerateBackupCodesResponse> {
  return apiClient<TwoFARegenerateBackupCodesResponse>(
    '/api/auth/v2/totp/backup-codes/regenerate',
    {
      method: 'POST',
      body: JSON.stringify(request),
    }
  );
}

/**
 * Verify 2FA code during login (LEGACY - uses password re-transmission)
 * @deprecated Use challengeTwoFA instead with pre_auth_token
 */
export async function verifyTwoFALogin(
  request: TwoFALoginRequest
): Promise<TwoFALoginResponse> {
  return apiClient<TwoFALoginResponse>('/api/auth/v2/totp/verify-login', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

/**
 * Challenge 2FA code during login using pre-auth token
 * This is the recommended approach that doesn't require password re-transmission
 */
export async function challengeTwoFA(
  request: TwoFAChallengeRequest,
  preAuthToken: string
): Promise<TwoFAChallengeResponse> {
  return apiClient<TwoFAChallengeResponse>('/api/auth/v2/2fa/challenge', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${preAuthToken}`,
    },
    body: JSON.stringify(request),
  });
}

/**
 * Start 2FA enrollment using pre-auth token
 * Returns QR code and secret for the user to scan
 */
export async function enrollTwoFA(
  preAuthToken: string
): Promise<TwoFAEnrollResponse> {
  return apiClient<TwoFAEnrollResponse>('/api/auth/v2/2fa/enroll', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${preAuthToken}`,
    },
  });
}

/**
 * Complete 2FA enrollment by verifying the TOTP code
 * Returns backup codes and session tokens
 */
export async function verifyEnrollTwoFA(
  request: TwoFAVerifyEnrollRequest,
  preAuthToken: string
): Promise<TwoFAVerifyEnrollResponse> {
  return apiClient<TwoFAVerifyEnrollResponse>('/api/auth/v2/2fa/verify-enroll', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${preAuthToken}`,
    },
    body: JSON.stringify(request),
  });
}
