# Dockerfile for Braintrust Trace Processor Service
# NOTE: This Dockerfile must be built from the repository root:
#   docker build -f monitoring/Dockerfile -t braintrust-processor:latest .
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY monitoring/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy common module (required for common.config.settings)
COPY common /app/common

# Copy application code
COPY monitoring/braintrust_processor.py .

# Set PYTHONPATH as fallback for sys.path bootstrap
ENV PYTHONPATH=/app

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8001/health')"

# Run the application
CMD ["uvicorn", "braintrust_processor:app", "--host", "0.0.0.0", "--port", "8001"]
