#!/usr/bin/env python3
"""
Phase 6 啟動腳本
初始化所有安全和監控系統
"""

import asyncio
import logging
import os
import sys
import time
from datetime import datetime
from typing import Dict, Any
import subprocess
import threading

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('phase6_startup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class Phase6SystemManager:
    """Phase 6 系統管理器"""
    
    def __init__(self):
        self.services = {}
        self.startup_time = datetime.now()
        
    def start_monitoring_system(self):
        """啟動監控系統"""
        try:
            logger.info("Starting monitoring system...")
            
            os.environ['MONITOR_BASE_URL'] = 'https://morningai-backend-v2.onrender.com'
            os.environ['SLACK_WEBHOOK_URL'] = os.environ.get('SLACK_WEBHOOK_URL', '')
            
            def run_monitoring():
                try:
                    from monitoring_system import main as monitoring_main
                    monitoring_main()
                except Exception as e:
                    logger.error(f"Monitoring system error: {e}")
            
            monitoring_thread = threading.Thread(target=run_monitoring, daemon=True)
            monitoring_thread.start()
            
            self.services['monitoring'] = {
                'status': 'running',
                'thread': monitoring_thread,
                'started_at': datetime.now()
            }
            
            logger.info("✅ Monitoring system started successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start monitoring system: {e}")
            return False
    
    def start_security_manager(self):
        """啟動安全管理器"""
        try:
            logger.info("Starting security manager...")
            
            from security_manager import SecurityManager
            
            security_config = {
                'master_key': os.environ.get('MASTER_KEY', 'default-master-key'),
                'secret_key': os.environ.get('SECRET_KEY', 'default-secret-key'),
                'audit_log_file': 'security_audit.log'
            }
            
            security_manager = SecurityManager(security_config)
            
            self.services['security'] = {
                'status': 'running',
                'manager': security_manager,
                'started_at': datetime.now()
            }
            
            logger.info("✅ Security manager started successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start security manager: {e}")
            return False
    
    async def start_meta_agent_hub(self):
        """啟動 Meta-Agent 決策中樞"""
        try:
            logger.info("Starting Meta-Agent Decision Hub...")
            
            from meta_agent_decision_hub import MetaAgentDecisionHub
            
            redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')
            
            hub = MetaAgentDecisionHub(redis_url=redis_url)
            
            def run_meta_agent():
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    async def monitor_and_decide():
                        while True:
                            try:
                                # 檢查系統健康狀況
                                status = hub.get_system_status()
                                logger.info(f"Meta-Agent status: {status}")
                                
                                await hub.process_trigger_event("routine_health_check")
                                
                                await asyncio.sleep(1800)
                                
                            except Exception as e:
                                logger.error(f"Meta-Agent monitoring error: {e}")
                                await asyncio.sleep(60)
                    
                    loop.run_until_complete(monitor_and_decide())
                    
                except Exception as e:
                    logger.error(f"Meta-Agent hub error: {e}")
            
            meta_agent_thread = threading.Thread(target=run_meta_agent, daemon=True)
            meta_agent_thread.start()
            
            self.services['meta_agent'] = {
                'status': 'running',
                'hub': hub,
                'thread': meta_agent_thread,
                'started_at': datetime.now()
            }
            
            logger.info("✅ Meta-Agent Decision Hub started successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start Meta-Agent Decision Hub: {e}")
            return False
    
    def start_governance_module(self):
        """啟動 AI 治理模組"""
        try:
            logger.info("Starting AI Governance Module...")
            
            from ai_governance_module import AIGovernanceModule
            
            governance_module = AIGovernanceModule()
            
            def run_governance():
                try:
                    governance_module.run(host='0.0.0.0', port=5002, debug=False)
                except Exception as e:
                    logger.error(f"Governance module error: {e}")
            
            governance_thread = threading.Thread(target=run_governance, daemon=True)
            governance_thread.start()
            
            self.services['governance'] = {
                'status': 'running',
                'module': governance_module,
                'thread': governance_thread,
                'started_at': datetime.now(),
                'url': 'http://localhost:5002/governance/dashboard'
            }
            
            logger.info("✅ AI Governance Module started successfully")
            logger.info("🌐 Governance Dashboard: http://localhost:5002/governance/dashboard")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start AI Governance Module: {e}")
            return False
    
    def verify_flask_backend(self):
        """驗證 Flask 後端狀態"""
        try:
            logger.info("Verifying Flask backend...")
            
            import requests
            response = requests.get('https://morningai-backend-v2.onrender.com/health', timeout=10)
            
            if response.status_code == 200:
                logger.info("✅ Flask backend is healthy")
                return True
            else:
                logger.warning(f"⚠️ Flask backend returned status {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to verify Flask backend: {e}")
            return False
    
    def verify_cloud_services(self):
        """驗證雲端服務連線"""
        try:
            logger.info("Verifying cloud services...")
            
            result = subprocess.run([
                sys.executable, 'test_cloud_connections.py'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                logger.info("✅ Cloud services verification completed")
                return True
            else:
                logger.warning(f"⚠️ Cloud services verification issues: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to verify cloud services: {e}")
            return False
    
    def get_system_status(self) -> Dict[str, Any]:
        """獲取系統狀態"""
        status = {
            'startup_time': self.startup_time.isoformat(),
            'uptime_seconds': (datetime.now() - self.startup_time).total_seconds(),
            'services': {}
        }
        
        for service_name, service_info in self.services.items():
            status['services'][service_name] = {
                'status': service_info['status'],
                'started_at': service_info['started_at'].isoformat(),
                'uptime_seconds': (datetime.now() - service_info['started_at']).total_seconds()
            }
            
            if 'url' in service_info:
                status['services'][service_name]['url'] = service_info['url']
        
        return status
    
    async def start_all_services(self):
        """啟動所有服務"""
        logger.info("🚀 Starting Phase 6: Security and Audit Enhancement")
        logger.info("=" * 60)
        
        success_count = 0
        total_services = 5
        
        if self.verify_flask_backend():
            success_count += 1
        
        if self.verify_cloud_services():
            success_count += 1
        
        if self.start_security_manager():
            success_count += 1
        
        if self.start_monitoring_system():
            success_count += 1
        
        if await self.start_meta_agent_hub():
            success_count += 1
        
        if self.start_governance_module():
            success_count += 1
            total_services += 1
        
        logger.info("=" * 60)
        logger.info(f"🎯 Phase 6 Startup Complete: {success_count}/{total_services} services started")
        
        if success_count == total_services:
            logger.info("🎉 All services started successfully!")
        else:
            logger.warning(f"⚠️ {total_services - success_count} services failed to start")
        
        status = self.get_system_status()
        logger.info("📊 System Status:")
        for service_name, service_status in status['services'].items():
            logger.info(f"  - {service_name}: {service_status['status']}")
            if 'url' in service_status:
                logger.info(f"    URL: {service_status['url']}")
        
        return success_count == total_services

async def main():
    """主函數"""
    try:
        manager = Phase6SystemManager()
        success = await manager.start_all_services()
        
        if success:
            logger.info("🎊 Phase 6: Security and Audit Enhancement is now active!")
            logger.info("🔗 Access points:")
            logger.info("  - Flask Backend: https://morningai-backend-v2.onrender.com/health")
            logger.info("  - Governance Dashboard: http://localhost:5002/governance/dashboard")
            logger.info("  - Monitoring Logs: monitoring.log")
            logger.info("  - Security Audit Logs: security_audit.log")
            
            logger.info("🔄 System is running. Press Ctrl+C to stop.")
            try:
                while True:
                    await asyncio.sleep(60)
                    status = manager.get_system_status()
                    logger.info(f"⏰ System uptime: {status['uptime_seconds']:.0f} seconds")
            except KeyboardInterrupt:
                logger.info("🛑 Shutdown requested by user")
        else:
            logger.error("❌ Phase 6 startup failed")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"💥 Critical error during startup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
