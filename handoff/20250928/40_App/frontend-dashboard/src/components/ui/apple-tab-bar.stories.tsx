import type { Meta, StoryObj } from '@storybook/react'
import { useState } from 'react'
import { AppleTabBar, AppleTabBarItem } from './apple-tab-bar'
import { Home, Search, Bell, User, Settings } from 'lucide-react'

const meta = {
  title: 'Apple Design System/AppleTabBar',
  component: AppleTabBar,
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        component: `
# AppleTabBar

iOS-style bottom tab navigation with smooth animations and haptic feedback.

## Features

- **iOS Design**: Authentic iOS tab bar styling with backdrop blur
- **Spring Animations**: Natural spring physics for interactions
- **Haptic Feedback**: Visual haptic feedback simulation
- **Badge Support**: Show notification counts on tabs
- **Active Indicator**: Smooth sliding active state
- **Accessibility**: Full ARIA support and keyboard navigation

## Design Principles

Based on Apple's Human Interface Guidelines:
- Clear visual hierarchy
- Smooth, natural animations
- Haptic feedback for interactions
- Accessible by default

## Usage

\`\`\`tsx
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
\`\`\`
        `,
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
    value: {
      control: 'text',
      description: 'Currently selected tab value',
    },
    onValueChange: {
      action: 'valueChanged',
      description: 'Callback when tab selection changes',
    },
  },
} satisfies Meta<typeof AppleTabBar>

export default meta
type Story = StoryObj<typeof meta>

function TabBarDemo({ initialValue = 'home' }: { initialValue?: string }) {
  const [value, setValue] = useState(initialValue)
  
  return (
    <div className="relative h-screen bg-gradient-to-b from-background to-accent/20">
      <div className="container mx-auto p-8">
        <h1 className="text-3xl font-bold mb-4">iOS Tab Bar Navigation</h1>
        <p className="text-muted-foreground mb-8">
          Current tab: <span className="font-semibold text-foreground">{value}</span>
        </p>
        
        <div className="bg-card rounded-xl p-6 shadow-lg">
          <h2 className="text-xl font-semibold mb-2">Content Area</h2>
          <p className="text-muted-foreground">
            This is where your main content would go. The tab bar is fixed at the bottom.
          </p>
        </div>
      </div>
      
      <AppleTabBar value={value} onValueChange={setValue}>
        <AppleTabBarItem value="home" icon={<Home className="w-6 h-6" />} label="Home" />
        <AppleTabBarItem value="search" icon={<Search className="w-6 h-6" />} label="Search" />
        <AppleTabBarItem value="notifications" icon={<Bell className="w-6 h-6" />} label="Alerts" />
        <AppleTabBarItem value="profile" icon={<User className="w-6 h-6" />} label="Profile" />
      </AppleTabBar>
    </div>
  )
}

export const Default: Story = {
  render: () => <TabBarDemo />,
}

export const WithBadges: Story = {
  render: () => {
    const [value, setValue] = useState('home')
    
    return (
      <div className="relative h-screen bg-gradient-to-b from-background to-accent/20">
        <div className="container mx-auto p-8">
          <h1 className="text-3xl font-bold mb-4">Tab Bar with Badges</h1>
          <p className="text-muted-foreground mb-8">
            Badges show notification counts on tabs
          </p>
        </div>
        
        <AppleTabBar value={value} onValueChange={setValue}>
          <AppleTabBarItem value="home" icon={<Home className="w-6 h-6" />} label="Home" />
          <AppleTabBarItem 
            value="search" 
            icon={<Search className="w-6 h-6" />} 
            label="Search" 
            badge={5}
          />
          <AppleTabBarItem 
            value="notifications" 
            icon={<Bell className="w-6 h-6" />} 
            label="Alerts" 
            badge={12}
          />
          <AppleTabBarItem 
            value="profile" 
            icon={<User className="w-6 h-6" />} 
            label="Profile" 
            badge={1}
          />
        </AppleTabBar>
      </div>
    )
  },
}

