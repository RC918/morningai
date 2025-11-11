"""Test policies.yaml path resolution"""
import os
import tempfile
from pathlib import Path
import pytest
import yaml


def test_policies_path_from_env():
    """Test that POLICIES_PATH environment variable is respected"""
    from governance.reputation_engine import ReputationEngine
    
    # Create a temporary policies file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        test_policies = {
            'reputation': {
                'initial_score': 150,
                'scoring_rules': {'test_event': 10},
                'permission_levels': {'test_level': {'min_score': 0}}
            }
        }
        yaml.dump(test_policies, f)
        temp_path = f.name
    
    try:
        # Set environment variable
        os.environ['POLICIES_PATH'] = temp_path
        
        # Create engine
        engine = ReputationEngine()
        
        # Verify it loaded the custom policies
        assert engine.reputation_config.get('initial_score') == 150
        assert engine.scoring_rules.get('test_event') == 10
    finally:
        # Clean up
        if 'POLICIES_PATH' in os.environ:
            del os.environ['POLICIES_PATH']
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_policies_path_resolution_from_repo_root():
    """Test that policies.yaml is found from repo root"""
    from governance.reputation_engine import ReputationEngine
    
    # Clear environment variable
    if 'POLICIES_PATH' in os.environ:
        del os.environ['POLICIES_PATH']
    
    # Create engine (should find config/policies.yaml from repo root)
    engine = ReputationEngine()
    
    # Verify it loaded valid policies
    assert engine.policies is not None
    assert 'reputation' in engine.policies
    assert 'scoring_rules' in engine.reputation_config
    assert 'permission_levels' in engine.reputation_config


def test_policies_path_explicit():
    """Test that explicit policies_path parameter works"""
    from governance.reputation_engine import ReputationEngine
    
    # Create a temporary policies file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        test_policies = {
            'reputation': {
                'initial_score': 200,
                'scoring_rules': {},
                'permission_levels': {}
            }
        }
        yaml.dump(test_policies, f)
        temp_path = f.name
    
    try:
        # Create engine with explicit path
        engine = ReputationEngine(policies_path=temp_path)
        
        # Verify it loaded the custom policies
        assert engine.reputation_config.get('initial_score') == 200
    finally:
        # Clean up
        if os.path.exists(temp_path):
            os.unlink(temp_path)
