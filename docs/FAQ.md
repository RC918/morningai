# MorningAI System Architecture

MorningAI's system architecture is designed to offer a scalable, efficient, and flexible platform for autonomous agent system code generation, FAQ generation, documentation management, and multi-platform integration. It leverages a modern tech stack and follows best practices for cloud-native applications. Below is an overview of the key components and how they interact within the MorningAI ecosystem.

## Overview

The MorningAI platform is built on a microservices architecture, utilizing various technologies such as React, Python with Flask, PostgreSQL via Supabase, Redis Queue (RQ), and OpenAI's GPT-4 for AI-driven features. This architecture enables MorningAI to handle complex workflows, manage large volumes of data efficiently, and integrate seamlessly with multiple platforms like Telegram, LINE, and Messenger.

### Frontend

- **Technology**: React + Vite + TailwindCSS
- **Path**: `/frontend`
- **Description**: The frontend is developed using React for building the user interface, Vite as the build tool for faster development and optimized production builds, and TailwindCSS for styling. The user interface is designed to be responsive and intuitive across devices.

### Backend

- **Technology**: Python + Flask + Gunicorn
- **Path**: `/backend`
- **Description**: The backend API is built with Flask, a lightweight WSGI web application framework in Python, providing the necessary endpoints for the frontend. Gunicorn is used as the WSGI HTTP Server to manage multiple worker processes for handling requests concurrently.

### Database

- **Technology**: PostgreSQL (Supabase) with Row Level Security
- **Path**: Not applicable (configured on Supabase)
- **Description**: PostgreSQL serves as the primary database, hosted on Supabase which adds additional features such as real-time subscriptions and row-level security to enhance data access control. Supabase simplifies database management and accelerates development.

### Queue System

- **Technology**: Redis Queue (RQ)
- **Path**: `/queue`
- **Description**: RQ is utilized for managing background tasks such as long-running computations or external API calls. It allows the application to remain responsive by offloading tasks that would otherwise block the main execution flow.

### Orchestration

- **Technology**: LangGraph
- **Path**: `/orchestration`
- **Description**: LangGraph orchestrates complex workflows among autonomous agents within the platform. It ensures tasks are executed in a coordinated manner based on predefined logic.

### AI Component

- **Technology**: OpenAI GPT-4
- **Integration Point**: `/backend/services/gpt_service.py`
- **Description**: GPT-4 powers the autonomous agent system for code generation and FAQ content creation. It enables sophisticated natural language understanding and generation capabilities within MorningAI.

### Deployment

- **Platform**: Render.com
- **CI/CD Integration**: Configured via Render dashboard
- **Description**: Render.com hosts both frontend and backend components of MorningAI. Continuous Integration/Continuous Deployment (CI/CD) pipelines are set up through Render's dashboard to automate deployments from the repository.

## Code Example: Integrating RQ with Flask

Here's an example of how you might set up Redis Queue with Flask:

```python
from redis import Redis
from rq import Queue
from flask import Flask

app = Flask(__name__)
redis_conn = Redis()
q = Queue(connection=redis_conn)

@app.route('/start-task')
def start_task():
    result = q.enqueue('my_background_task')
    return f"Task {result.id} added to queue at {result.enqueued_at}"

if __name__ == '__main__':
    app.run()
```

Replace `'my_background_task'` with your actual background task function name.

## Related Documentation Links

For more detailed information on each component:
- React: [https://reactjs.org/docs/getting-started.html](https://reactjs.org/docs/getting-started.html)
- Flask: [https://flask.palletsprojects.com/en/2.0.x/](https://flask.palletsprojects.com/en/2.0.x/)
- PostgreSQL & Supabase: [https://supabase.io/docs](https://supabase.io/docs)
- Redis Queue: [https://python-rq.org/docs/](https://python-rq.org/docs/)
- OpenAI GPT: [https://beta.openai.com/docs/](https://beta.openai.com/docs/)

## Common Troubleshooting Tips

**Issue:** Backend service fails to connect to PostgreSQL.
**Solution:** Verify that database credentials in your `.env` file match those provided by Supabase. Ensure that your IP address has access permissions in Supabase's settings if required.

**Issue:** Tasks not being processed by Redis Queue workers.
**Solution:** Check that RQ workers are running by executing `rq worker`. Ensure Redis server is accessible and that there are no network connectivity issues between your application server and Redis.

For further assistance or if you encounter specific problems not covered here, please refer to our detailed documentation or reach out through our support channels.

---
Generated by MorningAI Orchestrator using GPT-4

---

**Metadata**:
- Task: What is the system architecture?
- Trace ID: `cbba6c86-c72e-40d3-a9d2-c84f91195bad`
- Generated by: MorningAI Orchestrator using gpt-4-turbo-preview
- Repository: RC918/morningai
