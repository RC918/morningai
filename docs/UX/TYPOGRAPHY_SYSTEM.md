# Typography System - Apple-Level Design

**Last Updated**: 2025-10-24  
**Status**: Phase 1 Week 1 - Typography Enhancement  
**Compliance**: Apple Human Interface Guidelines, WCAG AA

---

## Overview

MorningAI's typography system follows Apple's Human Interface Guidelines, implementing a 14-level type scale that ensures clarity, hierarchy, and accessibility across all devices and contexts.

### Design Philosophy

**Clarity First**: Every typographic decision prioritizes readability and comprehension. Text should be effortless to read, with appropriate contrast, spacing, and sizing.

**Hierarchy Through Scale**: Our 14-level type scale creates clear visual hierarchy without relying on color or decoration. Size, weight, and spacing work together to guide the user's eye.

**Responsive by Default**: Typography adapts fluidly across breakpoints, maintaining optimal reading experiences from mobile to desktop.

**Accessibility Built-In**: All text meets WCAG AA standards for contrast (4.5:1 minimum) and supports dynamic type scaling for users with visual impairments.

---

## Type Scale

### Complete 14-Level Scale

Our type scale follows iOS naming conventions and sizing principles:

| Level | Size (rem) | Size (px) | Line Height | Use Case | Weight |
|-------|-----------|-----------|-------------|----------|--------|
| **Display 1** | 3.5rem | 56px | 1.1 | Hero headlines, landing pages | Bold (700) |
| **Display 2** | 3rem | 48px | 1.15 | Section headlines | Bold (700) |
| **Display 3** | 2.5rem | 40px | 1.2 | Page titles | Semibold (600) |
| **Large Title** | 2.125rem | 34px | 1.25 | Primary headings | Bold (700) |
| **Title 1** | 1.75rem | 28px | 1.3 | Section headings | Semibold (600) |
| **Title 2** | 1.375rem | 22px | 1.35 | Subsection headings | Semibold (600) |
| **Title 3** | 1.25rem | 20px | 1.4 | Card titles, list headers | Semibold (600) |
| **Headline** | 1.0625rem | 17px | 1.45 | Emphasized body text | Semibold (600) |
| **Body** | 1.0625rem | 17px | 1.5 | Primary body text | Regular (400) |
| **Callout** | 1rem | 16px | 1.5 | Secondary body text | Regular (400) |
| **Subhead** | 0.9375rem | 15px | 1.5 | Tertiary text, labels | Regular (400) |
| **Footnote** | 0.8125rem | 13px | 1.5 | Captions, helper text | Regular (400) |
| **Caption 1** | 0.75rem | 12px | 1.5 | Timestamps, metadata | Regular (400) |
| **Caption 2** | 0.6875rem | 11px | 1.5 | Fine print, legal text | Regular (400) |

### Responsive Scaling

Typography scales fluidly across breakpoints using CSS clamp():

```css
/* Display 1 - Scales from 2.5rem (mobile) to 3.5rem (desktop) */
font-size: clamp(2.5rem, 2rem + 2vw, 3.5rem);

/* Title 1 - Scales from 1.5rem (mobile) to 1.75rem (desktop) */
font-size: clamp(1.5rem, 1.25rem + 1vw, 1.75rem);

/* Body - Scales from 1rem (mobile) to 1.0625rem (desktop) */
font-size: clamp(1rem, 0.9rem + 0.3vw, 1.0625rem);
```

---

## Font Families

### Primary Font Stack

```css
font-family: Inter, -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'SF Pro Display', system-ui, sans-serif;
```

