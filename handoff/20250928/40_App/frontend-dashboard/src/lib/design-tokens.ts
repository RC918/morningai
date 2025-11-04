import tokens from '../../public/tokens.json'

export const getToken = (path: string): any => {
  return path.split('.').reduce((obj: any, key: string) => obj?.[key], tokens)
}

export const colors = {
  primary: tokens.color.primary,
  accent: tokens.color.accent,
  semantic: tokens.color.semantic,
  neutral: tokens.color.neutral,
  background: tokens.color.background
}

export const typography = {
  family: tokens.font.family,
  size: tokens.font.size,
  weight: tokens.font.weight,
  lineHeight: tokens.font.lineHeight
}

export const spacing = tokens.space
export const radius = tokens.radius
export const shadows = tokens.shadow
export const animations = tokens.animation
export const breakpoints = tokens.breakpoint

export const getCSSVariables = (): Record<string, any> => {
  const cssVars: Record<string, any> = {}
  
  Object.entries(colors.primary).forEach(([key, value]) => {
    cssVars[`--color-primary-${key}`] = value
  })
  
  Object.entries(colors.semantic.success).forEach(([key, value]) => {
    cssVars[`--color-success-${key}`] = value
  })
  
  Object.entries(colors.semantic.error).forEach(([key, value]) => {
    cssVars[`--color-error-${key}`] = value
  })
  
  Object.entries(spacing).forEach(([key, value]) => {
    cssVars[`--spacing-${key}`] = value
  })
  
  Object.entries(radius).forEach(([key, value]) => {
    cssVars[`--radius-${key}`] = value
  })
  
  return cssVars
}

export const applyDesignTokens = (scope: string | Element = '.theme-morning-ai'): HTMLElement => {
  const container = typeof scope === 'string' 
    ? document.querySelector(scope) 
    : scope
  
  const target = (container || document.documentElement) as HTMLElement
  const cssVars = getCSSVariables()
  
  Object.entries(cssVars).forEach(([property, value]) => {
    target.style.setProperty(property, value)
  })
  
  return target
}

export default {
  getToken,
  colors,
  typography,
  spacing,
  radius,
  shadows,
  animations,
  breakpoints,
  getCSSVariables,
  applyDesignTokens
}
