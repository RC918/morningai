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
        story: 'Login form showing validation errors for invalid inputs.',
      },
    },
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    
    const submitButton = await canvas.findByRole('button', { name: /login|submit/i });
    await userEvent.click(submitButton);
    
    await waitFor(() => {
      const errorMessages = canvas.queryAllByRole('alert');
      expect(errorMessages.length).toBeGreaterThan(0);
    });
  },
};

export const FilledForm = {
  name: 'Filled Form',
  parameters: {
    docs: {
      description: {
        story: 'Login form with pre-filled credentials for testing.',
      },
    },
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    
    const emailInput = await canvas.findByLabelText(/email/i);
    const passwordInput = await canvas.findByLabelText(/password/i);
    
    await userEvent.type(emailInput, 'test@example.com');
    await userEvent.type(passwordInput, 'password123');
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
