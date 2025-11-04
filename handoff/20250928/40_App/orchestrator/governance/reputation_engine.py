"""Reputation Engine - Agent reputation scoring and management"""
import os
import yaml
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta


class ReputationEngine:
    """Manages agent reputation scores and permission levels"""
    
    def __init__(self, supabase_client=None, policies_path: Optional[str] = None):
        self.supabase = supabase_client
        
        if policies_path is None:
            policies_path = os.path.join(
                os.path.dirname(__file__),
                '../../../../config/policies.yaml'
            )
        
        self.policies = self._load_policies(policies_path)
        self.reputation_config = self.policies.get('reputation', {})
        self.scoring_rules = self.reputation_config.get('scoring_rules', {})
        self.permission_levels = self.reputation_config.get('permission_levels', {})
    
    def _load_policies(self, path: str) -> Dict:
        """Load policies from YAML"""
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"[ReputationEngine] Error loading policies: {e}")
            return {}
    
    def _get_supabase(self):
        """Get Supabase client"""
        if self.supabase:
            return self.supabase
        
        try:
            from orchestrator.persistence.db_client import get_client
            return get_client()
        except (ImportError, ModuleNotFoundError):
            try:
                from persistence.db_client import get_client
                return get_client()
            except Exception as e:
                print(f"[ReputationEngine] Supabase unavailable: {e}")
                return None
        except Exception as e:
            print(f"[ReputationEngine] Supabase unavailable: {e}")
            return None
    
    def get_or_create_agent(self, agent_type: str) -> Optional[str]:
        """Get or create agent reputation record"""
        supabase = self._get_supabase()
        if not supabase:
            return None
        
        try:
            response = supabase.table('agent_reputation').select('*').eq('agent_type', agent_type).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]['agent_id']
            
            initial_score = self.reputation_config.get('initial_score', 100)
            response = supabase.table('agent_reputation').insert({
                'agent_type': agent_type,
                'reputation_score': initial_score,
                'permission_level': 'sandbox_only'
            }).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]['agent_id']
            
            return None
        except Exception as e:
            print(f"[ReputationEngine] Error getting/creating agent: {e}")
            return None
    
    def record_event(
        self,
        agent_id: str,
        event_type: str,
        trace_id: Optional[str] = None,
        reason: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """Record a reputation event"""
        supabase = self._get_supabase()
        if not supabase:
            print(f"[ReputationEngine] Supabase unavailable, skipping event recording")
            return False
        
        delta = self.scoring_rules.get(event_type, 0)
        
        try:
            supabase.rpc('record_reputation_event', {
                'p_agent_id': agent_id,
                'p_event_type': event_type,
                'p_delta': delta,
                'p_reason': reason,
                'p_trace_id': trace_id,
                'p_metadata': metadata
            }).execute()
            
            print(f"[ReputationEngine] Recorded {event_type} for {agent_id}: delta={delta}")
            return True
        except Exception as e:
            print(f"[ReputationEngine] Error recording event: {e}")
            return False
    
    def get_reputation(self, agent_id: str) -> Optional[Dict]:
        """Get agent reputation summary"""
        supabase = self._get_supabase()
        if not supabase:
            return None
        
        try:
            response = supabase.rpc('get_agent_reputation_summary', {
                'p_agent_id': agent_id
            }).execute()
            
            if response.data:
                return response.data
            return None
        except Exception as e:
            print(f"[ReputationEngine] Error getting reputation: {e}")
            return None
    
    def get_permission_level(self, agent_id: str) -> str:
        """Get agent's current permission level"""
        supabase = self._get_supabase()
        if not supabase:
            return 'sandbox_only'
        
        try:
            response = supabase.table('agent_reputation').select('permission_level').eq('agent_id', agent_id).single().execute()
            
            if response.data:
                return response.data['permission_level']
            return 'sandbox_only'
        except Exception as e:
            print(f"[ReputationEngine] Error getting permission level: {e}")
            return 'sandbox_only'
    
    def get_reputation_score(self, agent_id: str) -> int:
        """Get agent's current reputation score"""
        supabase = self._get_supabase()
        if not supabase:
            return 100
        
        try:
            response = supabase.table('agent_reputation').select('reputation_score').eq('agent_id', agent_id).single().execute()
            
            if response.data:
                return response.data['reputation_score']
            return 100
        except Exception as e:
            print(f"[ReputationEngine] Error getting reputation score: {e}")
            return 100
    
    def update_permission_level(self, agent_id: str) -> str:
        """Update agent's permission level based on score"""
        supabase = self._get_supabase()
        if not supabase:
            return 'sandbox_only'
        
        try:
            response = supabase.rpc('update_permission_level', {
                'p_agent_id': agent_id
            }).execute()
            
            if response.data:
                return response.data
            return 'sandbox_only'
        except Exception as e:
            print(f"[ReputationEngine] Error updating permission level: {e}")
            return 'sandbox_only'
    
    def get_allowed_operations(self, agent_id: str) -> list:
        """Get list of operations allowed for agent's permission level"""
        permission_level = self.get_permission_level(agent_id)
        
        level_config = self.permission_levels.get(permission_level, {})
        return level_config.get('allowed_operations', [])
    
    def can_perform_operation(self, agent_id: str, operation: str) -> bool:
        """Check if agent can perform specific operation"""
        allowed_operations = self.get_allowed_operations(agent_id)
        return operation in allowed_operations
    
    def get_recent_events(self, agent_id: str, limit: int = 10) -> list:
        """Get recent reputation events for agent"""
        supabase = self._get_supabase()
        if not supabase:
            return []
        
        try:
            response = supabase.table('reputation_events') \
                .select('*') \
                .eq('agent_id', agent_id) \
                .order('created_at', desc=True) \
                .limit(limit) \
                .execute()
            
            return response.data if response.data else []
        except Exception as e:
            print(f"[ReputationEngine] Error getting recent events: {e}")
            return []
    
    def get_leaderboard(self, limit: int = 10) -> list:
        """Get top agents by reputation score"""
        supabase = self._get_supabase()
        if not supabase:
            return []
        
        try:
            response = supabase.table('agent_reputation') \
                .select('agent_id, agent_type, reputation_score, permission_level') \
                .order('reputation_score', desc=True) \
                .limit(limit) \
                .execute()
            
            return response.data if response.data else []
        except Exception as e:
            print(f"[ReputationEngine] Error getting leaderboard: {e}")
            return []
    
    def apply_decay(self, agent_id: str) -> bool:
        """Apply reputation decay for inactive agents"""
        decay_config = self.reputation_config.get('decay', {})
        if not decay_config.get('enabled', False):
            return False
        
        supabase = self._get_supabase()
        if not supabase:
            return False
        
        try:
            response = supabase.table('agent_reputation') \
                .select('reputation_score, last_activity') \
                .eq('agent_id', agent_id) \
                .single() \
                .execute()
            
            if not response.data:
                return False
            
            current_score = response.data['reputation_score']
            last_activity = datetime.fromisoformat(response.data['last_activity'].replace('Z', '+00:00'))
            
            days_inactive = (datetime.now(last_activity.tzinfo) - last_activity).days
            if days_inactive < 7:
                return False
            
            decay_rate = decay_config.get('rate', 0.01)
            min_score = decay_config.get('min_score', 50)
            
            weeks_inactive = days_inactive // 7
            decay_amount = int(current_score * decay_rate * weeks_inactive)
            new_score = max(min_score, current_score - decay_amount)
            
            if new_score < current_score:
                supabase.rpc('update_agent_reputation', {
                    'p_agent_id': agent_id,
                    'p_delta': new_score - current_score
                }).execute()
                
                self.record_event(
                    agent_id,
                    'reputation_decay',
                    reason=f"Inactive for {days_inactive} days, decayed by {decay_amount} points"
                )
                
                print(f"[ReputationEngine] Applied decay to {agent_id}: {current_score} -> {new_score}")
                return True
            
            return False
        except Exception as e:
            print(f"[ReputationEngine] Error applying decay: {e}")
            return False
    
    def get_statistics(self) -> Dict:
        """Get overall reputation system statistics"""
        supabase = self._get_supabase()
        if not supabase:
            return {}
        
        try:
            response = supabase.table('agent_reputation') \
                .select('permission_level, reputation_score') \
                .execute()
            
            if not response.data:
                return {}
            
            agents = response.data
            
            total_agents = len(agents)
            avg_score = sum(a['reputation_score'] for a in agents) / total_agents if total_agents > 0 else 0
            
            level_counts = {}
            for agent in agents:
                level = agent['permission_level']
                level_counts[level] = level_counts.get(level, 0) + 1
            
            return {
                'total_agents': total_agents,
                'average_score': round(avg_score, 2),
                'agents_by_level': level_counts,
                'high_reputation_agents': len([a for a in agents if a['reputation_score'] >= 130]),
                'low_reputation_agents': len([a for a in agents if a['reputation_score'] < 90])
            }
        except Exception as e:
            print(f"[ReputationEngine] Error getting statistics: {e}")
            return {}


_reputation_engine = None


def get_reputation_engine() -> ReputationEngine:
    """Get or create global ReputationEngine instance"""
    global _reputation_engine
    if _reputation_engine is None:
        _reputation_engine = ReputationEngine()
    return _reputation_engine
