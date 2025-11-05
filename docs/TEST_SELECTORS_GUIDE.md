# Test Selectors Guide - data-testid Best Practices

## Overview

This guide establishes conventions for adding stable test selectors (`data-testid` attributes) to UI components for reliable automated testing.

**Status:** 📋 DOCUMENTATION (Implementation in future PR)  
**Priority:** Medium (Week 2-3)

---

## Why data-testid?

### Problems with Current Selectors

❌ **Fragile selectors currently used:**
```javascript
// Motion tests currently use:
page.click('a[href="/dashboard"]')  // Breaks if href changes
page.locator('button:has-text("Open")')  // Breaks if text changes or i18n
```

✅ **Stable selectors with data-testid:**
```javascript
// Recommended approach:
page.click('[data-testid="nav-dashboard-link"]')
page.click('[data-testid="modal-open-button"]')
```

### Benefits

1. **Decouples tests from implementation** - Text, classes, and structure can change
2. **Explicit test contract** - Clear which elements are test targets
3. **i18n-safe** - Works across all languages
4. **Performance** - Faster than complex CSS selectors
5. **Accessibility-friendly** - Doesn't interfere with ARIA attributes

---

## Naming Conventions

### Format

```
data-testid="{component}-{element}-{type}"
```

### Examples

```tsx
// Navigation
<a href="/dashboard" data-testid="nav-dashboard-link">Dashboard</a>

// Modal
<Dialog data-testid="modal-container">
  <Button data-testid="modal-confirm-button">Confirm</Button>
</Dialog>

// Form
<input type="email" data-testid="form-login-email-input" />
<button type="submit" data-testid="form-login-submit-button">Sign In</button>
```

---

## Implementation Priority

### Phase 1: Critical User Flows (Week 2)

Add `data-testid` to elements used in motion tests:

1. **Navigation links** - Dashboard, Settings, etc.
2. **Modal triggers** - Any button that opens a modal
3. **Form submissions** - Login, signup, settings forms
4. **Primary actions** - Save, Delete, Confirm buttons

### Phase 2: Common Components (Week 3)

Add to shared components in `@morningai/shared-ui`:

1. Button component
2. Input component
3. Modal/Dialog component
4. Card component
5. Table component

### Phase 3: Full Coverage (Week 4+)

Add to all interactive elements across both apps.

---

## Best Practices

### DO ✅

1. **Add to interactive elements** - Buttons, links, inputs
2. **Add to test targets** - Any element your tests need to find
3. **Use descriptive names** - Clear what the element does
4. **Be consistent** - Follow naming conventions
5. **Add to containers** - Helps scope queries

### DON'T ❌

1. **Don't use for styling** - Use classes instead
2. **Don't duplicate IDs** - Each testid should be unique per page
3. **Don't use dynamic values** - Except for list indices
4. **Don't rely on text content** - Use testids instead

---

**Last Updated:** November 5, 2025  
**Owner:** UI/UX Strategy Director  
**Status:** Documentation complete, implementation pending
