import type { Meta, StoryObj } from '@storybook/react'
import { AppleSpotlight, type SearchResult } from './apple-spotlight'
import {
  Search,
  File,
  Folder,
  User,
  Settings,
  Mail,
  Calendar,
  Image,
  Video,
  Music
} from 'lucide-react'
import { useEffect } from 'react'

const meta = {
  title: 'Apple Design System/AppleSpotlight',
  component: AppleSpotlight.Provider,
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        component: 'iOS-style Spotlight search component with keyboard shortcuts (Cmd+K), recent searches, and real-time results. Features smooth animations and keyboard navigation.'
      }
    }
  },
  tags: ['autodocs']
} satisfies Meta<typeof AppleSpotlight.Provider>

export default meta
type Story = StoryObj<any>

const SpotlightDemo = ({ onSearch }: { onSearch?: (query: string) => SearchResult[] }) => {
  const { useSpotlight } = AppleSpotlight
  const { open } = useSpotlight()

  useEffect(() => {
    setTimeout(() => open(), 100)
  }, [])

  return (
    <div className="w-full h-screen flex items-center justify-center bg-gradient-to-br from-blue-500 to-purple-600">
      <div className="text-center text-white">
        <h1 className="text-4xl font-bold mb-4">Spotlight Search</h1>
        <p className="text-lg mb-2">Press <kbd className="px-2 py-1 bg-white/20 rounded">Cmd+K</kbd> to open</p>
        <p className="text-sm text-white/70">Or click the button below</p>
      </div>
    </div>
  )
}

const mockSearchResults = (query: string): SearchResult[] => {
  const allResults: SearchResult[] = [
    {
      id: '1',
      title: 'Dashboard',
      subtitle: 'View your analytics dashboard',
      type: 'action',
      category: 'Pages',
      onSelect: () => console.log('Navigate to Dashboard')
    },
    {
      id: '2',
      title: 'Settings',
      subtitle: 'Manage your account settings',
      type: 'setting',
      icon: <Settings />,
      category: 'Pages',
      onSelect: () => console.log('Navigate to Settings')
    },
    {
      id: '3',
      title: 'Users',
      subtitle: 'Manage users and permissions',
      type: 'user',
      icon: <User />,
      category: 'Pages',
      onSelect: () => console.log('Navigate to Users')
    },
    {
      id: '4',
      title: 'project-report.pdf',
      subtitle: 'Documents/Reports',
      type: 'file',
      icon: <File />,
      category: 'Files',
      onSelect: () => console.log('Open file')
    },
    {
      id: '5',
      title: 'Images',
      subtitle: '245 items',
      type: 'folder',
      icon: <Folder />,
      category: 'Folders',
      onSelect: () => console.log('Open folder')
    },
    {
      id: '6',
      title: 'john.doe@example.com',
      subtitle: 'User Account',
      type: 'user',
      icon: <User />,
      category: 'Users',
      onSelect: () => console.log('View user')
    },
    {
      id: '7',
      title: 'Email Settings',
      subtitle: 'Configure email preferences',
      type: 'setting',
      icon: <Mail />,
      category: 'Settings',
      onSelect: () => console.log('Open email settings')
    },
    {
      id: '8',
      title: 'Calendar Events',
      subtitle: 'View upcoming events',
      type: 'action',
      icon: <Calendar />,
      category: 'Actions',
      onSelect: () => console.log('Open calendar')
    }
  ]

  const lowerQuery = query.toLowerCase()
  return allResults.filter(
    (result) =>
      result.title.toLowerCase().includes(lowerQuery) ||
      result.subtitle?.toLowerCase().includes(lowerQuery) ||
      result.category?.toLowerCase().includes(lowerQuery)
  )
}

export const Default: Story = {
  render: () => (
    <AppleSpotlight.Provider onSearch={mockSearchResults}>
      <SpotlightDemo onSearch={mockSearchResults} />
    </AppleSpotlight.Provider>
  )
}

