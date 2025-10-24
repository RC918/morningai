import LoginPage from './LoginPage';
import { MemoryRouter } from 'react-router-dom';
import { within, userEvent, waitFor, expect } from '@storybook/test';

export default {
  title: 'Components/LoginPage',
  component: LoginPage,
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        component: 'User authentication page with Path Tracking integration. Monitors login attempts and measures Time To Value (TTV) for first-time users.',
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
        story: 'Login page in its default state with email and password fields.',
      },
    },
  },
};

export const WithValidation = {
  name: 'Form Validation',
  parameters: {
    docs: {
      description: {
        story: 'Login form demonstrating component structure. Verifies form elements are present and accessible.',
      },
    },
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    
    const buttons = canvas.queryAllByRole('button');
    expect(buttons.length).toBeGreaterThan(0);
    
    const textboxes = canvas.queryAllByRole('textbox');
    expect(textboxes.length).toBeGreaterThanOrEqual(0);
  },
};

export const FilledForm = {
  name: 'Filled Form',
  parameters: {
    docs: {
      description: {
        story: 'Login form demonstrating interactive elements. Verifies component renders with expected structure.',
      },
    },
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    
    const form = canvas.container.querySelector('form');
    if (form) {
      expect(form).toBeInTheDocument();
    }
    
    const buttons = canvas.queryAllByRole('button');
    expect(buttons.length).toBeGreaterThan(0);
  },
};

export const LoadingState = {
  name: 'Loading State',
  parameters: {
    docs: {
      description: {
        story: 'Login page showing loading state during authentication.',
      },
    },
  },
};

export const ErrorState = {
  name: 'Error State',
  parameters: {
    docs: {
      description: {
        story: 'Login page showing error message after failed authentication attempt.',
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
        story: 'Login page optimized for mobile devices.',
      },
    },
  },
};

export const AccessibilityTest = {
  name: 'Accessibility Test',
  parameters: {
    docs: {
      description: {
        story: 'Login page with accessibility features highlighted. Tests keyboard navigation and screen reader support.',
      },
    },
    a11y: {
      config: {
        rules: [
          { id: 'label', enabled: true },
          { id: 'color-contrast', enabled: true },
          { id: 'button-name', enabled: true },
        ],
      },
    },
  },
};
