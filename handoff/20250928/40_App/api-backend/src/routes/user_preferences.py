from flask import Blueprint, jsonify, request
from src.models.user_preferences import UserPreferences, db
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

user_preferences_bp = Blueprint('user_preferences', __name__)

@user_preferences_bp.route('/user/preferences', methods=['GET'])
def get_user_preferences():
    """
    Get user preferences
    
    Query Parameters:
    - user_id: User ID (optional, defaults to 'anonymous' if not provided)
    
    Returns:
    - 200: User preferences object
    - 404: User preferences not found (will create default)
    """
    try:
        user_id = request.args.get('user_id', 'anonymous')
        
        preferences = UserPreferences.query.filter_by(user_id=user_id).first()
        
        if not preferences:
            preferences = UserPreferences(
                user_id=user_id,
                show_welcome_modal=True,
                theme='light',
                language='zh-TW',
                email_notifications=True,
                push_notifications=True
            )
            db.session.add(preferences)
            db.session.commit()
            
            logger.info(f"Created default preferences for user_id={user_id}")
        
        return jsonify(preferences.to_dict()), 200
        
    except Exception as e:
        logger.error(f"Error getting user preferences: {str(e)}")
        return jsonify({
            'error': 'Failed to get user preferences',
            'message': str(e)
        }), 500


@user_preferences_bp.route('/user/preferences', methods=['PUT', 'PATCH'])
def update_user_preferences():
    """
    Update user preferences
    
    Request Body:
    {
        "user_id": "string (required)",
        "show_welcome_modal": boolean,
        "theme": "light" | "dark",
        "language": "zh-TW" | "en-US",
        "dashboard_layout": object,
        "email_notifications": boolean,
        "push_notifications": boolean
    }
    
    Returns:
    - 200: Updated preferences
    - 400: Invalid request
    - 500: Server error
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'Invalid request',
                'message': 'Request body is required'
            }), 400
        
        user_id = data.get('user_id', 'anonymous')
        
        preferences = UserPreferences.query.filter_by(user_id=user_id).first()
        
        if not preferences:
            preferences = UserPreferences(user_id=user_id)
            db.session.add(preferences)
        
        preferences.update_from_dict(data)
        
        if 'show_welcome_modal' in data and not data['show_welcome_modal']:
            if not preferences.welcome_modal_completed_at:
                preferences.welcome_modal_completed_at = datetime.now()
        
        db.session.commit()
        
        logger.info(f"Updated preferences for user_id={user_id}")
        
        return jsonify(preferences.to_dict()), 200
        
    except Exception as e:
        logger.error(f"Error updating user preferences: {str(e)}")
        db.session.rollback()
        return jsonify({
            'error': 'Failed to update user preferences',
            'message': str(e)
        }), 500


@user_preferences_bp.route('/user/preferences', methods=['DELETE'])
def delete_user_preferences():
    """
    Delete user preferences (reset to defaults)
    
    Query Parameters:
    - user_id: User ID (required)
    
    Returns:
    - 204: Successfully deleted
    - 400: Invalid request
    - 404: Preferences not found
    - 500: Server error
    """
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({
                'error': 'Invalid request',
                'message': 'user_id is required'
            }), 400
        
        preferences = UserPreferences.query.filter_by(user_id=user_id).first()
        
        if not preferences:
            return jsonify({
                'error': 'Not found',
                'message': f'Preferences for user_id={user_id} not found'
            }), 404
        
        db.session.delete(preferences)
        db.session.commit()
        
        logger.info(f"Deleted preferences for user_id={user_id}")
        
        return '', 204
        
    except Exception as e:
        logger.error(f"Error deleting user preferences: {str(e)}")
        db.session.rollback()
        return jsonify({
            'error': 'Failed to delete user preferences',
            'message': str(e)
        }), 500
