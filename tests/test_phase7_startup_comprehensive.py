"""
Comprehensive tests for Phase 7 Startup System

Tests all Phase 7 initialization, configuration, and lifecycle management:
- Configuration loading and environment variable expansion
- Component initialization (Ops, Growth, PM, HITL)
- Phase 6 integration (Monitoring, Meta-Agent, Security)
- Background task management
- System lifecycle (start/stop)
- Environment validation
"""
import pytest
import asyncio
import yaml
import os
from unittest.mock import Mock, patch, AsyncMock, MagicMock, mock_open
from datetime import datetime
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from phase7_startup import Phase7System, main


@pytest.fixture
def mock_config():
    """Mock Phase 7 configuration"""
    return {
        'phase7': {'enabled': True, 'version': '1.0.0'},
        'ops_agent': {
            'enabled': True,
            'monitoring_interval': 30,
            'auto_scaling': {'enabled': True}
        },
        'growth_strategist': {
            'enabled': True,
            'gamification_analysis_interval': 3600
        },
        'pm_agent': {
            'enabled': True,
            'beta_screening': {'screening_interval': 86400}
        },
        'hitl_approval': {
            'enabled': True,
            'telegram': {
                'enabled': True,
                'bot_token': 'test-token',
                'admin_chat_id': '12345'
            },
            'cleanup': {'expired_requests_cleanup_interval': 3600}
        },
        'integration': {
            'phase6_security': True,
            'meta_agent_decision_hub': True,
            'monitoring_system': True
        },
        'logging': {'level': 'INFO'}
    }


@pytest.fixture
def mock_agents():
    """Mock all agent classes"""
    with patch('phase7_startup.OpsAgent') as ops, \
         patch('phase7_startup.GrowthStrategist') as growth, \
         patch('phase7_startup.PMAgent') as pm, \
         patch('phase7_startup.HITLApprovalSystem') as hitl:
        
        ops_instance = Mock()
        ops_instance.analyze_system_capacity = AsyncMock(return_value=Mock(current_load=0.5, estimated_headroom=0.5))
        ops_instance.trigger_auto_scaling = AsyncMock()
        ops_instance.get_performance_report = Mock(return_value={'status': 'ok'})
        ops.return_value = ops_instance
        
        growth_instance = Mock()
        growth_instance.analyze_gamification_effectiveness = AsyncMock(return_value={'current_effectiveness': 0.8})
        growth_instance.get_growth_report = Mock(return_value={'growth_rate': 0.15})
        growth.return_value = growth_instance
        
        pm_instance = Mock()
        pm_instance.screen_beta_candidates = AsyncMock(return_value=[])
        pm_instance.send_beta_invitations = AsyncMock()
        pm_instance.collect_and_analyze_feedback = AsyncMock(return_value=[])
        pm_instance.get_beta_program_status = Mock(return_value={'active_users': 10})
        pm.return_value = pm_instance
        
        hitl_instance = Mock()
        hitl_instance.cleanup_expired_requests = AsyncMock(return_value=0)
        hitl_instance.get_system_status = Mock(return_value={'pending_requests': 0})
        hitl.return_value = hitl_instance
        
        yield {
            'ops': ops,
            'growth': growth,
            'pm': pm,
            'hitl': hitl
        }


