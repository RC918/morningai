import type { Meta, StoryObj } from '@storybook/react';
import { LazyImage, ResponsiveImage } from './lazy-image';

const meta = {
  title: 'UI/LazyImage',
  component: LazyImage,
  parameters: {
    layout: 'padded',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof LazyImage>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <div className="w-full max-w-md">
      <LazyImage
        src="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=800&h=600&fit=crop"
        alt="Abstract gradient background"
        className="w-full h-64 object-cover rounded-lg"
      />
    </div>
  ),
};

export const WithPlaceholder: Story = {
  render: () => (
    <div className="w-full max-w-md">
      <LazyImage
        src="https://images.unsplash.com/photo-1557683316-973673baf926?w=800&h=600&fit=crop"
        alt="Gradient mesh background"
        className="w-full h-64 object-cover rounded-lg"
        placeholderClassName="bg-gradient-to-br from-blue-100 to-purple-100"
      />
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'LazyImage with custom placeholder gradient.',
      },
    },
  },
};

export const MultipleImages: Story = {
  render: () => (
    <div className="space-y-8">
      {[
        {
          src: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=800&h=400&fit=crop',
          alt: 'Image 1',
        },
        {
          src: 'https://images.unsplash.com/photo-1557683316-973673baf926?w=800&h=400&fit=crop',
          alt: 'Image 2',
        },
        {
          src: 'https://images.unsplash.com/photo-1579546929518-9e396f3cc809?w=800&h=400&fit=crop',
          alt: 'Image 3',
        },
        {
          src: 'https://images.unsplash.com/photo-1557682250-33bd709cbe85?w=800&h=400&fit=crop',
          alt: 'Image 4',
        },
      ].map((image, index) => (
        <LazyImage
          key={index}
          src={image.src}
          alt={image.alt}
          className="w-full h-48 object-cover rounded-lg"
        />
      ))}
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Multiple images with lazy loading. Scroll down to see images load as they enter the viewport.',
      },
    },
  },
};

export const ErrorState: Story = {
  render: () => (
    <div className="w-full max-w-md">
      <LazyImage
        src="https://invalid-url-that-will-fail.com/image.jpg"
        alt="This image will fail to load"
        className="w-full h-64 rounded-lg"
      />
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'LazyImage with error state when image fails to load.',
      },
    },
  },
};

export const CustomAspectRatio: Story = {
  render: () => (
    <div className="grid grid-cols-2 gap-4 max-w-2xl">
      <LazyImage
        src="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=400&h=400&fit=crop"
        alt="Square image"
        className="w-full aspect-square object-cover rounded-lg"
      />
      <LazyImage
        src="https://images.unsplash.com/photo-1557683316-973673baf926?w=400&h=600&fit=crop"
        alt="Portrait image"
        className="w-full aspect-[2/3] object-cover rounded-lg"
      />
      <LazyImage
        src="https://images.unsplash.com/photo-1579546929518-9e396f3cc809?w=600&h=400&fit=crop"
        alt="Landscape image"
        className="w-full aspect-[3/2] object-cover rounded-lg col-span-2"
      />
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'LazyImage with different aspect ratios.',
      },
    },
  },
};

export const ResponsiveImageExample: Story = {
  render: () => (
    <div className="w-full max-w-2xl">
      <ResponsiveImage
        src="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=800&h=600&fit=crop"
        alt="Responsive image with multiple sources"
        sources={[
          {
            srcSet: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=400&h=300&fit=crop',
            media: '(max-width: 640px)',
            type: 'image/webp',
          },
          {
            srcSet: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=800&h=600&fit=crop',
            media: '(max-width: 1024px)',
            type: 'image/webp',
          },
          {
            srcSet: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=1200&h=900&fit=crop',
            media: '(min-width: 1025px)',
            type: 'image/webp',
          },
        ]}
        className="w-full h-auto rounded-lg"
      />
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'ResponsiveImage component with multiple sources for different screen sizes.',
      },
    },
  },
};

export const Grid: Story = {
  render: () => (
    <div className="grid grid-cols-3 gap-4 max-w-4xl">
      {Array.from({ length: 9 }).map((_, index) => (
        <LazyImage
          key={index}
          src={`https://images.unsplash.com/photo-${1618005182384 + index}?w=400&h=400&fit=crop`}
          alt={`Grid image ${index + 1}`}
          className="w-full aspect-square object-cover rounded-lg"
        />
      ))}
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Grid of lazy-loaded images.',
      },
    },
  },
};
