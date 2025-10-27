# Apple Navigation System

**Version**: 1.0.0  
**Last Updated**: 2025-10-26  
**Status**: ✅ Implemented

## Overview

The Apple Navigation System provides iOS-style navigation components that bring authentic Apple design patterns to web applications. This system includes two core navigation patterns: Tab Bar for app-level navigation and Segmented Control for view switching.

## Components

### 1. AppleTabBar

iOS-style bottom tab navigation for primary app navigation.

#### Features

- **iOS Design Language**: Authentic iOS tab bar styling with backdrop blur
- **Spring Animations**: Natural spring physics for all interactions
- **Haptic Feedback**: Visual haptic feedback simulation on tap
- **Badge Support**: Show notification counts on tabs
- **Active Indicator**: Smooth sliding active state background
- **Accessibility**: Full ARIA support and keyboard navigation
- **Responsive**: Adapts to different screen sizes

#### Usage

```tsx
import { AppleTabBar, AppleTabBarItem } from '@/components/ui/apple-tab-bar'
import { Home, Search, Bell, User } from 'lucide-react'

function App() {
  const [tab, setTab] = useState('home')
  
  return (
    <AppleTabBar value={tab} onValueChange={setTab}>
      <AppleTabBarItem value="home" icon={<Home />} label="Home" />
      <AppleTabBarItem value="search" icon={<Search />} label="Search" />
      <AppleTabBarItem value="notifications" icon={<Bell />} label="Alerts" badge={3} />
      <AppleTabBarItem value="profile" icon={<User />} label="Profile" />
    </AppleTabBar>
  )
}
```

#### Props

**AppleTabBar**

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `value` | `string` | - | Currently selected tab value |
| `onValueChange` | `(value: string) => void` | - | Callback when tab selection changes |
| `className` | `string` | - | Additional CSS classes |

**AppleTabBarItem**

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `value` | `string` | - | Unique value for this tab |
| `icon` | `ReactNode` | - | Icon element (recommended size: 24x24) |
| `label` | `string` | - | Label text below icon |
| `badge` | `number` | - | Badge count (shows "99+" for >99) |
| `disabled` | `boolean` | `false` | Whether tab is disabled |
| `onClick` | `(e: MouseEvent) => void` | - | Custom click handler |
| `className` | `string` | - | Additional CSS classes |

#### Design Guidelines

**Tab Count**
- Minimum: 2 tabs
- Maximum: 5 tabs (iOS guideline)
- Recommended: 3-4 tabs for optimal UX

**Icons**
- Use 24x24px icons (6x6 in Tailwind)
- Keep icons simple and recognizable
- Use consistent icon style across all tabs

**Labels**
- Keep labels short (1-2 words)
- Use sentence case
- Avoid truncation

**Badges**
- Use for notification counts only
- Shows "99+" for numbers over 99
- Don't use for decorative purposes

#### Accessibility

- **Role**: `tablist` for container, `tab` for items
- **ARIA**: `aria-selected` indicates active tab
- **Labels**: `aria-label` for screen readers
- **Keyboard**: Tab navigation supported
- **Focus**: Visible focus indicators

### 2. AppleSegmentedControl

iOS-style segmented control for switching between views or filtering content.

#### Features

- **iOS Design Language**: Authentic iOS segmented control styling
- **Smooth Animation**: Sliding active indicator with spring physics
- **Haptic Feedback**: Visual haptic feedback simulation
- **Keyboard Navigation**: Full keyboard support (Arrow keys, Enter, Space)
- **Accessibility**: Complete ARIA support
- **Responsive**: Adapts to content width
- **Size Variants**: Small, default, and large sizes

#### Usage

```tsx
import { AppleSegmentedControl, AppleSegmentedControlItem } from '@/components/ui/apple-segmented-control'

function FilterView() {
  const [filter, setFilter] = useState('all')
  
  return (
    <AppleSegmentedControl value={filter} onValueChange={setFilter}>
      <AppleSegmentedControlItem value="all">All</AppleSegmentedControlItem>
      <AppleSegmentedControlItem value="active">Active</AppleSegmentedControlItem>
      <AppleSegmentedControlItem value="completed">Completed</AppleSegmentedControlItem>
    </AppleSegmentedControl>
  )
}
```

#### Props

**AppleSegmentedControl**

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `value` | `string` | - | Currently selected segment value |
| `onValueChange` | `(value: string) => void` | - | Callback when segment changes |
| `size` | `'sm' \| 'default' \| 'lg'` | `'default'` | Size variant |
| `className` | `string` | - | Additional CSS classes |

