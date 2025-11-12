# workhub-backend/users.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import SQLAlchemyError

from models import db, User
from auth import admin_required, get_current_user
from permissions import Permission
from validators import validator, ValidationError  # <-- relaxed validator (exception-based)

users_bp = Blueprint("users", __name__)


@users_bp.route("/", methods=["GET"])
@jwt_required()
def get_users():
    """
    Get all approved users only (excludes pending/rejected signups)
    Pending users are accessed via /api/auth/pending-users
    """
    try:
        current_user = get_current_user()
        if not current_user or not current_user.has_permission(Permission.USERS_READ):
            return jsonify({"error": "Access denied"}), 403
        
        # Only return approved users who have verified their email
        users = User.query.filter_by(
            signup_status='approved'
        ).order_by(User.created_at.desc()).all()
        return jsonify([u.to_dict() for u in users]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@users_bp.route("/<int:user_id>", methods=["GET"])
@jwt_required()
def get_user(user_id: int):
    try:
        current_user_id = int(get_jwt_identity())
        current_user = User.query.get(current_user_id)

        # Users can view their own profile; users with USERS_READ permission can view any
        if current_user_id != user_id and (not current_user or not current_user.has_permission(Permission.USERS_READ)):
            return jsonify({"error": "Access denied"}), 403

        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        return jsonify(user.to_dict()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@users_bp.route("/", methods=["POST"])
@jwt_required()
def create_user():
    """
    Admin creates a new user.
    Expected JSON: { name, email, password, confirm (optional), role: 'user'|'admin', send_verification: bool }
    - Name: letters/spaces/hyphen/apostrophe only, 2–50 chars (no digits)
    - Password: 8–128, must include upper+lower+digit+special
    - send_verification: if true, sends 6-digit verification code to email
    """
    from flask import current_app
    from verification_service import verification_service
    
    current_user = get_current_user()
    if not current_user or not current_user.has_permission(Permission.USERS_CREATE):
        return jsonify({"error": "Access denied"}), 403
    
    payload = request.get_json(silent=True) or {}
    try:
        data = validator.validate_user_payload(payload, db=db.session, check_unique_email=True)
        send_verification = payload.get("send_verification", False)

        user = User(
            name=data["name"],
            email=data["email"],
            role=data["role"],
            signup_status='approved',  # Admin-created users are auto-approved
            email_verified=False if send_verification else True,  # If sending verification, mark as unverified
        )
        # models.User should provide set_password() (hashes internally)
        user.set_password(data["password"])

        db.session.add(user)
        db.session.commit()
        
        # Send verification code if requested
        if send_verification:
            mail = current_app.extensions.get('mail')
            if mail:
                verification_service.create_and_send_code(user, mail)
        
        return jsonify({
            "message": "User created successfully" + (" - verification code sent" if send_verification else ""),
            "user": user.to_dict(),
            "verification_sent": send_verification
        }), 201

    except ValidationError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Database error occurred."}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@users_bp.route("/<int:user_id>", methods=["PUT"])
@jwt_required()
def update_user(user_id: int):
    """
    Partial update.
    Admins can edit anyone; non-admins can only edit themselves.
    Allowed fields: name, email, role (admin only), password (+confirm), theme, language, notifications_enabled
    """
    data = request.get_json(silent=True) or {}

    try:
        current_user_id = int(get_jwt_identity())
        current_user = User.query.get(current_user_id)

        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Only users with USERS_UPDATE permission can edit other users
        if current_user_id != user_id and (not current_user or not current_user.has_permission(Permission.USERS_UPDATE)):
            return jsonify({"error": "Access denied"}), 403

        # ---- Field-by-field validation (relaxed rules) ----
        if "name" in data:
            user.name = validator.validate_name(data["name"])

        if "email" in data and data["email"] != user.email:
            user.email = validator.validate_email(data["email"], db=db.session, require_unique=True)

        if "role" in data:
            # Only users with USERS_ASSIGN_ROLE permission can change role
            if not current_user or not current_user.has_permission(Permission.USERS_ASSIGN_ROLE):
                return jsonify({"error": "Only users with role assignment permission can change roles"}), 403
            role = (data["role"] or "").lower()
            valid_roles = {"super_admin", "admin", "manager", "team_lead", "developer", "viewer"}
            if role not in valid_roles:
                raise ValidationError(f"Role must be one of: {', '.join(valid_roles)}.")

            # Constraints:
            # - Admins may NOT assign super_admin to anyone; they can set only up to 'admin'
            # - Super Admin may assign ANY role (including super_admin)
            actor_role = (current_user.role or "viewer").lower()
            if actor_role == "admin" and role == "super_admin":
                return jsonify({"error": "Admins cannot assign the Super Admin role."}), 403
            if actor_role != "super_admin" and role == "super_admin":
                return jsonify({"error": "Only Super Admin may assign the Super Admin role."}), 403

            user.role = role

        if "password" in data:
            pw = validator.validate_password(data["password"])
            if "confirm" in data:
                validator.validate_password_confirmation(pw, data["confirm"])
            user.set_password(pw)

        # Personal settings (no special validation needed here)
        if "theme" in data:
            user.theme = data["theme"]
        if "language" in data:
            user.language = data["language"]
        if "notifications_enabled" in data:
            user.notifications_enabled = data["notifications_enabled"]

        db.session.commit()
        return jsonify({"message": "User updated successfully", "user": user.to_dict()}), 200

    except ValidationError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Database error occurred."}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@users_bp.route("/<int:user_id>", methods=["DELETE"])
@jwt_required()
def delete_user(user_id: int):
    """
    Requires users.delete permission. Prevent self-deletion.
    """
    try:
        current_user = get_current_user()
        if not current_user or not current_user.has_permission(Permission.USERS_DELETE):
            return jsonify({"error": "Access denied"}), 403
        
        current_user_id = int(get_jwt_identity())
        if current_user_id == user_id:
            return jsonify({"error": "Cannot delete your own account"}), 400

        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Safeguard: Admins (or any non-super_admin) cannot delete a super_admin account
        actor_role = (current_user.role or "viewer").lower()
        target_role = (user.role or "viewer").lower()
        if target_role == 'super_admin' and actor_role != 'super_admin':
            return jsonify({"error": "Only a Super Admin can delete a Super Admin account"}), 403

        # Cleanup dependent references to avoid FK errors
        from models import (
            Task, TimeLog, Comment, FileAttachment, NotificationPreference,
            Reminder, Meeting, MeetingInvitation, ChatConversation, ChatMessage,
            ProjectMember, Project, Notification, MessageReaction,
            ChatGroup, ChatGroupMember, GroupMessage, GroupMessageRead,
            GroupMessageReaction, GroupInvitation
        )
        
        # Null out task references
        Task.query.filter_by(assigned_to=user_id).update({Task.assigned_to: None}, synchronize_session=False)
        Task.query.filter_by(created_by=user_id).update({Task.created_by: None}, synchronize_session=False)
        db.session.flush()
        
        # Null out project owner references (or delete if no other members)
        projects_owned = Project.query.filter_by(owner_id=user_id).all()
        for project in projects_owned:
            # Check if project has other members
            other_members = ProjectMember.query.filter(
                ProjectMember.project_id == project.id,
                ProjectMember.user_id != user_id
            ).first()
            if other_members:
                # Reassign to first other member
                project.owner_id = other_members.user_id
            else:
                # No other members, delete the project (cascade will handle members)
                db.session.delete(project)
        db.session.flush()
        
        # Delete user-owned data
        TimeLog.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        Comment.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        FileAttachment.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        NotificationPreference.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        Reminder.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        Notification.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        db.session.flush()
        
        # Delete meeting invitations
        MeetingInvitation.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        # Delete meetings created by user (cascade will handle invitations)
        Meeting.query.filter_by(created_by=user_id).delete(synchronize_session=False)
        db.session.flush()
        
        # Delete chat conversations (where user is user1, user2, or requester)
        from sqlalchemy import or_
        ChatConversation.query.filter(
            or_(
                ChatConversation.user1_id == user_id,
                ChatConversation.user2_id == user_id,
                ChatConversation.requested_by == user_id
            )
        ).delete(synchronize_session=False)
        db.session.flush()
        
        # Delete chat messages
        ChatMessage.query.filter(
            or_(
                ChatMessage.sender_id == user_id,
                ChatMessage.recipient_id == user_id
            )
        ).delete(synchronize_session=False)
        db.session.flush()
        
        # Delete message reactions
        MessageReaction.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        db.session.flush()
        
        # Delete project memberships
        ProjectMember.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        db.session.flush()
        
        # Delete group memberships and related data
        ChatGroupMember.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        GroupMessageRead.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        GroupMessageReaction.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        GroupInvitation.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        # Delete group messages sent by user
        GroupMessage.query.filter_by(sender_id=user_id).delete(synchronize_session=False)
        # Delete groups created by user (cascade will handle members/messages)
        ChatGroup.query.filter_by(created_by=user_id).delete(synchronize_session=False)
        db.session.flush()

        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": "User deleted successfully"}), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        import traceback
        print(f"[User Deletion Error] SQLAlchemyError: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": f"Database error occurred: {str(e)}"}), 500
    except Exception as e:
        db.session.rollback()
        import traceback
        print(f"[User Deletion Error] Exception: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


@users_bp.route("/<int:user_id>/details", methods=["GET"])
@jwt_required()
def get_user_details(user_id: int):
    """
    Requires users.read permission: Get complete user details including password hash
    Returns: Full user object with all fields including sensitive data
    """
    try:
        current_user = get_current_user()
        if not current_user or not current_user.has_permission(Permission.USERS_READ):
            return jsonify({"error": "Access denied"}), 403
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Return full user details including password hash for admin
        details = user.to_dict(include_verification=True)
        details['password_hash'] = user.password_hash
        details['reset_token'] = user.reset_token
        details['reset_token_expires'] = user.reset_token_expires.isoformat() if user.reset_token_expires else None
        details['force_password_change'] = getattr(user, 'force_password_change', False)
        
        return jsonify(details), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
