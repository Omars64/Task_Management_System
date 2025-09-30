from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User
from auth import admin_required

users_bp = Blueprint('users', __name__)

@users_bp.route('/', methods=['GET'])
@admin_required
def get_users():
    try:
        users = User.query.all()
        return jsonify([user.to_dict() for user in users]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@users_bp.route('/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        # Users can view their own profile or admins can view any profile
        if current_user_id != user_id and current_user.role != 'admin':
            return jsonify({'error': 'Access denied'}), 403
        
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify(user.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@users_bp.route('/', methods=['POST'])
@admin_required
def create_user():
    try:
        data = request.get_json()
        
        if not data.get('email') or not data.get('password') or not data.get('name'):
            return jsonify({'error': 'Email, password, and name are required'}), 400
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already registered'}), 400
        
        user = User(
            email=data['email'],
            name=data['name'],
            role=data.get('role', 'user')
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'message': 'User created successfully',
            'user': user.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@users_bp.route('/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        # Only admins can change role or edit other users
        if current_user_id != user_id and current_user.role != 'admin':
            return jsonify({'error': 'Access denied'}), 403
        
        # Update allowed fields
        if 'name' in data:
            user.name = data['name']
        
        if 'email' in data and data['email'] != user.email:
            if User.query.filter_by(email=data['email']).first():
                return jsonify({'error': 'Email already in use'}), 400
            user.email = data['email']
        
        # Only admins can change roles
        if 'role' in data and current_user.role == 'admin':
            user.role = data['role']
        
        # Personal settings
        if 'theme' in data:
            user.theme = data['theme']
        if 'language' in data:
            user.language = data['language']
        if 'notifications_enabled' in data:
            user.notifications_enabled = data['notifications_enabled']
        
        db.session.commit()
        
        return jsonify({
            'message': 'User updated successfully',
            'user': user.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@users_bp.route('/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    try:
        current_user_id = get_jwt_identity()
        
        # Prevent self-deletion
        if current_user_id == user_id:
            return jsonify({'error': 'Cannot delete your own account'}), 400
        
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({'message': 'User deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500