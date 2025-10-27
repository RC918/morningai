# Typography System Migration Guide

**Version**: 1.0.0  
**Date**: 2025-10-25  
**Status**: Ready for Implementation

---

## Overview

This guide helps developers migrate existing components to use the new Apple-level Typography System while maintaining backward compatibility with Tailwind CSS.

### Migration Strategy

**Approach**: **Gradual, Non-Breaking Migration**

- ✅ New components: Use semantic typography classes
- ✅ Existing components: Keep Tailwind classes (both work)
- ✅ Refactoring: Migrate opportunistically during updates

**Key Principle**: Our typography system **extends** Tailwind, not replaces it.

---

## Quick Reference

### Old (Tailwind) → New (Semantic)

| Tailwind Class | Semantic Class | Use Case |
|----------------|----------------|----------|
| `text-4xl font-bold` | `text-display-1` | Hero headlines |
| `text-3xl font-bold` | `text-display-2` | Section headlines |
| `text-2xl font-semibold` | `text-large-title` | Page titles |
| `text-xl font-semibold` | `text-title-1` | Primary headings |
| `text-lg font-semibold` | `text-title-2` | Subsection headings |
| `text-base font-semibold` | `text-title-3` | Card titles |
| `text-base font-semibold` | `text-headline` | Emphasized text |
| `text-base` | `text-body` | Body text |
| `text-sm` | `text-callout` | Secondary text |
| `text-sm` | `text-subhead` | Labels |
| `text-xs` | `text-footnote` | Helper text |
| `text-xs` | `text-caption-1` | Timestamps |

---

## Migration Examples

### Example 1: Dashboard Header

#### Before (Tailwind)
```jsx
<header className="space-y-2">
  <h1 className="text-3xl font-bold text-gray-900">
    Dashboard
  </h1>
  <p className="text-base text-gray-600">
    Monitor your AI agents and system performance
  </p>
</header>
```

#### After (Semantic Typography)
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

#### Benefits
- ✅ Semantic meaning: "large-title" is clearer than "3xl"
- ✅ Consistent sizing: Follows iOS typography scale
- ✅ Automatic line-height: Optimized for readability
- ✅ Responsive: Can use `.text-responsive-title` for fluid scaling

---

### Example 2: Metric Card

#### Before (Tailwind)
```jsx
<div className="card">
  <h3 className="text-lg font-semibold text-gray-900 mb-2">
    Active Agents
  </h3>
  <p className="text-4xl font-bold text-blue-600 mb-1">
    24
  </p>
  <p className="text-xs text-gray-500">
    +3 from yesterday
  </p>
</div>
```

#### After (Semantic Typography)
```jsx
<div className="card">
  <h3 className="text-title-3 text-gray-900 mb-2">
    Active Agents
  </h3>
  <p className="text-display-2 font-bold text-primary-600 mb-1">
    24
  </p>
  <p className="text-footnote text-gray-500">
    +3 from yesterday
  </p>
</div>
```

#### Benefits
- ✅ Semantic hierarchy: title-3 → display-2 → footnote
- ✅ Consistent spacing: Optimized line-heights
- ✅ Better accessibility: Clear content structure

---

### Example 3: Form Label

#### Before (Tailwind)
```jsx
<div>
  <label className="text-sm font-medium text-gray-700 mb-1 block">
    Email Address
  </label>
  <input 
    type="email" 
    className="text-base text-gray-900 border border-gray-300 rounded-md px-3 py-2 w-full"
    placeholder="you@example.com"
  />
  <p className="text-xs text-gray-500 mt-1">
    We'll never share your email with anyone else.
  </p>
</div>
```

#### After (Semantic Typography)
```jsx
<div>
  <label className="text-subhead font-medium text-gray-700 mb-1 block">
    Email Address
  </label>
  <input 
    type="email" 
    className="text-body text-gray-900 border border-gray-300 rounded-md px-3 py-2 w-full"
    placeholder="you@example.com"
  />
  <p className="text-footnote text-gray-500 mt-1">
    We'll never share your email with anyone else.
  </p>
</div>
```

#### Benefits
- ✅ Semantic labels: "subhead" for labels, "body" for input, "footnote" for help text
- ✅ Consistent sizing: Matches iOS form patterns
- ✅ Better readability: Optimized line-heights

---

### Example 4: Alert Message

