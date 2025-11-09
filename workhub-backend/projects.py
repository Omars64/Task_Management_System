from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from models import db, Project
from auth import get_current_user
from permissions import Permission
from validators import validator, ValidationError


projects_bp = Blueprint('projects', __name__)


@projects_bp.route('/', methods=['GET'])
@jwt_required()
def list_projects():
    try:
        current_user = get_current_user()
        if not current_user or not current_user.has_permission(Permission.PROJECTS_READ):
            return jsonify({'error': 'Access denied'}), 403

        search = request.args.get('search')
        role = (current_user.role or '').lower()
        # Admin/super_admin can see all; others only see their projects
        if role in ['admin', 'super_admin']:
            query = Project.query
            if search:
                query = query.filter(Project.name.contains(search))
            projects = query.order_by(Project.created_at.desc()).all()
        else:
            from models import ProjectMember
            membership_project_ids = [m.project_id for m in ProjectMember.query.filter_by(user_id=current_user.id).all()]
            if not membership_project_ids:
                return jsonify([]), 200
            query = Project.query.filter(Project.id.in_(membership_project_ids))
            if search:
                query = query.filter(Project.name.contains(search))
            projects = query.order_by(Project.created_at.desc()).all()
        return jsonify([p.to_dict() for p in projects]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@projects_bp.route('/my', methods=['GET'])
@jwt_required()
def my_projects():
    try:
        current_user = get_current_user()
        if not current_user or not current_user.has_permission(Permission.PROJECTS_READ):
            return jsonify({'error': 'Access denied'}), 403
        from models import ProjectMember
        membership_project_ids = [m.project_id for m in ProjectMember.query.filter_by(user_id=current_user.id).all()]
        if not membership_project_ids:
            return jsonify([]), 200
        projects = Project.query.filter(Project.id.in_(membership_project_ids)).order_by(Project.created_at.desc()).all()
        return jsonify([p.to_dict() for p in projects]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@projects_bp.route('/', methods=['POST'])
@jwt_required()
def create_project():
    try:
        current_user = get_current_user()
        if not current_user or not current_user.has_permission(Permission.PROJECTS_CREATE):
            return jsonify({'error': 'Access denied'}), 403

        payload = request.get_json(silent=True) or {}
        try:
            data = validator.validate_project_payload(payload, db=db.session)
        except ValidationError as e:
            return jsonify({'error': str(e)}), 400

        project = Project(name=data['name'], description=data['description'], owner_id=data['owner_id'] or current_user.id)
        db.session.add(project)
        db.session.commit()
        return jsonify({'message': 'Project created', 'project': project.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@projects_bp.route('/<int:project_id>', methods=['GET'])
@jwt_required()
def get_project(project_id):
    try:
        current_user = get_current_user()
        if not current_user or not current_user.has_permission(Permission.PROJECTS_READ):
            return jsonify({'error': 'Access denied'}), 403
        project = Project.query.get(project_id)
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        # Non admins can only view if they are members
        role = (current_user.role or '').lower()
        if role not in ['admin', 'super_admin']:
            from models import ProjectMember
            if not ProjectMember.query.filter_by(project_id=project.id, user_id=current_user.id).first():
                return jsonify({'error': 'Access denied'}), 403
        # Include tasks, unique assignees, and members for the project
        from models import Task, User, ProjectMember
        from sqlalchemy.orm import joinedload
        
        # Eager load assignee to prevent N+1 queries
        tasks = Task.query.options(joinedload(Task.assignee)).filter_by(project_id=project.id).order_by(Task.created_at.desc()).all()
        assignee_ids = sorted({t.assigned_to for t in tasks if t.assigned_to})
        assignees = []
        if assignee_ids:
            users = User.query.filter(User.id.in_(assignee_ids)).all()
            assignees = [{'id': u.id, 'name': u.name, 'email': u.email, 'role': u.role} for u in users]

        # Members list - eager load user relationship to prevent N+1
        membership = []
        members = ProjectMember.query.options(joinedload(ProjectMember.user)).filter_by(project_id=project.id).all()
        for m in members:
            membership.append({'user_id': m.user_id, 'name': m.user.name if m.user else None, 'email': m.user.email if m.user else None, 'role': m.role, 'joined_at': m.joined_at.isoformat() if m.joined_at else None})

        data = project.to_dict(include_sprints=True)
        data['tasks'] = [t.to_dict() for t in tasks]
        data['assignees'] = assignees
        data['members'] = membership
        data['task_counts'] = {
            'total': len(tasks),
            'todo': len([t for t in tasks if t.status == 'todo']),
            'in_progress': len([t for t in tasks if t.status == 'in_progress']),
            'completed': len([t for t in tasks if t.status == 'completed'])
        }
        return jsonify(data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@projects_bp.route('/<int:project_id>', methods=['PUT'])
@jwt_required()
def update_project(project_id):
    try:
        current_user = get_current_user()
        if not current_user or not current_user.has_permission(Permission.PROJECTS_UPDATE):
            return jsonify({'error': 'Access denied'}), 403
        project = Project.query.get(project_id)
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        payload = request.get_json(silent=True) or {}
        try:
            data = validator.validate_project_payload(payload, db=db.session)
        except ValidationError as e:
            return jsonify({'error': str(e)}), 400
        project.name = data['name']
        project.description = data['description']
        project.owner_id = data['owner_id'] or project.owner_id
        db.session.commit()
        return jsonify({'message': 'Project updated', 'project': project.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@projects_bp.route('/<int:project_id>', methods=['DELETE'])
@jwt_required()
def delete_project(project_id):
    try:
        current_user = get_current_user()
        if not current_user or not current_user.has_permission(Permission.PROJECTS_DELETE):
            return jsonify({'error': 'Access denied'}), 403
        project = Project.query.get(project_id)
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        db.session.delete(project)
        db.session.commit()
        return jsonify({'message': 'Project deleted'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@projects_bp.route('/<int:project_id>/members', methods=['GET'])
@jwt_required()
def list_members(project_id):
    try:
        current_user = get_current_user()
        if not current_user or not current_user.has_permission(Permission.PROJECTS_READ):
            return jsonify({'error': 'Access denied'}), 403
        # Non admins can only list if they are members
        role = (current_user.role or '').lower()
        if role not in ['admin', 'super_admin']:
            from models import ProjectMember
            if not ProjectMember.query.filter_by(project_id=project_id, user_id=current_user.id).first():
                return jsonify({'error': 'Access denied'}), 403
        from models import ProjectMember
        members = ProjectMember.query.filter_by(project_id=project_id).all()
        return jsonify([
            {
                'user_id': m.user_id,
                'name': m.user.name if m.user else None,
                'email': m.user.email if m.user else None,
                'role': m.role,
                'joined_at': m.joined_at.isoformat() if m.joined_at else None
            }
            for m in members
        ]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@projects_bp.route('/<int:project_id>/members', methods=['POST'])
@jwt_required()
def add_member(project_id):
    try:
        current_user = get_current_user()
        if not current_user or not current_user.has_permission(Permission.PROJECTS_UPDATE):
            return jsonify({'error': 'Access denied'}), 403
        payload = request.get_json(silent=True) or {}
        user_id = payload.get('user_id')
        role = (payload.get('role') or '').strip() or None
        if not user_id:
            return jsonify({'error': 'user_id is required'}), 400
        from models import User, ProjectMember
        if not Project.query.get(project_id):
            return jsonify({'error': 'Project not found'}), 404
        if not User.query.get(user_id):
            return jsonify({'error': 'User not found'}), 404
        # Managers may only add within projects they belong to
        if (current_user.role or '').lower() == 'manager':
            if not ProjectMember.query.filter_by(project_id=project_id, user_id=current_user.id).first():
                return jsonify({'error': 'You may only manage members within your projects'}), 403
        existing = ProjectMember.query.filter_by(project_id=project_id, user_id=user_id).first()
        if existing:
            return jsonify({'message': 'User is already a member'}), 200
        membership = ProjectMember(project_id=project_id, user_id=user_id, role=role)
        db.session.add(membership)
        db.session.commit()
        return jsonify({'message': 'Member added'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@projects_bp.route('/<int:project_id>/members/<int:user_id>', methods=['DELETE'])
@jwt_required()
def remove_member(project_id, user_id):
    try:
        current_user = get_current_user()
        if not current_user or not current_user.has_permission(Permission.PROJECTS_UPDATE):
            return jsonify({'error': 'Access denied'}), 403
        from models import ProjectMember
        membership = ProjectMember.query.filter_by(project_id=project_id, user_id=user_id).first()
        if not membership:
            return jsonify({'error': 'Membership not found'}), 404
        if (current_user.role or '').lower() == 'manager':
            if not ProjectMember.query.filter_by(project_id=project_id, user_id=current_user.id).first():
                return jsonify({'error': 'You may only manage members within your projects'}), 403
        db.session.delete(membership)
        db.session.commit()
        return jsonify({'message': 'Member removed'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
