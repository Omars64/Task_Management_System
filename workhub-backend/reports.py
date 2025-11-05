from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Task, User, TimeLog, Project, Sprint
from datetime import datetime, timedelta
from auth import admin_required, get_current_user
from permissions import Permission
import pandas as pd
import io
from sqlalchemy import func
from io import StringIO

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/personal/task-status', methods=['GET'])
@jwt_required()
def personal_task_status():
    try:
        current_user_id = int(get_jwt_identity())
        
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
        current_user_id = int(get_jwt_identity())
        
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
        current_user_id = int(get_jwt_identity())
        
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
@jwt_required()
def admin_overview():
    try:
        current_user = get_current_user()
        if not current_user or not current_user.has_permission(Permission.REPORTS_VIEW_ALL):
            return jsonify({"error": "Access denied"}), 403
        
        # Optional filters
        project_id = request.args.get('project_id')
        sprint_id = request.args.get('sprint_id')

        query = Task.query
        if project_id:
            try:
                query = query.filter_by(project_id=int(project_id))
            except ValueError:
                return jsonify({'error': 'project_id must be an integer'}), 400
        if sprint_id:
            try:
                query = query.filter_by(sprint_id=int(sprint_id))
            except ValueError:
                return jsonify({'error': 'sprint_id must be an integer'}), 400

        all_tasks = query.all()
        
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
            'filters': {
                'project_id': int(project_id) if project_id else None,
                'sprint_id': int(sprint_id) if sprint_id else None,
            },
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
@jwt_required()
def sprint_summary():
    try:
        current_user = get_current_user()
        if not current_user or not current_user.has_permission(Permission.REPORTS_VIEW_ALL):
            return jsonify({"error": "Access denied"}), 403
        
        # Optional filters: project/sprint override date window
        project_id = request.args.get('project_id')
        sprint_id = request.args.get('sprint_id')
        days = request.args.get('days', 14, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)

        query = Task.query
        if sprint_id:
            try:
                query = query.filter_by(sprint_id=int(sprint_id))
            except ValueError:
                return jsonify({'error': 'sprint_id must be an integer'}), 400
        elif project_id:
            try:
                query = query.filter_by(project_id=int(project_id))
            except ValueError:
                return jsonify({'error': 'project_id must be an integer'}), 400
        else:
            query = query.filter(Task.created_at >= start_date)

        tasks = query.all()
        
        completed_in_sprint = [t for t in tasks if t.status == 'completed']
        in_progress = [t for t in tasks if t.status == 'in_progress']
        todo = [t for t in tasks if t.status == 'todo']
        
        return jsonify({
            'sprint_days': days,
            'start_date': start_date.isoformat(),
            'filters': {
                'project_id': int(project_id) if project_id else None,
                'sprint_id': int(sprint_id) if sprint_id else None,
            },
            'total_tasks': len(tasks),
            'completed': len(completed_in_sprint),
            'in_progress': len(in_progress),
            'todo': len(todo),
            'completion_rate': (len(completed_in_sprint) / len(tasks) * 100) if tasks else 0,
            'tasks': [task.to_dict() for task in tasks]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@reports_bp.route('/admin/sprint-burndown', methods=['GET'])
@jwt_required()
def sprint_burndown():
    try:
        current_user = get_current_user()
        if not current_user or not current_user.has_permission(Permission.REPORTS_VIEW_ALL):
            return jsonify({"error": "Access denied"}), 403

        project_id = request.args.get('project_id', type=int)
        sprint_id = request.args.get('sprint_id', type=int)
        days = request.args.get('days', 14, type=int)

        # Establish time window
        if sprint_id:
            sprint = Sprint.query.get(sprint_id)
            if not sprint:
                return jsonify({'error': 'Sprint not found'}), 404
            start_date = sprint.start_date
            end_date = sprint.end_date
        else:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)

        # Scope tasks
        query = Task.query
        if sprint_id:
            query = query.filter(Task.sprint_id == sprint_id)
        elif project_id:
            query = query.filter(Task.project_id == project_id)
        else:
            query = query.filter(Task.created_at >= start_date)

        tasks = query.all()
        total = len(tasks)

        # Build burndown points per day
        points = []
        d = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        final_day = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
        while d <= final_day:
            completed_by_day = 0
            for t in tasks:
                if t.completed_at and t.completed_at <= d + timedelta(days=1):
                    completed_by_day += 1
            remaining = max(0, total - completed_by_day)
            points.append({
                'date': d.date().isoformat(),
                'remaining': remaining,
                'completed': completed_by_day
            })
            d += timedelta(days=1)

        return jsonify({
            'total_tasks': total,
            'start_date': start_date.isoformat() if start_date else None,
            'end_date': end_date.isoformat() if end_date else None,
            'points': points
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@reports_bp.route('/admin/sprint-velocity', methods=['GET'])
@jwt_required()
def sprint_velocity():
    try:
        current_user = get_current_user()
        if not current_user or not current_user.has_permission(Permission.REPORTS_VIEW_ALL):
            return jsonify({"error": "Access denied"}), 403

        project_id = request.args.get('project_id', type=int)
        sprint_id = request.args.get('sprint_id', type=int)
        weeks = request.args.get('weeks', 4, type=int)

        end = datetime.utcnow()
        start = end - timedelta(days=weeks * 7)

        query = Task.query.filter(Task.completed_at.isnot(None), Task.completed_at >= start, Task.completed_at <= end)
        if sprint_id:
            query = query.filter(Task.sprint_id == sprint_id)
        elif project_id:
            query = query.filter(Task.project_id == project_id)

        tasks = query.all()

        # Aggregate per week number (ISO week)
        weekly = {}
        for t in tasks:
            wk = t.completed_at.isocalendar()[:2]  # (year, week)
            weekly[wk] = weekly.get(wk, 0) + 1

        series = []
        # Build contiguous week series from start to end
        cursor = start
        while cursor <= end:
            iso = cursor.isocalendar()
            key = (iso[0], iso[1])
            series.append({
                'year': key[0],
                'week': key[1],
                'completed': weekly.get(key, 0)
            })
            cursor += timedelta(days=7)

        avg = (sum(v['completed'] for v in series) / len(series)) if series else 0

        return jsonify({
            'weeks': weeks,
            'start_date': start.isoformat(),
            'end_date': end.isoformat(),
            'weekly': series,
            'average_completed_per_week': avg
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/export/csv', methods=['POST'])
@jwt_required()
def export_to_csv():
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({"error": "User not found"}), 404
        
        data = request.get_json()
        report_type = data.get('report_type', 'tasks')
        
        # Check if user can export reports
        can_export = current_user.has_permission(Permission.REPORTS_EXPORT)
        can_view_all = current_user.has_permission(Permission.REPORTS_VIEW_ALL)
        
        if not can_export:
            return jsonify({"error": "Access denied - export permission required"}), 403
        
        # Users with REPORTS_VIEW_ALL can export all tasks, others export only their own
        if can_view_all:
            tasks = Task.query.all()
        else:
            tasks = Task.query.filter_by(assigned_to=current_user.id).all()
        
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


@reports_bp.route('/export/period', methods=['GET'])
@jwt_required()
def export_by_period():
    """Export tasks grouped by day/month or raw for a custom range as CSV.
    Query params: period=daily|monthly|custom, start_date, end_date, project_id?, sprint_id?
    """
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({"error": "User not found"}), 404

        period = request.args.get('period', 'daily')
        project_id = request.args.get('project_id', type=int)
        sprint_id = request.args.get('sprint_id', type=int)
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')

        # date range defaults
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        if start_date_str:
            start_date = datetime.fromisoformat(start_date_str)
        if end_date_str:
            end_date = datetime.fromisoformat(end_date_str)

        # Scope tasks by permissions
        base_query = Task.query
        if project_id:
            base_query = base_query.filter(Task.project_id == project_id)
        if sprint_id:
            base_query = base_query.filter(Task.sprint_id == sprint_id)
        if not current_user.has_permission(Permission.REPORTS_VIEW_ALL):
            base_query = base_query.filter(Task.assigned_to == current_user.id)

        base_query = base_query.filter(Task.created_at >= start_date, Task.created_at <= end_date)
        tasks = base_query.all()

        # Build DataFrame
        rows = []
        for t in tasks:
            rows.append({
                'Date': t.created_at.date().isoformat() if t.created_at else '',
                'ID': t.id,
                'Title': t.title,
                'Status': t.status,
                'Priority': t.priority,
                'Assignee': t.assignee.name if t.assignee else 'Unassigned',
                'Project': t.project.name if getattr(t, 'project', None) else '',
                'Sprint': t.sprint.name if getattr(t, 'sprint', None) else '',
            })

        df = pd.DataFrame(rows)
        if df.empty:
            df = pd.DataFrame(columns=['Date','ID','Title','Status','Priority','Assignee','Project','Sprint'])

        if period in ('daily', 'monthly'):
            if period == 'monthly':
                df['Month'] = pd.to_datetime(df['Date']).dt.to_period('M').astype(str)
                group_key = 'Month'
            else:
                group_key = 'Date'
            grouped = df.groupby(group_key).agg(
                total_tasks=pd.NamedAgg(column='ID', aggfunc='count'),
                completed=pd.NamedAgg(column='Status', aggfunc=lambda s: (s == 'completed').sum()),
                in_progress=pd.NamedAgg(column='Status', aggfunc=lambda s: (s == 'in_progress').sum()),
                todo=pd.NamedAgg(column='Status', aggfunc=lambda s: (s == 'todo').sum()),
            ).reset_index()
            out_df = grouped
        else:
            # custom: return raw rows within range
            out_df = df

        output = io.BytesIO()
        out_df.to_csv(output, index=False)
        output.seek(0)

        filename = f"tasks_{period}_export_{datetime.utcnow().strftime('%Y%m%d')}.csv"
        return send_file(output, mimetype='text/csv', as_attachment=True, download_name=filename)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@reports_bp.route('/admin/daily-stats', methods=['GET'])
@jwt_required()
def daily_stats():
    """Return created and completed task counts per day for the last N days.
    Params: days=14, project_id?, sprint_id?"""
    try:
        current_user = get_current_user()
        if not current_user or not current_user.has_permission(Permission.REPORTS_VIEW_ALL):
            return jsonify({"error": "Access denied"}), 403

        days = request.args.get('days', 14, type=int)
        project_id = request.args.get('project_id', type=int)
        sprint_id = request.args.get('sprint_id', type=int)

        end = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        start = end - timedelta(days=days-1)

        # Scope query
        q = Task.query
        if project_id:
            q = q.filter(Task.project_id == project_id)
        if sprint_id:
            q = q.filter(Task.sprint_id == sprint_id)

        tasks = q.all()
        created_map = {}
        completed_map = {}
        # Initialize date map
        cursor = start
        while cursor <= end:
            key = cursor.date().isoformat()
            created_map[key] = 0
            completed_map[key] = 0
            cursor += timedelta(days=1)
        for t in tasks:
            if t.created_at:
                d = t.created_at.date().isoformat()
                if d in created_map:
                    created_map[d] += 1
            if t.completed_at:
                d2 = t.completed_at.date().isoformat()
                if d2 in completed_map:
                    completed_map[d2] += 1

        series = []
        cursor = start
        while cursor <= end:
            k = cursor.date().isoformat()
            series.append({
                'date': k,
                'created': created_map.get(k, 0),
                'completed': completed_map.get(k, 0)
            })
            cursor += timedelta(days=1)

        return jsonify({'days': days, 'start_date': start.isoformat(), 'end_date': end.isoformat(), 'series': series}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@reports_bp.route('/admin/overdue', methods=['GET'])
@jwt_required()
def overdue_tasks():
    try:
        current_user = get_current_user()
        if not current_user or not current_user.has_permission(Permission.REPORTS_VIEW_ALL):
            return jsonify({"error": "Access denied"}), 403

        project_id = request.args.get('project_id', type=int)
        sprint_id = request.args.get('sprint_id', type=int)
        limit = request.args.get('limit', 50, type=int)

        q = Task.query.filter(Task.status != 'completed', Task.due_date.isnot(None), Task.due_date < datetime.utcnow())
        if project_id:
            q = q.filter(Task.project_id == project_id)
        if sprint_id:
            q = q.filter(Task.sprint_id == sprint_id)

        tasks = q.order_by(Task.due_date.asc()).limit(limit).all()
        return jsonify({
            'count': q.count(),
            'tasks': [
                {
                    'id': t.id,
                    'title': t.title,
                    'due_date': t.due_date.isoformat() if t.due_date else None,
                    'priority': t.priority,
                    'assignee': t.assignee.name if t.assignee else None,
                    'project': t.project.name if getattr(t, 'project', None) else None,
                    'status': t.status,
                } for t in tasks
            ]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@reports_bp.route('/admin/top-projects-throughput', methods=['GET'])
@jwt_required()
def top_projects_throughput():
    try:
        current_user = get_current_user()
        if not current_user or not current_user.has_permission(Permission.REPORTS_VIEW_ALL):
            return jsonify({"error": "Access denied"}), 403

        days = request.args.get('days', 14, type=int)
        limit = request.args.get('limit', 5, type=int)
        since = datetime.utcnow() - timedelta(days=days)

        # count completed per project in range
        rows = db.session.query(Project.id, Project.name, func.count(Task.id).label('completed')) \
            .join(Task, Task.project_id == Project.id) \
            .filter(Task.completed_at.isnot(None), Task.completed_at >= since) \
            .group_by(Project.id).order_by(func.count(Task.id).desc()).limit(limit).all()

        return jsonify([
            { 'project_id': pid, 'project_name': pname, 'completed': comp } for pid, pname, comp in rows
        ]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@reports_bp.route('/admin/active-trend', methods=['GET'])
@jwt_required()
def active_trend():
    """Active tasks per day (not completed yet) over last N days."""
    try:
        current_user = get_current_user()
        if not current_user or not current_user.has_permission(Permission.REPORTS_VIEW_ALL):
            return jsonify({"error": "Access denied"}), 403

        days = request.args.get('days', 14, type=int)
        project_id = request.args.get('project_id', type=int)
        sprint_id = request.args.get('sprint_id', type=int)

        end = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        start = end - timedelta(days=days-1)

        q = Task.query
        if project_id:
            q = q.filter(Task.project_id == project_id)
        if sprint_id:
            q = q.filter(Task.sprint_id == sprint_id)
        tasks = q.all()

        # Build active counts per day without N+1 queries
        active_map = {}
        cursor = start
        while cursor <= end:
            active_map[cursor.date().isoformat()] = 0
            cursor += timedelta(days=1)

        for t in tasks:
            if not t.created_at:
                continue
            start_d = max(start.date(), t.created_at.date())
            # Active until the day before completed_at (if completed)
            last_active_day = end.date()
            if getattr(t, 'completed_at', None):
                ca = t.completed_at.date()
                if ca <= end.date():
                    last_active_day = (ca - timedelta(days=1))
            d = start_d
            while d <= last_active_day:
                key = d.isoformat()
                if key in active_map:
                    active_map[key] += 1
                d += timedelta(days=1)

        series = [{ 'date': k, 'active': active_map[k] } for k in sorted(active_map.keys())]
        return jsonify({ 'days': days, 'start_date': start.isoformat(), 'end_date': end.isoformat(), 'series': series }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500