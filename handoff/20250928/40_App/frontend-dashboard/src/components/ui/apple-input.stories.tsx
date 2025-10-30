import type { Meta, StoryObj } from '@storybook/react';
import { AppleInput } from './apple-input';
import { Mail, Lock, Search, User, Phone, CreditCard } from 'lucide-react';
import { useState } from 'react';

/**
 * AppleInput is an iOS-style input component with floating labels, spring animations, and haptic feedback.
 * 
 * ## Features
 * - 🎨 iOS-style floating label animations
 * - ⚡ Spring-based animations with Framer Motion
 * - 📱 Haptic feedback simulation
 * - 🎯 Smart validation state display
 * - ♿ Full accessibility support
 * - 🌙 Dark mode optimized
 * - 🔒 Built-in password toggle
 * - ✨ Material design backdrop blur
 * 
 * ## Design Philosophy
 * Inspired by iOS 17+ input fields with smooth spring animations and subtle haptic feedback.
 * The floating label provides a modern, space-efficient design while maintaining clarity.
 */
const meta = {
  title: 'UI/AppleInput',
  component: AppleInput,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: `
AppleInput brings Apple's design language to form inputs with smooth animations and intuitive interactions.

### Usage Guidelines
- Use floating labels for a modern, clean look
- Provide clear validation feedback with error/success states
- Include helper text for additional context
- Use appropriate input types for better mobile keyboards
- Add icons to enhance visual clarity
- Enable password toggle for password fields

### Accessibility
- Floating labels maintain proper label associations
- Error messages use aria-live regions
- Focus indicators follow WCAG guidelines
- Keyboard navigation fully supported
- Screen reader compatible
- Required fields clearly marked

### Performance
- Optimized spring animations (60 FPS)
- GPU-accelerated transforms
- Efficient re-renders with React.memo patterns
- Backdrop blur with fallbacks
        `,
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['default', 'filled', 'outline'],
      description: 'Visual style variant',
      table: {
        type: { summary: 'string' },
        defaultValue: { summary: 'default' },
      },
    },
    inputSize: {
      control: 'select',
      options: ['sm', 'default', 'lg'],
      description: 'Size of the input field',
      table: {
        type: { summary: 'string' },
        defaultValue: { summary: 'default' },
      },
    },
    state: {
      control: 'select',
      options: ['default', 'error', 'success'],
      description: 'Validation state',
      table: {
        type: { summary: 'string' },
        defaultValue: { summary: 'default' },
      },
    },
    haptic: {
      control: 'select',
      options: ['none', 'light', 'medium', 'heavy'],
      description: 'Haptic feedback intensity',
      table: {
        type: { summary: 'string' },
        defaultValue: { summary: 'light' },
      },
    },
    disabled: {
      control: 'boolean',
      description: 'Whether the input is disabled',
    },
    required: {
      control: 'boolean',
      description: 'Whether the input is required',
    },
    showPasswordToggle: {
      control: 'boolean',
      description: 'Show password visibility toggle (password type only)',
    },
  },
} satisfies Meta<typeof AppleInput>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    label: 'Email',
    placeholder: 'Enter your email',
    type: 'email',
  },
};

export const WithValue: Story = {
  args: {
    label: 'Username',
    defaultValue: 'john.doe',
  },
};

export const Disabled: Story = {
  args: {
    label: 'Disabled Field',
    placeholder: 'Cannot edit',
    disabled: true,
    defaultValue: 'Disabled value',
  },
};

export const Required: Story = {
  args: {
    label: 'Email',
    placeholder: 'Enter your email',
    type: 'email',
    required: true,
    helperText: 'This field is required',
  },
};

export const FilledVariant: Story = {
  args: {
    label: 'Search',
    placeholder: 'Search...',
    variant: 'filled',
    leftIcon: <Search className="w-4 h-4" />,
  },
};

export const OutlineVariant: Story = {
  args: {
    label: 'Username',
    placeholder: 'Enter username',
    variant: 'outline',
  },
};

export const SmallSize: Story = {
  args: {
    label: 'Small Input',
    placeholder: 'Small size',
    inputSize: 'sm',
  },
};

export const LargeSize: Story = {
  args: {
    label: 'Large Input',
    placeholder: 'Large size',
    inputSize: 'lg',
  },
};

export const ErrorState: Story = {
  args: {
    label: 'Email',
    placeholder: 'Enter your email',
    type: 'email',
    state: 'error',
    errorText: 'Please enter a valid email address',
    defaultValue: 'invalid-email',
  },
};

