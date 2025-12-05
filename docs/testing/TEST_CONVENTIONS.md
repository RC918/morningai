# Frontend Testing Conventions

This document outlines the testing conventions and best practices for the MorningAI frontend applications.

## Table of Contents

- [i18n Label Patterns](#i18n-label-patterns)
- [Query Priority](#query-priority)
- [Form Field Testing](#form-field-testing)
- [SSO Button Testing](#sso-button-testing)
- [Accessibility Testing](#accessibility-testing)

## i18n Label Patterns

### Overview

When testing components that use i18n translations, we use anchored regex patterns to query form fields. This approach:

1. Works in test environments where i18n keys are displayed directly
2. Works in production-like environments with actual translations
3. Prevents false matches between similar field names

### Pattern Design Principles

```typescript
// GOOD: Anchored pattern with i18n key and translations
const EMAIL_LABEL = /^auth\.login\.email$|^Email$|^電子郵件$/i

// BAD: Unanchored pattern that could match unintended elements
const EMAIL_LABEL = /email/i  // Could match "Confirm Email", "email-helper", etc.
```

**Key principles:**

1. **Use anchors (`^` and `$`)** - Ensures exact matches only
2. **Include i18n key first** - For test environments that show raw keys
3. **Include all supported translations** - Currently English and Traditional Chinese
4. **Use case-insensitive flag (`/i`)** - Handles capitalization variations

### Using Shared Constants

Import patterns from the shared constants file:

```typescript
import {
  LOGIN_EMAIL_LABEL,
  LOGIN_PASSWORD_LABEL,
  SIGNUP_FULL_NAME_LABEL,
  SIGNUP_EMAIL_LABEL,
  SIGNUP_PASSWORD_LABEL,
  SIGNUP_CONFIRM_PASSWORD_LABEL,
} from '@/test/i18n-label-patterns'

// Usage
const emailInput = screen.getByLabelText(LOGIN_EMAIL_LABEL)
const passwordInput = screen.getByLabelText(LOGIN_PASSWORD_LABEL)
```

### Available Patterns

| Constant | Matches | Used For |
|----------|---------|----------|
| `LOGIN_EMAIL_LABEL` | auth.login.email, Email, 電子郵件 | LoginPage email field |
| `LOGIN_PASSWORD_LABEL` | auth.login.password, Password, 密碼 | LoginPage password field |
| `SIGNUP_FULL_NAME_LABEL` | auth.signup.fullName, Full Name, 姓名 | SignupPage name field |
| `SIGNUP_EMAIL_LABEL` | auth.signup.email, Email, 電子郵件 | SignupPage email field |
| `SIGNUP_PASSWORD_LABEL` | auth.signup.password, Password, 密碼 | SignupPage password field |
| `SIGNUP_CONFIRM_PASSWORD_LABEL` | auth.signup.confirmPassword, Confirm Password, 確認密碼 | SignupPage confirm password field |

### Adding New Patterns

When adding new i18n label patterns:

1. Add the constant to `src/test/i18n-label-patterns.ts`
2. Include JSDoc comment explaining the pattern
3. Follow the naming convention: `{PAGE}_{FIELD}_LABEL`
4. Include all supported language translations

## Query Priority

Follow @testing-library's [query priority](https://testing-library.com/docs/queries/about#priority):

1. **Accessible queries** (preferred)
   - `getByRole` - For elements with ARIA roles
   - `getByLabelText` - For form fields with labels
   - `getByPlaceholderText` - For inputs with placeholders
   - `getByText` - For non-interactive elements

2. **Semantic queries**
   - `getByAltText` - For images
   - `getByTitle` - For elements with title attribute

3. **Test IDs** (last resort)
   - `getByTestId` - Only when other queries aren't possible

### Examples

```typescript
// GOOD: Query by accessible role
const submitButton = screen.getByRole('button', { name: /submit/i })

// GOOD: Query by label for form fields
const emailInput = screen.getByLabelText(LOGIN_EMAIL_LABEL)

// ACCEPTABLE: Query by href for links
const forgotPasswordLink = container.querySelector('a[href="/forgot-password"]')

// AVOID: Query by class or implementation details
const button = container.querySelector('.submit-btn')  // Don't do this
```

## Form Field Testing

### Standard Test Structure

```typescript
describe('Form Interaction', () => {
  it('should update email field on change', async () => {
    const { user } = renderComponent()
    const emailInput = screen.getByLabelText(LOGIN_EMAIL_LABEL)
    
    await user.clear(emailInput)
    await user.type(emailInput, 'test@example.com')
    
    expect(emailInput).toHaveValue('test@example.com')
  })
})
```

### Key Practices

1. **Use `userEvent` over `fireEvent`** - More realistic user interactions
2. **Clear fields before typing** - Ensures predictable state
3. **Use async/await** - `userEvent` methods are asynchronous
4. **Test both rendering and interaction** - Separate test cases

## SSO Button Testing

SSO buttons should have proper `aria-label` attributes for accessibility:

```typescript
// Query SSO buttons by aria-label
const googleButton = screen.getByRole('button', { name: /google/i })
const appleButton = screen.getByRole('button', { name: /apple/i })
const githubButton = screen.getByRole('button', { name: /github/i })

// Verify accessible names
expect(googleButton).toHaveAccessibleName()
```

## Accessibility Testing

### Form Structure Tests

```typescript
it('should have proper form structure', () => {
  const { container } = renderComponent()
  
  // Form should exist
  const form = container.querySelector('form')
  expect(form).toBeInTheDocument()
  
  // All required inputs should be accessible by label
  const emailInput = screen.getByLabelText(LOGIN_EMAIL_LABEL)
  expect(emailInput).toHaveAttribute('required')
})
```

### Checklist

- [ ] All form fields have associated labels
- [ ] Required fields have `required` attribute
- [ ] Interactive elements have accessible names
- [ ] Focus order is logical
- [ ] Error messages are announced to screen readers

## Mock Setup

### Standard Mocks

```typescript
// Mock AppleInput to render accessible label
vi.mock('@/components/ui/apple-input', () => ({
  AppleInput: ({ label, ...props }: { label?: string; [key: string]: any }) => (
    <div>
      {label && <label htmlFor={props.id}>{label}</label>}
      <input {...props} />
    </div>
  )
}))

// Mock framer-motion to avoid animation issues
vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }) => <div {...props}>{children}</div>
  },
  AnimatePresence: ({ children }) => <>{children}</>,
  useReducedMotion: () => true
}))
```

## File Organization

```
src/
├── components/
│   └── __tests__/
│       ├── LoginPage.test.tsx
│       └── SignupPage.test.tsx
├── test/
│   ├── i18n-label-patterns.ts  # Shared i18n regex patterns
│   ├── setup.ts                 # Vitest setup
│   └── vitest-matchers.d.ts     # Custom matcher types
```

## Related Resources

- [@testing-library/react Documentation](https://testing-library.com/docs/react-testing-library/intro/)
- [Vitest Documentation](https://vitest.dev/)
- [WAI-ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/)