const fileSearchResults = (query: string): SearchResult[] => {
  const files: SearchResult[] = [
    {
      id: '1',
      title: 'presentation.pptx',
      subtitle: 'Documents/Work',
      type: 'file',
      icon: <File />,
      category: 'PowerPoint',
      onSelect: () => console.log('Open presentation')
    },
    {
      id: '2',
      title: 'budget-2024.xlsx',
      subtitle: 'Documents/Finance',
      type: 'file',
      icon: <File />,
      category: 'Excel',
      onSelect: () => console.log('Open spreadsheet')
    },
    {
      id: '3',
      title: 'vacation-photo.jpg',
      subtitle: 'Pictures/2024',
      type: 'file',
      icon: <Image />,
      category: 'Image',
      onSelect: () => console.log('Open image')
    },
    {
      id: '4',
      title: 'meeting-recording.mp4',
      subtitle: 'Videos/Work',
      type: 'file',
      icon: <Video />,
      category: 'Video',
      onSelect: () => console.log('Open video')
    },
    {
      id: '5',
      title: 'favorite-song.mp3',
      subtitle: 'Music/Playlist',
      type: 'file',
      icon: <Music />,
      category: 'Audio',
      onSelect: () => console.log('Play music')
    }
  ]

  const lowerQuery = query.toLowerCase()
  return files.filter(
    (file) =>
      file.title.toLowerCase().includes(lowerQuery) ||
      file.subtitle?.toLowerCase().includes(lowerQuery)
  )
}

export const FileSearch: Story = {
  render: () => (
    <AppleSpotlight.Provider onSearch={fileSearchResults}>
      <SpotlightDemo onSearch={fileSearchResults} />
    </AppleSpotlight.Provider>
  )
}

const userSearchResults = (query: string): SearchResult[] => {
  const users: SearchResult[] = [
    {
      id: '1',
      title: 'John Doe',
      subtitle: 'john.doe@example.com',
      type: 'user',
      icon: <User />,
      category: 'Admin',
      onSelect: () => console.log('View John Doe')
    },
    {
      id: '2',
      title: 'Jane Smith',
      subtitle: 'jane.smith@example.com',
      type: 'user',
      icon: <User />,
      category: 'User',
      onSelect: () => console.log('View Jane Smith')
    },
    {
      id: '3',
      title: 'Bob Johnson',
      subtitle: 'bob.johnson@example.com',
      type: 'user',
      icon: <User />,
      category: 'User',
      onSelect: () => console.log('View Bob Johnson')
    },
    {
      id: '4',
      title: 'Alice Williams',
      subtitle: 'alice.williams@example.com',
      type: 'user',
      icon: <User />,
      category: 'Manager',
      onSelect: () => console.log('View Alice Williams')
    }
  ]

  const lowerQuery = query.toLowerCase()
  return users.filter(
    (user) =>
      user.title.toLowerCase().includes(lowerQuery) ||
      user.subtitle?.toLowerCase().includes(lowerQuery)
  )
}

export const UserSearch: Story = {
  render: () => (
    <AppleSpotlight.Provider onSearch={userSearchResults}>
      <SpotlightDemo onSearch={userSearchResults} />
    </AppleSpotlight.Provider>
  )
}

const settingsSearchResults = (query: string): SearchResult[] => {
  const settings: SearchResult[] = [
    {
      id: '1',
      title: 'Account Settings',
      subtitle: 'Manage your account',
      type: 'setting',
      icon: <Settings />,
      category: 'Account',
      onSelect: () => console.log('Open account settings')
    },
    {
      id: '2',
      title: 'Privacy Settings',
      subtitle: 'Control your privacy',
      type: 'setting',
      icon: <Settings />,
      category: 'Privacy',
      onSelect: () => console.log('Open privacy settings')
    },
    {
      id: '3',
      title: 'Notification Settings',
      subtitle: 'Manage notifications',
      type: 'setting',
      icon: <Settings />,
      category: 'Notifications',
      onSelect: () => console.log('Open notification settings')
    },
    {
      id: '4',
      title: 'Security Settings',
      subtitle: 'Manage security',
      type: 'setting',
      icon: <Settings />,
      category: 'Security',
      onSelect: () => console.log('Open security settings')
    }
  ]

  const lowerQuery = query.toLowerCase()
  return settings.filter(
    (setting) =>
      setting.title.toLowerCase().includes(lowerQuery) ||
      setting.subtitle?.toLowerCase().includes(lowerQuery)
  )
}

