import { useState } from 'react'
import { http, HttpResponse } from 'msw'
import ApprovalWorkflow from './ApprovalWorkflow'

export default {
  title: 'Sessions/ApprovalWorkflow',
  component: ApprovalWorkflow,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
    msw: {
      handlers: [
        http.post('/api/sessions/:sessionId/tasks/:taskId/approve', () => {
          return HttpResponse.json({ success: true })
        }),
        http.post('/api/sessions/:sessionId/tasks/:taskId/reject', () => {
          return HttpResponse.json({ success: true })
        }),
      ],
    },
  },
  argTypes: {
    sessionId: { control: 'text' },
    taskId: { control: 'text' },
    isOpen: { control: 'boolean' },
    approvalData: { control: 'object' },
    onClose: { action: 'closed' },
    onApproved: { action: 'approved' },
    onRejected: { action: 'rejected' },
  },
}

const ApprovalWorkflowWrapper = (args) => {
  const [isOpen, setIsOpen] = useState(args.isOpen)
  
  return (
    <>
      <button 
        onClick={() => setIsOpen(true)}
        className="px-4 py-2 bg-wisdom text-white rounded-lg hover:bg-wisdom-dark"
      >
        Open Approval Dialog
      </button>
      <ApprovalWorkflow 
        {...args} 
        isOpen={isOpen} 
        onClose={() => {
          setIsOpen(false)
          args.onClose?.()
        }}
      />
    </>
  )
}

export const LowRisk = {
  render: ApprovalWorkflowWrapper,
  args: {
    sessionId: 'session-123',
    taskId: 'task-456',
    isOpen: true,
    approvalData: {
      taskName: 'Update README documentation',
      description: 'Add installation instructions and API documentation.',
      reason: 'This task modifies documentation files only. No code changes involved.',
      riskLevel: 'low',
      affectedResources: [
        { id: '1', name: 'README.md', type: 'code', action: 'modify' },
        { id: '2', name: 'docs/api.md', type: 'code', action: 'create' },
      ],
    },
  },
  parameters: {
    docs: {
      description: {
        story: 'Low risk approval for documentation changes.',
      },
    },
  },
}

export const MediumRisk = {
  render: ApprovalWorkflowWrapper,
  args: {
    sessionId: 'session-123',
    taskId: 'task-789',
    isOpen: true,
    approvalData: {
      taskName: 'Deploy to staging environment',
      description: 'Deploy the latest build to staging for QA testing.',
      reason: 'Staging deployment may affect ongoing QA tests. Coordinate with QA team.',
      riskLevel: 'medium',
      affectedResources: [
        { id: '1', name: 'staging-server', type: 'server', action: 'deploy' },
        { id: '2', name: 'staging-db', type: 'database', action: 'migrate' },
      ],
    },
  },
  parameters: {
    docs: {
      description: {
        story: 'Medium risk approval for staging deployment.',
      },
    },
  },
}

export const HighRisk = {
  render: ApprovalWorkflowWrapper,
  args: {
    sessionId: 'session-123',
    taskId: 'task-101',
    isOpen: true,
    approvalData: {
      taskName: 'Deploy to production',
      description: 'Deploy the authenticated release to production servers.',
      reason: 'Production deployment will affect all users. Ensure rollback plan is ready.',
      riskLevel: 'high',
      affectedResources: [
        { id: '1', name: 'prod-server-1', type: 'server', action: 'deploy' },
        { id: '2', name: 'prod-server-2', type: 'server', action: 'deploy' },
        { id: '3', name: 'prod-database', type: 'database', action: 'migrate' },
        { id: '4', name: 'cdn-cache', type: 'server', action: 'invalidate' },
      ],
    },
  },
  parameters: {
    docs: {
      description: {
        story: 'High risk approval for production deployment.',
      },
    },
  },
}

export const CriticalRisk = {
  render: ApprovalWorkflowWrapper,
  args: {
    sessionId: 'session-123',
    taskId: 'task-999',
    isOpen: true,
    approvalData: {
      taskName: 'Database schema migration',
      description: 'Apply breaking schema changes to production database.',
      reason: 'CRITICAL: This migration includes destructive changes. Data loss is possible if rollback fails. Requires CTO approval.',
      riskLevel: 'critical',
      affectedResources: [
        { id: '1', name: 'prod-database', type: 'database', action: 'migrate' },
        { id: '2', name: 'users_table', type: 'database', action: 'alter' },
        { id: '3', name: 'sessions_table', type: 'database', action: 'drop' },
        { id: '4', name: 'backup-service', type: 'server', action: 'trigger' },
      ],
    },
  },
  parameters: {
    docs: {
      description: {
        story: 'Critical risk approval requiring executive approval.',
      },
    },
  },
}

