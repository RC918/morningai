# Pagination Accessibility Pattern

## Overview

This document describes the accessibility pattern used for pagination controls in the MorningAI platform, specifically implemented in the `AgentExecutionLogs` component. This pattern should be followed for all future pagination implementations to ensure consistent accessibility across the platform.

## Implementation

### Semantic Structure

Pagination controls should be wrapped in a `<nav>` element with appropriate ARIA attributes:

```tsx
<nav 
  aria-label={t('pagination.label')}
  aria-describedby={paginationDescId}
>
  {/* Pagination controls */}
</nav>
```

### Key Features

#### 1. Semantic HTML
- Use `<nav>` element to identify pagination as a navigation landmark
- Use `<button>` elements for pagination controls (not `<a>` links)
- Provide clear, descriptive labels for all interactive elements

#### 2. ARIA Attributes

**Navigation Label** (`aria-label`):
- Identifies the navigation region for screen readers
- Should be localized (e.g., "Pagination" in English, "分頁導航" in Chinese)

**Description** (`aria-describedby`):
- Links to the element showing current page range (e.g., "Showing 1-50 of 100")
- Provides context about what the pagination controls affect

**Controls** (`aria-controls`):
- Points to the ID of the content being paginated (e.g., the table)
- Helps screen readers understand the relationship between controls and content

**Live Region** (`aria-live="polite"`, `aria-atomic="true"`):
- Applied to the page indicator element
- Announces page changes to screen readers without interrupting the user

#### 3. Dynamic IDs

Use React's `useId()` hook to generate unique IDs for multi-instance rendering:

```tsx
const tableId = useId()
const paginationDescId = useId()
```

This ensures that if multiple instances of the component are rendered on the same page, each will have unique IDs and proper ARIA relationships.

#### 4. Button States

Pagination buttons should have proper disabled states:

```tsx
<Button
  disabled={pagination.page === 1}
  aria-label={t('pagination.previous')}
  aria-controls={tableId}
>
  Previous
</Button>
```

### Complete Example

```tsx
const MyPaginatedComponent = () => {
  const { t } = useTranslation()
  const tableId = useId()
  const paginationDescId = useId()
  
  return (
    <>
      <Table id={tableId}>
        {/* Table content */}
      </Table>
      
      {pagination.total_pages > 1 && (
        <nav 
          aria-label={t('pagination.label')}
          aria-describedby={paginationDescId}
        >
          <p id={paginationDescId}>
            {t('pagination.showing', {
              start: (pagination.page - 1) * pagination.page_size + 1,
              end: Math.min(pagination.page * pagination.page_size, pagination.total_items),
              total: pagination.total_items
            })}
          </p>
          
          <div>
            <Button
              onClick={() => handlePageChange(pagination.page - 1)}
              disabled={pagination.page === 1}
              aria-label={t('pagination.previous')}
              aria-controls={tableId}
            >
              Previous
            </Button>
            
            <span 
              aria-live="polite"
              aria-atomic="true"
            >
              {t('pagination.page', {
                current: pagination.page,
                total: pagination.total_pages
              })}
            </span>
            
            <Button
              onClick={() => handlePageChange(pagination.page + 1)}
              disabled={pagination.page === pagination.total_pages}
              aria-label={t('pagination.next')}
              aria-controls={tableId}
            >
              Next
            </Button>
          </div>
        </nav>
      )}
    </>
  )
}
```

## Testing

### E2E Testing Considerations

When writing E2E tests for pagination:

1. **Use data attributes for stability**: Always include `data-testid` attributes for reliable element selection
2. **Test with data attributes first**: Use `data-current` and `data-total` attributes as the primary assertions
3. **Locale-agnostic text verification**: When verifying visible text, check for page numbers rather than full localized strings to prevent flakiness when locale changes

Example:

```typescript
// ✅ Good: Stable data attribute assertions
await expect(pageIndicator).toHaveAttribute('data-current', '1')
await expect(pageIndicator).toHaveAttribute('data-total', '2')

// ✅ Good: Locale-agnostic text verification
const pageText = await pageIndicator.textContent()
expect(pageText).toContain('1')
expect(pageText).toContain('2')

// ❌ Avoid: Locale-specific text assertions (causes flakiness)
await expect(pageIndicator).toContainText('Page 1 of 2')
```

### Accessibility Testing

Use automated accessibility testing tools to verify:

1. **Storybook A11y Tests**: Run `npm run test-storybook` to check for violations
2. **axe-core**: Verify no violations in browser console
3. **Screen Reader Testing**: Manually test with NVDA/JAWS (Windows) or VoiceOver (macOS)

Expected screen reader announcements:
- When entering pagination: "Pagination navigation, Showing 1-50 of 100"
- When clicking next: "Page 2 of 10" (polite announcement)
- When clicking previous: "Page 1 of 10" (polite announcement)

## Localization

Ensure all pagination-related strings are properly localized:

```json
{
  "pagination": {
    "label": "Pagination",
    "showing": "Showing {{start}}-{{end}} of {{total}}",
    "page": "Page {{current}} of {{total}}",
    "previous": "Previous",
    "next": "Next"
  }
}
```

## References

- [ARIA Authoring Practices Guide - Pagination](https://www.w3.org/WAI/ARIA/apg/patterns/pagination/)
- [WebAIM - Creating Accessible Tables](https://webaim.org/techniques/tables/)
- [React useId Hook](https://react.dev/reference/react/useId)

## Related Components

- `AgentExecutionLogs` (handoff/20250928/40_App/owner-console/src/components/AgentExecutionLogs.tsx)
- `Table` component (packages/shared-ui/src/components/ui/table.tsx)
- `Button` component (packages/shared-ui/src/components/ui/button.tsx)

## Version History

- **v1.0** (2025-11-23): Initial pattern documentation based on PR #1482 P2 improvements
