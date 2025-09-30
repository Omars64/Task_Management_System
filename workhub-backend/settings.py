from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, SystemSettings, User
from auth import admin_required

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/system', methods=['GET'])
@jwt_required()
def get_system_settings():
    try:
        settings = SystemSettings.query.first()
        
        if not settings:
            # Create default settings if none exist
            settings = SystemSettings()
            db.session.add(settings)
            db.session.commit()
        
        return jsonify(settings.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/system', methods=['PUT'])
@admin_required
def update_system_settings():
    try:
        settings = SystemSettings.query.first()
        
        if not settings:
            settings = SystemSettings()
            db.session.add(settings)
        
        data = request.get_json()
        
        if 'site_title' in data:
            settings.site_title = data['site_title']
        if 'default_role' in data:
            settings.default_role = data['default_role']
        if 'email_notifications_enabled' in data:
            settings.email_notifications_enabled = data['email_notifications_enabled']
        if 'default_language' in data:
            settings.default_language = data['default_language']
        
        db.session.commit()
        
        return jsonify({
            'message': 'System settings updated successfully',
            'settings': settings.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/personal', methods=['GET'])
@jwt_required()
def get_personal_settings():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'theme': user.theme,
            'language': user.language,
            'notifications_enabled': user.notifications_enabled
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/personal', methods=['PUT'])
@jwt_required()
def update_personal_settings():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        if 'theme' in data:
            user.theme = data['theme']
        if 'language' in data:
            user.language = data['language']
        if 'notifications_enabled' in data:
            user.notifications_enabled = data['notifications_enabled']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Personal settings updated successfully',
            'settings': {
                'theme': user.theme,
                'language': user.language,
                'notifications_enabled': user.notifications_enabled
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500