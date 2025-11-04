FROM python:3.11-bookworm

# Dev Agent Sandbox - Secure isolated environment for autonomous development operations
# Includes IDE tooling, LSP servers, and development utilities

# Install system dependencies for development
RUN apt-get update && apt-get install -y \
    curl \
    git \
    bash \
    jq \
    ca-certificates \
    build-essential \
    nodejs \
    npm \
    wget \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 20.x (LTS)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Install VSCode Server (code-server) for web-based IDE access
RUN curl -fsSL https://code-server.dev/install.sh | sh

# Install Python LSP Server and development tools
RUN pip install --no-cache-dir \
    python-lsp-server[all] \
    pylsp-mypy \
    pyls-isort \
    python-lsp-black \
    pylsp-rope \
    ruff-lsp

# Install TypeScript/JavaScript LSP Server
RUN npm install -g typescript typescript-language-server

# Install additional language servers
RUN npm install -g \
    vscode-langservers-extracted \
    yaml-language-server \
    dockerfile-language-server-nodejs

# Install Playwright for browser automation
RUN pip install playwright==1.40.0 && \
    playwright install --with-deps chromium

# Create non-root user for security
RUN useradd -m -u 1001 agentuser && \
    mkdir -p /workspace && \
    chown agentuser:agentuser /workspace

WORKDIR /home/agentuser

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy MCP client and sandbox scripts
COPY mcp_client.py .
COPY dev_agent_sandbox.py .

# Copy MCP integration
RUN mkdir -p /app
COPY mcp /app/mcp

# Switch to non-root user
USER agentuser

# Configure code-server
RUN mkdir -p /home/agentuser/.config/code-server && \
    echo "bind-addr: 127.0.0.1:8443" > /home/agentuser/.config/code-server/config.yaml && \
    echo "auth: none" >> /home/agentuser/.config/code-server/config.yaml && \
    echo "cert: false" >> /home/agentuser/.config/code-server/config.yaml

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Start MCP server
CMD ["python", "mcp_client.py"]
