# Apple Live Activity System

## Overview

The Apple Live Activity system provides iOS-style real-time activity notifications that display ongoing tasks, progress updates, and quick actions. This component replicates the native iOS Live Activities experience with smooth animations, expandable views, and interactive elements.

## Design Philosophy

### iOS Live Activities Principles

1. **Real-Time Updates**: Activities update dynamically to show current progress and status
2. **Compact & Expandable**: Start with minimal information, expand for details
3. **Glanceable Information**: Key information visible at a glance
4. **Quick Actions**: Perform actions without opening the app
5. **Contextual Relevance**: Show activities that matter in the moment

### Visual Design

- **Glassmorphism**: Frosted glass effect with backdrop blur
- **Rounded Corners**: 24px border radius for soft, modern look
- **Depth & Shadow**: Multi-layer shadows for floating appearance
- **Smooth Animations**: Spring-based animations for natural feel
- **Color Variants**: Semantic colors for different activity states

## Component Architecture

### Core Components

```jsx
import { AppleLiveActivity } from '@/components/ui/apple-live-activity'

// Provider wraps your app
<AppleLiveActivity.Provider position="top">
  <YourApp />
</AppleLiveActivity.Provider>

// Use the hook to control activities
const { addActivity, updateActivity, dismissActivity } = AppleLiveActivity.useLiveActivity()
```

### Activity Structure

```typescript
interface LiveActivityConfig {
  id?: string                    // Unique identifier (auto-generated if not provided)
  title: string                  // Main title
  subtitle?: string              // Secondary text
  icon?: React.ReactNode | string // Icon component or emoji
  progress?: number              // Progress percentage (0-100)
  status?: string                // Status text
  variant?: 'default' | 'primary' | 'success' | 'warning' | 'error'
  expandable?: boolean           // Can be expanded (default: true)
  metadata?: Record<string, string> // Key-value pairs shown when expanded
  actions?: Array<{
    id: string
    label: string
    variant: 'primary' | 'secondary'
    onPress: () => void
  }>
}
```

## Usage Examples

### Basic Activity

```jsx
const { addActivity } = AppleLiveActivity.useLiveActivity()

addActivity({
  title: 'Download in Progress',
  subtitle: 'document.pdf',
  icon: <Download />,
  progress: 45,
  status: '2.3 MB of 5.1 MB'
})
```

### Activity with Actions

```jsx
addActivity({
  title: 'Now Playing',
  subtitle: 'Summer Breeze - Artist Name',
  icon: '🎵',
  expandable: true,
  actions: [
    {
      id: 'pause',
      label: 'Pause',
      variant: 'secondary',
      onPress: () => pauseMusic()
    },
    {
      id: 'next',
      label: 'Next',
      variant: 'primary',
      onPress: () => nextTrack()
    }
  ]
})
```

### Activity with Metadata

```jsx
addActivity({
  title: 'Timer Running',
  subtitle: 'Focus Session',
  icon: <Timer />,
  progress: 60,
  status: '15:00 remaining',
  expandable: true,
  metadata: {
    'Started': '2:30 PM',
    'Duration': '25 minutes',
    'Type': 'Deep Work'
  },
  actions: [
    {
      id: 'stop',
      label: 'Stop',
      variant: 'secondary',
      onPress: () => stopTimer()
    },
    {
      id: 'pause',
      label: 'Pause',
      variant: 'primary',
      onPress: () => pauseTimer()
    }
  ]
})
```

### Updating Activities

```jsx
const { id, update } = addActivity({
  title: 'Downloading',
  progress: 0
})

// Update progress
setInterval(() => {
  update({
    progress: currentProgress,
    status: `${currentProgress}% complete`
  })
}, 1000)

// Update on completion
update({
  title: 'Download Complete',
  progress: 100,
  variant: 'success',
  actions: [
    {
      id: 'open',
      label: 'Open',
      variant: 'primary',
      onPress: () => openFile()
    }
  ]
})
```

### Manual Control

```jsx
const { addActivity, updateActivity, dismissActivity } = AppleLiveActivity.useLiveActivity()

// Add with custom ID
const activityId = 'download-123'
addActivity({
  id: activityId,
  title: 'Download Starting',
  progress: 0
})

// Update by ID
updateActivity(activityId, {
  progress: 50,
  status: 'Halfway there'
})

// Dismiss by ID
dismissActivity(activityId)
```

