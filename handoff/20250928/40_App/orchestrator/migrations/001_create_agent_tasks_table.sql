
CREATE TABLE IF NOT EXISTS agent_tasks (
  task_id uuid PRIMARY KEY,
  trace_id uuid NOT NULL,
  job_id text,
  question text,
  status text CHECK (status IN ('queued', 'running', 'done', 'error')),
  pr_url text,
  error_msg text,
  created_at timestamptz NOT NULL DEFAULT now(),
  started_at timestamptz,
  finished_at timestamptz,
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_agent_tasks_created_at ON agent_tasks (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_tasks_status ON agent_tasks (status);
CREATE INDEX IF NOT EXISTS idx_agent_tasks_trace_id ON agent_tasks (trace_id);

COMMENT ON TABLE agent_tasks IS 'Agent task execution audit trail - tracks FAQ generation tasks from enqueue to completion';
COMMENT ON COLUMN agent_tasks.task_id IS 'Unique task identifier (UUID)';
COMMENT ON COLUMN agent_tasks.trace_id IS 'Trace identifier for distributed tracing (typically same as task_id)';
COMMENT ON COLUMN agent_tasks.job_id IS 'RQ job identifier';
COMMENT ON COLUMN agent_tasks.question IS 'FAQ question text submitted by user';
COMMENT ON COLUMN agent_tasks.status IS 'Task status: queued (initial) -> running (worker started) -> done/error (terminal states)';
COMMENT ON COLUMN agent_tasks.pr_url IS 'GitHub Pull Request URL (populated on success)';
COMMENT ON COLUMN agent_tasks.error_msg IS 'Error message (populated on failure, max 500 chars)';
COMMENT ON COLUMN agent_tasks.created_at IS 'Task creation timestamp (when API enqueued)';
COMMENT ON COLUMN agent_tasks.started_at IS 'Task start timestamp (when worker began processing)';
COMMENT ON COLUMN agent_tasks.finished_at IS 'Task completion timestamp (done or error)';
COMMENT ON COLUMN agent_tasks.updated_at IS 'Last update timestamp (modified on every state transition)';
