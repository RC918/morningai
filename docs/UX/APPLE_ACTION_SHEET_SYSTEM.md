# Apple Action Sheet System

## Overview

The Apple Action Sheet component provides an iOS-style bottom sheet for presenting action options to users. It follows Apple's Human Interface Guidelines and delivers a native iOS experience with smooth animations, haptic feedback, and accessibility support.

**Component Location**: `src/components/ui/apple-action-sheet.tsx`

### Key Features

- ✅ iOS-style bottom slide-in animation
- ✅ Glassmorphism backdrop with blur effect
- ✅ Action list with icons and labels
- ✅ Destructive action highlighting
- ✅ Disabled action support
- ✅ Custom cancel button label
- ✅ Haptic feedback integration
- ✅ Keyboard navigation (Escape to close)
- ✅ Focus management and restoration
- ✅ ARIA accessibility attributes
- ✅ TypeScript type safety
- ✅ Framer Motion animations
- ✅ Context API for global state

---

## Component Architecture

### Provider Pattern

The component uses React Context API for global state management:

```typescript
<AppleActionSheet.Provider>
  <YourApp />
</AppleActionSheet.Provider>
```

### Hook Usage

Access action sheet functionality via the custom hook:

```typescript
const { show, hide, isVisible } = AppleActionSheet.useActionSheet()
```

---

## Type Definitions

### ActionSheetAction

```typescript
type ActionSheetAction = {
  id: string                    // Unique identifier
  label: string                 // Action label text
  icon?: React.ReactNode        // Optional icon component
  destructive?: boolean         // Red styling for dangerous actions
  disabled?: boolean            // Disable action interaction
  onSelect: () => void          // Callback when action is selected
}
```

### ActionSheetOptions

```typescript
type ActionSheetOptions = {
  title?: string                // Optional title
  message?: string              // Optional description
  actions: ActionSheetAction[]  // Array of actions
  cancelLabel?: string          // Custom cancel button text (default: "Cancel")
  onCancel?: () => void         // Callback when cancelled
}
```

---

## Usage Examples

### Basic Usage

```typescript
import { AppleActionSheet } from '@/components/ui/apple-action-sheet'

function App() {
  return (
    <AppleActionSheet.Provider>
      <YourApp />
    </AppleActionSheet.Provider>
  )
}

function MyComponent() {
  const { show } = AppleActionSheet.useActionSheet()

  const handleShowActions = () => {
    show({
      title: 'Choose an action',
      message: 'Select one of the options below',
      actions: [
        {
          id: '1',
          label: 'Edit',
          onSelect: () => console.log('Edit selected')
        },
        {
          id: '2',
          label: 'Share',
          onSelect: () => console.log('Share selected')
        },
        {
          id: '3',
          label: 'Delete',
          destructive: true,
          onSelect: () => console.log('Delete selected')
        }
      ]
    })
  }

  return (
    <button onClick={handleShowActions}>
      Show Actions
    </button>
  )
}
```

### With Icons

```typescript
import { Edit, Share2, Trash2 } from 'lucide-react'

const { show } = AppleActionSheet.useActionSheet()

show({
  title: 'File Actions',
  actions: [
    {
      id: '1',
      label: 'Edit',
      icon: <Edit className="w-5 h-5" />,
      onSelect: () => handleEdit()
    },
    {
      id: '2',
      label: 'Share',
      icon: <Share2 className="w-5 h-5" />,
      onSelect: () => handleShare()
    },
    {
      id: '3',
      label: 'Delete',
      icon: <Trash2 className="w-5 h-5" />,
      destructive: true,
      onSelect: () => handleDelete()
    }
  ]
})
```

### Destructive Confirmation

```typescript
show({
  title: 'Delete Item',
  message: 'This action cannot be undone. Are you sure you want to delete this item?',
  actions: [
    {
      id: '1',
      label: 'Delete',
      destructive: true,
      onSelect: () => {
        // Perform deletion
        console.log('Item deleted')
      }
    }
  ],
  cancelLabel: 'Keep Item',
  onCancel: () => console.log('Deletion cancelled')
})
```

### With Disabled Actions

```typescript
show({
  title: 'Document Actions',
  message: 'Some actions are not available for this document',
  actions: [
    {
      id: '1',
      label: 'Edit',
      onSelect: () => handleEdit()
    },
    {
      id: '2',
      label: 'Share',
      disabled: true,  // Grayed out and non-interactive
      onSelect: () => handleShare()
    },
    {
      id: '3',
      label: 'Download',
      disabled: true,
      onSelect: () => handleDownload()
    }
  ]
})
```

### Programmatic Control

```typescript
const { show, hide, isVisible } = AppleActionSheet.useActionSheet()

// Show action sheet
show({ actions: [...] })

// Hide action sheet programmatically
hide()

// Check visibility
console.log('Action sheet visible:', isVisible)
```

