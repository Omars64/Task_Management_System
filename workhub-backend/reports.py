from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Task, User, TimeLog
from datetime import datetime, timedelta
from auth import admin_required
import pandas as pd
import io
from sqlalchemy import func

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/personal/task-status', methods=['GET'])
@jwt_required()
def personal_task_status():
    try:
        current_user_id = get_jwt_identity()
        
        # Count tasks by status
        tasks = Task.query.filter_by(assigned_to=current_user_id).all()
        
        status_counts = {
            'todo': 0,
            'in_progress': 0,
            'completed': 0,
            'total': len(tasks)
        }
        
        for task in tasks:
            if task.status in status_counts:
                status_counts[task.status] += 1
        
        # Priority breakdown
        priority_counts = {'low': 0, 'medium': 0, 'high': 0}
        for task in tasks:
            if task.priority in priority_counts:
                priority_counts[task.priority] += 1
        
        return jsonify({
            'status_counts': status_counts,
            'priority_counts': priority_counts,
            'tasks': [task.to_dict() for task in tasks]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/personal/time-logs', methods=['GET'])
@jwt_required()
def personal_time_logs():
    try:
        current_user_id = get_jwt_identity()
        
        # Get date range from query params
        days = request.args.get('days', 30, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        time_logs = TimeLog.query.filter(
            TimeLog.user_id == current_user_id,
            TimeLog.logged_at >= start_date
        ).order_by(TimeLog.logged_at.desc()).all()
        
        total_hours = sum(log.hours for log in time_logs)
        
        return jsonify({
            'time_logs': [log.to_dict() for log in time_logs],
            'total_hours': total_hours,
            'period_days': days
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/personal/activity', methods=['GET'])
@jwt_required()
def personal_activity():
    try:
        current_user_id = get_jwt_identity()
        
        # Get tasks created in last 30 days
        days = request.args.get('days', 30, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        tasks = Task.query.filter(
            Task.assigned_to == current_user_id,
            Task.created_at >= start_date
        ).order_by(Task.created_at.desc()).all()
        
        completed_tasks = [t for t in tasks if t.status == 'completed']
        
        return jsonify({
            'total_tasks': len(tasks),
            'completed_tasks': len(completed_tasks),
            'pending_tasks': len(tasks) - len(completed_tasks),
            'completion_rate': (len(completed_tasks) / len(tasks) * 100) if tasks else 0,
            'recent_tasks': [task.to_dict() for task in tasks[:10]]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/admin/overview', methods=['GET'])
@admin_required
def admin_overview():
    try:
        # Get all tasks
        all_tasks = Task.query.all()
        
        # Status counts
        status_counts = {
            'todo': 0,
            'in_progress': 0,
            'completed': 0,
            'total': len(all_tasks)
        }
        
        for task in all_tasks:
            if task.status in status_counts:
                status_counts[task.status] += 1
        
        # Priority counts
        priority_counts = {'low': 0, 'medium': 0, 'high': 0}
        for task in all_tasks:
            if task.priority in priority_counts:
                priority_counts[task.priority] += 1
        
        # User stats
        total_users = User.query.count()
        admin_count = User.query.filter_by(role='admin').count()
        user_count = User.query.filter_by(role='user').count()
        
        # Tasks by user
        user_task_counts = db.session.query(
            User.id,
            User.name,
            func.count(Task.id).label('task_count')
        ).outerjoin(Task, User.id == Task.assigned_to).group_by(User.id).all()
        
        user_stats = [
            {'user_id': u.id, 'user_name': u.name, 'task_count': u.task_count}
            for u in user_task_counts
        ]
        
        return jsonify({
            'status_counts': status_counts,
            'priority_counts': priority_counts,
            'user_stats': {
                'total': total_users,
                'admins': admin_count,
                'users': user_count
            },
            'tasks_by_user': user_stats
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/admin/sprint-summary', methods=['GET'])
@admin_required
def sprint_summary():
    try:
        # Get date range
        days = request.args.get('days', 14, type=int)  # Default 2-week sprint
        start_date = datetime.utcnow() - timedelta(days=days)
        
        tasks = Task.query.filter(Task.created_at >= start_date).all()
        
        completed_in_sprint = [t for t in tasks if t.status == 'completed']
        in_progress = [t for t in tasks if t.status == 'in_progress']
        todo = [t for t in tasks if t.status == 'todo']
        
        return jsonify({
            'sprint_days': days,
            'start_date': start_date.isoformat(),
            'total_tasks': len(tasks),
            'completed': len(completed_in_sprint),
            'in_progress': len(in_progress),
            'todo': len(todo),
            'completion_rate': (len(completed_in_sprint) / len(tasks) * 100) if tasks else 0,
            'tasks': [task.to_dict() for task in tasks]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/export/csv', methods=['POST'])
@jwt_required()
def export_to_csv():
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        data = request.get_json()
        report_type = data.get('report_type', 'tasks')
        
        if current_user.role == 'admin':
            tasks = Task.query.all()
        else:
            tasks = Task.query.filter_by(assigned_to=current_user_id).all()
        
        # Convert tasks to DataFrame
        task_data = []
        for task in tasks:
            task_data.append({
                'ID': task.id,
                'Title': task.title,
                'Description': task.description,
                'Status': task.status,
                'Priority': task.priority,
                'Assigned To': task.assignee.name if task.assignee else 'Unassigned',
                'Created By': task.creator.name if task.creator else 'Unknown',
                'Due Date': task.due_date.strftime('%Y-%m-%d') if task.due_date else '',
                'Created At': task.created_at.strftime('%Y-%m-%d %H:%M') if task.created_at else '',
                'Completed At': task.completed_at.strftime('%Y-%m-%d %H:%M') if task.completed_at else ''
            })
        
        df = pd.DataFrame(task_data)
        
        # Create CSV in memory
        output = io.BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)
        
        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'tasks_report_{datetime.utcnow().strftime("%Y%m%d")}.csv'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500