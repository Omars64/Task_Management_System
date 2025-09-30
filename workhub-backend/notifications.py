from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Notification

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/', methods=['GET'])
@jwt_required()
def get_notifications():
    try:
        current_user_id = get_jwt_identity()
        
        # Get query parameters
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        limit = request.args.get('limit', type=int)
        
        query = Notification.query.filter_by(user_id=current_user_id)
        
        if unread_only:
            query = query.filter_by(is_read=False)
        
        query = query.order_by(Notification.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        notifications = query.all()
        
        return jsonify([notification.to_dict() for notification in notifications]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@notifications_bp.route('/unread-count', methods=['GET'])
@jwt_required()
def get_unread_count():
    try:
        current_user_id = get_jwt_identity()
        
        count = Notification.query.filter_by(
            user_id=current_user_id,
            is_read=False
        ).count()
        
        return jsonify({'unread_count': count}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@notifications_bp.route('/<int:notification_id>/read', methods=['PUT'])
@jwt_required()
def mark_as_read(notification_id):
    try:
        current_user_id = get_jwt_identity()
        
        notification = Notification.query.get(notification_id)
        
        if not notification:
            return jsonify({'error': 'Notification not found'}), 404
        
        if notification.user_id != current_user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        notification.is_read = True
        db.session.commit()
        
        return jsonify({
            'message': 'Notification marked as read',
            'notification': notification.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@notifications_bp.route('/mark-all-read', methods=['PUT'])
@jwt_required()
def mark_all_as_read():
    try:
        current_user_id = get_jwt_identity()
        
        Notification.query.filter_by(
            user_id=current_user_id,
            is_read=False
        ).update({'is_read': True})
        
        db.session.commit()
        
        return jsonify({'message': 'All notifications marked as read'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@notifications_bp.route('/<int:notification_id>', methods=['DELETE'])
@jwt_required()
def delete_notification(notification_id):
    try:
        current_user_id = get_jwt_identity()
        
        notification = Notification.query.get(notification_id)
        
        if not notification:
            return jsonify({'error': 'Notification not found'}), 404
        
        if notification.user_id != current_user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        db.session.delete(notification)
        db.session.commit()
        
        return jsonify({'message': 'Notification deleted'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@notifications_bp.route('/clear-all', methods=['DELETE'])
@jwt_required()
def clear_all_notifications():
    try:
        current_user_id = get_jwt_identity()
        
        Notification.query.filter_by(user_id=current_user_id).delete()
        db.session.commit()
        
        return jsonify({'message': 'All notifications cleared'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500