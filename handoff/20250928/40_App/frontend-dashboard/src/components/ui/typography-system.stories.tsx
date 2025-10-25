import type { Meta, StoryObj } from '@storybook/react';

/**
 * Typography System - Apple-Level Design
 * 
 * Our typography system follows Apple's Human Interface Guidelines with a 14-level type scale
 * that ensures clarity, hierarchy, and accessibility across all devices.
 * 
 * ## Key Features
 * - 14-level type scale (Display 1-3, Titles, Body, Small text)
 * - Responsive fluid typography with CSS clamp()
 * - WCAG AA compliant contrast ratios
 * - Dynamic type support
 * - Optimized line heights and letter spacing
 * 
 * ## Font Stack
 * Primary: Inter, -apple-system, BlinkMacSystemFont, system-ui, sans-serif
 * Monospace: JetBrains Mono, SF Mono, Monaco, monospace
 */
const meta = {
  title: 'Design System/Typography',
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: 'Complete typography system with 14 levels following Apple HIG standards.',
      },
    },
  },
  tags: ['autodocs'],
} satisfies Meta;

export default meta;
type Story = StoryObj<typeof meta>;

/**
 * ## Type Scale Overview
 * 
 * All 14 levels of our typography system, from Display 1 (56px) to Caption 2 (11px).
 * Each level is designed for specific use cases and maintains optimal readability.
 */
export const TypeScale: Story = {
  render: () => (
    <div className="space-y-8">
      <div>
        <h2 className="text-title-2 text-gray-900 mb-6">Complete Type Scale</h2>
        <div className="space-y-6">
          {/* Display Styles */}
          <div className="border-b border-gray-200 pb-6">
            <h3 className="text-title-3 text-gray-800 mb-4">Display Styles</h3>
            <div className="space-y-4">
              <div>
                <p className="text-display-1 text-gray-900">Display 1</p>
                <p className="text-footnote text-gray-500 mt-1">
                  56px / 3.5rem • Bold (700) • Line height 1.1 • -0.02em tracking
                </p>
                <p className="text-caption-1 text-gray-400 mt-1">
                  Use for: Hero headlines, landing pages
                </p>
              </div>
              
              <div>
                <p className="text-display-2 text-gray-900">Display 2</p>
                <p className="text-footnote text-gray-500 mt-1">
                  48px / 3rem • Bold (700) • Line height 1.15 • -0.02em tracking
                </p>
                <p className="text-caption-1 text-gray-400 mt-1">
                  Use for: Section headlines
                </p>
              </div>
              
              <div>
                <p className="text-display-3 text-gray-900">Display 3</p>
                <p className="text-footnote text-gray-500 mt-1">
                  40px / 2.5rem • Semibold (600) • Line height 1.2 • -0.01em tracking
                </p>
                <p className="text-caption-1 text-gray-400 mt-1">
                  Use for: Page titles
                </p>
              </div>
            </div>
          </div>

          {/* Title Styles */}
          <div className="border-b border-gray-200 pb-6">
            <h3 className="text-title-3 text-gray-800 mb-4">Title Styles</h3>
            <div className="space-y-4">
              <div>
                <p className="text-large-title text-gray-900">Large Title</p>
                <p className="text-footnote text-gray-500 mt-1">
                  34px / 2.125rem • Bold (700) • Line height 1.25 • -0.01em tracking
                </p>
                <p className="text-caption-1 text-gray-400 mt-1">
                  Use for: Primary headings
                </p>
              </div>
              
              <div>
                <p className="text-title-1 text-gray-900">Title 1</p>
                <p className="text-footnote text-gray-500 mt-1">
                  28px / 1.75rem • Semibold (600) • Line height 1.3
                </p>
                <p className="text-caption-1 text-gray-400 mt-1">
                  Use for: Section headings
                </p>
              </div>
              
              <div>
                <p className="text-title-2 text-gray-900">Title 2</p>
                <p className="text-footnote text-gray-500 mt-1">
                  22px / 1.375rem • Semibold (600) • Line height 1.35
                </p>
                <p className="text-caption-1 text-gray-400 mt-1">
                  Use for: Subsection headings
                </p>
              </div>
              
              <div>
                <p className="text-title-3 text-gray-900">Title 3</p>
                <p className="text-footnote text-gray-500 mt-1">
                  20px / 1.25rem • Semibold (600) • Line height 1.4
                </p>
                <p className="text-caption-1 text-gray-400 mt-1">
                  Use for: Card titles, list headers
                </p>
              </div>
            </div>
          </div>

          {/* Body Styles */}
          <div className="border-b border-gray-200 pb-6">
            <h3 className="text-title-3 text-gray-800 mb-4">Body Styles</h3>
            <div className="space-y-4">
              <div>
                <p className="text-headline text-gray-900">Headline</p>
                <p className="text-footnote text-gray-500 mt-1">
                  17px / 1.0625rem • Semibold (600) • Line height 1.45
                </p>
                <p className="text-caption-1 text-gray-400 mt-1">
                  Use for: Emphasized body text
                </p>
              </div>
              
              <div>
                <p className="text-body text-gray-900">Body</p>
                <p className="text-footnote text-gray-500 mt-1">
                  17px / 1.0625rem • Regular (400) • Line height 1.5
                </p>
                <p className="text-caption-1 text-gray-400 mt-1">
                  Use for: Primary body text
                </p>
              </div>
              
              <div>
                <p className="text-callout text-gray-900">Callout</p>
                <p className="text-footnote text-gray-500 mt-1">
                  16px / 1rem • Regular (400) • Line height 1.5
                </p>
                <p className="text-caption-1 text-gray-400 mt-1">
                  Use for: Secondary body text
                </p>
              </div>
              
              <div>
                <p className="text-subhead text-gray-900">Subhead</p>
                <p className="text-footnote text-gray-500 mt-1">
                  15px / 0.9375rem • Regular (400) • Line height 1.5
                </p>
                <p className="text-caption-1 text-gray-400 mt-1">
                  Use for: Tertiary text, labels
                </p>
              </div>
            </div>
          </div>

          {/* Small Text Styles */}
          <div>
            <h3 className="text-title-3 text-gray-800 mb-4">Small Text Styles</h3>
            <div className="space-y-4">
              <div>
                <p className="text-footnote text-gray-900">Footnote</p>
                <p className="text-footnote text-gray-500 mt-1">
                  13px / 0.8125rem • Regular (400) • Line height 1.5
                </p>
                <p className="text-caption-1 text-gray-400 mt-1">
                  Use for: Captions, helper text
                </p>
              </div>
              
              <div>
                <p className="text-caption-1 text-gray-900">Caption 1</p>
                <p className="text-footnote text-gray-500 mt-1">
                  12px / 0.75rem • Regular (400) • Line height 1.5
                </p>
                <p className="text-caption-1 text-gray-400 mt-1">
                  Use for: Timestamps, metadata
                </p>
              </div>
              
              <div>
                <p className="text-caption-2 text-gray-900">Caption 2</p>
                <p className="text-footnote text-gray-500 mt-1">
                  11px / 0.6875rem • Regular (400) • Line height 1.5
                </p>
                <p className="text-caption-1 text-gray-400 mt-1">
                  Use for: Fine print, legal text
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  ),
};

