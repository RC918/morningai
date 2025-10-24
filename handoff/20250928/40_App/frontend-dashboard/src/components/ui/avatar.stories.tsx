import type { Meta, StoryObj } from '@storybook/react';
import { Avatar, AvatarImage, AvatarFallback } from './avatar';

const meta = {
  title: 'UI/Avatar',
  component: Avatar,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof Avatar>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <Avatar>
      <AvatarImage src="https://api.dicebear.com/7.x/avataaars/svg?seed=Ryan" alt="Ryan Chen" />
      <AvatarFallback>RC</AvatarFallback>
    </Avatar>
  ),
};

export const WithFallback: Story = {
  render: () => (
    <Avatar>
      <AvatarImage src="/invalid-image.jpg" alt="User" />
      <AvatarFallback>JD</AvatarFallback>
    </Avatar>
  ),
  parameters: {
    docs: {
      description: {
        story: 'When the image fails to load, the fallback text is displayed.',
      },
    },
  },
};

export const FallbackOnly: Story = {
  render: () => (
    <Avatar>
      <AvatarFallback>AB</AvatarFallback>
    </Avatar>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Avatar with only fallback text, no image source.',
      },
    },
  },
};

export const CustomSize: Story = {
  render: () => (
    <div className="flex items-center gap-4">
      <Avatar className="size-8">
        <AvatarImage src="https://api.dicebear.com/7.x/avataaars/svg?seed=Small" />
        <AvatarFallback>SM</AvatarFallback>
      </Avatar>
      <Avatar className="size-12">
        <AvatarImage src="https://api.dicebear.com/7.x/avataaars/svg?seed=Medium" />
        <AvatarFallback>MD</AvatarFallback>
      </Avatar>
      <Avatar className="size-16">
        <AvatarImage src="https://api.dicebear.com/7.x/avataaars/svg?seed=Large" />
        <AvatarFallback>LG</AvatarFallback>
      </Avatar>
      <Avatar className="size-24">
        <AvatarImage src="https://api.dicebear.com/7.x/avataaars/svg?seed=XLarge" />
        <AvatarFallback>XL</AvatarFallback>
      </Avatar>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Avatars in different sizes using Tailwind size utilities.',
      },
    },
  },
};

export const CustomColors: Story = {
  render: () => (
    <div className="flex items-center gap-4">
      <Avatar>
        <AvatarFallback className="bg-blue-100 text-blue-600">BL</AvatarFallback>
      </Avatar>
      <Avatar>
        <AvatarFallback className="bg-green-100 text-green-600">GR</AvatarFallback>
      </Avatar>
      <Avatar>
        <AvatarFallback className="bg-purple-100 text-purple-600">PU</AvatarFallback>
      </Avatar>
      <Avatar>
        <AvatarFallback className="bg-red-100 text-red-600">RD</AvatarFallback>
      </Avatar>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Avatars with custom background and text colors.',
      },
    },
  },
};

export const AvatarGroup: Story = {
  render: () => (
    <div className="flex -space-x-4">
      <Avatar className="border-2 border-white">
        <AvatarImage src="https://api.dicebear.com/7.x/avataaars/svg?seed=User1" />
        <AvatarFallback>U1</AvatarFallback>
      </Avatar>
      <Avatar className="border-2 border-white">
        <AvatarImage src="https://api.dicebear.com/7.x/avataaars/svg?seed=User2" />
        <AvatarFallback>U2</AvatarFallback>
      </Avatar>
      <Avatar className="border-2 border-white">
        <AvatarImage src="https://api.dicebear.com/7.x/avataaars/svg?seed=User3" />
        <AvatarFallback>U3</AvatarFallback>
      </Avatar>
      <Avatar className="border-2 border-white">
        <AvatarFallback className="bg-gray-200 text-gray-600">+5</AvatarFallback>
      </Avatar>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Multiple avatars overlapping to show a group of users.',
      },
    },
  },
};

export const WithText: Story = {
  render: () => (
    <div className="flex items-center gap-3">
      <Avatar>
        <AvatarImage src="https://api.dicebear.com/7.x/avataaars/svg?seed=Ryan" />
        <AvatarFallback>RC</AvatarFallback>
      </Avatar>
      <div>
        <p className="text-sm font-medium">Ryan Chen</p>
        <p className="text-xs text-muted-foreground">ryan@morningai.com</p>
      </div>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Avatar combined with user information text.',
      },
    },
  },
};
