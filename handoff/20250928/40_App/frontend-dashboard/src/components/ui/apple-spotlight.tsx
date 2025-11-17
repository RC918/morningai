import React, { useState, useCallback, useEffect, useRef, createContext, useContext } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Search, X, Clock, TrendingUp, Hash, File, Folder, User, Settings } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { triggerHaptic } from '@/lib/spring-animation'
import { useScreenReaderAnnouncement, useFocusTrap } from '@/hooks/use-accessibility'

type SearchResultType = 'recent' | 'suggestion' | 'file' | 'folder' | 'user' | 'setting' | 'action'

interface SearchResult {
  id: string
  title: string
  subtitle?: string
  type: SearchResultType
  icon?: React.ReactNode
  category?: string
  onSelect: () => void
  metadata?: Record<string, unknown>
}

interface SearchCategory {
  id: string
  title: string
  results: SearchResult[]
}

interface SpotlightContextValue {
  isOpen: boolean
  open: () => void
  close: () => void
  toggle: () => void
  searchQuery: string
  setSearchQuery: (query: string) => void
  results: SearchResult[]
  setResults: (results: SearchResult[]) => void
  recentSearches: string[]
  addRecentSearch: (query: string) => void
  clearRecentSearches: () => void
}

const SpotlightContext = createContext<SpotlightContextValue | undefined>(undefined)

export const useAppleSpotlight = () => {
  const context = useContext(SpotlightContext)
  if (!context) {
    throw new Error('useAppleSpotlight must be used within AppleSpotlightProvider')
  }
  return context
}

interface SpotlightProviderProps {
  children: React.ReactNode
  onSearch?: (query: string) => SearchResult[] | Promise<SearchResult[]>
  maxRecentSearches?: number
}

const getIconForType = (type: SearchResultType): React.ReactNode => {
  switch (type) {
    case 'recent':
      return <Clock className="w-4 h-4" />
    case 'suggestion':
      return <TrendingUp className="w-4 h-4" />
    case 'file':
      return <File className="w-4 h-4" />
    case 'folder':
      return <Folder className="w-4 h-4" />
    case 'user':
      return <User className="w-4 h-4" />
    case 'setting':
      return <Settings className="w-4 h-4" />
    case 'action':
      return <Hash className="w-4 h-4" />
    default:
      return <Search className="w-4 h-4" />
  }
}

const SearchResultItem: React.FC<{
  result: SearchResult
  isSelected: boolean
  onSelect: () => void
  onHover: () => void
}> = ({ result, isSelected, onSelect, onHover }) => {
  const { t } = useTranslation()
  const itemRef = useRef<HTMLDivElement>(null)
  const { announce } = useScreenReaderAnnouncement()

  const handleClick = () => {
    if (itemRef.current) {
      triggerHaptic(itemRef.current, 'light')
    }
    announce(`Selected ${result.title}`, 'polite')
    onSelect()
  }

  return (
    <motion.div
      ref={itemRef}
      id={`result-${result.id}`}
      role="option"
      aria-selected={isSelected}
      aria-label={`${result.title}${result.subtitle ? `, ${result.subtitle}` : ''}${result.category ? `, ${result.category}` : ''}`}
      className={`
        flex items-center gap-3 px-4 py-3 cursor-pointer rounded-xl transition-all
        ${isSelected ? 'bg-primary-500/20 border border-primary-500/30' : 'hover:bg-white/5'}
      `}
      onClick={handleClick}
      onMouseEnter={onHover}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          handleClick()
        }
      }}
      tabIndex={0}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{
        type: 'spring',
        stiffness: 500,
        damping: 30
      }}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
    >
      <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-white/10 text-white/70">
        {result.icon || getIconForType(result.type)}
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium text-white/90 truncate">
          {result.title}
        </div>
        {result.subtitle && (
          <div className="text-xs text-white/60 truncate">
            {result.subtitle}
          </div>
        )}
      </div>
      {result.category && (
        <div className="text-xs text-white/50 px-2 py-1 rounded-md bg-white/5">
          {result.category}
        </div>
      )}
    </motion.div>
  )
}

