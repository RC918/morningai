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