export const WithCredentialsAccess = {
  render: ApprovalWorkflowWrapper,
  args: {
    sessionId: 'session-123',
    taskId: 'task-sec-1',
    isOpen: true,
    approvalData: {
      taskName: 'Rotate API credentials',
      description: 'Generate new API keys and update environment variables.',
      reason: 'This task will access and modify sensitive credentials. Ensure secure handling.',
      riskLevel: 'high',
      affectedResources: [
        { id: '1', name: 'API_KEY', type: 'credentials', action: 'rotate' },
        { id: '2', name: 'DATABASE_URL', type: 'credentials', action: 'update' },
        { id: '3', name: 'secrets-manager', type: 'server', action: 'write' },
      ],
    },
  },
  parameters: {
    docs: {
      description: {
        story: 'Approval for tasks involving credential access.',
      },
    },
  },
}

export const ManyAffectedResources = {
  render: ApprovalWorkflowWrapper,
  args: {
    sessionId: 'session-123',
    taskId: 'task-bulk-1',
    isOpen: true,
    approvalData: {
      taskName: 'Full system update',
      description: 'Apply updates across all microservices.',
      reason: 'Coordinated update across multiple services. Some downtime expected.',
      riskLevel: 'high',
      affectedResources: [
        { id: '1', name: 'auth-service', type: 'server', action: 'restart' },
        { id: '2', name: 'api-gateway', type: 'server', action: 'restart' },
        { id: '3', name: 'user-service', type: 'server', action: 'restart' },
        { id: '4', name: 'payment-service', type: 'server', action: 'restart' },
        { id: '5', name: 'notification-service', type: 'server', action: 'restart' },
        { id: '6', name: 'analytics-service', type: 'server', action: 'restart' },
        { id: '7', name: 'main-database', type: 'database', action: 'backup' },
        { id: '8', name: 'cache-cluster', type: 'server', action: 'flush' },
      ],
    },
  },
  parameters: {
    docs: {
      description: {
        story: 'Approval with many affected resources.',
      },
    },
  },
}

export const NoAffectedResources = {
  render: ApprovalWorkflowWrapper,
  args: {
    sessionId: 'session-123',
    taskId: 'task-simple-1',
    isOpen: true,
    approvalData: {
      taskName: 'Run code analysis',
      description: 'Execute static code analysis on the repository.',
      reason: 'Read-only operation. No resources will be modified.',
      riskLevel: 'low',
      affectedResources: [],
    },
  },
  parameters: {
    docs: {
      description: {
        story: 'Approval with no affected resources listed.',
      },
    },
  },
}

export const WithError = {
  render: ApprovalWorkflowWrapper,
  args: {
    sessionId: 'session-123',
    taskId: 'task-error-1',
    isOpen: true,
    approvalData: {
      taskName: 'Deploy to production',
      description: 'Deploy the latest build.',
      reason: 'Standard production deployment.',
      riskLevel: 'medium',
      affectedResources: [
        { id: '1', name: 'prod-server', type: 'server', action: 'deploy' },
      ],
    },
  },
  parameters: {
    msw: {
      handlers: [
        http.post('/api/sessions/:sessionId/tasks/:taskId/approve', () => {
          return HttpResponse.json(
            { error: 'Approval failed: Session has expired' },
            { status: 400 }
          )
        }),
        http.post('/api/sessions/:sessionId/tasks/:taskId/reject', () => {
          return HttpResponse.json(
            { error: 'Rejection failed: Insufficient permissions' },
            { status: 403 }
          )
        }),
      ],
    },
    docs: {
      description: {
        story: 'Demonstrates error handling when API calls fail.',
      },
    },
  },
}

export const Closed = {
  render: ApprovalWorkflowWrapper,
  args: {
    sessionId: 'session-123',
    taskId: 'task-456',
    isOpen: false,
    approvalData: {
      taskName: 'Sample task',
      reason: 'Sample reason',
      riskLevel: 'low',
      affectedResources: [],
    },
  },
  parameters: {
    docs: {
      description: {
        story: 'Dialog in closed state. Click the button to open.',
      },
    },
  },
}
