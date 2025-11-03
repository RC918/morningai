/**
 * 2FA/TOTP Types
 * 
 * Type definitions for Two-Factor Authentication API responses and requests
 * Based on backend API in handoff/20250928/40_App/api-backend/src/routes/totp.py
 */

export interface TwoFASetupResponse {
  secret: string;
  qr_code: string;
  backup_codes: string[];
}

export interface TwoFAVerifySetupRequest {
  code: string;
}

export interface TwoFAVerifySetupResponse {
  success: boolean;
  enabled: boolean;
}

export interface TwoFADisableRequest {
  password: string;
  totp_code: string;
}

export interface TwoFADisableResponse {
  success: boolean;
  enabled: boolean;
}

export interface TwoFARegenerateBackupCodesRequest {
  password: string;
}

export interface TwoFARegenerateBackupCodesResponse {
  backup_codes: string[];
}

export interface TwoFAStatusResponse {
  enabled: boolean;
  verified_at: string | null;
  backup_codes_remaining: number;
}

export interface TwoFASetupRequest {
  password: string;
}

export interface TwoFALoginRequest {
  totp_code?: string;
  backup_code?: string;
  remember_device?: boolean;
}