export const SettingsSearch: Story = {
  render: () => (
    <AppleSpotlight.Provider onSearch={settingsSearchResults}>
      <SpotlightDemo onSearch={settingsSearchResults} />
    </AppleSpotlight.Provider>
  )
}

const emptySearchResults = (): SearchResult[] => {
  return []
}

export const NoResults: Story = {
  render: () => (
    <AppleSpotlight.Provider onSearch={emptySearchResults}>
      <SpotlightDemo onSearch={emptySearchResults} />
    </AppleSpotlight.Provider>
  )
}

export const WithRecentSearches: Story = {
  render: () => (
    <AppleSpotlight.Provider onSearch={mockSearchResults} maxRecentSearches={5}>
      <SpotlightDemo onSearch={mockSearchResults} />
    </AppleSpotlight.Provider>
  )
}

const asyncSearchResults = async (query: string): Promise<SearchResult[]> => {
  await new Promise((resolve) => setTimeout(resolve, 500))
  return mockSearchResults(query)
}

export const AsyncSearch: Story = {
  render: () => (
    <AppleSpotlight.Provider onSearch={asyncSearchResults}>
      <SpotlightDemo />
    </AppleSpotlight.Provider>
  )
}

const InteractiveDemo = () => {
  const { useSpotlight } = AppleSpotlight
  const { toggle, isOpen } = useSpotlight()

  return (
    <div className="w-full h-screen flex items-center justify-center bg-gradient-to-br from-purple-500 to-pink-600">
      <div className="text-center text-white">
        <h1 className="text-4xl font-bold mb-6">Spotlight Search Demo</h1>
        <p className="text-lg mb-4">
          Press <kbd className="px-3 py-2 bg-white/20 rounded-lg font-mono">Cmd+K</kbd> or{' '}
          <kbd className="px-3 py-2 bg-white/20 rounded-lg font-mono">Ctrl+K</kbd>
        </p>
        <button
          onClick={toggle}
          className="px-6 py-3 bg-white text-purple-600 font-semibold rounded-xl shadow-lg hover:shadow-xl transition-all"
        >
          {isOpen ? 'Close' : 'Open'} Spotlight
        </button>
        <div className="mt-8 text-sm text-white/70">
          <p>Try searching for:</p>
          <p className="mt-2">Dashboard, Settings, Users, Files, etc.</p>
        </div>
      </div>
    </div>
  )
}

export const Interactive: Story = {
  render: () => (
    <AppleSpotlight.Provider onSearch={mockSearchResults}>
      <InteractiveDemo />
    </AppleSpotlight.Provider>
  )
}

const largeResultSet = (query: string): SearchResult[] => {
  const results: SearchResult[] = []
  for (let i = 1; i <= 50; i++) {
    results.push({
      id: `result-${i}`,
      title: `Result ${i}`,
      subtitle: `This is result number ${i}`,
      type: i % 5 === 0 ? 'folder' : 'file',
      category: i % 3 === 0 ? 'Important' : 'Normal',
      onSelect: () => console.log(`Selected result ${i}`)
    })
  }

  const lowerQuery = query.toLowerCase()
  return results.filter(
    (result) =>
      result.title.toLowerCase().includes(lowerQuery) ||
      result.subtitle?.toLowerCase().includes(lowerQuery)
  )
}

export const LargeResultSet: Story = {
  render: () => (
    <AppleSpotlight.Provider onSearch={largeResultSet}>
      <SpotlightDemo onSearch={largeResultSet} />
    </AppleSpotlight.Provider>
  )
}

const customMaxRecent = (query: string): SearchResult[] => {
  return mockSearchResults(query)
}

export const CustomMaxRecentSearches: Story = {
  render: () => (
    <AppleSpotlight.Provider onSearch={customMaxRecent} maxRecentSearches={10}>
      <SpotlightDemo onSearch={customMaxRecent} />
    </AppleSpotlight.Provider>
  )
}