class TestConfigurationLoading:
    """Test configuration loading and parsing"""
    
    def test_load_config_from_file(self, mock_config):
        """Test loading configuration from YAML file"""
        yaml_content = yaml.dump(mock_config)
        
        with patch('builtins.open', mock_open(read_data=yaml_content)):
            system = Phase7System('test_config.yaml')
            
            assert system.config['phase7']['enabled'] is True
            assert system.config['phase7']['version'] == '1.0.0'
            assert system.config['ops_agent']['enabled'] is True
    
    def test_load_config_file_not_found(self):
        """Test fallback to default config when file not found"""
        with patch('builtins.open', side_effect=FileNotFoundError()):
            system = Phase7System('nonexistent.yaml')
            
            assert system.config['phase7']['enabled'] is True
            assert 'ops_agent' in system.config
            assert 'growth_strategist' in system.config
    
    def test_expand_environment_variables(self, mock_config):
        """Test environment variable expansion in config"""
        mock_config['ops_agent']['api_key'] = '${TEST_API_KEY}'
        mock_config['hitl_approval']['telegram']['bot_token'] = '${TELEGRAM_TOKEN}'
        
        yaml_content = yaml.dump(mock_config)
        
        with patch.dict(os.environ, {'TEST_API_KEY': 'secret123', 'TELEGRAM_TOKEN': 'bot456'}), \
             patch('builtins.open', mock_open(read_data=yaml_content)):
            system = Phase7System('test_config.yaml')
            
            assert system.config['ops_agent']['api_key'] == 'secret123'
            assert system.config['hitl_approval']['telegram']['bot_token'] == 'bot456'
    
    def test_expand_env_vars_missing(self, mock_config):
        """Test environment variable expansion with missing vars"""
        mock_config['test_key'] = '${MISSING_VAR}'
        
        yaml_content = yaml.dump(mock_config)
        
        with patch('builtins.open', mock_open(read_data=yaml_content)):
            system = Phase7System('test_config.yaml')
            
            assert system.config['test_key'] == '${MISSING_VAR}'
    
    def test_expand_nested_env_vars(self, mock_config):
        """Test environment variable expansion in nested structures"""
        mock_config['nested'] = {
            'level1': {
                'level2': '${NESTED_VAR}'
            },
            'list': ['${LIST_VAR1}', '${LIST_VAR2}']
        }
        
        yaml_content = yaml.dump(mock_config)
        
        with patch.dict(os.environ, {'NESTED_VAR': 'nested_value', 'LIST_VAR1': 'item1', 'LIST_VAR2': 'item2'}), \
             patch('builtins.open', mock_open(read_data=yaml_content)):
            system = Phase7System('test_config.yaml')
            
            assert system.config['nested']['level1']['level2'] == 'nested_value'
            assert system.config['nested']['list'] == ['item1', 'item2']
    
    def test_default_config_structure(self):
        """Test default configuration structure"""
        with patch('builtins.open', side_effect=FileNotFoundError()):
            system = Phase7System()
            
            assert 'phase7' in system.config
            assert 'ops_agent' in system.config
            assert 'growth_strategist' in system.config
            assert 'pm_agent' in system.config
            assert 'hitl_approval' in system.config
            assert 'integration' in system.config
            assert 'logging' in system.config


class TestLoggingSetup:
    """Test logging configuration"""
    
    def test_setup_logging_default(self, mock_config):
        """Test default logging setup"""
        yaml_content = yaml.dump(mock_config)
        
        with patch('builtins.open', mock_open(read_data=yaml_content)):
            system = Phase7System('test_config.yaml')
            
            assert system.logger is not None
            assert system.logger.name == 'phase7_startup'
    
    def test_setup_logging_with_file(self, mock_config):
        """Test logging setup with file output"""
        mock_config['logging']['file'] = 'phase7.log'
        yaml_content = yaml.dump(mock_config)
        
        with patch('builtins.open', mock_open(read_data=yaml_content)):
            system = Phase7System('test_config.yaml')
            
            assert system.logger is not None
    
    def test_setup_logging_custom_level(self, mock_config):
        """Test logging setup with custom level"""
        mock_config['logging']['level'] = 'DEBUG'
        yaml_content = yaml.dump(mock_config)
        
        with patch('builtins.open', mock_open(read_data=yaml_content)):
            system = Phase7System('test_config.yaml')
            
            assert system.logger is not None


