# Apple Spotlight Search System

## Overview

The Apple Spotlight Search system provides an iOS/macOS-style universal search interface with keyboard shortcuts (Cmd+K / Ctrl+K), real-time results, recent searches, and smooth animations. This component implements the authentic Spotlight search experience with keyboard navigation, debounced search, and customizable result types.

## Component Architecture

### Core Components

1. **AppleSpotlightProvider** - Context provider for state management
2. **SpotlightPanel** - Main search panel with input and results
3. **SearchResultItem** - Individual search result component
4. **useAppleSpotlight** - Hook for accessing spotlight context

## Features

### Keyboard Shortcuts

- **Cmd+K** (macOS) / **Ctrl+K** (Windows/Linux) - Open Spotlight
- **Escape** - Close Spotlight
- **↑↓** - Navigate results
- **Enter** - Select result
- **Tab** - Focus next element

### Search Functionality

- **Real-time Search** - Debounced search with 300ms delay
- **Async Support** - Handles both sync and async search functions
- **Result Filtering** - Client-side or server-side filtering
- **Empty State** - Helpful messages when no results found

### Recent Searches

- **Auto-save** - Automatically saves successful searches
- **Configurable Limit** - Set max number of recent searches (default: 5)
- **Clear All** - One-click to clear all recent searches
- **Click to Search** - Click recent search to populate input

### Visual Design

- **Glassmorphism** - Backdrop blur with semi-transparent background
- **Spring Animations** - iOS-style physics (stiffness: 500, damping: 30)
- **Hover Effects** - Smooth hover transitions on results
- **Selected State** - Visual indicator for keyboard-selected result

## Usage

### Basic Setup

```tsx
import { AppleSpotlight } from '@/components/ui/apple-spotlight'
import { File, Folder, User } from 'lucide-react'

function App() {
  const handleSearch = (query: string) => {
    // Return search results
    return [
      {
        id: '1',
        title: 'Dashboard',
        subtitle: 'View your analytics',
        type: 'action',
        category: 'Pages',
        onSelect: () => navigate('/dashboard')
      },
      {
        id: '2',
        title: 'Settings',
        subtitle: 'Manage your account',
        type: 'setting',
        category: 'Pages',
        onSelect: () => navigate('/settings')
      }
    ]
  }

  return (
    <AppleSpotlight.Provider onSearch={handleSearch}>
      <YourApp />
    </AppleSpotlight.Provider>
  )
}
```

### Using the Hook

```tsx
function SearchButton() {
  const { toggle, isOpen } = AppleSpotlight.useSpotlight()

  return (
    <button onClick={toggle}>
      {isOpen ? 'Close' : 'Open'} Search
    </button>
  )
}
```

### Async Search

```tsx
const handleAsyncSearch = async (query: string) => {
  const response = await fetch(`/api/search?q=${query}`)
  const data = await response.json()
  
  return data.results.map(result => ({
    id: result.id,
    title: result.title,
    subtitle: result.description,
    type: result.type,
    category: result.category,
    onSelect: () => handleResultSelect(result)
  }))
}

<AppleSpotlight.Provider onSearch={handleAsyncSearch}>
  <App />
</AppleSpotlight.Provider>
```

### Custom Result Icons

```tsx
const searchResults = [
  {
    id: '1',
    title: 'project-report.pdf',
    subtitle: 'Documents/Reports',
    type: 'file',
    icon: <File className="w-4 h-4" />,
    category: 'Files',
    onSelect: () => openFile('project-report.pdf')
  },
  {
    id: '2',
    title: 'Images',
    subtitle: '245 items',
    type: 'folder',
    icon: <Folder className="w-4 h-4" />,
    category: 'Folders',
    onSelect: () => openFolder('images')
  }
]
```

### Recent Searches Configuration

```tsx
<AppleSpotlight.Provider 
  onSearch={handleSearch}
  maxRecentSearches={10}
>
  <App />
</AppleSpotlight.Provider>
```

## Type Definitions

### SearchResult

```typescript
interface SearchResult {
  id: string                      // Unique identifier
  title: string                   // Result title
  subtitle?: string               // Optional subtitle/description
  type: SearchResultType          // Result type
  icon?: React.ReactNode          // Custom icon (optional)
  category?: string               // Result category
  onSelect: () => void            // Selection handler
  metadata?: Record<string, unknown>  // Additional metadata
}
```

### SearchResultType

```typescript
type SearchResultType = 
  | 'recent'      // Recent search
  | 'suggestion'  // Search suggestion
  | 'file'        // File result
  | 'folder'      // Folder result
  | 'user'        // User result
  | 'setting'     // Setting result
  | 'action'      // Action result
```