#### Before (Tailwind)
```jsx
<div className="bg-green-50 border border-green-200 rounded-lg p-4">
  <h4 className="text-base font-semibold text-green-900 mb-1">
    Success!
  </h4>
  <p className="text-sm text-green-700">
    Your changes have been saved successfully.
  </p>
</div>
```

#### After (Semantic Typography)
```jsx
<div className="bg-success-50 border border-success-200 rounded-lg p-4">
  <h4 className="text-headline text-success-900 mb-1">
    Success!
  </h4>
  <p className="text-callout text-success-700">
    Your changes have been saved successfully.
  </p>
</div>
```

#### Benefits
- ✅ Semantic colors: `success-*` instead of `green-*`
- ✅ Semantic typography: "headline" for emphasis, "callout" for message
- ✅ Consistent with design system

---

### Example 5: Article Layout

#### Before (Tailwind)
```jsx
<article className="max-w-2xl">
  <h1 className="text-4xl font-bold text-gray-900 mb-2">
    Getting Started with MorningAI
  </h1>
  <p className="text-sm text-gray-500 mb-6">
    Published on October 24, 2025 • 5 min read
  </p>
  <p className="text-base text-gray-700 leading-relaxed mb-4">
    Welcome to MorningAI! This guide will help you get started...
  </p>
</article>
```

#### After (Semantic Typography)
```jsx
<article className="max-w-2xl">
  <h1 className="text-display-3 text-gray-900 mb-2">
    Getting Started with MorningAI
  </h1>
  <p className="text-subhead text-gray-500 mb-6">
    Published on October 24, 2025 • 5 min read
  </p>
  <p className="text-body text-gray-700 leading-relaxed mb-4">
    Welcome to MorningAI! This guide will help you get started...
  </p>
</article>
```

#### Benefits
- ✅ Semantic article structure: display-3 → subhead → body
- ✅ Optimized for reading: Better line-heights and spacing
- ✅ Responsive: Can use `.text-responsive-display` for mobile

---

## Component-Specific Guidelines

### Button Component

**Status**: ✅ No migration needed

**Reason**: Button uses `text-sm font-medium` which is appropriate for UI controls.

**Recommendation**: Keep existing Tailwind classes for buttons.

```jsx
// ✅ Good - Keep as is
<Button className="text-sm font-medium">
  Click Me
</Button>

// ❌ Don't change to semantic classes
<Button className="text-callout font-medium">
  Click Me
</Button>
```

---

### Card Component

**Status**: ⚠️ Partial migration recommended

**Recommendation**: Use semantic classes for card content, keep Tailwind for layout.

```jsx
// ✅ Good - Mix semantic typography with Tailwind layout
<Card>
  <CardHeader>
    <CardTitle className="text-title-3">Card Title</CardTitle>
    <CardDescription className="text-subhead">Description</CardDescription>
  </CardHeader>
  <CardContent>
    <p className="text-body">Content goes here</p>
  </CardContent>
</Card>
```

---

### Dialog Component

**Status**: ⚠️ Partial migration recommended

**Recommendation**: Use semantic classes for dialog content.

```jsx
// ✅ Good
<Dialog>
  <DialogHeader>
    <DialogTitle className="text-title-2">Dialog Title</DialogTitle>
    <DialogDescription className="text-callout">
      This is a description of the dialog.
    </DialogDescription>
  </DialogHeader>
  <DialogContent>
    <p className="text-body">Dialog content...</p>
  </DialogContent>
</Dialog>
```

---

### Navbar Component

**Status**: ✅ No migration needed

**Reason**: Navbar uses compact UI text which is appropriate with Tailwind classes.

**Recommendation**: Keep existing Tailwind classes.

---

### Popover Component

**Status**: ⚠️ Partial migration recommended

**Recommendation**: Use semantic classes for popover content.

```jsx
// ✅ Good
<Popover>
  <PopoverTrigger>Open</PopoverTrigger>
  <PopoverContent>
    <h4 className="text-headline mb-2">Popover Title</h4>
    <p className="text-callout">Popover content...</p>
  </PopoverContent>
</Popover>
```

---

## Responsive Typography

### When to Use Responsive Classes

Use `.text-responsive-*` classes for:
- ✅ Hero sections
- ✅ Landing pages
- ✅ Marketing content
- ✅ Article titles

