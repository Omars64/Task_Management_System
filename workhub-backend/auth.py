# workhub-backend/auth.py
from functools import wraps
from datetime import timedelta
import secrets
import string

from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    jwt_required,
    create_access_token,
    get_jwt_identity,
)

from models import db, User
from validators import validator, ValidationError  # relaxed, exception-based validator
from password_reset import PasswordResetService
from permissions import has_permission

# NOTE: No url_prefix here; app.py registers the blueprint with a prefix (e.g. "/api/auth")
auth_bp = Blueprint("auth", __name__)


# --------------------------- Helpers / Decorators ----------------------------

def admin_required(fn):
    """Decorator that ensures the requester is an authenticated admin."""
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        uid = get_jwt_identity()
        try:
            uid_int = int(uid) if uid is not None else None
        except (TypeError, ValueError):
            return jsonify({"error": "Invalid token"}), 401

        user = User.query.get(uid_int) if uid_int is not None else None
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Check for admin or super_admin role
        if user.role not in ["admin", "super_admin"]:
            return jsonify({"error": "Admin access required"}), 403
        return fn(*args, **kwargs)
    return wrapper

# Some parts of the app may import this name
require_admin = admin_required


def get_current_user():
    """Helper function to get the current authenticated user"""
    uid = get_jwt_identity()
    try:
        uid_int = int(uid) if uid is not None else None
    except (TypeError, ValueError):
        return None
    
    return User.query.get(uid_int)


def permission_required(permission):
    """
    Decorator that ensures the requester has a specific permission
    
    Usage:
        @permission_required("tasks.create")
        def create_task():
            ...
    """
    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            user = get_current_user()
            if not user:
                return jsonify({"error": "User not found"}), 404
            
            if not has_permission(user.role, permission):
                return jsonify({
                    "error": "Insufficient permissions",
                    "required_permission": permission
                }), 403
            
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def role_required(allowed_roles):
    """
    Decorator that ensures the requester has one of the allowed roles
    
    Usage:
        @role_required(["admin", "manager"])
        def some_function():
            ...
    """
    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            user = get_current_user()
            if not user:
                return jsonify({"error": "User not found"}), 404
            
            if user.role.lower() not in [role.lower() for role in allowed_roles]:
                return jsonify({
                    "error": "Insufficient permissions",
                    "required_roles": allowed_roles
                }), 403
            
            return fn(*args, **kwargs)
        return wrapper
    return decorator


# ------------------------------- Routes -------------------------------------

@auth_bp.post("/login")
def login():
    """
    JSON: { "email": "...", "password": "..." }
    Returns: { "access_token": "<JWT>", "user": {...} }
    """
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""

    # Validate email format only (not uniqueness) and basic presence
    try:
        validator.validate_email(email)  # format check only
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400

    if not password:
        return jsonify({"error": "Password is required"}), 400

    # Case-insensitive lookup
    user = User.query.filter(User.email.ilike(email)).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid email or password"}), 401
    
    # Check if user signup is approved
    if user.signup_status == 'pending':
        return jsonify({"error": "Your account is pending admin approval. Please wait for approval."}), 403
    
    if user.signup_status == 'rejected':
        return jsonify({"error": "Your account signup was rejected. Please contact support."}), 403

    # Check if user needs to change password
    force_password_change = getattr(user, 'force_password_change', False)
    
    # JWT subject (identity) must be a string; 30 minutes typical
    access_token = create_access_token(identity=str(user.id), expires_delta=timedelta(minutes=30))
    
    user_dict = user.to_dict()
    user_dict['force_password_change'] = force_password_change
    
    return jsonify({
        "access_token": access_token, 
        "user": user_dict
    }), 200


@auth_bp.post("/register")
@admin_required
def register():
    """
    Admin-only: create a new user account.
    JSON: { name, email, password, confirm, role('user'|'admin') }
    Mirrors /users POST and uses the same relaxed validation.
    """
    payload = request.get_json(silent=True) or {}
    try:
        data = validator.validate_user_payload(payload, db=db.session, check_unique_email=True)
        user = User(
            name=data["name"],
            email=data["email"],
            role=data["role"],
            signup_status='approved',  # Admin-created users are auto-approved
            email_verified=True  # Admin-created users don't need email verification
        )
        user.set_password(data["password"])
        db.session.add(user)
        db.session.commit()
        return jsonify({"message": "User registered", "user": user.to_dict()}), 201
    except ValidationError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Database error occurred."}), 500


