FROM python:3.11-bookworm

# Ops Agent Sandbox - Secure isolated environment for autonomous agent operations
RUN apt-get update && apt-get install -y \
    curl \
    git \
    bash \
    jq \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN pip install playwright==1.40.0 && \
    playwright install --with-deps chromium

RUN useradd -m -u 1001 agentuser && \
    mkdir -p /workspace && \
    chown agentuser:agentuser /workspace

WORKDIR /home/agentuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY mcp_client.py .
COPY ops_agent_sandbox.py .

RUN mkdir -p /app
COPY mcp /app/mcp

USER agentuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

CMD ["python", "mcp_client.py"]
