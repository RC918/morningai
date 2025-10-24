import type { Meta, StoryObj } from '@storybook/react';
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableFooter,
  TableHead,
  TableHeader,
  TableRow,
} from './table';
import { Badge } from './badge';
import { Checkbox } from './checkbox';

/**
 * The Table component provides a flexible and accessible data table interface.
 * It's composed of multiple sub-components that work together to create rich table layouts.
 * 
 * ## Features
 * - Responsive design with horizontal scrolling on small screens
 * - Hover states for better row identification
 * - Support for row selection with checkboxes
 * - Footer row for totals and summaries
 * - Caption support for accessibility
 * - Customizable styling with Tailwind CSS
 */
const meta = {
  title: 'UI/Table',
  component: Table,
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: `
The Table component is a comprehensive solution for displaying tabular data. It consists of multiple sub-components that provide semantic HTML structure and consistent styling.

### Sub-components
- **Table**: Main container with horizontal scroll support
- **TableHeader**: Contains column headers
- **TableBody**: Contains data rows
- **TableFooter**: Optional footer for summaries
- **TableRow**: Individual row with hover effects
- **TableHead**: Column header cell
- **TableCell**: Data cell
- **TableCaption**: Accessible table description

### Usage Guidelines
- Use for displaying structured data with multiple columns
- Include TableCaption for accessibility
- Use TableHeader for column labels
- Use TableFooter for totals or summaries
- Keep column count reasonable for mobile devices
- Consider pagination for large datasets

### Accessibility
- Semantic HTML table elements
- Caption support for screen readers
- Proper header associations
- Keyboard navigation support
- High contrast hover states
        `,
      },
    },
  },
  tags: ['autodocs'],
} satisfies Meta<typeof Table>;

export default meta;
type Story = StoryObj<typeof meta>;

const invoices = [
  {
    invoice: 'INV001',
    paymentStatus: 'Paid',
    totalAmount: '$250.00',
    paymentMethod: 'Credit Card',
  },
  {
    invoice: 'INV002',
    paymentStatus: 'Pending',
    totalAmount: '$150.00',
    paymentMethod: 'PayPal',
  },
  {
    invoice: 'INV003',
    paymentStatus: 'Unpaid',
    totalAmount: '$350.00',
    paymentMethod: 'Bank Transfer',
  },
  {
    invoice: 'INV004',
    paymentStatus: 'Paid',
    totalAmount: '$450.00',
    paymentMethod: 'Credit Card',
  },
  {
    invoice: 'INV005',
    paymentStatus: 'Paid',
    totalAmount: '$550.00',
    paymentMethod: 'PayPal',
  },
];

export const Default: Story = {
  render: () => (
    <Table>
      <TableCaption>A list of your recent invoices.</TableCaption>
      <TableHeader>
        <TableRow>
          <TableHead className="w-[100px]">Invoice</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Method</TableHead>
          <TableHead className="text-right">Amount</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {invoices.map((invoice) => (
          <TableRow key={invoice.invoice}>
            <TableCell className="font-medium">{invoice.invoice}</TableCell>
            <TableCell>{invoice.paymentStatus}</TableCell>
            <TableCell>{invoice.paymentMethod}</TableCell>
            <TableCell className="text-right">{invoice.totalAmount}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Basic table with caption showing invoice data.',
      },
    },
  },
};

export const WithFooter: Story = {
  render: () => (
    <Table>
      <TableCaption>A list of your recent invoices.</TableCaption>
      <TableHeader>
        <TableRow>
          <TableHead className="w-[100px]">Invoice</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Method</TableHead>
          <TableHead className="text-right">Amount</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {invoices.map((invoice) => (
          <TableRow key={invoice.invoice}>
            <TableCell className="font-medium">{invoice.invoice}</TableCell>
            <TableCell>{invoice.paymentStatus}</TableCell>
            <TableCell>{invoice.paymentMethod}</TableCell>
            <TableCell className="text-right">{invoice.totalAmount}</TableCell>
          </TableRow>
        ))}
      </TableBody>
      <TableFooter>
        <TableRow>
          <TableCell colSpan={3}>Total</TableCell>
          <TableCell className="text-right">$1,750.00</TableCell>
        </TableRow>
      </TableFooter>
    </Table>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Table with footer row showing totals.',
      },
    },
  },
};

