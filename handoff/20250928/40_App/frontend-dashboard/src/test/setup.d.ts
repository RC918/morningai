import type { AxeResults } from 'axe-core';

declare global {
  namespace Vi {
    interface Assertion<T = any> {
      /**
       * Custom matcher from jest-axe for accessibility testing
       * @see https://github.com/nickcolley/jest-axe
       */
      toHaveNoViolations(): T;
    }
    
    interface AsymmetricMatchersContaining {
      toHaveNoViolations(): any;
    }
  }
}

export {};
