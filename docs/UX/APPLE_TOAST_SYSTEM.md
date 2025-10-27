# Apple Dynamic Toast System

## Overview

The Apple Dynamic Toast system is an iOS-inspired notification component that provides a premium, native-feeling toast experience with Dynamic Island-style design, spring animations, and gesture support.

## Features

### 🎨 Design
- **Dynamic Island Style**: Pill-shaped toasts with rounded corners and backdrop blur
- **iOS Materials**: Translucent backgrounds with backdrop-filter blur effects
- **Variant Support**: Success, Error, Warning, Info, and Default variants
- **Dark Mode**: Full dark mode support with appropriate color adjustments

### ⚡ Animations
- **Spring Physics**: Natural, bouncy animations using Framer Motion springs
- **Smooth Transitions**: Enter/exit animations with proper easing
- **Layout Animations**: Automatic layout shifts when toasts are added/removed

### 👆 Interactions
- **Drag to Dismiss**: Swipe up to dismiss toasts
- **Click to Close**: X button for manual dismissal
- **Auto-dismiss**: Configurable duration (default 5000ms)
- **Persistent Toasts**: Set duration to 0 for toasts that don't auto-dismiss

### ♿ Accessibility
- **ARIA Live Regions**: Proper screen reader announcements
- **Keyboard Navigation**: Accessible close buttons
- **Semantic HTML**: Proper roles and labels

## Installation

The AppleToast system is already installed in the project. To use it:

```jsx
import { AppleToastProvider, useAppleToast } from '@/components/ui/apple-toast'
```

## Usage

### 1. Wrap your app with AppleToastProvider

```jsx
import { AppleToastProvider } from '@/components/ui/apple-toast'

function App() {
  return (
    <AppleToastProvider>
      {/* Your app content */}
    </AppleToastProvider>
  )
}
```

### 2. Use the toast hook in your components

```jsx
import { useAppleToast } from '@/components/ui/apple-toast'

function MyComponent() {
  const toast = useAppleToast()

  const handleSuccess = () => {
    toast.success('Success!', 'Your changes have been saved.')
  }

  const handleError = () => {
    toast.error('Error!', 'Something went wrong.')
  }

  return (
    <div>
      <button onClick={handleSuccess}>Save</button>
      <button onClick={handleError}>Trigger Error</button>
    </div>
  )
}
```

## API Reference

### useAppleToast()

Returns an object with the following methods:

#### `toast(options)`
Show a toast with custom options.

```jsx
toast({
  title: 'Custom Toast',
  description: 'This is a custom message',
  variant: 'default', // 'success' | 'error' | 'warning' | 'info' | 'default'
  duration: 5000 // milliseconds, 0 for persistent
})
```

Or use the shorthand:
```jsx
toast('Simple message')
```

#### `success(title, description?)`
Show a success toast.

```jsx
toast.success('Success!', 'Operation completed successfully.')
```

#### `error(title, description?)`
Show an error toast.

```jsx
toast.error('Error!', 'Something went wrong.')
```

#### `warning(title, description?)`
Show a warning toast.

```jsx
toast.warning('Warning!', 'This action cannot be undone.')
```

#### `info(title, description?)`
Show an info toast.

```jsx
toast.info('Info', 'New features are available.')
```

#### `dismiss(id)`
Dismiss a specific toast by ID.

```jsx
const { id } = toast.success('Success!')
// Later...
toast.dismiss(id)
```

#### `dismissAll()`
Dismiss all active toasts.

```jsx
toast.dismissAll()
```

### Return Value

All toast methods return an object with:
- `id`: Unique identifier for the toast
- `dismiss()`: Function to dismiss this specific toast

```jsx
const myToast = toast.success('Success!')
// Later...
myToast.dismiss()
```

## Examples

### Basic Usage

```jsx
function SaveButton() {
  const toast = useAppleToast()
  const [saving, setSaving] = useState(false)

  const handleSave = async () => {
    setSaving(true)
    try {
      await saveData()
      toast.success('Saved!', 'Your changes have been saved.')
    } catch (error) {
      toast.error('Error!', error.message)
    } finally {
      setSaving(false)
    }
  }

  return <button onClick={handleSave}>Save</button>
}
```

### Persistent Toast

```jsx
function ImportantNotification() {
  const toast = useAppleToast()

  const showImportantMessage = () => {
    toast.toast({
      title: 'Important!',
      description: 'Please read this carefully.',
      duration: 0 // Won't auto-dismiss
    })
  }

  return <button onClick={showImportantMessage}>Show Important</button>
}
```

### Multiple Toasts

```jsx
function BatchOperations() {
  const toast = useAppleToast()

  const handleBatchOperation = async () => {
    const operations = [op1, op2, op3]
    
    for (const op of operations) {
      try {
        await op()
        toast.success(`${op.name} completed`)
      } catch (error) {
        toast.error(`${op.name} failed`, error.message)
      }
    }
  }

  return <button onClick={handleBatchOperation}>Run Batch</button>
}
```

### Custom Duration

```jsx
function QuickNotification() {
  const toast = useAppleToast()

  const showQuickMessage = () => {
    toast.toast({
      title: 'Quick message',
      duration: 2000 // 2 seconds
    })
  }

  return <button onClick={showQuickMessage}>Show Quick</button>
}
```

## Design Tokens

The toast system uses the following design tokens from `@/lib/design-tokens`:

- `colors`: For variant colors and backgrounds
- `spacing`: For padding and gaps

## Variants

### Success
- **Color**: Green (`bg-green-500/90`)
- **Icon**: CheckCircle2
- **Use**: Successful operations, confirmations

