import * as React from 'react'
import type { Meta, StoryObj } from '@storybook/react'
import { Slider } from './slider'
import { Label } from './label'

const meta = {
  title: 'Components/Slider',
  component: Slider,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    min: {
      control: 'number',
      description: 'Minimum value',
    },
    max: {
      control: 'number',
      description: 'Maximum value',
    },
    step: {
      control: 'number',
      description: 'Step increment',
    },
    disabled: {
      control: 'boolean',
      description: 'Whether the slider is disabled',
    },
  },
} satisfies Meta<typeof Slider>

export default meta
type Story = StoryObj<typeof meta>

export const Default: Story = {
  args: {
    defaultValue: [50],
    max: 100,
    step: 1,
    className: 'w-[300px]',
    thumbLabel: 'Default slider',
  },
}

export const WithLabel: Story = {
  render: () => {
    const [value, setValue] = React.useState([50])
    return (
      <div className="grid gap-4 w-[300px]">
        <div className="flex items-center justify-between">
          <Label htmlFor="volume">Volume</Label>
          <span className="text-sm text-muted-foreground">{value[0]}%</span>
        </div>
        <Slider id="volume" value={value} onValueChange={setValue} max={100} step={1} thumbLabel="Volume" />
      </div>
    )
  },
}

export const Range: Story = {
  render: () => {
    const [value, setValue] = React.useState([25, 75])
    return (
      <div className="grid gap-4 w-[300px]">
        <div className="flex items-center justify-between">
          <Label>Price Range</Label>
          <span className="text-sm text-muted-foreground">${value[0]} - ${value[1]}</span>
        </div>
        <Slider value={value} onValueChange={setValue} max={100} step={1} thumbLabel={['Minimum price', 'Maximum price']} />
      </div>
    )
  },
}

export const Disabled: Story = {
  args: {
    defaultValue: [50],
    max: 100,
    step: 1,
    disabled: true,
    className: 'w-[300px]',
    thumbLabel: 'Disabled slider',
  },
}

export const CustomStep: Story = {
  render: () => (
    <div className="grid gap-4 w-[300px]">
      <div className="flex items-center justify-between">
        <Label>Step: 10</Label>
        <span className="text-sm text-muted-foreground">50</span>
      </div>
      <Slider defaultValue={[50]} max={100} step={10} thumbLabel="Custom step slider" />
    </div>
  ),
}

export const SmallRange: Story = {
  render: () => (
    <div className="grid gap-4 w-[300px]">
      <div className="flex items-center justify-between">
        <Label>Rating (1-5)</Label>
        <span className="text-sm text-muted-foreground">3</span>
      </div>
      <Slider defaultValue={[3]} min={1} max={5} step={1} thumbLabel="Rating slider" />
    </div>
  ),
}

export const AllVariants: Story = {
  render: () => (
    <div className="flex flex-col gap-8 w-[300px]">
      <div className="grid gap-2">
        <Label>Default</Label>
        <Slider defaultValue={[50]} max={100} step={1} thumbLabel="Default slider" />
      </div>
      <div className="grid gap-2">
        <Label>Range Selection</Label>
        <Slider defaultValue={[25, 75]} max={100} step={1} thumbLabel={['Range minimum', 'Range maximum']} />
      </div>
      <div className="grid gap-2">
        <Label>Disabled</Label>
        <Slider defaultValue={[50]} max={100} step={1} disabled thumbLabel="Disabled slider" />
      </div>
      <div className="grid gap-2">
        <Label>Custom Step (25)</Label>
        <Slider defaultValue={[50]} max={100} step={25} thumbLabel="Custom step slider" />
      </div>
    </div>
  ),
}
