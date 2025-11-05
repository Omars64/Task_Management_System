from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta

from models import db, Reminder, User, Task
from auth import get_current_user
from notifications import create_notification_with_email
from validators import validator, ValidationError

reminders_bp = Blueprint('reminders', __name__)


@reminders_bp.route('/', methods=['GET'])
@jwt_required()
def get_reminders():
    """Get all reminders for current user"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'Unauthorized'}), 401

        reminders = Reminder.query.filter_by(user_id=current_user.id).order_by(Reminder.reminder_date.asc()).all()
        return jsonify([r.to_dict() for r in reminders]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@reminders_bp.route('/', methods=['POST'])
@jwt_required()
def create_reminder():
    """Create a new reminder"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'Unauthorized'}), 401

        payload = request.get_json(silent=True) or {}
        
        # Validate required fields
        title = payload.get('title', '').strip()
        if not title:
            return jsonify({'error': 'Title is required'}), 400

        reminder_type = payload.get('reminder_type', 'custom')
        reminder_date_str = payload.get('reminder_date')
        task_id = payload.get('task_id')
        days_before = payload.get('days_before')
        time_based = payload.get('time_based')
        reminder_date = None

        # Validate task_id if provided
        if task_id:
            task = Task.query.get(task_id)
            if not task:
                return jsonify({'error': 'Task not found'}), 404
            # Verify user has access to this task (assigned to them OR has TASKS_READ permission OR is in the same project)
            from permissions import Permission
            from models import ProjectMember
            has_access = (
                task.assigned_to == current_user.id or
                current_user.has_permission(Permission.TASKS_READ) or
                (task.project_id and ProjectMember.query.filter_by(project_id=task.project_id, user_id=current_user.id).first())
            )
            if not has_access:
                return jsonify({'error': 'Access denied. You do not have access to this task.'}), 403

        # Calculate reminder_date based on type
        if reminder_type == 'custom':
            if not reminder_date_str:
                return jsonify({'error': 'Reminder date is required for custom type'}), 400
            try:
                reminder_date = datetime.fromisoformat(reminder_date_str.replace('Z', '+00:00'))
            except Exception:
                return jsonify({'error': 'Invalid reminder date format. Use ISO 8601 format.'}), 400
        elif reminder_type == 'days_before' and task_id and days_before:
            if not task or not task.due_date:
                return jsonify({'error': 'Task must have a due date for days_before reminder'}), 400
            reminder_date = task.due_date - timedelta(days=int(days_before))
        elif reminder_type == 'time_based' and time_based:
            try:
                reminder_date = datetime.fromisoformat(time_based.replace('Z', '+00:00'))
            except Exception:
                return jsonify({'error': 'Invalid time_based format'}), 400
        elif reminder_type == 'task_deadline' and task_id:
            if not task or not task.due_date:
                return jsonify({'error': 'Task must have a due date'}), 400
            reminder_date = task.due_date
        else:
            return jsonify({'error': 'Invalid reminder type or missing required fields'}), 400

        # Validate reminder_date is set
        if reminder_date is None:
            return jsonify({'error': 'Reminder date could not be determined'}), 400

        # Parse time_based safely
        time_based_dt = None
        if time_based:
            try:
                time_based_dt = datetime.fromisoformat(time_based.replace('Z', '+00:00'))
            except Exception:
                pass  # Ignore invalid time_based if provided

        reminder = Reminder(
            user_id=current_user.id,
            task_id=task_id if task_id else None,
            title=title,
            description=payload.get('description', '').strip(),
            reminder_date=reminder_date,
            reminder_type=reminder_type,
            days_before=int(days_before) if days_before else None,
            time_based=time_based_dt,
            is_sent=False
        )
        
        db.session.add(reminder)
        db.session.commit()
        
        return jsonify({'message': 'Reminder created successfully', 'reminder': reminder.to_dict()}), 201

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': 'Database error occurred.'}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@reminders_bp.route('/<int:reminder_id>', methods=['PUT'])
@jwt_required()
def update_reminder(reminder_id):
    """Update a reminder"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'Unauthorized'}), 401

        reminder = Reminder.query.get(reminder_id)
        if not reminder:
            return jsonify({'error': 'Reminder not found'}), 404

        if reminder.user_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403

        payload = request.get_json(silent=True) or {}
        
        if 'title' in payload:
            reminder.title = payload['title'].strip()
        if 'description' in payload:
            reminder.description = payload['description'].strip()
        if 'reminder_date' in payload:
            try:
                reminder.reminder_date = datetime.fromisoformat(payload['reminder_date'].replace('Z', '+00:00'))
            except Exception:
                return jsonify({'error': 'Invalid date format'}), 400
        if 'reminder_type' in payload:
            reminder.reminder_type = payload['reminder_type']
        if 'days_before' in payload:
            reminder.days_before = payload['days_before']
        if 'time_based' in payload:
            try:
                reminder.time_based = datetime.fromisoformat(payload['time_based'].replace('Z', '+00:00'))
            except Exception:
                pass

        db.session.commit()
        return jsonify({'message': 'Reminder updated successfully', 'reminder': reminder.to_dict()}), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': 'Database error occurred.'}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@reminders_bp.route('/<int:reminder_id>', methods=['DELETE'])
@jwt_required()
def delete_reminder(reminder_id):
    """Delete a reminder"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'Unauthorized'}), 401

        reminder = Reminder.query.get(reminder_id)
        if not reminder:
            return jsonify({'error': 'Reminder not found'}), 404

        if reminder.user_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403

        db.session.delete(reminder)
        db.session.commit()
        return jsonify({'message': 'Reminder deleted successfully'}), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': 'Database error occurred.'}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