const SpotlightPanel: React.FC = () => {
  const { t } = useTranslation()
  const {
    isOpen,
    close,
    searchQuery,
    setSearchQuery,
    results,
    recentSearches,
    addRecentSearch,
    clearRecentSearches
  } = useAppleSpotlight()

  const [selectedIndex, setSelectedIndex] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)
  const panelRef = useFocusTrap<HTMLDivElement>(isOpen)
  const { announce } = useScreenReaderAnnouncement()

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus()
    }
  }, [isOpen])

  useEffect(() => {
    setSelectedIndex(0)
    if (results.length > 0) {
      announce(`${results.length} ${t('results found', 'results found')}`, 'polite')
    }
  }, [results, announce, t])

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Escape') {
        close()
      } else if (e.key === 'ArrowDown') {
        e.preventDefault()
        setSelectedIndex((prev) => Math.min(prev + 1, results.length - 1))
      } else if (e.key === 'ArrowUp') {
        e.preventDefault()
        setSelectedIndex((prev) => Math.max(prev - 1, 0))
      } else if (e.key === 'Enter' && results[selectedIndex]) {
        e.preventDefault()
        results[selectedIndex].onSelect()
        if (searchQuery.trim()) {
          addRecentSearch(searchQuery)
        }
        close()
      }
    },
    [close, results, selectedIndex, searchQuery, addRecentSearch]
  )

  const handleResultSelect = (result: SearchResult) => {
    result.onSelect()
    if (searchQuery.trim()) {
      addRecentSearch(searchQuery)
    }
    close()
  }

  const handleClearSearch = () => {
    setSearchQuery('')
    if (inputRef.current) {
      inputRef.current.focus()
      triggerHaptic(inputRef.current, 'light')
    }
  }

  const handleClearRecent = () => {
    clearRecentSearches()
    if (panelRef.current) {
      triggerHaptic(panelRef.current, 'medium')
    }
  }

  const displayResults = searchQuery.trim() ? results : []
  const showRecentSearches = !searchQuery.trim() && recentSearches.length > 0

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={close}
          />
          <motion.div
            ref={panelRef}
            role="dialog"
            aria-label="Spotlight Search"
            aria-modal="true"
            className="fixed top-20 left-1/2 -translate-x-1/2 z-50 w-full max-w-2xl"
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{
              type: 'spring',
              stiffness: 500,
              damping: 30
            }}
          >
            <div className="bg-neutral-900/95 backdrop-blur-xl rounded-2xl border border-white/20 shadow-2xl overflow-hidden">
              <div className="flex items-center gap-3 px-4 py-4 border-b border-white/10">
                <Search className="w-5 h-5 text-white/50" />
                <input
                  ref={inputRef}
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={t('Search', 'Search')}
                  className="flex-1 bg-transparent text-white placeholder-white/50 outline-none text-base"
                  autoComplete="off"
                  spellCheck="false"
                  role="searchbox"
                  aria-label="Search"
                  aria-autocomplete="list"
                  aria-controls="search-results"
                  aria-activedescendant={results[selectedIndex] ? `result-${results[selectedIndex].id}` : undefined}
                />
                {searchQuery && (
                  <button
                    onClick={handleClearSearch}
                    className="p-1 rounded-full hover:bg-white/10 active:bg-white/20 transition-colors"
                    aria-label="Clear search"
                  >
                    <X className="w-4 h-4 text-white/70" />
                  </button>
                )}
              </div>

              <div className="max-h-96 overflow-y-auto" id="search-results" role="listbox">
                {showRecentSearches && (
                  <div className="p-4">
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="text-xs font-semibold text-white/50 uppercase tracking-wider">
                        {t('Recent Searches', 'Recent Searches')}
                      </h3>
                      <button
                        onClick={handleClearRecent}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault()
                            handleClearRecent()
                          }
                        }}
                        className="text-xs text-primary-400 hover:text-primary-300 transition-colors"
                        aria-label="Clear recent searches"
                      >
                        {t('Clear', 'Clear')}
                      </button>
                    </div>
                    <div className="space-y-1">
                      {recentSearches.map((search, index) => (
                        <motion.div
                          key={`recent-${index}`}
                          className="flex items-center gap-3 px-4 py-2 cursor-pointer rounded-lg hover:bg-white/5 transition-colors"
                          onClick={() => setSearchQuery(search)}
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: index * 0.05 }}
                        >
                          <Clock className="w-4 h-4 text-white/50" />
                          <span className="text-sm text-white/70">{search}</span>
                        </motion.div>
                      ))}
                    </div>
                  </div>
                )}

                {displayResults.length > 0 && (
                  <div className="p-4 space-y-1">
                    {displayResults.map((result, index) => (
                      <SearchResultItem
                        key={result.id}
                        result={result}
                        isSelected={index === selectedIndex}
                        onSelect={() => handleResultSelect(result)}
                        onHover={() => setSelectedIndex(index)}
                      />
                    ))}
                  </div>
                )}

                {searchQuery.trim() && displayResults.length === 0 && (
                  <div className="p-8 text-center">
                    <Search className="w-12 h-12 text-white/20 mx-auto mb-3" />
                    <p className="text-white/50 text-sm">
                      {t('No results found', 'No results found')}
                    </p>
                  </div>
                )}

                {!searchQuery.trim() && !showRecentSearches && (
                  <div className="p-8 text-center">
                    <Search className="w-12 h-12 text-white/20 mx-auto mb-3" />
                    <p className="text-white/50 text-sm">
                      {t('Start typing to search', 'Start typing to search')}
                    </p>
                  </div>
                )}
              </div>

              <div className="px-4 py-3 border-t border-white/10 bg-white/5">
                <div className="flex items-center justify-between text-xs text-white/50">
                  <div className="flex items-center gap-4">
                    <span>↑↓ {t('Navigate', 'Navigate')}</span>
                    <span>↵ {t('Select', 'Select')}</span>
                    <span>Esc {t('Close', 'Close')}</span>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}

