from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Notification, NotificationPreference, User, Task, Comment, ChatConversation, Project, ProjectMember
from email_service import email_service
from permissions import Permission
import logging
import threading
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

notifications_bp = Blueprint('notifications', __name__)


def create_notification(user_id, title, message, notif_type, related_task_id=None, related_conversation_id=None, send_email=True):
    """
    Helper function to create a notification (simplified version without email)
    
    Args:
        user_id: ID of the user to notify
        title: Notification title
        message: Notification message
        notif_type: Type of notification
        related_task_id: Optional task ID
        related_conversation_id: Optional conversation ID
        send_email: Whether to also send email notification
    
    Returns:
        Notification object
    """
    try:
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=notif_type,
            related_task_id=related_task_id,
            related_conversation_id=related_conversation_id
        )
        db.session.add(notification)
        db.session.commit()
        return notification
    except Exception as e:
        logger.error(f"Error creating notification: {str(e)}")
        db.session.rollback()
        return None


def create_notification_with_email(user_id, title, message, notif_type, related_task_id=None, related_conversation_id=None, send_email=True):
    """
    Helper function to create a notification and optionally send an email
    
    Args:
        user_id: ID of the user to notify
        title: Notification title
        message: Notification message
        notif_type: Type of notification ('task_assigned', 'task_updated', 'comment', etc.)
        related_task_id: Optional task ID
        send_email: Whether to also send email notification
    
    Returns:
        Notification object
    """
    try:
        # Create in-app notification
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=notif_type,
            related_task_id=related_task_id,
            related_conversation_id=related_conversation_id
        )
        db.session.add(notification)
        db.session.commit()
        
        # Check if email notification should be sent
        if send_email and email_service.enabled:
            # Get user preferences
            prefs = NotificationPreference.query.filter_by(user_id=user_id).first()
            if not prefs:
                # Create default preferences if they don't exist
                prefs = NotificationPreference(user_id=user_id)
                db.session.add(prefs)
                db.session.commit()
            
            # Check if user wants email for this notification type
            email_pref_field = f"email_{notif_type}"
            if hasattr(prefs, email_pref_field) and getattr(prefs, email_pref_field):
                # Get user email
                user = User.query.get(user_id)
                if user and user.email:
                    # Get task data if task ID provided
                    task_data = {}
                    if related_task_id:
                        task = Task.query.get(related_task_id)
                        if task:
                            base_url = current_app.config.get('FRONTEND_URL', 'http://localhost:5173')
                            # Safely access task attributes to prevent AttributeError
                            task_data = {
                                'title': task.title if hasattr(task, 'title') else 'Unknown Task',
                                'description': getattr(task, 'description', '') or 'No description',
                                'priority': task.priority if hasattr(task, 'priority') else 'medium',
                                'status': task.status if hasattr(task, 'status') else 'todo',
                                'due_date': task.due_date.strftime('%Y-%m-%d %H:%M') if (hasattr(task, 'due_date') and task.due_date) else 'Not set',
                                'task_url': f"{base_url}/tasks?taskId={task.id if hasattr(task, 'id') else related_task_id}"
                            }
                    
                    # Send email in background thread to avoid blocking the API response
                    def send_email_async():
                        try:
                            # Send appropriate email based on notification type
                            if notif_type == 'task_assigned' and task_data:
                                email_service.send_task_assigned(user.email, task_data)
                            elif notif_type == 'task_updated' and task_data:
                                # Extract changes from message (simplified)
                                email_service.send_task_updated(user.email, task_data, {})
                            elif notif_type == 'comment' and task_data:
                                # Extract comment data from message
                                comment_data = {'author_name': 'A user', 'content': message}
                                email_service.send_comment_notification(user.email, task_data, comment_data)
                            elif notif_type == 'task_due_soon' and task_data:
                                email_service.send_task_due_soon(user.email, task_data)
                            elif notif_type == 'task_overdue' and task_data:
                                email_service.send_task_overdue(user.email, task_data)
                            elif notif_type in ('meeting_invitation', 'meeting_response'):
                                # Meeting notifications - message contains the meeting info
                                email_service.send_generic_notification(
                                    user.email, 
                                    title, 
                                    message
                                )
                        except Exception as e:
                            logger.error(f"Error sending email in background: {str(e)}")
                    
                    # Start email sending in background thread
                    thread = threading.Thread(target=send_email_async, daemon=True)
                    thread.start()
        
        return notification
    
    except Exception as e:
        logger.error(f"Error creating notification with email: {str(e)}")
        db.session.rollback()
        return None