Don't use for:
- ❌ UI controls (buttons, inputs)
- ❌ Navigation
- ❌ Data tables
- ❌ Form labels

### Example

```jsx
// ✅ Good - Hero section
<section className="hero">
  <h1 className="text-responsive-display text-gray-900">
    Welcome to MorningAI
  </h1>
  <p className="text-responsive-body text-gray-600">
    Your AI agent platform
  </p>
</section>

// ❌ Don't use for UI
<Button className="text-responsive-body">
  Click Me
</Button>
```

---

## Migration Checklist

### For New Components

- [ ] Use semantic typography classes (`.text-title-1`, `.text-body`, etc.)
- [ ] Use semantic color classes (`.text-primary-text`, `.text-success-600`, etc.)
- [ ] Avoid hard-coded font sizes
- [ ] Test on mobile, tablet, and desktop
- [ ] Verify WCAG AA contrast ratios

### For Existing Components

- [ ] Identify components with typography (headers, paragraphs, labels)
- [ ] Replace Tailwind size classes with semantic classes
- [ ] Test visual appearance before/after
- [ ] Update Storybook stories if applicable
- [ ] Document any breaking changes

### For Refactoring

- [ ] Migrate opportunistically during feature work
- [ ] Don't refactor just for the sake of refactoring
- [ ] Prioritize high-traffic pages first
- [ ] Test thoroughly after migration

---

## Testing Guidelines

### Visual Regression Testing

1. **Take screenshots before migration**
   ```bash
   npm run test:visual -- --update-snapshots
   ```

2. **Migrate component**

3. **Compare screenshots**
   ```bash
   npm run test:visual
   ```

4. **Verify no visual regressions**

### Accessibility Testing

1. **Check contrast ratios**
   - Use axe DevTools or WebAIM Contrast Checker
   - Verify all text meets WCAG AA (4.5:1 minimum)

2. **Test with screen readers**
   - VoiceOver (macOS/iOS)
   - NVDA (Windows)
   - JAWS (Windows)

3. **Test keyboard navigation**
   - Verify focus indicators are visible
   - Check tab order is logical

### Cross-Browser Testing

Test in:
- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)
- Mobile Safari (iOS 15+)
- Chrome Mobile (Android 10+)

---

## Common Pitfalls

### ❌ Don't Mix Semantic and Size Classes

```jsx
// ❌ Bad - Conflicting classes
<h1 className="text-title-1 text-3xl">
  Title
</h1>

// ✅ Good - Use one or the other
<h1 className="text-title-1">
  Title
</h1>
```

### ❌ Don't Override Semantic Classes

```jsx
// ❌ Bad - Defeats the purpose
<p className="text-body text-2xl">
  Content
</p>

// ✅ Good - Use the right semantic class
<p className="text-title-2">
  Content
</p>
```

### ❌ Don't Use Display Classes for UI

```jsx
// ❌ Bad - Too large for UI
<Button className="text-display-1">
  Click Me
</Button>

// ✅ Good - Appropriate size
<Button className="text-sm">
  Click Me
</Button>
```

---

## FAQ

### Q: Do I need to migrate all components immediately?

**A**: No. Migration is gradual and non-breaking. Existing components work fine with Tailwind classes.

### Q: Can I mix Tailwind and semantic classes?

**A**: Yes, but avoid conflicting classes (e.g., don't use both `text-base` and `text-body` on the same element).

### Q: What about third-party components?

**A**: Keep their original classes. Only migrate components you control.

### Q: How do I handle responsive typography?

**A**: Use `.text-responsive-*` classes for content that should scale with viewport. Use fixed sizes for UI controls.

### Q: What if I need a custom font size?

**A**: Use Tailwind's arbitrary values: `text-[18px]`. But prefer semantic classes when possible.

---

## Resources

- [Typography System Documentation](./TYPOGRAPHY_SYSTEM.md)
- [Color System Documentation](./COLOR_SYSTEM.md)
- [Apple Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/typography)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)

---

## Support

For questions or issues:
1. Check this migration guide
2. Review [TYPOGRAPHY_SYSTEM.md](./TYPOGRAPHY_SYSTEM.md)
3. Ask in #design-system Slack channel
4. Create an issue in GitHub

---

**Version**: 1.0.0  
**Last Updated**: 2025-10-25  
**Maintained by**: UI/UX Team
