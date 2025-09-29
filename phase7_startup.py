#!/usr/bin/env python3
"""
Phase 7 Startup System
Initializes and coordinates all Phase 7 components
"""

import asyncio
import logging
import yaml
import os
from typing import Dict, Optional
from datetime import datetime

from ops_agent import OpsAgent
from growth_strategist import GrowthStrategist
from pm_agent import PMAgent
from hitl_approval_system import HITLApprovalSystem

try:
    from meta_agent_decision_hub import MetaAgentDecisionHub
    from monitoring_system import MonitoringSystem
    from security_manager import SecurityManager
    PHASE6_AVAILABLE = True
except ImportError:
    PHASE6_AVAILABLE = False
    
class Phase7System:
    """Phase 7 system coordinator"""
    
    def __init__(self, config_path: str = "phase7_config.yaml"):
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()
        
        self.monitoring_system = None
        self.meta_agent = None
        self.security_manager = None
        self.ops_agent = None
        self.growth_strategist = None
        self.pm_agent = None
        self.hitl_system = None
        
        self.running = False
        self.background_tasks = []
        
    def _load_config(self, config_path: str) -> Dict:
        """Load Phase 7 configuration"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                return self._expand_env_vars(config)
        except FileNotFoundError:
            self.logger.warning(f"Config file {config_path} not found, using defaults")
            return self._default_config()
            
    def _expand_env_vars(self, config: Dict) -> Dict:
        """Expand environment variables in configuration"""
        def expand_value(value):
            if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                env_var = value[2:-1]
                return os.environ.get(env_var, value)
            elif isinstance(value, dict):
                return {k: expand_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [expand_value(item) for item in value]
            return value
            
        return expand_value(config)
            
    def _default_config(self) -> Dict:
        """Default configuration if file not found"""
        return {
            'phase7': {'enabled': True, 'version': '1.0.0'},
            'ops_agent': {'enabled': True},
            'growth_strategist': {'enabled': True},
            'pm_agent': {'enabled': True},
            'hitl_approval': {'enabled': True},
            'integration': {
                'phase6_security': True,
                'meta_agent_decision_hub': True,
                'monitoring_system': True
            },
            'logging': {'level': 'INFO'}
        }
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        log_config = self.config.get('logging', {})
        level = getattr(logging, log_config.get('level', 'INFO'))
        
        logging.basicConfig(
            level=level,
            format=log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
            filename=log_config.get('file'),
            filemode='a'
        )
        
        if log_config.get('file'):
            console_handler = logging.StreamHandler()
            console_handler.setLevel(level)
            formatter = logging.Formatter(log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            console_handler.setFormatter(formatter)
            logging.getLogger().addHandler(console_handler)
        
        return logging.getLogger(__name__)
        
    async def initialize(self):
        """Initialize all Phase 7 components"""
        self.logger.info("Initializing Phase 7: Performance, Growth & Beta Introduction")
        
        if PHASE6_AVAILABLE and self.config.get('integration', {}).get('monitoring_system'):
            try:
                self.monitoring_system = MonitoringSystem("https://morningai-backend-v2.onrender.com")
                self.logger.info("Phase 6 monitoring system integrated")
            except Exception as e:
                self.logger.warning(f"Failed to initialize monitoring system: {e}")
                
        if PHASE6_AVAILABLE and self.config.get('integration', {}).get('meta_agent_decision_hub'):
            try:
                self.meta_agent = MetaAgentDecisionHub()
                self.logger.info("Phase 6 Meta-Agent decision hub integrated")
            except Exception as e:
                self.logger.warning(f"Failed to initialize Meta-Agent: {e}")
                
        if PHASE6_AVAILABLE and self.config.get('integration', {}).get('phase6_security'):
            try:
                security_config = {
                    'master_key': os.environ.get('MASTER_KEY', 'default-master-key'),
                    'secret_key': os.environ.get('SECRET_KEY', 'default-secret-key'),
                    'audit_log_file': 'phase7_security_audit.log'
                }
                self.security_manager = SecurityManager(security_config)
                self.logger.info("Phase 6 security manager integrated")
            except Exception as e:
                self.logger.warning(f"Failed to initialize security manager: {e}")
                
        if self.config.get('ops_agent', {}).get('enabled'):
            self.ops_agent = OpsAgent(monitoring_system=self.monitoring_system)
            self.logger.info("Ops_Agent initialized")
            
        if self.config.get('growth_strategist', {}).get('enabled'):
            self.growth_strategist = GrowthStrategist(
                ops_agent=self.ops_agent,
                meta_agent=self.meta_agent
            )
            self.logger.info("GrowthStrategist initialized")
            
        if self.config.get('pm_agent', {}).get('enabled'):
            self.pm_agent = PMAgent()
            self.logger.info("PM_Agent initialized")
            
        if self.config.get('hitl_approval', {}).get('enabled'):
            telegram_config = self.config.get('hitl_approval', {}).get('telegram', {})
            bot_token = telegram_config.get('bot_token') if telegram_config.get('enabled') else None
            admin_chat_id = telegram_config.get('admin_chat_id')
            
            self.hitl_system = HITLApprovalSystem(
                telegram_bot_token=bot_token,
                admin_chat_id=admin_chat_id
            )
            self.logger.info("HITL Approval System initialized")
            
    async def start(self):
        """Start Phase 7 system"""
        if not self.config.get('phase7', {}).get('enabled'):
            self.logger.warning("Phase 7 is disabled in configuration")
            return
            
        await self.initialize()
        self.running = True
        
        if self.ops_agent:
            task = asyncio.create_task(self._ops_monitoring_loop())
            self.background_tasks.append(task)
            
        if self.growth_strategist:
            task = asyncio.create_task(self._growth_analysis_loop())
            self.background_tasks.append(task)
            
        if self.pm_agent:
            task = asyncio.create_task(self._beta_management_loop())
            self.background_tasks.append(task)
            
        if self.hitl_system:
            task = asyncio.create_task(self._hitl_cleanup_loop())
            self.background_tasks.append(task)
            
        self.logger.info(f"Phase 7 system started successfully with {len(self.background_tasks)} background tasks")
        
        if self.background_tasks:
            try:
                await asyncio.gather(*self.background_tasks)
            except asyncio.CancelledError:
                self.logger.info("Background tasks cancelled")
                
    async def stop(self):
        """Stop Phase 7 system"""
        self.running = False
        
        for task in self.background_tasks:
            task.cancel()
            
        if self.background_tasks:
            await asyncio.gather(*self.background_tasks, return_exceptions=True)
            
        self.logger.info("Phase 7 system stopped")
        
    async def _ops_monitoring_loop(self):
        """Background task for operations monitoring"""
        interval = self.config.get('ops_agent', {}).get('monitoring_interval', 30)
        
        while self.running:
            try:
                capacity = await self.ops_agent.analyze_system_capacity()
                self.logger.debug(f"System capacity: load={capacity.current_load:.2f}, headroom={capacity.estimated_headroom:.2f}")
                
                if capacity.current_load > 0.9 and self.config.get('ops_agent', {}).get('auto_scaling', {}).get('enabled'):
                    await self.ops_agent.trigger_auto_scaling()
                    
            except Exception as e:
                self.logger.error(f"Ops monitoring error: {e}")
                
            await asyncio.sleep(interval)
            
    async def _growth_analysis_loop(self):
        """Background task for growth analysis"""
        interval = self.config.get('growth_strategist', {}).get('gamification_analysis_interval', 3600)
        
        while self.running:
            try:
                analysis = await self.growth_strategist.analyze_gamification_effectiveness()
                self.logger.debug(f"Gamification effectiveness: {analysis.get('current_effectiveness', {})}")
                
            except Exception as e:
                self.logger.error(f"Growth analysis error: {e}")
                
            await asyncio.sleep(interval)
            
    async def _beta_management_loop(self):
        """Background task for Beta management"""
        interval = self.config.get('pm_agent', {}).get('beta_screening', {}).get('screening_interval', 86400)
        
        while self.running:
            try:
                candidates = await self.pm_agent.screen_beta_candidates()
                if candidates:
                    await self.pm_agent.send_beta_invitations(candidates)
                    self.logger.info(f"Processed {len(candidates)} Beta candidates")
                    
                stories = await self.pm_agent.collect_and_analyze_feedback()
                if stories:
                    self.logger.info(f"Generated {len(stories)} user stories from feedback")
                    
            except Exception as e:
                self.logger.error(f"Beta management error: {e}")
                
            await asyncio.sleep(interval)
            
    async def _hitl_cleanup_loop(self):
        """Background task for HITL system cleanup"""
        interval = self.config.get('hitl_approval', {}).get('cleanup', {}).get('expired_requests_cleanup_interval', 3600)
        
        while self.running:
            try:
                expired_count = await self.hitl_system.cleanup_expired_requests()
                if expired_count > 0:
                    self.logger.info(f"Cleaned up {expired_count} expired approval requests")
                    
            except Exception as e:
                self.logger.error(f"HITL cleanup error: {e}")
                
            await asyncio.sleep(interval)
            
    def get_system_status(self) -> Dict:
        """Get comprehensive Phase 7 system status"""
        status = {
            'phase': 'Phase 7: Performance, Growth & Beta Introduction',
            'version': self.config.get('phase7', {}).get('version', '1.0.0'),
            'running': self.running,
            'initialized_at': datetime.now().isoformat(),
            'components': {},
            'integration': {},
            'background_tasks': len(self.background_tasks)
        }
        
        if self.ops_agent:
            status['components']['ops_agent'] = self.ops_agent.get_performance_report()
        if self.growth_strategist:
            status['components']['growth_strategist'] = self.growth_strategist.get_growth_report()
        if self.pm_agent:
            status['components']['pm_agent'] = self.pm_agent.get_beta_program_status()
        if self.hitl_system:
            status['components']['hitl_system'] = self.hitl_system.get_system_status()
            
        status['integration'] = {
            'phase6_available': PHASE6_AVAILABLE,
            'monitoring_system': self.monitoring_system is not None,
            'meta_agent': self.meta_agent is not None,
            'security_manager': self.security_manager is not None
        }
        
        return status

async def main():
    """Main entry point"""
    system = Phase7System()
    try:
        await system.start()
    except KeyboardInterrupt:
        print("\nShutting down Phase 7 system...")
        await system.stop()
        
if __name__ == "__main__":
    asyncio.run(main())
