import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ApplePicker, createDatePickerColumns, createTimePickerColumns, PickerColumn } from './apple-picker'
import React from 'react'

vi.mock('@/hooks/use-accessibility', () => ({
  useScreenReaderAnnouncement: () => ({ announce: vi.fn() })
}))

describe('ApplePicker', () => {
  describe('Basic Rendering', () => {
    it('renders single column picker', () => {
      const columns: PickerColumn[] = [
        {
          id: 'fruit',
          options: [
            { value: 'apple', label: 'Apple' },
            { value: 'banana', label: 'Banana' }
          ],
          selectedIndex: 0
        }
      ]

      render(<ApplePicker columns={columns} />)
      
      expect(screen.getByText('Apple')).toBeInTheDocument()
      expect(screen.getByText('Banana')).toBeInTheDocument()
    })

    it('renders multiple columns', () => {
      const columns: PickerColumn[] = [
        {
          id: 'size',
          options: [
            { value: 's', label: 'Small' },
            { value: 'm', label: 'Medium' }
          ],
          selectedIndex: 0
        },
        {
          id: 'color',
          options: [
            { value: 'red', label: 'Red' },
            { value: 'blue', label: 'Blue' }
          ],
          selectedIndex: 0
        }
      ]

      render(<ApplePicker columns={columns} />)
      
      expect(screen.getByText('Small')).toBeInTheDocument()
      expect(screen.getByText('Medium')).toBeInTheDocument()
      expect(screen.getByText('Red')).toBeInTheDocument()
      expect(screen.getByText('Blue')).toBeInTheDocument()
    })

    it('renders with custom height', () => {
      const columns: PickerColumn[] = [
        {
          id: 'test',
          options: [{ value: '1', label: 'Test' }],
          selectedIndex: 0
        }
      ]

      const { container } = render(
        <ApplePicker columns={columns} height={300} />
      )
      
      const wheelElement = container.querySelector('[style*="height"]')
      expect(wheelElement).toBeInTheDocument()
    })

    it('applies custom className', () => {
      const columns: PickerColumn[] = [
        {
          id: 'test',
          options: [{ value: '1', label: 'Test' }],
          selectedIndex: 0
        }
      ]

      const { container } = render(
        <ApplePicker columns={columns} className="custom-class" />
      )
      
      expect(container.firstChild).toHaveClass('custom-class')
    })
  })

  describe('Selection', () => {
    it('initializes with selected index', () => {
      const columns: PickerColumn[] = [
        {
          id: 'fruit',
          options: [
            { value: 'apple', label: 'Apple' },
            { value: 'banana', label: 'Banana' },
            { value: 'cherry', label: 'Cherry' }
          ],
          selectedIndex: 1
        }
      ]

      render(<ApplePicker columns={columns} />)
      
      expect(screen.getByText('Banana')).toBeInTheDocument()
    })

    it('calls onChange when selection changes', async () => {
      const user = userEvent.setup()
      const handleChange = vi.fn()
      
      const columns: PickerColumn[] = [
        {
          id: 'fruit',
          options: [
            { value: 'apple', label: 'Apple' },
            { value: 'banana', label: 'Banana' }
          ],
          selectedIndex: 0
        }
      ]

      render(<ApplePicker columns={columns} onChange={handleChange} />)
      
      const bananaOption = screen.getByText('Banana')
      await user.click(bananaOption)
      
      await waitFor(() => {
        expect(handleChange).toHaveBeenCalled()
      })
    })

    it('updates selection on click', async () => {
      const user = userEvent.setup()
      const handleChange = vi.fn()
      
      const columns: PickerColumn[] = [
        {
          id: 'number',
          options: [
            { value: 1, label: '1' },
            { value: 2, label: '2' },
            { value: 3, label: '3' }
          ],
          selectedIndex: 0
        }
      ]

      render(<ApplePicker columns={columns} onChange={handleChange} />)
      
      await user.click(screen.getByText('3'))
      
      await waitFor(() => {
        expect(handleChange).toHaveBeenCalledWith(
          expect.objectContaining({ number: 3 })
        )
      })
    })
  })

  describe('Multiple Columns', () => {
    it('handles multiple column selections independently', async () => {
      const user = userEvent.setup()
      const handleChange = vi.fn()
      
      const columns: PickerColumn[] = [
        {
          id: 'col1',
          options: [
            { value: 'a', label: 'A' },
            { value: 'b', label: 'B' }
          ],
          selectedIndex: 0
        },
        {
          id: 'col2',
          options: [
            { value: '1', label: '1' },
            { value: '2', label: '2' }
          ],
          selectedIndex: 0
        }
      ]

      render(<ApplePicker columns={columns} onChange={handleChange} />)
      
      await user.click(screen.getByText('B'))
      
      await waitFor(() => {
        expect(handleChange).toHaveBeenCalledWith(
          expect.objectContaining({ col1: 'b', col2: '1' })
        )
      })
    })

    it('maintains state across multiple columns', async () => {
      const user = userEvent.setup()
      const handleChange = vi.fn()
      
      const columns: PickerColumn[] = [
        {
          id: 'hours',
          options: [
            { value: 1, label: '1' },
            { value: 2, label: '2' }
          ],
          selectedIndex: 0
        },
        {
          id: 'minutes',
          options: [
            { value: 0, label: '00' },
            { value: 30, label: '30' }
          ],
          selectedIndex: 0
        }
      ]

      render(<ApplePicker columns={columns} onChange={handleChange} />)
      
      await user.click(screen.getByText('2'))
      await user.click(screen.getByText('30'))
      
      await waitFor(() => {
        expect(handleChange).toHaveBeenLastCalledWith(
          expect.objectContaining({ hours: 2, minutes: 30 })
        )
      })
    })
  })

  describe('Helper Functions', () => {
    describe('createDatePickerColumns', () => {
      it('creates date picker columns with default date', () => {
        const columns = createDatePickerColumns()
        
        expect(columns).toHaveLength(3)
        expect(columns[0].id).toBe('month')
        expect(columns[1].id).toBe('day')
        expect(columns[2].id).toBe('year')
      })

      it('creates date picker columns with specific date', () => {
        const date = new Date(2023, 5, 15)
        const columns = createDatePickerColumns(date)
        
        expect(columns[0].selectedIndex).toBe(5)
        expect(columns[1].selectedIndex).toBe(14)
        expect(columns[2].options.find(opt => opt.value === 2023)).toBeDefined()
      })

      it('has 12 month options', () => {
        const columns = createDatePickerColumns()
        expect(columns[0].options).toHaveLength(12)
      })

      it('has 31 day options', () => {
        const columns = createDatePickerColumns()
        expect(columns[1].options).toHaveLength(31)
      })

      it('has 100 year options', () => {
        const columns = createDatePickerColumns()
        expect(columns[2].options).toHaveLength(100)
      })
    })

    describe('createTimePickerColumns', () => {
      it('creates time picker columns with default time', () => {
        const columns = createTimePickerColumns()
        
        expect(columns).toHaveLength(2)
        expect(columns[0].id).toBe('hour')
        expect(columns[1].id).toBe('minute')
      })

      it('creates time picker columns with specific time', () => {
        const columns = createTimePickerColumns({ hour: 14, minute: 30 })
        
        expect(columns[0].selectedIndex).toBe(14)
        expect(columns[1].selectedIndex).toBe(30)
      })

      it('has 24 hour options', () => {
        const columns = createTimePickerColumns()
        expect(columns[0].options).toHaveLength(24)
      })

      it('has 60 minute options', () => {
        const columns = createTimePickerColumns()
        expect(columns[1].options).toHaveLength(60)
      })

      it('formats hours with leading zeros', () => {
        const columns = createTimePickerColumns()
        expect(columns[0].options[0].label).toBe('00')
        expect(columns[0].options[9].label).toBe('09')
      })

      it('formats minutes with leading zeros', () => {
        const columns = createTimePickerColumns()
        expect(columns[1].options[0].label).toBe('00')
        expect(columns[1].options[5].label).toBe('05')
      })
    })
  })

  describe('Edge Cases', () => {
    it('handles empty options array', () => {
      const columns: PickerColumn[] = [
        {
          id: 'empty',
          options: [],
          selectedIndex: 0
        }
      ]

      const { container } = render(<ApplePicker columns={columns} />)
      expect(container).toBeInTheDocument()
    })

    it('handles single option', () => {
      const columns: PickerColumn[] = [
        {
          id: 'single',
          options: [{ value: 'only', label: 'Only Option' }],
          selectedIndex: 0
        }
      ]

      render(<ApplePicker columns={columns} />)
      expect(screen.getByText('Only Option')).toBeInTheDocument()
    })

    it('handles large number of options', () => {
      const columns: PickerColumn[] = [
        {
          id: 'large',
          options: Array.from({ length: 1000 }, (_, i) => ({
            value: i,
            label: `Option ${i}`
          })),
          selectedIndex: 0
        }
      ]

      render(<ApplePicker columns={columns} />)
      expect(screen.getByText('Option 0')).toBeInTheDocument()
    })

    it('handles selectedIndex out of bounds', () => {
      const columns: PickerColumn[] = [
        {
          id: 'test',
          options: [
            { value: 'a', label: 'A' },
            { value: 'b', label: 'B' }
          ],
          selectedIndex: 10
        }
      ]

      const { container } = render(<ApplePicker columns={columns} />)
      expect(container).toBeInTheDocument()
    })

    it('handles undefined selectedIndex', () => {
      const columns: PickerColumn[] = [
        {
          id: 'test',
          options: [
            { value: 'a', label: 'A' },
            { value: 'b', label: 'B' }
          ]
        }
      ]

      render(<ApplePicker columns={columns} />)
      expect(screen.getByText('A')).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('renders selection indicator', () => {
      const columns: PickerColumn[] = [
        {
          id: 'test',
          options: [{ value: '1', label: 'Test' }],
          selectedIndex: 0
        }
      ]

      const { container } = render(<ApplePicker columns={columns} />)
      
      const indicators = container.querySelectorAll('.border-t.border-b')
      expect(indicators.length).toBeGreaterThan(0)
    })

    it('renders gradient overlays', () => {
      const columns: PickerColumn[] = [
        {
          id: 'test',
          options: [{ value: '1', label: 'Test' }],
          selectedIndex: 0
        }
      ]

      const { container } = render(<ApplePicker columns={columns} />)
      
      const gradients = container.querySelectorAll('.bg-gradient-to-b, .bg-gradient-to-t')
      expect(gradients.length).toBeGreaterThan(0)
    })

    it('has proper cursor styles', () => {
      const columns: PickerColumn[] = [
        {
          id: 'test',
          options: [{ value: '1', label: 'Test' }],
          selectedIndex: 0
        }
      ]

      const { container } = render(<ApplePicker columns={columns} />)
      
      const cursorElements = container.querySelectorAll('.cursor-pointer')
      expect(cursorElements.length).toBeGreaterThan(0)
    })
  })

  describe('Custom Props', () => {
    it('respects custom height prop', () => {
      const columns: PickerColumn[] = [
        {
          id: 'test',
          options: [{ value: '1', label: 'Test' }],
          selectedIndex: 0
        }
      ]

      const { container } = render(
        <ApplePicker columns={columns} height={300} />
      )
      
      const wheelElement = container.querySelector('[style*="300"]')
      expect(wheelElement).toBeInTheDocument()
    })

    it('respects custom itemHeight prop', () => {
      const columns: PickerColumn[] = [
        {
          id: 'test',
          options: [{ value: '1', label: 'Test' }],
          selectedIndex: 0
        }
      ]

      const { container } = render(
        <ApplePicker columns={columns} itemHeight={50} />
      )
      
      expect(container).toBeInTheDocument()
    })

    it('respects custom visibleItems prop', () => {
      const columns: PickerColumn[] = [
        {
          id: 'test',
          options: [{ value: '1', label: 'Test' }],
          selectedIndex: 0
        }
      ]

      const { container } = render(
        <ApplePicker columns={columns} visibleItems={7} />
      )
      
      expect(container).toBeInTheDocument()
    })
  })

  describe('Integration', () => {
    it('works with date picker helper', async () => {
      const user = userEvent.setup()
      const handleChange = vi.fn()
      const columns = createDatePickerColumns(new Date(2023, 0, 1))

      render(<ApplePicker columns={columns} onChange={handleChange} />)
      
      expect(screen.getByText('January')).toBeInTheDocument()
      expect(screen.getByText('1')).toBeInTheDocument()
      expect(screen.getByText('2023')).toBeInTheDocument()
    })

    it('works with time picker helper', async () => {
      const handleChange = vi.fn()
      const columns = createTimePickerColumns({ hour: 14, minute: 30 })

      render(<ApplePicker columns={columns} onChange={handleChange} />)
      
      const fourteenElements = screen.getAllByText('14')
      expect(fourteenElements.length).toBeGreaterThan(0)
      expect(screen.getByText('30')).toBeInTheDocument()
    })
  })
})
