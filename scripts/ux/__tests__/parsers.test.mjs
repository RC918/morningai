/**
 * Unit tests for UX metrics parsers
 * @vitest-environment node
 */

import { describe, it, expect } from 'vitest';
import {
  parseI18nCoverage,
  parseA11yViolations,
  parseMotionP95,
  parseVrtMismatch,
  evaluateThreshold
} from '../parsers.mjs';

describe('parseI18nCoverage', () => {
  it('should parse standard format "coverage: 96.2%"', () => {
    expect(parseI18nCoverage('coverage: 96.2%')).toBe(96.2);
  });

  it('should parse format without colon "Coverage 96%"', () => {
    expect(parseI18nCoverage('Coverage 96%')).toBe(96);
  });

  it('should parse format with dash "i18n coverage – 95.00 %"', () => {
    expect(parseI18nCoverage('i18n coverage – 95.00 %')).toBe(95.00);
  });

  it('should parse format with hyphen "coverage - 98.5%"', () => {
    expect(parseI18nCoverage('coverage - 98.5%')).toBe(98.5);
  });

  it('should be case insensitive', () => {
    expect(parseI18nCoverage('COVERAGE: 100%')).toBe(100);
    expect(parseI18nCoverage('Coverage: 95.5%')).toBe(95.5);
  });

  it('should handle extra whitespace', () => {
    expect(parseI18nCoverage('coverage:    96.2   %')).toBe(96.2);
  });

  it('should parse integer values', () => {
    expect(parseI18nCoverage('coverage: 100%')).toBe(100);
  });

  it('should parse decimal values', () => {
    expect(parseI18nCoverage('coverage: 96.25%')).toBe(96.25);
  });

  it('should return null for non-matching text', () => {
    expect(parseI18nCoverage('no coverage here')).toBeNull();
    expect(parseI18nCoverage('96.2%')).toBeNull();
  });

  it('should return null for null input', () => {
    expect(parseI18nCoverage(null)).toBeNull();
  });

  it('should return null for undefined input', () => {
    expect(parseI18nCoverage(undefined)).toBeNull();
  });

  it('should return null for non-string input', () => {
    expect(parseI18nCoverage(123)).toBeNull();
    expect(parseI18nCoverage({})).toBeNull();
  });

  it('should parse from multi-line text', () => {
    const text = `
      i18n Coverage Report
      coverage: 96.5%
      Total keys: 828
    `;
    expect(parseI18nCoverage(text)).toBe(96.5);
  });
});

describe('parseA11yViolations', () => {
  it('should parse standard format "critical: 0, serious: 2"', () => {
    expect(parseA11yViolations('critical: 0, serious: 2')).toEqual({
      critical: 0,
      serious: 2
    });
  });

  it('should parse format with "Issues" "Critical Issues: 1; Serious: 0"', () => {
    expect(parseA11yViolations('Critical Issues: 1; Serious: 0')).toEqual({
      critical: 1,
      serious: 0
    });
  });

  it('should parse multi-line format', () => {
    const text = `
      Critical 2
      Serious 1
    `;
    expect(parseA11yViolations(text)).toEqual({
      critical: 2,
      serious: 1
    });
  });

  it('should parse when only critical is present', () => {
    expect(parseA11yViolations('critical: 3')).toEqual({
      critical: 3,
      serious: 0
    });
  });

  it('should parse when only serious is present', () => {
    expect(parseA11yViolations('serious: 5')).toEqual({
      critical: 0,
      serious: 5
    });
  });

  it('should be case insensitive', () => {
    expect(parseA11yViolations('CRITICAL: 1, SERIOUS: 2')).toEqual({
      critical: 1,
      serious: 2
    });
  });

  it('should handle extra whitespace', () => {
    expect(parseA11yViolations('critical:    0  ,  serious:    2')).toEqual({
      critical: 0,
      serious: 2
    });
  });

  it('should return null for non-matching text', () => {
    expect(parseA11yViolations('no violations here')).toBeNull();
  });

  it('should return null for null input', () => {
    expect(parseA11yViolations(null)).toBeNull();
  });

  it('should return null for undefined input', () => {
    expect(parseA11yViolations(undefined)).toBeNull();
  });

  it('should parse from complex output', () => {
    const text = `
      Accessibility Audit Results
      Critical Issues: 0
      Serious Issues: 1
      Moderate: 3
      Minor: 5
    `;
    expect(parseA11yViolations(text)).toEqual({
      critical: 0,
      serious: 1
    });
  });
});

