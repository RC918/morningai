import * as matchers from '@testing-library/jest-dom/matchers'
import { expect } from 'vitest'
import { axe, toHaveNoViolations } from 'jest-axe'

expect.extend(matchers)
expect.extend(toHaveNoViolations)

export { axe }