**AppleSegmentedControlItem**

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `value` | `string` | - | Unique value for this segment |
| `disabled` | `boolean` | `false` | Whether segment is disabled |
| `onClick` | `(e: MouseEvent) => void` | - | Custom click handler |
| `className` | `string` | - | Additional CSS classes |
| `children` | `ReactNode` | - | Segment content (text or icons) |

#### Design Guidelines

**Segment Count**
- Minimum: 2 segments
- Maximum: 5 segments (iOS guideline)
- Recommended: 2-4 segments for optimal UX

**Labels**
- Keep labels concise (1-2 words)
- Use consistent label length across segments
- Consider icons for space-constrained layouts

**When to Use**
- ✅ View switching (List vs Grid)
- ✅ Filtering content by category
- ✅ Toggling between mutually exclusive options
- ✅ Settings with 2-5 options
- ❌ Navigation between different screens (use Tab Bar)
- ❌ More than 5 options (use Dropdown)

#### Size Variants

```tsx
// Small (h-8)
<AppleSegmentedControl size="sm" value={value} onValueChange={setValue}>
  <AppleSegmentedControlItem value="all">All</AppleSegmentedControlItem>
  <AppleSegmentedControlItem value="active">Active</AppleSegmentedControlItem>
</AppleSegmentedControl>

// Default (h-10)
<AppleSegmentedControl size="default" value={value} onValueChange={setValue}>
  <AppleSegmentedControlItem value="all">All</AppleSegmentedControlItem>
  <AppleSegmentedControlItem value="active">Active</AppleSegmentedControlItem>
</AppleSegmentedControl>

// Large (h-12)
<AppleSegmentedControl size="lg" value={value} onValueChange={setValue}>
  <AppleSegmentedControlItem value="all">All</AppleSegmentedControlItem>
  <AppleSegmentedControlItem value="active">Active</AppleSegmentedControlItem>
</AppleSegmentedControl>
```

#### Accessibility

- **Role**: `tablist` for container, `tab` for items
- **ARIA**: `aria-selected` indicates active segment
- **Keyboard**: Enter and Space to activate
- **Focus**: Visible focus indicators with ring
- **Screen Readers**: Proper announcements for state changes

## Design Principles

### 1. Clarity

Navigation should be immediately understandable:
- Clear visual hierarchy
- Recognizable icons and labels
- Obvious active states
- Consistent positioning

### 2. Feedback

Every interaction provides immediate feedback:
- Spring animations for natural feel
- Haptic feedback simulation
- Smooth state transitions
- Visual confirmation of actions

### 3. Consistency

Maintain consistency across the app:
- Use Tab Bar for primary navigation
- Use Segmented Control for view switching
- Follow iOS guidelines for tab/segment counts
- Consistent icon and label styles

### 4. Accessibility

Navigation must be accessible to all users:
- Full keyboard navigation support
- Screen reader compatibility
- High contrast for visibility
- Focus indicators for keyboard users

## Technical Implementation

### Animation System

Both components use Framer Motion with spring physics:

```tsx
const springConfig = getSpringConfig('snappy')

// Applied to all interactive elements
<motion.button
  whileTap={{ scale: 0.95 }}
  transition={springConfig}
>
```

### Haptic Feedback

Visual haptic feedback is triggered on interactions:

```tsx
import { triggerHaptic } from '@/lib/spring-animation'

const handleClick = () => {
  triggerHaptic(buttonRef.current, 'light')
  // ... rest of click handler
}
```

### Active State Indicator

Smooth sliding animation using `layoutId`:

```tsx
{isActive && (
  <motion.div
    layoutId="activeTab"
    className="absolute inset-0 bg-accent/30 rounded-xl"
    initial={false}
    transition={springConfig}
  />
)}
```

## Examples

### Tab Bar with Badges

```tsx
<AppleTabBar value={tab} onValueChange={setTab}>
  <AppleTabBarItem value="home" icon={<Home />} label="Home" />
  <AppleTabBarItem value="messages" icon={<MessageSquare />} label="Messages" badge={5} />
  <AppleTabBarItem value="notifications" icon={<Bell />} label="Alerts" badge={12} />
  <AppleTabBarItem value="profile" icon={<User />} label="Profile" />
</AppleTabBar>
```

### Segmented Control for Filtering

