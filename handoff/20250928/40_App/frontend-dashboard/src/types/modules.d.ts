
declare module 'jest-axe' {
  export interface AxeResults {
    violations: any[]
    passes: any[]
    incomplete: any[]
    inapplicable: any[]
  }
  
  export const axe: (element?: Element | Document | DocumentFragment) => Promise<AxeResults>
  
  type MatcherFn = (this: any, received: any, ...args: any[]) => any
  type MatchersObjectLite = Record<string, MatcherFn>
  export const toHaveNoViolations: MatchersObjectLite
  
  export const configureAxe: (options?: any) => typeof axe
}

declare module './tolgee' {
  const tolgee: any
  export default tolgee
}