@notifications_bp.route('/', methods=['GET'])
@jwt_required()
def get_notifications():
    try:
        current_user_id = int(get_jwt_identity())
        
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
        current_user_id = int(get_jwt_identity())
        
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
        current_user_id = int(get_jwt_identity())
        
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
        current_user_id = int(get_jwt_identity())
        
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
        current_user_id = int(get_jwt_identity())
        
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
        current_user_id = int(get_jwt_identity())
        
        Notification.query.filter_by(user_id=current_user_id).delete()
        db.session.commit()
        
        return jsonify({'message': 'All notifications cleared'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@notifications_bp.route('/project-activity', methods=['GET'])
@jwt_required()
def get_project_activity():
    """Return recent activity for a project by correlating notifications with task's project_id"""
    try:
        project_id = request.args.get('project_id', type=int)
        limit = request.args.get('limit', default=50, type=int)
        if not project_id:
            return jsonify({'error': 'project_id is required'}), 400

        # Join notifications -> tasks on related_task_id and filter by project_id
        rows = (
            db.session.query(Notification, Task)
            .join(Task, Notification.related_task_id == Task.id)
            .filter(Task.project_id == project_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
            .all()
        )

        result = []
        for n, t in rows:
            # Safely access task attributes to prevent AttributeError
            task_data = {}
            if t:
                task_data = {
                    'task_id': t.id if hasattr(t, 'id') else None,
                    'task_title': t.title if hasattr(t, 'title') else None,
                    'task_status': t.status if hasattr(t, 'status') else None,
                    'task_priority': t.priority if hasattr(t, 'priority') else None,
                }
            
            result.append({
                'id': n.id if hasattr(n, 'id') else None,
                'type': n.type if hasattr(n, 'type') else None,
                'title': n.title if hasattr(n, 'title') else None,
                'message': n.message if hasattr(n, 'message') else None,
                'created_at': n.created_at.isoformat() if (hasattr(n, 'created_at') and n.created_at) else None,
                **task_data
            })

        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@notifications_bp.route('/preferences', methods=['GET'])
@jwt_required()
def get_notification_preferences():
    """Get user's notification preferences"""
    try:
        current_user_id = int(get_jwt_identity())
        
        prefs = NotificationPreference.query.filter_by(user_id=current_user_id).first()
        
        if not prefs:
            # Create default preferences if they don't exist
            prefs = NotificationPreference(user_id=current_user_id)
            db.session.add(prefs)
            db.session.commit()
        
        return jsonify(prefs.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@notifications_bp.route('/preferences', methods=['PUT'])
@jwt_required()
def update_notification_preferences():
    """Update user's notification preferences"""
    try:
        current_user_id = int(get_jwt_identity())
        data = request.get_json()
        
        prefs = NotificationPreference.query.filter_by(user_id=current_user_id).first()
        
        if not prefs:
            prefs = NotificationPreference(user_id=current_user_id)
            db.session.add(prefs)
        
        # Update email notification preferences
        if 'email_task_assigned' in data:
            prefs.email_task_assigned = data['email_task_assigned']
        if 'email_task_updated' in data:
            prefs.email_task_updated = data['email_task_updated']
        if 'email_task_commented' in data:
            prefs.email_task_commented = data['email_task_commented']
        if 'email_task_due_soon' in data:
            prefs.email_task_due_soon = data['email_task_due_soon']
        if 'email_task_overdue' in data:
            prefs.email_task_overdue = data['email_task_overdue']
        
        # Update in-app notification preferences
        if 'inapp_task_assigned' in data:
            prefs.inapp_task_assigned = data['inapp_task_assigned']
        if 'inapp_task_updated' in data:
            prefs.inapp_task_updated = data['inapp_task_updated']
        if 'inapp_task_commented' in data:
            prefs.inapp_task_commented = data['inapp_task_commented']
        if 'inapp_task_due_soon' in data:
            prefs.inapp_task_due_soon = data['inapp_task_due_soon']
        if 'inapp_task_overdue' in data:
            prefs.inapp_task_overdue = data['inapp_task_overdue']
        
        # Update digest settings
        if 'daily_digest' in data:
            prefs.daily_digest = data['daily_digest']
        if 'weekly_digest' in data:
            prefs.weekly_digest = data['weekly_digest']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Notification preferences updated successfully',
            'preferences': prefs.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@notifications_bp.route('/<int:notification_id>/resolve', methods=['POST'])
@jwt_required()
def resolve_notification(notification_id):
    """
    Resolve a notification: mark as read, verify access, and return redirect URL
    
    Returns:
        {
            "redirect_url": "/tasks/123?origin=notif&notifId=456&tab=activity&commentId=789",
            "error": null
        }
        OR
        {
            "redirect_url": null,
            "error": "Task not found or access denied"
        }
    """
    try:
        current_user_id = int(get_jwt_identity())
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return jsonify({'error': 'User not found', 'redirect_url': None}), 404
        
        # Get notification
        notification = Notification.query.get(notification_id)
        if not notification:
            return jsonify({'error': 'Notification not found', 'redirect_url': None}), 404
        
        # Verify notification belongs to current user
        if notification.user_id != current_user_id:
            return jsonify({'error': 'Access denied', 'redirect_url': None}), 403
        
        # Mark as read
        notification.is_read = True
        db.session.commit()
        
        # Build redirect URL based on notification type
        redirect_url = None
        error = None
        
        # Task-related notifications
        if notification.related_task_id:
            task = Task.query.get(notification.related_task_id)
            if not task:
                error = 'Task not found'
            else:
                # Check access: user has TASKS_READ permission OR is assignee
                has_access = (
                    current_user.has_permission(Permission.TASKS_READ) or 
                    task.assigned_to == current_user_id
                )
                
                # Also check if user is project member (for managers/team leads)
                if not has_access and task.project_id:
                    role = (current_user.role or 'viewer').lower()
                    if role in ('manager', 'team_lead'):
                        is_member = ProjectMember.query.filter_by(
                            project_id=task.project_id, 
                            user_id=current_user_id
                        ).first() is not None
                        if is_member:
                            has_access = True
                
                if not has_access:
                    error = 'Access denied to this task'
                else:
                    # Build URL with query parameters
                    params = {
                        'origin': 'notif',
                        'notifId': str(notification_id)
                    }
                    
                    # For comment notifications, add tab and commentId
                    if notification.type == 'comment':
                        params['tab'] = 'activity'
                        # Try to find the most recent comment for this task
                        # (We don't store comment_id in notification yet, so use latest)
                        comment = Comment.query.filter_by(task_id=task.id).order_by(Comment.created_at.desc()).first()
                        if comment:
                            params['commentId'] = str(comment.id)
                    
                    query_string = urlencode(params)
                    redirect_url = f"/tasks?taskId={task.id}&{query_string}"
        
        # Chat-related notifications
        elif notification.related_conversation_id:
            conversation = ChatConversation.query.get(notification.related_conversation_id)
            if not conversation:
                error = 'Conversation not found'
            else:
                # Verify user is part of conversation
                if conversation.user1_id != current_user_id and conversation.user2_id != current_user_id:
                    error = 'Access denied to this conversation'
                else:
                    params = {
                        'origin': 'notif',
                        'notifId': str(notification_id)
                    }
                    query_string = urlencode(params)
                    redirect_url = f"/chat?conversationId={conversation.id}&{query_string}"
        
        # Project-related notifications (if we add project_id to notifications later)
        # For now, project notifications might be linked via task.project_id
        
        # Meeting-related notifications (if we add meeting_id to notifications later)
        
        # If no redirect URL could be determined, return error
        if not redirect_url:
            if not error:
                error = 'No valid target found for this notification'
            return jsonify({
                'error': error,
                'redirect_url': None
            }), 404
        
        return jsonify({
            'redirect_url': redirect_url,
            'error': None
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error resolving notification {notification_id}: {str(e)}")
        return jsonify({
            'error': f'Failed to resolve notification: {str(e)}',
            'redirect_url': None
        }), 500