export const AppleSpotlightProvider: React.FC<SpotlightProviderProps> = ({
  children,
  onSearch,
  maxRecentSearches = 5
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [recentSearches, setRecentSearches] = useState<string[]>([])
  const { announce } = useScreenReaderAnnouncement()

  const open = useCallback(() => {
    setIsOpen(true)
    announce('Spotlight opened', 'polite')
  }, [announce])

  const close = useCallback(() => {
    setIsOpen(false)
    setSearchQuery('')
    setResults([])
    announce('Spotlight closed', 'polite')
  }, [announce])

  const toggle = useCallback(() => {
    setIsOpen((prev) => !prev)
  }, [])

  const addRecentSearch = useCallback(
    (query: string) => {
      const trimmedQuery = query.trim()
      if (!trimmedQuery) return

      setRecentSearches((prev) => {
        const filtered = prev.filter((q) => q !== trimmedQuery)
        return [trimmedQuery, ...filtered].slice(0, maxRecentSearches)
      })
    },
    [maxRecentSearches]
  )

  const clearRecentSearches = useCallback(() => {
    setRecentSearches([])
  }, [])

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        toggle()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [toggle])

  useEffect(() => {
    if (!searchQuery.trim() || !onSearch) {
      setResults([])
      return
    }

    const performSearch = async () => {
      try {
        const searchResults = await Promise.resolve(onSearch(searchQuery))
        setResults(searchResults)
      } catch (error) {
        console.error('Search error:', error)
        setResults([])
      }
    }

    const debounceTimer = setTimeout(performSearch, 300)
    return () => clearTimeout(debounceTimer)
  }, [searchQuery, onSearch])

  const value: SpotlightContextValue = {
    isOpen,
    open,
    close,
    toggle,
    searchQuery,
    setSearchQuery,
    results,
    setResults,
    recentSearches,
    addRecentSearch,
    clearRecentSearches
  }

  return (
    <SpotlightContext.Provider value={value}>
      {children}
      <SpotlightPanel />
    </SpotlightContext.Provider>
  )
}

export const AppleSpotlight = {
  Provider: AppleSpotlightProvider,
  useSpotlight: useAppleSpotlight
}

export type {
  SearchResult,
  SearchResultType,
  SearchCategory,
  SpotlightContextValue,
  SpotlightProviderProps
}
