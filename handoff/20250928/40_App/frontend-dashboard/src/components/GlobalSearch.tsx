import React, { useState, useEffect, useCallback, useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import {
  Search, FileText, Settings, BarChart3, Command, ArrowRight, LucideIcon
} from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@morningai/shared-ui'
import { AppleInput } from '@/components/ui/apple-input'
import { Badge } from '@morningai/shared-ui'
import { SEARCH_CATEGORIES, getSearchableItems } from '@/lib/searchRegistry'

interface SearchItem {
  id: string
  title: string
  description?: string
  category: string
  path?: string
  action?: () => void
  keywords?: string[]
  weight: number
  score?: number
}

const CATEGORY_ICONS: Record<string, LucideIcon> = {
  [SEARCH_CATEGORIES.PAGES]: FileText,
  [SEARCH_CATEGORIES.WIDGETS]: BarChart3,
  [SEARCH_CATEGORIES.SETTINGS]: Settings,
  [SEARCH_CATEGORIES.DOCS]: FileText
}

/**
 * GlobalSearch Component
 * 
 * Provides Cmd+K / Ctrl+K global search functionality
 * Searches across pages, widgets, settings, and documentation
 * 
 * Features:
 * - Fuzzy search with weighted scoring
 * - Keyboard navigation (Arrow keys, Enter, Escape)
 * - Category filtering
 * - Recent searches
 * - Quick actions
 */
export const GlobalSearch = (): React.ReactElement => {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [isOpen, setIsOpen] = useState<boolean>(false)
  const [query, setQuery] = useState<string>('')
  const [selectedIndex, setSelectedIndex] = useState<number>(0)
  const [recentSearches, setRecentSearches] = useState<SearchItem[]>([])

  const searchableItems: SearchItem[] = useMemo(() => getSearchableItems(t), [t])

  const fuzzySearch = useCallback((searchQuery: string, items: SearchItem[]): SearchItem[] => {
    if (!searchQuery.trim()) return []

    const lowerQuery = searchQuery.toLowerCase()
    const queryWords = lowerQuery.split(/\s+/)

    const scored: SearchItem[] = items.map((item: SearchItem): SearchItem => {
      let score: number = 0
      const lowerTitle: string = item.title.toLowerCase()
      const lowerDescription: string = item.description?.toLowerCase() || ''
      const keywords: string[] = item.keywords || []

      if (lowerTitle === lowerQuery) {
        score += 100 * item.weight
      } else if (lowerTitle.startsWith(lowerQuery)) {
        score += 50 * item.weight
      } else if (lowerTitle.includes(lowerQuery)) {
        score += 30 * item.weight
      }

      queryWords.forEach((word: string) => {
        if (lowerTitle.includes(word)) score += 20 * item.weight
        if (lowerDescription.includes(word)) score += 10 * item.weight
        if (keywords.some((k: string) => k.includes(word))) score += 15 * item.weight
      })

      const titleWords: string[] = lowerTitle.split(/\s+/)
      queryWords.forEach((queryWord: string) => {
        titleWords.forEach((titleWord: string) => {
          if (titleWord.startsWith(queryWord)) {
            score += 5 * item.weight
          }
        })
      })

      return { ...item, score }
    })

    return scored
      .filter((item: SearchItem) => (item.score ?? 0) > 0)
      .sort((a: SearchItem, b: SearchItem) => (b.score ?? 0) - (a.score ?? 0))
      .slice(0, 10)
  }, [])

  const searchResults: SearchItem[] = useMemo(() => {
    return fuzzySearch(query, searchableItems)
  }, [query, searchableItems, fuzzySearch])

  const handleSelect = useCallback((item: SearchItem): void => {
    if (item.path) {
      navigate(item.path)
    } else if (item.action) {
      item.action()
    }

    setRecentSearches((prev: SearchItem[]) => {
      const filtered: SearchItem[] = prev.filter((s: SearchItem) => s.id !== item.id)
      return [item, ...filtered].slice(0, 5)
    })

    setIsOpen(false)
    setQuery('')
    setSelectedIndex(0)
  }, [navigate])

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent): void => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setIsOpen(prev => !prev)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  useEffect(() => {
    if (!isOpen) {
      setQuery('')
      setSelectedIndex(0)
    }
  }, [isOpen])

  useEffect(() => {
    if (!isOpen) return

    const handleKeyDown = (e: KeyboardEvent): void => {
      const results: SearchItem[] = query ? searchResults : recentSearches

      if (e.key === 'ArrowDown') {
        e.preventDefault()
        setSelectedIndex(prev => (prev + 1) % results.length)
      } else if (e.key === 'ArrowUp') {
        e.preventDefault()
        setSelectedIndex(prev => (prev - 1 + results.length) % results.length)
      } else if (e.key === 'Enter' && results[selectedIndex]) {
        e.preventDefault()
        handleSelect(results[selectedIndex])
      } else if (e.key === 'Escape') {
        e.preventDefault()
        setIsOpen(false)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, query, searchResults, recentSearches, selectedIndex, handleSelect])

  const getCategoryLabel = (category: string): string => {
    const labels: Record<string, string> = {
      [SEARCH_CATEGORIES.PAGES]: t('search.categories.pages'),
      [SEARCH_CATEGORIES.WIDGETS]: t('search.categories.widgets'),
      [SEARCH_CATEGORIES.SETTINGS]: t('search.categories.settings'),
      [SEARCH_CATEGORIES.DOCS]: t('search.categories.docs')
    }
    return labels[category] || category
  }

  const displayResults: SearchItem[] = query ? searchResults : recentSearches

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogContent className="max-w-2xl p-0 gap-0">
        <DialogHeader className="px-4 pt-4 pb-2 border-b">
          <div className="flex items-center gap-2">
            <AppleInput
              value={query}
              onChange={(e) => {
                setQuery(e.target.value)
                setSelectedIndex(0)
              }}
              placeholder={t('search.placeholder')}
              leftIcon={<Search className="w-5 h-5" />}
              variant="filled"
              className="border-0 focus-visible:ring-0 focus-visible:ring-offset-0 text-lg"
              autoFocus
              haptic="none"
            />
            <div className="flex items-center gap-1 text-xs text-gray-600 bg-gray-100 px-2 py-1 rounded">
              <Command className="w-3 h-3" />
              <span>K</span>
            </div>
          </div>
        </DialogHeader>

        <div className="max-h-96 overflow-y-auto p-2">
          {!query && recentSearches.length > 0 && (
            <div className="px-2 py-1 text-xs font-medium text-gray-600 uppercase">
              {t('search.recentSearches')}
            </div>
          )}

          {displayResults.length === 0 && query && (
            <div className="p-8 text-center text-gray-600">
              <Search className="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p className="text-sm">{t('search.noResults')}</p>
              <p className="text-xs mt-1">{t('search.tryDifferentKeywords')}</p>
            </div>
          )}

          {displayResults.map((item: SearchItem, index: number) => {
            const Icon: LucideIcon = CATEGORY_ICONS[item.category] || FileText
            const isSelected: boolean = index === selectedIndex

            return (
              <button
                key={item.id}
                onClick={() => handleSelect(item)}
                onMouseEnter={() => setSelectedIndex(index)}
                className={`w-full flex items-center gap-3 p-3 rounded-lg text-left transition-colors ${
                  isSelected ? 'bg-primary-50 border-primary-200' : 'hover:bg-gray-50'
                }`}
              >
                <div className={`p-2 rounded-md ${isSelected ? 'bg-primary-100' : 'bg-gray-100'}`}>
                  <Icon className={`w-4 h-4 ${isSelected ? 'text-primary-600' : 'text-gray-600'}`} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-sm truncate">{item.title}</span>
                    <Badge variant="outline" className="text-xs">
                      {getCategoryLabel(item.category)}
                    </Badge>
                  </div>
                  {item.description && (
                    <p className="text-xs text-gray-600 truncate mt-0.5">
                      {item.description}
                    </p>
                  )}
                </div>
                {isSelected && (
                  <ArrowRight className="w-4 h-4 text-gray-600 flex-shrink-0" />
                )}
              </button>
            )
          })}
        </div>

        <div className="border-t px-4 py-2 text-xs text-gray-600 flex items-center justify-between bg-gray-50">
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1">
              <kbd className="px-1.5 py-0.5 bg-white border rounded">↑↓</kbd>
              {t('search.navigate')}
            </span>
            <span className="flex items-center gap-1">
              <kbd className="px-1.5 py-0.5 bg-white border rounded">↵</kbd>
              {t('search.select')}
            </span>
            <span className="flex items-center gap-1">
              <kbd className="px-1.5 py-0.5 bg-white border rounded">esc</kbd>
              {t('search.close')}
            </span>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}

export default GlobalSearch
