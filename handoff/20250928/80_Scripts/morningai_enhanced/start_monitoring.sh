#!/bin/bash

# 服務監控系統啟動腳本

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

# 檢查 Python 環境
check_python() {
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 not found. Please install Python 3.7 or higher."
        exit 1
    fi
    
    python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    log_info "Python version: $python_version"
}

# 安裝依賴
install_dependencies() {
    log_info "Installing Python dependencies..."
    pip3 install requests statistics dataclasses typing || {
        log_error "Failed to install dependencies"
        exit 1
    }
}

# 檢查配置
check_config() {
    if [ ! -f ".env" ]; then
        log_warn ".env file not found. Creating from example..."
        python3 monitoring_config.py
        cp .env.example .env
        log_warn "Please edit .env file with your configuration before running the monitoring system."
        return 1
    fi
    
    # 載入環境變數
    if [ -f ".env" ]; then
        export $(cat .env | grep -v '^#' | xargs)
    fi
    
    # 檢查必要配置
    if [ -z "$MONITOR_BASE_URL" ]; then
        log_error "MONITOR_BASE_URL not set in .env file"
        return 1
    fi
    
    log_info "Configuration loaded from .env"
    return 0
}

# 創建必要目錄
create_directories() {
    mkdir -p logs
    mkdir -p data
    mkdir -p reports
    log_info "Created necessary directories"
}

# 啟動監控系統
start_monitoring() {
    log_info "Starting monitoring system..."
    log_info "Base URL: $MONITOR_BASE_URL"
    log_info "Check interval: ${CHECK_INTERVAL:-3600} seconds"
    
    # 在背景執行監控系統
    nohup python3 monitoring_system.py > logs/monitoring_output.log 2>&1 &
    
    # 獲取 PID
    MONITOR_PID=$!
    echo $MONITOR_PID > monitoring.pid
    
    log_info "Monitoring system started with PID: $MONITOR_PID"
    log_info "Logs are being written to logs/monitoring_output.log"
    log_info "To stop the monitoring system, run: ./stop_monitoring.sh"
}

# 檢查是否已經在運行
check_running() {
    if [ -f "monitoring.pid" ]; then
        PID=$(cat monitoring.pid)
        if ps -p $PID > /dev/null 2>&1; then
            log_warn "Monitoring system is already running with PID: $PID"
            log_warn "To stop it, run: ./stop_monitoring.sh"
            exit 1
        else
            log_warn "Found stale PID file, removing..."
            rm monitoring.pid
        fi
    fi
}

# 主函數
main() {
    log_info "=== 服務監控系統啟動 ==="
    
    check_running
    check_python
    install_dependencies
    create_directories
    
    if ! check_config; then
        log_error "Configuration check failed. Please fix the configuration and try again."
        exit 1
    fi
    
    start_monitoring
    
    log_info "=== 監控系統啟動完成 ==="
    log_info "You can check the status with: tail -f logs/monitoring_output.log"
}

# 執行主函數
main "$@"