### SpotlightContextValue

```typescript
interface SpotlightContextValue {
  isOpen: boolean                 // Panel open state
  open: () => void                // Open panel
  close: () => void               // Close panel
  toggle: () => void              // Toggle panel
  searchQuery: string             // Current search query
  setSearchQuery: (query: string) => void  // Update query
  results: SearchResult[]         // Current results
  setResults: (results: SearchResult[]) => void  // Update results
  recentSearches: string[]        // Recent search queries
  addRecentSearch: (query: string) => void  // Add recent search
  clearRecentSearches: () => void // Clear all recent searches
}
```

## Design Patterns

### Result Organization

Organize results by relevance and type:

1. **Exact Matches** - Show exact title matches first
2. **Partial Matches** - Show partial matches next
3. **Category Grouping** - Group by category (Pages, Files, Users, etc.)
4. **Recent Items** - Show recently accessed items

### Search Strategies

#### Client-Side Search

```tsx
const handleClientSearch = (query: string) => {
  const allResults = getAllResults()
  return allResults.filter(result =>
    result.title.toLowerCase().includes(query.toLowerCase()) ||
    result.subtitle?.toLowerCase().includes(query.toLowerCase())
  )
}
```

#### Server-Side Search

```tsx
const handleServerSearch = async (query: string) => {
  const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`)
  return await response.json()
}
```

#### Hybrid Search

```tsx
const handleHybridSearch = async (query: string) => {
  // Quick local results
  const localResults = getLocalResults(query)
  
  // Fetch remote results
  const remoteResults = await fetchRemoteResults(query)
  
  // Merge and deduplicate
  return mergeResults(localResults, remoteResults)
}
```

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

- **Panel Slide**: 0.3s spring animation from top
- **Result Fade In**: Staggered fade in with 50ms delay
- **Hover Scale**: Scale 1.02 on hover
- **Press Scale**: Scale 0.98 on press
- **Backdrop**: Fade in/out 0.2s

## Accessibility

### Keyboard Navigation

- **Cmd+K / Ctrl+K**: Open Spotlight
- **Escape**: Close Spotlight
- **↑↓**: Navigate results
- **Enter**: Select result
- **Tab**: Focus management

### Screen Readers

- Descriptive labels for all interactive elements
- Result count announcements
- Selection state announcements
- Search status updates

### ARIA Attributes

```tsx
<input
  role="searchbox"
  aria-label="Search"
  aria-autocomplete="list"
  aria-controls="search-results"
  aria-activedescendant={selectedResultId}
/>

<div
  role="listbox"
  id="search-results"
  aria-label="Search results"
>
  <div
    role="option"
    aria-selected={isSelected}
  >
    {result.title}
  </div>
</div>
```

## Performance Considerations

### Optimization Strategies

1. **Debouncing** - 300ms debounce on search input
2. **Memoization** - Result items are memoized
3. **Virtual Scrolling** - For large result sets (future enhancement)
4. **Lazy Loading** - Load results on demand
5. **Result Caching** - Cache recent search results

### Best Practices

- Limit results to 20-50 for optimal performance
- Use pagination for large result sets
- Implement result caching for common queries
- Debounce search input to reduce API calls
- Use React.memo for result items

## Testing

### Unit Tests

The component includes 30+ comprehensive unit tests covering:

- Provider and context functionality
- Spotlight panel open/close
- Search functionality and filtering
- Keyboard navigation (arrows, enter, escape)
- Recent searches management
- Search result rendering
- Backdrop interactions
- Keyboard shortcuts (Cmd+K, Ctrl+K)
- Context methods (open, close, toggle)
- Async search support

### Test Coverage

```bash
npm run test apple-spotlight.test.tsx
```

### Storybook Stories

Interactive stories demonstrating:

- Default spotlight search
- File search
- User search
- Settings search
- No results state
- Recent searches
- Async search
- Large result sets
- Custom max recent searches
- Interactive demo

View in Storybook:

```bash
npm run storybook
```

## Integration Examples

### Dashboard Integration

```tsx
import { AppleSpotlight } from '@/components/ui/apple-spotlight'
import { useNavigate } from 'react-router-dom'