**Inter** is our primary typeface, chosen for:
- Excellent readability at all sizes
- Wide language support (Latin, Cyrillic, Greek)
- Variable font support (weight 100-900)
- Open source and self-hostable
- Similar metrics to SF Pro (Apple's system font)

### Monospace Font Stack

```css
font-family: 'JetBrains Mono', 'SF Mono', Monaco, 'Cascadia Code', 'Courier New', monospace;
```

Used for:
- Code snippets
- API keys and tokens
- Technical data (IDs, hashes)
- Terminal output

### Display Font Stack

```css
font-family: Inter, -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
```

Used for:
- Large headlines (Display 1-3)
- Marketing content
- Hero sections

---

## Font Weights

### Weight Scale

| Weight | Value | Use Case |
|--------|-------|----------|
| **Light** | 300 | Large display text (optional) |
| **Regular** | 400 | Body text, default weight |
| **Medium** | 500 | Subtle emphasis, navigation |
| **Semibold** | 600 | Headings, important labels |
| **Bold** | 700 | Strong emphasis, CTAs |

### Weight Guidelines

**Don't use too many weights**: Stick to 2-3 weights per design to maintain consistency.

**Pair weights with size**: Larger text can use lighter weights; smaller text needs heavier weights for legibility.

**Consider contrast**: On dark backgrounds, lighter weights may appear thinner than on light backgrounds.

---

## Line Height & Spacing

### Line Height Principles

**Tighter for Headlines**: Large text (Display, Titles) uses line-height 1.1-1.3 for visual impact.

**Comfortable for Body**: Body text uses line-height 1.5 for optimal readability.

**Consistent for UI**: Interface elements use line-height 1.5 for predictable spacing.

### Line Height Scale

```css
--line-height-tight: 1.25;    /* Headlines, titles */
--line-height-normal: 1.5;    /* Body text, UI */
--line-height-relaxed: 1.75;  /* Long-form content */
```

### Letter Spacing

```css
/* Display text - Slightly tighter */
letter-spacing: -0.02em;

/* Headlines - Neutral */
letter-spacing: 0;

/* Body text - Neutral */
letter-spacing: 0;

/* Small text - Slightly wider */
letter-spacing: 0.01em;

/* All caps - Much wider */
letter-spacing: 0.05em;
text-transform: uppercase;
```

---

## Accessibility

### WCAG AA Compliance

**Minimum Contrast Ratios**:
- Normal text (< 18px): 4.5:1
- Large text (≥ 18px or ≥ 14px bold): 3:1
- UI components: 3:1

**Our Standards**:
- Body text on white: 6.12:1 (using #0051D0)
- Headings on white: 6.12:1 (using #0051D0)
- Muted text on white: 4.54:1 (using #6b7280)

### Dynamic Type Support

Support user font size preferences:

```css
/* Respect user's font size settings */
html {
  font-size: 100%; /* 16px default, but respects browser settings */
}

/* Use rem units for all typography */
.body-text {
  font-size: 1.0625rem; /* Scales with user preference */
}
```

### Focus Indicators

All interactive text elements have visible focus indicators:

```css
a:focus-visible,
button:focus-visible {
  outline: 2px solid #0051D0;
  outline-offset: 2px;
  border-radius: 4px;
}
```

---

## Implementation

### CSS Custom Properties

```css
:root {
  /* Font Families */
  --font-sans: Inter, -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', 'SF Mono', Monaco, monospace;
  --font-display: Inter, -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
  
  /* Font Sizes */
  --font-size-caption2: 0.6875rem;   /* 11px */
  --font-size-caption1: 0.75rem;     /* 12px */
  --font-size-footnote: 0.8125rem;   /* 13px */
  --font-size-subhead: 0.9375rem;    /* 15px */
  --font-size-callout: 1rem;         /* 16px */
  --font-size-body: 1.0625rem;       /* 17px */
  --font-size-headline: 1.0625rem;   /* 17px */
  --font-size-title3: 1.25rem;       /* 20px */
  --font-size-title2: 1.375rem;      /* 22px */
  --font-size-title1: 1.75rem;       /* 28px */
  --font-size-large: 2.125rem;       /* 34px */
  --font-size-display3: 2.5rem;      /* 40px */
  --font-size-display2: 3rem;        /* 48px */
  --font-size-display1: 3.5rem;      /* 56px */
  
  /* Font Weights */
  --font-weight-light: 300;
  --font-weight-normal: 400;
  --font-weight-medium: 500;
  --font-weight-semibold: 600;
  --font-weight-bold: 700;
  
  /* Line Heights */
  --line-height-tight: 1.25;
  --line-height-normal: 1.5;
  --line-height-relaxed: 1.75;
}
```

### Utility Classes

```css
/* Display Styles */
.text-display-1 {
  font-size: var(--font-size-display1);
  font-weight: var(--font-weight-bold);
  line-height: 1.1;
  letter-spacing: -0.02em;
}

.text-display-2 {
  font-size: var(--font-size-display2);
  font-weight: var(--font-weight-bold);
  line-height: 1.15;
  letter-spacing: -0.02em;
}

.text-display-3 {
  font-size: var(--font-size-display3);
  font-weight: var(--font-weight-semibold);
  line-height: 1.2;
  letter-spacing: -0.01em;
}

/* Title Styles */
.text-large-title {
  font-size: var(--font-size-large);
  font-weight: var(--font-weight-bold);
  line-height: 1.25;
  letter-spacing: -0.01em;
}

.text-title-1 {
  font-size: var(--font-size-title1);
  font-weight: var(--font-weight-semibold);
  line-height: 1.3;
}

.text-title-2 {
  font-size: var(--font-size-title2);
  font-weight: var(--font-weight-semibold);
  line-height: 1.35;
}

.text-title-3 {
  font-size: var(--font-size-title3);
  font-weight: var(--font-weight-semibold);
  line-height: 1.4;
}

/* Body Styles */
.text-headline {
  font-size: var(--font-size-headline);
  font-weight: var(--font-weight-semibold);
  line-height: 1.45;
}

.text-body {
  font-size: var(--font-size-body);
  font-weight: var(--font-weight-normal);
  line-height: 1.5;
}

.text-callout {
  font-size: var(--font-size-callout);
  font-weight: var(--font-weight-normal);
  line-height: 1.5;
}

.text-subhead {
  font-size: var(--font-size-subhead);
  font-weight: var(--font-weight-normal);
  line-height: 1.5;
}

/* Small Text Styles */
.text-footnote {
  font-size: var(--font-size-footnote);
  font-weight: var(--font-weight-normal);
  line-height: 1.5;
}

.text-caption-1 {
  font-size: var(--font-size-caption1);
  font-weight: var(--font-weight-normal);
  line-height: 1.5;
}

.text-caption-2 {
  font-size: var(--font-size-caption2);
  font-weight: var(--font-weight-normal);
  line-height: 1.5;
}

/* Responsive Typography */
.text-responsive-display {
  font-size: clamp(2.5rem, 2rem + 2vw, 3.5rem);
  font-weight: var(--font-weight-bold);
  line-height: 1.1;
}

.text-responsive-title {
  font-size: clamp(1.5rem, 1.25rem + 1vw, 1.75rem);
  font-weight: var(--font-weight-semibold);
  line-height: 1.3;
}

.text-responsive-body {
  font-size: clamp(1rem, 0.9rem + 0.3vw, 1.0625rem);
  line-height: 1.5;
}
```

### React/JSX Usage

```jsx
// Display text
<h1 className="text-display-1 text-gray-900">
  Welcome to MorningAI
</h1>

// Title text
<h2 className="text-title-1 text-gray-800">
  Dashboard Overview
</h2>

// Body text
<p className="text-body text-gray-700">
  Your AI agents are running smoothly with 99.9% uptime.
</p>

// Small text
<span className="text-footnote text-gray-500">
  Last updated 2 minutes ago
</span>

// Responsive text
<h1 className="text-responsive-display text-gray-900">
  Scale with viewport
</h1>
```

---

## Best Practices

### Do's ✅

**Use the type scale consistently**: Don't create custom font sizes outside the scale.

**Maintain hierarchy**: Larger text should always be more important than smaller text.

**Limit font weights**: Use 2-3 weights maximum per design.

**Test at different sizes**: Verify readability on mobile, tablet, and desktop.

**Support dynamic type**: Use rem units and respect user preferences.

**Ensure sufficient contrast**: Always meet WCAG AA standards (4.5:1 for body text).

### Don'ts ❌

**Don't use too many type styles**: Limit to 3-4 styles per screen.

**Don't rely on color alone**: Use size and weight to create hierarchy.

**Don't use small text for critical information**: Minimum 13px (0.8125rem) for body text.

**Don't ignore line length**: Keep body text between 45-75 characters per line.

**Don't use all caps for long text**: Reserve for labels and short headings.

**Don't use light weights on small text**: Minimum 400 weight for text under 16px.

---

## Examples

### Dashboard Header

```jsx
<header className="space-y-2">
  <h1 className="text-large-title text-gray-900">
    Dashboard
  </h1>
  <p className="text-body text-gray-600">
    Monitor your AI agents and system performance
  </p>
</header>
```

### Card Component

```jsx
<div className="card">
  <h3 className="text-title-3 text-gray-900 mb-2">
    Active Agents
  </h3>
  <p className="text-headline text-primary-600 mb-1">
    24
  </p>
  <p className="text-footnote text-gray-500">
    +3 from yesterday
  </p>
</div>
```

### Form Label

```jsx
<label className="text-subhead font-medium text-gray-700 mb-1">
  Email Address
</label>
<input 
  type="email" 
  className="text-body text-gray-900"
  placeholder="you@example.com"
/>
<p className="text-footnote text-gray-500 mt-1">
  We'll never share your email with anyone else.
</p>
```

### Alert Message

```jsx
<div className="alert alert-success">
  <h4 className="text-headline text-success-900 mb-1">
    Success!
  </h4>
  <p className="text-callout text-success-700">
    Your changes have been saved successfully.
  </p>
</div>
```

---

## Migration Guide

### From Old System

If you're migrating from the old 8-level system:

| Old Class | New Class | Notes |
|-----------|-----------|-------|
| `.text-xs` | `.text-caption-2` | 11px → 11px |
| `.text-sm` | `.text-footnote` | 12px → 13px |
| `.text-base` | `.text-body` | 16px → 17px |
| `.text-lg` | `.text-title-3` | 18px → 20px |
| `.text-xl` | `.text-title-2` | 20px → 22px |
| `.text-2xl` | `.text-title-1` | 24px → 28px |
| `.text-3xl` | `.text-large` | 30px → 34px |
| `.text-4xl` | `.text-display-3` | 36px → 40px |

### Automated Migration

Use this script to update your codebase:

```bash
# Find and replace old classes
find src -type f -name "*.jsx" -o -name "*.tsx" | xargs sed -i '' \
  -e 's/text-xs/text-caption-2/g' \
  -e 's/text-sm/text-footnote/g' \
  -e 's/text-base/text-body/g' \
  -e 's/text-lg/text-title-3/g' \
  -e 's/text-xl/text-title-2/g' \
  -e 's/text-2xl/text-title-1/g' \
  -e 's/text-3xl/text-large/g' \
  -e 's/text-4xl/text-display-3/g'
```

---

## Testing

### Visual Regression Testing

Test typography changes with visual regression tools:

```bash
# Run visual tests
npm run test:visual

# Update snapshots
npm run test:visual -- -u
```

### Accessibility Testing

```bash
# Run axe accessibility tests
npm run test:a11y

# Check contrast ratios
npm run test:contrast
```

### Cross-Browser Testing

Test typography rendering in:
- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)
- Mobile Safari (iOS 15+)
- Chrome Mobile (Android 10+)

---

## Browser Compatibility

### Modern CSS Features

Our typography system uses modern CSS features that require recent browser versions. Below is a comprehensive compatibility guide.

#### CSS Custom Properties (CSS Variables)

**Status**: ✅ Fully Supported

```css
.text-body {
  font-size: var(--font-size-body, 1.0625rem);
}
```

**Browser Support**:
- Chrome 49+ (March 2016) ✅
- Firefox 31+ (July 2014) ✅
- Safari 9.1+ (March 2016) ✅
- Edge 15+ (April 2017) ✅
- iOS Safari 9.3+ ✅
- Chrome Android 49+ ✅

**Fallback Strategy**: All CSS variables include fallback values
```css
font-size: var(--font-size-body, 1.0625rem); /* Fallback: 1.0625rem */
```

**Impact**: IE 11 not supported (project requirement)

---

#### CSS `clamp()` Function (Responsive Typography)

**Status**: ✅ Well Supported

```css
.text-responsive-display {
  font-size: clamp(2.5rem, 2rem + 2vw, 3.5rem);
}
```

**Browser Support**:
- Chrome 79+ (December 2019) ✅
- Firefox 75+ (April 2020) ✅
- Safari 13.1+ (March 2020) ✅
- Edge 79+ (January 2020) ✅
- iOS Safari 13.4+ ✅
- Chrome Android 79+ ✅

**Fallback Strategy**: Use fixed font sizes for older browsers
```css
/* Fallback for older browsers */
.text-responsive-display {
  font-size: 3rem; /* Fixed size */
  font-size: clamp(2.5rem, 2rem + 2vw, 3.5rem); /* Progressive enhancement */
}
```

**Impact**: Older browsers (pre-2020) will see fixed font sizes instead of fluid scaling. Content remains readable.

---

#### `text-wrap: balance` and `text-wrap: pretty`

**Status**: ⚠️ Modern Browsers Only (2023+)

```css
.text-balance {
  text-wrap: balance;
}

.text-pretty {
  text-wrap: pretty;
}
```

**Browser Support**:

**`text-wrap: balance`**:
- Chrome 114+ (May 2023) ✅
- Edge 114+ (June 2023) ✅
- Safari 17.4+ (March 2024) ✅
- Firefox 121+ (December 2023) ✅

**`text-wrap: pretty`**:
- Chrome 117+ (September 2023) ✅
- Edge 117+ (September 2023) ✅
- Safari 17.5+ (May 2024) ✅
- Firefox 121+ (December 2023) ✅

**Fallback Strategy**: Graceful degradation
```css
.text-balance {
  text-wrap: balance;
  /* Older browsers ignore this property and use default wrapping */
}
```

**Impact**: 
- ✅ Modern browsers (2023+): Balanced, visually pleasing text wrapping
- ⚠️ Older browsers: Standard text wrapping (no visual breakage)
- 📊 Global browser support: ~85% (as of October 2024)

**Recommendation**: Safe to use. Older browsers will display text normally without any visual issues.

---

#### `-webkit-line-clamp` (Text Truncation)

**Status**: ✅ Well Supported (with prefix)

```css
.text-truncate-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
```

**Browser Support**:
- Chrome 6+ (2010) ✅
- Firefox 68+ (July 2019) ✅
- Safari 5+ (2010) ✅
- Edge 17+ (April 2018) ✅
- iOS Safari 5+ ✅
- Chrome Android 18+ ✅

**Fallback Strategy**: Show full text
```css
.text-truncate-2 {
  overflow: hidden;
  /* Older browsers will show full text without truncation */
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}
```

**Impact**: Excellent support. Older browsers show full text (acceptable fallback).

---

#### Variable Fonts

**Status**: ✅ Well Supported

```css
font-family: Inter, -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
font-variation-settings: 'wght' 500;
```

**Browser Support**:
- Chrome 62+ (October 2017) ✅
- Firefox 62+ (September 2018) ✅
- Safari 11+ (September 2017) ✅
- Edge 17+ (April 2018) ✅
- iOS Safari 11+ ✅
- Chrome Android 62+ ✅

**Fallback Strategy**: System fonts
```css
/* If Inter fails to load, fall back to system fonts */
font-family: Inter, -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
```

**Impact**: Excellent support. System fonts provide consistent fallback.

---

### Browser Support Matrix

| Feature | Chrome | Firefox | Safari | Edge | iOS Safari | Chrome Android | Support Level |
|---------|--------|---------|--------|------|------------|----------------|---------------|
| CSS Variables | 49+ | 31+ | 9.1+ | 15+ | 9.3+ | 49+ | ✅ Excellent |
| `clamp()` | 79+ | 75+ | 13.1+ | 79+ | 13.4+ | 79+ | ✅ Good |
| `text-wrap: balance` | 114+ | 121+ | 17.4+ | 114+ | 17.4+ | 114+ | ⚠️ Modern |
| `text-wrap: pretty` | 117+ | 121+ | 17.5+ | 117+ | 17.5+ | 117+ | ⚠️ Modern |
| `-webkit-line-clamp` | 6+ | 68+ | 5+ | 17+ | 5+ | 18+ | ✅ Excellent |
| Variable Fonts | 62+ | 62+ | 11+ | 17+ | 11+ | 62+ | ✅ Excellent |

---

### Minimum Browser Requirements

**Recommended Minimum Versions** (for full feature support):

- **Chrome**: 114+ (May 2023)
- **Firefox**: 121+ (December 2023)
- **Safari**: 17.4+ (March 2024)
- **Edge**: 114+ (June 2023)
- **iOS Safari**: 17.4+ (March 2024)
- **Chrome Android**: 114+ (May 2023)

**Acceptable Minimum Versions** (with graceful degradation):

- **Chrome**: 79+ (December 2019)
- **Firefox**: 75+ (April 2020)
- **Safari**: 13.1+ (March 2020)
- **Edge**: 79+ (January 2020)
- **iOS Safari**: 13.4+ (March 2020)
- **Chrome Android**: 79+ (December 2019)

---

### Testing Recommendations

#### 1. Test in Target Browsers

**Priority 1** (Must test):
- Chrome (latest)
- Safari (latest)
- Firefox (latest)
- Mobile Safari (iOS 16+)

**Priority 2** (Should test):
- Edge (latest)
- Chrome Android (latest)
- Samsung Internet (latest)

**Priority 3** (Nice to have):
- Safari (iOS 15)
- Firefox ESR

#### 2. Feature Detection

Use feature detection for modern CSS:

```javascript
// Check for text-wrap support
const supportsTextWrap = CSS.supports('text-wrap', 'balance');

if (supportsTextWrap) {
  document.body.classList.add('supports-text-wrap');
}
```

```css
/* Apply text-wrap only if supported */
.supports-text-wrap .text-balance {
  text-wrap: balance;
}
```

#### 3. Progressive Enhancement

Always provide fallbacks:

```css
/* Base styles (all browsers) */
.heading {
  font-size: 2rem;
  line-height: 1.2;
}

/* Enhanced styles (modern browsers) */
@supports (font-size: clamp(1rem, 2vw, 3rem)) {
  .heading {
    font-size: clamp(1.5rem, 2vw + 1rem, 2.5rem);
  }
}
```

---

### Known Issues and Workarounds

#### Issue 1: `text-wrap: balance` in Firefox

**Problem**: Firefox 121-126 had rendering bugs with `text-wrap: balance` on long paragraphs.

**Workaround**: Limit usage to headings and short paragraphs (< 4 lines).

```css
/* Safe usage */
h1, h2, h3 {
  text-wrap: balance;
  max-width: 50ch; /* Limit line length */
}

/* Avoid for long paragraphs */
p {
  /* Don't use text-wrap: balance here */
}
```

**Status**: Fixed in Firefox 127+ (June 2024)

---

#### Issue 2: Variable Font Rendering on Windows

**Problem**: Some Windows systems render variable fonts with poor hinting.

**Workaround**: Use `font-smooth` and `text-rendering` properties.

```css
body {
  font-family: Inter, system-ui, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
}
```

---

#### Issue 3: `clamp()` with `calc()` in Safari 13

**Problem**: Safari 13.0 had bugs with nested `calc()` inside `clamp()`.

**Workaround**: Simplify calculations or use Safari 13.1+.

```css
/* Problematic in Safari 13.0 */
font-size: clamp(1rem, calc(1rem + 2vw), 3rem);

/* Better compatibility */
font-size: clamp(1rem, 1rem + 2vw, 3rem);
```

**Status**: Fixed in Safari 13.1+ (March 2020)

---

### Performance Considerations

#### Variable Fonts

**Impact**: Minimal performance impact. Variable fonts are often smaller than loading multiple font weights.

```
Traditional: 
- Regular (400): 120KB
- Medium (500): 125KB
- Bold (700): 130KB
Total: 375KB

Variable Font:
- Inter Variable: 280KB
Savings: 95KB (25% smaller)
```

#### CSS Custom Properties

**Impact**: Negligible. CSS variables have minimal performance overhead.

#### `text-wrap: balance`

**Impact**: Slight layout cost. Browser recalculates text wrapping.

**Recommendation**: Use sparingly on headings, not on large blocks of text.

---

### Migration Path for Legacy Browsers

If you need to support older browsers (pre-2020):

#### 1. Provide Fixed Font Sizes

```css
/* Fallback for older browsers */
.text-display-1 {
  font-size: 3.5rem; /* Fixed size */
}

/* Progressive enhancement for modern browsers */
@supports (font-size: clamp(1rem, 2vw, 3rem)) {
  .text-display-1 {
    font-size: clamp(2.5rem, 2rem + 2vw, 3.5rem);
  }
}
```

#### 2. Polyfill CSS Variables (Not Recommended)

```html
<!-- Only if you MUST support IE 11 -->
<script src="https://cdn.jsdelivr.net/npm/css-vars-ponyfill@2"></script>
<script>
  cssVars({
    include: 'style,link[rel="stylesheet"]',
    onlyLegacy: true
  });
</script>
```

**Note**: We don't recommend supporting IE 11. Focus on modern browsers.

---

### Accessibility and Browser Support

**Important**: All typography features degrade gracefully. Older browsers will display text with:
- ✅ Correct font sizes (using fallback values)
- ✅ Proper contrast ratios
- ✅ Readable line heights
- ✅ Semantic HTML structure

**No accessibility features are lost in older browsers.**

---

## Resources

### Apple Human Interface Guidelines
- [Typography](https://developer.apple.com/design/human-interface-guidelines/typography)
- [SF Pro Font](https://developer.apple.com/fonts/)
- [Dynamic Type](https://developer.apple.com/design/human-interface-guidelines/dynamic-type)

### WCAG Guidelines
- [WCAG 2.1 Level AA](https://www.w3.org/WAI/WCAG21/quickref/)
- [Contrast Checker](https://webaim.org/resources/contrastchecker/)

### Browser Compatibility
- [Can I Use - CSS Variables](https://caniuse.com/css-variables)
- [Can I Use - CSS clamp()](https://caniuse.com/css-math-functions)
- [Can I Use - text-wrap](https://caniuse.com/mdn-css_properties_text-wrap)
- [MDN - CSS text-wrap](https://developer.mozilla.org/en-US/docs/Web/CSS/text-wrap)

### Tools
- [Type Scale Calculator](https://typescale.com/)
- [Modular Scale](https://www.modularscale.com/)
- [Inter Font](https://rsms.me/inter/)
- [BrowserStack](https://www.browserstack.com/) - Cross-browser testing

---

**Version**: 1.1.0  
**Last Updated**: 2025-10-25  
**Maintained by**: UI/UX Team
