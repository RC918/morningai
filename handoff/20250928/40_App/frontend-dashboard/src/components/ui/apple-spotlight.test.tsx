import React from 'react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AppleSpotlight, type SearchResult } from './apple-spotlight'
import { User, File } from 'lucide-react'

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, defaultValue?: string) => defaultValue || key
  })
}))

vi.mock('@/lib/spring-animation', () => ({
  triggerHaptic: vi.fn()
}))

vi.mock('@/hooks/use-accessibility', () => ({
  useScreenReaderAnnouncement: () => vi.fn(),
  useFocusTrap: () => {}
}))

const TestWrapper = ({ children, onSearch, maxRecentSearches }: {
  children: React.ReactNode
  onSearch?: (query: string) => SearchResult[]
  maxRecentSearches?: number
}) => (
  <AppleSpotlight.Provider onSearch={onSearch} maxRecentSearches={maxRecentSearches}>
    {children}
  </AppleSpotlight.Provider>
)

const TestComponent = () => {
  const { open } = AppleSpotlight.useSpotlight()

  React.useEffect(() => {
    open()
  }, [])

  return <div>Test Component</div>
}

const mockSearchResults: SearchResult[] = [
  {
    id: '1',
    title: 'Dashboard',
    subtitle: 'View analytics',
    type: 'action',
    category: 'Pages',
    onSelect: vi.fn()
  },
  {
    id: '2',
    title: 'Settings',
    subtitle: 'Manage settings',
    type: 'setting',
    category: 'Pages',
    onSelect: vi.fn()
  },
  {
    id: '3',
    title: 'Users',
    subtitle: 'Manage users',
    type: 'user',
    icon: <User />,
    category: 'Pages',
    onSelect: vi.fn()
  }
]

const mockOnSearch = (query: string): SearchResult[] => {
  return mockSearchResults.filter((result) =>
    result.title.toLowerCase().includes(query.toLowerCase())
  )
}