/**
 * ## Responsive Typography
 * 
 * Fluid typography that scales smoothly across all viewport sizes using CSS clamp().
 * Resize your browser to see the text scale automatically.
 */
export const ResponsiveTypography: Story = {
  render: () => (
    <div className="space-y-8">
      <div>
        <h2 className="text-title-2 text-gray-900 mb-4">Responsive Fluid Typography</h2>
        <p className="text-body text-gray-600 mb-6">
          Resize your browser window to see the text scale smoothly.
        </p>
        
        <div className="space-y-6 border border-gray-200 rounded-lg p-6">
          <div>
            <p className="text-responsive-display text-gray-900">
              Responsive Display
            </p>
            <p className="text-footnote text-gray-500 mt-2">
              Scales from 40px (mobile) to 56px (desktop)
            </p>
            <code className="text-caption-1 text-gray-600 bg-gray-100 px-2 py-1 rounded mt-2 inline-block">
              clamp(2.5rem, 2rem + 2vw, 3.5rem)
            </code>
          </div>
          
          <div>
            <p className="text-responsive-title text-gray-900">
              Responsive Title
            </p>
            <p className="text-footnote text-gray-500 mt-2">
              Scales from 24px (mobile) to 28px (desktop)
            </p>
            <code className="text-caption-1 text-gray-600 bg-gray-100 px-2 py-1 rounded mt-2 inline-block">
              clamp(1.5rem, 1.25rem + 1vw, 1.75rem)
            </code>
          </div>
          
          <div>
            <p className="text-responsive-body text-gray-900">
              Responsive Body Text - This is a longer paragraph to demonstrate how body text scales
              across different viewport sizes. The text remains readable at all sizes while
              maintaining optimal line length and spacing.
            </p>
            <p className="text-footnote text-gray-500 mt-2">
              Scales from 16px (mobile) to 17px (desktop)
            </p>
            <code className="text-caption-1 text-gray-600 bg-gray-100 px-2 py-1 rounded mt-2 inline-block">
              clamp(1rem, 0.9rem + 0.3vw, 1.0625rem)
            </code>
          </div>
        </div>
      </div>
    </div>
  ),
};

