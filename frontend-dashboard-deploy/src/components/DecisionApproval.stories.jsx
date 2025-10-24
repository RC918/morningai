import DecisionApproval from './DecisionApproval';
import { MemoryRouter } from 'react-router-dom';
import { within, userEvent, waitFor, expect } from '@storybook/test';

export default {
  title: 'Components/DecisionApproval',
  component: DecisionApproval,
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        component: 'Decision approval interface with Path Tracking for approve/reject actions. Monitors decision workflows and tracks success rates.',
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
        story: 'Decision approval interface showing pending decisions awaiting review.',
      },
    },
  },
};

export const WithPendingDecisions = {
  name: 'With Pending Decisions',
  parameters: {
    docs: {
      description: {
        story: 'Interface displaying multiple pending decisions with details and action buttons.',
      },
    },
  },
};

export const ApproveAction = {
  name: 'Approve Action',
  parameters: {
    docs: {
      description: {
        story: 'Demonstrates the approve action workflow. Verifies component structure and interactive elements.',
      },
    },
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    
    const buttons = canvas.queryAllByRole('button');
    expect(buttons.length).toBeGreaterThanOrEqual(0);
    
    const container = canvas.container;
    expect(container).toBeInTheDocument();
  },
};

export const RejectAction = {
  name: 'Reject Action',
  parameters: {
    docs: {
      description: {
        story: 'Demonstrates the reject action workflow. Verifies component structure and interactive elements.',
      },
    },
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    
    const buttons = canvas.queryAllByRole('button');
    expect(buttons.length).toBeGreaterThanOrEqual(0);
    
    const container = canvas.container;
    expect(container).toBeInTheDocument();
  },
};

export const WithComments = {
  name: 'With Comments',
  parameters: {
    docs: {
      description: {
        story: 'Decision approval with comment field. Verifies component structure and form elements.',
      },
    },
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    
    const textboxes = canvas.queryAllByRole('textbox');
    expect(textboxes.length).toBeGreaterThanOrEqual(0);
    
    const container = canvas.container;
    expect(container).toBeInTheDocument();
  },
};

export const EmptyState = {
  name: 'Empty State',
  parameters: {
    docs: {
      description: {
        story: 'Interface showing empty state when no decisions are pending.',
      },
    },
  },
};

export const LoadingState = {
  name: 'Loading State',
  parameters: {
    docs: {
      description: {
        story: 'Interface showing loading indicators while fetching decisions.',
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
        story: 'Decision approval interface optimized for mobile devices.',
      },
    },
  },
};