describe('AppleSpotlight', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Provider and Context', () => {
    it('provides spotlight context', () => {
      const TestHook = () => {
        const { open, close, toggle } = AppleSpotlight.useSpotlight()
        expect(open).toBeDefined()
        expect(close).toBeDefined()
        expect(toggle).toBeDefined()
        return <div>Hook Test</div>
      }

      render(
        <TestWrapper>
          <TestHook />
        </TestWrapper>
      )

      expect(screen.getByText('Hook Test')).toBeInTheDocument()
    })

    it('throws error when used outside provider', () => {
      const TestHook = () => {
        try {
          AppleSpotlight.useSpotlight()
          return <div>Should not render</div>
        } catch (error) {
          return <div>Error caught</div>
        }
      }

      render(<TestHook />)
      expect(screen.getByText('Error caught')).toBeInTheDocument()
    })
  })

  describe('Spotlight Panel', () => {
    it('opens and closes spotlight', async () => {
      const user = userEvent.setup()
      const TestToggle = () => {
        const { toggle, isOpen } = AppleSpotlight.useSpotlight()
        return (
          <button onClick={toggle}>
            {isOpen ? 'Close' : 'Open'}
          </button>
        )
      }

      render(
        <TestWrapper>
          <TestToggle />
        </TestWrapper>
      )

      const button = screen.getByText('Open')
      expect(button).toBeInTheDocument()

      await user.click(button)

      await waitFor(() => {
        expect(screen.getByPlaceholderText('Search')).toBeInTheDocument()
      })

      await user.click(screen.getByText('Close'))

      await waitFor(() => {
        expect(screen.queryByPlaceholderText('Search')).not.toBeInTheDocument()
      })
    })

    it('displays search input when open', async () => {
      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByPlaceholderText('Search')).toBeInTheDocument()
      })
    })

    it('focuses search input when opened', async () => {
      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      )

      await waitFor(() => {
        const input = screen.getByPlaceholderText('Search')
        expect(input).toHaveFocus()
      })
    })
  })

  describe('Search Functionality', () => {
    it('updates search query on input', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper onSearch={mockOnSearch}>
          <TestComponent />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByPlaceholderText('Search')).toBeInTheDocument()
      })

      const input = screen.getByPlaceholderText('Search')
      await user.type(input, 'Dashboard')

      expect(input).toHaveValue('Dashboard')
    })

    it('displays search results', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper onSearch={mockOnSearch}>
          <TestComponent />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByPlaceholderText('Search')).toBeInTheDocument()
      })

      const input = screen.getByPlaceholderText('Search')
      await user.type(input, 'Dashboard')

      await waitFor(() => {
        expect(screen.getByText('Dashboard')).toBeInTheDocument()
        expect(screen.getByText('View analytics')).toBeInTheDocument()
      })
    })

    it('filters results based on query', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper onSearch={mockOnSearch}>
          <TestComponent />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByPlaceholderText('Search')).toBeInTheDocument()
      })

      const input = screen.getByPlaceholderText('Search')
      await user.type(input, 'Settings')

      await waitFor(() => {
        expect(screen.getByText('Settings')).toBeInTheDocument()
        expect(screen.queryByText('Dashboard')).not.toBeInTheDocument()
      })
    })

    it('shows no results message when no matches', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper onSearch={mockOnSearch}>
          <TestComponent />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByPlaceholderText('Search')).toBeInTheDocument()
      })

      const input = screen.getByPlaceholderText('Search')
      await user.type(input, 'NonexistentQuery')

      await waitFor(() => {
        expect(screen.getByText('No results found')).toBeInTheDocument()
      })
    })

    it('clears search query', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper onSearch={mockOnSearch}>
          <TestComponent />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByPlaceholderText('Search')).toBeInTheDocument()
      })

      const input = screen.getByPlaceholderText('Search')
      await user.type(input, 'Dashboard')

      expect(input).toHaveValue('Dashboard')

      const clearButton = screen.getByLabelText('Clear search')
      await user.click(clearButton)

      expect(input).toHaveValue('')
    })
  })

  describe('Keyboard Navigation', () => {
    it('closes on Escape key', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper onSearch={mockOnSearch}>
          <TestComponent />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByPlaceholderText('Search')).toBeInTheDocument()
      })

      const input = screen.getByPlaceholderText('Search')
      await user.type(input, '{Escape}')

      await waitFor(() => {
        expect(screen.queryByPlaceholderText('Search')).not.toBeInTheDocument()
      })
    })

    it('navigates results with arrow keys', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper onSearch={mockOnSearch}>
          <TestComponent />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByPlaceholderText('Search')).toBeInTheDocument()
      })

      const input = screen.getByPlaceholderText('Search')
      await user.type(input, 'a')

      await waitFor(() => {
        expect(screen.getByText('Dashboard')).toBeInTheDocument()
      })

      await user.type(input, '{ArrowDown}')
      await user.type(input, '{ArrowUp}')

      expect(input).toHaveFocus()
    })

    it('selects result with Enter key', async () => {
      const user = userEvent.setup()
      const onSelect = vi.fn()
      const customResults: SearchResult[] = [
        {
          id: '1',
          title: 'Dashboard',
          subtitle: 'View analytics',
          type: 'action',
          onSelect
        }
      ]

      const customSearch = (query: string) => {
        return customResults.filter((r) =>
          r.title.toLowerCase().includes(query.toLowerCase())
        )
      }

      render(
        <TestWrapper onSearch={customSearch}>
          <TestComponent />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByPlaceholderText('Search')).toBeInTheDocument()
      })

      const input = screen.getByPlaceholderText('Search')
      await user.type(input, 'Dashboard')

      await waitFor(() => {
        expect(screen.getByText('Dashboard')).toBeInTheDocument()
      })

      await user.type(input, '{Enter}')

      expect(onSelect).toHaveBeenCalled()
    })
  })

  describe('Recent Searches', () => {
    it('displays recent searches when query is empty', async () => {
      const TestWithRecent = () => {
        const { open, addRecentSearch } = AppleSpotlight.useSpotlight()
        
        React.useEffect(() => {
          addRecentSearch('Dashboard')
          addRecentSearch('Settings')
          open()
        }, [])
        
        return <div>Test</div>
      }

      render(
        <TestWrapper onSearch={mockOnSearch}>
          <TestWithRecent />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Recent Searches')).toBeInTheDocument()
        expect(screen.getByText('Settings')).toBeInTheDocument()
        expect(screen.getByText('Dashboard')).toBeInTheDocument()
      })
    })

    it('clears recent searches', async () => {
      const user = userEvent.setup()
      
      const TestWithRecent = () => {
        const { open, addRecentSearch } = AppleSpotlight.useSpotlight()
        
        React.useEffect(() => {
          addRecentSearch('Dashboard')
          addRecentSearch('Settings')
          open()
        }, [])
        
        return <div>Test</div>
      }

      render(
        <TestWrapper onSearch={mockOnSearch}>
          <TestWithRecent />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Recent Searches')).toBeInTheDocument()
      })

      const clearButton = screen.getByText('Clear')
      await user.click(clearButton)

      await waitFor(() => {
        expect(screen.queryByText('Recent Searches')).not.toBeInTheDocument()
      })
    })

    it('limits recent searches to maxRecentSearches', async () => {
      const TestWithRecent = () => {
        const { open, addRecentSearch, recentSearches } = AppleSpotlight.useSpotlight()
        
        React.useEffect(() => {
          addRecentSearch('First')
          addRecentSearch('Second')
          addRecentSearch('Third')
          open()
        }, [])
        
        return <div>Searches: {recentSearches.length}</div>
      }

      render(
        <TestWrapper onSearch={mockOnSearch} maxRecentSearches={2}>
          <TestWithRecent />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Searches: 2')).toBeInTheDocument()
      })
    })
  })

  describe('Search Result Item', () => {
    it('displays result title and subtitle', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper onSearch={mockOnSearch}>
          <TestComponent />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByPlaceholderText('Search')).toBeInTheDocument()
      })

      const input = screen.getByPlaceholderText('Search')
      await user.type(input, 'Dashboard')

      await waitFor(() => {
        expect(screen.getByText('Dashboard')).toBeInTheDocument()
        expect(screen.getByText('View analytics')).toBeInTheDocument()
      })
    })

    it('displays result category', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper onSearch={mockOnSearch}>
          <TestComponent />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByPlaceholderText('Search')).toBeInTheDocument()
      })

      const input = screen.getByPlaceholderText('Search')
      await user.type(input, 'Dashboard')

      await waitFor(() => {
        expect(screen.getByText('Pages')).toBeInTheDocument()
      })
    })

    it('calls onSelect when clicked', async () => {
      const user = userEvent.setup()
      const onSelect = vi.fn()
      const customResults: SearchResult[] = [
        {
          id: '1',
          title: 'Dashboard',
          subtitle: 'View analytics',
          type: 'action',
          onSelect
        }
      ]

      const customSearch = (query: string) => {
        return customResults.filter((r) =>
          r.title.toLowerCase().includes(query.toLowerCase())
        )
      }

      render(
        <TestWrapper onSearch={customSearch}>
          <TestComponent />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByPlaceholderText('Search')).toBeInTheDocument()
      })

      const input = screen.getByPlaceholderText('Search')
      await user.type(input, 'Dashboard')

      await waitFor(() => {
        expect(screen.getByText('Dashboard')).toBeInTheDocument()
      })

      await user.click(screen.getByText('Dashboard'))

      expect(onSelect).toHaveBeenCalled()
    })
  })

  describe('Backdrop', () => {
    it('closes spotlight when backdrop is clicked', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper onSearch={mockOnSearch}>
          <TestComponent />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByPlaceholderText('Search')).toBeInTheDocument()
      })

      const backdrop = document.querySelector('.fixed.bg-black\\/50')
      if (backdrop) {
        await user.click(backdrop as HTMLElement)
      }

      await waitFor(() => {
        expect(screen.queryByPlaceholderText('Search')).not.toBeInTheDocument()
      })
    })
  })

  describe('Keyboard Shortcut', () => {
    it('opens spotlight with Cmd+K', async () => {
      render(
        <TestWrapper onSearch={mockOnSearch}>
          <div>Test</div>
        </TestWrapper>
      )

      expect(screen.queryByPlaceholderText('Search')).not.toBeInTheDocument()

      fireEvent.keyDown(window, { key: 'k', metaKey: true })

      await waitFor(() => {
        expect(screen.getByPlaceholderText('Search')).toBeInTheDocument()
      })
    })

    it('opens spotlight with Ctrl+K', async () => {
      render(
        <TestWrapper onSearch={mockOnSearch}>
          <div>Test</div>
        </TestWrapper>
      )

      expect(screen.queryByPlaceholderText('Search')).not.toBeInTheDocument()

      fireEvent.keyDown(window, { key: 'k', ctrlKey: true })

      await waitFor(() => {
        expect(screen.getByPlaceholderText('Search')).toBeInTheDocument()
      })
    })
  })

  describe('Context Methods', () => {
    it('provides open method', async () => {
      const TestOpen = () => {
        const { open, isOpen } = AppleSpotlight.useSpotlight()
        return (
          <>
            <button onClick={open}>Open</button>
            <div>{isOpen ? 'Open' : 'Closed'}</div>
          </>
        )
      }

      const user = userEvent.setup()
      render(
        <TestWrapper onSearch={mockOnSearch}>
          <TestOpen />
        </TestWrapper>
      )

      expect(screen.getByText('Closed')).toBeInTheDocument()

      await user.click(screen.getByText('Open'))

      await waitFor(() => {
        expect(screen.getByPlaceholderText('Search')).toBeInTheDocument()
      })
    })

    it('provides close method', async () => {
      const TestClose = () => {
        const { open, close, isOpen } = AppleSpotlight.useSpotlight()
        React.useEffect(() => {
          open()
        }, [])
        return (
          <>
            <button onClick={close}>Close</button>
            <div>{isOpen ? 'Open' : 'Closed'}</div>
          </>
        )
      }

      const user = userEvent.setup()
      render(
        <TestWrapper onSearch={mockOnSearch}>
          <TestClose />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByPlaceholderText('Search')).toBeInTheDocument()
      })

      await user.click(screen.getByText('Close'))

      await waitFor(() => {
        expect(screen.queryByPlaceholderText('Search')).not.toBeInTheDocument()
      })
    })

    it('provides toggle method', async () => {
      const TestToggle = () => {
        const { toggle, isOpen } = AppleSpotlight.useSpotlight()
        return (
          <>
            <button onClick={toggle}>Toggle</button>
            <div>{isOpen ? 'Open' : 'Closed'}</div>
          </>
        )
      }

      const user = userEvent.setup()
      render(
        <TestWrapper onSearch={mockOnSearch}>
          <TestToggle />
        </TestWrapper>
      )

      expect(screen.getByText('Closed')).toBeInTheDocument()

      await user.click(screen.getByText('Toggle'))

      await waitFor(() => {
        expect(screen.getByPlaceholderText('Search')).toBeInTheDocument()
      })

      await user.click(screen.getByText('Toggle'))

      await waitFor(() => {
        expect(screen.queryByPlaceholderText('Search')).not.toBeInTheDocument()
      })
    })
  })

  describe('Async Search', () => {
    it('handles async search results', async () => {
      const user = userEvent.setup()
      const asyncSearch = async (query: string): Promise<SearchResult[]> => {
        await new Promise((resolve) => setTimeout(resolve, 100))
        return mockOnSearch(query)
      }

      render(
        <TestWrapper onSearch={asyncSearch}>
          <TestComponent />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByPlaceholderText('Search')).toBeInTheDocument()
      })

      const input = screen.getByPlaceholderText('Search')
      await user.type(input, 'Dashboard')

      await waitFor(() => {
        expect(screen.getByText('Dashboard')).toBeInTheDocument()
      }, { timeout: 2000 })
    })
  })
})