export const WithBadges: Story = {
  render: () => (
    <Table>
      <TableCaption>Invoice status with visual indicators.</TableCaption>
      <TableHeader>
        <TableRow>
          <TableHead className="w-[100px]">Invoice</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Method</TableHead>
          <TableHead className="text-right">Amount</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {invoices.map((invoice) => (
          <TableRow key={invoice.invoice}>
            <TableCell className="font-medium">{invoice.invoice}</TableCell>
            <TableCell>
              <Badge
                variant={
                  invoice.paymentStatus === 'Paid'
                    ? 'default'
                    : invoice.paymentStatus === 'Pending'
                    ? 'secondary'
                    : 'destructive'
                }
              >
                {invoice.paymentStatus}
              </Badge>
            </TableCell>
            <TableCell>{invoice.paymentMethod}</TableCell>
            <TableCell className="text-right">{invoice.totalAmount}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Table with Badge components for status visualization.',
      },
    },
  },
};

export const WithCheckboxes: Story = {
  render: () => (
    <Table>
      <TableCaption>Selectable invoice list.</TableCaption>
      <TableHeader>
        <TableRow>
          <TableHead className="w-[50px]">
            <Checkbox />
          </TableHead>
          <TableHead className="w-[100px]">Invoice</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Method</TableHead>
          <TableHead className="text-right">Amount</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {invoices.map((invoice) => (
          <TableRow key={invoice.invoice}>
            <TableCell>
              <Checkbox />
            </TableCell>
            <TableCell className="font-medium">{invoice.invoice}</TableCell>
            <TableCell>{invoice.paymentStatus}</TableCell>
            <TableCell>{invoice.paymentMethod}</TableCell>
            <TableCell className="text-right">{invoice.totalAmount}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Table with checkboxes for row selection.',
      },
    },
  },
};

export const EmptyState: Story = {
  render: () => (
    <Table>
      <TableCaption>No invoices found.</TableCaption>
      <TableHeader>
        <TableRow>
          <TableHead className="w-[100px]">Invoice</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Method</TableHead>
          <TableHead className="text-right">Amount</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        <TableRow>
          <TableCell colSpan={4} className="h-24 text-center">
            No results.
          </TableCell>
        </TableRow>
      </TableBody>
    </Table>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Table showing empty state when no data is available.',
      },
    },
  },
};

export const SingleRow: Story = {
  render: () => (
    <Table>
      <TableCaption>Single invoice entry.</TableCaption>
      <TableHeader>
        <TableRow>
          <TableHead className="w-[100px]">Invoice</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Method</TableHead>
          <TableHead className="text-right">Amount</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        <TableRow>
          <TableCell className="font-medium">INV001</TableCell>
          <TableCell>Paid</TableCell>
          <TableCell>Credit Card</TableCell>
          <TableCell className="text-right">$250.00</TableCell>
        </TableRow>
      </TableBody>
    </Table>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Table with only one data row.',
      },
    },
  },
};

export const ManyColumns: Story = {
  render: () => (
    <Table>
      <TableCaption>Invoice details with many columns.</TableCaption>
      <TableHeader>
        <TableRow>
          <TableHead>Invoice</TableHead>
          <TableHead>Customer</TableHead>
          <TableHead>Email</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Method</TableHead>
          <TableHead>Date</TableHead>
          <TableHead>Due Date</TableHead>
          <TableHead className="text-right">Amount</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        <TableRow>
          <TableCell className="font-medium">INV001</TableCell>
          <TableCell>John Doe</TableCell>
          <TableCell>john@example.com</TableCell>
          <TableCell>Paid</TableCell>
          <TableCell>Credit Card</TableCell>
          <TableCell>2024-01-15</TableCell>
          <TableCell>2024-02-15</TableCell>
          <TableCell className="text-right">$250.00</TableCell>
        </TableRow>
        <TableRow>
          <TableCell className="font-medium">INV002</TableCell>
          <TableCell>Jane Smith</TableCell>
          <TableCell>jane@example.com</TableCell>
          <TableCell>Pending</TableCell>
          <TableCell>PayPal</TableCell>
          <TableCell>2024-01-16</TableCell>
          <TableCell>2024-02-16</TableCell>
          <TableCell className="text-right">$150.00</TableCell>
        </TableRow>
      </TableBody>
    </Table>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Table with many columns to demonstrate horizontal scrolling on small screens.',
      },
    },
  },
};

