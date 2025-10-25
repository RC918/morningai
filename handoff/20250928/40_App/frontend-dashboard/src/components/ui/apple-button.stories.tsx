import type { Meta, StoryObj } from '@storybook/react';
import { AppleButton } from './apple-button';
import { 
  Download, 
  Trash2, 
  Plus, 
  Check, 
  X,
  Heart,
  Share2,
  Settings,
  ChevronRight
} from 'lucide-react';

const meta: Meta<typeof AppleButton> = {
  title: 'Design System/Apple Button',
  component: AppleButton,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['primary', 'secondary', 'destructive', 'outline', 'ghost', 'link', 'filled', 'tinted'],
    },
    size: {
      control: 'select',
      options: ['sm', 'default', 'lg', 'icon', 'icon-sm', 'icon-lg'],
    },
    haptic: {
      control: 'select',
      options: ['none', 'light', 'medium', 'heavy'],
    },
    disabled: {
      control: 'boolean',
    },
  },
};

export default meta;
type Story = StoryObj<typeof AppleButton>;

export const Primary: Story = {
  args: {
    children: 'Primary Button',
    variant: 'primary',
  },
};

export const AllVariants: Story = {
  render: () => (
    <div className="flex flex-col gap-4 p-8">
      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-muted-foreground">Button Variants</h3>
        <div className="flex flex-wrap gap-3">
          <AppleButton variant="primary">Primary</AppleButton>
          <AppleButton variant="secondary">Secondary</AppleButton>
          <AppleButton variant="destructive">Destructive</AppleButton>
          <AppleButton variant="outline">Outline</AppleButton>
          <AppleButton variant="ghost">Ghost</AppleButton>
          <AppleButton variant="link">Link</AppleButton>
          <AppleButton variant="filled">Filled</AppleButton>
          <AppleButton variant="tinted">Tinted</AppleButton>
        </div>
      </div>
    </div>
  ),
};

export const Sizes: Story = {
  render: () => (
    <div className="flex flex-col gap-4 p-8">
      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-muted-foreground">Button Sizes</h3>
        <div className="flex items-center flex-wrap gap-3">
          <AppleButton size="sm">Small</AppleButton>
          <AppleButton size="default">Default</AppleButton>
          <AppleButton size="lg">Large</AppleButton>
        </div>
      </div>
    </div>
  ),
};

export const WithIcons: Story = {
  render: () => (
    <div className="flex flex-col gap-6 p-8">
      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-muted-foreground">Buttons with Icons</h3>
        <div className="flex flex-wrap gap-3">
          <AppleButton variant="primary">
            <Download className="size-4" />
            Download
          </AppleButton>
          <AppleButton variant="destructive">
            <Trash2 className="size-4" />
            Delete
          </AppleButton>
          <AppleButton variant="outline">
            <Plus className="size-4" />
            Add New
          </AppleButton>
          <AppleButton variant="ghost">
            <Settings className="size-4" />
            Settings
          </AppleButton>
        </div>
      </div>

      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-muted-foreground">Icon-only Buttons</h3>
        <div className="flex flex-wrap gap-3">
          <AppleButton variant="primary" size="icon">
            <Plus className="size-5" />
          </AppleButton>
          <AppleButton variant="secondary" size="icon">
            <Heart className="size-5" />
          </AppleButton>
          <AppleButton variant="outline" size="icon">
            <Share2 className="size-5" />
          </AppleButton>
          <AppleButton variant="ghost" size="icon">
            <Settings className="size-5" />
          </AppleButton>
        </div>
      </div>

      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-muted-foreground">Icon Sizes</h3>
        <div className="flex items-center flex-wrap gap-3">
          <AppleButton variant="primary" size="icon-sm">
            <Plus className="size-4" />
          </AppleButton>
          <AppleButton variant="primary" size="icon">
            <Plus className="size-5" />
          </AppleButton>
          <AppleButton variant="primary" size="icon-lg">
            <Plus className="size-6" />
          </AppleButton>
        </div>
      </div>
    </div>
  ),
};

