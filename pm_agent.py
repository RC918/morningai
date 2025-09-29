#!/usr/bin/env python3
"""
PM_Agent - Product Manager for Beta tenant management
Autonomous Beta user screening, feedback collection, and story creation
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
import json
import uuid

@dataclass
class BetaCandidate:
    """Beta testing candidate"""
    user_id: str
    activity_score: float
    engagement_metrics: Dict
    qualification_reason: str
    invited_at: Optional[datetime] = None
    
@dataclass
class UserStory:
    """User story generated from feedback"""
    story_id: str
    title: str
    description: str
    priority: str
    estimated_effort: int
    source_feedback: str
    created_at: datetime
    
@dataclass
class FeedbackAnalysis:
    """Analyzed user feedback"""
    feedback_id: str
    user_id: str
    original_text: str
    sentiment: str
    category: str
    priority_score: float
    extracted_requirements: List[str]

class PMAgent:
    """Product Manager Agent for Beta program management"""
    
    def __init__(self, support_agent=None):
        self.support_agent = support_agent
        self.logger = logging.getLogger(__name__)
        self.beta_candidates = []
        self.user_stories = []
        self.feedback_history = []
        
    async def screen_beta_candidates(self, min_activity_score: float = 0.8) -> List[BetaCandidate]:
        """Screen high-activity users for Beta testing"""
        mock_users = [
            {'user_id': 'user_001', 'activity_score': 0.85, 'daily_logins': 25, 'features_used': 8},
            {'user_id': 'user_002', 'activity_score': 0.92, 'daily_logins': 28, 'features_used': 12},
            {'user_id': 'user_003', 'activity_score': 0.78, 'daily_logins': 20, 'features_used': 6},
            {'user_id': 'user_004', 'activity_score': 0.88, 'daily_logins': 26, 'features_used': 10},
            {'user_id': 'user_005', 'activity_score': 0.95, 'daily_logins': 30, 'features_used': 15},
        ]
        
        candidates = []
        for user in mock_users:
            if user['activity_score'] >= min_activity_score:
                candidate = BetaCandidate(
                    user_id=user['user_id'],
                    activity_score=user['activity_score'],
                    engagement_metrics={
                        'daily_logins': user['daily_logins'],
                        'features_used': user['features_used']
                    },
                    qualification_reason=f"High activity score: {user['activity_score']}"
                )
                candidates.append(candidate)
                
        self.beta_candidates.extend(candidates)
        self.logger.info(f"Screened {len(candidates)} Beta candidates from {len(mock_users)} users")
        return candidates
        
    async def send_beta_invitations(self, candidates: List[BetaCandidate]) -> Dict:
        """Send Beta testing invitations to qualified candidates"""
        sent_count = 0
        for candidate in candidates:
            candidate.invited_at = datetime.now()
            sent_count += 1
            self.logger.info(f"Beta invitation sent to {candidate.user_id}")
            
        return {
            'invitations_sent': sent_count,
            'total_candidates': len(candidates),
            'success_rate': 1.0,
            'timestamp': datetime.now().isoformat()
        }
        
    async def collect_and_analyze_feedback(self) -> List[UserStory]:
        """Collect Beta feedback and generate user stories using NLP"""
        mock_feedback = [
            {
                'user_id': 'user_001',
                'feedback': 'The AI response time is too slow during peak hours, sometimes taking over 10 seconds',
                'sentiment': 'negative',
                'category': 'performance',
                'priority_score': 0.9
            },
            {
                'user_id': 'user_002', 
                'feedback': 'Would love to have more customization options for the dashboard layout and themes',
                'sentiment': 'positive',
                'category': 'feature_request',
                'priority_score': 0.6
            },
            {
                'user_id': 'user_004',
                'feedback': 'The mobile app crashes when I try to upload large files',
                'sentiment': 'negative',
                'category': 'bug',
                'priority_score': 0.8
            }
        ]
        
        new_stories = []
        for feedback in mock_feedback:
            analysis = FeedbackAnalysis(
                feedback_id=str(uuid.uuid4()),
                user_id=feedback['user_id'],
                original_text=feedback['feedback'],
                sentiment=feedback['sentiment'],
                category=feedback['category'],
                priority_score=feedback['priority_score'],
                extracted_requirements=self._extract_requirements(feedback['feedback'])
            )
            
            self.feedback_history.append(analysis)
            
            story = self._create_user_story_from_feedback(analysis)
            if story:
                new_stories.append(story)
                
        self.user_stories.extend(new_stories)
        self.logger.info(f"Generated {len(new_stories)} user stories from feedback analysis")
        return new_stories
        
    def _extract_requirements(self, feedback_text: str) -> List[str]:
        """Extract requirements from feedback text using simple NLP"""
        requirements = []
        
        if 'slow' in feedback_text.lower() or 'performance' in feedback_text.lower():
            requirements.append('Improve response time')
        if 'customization' in feedback_text.lower() or 'customize' in feedback_text.lower():
            requirements.append('Add customization options')
        if 'crash' in feedback_text.lower() or 'bug' in feedback_text.lower():
            requirements.append('Fix stability issues')
        if 'mobile' in feedback_text.lower():
            requirements.append('Mobile app improvement')
            
        return requirements
        
    def _create_user_story_from_feedback(self, analysis: FeedbackAnalysis) -> Optional[UserStory]:
        """Create user story from analyzed feedback"""
        story_templates = {
            'performance': {
                'title': 'Optimize {component} performance during peak hours',
                'description': 'As a user, I want faster response times so that I can work efficiently without delays.',
                'priority': 'high',
                'effort': 8
            },
            'feature_request': {
                'title': 'Add {feature} customization options',
                'description': 'As a user, I want to customize {feature} so that I can personalize my experience.',
                'priority': 'medium',
                'effort': 5
            },
            'bug': {
                'title': 'Fix {component} stability issues',
                'description': 'As a user, I want {component} to work reliably so that I can complete my tasks without interruption.',
                'priority': 'high',
                'effort': 6
            }
        }
        
        if analysis.category not in story_templates:
            return None
            
        template = story_templates[analysis.category]
        
        component = 'system'
        if 'dashboard' in analysis.original_text.lower():
            component = 'dashboard'
        elif 'mobile' in analysis.original_text.lower():
            component = 'mobile app'
        elif 'ai' in analysis.original_text.lower():
            component = 'AI response'
            
        story = UserStory(
            story_id=f"story_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{analysis.feedback_id[:8]}",
            title=template['title'].format(component=component, feature=component),
            description=f"{template['description'].format(component=component, feature=component)}\n\nOriginal feedback: {analysis.original_text}",
            priority=template['priority'],
            estimated_effort=template['effort'],
            source_feedback=analysis.original_text,
            created_at=datetime.now()
        )
        
        return story
        
    async def generate_sprint_planning_report(self) -> Dict:
        """Generate Sprint planning report from user stories"""
        if not self.user_stories:
            return {'message': 'No user stories available for Sprint planning'}
            
        high_priority = [s for s in self.user_stories if s.priority == 'high']
        medium_priority = [s for s in self.user_stories if s.priority == 'medium']
        low_priority = [s for s in self.user_stories if s.priority == 'low']
        
        total_effort = sum(story.estimated_effort for story in self.user_stories)
        
        return {
            'sprint_summary': {
                'total_stories': len(self.user_stories),
                'total_effort_points': total_effort,
                'high_priority_count': len(high_priority),
                'medium_priority_count': len(medium_priority),
                'low_priority_count': len(low_priority)
            },
            'recommended_sprint_stories': high_priority[:5],  # Top 5 high priority
            'backlog_stories': medium_priority + low_priority,
            'generated_at': datetime.now().isoformat()
        }
        
    def get_beta_program_status(self) -> Dict:
        """Get current Beta program status"""
        active_candidates = [c for c in self.beta_candidates if c.invited_at]
        
        return {
            'agent': 'PM_Agent',
            'beta_program': {
                'total_candidates': len(self.beta_candidates),
                'invited_candidates': len(active_candidates),
                'average_activity_score': sum(c.activity_score for c in self.beta_candidates) / len(self.beta_candidates) if self.beta_candidates else 0
            },
            'user_stories': {
                'total_generated': len(self.user_stories),
                'by_priority': {
                    'high': len([s for s in self.user_stories if s.priority == 'high']),
                    'medium': len([s for s in self.user_stories if s.priority == 'medium']),
                    'low': len([s for s in self.user_stories if s.priority == 'low'])
                }
            },
            'feedback_analysis': {
                'total_feedback': len(self.feedback_history),
                'sentiment_distribution': self._get_sentiment_distribution()
            },
            'status': 'operational'
        }
        
    def _get_sentiment_distribution(self) -> Dict:
        """Get sentiment distribution from feedback"""
        if not self.feedback_history:
            return {}
            
        sentiments = [f.sentiment for f in self.feedback_history]
        return {
            'positive': sentiments.count('positive'),
            'negative': sentiments.count('negative'),
            'neutral': sentiments.count('neutral')
        }
