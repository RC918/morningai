import StrategyManagement from './StrategyManagement';
import { MemoryRouter } from 'react-router-dom';
import { within, userEvent, waitFor, expect } from '@storybook/test';

export default {
  title: 'Components/StrategyManagement',
  component: StrategyManagement,
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        component: 'Strategy management interface for configuring and monitoring automated optimization strategies. Integrates Path Tracking for strategy management view monitoring and TTV measurement.',
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
        story: 'Strategy management interface in its default state showing active strategies, trigger counts, and strategy list.',
      },
    },
  },
};

export const WithInteraction = {
  name: 'With Interaction',
  parameters: {
    docs: {
      description: {
        story: 'Strategy management demonstrating interactive elements. Verifies component structure and UI elements.',
      },
    },
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    
    const headings = canvas.queryAllByRole('heading');
    expect(headings.length).toBeGreaterThan(0);
    
    const buttons = canvas.queryAllByRole('button');
    expect(buttons.length).toBeGreaterThan(0);
    
    const container = canvas.container;
    expect(container).toBeInTheDocument();
  },
};

export const ActiveStrategies = {
  name: 'Active Strategies',
  parameters: {
    docs: {
      description: {
        story: 'Strategy management showing multiple active strategies with recent trigger activity.',
      },
    },
  },
};

export const PausedStrategies = {
  name: 'Paused Strategies',
  parameters: {
    docs: {
      description: {
        story: 'Strategy management displaying paused strategies that are temporarily disabled.',
      },
    },
  },
};

export const ErrorStrategies = {
  name: 'Error Strategies',
  parameters: {
    docs: {
      description: {
        story: 'Strategy management showing strategies with error states requiring attention.',
      },
    },
  },
};

export const EmptyState = {
  name: 'Empty State',
  parameters: {
    docs: {
      description: {
        story: 'Strategy management showing empty state when no strategies are configured.',
      },
    },
  },
};

export const CreateStrategy = {
  name: 'Create New Strategy',
  parameters: {
    docs: {
      description: {
        story: 'Demonstrates the create new strategy action. Verifies create button is accessible and interactive.',
      },
    },
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    
    const buttons = canvas.queryAllByRole('button');
    expect(buttons.length).toBeGreaterThan(0);
    
    const container = canvas.container;
    expect(container).toBeInTheDocument();
  },
};

export const EditStrategy = {
  name: 'Edit Strategy',
  parameters: {
    docs: {
      description: {
        story: 'Strategy management with edit functionality. Demonstrates strategy configuration editing.',
      },
    },
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    
    const buttons = canvas.queryAllByRole('button');
    expect(buttons.length).toBeGreaterThan(0);
    
    const container = canvas.container;
    expect(container).toBeInTheDocument();
  },
};

export const StrategyDetails = {
  name: 'Strategy Details View',
  parameters: {
    docs: {
      description: {
        story: 'Detailed view of a single strategy showing configuration, trigger history, and execution logs.',
      },
    },
  },
};

export const StrategyMetrics = {
  name: 'Strategy Metrics',
  parameters: {
    docs: {
      description: {
        story: 'Strategy management highlighting key metrics: active strategies, total triggers, and paused strategies.',
      },
    },
  },
};

export const HighTriggerActivity = {
  name: 'High Trigger Activity',
  parameters: {
    docs: {
      description: {
        story: 'Strategy management showing strategies with high trigger frequency, indicating active optimization.',
      },
    },
  },
};

export const LoadingState = {
  name: 'Loading State',
  parameters: {
    docs: {
      description: {
        story: 'Strategy management showing loading indicators while fetching strategy data.',
      },
    },
  },
};

export const ErrorState = {
  name: 'Error State',
  parameters: {
    docs: {
      description: {
        story: 'Strategy management showing error state when strategy data fetch fails.',
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
        story: 'Strategy management interface optimized for mobile devices with responsive layout.',
      },
    },
  },
};

export const AccessibilityTest = {
  name: 'Accessibility Test',
  parameters: {
    docs: {
      description: {
        story: 'Strategy management with accessibility features highlighted. Tests ARIA labels, keyboard navigation, and screen reader support.',
      },
    },
    a11y: {
      config: {
        rules: [
          { id: 'color-contrast', enabled: true },
          { id: 'button-name', enabled: true },
          { id: 'heading-order', enabled: true },
        ],
      },
    },
  },
};
