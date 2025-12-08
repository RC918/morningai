# Apple Control Center System

## Overview

The Apple Control Center system provides an iOS-style control panel for quick access to system controls and settings. This component implements the authentic iOS Control Center experience with grid layout, long-press actions, glassmorphism effects, and haptic feedback.

## Component Architecture

### Core Components

1. **AppleControlCenterProvider** - Context provider for state management
2. **ControlCenterPanel** - Main panel component with grid layout
3. **ControlCard** - Individual control card with interactions
4. **useAppleControlCenter** - Hook for accessing control center context

## Features

### Grid Layout System

The Control Center uses a flexible grid layout that supports multiple control sizes:

- **1x1**: Standard single control (e.g., Wi-Fi, Bluetooth)
- **2x1**: Wide control (e.g., Music player, Brightness slider)
- **1x2**: Tall control (e.g., Volume slider)
- **2x2**: Large control (e.g., Now Playing with album art)

### Control Variants

Five visual variants for different control states:

- **default**: Standard control appearance
- **primary**: Blue accent (Wi-Fi, Bluetooth)
- **success**: Green accent (success states)
- **warning**: Orange accent (warning states)
- **danger**: Red accent (critical states)

### Interactive Features

1. **Tap**: Quick toggle or action
2. **Long Press**: Expand to show additional actions (500ms threshold)
3. **Haptic Feedback**: Light feedback on press, medium on long press
4. **Backdrop Dismiss**: Click outside to close

### Visual Design

- **Glassmorphism**: Backdrop blur with semi-transparent backgrounds
- **Spring Animations**: Smooth transitions with iOS-style physics (stiffness: 500, damping: 30)
- **Rounded Corners**: 20px border radius for cards
- **Shadows**: Subtle shadows for depth

## Usage

### Basic Setup

```tsx
import { AppleControlCenter } from '@/components/ui/apple-control-center'
import { Wifi, Bluetooth } from 'lucide-react'

function App() {
  const controls = [
    {
      id: 'wifi',
      title: 'Wi-Fi',
      subtitle: 'Home Network',
      icon: <Wifi />,
      size: '1x1',
      variant: 'primary',
      active: true,
      onPress: () => console.log('Wi-Fi toggled')
    },
    {
      id: 'bluetooth',
      title: 'Bluetooth',
      subtitle: 'AirPods Pro',
      icon: <Bluetooth />,
      size: '1x1',
      variant: 'primary',
      active: true,
      onPress: () => console.log('Bluetooth toggled')
    }
  ]

  return (
    <AppleControlCenter.Provider controls={controls}>
      <YourApp />
    </AppleControlCenter.Provider>
  )
}
```

### Using the Hook

```tsx
function ControlCenterButton() {
  const { toggle, isOpen } = AppleControlCenter.useControlCenter()

  return (
    <button onClick={toggle}>
      {isOpen ? 'Close' : 'Open'} Control Center
    </button>
  )
}
```

### Control with Actions

```tsx
const wifiControl = {
  id: 'wifi',
  title: 'Wi-Fi',
  subtitle: 'Home Network',
  icon: <Wifi />,
  size: '1x1',
  variant: 'primary',
  active: true,
  actions: [
    {
      id: 'home',
      label: 'Home Network',
      onPress: () => connectToNetwork('home')
    },
    {
      id: 'office',
      label: 'Office Network',
      onPress: () => connectToNetwork('office')
    },
    {
      id: 'settings',
      label: 'Wi-Fi Settings',
      onPress: () => openSettings('wifi')
    }
  ],
  onLongPress: () => console.log('Wi-Fi long pressed')
}
```

### Control with Value Display

```tsx
const brightnessControl = {
  id: 'brightness',
  title: 'Brightness',
  icon: <Sun />,
  size: '1x2',
  variant: 'default',
  value: '75%',
  onPress: () => adjustBrightness()
}
```

## Type Definitions

### Control

