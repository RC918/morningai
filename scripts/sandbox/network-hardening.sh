#!/bin/bash

set -e

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

check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "Please run as root (sudo)"
        exit 1
    fi
}

create_sandbox_chain() {
    log_info "Creating SANDBOX_EGRESS iptables chain..."
    
    if iptables -L SANDBOX_EGRESS -n &> /dev/null; then
        log_warn "Chain SANDBOX_EGRESS already exists, flushing..."
        iptables -F SANDBOX_EGRESS
    else
        iptables -N SANDBOX_EGRESS
    fi
}

allow_dns() {
    log_info "Allowing DNS (UDP 53)..."
    iptables -A SANDBOX_EGRESS -p udp --dport 53 -j ACCEPT
}

allow_http_https() {
    log_info "Allowing HTTP/HTTPS (TCP 80/443)..."
    iptables -A SANDBOX_EGRESS -p tcp --dport 80 -j ACCEPT
    iptables -A SANDBOX_EGRESS -p tcp --dport 443 -j ACCEPT
}

allow_mcp_server() {
    log_info "Allowing MCP Server (TCP 8080)..."
    iptables -A SANDBOX_EGRESS -p tcp --dport 8080 -j ACCEPT
}

allow_established() {
    log_info "Allowing established connections..."
    iptables -A SANDBOX_EGRESS -m state --state ESTABLISHED,RELATED -j ACCEPT
}

block_all_others() {
    log_info "Blocking all other outbound traffic..."
    iptables -A SANDBOX_EGRESS -j LOG --log-prefix "SANDBOX_BLOCKED: " --log-level 4
    iptables -A SANDBOX_EGRESS -j DROP
}

apply_to_docker() {
    log_info "Applying rules to Docker bridge..."
    
    if ! iptables -C FORWARD -i docker0 -j SANDBOX_EGRESS &> /dev/null; then
        iptables -I FORWARD 1 -i docker0 -j SANDBOX_EGRESS
    else
        log_warn "Rule already applied to FORWARD chain"
    fi
}

rate_limit() {
    log_info "Setting up rate limiting (1000 conn/sec)..."
    iptables -I SANDBOX_EGRESS 1 -m hashlimit \
        --hashlimit-above 1000/sec \
        --hashlimit-burst 2000 \
        --hashlimit-mode srcip \
        --hashlimit-name sandbox_rate \
        -j DROP
}

show_rules() {
    log_info "Current SANDBOX_EGRESS rules:"
    iptables -L SANDBOX_EGRESS -n -v --line-numbers
    echo ""
    log_info "FORWARD chain rules:"
    iptables -L FORWARD -n -v --line-numbers | grep SANDBOX_EGRESS
}

remove_rules() {
    log_warn "Removing SANDBOX_EGRESS rules..."
    
    iptables -D FORWARD -i docker0 -j SANDBOX_EGRESS 2>/dev/null || true
    
    iptables -F SANDBOX_EGRESS 2>/dev/null || true
    
    iptables -X SANDBOX_EGRESS 2>/dev/null || true
    
    log_info "Rules removed"
}

persist_rules() {
    log_info "Persisting iptables rules..."
    
    if command -v iptables-save &> /dev/null; then
        iptables-save > /etc/iptables/rules.v4
        log_info "Rules saved to /etc/iptables/rules.v4"
    else
        log_warn "iptables-save not found. Rules will not persist after reboot"
        log_info "Install iptables-persistent: sudo apt-get install iptables-persistent"
    fi
}

case "${1:-}" in
    apply)
        check_root
        create_sandbox_chain
        allow_established
        allow_dns
        allow_http_https
        allow_mcp_server
        rate_limit
        block_all_others
        apply_to_docker
        show_rules
        persist_rules
        log_info "✅ Network hardening applied successfully"
        ;;
    remove)
        check_root
        remove_rules
        log_info "✅ Network hardening removed"
        ;;
    status)
        show_rules
        ;;
    *)
        echo "Usage: $0 {apply|remove|status}"
        echo ""
        echo "Commands:"
        echo "  apply  - Apply network hardening rules"
        echo "  remove - Remove network hardening rules"
        echo "  status - Show current rules"
        exit 1
        ;;
esac
