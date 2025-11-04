import { describe, it, expect, vi, beforeEach } from 'vitest';
import * as twoFAApi from '../2fa-api';
import * as apiClient from '../api-client';

vi.mock('../api-client', () => ({
  apiClient: vi.fn(),
}));

describe('2FA API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getTwoFAStatus', () => {
    it('should call apiClient with correct endpoint', async () => {
      const mockResponse = {
        enabled: true,
        verified_at: '2025-11-02T12:00:00Z',
        backup_codes_remaining: 7,
      };

      vi.mocked(apiClient.apiClient).mockResolvedValue(mockResponse);

      const result = await twoFAApi.getTwoFAStatus();

      expect(apiClient.apiClient).toHaveBeenCalledWith('/api/auth/v2/totp/status', {
        method: 'GET',
      });
      expect(result).toEqual(mockResponse);
    });

    it('should handle wrapped response format', async () => {
      const mockData = {
        enabled: true,
        verified_at: '2025-11-02T12:00:00Z',
        backup_codes_remaining: 7,
      };
      const mockResponse = { data: mockData };

      vi.mocked(apiClient.apiClient).mockResolvedValue(mockResponse);

      const result = await twoFAApi.getTwoFAStatus();

      expect(result).toEqual(mockData);
    });

    it('should handle errors', async () => {
      const mockError = new Error('Network error');
      vi.mocked(apiClient.apiClient).mockRejectedValue(mockError);

      await expect(twoFAApi.getTwoFAStatus()).rejects.toThrow('Network error');
    });
  });

  describe('setupTwoFA', () => {
    it('should call apiClient with password', async () => {
      const mockResponse = {
        secret: 'BASE32SECRET',
        qr_code: 'data:image/png;base64,...',
        backup_codes: ['CODE1', 'CODE2'],
      };

      vi.mocked(apiClient.apiClient).mockResolvedValue(mockResponse);

      const result = await twoFAApi.setupTwoFA({ password: 'test123' });

      expect(apiClient.apiClient).toHaveBeenCalledWith('/api/auth/v2/totp/setup', {
        method: 'POST',
        body: JSON.stringify({ password: 'test123' }),
      });
      expect(result).toEqual(mockResponse);
    });
  });

  describe('verifyTwoFASetup', () => {
    it('should call apiClient with TOTP code', async () => {
      const mockResponse = {
        success: true,
        enabled: true,
      };

      vi.mocked(apiClient.apiClient).mockResolvedValue(mockResponse);

      const result = await twoFAApi.verifyTwoFASetup({ code: '123456' });

      expect(apiClient.apiClient).toHaveBeenCalledWith('/api/auth/v2/totp/verify-setup', {
        method: 'POST',
        body: JSON.stringify({ code: '123456' }),
      });
      expect(result).toEqual(mockResponse);
    });
  });

  describe('disableTwoFA', () => {
    it('should call apiClient with password and TOTP code', async () => {
      const mockResponse = {
        success: true,
        enabled: false,
      };

      vi.mocked(apiClient.apiClient).mockResolvedValue(mockResponse);

      const result = await twoFAApi.disableTwoFA({
        password: 'test123',
        totp_code: '123456',
      });

      expect(apiClient.apiClient).toHaveBeenCalledWith('/api/auth/v2/totp/disable', {
        method: 'POST',
        body: JSON.stringify({ password: 'test123', totp_code: '123456' }),
      });
      expect(result).toEqual(mockResponse);
    });
  });

  describe('regenerateBackupCodes', () => {
    it('should call apiClient with password', async () => {
      const mockResponse = {
        backup_codes: ['NEW1', 'NEW2', 'NEW3'],
      };

      vi.mocked(apiClient.apiClient).mockResolvedValue(mockResponse);

      const result = await twoFAApi.regenerateBackupCodes({ password: 'test123' });

      expect(apiClient.apiClient).toHaveBeenCalledWith(
        '/api/auth/v2/totp/backup-codes/regenerate',
        {
          method: 'POST',
          body: JSON.stringify({ password: 'test123' }),
        }
      );
      expect(result).toEqual(mockResponse);
    });
  });
});
