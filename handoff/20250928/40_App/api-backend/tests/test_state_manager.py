#!/usr/bin/env python3
"""
Tests for Persistent State Manager
"""

import pytest
import os
import tempfile
from datetime import datetime, timedelta
from src.persistence.state_manager import (
    PersistentStateManager,
    StateCheckpoint,
    persistent_state_manager
)


class TestPersistentStateManager:
    """Test suite for PersistentStateManager class"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        self.manager = PersistentStateManager(db_path=self.temp_db.name)
    
    def teardown_method(self):
        """Cleanup test fixtures"""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_init(self):
        """Test state manager initialization"""
        manager = PersistentStateManager(db_path=':memory:')
        assert manager.db_path == ':memory:'
        assert manager.logger is not None
    
    def test_save_beta_candidate(self):
        """Test saving Beta candidate"""
        candidate_data = {
            'user_id': 'user123',
            'activity_score': 85.5,
            'engagement_metrics': {'logins': 10, 'tasks': 20},
            'qualification_reason': 'High activity',
            'status': 'pending'
        }
        
        result = self.manager.save_beta_candidate(candidate_data)
        assert result is True
    
    def test_load_beta_candidates(self):
        """Test loading Beta candidates"""
        candidate_data = {
            'user_id': 'user456',
            'activity_score': 90.0,
            'engagement_metrics': {'logins': 15, 'tasks': 30},
            'qualification_reason': 'Very active',
            'status': 'pending'
        }
        
        self.manager.save_beta_candidate(candidate_data)
        candidates = self.manager.load_beta_candidates()
        
        assert len(candidates) == 1
        assert candidates[0]['user_id'] == 'user456'
        assert candidates[0]['activity_score'] == 90.0
        assert candidates[0]['engagement_metrics']['logins'] == 15
    
    def test_load_beta_candidates_by_status(self):
        """Test loading Beta candidates filtered by status"""
        self.manager.save_beta_candidate({
            'user_id': 'user1',
            'activity_score': 80.0,
            'engagement_metrics': {},
            'qualification_reason': 'Active',
            'status': 'pending'
        })
        self.manager.save_beta_candidate({
            'user_id': 'user2',
            'activity_score': 85.0,
            'engagement_metrics': {},
            'qualification_reason': 'Active',
            'status': 'approved'
        })
        
        pending = self.manager.load_beta_candidates(status='pending')
        approved = self.manager.load_beta_candidates(status='approved')
        
        assert len(pending) == 1
        assert len(approved) == 1
        assert pending[0]['status'] == 'pending'
        assert approved[0]['status'] == 'approved'
    
    def test_save_approval_request(self):
        """Test saving approval request"""
        request_data = {
            'request_id': 'req123',
            'trace_id': 'trace456',
            'title': 'Deploy to production',
            'description': 'Need approval for deployment',
            'context': {'environment': 'production'},
            'prompt_details': 'Deploy v2.0',
            'requester_agent': 'OpsAgent',
            'priority': 'high',
            'status': 'pending',
            'created_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(hours=1)).isoformat()
        }
        
        result = self.manager.save_approval_request(request_data)
        assert result is True
    
    def test_load_approval_requests(self):
        """Test loading approval requests"""
        request_data = {
            'request_id': 'req789',
            'trace_id': 'trace101112',
            'title': 'Database migration',
            'description': 'Approve schema changes',
            'context': {'tables': ['users', 'orders']},
            'prompt_details': 'Migrate to v3',
            'requester_agent': 'DBAgent',
            'priority': 'medium',
            'status': 'pending',
            'created_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(hours=2)).isoformat()
        }
        
        self.manager.save_approval_request(request_data)
        requests = self.manager.load_approval_requests()
        
        assert len(requests) == 1
        assert requests[0]['request_id'] == 'req789'
        assert requests[0]['context']['tables'] == ['users', 'orders']
    
    def test_load_approval_requests_by_status(self):
        """Test loading approval requests filtered by status"""
        self.manager.save_approval_request({
            'request_id': 'req1',
            'trace_id': 'trace1',
            'title': 'Request 1',
            'description': 'Test',
            'context': {},
            'prompt_details': 'Test',
            'requester_agent': 'TestAgent',
            'priority': 'low',
            'status': 'pending',
            'created_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(hours=1)).isoformat()
        })
        self.manager.save_approval_request({
            'request_id': 'req2',
            'trace_id': 'trace2',
            'title': 'Request 2',
            'description': 'Test',
            'context': {},
            'prompt_details': 'Test',
            'requester_agent': 'TestAgent',
            'priority': 'low',
            'status': 'approved',
            'created_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(hours=1)).isoformat()
        })
        
        pending = self.manager.load_approval_requests(status='pending')
        approved = self.manager.load_approval_requests(status='approved')
        
        assert len(pending) == 1
        assert len(approved) == 1
    
    def test_save_user_story(self):
        """Test saving user story"""
        story_data = {
            'story_id': 'story123',
            'title': 'Add dark mode',
            'description': 'Implement dark mode toggle',
            'priority': 'high',
            'estimated_effort': 8,
            'source_feedback': 'user_survey',
            'status': 'backlog'
        }
        
        result = self.manager.save_user_story(story_data)
        assert result is True
    
    def test_save_gamification_rule(self):
        """Test saving gamification rule"""
        rule_data = {
            'rule_id': 'rule123',
            'name': 'First login bonus',
            'trigger_condition': 'first_login',
            'reward_type': 'points',
            'reward_amount': 100,
            'effectiveness_score': 0.85,
            'last_updated': datetime.now().isoformat(),
            'active': True
        }
        
        result = self.manager.save_gamification_rule(rule_data)
        assert result is True
    
    def test_create_checkpoint(self):
        """Test creating state checkpoint"""
        state_data = {
            'active_sessions': 5,
            'pending_tasks': 10,
            'error_count': 2
        }
        metadata = {'reason': 'backup', 'version': '1.0'}
        
        checkpoint_id = self.manager.create_checkpoint(
            'test_component',
            state_data,
            metadata
        )
        
        assert checkpoint_id is not None
        assert 'test_component' in checkpoint_id
    
    def test_restore_from_checkpoint(self):
        """Test restoring from checkpoint"""
        state_data = {
            'active_sessions': 5,
            'pending_tasks': 10
        }
        
        checkpoint_id = self.manager.create_checkpoint(
            'test_component',
            state_data
        )
        
        restored = self.manager.restore_from_checkpoint('test_component')
        
        assert restored is not None
        assert restored['component_name'] == 'test_component'
        assert restored['state']['active_sessions'] == 5
        assert restored['state']['pending_tasks'] == 10
    
    def test_restore_from_checkpoint_specific(self):
        """Test restoring from specific checkpoint"""
        state_data1 = {'value': 1}
        state_data2 = {'value': 2}
        
        checkpoint_id1 = self.manager.create_checkpoint('comp1', state_data1)
        checkpoint_id2 = self.manager.create_checkpoint('comp1', state_data2)
        
        restored = self.manager.restore_from_checkpoint('comp1', checkpoint_id1)
        
        assert restored['checkpoint_id'] == checkpoint_id1
        assert restored['state']['value'] == 1
    
    def test_restore_from_checkpoint_not_found(self):
        """Test restoring from non-existent checkpoint"""
        restored = self.manager.restore_from_checkpoint('nonexistent')
        assert restored is None
    
    def test_get_storage_stats(self):
        """Test getting storage statistics"""
        self.manager.save_beta_candidate({
            'user_id': 'user1',
            'activity_score': 80.0,
            'engagement_metrics': {},
            'qualification_reason': 'Active'
        })
        
        stats = self.manager.get_storage_stats()
        
        assert 'beta_candidates' in stats
        assert 'approval_requests' in stats
        assert 'state_checkpoints' in stats
        assert stats['beta_candidates'] == 1
    
    def test_save_dashboard_layout(self):
        """Test saving dashboard layout"""
        layout = {
            'widgets': ['chart1', 'chart2'],
            'theme': 'dark'
        }
        
        self.manager.save_dashboard_layout('user123', layout)
        
        loaded = self.manager.load_dashboard_layout('user123')
        assert loaded['widgets'] == ['chart1', 'chart2']
        assert loaded['theme'] == 'dark'
    
    def test_load_dashboard_layout_not_found(self):
        """Test loading non-existent dashboard layout"""
        result = self.manager.load_dashboard_layout('nonexistent')
        assert result is None
    
    def test_save_report_history(self):
        """Test saving report history"""
        self.manager.save_report_history(
            report_id='report123',
            name='Monthly Report',
            report_type='performance',
            format_type='pdf',
            file_path='/tmp/report.pdf',
            status='completed'
        )
        
        history = self.manager.get_report_history(limit=10)
        assert len(history) == 1
        assert history[0]['id'] == 'report123'
        assert history[0]['name'] == 'Monthly Report'
    
    def test_get_report_history_limit(self):
        """Test getting report history with limit"""
        for i in range(5):
            self.manager.save_report_history(
                report_id=f'report{i}',
                name=f'Report {i}',
                report_type='performance',
                format_type='pdf'
            )
        
        history = self.manager.get_report_history(limit=3)
        assert len(history) == 3
    
    def test_checkpoint_limit(self):
        """Test that old checkpoints are cleaned up"""
        for i in range(15):
            self.manager.create_checkpoint(
                'test_component',
                {'iteration': i}
            )
        
        stats = self.manager.get_storage_stats()
        assert stats['state_checkpoints'] <= 10


class TestStateCheckpoint:
    """Test suite for StateCheckpoint dataclass"""
    
    def test_state_checkpoint_creation(self):
        """Test creating StateCheckpoint instance"""
        checkpoint = StateCheckpoint(
            checkpoint_id='chk123',
            component_name='test_component',
            state_data={'key': 'value'},
            created_at=datetime.now(),
            metadata={'version': '1.0'}
        )
        
        assert checkpoint.checkpoint_id == 'chk123'
        assert checkpoint.component_name == 'test_component'
        assert checkpoint.state_data['key'] == 'value'
        assert checkpoint.metadata['version'] == '1.0'
