import Dashboard from './Dashboard';
import { MemoryRouter } from 'react-router-dom';
import { within, userEvent, waitFor, expect } from '@storybook/test';

export default {
  title: 'Components/Dashboard',
  component: Dashboard,
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        component: 'Main dashboard component displaying key metrics, recent activities, and quick actions. Integrates Path Tracking for user journey monitoring and TTV (Time To Value) measurement.',
      },
    },
  },
  decorators: [
    (Story) => (
      <MemoryRouter>
        <Story />
      </MemoryRouter>
    ),
  ],
  tags: ['autodocs'],
};

export const Default = {
  name: 'Default State',
  parameters: {
    docs: {
      description: {
        story: 'Dashboard in its default state with sample data. Shows metrics cards, recent activities, and quick action buttons.',
      },
    },
  },
};

export const WithPathTracking = {
  name: 'With Path Tracking',
  parameters: {
    docs: {
      description: {
        story: 'Dashboard with Path Tracking enabled. Monitors user interactions and sends data to Sentry for analytics.',
      },
    },
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    
    const saveButton = await canvas.findByRole('button', { name: /save/i });
    await userEvent.click(saveButton);
    
    await waitFor(() => {
      expect(canvas.getByText(/saved successfully/i)).toBeInTheDocument();
    });
  },
};

export const LoadingState = {
  name: 'Loading State',
  parameters: {
    docs: {
      description: {
        story: 'Dashboard showing loading indicators while data is being fetched.',
      },
    },
  },
};

export const ErrorState = {
  name: 'Error State',
  parameters: {
    docs: {
      description: {
        story: 'Dashboard showing error state when data fetch fails.',
      },
    },
  },
};

export const MobileView = {
  name: 'Mobile View',
  parameters: {
    viewport: {
      defaultViewport: 'mobile1',
    },
    docs: {
      description: {
        story: 'Dashboard optimized for mobile devices with responsive layout.',
      },
    },
  },
};