export const HapticFeedback: Story = {
  render: () => (
    <div className="flex flex-col gap-4 p-8">
      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-muted-foreground">Haptic Feedback Levels</h3>
        <p className="text-sm text-muted-foreground">Click buttons to feel different haptic intensities</p>
        <div className="flex flex-wrap gap-3">
          <AppleButton haptic="none">No Haptic</AppleButton>
          <AppleButton haptic="light">Light</AppleButton>
          <AppleButton haptic="medium">Medium (Default)</AppleButton>
          <AppleButton haptic="heavy">Heavy</AppleButton>
        </div>
      </div>
    </div>
  ),
};

export const States: Story = {
  render: () => (
    <div className="flex flex-col gap-6 p-8">
      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-muted-foreground">Button States</h3>
        <div className="flex flex-wrap gap-3">
          <AppleButton>Normal</AppleButton>
          <AppleButton disabled>Disabled</AppleButton>
        </div>
      </div>

      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-muted-foreground">Interactive States</h3>
        <p className="text-sm text-muted-foreground">Hover and click to see spring animations</p>
        <div className="flex flex-wrap gap-3">
          <AppleButton variant="primary">Hover Me</AppleButton>
          <AppleButton variant="secondary">Click Me</AppleButton>
          <AppleButton variant="outline">Press Me</AppleButton>
        </div>
      </div>
    </div>
  ),
};

export const ActionButtons: Story = {
  render: () => (
    <div className="flex flex-col gap-6 p-8 max-w-md">
      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-muted-foreground">Common Actions</h3>
        <div className="flex flex-col gap-2">
          <AppleButton variant="primary" className="w-full">
            <Check className="size-4" />
            Confirm
          </AppleButton>
          <AppleButton variant="outline" className="w-full">
            <X className="size-4" />
            Cancel
          </AppleButton>
        </div>
      </div>

      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-muted-foreground">Destructive Actions</h3>
        <div className="flex flex-col gap-2">
          <AppleButton variant="destructive" className="w-full" haptic="heavy">
            <Trash2 className="size-4" />
            Delete Account
          </AppleButton>
          <AppleButton variant="outline" className="w-full">
            Keep Account
          </AppleButton>
        </div>
      </div>
    </div>
  ),
};

export const ButtonGroups: Story = {
  render: () => (
    <div className="flex flex-col gap-6 p-8">
      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-muted-foreground">Horizontal Button Group</h3>
        <div className="inline-flex rounded-xl overflow-hidden border border-input">
          <AppleButton variant="ghost" className="rounded-none border-r border-input">
            Option 1
          </AppleButton>
          <AppleButton variant="ghost" className="rounded-none border-r border-input">
            Option 2
          </AppleButton>
          <AppleButton variant="ghost" className="rounded-none">
            Option 3
          </AppleButton>
        </div>
      </div>

      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-muted-foreground">Icon Button Group</h3>
        <div className="inline-flex rounded-xl overflow-hidden border border-input">
          <AppleButton variant="ghost" size="icon" className="rounded-none border-r border-input">
            <Heart className="size-5" />
          </AppleButton>
          <AppleButton variant="ghost" size="icon" className="rounded-none border-r border-input">
            <Share2 className="size-5" />
          </AppleButton>
          <AppleButton variant="ghost" size="icon" className="rounded-none">
            <Download className="size-5" />
          </AppleButton>
        </div>
      </div>
    </div>
  ),
};

export const LoadingStates: Story = {
  render: () => {
    const [loading, setLoading] = React.useState(false);

    const handleClick = () => {
      setLoading(true);
      setTimeout(() => setLoading(false), 2000);
    };

    return (
      <div className="flex flex-col gap-4 p-8">
        <div className="space-y-2">
          <h3 className="text-sm font-semibold text-muted-foreground">Loading State</h3>
          <AppleButton 
            variant="primary" 
            disabled={loading}
            onClick={handleClick}
          >
            {loading ? (
              <>
                <div className="size-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Processing...
              </>
            ) : (
              <>
                <Check className="size-4" />
                Submit
              </>
            )}
          </AppleButton>
        </div>
      </div>
    );
  },
};

