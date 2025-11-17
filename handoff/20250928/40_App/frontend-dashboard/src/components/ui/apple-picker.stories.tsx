import type { Meta, StoryObj } from '@storybook/react'
import { ApplePicker, createDatePickerColumns, createTimePickerColumns, PickerColumn } from './apple-picker'
import { useState } from 'react'

const meta: Meta<typeof ApplePicker> = {
  title: 'Apple Components/ApplePicker',
  component: ApplePicker,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'iOS-style wheel picker component with 3D perspective effects and smooth scrolling.'
      }
    }
  },
  tags: ['autodocs']
}

export default meta
type Story = StoryObj<typeof ApplePicker>

export const SingleColumn: Story = {
  render: () => {
    const [value, setValue] = useState<Record<string, string | number>>({})

    const columns: PickerColumn[] = [
      {
        id: 'fruit',
        options: [
          { value: 'apple', label: 'Apple' },
          { value: 'banana', label: 'Banana' },
          { value: 'cherry', label: 'Cherry' },
          { value: 'date', label: 'Date' },
          { value: 'elderberry', label: 'Elderberry' },
          { value: 'fig', label: 'Fig' },
          { value: 'grape', label: 'Grape' },
          { value: 'honeydew', label: 'Honeydew' }
        ],
        selectedIndex: 0
      }
    ]

    return (
      <div className="space-y-4">
        <ApplePicker columns={columns} onChange={setValue} />
        <div className="text-center text-sm text-neutral-600">
          Selected: {value.fruit || 'None'}
        </div>
      </div>
    )
  }
}

export const TwoColumns: Story = {
  render: () => {
    const [value, setValue] = useState<Record<string, string | number>>({})

    const columns: PickerColumn[] = [
      {
        id: 'size',
        options: [
          { value: 'xs', label: 'XS' },
          { value: 's', label: 'S' },
          { value: 'm', label: 'M' },
          { value: 'l', label: 'L' },
          { value: 'xl', label: 'XL' },
          { value: 'xxl', label: 'XXL' }
        ],
        selectedIndex: 2
      },
      {
        id: 'color',
        options: [
          { value: 'red', label: 'Red' },
          { value: 'blue', label: 'Blue' },
          { value: 'green', label: 'Green' },
          { value: 'yellow', label: 'Yellow' },
          { value: 'black', label: 'Black' },
          { value: 'white', label: 'White' }
        ],
        selectedIndex: 0
      }
    ]

    return (
      <div className="space-y-4">
        <ApplePicker columns={columns} onChange={setValue} />
        <div className="text-center text-sm text-neutral-600">
          Selected: {value.size} / {value.color}
        </div>
      </div>
    )
  }
}

export const ThreeColumns: Story = {
  render: () => {
    const [value, setValue] = useState<Record<string, string | number>>({})

    const columns: PickerColumn[] = [
      {
        id: 'hours',
        options: Array.from({ length: 12 }, (_, i) => ({
          value: i + 1,
          label: String(i + 1)
        })),
        selectedIndex: 11
      },
      {
        id: 'minutes',
        options: Array.from({ length: 60 }, (_, i) => ({
          value: i,
          label: String(i).padStart(2, '0')
        })),
        selectedIndex: 0
      },
      {
        id: 'period',
        options: [
          { value: 'AM', label: 'AM' },
          { value: 'PM', label: 'PM' }
        ],
        selectedIndex: 0
      }
    ]

    return (
      <div className="space-y-4">
        <ApplePicker columns={columns} onChange={setValue} />
        <div className="text-center text-sm text-neutral-600">
          Selected: {value.hours}:{String(value.minutes).padStart(2, '0')} {value.period}
        </div>
      </div>
    )
  }
}

export const DatePicker: Story = {
  render: () => {
    const [value, setValue] = useState<Record<string, string | number>>({})
    const columns = createDatePickerColumns(new Date())

    return (
      <div className="space-y-4">
        <ApplePicker columns={columns} onChange={setValue} />
        <div className="text-center text-sm text-neutral-600">
          Selected: {value.month !== undefined ? Number(value.month) + 1 : ''}/{value.day}/{value.year}
        </div>
      </div>
    )
  }
}

export const TimePicker: Story = {
  render: () => {
    const [value, setValue] = useState<Record<string, string | number>>({})
    const columns = createTimePickerColumns({ hour: 14, minute: 30 })

    return (
      <div className="space-y-4">
        <ApplePicker columns={columns} onChange={setValue} />
        <div className="text-center text-sm text-neutral-600">
          Selected: {String(value.hour).padStart(2, '0')}:{String(value.minute).padStart(2, '0')}
        </div>
      </div>
    )
  }
}

export const NumberRange: Story = {
  render: () => {
    const [value, setValue] = useState<Record<string, string | number>>({})

    const columns: PickerColumn[] = [
      {
        id: 'number',
        options: Array.from({ length: 100 }, (_, i) => ({
          value: i,
          label: String(i)
        })),
        selectedIndex: 50
      }
    ]

    return (
      <div className="space-y-4">
        <ApplePicker columns={columns} onChange={setValue} />
        <div className="text-center text-sm text-neutral-600">
          Selected: {value.number}
        </div>
      </div>
    )
  }
}

