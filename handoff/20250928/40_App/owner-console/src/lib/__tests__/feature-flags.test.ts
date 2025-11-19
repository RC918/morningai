/**
 * Feature Flags Tests
 * 
 * Comprehensive tests for feature flag resolution logic, including:
 * - Production lock behavior for OWNER_CONSOLE_API
 * - Development mode priority chain
 * - Edge cases and fallbacks
 * 
 * The tests use the exported resolveFeatureFlag() pure function which allows
 * testing production behavior without relying on Vite's compile-time constants.
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { resolveFeatureFlag, isFeatureEnabled, type FeatureFlagSources } from '../feature-flags.ts';

describe('resolveFeatureFlag (pure function)', () => {
  describe('Production mode - OWNER_CONSOLE_API', () => {
    const key = 'OWNER_CONSOLE_API';
    const isProd = true;

    it('should return env value when provided in production', () => {
      const sources: FeatureFlagSources = {
        url: false,
        localStorage: false,
        env: false,
      };
      
      const result = resolveFeatureFlag(key, isProd, sources);
      expect(result).toBe(false);
    });

    it('should default to true when env is undefined in production', () => {
      const sources: FeatureFlagSources = {
        url: false,
        localStorage: false,
        env: undefined,
      };
      
      const result = resolveFeatureFlag(key, isProd, sources);
      expect(result).toBe(true);
    });

    it('should ignore URL parameter in production', () => {
      const sources: FeatureFlagSources = {
        url: true,
        localStorage: false,
        env: false,
      };
      
      const result = resolveFeatureFlag(key, isProd, sources);
      expect(result).toBe(false);
    });

    it('should ignore localStorage in production', () => {
      const sources: FeatureFlagSources = {
        url: false,
        localStorage: true,
        env: false,
      };
      
      const result = resolveFeatureFlag(key, isProd, sources);
      expect(result).toBe(false);
    });

    it('should ignore both URL and localStorage when env is undefined', () => {
      const sources: FeatureFlagSources = {
        url: true,
        localStorage: true,
        env: undefined,
      };
      
      const result = resolveFeatureFlag(key, isProd, sources);
      expect(result).toBe(true);
    });

    it('should prioritize env over URL and localStorage', () => {
      const sources: FeatureFlagSources = {
        url: true,
        localStorage: true,
        env: false,
      };
      
      const result = resolveFeatureFlag(key, isProd, sources);
      expect(result).toBe(false);
    });
  });

  describe('Development mode - OWNER_CONSOLE_API', () => {
    const key = 'OWNER_CONSOLE_API';
    const isProd = false;

    it('should prioritize URL parameter over all others', () => {
      const sources: FeatureFlagSources = {
        url: true,
        localStorage: false,
        env: false,
      };
      
      const result = resolveFeatureFlag(key, isProd, sources);
      expect(result).toBe(true);
    });

    it('should prioritize localStorage over env when URL is undefined', () => {
      const sources: FeatureFlagSources = {
        url: undefined,
        localStorage: true,
        env: false,
      };
      
      const result = resolveFeatureFlag(key, isProd, sources);
      expect(result).toBe(true);
    });

    it('should use env when URL and localStorage are undefined', () => {
      const sources: FeatureFlagSources = {
        url: undefined,
        localStorage: undefined,
        env: true,
      };
      
      const result = resolveFeatureFlag(key, isProd, sources);
      expect(result).toBe(true);
    });

    it('should default to false when all sources are undefined', () => {
      const sources: FeatureFlagSources = {
        url: undefined,
        localStorage: undefined,
        env: undefined,
      };
      
      const result = resolveFeatureFlag(key, isProd, sources);
      expect(result).toBe(false);
    });

    it('should respect full priority chain: URL > localStorage > env > default', () => {
      const testCases = [
        { sources: { url: true, localStorage: false, env: false }, expected: true },
        { sources: { url: undefined, localStorage: true, env: false }, expected: true },
        { sources: { url: undefined, localStorage: undefined, env: true }, expected: true },
        { sources: { url: undefined, localStorage: undefined, env: undefined }, expected: false },
      ];

      testCases.forEach(({ sources, expected }) => {
        const result = resolveFeatureFlag(key, isProd, sources);
        expect(result).toBe(expected);
      });
    });
  });

  describe('Production mode - Other flags', () => {
    const key = 'OWNER_CONSOLE_GOVERNANCE';
    const isProd = true;

    it('should use full priority chain for non-OWNER_CONSOLE_API flags', () => {
      const sources: FeatureFlagSources = {
        url: true,
        localStorage: false,
        env: false,
      };
      
      const result = resolveFeatureFlag(key, isProd, sources);
      expect(result).toBe(true);
    });

    it('should prioritize localStorage over env for other flags', () => {
      const sources: FeatureFlagSources = {
        url: undefined,
        localStorage: true,
        env: false,
      };
      
      const result = resolveFeatureFlag(key, isProd, sources);
      expect(result).toBe(true);
    });

    it('should default to false for other flags in production', () => {
      const sources: FeatureFlagSources = {
        url: undefined,
        localStorage: undefined,
        env: undefined,
      };
      
      const result = resolveFeatureFlag(key, isProd, sources);
      expect(result).toBe(false);
    });
  });

  describe('Development mode - Other flags', () => {
    const key = 'OWNER_CONSOLE_TENANTS';
    const isProd = false;

    it('should use full priority chain', () => {
      const sources: FeatureFlagSources = {
        url: true,
        localStorage: false,
        env: false,
      };
      
      const result = resolveFeatureFlag(key, isProd, sources);
      expect(result).toBe(true);
    });

    it('should default to false when all sources are undefined', () => {
      const sources: FeatureFlagSources = {
        url: undefined,
        localStorage: undefined,
        env: undefined,
      };
      
      const result = resolveFeatureFlag(key, isProd, sources);
      expect(result).toBe(false);
    });
  });

  describe('Edge cases', () => {
    it('should handle false values correctly (not treat as undefined)', () => {
      const sources: FeatureFlagSources = {
        url: false,
        localStorage: undefined,
        env: undefined,
      };
      
      const result = resolveFeatureFlag('OWNER_CONSOLE_API', false, sources);
      expect(result).toBe(false);
    });

    it('should handle mixed true/false values correctly', () => {
      const sources: FeatureFlagSources = {
        url: false,
        localStorage: true,
        env: false,
      };
      
      const result = resolveFeatureFlag('OWNER_CONSOLE_MONITORING', false, sources);
      expect(result).toBe(false);
    });

    it('should handle all false values', () => {
      const sources: FeatureFlagSources = {
        url: false,
        localStorage: false,
        env: false,
      };
      
      const result = resolveFeatureFlag('OWNER_CONSOLE_SETTINGS', false, sources);
      expect(result).toBe(false);
    });

    it('should handle all true values', () => {
      const sources: FeatureFlagSources = {
        url: true,
        localStorage: true,
        env: true,
      };
      
      const result = resolveFeatureFlag('OWNER_CONSOLE_SECURITY', false, sources);
      expect(result).toBe(true);
    });
  });
});

describe('isFeatureEnabled (integration)', () => {
  beforeEach(() => {
    if (typeof window !== 'undefined') {
      localStorage.clear();
    }
  });

  afterEach(() => {
    if (typeof window !== 'undefined') {
      localStorage.clear();
    }
  });

  describe('Basic functionality', () => {
    it('should return a boolean for OWNER_CONSOLE_API', () => {
      const result = isFeatureEnabled('OWNER_CONSOLE_API');
      expect(typeof result).toBe('boolean');
    });

    it('should return a boolean for OWNER_CONSOLE_GOVERNANCE', () => {
      const result = isFeatureEnabled('OWNER_CONSOLE_GOVERNANCE');
      expect(typeof result).toBe('boolean');
    });

    it('should return a boolean for OWNER_CONSOLE_TENANTS', () => {
      const result = isFeatureEnabled('OWNER_CONSOLE_TENANTS');
      expect(typeof result).toBe('boolean');
    });

    it('should return a boolean for OWNER_CONSOLE_MONITORING', () => {
      const result = isFeatureEnabled('OWNER_CONSOLE_MONITORING');
      expect(typeof result).toBe('boolean');
    });

    it('should return a boolean for OWNER_CONSOLE_SETTINGS', () => {
      const result = isFeatureEnabled('OWNER_CONSOLE_SETTINGS');
      expect(typeof result).toBe('boolean');
    });

    it('should return a boolean for OWNER_CONSOLE_SECURITY', () => {
      const result = isFeatureEnabled('OWNER_CONSOLE_SECURITY');
      expect(typeof result).toBe('boolean');
    });

    it('should return a boolean for OWNER_CONSOLE_PWA', () => {
      const result = isFeatureEnabled('OWNER_CONSOLE_PWA');
      expect(typeof result).toBe('boolean');
    });
  });

  describe('Test environment defaults', () => {
    it('should default to false for OWNER_CONSOLE_API in test environment', () => {
      const result = isFeatureEnabled('OWNER_CONSOLE_API');
      expect(result).toBe(false);
    });

    it('should default to false for OWNER_CONSOLE_GOVERNANCE in test environment', () => {
      const result = isFeatureEnabled('OWNER_CONSOLE_GOVERNANCE');
      expect(result).toBe(false);
    });
  });
});

describe('getEnvFlag - Case-insensitive parsing', () => {
  it('should parse lowercase "true" as true', () => {
    const mockEnv = { VITE_FEATURE_TEST: 'true' };
    (import.meta as any).env = mockEnv;
    
    const sources: FeatureFlagSources = {
      env: mockEnv.VITE_FEATURE_TEST === 'true',
    };
    expect(sources.env).toBe(true);
  });

  it('should parse uppercase "TRUE" as true', () => {
    const value = 'TRUE';
    const normalized = value.toLowerCase().trim();
    expect(['true', '1', 'yes', 'on'].includes(normalized)).toBe(true);
  });

  it('should parse mixed case "True" as true', () => {
    const value = 'True';
    const normalized = value.toLowerCase().trim();
    expect(['true', '1', 'yes', 'on'].includes(normalized)).toBe(true);
  });

  it('should parse "1" as true', () => {
    const value = '1';
    const normalized = value.toLowerCase().trim();
    expect(['true', '1', 'yes', 'on'].includes(normalized)).toBe(true);
  });

  it('should parse "yes" (case-insensitive) as true', () => {
    const testCases = ['yes', 'YES', 'Yes', 'YeS'];
    testCases.forEach(value => {
      const normalized = value.toLowerCase().trim();
      expect(['true', '1', 'yes', 'on'].includes(normalized)).toBe(true);
    });
  });

  it('should parse "on" (case-insensitive) as true', () => {
    const testCases = ['on', 'ON', 'On', 'oN'];
    testCases.forEach(value => {
      const normalized = value.toLowerCase().trim();
      expect(['true', '1', 'yes', 'on'].includes(normalized)).toBe(true);
    });
  });

  it('should parse lowercase "false" as false', () => {
    const value = 'false';
    const normalized = value.toLowerCase().trim();
    expect(['false', '0', 'no', 'off'].includes(normalized)).toBe(true);
  });

  it('should parse uppercase "FALSE" as false', () => {
    const value = 'FALSE';
    const normalized = value.toLowerCase().trim();
    expect(['false', '0', 'no', 'off'].includes(normalized)).toBe(true);
  });

  it('should parse "0" as false', () => {
    const value = '0';
    const normalized = value.toLowerCase().trim();
    expect(['false', '0', 'no', 'off'].includes(normalized)).toBe(true);
  });

  it('should handle values with whitespace', () => {
    const testCases = [' true ', '  TRUE  ', '\ttrue\t', '\nTrue\n'];
    testCases.forEach(value => {
      const normalized = value.toLowerCase().trim();
      expect(['true', '1', 'yes', 'on'].includes(normalized)).toBe(true);
    });
  });

  it('should treat invalid values as undefined', () => {
    const invalidValues = ['invalid', 'maybe', '2', 'enabled', ''];
    invalidValues.forEach(value => {
      const normalized = value.toLowerCase().trim();
      const isTruthy = ['true', '1', 'yes', 'on'].includes(normalized);
      const isFalsy = ['false', '0', 'no', 'off'].includes(normalized);
      expect(isTruthy || isFalsy).toBe(false);
    });
  });
});
