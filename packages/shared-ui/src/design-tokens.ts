/**
 * Design Tokens Utility
 * Centralized design token access for all MorningAI applications
 * 
 * This module provides a unified interface to access design tokens
 * defined in tokens.json. It supports both direct token access and
 * CSS variable generation for runtime theming.
 * 
 * @packageDocumentation
 */

import tokens from './tokens.json'

/**
 * Type-safe token access using dot notation
 * @example
 * ```ts
 * const primaryColor = getToken('color.primary.500')
 * const spacing = getToken('space.md')
 * ```
 */
export const getToken = (path: string): any => {
  return path.split('.').reduce((obj: any, key: string) => obj?.[key], tokens)
}

/**
 * Color tokens organized by category
 */
export const colors = {
  primary: tokens.color.primary,
  accent: tokens.color.accent,
  semantic: tokens.color.semantic,
  neutral: tokens.color.neutral,
  background: tokens.color.background
} as const

/**
 * Typography tokens including font family, size, weight, and line height
 */
export const typography = {
  family: tokens.font.family,
  size: tokens.font.size,
  weight: tokens.font.weight,
  lineHeight: tokens.font.lineHeight
}

/**
 * Spacing tokens for consistent layout
 */
export const spacing = tokens.space

/**
 * Border radius tokens
 */
export const radius = tokens.radius

/**
 * Shadow tokens for elevation
 */
export const shadows = tokens.shadow

/**
 * Animation tokens including duration and easing
 */
export const animations = tokens.animation

/**
 * Breakpoint tokens for responsive design
 */
export const breakpoints = tokens.breakpoint

/**
 * Accessibility tokens including WCAG AAA colors and focus styles
 */
export const accessibility = tokens.accessibility

/**
 * Recursively flatten a nested object into CSS variable format
 * 
 * @param obj - Object to flatten
 * @param prefix - CSS variable prefix (e.g., 'color-primary')
 * @returns Record of CSS variable names to values
 * 
 * @internal
 */
const flattenTokens = (obj: any, prefix: string): Record<string, string> => {
  const result: Record<string, string> = {}
  
  for (const [key, value] of Object.entries(obj)) {
    const cssVarName = `--${prefix}-${key}`
    
    if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
      const nested = flattenTokens(value, `${prefix}-${key}`)
      Object.assign(result, nested)
    } else {
      result[cssVarName] = String(value)
    }
  }
  
  return result
}

/**
 * Generate CSS custom properties from design tokens
 * 
 * This function creates a flat object of CSS variables that can be
 * applied to the DOM for runtime theming. It uses recursive traversal
 * to automatically handle all token categories, including dynamically
 * added accent colors or other nested structures.
 * 
 * @returns Record of CSS variable names to values
 * 
 * @example
 * ```ts
 * const cssVars = getCSSVariables()
 * // {
 * //   '--color-primary-500': '#0ea5e9',
 * //   '--spacing-md': '16px',
 * //   '--color-accent-purple-500': '#8b5cf6',
 * //   '--color-accent-orange-500': '#f59e0b',
 * //   ...
 * // }
 * ```
 */
export const getCSSVariables = (): Record<string, string> => {
  const cssVars: Record<string, string> = {}
  
  Object.assign(cssVars, flattenTokens(colors.primary, 'color-primary'))
  
  for (const [accentName, accentShades] of Object.entries(colors.accent)) {
    Object.assign(cssVars, flattenTokens(accentShades, `color-accent-${accentName}`))
  }
  
  for (const [semanticName, semanticShades] of Object.entries(colors.semantic)) {
    Object.assign(cssVars, flattenTokens(semanticShades, `color-${semanticName}`))
  }
  
  Object.assign(cssVars, flattenTokens(colors.neutral, 'color-neutral'))
  Object.assign(cssVars, flattenTokens(colors.background, 'color-background'))
  
  Object.assign(cssVars, flattenTokens(spacing, 'spacing'))
  
  // Process radius tokens
  Object.assign(cssVars, flattenTokens(radius, 'radius'))
  
  Object.assign(cssVars, flattenTokens(shadows, 'shadow'))
  
  Object.assign(cssVars, flattenTokens(typography.family, 'font-family'))
  Object.assign(cssVars, flattenTokens(typography.size, 'font-size'))
  Object.assign(cssVars, flattenTokens(typography.weight, 'font-weight'))
  Object.assign(cssVars, flattenTokens(typography.lineHeight, 'line-height'))
  
  Object.assign(cssVars, flattenTokens(animations.duration, 'animation-duration'))
  Object.assign(cssVars, flattenTokens(animations.easing, 'animation-easing'))
  
  Object.assign(cssVars, flattenTokens(breakpoints, 'breakpoint'))
  
  if (accessibility['wcag-aaa']?.colors) {
    Object.assign(cssVars, flattenTokens(accessibility['wcag-aaa'].colors, 'a11y-color'))
  }
  
  if (accessibility.focus) {
    Object.assign(cssVars, flattenTokens(accessibility.focus, 'a11y-focus'))
  }
  
  return cssVars
}

/**
 * Apply design tokens as CSS custom properties to a DOM element
 * 
 * This function injects all design tokens as CSS variables into the
 * specified element or selector. Useful for runtime theming.
 * 
 * @param scope - CSS selector string or DOM element to apply tokens to
 * @returns The target HTML element
 * 
 * @example
 * ```ts
 * // Apply to document root
 * applyDesignTokens()
 * 
 * // Apply to specific element
 * applyDesignTokens('.theme-container')
 * 
 * // Apply to element reference
 * const el = document.querySelector('.app')
 * applyDesignTokens(el)
 * ```
 */
export const applyDesignTokens = (scope?: string | Element): HTMLElement => {
  let target: HTMLElement
  
  if (!scope) {
    target = document.documentElement
  } else if (typeof scope === 'string') {
    const element = document.querySelector(scope)
    target = (element || document.documentElement) as HTMLElement
  } else {
    target = scope as HTMLElement
  }
  
  const cssVars = getCSSVariables()
  
  Object.entries(cssVars).forEach(([property, value]) => {
    target.style.setProperty(property, value)
  })
  
  return target
}

/**
 * Default export with all token utilities
 */
export default {
  getToken,
  colors,
  typography,
  spacing,
  radius,
  shadows,
  animations,
  breakpoints,
  accessibility,
  getCSSVariables,
  applyDesignTokens,
  
  tokens
}
