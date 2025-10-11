#!/bin/bash

set -e

APP_NAME="morningai-sandbox-ops-agent"
REGION="sin"  # Singapore (closest to Taiwan)
DOCKERFILE_PATH="handoff/20250928/40_App/orchestrator/sandbox/ops_agent/Dockerfile"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_flyctl() {
    if ! command -v flyctl &> /dev/null; then
        log_error "flyctl CLI not found. Please install: https://fly.io/docs/hands-on/install-flyctl/"
        exit 1
    fi
    log_info "flyctl version: $(flyctl version)"
}

check_auth() {
    if ! flyctl auth whoami &> /dev/null; then
        log_error "Not authenticated. Please run: flyctl auth login"
        exit 1
    fi
    log_info "Authenticated as: $(flyctl auth whoami)"
}

start_sandbox() {
    log_info "🚀 Starting Ops_Agent Sandbox on Fly.io..."
    
    if flyctl apps list | grep -q "$APP_NAME"; then
        log_info "App $APP_NAME already exists. Deploying updates..."
    else
        log_info "Creating new app: $APP_NAME"
        flyctl apps create "$APP_NAME" --org personal
    fi
    
    log_info "Deploying from Dockerfile: $DOCKERFILE_PATH"
    flyctl deploy \
        --app "$APP_NAME" \
        --dockerfile "$DOCKERFILE_PATH" \
        --primary-region "$REGION" \
        --vm-size shared-cpu-1x \
        --vm-memory 256 \
        --no-public-ips \
        --wait-timeout 300
    
    log_info "Setting environment secrets..."
    flyctl secrets set \
        --app "$APP_NAME" \
        AGENT_TYPE=ops_agent \
        MCP_SERVER_URL="${MCP_SERVER_URL:-http://localhost:8080}" \
        > /dev/null
    
    log_info "✅ Sandbox deployed successfully!"
    log_info "App URL: https://$APP_NAME.fly.dev"
    log_info ""
    log_info "Next steps:"
    log_info "  - View logs: ./scripts/sandbox/flyio-deploy.sh logs"
    log_info "  - Check status: ./scripts/sandbox/flyio-deploy.sh status"
    log_info "  - Stop sandbox: ./scripts/sandbox/flyio-deploy.sh stop"
}

stop_sandbox() {
    log_info "🛑 Stopping Ops_Agent Sandbox..."
    
    if ! flyctl apps list | grep -q "$APP_NAME"; then
        log_warn "App $APP_NAME does not exist"
        return
    fi
    
    log_info "Scaling to 0 instances (cost: $0/month)..."
    flyctl scale count 0 --app "$APP_NAME" --yes
    
    log_info "✅ Sandbox stopped (scaled to 0)"
    log_info "To fully delete: flyctl apps destroy $APP_NAME --yes"
}

show_status() {
    log_info "📊 Sandbox Status"
    echo ""
    
    if ! flyctl apps list | grep -q "$APP_NAME"; then
        log_warn "App $APP_NAME does not exist"
        return
    fi
    
    flyctl status --app "$APP_NAME"
    echo ""
    
    log_info "💰 Resource Usage"
    flyctl scale show --app "$APP_NAME"
}

show_logs() {
    log_info "📜 Sandbox Logs (last 100 lines)"
    
    if ! flyctl apps list | grep -q "$APP_NAME"; then
        log_error "App $APP_NAME does not exist"
        exit 1
    fi
    
    flyctl logs --app "$APP_NAME"
}

destroy_sandbox() {
    log_warn "⚠️  This will permanently delete the sandbox!"
    read -p "Are you sure? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        log_info "Aborted"
        return
    fi
    
    log_info "Destroying app: $APP_NAME"
    flyctl apps destroy "$APP_NAME" --yes
    
    log_info "✅ Sandbox destroyed"
}

case "${1:-}" in
    start)
        check_flyctl
        check_auth
        start_sandbox
        ;;
    stop)
        check_flyctl
        check_auth
        stop_sandbox
        ;;
    status)
        check_flyctl
        check_auth
        show_status
        ;;
    logs)
        check_flyctl
        check_auth
        show_logs
        ;;
    destroy)
        check_flyctl
        check_auth
        destroy_sandbox
        ;;
    *)
        echo "Usage: $0 {start|stop|status|logs|destroy}"
        echo ""
        echo "Commands:"
        echo "  start   - Deploy/update sandbox (cost: ~$2/month)"
        echo "  stop    - Scale to 0 instances (cost: $0/month)"
        echo "  status  - Show sandbox status and resource usage"
        echo "  logs    - View sandbox logs"
        echo "  destroy - Permanently delete sandbox"
        exit 1
        ;;
esac