class TestComponentInitialization:
    """Test component initialization"""
    
    @pytest.mark.asyncio
    async def test_initialize_ops_agent(self, mock_config, mock_agents):
        """Test Ops Agent initialization"""
        yaml_content = yaml.dump(mock_config)
        
        with patch('builtins.open', mock_open(read_data=yaml_content)), \
             patch('phase7_startup.PHASE6_AVAILABLE', False):
            system = Phase7System('test_config.yaml')
            await system.initialize()
            
            assert system.ops_agent is not None
            mock_agents['ops'].assert_called_once()
    
    @pytest.mark.asyncio
    async def test_initialize_growth_strategist(self, mock_config, mock_agents):
        """Test Growth Strategist initialization"""
        yaml_content = yaml.dump(mock_config)
        
        with patch('builtins.open', mock_open(read_data=yaml_content)), \
             patch('phase7_startup.PHASE6_AVAILABLE', False):
            system = Phase7System('test_config.yaml')
            await system.initialize()
            
            assert system.growth_strategist is not None
            mock_agents['growth'].assert_called_once()
    
    @pytest.mark.asyncio
    async def test_initialize_pm_agent(self, mock_config, mock_agents):
        """Test PM Agent initialization"""
        yaml_content = yaml.dump(mock_config)
        
        with patch('builtins.open', mock_open(read_data=yaml_content)), \
             patch('phase7_startup.PHASE6_AVAILABLE', False):
            system = Phase7System('test_config.yaml')
            await system.initialize()
            
            assert system.pm_agent is not None
            mock_agents['pm'].assert_called_once()
    
    @pytest.mark.asyncio
    async def test_initialize_hitl_system(self, mock_config, mock_agents):
        """Test HITL system initialization"""
        yaml_content = yaml.dump(mock_config)
        
        with patch('builtins.open', mock_open(read_data=yaml_content)), \
             patch('phase7_startup.PHASE6_AVAILABLE', False):
            system = Phase7System('test_config.yaml')
            await system.initialize()
            
            assert system.hitl_system is not None
            mock_agents['hitl'].assert_called_once_with(
                telegram_bot_token='test-token',
                admin_chat_id='12345'
            )
    
    @pytest.mark.asyncio
    async def test_initialize_disabled_components(self, mock_config, mock_agents):
        """Test initialization with disabled components"""
        mock_config['ops_agent']['enabled'] = False
        mock_config['growth_strategist']['enabled'] = False
        yaml_content = yaml.dump(mock_config)
        
        with patch('builtins.open', mock_open(read_data=yaml_content)), \
             patch('phase7_startup.PHASE6_AVAILABLE', False):
            system = Phase7System('test_config.yaml')
            await system.initialize()
            
            assert system.ops_agent is None
            assert system.growth_strategist is None
            assert system.pm_agent is not None  # Still enabled


