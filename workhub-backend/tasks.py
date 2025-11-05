# workhub-backend/tasks.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone

from models import db, Task, User, Notification, Comment, TimeLog, FileAttachment, ProjectMember
from notifications import create_notification_with_email as notify_with_email
from sqlalchemy import or_, text
from sqlalchemy.orm import joinedload
from auth import admin_required, get_current_user
from permissions import Permission
from validators import validator, ValidationError  # <-- relaxed, exception-based
from security_middleware import rate_limit

tasks_bp = Blueprint('tasks', __name__)  # app.py registers with url_prefix (e.g., "/api/tasks")


# ------------------------------ helpers -------------------------------------

def _get_current_user():
    uid = get_jwt_identity()
    try:
        uid_int = int(uid) if uid is not None else None
    except (TypeError, ValueError):
        return None
    return User.query.get(uid_int) if uid_int is not None else None


def create_notification(user_id, title, message, notification_type, task_id=None):
    """Helper to create notifications (same behavior as before)."""
    if not user_id:
        return
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=notification_type,
        related_task_id=task_id
    )
    db.session.add(notification)


def _ensure_task_project_sprint_columns():
    """Idempotently add project_id and sprint_id to tasks if missing (MSSQL)."""
    try:
        with db.engine.begin() as conn:
            conn.execute(text(
                """
                IF NOT EXISTS (
                    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME='tasks' AND COLUMN_NAME='project_id'
                )
                BEGIN
                    ALTER TABLE dbo.tasks ADD project_id INT NULL;
                END
                """
            ))
            conn.execute(text(
                """
                IF NOT EXISTS (
                    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME='tasks' AND COLUMN_NAME='sprint_id'
                )
                BEGIN
                    ALTER TABLE dbo.tasks ADD sprint_id INT NULL;
                END
                """
            ))
    except Exception:
        # Ignore here; handlers will surface errors if still failing
        pass


def _ensure_task_indexes():
    """Idempotently create helpful indexes on tasks for performance (MSSQL)."""
    try:
        with db.engine.begin() as conn:
            # Helper to create index if missing
            def create_index_if_missing(index_name, table_name, column_name):
                conn.execute(text(
                    f"""
                    IF NOT EXISTS (
                        SELECT 1 FROM sys.indexes i
                        WHERE i.name = '{index_name}' AND i.object_id = OBJECT_ID('{table_name}')
                    )
                    BEGIN
                        CREATE INDEX [{index_name}] ON {table_name}([{column_name}]);
                    END
                    """
                ))

            create_index_if_missing('ix_tasks_assigned_to', 'dbo.tasks', 'assigned_to')
            create_index_if_missing('ix_tasks_project_id', 'dbo.tasks', 'project_id')
            create_index_if_missing('ix_tasks_sprint_id', 'dbo.tasks', 'sprint_id')
            create_index_if_missing('ix_tasks_status', 'dbo.tasks', 'status')
            create_index_if_missing('ix_tasks_priority', 'dbo.tasks', 'priority')
            create_index_if_missing('ix_tasks_created_at', 'dbo.tasks', 'created_at')
    except Exception:
        # Non-fatal; continue without blocking request
        pass


def _ensure_comment_parent_column():
    """Idempotently add parent_comment_id to comments if missing (MSSQL)."""
    try:
        with db.engine.begin() as conn:
            conn.execute(text(
                """
                IF NOT EXISTS (
                    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME='comments' AND COLUMN_NAME='parent_comment_id'
                )
                BEGIN
                    ALTER TABLE dbo.comments ADD parent_comment_id INT NULL;
                END
                """
            ))
    except Exception:
        pass


# ------------------------------- queries ------------------------------------

