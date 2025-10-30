/// <reference types="vitest" />

declare module 'vitest' {
  interface Assertion<T = any> {
    /**
     * Custom matcher from jest-axe for accessibility testing
     * @see https://github.com/nickcolley/jest-axe
     */
    toHaveNoViolations(): void;
  }
  
  interface AsymmetricMatchersContaining {
    toHaveNoViolations(): void;
  }
}

export {};
