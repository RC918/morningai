import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { TotpInput } from '../TotpInput';

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, params?: any) => {
      const translations: Record<string, string> = {
        'auth.2fa.totpCodeLabel': 'Verification Code',
        'auth.2fa.totpCodeHelp': 'Enter the 6-digit code from your authenticator app',
        'auth.2fa.totpDigitLabel': `Digit ${params?.index || 1}`,
      };
      return translations[key] || key;
    },
  }),
}));

vi.mock('@/lib/spring-animation', () => ({
  getSpringConfig: () => ({ duration: 0.2 }),
  triggerHaptic: vi.fn(),
}));

vi.mock('framer-motion', () => {
  const React = require('react');
  return {
    motion: {
      input: React.forwardRef((props: any, ref: any) => {
        const { whileFocus, whileHover, whileTap, transition, ...inputProps } = props;
        return <input ref={ref} {...inputProps} />;
      }),
    },
  };
});

describe('TotpInput', () => {
  let mockOnChange: ReturnType<typeof vi.fn>;
  let mockOnComplete: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    mockOnChange = vi.fn();
    mockOnComplete = vi.fn();
  });

  it('renders 6 input boxes', () => {
    render(<TotpInput value="" onChange={mockOnChange} />);
    
    const inputs = screen.getAllByRole('textbox');
    expect(inputs).toHaveLength(6);
  });

  it('accepts only numeric input', async () => {
    const user = userEvent.setup();
    render(<TotpInput value="" onChange={mockOnChange} />);
    
    const inputs = screen.getAllByRole('textbox');
    
    await user.type(inputs[0], 'a');
    expect(mockOnChange).not.toHaveBeenCalled();
    
    await user.type(inputs[0], '1');
    expect(mockOnChange).toHaveBeenCalledWith('1');
  });

  it('auto-advances to next input after entering digit', async () => {
    const user = userEvent.setup();
    render(<TotpInput value="" onChange={mockOnChange} />);
    
    const inputs = screen.getAllByRole('textbox') as HTMLInputElement[];
    
    await user.type(inputs[0], '1');
    
    await waitFor(() => {
      expect(document.activeElement).toBe(inputs[1]);
    });
  });

  it('handles backspace to move to previous input', async () => {
    const user = userEvent.setup();
    render(<TotpInput value="12" onChange={mockOnChange} />);
    
    const inputs = screen.getAllByRole('textbox') as HTMLInputElement[];
    
    inputs[1].focus();
    await user.keyboard('{Backspace}');
    
    await waitFor(() => {
      expect(document.activeElement).toBe(inputs[0]);
    });
  });

  it('handles paste of 6-digit code', async () => {
    render(<TotpInput value="" onChange={mockOnChange} />);
    
    const inputs = screen.getAllByRole('textbox');
    
    fireEvent.paste(inputs[0], {
      clipboardData: {
        getData: () => '123456',
      },
    });
    
    expect(mockOnChange).toHaveBeenCalledWith('123456');
  });

  it('handles paste with non-numeric characters', async () => {
    render(<TotpInput value="" onChange={mockOnChange} />);
    
    const inputs = screen.getAllByRole('textbox');
    
    fireEvent.paste(inputs[0], {
      clipboardData: {
        getData: () => '12-34-56',
      },
    });
    
    expect(mockOnChange).toHaveBeenCalledWith('123456');
  });

  it('calls onComplete when 6 digits are entered', async () => {
    const user = userEvent.setup();
    const { rerender } = render(
      <TotpInput value="" onChange={mockOnChange} onComplete={mockOnComplete} />
    );
    
    rerender(
      <TotpInput value="123456" onChange={mockOnChange} onComplete={mockOnComplete} />
    );
    
    await waitFor(() => {
      expect(mockOnComplete).toHaveBeenCalledWith('123456');
    });
  });

  it('displays error state', () => {
    render(<TotpInput value="" onChange={mockOnChange} error={true} />);
    
    const inputs = screen.getAllByRole('textbox');
    expect(inputs[0]).toHaveClass('border-destructive');
  });

  it('disables input when disabled prop is true', () => {
    render(<TotpInput value="" onChange={mockOnChange} disabled={true} />);
    
    const inputs = screen.getAllByRole('textbox');
    inputs.forEach(input => {
      expect(input).toBeDisabled();
    });
  });

  it('handles arrow key navigation', async () => {
    const user = userEvent.setup();
    render(<TotpInput value="123" onChange={mockOnChange} />);
    
    const inputs = screen.getAllByRole('textbox') as HTMLInputElement[];
    
    inputs[1].focus();
    await user.keyboard('{ArrowLeft}');
    
    await waitFor(() => {
      expect(document.activeElement).toBe(inputs[0]);
    });
    
    await user.keyboard('{ArrowRight}');
    
    await waitFor(() => {
      expect(document.activeElement).toBe(inputs[1]);
    });
  });

  it('selects input content on focus', async () => {
    render(<TotpInput value="123456" onChange={mockOnChange} />);
    
    const inputs = screen.getAllByRole('textbox') as HTMLInputElement[];
    
    inputs[0].focus();
    
    const selectSpy = vi.spyOn(inputs[0], 'select');
    fireEvent.focus(inputs[0]);
    
    expect(selectSpy).toHaveBeenCalled();
  });

  it('limits input to 6 digits', async () => {
    render(<TotpInput value="" onChange={mockOnChange} />);
    
    const inputs = screen.getAllByRole('textbox');
    
    fireEvent.paste(inputs[0], {
      clipboardData: {
        getData: () => '1234567890',
      },
    });
    
    expect(mockOnChange).toHaveBeenCalledWith('123456');
  });

  it('handles partial paste in middle of input', async () => {
    render(<TotpInput value="12" onChange={mockOnChange} />);
    
    const inputs = screen.getAllByRole('textbox');
    
    fireEvent.paste(inputs[2], {
      clipboardData: {
        getData: () => '3456',
      },
    });
    
    expect(mockOnChange).toHaveBeenCalledWith('123456');
  });

  it('auto-focuses first input when autoFocus is true', () => {
    render(<TotpInput value="" onChange={mockOnChange} autoFocus={true} />);
    
    const inputs = screen.getAllByRole('textbox') as HTMLInputElement[];
    
    waitFor(() => {
      expect(document.activeElement).toBe(inputs[0]);
    });
  });

  it('does not auto-focus when autoFocus is false', () => {
    render(<TotpInput value="" onChange={mockOnChange} autoFocus={false} />);
    
    const inputs = screen.getAllByRole('textbox') as HTMLInputElement[];
    
    expect(document.activeElement).not.toBe(inputs[0]);
  });

  it('displays current value correctly', () => {
    render(<TotpInput value="123" onChange={mockOnChange} />);
    
    const inputs = screen.getAllByRole('textbox') as HTMLInputElement[];
    
    expect(inputs[0].value).toBe('1');
    expect(inputs[1].value).toBe('2');
    expect(inputs[2].value).toBe('3');
    expect(inputs[3].value).toBe('');
    expect(inputs[4].value).toBe('');
    expect(inputs[5].value).toBe('');
  });

  it('clears digit when backspace is pressed on filled input', async () => {
    const user = userEvent.setup();
    render(<TotpInput value="123456" onChange={mockOnChange} />);
    
    const inputs = screen.getAllByRole('textbox') as HTMLInputElement[];
    
    inputs[2].focus();
    await user.keyboard('{Backspace}');
    
    expect(mockOnChange).toHaveBeenCalled();
  });

  it('does not change value when disabled', async () => {
    const user = userEvent.setup();
    render(<TotpInput value="" onChange={mockOnChange} disabled={true} />);
    
    const inputs = screen.getAllByRole('textbox');
    
    await user.type(inputs[0], '1');
    
    expect(mockOnChange).not.toHaveBeenCalled();
  });
});