class TestPhase6Integration:
    """Test Phase 6 component integration"""
    
    @pytest.mark.asyncio
    async def test_integrate_monitoring_system(self, mock_config):
        """Test monitoring system integration"""
        yaml_content = yaml.dump(mock_config)
        
        with patch('builtins.open', mock_open(read_data=yaml_content)), \
             patch('phase7_startup.PHASE6_AVAILABLE', True), \
             patch('phase7_startup.MonitoringSystem') as mock_monitoring, \
             patch('phase7_startup.OpsAgent'), \
             patch('phase7_startup.GrowthStrategist'), \
             patch('phase7_startup.PMAgent'), \
             patch('phase7_startup.HITLApprovalSystem'):
            
            system = Phase7System('test_config.yaml')
            await system.initialize()
            
            assert system.monitoring_system is not None
            mock_monitoring.assert_called_once_with("https://morningai-backend-v2.onrender.com")
    
    @pytest.mark.asyncio
    async def test_integrate_meta_agent(self, mock_config):
        """Test Meta-Agent integration"""
        yaml_content = yaml.dump(mock_config)
        
        with patch('builtins.open', mock_open(read_data=yaml_content)), \
             patch('phase7_startup.PHASE6_AVAILABLE', True), \
             patch('phase7_startup.MetaAgentDecisionHub') as mock_meta, \
             patch('phase7_startup.OpsAgent'), \
             patch('phase7_startup.GrowthStrategist'), \
             patch('phase7_startup.PMAgent'), \
             patch('phase7_startup.HITLApprovalSystem'):
            
            system = Phase7System('test_config.yaml')
            await system.initialize()
            
            assert system.meta_agent is not None
            mock_meta.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_integrate_security_manager(self, mock_config):
        """Test Security Manager integration"""
        yaml_content = yaml.dump(mock_config)
        
        with patch('builtins.open', mock_open(read_data=yaml_content)), \
             patch.dict(os.environ, {'MASTER_KEY': 'test-master', 'SECRET_KEY': 'test-secret'}), \
             patch('phase7_startup.PHASE6_AVAILABLE', True), \
             patch('phase7_startup.SecurityManager') as mock_security, \
             patch('phase7_startup.OpsAgent'), \
             patch('phase7_startup.GrowthStrategist'), \
             patch('phase7_startup.PMAgent'), \
             patch('phase7_startup.HITLApprovalSystem'):
            
            system = Phase7System('test_config.yaml')
            await system.initialize()
            
            assert system.security_manager is not None
            mock_security.assert_called_once()
            call_args = mock_security.call_args[0][0]
            assert call_args['master_key'] == 'test-master'
            assert call_args['secret_key'] == 'test-secret'
    
    @pytest.mark.asyncio
    async def test_phase6_unavailable(self, mock_config, mock_agents):
        """Test graceful handling when Phase 6 is unavailable"""
        yaml_content = yaml.dump(mock_config)
        
        with patch('builtins.open', mock_open(read_data=yaml_content)), \
             patch('phase7_startup.PHASE6_AVAILABLE', False):
            system = Phase7System('test_config.yaml')
            await system.initialize()
            
            assert system.monitoring_system is None
            assert system.meta_agent is None
            assert system.security_manager is None
            assert system.ops_agent is not None


class TestSystemLifecycle:
    """Test system start/stop lifecycle"""
    
    @pytest.mark.asyncio
    async def test_start_system(self, mock_config, mock_agents):
        """Test system startup"""
        yaml_content = yaml.dump(mock_config)
        
        with patch('builtins.open', mock_open(read_data=yaml_content)), \
             patch('phase7_startup.PHASE6_AVAILABLE', False):
            system = Phase7System('test_config.yaml')
            
            start_task = asyncio.create_task(system.start())
            await asyncio.sleep(0.1)  # Let it initialize
            
            assert system.running is True
            assert len(system.background_tasks) == 4  # ops, growth, pm, hitl
            
            await system.stop()
            await start_task
    
    @pytest.mark.asyncio
    async def test_start_disabled_system(self, mock_config, mock_agents):
        """Test starting disabled system"""
        mock_config['phase7']['enabled'] = False
        yaml_content = yaml.dump(mock_config)
        
        with patch('builtins.open', mock_open(read_data=yaml_content)), \
             patch('phase7_startup.PHASE6_AVAILABLE', False):
            system = Phase7System('test_config.yaml')
            await system.start()
            
            assert system.running is False
            assert len(system.background_tasks) == 0
    
    @pytest.mark.asyncio
    async def test_stop_system(self, mock_config, mock_agents):
        """Test system shutdown"""
        yaml_content = yaml.dump(mock_config)
        
        with patch('builtins.open', mock_open(read_data=yaml_content)), \
             patch('phase7_startup.PHASE6_AVAILABLE', False):
            system = Phase7System('test_config.yaml')
            
            start_task = asyncio.create_task(system.start())
            await asyncio.sleep(0.1)
            
            await system.stop()
            
            assert system.running is False
            for task in system.background_tasks:
                assert task.cancelled() or task.done()
            
            await start_task


