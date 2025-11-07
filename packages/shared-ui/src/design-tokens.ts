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
 * Color shade values (50-900 scale)
 */
type ColorShade = '50' | '100' | '200' | '300' | '400' | '500' | '600' | '700' | '800' | '900' | 'text-aaa'

/**
 * Accent color names
 */
type AccentColor = 'purple' | 'orange'

/**
 * Semantic color names
 */
type SemanticColor = 'success' | 'error' | 'warning' | 'info'

/**
 * Spacing scale values
 */
type SpacingScale = 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl' | '3xl' | '4xl'

/**
 * Font size values
 */
type FontSize = 'caption' | 'small' | 'body' | 'heading3' | 'heading2' | 'heading1' | 'display'

/**
 * Font weight values
 */
type FontWeight = 'regular' | 'medium' | 'semibold' | 'bold'

/**
 * Border radius values
 */
type RadiusSize = 'sm' | 'md' | 'lg' | 'xl' | '2xl' | 'full'

/**
 * Shadow size values
 */
type ShadowSize = 'sm' | 'md' | 'lg' | 'xl' | '2xl'

/**
 * Type-safe token paths for common design tokens
 * Provides autocomplete and type checking for token access
 */
export type TokenPath =
  | `color.primary.${ColorShade}`
  | `color.accent.${AccentColor}.${ColorShade}`
  | `color.semantic.${SemanticColor}.${ColorShade}`
  | `color.neutral.${ColorShade}`
  | `color.background.${'base' | 'surface' | 'overlay'}`
  | `space.${SpacingScale}`
  | `font.family.${'primary' | 'secondary' | 'mono'}`
  | `font.size.${FontSize}`
  | `font.weight.${FontWeight}`
  | `font.lineHeight.${FontSize}`
  | `radius.${RadiusSize}`
  | `shadow.${ShadowSize}`
  | `animation.duration.${'instant' | 'fast' | 'normal' | 'slow'}`
  | `animation.easing.${'linear' | 'easeIn' | 'easeOut' | 'easeInOut' | 'spring'}`
  | `breakpoint.${'mobile' | 'tablet' | 'desktop'}`
  | `accessibility.wcag-aaa.contrast.${'normal-text' | 'large-text' | 'ui-components'}`
  | `accessibility.wcag-aaa.colors.${'primary-text' | 'success-text' | 'error-text' | 'warning-text' | 'info-text'}`
  | `accessibility.focus.${'outline-width' | 'outline-offset' | 'outline-color'}`
  | `accessibility.touch-target.min-size`
  | `accessibility.animation.reduced-motion-duration`
  | string

/**
 * Type-safe token access using dot notation
 * 
 * Provides IDE autocomplete for common token paths while maintaining
 * flexibility for dynamic or less common paths.
 * 
 * @param path - Dot-notation path to token (e.g., 'color.primary.500')
 * @returns Token value (string for colors, spacing, etc.)
 * 
 * @example
 * ```ts
 * // Autocomplete available for common paths
 * const primaryColor = getToken('color.primary.500')
 * const spacing = getToken('space.md')
 * const fontBold = getToken('font.weight.bold')
 * 
 * // Dynamic paths still work
 * const dynamicPath = `color.${colorType}.${shade}` as TokenPath
 * const color = getToken(dynamicPath)
 * ```
 */
export const getToken = (path: TokenPath): string | undefined => {
  const value = path.split('.').reduce((obj: any, key: string) => obj?.[key], tokens)
  return value !== undefined ? String(value) : undefined
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
 * Generate CSS custom properties from design tokens
 * 
 * This function creates a flat object of CSS variables that can be
 * applied to the DOM for runtime theming.
 * 
 * @returns Record of CSS variable names to values
 * 
 * @example
 * ```ts
 * const cssVars = getCSSVariables()
 * // {
 * //   '--color-primary-500': '#0ea5e9',
 * //   '--spacing-md': '16px',
 * //   ...
 * // }
 * ```
 */
export const getCSSVariables = (): Record<string, string> => {
  const cssVars: Record<string, string> = {}
  
  Object.entries(colors.primary).forEach(([key, value]) => {
    cssVars[`--color-primary-${key}`] = value as string
  })
  
  Object.entries(colors.accent.purple).forEach(([key, value]) => {
    cssVars[`--color-accent-purple-${key}`] = value as string
  })
  
  Object.entries(colors.accent.orange).forEach(([key, value]) => {
    cssVars[`--color-accent-orange-${key}`] = value as string
  })
  
  Object.entries(colors.semantic.success).forEach(([key, value]) => {
    cssVars[`--color-success-${key}`] = value as string
  })
  
  Object.entries(colors.semantic.error).forEach(([key, value]) => {
    cssVars[`--color-error-${key}`] = value as string
  })
  
  Object.entries(colors.semantic.warning).forEach(([key, value]) => {
    cssVars[`--color-warning-${key}`] = value as string
  })
  
  Object.entries(colors.semantic.info).forEach(([key, value]) => {
    cssVars[`--color-info-${key}`] = value as string
  })
  
  Object.entries(colors.neutral).forEach(([key, value]) => {
    cssVars[`--color-neutral-${key}`] = value as string
  })
  
  Object.entries(colors.background).forEach(([key, value]) => {
    cssVars[`--color-background-${key}`] = value as string
  })
  
  Object.entries(spacing).forEach(([key, value]) => {
    cssVars[`--spacing-${key}`] = value as string
  })
  
  Object.entries(radius).forEach(([key, value]) => {
    cssVars[`--radius-${key}`] = value as string
  })
  
  Object.entries(shadows).forEach(([key, value]) => {
    cssVars[`--shadow-${key}`] = value as string
  })
  
  Object.entries(typography.family).forEach(([key, value]) => {
    cssVars[`--font-family-${key}`] = value as string
  })
  
  Object.entries(typography.size).forEach(([key, value]) => {
    cssVars[`--font-size-${key}`] = value as string
  })
  
  Object.entries(typography.weight).forEach(([key, value]) => {
    cssVars[`--font-weight-${key}`] = value as string
  })
  
  Object.entries(typography.lineHeight).forEach(([key, value]) => {
    cssVars[`--line-height-${key}`] = value as string
  })
  
  Object.entries(animations.duration).forEach(([key, value]) => {
    cssVars[`--animation-duration-${key}`] = value as string
  })
  
  Object.entries(animations.easing).forEach(([key, value]) => {
    cssVars[`--animation-easing-${key}`] = value as string
  })
  
  Object.entries(breakpoints).forEach(([key, value]) => {
    cssVars[`--breakpoint-${key}`] = value as string
  })
  
  if (accessibility['wcag-aaa']?.colors) {
    Object.entries(accessibility['wcag-aaa'].colors).forEach(([key, value]) => {
      cssVars[`--a11y-color-${key}`] = value as string
    })
  }
  
  if (accessibility.focus) {
    Object.entries(accessibility.focus).forEach(([key, value]) => {
      cssVars[`--a11y-focus-${key}`] = value as string
    })
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