/**
 * ## Font Weights
 * 
 * Our font weight scale from Light (300) to Bold (700).
 * Use appropriate weights to create hierarchy and emphasis.
 */
export const FontWeights: Story = {
  render: () => (
    <div className="space-y-6">
      <div>
        <h2 className="text-title-2 text-gray-900 mb-4">Font Weight Scale</h2>
        <div className="space-y-4">
          <div>
            <p className="text-title-1 font-light text-gray-900">Light (300)</p>
            <p className="text-footnote text-gray-500">
              Use for: Large display text (optional)
            </p>
          </div>
          
          <div>
            <p className="text-title-1 font-normal text-gray-900">Regular (400)</p>
            <p className="text-footnote text-gray-500">
              Use for: Body text, default weight
            </p>
          </div>
          
          <div>
            <p className="text-title-1 font-medium text-gray-900">Medium (500)</p>
            <p className="text-footnote text-gray-500">
              Use for: Subtle emphasis, navigation
            </p>
          </div>
          
          <div>
            <p className="text-title-1 font-semibold text-gray-900">Semibold (600)</p>
            <p className="text-footnote text-gray-500">
              Use for: Headings, important labels
            </p>
          </div>
          
          <div>
            <p className="text-title-1 font-bold text-gray-900">Bold (700)</p>
            <p className="text-footnote text-gray-500">
              Use for: Strong emphasis, CTAs
            </p>
          </div>
        </div>
      </div>
      
      <div className="border-t border-gray-200 pt-6">
        <h3 className="text-title-3 text-gray-800 mb-4">Weight Pairing Examples</h3>
        <div className="space-y-6">
          <div className="border border-gray-200 rounded-lg p-4">
            <h4 className="text-title-2 font-semibold text-gray-900 mb-2">
              Dashboard Overview
            </h4>
            <p className="text-body font-normal text-gray-700">
              Your AI agents are running smoothly with 99.9% uptime. All systems operational.
            </p>
          </div>
          
          <div className="border border-gray-200 rounded-lg p-4">
            <h4 className="text-headline font-semibold text-gray-900 mb-1">
              Active Agents
            </h4>
            <p className="text-display-2 font-bold text-primary-600 mb-1">
              24
            </p>
            <p className="text-footnote font-normal text-gray-500">
              +3 from yesterday
            </p>
          </div>
        </div>
      </div>
    </div>
  ),
};

/**
 * ## Line Height & Spacing
 * 
 * Proper line height ensures readability. Headlines use tighter line heights (1.25),
 * while body text uses comfortable spacing (1.5).
 */
export const LineHeightSpacing: Story = {
  render: () => (
    <div className="space-y-8">
      <div>
        <h2 className="text-title-2 text-gray-900 mb-4">Line Height Examples</h2>
        
        <div className="space-y-6">
          <div className="border border-gray-200 rounded-lg p-4">
            <h3 className="text-title-3 text-gray-800 mb-2">Tight (1.25)</h3>
            <p className="text-title-1 leading-tight text-gray-900">
              This is a headline with tight line height.
              Perfect for large display text and titles.
              Creates visual impact and saves space.
            </p>
            <p className="text-footnote text-gray-500 mt-2">
              Use for: Headlines, titles, display text
            </p>
          </div>
          
          <div className="border border-gray-200 rounded-lg p-4">
            <h3 className="text-title-3 text-gray-800 mb-2">Normal (1.5)</h3>
            <p className="text-body leading-normal text-gray-900">
              This is body text with normal line height.
              Optimal for reading longer paragraphs.
              Provides comfortable spacing between lines.
              Makes text easy to scan and comprehend.
            </p>
            <p className="text-footnote text-gray-500 mt-2">
              Use for: Body text, UI elements, most content
            </p>
          </div>
          
          <div className="border border-gray-200 rounded-lg p-4">
            <h3 className="text-title-3 text-gray-800 mb-2">Relaxed (1.75)</h3>
            <p className="text-body leading-relaxed text-gray-900">
              This is long-form content with relaxed line height.
              Extra spacing improves readability for extended reading.
              Reduces eye strain during long reading sessions.
              Perfect for articles, documentation, and blog posts.
            </p>
            <p className="text-footnote text-gray-500 mt-2">
              Use for: Long-form content, articles, documentation
            </p>
          </div>
        </div>
      </div>
      
      <div className="border-t border-gray-200 pt-6">
        <h3 className="text-title-3 text-gray-800 mb-4">Letter Spacing</h3>
        <div className="space-y-4">
          <div>
            <p className="text-title-1 tracking-tighter text-gray-900">
              Tighter (-0.02em)
            </p>
            <p className="text-footnote text-gray-500">
              Use for: Large display text
            </p>
          </div>
          
          <div>
            <p className="text-title-1 tracking-tight text-gray-900">
              Tight (-0.01em)
            </p>
            <p className="text-footnote text-gray-500">
              Use for: Headlines, titles
            </p>
          </div>
          
          <div>
            <p className="text-title-1 tracking-normal text-gray-900">
              Normal (0)
            </p>
            <p className="text-footnote text-gray-500">
              Use for: Body text, default
            </p>
          </div>
          
          <div>
            <p className="text-title-1 tracking-wide text-gray-900">
              Wide (0.01em)
            </p>
            <p className="text-footnote text-gray-500">
              Use for: Small text
            </p>
          </div>
          
          <div>
            <p className="text-title-1 tracking-wider text-gray-900 uppercase">
              Wider (0.05em)
            </p>
            <p className="text-footnote text-gray-500">
              Use for: All caps text
            </p>
          </div>
        </div>
      </div>
    </div>
  ),
};

