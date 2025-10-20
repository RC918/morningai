import { vi } from 'vitest'

global.console = {
  ...console,
  warn: vi.fn(),
  error: vi.fn(),
}
