# Orchestrator API Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY orchestrator/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy orchestrator code
COPY orchestrator/ /app/

# Install orchestrator package
RUN pip install --no-cache-dir -e /app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5)"

# Run the application
CMD ["uvicorn", "orchestrator.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