class TestBackgroundTasks:
    """Test background monitoring tasks"""
    
    @pytest.mark.asyncio
    async def test_ops_monitoring_loop(self, mock_config, mock_agents):
        """Test ops monitoring background task"""
        mock_config['ops_agent']['monitoring_interval'] = 0.1
        yaml_content = yaml.dump(mock_config)
        
        with patch('builtins.open', mock_open(read_data=yaml_content)), \
             patch('phase7_startup.PHASE6_AVAILABLE', False):
            system = Phase7System('test_config.yaml')
            
            start_task = asyncio.create_task(system.start())
            await asyncio.sleep(0.3)  # Let it run a few iterations
            
            assert mock_agents['ops'].return_value.analyze_system_capacity.call_count >= 1
            
            await system.stop()
            await start_task
    
    @pytest.mark.asyncio
    async def test_ops_auto_scaling_trigger(self, mock_config, mock_agents):
        """Test auto-scaling trigger on high load"""
        mock_config['ops_agent']['monitoring_interval'] = 0.1
        yaml_content = yaml.dump(mock_config)
        
        mock_agents['ops'].return_value.analyze_system_capacity = AsyncMock(
            return_value=Mock(current_load=0.95, estimated_headroom=0.05)
        )
        
        with patch('builtins.open', mock_open(read_data=yaml_content)), \
             patch('phase7_startup.PHASE6_AVAILABLE', False):
            system = Phase7System('test_config.yaml')
            
            start_task = asyncio.create_task(system.start())
            await asyncio.sleep(0.3)
            
            assert mock_agents['ops'].return_value.trigger_auto_scaling.call_count >= 1
            
            await system.stop()
            await start_task
    
    @pytest.mark.asyncio
    async def test_growth_analysis_loop(self, mock_config, mock_agents):
        """Test growth analysis background task"""
        mock_config['growth_strategist']['gamification_analysis_interval'] = 0.1
        yaml_content = yaml.dump(mock_config)
        
        with patch('builtins.open', mock_open(read_data=yaml_content)), \
             patch('phase7_startup.PHASE6_AVAILABLE', False):
            system = Phase7System('test_config.yaml')
            
            start_task = asyncio.create_task(system.start())
            await asyncio.sleep(0.3)
            
            assert mock_agents['growth'].return_value.analyze_gamification_effectiveness.call_count >= 1
            
            await system.stop()
            await start_task
    
    @pytest.mark.asyncio
    async def test_beta_management_loop(self, mock_config, mock_agents):
        """Test beta management background task"""
        mock_config['pm_agent']['beta_screening']['screening_interval'] = 0.1
        yaml_content = yaml.dump(mock_config)
        
        mock_agents['pm'].return_value.screen_beta_candidates = AsyncMock(
            return_value=[{'user_id': '1'}, {'user_id': '2'}]
        )
        
        with patch('builtins.open', mock_open(read_data=yaml_content)), \
             patch('phase7_startup.PHASE6_AVAILABLE', False):
            system = Phase7System('test_config.yaml')
            
            start_task = asyncio.create_task(system.start())
            await asyncio.sleep(0.3)
            
            assert mock_agents['pm'].return_value.screen_beta_candidates.call_count >= 1
            assert mock_agents['pm'].return_value.send_beta_invitations.call_count >= 1
            
            await system.stop()
            await start_task
    
    @pytest.mark.asyncio
    async def test_hitl_cleanup_loop(self, mock_config, mock_agents):
        """Test HITL cleanup background task"""
        mock_config['hitl_approval']['cleanup']['expired_requests_cleanup_interval'] = 0.1
        yaml_content = yaml.dump(mock_config)
        
        mock_agents['hitl'].return_value.cleanup_expired_requests = AsyncMock(return_value=5)
        
        with patch('builtins.open', mock_open(read_data=yaml_content)), \
             patch('phase7_startup.PHASE6_AVAILABLE', False):
            system = Phase7System('test_config.yaml')
            
            start_task = asyncio.create_task(system.start())
            await asyncio.sleep(0.3)
            
            assert mock_agents['hitl'].return_value.cleanup_expired_requests.call_count >= 1
            
            await system.stop()
            await start_task