export const LongContent: Story = {
  render: () => (
    <Table>
      <TableCaption>Invoices with long text content.</TableCaption>
      <TableHeader>
        <TableRow>
          <TableHead className="w-[100px]">Invoice</TableHead>
          <TableHead>Description</TableHead>
          <TableHead>Status</TableHead>
          <TableHead className="text-right">Amount</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        <TableRow>
          <TableCell className="font-medium">INV001</TableCell>
          <TableCell>
            Professional services for website development including design, frontend implementation, backend API development, and deployment
          </TableCell>
          <TableCell>Paid</TableCell>
          <TableCell className="text-right">$2,500.00</TableCell>
        </TableRow>
        <TableRow>
          <TableCell className="font-medium">INV002</TableCell>
          <TableCell>
            Monthly subscription for cloud hosting services with premium support and automatic backups
          </TableCell>
          <TableCell>Pending</TableCell>
          <TableCell className="text-right">$150.00</TableCell>
        </TableRow>
      </TableBody>
    </Table>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Table with long text content to test text wrapping behavior.',
      },
    },
  },
};

export const CompactTable: Story = {
  render: () => (
    <Table>
      <TableCaption>Compact table with minimal data.</TableCaption>
      <TableHeader>
        <TableRow>
          <TableHead>ID</TableHead>
          <TableHead>Name</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        <TableRow>
          <TableCell>1</TableCell>
          <TableCell>A</TableCell>
        </TableRow>
        <TableRow>
          <TableCell>2</TableCell>
          <TableCell>B</TableCell>
        </TableRow>
        <TableRow>
          <TableCell>3</TableCell>
          <TableCell>C</TableCell>
        </TableRow>
      </TableBody>
    </Table>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Minimal table with just two columns and short content.',
      },
    },
  },
};

export const ManyRows: Story = {
  render: () => {
    const manyInvoices = Array.from({ length: 20 }, (_, i) => ({
      invoice: `INV${String(i + 1).padStart(3, '0')}`,
      paymentStatus: ['Paid', 'Pending', 'Unpaid'][i % 3],
      totalAmount: `$${(Math.random() * 1000).toFixed(2)}`,
      paymentMethod: ['Credit Card', 'PayPal', 'Bank Transfer'][i % 3],
    }));

    return (
      <Table>
        <TableCaption>Large dataset with many rows.</TableCaption>
        <TableHeader>
          <TableRow>
            <TableHead className="w-[100px]">Invoice</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Method</TableHead>
            <TableHead className="text-right">Amount</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {manyInvoices.map((invoice) => (
            <TableRow key={invoice.invoice}>
              <TableCell className="font-medium">{invoice.invoice}</TableCell>
              <TableCell>{invoice.paymentStatus}</TableCell>
              <TableCell>{invoice.paymentMethod}</TableCell>
              <TableCell className="text-right">{invoice.totalAmount}</TableCell>
            </TableRow>
          ))}
        </TableBody>
        <TableFooter>
          <TableRow>
            <TableCell colSpan={3}>Total ({manyInvoices.length} items)</TableCell>
            <TableCell className="text-right">
              $
              {manyInvoices
                .reduce((sum, inv) => sum + parseFloat(inv.totalAmount.slice(1)), 0)
                .toFixed(2)}
            </TableCell>
          </TableRow>
        </TableFooter>
      </Table>
    );
  },
  parameters: {
    docs: {
      description: {
        story: 'Table with many rows to test scrolling and performance.',
      },
    },
  },
};