export const NavigationButtons: Story = {
  render: () => (
    <div className="flex flex-col gap-4 p-8 max-w-sm">
      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-muted-foreground">Navigation Style</h3>
        <div className="flex flex-col gap-2">
          <AppleButton variant="ghost" className="w-full justify-between">
            Profile Settings
            <ChevronRight className="size-4" />
          </AppleButton>
          <AppleButton variant="ghost" className="w-full justify-between">
            Privacy & Security
            <ChevronRight className="size-4" />
          </AppleButton>
          <AppleButton variant="ghost" className="w-full justify-between">
            Notifications
            <ChevronRight className="size-4" />
          </AppleButton>
        </div>
      </div>
    </div>
  ),
};

export const DarkMode: Story = {
  render: () => (
    <div className="flex flex-col gap-6 p-8">
      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-muted-foreground">Light Mode</h3>
        <div className="flex flex-wrap gap-3 p-4 bg-background rounded-xl border">
          <AppleButton variant="primary">Primary</AppleButton>
          <AppleButton variant="secondary">Secondary</AppleButton>
          <AppleButton variant="outline">Outline</AppleButton>
          <AppleButton variant="tinted">Tinted</AppleButton>
        </div>
      </div>

      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-muted-foreground">Dark Mode</h3>
        <div className="flex flex-wrap gap-3 p-4 bg-slate-900 rounded-xl border border-slate-800 dark">
          <AppleButton variant="primary">Primary</AppleButton>
          <AppleButton variant="secondary">Secondary</AppleButton>
          <AppleButton variant="outline">Outline</AppleButton>
          <AppleButton variant="tinted">Tinted</AppleButton>
        </div>
      </div>
    </div>
  ),
};

export const RealWorldExamples: Story = {
  render: () => (
    <div className="flex flex-col gap-6 p-8 max-w-2xl">
      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-muted-foreground">Form Actions</h3>
        <div className="p-6 bg-background rounded-xl border space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Email Address</label>
            <input 
              type="email" 
              placeholder="you@example.com"
              className="w-full h-10 px-4 rounded-xl border border-input bg-background"
            />
          </div>
          <div className="flex gap-2">
            <AppleButton variant="primary" className="flex-1">
              Save Changes
            </AppleButton>
            <AppleButton variant="outline">
              Cancel
            </AppleButton>
          </div>
        </div>
      </div>

      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-muted-foreground">Card Actions</h3>
        <div className="p-6 bg-background rounded-xl border space-y-4">
          <div className="flex items-start gap-4">
            <div className="size-12 rounded-xl bg-primary/10 flex items-center justify-center">
              <Download className="size-6 text-primary" />
            </div>
            <div className="flex-1">
              <h4 className="font-semibold">Download Report</h4>
              <p className="text-sm text-muted-foreground">Export your data as PDF or CSV</p>
            </div>
          </div>
          <div className="flex gap-2">
            <AppleButton variant="tinted" size="sm">
              <Download className="size-4" />
              PDF
            </AppleButton>
            <AppleButton variant="tinted" size="sm">
              <Download className="size-4" />
              CSV
            </AppleButton>
          </div>
        </div>
      </div>

      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-muted-foreground">Toolbar</h3>
        <div className="flex items-center justify-between p-3 bg-background rounded-xl border">
          <div className="flex gap-1">
            <AppleButton variant="ghost" size="icon-sm">
              <Plus className="size-4" />
            </AppleButton>
            <AppleButton variant="ghost" size="icon-sm">
              <Share2 className="size-4" />
            </AppleButton>
            <AppleButton variant="ghost" size="icon-sm">
              <Download className="size-4" />
            </AppleButton>
          </div>
          <div className="flex gap-2">
            <AppleButton variant="outline" size="sm">
              Cancel
            </AppleButton>
            <AppleButton variant="primary" size="sm">
              Done
            </AppleButton>
          </div>
        </div>
      </div>
    </div>
  ),
};
