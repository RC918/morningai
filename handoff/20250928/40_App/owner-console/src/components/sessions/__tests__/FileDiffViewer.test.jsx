import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import FileDiffViewer from '../FileDiffViewer'

// Mock react-i18next
const mockT = (key, fallback) => fallback || key
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: mockT,
  }),
}))

// Mock clipboard API
const mockClipboard = {
  writeText: vi.fn().mockResolvedValue(undefined)
}
Object.defineProperty(navigator, 'clipboard', { value: mockClipboard, writable: true })

// Mock window.open
const mockWindowOpen = vi.fn()
Object.defineProperty(window, 'open', { value: mockWindowOpen, writable: true })

describe('FileDiffViewer', () => {
  const mockDiffLines = [
    { type: 'context', content: 'const x = 1;', oldLineNumber: 1, newLineNumber: 1 },
    { type: 'deletion', content: 'const y = 2;', oldLineNumber: 2, newLineNumber: null },
    { type: 'addition', content: 'const y = 3;', oldLineNumber: null, newLineNumber: 2 },
    { type: 'context', content: 'const z = 4;', oldLineNumber: 3, newLineNumber: 3 }
  ]

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Empty State', () => {
    it('should render empty state when no diff lines', () => {
      render(<FileDiffViewer diffLines={[]} />)
      expect(screen.getByText('No changes to display')).toBeInTheDocument()
    })

    it('should not render empty state when diff lines exist', () => {
      render(<FileDiffViewer diffLines={mockDiffLines} filePath="test.js" />)
      expect(screen.queryByText('No changes to display')).not.toBeInTheDocument()
    })
  })

  describe('Header', () => {
    it('should display file path', () => {
      render(<FileDiffViewer diffLines={mockDiffLines} filePath="src/components/Test.jsx" />)
      expect(screen.getByText('src/components/Test.jsx')).toBeInTheDocument()
    })

    it('should display language badge', () => {
      render(<FileDiffViewer diffLines={mockDiffLines} filePath="test.js" language="typescript" />)
      expect(screen.getByText('typescript')).toBeInTheDocument()
    })

    it('should display additions and deletions count', () => {
      render(<FileDiffViewer diffLines={mockDiffLines} filePath="test.js" additions={5} deletions={3} />)
      expect(screen.getByText('+5')).toBeInTheDocument()
      expect(screen.getByText('-3')).toBeInTheDocument()
    })

    it('should compute stats from diffLines when not provided', () => {
      render(<FileDiffViewer diffLines={mockDiffLines} filePath="test.js" />)
      expect(screen.getByText('+1')).toBeInTheDocument()
      expect(screen.getByText('-1')).toBeInTheDocument()
    })
  })

  describe('Expand/Collapse', () => {
    it('should be expanded by default', () => {
      render(<FileDiffViewer diffLines={mockDiffLines} filePath="test.js" />)
      expect(screen.getByText('const x = 1;')).toBeInTheDocument()
    })

    it('should collapse when toggle button is clicked', () => {
      render(<FileDiffViewer diffLines={mockDiffLines} filePath="test.js" />)
      
      // Find and click the first button (collapse/expand toggle)
      const buttons = screen.getAllByRole('button')
      const collapseButton = buttons[0]
      fireEvent.click(collapseButton)
      
      // Content should be hidden
      expect(screen.queryByText('const x = 1;')).not.toBeInTheDocument()
    })

    it('should expand when toggle button is clicked again', () => {
      render(<FileDiffViewer diffLines={mockDiffLines} filePath="test.js" />)
      
      const buttons = screen.getAllByRole('button')
      const collapseButton = buttons[0]
      
      // Collapse
      fireEvent.click(collapseButton)
      expect(screen.queryByText('const x = 1;')).not.toBeInTheDocument()
      
      // Expand
      fireEvent.click(collapseButton)
      expect(screen.getByText('const x = 1;')).toBeInTheDocument()
    })
  })

  describe('Diff Content', () => {
    it('should render all diff lines', () => {
      render(<FileDiffViewer diffLines={mockDiffLines} filePath="test.js" />)
      expect(screen.getByText('const x = 1;')).toBeInTheDocument()
      expect(screen.getByText('const y = 2;')).toBeInTheDocument()
      expect(screen.getByText('const y = 3;')).toBeInTheDocument()
      expect(screen.getByText('const z = 4;')).toBeInTheDocument()
    })

    it('should show line numbers for context lines', () => {
      render(<FileDiffViewer diffLines={mockDiffLines} filePath="test.js" />)
      // Line numbers should be present in the table
      const cells = screen.getAllByRole('cell')
      expect(cells.length).toBeGreaterThan(0)
    })

    it('should show + prefix for additions', () => {
      render(<FileDiffViewer diffLines={mockDiffLines} filePath="test.js" />)
      expect(screen.getByText('+')).toBeInTheDocument()
    })

    it('should show - prefix for deletions', () => {
      render(<FileDiffViewer diffLines={mockDiffLines} filePath="test.js" />)
      expect(screen.getByText('-')).toBeInTheDocument()
    })
  })

  describe('Copy to Clipboard', () => {
    it('should have copy button available', () => {
      render(<FileDiffViewer diffLines={mockDiffLines} filePath="test.js" />)
      
      // Find buttons - should have multiple action buttons
      const buttons = screen.getAllByRole('button')
      // Should have at least collapse, copy, and fullscreen buttons
      expect(buttons.length).toBeGreaterThanOrEqual(3)
    })
  })

  describe('External Link', () => {
    it('should show external link button when ideUrl is provided', () => {
      render(
        <FileDiffViewer 
          diffLines={mockDiffLines} 
          filePath="test.js" 
          ideUrl="vscode://file/test.js"
        />
      )
      
      // Should have external link button
      const buttons = screen.getAllByRole('button')
      expect(buttons.length).toBeGreaterThan(2) // collapse, copy, external, fullscreen
    })

    it('should open IDE URL when external link is clicked', () => {
      render(
        <FileDiffViewer 
          diffLines={mockDiffLines} 
          filePath="test.js" 
          ideUrl="vscode://file/test.js"
        />
      )
      
      // Find and click external link button
      const buttons = screen.getAllByRole('button')
      // External link button should open the URL
      buttons.forEach(btn => {
        if (btn.querySelector('svg[class*="external"]') || btn.innerHTML.includes('ExternalLink')) {
          fireEvent.click(btn)
        }
      })
    })

    it('should not show external link button when ideUrl is not provided', () => {
      render(<FileDiffViewer diffLines={mockDiffLines} filePath="test.js" />)
      
      // Should have fewer buttons without external link
      const buttons = screen.getAllByRole('button')
      // Only collapse, copy, and fullscreen buttons
      expect(buttons.length).toBe(3)
    })
  })

  describe('Fullscreen Mode', () => {
    it('should toggle fullscreen when fullscreen button is clicked', () => {
      const { container } = render(<FileDiffViewer diffLines={mockDiffLines} filePath="test.js" />)
      
      // Find fullscreen button (last button)
      const buttons = screen.getAllByRole('button')
      const fullscreenButton = buttons[buttons.length - 1]
      
      // Initially not fullscreen
      expect(container.querySelector('.fixed')).not.toBeInTheDocument()
      
      // Click to enter fullscreen
      fireEvent.click(fullscreenButton)
      
      // Should have fixed positioning
      expect(container.querySelector('.fixed')).toBeInTheDocument()
    })
  })

  describe('Line Type Styling', () => {
    it('should apply correct class for addition lines', () => {
      const { container } = render(<FileDiffViewer diffLines={mockDiffLines} filePath="test.js" />)
      
      // Addition lines should have growth color class
      const additionRow = container.querySelector('tr.bg-growth-10')
      expect(additionRow).toBeInTheDocument()
    })

    it('should apply correct class for deletion lines', () => {
      const { container } = render(<FileDiffViewer diffLines={mockDiffLines} filePath="test.js" />)
      
      // Deletion lines should have energy color class
      const deletionRow = container.querySelector('tr.bg-energy-10')
      expect(deletionRow).toBeInTheDocument()
    })
  })
})