export const SuccessState: Story = {
  args: {
    label: 'Email',
    placeholder: 'Enter your email',
    type: 'email',
    state: 'success',
    successText: 'Email is available!',
    defaultValue: 'john.doe@example.com',
  },
};

export const WithLeftIcon: Story = {
  args: {
    label: 'Email',
    placeholder: 'Enter your email',
    type: 'email',
    leftIcon: <Mail className="w-4 h-4" />,
  },
};

export const WithRightIcon: Story = {
  args: {
    label: 'Search',
    placeholder: 'Search...',
    rightIcon: <Search className="w-4 h-4" />,
  },
};

export const Password: Story = {
  args: {
    label: 'Password',
    placeholder: 'Enter your password',
    type: 'password',
    showPasswordToggle: true,
    leftIcon: <Lock className="w-4 h-4" />,
  },
};

export const PasswordWithValidation: Story = {
  args: {
    label: 'Password',
    placeholder: 'Enter your password',
    type: 'password',
    showPasswordToggle: true,
    state: 'error',
    errorText: 'Password must be at least 8 characters',
    leftIcon: <Lock className="w-4 h-4" />,
  },
};

export const WithHelperText: Story = {
  args: {
    label: 'Username',
    placeholder: 'Choose a username',
    helperText: 'Username must be 3-20 characters long',
  },
};

export const EmailInput: Story = {
  args: {
    label: 'Email Address',
    placeholder: 'name@example.com',
    type: 'email',
    leftIcon: <Mail className="w-4 h-4" />,
    helperText: 'We\'ll never share your email',
  },
};

export const PhoneInput: Story = {
  args: {
    label: 'Phone Number',
    placeholder: '(123) 456-7890',
    type: 'tel',
    leftIcon: <Phone className="w-4 h-4" />,
  },
};

export const NumberInput: Story = {
  args: {
    label: 'Age',
    placeholder: '0',
    type: 'number',
    min: 0,
    max: 120,
  },
};

export const SearchInput: Story = {
  args: {
    label: 'Search',
    placeholder: 'Search products...',
    type: 'search',
    variant: 'filled',
    leftIcon: <Search className="w-4 h-4" />,
  },
};

export const InteractiveValidation: Story = {
  render: () => {
    const [email, setEmail] = useState('');
    const [state, setState] = useState<'default' | 'error' | 'success'>('default');
    const [message, setMessage] = useState('');

    const validateEmail = (value: string) => {
      if (!value) {
        setState('default');
        setMessage('');
      } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
        setState('error');
        setMessage('Please enter a valid email address');
      } else {
        setState('success');
        setMessage('Email looks good!');
      }
    };

    return (
      <div className="w-80">
        <AppleInput
          label="Email"
          placeholder="Enter your email"
          type="email"
          value={email}
          onChange={(e) => {
            setEmail(e.target.value);
            validateEmail(e.target.value);
          }}
          state={state}
          errorText={state === 'error' ? message : undefined}
          successText={state === 'success' ? message : undefined}
          leftIcon={<Mail className="w-4 h-4" />}
        />
      </div>
    );
  },
};

export const PasswordStrength: Story = {
  render: () => {
    const [password, setPassword] = useState('');
    const [strength, setStrength] = useState<'weak' | 'medium' | 'strong'>('weak');

    const calculateStrength = (value: string) => {
      if (value.length < 6) return 'weak';
      if (value.length < 10) return 'medium';
      return 'strong';
    };

    const getStrengthColor = () => {
      switch (strength) {
        case 'weak': return 'bg-red-500';
        case 'medium': return 'bg-yellow-500';
        case 'strong': return 'bg-green-500';
      }
    };

    return (
      <div className="w-80 space-y-2">
        <AppleInput
          label="Password"
          placeholder="Enter your password"
          type="password"
          showPasswordToggle
          value={password}
          onChange={(e) => {
            setPassword(e.target.value);
            setStrength(calculateStrength(e.target.value));
          }}
          leftIcon={<Lock className="w-4 h-4" />}
          helperText={`Password strength: ${strength}`}
        />
        <div className="flex gap-1">
          <div className={`h-1 flex-1 rounded-full ${password.length > 0 ? getStrengthColor() : 'bg-gray-200'}`} />
          <div className={`h-1 flex-1 rounded-full ${strength !== 'weak' ? getStrengthColor() : 'bg-gray-200'}`} />
          <div className={`h-1 flex-1 rounded-full ${strength === 'strong' ? getStrengthColor() : 'bg-gray-200'}`} />
        </div>
      </div>
    );
  },
};

