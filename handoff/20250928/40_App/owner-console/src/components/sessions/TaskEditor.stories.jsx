/* eslint-disable i18next/no-literal-string */
/* NOTE: This file is exempted from strict i18n checks as Storybook stories
 * are developer documentation, not user-facing UI. This aligns with the
 * established pattern in frontend-dashboard stories.
 */

import { useState } from 'react'
import TaskEditor from './TaskEditor'

export default {
  title: 'Sessions/TaskEditor',
  component: TaskEditor,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
  },
  argTypes: {
    task: { control: 'object' },
    isOpen: { control: 'boolean' },
    isNewTask: { control: 'boolean' },
    onClose: { action: 'closed' },
    onSave: { action: 'saved' },
    onDelete: { action: 'deleted' },
  },
}

const TaskEditorWrapper = (args) => {
  const [isOpen, setIsOpen] = useState(args.isOpen)
  
  return (
    <>
      <button 
        onClick={() => setIsOpen(true)}
        className="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600"
      >
        Open Task Editor
      </button>
      <TaskEditor 
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

export const NewTask = {
  render: TaskEditorWrapper,
  args: {
    task: null,
    isOpen: true,
    isNewTask: true,
  },
  parameters: {
    docs: {
      description: {
        story: 'Create a new task with empty form fields.',
      },
    },
  },
}

export const EditExistingTask = {
  render: TaskEditorWrapper,
  args: {
    task: {
      id: '1',
      name: 'Implement user authentication',
      description: 'Add JWT-based authentication with refresh tokens and secure cookie storage.',
      type: 'WRITE_CODE',
    },
    isOpen: true,
    isNewTask: false,
  },
  parameters: {
    docs: {
      description: {
        story: 'Edit an existing task with pre-filled form fields.',
      },
    },
  },
}

export const AnalyzeCodeTask = {
  render: TaskEditorWrapper,
  args: {
    task: {
      id: '2',
      name: 'Analyze legacy codebase',
      description: 'Review existing code structure and identify refactoring opportunities.',
      type: 'ANALYZE_CODE',
    },
    isOpen: true,
    isNewTask: false,
  },
}

export const WriteTestTask = {
  render: TaskEditorWrapper,
  args: {
    task: {
      id: '3',
      name: 'Write integration tests',
      description: 'Create comprehensive integration tests for the API endpoints.',
      type: 'WRITE_TEST',
    },
    isOpen: true,
    isNewTask: false,
  },
}

export const RunTestTask = {
  render: TaskEditorWrapper,
  args: {
    task: {
      id: '4',
      name: 'Execute test suite',
      description: 'Run all unit and integration tests.',
      type: 'RUN_TEST',
    },
    isOpen: true,
    isNewTask: false,
  },
}

export const CodeReviewTask = {
  render: TaskEditorWrapper,
  args: {
    task: {
      id: '5',
      name: 'Review pull request',
      description: 'Perform code review on the authentication PR.',
      type: 'CODE_REVIEW',
    },
    isOpen: true,
    isNewTask: false,
  },
}

export const SetupEnvironmentTask = {
  render: TaskEditorWrapper,
  args: {
    task: {
      id: '6',
      name: 'Configure development environment',
      description: 'Set up Docker containers and environment variables.',
      type: 'SETUP_ENVIRONMENT',
    },
    isOpen: true,
    isNewTask: false,
  },
}

export const DeploymentTask = {
  render: TaskEditorWrapper,
  args: {
    task: {
      id: '7',
      name: 'Deploy to production',
      description: 'Deploy the application to production servers.',
      type: 'DEPLOYMENT',
    },
    isOpen: true,
    isNewTask: false,
  },
}

export const VerificationTask = {
  render: TaskEditorWrapper,
  args: {
    task: {
      id: '8',
      name: 'Verify deployment',
      description: 'Run smoke tests and verify the deployment is successful.',
      type: 'VERIFICATION',
    },
    isOpen: true,
    isNewTask: false,
  },
}

export const DocumentationTask = {
  render: TaskEditorWrapper,
  args: {
    task: {
      id: '9',
      name: 'Update API documentation',
      description: 'Document new endpoints and update OpenAPI spec.',
      type: 'DOCUMENTATION',
    },
    isOpen: true,
    isNewTask: false,
  },
}

export const CleanupTask = {
  render: TaskEditorWrapper,
  args: {
    task: {
      id: '10',
      name: 'Clean up temporary files',
      description: 'Remove build artifacts and temporary files.',
      type: 'CLEANUP',
    },
    isOpen: true,
    isNewTask: false,
  },
}

export const LongTaskName = {
  render: TaskEditorWrapper,
  args: {
    task: {
      id: '11',
      name: 'This is a very long task name that approaches the maximum character limit to test how the form handles long text input and whether validation works correctly',
      description: 'Testing long task names.',
      type: 'WRITE_CODE',
    },
    isOpen: true,
    isNewTask: false,
  },
  parameters: {
    docs: {
      description: {
        story: 'Task with a long name approaching the 200 character limit.',
      },
    },
  },
}

export const WithDeleteOption = {
  render: TaskEditorWrapper,
  args: {
    task: {
      id: '12',
      name: 'Task to be deleted',
      description: 'This task can be deleted.',
      type: 'WRITE_CODE',
    },
    isOpen: true,
    isNewTask: false,
    onDelete: (taskId) => console.log('Delete task:', taskId),
  },
  parameters: {
    docs: {
      description: {
        story: 'Edit mode with delete option available.',
      },
    },
  },
}

export const Closed = {
  render: TaskEditorWrapper,
  args: {
    task: null,
    isOpen: false,
    isNewTask: true,
  },
  parameters: {
    docs: {
      description: {
        story: 'Dialog in closed state. Click the button to open.',
      },
    },
  },
}
