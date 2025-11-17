import React, { useState, useRef, useEffect, useCallback } from 'react'
import { motion, useMotionValue, useTransform, animate } from 'framer-motion'
import { cn } from '@/lib/utils'
import { triggerHaptic } from '@/lib/spring-animation'
import { useScreenReaderAnnouncement } from '@/hooks/use-accessibility'

export type PickerOption = {
  value: string | number
  label: string
}

export type PickerColumn = {
  id: string
  options: PickerOption[]
  selectedIndex?: number
}

export type ApplePickerProps = {
  columns: PickerColumn[]
  onChange?: (values: Record<string, string | number>) => void
  height?: number
  itemHeight?: number
  visibleItems?: number
  className?: string
}

const PickerItem = ({
  option,
  index,
  y,
  itemHeight,
  halfVisible,
  currentIndex,
  getOffsetFromIndex,
  snapToIndex
}: {
  option: PickerOption
  index: number
  y: any
  itemHeight: number
  halfVisible: number
  currentIndex: number
  getOffsetFromIndex: (index: number) => number
  snapToIndex: (index: number) => void
}) => {
  const offset = useTransform(
    y,
    (value: number) => {
      const itemOffset = getOffsetFromIndex(index)
      const distance = (value - itemOffset) / itemHeight
      return distance
    }
  )

  const opacity = useTransform(
    offset,
    [-halfVisible, -1, 0, 1, halfVisible],
    [0.3, 0.5, 1, 0.5, 0.3]
  )

  const scale = useTransform(
    offset,
    [-halfVisible, -1, 0, 1, halfVisible],
    [0.7, 0.85, 1, 0.85, 0.7]
  )

  const rotateX = useTransform(
    offset,
    [-halfVisible, 0, halfVisible],
    [30, 0, -30]
  )

  return (
    <motion.div
      key={option.value}
      id={`picker-option-${index}`}
      role="option"
      aria-selected={index === currentIndex}
      style={{
        opacity,
        scale,
        rotateX,
        height: itemHeight
      }}
      className="flex items-center justify-center text-base font-medium text-neutral-900 dark:text-white cursor-pointer"
      onClick={() => snapToIndex(index)}
    >
      {option.label}
    </motion.div>
  )
}

const PickerWheel = ({
  options,
  selectedIndex = 0,
  onChange,
  height = 216,
  itemHeight = 36,
  visibleItems = 5,
  columnId
}: {
  options: PickerOption[]
  selectedIndex?: number
  onChange?: (index: number) => void
  height?: number
  itemHeight?: number
  visibleItems?: number
  columnId?: string
}) => {
  const wheelRef = useRef<HTMLDivElement>(null)
  const y = useMotionValue(0)
  const [currentIndex, setCurrentIndex] = useState(selectedIndex)
  const isDragging = useRef(false)
  const startY = useRef(0)
  const startOffset = useRef(0)
  const { announce } = useScreenReaderAnnouncement()

  const getOffsetFromIndex = (index: number) => {
    return -index * itemHeight
  }

  const getIndexFromOffset = (offset: number) => {
    const index = Math.round(-offset / itemHeight)
    return Math.max(0, Math.min(options.length - 1, index))
  }

  const snapToIndex = useCallback((index: number) => {
    const targetOffset = getOffsetFromIndex(index)
    
    animate(y, targetOffset, {
      type: 'spring',
      stiffness: 300,
      damping: 30,
      mass: 0.8
    })

    setCurrentIndex(index)
    
    if (wheelRef.current) {
      triggerHaptic(wheelRef.current, 'light')
    }
    
    const selectedOption = options[index]
    if (selectedOption) {
      const message = columnId 
        ? `${columnId}: ${selectedOption.label}` 
        : selectedOption.label
      announce(message, 'polite')
    }
    
    if (onChange) {
      onChange(index)
    }
  }, [y, itemHeight, onChange, options, columnId, announce])

  const handleDragStart = (e: React.PointerEvent) => {
    isDragging.current = true
    startY.current = e.clientY
    startOffset.current = y.get()
  }

  const handleDrag = (e: React.PointerEvent) => {
    if (!isDragging.current) return
    
    const deltaY = e.clientY - startY.current
    const newOffset = startOffset.current + deltaY
    
    const maxOffset = 0
    const minOffset = -(options.length - 1) * itemHeight
    
    let constrainedOffset = newOffset
    if (newOffset > maxOffset) {
      constrainedOffset = maxOffset + (newOffset - maxOffset) * 0.3
    } else if (newOffset < minOffset) {
      constrainedOffset = minOffset + (newOffset - minOffset) * 0.3
    }
    
    y.set(constrainedOffset)
  }

  const handleDragEnd = () => {
    if (!isDragging.current) return
    isDragging.current = false
    
    const currentOffset = y.get()
    const targetIndex = getIndexFromOffset(currentOffset)
    snapToIndex(targetIndex)
  }

  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault()
    const delta = e.deltaY > 0 ? 1 : -1
    const newIndex = Math.max(0, Math.min(options.length - 1, currentIndex + delta))
    snapToIndex(newIndex)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowUp') {
      e.preventDefault()
      const newIndex = Math.max(0, currentIndex - 1)
      snapToIndex(newIndex)
    } else if (e.key === 'ArrowDown') {
      e.preventDefault()
      const newIndex = Math.min(options.length - 1, currentIndex + 1)
      snapToIndex(newIndex)
    }
  }

  useEffect(() => {
    y.set(getOffsetFromIndex(selectedIndex))
    setCurrentIndex(selectedIndex)
  }, [selectedIndex])

  const halfVisible = Math.floor(visibleItems / 2)

  return (
    <div
      ref={wheelRef}
      role="listbox"
      aria-label={columnId ? `${columnId} picker` : 'Picker'}
      aria-activedescendant={`picker-option-${currentIndex}`}
      tabIndex={0}
      onKeyDown={handleKeyDown}
      className="relative overflow-hidden select-none focus:outline-none focus:ring-2 focus:ring-primary-500 rounded-xl"
      style={{ height }}
      onPointerDown={handleDragStart}
      onPointerMove={handleDrag}
      onPointerUp={handleDragEnd}
      onPointerLeave={handleDragEnd}
      onWheel={handleWheel}
    >
      {/* Selection indicator */}
      <div
        className="absolute left-0 right-0 pointer-events-none z-10"
        style={{
          top: `${(height - itemHeight) / 2}px`,
          height: `${itemHeight}px`
        }}
      >
        <div className="absolute inset-0 border-t border-b border-neutral-300 dark:border-neutral-600" />
      </div>

      {/* Gradient overlays */}
      <div className="absolute inset-x-0 top-0 h-20 bg-gradient-to-b from-white dark:from-gray-900 to-transparent pointer-events-none z-10" />
      <div className="absolute inset-x-0 bottom-0 h-20 bg-gradient-to-t from-white dark:from-gray-900 to-transparent pointer-events-none z-10" />

      {/* Options */}
      <motion.div
        style={{ y }}
        className="relative"
        drag="y"
        dragConstraints={{ top: -(options.length - 1) * itemHeight, bottom: 0 }}
        dragElastic={0.1}
        onDragEnd={() => {
          const currentOffset = y.get()
          const targetIndex = getIndexFromOffset(currentOffset)
          snapToIndex(targetIndex)
        }}
      >
        <div style={{ paddingTop: `${(height - itemHeight) / 2}px`, paddingBottom: `${(height - itemHeight) / 2}px` }}>
          {options.map((option, index) => (
            <PickerItem
              key={option.value}
              option={option}
              index={index}
              y={y}
              itemHeight={itemHeight}
              halfVisible={halfVisible}
              currentIndex={currentIndex}
              getOffsetFromIndex={getOffsetFromIndex}
              snapToIndex={snapToIndex}
            />
          ))}
        </div>
      </motion.div>
    </div>
  )
}