/**
 * ## Real-World Examples
 * 
 * See how typography works in actual UI components and layouts.
 */
export const RealWorldExamples: Story = {
  render: () => (
    <div className="space-y-8">
      <div>
        <h2 className="text-title-2 text-gray-900 mb-6">Component Examples</h2>
        
        {/* Dashboard Header */}
        <div className="border border-gray-200 rounded-lg p-6 mb-6">
          <h3 className="text-caption-1 text-gray-500 uppercase tracking-wider mb-4">
            Dashboard Header
          </h3>
          <header className="space-y-2">
            <h1 className="text-large-title text-gray-900">
              Dashboard
            </h1>
            <p className="text-body text-gray-600">
              Monitor your AI agents and system performance
            </p>
          </header>
        </div>
        
        {/* Metric Card */}
        <div className="border border-gray-200 rounded-lg p-6 mb-6">
          <h3 className="text-caption-1 text-gray-500 uppercase tracking-wider mb-4">
            Metric Card
          </h3>
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <h3 className="text-title-3 text-gray-900 mb-2">
              Active Agents
            </h3>
            <p className="text-display-2 font-bold text-primary-600 mb-1">
              24
            </p>
            <p className="text-footnote text-success-600">
              +3 from yesterday
            </p>
          </div>
        </div>
        
        {/* Form */}
        <div className="border border-gray-200 rounded-lg p-6 mb-6">
          <h3 className="text-caption-1 text-gray-500 uppercase tracking-wider mb-4">
            Form Example
          </h3>
          <div className="space-y-4">
            <div>
              <label className="text-subhead font-medium text-gray-700 mb-1 block">
                Email Address
              </label>
              <input 
                type="email" 
                className="text-body text-gray-900 border border-gray-300 rounded-md px-3 py-2 w-full"
                placeholder="you@example.com"
              />
              <p className="text-footnote text-gray-500 mt-1">
                We'll never share your email with anyone else.
              </p>
            </div>
          </div>
        </div>
        
        {/* Alert */}
        <div className="border border-gray-200 rounded-lg p-6 mb-6">
          <h3 className="text-caption-1 text-gray-500 uppercase tracking-wider mb-4">
            Alert Message
          </h3>
          <div className="bg-success-50 border border-success-200 rounded-lg p-4">
            <h4 className="text-headline text-success-900 mb-1">
              Success!
            </h4>
            <p className="text-callout text-success-700">
              Your changes have been saved successfully.
            </p>
          </div>
        </div>
        
        {/* Article */}
        <div className="border border-gray-200 rounded-lg p-6">
          <h3 className="text-caption-1 text-gray-500 uppercase tracking-wider mb-4">
            Article Layout
          </h3>
          <article className="max-w-2xl">
            <h1 className="text-display-3 text-gray-900 mb-2">
              Getting Started with MorningAI
            </h1>
            <p className="text-subhead text-gray-500 mb-6">
              Published on October 24, 2025 • 5 min read
            </p>
            <p className="text-body text-gray-700 leading-relaxed mb-4">
              Welcome to MorningAI! This guide will help you get started with our platform
              and show you how to create your first AI agent. We've designed the experience
              to be intuitive and powerful, following Apple's design principles.
            </p>
            <p className="text-body text-gray-700 leading-relaxed">
              Our typography system ensures that all content is readable and accessible,
              with proper hierarchy and spacing throughout the interface.
            </p>
          </article>
        </div>
      </div>
    </div>
  ),
};