class TestSystemStatus:
    """Test system status reporting"""
    
    def test_get_system_status(self, mock_config, mock_agents):
        """Test comprehensive system status"""
        yaml_content = yaml.dump(mock_config)
        
        with patch('builtins.open', mock_open(read_data=yaml_content)), \
             patch('phase7_startup.PHASE6_AVAILABLE', True):
            system = Phase7System('test_config.yaml')
            system.running = True
            system.ops_agent = mock_agents['ops'].return_value
            system.growth_strategist = mock_agents['growth'].return_value
            system.pm_agent = mock_agents['pm'].return_value
            system.hitl_system = mock_agents['hitl'].return_value
            system.monitoring_system = Mock()
            system.meta_agent = Mock()
            system.security_manager = Mock()
            
            status = system.get_system_status()
            
            assert status['phase'] == 'Phase 7: Performance, Growth & Beta Introduction'
            assert status['version'] == '1.0.0'
            assert status['running'] is True
            assert 'ops_agent' in status['components']
            assert 'growth_strategist' in status['components']
            assert 'pm_agent' in status['components']
            assert 'hitl_system' in status['components']
            assert status['integration']['phase6_available'] is True
            assert status['integration']['monitoring_system'] is True
    
    def test_get_system_status_minimal(self, mock_config):
        """Test system status with minimal components"""
        mock_config['ops_agent']['enabled'] = False
        mock_config['growth_strategist']['enabled'] = False
        yaml_content = yaml.dump(mock_config)
        
        with patch('builtins.open', mock_open(read_data=yaml_content)), \
             patch('phase7_startup.PHASE6_AVAILABLE', False):
            system = Phase7System('test_config.yaml')
            
            status = system.get_system_status()
            
            assert status['phase'] == 'Phase 7: Performance, Growth & Beta Introduction'
            assert status['integration']['phase6_available'] is False
            assert status['integration']['monitoring_system'] is False


class TestEnvironmentValidation:
    """Test environment validation"""
    
    @pytest.mark.asyncio
    async def test_validate_environment_success(self, mock_config):
        """Test successful environment validation"""
        yaml_content = yaml.dump(mock_config)
        
        mock_validator = Mock()
        mock_validator.validate_environment.return_value = Mock(
            valid=True,
            errors=[],
            warnings=[]
        )
        
        with patch('builtins.open', mock_open(read_data=yaml_content)), \
             patch('env_schema_validator.env_schema_validator', mock_validator), \
             patch('phase7_startup.PHASE6_AVAILABLE', False), \
             patch('phase7_startup.OpsAgent'), \
             patch('phase7_startup.GrowthStrategist'), \
             patch('phase7_startup.PMAgent'), \
             patch('phase7_startup.HITLApprovalSystem'):
            
            system = Phase7System('test_config.yaml')
            await system.initialize()
            
            mock_validator.validate_environment.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_validate_environment_with_warnings(self, mock_config):
        """Test environment validation with warnings"""
        yaml_content = yaml.dump(mock_config)
        
        mock_validator = Mock()
        mock_validator.validate_environment.return_value = Mock(
            valid=True,
            errors=[],
            warnings=['Missing optional variable: SENTRY_DSN']
        )
        
        with patch('builtins.open', mock_open(read_data=yaml_content)), \
             patch('env_schema_validator.env_schema_validator', mock_validator), \
             patch('phase7_startup.PHASE6_AVAILABLE', False), \
             patch('phase7_startup.OpsAgent'), \
             patch('phase7_startup.GrowthStrategist'), \
             patch('phase7_startup.PMAgent'), \
             patch('phase7_startup.HITLApprovalSystem'):
            
            system = Phase7System('test_config.yaml')
            await system.initialize()
    
    @pytest.mark.asyncio
    async def test_validate_environment_failure(self, mock_config):
        """Test environment validation failure"""
        yaml_content = yaml.dump(mock_config)
        
        mock_validator = Mock()
        mock_validator.validate_environment.return_value = Mock(
            valid=False,
            errors=['Missing required variable: DATABASE_URL'],
            warnings=[]
        )
        
        with patch('builtins.open', mock_open(read_data=yaml_content)), \
             patch('env_schema_validator.env_schema_validator', mock_validator), \
             patch('phase7_startup.PHASE6_AVAILABLE', False):
            
            system = Phase7System('test_config.yaml')
            
            with pytest.raises(RuntimeError, match="Environment validation failed"):
                await system.initialize()
    
    @pytest.mark.asyncio
    async def test_validate_environment_not_available(self, mock_config):
        """Test graceful handling when validator not available"""
        yaml_content = yaml.dump(mock_config)
        
        with patch('builtins.open', mock_open(read_data=yaml_content)), \
             patch('builtins.__import__', side_effect=ImportError('env_schema_validator not found')), \
             patch('phase7_startup.PHASE6_AVAILABLE', False), \
             patch('phase7_startup.OpsAgent'), \
             patch('phase7_startup.GrowthStrategist'), \
             patch('phase7_startup.PMAgent'), \
             patch('phase7_startup.HITLApprovalSystem'):
            
            system = Phase7System('test_config.yaml')
            await system.initialize()