@auth_bp.get("/me")
@jwt_required()
def me():
    uid = get_jwt_identity()
    try:
        uid_int = int(uid) if uid is not None else None
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid token"}), 401

    user = User.query.get(uid_int) if uid_int is not None else None
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user.to_dict()), 200


@auth_bp.post("/change-password")
@jwt_required()
def change_password():
    """
    JSON: { old_password, new_password, confirm (optional) }
    Enforces relaxed password rules; new must differ from old.
    """
    uid = get_jwt_identity()
    try:
        uid_int = int(uid) if uid is not None else None
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid token"}), 401

    user = User.query.get(uid_int) if uid_int is not None else None
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json(silent=True) or {}
    old_pw = data.get("old_password") or ""
    new_pw = data.get("new_password") or ""
    confirm = data.get("confirm", None)

    if not old_pw or not new_pw:
        return jsonify({"error": "Old password and new password are required"}), 400

    if not user.check_password(old_pw):
        return jsonify({"error": "Invalid old password"}), 401

    try:
        # relaxed rule: upper + lower + digit + special, 8–128
        new_pw = validator.validate_password(new_pw)
        if confirm is not None:
            validator.validate_password_confirmation(new_pw, confirm)
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400

    # Must be different from current
    if user.check_password(new_pw):
        return jsonify({"error": "New password must be different from current password"}), 400

    try:
        user.set_password(new_pw)
        # Clear force password change flag if it was set
        user.force_password_change = False
        db.session.commit()
        return jsonify({"message": "Password changed successfully"}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Database error occurred."}), 500


@auth_bp.post("/validate-email")
def validate_email_realtime():
    """
    Real-time email validation endpoint
    Checks email format, disposable domains, typos, and MX records
    
    JSON: { "email": "...", "check_mx": true/false }
    Returns: { "valid": bool, "errors": [], "warnings": [], "suggestions": [] }
    """
    data = request.get_json() or {}
    email = data.get("email", "").strip()
    check_mx = data.get("check_mx", True)  # Default to checking MX records
    
    if not email:
        return jsonify({
            "valid": False,
            "errors": ["Email is required"],
            "warnings": [],
            "suggestions": []
        }), 400
    
    # Import email validator
    try:
        from email_validator import email_validator
        result = email_validator.validate_email_comprehensive(email, check_mx=check_mx)
        return jsonify(result), 200
    except Exception as e:
        # Fallback to basic validation if email_validator fails
        try:
            validator.validate_email(email)
            return jsonify({
                "valid": True,
                "email": email,
                "normalized_email": email.lower(),
                "errors": [],
                "warnings": [],
                "suggestions": []
            }), 200
        except ValidationError as ve:
            return jsonify({
                "valid": False,
                "email": email,
                "normalized_email": "",
                "errors": [str(ve)],
                "warnings": [],
                "suggestions": []
            }), 200  # Return 200 with validation result


@auth_bp.get("/check-email-exists")
def check_email_exists():
    """
    Check if email exists in the database
    Used for registration to prevent duplicates
    
    Query param: ?email=...
    Returns: { "exists": bool, "message": "..." }
    """
    email = request.args.get("email", "").strip().lower()
    
    if not email:
        return jsonify({"error": "Email parameter required"}), 400
    
    # Check if email exists and is NOT in rejected state (rejected can re-apply)
    existing = User.query.filter(User.email.ilike(email)).first()
    exists = existing is not None and getattr(existing, 'signup_status', 'approved') != 'rejected'
    
    if exists:
        return jsonify({
            "exists": True,
            "message": "This email is already registered. Try logging in instead."
        }), 200
    else:
        return jsonify({
            "exists": False,
            "message": "Email is available"
        }), 200


@auth_bp.get("/account-status")
def account_status():
    """
    Lightweight account status lookup by email.
    Query: ?email=...
    Returns: { exists, email_verified, signup_status }
    """
    email = request.args.get("email", "").strip().lower()
    if not email:
        return jsonify({"error": "Email parameter required"}), 400
    user = User.query.filter(User.email.ilike(email)).first()
    if not user:
        return jsonify({
            "exists": False,
            "email_verified": False,
            "signup_status": None
        }), 200
    return jsonify({
        "exists": True,
        "email_verified": bool(getattr(user, 'email_verified', False)),
        "signup_status": getattr(user, 'signup_status', 'approved')
    }), 200


@auth_bp.post("/signup")
def signup():
    """
    Public signup endpoint - creates user with pending status
    JSON: { name, email, password, confirm }
    Returns: { "message": "...", "user_id": int, "needs_verification": true }
    """
    from flask import current_app
    from verification_service import verification_service
    
    payload = request.get_json(silent=True) or {}
    
    try:
        # First, normalize inputs and allow previously rejected users to re-apply
        # Validate fields but DO NOT require unique email yet
        prelim = {
            "name": validator.validate_name(payload.get("name", "")),
            "email": validator.validate_email(payload.get("email", ""), db=db.session, require_unique=False),
            "password": validator.validate_password(payload.get("password", "")),
        }
        if "confirm" in payload:
            validator.validate_password_confirmation(prelim["password"], payload.get("confirm"))

        # If an account with this email exists and was rejected, reset it to pending
        existing = User.query.filter(User.email.ilike(prelim["email"]) ).first()
        if existing and getattr(existing, 'signup_status', 'approved') == 'rejected':
            existing.name = prelim["name"]
            existing.set_password(prelim["password"])
            existing.signup_status = 'pending'
            existing.email_verified = False
            # Clear prior rejection metadata if present
            if hasattr(existing, 'rejection_reason'):
                existing.rejection_reason = None
            db.session.commit()
            user = existing
        else:
            # For new users (or duplicates not rejected), enforce unique constraint via validator
            data = validator.validate_user_payload(payload, db=db.session, check_unique_email=True)
            user = User(
                name=data["name"],
                email=data["email"],
                role='developer',
                signup_status='pending',
                email_verified=False
            )
            user.set_password(data["password"])
            db.session.add(user)
            db.session.commit()
        
        # Send verification code
        mail = current_app.extensions.get('mail')
        verification_result = {'email_sent': False, 'code': None}
        
        # Always call create_and_send_code (it handles None mail gracefully)
        verification_result = verification_service.create_and_send_code(user, mail)
        
        # NOTE: Admin notification is sent AFTER email verification (in verify-email endpoint)
        # This ensures admins only receive requests for users who have verified their email
        
        # SECURITY: Never include verification code in API response
        # Code is sent via email only (or logged server-side in development)
        response_data = {
            "message": "Signup successful! Please check your email for verification code.",
            "user_id": user.id,
            "needs_verification": True,
            "needs_approval": True,
            "email_sent": verification_result.get('email_sent', False)
        }
        
        # If email wasn't sent (dev mode), update message but don't expose code
        if not verification_result.get('email_sent'):
            response_data['message'] = "Signup successful! Verification code has been generated. Please check server logs for the code (email not configured)."
        
        return jsonify(response_data), 201
        
    except ValidationError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Signup failed: {str(e)}"}), 500


@auth_bp.post("/verify-email")
def verify_email():
    """
    Verify email with 6-digit code
    JSON: { "email": "...", "code": "123456" }
    Returns: { "message": "Email verified successfully!" }
    """
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip()
    code = (data.get("code") or "").strip()
    
    if not email or not code:
        return jsonify({"error": "Email and code are required"}), 400
    
    # Find user
    user = User.query.filter(User.email.ilike(email)).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Verify code
    from verification_service import verification_service
    success, message = verification_service.verify_code(user, code)
    
    if success:
        # After successful verification, notify user that admin approval is required (in background)
        try:
            from flask import current_app
            import threading
            mail = current_app.extensions.get('mail')
            if mail:
                def send_user_email_async():
                    try:
                        from flask_mail import Message
                        msg = Message(
                            subject="Email Verified - Pending Admin Approval",
                            recipients=[user.email],
                            html=f"""
                            <html>
                              <body style=\"font-family: Arial, sans-serif; line-height: 1.6; color: #333;\">
                                <div style=\"max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;\">
                                  <h2 style=\"color: #4CAF50;\">Thanks, {user.name}! Your email is verified.</h2>
                                  <p>Your account is now <strong>pending admin approval</strong>. You will receive an email once an administrator approves your access.</p>
                                  <p style=\"color:#666;font-size:14px;\">You can close this window. Try signing in after you receive the approval email.</p>
                                  <hr style=\"border:none;border-top:1px solid #eee;margin:30px 0;\">
                                  <p style=\"color:#999;font-size:12px;text-align:center;\">WorkHub Task Management System</p>
                                </div>
                              </body>
                            </html>
                            """,
                            body=f"""
                            Thanks, {user.name}! Your email is verified.
                            
                            Your account is now pending admin approval. You will receive an email once an administrator approves your access.
                            
                            WorkHub Task Management System
                            """
                        )
                        mail.send(msg)
                    except Exception as e:
                        print(f"Error sending user notification email: {e}")
                
                # Send in background thread
                thread = threading.Thread(target=send_user_email_async, daemon=True)
                thread.start()
        except Exception:
            # Non-fatal: continue even if email fails
            pass
        
        # NOW notify admins/superadmins about the new signup (only after email verification) - in background
        try:
            from flask import current_app
            import threading
            mail = current_app.extensions.get('mail')
            if mail:
                def send_admin_notification_async():
                    try:
                        verification_service.send_admin_notification(user, mail)
                    except Exception as e:
                        print(f"Failed to send admin notification: {e}")
                
                # Send in background thread
                thread = threading.Thread(target=send_admin_notification_async, daemon=True)
                thread.start()
        except Exception as e:
            print(f"Failed to send admin notification: {e}")
            # Non-fatal: continue even if admin notification fails
        
        return jsonify({"message": message, "verified": True}), 200
    else:
        return jsonify({"error": message, "verified": False}), 400


@auth_bp.post("/resend-verification")
def resend_verification():
    """
    Resend verification code
    JSON: { "email": "..." }
    Returns: { "message": "Verification code sent!" }
    """
    from flask import current_app
    from verification_service import verification_service
    
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip()
    
    if not email:
        return jsonify({"error": "Email is required"}), 400
    
    # Find user
    user = User.query.filter(User.email.ilike(email)).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    if user.email_verified:
        return jsonify({"message": "Email already verified"}), 200
    
    # Send new code
    mail = current_app.extensions.get('mail')
    
    # Always call create_and_send_code (it handles None mail gracefully)
    result = verification_service.create_and_send_code(user, mail)
    
    # SECURITY: Never include verification code in API response
    # Code is sent via email only (or logged server-side in development)
    response_data = {
        "message": "Verification code sent to your email",
        "email_sent": result.get('email_sent', False)
    }
    
    # If email wasn't sent (dev mode), update message but don't expose code
    if not result.get('email_sent'):
        response_data['message'] = "Verification code generated. Please check server logs for the code (email not configured)."
    
    return jsonify(response_data), 200


@auth_bp.get("/pending-users")
@admin_required
def get_pending_users():
    """
    Get all pending user signups (admin only)
    Returns: { "pending_users": [...] }
    """
    pending = User.query.filter_by(signup_status='pending').order_by(User.created_at.desc()).all()
    return jsonify({
        "pending_users": [u.to_dict(include_verification=True) for u in pending]
    }), 200


@auth_bp.get("/rejected-users")
@admin_required
def get_rejected_users():
    """
    Get all rejected user signups (admin only)
    Returns: { "rejected_users": [...] }
    """
    rejected = User.query.filter_by(signup_status='rejected').order_by(User.created_at.desc()).all()
    return jsonify({
        "rejected_users": [u.to_dict(include_verification=True) for u in rejected]
    }), 200


@auth_bp.post("/approve-user/<int:user_id>")
@admin_required
def approve_user(user_id):
    """
    Approve a pending user signup (admin only)
    JSON: {} (no body needed)
    Returns: { "message": "User approved successfully" }
    """
    from flask import current_app
    from verification_service import verification_service
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    if user.signup_status != 'pending':
        return jsonify({"error": "User is not pending approval"}), 400
    
    # Get admin who is approving
    admin_id = int(get_jwt_identity())
    
    # Approve user
    user.signup_status = 'approved'
    user.approved_by = admin_id
    from datetime import datetime
    user.approved_at = datetime.utcnow()
    
    db.session.commit()
    
    # Send approval email
    mail = current_app.extensions.get('mail')
    if mail:
        verification_service.send_approval_email(user, mail)
    
    return jsonify({
        "message": "User approved successfully",
        "user": user.to_dict()
    }), 200


@auth_bp.post("/reject-user/<int:user_id>")
@admin_required
def reject_user(user_id):
    """
    Reject a pending user signup (admin only)
    JSON: { "reason": "..." } (optional)
    Returns: { "message": "User rejected" }
    """
    from flask import current_app
    from verification_service import verification_service
    
    data = request.get_json(silent=True) or {}
    reason = data.get("reason", "").strip()
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    if user.signup_status != 'pending':
        return jsonify({"error": "User is not pending approval"}), 400
    
    # Reject user
    user.signup_status = 'rejected'
    user.rejection_reason = reason if reason else None
    from datetime import datetime
    user.approved_at = datetime.utcnow()
    user.approved_by = int(get_jwt_identity())
    
    db.session.commit()
    
    # Send rejection email in background thread to avoid blocking the API response
    mail = current_app.extensions.get('mail')
    if mail:
        import threading
        def send_email_async():
            try:
                verification_service.send_rejection_email(user, reason, mail)
            except Exception as e:
                print(f"Error sending rejection email in background: {str(e)}")
        
        # Start email sending in background thread
        thread = threading.Thread(target=send_email_async, daemon=True)
        thread.start()
    
    return jsonify({
        "message": "User rejected",
        "user": user.to_dict(include_verification=True)
    }), 200


# --------------------- Password Reset Endpoints ---------------------

@auth_bp.post("/forgot-password")
def forgot_password():
    """
    Request a password reset via email
    JSON: { "email": "..." }
    Returns: { "success": true, "message": "..." }
    """
    from flask import current_app
    
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()
    
    if not email:
        return jsonify({"error": "Email is required"}), 400
    
    # Validate email format
    try:
        validator.validate_email(email)
    except ValidationError:
        return jsonify({"error": "Invalid email format"}), 400
    
    # Get mail instance from app
    mail = current_app.extensions.get('mail')
    
    # Request password reset
    result = PasswordResetService.request_password_reset(email, mail)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 500


@auth_bp.post("/reset-password")
def reset_password():
    """
    Reset password using a valid token
    JSON: { "token": "...", "new_password": "..." }
    Returns: { "success": true, "message": "..." }
    """
    import sys
    import logging
    logger = logging.getLogger(__name__)
    
    # Force logging to stderr
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    
    # Force immediate output to stdout/stderr
    print("=" * 50, file=sys.stdout)
    print("RESET PASSWORD ENDPOINT CALLED", file=sys.stdout)
    print("=" * 50, file=sys.stdout)
    print("=" * 50, file=sys.stderr)
    print("RESET PASSWORD ENDPOINT CALLED", file=sys.stderr)
    print("=" * 50, file=sys.stderr)
    
    logger.error("=" * 50)
    logger.error("RESET PASSWORD ENDPOINT CALLED")
    logger.error("=" * 50)
    
    data = request.get_json(silent=True) or {}
    token = data.get("token", "").strip()
    new_password = data.get("new_password", "")
    
    # Debug logging - using logger.error to ensure visibility
    logger.error(f"RESET PASSWORD DEBUG - Token: {token[:20] if token else 'None'}, Password length: {len(new_password)}")
    logger.error(f"RESET PASSWORD DEBUG - Data keys: {list(data.keys())}")
    sys.stdout.flush()
    sys.stderr.flush()
    
    if not token:
        logger.error("RESET PASSWORD ERROR - No token provided")
        return jsonify({"error": "Reset token is required"}), 400
    
    if not new_password:
        logger.error("RESET PASSWORD ERROR - No password provided")
        return jsonify({"error": "New password is required"}), 400
    
    # Validate password
    try:
        validator.validate_password(new_password)
    except ValidationError as e:
        logger.error(f"RESET PASSWORD ERROR - Password validation failed: {e}")
        return jsonify({"error": str(e)}), 400
    
    # Reset password
    success, message = PasswordResetService.reset_password(token, new_password)
    
    if success:
        return jsonify({
            "success": True,
            "message": message
        }), 200
    else:
        return jsonify({
            "success": False,
            "error": message
        }), 400

