/* eslint-disable i18next/no-literal-string */
/* NOTE: This file is exempted from strict i18n checks as Storybook stories
 * are developer documentation, not user-facing UI. This aligns with the
 * established pattern in frontend-dashboard stories.
 */

import TaskPlanTimeline from './TaskPlanTimeline'

export default {
  title: 'Sessions/TaskPlanTimeline',
  component: TaskPlanTimeline,
  tags: ['autodocs'],
  parameters: {
    layout: 'padded',
  },
  argTypes: {
    tasks: { control: 'object' },
    completedTasks: { control: 'number' },
    totalTasks: { control: 'number' },
    confidence: { control: { type: 'range', min: 0, max: 1, step: 0.1 } },
    editable: { control: 'boolean' },
    onTaskReorder: { action: 'taskReordered' },
    onTaskEdit: { action: 'taskEdited' },
    onTaskApprove: { action: 'taskApproved' },
  },
}

const createTask = (id, name, status, type = 'WRITE_CODE', extras = {}) => ({
  id,
  name,
  status,
  type,
  description: `Description for ${name}`,
  ...extras,
})

const sampleTasks = [
  createTask('1', 'Analyze existing codebase', 'completed', 'ANALYZE_CODE', {
    startedAt: '2024-01-15T10:00:00Z',
    completedAt: '2024-01-15T10:15:00Z',
    duration: '15m',
  }),
  createTask('2', 'Write unit tests for auth module', 'completed', 'WRITE_TEST', {
    startedAt: '2024-01-15T10:15:00Z',
    completedAt: '2024-01-15T10:45:00Z',
    duration: '30m',
  }),
  createTask('3', 'Implement authentication service', 'running', 'WRITE_CODE', {
    startedAt: '2024-01-15T10:45:00Z',
  }),
  createTask('4', 'Run integration tests', 'pending', 'RUN_TEST'),
  createTask('5', 'Code review', 'pending', 'CODE_REVIEW'),
  createTask('6', 'Deploy to staging', 'pending', 'DEPLOYMENT'),
]

export const Default = {
  args: {
    tasks: sampleTasks,
    completedTasks: 2,
    totalTasks: 6,
    confidence: 0.85,
    editable: false,
  },
}

export const AllTaskStatuses = {
  args: {
    tasks: [
      createTask('1', 'Completed task', 'completed', 'ANALYZE_CODE', {
        startedAt: '2024-01-15T10:00:00Z',
        completedAt: '2024-01-15T10:15:00Z',
        duration: '15m',
      }),
      createTask('2', 'Running task', 'running', 'WRITE_CODE', {
        startedAt: '2024-01-15T10:15:00Z',
      }),
      createTask('3', 'Failed task', 'failed', 'RUN_TEST', {
        startedAt: '2024-01-15T10:30:00Z',
        completedAt: '2024-01-15T10:35:00Z',
        errorMessage: 'Test assertion failed: expected 200 but got 404',
      }),
      createTask('4', 'Waiting for approval', 'waiting_approval', 'DEPLOYMENT', {
        approvalReason: 'Production deployment requires manual approval',
      }),
      createTask('5', 'Paused task', 'paused', 'VERIFICATION'),
      createTask('6', 'Pending task', 'pending', 'DOCUMENTATION'),
    ],
    completedTasks: 1,
    totalTasks: 6,
    confidence: 0.72,
    editable: false,
  },
}

export const EditMode = {
  args: {
    tasks: sampleTasks,
    completedTasks: 2,
    totalTasks: 6,
    confidence: 0.85,
    editable: true,
  },
  parameters: {
    docs: {
      description: {
        story: 'In edit mode, tasks can be reordered via drag-and-drop. Pending tasks can also be edited.',
      },
    },
  },
}

export const EmptyState = {
  args: {
    tasks: [],
    completedTasks: 0,
    totalTasks: 0,
    confidence: 0,
    editable: false,
  },
}

