import type { Meta, StoryObj } from '@storybook/react';
import { Tooltip, TooltipTrigger, TooltipContent } from './tooltip';
import { Button } from './button';
import { Info, HelpCircle, Settings } from 'lucide-react';

const meta = {
  title: 'UI/Tooltip',
  component: Tooltip,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof Tooltip>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button variant="outline">Hover me</Button>
      </TooltipTrigger>
      <TooltipContent>
        <p>This is a tooltip</p>
      </TooltipContent>
    </Tooltip>
  ),
};

export const WithIcon: Story = {
  render: () => (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button variant="ghost" size="icon">
          <Info className="h-4 w-4" />
        </Button>
      </TooltipTrigger>
      <TooltipContent>
        <p>Click for more information</p>
      </TooltipContent>
    </Tooltip>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Tooltip on an icon button.',
      },
    },
  },
};

export const Positions: Story = {
  render: () => (
    <div className="flex flex-col items-center gap-16">
      <Tooltip>
        <TooltipTrigger asChild>
          <Button variant="outline">Top</Button>
        </TooltipTrigger>
        <TooltipContent side="top">
          <p>Tooltip on top</p>
        </TooltipContent>
      </Tooltip>
      
      <div className="flex gap-16">
        <Tooltip>
          <TooltipTrigger asChild>
            <Button variant="outline">Left</Button>
          </TooltipTrigger>
          <TooltipContent side="left">
            <p>Tooltip on left</p>
          </TooltipContent>
        </Tooltip>
        
        <Tooltip>
          <TooltipTrigger asChild>
            <Button variant="outline">Right</Button>
          </TooltipTrigger>
          <TooltipContent side="right">
            <p>Tooltip on right</p>
          </TooltipContent>
        </Tooltip>
      </div>
      
      <Tooltip>
        <TooltipTrigger asChild>
          <Button variant="outline">Bottom</Button>
        </TooltipTrigger>
        <TooltipContent side="bottom">
          <p>Tooltip on bottom</p>
        </TooltipContent>
      </Tooltip>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Tooltips can be positioned on all four sides.',
      },
    },
  },
};

export const LongContent: Story = {
  render: () => (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button variant="outline">Hover for details</Button>
      </TooltipTrigger>
      <TooltipContent className="max-w-xs">
        <p>
          This tooltip contains longer content that wraps to multiple lines. 
          The max-width ensures it doesn't become too wide and remains readable.
        </p>
      </TooltipContent>
    </Tooltip>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Tooltip with longer content that wraps to multiple lines.',
      },
    },
  },
};

export const OnText: Story = {
  render: () => (
    <p className="text-sm">
      This is some text with a{' '}
      <Tooltip>
        <TooltipTrigger asChild>
          <span className="underline decoration-dotted cursor-help">technical term</span>
        </TooltipTrigger>
        <TooltipContent>
          <p>A detailed explanation of the technical term</p>
        </TooltipContent>
      </Tooltip>
      {' '}that needs explanation.
    </p>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Tooltip on inline text with dotted underline.',
      },
    },
  },
};

export const MultipleTooltips: Story = {
  render: () => (
    <div className="flex gap-4">
      <Tooltip>
        <TooltipTrigger asChild>
          <Button variant="ghost" size="icon">
            <HelpCircle className="h-4 w-4" />
          </Button>
        </TooltipTrigger>
        <TooltipContent>
          <p>Get help</p>
        </TooltipContent>
      </Tooltip>
      
      <Tooltip>
        <TooltipTrigger asChild>
          <Button variant="ghost" size="icon">
            <Settings className="h-4 w-4" />
          </Button>
        </TooltipTrigger>
        <TooltipContent>
          <p>Open settings</p>
        </TooltipContent>
      </Tooltip>
      
      <Tooltip>
        <TooltipTrigger asChild>
          <Button variant="ghost" size="icon">
            <Info className="h-4 w-4" />
          </Button>
        </TooltipTrigger>
        <TooltipContent>
          <p>View information</p>
        </TooltipContent>
      </Tooltip>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Multiple tooltips on different elements.',
      },
    },
  },
};

export const CustomOffset: Story = {
  render: () => (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button variant="outline">Custom offset</Button>
      </TooltipTrigger>
      <TooltipContent sideOffset={10}>
        <p>This tooltip has a custom offset of 10px</p>
      </TooltipContent>
    </Tooltip>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Tooltip with custom sideOffset to control distance from trigger.',
      },
    },
  },
};
