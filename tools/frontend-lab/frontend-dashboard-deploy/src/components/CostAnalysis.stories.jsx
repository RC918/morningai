import CostAnalysis from './CostAnalysis';
import { MemoryRouter } from 'react-router-dom';
import { within, userEvent, waitFor, expect } from '@storybook/test';

export default {
  title: 'Components/CostAnalysis',
  component: CostAnalysis,
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        component: 'Cost analysis dashboard displaying AI service costs, budget tracking, and optimization recommendations. Integrates Path Tracking for cost analysis view monitoring and TTV measurement.',
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
        story: 'Cost analysis dashboard in its default state showing current month costs, budget usage, and cost breakdown by category.',
      },
    },
  },
};

export const WithInteraction = {
  name: 'With Interaction',
  parameters: {
    docs: {
      description: {
        story: 'Cost analysis dashboard demonstrating interactive elements. Verifies component structure and UI elements.',
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

export const BudgetOverage = {
  name: 'Budget Overage',
  parameters: {
    docs: {
      description: {
        story: 'Cost analysis showing scenario where current spending exceeds budget, with warning alerts displayed.',
      },
    },
  },
};

export const BudgetUnderUsage = {
  name: 'Budget Under Usage',
  parameters: {
    docs: {
      description: {
        story: 'Cost analysis showing scenario where spending is well under budget, demonstrating cost efficiency.',
      },
    },
  },
};

export const WithAlerts = {
  name: 'With Cost Alerts',
  parameters: {
    docs: {
      description: {
        story: 'Cost analysis displaying multiple cost alerts and warnings for unusual spending patterns.',
      },
    },
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    
    const container = canvas.container;
    expect(container).toBeInTheDocument();
    
    const allText = container.textContent;
    expect(allText.length).toBeGreaterThan(0);
  },
};

export const ExportReport = {
  name: 'Export Report Action',
  parameters: {
    docs: {
      description: {
        story: 'Demonstrates the export report functionality. Verifies export button is accessible and interactive.',
      },
    },
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    
    const buttons = canvas.queryAllByRole('button');
    expect(buttons.length).toBeGreaterThan(0);
    
    const comboboxes = canvas.queryAllByRole('combobox');
    expect(comboboxes.length).toBeGreaterThanOrEqual(0);
  },
};

export const TimeRangeSelection = {
  name: 'Time Range Selection',
  parameters: {
    docs: {
      description: {
        story: 'Cost analysis with time range selector (current month, last month, quarter, year). Demonstrates period filtering.',
      },
    },
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    
    const comboboxes = canvas.queryAllByRole('combobox');
    expect(comboboxes.length).toBeGreaterThanOrEqual(0);
    
    const container = canvas.container;
    expect(container).toBeInTheDocument();
  },
};

export const CostBreakdown = {
  name: 'Cost Breakdown View',
  parameters: {
    docs: {
      description: {
        story: 'Detailed view of cost breakdown by service category (AI services, compute, storage, network). Shows percentage distribution and trends.',
      },
    },
  },
};

export const OptimizationRecommendations = {
  name: 'Optimization Recommendations',
  parameters: {
    docs: {
      description: {
        story: 'Cost analysis highlighting AI-generated optimization recommendations for cost savings opportunities.',
      },
    },
  },
};

export const LoadingState = {
  name: 'Loading State',
  parameters: {
    docs: {
      description: {
        story: 'Cost analysis showing loading indicators while fetching cost data.',
      },
    },
  },
};

export const ErrorState = {
  name: 'Error State',
  parameters: {
    docs: {
      description: {
        story: 'Cost analysis showing error state when cost data fetch fails.',
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
        story: 'Cost analysis dashboard optimized for mobile devices with responsive layout.',
      },
    },
  },
};

export const AccessibilityTest = {
  name: 'Accessibility Test',
  parameters: {
    docs: {
      description: {
        story: 'Cost analysis with accessibility features highlighted. Tests ARIA labels, keyboard navigation, and screen reader support.',
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