---

## Design Patterns

### Visual Design

**Glassmorphism Effect**:
```css
background: white/95% with backdrop-blur-xl
border: white/20% with rounded-2xl corners
shadow: 2xl for depth
```

**Action Buttons**:
- Default: Blue text (`text-blue-600`)
- Destructive: Red text (`text-red-600`) with warning icon
- Disabled: 50% opacity with cursor-not-allowed
- Hover: Light gray background
- Active: Darker gray background

**Cancel Button**:
- Separate card below actions
- Bold text styling
- Same blue color as default actions
- Slightly larger spacing

### Animation Specifications

**Slide-In Animation**:
```typescript
initial: { y: '100%', opacity: 0 }
animate: { y: 0, opacity: 1 }
exit: { y: '100%', opacity: 0 }
transition: {
  type: 'spring',
  stiffness: 500,
  damping: 30,
  mass: 1
}
```

**Backdrop Animation**:
```typescript
initial: { opacity: 0 }
animate: { opacity: 1 }
exit: { opacity: 0 }
transition: { duration: 0.2 }
```

**Action Stagger**:
- Each action animates with 50ms delay
- Creates cascading entrance effect
- Cancel button has additional 100ms delay

**Button Interactions**:
- Hover: `scale: 1.02`
- Tap: `scale: 0.98`
- Smooth spring transitions

---

## Accessibility

### ARIA Attributes

```typescript
<div
  role="dialog"
  aria-modal="true"
  aria-labelledby="action-sheet-title"
  aria-describedby="action-sheet-message"
>
```

### Keyboard Navigation

- **Escape**: Close action sheet
- **Tab**: Navigate between actions
- **Enter/Space**: Select focused action
- **Shift+Tab**: Reverse navigation

### Focus Management

1. **On Open**: Focus moves to first action button
2. **Tab Trap**: Focus stays within action sheet
3. **On Close**: Focus returns to trigger element
4. **Disabled Actions**: Skipped in tab order

### Screen Reader Support

- Proper heading hierarchy
- Descriptive button labels
- Action state announcements
- Modal dialog semantics

---

## Performance Considerations

### Optimization Strategies

1. **useCallback Hooks**:
   ```typescript
   const show = useCallback((options) => { ... }, [])
   const hide = useCallback(() => { ... }, [])
   ```

2. **AnimatePresence**:
   - Handles exit animations efficiently
   - Removes from DOM after animation
   - Mode: "wait" for single instance

3. **Event Handlers**:
   - Debounced backdrop clicks
   - Optimized keyboard listeners
   - Cleanup on unmount

4. **Conditional Rendering**:
   - Only renders when visible
   - Lazy initialization
   - Minimal re-renders

### Bundle Size

- Component: ~8KB (minified)
- Dependencies: Framer Motion, Lucide React
- Tree-shakeable exports

---

## Testing

### Test Coverage

**21 unit tests** covering:

1. **Provider and Context** (2 tests)
   - Context provision
   - Error handling outside provider

2. **Action Sheet Display** (4 tests)
   - Show/hide functionality
   - Cancel button display
   - Custom cancel label

3. **Actions** (5 tests)
   - Action selection
   - Auto-close after selection
   - Disabled action handling
   - Destructive action styling
   - Multiple actions rendering

4. **Cancel Button** (2 tests)
   - Close on cancel
   - onCancel callback

5. **Backdrop** (1 test)
   - Close on backdrop click

6. **Keyboard Navigation** (2 tests)
   - Escape key handling
   - Focus management

7. **Accessibility** (2 tests)
   - ARIA attributes
   - Focus restoration

8. **Optional Props** (3 tests)
   - Without title
   - Without message
   - With icons

### Running Tests

```bash
npm run test -- apple-action-sheet.test.tsx
```

### Test Example

```typescript
it('calls onSelect when action is clicked', async () => {
  const onSelect = vi.fn()
  const { show } = AppleActionSheet.useActionSheet()

  show({
    actions: [{
      id: '1',
      label: 'Test Action',
      onSelect
    }]
  })

  await user.click(screen.getByText('Test Action'))
  expect(onSelect).toHaveBeenCalledTimes(1)
})
```

---

## Integration Examples

### Delete Confirmation

```typescript
const handleDelete = () => {
  show({
    title: 'Delete Item',
    message: 'This action cannot be undone.',
    actions: [
      {
        id: 'delete',
        label: 'Delete',
        destructive: true,
        onSelect: async () => {
          await deleteItem(itemId)
          toast.success('Item deleted')
        }
      }
    ],
    cancelLabel: 'Cancel',
    onCancel: () => console.log('Deletion cancelled')
  })
}
```

### Share Sheet