@tasks_bp.route('/', methods=['GET'])
@rate_limit(max_requests=120, time_window=60)
@jwt_required()
def get_tasks():
    try:
        _ensure_task_project_sprint_columns()
        _ensure_task_indexes()
        current_user = _get_current_user()
        if not current_user:
            return jsonify({'error': 'Unauthorized'}), 401

        # Filters
        status = request.args.get('status')
        priority = request.args.get('priority')
        assigned_to = request.args.get('assigned_to')
        search = request.args.get('search')
        project_id = request.args.get('project_id')
        sprint_id = request.args.get('sprint_id')

        # Base scope by role
        role = (current_user.role or 'viewer').lower()
        if role in ('super_admin', 'admin'):
            query = Task.query
        elif role in ('manager', 'team_lead'):
            # Limit to tasks from projects the user is a member of; also include tasks assigned to them lacking project
            member_project_ids = [m.project_id for m in ProjectMember.query.filter_by(user_id=current_user.id).all()]
            if member_project_ids:
                query = Task.query.filter(
                    or_(Task.project_id.in_(member_project_ids), Task.assigned_to == current_user.id)
                )
            else:
                query = Task.query.filter_by(assigned_to=current_user.id)
        else:
            # developer/viewer: only assigned tasks
            query = Task.query.filter_by(assigned_to=current_user.id)

        # Apply filters
        if status:
            query = query.filter_by(status=status)
        if priority:
            query = query.filter_by(priority=priority)
        if assigned_to and current_user.has_permission(Permission.TASKS_READ):
            try:
                query = query.filter_by(assigned_to=int(assigned_to))
            except ValueError:
                return jsonify({'error': 'assigned_to must be an integer'}), 400
        if search:
            query = query.filter(
                or_(
                    Task.title.contains(search),
                    Task.description.contains(search)
                )
            )
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

        # Optional pagination
        page = request.args.get('page', type=int)
        page_size = request.args.get('page_size', type=int)

        query = query.order_by(Task.created_at.desc())

        if page and page_size:
            pagination = query.paginate(page=page, per_page=page_size, error_out=False)
            items = [t.to_dict() for t in pagination.items]
            meta = {
                'page': pagination.page,
                'page_size': pagination.per_page,
                'total_pages': pagination.pages,
                'total_items': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev,
            }
            return jsonify({'items': items, 'meta': meta}), 200
        else:
            tasks = query.all()
            return jsonify([t.to_dict() for t in tasks]), 200
    except Exception as e:
        # Log and include details for diagnosis
        try:
            print(f"/api/tasks GET error: {e}")
        except Exception:
            pass
        return jsonify({'error': 'Failed to fetch tasks', 'details': str(e)}), 500


@tasks_bp.route('/<int:task_id>', methods=['GET'])
@jwt_required()
def get_task(task_id):
    try:
        current_user = _get_current_user()
        if not current_user:
            return jsonify({'error': 'Unauthorized'}), 401

        # Get task without eager loading first to check permissions
        task = Task.query.get(task_id)
        
        if not task:
            return jsonify({'error': 'Task not found'}), 404

        # Access: users with TASKS_READ or assignee
        if not current_user.has_permission(Permission.TASKS_READ) and task.assigned_to != current_user.id:
            return jsonify({'error': 'Access denied'}), 403

        # Now eager load comments and time_logs
        try:
            task = Task.query.options(
                joinedload(Task.comments),
                joinedload(Task.time_logs)
            ).get(task_id)
        except Exception as e:
            print(f"Warning: Could not eager load relationships: {e}")
            task = Task.query.get(task_id)

        # Safely build task dictionary with error handling
        try:
            d = task.to_dict(include_subtasks=True)
        except Exception as e:
            print(f"Error in task.to_dict(): {e}")
            import traceback
            traceback.print_exc()
            # Build basic dict manually if to_dict fails
            d = {
                'id': task.id,
                'title': task.title if hasattr(task, 'title') else 'Unknown',
                'description': task.description if hasattr(task, 'description') else None,
                'priority': task.priority if hasattr(task, 'priority') else 'medium',
                'status': task.status if hasattr(task, 'status') else 'todo',
                'due_date': task.due_date.isoformat() if (hasattr(task, 'due_date') and task.due_date) else None,
                'assigned_to': task.assigned_to if hasattr(task, 'assigned_to') else None,
                'created_by': task.created_by if hasattr(task, 'created_by') else None,
                'project_id': task.project_id if hasattr(task, 'project_id') else None,
                'sprint_id': task.sprint_id if hasattr(task, 'sprint_id') else None,
            }
        
        # Safely get comments and time_logs
        try:
            if hasattr(task, 'comments'):
                comments_list = list(task.comments) if task.comments else []
                d['comments'] = [c.to_dict() for c in comments_list if c]
            else:
                d['comments'] = []
        except Exception as e:
            print(f"Error getting comments: {e}")
            import traceback
            traceback.print_exc()
            d['comments'] = []
        try:
            if hasattr(task, 'time_logs'):
                time_logs_list = list(task.time_logs) if task.time_logs else []
                d['time_logs'] = [l.to_dict() for l in time_logs_list if l]
            else:
                d['time_logs'] = []
        except Exception as e:
            print(f"Error getting time_logs: {e}")
            import traceback
            traceback.print_exc()
            d['time_logs'] = []
        return jsonify(d), 200
    except Exception as e:
        import traceback
        print(f"/api/tasks/{task_id} GET error: {e}")
        traceback.print_exc()
        return jsonify({'error': 'Failed to fetch task', 'details': str(e)}), 500


# ------------------------------- mutations ----------------------------------

