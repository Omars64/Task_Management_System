from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Task, User, Notification, Comment, TimeLog
from datetime import datetime
from auth import admin_required
from email_service import send_notification_email

tasks_bp = Blueprint('tasks', __name__)

def create_notification(user_id, title, message, notification_type, task_id=None):
    """Helper function to create notifications"""
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=notification_type,
        related_task_id=task_id
    )
    db.session.add(notification)
    
    # Send email notification if user has email notifications enabled
    user = User.query.get(user_id)
    if user and user.notifications_enabled:
        task_title = None
        if task_id:
            task = Task.query.get(task_id)
            if task:
                task_title = task.title
        
        send_notification_email(
            user.email,
            user.name,
            title,
            message,
            task_title
        )

@tasks_bp.route('/', methods=['GET'])
@jwt_required()
def get_tasks():
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        # Get query parameters for filtering
        status = request.args.get('status')
        priority = request.args.get('priority')
        assigned_to = request.args.get('assigned_to')
        search = request.args.get('search')
        
        # Base query
        if current_user.role == 'admin':
            query = Task.query
        else:
            # Regular users only see their assigned tasks
            query = Task.query.filter_by(assigned_to=current_user_id)
        
        # Apply filters
        if status:
            query = query.filter_by(status=status)
        if priority:
            query = query.filter_by(priority=priority)
        if assigned_to and current_user.role == 'admin':
            query = query.filter_by(assigned_to=int(assigned_to))
        if search:
            query = query.filter(
                db.or_(
                    Task.title.contains(search),
                    Task.description.contains(search)
                )
            )
        
        tasks = query.order_by(Task.created_at.desc()).all()
        
        return jsonify([task.to_dict() for task in tasks]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@tasks_bp.route('/<int:task_id>', methods=['GET'])
@jwt_required()
def get_task(task_id):
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        task = Task.query.get(task_id)
        
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        # Check access
        if current_user.role != 'admin' and task.assigned_to != current_user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        task_dict = task.to_dict()
        
        # Include comments
        comments = [comment.to_dict() for comment in task.comments]
        task_dict['comments'] = comments
        
        # Include time logs
        time_logs = [log.to_dict() for log in task.time_logs]
        task_dict['time_logs'] = time_logs
        
        return jsonify(task_dict), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@tasks_bp.route('/', methods=['POST'])
@admin_required
def create_task():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data.get('title'):
            return jsonify({'error': 'Title is required'}), 400
        
        task = Task(
            title=data['title'],
            description=data.get('description', ''),
            priority=data.get('priority', 'medium'),
            status=data.get('status', 'todo'),
            assigned_to=data.get('assigned_to'),
            created_by=current_user_id
        )
        
        if data.get('due_date'):
            try:
                task.due_date = datetime.fromisoformat(data['due_date'].replace('Z', '+00:00'))
            except:
                return jsonify({'error': 'Invalid due_date format'}), 400
        
        db.session.add(task)
        db.session.flush()
        
        # Create notification for assigned user
        if task.assigned_to:
            create_notification(
                task.assigned_to,
                'New Task Assigned',
                f'You have been assigned a new task: {task.title}',
                'task_assigned',
                task.id
            )
        
        db.session.commit()
        
        return jsonify({
            'message': 'Task created successfully',
            'task': task.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@tasks_bp.route('/<int:task_id>', methods=['PUT'])
@jwt_required()
def update_task(task_id):
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        task = Task.query.get(task_id)
        
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        data = request.get_json()
        
        # Check permissions
        is_admin = current_user.role == 'admin'
        is_assignee = task.assigned_to == current_user_id
        
        if not is_admin and not is_assignee:
            return jsonify({'error': 'Access denied'}), 403
        
        # Track if status changed to completed
        old_status = task.status
        
        # Update fields - admins can update everything, users can only update status
        if is_admin:
            if 'title' in data:
                task.title = data['title']
            if 'description' in data:
                task.description = data['description']
            if 'priority' in data:
                task.priority = data['priority']
            if 'assigned_to' in data:
                old_assignee = task.assigned_to
                task.assigned_to = data['assigned_to']
                
                # Notify new assignee if changed
                if old_assignee != task.assigned_to and task.assigned_to:
                    create_notification(
                        task.assigned_to,
                        'Task Assigned',
                        f'You have been assigned to task: {task.title}',
                        'task_assigned',
                        task.id
                    )
            if 'due_date' in data:
                if data['due_date']:
                    try:
                        task.due_date = datetime.fromisoformat(data['due_date'].replace('Z', '+00:00'))
                    except:
                        return jsonify({'error': 'Invalid due_date format'}), 400
                else:
                    task.due_date = None
        
        # Both admin and assignee can update status
        if 'status' in data:
            task.status = data['status']
            
            # Set completion time
            if task.status == 'completed' and old_status != 'completed':
                task.completed_at = datetime.utcnow()
                
                # Notify creator
                if task.created_by and task.created_by != current_user_id:
                    create_notification(
                        task.created_by,
                        'Task Completed',
                        f'Task "{task.title}" has been completed',
                        'task_updated',
                        task.id
                    )
            elif task.status != 'completed' and old_status == 'completed':
                task.completed_at = None
        
        task.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Task updated successfully',
            'task': task.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@tasks_bp.route('/<int:task_id>', methods=['DELETE'])
@admin_required
def delete_task(task_id):
    try:
        task = Task.query.get(task_id)
        
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        db.session.delete(task)
        db.session.commit()
        
        return jsonify({'message': 'Task deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@tasks_bp.route('/<int:task_id>/comments', methods=['POST'])
@jwt_required()
def add_comment(task_id):
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        task = Task.query.get(task_id)
        
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        # Check access
        if current_user.role != 'admin' and task.assigned_to != current_user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        data = request.get_json()
        
        if not data.get('content'):
            return jsonify({'error': 'Comment content is required'}), 400
        
        comment = Comment(
            task_id=task_id,
            user_id=current_user_id,
            content=data['content']
        )
        
        db.session.add(comment)
        
        # Notify assignee and creator (if different from commenter)
        notification_users = set()
        if task.assigned_to and task.assigned_to != current_user_id:
            notification_users.add(task.assigned_to)
        if task.created_by and task.created_by != current_user_id:
            notification_users.add(task.created_by)
        
        for user_id in notification_users:
            create_notification(
                user_id,
                'New Comment',
                f'{current_user.name} commented on task: {task.title}',
                'comment',
                task.id
            )
        
        db.session.commit()
        
        return jsonify({
            'message': 'Comment added successfully',
            'comment': comment.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@tasks_bp.route('/<int:task_id>/time-logs', methods=['POST'])
@jwt_required()
def add_time_log(task_id):
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        task = Task.query.get(task_id)
        
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        # Check access
        if current_user.role != 'admin' and task.assigned_to != current_user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        data = request.get_json()
        
        if not data.get('hours') or data.get('hours') <= 0:
            return jsonify({'error': 'Valid hours are required'}), 400
        
        time_log = TimeLog(
            task_id=task_id,
            user_id=current_user_id,
            hours=data['hours'],
            description=data.get('description', '')
        )
        
        db.session.add(time_log)
        db.session.commit()
        
        return jsonify({
            'message': 'Time logged successfully',
            'time_log': time_log.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@tasks_bp.route('/<int:task_id>/time-logs', methods=['GET'])
@jwt_required()
def get_time_logs(task_id):
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        task = Task.query.get(task_id)
        
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        # Check access
        if current_user.role != 'admin' and task.assigned_to != current_user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        time_logs = TimeLog.query.filter_by(task_id=task_id).order_by(TimeLog.logged_at.desc()).all()
        
        return jsonify([log.to_dict() for log in time_logs]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@tasks_bp.route('/time-logs/<int:log_id>', methods=['DELETE'])
@jwt_required()
def delete_time_log(log_id):
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        time_log = TimeLog.query.get(log_id)
        
        if not time_log:
            return jsonify({'error': 'Time log not found'}), 404
        
        # Check access - only the user who created the log or admin can delete
        if current_user.role != 'admin' and time_log.user_id != current_user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        db.session.delete(time_log)
        db.session.commit()
        
        return jsonify({'message': 'Time log deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500