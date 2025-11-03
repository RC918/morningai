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
  const result = await apiClient<{ data: TwoFAStatusResponse }>(
    '/api/auth/v2/totp/status',
    { method: 'GET' }
  );
  return (result as any).data || result;
}

/**
 * Setup TOTP for the authenticated user
 * Returns secret, QR code, and backup codes
 */
export async function setupTwoFA(
  request: TwoFASetupRequest
): Promise<TwoFASetupResponse> {
  const result = await apiClient<{ data: TwoFASetupResponse }>(
    '/api/auth/v2/totp/setup',
    {
      method: 'POST',
      body: JSON.stringify(request),
    }
  );
  return (result as any).data || result;
}

/**
 * Verify TOTP code and enable 2FA
 */
export async function verifyTwoFASetup(
  request: TwoFAVerifySetupRequest
): Promise<TwoFAVerifySetupResponse> {
  const result = await apiClient<{ data: TwoFAVerifySetupResponse }>(
    '/api/auth/v2/totp/verify-setup',
    {
      method: 'POST',
      body: JSON.stringify(request),
    }
  );
  return (result as any).data || result;
}

/**
 * Disable TOTP for the authenticated user
 * Requires password and current TOTP code
 */
export async function disableTwoFA(
  request: TwoFADisableRequest
): Promise<TwoFADisableResponse> {
  const result = await apiClient<{ data: TwoFADisableResponse }>(
    '/api/auth/v2/totp/disable',
    {
      method: 'POST',
      body: JSON.stringify(request),
    }
  );
  return (result as any).data || result;
}

/**
 * Regenerate backup codes
 * Requires password confirmation
 */
export async function regenerateBackupCodes(
  request: TwoFARegenerateBackupCodesRequest
): Promise<TwoFARegenerateBackupCodesResponse> {
  const result = await apiClient<{ data: TwoFARegenerateBackupCodesResponse }>(
    '/api/auth/v2/totp/backup-codes/regenerate',
    {
      method: 'POST',
      body: JSON.stringify(request),
    }
  );
  return (result as any).data || result;
}

/**
 * Verify 2FA code during login
 * This function will be used once the backend implements the verify-login endpoint
 */
export async function verifyTwoFALogin(request: {
  totp_code?: string
  backup_code?: string
  remember_device?: boolean
}): Promise<any> {
  return apiClient('/api/auth/v2/totp/verify-login', {
    method: 'POST',
    body: JSON.stringify(request),
  })
}
