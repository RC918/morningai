import { describe, expect, test } from 'vitest'
import tokens from '@morningai/shared-ui/tokens.json'

describe('shared-ui tokens.json import', () => {
  test('tokens import resolves and has expected shape', () => {
    const typed: typeof tokens = tokens

    expect(tokens).toBeDefined()
    expect(tokens.color).toBeDefined()
    expect(tokens.color.background).toBeDefined()
    expect(tokens.color.background.base).toBeTypeOf('string')
    expect(tokens.font).toBeDefined()
    expect(tokens.space).toBeDefined()
  })

  test('tokens type annotation works correctly', () => {
    const colorBase: string = tokens.color.background.base
    expect(colorBase).toBeTypeOf('string')
  })
})
