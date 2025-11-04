from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    preferences = db.Column(db.Text, nullable=True, default='{}')

    def __repr__(self):
        return f'<User {self.username}>'

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def get_preferences(self):
        """Get user preferences as a dictionary"""
        try:
            return json.loads(self.preferences) if self.preferences else {}
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_preferences(self, prefs_dict):
        """Set user preferences from a dictionary"""
        self.preferences = json.dumps(prefs_dict)