export const ApplePicker = ({
  columns,
  onChange,
  height = 216,
  itemHeight = 36,
  visibleItems = 5,
  className
}: ApplePickerProps) => {
  const [selectedValues, setSelectedValues] = useState<Record<string, string | number>>(() => {
    const initial: Record<string, string | number> = {}
    columns.forEach(col => {
      const index = col.selectedIndex || 0
      initial[col.id] = col.options[index]?.value || ''
    })
    return initial
  })

  const handleColumnChange = useCallback((columnId: string, index: number, options: PickerOption[]) => {
    const newValue = options[index]?.value
    if (newValue !== undefined) {
      setSelectedValues(prev => {
        const updated = { ...prev, [columnId]: newValue }
        if (onChange) {
          onChange(updated)
        }
        return updated
      })
    }
  }, [onChange])

  return (
    <div className={cn('flex gap-2 bg-white dark:bg-neutral-900 rounded-2xl p-4', className)}>
      {columns.map((column) => (
        <div key={column.id} className="flex-1">
          <PickerWheel
            options={column.options}
            selectedIndex={column.selectedIndex || 0}
            onChange={(index) => handleColumnChange(column.id, index, column.options)}
            height={height}
            itemHeight={itemHeight}
            visibleItems={visibleItems}
            columnId={column.id}
          />
        </div>
      ))}
    </div>
  )
}

export const createDatePickerColumns = (
  selectedDate: Date = new Date()
): PickerColumn[] => {
  const months = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ]

  const days = Array.from({ length: 31 }, (_, i) => ({
    value: i + 1,
    label: String(i + 1)
  }))

  const years = Array.from({ length: 100 }, (_, i) => {
    const year = new Date().getFullYear() - 50 + i
    return { value: year, label: String(year) }
  })

  return [
    {
      id: 'month',
      options: months.map((month, i) => ({ value: i, label: month })),
      selectedIndex: selectedDate.getMonth()
    },
    {
      id: 'day',
      options: days,
      selectedIndex: selectedDate.getDate() - 1
    },
    {
      id: 'year',
      options: years,
      selectedIndex: years.findIndex(y => y.value === selectedDate.getFullYear())
    }
  ]
}

export const createTimePickerColumns = (
  selectedTime: { hour: number; minute: number } = { hour: 12, minute: 0 }
): PickerColumn[] => {
  const hours = Array.from({ length: 24 }, (_, i) => ({
    value: i,
    label: String(i).padStart(2, '0')
  }))

  const minutes = Array.from({ length: 60 }, (_, i) => ({
    value: i,
    label: String(i).padStart(2, '0')
  }))

  return [
    {
      id: 'hour',
      options: hours,
      selectedIndex: selectedTime.hour
    },
    {
      id: 'minute',
      options: minutes,
      selectedIndex: selectedTime.minute
    }
  ]
}
