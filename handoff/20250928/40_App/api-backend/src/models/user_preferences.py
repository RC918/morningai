from flask_sqlalchemy import SQLAlchemy
from src.models.user import db
import json

class UserPreferences(db.Model):
    """User preferences model for storing user-specific settings"""
    __tablename__ = 'user_preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(255), unique=True, nullable=False, index=True)
    
    show_welcome_modal = db.Column(db.Boolean, default=True, nullable=False)
    welcome_modal_completed_at = db.Column(db.DateTime, nullable=True)
    
    theme = db.Column(db.String(20), default='light', nullable=False)
    
    language = db.Column(db.String(10), default='zh-TW', nullable=False)
    
    dashboard_layout = db.Column(db.Text, nullable=True)
    
    email_notifications = db.Column(db.Boolean, default=True, nullable=False)
    push_notifications = db.Column(db.Boolean, default=True, nullable=False)
    
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now(), nullable=False)
    
    def __repr__(self):
        return f'<UserPreferences user_id={self.user_id}>'
    
    def to_dict(self):
        """Convert model to dictionary"""
        dashboard_layout = None
        if self.dashboard_layout:
            try:
                dashboard_layout = json.loads(self.dashboard_layout)
            except json.JSONDecodeError:
                dashboard_layout = None
        
        return {
            'user_id': self.user_id,
            'show_welcome_modal': self.show_welcome_modal,
            'welcome_modal_completed_at': self.welcome_modal_completed_at.isoformat() if self.welcome_modal_completed_at else None,
            'theme': self.theme,
            'language': self.language,
            'dashboard_layout': dashboard_layout,
            'email_notifications': self.email_notifications,
            'push_notifications': self.push_notifications,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def update_from_dict(self, data):
        """Update model from dictionary"""
        if 'show_welcome_modal' in data:
            self.show_welcome_modal = bool(data['show_welcome_modal'])
        
        if 'theme' in data:
            self.theme = data['theme']
        
        if 'language' in data:
            self.language = data['language']
        
        if 'dashboard_layout' in data:
            if isinstance(data['dashboard_layout'], dict):
                self.dashboard_layout = json.dumps(data['dashboard_layout'])
            elif isinstance(data['dashboard_layout'], str):
                self.dashboard_layout = data['dashboard_layout']
            else:
                self.dashboard_layout = None
        
        if 'email_notifications' in data:
            self.email_notifications = bool(data['email_notifications'])
        
        if 'push_notifications' in data:
            self.push_notifications = bool(data['push_notifications'])
        
        if 'welcome_modal_completed_at' in data:
            self.welcome_modal_completed_at = data['welcome_modal_completed_at']
