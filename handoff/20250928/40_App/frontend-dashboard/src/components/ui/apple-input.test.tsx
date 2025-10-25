import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AppleInput } from './apple-input';
import { Mail, Lock } from 'lucide-react';

vi.mock('framer-motion', () => ({
  motion: {
    input: ({ children, ...props }: any) => <input {...props}>{children}</input>,
    label: ({ children, ...props }: any) => <label {...props}>{children}</label>,
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
    button: ({ children, ...props }: any) => <button {...props}>{children}</button>,
    p: ({ children, ...props }: any) => <p {...props}>{children}</p>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

vi.mock('@/lib/spring-animation', () => ({
  getSpringConfig: vi.fn(() => ({ duration: 0.3 })),
  triggerHaptic: vi.fn(),
}));

describe('AppleInput', () => {
  describe('Basic Rendering', () => {
    it('renders without crashing', () => {
      render(<AppleInput />);
      expect(screen.getByRole('textbox')).toBeInTheDocument();
    });

    it('renders with label', () => {
      render(<AppleInput label="Email" />);
      expect(screen.getByText('Email')).toBeInTheDocument();
    });

    it('renders with placeholder', () => {
      render(<AppleInput placeholder="Enter email" />);
      expect(screen.getByPlaceholderText('Enter email')).toBeInTheDocument();
    });

    it('renders with default value', () => {
      render(<AppleInput defaultValue="test@example.com" />);
      expect(screen.getByDisplayValue('test@example.com')).toBeInTheDocument();
    });

    it('renders with controlled value', () => {
      render(<AppleInput value="controlled value" onChange={() => {}} />);
      expect(screen.getByDisplayValue('controlled value')).toBeInTheDocument();
    });
  });

  describe('Input Types', () => {
    it('renders text input by default', () => {
      render(<AppleInput />);
      expect(screen.getByRole('textbox')).toHaveAttribute('type', 'text');
    });

    it('renders email input', () => {
      render(<AppleInput type="email" />);
      const input = screen.getByRole('textbox');
      expect(input).toHaveAttribute('type', 'email');
    });

    it('renders password input', () => {
      render(<AppleInput type="password" data-testid="password-input" />);
      const input = screen.getByTestId('password-input') as HTMLInputElement;
      expect(input.type).toBe('password');
    });

    it('renders number input', () => {
      render(<AppleInput type="number" />);
      expect(screen.getByRole('spinbutton')).toBeInTheDocument();
    });

    it('renders search input', () => {
      render(<AppleInput type="search" />);
      expect(screen.getByRole('searchbox')).toBeInTheDocument();
    });
  });

  describe('Variants', () => {
    it('applies default variant classes', () => {
      render(<AppleInput variant="default" />);
      const input = screen.getByRole('textbox');
      expect(input.className).toContain('border-input');
    });

    it('applies filled variant classes', () => {
      render(<AppleInput variant="filled" />);
      const input = screen.getByRole('textbox');
      expect(input.className).toContain('bg-accent');
    });

    it('applies outline variant classes', () => {
      render(<AppleInput variant="outline" />);
      const input = screen.getByRole('textbox');
      expect(input.className).toContain('bg-transparent');
    });
  });

  describe('Sizes', () => {
    it('applies small size classes', () => {
      render(<AppleInput inputSize="sm" />);
      const input = screen.getByRole('textbox');
      expect(input.className).toContain('h-9');
    });

    it('applies default size classes', () => {
      render(<AppleInput inputSize="default" />);
      const input = screen.getByRole('textbox');
      expect(input.className).toContain('h-11');
    });

    it('applies large size classes', () => {
      render(<AppleInput inputSize="lg" />);
      const input = screen.getByRole('textbox');
      expect(input.className).toContain('h-13');
    });
  });

  describe('States', () => {
    it('applies error state classes', () => {
      render(<AppleInput state="error" />);
      const input = screen.getByRole('textbox');
      expect(input.className).toContain('border-destructive');
    });

    it('applies success state classes', () => {
      render(<AppleInput state="success" />);
      const input = screen.getByRole('textbox');
      expect(input.className).toContain('border-green-500');
    });

    it('displays error text', () => {
      render(<AppleInput state="error" errorText="Invalid input" />);
      expect(screen.getByText('Invalid input')).toBeInTheDocument();
    });

    it('displays success text', () => {
      render(<AppleInput state="success" successText="Looks good!" />);
      expect(screen.getByText('Looks good!')).toBeInTheDocument();
    });

    it('error text has alert role', () => {
      render(<AppleInput state="error" errorText="Error message" />);
      const errorText = screen.getByRole('alert');
      expect(errorText).toHaveTextContent('Error message');
    });
  });

  describe('Helper Text', () => {
    it('displays helper text', () => {
      render(<AppleInput helperText="This is helper text" />);
      expect(screen.getByText('This is helper text')).toBeInTheDocument();
    });

    it('prioritizes error text over helper text', () => {
      render(
        <AppleInput
          helperText="Helper text"
          errorText="Error text"
          state="error"
        />
      );
      expect(screen.getByText('Error text')).toBeInTheDocument();
      expect(screen.queryByText('Helper text')).not.toBeInTheDocument();
    });

    it('prioritizes success text over helper text', () => {
      render(
        <AppleInput
          helperText="Helper text"
          successText="Success text"
          state="success"
        />
      );
      expect(screen.getByText('Success text')).toBeInTheDocument();
      expect(screen.queryByText('Helper text')).not.toBeInTheDocument();
    });
  });

  describe('Icons', () => {
    it('renders left icon', () => {
      render(<AppleInput leftIcon={<Mail data-testid="mail-icon" />} />);
      expect(screen.getByTestId('mail-icon')).toBeInTheDocument();
    });

    it('renders right icon', () => {
      render(<AppleInput rightIcon={<Lock data-testid="lock-icon" />} />);
      expect(screen.getByTestId('lock-icon')).toBeInTheDocument();
    });

    it('applies padding when left icon is present', () => {
      render(<AppleInput leftIcon={<Mail />} />);
      const input = screen.getByRole('textbox');
      expect(input.className).toContain('pl-10');
    });

    it('applies padding when right icon is present', () => {
      render(<AppleInput rightIcon={<Lock />} />);
      const input = screen.getByRole('textbox');
      expect(input.className).toContain('pr-10');
    });
  });

  describe('Password Toggle', () => {
    it('renders password toggle button for password type', () => {
      render(<AppleInput type="password" showPasswordToggle />);
      expect(screen.getByLabelText('Show password')).toBeInTheDocument();
    });

    it('does not render password toggle when showPasswordToggle is false', () => {
      render(<AppleInput type="password" showPasswordToggle={false} />);
      expect(screen.queryByLabelText('Show password')).not.toBeInTheDocument();
    });

    it('toggles password visibility on click', async () => {
      render(<AppleInput type="password" showPasswordToggle data-testid="password-toggle-input" />);
      const input = screen.getByTestId('password-toggle-input') as HTMLInputElement;
      const toggleButton = screen.getByLabelText('Show password');

      expect(input.type).toBe('password');

      await userEvent.click(toggleButton);
      expect(input.type).toBe('text');
      expect(screen.getByLabelText('Hide password')).toBeInTheDocument();

      await userEvent.click(toggleButton);
      expect(input.type).toBe('password');
      expect(screen.getByLabelText('Show password')).toBeInTheDocument();
    });
  });

  describe('Required Field', () => {
    it('renders required indicator', () => {
      render(<AppleInput label="Email" required />);
      expect(screen.getByText('*')).toBeInTheDocument();
    });

    it('applies required attribute to input', () => {
      render(<AppleInput required />);
      expect(screen.getByRole('textbox')).toHaveAttribute('required');
    });
  });

  describe('Disabled State', () => {
    it('applies disabled attribute', () => {
      render(<AppleInput disabled />);
      expect(screen.getByRole('textbox')).toBeDisabled();
    });

    it('applies disabled opacity classes', () => {
      render(<AppleInput disabled />);
      const input = screen.getByRole('textbox');
      expect(input.className).toContain('disabled:opacity-50');
    });

    it('disables label when input is disabled', () => {
      render(<AppleInput label="Email" disabled />);
      const label = screen.getByText('Email');
      expect(label.className).toContain('opacity-50');
    });
  });

  describe('Event Handlers', () => {
    it('calls onChange handler', async () => {
      const handleChange = vi.fn();
      render(<AppleInput onChange={handleChange} />);
      const input = screen.getByRole('textbox');

      await userEvent.type(input, 'test');
      expect(handleChange).toHaveBeenCalled();
    });

    it('calls onFocus handler', async () => {
      const handleFocus = vi.fn();
      render(<AppleInput onFocus={handleFocus} />);
      const input = screen.getByRole('textbox');

      await userEvent.click(input);
      expect(handleFocus).toHaveBeenCalled();
    });

    it('calls onBlur handler', async () => {
      const handleBlur = vi.fn();
      render(<AppleInput onBlur={handleBlur} />);
      const input = screen.getByRole('textbox');

      await userEvent.click(input);
      await userEvent.tab();
      expect(handleBlur).toHaveBeenCalled();
    });
  });

  describe('Floating Label', () => {
    it('label floats when input has value', () => {
      render(<AppleInput label="Email" defaultValue="test@example.com" />);
      const label = screen.getByText('Email');
      expect(label.className).toContain('text-xs');
    });

    it('label floats when input is focused', async () => {
      render(<AppleInput label="Email" />);
      const input = screen.getByRole('textbox');
      const label = screen.getByText('Email');

      await userEvent.click(input);
      expect(label.className).toContain('text-xs');
    });

    it('label returns to default when input loses focus and is empty', async () => {
      render(<AppleInput label="Email" />);
      const input = screen.getByRole('textbox');

      await userEvent.click(input);
      await userEvent.tab();
      
      const label = screen.getByText('Email');
      expect(label.className).toContain('text-sm');
    });
  });

  describe('Accessibility', () => {
    it('associates label with input via htmlFor', () => {
      render(<AppleInput label="Email" id="email-input" />);
      const label = screen.getByText('Email');
      const input = screen.getByRole('textbox');
      
      expect(label).toHaveAttribute('for', 'email-input');
      expect(input).toHaveAttribute('id', 'email-input');
    });

    it('error message has aria-live="assertive"', () => {
      render(<AppleInput state="error" errorText="Error message" />);
      const errorText = screen.getByRole('alert');
      expect(errorText).toHaveAttribute('aria-live', 'assertive');
    });

    it('success message has aria-live="polite"', () => {
      render(<AppleInput state="success" successText="Success message" />);
      const successText = screen.getByText('Success message');
      expect(successText).toHaveAttribute('aria-live', 'polite');
    });

    it('supports keyboard navigation', async () => {
      render(<AppleInput />);
      const input = screen.getByRole('textbox');

      await userEvent.tab();
      expect(input).toHaveFocus();
    });

    it('password toggle has accessible label', () => {
      render(<AppleInput type="password" showPasswordToggle />);
      expect(screen.getByLabelText('Show password')).toBeInTheDocument();
    });
  });

  describe('Custom Props', () => {
    it('forwards custom className', () => {
      render(<AppleInput className="custom-class" />);
      const input = screen.getByRole('textbox');
      expect(input.className).toContain('custom-class');
    });

    it('forwards maxLength attribute', () => {
      render(<AppleInput maxLength={10} />);
      expect(screen.getByRole('textbox')).toHaveAttribute('maxLength', '10');
    });

    it('forwards pattern attribute', () => {
      render(<AppleInput pattern="[0-9]*" />);
      expect(screen.getByRole('textbox')).toHaveAttribute('pattern', '[0-9]*');
    });

    it('forwards min and max for number inputs', () => {
      render(<AppleInput type="number" min={0} max={100} />);
      const input = screen.getByRole('spinbutton');
      expect(input).toHaveAttribute('min', '0');
      expect(input).toHaveAttribute('max', '100');
    });

    it('forwards readOnly attribute', () => {
      render(<AppleInput readOnly />);
      expect(screen.getByRole('textbox')).toHaveAttribute('readOnly');
    });
  });

  describe('Edge Cases', () => {
    it('handles empty label gracefully', () => {
      render(<AppleInput label="" />);
      expect(screen.getByRole('textbox')).toBeInTheDocument();
    });

    it('handles very long values', () => {
      const longValue = 'a'.repeat(1000);
      render(<AppleInput defaultValue={longValue} />);
      expect(screen.getByDisplayValue(longValue)).toBeInTheDocument();
    });

    it('handles rapid state changes', async () => {
      const { rerender } = render(<AppleInput state="default" />);
      
      rerender(<AppleInput state="error" errorText="Error" />);
      expect(screen.getByText('Error')).toBeInTheDocument();
      
      rerender(<AppleInput state="success" successText="Success" />);
      expect(screen.getByText('Success')).toBeInTheDocument();
      
      rerender(<AppleInput state="default" />);
      expect(screen.queryByText('Error')).not.toBeInTheDocument();
      expect(screen.queryByText('Success')).not.toBeInTheDocument();
    });

    it('handles multiple inputs in same form', () => {
      render(
        <div>
          <AppleInput label="First Name" id="first-name" />
          <AppleInput label="Last Name" id="last-name" />
          <AppleInput label="Email" id="email" />
        </div>
      );
      
      expect(screen.getByLabelText('First Name')).toBeInTheDocument();
      expect(screen.getByLabelText('Last Name')).toBeInTheDocument();
      expect(screen.getByLabelText('Email')).toBeInTheDocument();
    });
  });

  describe('Haptic Feedback', () => {
    it('triggers haptic feedback on focus', async () => {
      const { triggerHaptic } = await import('@/lib/spring-animation');
      render(<AppleInput haptic="medium" />);
      const input = screen.getByRole('textbox');

      await userEvent.click(input);
      expect(triggerHaptic).toHaveBeenCalled();
    });

    it('does not trigger haptic when haptic="none"', async () => {
      const { triggerHaptic } = await import('@/lib/spring-animation');
      vi.clearAllMocks();
      
      render(<AppleInput haptic="none" />);
      const input = screen.getByRole('textbox');

      await userEvent.click(input);
      expect(triggerHaptic).not.toHaveBeenCalled();
    });

    it('triggers haptic on password toggle', async () => {
      const { triggerHaptic } = await import('@/lib/spring-animation');
      vi.clearAllMocks();
      
      render(<AppleInput type="password" showPasswordToggle />);
      const toggleButton = screen.getByLabelText('Show password');

      await userEvent.click(toggleButton);
      expect(triggerHaptic).toHaveBeenCalled();
    });
  });

  describe('Display Name', () => {
    it('has correct display name', () => {
      expect(AppleInput.displayName).toBe('AppleInput');
    });
  });
});