export const FiveTabs: Story = {
  render: () => {
    const [value, setValue] = useState('home')
    
    return (
      <div className="relative h-screen bg-gradient-to-b from-background to-accent/20">
        <div className="container mx-auto p-8">
          <h1 className="text-3xl font-bold mb-4">Five Tab Layout</h1>
          <p className="text-muted-foreground mb-8">
            iOS supports up to 5 tabs in the tab bar
          </p>
        </div>
        
        <AppleTabBar value={value} onValueChange={setValue}>
          <AppleTabBarItem value="home" icon={<Home className="w-6 h-6" />} label="Home" />
          <AppleTabBarItem value="search" icon={<Search className="w-6 h-6" />} label="Search" />
          <AppleTabBarItem 
            value="notifications" 
            icon={<Bell className="w-6 h-6" />} 
            label="Alerts" 
            badge={3}
          />
          <AppleTabBarItem value="settings" icon={<Settings className="w-6 h-6" />} label="Settings" />
          <AppleTabBarItem value="profile" icon={<User className="w-6 h-6" />} label="Profile" />
        </AppleTabBar>
      </div>
    )
  },
}

export const WithDisabledTab: Story = {
  render: () => {
    const [value, setValue] = useState('home')
    
    return (
      <div className="relative h-screen bg-gradient-to-b from-background to-accent/20">
        <div className="container mx-auto p-8">
          <h1 className="text-3xl font-bold mb-4">Disabled Tab</h1>
          <p className="text-muted-foreground mb-8">
            Some tabs can be disabled based on user permissions or state
          </p>
        </div>
        
        <AppleTabBar value={value} onValueChange={setValue}>
          <AppleTabBarItem value="home" icon={<Home className="w-6 h-6" />} label="Home" />
          <AppleTabBarItem value="search" icon={<Search className="w-6 h-6" />} label="Search" />
          <AppleTabBarItem 
            value="notifications" 
            icon={<Bell className="w-6 h-6" />} 
            label="Alerts" 
            disabled
          />
          <AppleTabBarItem value="profile" icon={<User className="w-6 h-6" />} label="Profile" />
        </AppleTabBar>
      </div>
    )
  },
}

export const LargeBadgeNumbers: Story = {
  render: () => {
    const [value, setValue] = useState('home')
    
    return (
      <div className="relative h-screen bg-gradient-to-b from-background to-accent/20">
        <div className="container mx-auto p-8">
          <h1 className="text-3xl font-bold mb-4">Large Badge Numbers</h1>
          <p className="text-muted-foreground mb-8">
            Badges show "99+" for numbers over 99
          </p>
        </div>
        
        <AppleTabBar value={value} onValueChange={setValue}>
          <AppleTabBarItem value="home" icon={<Home className="w-6 h-6" />} label="Home" />
          <AppleTabBarItem 
            value="search" 
            icon={<Search className="w-6 h-6" />} 
            label="Search" 
            badge={42}
          />
          <AppleTabBarItem 
            value="notifications" 
            icon={<Bell className="w-6 h-6" />} 
            label="Alerts" 
            badge={150}
          />
          <AppleTabBarItem value="profile" icon={<User className="w-6 h-6" />} label="Profile" />
        </AppleTabBar>
      </div>
    )
  },
}

export const DarkMode: Story = {
  render: () => {
    const [value, setValue] = useState('home')
    
    return (
      <div className="dark relative h-screen bg-gradient-to-b from-background to-accent/20">
        <div className="container mx-auto p-8">
          <h1 className="text-3xl font-bold mb-4">Dark Mode</h1>
          <p className="text-muted-foreground mb-8">
            Tab bar adapts to dark mode with proper contrast
          </p>
        </div>
        
        <AppleTabBar value={value} onValueChange={setValue}>
          <AppleTabBarItem value="home" icon={<Home className="w-6 h-6" />} label="Home" />
          <AppleTabBarItem 
            value="search" 
            icon={<Search className="w-6 h-6" />} 
            label="Search" 
            badge={5}
          />
          <AppleTabBarItem 
            value="notifications" 
            icon={<Bell className="w-6 h-6" />} 
            label="Alerts" 
            badge={12}
          />
          <AppleTabBarItem value="profile" icon={<User className="w-6 h-6" />} label="Profile" />
        </AppleTabBar>
      </div>
    )
  },
}