@tasks_bp.route('/', methods=['POST'])
@jwt_required()
def create_task():
    try:
        _ensure_task_project_sprint_columns()
        current_user = _get_current_user()
        if not current_user:
            return jsonify({'error': 'Unauthorized'}), 401
        
        # Check permission to create tasks
        if not current_user.has_permission(Permission.TASKS_CREATE):
            return jsonify({'error': 'Access denied'}), 403

        payload = request.get_json(silent=True) or {}

        # Validate with relaxed validator (title/description/priority/due_date/assignee/project/sprint)
        try:
            data = validator.validate_task_payload(payload, db=db.session, require_assigned_to=False)
        except ValidationError as e:
            return jsonify({'error': str(e)}), 400

        # Enforce project-scoped creation for manager/team_lead
        actor_role = (current_user.role or 'viewer').lower()
        if actor_role in ('manager', 'team_lead'):
            if not data.get('project_id'):
                return jsonify({'error': 'Managers and Team Leads must specify project_id when creating tasks'}), 400
            # current user must be member of the project
            if not ProjectMember.query.filter_by(project_id=data['project_id'], user_id=current_user.id).first():
                return jsonify({'error': 'You may only create tasks within your projects'}), 403
            # if assigning, the assignee must also be a member of the same project
            if data.get('assigned_to'):
                if not ProjectMember.query.filter_by(project_id=data['project_id'], user_id=data['assigned_to']).first():
                    return jsonify({'error': 'Assignee must be a member of the same project'}), 400

        task = Task(
            title=data['title'],
            description=data['description'],
            priority=data['priority'],
            status=payload.get('status', 'todo'),  # keep your original default
            assigned_to=data['assigned_to'],
            created_by=current_user.id,
            due_date=data['due_date'],
            project_id=data.get('project_id'),
            sprint_id=data.get('sprint_id'),
        )

        db.session.add(task)
        db.session.flush()  # get task.id

        # Notify assignee if set
        if task.assigned_to:
            # Create in-app notification and send email if user preference allows
            notify_with_email(
                user_id=task.assigned_to,
                title='New Task Assigned',
                message=f'You have been assigned a new task: {task.title}',
                notif_type='task_assigned',
                related_task_id=task.id,
                send_email=True
            )

        db.session.commit()
        return jsonify({'message': 'Task created successfully', 'task': task.to_dict()}), 201

    except SQLAlchemyError as e:
        db.session.rollback()
        msg = str(getattr(e, 'orig', e))
        return jsonify({'error': 'Database error occurred.', 'details': msg}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@tasks_bp.route('/<int:task_id>', methods=['PUT'])
@jwt_required()
def update_task(task_id):
    try:
        _ensure_task_project_sprint_columns()
        current_user = _get_current_user()
        if not current_user:
            return jsonify({'error': 'Unauthorized'}), 401

        task = Task.query.get(task_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404

        # Permissions: users with TASKS_UPDATE or assignee can modify
        # For managers/team leads: also allow if task is in their assigned projects
        has_update_permission = current_user.has_permission(Permission.TASKS_UPDATE)
        is_assignee = (task.assigned_to == current_user.id)
        actor_role = (current_user.role or 'viewer').lower()
        is_project_member = False
        if actor_role in ('manager', 'team_lead') and task.project_id:
            is_project_member = ProjectMember.query.filter_by(
                project_id=task.project_id, user_id=current_user.id
            ).first() is not None
        
        if not (has_update_permission or is_assignee or is_project_member):
            return jsonify({'error': 'Access denied'}), 403

        payload = request.get_json(silent=True) or {}
        old_status = task.status
        old_assignee = task.assigned_to

        # Build a merged view for validation parity (unchanged fields fall back)
        merged = {
            'title': payload.get('title', task.title),
            'description': payload.get('description', task.description),
            'priority': payload.get('priority', task.priority),
            'due_date': payload.get('due_date', task.due_date.isoformat() if task.due_date else None),
            'assigned_to': payload.get('assigned_to', task.assigned_to),
            'project_id': payload.get('project_id', task.project_id),
            'sprint_id': payload.get('sprint_id', task.sprint_id),
        }

        # Only users with TASKS_UPDATE can change title/description/priority/assigned_to/due_date
        try:
            if has_update_permission:
                v = validator.validate_task_payload(merged, db=db.session)
                # For managers/team leads: enforce same-project constraints when changing assignee/project
                actor_role = (current_user.role or 'viewer').lower()
                if actor_role in ('manager', 'team_lead'):
                    # Check if task currently belongs to a project they're a member of
                    current_task_project = task.project_id
                    can_manage_current_task = False
                    if current_task_project:
                        can_manage_current_task = ProjectMember.query.filter_by(
                            project_id=current_task_project, user_id=current_user.id
                        ).first() is not None
                    else:
                        # If task has no project, managers/team leads can't manage it (must have project)
                        return jsonify({'error': 'Tasks must belong to a project you are assigned to'}), 403
                    
                    # If updating project_id, ensure they're a member of the new project
                    proj_id = v['project_id']
                    if 'project_id' in payload:
                        if not proj_id:
                            return jsonify({'error': 'project_id is required for managers and team leads'}), 400
                        if not ProjectMember.query.filter_by(project_id=proj_id, user_id=current_user.id).first():
                            return jsonify({'error': 'You may only move tasks to projects you are assigned to'}), 403
                    elif not can_manage_current_task:
                        return jsonify({'error': 'You may only update tasks within your assigned projects'}), 403
                    
                    # Ensure assignee is a member of the project (use new project_id if changing, else current)
                    target_project_id = proj_id if 'project_id' in payload else current_task_project
                    if 'assigned_to' in payload and v.get('assigned_to'):
                        if not target_project_id:
                            return jsonify({'error': 'project_id is required to change assignment'}), 400
                        if not ProjectMember.query.filter_by(project_id=target_project_id, user_id=v['assigned_to']).first():
                            return jsonify({'error': 'Assignee must be a member of the same project'}), 400
                if 'title' in payload:
                    task.title = v['title']
                if 'description' in payload:
                    task.description = v['description']
                if 'priority' in payload:
                    # Restrict priority changes to manager/admin/super_admin
                    actor_role = (current_user.role or 'viewer').lower()
                    if actor_role not in ('manager', 'admin', 'super_admin'):
                        return jsonify({'error': 'Only managers, admins, and super admins can change priority.'}), 403
                    task.priority = v['priority']
                if 'due_date' in payload:
                    task.due_date = v['due_date']
                if 'assigned_to' in payload:
                    task.assigned_to = v['assigned_to']
                if 'project_id' in payload:
                    task.project_id = v['project_id']
                if 'sprint_id' in payload:
                    task.sprint_id = v['sprint_id']
                # Handle dependency update (blocks relationship)
                if 'blocks_task_id' in payload:
                    # Restrict blocking to manager/admin/super_admin
                    actor_role = (current_user.role or 'viewer').lower()
                    if actor_role not in ('manager', 'admin', 'super_admin'):
                        return jsonify({'error': 'Only managers, admins, and super admins can block tasks.'}), 403
                    new_blocks = payload.get('blocks_task_id')
                    if new_blocks in (None, ''):
                        task.blocks_task_id = None
                    else:
                        try:
                            new_blocks_int = int(new_blocks)
                        except (TypeError, ValueError):
                            return jsonify({'error': 'blocks_task_id must be an integer or null'}), 400
                        if new_blocks_int == task.id:
                            return jsonify({'error': 'A task cannot block itself'}), 400
                        target = Task.query.get(new_blocks_int)
                        if not target:
                            return jsonify({'error': 'Blocked task not found'}), 404
                        task.blocks_task_id = new_blocks_int
            else:
                # non-admins cannot change these fields; enforcing old workflow
                pass
        except ValidationError as e:
            return jsonify({'error': str(e)}), 400

        # Both admin and assignee can update status (keep your original rule)
        if 'status' in payload:
            new_status = payload['status']
            # Enforce dependency rule: a task cannot be set to completed if it is blocked by another incomplete task
            if new_status == 'completed':
                # If this task is blocked by another (some other task points to this as blocks_task_id), prevent completion
                from models import Task as TaskModel
                blocking_tasks = TaskModel.query.filter_by(blocks_task_id=task.id).all()
                for blk in blocking_tasks:
                    if blk.status != 'completed':
                        return jsonify({'error': f'Task is blocked by "{blk.title}". Complete it first.'}), 400

            task.status = new_status

            # completed_at bookkeeping + creator notification
            if new_status == 'completed' and old_status != 'completed':
                # Use UTC to match backend style elsewhere
                if hasattr(task, 'completed_at'):
                    task.completed_at = datetime.now(timezone.utc)
                if task.created_by and task.created_by != current_user.id:
                    notify_with_email(
                        user_id=task.created_by,
                        title='Task Completed',
                        message=f'Task "{task.title}" has been completed',
                        notif_type='task_updated',
                        related_task_id=task.id,
                        send_email=True
                    )
            elif new_status != 'completed' and old_status == 'completed':
                if hasattr(task, 'completed_at'):
                    task.completed_at = None

        task.updated_at = datetime.utcnow()

        # Rule: Completed tasks cannot be set to block other tasks, and you cannot set a completed task as a blocker
        if getattr(task, 'blocks_task_id', None):
            from models import Task as TaskModel
            blocker = TaskModel.query.get(task.blocks_task_id)
            if task.status == 'completed':
                task.blocks_task_id = None
            elif blocker and blocker.status == 'completed':
                return jsonify({'error': 'A completed task cannot be used to block another task.'}), 400

        # If user with update permission changed assignee, send assignment notification
        if has_update_permission and task.assigned_to and old_assignee != task.assigned_to:
            notify_with_email(
                user_id=task.assigned_to,
                title='Task Assigned',
                message=f'You have been assigned to task: {task.title}',
                notif_type='task_assigned',
                related_task_id=task.id,
                send_email=True
            )

        db.session.commit()
        return jsonify({'message': 'Task updated successfully', 'task': task.to_dict()}), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        msg = str(getattr(e, 'orig', e))
        return jsonify({'error': 'Database error occurred.', 'details': msg}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@tasks_bp.route('/<int:task_id>', methods=['DELETE'])
@jwt_required()
def delete_task(task_id):
    try:
        current_user = _get_current_user()
        if not current_user:
            return jsonify({'error': 'Unauthorized'}), 401
        
        task = Task.query.get(task_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        # Check if user has permission to delete tasks
        can_delete_any = current_user.has_permission(Permission.TASKS_DELETE_ANY)
        is_creator = task.created_by == current_user.id
        
        # For managers and team leads: allow deletion of ANY task in their assigned projects
        actor_role = (current_user.role or 'viewer').lower()
        is_project_member = False
        if actor_role in ('manager', 'team_lead') and task.project_id:
            is_project_member = ProjectMember.query.filter_by(
                project_id=task.project_id, user_id=current_user.id
            ).first() is not None
        
        if not (can_delete_any or (current_user.has_permission(Permission.TASKS_DELETE) and (is_creator or is_project_member))):
            return jsonify({'error': 'Access denied'}), 403

        # Clear notifications referencing this task (to avoid FK issues)
        Notification.query.filter_by(related_task_id=task_id).update(
            {Notification.related_task_id: None},
            synchronize_session=False
        )
        db.session.flush()

        # Remove dependent records with NOT NULL FKs
        TimeLog.query.filter_by(task_id=task_id).delete(synchronize_session=False)
        Comment.query.filter_by(task_id=task_id).delete(synchronize_session=False)
        FileAttachment.query.filter_by(task_id=task_id).delete(synchronize_session=False)
        db.session.flush()

        db.session.delete(task)
        db.session.commit()
        return jsonify({'message': 'Task deleted successfully'}), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        msg = str(getattr(e, 'orig', e))
        return jsonify({'error': 'Database error occurred.', 'details': msg}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ------------------------------- comments -----------------------------------

@tasks_bp.route('/<int:task_id>/comments', methods=['POST'])
@jwt_required()
def add_comment(task_id):
    try:
        _ensure_comment_parent_column()
        current_user = _get_current_user()
        if not current_user:
            return jsonify({'error': 'Unauthorized'}), 401

        task = Task.query.get(task_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404

        # Access: users with TASKS_READ or assignee
        if not current_user.has_permission(Permission.TASKS_READ) and task.assigned_to != current_user.id:
            return jsonify({'error': 'Access denied'}), 403

        payload = request.get_json(silent=True) or {}
        try:
            c = validator.validate_comment(payload)  # { "content": "...", parent_comment_id? }
        except ValidationError as e:
            return jsonify({'error': str(e)}), 400

        parent_comment_id = payload.get('parent_comment_id')
        if parent_comment_id not in (None, ''):
            try:
                parent_comment_id = int(parent_comment_id)
            except (TypeError, ValueError):
                return jsonify({'error': 'parent_comment_id must be an integer'}), 400
            # Ensure parent exists and belongs to same task
            parent = Comment.query.get(parent_comment_id)
            if not parent or parent.task_id != task.id:
                return jsonify({'error': 'Parent comment not found for this task'}), 404
        else:
            parent_comment_id = None

        comment = Comment(task_id=task.id, user_id=current_user.id, content=c['content'], parent_comment_id=parent_comment_id)
        db.session.add(comment)

        # Notify assignee and creator (not the commenter)
        notify_users = set()
        if task.assigned_to and task.assigned_to != current_user.id:
            notify_users.add(task.assigned_to)
        if task.created_by and task.created_by != current_user.id:
            notify_users.add(task.created_by)

        # Parse @mentions in content and notify mentioned users
        # Extract plain text from HTML for mention detection
        try:
            import re
            import bleach
            plain_text = bleach.clean(c['content'], tags=[], strip=True)
            mentioned = set()
            for m in re.findall(r"@([A-Za-z0-9_.'-]{2,50})", plain_text):
                name = m.strip()
                if not name:
                    continue
                user = User.query.filter(User.name.ilike(name)).first()
                if user and user.id != current_user.id:
                    mentioned.add(user.id)
            notify_users.update(mentioned)
        except Exception:
            pass

        for uid in notify_users:
            notify_with_email(
                user_id=uid,
                title='New Comment',
                message=f'{current_user.name} commented on task: {task.title}',
                notif_type='comment',
                related_task_id=task.id,
                send_email=True
            )

        db.session.commit()
        return jsonify({'message': 'Comment added successfully', 'comment': comment.to_dict()}), 201

    except SQLAlchemyError as e:
        db.session.rollback()
        msg = str(getattr(e, 'orig', e))
        return jsonify({'error': 'Database error occurred.', 'details': msg}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@tasks_bp.route('/<int:task_id>/comments/<int:comment_id>', methods=['PUT'])
@jwt_required()
def update_comment(task_id, comment_id):
    """Update a comment - only owner can edit"""
    try:
        current_user = _get_current_user()
        if not current_user:
            return jsonify({'error': 'Unauthorized'}), 401

        comment = Comment.query.get(comment_id)
        if not comment or comment.task_id != task_id:
            return jsonify({'error': 'Comment not found'}), 404

        # Only comment owner can edit
        if comment.user_id != current_user.id:
            return jsonify({'error': 'You can only edit your own comments'}), 403

        payload = request.get_json(silent=True) or {}
        try:
            c = validator.validate_comment(payload, allow_html=True)
        except ValidationError as e:
            return jsonify({'error': str(e)}), 400

        comment.content = c['content']
        db.session.commit()
        return jsonify({'message': 'Comment updated successfully', 'comment': comment.to_dict()}), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': 'Database error occurred.'}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@tasks_bp.route('/<int:task_id>/comments/<int:comment_id>', methods=['DELETE'])
@jwt_required()
def delete_comment(task_id, comment_id):
    """Delete a comment - owner or admin can delete"""
    try:
        current_user = _get_current_user()
        if not current_user:
            return jsonify({'error': 'Unauthorized'}), 401

        comment = Comment.query.get(comment_id)
        if not comment or comment.task_id != task_id:
            return jsonify({'error': 'Comment not found'}), 404

        # Only comment owner or admin can delete
        is_owner = comment.user_id == current_user.id
        is_admin = current_user.has_permission(Permission.COMMENTS_DELETE_ANY)
        
        if not (is_owner or is_admin):
            return jsonify({'error': 'Access denied'}), 403

        # Delete comment (cascade will delete replies)
        db.session.delete(comment)
        db.session.commit()
        return jsonify({'message': 'Comment deleted successfully'}), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': 'Database error occurred.'}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ------------------------------ calendar -----------------------------------

@tasks_bp.route('/calendar', methods=['GET'])
@jwt_required()
def get_calendar_tasks():
    """Get tasks for calendar view by date range"""
    try:
        current_user = _get_current_user()
        if not current_user:
            return jsonify({'error': 'Unauthorized'}), 401

        # Get date range params
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        # Default to current month if not provided
        if not start_date_str or not end_date_str:
            from datetime import timedelta
            now = datetime.utcnow()
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            # Get last day of current month
            if now.month == 12:
                end_date = datetime(now.year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = datetime(now.year, now.month + 1, 1) - timedelta(days=1)
            end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        else:
            try:
                # Parse ISO format dates, handling timezone
                start_date_str_clean = start_date_str.replace('Z', '+00:00') if start_date_str.endswith('Z') else start_date_str
                end_date_str_clean = end_date_str.replace('Z', '+00:00') if end_date_str.endswith('Z') else end_date_str
                
                start_date = datetime.fromisoformat(start_date_str_clean)
                end_date = datetime.fromisoformat(end_date_str_clean)
                
                # Convert to UTC naive datetime for SQL Server (which doesn't support timezone)
                if start_date.tzinfo:
                    start_date = start_date.astimezone(timezone.utc).replace(tzinfo=None)
                if end_date.tzinfo:
                    end_date = end_date.astimezone(timezone.utc).replace(tzinfo=None)
            except Exception as e:
                import traceback
                print(f"Date parsing error: {e}")
                traceback.print_exc()
                return jsonify({'error': f'Invalid date format. Use ISO 8601 format. Error: {str(e)}'}), 400

        # Base scope by role (same logic as get_tasks)
        role = (current_user.role or 'viewer').lower()
        if role in ('super_admin', 'admin'):
            query = Task.query
        elif role in ('manager', 'team_lead'):
            member_project_ids = [m.project_id for m in ProjectMember.query.filter_by(user_id=current_user.id).all()]
            if member_project_ids:
                query = Task.query.filter(
                    or_(Task.project_id.in_(member_project_ids), Task.assigned_to == current_user.id)
                )
            else:
                query = Task.query.filter_by(assigned_to=current_user.id)
        else:
            query = Task.query.filter_by(assigned_to=current_user.id)

        # Additional filters
        project_id = request.args.get('project_id', type=int)
        sprint_id = request.args.get('sprint_id', type=int)
        assigned_to = request.args.get('assigned_to', type=int)
        status = request.args.get('status')

        if project_id:
            query = query.filter_by(project_id=project_id)
        if sprint_id:
            query = query.filter_by(sprint_id=sprint_id)
        if assigned_to and current_user.has_permission(Permission.TASKS_READ):
            query = query.filter_by(assigned_to=assigned_to)
        if status:
            query = query.filter_by(status=status)

        # Filter by due_date within range
        query = query.filter(
            Task.due_date.isnot(None),
            Task.due_date >= start_date,
            Task.due_date <= end_date
        )

        tasks = query.order_by(Task.due_date.asc()).all()
        
        # Group tasks by date
        tasks_by_date = {}
        for task in tasks:
            if task.due_date:
                date_key = task.due_date.date().isoformat()
                if date_key not in tasks_by_date:
                    tasks_by_date[date_key] = []
                tasks_by_date[date_key].append(task.to_dict())

        return jsonify({
            'tasks_by_date': tasks_by_date,
            'total_tasks': len(tasks),
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@tasks_bp.route('/<int:task_id>/update-due-date', methods=['PUT'])
@jwt_required()
def update_task_due_date(task_id):
    """Update task due date (for calendar drag-and-drop)"""
    try:
        current_user = _get_current_user()
        if not current_user:
            return jsonify({'error': 'Unauthorized'}), 401

        task = Task.query.get(task_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404

        # Check permissions
        role = (current_user.role or 'viewer').lower()
        can_update = False
        if role in ('super_admin', 'admin'):
            can_update = True
        elif role in ('manager', 'team_lead'):
            if task.project_id:
                can_update = ProjectMember.query.filter_by(
                    project_id=task.project_id, user_id=current_user.id
                ).first() is not None
            can_update = can_update or task.assigned_to == current_user.id
        else:
            can_update = task.assigned_to == current_user.id

        if not can_update:
            return jsonify({'error': 'Access denied'}), 403

        payload = request.get_json(silent=True) or {}
        due_date_str = payload.get('due_date')
        
        if due_date_str:
            try:
                due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
            except Exception:
                return jsonify({'error': 'Invalid date format. Use ISO 8601 format.'}), 400
        else:
            due_date = None

        task.due_date = due_date
        db.session.commit()
        
        return jsonify({
            'message': 'Task due date updated successfully',
            'task': task.to_dict()
        }), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': 'Database error occurred.'}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ------------------------------ time logs -----------------------------------

@tasks_bp.route('/<int:task_id>/time-logs', methods=['POST'])
@jwt_required()
def add_time_log(task_id):
    try:
        current_user = _get_current_user()
        if not current_user:
            return jsonify({'error': 'Unauthorized'}), 401

        task = Task.query.get(task_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404

        # Access: users with TASKS_READ or assignee
        if not current_user.has_permission(Permission.TASKS_READ) and task.assigned_to != current_user.id:
            return jsonify({'error': 'Access denied'}), 403

        payload = request.get_json(silent=True) or {}
        try:
            tl = validator.validate_time_log(payload)  # { "hours": float }
        except ValidationError as e:
            return jsonify({'error': str(e)}), 400

        time_log = TimeLog(
            task_id=task.id,
            user_id=current_user.id,
            hours=tl['hours'],
            description=(payload.get('description') or '').strip()
        )
        db.session.add(time_log)
        db.session.commit()
        return jsonify({'message': 'Time logged successfully', 'time_log': time_log.to_dict()}), 201

    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({'error': 'Database error occurred.'}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@tasks_bp.route('/<int:task_id>/time-logs', methods=['GET'])
@jwt_required()
def get_time_logs(task_id):
    try:
        current_user = _get_current_user()
        if not current_user:
            return jsonify({'error': 'Unauthorized'}), 401

        task = Task.query.get(task_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404

        # Access: users with TASKS_READ or assignee
        if not current_user.has_permission(Permission.TASKS_READ) and task.assigned_to != current_user.id:
            return jsonify({'error': 'Access denied'}), 403

        logs = TimeLog.query.filter_by(task_id=task_id).order_by(TimeLog.logged_at.desc()).all()
        return jsonify([l.to_dict() for l in logs]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@tasks_bp.route('/time-logs/<int:log_id>', methods=['DELETE'])
@jwt_required()
def delete_time_log(log_id):
    try:
        current_user = _get_current_user()
        if not current_user:
            return jsonify({'error': 'Unauthorized'}), 401

        log = TimeLog.query.get(log_id)
        if not log:
            return jsonify({'error': 'Time log not found'}), 404

        # Access: admin or owner
        if current_user.role != 'admin' and log.user_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403

        db.session.delete(log)
        db.session.commit()
        return jsonify({'message': 'Time log deleted successfully'}), 200

    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({'error': 'Database error occurred.'}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ------------------------------- bulk operations and subtasks -----------------------------------

@tasks_bp.route('/bulk', methods=['POST'])
@jwt_required()
def bulk_update():
    """Bulk update tasks"""
    try:
        current_user = _get_current_user()
        if not current_user:
            return jsonify({'error': 'Unauthorized'}), 401
        
        if not current_user.has_permission(Permission.TASKS_UPDATE):
            return jsonify({'error': 'Access denied'}), 403
        
        data = request.get_json()
        task_ids = data.get('task_ids', [])
        
        if not task_ids or not isinstance(task_ids, list):
            return jsonify({'error': 'task_ids must be a non-empty array'}), 400
        
        tasks = Task.query.filter(Task.id.in_(task_ids)).all()
        
        if 'assigned_to' in data:
            new_assignee = data['assigned_to']
            if new_assignee:
                user = User.query.get(int(new_assignee))
                if not user:
                    return jsonify({'error': 'Invalid user ID'}), 400
            for task in tasks:
                old_assignee = task.assigned_to
                task.assigned_to = int(new_assignee) if new_assignee else None
                if task.assigned_to and old_assignee != task.assigned_to:
                    notify_with_email(
                        user_id=task.assigned_to,
                        title='Task Assigned',
                        message=f'You have been assigned to task: {task.title}',
                        notif_type='task_assigned',
                        related_task_id=task.id,
                        send_email=True
                    )
        
        if 'status' in data:
            new_status = data['status']
            
            # Enforce dependency checks when changing to 'completed' status
            if new_status == 'completed':
                from models import Task as TaskModel
                # Check each task for blocking dependencies
                for task in tasks:
                    if task.status != 'completed':  # Only check if not already completed
                        blocking_tasks = TaskModel.query.filter_by(blocks_task_id=task.id).all()
                        for blk in blocking_tasks:
                            if blk.status != 'completed':
                                return jsonify({
                                    'error': f'Cannot bulk update: Task "{task.title}" is blocked by "{blk.title}". Complete blocking tasks first.'
                                }), 400
            
            # Apply status changes after validation
            for task in tasks:
                old_status = task.status
                task.status = new_status
                if new_status == 'completed' and old_status != 'completed':
                    task.completed_at = datetime.utcnow()
                    if task.created_by and task.created_by != current_user.id:
                        notify_with_email(
                            user_id=task.created_by,
                            title='Task Completed',
                            message=f'Task "{task.title}" has been completed',
                            notif_type='task_updated',
                            related_task_id=task.id,
                            send_email=True
                        )
                elif new_status != 'completed' and old_status == 'completed':
                    task.completed_at = None
        
        if 'priority' in data:
            new_priority = data['priority']
            for task in tasks:
                task.priority = new_priority
        
        db.session.commit()
        return jsonify({'message': f'Updated {len(tasks)} tasks successfully'}), 200
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({'error': 'Database error occurred.'}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@tasks_bp.route('/bulk', methods=['DELETE'])
@jwt_required()
def bulk_delete():
    """Bulk delete tasks"""
    try:
        current_user = _get_current_user()
        if not current_user:
            return jsonify({'error': 'Unauthorized'}), 401
        
        if not current_user.has_permission(Permission.TASKS_DELETE_ANY):
            return jsonify({'error': 'Access denied'}), 403
        
        data = request.get_json()
        task_ids = data.get('task_ids', [])
        
        if not task_ids or not isinstance(task_ids, list):
            return jsonify({'error': 'task_ids must be a non-empty array'}), 400
        
        tasks = Task.query.filter(Task.id.in_(task_ids)).all()
        Notification.query.filter(Notification.related_task_id.in_(task_ids)).update({Notification.related_task_id: None}, synchronize_session=False)
        db.session.flush()
        TimeLog.query.filter(TimeLog.task_id.in_(task_ids)).delete(synchronize_session=False)
        Comment.query.filter(Comment.task_id.in_(task_ids)).delete(synchronize_session=False)
        db.session.flush()
        for task in tasks:
            db.session.delete(task)
        db.session.commit()
        return jsonify({'message': f'Deleted {len(tasks)} tasks successfully'}), 200
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({'error': 'Database error occurred.'}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@tasks_bp.route('/<int:task_id>/subtasks', methods=['GET'])
@jwt_required()
def get_subtasks(task_id):
    try:
        current_user = _get_current_user()
        if not current_user:
            return jsonify({'error': 'Unauthorized'}), 401
        task = Task.query.get(task_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        if not current_user.has_permission(Permission.TASKS_READ) and task.assigned_to != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        subtasks = Task.query.filter_by(parent_task_id=task_id).order_by(Task.created_at).all()
        return jsonify([t.to_dict(include_subtasks=False) for t in subtasks]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@tasks_bp.route('/<int:task_id>/subtasks', methods=['POST'])
@jwt_required()
def create_subtask(task_id):
    try:
        current_user = _get_current_user()
        if not current_user:
            return jsonify({'error': 'Unauthorized'}), 401
        parent_task = Task.query.get(task_id)
        if not parent_task:
            return jsonify({'error': 'Parent task not found'}), 404
        if not current_user.has_permission(Permission.TASKS_CREATE):
            return jsonify({'error': 'Access denied'}), 403
        data = request.get_json()
        try:
            v = validator.validate_task_payload(data, db=db.session, require_assigned_to=False)
        except ValidationError as e:
            return jsonify({'error': str(e)}), 400
        subtask = Task(title=v['title'], description=v.get('description', ''), priority=v['priority'], status='todo', parent_task_id=task_id, assigned_to=v.get('assigned_to'), created_by=current_user.id, due_date=v.get('due_date'))
        db.session.add(subtask)
        db.session.flush()
        if subtask.assigned_to:
            notify_with_email(
                user_id=subtask.assigned_to,
                title='New Subtask Assigned',
                message=f'You have been assigned a new subtask: {subtask.title} (parent: {parent_task.title})',
                notif_type='task_assigned',
                related_task_id=subtask.id,
                send_email=True
            )
        db.session.commit()
        return jsonify({'message': 'Subtask created successfully', 'task': subtask.to_dict()}), 201
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({'error': 'Database error occurred.'}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500