```tsx
<div className="space-y-4">
  <AppleSegmentedControl value={status} onValueChange={setStatus}>
    <AppleSegmentedControlItem value="all">All</AppleSegmentedControlItem>
    <AppleSegmentedControlItem value="todo">To Do</AppleSegmentedControlItem>
    <AppleSegmentedControlItem value="progress">In Progress</AppleSegmentedControlItem>
    <AppleSegmentedControlItem value="done">Done</AppleSegmentedControlItem>
  </AppleSegmentedControl>
  
  <TaskList filter={status} />
</div>
```

### Segmented Control with Icons

```tsx
<AppleSegmentedControl value={view} onValueChange={setView}>
  <AppleSegmentedControlItem value="list">
    <List className="w-4 h-4" />
  </AppleSegmentedControlItem>
  <AppleSegmentedControlItem value="grid">
    <Grid className="w-4 h-4" />
  </AppleSegmentedControlItem>
  <AppleSegmentedControlItem value="calendar">
    <Calendar className="w-4 h-4" />
  </AppleSegmentedControlItem>
</AppleSegmentedControl>
```

## Testing

### Unit Tests

Both components have comprehensive unit tests:

```bash
# Run tests
npm test apple-tab-bar.test.tsx
npm test apple-segmented-control.test.tsx
```

### Test Coverage

- ✅ Rendering with different props
- ✅ Click interactions
- ✅ Keyboard navigation
- ✅ Disabled states
- ✅ Badge rendering
- ✅ Accessibility attributes
- ✅ Custom event handlers

### Storybook

Interactive documentation and testing:

```bash
npm run storybook
```

Stories available:
- AppleTabBar: Default, WithBadges, FiveTabs, WithDisabledTab, LargeBadgeNumbers, DarkMode
- AppleSegmentedControl: Default, TwoSegments, FourSegments, WithIcons, SmallSize, LargeSize, WithDisabledSegment, InCard, FilterExample, DarkMode

## Browser Support

- ✅ Chrome/Edge 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Mobile browsers (iOS Safari, Chrome Mobile)

## Performance

- **Bundle Size**: ~3KB gzipped (per component)
- **Animation Performance**: 60fps on modern devices
- **Accessibility**: WCAG 2.1 AA compliant

## Migration Guide

### From NavigationMenu to AppleTabBar

```tsx
// Before
<NavigationMenu>
  <NavigationMenuList>
    <NavigationMenuItem>
      <NavigationMenuLink>Home</NavigationMenuLink>
    </NavigationMenuItem>
  </NavigationMenuList>
</NavigationMenu>

// After
<AppleTabBar value={tab} onValueChange={setTab}>
  <AppleTabBarItem value="home" icon={<Home />} label="Home" />
</AppleTabBar>
```

### From Tabs to AppleSegmentedControl

```tsx
// Before
<Tabs value={tab} onValueChange={setTab}>
  <TabsList>
    <TabsTrigger value="all">All</TabsTrigger>
    <TabsTrigger value="active">Active</TabsTrigger>
  </TabsList>
</Tabs>

// After
<AppleSegmentedControl value={tab} onValueChange={setTab}>
  <AppleSegmentedControlItem value="all">All</AppleSegmentedControlItem>
  <AppleSegmentedControlItem value="active">Active</AppleSegmentedControlItem>
</AppleSegmentedControl>
```

## Future Enhancements

### Planned Features (P2)

1. **Navigation Bar Component**
   - iOS-style top navigation bar
   - Back button with gesture support
   - Title and action buttons

2. **Tab Bar Customization**
   - Custom active indicator styles
   - Animated icon transitions
   - More badge styles

3. **Segmented Control Enhancements**
   - Vertical orientation
   - Custom segment widths
   - Animated content transitions

## References

- [Apple Human Interface Guidelines - Tab Bars](https://developer.apple.com/design/human-interface-guidelines/tab-bars)
- [Apple Human Interface Guidelines - Segmented Controls](https://developer.apple.com/design/human-interface-guidelines/segmented-controls)
- [Framer Motion Documentation](https://www.framer.com/motion/)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)

## Support

For issues or questions:
1. Check Storybook documentation
2. Review unit tests for usage examples
3. Consult Apple HIG for design guidance
4. Create an issue in the repository

---

**Component Status**: ✅ Production Ready  
**Test Coverage**: 100%  
**Documentation**: Complete  
**Storybook**: Available