## Variants

### Default
Neutral gray background for general activities.

```jsx
addActivity({
  title: 'Background Task',
  variant: 'default'
})
```

### Primary
Blue background for primary actions or important activities.

```jsx
addActivity({
  title: 'Charging',
  variant: 'primary'
})
```

### Success
Green background for completed or successful activities.

```jsx
addActivity({
  title: 'Download Complete',
  variant: 'success'
})
```

### Warning
Orange background for warnings or attention-needed activities.

```jsx
addActivity({
  title: 'Low Storage',
  variant: 'warning'
})
```

### Error
Red background for errors or failed activities.

```jsx
addActivity({
  title: 'Download Failed',
  variant: 'error'
})
```

## Features

### Expandable Views

Activities can be expanded to show additional information and actions:

- **Compact View**: Shows title, subtitle, icon, progress, and status
- **Expanded View**: Reveals metadata and action buttons
- **Toggle**: Click anywhere on the activity to expand/collapse
- **Disable**: Set `expandable: false` to prevent expansion

### Progress Tracking

Display real-time progress with animated progress bars:

```jsx
addActivity({
  title: 'Processing',
  progress: 75,  // 0-100
  status: '3 of 4 items complete'
})
```

- Progress bar animates smoothly with spring physics
- Percentage displayed below the bar
- Automatically clamps values between 0-100

### Quick Actions

Add interactive buttons for common actions:

```jsx
actions: [
  {
    id: 'primary-action',
    label: 'Continue',
    variant: 'primary',  // White background
    onPress: () => handleContinue()
  },
  {
    id: 'secondary-action',
    label: 'Cancel',
    variant: 'secondary',  // Translucent background
    onPress: () => handleCancel()
  }
]
```

### Metadata Display

Show detailed information when expanded:

```jsx
metadata: {
  'File Size': '150 MB',
  'Download Speed': '5.2 MB/s',
  'Time Remaining': '30 seconds',
  'Source': 'cloud.example.com'
}
```

### Icon Support

Use Lucide icons or emojis:

```jsx
// Lucide icon
icon: <Download />

// Emoji
icon: '🎵'

// Custom component
icon: <CustomIcon className="w-5 h-5" />
```

## Provider Configuration

### Position

Control where activities appear:

```jsx
// Top of screen (default)
<AppleLiveActivity.Provider position="top">

// Bottom of screen
<AppleLiveActivity.Provider position="bottom">
```

### Maximum Activities

The system automatically limits to 3 concurrent activities (MAX_ACTIVITIES). When a 4th activity is added, the oldest is automatically removed.

## Animations

### Entry Animation
- Fade in with scale up
- Slide down from top
- Spring physics for natural feel

### Exit Animation
- Fade out with scale down
- Slide up
- Smooth spring transition

### Progress Animation
- Width animates with spring physics
- Smooth percentage updates
- No jarring jumps

### Expand/Collapse
- Height animates automatically
- Content fades in/out
- Spring-based timing

### Haptic Feedback
- Light haptic on expand/collapse
- Medium haptic on dismiss
- Light haptic on action press

## Accessibility

### ARIA Attributes

```jsx
// Container
aria-live="polite"
aria-atomic="false"

// Buttons
aria-label="Expand"
aria-label="Collapse"
aria-label="Dismiss"
```

### Keyboard Support

- Activities are focusable
- Buttons are keyboard accessible
- Proper tab order maintained

### Screen Readers

- Announces new activities
- Reads activity updates
- Describes button actions

## Best Practices

### When to Use Live Activities

✅ **Good Use Cases:**
- File downloads/uploads
- Media playback
- Timers and countdowns
- Background tasks
- Delivery tracking
- Charging status
- Processing operations

❌ **Avoid For:**
- Static notifications
- One-time alerts (use Toast instead)
- Non-time-sensitive information
- Promotional messages

### Activity Lifecycle

1. **Start**: Add activity when task begins
2. **Update**: Continuously update progress and status
3. **Complete**: Update to success variant with completion actions
4. **Dismiss**: Auto-dismiss after completion or user dismissal

### Progress Updates

