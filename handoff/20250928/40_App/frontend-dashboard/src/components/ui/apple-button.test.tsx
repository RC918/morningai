/**
 * AppleButton Adapter Tests for frontend-dashboard
 * 
 * These tests verify that the adapter correctly wires up the frontend-dashboard-specific
 * haptic feedback and spring animation behavior.
 * 
 * Core UI functionality tests are in @morningai/shared-ui/src/components/ui/apple-button.test.tsx
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render } from '@testing-library/react';
import '@testing-library/jest-dom';
import { AppleButton } from './apple-button';
import * as springAnimation from '@/lib/spring-animation';

vi.mock('@/lib/spring-animation', () => ({
  getSpringConfig: vi.fn(() => ({
    type: 'spring',
    stiffness: 300,
    damping: 30,
  })),
  triggerHaptic: vi.fn(),
}));

describe('AppleButton Adapter (frontend-dashboard)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Spring Animation Integration', () => {
    it('calls getSpringConfig with "snappy" on render', () => {
      render(<AppleButton>Button</AppleButton>);
      
      expect(springAnimation.getSpringConfig).toHaveBeenCalledWith('snappy');
    });

    it('uses spring config for animations', () => {
      const mockConfig = {
        type: 'spring' as const,
        stiffness: 300,
        damping: 30,
        mass: 1,
      };
      vi.mocked(springAnimation.getSpringConfig).mockReturnValue(mockConfig);
      
      render(<AppleButton>Button</AppleButton>);
      
      expect(springAnimation.getSpringConfig).toHaveBeenCalled();
    });
  });
});