export const LoginForm: Story = {
  render: () => {
    return (
      <div className="w-80 space-y-4 p-6 rounded-2xl bg-background/50 backdrop-blur-xl border border-border/50">
        <div className="text-center mb-6">
          <h2 className="text-2xl font-semibold">Welcome Back</h2>
          <p className="text-sm text-muted-foreground mt-1">Sign in to your account</p>
        </div>
        
        <AppleInput
          label="Email"
          placeholder="Enter your email"
          type="email"
          leftIcon={<Mail className="w-4 h-4" />}
          required
        />
        
        <AppleInput
          label="Password"
          placeholder="Enter your password"
          type="password"
          showPasswordToggle
          leftIcon={<Lock className="w-4 h-4" />}
          required
        />
        
        <button className="w-full h-11 bg-primary text-primary-foreground rounded-xl font-medium hover:opacity-90 transition-opacity">
          Sign In
        </button>
      </div>
    );
  },
};

export const SignupForm: Story = {
  render: () => {
    return (
      <div className="w-80 space-y-4 p-6 rounded-2xl bg-background/50 backdrop-blur-xl border border-border/50">
        <div className="text-center mb-6">
          <h2 className="text-2xl font-semibold">Create Account</h2>
          <p className="text-sm text-muted-foreground mt-1">Join us today</p>
        </div>
        
        <AppleInput
          label="Full Name"
          placeholder="Enter your name"
          leftIcon={<User className="w-4 h-4" />}
          required
        />
        
        <AppleInput
          label="Email"
          placeholder="Enter your email"
          type="email"
          leftIcon={<Mail className="w-4 h-4" />}
          required
        />
        
        <AppleInput
          label="Password"
          placeholder="Create a password"
          type="password"
          showPasswordToggle
          leftIcon={<Lock className="w-4 h-4" />}
          helperText="Must be at least 8 characters"
          required
        />
        
        <button className="w-full h-11 bg-primary text-primary-foreground rounded-xl font-medium hover:opacity-90 transition-opacity">
          Create Account
        </button>
      </div>
    );
  },
};

export const LongLabel: Story = {
  args: {
    label: 'This is a very long label that might need to be truncated',
    placeholder: 'Enter value',
  },
};

export const LongValue: Story = {
  args: {
    label: 'URL',
    defaultValue: 'https://www.example.com/very/long/path/that/extends/beyond/the/visible/area',
  },
};

export const MultipleInputs: Story = {
  render: () => {
    return (
      <div className="w-96 space-y-4">
        <AppleInput
          label="First Name"
          placeholder="John"
          leftIcon={<User className="w-4 h-4" />}
        />
        <AppleInput
          label="Last Name"
          placeholder="Doe"
          leftIcon={<User className="w-4 h-4" />}
        />
        <AppleInput
          label="Email"
          placeholder="john.doe@example.com"
          type="email"
          leftIcon={<Mail className="w-4 h-4" />}
        />
        <AppleInput
          label="Phone"
          placeholder="(123) 456-7890"
          type="tel"
          leftIcon={<Phone className="w-4 h-4" />}
        />
      </div>
    );
  },
};

export const PaymentForm: Story = {
  render: () => {
    return (
      <div className="w-96 space-y-4 p-6 rounded-2xl bg-background/50 backdrop-blur-xl border border-border/50">
        <div className="text-center mb-6">
          <h2 className="text-2xl font-semibold">Payment Details</h2>
          <p className="text-sm text-muted-foreground mt-1">Enter your card information</p>
        </div>
        
        <AppleInput
          label="Card Number"
          placeholder="1234 5678 9012 3456"
          type="text"
          leftIcon={<CreditCard className="w-4 h-4" />}
          maxLength={19}
        />
        
        <div className="grid grid-cols-2 gap-4">
          <AppleInput
            label="Expiry Date"
            placeholder="MM/YY"
            type="text"
            maxLength={5}
          />
          
          <AppleInput
            label="CVV"
            placeholder="123"
            type="text"
            maxLength={3}
          />
        </div>
        
        <AppleInput
          label="Cardholder Name"
          placeholder="John Doe"
          leftIcon={<User className="w-4 h-4" />}
        />
        
        <button className="w-full h-11 bg-primary text-primary-foreground rounded-xl font-medium hover:opacity-90 transition-opacity">
          Complete Payment
        </button>
      </div>
    );
  },
};