```typescript
import { MessageSquare, Mail, Copy } from 'lucide-react'

const handleShare = () => {
  show({
    title: 'Share',
    message: 'Choose how you want to share this content',
    actions: [
      {
        id: 'message',
        label: 'Message',
        icon: <MessageSquare className="w-5 h-5" />,
        onSelect: () => shareViaMessage()
      },
      {
        id: 'mail',
        label: 'Mail',
        icon: <Mail className="w-5 h-5" />,
        onSelect: () => shareViaEmail()
      },
      {
        id: 'copy',
        label: 'Copy Link',
        icon: <Copy className="w-5 h-5" />,
        onSelect: () => {
          navigator.clipboard.writeText(shareUrl)
          toast.success('Link copied')
        }
      }
    ]
  })
}
```

### Context Menu Replacement

```typescript
const handleContextMenu = (e: React.MouseEvent) => {
  e.preventDefault()
  
  show({
    title: 'Options',
    actions: [
      {
        id: 'edit',
        label: 'Edit',
        icon: <Edit className="w-5 h-5" />,
        onSelect: () => handleEdit()
      },
      {
        id: 'duplicate',
        label: 'Duplicate',
        icon: <Copy className="w-5 h-5" />,
        onSelect: () => handleDuplicate()
      },
      {
        id: 'delete',
        label: 'Delete',
        icon: <Trash2 className="w-5 h-5" />,
        destructive: true,
        onSelect: () => handleDelete()
      }
    ]
  })
}
```

---

## Browser Compatibility

### Supported Browsers

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+
- ✅ iOS Safari 14+
- ✅ Chrome Android 90+

### Required Features

- CSS backdrop-filter (for blur effect)
- Framer Motion support
- ES6+ JavaScript features
- CSS Grid and Flexbox

### Fallbacks

- Backdrop blur degrades gracefully
- Animations work without GPU acceleration
- Touch events fallback to mouse events

---

## Troubleshooting

### Common Issues

**Issue**: Action sheet doesn't appear
```typescript
// ❌ Wrong: Missing Provider
<MyComponent />

// ✅ Correct: Wrap with Provider
<AppleActionSheet.Provider>
  <MyComponent />
</AppleActionSheet.Provider>
```

**Issue**: Hook error outside provider
```typescript
// Error: useAppleActionSheet must be used within AppleActionSheetProvider

// Solution: Ensure component is inside Provider
```

**Issue**: Actions not closing sheet
```typescript
// ❌ Wrong: Manually calling hide()
onSelect: () => {
  doSomething()
  hide()  // Not needed
}

// ✅ Correct: Sheet auto-closes
onSelect: () => {
  doSomething()  // Sheet closes automatically
}
```

**Issue**: Backdrop not clickable
```typescript
// Check z-index conflicts
// Ensure no overlapping fixed elements
// Verify backdrop is rendered
```

---

## Future Enhancements

### Planned Features

1. **Swipe to Dismiss**
   - Drag gesture support
   - Velocity-based closing
   - Elastic resistance

2. **Action Groups**
   - Grouped actions with headers
   - Visual separators
   - Collapsible sections

3. **Custom Styling**
   - Theme variants
   - Custom colors
   - Size options (compact, regular, large)

4. **Animations**
   - Custom animation presets
   - Configurable timing
   - Direction options (bottom, top, side)

5. **Advanced Features**
   - Search/filter actions
   - Nested action sheets
   - Action history
   - Keyboard shortcuts per action

---

## Related Components

- **AppleSheet**: General-purpose bottom sheet with custom content
- **AppleModal**: Full-screen modal dialogs
- **AppleToast**: Temporary notifications
- **AppleSpotlight**: Global search interface

---

## Resources

### Design References

- [Apple Human Interface Guidelines - Action Sheets](https://developer.apple.com/design/human-interface-guidelines/action-sheets)
- [iOS 17 Design Patterns](https://developer.apple.com/design/)
- [Material Design - Bottom Sheets](https://m3.material.io/components/bottom-sheets)

### Technical Documentation

- [Framer Motion Documentation](https://www.framer.com/motion/)
- [React Context API](https://react.dev/reference/react/useContext)
- [ARIA Dialog Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/)

---

## Changelog

### Version 1.0.0 (2025-10-26)

**Initial Release**
- ✅ Core action sheet functionality
- ✅ iOS-style animations
- ✅ Destructive action support
- ✅ Disabled action handling
- ✅ Custom cancel label
- ✅ Icon support
- ✅ Haptic feedback
- ✅ Full accessibility
- ✅ 21 unit tests (100% passing)
- ✅ 12 Storybook stories
- ✅ TypeScript support
- ✅ Comprehensive documentation

---

## License

Part of the MorningAI Design System. Internal use only.

---

## Support

For questions or issues:
- Check Storybook for interactive examples
- Review test cases for usage patterns
- Consult related component documentation
- Contact the UI/UX team

---

**Last Updated**: 2025-10-26  
**Component Version**: 1.0.0  
**Maintainer**: UI/UX Team
