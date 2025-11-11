import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import type { SpyInstance } from 'vitest';
import { sanitizeRedirect } from '../redirect-security';

describe('sanitizeRedirect', () => {
  let consoleWarnSpy: SpyInstance;

  beforeEach(() => {
    consoleWarnSpy = vi.spyOn(console, 'warn');
    consoleWarnSpy.mockImplementation(() => {});
  });

  afterEach(() => {
    consoleWarnSpy.mockRestore();
  });

  describe('Valid relative paths', () => {
    it('should allow valid relative paths', () => {
      expect(sanitizeRedirect('/settings/2fa')).toBe('/settings/2fa');
      expect(sanitizeRedirect('/dashboard')).toBe('/dashboard');
      expect(sanitizeRedirect('/')).toBe('/');
      expect(sanitizeRedirect('/users/123')).toBe('/users/123');
    });

    it('should allow paths with query parameters', () => {
      expect(sanitizeRedirect('/settings?tab=security')).toBe('/settings?tab=security');
      expect(sanitizeRedirect('/dashboard?view=overview')).toBe('/dashboard?view=overview');
    });

    it('should allow paths with hash fragments', () => {
      expect(sanitizeRedirect('/settings#security')).toBe('/settings#security');
      expect(sanitizeRedirect('/dashboard#top')).toBe('/dashboard#top');
    });

    it('should handle paths with whitespace', () => {
      expect(sanitizeRedirect('  /settings/2fa  ')).toBe('/settings/2fa');
      expect(sanitizeRedirect('\n/dashboard\n')).toBe('/dashboard');
    });
  });

  describe('Absolute URLs (should be rejected)', () => {
    it('should reject http URLs', () => {
      expect(sanitizeRedirect('http://evil.com')).toBe('/');
      expect(consoleWarnSpy).toHaveBeenCalledWith(
        '[Security] Rejected non-relative redirect:',
        'http://evil.com'
      );
    });

    it('should reject https URLs', () => {
      expect(sanitizeRedirect('https://evil.com')).toBe('/');
      expect(consoleWarnSpy).toHaveBeenCalledWith(
        '[Security] Rejected non-relative redirect:',
        'https://evil.com'
      );
    });

    it('should reject URLs with paths', () => {
      expect(sanitizeRedirect('https://evil.com/path')).toBe('/');
      expect(sanitizeRedirect('http://evil.com/settings')).toBe('/');
    });
  });

  describe('Protocol-relative URLs (should be rejected)', () => {
    it('should reject protocol-relative URLs', () => {
      expect(sanitizeRedirect('//evil.com')).toBe('/');
      expect(consoleWarnSpy).toHaveBeenCalledWith(
        '[Security] Rejected protocol-relative redirect:',
        '//evil.com'
      );
    });

    it('should reject protocol-relative URLs with paths', () => {
      expect(sanitizeRedirect('//evil.com/path')).toBe('/');
      expect(consoleWarnSpy).toHaveBeenCalledWith(
        '[Security] Rejected protocol-relative redirect:',
        '//evil.com/path'
      );
    });
  });

  describe('Dangerous protocols (should be rejected)', () => {
    it('should reject javascript: protocol', () => {
      expect(sanitizeRedirect('javascript:alert(1)')).toBe('/');
      expect(consoleWarnSpy).toHaveBeenCalledWith(
        '[Security] Rejected dangerous protocol redirect:',
        'javascript:alert(1)'
      );
    });

    it('should reject javascript: protocol with different casing', () => {
      expect(sanitizeRedirect('JavaScript:alert(1)')).toBe('/');
      expect(sanitizeRedirect('JAVASCRIPT:alert(1)')).toBe('/');
    });

    it('should reject data: protocol', () => {
      expect(sanitizeRedirect('data:text/html,<script>alert(1)</script>')).toBe('/');
      expect(consoleWarnSpy).toHaveBeenCalledWith(
        '[Security] Rejected dangerous protocol redirect:',
        'data:text/html,<script>alert(1)</script>'
      );
    });

    it('should reject data: protocol with different casing', () => {
      expect(sanitizeRedirect('Data:text/html,test')).toBe('/');
      expect(sanitizeRedirect('DATA:text/html,test')).toBe('/');
    });
  });

  describe('Null and undefined inputs', () => {
    it('should handle null', () => {
      expect(sanitizeRedirect(null)).toBe('/');
    });

    it('should handle undefined', () => {
      expect(sanitizeRedirect(undefined)).toBe('/');
    });

    it('should handle empty string', () => {
      expect(sanitizeRedirect('')).toBe('/');
    });

    it('should handle whitespace-only string', () => {
      expect(sanitizeRedirect('   ')).toBe('/');
    });
  });

  describe('Edge cases', () => {
    it('should handle non-string inputs', () => {
      // @ts-expect-error Testing runtime behavior with invalid input
      expect(sanitizeRedirect(123)).toBe('/');
      // @ts-expect-error Testing runtime behavior with invalid input
      expect(sanitizeRedirect({})).toBe('/');
      // @ts-expect-error Testing runtime behavior with invalid input
      expect(sanitizeRedirect([])).toBe('/');
    });

    it('should reject relative paths not starting with /', () => {
      expect(sanitizeRedirect('settings/2fa')).toBe('/');
      expect(sanitizeRedirect('dashboard')).toBe('/');
    });

    it('should handle URLs with encoded characters', () => {
      expect(sanitizeRedirect('/settings%2F2fa')).toBe('/settings%2F2fa');
      expect(sanitizeRedirect('/user%20profile')).toBe('/user%20profile');
    });

    it('should handle very long paths', () => {
      const longPath = '/settings/' + 'a'.repeat(1000);
      expect(sanitizeRedirect(longPath)).toBe(longPath);
    });
  });
});
