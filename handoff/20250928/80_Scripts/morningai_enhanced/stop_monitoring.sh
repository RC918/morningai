#!/bin/bash

# 服務監控系統停止腳本

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日誌函數
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 停止監控系統
stop_monitoring() {
    if [ ! -f "monitoring.pid" ]; then
        log_warn "No PID file found. Monitoring system may not be running."
        return 1
    fi
    
    PID=$(cat monitoring.pid)
    
    if ! ps -p $PID > /dev/null 2>&1; then
        log_warn "Process with PID $PID is not running."
        rm monitoring.pid
        return 1
    fi
    
    log_info "Stopping monitoring system (PID: $PID)..."
    
    # 嘗試優雅停止
    kill -TERM $PID
    
    # 等待最多 10 秒
    for i in {1..10}; do
        if ! ps -p $PID > /dev/null 2>&1; then
            log_info "Monitoring system stopped gracefully."
            rm monitoring.pid
            return 0
        fi
        sleep 1
    done
    
    # 強制停止
    log_warn "Graceful shutdown failed, forcing stop..."
    kill -KILL $PID
    
    # 再次檢查
    sleep 2
    if ! ps -p $PID > /dev/null 2>&1; then
        log_info "Monitoring system stopped forcefully."
        rm monitoring.pid
        return 0
    else
        log_error "Failed to stop monitoring system."
        return 1
    fi
}

# 檢查狀態
check_status() {
    if [ -f "monitoring.pid" ]; then
        PID=$(cat monitoring.pid)
        if ps -p $PID > /dev/null 2>&1; then
            log_info "Monitoring system is running with PID: $PID"
            
            # 顯示進程資訊
            echo "Process info:"
            ps -p $PID -o pid,ppid,cmd,etime,pcpu,pmem
            
            # 顯示最近的日誌
            if [ -f "logs/monitoring_output.log" ]; then
                echo ""
                echo "Recent logs (last 10 lines):"
                tail -n 10 logs/monitoring_output.log
            fi
        else
            log_warn "PID file exists but process is not running."
            rm monitoring.pid
        fi
    else
        log_info "Monitoring system is not running."
    fi
}

# 主函數
main() {
    case "${1:-stop}" in
        "stop")
            log_info "=== 停止服務監控系統 ==="
            if stop_monitoring; then
                log_info "=== 監控系統已停止 ==="
            else
                log_error "=== 停止監控系統失敗 ==="
                exit 1
            fi
            ;;
        "status")
            log_info "=== 檢查監控系統狀態 ==="
            check_status
            ;;
        "restart")
            log_info "=== 重啟監控系統 ==="
            stop_monitoring
            sleep 2
            ./start_monitoring.sh
            ;;
        *)
            echo "Usage: $0 {stop|status|restart}"
            echo "  stop    - Stop the monitoring system"
            echo "  status  - Check monitoring system status"
            echo "  restart - Restart the monitoring system"
            exit 1
            ;;
    esac
}

# 執行主函數
main "$@"

