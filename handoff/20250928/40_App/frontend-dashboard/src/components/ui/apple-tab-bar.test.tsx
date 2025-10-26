import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { AppleTabBar, AppleTabBarItem } from './apple-tab-bar'
import { Home, Search, Bell, User } from 'lucide-react'

describe('AppleTabBar', () => {
  it('renders tab bar with items', () => {
    render(
      <AppleTabBar value="home" onValueChange={vi.fn()}>
        <AppleTabBarItem value="home" icon={<Home />} label="Home" />
        <AppleTabBarItem value="search" icon={<Search />} label="Search" />
      </AppleTabBar>
    )
    
    expect(screen.getByRole('tablist')).toBeInTheDocument()
    expect(screen.getByLabelText('Home')).toBeInTheDocument()
    expect(screen.getByLabelText('Search')).toBeInTheDocument()
  })

  it('marks active tab with aria-selected', () => {
    render(
      <AppleTabBar value="search" onValueChange={vi.fn()}>
        <AppleTabBarItem value="home" icon={<Home />} label="Home" />
        <AppleTabBarItem value="search" icon={<Search />} label="Search" />
      </AppleTabBar>
    )
    
    const homeTab = screen.getByLabelText('Home')
    const searchTab = screen.getByLabelText('Search')
    
    expect(homeTab).toHaveAttribute('aria-selected', 'false')
    expect(searchTab).toHaveAttribute('aria-selected', 'true')
  })

  it('calls onValueChange when tab is clicked', () => {
    const handleChange = vi.fn()
    
    render(
      <AppleTabBar value="home" onValueChange={handleChange}>
        <AppleTabBarItem value="home" icon={<Home />} label="Home" />
        <AppleTabBarItem value="search" icon={<Search />} label="Search" />
      </AppleTabBar>
    )
    
    fireEvent.click(screen.getByLabelText('Search'))
    expect(handleChange).toHaveBeenCalledWith('search')
  })

  it('does not call onValueChange when disabled tab is clicked', () => {
    const handleChange = vi.fn()
    
    render(
      <AppleTabBar value="home" onValueChange={handleChange}>
        <AppleTabBarItem value="home" icon={<Home />} label="Home" />
        <AppleTabBarItem value="search" icon={<Search />} label="Search" disabled />
      </AppleTabBar>
    )
    
    fireEvent.click(screen.getByLabelText('Search'))
    expect(handleChange).not.toHaveBeenCalled()
  })

  it('renders badge when provided', () => {
    render(
      <AppleTabBar value="home" onValueChange={vi.fn()}>
        <AppleTabBarItem value="home" icon={<Home />} label="Home" />
        <AppleTabBarItem value="notifications" icon={<Bell />} label="Alerts" badge={5} />
      </AppleTabBar>
    )
    
    expect(screen.getByText('5')).toBeInTheDocument()
  })

  it('renders "99+" for badges over 99', () => {
    render(
      <AppleTabBar value="home" onValueChange={vi.fn()}>
        <AppleTabBarItem value="home" icon={<Home />} label="Home" />
        <AppleTabBarItem value="notifications" icon={<Bell />} label="Alerts" badge={150} />
      </AppleTabBar>
    )
    
    expect(screen.getByText('99+')).toBeInTheDocument()
  })

  it('does not render badge when value is 0', () => {
    render(
      <AppleTabBar value="home" onValueChange={vi.fn()}>
        <AppleTabBarItem value="home" icon={<Home />} label="Home" />
        <AppleTabBarItem value="notifications" icon={<Bell />} label="Alerts" badge={0} />
      </AppleTabBar>
    )
    
    expect(screen.queryByText('0')).not.toBeInTheDocument()
  })

  it('applies disabled styles to disabled tabs', () => {
    render(
      <AppleTabBar value="home" onValueChange={vi.fn()}>
        <AppleTabBarItem value="home" icon={<Home />} label="Home" />
        <AppleTabBarItem value="search" icon={<Search />} label="Search" disabled />
      </AppleTabBar>
    )
    
    const disabledTab = screen.getByLabelText('Search')
    expect(disabledTab).toBeDisabled()
  })

  it('renders multiple tabs correctly', () => {
    render(
      <AppleTabBar value="home" onValueChange={vi.fn()}>
        <AppleTabBarItem value="home" icon={<Home />} label="Home" />
        <AppleTabBarItem value="search" icon={<Search />} label="Search" />
        <AppleTabBarItem value="notifications" icon={<Bell />} label="Alerts" />
        <AppleTabBarItem value="profile" icon={<User />} label="Profile" />
      </AppleTabBar>
    )
    
    expect(screen.getAllByRole('tab')).toHaveLength(4)
  })

  it('handles custom className', () => {
    render(
      <AppleTabBar value="home" onValueChange={vi.fn()} className="custom-class">
        <AppleTabBarItem value="home" icon={<Home />} label="Home" />
      </AppleTabBar>
    )
    
    const tablist = screen.getByRole('tablist')
    expect(tablist).toHaveClass('custom-class')
  })

  it('handles custom onClick handler', () => {
    const handleClick = vi.fn()
    const handleChange = vi.fn()
    
    render(
      <AppleTabBar value="home" onValueChange={handleChange}>
        <AppleTabBarItem 
          value="search" 
          icon={<Search />} 
          label="Search" 
          onClick={handleClick}
        />
      </AppleTabBar>
    )
    
    fireEvent.click(screen.getByLabelText('Search'))
    expect(handleClick).toHaveBeenCalled()
    expect(handleChange).toHaveBeenCalledWith('search')
  })

  it('has proper accessibility attributes', () => {
    render(
      <AppleTabBar value="home" onValueChange={vi.fn()}>
        <AppleTabBarItem value="home" icon={<Home />} label="Home" />
        <AppleTabBarItem value="search" icon={<Search />} label="Search" />
      </AppleTabBar>
    )
    
    const tablist = screen.getByRole('tablist')
    expect(tablist).toHaveAttribute('aria-label', 'Main navigation')
    
    const tabs = screen.getAllByRole('tab')
    tabs.forEach(tab => {
      expect(tab).toHaveAttribute('aria-selected')
      expect(tab).toHaveAttribute('aria-label')
    })
  })
})