```typescript
interface Control {
  id: string                    // Unique identifier
  title: string                 // Control title
  subtitle?: string             // Optional subtitle
  icon: React.ReactNode         // Icon component
  size?: ControlSize            // '1x1' | '2x1' | '1x2' | '2x2'
  variant?: ControlVariant      // 'default' | 'primary' | 'success' | 'warning' | 'danger'
  active?: boolean              // Active state
  value?: string | number       // Display value (e.g., '75%')
  actions?: ControlAction[]     // Long-press actions
  onPress?: () => void          // Tap handler
  onLongPress?: () => void      // Long press handler
}
```

### ControlAction

```typescript
interface ControlAction {
  id: string                    // Unique identifier
  label: string                 // Action label
  icon?: React.ReactNode        // Optional icon
  onPress: () => void           // Action handler
}
```

### Context Value

```typescript
interface ControlCenterContextValue {
  isOpen: boolean               // Panel open state
  open: () => void              // Open panel
  close: () => void             // Close panel
  toggle: () => void            // Toggle panel
  controls: Control[]           // Current controls
  setControls: (controls: Control[]) => void  // Update controls
}
```

## Design Patterns

### Control Organization

Organize controls by frequency of use and logical grouping:

1. **Top Row**: Most frequently used (Wi-Fi, Bluetooth, Airplane Mode)
2. **Middle Rows**: Media controls, brightness, volume
3. **Bottom Rows**: Less frequent controls (Timer, Calculator, Camera)

### Size Guidelines

- Use **1x1** for simple toggles
- Use **2x1** for controls with sliders or additional info
- Use **1x2** for vertical sliders (volume, brightness)
- Use **2x2** for rich media controls (music player with album art)

### Variant Usage

- **primary**: Connectivity controls (Wi-Fi, Bluetooth, Cellular)
- **success**: Positive actions (Connected, Enabled)
- **warning**: Attention needed (Low Battery, Limited Connectivity)
- **danger**: Critical states (Airplane Mode, Do Not Disturb)
- **default**: Standard controls

## Animation Specifications

### Spring Physics

```typescript
const springConfig = {
  type: 'spring',
  stiffness: 500,
  damping: 30
}
```

### Transitions

- **Panel Slide**: 0.3s spring animation from top-right
- **Card Press**: Scale 0.95 on press
- **Actions Expand**: Fade in with scale animation
- **Backdrop**: Fade in/out 0.2s

## Accessibility

### Keyboard Navigation

- **Escape**: Close control center
- **Tab**: Navigate between controls
- **Enter/Space**: Activate control
- **Arrow Keys**: Navigate grid (future enhancement)

### Screen Readers

- Descriptive labels for all controls
- Active state announcements
- Action availability announcements
- Close button with aria-label

### ARIA Attributes

```tsx
<button
  role="button"
  aria-label="Wi-Fi Control"
  aria-pressed={active}
  aria-expanded={hasActions && isExpanded}
>
```

## Performance Considerations

### Optimization Strategies

1. **Memoization**: Control cards are memoized to prevent unnecessary re-renders
2. **Lazy Loading**: Actions panel only renders when expanded
3. **Event Delegation**: Single event listener for backdrop clicks
4. **CSS Transforms**: Use transform for animations (GPU-accelerated)

### Best Practices

- Limit controls to 8-12 for optimal performance
- Use SVG icons for crisp rendering at all sizes
- Implement virtualization for large control sets (future enhancement)
- Debounce rapid state changes

## Testing

### Unit Tests

The component includes 31+ comprehensive unit tests covering:

- Provider and context functionality
- Control rendering and interactions
- Size and variant applications
- Active/inactive states
- Long-press actions
- Multiple controls
- Backdrop interactions
- Accessibility features
- Context methods (open, close, toggle)

### Test Coverage

```bash
npm run test apple-control-center.test.tsx
```

### Storybook Stories

Interactive stories demonstrating:

- Default control center
- Different control sizes
- All variants
- Long-press actions
- Mixed layouts
- Dark mode example
- Minimal controls
- Interactive demo

View in Storybook:

```bash
npm run storybook
```

## Integration Examples

### Dashboard Integration

```tsx
import { AppleControlCenter } from '@/components/ui/apple-control-center'
import { useSystemControls } from '@/hooks/useSystemControls'

function Dashboard() {
  const { controls } = useSystemControls()

  return (
    <AppleControlCenter.Provider controls={controls}>
      <DashboardHeader />
      <DashboardContent />
    </AppleControlCenter.Provider>
  )
}
```