### Error
- **Color**: Red (`bg-red-500/90`)
- **Icon**: AlertCircle
- **Use**: Errors, failures, critical issues

### Warning
- **Color**: Orange (`bg-orange-500/90`)
- **Icon**: AlertTriangle
- **Use**: Warnings, cautions, important notices

### Info
- **Color**: Blue (`bg-blue-500/90`)
- **Icon**: Info
- **Use**: Information, tips, updates

### Default
- **Color**: Gray (`bg-gray-900/90`)
- **Icon**: None
- **Use**: General messages, neutral notifications

## Styling

### Customization

The toast component uses Tailwind CSS classes and can be customized through:

1. **Variant Colors**: Modify the `toastVariants` object in `apple-toast.jsx`
2. **Animation**: Adjust spring parameters in the motion config
3. **Positioning**: Change the container position in the provider
4. **Size**: Modify `min-w-[320px] max-w-[420px]` classes

### Dark Mode

Dark mode is automatically supported through Tailwind's `dark:` prefix:

```jsx
// Light mode: bg-green-500/90
// Dark mode: dark:bg-green-600/90
```

## Accessibility

### Screen Readers

The toast container has proper ARIA attributes:
- `aria-live="polite"`: Announces toasts to screen readers
- `aria-atomic="false"`: Only announces new content

### Keyboard Navigation

- Close buttons are keyboard accessible
- Proper focus management
- Semantic HTML structure

### Best Practices

1. **Keep messages concise**: Short titles and descriptions
2. **Use appropriate variants**: Match the variant to the message type
3. **Don't overuse**: Limit simultaneous toasts to avoid overwhelming users
4. **Provide context**: Include helpful descriptions when needed
5. **Consider duration**: Longer messages need longer durations

## Migration from Sonner

If you're currently using Sonner toasts, you can gradually migrate:

### Before (Sonner)
```jsx
import { toast } from 'sonner'

toast.success('Success!')
toast.error('Error!')
```

### After (AppleToast)
```jsx
import { useAppleToast } from '@/components/ui/apple-toast'

function MyComponent() {
  const toast = useAppleToast()
  
  toast.success('Success!')
  toast.error('Error!')
}
```

### Coexistence

Both systems can coexist during migration:
- Sonner: For legacy code
- AppleToast: For new features

## Performance

### Optimizations

1. **Animation Budget**: Uses Framer Motion's optimized animations
2. **Layout Animations**: Efficient layout shifts with `layout` prop
3. **Cleanup**: Automatic cleanup of dismissed toasts
4. **Memoization**: Context value is memoized to prevent unnecessary re-renders

### Best Practices

1. **Limit Simultaneous Toasts**: Keep to 3-5 maximum
2. **Use Appropriate Durations**: Don't make users wait too long
3. **Batch Operations**: Group related notifications when possible

## Testing

Unit tests are available in `apple-toast.test.tsx`:

```bash
npm test apple-toast.test.tsx
```

## Storybook

Interactive examples are available in Storybook:

```bash
npm run storybook
```

Navigate to **UI/AppleToast** to see all variants and examples.

## Technical Details

### Dependencies

- **React**: Context API for state management
- **Framer Motion**: Spring animations and gestures
- **Lucide React**: Icons
- **Tailwind CSS**: Styling

### File Structure

```
src/components/ui/
├── apple-toast.jsx          # Main component
├── apple-toast.test.tsx     # Unit tests
└── apple-toast.stories.tsx  # Storybook stories
```

### Animation Configuration

```javascript
transition={{
  type: 'spring',
  stiffness: 500,  // Higher = snappier
  damping: 30,     // Higher = less bouncy
  mass: 1          // Weight of the element
}}
```

### Gesture Configuration

```javascript
drag="y"
dragConstraints={{ top: 0, bottom: 0 }}
dragElastic={0.2}
onDragEnd={(e, { offset, velocity }) => {
  if (offset.y < -50 || velocity.y < -500) {
    onDismiss(id)
  }
}}
```

## Troubleshooting

### Toast not showing

1. Ensure `AppleToastProvider` wraps your component
2. Check that you're using `useAppleToast()` hook correctly
3. Verify no z-index conflicts

### Animations not working

1. Check that Framer Motion is installed
2. Verify `prefers-reduced-motion` settings
3. Check browser compatibility

### Styling issues

1. Ensure Tailwind CSS is configured correctly
2. Check for CSS conflicts
3. Verify backdrop-filter support in browser

## Browser Support

- **Modern Browsers**: Full support (Chrome, Firefox, Safari, Edge)
- **Backdrop Filter**: Requires modern browser (fallback to solid background)
- **Spring Animations**: Requires JavaScript enabled

## Future Enhancements

Potential improvements for future versions:

1. **Sound Effects**: Optional haptic/sound feedback
2. **Action Buttons**: Add action buttons to toasts
3. **Progress Indicators**: Show progress for long operations
4. **Toast Queue**: Advanced queue management
5. **Position Options**: Support different positions (top, bottom, corners)
6. **Custom Icons**: Allow custom icons per toast
7. **Rich Content**: Support for custom JSX content

## Related Components

- **AppleButton**: iOS-style buttons
- **AppleInput**: iOS-style inputs
- **Modal/Sheet**: For more complex notifications

## Support

For issues or questions:
1. Check this documentation
2. Review Storybook examples
3. Check unit tests for usage patterns
4. Consult the team

---

**Last Updated**: 2025-10-26  
**Version**: 1.0.0  
**Author**: UI/UX Team