export const HighProgress = {
  args: {
    tasks: [
      createTask('1', 'Setup environment', 'completed', 'SETUP_ENVIRONMENT'),
      createTask('2', 'Analyze code', 'completed', 'ANALYZE_CODE'),
      createTask('3', 'Write implementation', 'completed', 'WRITE_CODE'),
      createTask('4', 'Write tests', 'completed', 'WRITE_TEST'),
      createTask('5', 'Run tests', 'completed', 'RUN_TEST'),
      createTask('6', 'Final verification', 'running', 'VERIFICATION'),
    ],
    completedTasks: 5,
    totalTasks: 6,
    confidence: 0.95,
    editable: false,
  },
}

export const LowProgress = {
  args: {
    tasks: [
      createTask('1', 'Initial analysis', 'running', 'ANALYZE_CODE'),
      createTask('2', 'Design solution', 'pending', 'WRITE_CODE'),
      createTask('3', 'Implement feature', 'pending', 'WRITE_CODE'),
      createTask('4', 'Write tests', 'pending', 'WRITE_TEST'),
      createTask('5', 'Deploy', 'pending', 'DEPLOYMENT'),
    ],
    completedTasks: 0,
    totalTasks: 5,
    confidence: 0.45,
    editable: false,
  },
}

export const HighConfidence = {
  args: {
    tasks: sampleTasks.slice(0, 3),
    completedTasks: 2,
    totalTasks: 3,
    confidence: 0.98,
    editable: false,
  },
}

export const MediumConfidence = {
  args: {
    tasks: sampleTasks.slice(0, 3),
    completedTasks: 1,
    totalTasks: 3,
    confidence: 0.65,
    editable: false,
  },
}

export const LowConfidence = {
  args: {
    tasks: sampleTasks.slice(0, 3),
    completedTasks: 0,
    totalTasks: 3,
    confidence: 0.35,
    editable: false,
  },
}

export const WithFailedTask = {
  args: {
    tasks: [
      createTask('1', 'Setup project', 'completed', 'SETUP_ENVIRONMENT'),
      createTask('2', 'Run initial tests', 'failed', 'RUN_TEST', {
        startedAt: '2024-01-15T10:00:00Z',
        completedAt: '2024-01-15T10:05:00Z',
        errorMessage: 'Connection refused: Unable to connect to database at localhost:5432. Please ensure PostgreSQL is running.',
      }),
      createTask('3', 'Fix database connection', 'pending', 'WRITE_CODE'),
    ],
    completedTasks: 1,
    totalTasks: 3,
    confidence: 0.55,
    editable: false,
  },
}

export const WithApprovalRequired = {
  args: {
    tasks: [
      createTask('1', 'Build application', 'completed', 'WRITE_CODE'),
      createTask('2', 'Run security scan', 'completed', 'VERIFICATION'),
      createTask('3', 'Deploy to production', 'waiting_approval', 'DEPLOYMENT', {
        approvalReason: 'Production deployment requires CTO approval due to database schema changes',
      }),
      createTask('4', 'Post-deployment verification', 'pending', 'VERIFICATION'),
    ],
    completedTasks: 2,
    totalTasks: 4,
    confidence: 0.88,
    editable: false,
  },
}

export const AllTaskTypes = {
  args: {
    tasks: [
      createTask('1', 'Analyze existing code', 'completed', 'ANALYZE_CODE'),
      createTask('2', 'Write new feature', 'completed', 'WRITE_CODE'),
      createTask('3', 'Write unit tests', 'completed', 'WRITE_TEST'),
      createTask('4', 'Run test suite', 'running', 'RUN_TEST'),
      createTask('5', 'Code review', 'pending', 'CODE_REVIEW'),
      createTask('6', 'Setup CI/CD', 'pending', 'SETUP_ENVIRONMENT'),
      createTask('7', 'Deploy to staging', 'pending', 'DEPLOYMENT'),
      createTask('8', 'Verify deployment', 'pending', 'VERIFICATION'),
      createTask('9', 'Update documentation', 'pending', 'DOCUMENTATION'),
      createTask('10', 'Cleanup temp files', 'pending', 'CLEANUP'),
    ],
    completedTasks: 3,
    totalTasks: 10,
    confidence: 0.78,
    editable: false,
  },
}
