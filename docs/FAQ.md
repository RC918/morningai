# System Architecture of MorningAI

The system architecture of MorningAI is designed to be robust, scalable, and efficient, facilitating seamless integration and real-time task orchestration across various platforms. This document provides an overview of the architecture, focusing on key components and their interactions within the MorningAI platform.

## Overview

MorningAI leverages a microservices-based architecture, utilizing a range of technologies to ensure high performance, reliability, and scalability. The core components of the system include:

- **Frontend**: Developed with React, Vite, and TailwindCSS for a responsive and modern user interface.
- **Backend**: Python and Flask serve as the backbone of the server-side application, with Gunicorn for multi-worker support ensuring scalability and efficiency.
- **Database**: PostgreSQL with Row Level Security (RLS) is used for data storage, enhanced by Supabase for additional functionality including authentication and real-time subscriptions.
- **Queue System**: Redis Queue (RQ) is utilized for managing background tasks and job queues, allowing for efficient task scheduling and execution.
- **Orchestration**: LangGraph orchestrates agent workflows, enabling complex autonomous operations within the system with PostgreSQL checkpointing for state persistence.
- **AI Integration**: Multi-model routing architecture (EPIC #2594) with support for multiple LLM providers (AliCloud DashScope, SiliconFlow, OpenAI, Gemini). The routing engine dynamically selects models based on task type and risk level using a tiered approach (Tier 0-3) with cross-generation fallback for resilience. See [Routing Policy Documentation](./ROUTING_POLICY.md) for details.
- **Deployment**: Render.com is used for hosting, benefiting from its CI/CD features for streamlined deployment processes.

### Detailed Component Interaction

1. **Frontend**:
   - Users interact with the MorningAI platform through the web interface built with React.
   - TailwindCSS is employed for styling, ensuring a consistent look and feel across different devices.

```jsx
// Example: Frontend component in React
import React from 'react';

function App() {
  return (
    <div className="app-container">
      <h1>Welcome to MorningAI</h1>
      // More UI components here
    </div>
  );
}

export default App;
```

2. **Backend**:
   - Flask routes handle API requests from the frontend, interacting with the database or queue system as needed.
   - Gunicorn serves as the WSGI HTTP Server to manage multiple worker processes.

```python
# Example: Flask route in app.py
from flask import Flask

app = Flask(__name__)

@app.route('/api/data', methods=['GET'])
def get_data():
    # Logic to fetch or process data here
    return {"data": "Sample data"}

if __name__ == '__main__':
    app.run()
```

3. **Database Operations**:
   - Supabase adds real-time capabilities and easy management tools on top of PostgreSQL.

```sql
-- Example: PostgreSQL query with RLS
CREATE TABLE secure_data (
    id SERIAL PRIMARY KEY,
    info TEXT,
    user_id INTEGER REFERENCES users(id)
);
```

4. **Queue Management**:
   - Background tasks are handled via Redis Queue, allowing asynchronous processing of long-running operations.

```python
# Example: Enqueuing a job in Redis Queue
from rq import Queue
from redis import Redis
import my_background_task

redis_conn = Redis()
q = Queue(connection=redis_conn)

result = q.enqueue(my_background_task.process_data, 'http://example.com')
```

5. **Deployment**:
   - Continuous Integration and Deployment through Render.com automates the deployment process every time changes are pushed to the repository.

### Related Documentation Links

- React Documentation: [https://reactjs.org/docs/getting-started.html](https://reactjs.org/docs/getting-started.html)
- Flask Documentation: [https://flask.palletsprojects.com/en/2.0.x/](https://flask.palletsprojects.com/en/2.0.x/)
- PostgreSQL RLS: [https://www.postgresql.org/docs/current/ddl-rowsecurity.html](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- Redis Queue Documentation: [https://python-rq.org/docs/](https://python-rq.org/docs/)
- Render.com CI/CD: [https://render.com/docs/ci-cd](https://render.com/docs/ci-cd)

### Common Troubleshooting Tips

1. **Frontend Issues**: Ensure dependencies are up to date and correctly installed. Check console logs for errors during development.
2. **Backend Connectivity**: Verify that environment variables for database connections are correctly set. Test endpoints using tools like Postman.
3. **Database Permissions**: When facing RLS issues, ensure roles and policies are correctly defined in PostgreSQL.
4. **Queue Processing Delays**: Monitor Redis Queue dashboard for failed jobs or bottlenecks in task processing.
5. **Deployment Failures**: Check build logs in Render.com for specific errors related to deployment failures.

This comprehensive overview aims to equip developers with a fundamental understanding of MorningAI's system architecture, promoting efficient development and troubleshooting practices within this ecosystem.

---
Generated by MorningAI Orchestrator using GPT-4

---

**Metadata**:
- Task: What is the system architecture?
- Trace ID: `00b32bea-50b3-494c-a8a7-178118e23a74`
- Generated by: MorningAI Orchestrator using gpt-4-turbo-preview
- Provider: openai
- Repository: RC918/morningai
