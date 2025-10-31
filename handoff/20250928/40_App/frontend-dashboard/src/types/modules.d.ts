
declare module 'jest-axe' {
  import { RuleObject } from 'axe-core'
  
  export interface AxeResults {
    violations: RuleObject[]
    passes: RuleObject[]
    incomplete: RuleObject[]
    inapplicable: RuleObject[]
  }
  
  export function axe(element: Element | Document): Promise<AxeResults>
  export function toHaveNoViolations(results: AxeResults): void
  export const configureAxe: (options: any) => typeof axe
}
