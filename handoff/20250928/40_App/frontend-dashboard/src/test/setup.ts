import '@testing-library/jest-dom/vitest'
import { expect } from 'vitest'
import { axe, toHaveNoViolations } from 'jest-axe'

expect.extend(toHaveNoViolations)

export { axe }
