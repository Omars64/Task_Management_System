from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from sqlalchemy import or_

from models import db, Meeting, MeetingInvitation, User, Project, ProjectMember
from auth import get_current_user
from notifications import create_notification_with_email
from validators import validator, ValidationError

meetings_bp = Blueprint('meetings', __name__)


@meetings_bp.route('/', methods=['GET'])
@jwt_required()
def get_meetings():
    """Get meetings for current user (created or invited)"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'Unauthorized'}), 401

        # Get date range
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')

        query = Meeting.query.filter(
            or_(
                Meeting.created_by == current_user.id,
                Meeting.id.in_(
                    db.session.query(MeetingInvitation.meeting_id).filter_by(user_id=current_user.id)
                )
            )
        )

        if start_date_str and end_date_str:
            try:
                start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
                end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
                query = query.filter(
                    Meeting.start_time >= start_date,
                    Meeting.end_time <= end_date
                )
            except Exception:
                pass

        meetings = query.order_by(Meeting.start_time.asc()).all()
        return jsonify([m.to_dict() for m in meetings]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@meetings_bp.route('/', methods=['POST'])
@jwt_required()
def create_meeting():
    """Create a new meeting"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'Unauthorized'}), 401

        payload = request.get_json(silent=True) or {}
        
        # Validate required fields
        title = payload.get('title', '').strip()
        if not title:
            return jsonify({'error': 'Title is required'}), 400

        start_time_str = payload.get('start_time')
        end_time_str = payload.get('end_time')
        if not start_time_str or not end_time_str:
            return jsonify({'error': 'Start time and end time are required'}), 400

        try:
            start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
        except Exception:
            return jsonify({'error': 'Invalid date format. Use ISO 8601 format.'}), 400

        if end_time <= start_time:
            return jsonify({'error': 'End time must be after start time'}), 400

        project_id = payload.get('project_id')
        if project_id:
            project = Project.query.get(project_id)
            if not project:
                return jsonify({'error': 'Project not found'}), 404

        meeting = Meeting(
            title=title,
            description=payload.get('description', '').strip(),
            start_time=start_time,
            end_time=end_time,
            location=payload.get('location', '').strip(),
            created_by=current_user.id,
            project_id=project_id
        )
        
        db.session.add(meeting)
        db.session.flush()

        # Create invitations
        invite_user_ids = payload.get('invite_user_ids', [])
        for user_id in invite_user_ids:
            user = User.query.get(user_id)
            if user and user.id != current_user.id:
                invitation = MeetingInvitation(
                    meeting_id=meeting.id,
                    user_id=user_id,
                    status='pending'
                )
                db.session.add(invitation)
                
                # Send notification
                create_notification_with_email(
                    user_id=user_id,
                    title='Meeting Invitation',
                    message=f'{current_user.name} invited you to a meeting: {title}',
                    notif_type='meeting_invitation',
                    related_task_id=None,
                    send_email=True
                )

        db.session.commit()
        
        return jsonify({'message': 'Meeting created successfully', 'meeting': meeting.to_dict()}), 201

    except SQLAlchemyError as e:
        db.session.rollback()
        import traceback
        print(f"[Meeting Creation Error] SQLAlchemyError: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': f'Database error occurred: {str(e)}'}), 500
    except Exception as e:
        db.session.rollback()
        import traceback
        print(f"[Meeting Creation Error] Exception: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@meetings_bp.route('/<int:meeting_id>', methods=['PUT'])
@jwt_required()
def update_meeting(meeting_id):
    """Update a meeting"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'Unauthorized'}), 401

        meeting = Meeting.query.get(meeting_id)
        if not meeting:
            return jsonify({'error': 'Meeting not found'}), 404

        if meeting.created_by != current_user.id:
            return jsonify({'error': 'Only the creator can update the meeting'}), 403

        payload = request.get_json(silent=True) or {}
        
        if 'title' in payload:
            meeting.title = payload['title'].strip()
        if 'description' in payload:
            meeting.description = payload['description'].strip()
        if 'start_time' in payload:
            try:
                meeting.start_time = datetime.fromisoformat(payload['start_time'].replace('Z', '+00:00'))
            except Exception:
                return jsonify({'error': 'Invalid start_time format'}), 400
        if 'end_time' in payload:
            try:
                meeting.end_time = datetime.fromisoformat(payload['end_time'].replace('Z', '+00:00'))
            except Exception:
                return jsonify({'error': 'Invalid end_time format'}), 400
        if 'location' in payload:
            meeting.location = payload['location'].strip()
        if 'project_id' in payload:
            meeting.project_id = payload['project_id']

        # Add new invitations
        new_invite_user_ids = payload.get('invite_user_ids', [])
        existing_user_ids = [inv.user_id for inv in meeting.invitations]
        
        for user_id in new_invite_user_ids:
            if user_id not in existing_user_ids and user_id != current_user.id:
                user = User.query.get(user_id)
                if user:
                    invitation = MeetingInvitation(
                        meeting_id=meeting.id,
                        user_id=user_id,
                        status='pending'
                    )
                    db.session.add(invitation)
                    
                    create_notification_with_email(
                        user_id=user_id,
                        title='Meeting Invitation',
                        message=f'{current_user.name} invited you to a meeting: {meeting.title}',
                        notif_type='meeting_invitation',
                        related_task_id=None,
                        send_email=True
                    )

        db.session.commit()
        return jsonify({'message': 'Meeting updated successfully', 'meeting': meeting.to_dict()}), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': 'Database error occurred.'}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@meetings_bp.route('/<int:meeting_id>', methods=['DELETE'])
@jwt_required()
def delete_meeting(meeting_id):
    """Delete a meeting"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'Unauthorized'}), 401

        meeting = Meeting.query.get(meeting_id)
        if not meeting:
            return jsonify({'error': 'Meeting not found'}), 404

        # Allow deletion by creator or admins
        role = (current_user.role or '').lower().replace(' ', '_')
        is_creator = meeting.created_by == current_user.id
        is_admin = role in ('admin', 'super_admin')
        
        print(f"[DELETE DEBUG] Meeting ID: {meeting_id}, Created by: {meeting.created_by}, Current user: {current_user.id}, Role: {role}, Is creator: {is_creator}, Is admin: {is_admin}")
        
        if not is_creator and not is_admin:
            return jsonify({'error': 'Only the creator or an admin can delete the meeting'}), 403

        db.session.delete(meeting)
        db.session.commit()
        return jsonify({'message': 'Meeting deleted successfully'}), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': 'Database error occurred.'}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@meetings_bp.route('/<int:meeting_id>/invitations/<int:invitation_id>/respond', methods=['POST'])
@jwt_required()
def respond_to_invitation(meeting_id, invitation_id):
    """Respond to a meeting invitation (confirm or reject)"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'Unauthorized'}), 401

        invitation = MeetingInvitation.query.get(invitation_id)
        if not invitation:
            return jsonify({'error': 'Invitation not found'}), 404

        if invitation.user_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403

        if invitation.meeting_id != meeting_id:
            return jsonify({'error': 'Invitation does not belong to this meeting'}), 400

        if invitation.status != 'pending':
            return jsonify({'error': 'Invitation has already been responded to'}), 400

        payload = request.get_json(silent=True) or {}
        status = payload.get('status')  # 'confirmed' or 'rejected'
        rejection_reason = payload.get('rejection_reason', '').strip()

        if status not in ['confirmed', 'rejected']:
            return jsonify({'error': 'Status must be "confirmed" or "rejected"'}), 400

        if status == 'rejected' and not rejection_reason:
            return jsonify({'error': 'Rejection reason is required when rejecting'}), 400

        invitation.status = status
        invitation.rejection_reason = rejection_reason if status == 'rejected' else None
        invitation.responded_at = datetime.utcnow()

        db.session.commit()

        # Notify meeting creator
        meeting = Meeting.query.get(meeting_id)
        if meeting:
            status_text = 'confirmed' if status == 'confirmed' else 'rejected'
            create_notification_with_email(
                user_id=meeting.created_by,
                title='Meeting Response',
                message=f'{current_user.name} {status_text} your meeting invitation: {meeting.title}',
                notif_type='meeting_response',
                related_task_id=None,
                send_email=True
            )

        return jsonify({'message': f'Invitation {status} successfully', 'invitation': invitation.to_dict()}), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': 'Database error occurred.'}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@meetings_bp.route('/<int:meeting_id>/invitations', methods=['GET'])
@jwt_required()
def get_meeting_invitations(meeting_id):
    """Get all invitations for a meeting"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'Unauthorized'}), 401

        meeting = Meeting.query.get(meeting_id)
        if not meeting:
            return jsonify({'error': 'Meeting not found'}), 404

        # Only creator or invited users can view
        if meeting.created_by != current_user.id:
            invitation = MeetingInvitation.query.filter_by(meeting_id=meeting_id, user_id=current_user.id).first()
            if not invitation:
                return jsonify({'error': 'Access denied'}), 403

        invitations = MeetingInvitation.query.filter_by(meeting_id=meeting_id).all()
        return jsonify([inv.to_dict() for inv in invitations]), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