describe('parseMotionP95', () => {
  it('should parse standard format "p95: 16.5ms"', () => {
    expect(parseMotionP95('p95: 16.5ms')).toBe(16.5);
  });

  it('should parse format with equals "P95 = 17 ms"', () => {
    expect(parseMotionP95('P95 = 17 ms')).toBe(17);
  });

  it('should parse format without unit "p95 17"', () => {
    expect(parseMotionP95('p95 17')).toBe(17);
  });

  it('should parse format with "FrameTime" "p95FrameTime: 16.67"', () => {
    expect(parseMotionP95('p95FrameTime: 16.67')).toBe(16.67);
  });

  it('should parse format with spaces "p95 frame time: 15.5ms"', () => {
    expect(parseMotionP95('p95 frame time: 15.5ms')).toBe(15.5);
  });

  it('should be case insensitive', () => {
    expect(parseMotionP95('P95: 16.5MS')).toBe(16.5);
  });

  it('should handle extra whitespace', () => {
    expect(parseMotionP95('p95:    16.5   ms')).toBe(16.5);
  });

  it('should parse integer values', () => {
    expect(parseMotionP95('p95: 17ms')).toBe(17);
  });

  it('should parse decimal values', () => {
    expect(parseMotionP95('p95: 16.67ms')).toBe(16.67);
  });

  it('should return null for non-matching text', () => {
    expect(parseMotionP95('no p95 here')).toBeNull();
  });

  it('should return null for null input', () => {
    expect(parseMotionP95(null)).toBeNull();
  });

  it('should return null for undefined input', () => {
    expect(parseMotionP95(undefined)).toBeNull();
  });

  it('should parse from multi-line text', () => {
    const text = `
      Motion Performance Report
      p95: 16.5ms
      p99: 20.1ms
    `;
    expect(parseMotionP95(text)).toBe(16.5);
  });
});

describe('parseVrtMismatch', () => {
  it('should parse standard format "mismatch: 0.12%"', () => {
    expect(parseVrtMismatch('mismatch: 0.12%')).toBe(0.12);
  });

  it('should parse format with space "Mismatch 0.5 %"', () => {
    expect(parseVrtMismatch('Mismatch 0.5 %')).toBe(0.5);
  });

  it('should parse format with "visual" prefix "visual mismatch: 0.05%"', () => {
    expect(parseVrtMismatch('visual mismatch: 0.05%')).toBe(0.05);
  });

  it('should be case insensitive', () => {
    expect(parseVrtMismatch('MISMATCH: 0.12%')).toBe(0.12);
  });

  it('should handle extra whitespace', () => {
    expect(parseVrtMismatch('mismatch:    0.12   %')).toBe(0.12);
  });

  it('should parse integer values', () => {
    expect(parseVrtMismatch('mismatch: 1%')).toBe(1);
  });

  it('should parse decimal values', () => {
    expect(parseVrtMismatch('mismatch: 0.125%')).toBe(0.125);
  });

  it('should return null for non-matching text', () => {
    expect(parseVrtMismatch('no mismatch here')).toBeNull();
  });

  it('should return null for null input', () => {
    expect(parseVrtMismatch(null)).toBeNull();
  });

  it('should return null for undefined input', () => {
    expect(parseVrtMismatch(undefined)).toBeNull();
  });

  it('should parse from multi-line text', () => {
    const text = `
      Visual Regression Test Results
      mismatch: 0.12%
      Total screenshots: 50
    `;
    expect(parseVrtMismatch(text)).toBe(0.12);
  });
});

describe('evaluateThreshold', () => {
  describe('lte (less than or equal) comparison', () => {
    it('should return true when value is less than threshold', () => {
      expect(evaluateThreshold(5, 10, 'lte')).toBe(true);
    });

    it('should return true when value equals threshold', () => {
      expect(evaluateThreshold(10, 10, 'lte')).toBe(true);
    });

    it('should return false when value is greater than threshold', () => {
      expect(evaluateThreshold(15, 10, 'lte')).toBe(false);
    });

    it('should use lte as default comparison', () => {
      expect(evaluateThreshold(5, 10)).toBe(true);
      expect(evaluateThreshold(15, 10)).toBe(false);
    });
  });

  describe('gte (greater than or equal) comparison', () => {
    it('should return true when value is greater than threshold', () => {
      expect(evaluateThreshold(15, 10, 'gte')).toBe(true);
    });

    it('should return true when value equals threshold', () => {
      expect(evaluateThreshold(10, 10, 'gte')).toBe(true);
    });

    it('should return false when value is less than threshold', () => {
      expect(evaluateThreshold(5, 10, 'gte')).toBe(false);
    });
  });

  describe('edge cases', () => {
    it('should return false for null value', () => {
      expect(evaluateThreshold(null, 10, 'lte')).toBe(false);
    });

    it('should return false for undefined value', () => {
      expect(evaluateThreshold(undefined, 10, 'lte')).toBe(false);
    });

    it('should return false for null threshold', () => {
      expect(evaluateThreshold(5, null, 'lte')).toBe(false);
    });

    it('should return false for undefined threshold', () => {
      expect(evaluateThreshold(5, undefined, 'lte')).toBe(false);
    });

    it('should return false for invalid comparison', () => {
      expect(evaluateThreshold(5, 10, 'invalid')).toBe(false);
    });

    it('should handle decimal values', () => {
      expect(evaluateThreshold(16.5, 16.67, 'lte')).toBe(true);
      expect(evaluateThreshold(16.7, 16.67, 'lte')).toBe(false);
    });

    it('should handle zero values', () => {
      expect(evaluateThreshold(0, 0, 'lte')).toBe(true);
      expect(evaluateThreshold(0, 1, 'lte')).toBe(true);
      expect(evaluateThreshold(1, 0, 'lte')).toBe(false);
    });
  });
});