function Dashboard() {
  const navigate = useNavigate()

  const handleSearch = (query: string) => {
    const pages = [
      { path: '/dashboard', title: 'Dashboard', description: 'View analytics' },
      { path: '/settings', title: 'Settings', description: 'Manage settings' },
      { path: '/users', title: 'Users', description: 'Manage users' }
    ]

    return pages
      .filter(page => 
        page.title.toLowerCase().includes(query.toLowerCase())
      )
      .map(page => ({
        id: page.path,
        title: page.title,
        subtitle: page.description,
        type: 'action' as const,
        category: 'Pages',
        onSelect: () => navigate(page.path)
      }))
  }

  return (
    <AppleSpotlight.Provider onSearch={handleSearch}>
      <DashboardContent />
    </AppleSpotlight.Provider>
  )
}
```

### File Search Integration

```tsx
function FileExplorer() {
  const handleFileSearch = async (query: string) => {
    const files = await searchFiles(query)
    
    return files.map(file => ({
      id: file.id,
      title: file.name,
      subtitle: file.path,
      type: 'file' as const,
      icon: getFileIcon(file.type),
      category: file.type,
      onSelect: () => openFile(file)
    }))
  }

  return (
    <AppleSpotlight.Provider onSearch={handleFileSearch}>
      <FileExplorerContent />
    </AppleSpotlight.Provider>
  )
}
```

### Command Palette Integration

```tsx
function CommandPalette() {
  const handleCommandSearch = (query: string) => {
    const commands = [
      {
        id: 'new-file',
        title: 'New File',
        subtitle: 'Create a new file',
        shortcut: 'Cmd+N',
        action: () => createNewFile()
      },
      {
        id: 'save',
        title: 'Save',
        subtitle: 'Save current file',
        shortcut: 'Cmd+S',
        action: () => saveFile()
      }
    ]

    return commands
      .filter(cmd => 
        cmd.title.toLowerCase().includes(query.toLowerCase())
      )
      .map(cmd => ({
        id: cmd.id,
        title: cmd.title,
        subtitle: `${cmd.subtitle} (${cmd.shortcut})`,
        type: 'action' as const,
        category: 'Commands',
        onSelect: cmd.action
      }))
  }

  return (
    <AppleSpotlight.Provider onSearch={handleCommandSearch}>
      <App />
    </AppleSpotlight.Provider>
  )
}
```

## Browser Compatibility

- **Chrome**: 90+
- **Firefox**: 88+
- **Safari**: 14+
- **Edge**: 90+

### Required Features

- CSS backdrop-filter (for glassmorphism)
- Framer Motion (React 18+)
- Keyboard event handling
- Focus management

## Future Enhancements

### Planned Features

1. **Search History** - Persistent search history across sessions
2. **Search Suggestions** - AI-powered search suggestions
3. **Result Previews** - Quick preview on hover
4. **Multi-Select** - Select multiple results
5. **Filters** - Filter by type, category, date
6. **Sorting** - Sort by relevance, date, name
7. **Voice Search** - Voice input support
8. **Search Analytics** - Track popular searches

### API Enhancements

1. **Search Plugins** - Extensible search providers
2. **Custom Renderers** - Custom result renderers
3. **Search Middleware** - Intercept and modify searches
4. **Result Actions** - Context menu for results

## Troubleshooting

### Common Issues

**Issue**: Spotlight doesn't open with Cmd+K
- **Solution**: Ensure Provider wraps your app and no other component is capturing the shortcut

**Issue**: Search results not appearing
- **Solution**: Verify onSearch function returns correct SearchResult[] format

**Issue**: Glassmorphism not working
- **Solution**: Check browser support for backdrop-filter

**Issue**: Keyboard navigation not working
- **Solution**: Ensure input has focus and no other elements are capturing keyboard events

### Debug Mode

Enable debug logging:

```tsx
<AppleSpotlight.Provider 
  onSearch={handleSearch}
  debug
>
  <App />
</AppleSpotlight.Provider>
```

## Related Components

- **AppleControlCenter**: Quick access control panel
- **AppleSheet**: Bottom sheet modal
- **AppleModal**: Full-screen modal
- **AppleTabBar**: Bottom navigation bar
- **AppleSegmentedControl**: Segmented control picker

## Resources

- [macOS Human Interface Guidelines - Search](https://developer.apple.com/design/human-interface-guidelines/search-fields)
- [Framer Motion Documentation](https://www.framer.com/motion/)
- [React Context API](https://react.dev/reference/react/useContext)
- [Keyboard Event Handling](https://developer.mozilla.org/en-US/docs/Web/API/KeyboardEvent)

## Changelog

### Version 1.0.0 (2025-10-26)

- Initial release
- Keyboard shortcuts (Cmd+K, Ctrl+K)
- Real-time search with debouncing
- Recent searches with configurable limit
- Keyboard navigation (arrows, enter, escape)
- Async search support
- Glassmorphism effects
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
