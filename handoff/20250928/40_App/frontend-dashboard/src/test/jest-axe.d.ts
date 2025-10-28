import 'vitest'
import type { JestAxeConfigureOptions, AxeResults } from 'jest-axe'

declare module 'vitest' {
  interface Assertion<T = any> {
    /**
     * Assert that the given HTML element has no accessibility violations
     * @param options - Optional jest-axe configuration options
     */
    toHaveNoViolations(options?: JestAxeConfigureOptions): T
  }

  interface AsymmetricMatchersContaining {
    /**
     * Assert that the given HTML element has no accessibility violations
     * @param options - Optional jest-axe configuration options
     */
    toHaveNoViolations(options?: JestAxeConfigureOptions): any
  }
}
