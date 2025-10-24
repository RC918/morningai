import type { Meta, StoryObj } from '@storybook/react';
import { Tabs, TabsList, TabsTrigger, TabsContent } from './tabs';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from './card';

const meta = {
  title: 'UI/Tabs',
  component: Tabs,
  parameters: {
    layout: 'padded',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof Tabs>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <Tabs defaultValue="account" className="w-full max-w-md">
      <TabsList>
        <TabsTrigger value="account">Account</TabsTrigger>
        <TabsTrigger value="password">Password</TabsTrigger>
        <TabsTrigger value="notifications">Notifications</TabsTrigger>
      </TabsList>
      <TabsContent value="account">
        <Card>
          <CardHeader>
            <CardTitle>Account</CardTitle>
            <CardDescription>
              Make changes to your account here.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="space-y-1">
              <label className="text-sm font-medium">Name</label>
              <input className="w-full px-3 py-2 border rounded-md" defaultValue="Ryan Chen" />
            </div>
            <div className="space-y-1">
              <label className="text-sm font-medium">Email</label>
              <input className="w-full px-3 py-2 border rounded-md" defaultValue="ryan@morningai.com" />
            </div>
          </CardContent>
        </Card>
      </TabsContent>
      <TabsContent value="password">
        <Card>
          <CardHeader>
            <CardTitle>Password</CardTitle>
            <CardDescription>
              Change your password here.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="space-y-1">
              <label className="text-sm font-medium">Current Password</label>
              <input type="password" className="w-full px-3 py-2 border rounded-md" />
            </div>
            <div className="space-y-1">
              <label className="text-sm font-medium">New Password</label>
              <input type="password" className="w-full px-3 py-2 border rounded-md" />
            </div>
          </CardContent>
        </Card>
      </TabsContent>
      <TabsContent value="notifications">
        <Card>
          <CardHeader>
            <CardTitle>Notifications</CardTitle>
            <CardDescription>
              Manage your notification preferences.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium">Email notifications</label>
              <input type="checkbox" defaultChecked />
            </div>
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium">Push notifications</label>
              <input type="checkbox" />
            </div>
          </CardContent>
        </Card>
      </TabsContent>
    </Tabs>
  ),
};

export const Simple: Story = {
  render: () => (
    <Tabs defaultValue="overview" className="w-full max-w-md">
      <TabsList>
        <TabsTrigger value="overview">Overview</TabsTrigger>
        <TabsTrigger value="analytics">Analytics</TabsTrigger>
        <TabsTrigger value="reports">Reports</TabsTrigger>
      </TabsList>
      <TabsContent value="overview" className="mt-4">
        <p className="text-sm text-muted-foreground">
          View your dashboard overview with key metrics and insights.
        </p>
      </TabsContent>
      <TabsContent value="analytics" className="mt-4">
        <p className="text-sm text-muted-foreground">
          Detailed analytics and performance metrics for your account.
        </p>
      </TabsContent>
      <TabsContent value="reports" className="mt-4">
        <p className="text-sm text-muted-foreground">
          Generate and download custom reports for your data.
        </p>
      </TabsContent>
    </Tabs>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Simple tabs with text content only.',
      },
    },
  },
};

export const FullWidth: Story = {
  render: () => (
    <Tabs defaultValue="all" className="w-full">
      <TabsList className="w-full">
        <TabsTrigger value="all" className="flex-1">All</TabsTrigger>
        <TabsTrigger value="active" className="flex-1">Active</TabsTrigger>
        <TabsTrigger value="completed" className="flex-1">Completed</TabsTrigger>
        <TabsTrigger value="archived" className="flex-1">Archived</TabsTrigger>
      </TabsList>
      <TabsContent value="all" className="mt-4">
        <div className="space-y-2">
          <div className="p-3 border rounded-md">Task 1</div>
          <div className="p-3 border rounded-md">Task 2</div>
          <div className="p-3 border rounded-md">Task 3</div>
        </div>
      </TabsContent>
      <TabsContent value="active" className="mt-4">
        <div className="space-y-2">
          <div className="p-3 border rounded-md">Active Task 1</div>
          <div className="p-3 border rounded-md">Active Task 2</div>
        </div>
      </TabsContent>
      <TabsContent value="completed" className="mt-4">
        <div className="space-y-2">
          <div className="p-3 border rounded-md">Completed Task 1</div>
        </div>
      </TabsContent>
      <TabsContent value="archived" className="mt-4">
        <p className="text-sm text-muted-foreground">No archived tasks</p>
      </TabsContent>
    </Tabs>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Tabs with full-width triggers that distribute evenly.',
      },
    },
  },
};