/**
 * ## Accessibility
 * 
 * All typography meets WCAG AA standards for contrast and readability.
 */
export const Accessibility: Story = {
  render: () => (
    <div className="space-y-6">
      <div>
        <h2 className="text-title-2 text-gray-900 mb-4">WCAG AA Compliance</h2>
        
        <div className="space-y-4">
          <div className="border border-gray-200 rounded-lg p-4">
            <h3 className="text-title-3 text-gray-900 mb-2">
              Contrast Ratios
            </h3>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-body text-gray-900">Body text on white</span>
                <span className="text-footnote text-success-600 font-medium">
                  6.12:1 ✓
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-body text-gray-700">Secondary text on white</span>
                <span className="text-footnote text-success-600 font-medium">
                  5.85:1 ✓
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-body text-gray-600">Tertiary text on white</span>
                <span className="text-footnote text-success-600 font-medium">
                  4.54:1 ✓
                </span>
              </div>
            </div>
          </div>
          
          <div className="border border-gray-200 rounded-lg p-4">
            <h3 className="text-title-3 text-gray-900 mb-2">
              Dynamic Type Support
            </h3>
            <p className="text-body text-gray-700 mb-2">
              All typography uses rem units and respects user font size preferences.
            </p>
            <code className="text-caption-1 text-gray-600 bg-gray-100 px-2 py-1 rounded">
              font-size: 1.0625rem; /* Scales with user settings */
            </code>
          </div>
          
          <div className="border border-gray-200 rounded-lg p-4">
            <h3 className="text-title-3 text-gray-900 mb-2">
              Focus Indicators
            </h3>
            <p className="text-body text-gray-700 mb-3">
              All interactive text elements have visible focus indicators:
            </p>
            <div className="space-y-2">
              <a href="#" className="text-body text-primary-text underline block">
                This is a focusable link
              </a>
              <button className="text-body text-primary-text underline">
                This is a focusable button
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  ),
};

/**
 * ## Usage Guidelines
 * 
 * Best practices for using the typography system.
 */
export const UsageGuidelines: Story = {
  render: () => (
    <div className="space-y-8">
      <div>
        <h2 className="text-title-2 text-gray-900 mb-6">Do's and Don'ts</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Do's */}
          <div className="border border-success-200 bg-success-50 rounded-lg p-6">
            <h3 className="text-title-3 text-success-900 mb-4">✅ Do</h3>
            <ul className="space-y-3 text-body text-success-800">
              <li>• Use the type scale consistently</li>
              <li>• Maintain clear hierarchy</li>
              <li>• Limit to 2-3 weights per design</li>
              <li>• Test at different sizes</li>
              <li>• Support dynamic type</li>
              <li>• Ensure sufficient contrast</li>
            </ul>
          </div>
          
          {/* Don'ts */}
          <div className="border border-error-200 bg-error-50 rounded-lg p-6">
            <h3 className="text-title-3 text-error-900 mb-4">❌ Don't</h3>
            <ul className="space-y-3 text-body text-error-800">
              <li>• Create custom font sizes</li>
              <li>• Use too many type styles</li>
              <li>• Rely on color alone for hierarchy</li>
              <li>• Use small text for critical info</li>
              <li>• Use all caps for long text</li>
              <li>• Use light weights on small text</li>
            </ul>
          </div>
        </div>
      </div>
      
      <div className="border-t border-gray-200 pt-6">
        <h3 className="text-title-3 text-gray-800 mb-4">Code Examples</h3>
        
        <div className="space-y-4">
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <p className="text-subhead font-medium text-gray-700 mb-2">
              Dashboard Header
            </p>
            <pre className="text-caption-1 text-gray-800 overflow-x-auto">
{`<header className="space-y-2">
  <h1 className="text-large-title text-gray-900">
    Dashboard
  </h1>
  <p className="text-body text-gray-600">
    Monitor your AI agents
  </p>
</header>`}
            </pre>
          </div>
          
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <p className="text-subhead font-medium text-gray-700 mb-2">
              Metric Card
            </p>
            <pre className="text-caption-1 text-gray-800 overflow-x-auto">
{`<div className="card">
  <h3 className="text-title-3 text-gray-900 mb-2">
    Active Agents
  </h3>
  <p className="text-headline text-primary-600 mb-1">
    24
  </p>
  <p className="text-footnote text-gray-500">
    +3 from yesterday
  </p>
</div>`}
            </pre>
          </div>
        </div>
      </div>
    </div>
  ),
};
