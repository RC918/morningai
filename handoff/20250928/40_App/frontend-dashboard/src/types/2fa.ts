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
  feature_disabled?: boolean;
}

export interface TwoFASetupRequest {
  password: string;
}

export interface TwoFALoginRequest {
  email: string;
  password: string;
  totp_code?: string;
  backup_code?: string;
  remember_device?: boolean;
}

export interface TwoFAChallengeRequest {
  code?: string;
  backup_code?: string;
  remember_device?: boolean;
}

export interface TwoFAEnrollRequest {
}

export interface TwoFAEnrollResponse {
  secret: string;
  qr_code: string;
}

export interface TwoFAVerifyEnrollRequest {
  code: string;
}

export interface TwoFAVerifyEnrollResponse {
  success: boolean;
  backup_codes: string[];
  user: {
    id: string;
    email: string;
    name: string;
    role: string;
    tenantId: string;
    avatar?: string;
  };
  tokens: {
    expiresAt: number;
  };
}

export interface TwoFALoginResponse {
  success: boolean;
  user_id: string;
  backup_codes_remaining?: number;
  device_trusted?: boolean;
}

export interface TwoFAChallengeResponse {
  success: boolean;
  user: {
    id: string;
    email: string;
    name: string;
    role: string;
    tenantId: string;
    avatar?: string;
  };
  tokens: {
    expiresAt: number;
  };
  backup_codes_remaining?: number;
  device_trusted?: boolean;
}

export interface LoginResponse {
  success: boolean;
  user?: any;
  requires_2fa?: boolean;
  message?: string;
  next_step?: 'enroll_2fa' | 'challenge_2fa' | 'session';
  tmp_login_token?: string;
}