export const CustomHeight: Story = {
  render: () => {
    const [value, setValue] = useState<Record<string, string | number>>({})

    const columns: PickerColumn[] = [
      {
        id: 'item',
        options: [
          { value: '1', label: 'Item 1' },
          { value: '2', label: 'Item 2' },
          { value: '3', label: 'Item 3' },
          { value: '4', label: 'Item 4' },
          { value: '5', label: 'Item 5' }
        ],
        selectedIndex: 2
      }
    ]

    return (
      <div className="space-y-4">
        <ApplePicker 
          columns={columns} 
          onChange={setValue}
          height={300}
          itemHeight={50}
          visibleItems={5}
        />
        <div className="text-center text-sm text-neutral-600">
          Selected: {value.item}
        </div>
      </div>
    )
  }
}

export const CompactSize: Story = {
  render: () => {
    const [value, setValue] = useState<Record<string, string | number>>({})

    const columns: PickerColumn[] = [
      {
        id: 'option',
        options: [
          { value: 'a', label: 'Option A' },
          { value: 'b', label: 'Option B' },
          { value: 'c', label: 'Option C' },
          { value: 'd', label: 'Option D' }
        ],
        selectedIndex: 0
      }
    ]

    return (
      <div className="space-y-4">
        <ApplePicker 
          columns={columns} 
          onChange={setValue}
          height={144}
          itemHeight={32}
          visibleItems={3}
        />
        <div className="text-center text-sm text-neutral-600">
          Selected: {value.option}
        </div>
      </div>
    )
  }
}

export const CountrySelector: Story = {
  render: () => {
    const [value, setValue] = useState<Record<string, string | number>>({})

    const columns: PickerColumn[] = [
      {
        id: 'country',
        options: [
          { value: 'us', label: 'United States' },
          { value: 'uk', label: 'United Kingdom' },
          { value: 'ca', label: 'Canada' },
          { value: 'au', label: 'Australia' },
          { value: 'de', label: 'Germany' },
          { value: 'fr', label: 'France' },
          { value: 'jp', label: 'Japan' },
          { value: 'cn', label: 'China' },
          { value: 'in', label: 'India' },
          { value: 'br', label: 'Brazil' }
        ],
        selectedIndex: 0
      }
    ]

    return (
      <div className="space-y-4">
        <ApplePicker columns={columns} onChange={setValue} />
        <div className="text-center text-sm text-neutral-600">
          Selected: {value.country}
        </div>
      </div>
    )
  }
}

export const HeightWeightPicker: Story = {
  render: () => {
    const [value, setValue] = useState<Record<string, string | number>>({})

    const columns: PickerColumn[] = [
      {
        id: 'feet',
        options: Array.from({ length: 8 }, (_, i) => ({
          value: i + 1,
          label: `${i + 1} ft`
        })),
        selectedIndex: 4
      },
      {
        id: 'inches',
        options: Array.from({ length: 12 }, (_, i) => ({
          value: i,
          label: `${i} in`
        })),
        selectedIndex: 0
      }
    ]

    return (
      <div className="space-y-4">
        <ApplePicker columns={columns} onChange={setValue} />
        <div className="text-center text-sm text-neutral-600">
          Selected: {value.feet} {value.inches}
        </div>
      </div>
    )
  }
}

export const Interactive: Story = {
  render: () => {
    const InteractiveDemo = () => {
      const [value, setValue] = useState<Record<string, string | number>>({})
      const [showPicker, setShowPicker] = useState(false)

      const columns: PickerColumn[] = [
        {
          id: 'category',
          options: [
            { value: 'work', label: 'Work' },
            { value: 'personal', label: 'Personal' },
            { value: 'urgent', label: 'Urgent' },
            { value: 'low', label: 'Low Priority' }
          ],
          selectedIndex: 0
        }
      ]

      return (
        <div className="space-y-4">
          <button
            onClick={() => setShowPicker(!showPicker)}
            className="px-6 py-3 bg-primary-600 text-white rounded-xl font-medium hover:bg-primary-700 transition-colors"
          >
            {showPicker ? 'Hide' : 'Show'} Picker
          </button>
          
          {showPicker && (
            <ApplePicker columns={columns} onChange={setValue} />
          )}
          
          <div className="text-center text-sm text-neutral-600">
            Selected: {value.category || 'None'}
          </div>
        </div>
      )
    }

    return <InteractiveDemo />
  }
}

export const MultiColumnComplex: Story = {
  render: () => {
    const [value, setValue] = useState<Record<string, string | number>>({})

    const columns: PickerColumn[] = [
      {
        id: 'day',
        options: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map(day => ({
          value: day.toLowerCase(),
          label: day
        })),
        selectedIndex: 0
      },
      {
        id: 'hour',
        options: Array.from({ length: 24 }, (_, i) => ({
          value: i,
          label: String(i).padStart(2, '0')
        })),
        selectedIndex: 9
      },
      {
        id: 'minute',
        options: Array.from({ length: 60 }, (_, i) => ({
          value: i,
          label: String(i).padStart(2, '0')
        })),
        selectedIndex: 0
      }
    ]

    return (
      <div className="space-y-4">
        <ApplePicker columns={columns} onChange={setValue} />
        <div className="text-center text-sm text-neutral-600">
          Selected: {value.day} {String(value.hour).padStart(2, '0')}:{String(value.minute).padStart(2, '0')}
        </div>
      </div>
    )
  }
}