```jsx
// Good: Smooth, frequent updates
const { id, update } = addActivity({ title: 'Processing', progress: 0 })

const interval = setInterval(() => {
  const newProgress = calculateProgress()
  update({ progress: newProgress })
  
  if (newProgress >= 100) {
    clearInterval(interval)
    update({ variant: 'success', title: 'Complete' })
  }
}, 100)

// Bad: Infrequent, jumpy updates
update({ progress: 0 })
setTimeout(() => update({ progress: 100 }), 5000)
```

### Action Design

- **Primary Action**: Most important or expected action (white background)
- **Secondary Actions**: Alternative or cancel actions (translucent)
- **Limit Actions**: Maximum 2-3 actions for clarity
- **Clear Labels**: Use action verbs (Open, Pause, Cancel)

### Content Guidelines

- **Title**: Short, descriptive (2-4 words)
- **Subtitle**: Additional context (filename, artist, etc.)
- **Status**: Current state or time remaining
- **Metadata**: Detailed information for expanded view

## Technical Implementation

### Spring Animation

Uses Framer Motion spring physics:

```jsx
transition={{
  type: 'spring',
  stiffness: 500,
  damping: 30,
  mass: 1
}}
```

### Glassmorphism

```jsx
className="backdrop-blur-xl bg-gray-900/90"
```

### Shadow System

```jsx
style={{
  boxShadow: '0 10px 40px rgba(0, 0, 0, 0.2), 0 2px 8px rgba(0, 0, 0, 0.1)'
}}
```

### Context Management

```jsx
const LiveActivityContext = createContext(null)

export const useAppleLiveActivity = () => {
  const context = useContext(LiveActivityContext)
  if (!context) {
    throw new Error('useAppleLiveActivity must be used within AppleLiveActivityProvider')
  }
  return context
}
```

## Performance Considerations

### Optimization Tips

1. **Limit Updates**: Don't update more than 10 times per second
2. **Batch Updates**: Combine multiple property updates
3. **Cleanup**: Dismiss completed activities promptly
4. **Memory**: Maximum 3 concurrent activities enforced

### Update Throttling

```jsx
import { throttle } from 'lodash'

const throttledUpdate = throttle((progress) => {
  updateActivity(id, { progress })
}, 100)
```

## Testing

### Unit Tests

```jsx
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AppleLiveActivity } from './apple-live-activity'

it('displays and updates activity', async () => {
  const { addActivity, updateActivity } = renderWithProvider()
  
  const { id } = addActivity({
    title: 'Download',
    progress: 0
  })
  
  expect(screen.getByText('Download')).toBeInTheDocument()
  
  updateActivity(id, { progress: 50 })
  
  await waitFor(() => {
    expect(screen.getByText('50%')).toBeInTheDocument()
  })
})
```

### Storybook Stories

Comprehensive stories available in `apple-live-activity.stories.tsx`:

- Default activity
- With actions
- With metadata
- All variants
- Live progress updates
- Multiple activities
- Position variants

## Migration Guide

### From Toast to Live Activity

**Use Toast for:**
- One-time notifications
- Success/error messages
- Brief confirmations

**Use Live Activity for:**
- Ongoing processes
- Progress tracking
- Interactive updates

### Example Migration

```jsx
// Before: Toast
toast.success('Download started')

// After: Live Activity
const { id, update } = addActivity({
  title: 'Downloading',
  subtitle: 'file.pdf',
  progress: 0
})

// Update progress
onProgress((p) => update({ progress: p }))

// On complete
onComplete(() => {
  update({
    title: 'Download Complete',
    variant: 'success',
    actions: [{ id: 'open', label: 'Open', variant: 'primary' }]
  })
})
```

## Related Components

- **AppleToast**: For brief notifications
- **AppleModal**: For focused interactions
- **AppleSheet**: For bottom-up content
- **AppleButton**: For consistent button styling

## Resources

- [iOS Live Activities HIG](https://developer.apple.com/design/human-interface-guidelines/live-activities)
- [ActivityKit Documentation](https://developer.apple.com/documentation/activitykit)
- [Framer Motion](https://www.framer.com/motion/)

## Changelog

### Version 1.0.0 (2025-10-26)
- Initial implementation
- Expandable views
- Progress tracking
- Quick actions
- Metadata display
- Multiple variants
- Spring animations
- Haptic feedback
- Comprehensive tests
- Storybook stories
