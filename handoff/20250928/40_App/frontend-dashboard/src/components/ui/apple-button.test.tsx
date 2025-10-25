/**
 * AppleButton Component Unit Tests
 * Target: 80% code coverage
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { AppleButton } from './apple-button';
import * as springAnimation from '@/lib/spring-animation';

vi.mock('@/lib/spring-animation', () => ({
  getSpringConfig: vi.fn(() => ({
    type: 'spring',
    stiffness: 300,
    damping: 30,
  })),
  triggerHaptic: vi.fn(),
}));

describe('AppleButton', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders with default props', () => {
      render(<AppleButton>Click me</AppleButton>);
      const button = screen.getByRole('button', { name: /click me/i });
      
      expect(button).toBeInTheDocument();
      expect(button).toHaveTextContent('Click me');
    });

    it('renders with children', () => {
      render(
        <AppleButton>
          <span>Icon</span>
          <span>Text</span>
        </AppleButton>
      );
      
      expect(screen.getByText('Icon')).toBeInTheDocument();
      expect(screen.getByText('Text')).toBeInTheDocument();
    });

    it('applies data-slot attribute', () => {
      render(<AppleButton>Button</AppleButton>);
      const button = screen.getByRole('button');
      
      expect(button).toHaveAttribute('data-slot', 'button');
    });
  });

  describe('Variants', () => {
    const variants = [
      'primary',
      'secondary',
      'destructive',
      'outline',
      'ghost',
      'link',
      'filled',
      'tinted',
    ] as const;

    variants.forEach((variant) => {
      it(`renders ${variant} variant correctly`, () => {
        render(<AppleButton variant={variant}>{variant}</AppleButton>);
        const button = screen.getByRole('button');
        
        expect(button).toBeInTheDocument();
        expect(button).toHaveTextContent(variant);
      });
    });
  });

  describe('Sizes', () => {
    const sizes = ['sm', 'default', 'lg', 'icon', 'icon-sm', 'icon-lg'] as const;

    sizes.forEach((size) => {
      it(`renders ${size} size correctly`, () => {
        render(<AppleButton size={size}>Button</AppleButton>);
        const button = screen.getByRole('button');
        
        expect(button).toBeInTheDocument();
      });
    });
  });

  describe('Haptic Feedback', () => {
    it('triggers haptic feedback on click with default level', async () => {
      const user = userEvent.setup();
      render(<AppleButton>Click</AppleButton>);
      const button = screen.getByRole('button');
      
      await user.click(button);
      
      expect(springAnimation.triggerHaptic).toHaveBeenCalledWith(
        expect.any(Object),
        'medium'
      );
    });

    it('triggers light haptic feedback', async () => {
      const user = userEvent.setup();
      render(<AppleButton haptic="light">Click</AppleButton>);
      const button = screen.getByRole('button');
      
      await user.click(button);
      
      expect(springAnimation.triggerHaptic).toHaveBeenCalledWith(
        expect.any(Object),
        'light'
      );
    });

    it('triggers heavy haptic feedback', async () => {
      const user = userEvent.setup();
      render(<AppleButton haptic="heavy">Click</AppleButton>);
      const button = screen.getByRole('button');
      
      await user.click(button);
      
      expect(springAnimation.triggerHaptic).toHaveBeenCalledWith(
        expect.any(Object),
        'heavy'
      );
    });

    it('does not trigger haptic feedback when haptic is none', async () => {
      const user = userEvent.setup();
      render(<AppleButton haptic="none">Click</AppleButton>);
      const button = screen.getByRole('button');
      
      await user.click(button);
      
      expect(springAnimation.triggerHaptic).not.toHaveBeenCalled();
    });

    it('does not trigger haptic feedback when disabled', async () => {
      const user = userEvent.setup();
      render(<AppleButton disabled>Click</AppleButton>);
      const button = screen.getByRole('button');
      
      await user.click(button);
      
      expect(springAnimation.triggerHaptic).not.toHaveBeenCalled();
    });
  });

  describe('Click Handler', () => {
    it('calls onClick when clicked', async () => {
      const handleClick = vi.fn();
      const user = userEvent.setup();
      render(<AppleButton onClick={handleClick}>Click</AppleButton>);
      const button = screen.getByRole('button');
      
      await user.click(button);
      
      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('does not call onClick when disabled', async () => {
      const handleClick = vi.fn();
      const user = userEvent.setup();
      render(<AppleButton onClick={handleClick} disabled>Click</AppleButton>);
      const button = screen.getByRole('button');
      
      await user.click(button);
      
      expect(handleClick).not.toHaveBeenCalled();
    });

    it('passes event to onClick handler', async () => {
      const handleClick = vi.fn();
      const user = userEvent.setup();
      render(<AppleButton onClick={handleClick}>Click</AppleButton>);
      const button = screen.getByRole('button');
      
      await user.click(button);
      
      expect(handleClick).toHaveBeenCalledWith(expect.any(Object));
    });
  });

  describe('Disabled State', () => {
    it('renders disabled button', () => {
      render(<AppleButton disabled>Disabled</AppleButton>);
      const button = screen.getByRole('button');
      
      expect(button).toBeDisabled();
    });

    it('applies disabled attribute', () => {
      render(<AppleButton disabled>Disabled</AppleButton>);
      const button = screen.getByRole('button');
      
      expect(button).toHaveAttribute('disabled');
    });

    it('does not trigger haptic feedback when disabled', async () => {
      const user = userEvent.setup();
      render(<AppleButton disabled>Click</AppleButton>);
      const button = screen.getByRole('button');
      
      await user.click(button);
      
      expect(springAnimation.triggerHaptic).not.toHaveBeenCalled();
    });
  });

  describe('Custom className', () => {
    it('applies custom className', () => {
      render(<AppleButton className="custom-class">Button</AppleButton>);
      const button = screen.getByRole('button');
      
      expect(button).toHaveClass('custom-class');
    });

    it('merges custom className with variant classes', () => {
      render(
        <AppleButton variant="primary" className="custom-class">
          Button
        </AppleButton>
      );
      const button = screen.getByRole('button');
      
      expect(button).toHaveClass('custom-class');
    });
  });

  describe('Spring Animation Integration', () => {
    it('calls getSpringConfig on render', () => {
      render(<AppleButton>Button</AppleButton>);
      
      expect(springAnimation.getSpringConfig).toHaveBeenCalledWith('snappy');
    });

    it('uses spring config for animations', () => {
      const mockConfig = {
        type: 'spring',
        stiffness: 300,
        damping: 30,
      };
      vi.mocked(springAnimation.getSpringConfig).mockReturnValue(mockConfig);
      
      render(<AppleButton>Button</AppleButton>);
      
      expect(springAnimation.getSpringConfig).toHaveBeenCalled();
    });
  });

  describe('Accessibility', () => {
    it('is keyboard accessible', async () => {
      const handleClick = vi.fn();
      const user = userEvent.setup();
      render(<AppleButton onClick={handleClick}>Button</AppleButton>);
      const button = screen.getByRole('button');
      
      button.focus();
      expect(button).toHaveFocus();
      
      await user.keyboard('{Enter}');
      expect(handleClick).toHaveBeenCalled();
    });

    it('supports Space key activation', async () => {
      const handleClick = vi.fn();
      const user = userEvent.setup();
      render(<AppleButton onClick={handleClick}>Button</AppleButton>);
      const button = screen.getByRole('button');
      
      button.focus();
      await user.keyboard(' ');
      
      expect(handleClick).toHaveBeenCalled();
    });

    it('has correct role', () => {
      render(<AppleButton>Button</AppleButton>);
      const button = screen.getByRole('button');
      
      expect(button).toBeInTheDocument();
    });

    it('supports aria-label', () => {
      render(<AppleButton aria-label="Custom label">Button</AppleButton>);
      const button = screen.getByRole('button', { name: /custom label/i });
      
      expect(button).toBeInTheDocument();
    });

    it('supports aria-describedby', () => {
      render(
        <>
          <AppleButton aria-describedby="description">Button</AppleButton>
          <div id="description">Description text</div>
        </>
      );
      const button = screen.getByRole('button');
      
      expect(button).toHaveAttribute('aria-describedby', 'description');
    });
  });

  describe('asChild prop', () => {
    it('renders as Slot when asChild is true', () => {
      render(
        <AppleButton asChild>
          <a href="/test">Link Button</a>
        </AppleButton>
      );
      
      const link = screen.getByRole('link');
      expect(link).toBeInTheDocument();
      expect(link).toHaveAttribute('href', '/test');
    });
  });

  describe('Variant Combinations', () => {
    it('renders primary button with small size', () => {
      render(
        <AppleButton variant="primary" size="sm">
          Small Primary
        </AppleButton>
      );
      const button = screen.getByRole('button');
      
      expect(button).toBeInTheDocument();
      expect(button).toHaveTextContent('Small Primary');
    });

    it('renders destructive button with large size', () => {
      render(
        <AppleButton variant="destructive" size="lg">
          Large Destructive
        </AppleButton>
      );
      const button = screen.getByRole('button');
      
      expect(button).toBeInTheDocument();
      expect(button).toHaveTextContent('Large Destructive');
    });

    it('renders outline button with icon size', () => {
      render(
        <AppleButton variant="outline" size="icon">
          +
        </AppleButton>
      );
      const button = screen.getByRole('button');
      
      expect(button).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('handles rapid clicks', async () => {
      const handleClick = vi.fn();
      const user = userEvent.setup();
      render(<AppleButton onClick={handleClick}>Click</AppleButton>);
      const button = screen.getByRole('button');
      
      await user.click(button);
      await user.click(button);
      await user.click(button);
      
      expect(handleClick).toHaveBeenCalledTimes(3);
      expect(springAnimation.triggerHaptic).toHaveBeenCalledTimes(3);
    });

    it('handles empty children', () => {
      render(<AppleButton />);
      const button = screen.getByRole('button');
      
      expect(button).toBeInTheDocument();
    });

    it('handles null onClick', async () => {
      const user = userEvent.setup();
      render(<AppleButton onClick={undefined}>Click</AppleButton>);
      const button = screen.getByRole('button');
      
      await user.click(button);
      
      expect(springAnimation.triggerHaptic).toHaveBeenCalled();
    });

    it('maintains ref through clicks', async () => {
      const user = userEvent.setup();
      render(<AppleButton>Click</AppleButton>);
      const button = screen.getByRole('button');
      
      await user.click(button);
      await user.click(button);
      
      expect(springAnimation.triggerHaptic).toHaveBeenCalledTimes(2);
      expect(springAnimation.triggerHaptic).toHaveBeenCalledWith(
        expect.any(Object),
        'medium'
      );
    });
  });

  describe('Snapshot Tests', () => {
    it('matches snapshot for primary variant', () => {
      const { container } = render(
        <AppleButton variant="primary">Primary</AppleButton>
      );
      
      expect(container).toMatchSnapshot();
    });

    it('matches snapshot for all variants', () => {
      const { container } = render(
        <div>
          <AppleButton variant="primary">Primary</AppleButton>
          <AppleButton variant="secondary">Secondary</AppleButton>
          <AppleButton variant="destructive">Destructive</AppleButton>
          <AppleButton variant="outline">Outline</AppleButton>
          <AppleButton variant="ghost">Ghost</AppleButton>
          <AppleButton variant="link">Link</AppleButton>
          <AppleButton variant="filled">Filled</AppleButton>
          <AppleButton variant="tinted">Tinted</AppleButton>
        </div>
      );
      
      expect(container).toMatchSnapshot();
    });

    it('matches snapshot for all sizes', () => {
      const { container } = render(
        <div>
          <AppleButton size="sm">Small</AppleButton>
          <AppleButton size="default">Default</AppleButton>
          <AppleButton size="lg">Large</AppleButton>
          <AppleButton size="icon">+</AppleButton>
          <AppleButton size="icon-sm">+</AppleButton>
          <AppleButton size="icon-lg">+</AppleButton>
        </div>
      );
      
      expect(container).toMatchSnapshot();
    });

    it('matches snapshot for disabled state', () => {
      const { container } = render(
        <div>
          <AppleButton>Normal</AppleButton>
          <AppleButton disabled>Disabled</AppleButton>
        </div>
      );
      
      expect(container).toMatchSnapshot();
    });
  });
});