### Settings Page Integration

```tsx
function SettingsPage() {
  const { toggle } = AppleControlCenter.useControlCenter()

  return (
    <div>
      <h1>Settings</h1>
      <button onClick={toggle}>
        Open Control Center
      </button>
    </div>
  )
}
```

### Custom Control Hook

```tsx
function useWifiControl() {
  const [isConnected, setIsConnected] = useState(false)
  const [network, setNetwork] = useState('Home')

  return {
    id: 'wifi',
    title: 'Wi-Fi',
    subtitle: isConnected ? network : 'Off',
    icon: <Wifi />,
    size: '1x1' as const,
    variant: 'primary' as const,
    active: isConnected,
    actions: [
      {
        id: 'home',
        label: 'Home Network',
        onPress: () => {
          setNetwork('Home')
          setIsConnected(true)
        }
      },
      {
        id: 'office',
        label: 'Office Network',
        onPress: () => {
          setNetwork('Office')
          setIsConnected(true)
        }
      }
    ],
    onPress: () => setIsConnected(!isConnected)
  }
}
```

## Browser Compatibility

- **Chrome**: 90+
- **Firefox**: 88+
- **Safari**: 14+
- **Edge**: 90+

### Required Features

- CSS backdrop-filter (for glassmorphism)
- CSS Grid
- Framer Motion (React 19+)
- Touch events (for mobile)

## Future Enhancements

### Planned Features

1. **Drag to Reorder**: Allow users to customize control layout
2. **Custom Control Sizes**: Support for 3x3, 4x4 grids
3. **Control Groups**: Collapsible groups of related controls
4. **Widgets**: Rich interactive widgets (weather, calendar)
5. **Themes**: Light/dark mode support
6. **Persistence**: Save control layout to localStorage
7. **Keyboard Navigation**: Full keyboard support with arrow keys
8. **Gestures**: Swipe to dismiss, pinch to zoom

### API Enhancements

1. **Dynamic Controls**: Add/remove controls at runtime
2. **Control State Sync**: Sync with system state
3. **Event Emitters**: Subscribe to control events
4. **Middleware**: Intercept control actions

## Troubleshooting

### Common Issues

**Issue**: Control Center doesn't appear
- **Solution**: Ensure Provider wraps your app and controls are set

**Issue**: Long press doesn't work
- **Solution**: Verify control has `actions` array defined

**Issue**: Glassmorphism not working
- **Solution**: Check browser support for backdrop-filter

**Issue**: Animations are janky
- **Solution**: Reduce number of controls or disable animations on low-end devices

### Debug Mode

Enable debug logging:

```tsx
<AppleControlCenter.Provider controls={controls} debug>
  <App />
</AppleControlCenter.Provider>
```

## Related Components

- **AppleLiveActivity**: Dynamic Island-style notifications
- **AppleSheet**: Bottom sheet modal
- **AppleModal**: Full-screen modal
- **AppleTabBar**: Bottom navigation bar
- **AppleSegmentedControl**: Segmented control picker

## Resources

- [iOS Human Interface Guidelines - Control Center](https://developer.apple.com/design/human-interface-guidelines/control-center)
- [Framer Motion Documentation](https://www.framer.com/motion/)
- [React Context API](https://react.dev/reference/react/useContext)
- [CSS Backdrop Filter](https://developer.mozilla.org/en-US/docs/Web/CSS/backdrop-filter)

## Changelog

### Version 1.0.0 (2025-10-23)

- Initial release
- Grid layout system with 4 size options
- 5 visual variants
- Long-press actions
- Glassmorphism effects
- Haptic feedback
- Spring animations
- Comprehensive tests and stories
- Full TypeScript support
- Accessibility features

## License

MIT License - See LICENSE file for details

## Support

For issues, questions, or contributions:
- GitHub Issues: [morningai/issues](https://github.com/RC918/morningai/issues)
- Documentation: [docs/UX/](https://github.com/RC918/morningai/tree/main/docs/UX)
- Storybook: [storybook.morningai.com](https://storybook.morningai.com)
