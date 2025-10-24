from flask import Blueprint, jsonify, request
from src.models.user import User, db
from src.middleware.auth_middleware import jwt_required
import json
import os
import logging

logger = logging.getLogger(__name__)

user_bp = Blueprint('user', __name__)

def get_supabase_client():
    """Get Supabase client instance"""
    try:
        from orchestrator.persistence.db_client import get_client
        return get_client()
    except Exception as e:
        logger.error(f"Failed to get Supabase client: {e}")
        raise

def is_production():
    """Check if running in production (using Supabase)"""
    from flask import current_app
    is_testing = current_app.config.get('TESTING', False)
    has_supabase_db = os.environ.get('DATABASE_URL') and 'supabase' in os.environ.get('DATABASE_URL', '')
    return has_supabase_db and not is_testing

@user_bp.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])

@user_bp.route('/users', methods=['POST'])
def create_user():
    
    data = request.json
    user = User(username=data['username'], email=data['email'])
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201

@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())

@user_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.json
    user.username = data.get('username', user.username)
    user.email = data.get('email', user.email)
    db.session.commit()
    return jsonify(user.to_dict())

@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return '', 204

@user_bp.route('/user/profile', methods=['GET'])
@jwt_required
def get_user_profile():
    """Get current user's profile"""
    user_id = request.user_id
    
    if is_production():
        try:
            client = get_supabase_client()
            response = client.table("user_profiles") \
                .select("id, display_name, role, created_at") \
                .eq("id", user_id) \
                .single() \
                .execute()
            
            if not response.data:
                return jsonify({"error": "User not found"}), 404
            
            return jsonify(response.data)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        user = User.query.get_or_404(user_id)
        return jsonify(user.to_dict())

@user_bp.route('/user/preferences', methods=['GET'])
@jwt_required
def get_user_preferences():
    """Get current user's preferences"""
    user_id = request.user_id
    
    if is_production():
        try:
            client = get_supabase_client()
            response = client.table("user_profiles") \
                .select("preferences") \
                .eq("id", user_id) \
                .single() \
                .execute()
            
            if not response.data:
                return jsonify({"error": "User not found"}), 404
            
            prefs_str = response.data.get('preferences', '{}')
            try:
                prefs = json.loads(prefs_str) if prefs_str else {}
            except json.JSONDecodeError:
                prefs = {}
            
            return jsonify(prefs)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        user = User.query.get_or_404(user_id)
        return jsonify(user.get_preferences())

@user_bp.route('/user/preferences', methods=['POST'])
@jwt_required
def update_user_preferences():
    """Update current user's preferences"""
    user_id = request.user_id
    data = request.json or {}
    
    if is_production():
        try:
            client = get_supabase_client()
            
            response = client.table("user_profiles") \
                .select("preferences") \
                .eq("id", user_id) \
                .single() \
                .execute()
            
            if not response.data:
                return jsonify({"error": "User not found"}), 404
            
            prefs_str = response.data.get('preferences', '{}')
            try:
                current_prefs = json.loads(prefs_str) if prefs_str else {}
            except json.JSONDecodeError:
                current_prefs = {}
            
            current_prefs.update(data)
            
            update_response = client.table("user_profiles") \
                .update({"preferences": json.dumps(current_prefs)}) \
                .eq("id", user_id) \
                .execute()
            
            return jsonify(current_prefs)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        user = User.query.get_or_404(user_id)
        current_prefs = user.get_preferences()
        current_prefs.update(data)
        user.set_preferences(current_prefs)
        db.session.commit()
        return jsonify(user.get_preferences())
