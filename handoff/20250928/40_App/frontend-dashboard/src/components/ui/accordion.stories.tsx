import type { Meta, StoryObj } from '@storybook/react';
import { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from './accordion';

const meta = {
  title: 'UI/Accordion',
  component: Accordion,
  parameters: {
    layout: 'padded',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof Accordion>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Single: Story = {
  render: () => (
    <Accordion type="single" collapsible className="w-full max-w-md">
      <AccordionItem value="item-1">
        <AccordionTrigger>What is Morning AI?</AccordionTrigger>
        <AccordionContent>
          Morning AI is an intelligent automation platform that helps businesses streamline their workflows and make data-driven decisions.
        </AccordionContent>
      </AccordionItem>
      <AccordionItem value="item-2">
        <AccordionTrigger>How does it work?</AccordionTrigger>
        <AccordionContent>
          Our platform uses advanced AI algorithms to analyze your data, identify patterns, and provide actionable insights. It integrates seamlessly with your existing tools and workflows.
        </AccordionContent>
      </AccordionItem>
      <AccordionItem value="item-3">
        <AccordionTrigger>Is it secure?</AccordionTrigger>
        <AccordionContent>
          Yes, security is our top priority. We use industry-standard encryption, regular security audits, and comply with major data protection regulations including GDPR and SOC 2.
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Single accordion - only one item can be open at a time.',
      },
    },
  },
};

export const Multiple: Story = {
  render: () => (
    <Accordion type="multiple" className="w-full max-w-md">
      <AccordionItem value="item-1">
        <AccordionTrigger>Features</AccordionTrigger>
        <AccordionContent>
          <ul className="list-disc pl-4 space-y-1">
            <li>Real-time analytics</li>
            <li>Automated workflows</li>
            <li>Custom integrations</li>
            <li>24/7 support</li>
          </ul>
        </AccordionContent>
      </AccordionItem>
      <AccordionItem value="item-2">
        <AccordionTrigger>Pricing</AccordionTrigger>
        <AccordionContent>
          <p>We offer flexible pricing plans to suit businesses of all sizes:</p>
          <ul className="list-disc pl-4 mt-2 space-y-1">
            <li>Starter: $29/month</li>
            <li>Professional: $99/month</li>
            <li>Enterprise: Custom pricing</li>
          </ul>
        </AccordionContent>
      </AccordionItem>
      <AccordionItem value="item-3">
        <AccordionTrigger>Support</AccordionTrigger>
        <AccordionContent>
          Our support team is available 24/7 via email, chat, and phone. We also provide comprehensive documentation and video tutorials.
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Multiple accordion - multiple items can be open simultaneously.',
      },
    },
  },
};

export const DefaultOpen: Story = {
  render: () => (
    <Accordion type="single" collapsible defaultValue="item-2" className="w-full max-w-md">
      <AccordionItem value="item-1">
        <AccordionTrigger>Getting Started</AccordionTrigger>
        <AccordionContent>
          Follow our quick start guide to set up your account and configure your first workflow.
        </AccordionContent>
      </AccordionItem>
      <AccordionItem value="item-2">
        <AccordionTrigger>Quick Start Guide</AccordionTrigger>
        <AccordionContent>
          <ol className="list-decimal pl-4 space-y-2">
            <li>Create your account</li>
            <li>Connect your data sources</li>
            <li>Configure your first workflow</li>
            <li>Monitor results in real-time</li>
          </ol>
        </AccordionContent>
      </AccordionItem>
      <AccordionItem value="item-3">
        <AccordionTrigger>Advanced Features</AccordionTrigger>
        <AccordionContent>
          Explore advanced features like custom integrations, API access, and enterprise-grade security options.
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Accordion with a default open item using defaultValue prop.',
      },
    },
  },
};

export const WithRichContent: Story = {
  render: () => (
    <Accordion type="single" collapsible className="w-full max-w-md">
      <AccordionItem value="item-1">
        <AccordionTrigger>System Requirements</AccordionTrigger>
        <AccordionContent>
          <div className="space-y-3">
            <div>
              <h4 className="font-medium mb-1">Minimum Requirements</h4>
              <ul className="list-disc pl-4 text-sm">
                <li>Modern web browser (Chrome, Firefox, Safari, Edge)</li>
                <li>Internet connection (1 Mbps minimum)</li>
                <li>JavaScript enabled</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium mb-1">Recommended</h4>
              <ul className="list-disc pl-4 text-sm">
                <li>Latest browser version</li>
                <li>High-speed internet (10+ Mbps)</li>
                <li>Desktop or tablet device</li>
              </ul>
            </div>
          </div>
        </AccordionContent>
      </AccordionItem>
      <AccordionItem value="item-2">
        <AccordionTrigger>API Documentation</AccordionTrigger>
        <AccordionContent>
          <p className="mb-2">Access our comprehensive API documentation:</p>
          <div className="bg-muted p-3 rounded-md text-sm font-mono">
            https://api.morningai.com/docs
          </div>
          <p className="mt-2 text-sm">
            Includes authentication guides, endpoint references, and code examples in multiple languages.
          </p>
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Accordion with rich content including headings, lists, and code blocks.',
      },
    },
  },
};