class TestMainEntryPoint:
    """Test main entry point"""
    
    @pytest.mark.asyncio
    async def test_main_function(self, mock_config, mock_agents):
        """Test main entry point"""
        yaml_content = yaml.dump(mock_config)
        
        with patch('builtins.open', mock_open(read_data=yaml_content)), \
             patch('phase7_startup.PHASE6_AVAILABLE', False):
            
            with patch('phase7_startup.Phase7System') as mock_system_class:
                mock_system = Mock()
                mock_system.start = AsyncMock()
                mock_system_class.return_value = mock_system
                
                main_task = asyncio.create_task(main())
                await asyncio.sleep(0.1)
                main_task.cancel()
                
                try:
                    await main_task
                except asyncio.CancelledError:
                    pass
                
                mock_system.start.assert_called_once()


class TestErrorHandling:
    """Test error handling in background tasks"""
    
    @pytest.mark.asyncio
    async def test_ops_monitoring_error_handling(self, mock_config, mock_agents):
        """Test error handling in ops monitoring loop"""
        mock_config['ops_agent']['monitoring_interval'] = 0.1
        yaml_content = yaml.dump(mock_config)
        
        mock_agents['ops'].return_value.analyze_system_capacity = AsyncMock(
            side_effect=[Exception('Test error'), Mock(current_load=0.5, estimated_headroom=0.5)]
        )
        
        with patch('builtins.open', mock_open(read_data=yaml_content)), \
             patch('phase7_startup.PHASE6_AVAILABLE', False):
            system = Phase7System('test_config.yaml')
            
            start_task = asyncio.create_task(system.start())
            await asyncio.sleep(0.3)
            
            assert system.running is True
            
            await system.stop()
            await start_task
    
    @pytest.mark.asyncio
    async def test_component_initialization_error(self, mock_config):
        """Test graceful handling of component initialization errors"""
        yaml_content = yaml.dump(mock_config)
        
        with patch('builtins.open', mock_open(read_data=yaml_content)), \
             patch('phase7_startup.PHASE6_AVAILABLE', True), \
             patch('phase7_startup.MonitoringSystem', side_effect=Exception('Init failed')), \
             patch('phase7_startup.OpsAgent'), \
             patch('phase7_startup.GrowthStrategist'), \
             patch('phase7_startup.PMAgent'), \
             patch('phase7_startup.HITLApprovalSystem'):
            
            system = Phase7System('test_config.yaml')
            await system.initialize()
            
            assert system.monitoring_system is None
            assert system.ops_agent is not None
