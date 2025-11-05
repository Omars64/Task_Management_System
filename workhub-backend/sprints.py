from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from models import db, Sprint
from auth import get_current_user
from permissions import Permission
from validators import validator, ValidationError


sprints_bp = Blueprint('sprints', __name__)


@sprints_bp.route('/', methods=['GET'])
@jwt_required()
def list_sprints():
    try:
        current_user = get_current_user()
        if not current_user or not current_user.has_permission(Permission.SPRINTS_READ):
            return jsonify({'error': 'Access denied'}), 403
        project_id = request.args.get('project_id')
        query = Sprint.query
        if project_id:
            try:
                query = query.filter_by(project_id=int(project_id))
            except ValueError:
                return jsonify({'error': 'project_id must be an integer'}), 400
        sprints = query.order_by(Sprint.start_date.desc()).all()
        return jsonify([s.to_dict() for s in sprints]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@sprints_bp.route('/', methods=['POST'])
@jwt_required()
def create_sprint():
    try:
        current_user = get_current_user()
        if not current_user or not current_user.has_permission(Permission.SPRINTS_CREATE):
            return jsonify({'error': 'Access denied'}), 403
        payload = request.get_json(silent=True) or {}
        try:
            data = validator.validate_sprint_payload(payload, db=db.session)
        except ValidationError as e:
            return jsonify({'error': str(e)}), 400
        sprint = Sprint(
            project_id=data['project_id'],
            name=data['name'],
            goal=data['goal'],
            start_date=data['start_date'],
            end_date=data['end_date'],
        )
        db.session.add(sprint)
        db.session.commit()
        return jsonify({'message': 'Sprint created', 'sprint': sprint.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@sprints_bp.route('/<int:sprint_id>', methods=['GET'])
@jwt_required()
def get_sprint(sprint_id):
    try:
        current_user = get_current_user()
        if not current_user or not current_user.has_permission(Permission.SPRINTS_READ):
            return jsonify({'error': 'Access denied'}), 403
        sprint = Sprint.query.get(sprint_id)
        if not sprint:
            return jsonify({'error': 'Sprint not found'}), 404
        return jsonify(sprint.to_dict(include_project=True)), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@sprints_bp.route('/<int:sprint_id>', methods=['PUT'])
@jwt_required()
def update_sprint(sprint_id):
    try:
        current_user = get_current_user()
        if not current_user or not current_user.has_permission(Permission.SPRINTS_UPDATE):
            return jsonify({'error': 'Access denied'}), 403
        sprint = Sprint.query.get(sprint_id)
        if not sprint:
            return jsonify({'error': 'Sprint not found'}), 404
        payload = request.get_json(silent=True) or {}
        try:
            data = validator.validate_sprint_payload({**payload, 'project_id': payload.get('project_id', sprint.project_id)}, db=db.session)
        except ValidationError as e:
            return jsonify({'error': str(e)}), 400
        sprint.project_id = data['project_id']
        sprint.name = data['name']
        sprint.goal = data['goal']
        sprint.start_date = data['start_date']
        sprint.end_date = data['end_date']
        db.session.commit()
        return jsonify({'message': 'Sprint updated', 'sprint': sprint.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@sprints_bp.route('/<int:sprint_id>', methods=['DELETE'])
@jwt_required()
def delete_sprint(sprint_id):
    try:
        current_user = get_current_user()
        if not current_user or not current_user.has_permission(Permission.SPRINTS_DELETE):
            return jsonify({'error': 'Access denied'}), 403
        sprint = Sprint.query.get(sprint_id)
        if not sprint:
            return jsonify({'error': 'Sprint not found'}), 404
        db.session.delete(sprint)
        db.session.commit()
        return jsonify({'message': 'Sprint deleted'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


