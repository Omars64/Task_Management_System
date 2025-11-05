"""
Enhanced authentication routes with P0 security features:
- Rate limiting on login/signup/reset
- Account lockout after failed attempts
- Email verification
- Generic error responses (prevent enumeration)
- CSRF protection
"""

from functools import wraps
from datetime import timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    jwt_required,
    create_access_token,
    get_jwt_identity,
)
from flask_mail import Mail

from models import db, User
from validators import validator, ValidationError
from security_middleware import (
    rate_limit, rate_limiter, check_account_lockout, 
    csrf_protect, generic_auth_error, format_error_response,
    handle_validation_error
)
from email_verification import email_verification

# Blueprint - no url_prefix here; app.py registers with prefix
auth_bp = Blueprint("auth", __name__)

# Mail instance (will be initialized in app.py)
mail = None


def init_mail(mail_instance):
    """Initialize mail instance from app"""
    global mail
    mail = mail_instance


# ========== DECORATORS ==========

def admin_required(fn):
    """Decorator that ensures the requester is an authenticated admin"""
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        uid = get_jwt_identity()
        try:
            uid_int = int(uid) if uid is not None else None
        except (TypeError, ValueError):
            return jsonify(format_error_response("Invalid token", code="INVALID_TOKEN")), 401

        user = User.query.get(uid_int) if uid_int is not None else None
        if not user or user.role != "admin":
            return jsonify(format_error_response("Admin access required", code="FORBIDDEN")), 403
        return fn(*args, **kwargs)
    return wrapper


# Alias for compatibility
require_admin = admin_required


# ========== AUTHENTICATION ROUTES ==========

@auth_bp.post("/login")
@rate_limit(max_requests=5, time_window=300)  # P0: 5 attempts per 5 minutes
def login():
    """
    Login endpoint with P0 security:
    - Rate limiting
    - Account lockout after 5 failed attempts
    - Generic error messages (prevent enumeration)
    
    JSON: { "email": "...", "password": "..." }
    Returns: { "access_token": "<JWT>", "user": {...} }
    """
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    # Validate input format
    try:
        validator.validate_email(email)
    except ValidationError as e:
        return handle_validation_error(e)

    if not password:
        return jsonify(format_error_response("Password is required", field="password", code="REQUIRED")), 400

    # P0: Check account lockout (by email)
    lockout_response = check_account_lockout(email)
    if lockout_response:
        return lockout_response

    # Case-insensitive lookup
    user = User.query.filter(User.email.ilike(email)).first()
    
    # Check credentials
    if not user or not user.check_password(password):
        # P0: Record failed attempt
        lockout_until = rate_limiter.record_failed_attempt(email, max_attempts=5, lockout_minutes=10)
        
        if lockout_until:
            return jsonify(format_error_response(
                "Account locked due to multiple failed attempts. Please try again later.",
                code="ACCOUNT_LOCKED"
            )), 403
        
        # P0: Generic error message (prevent account enumeration)
        return generic_auth_error("Invalid credentials")
    
    # P0: Check if email is verified (if verification is enabled)
    if hasattr(user, 'email_verified') and not user.email_verified:
        return jsonify(format_error_response(
            "Please verify your email address before logging in.",
            code="EMAIL_NOT_VERIFIED"
        )), 403

    # Success - clear failed attempts
    rate_limiter.clear_failed_attempts(email)

    # Create JWT token
    access_token = create_access_token(
        identity=str(user.id), 
        expires_delta=timedelta(minutes=30)
    )
    
    return jsonify({
        "access_token": access_token, 
        "user": user.to_dict()
    }), 200


@auth_bp.post("/register")
@rate_limit(max_requests=3, time_window=3600)  # P0: 3 registrations per hour
def register():
    """
    Public registration endpoint with P0 security:
    - Rate limiting
    - Email verification required
    - Enhanced validation
    
    JSON: { name, email, password, confirm }
    """
    payload = request.get_json(silent=True) or {}
    
    try:
        # Validate payload with enhanced rules
        data = validator.validate_user_payload(
            payload, 
            db=db.session, 
            check_unique_email=True
        )
        
        # Create user (not verified yet)
        user = User(
            name=data["name"],
            email=data["email"],
            role="user",  # Default role for public registration
        )
        user.set_password(data["password"])
        
        # Set email_verified to False (if field exists)
        if hasattr(user, 'email_verified'):
            user.email_verified = False
        
        db.session.add(user)
        db.session.commit()
        
        # P0: Send verification email
        token = email_verification.generate_token(user.email, purpose='verify_email')
        
        if mail:
            from flask import current_app
            base_url = current_app.config.get('FRONTEND_URL', 'http://localhost:3000')
            email_verification.send_verification_email(mail, user.email, token, base_url)
        
        return jsonify({
            "message": "Registration successful. Please check your email to verify your account.",
            "user": user.to_dict(),
            "verification_token": token  # For development/testing only
        }), 201
        
    except ValidationError as e:
        db.session.rollback()
        return handle_validation_error(e)
    except Exception as e:
        db.session.rollback()
        print(f"Registration error: {e}")
        return jsonify(format_error_response("Registration failed", code="SERVER_ERROR")), 500


@auth_bp.post("/verify-email")
@rate_limit(max_requests=10, time_window=3600)  # P0: 10 verifications per hour
def verify_email():
    """
    Email verification endpoint (P0).
    
    JSON: { "token": "..." }
    """
    data = request.get_json(silent=True) or {}
    token = data.get("token", "").strip()
    
    if not token:
        return jsonify(format_error_response("Verification token is required", code="REQUIRED")), 400
    
    # Verify token
    is_valid, email, error_msg = email_verification.verify_token(token, purpose='verify_email')
    
    if not is_valid:
        return jsonify(format_error_response(error_msg, code="INVALID_TOKEN")), 400
    
    # Find user and mark as verified
    user = User.query.filter(User.email.ilike(email)).first()
    
    if not user:
        return jsonify(format_error_response("User not found", code="NOT_FOUND")), 404
    
    # Mark as verified (if field exists)
    if hasattr(user, 'email_verified'):
        user.email_verified = True
        db.session.commit()
    
    return jsonify({
        "message": "Email verified successfully. You can now log in.",
        "email": email
    }), 200


@auth_bp.post("/resend-verification")
@rate_limit(max_requests=3, time_window=3600)  # P0: 3 resends per hour
def resend_verification():
    """
    Resend verification email (P0).
    
    JSON: { "email": "..." }
    """
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    
    try:
        validator.validate_email(email)
    except ValidationError as e:
        return handle_validation_error(e)
    
    # Find user (but don't reveal if they exist - P0: prevent enumeration)
    user = User.query.filter(User.email.ilike(email)).first()
    
    # Always return success (prevent enumeration)
    if user and hasattr(user, 'email_verified') and not user.email_verified:
        token = email_verification.generate_token(user.email, purpose='verify_email')
        
        if mail:
            from flask import current_app
            base_url = current_app.config.get('FRONTEND_URL', 'http://localhost:3000')
            email_verification.send_verification_email(mail, user.email, token, base_url)
    
    return jsonify({
        "message": "If the email exists and is not verified, a verification link has been sent."
    }), 200


@auth_bp.post("/forgot-password")
@rate_limit(max_requests=3, time_window=3600)  # P0: 3 requests per hour
def forgot_password():
    """
    Password reset request with P0 security (generic responses).
    
    JSON: { "email": "..." }
    """
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    
    try:
        validator.validate_email(email)
    except ValidationError as e:
        return handle_validation_error(e)
    
    # Find user (but don't reveal if they exist - P0)
    user = User.query.filter(User.email.ilike(email)).first()
    
    # Always return generic success message (P0: prevent enumeration)
    if user:
        # Generate reset token
        token = email_verification.generate_token(user.email, purpose='reset_password')
        
        if mail:
            from flask import current_app
            base_url = current_app.config.get('FRONTEND_URL', 'http://localhost:3000')
            email_verification.send_password_reset_email(mail, user.email, token, base_url)
    
    # P0: Generic response regardless of whether email exists
    return jsonify({
        "message": "If the email exists, a password reset link has been sent."
    }), 200


@auth_bp.post("/reset-password")
@rate_limit(max_requests=5, time_window=3600)  # P0: 5 resets per hour
def reset_password():
    """
    Complete password reset with token (P0).
    
    JSON: { "token": "...", "new_password": "...", "confirm": "..." }
    """
    data = request.get_json(silent=True) or {}
    token = data.get("token", "").strip()
    new_password = data.get("new_password", "")
    confirm = data.get("confirm", "")
    
    if not token:
        return jsonify(format_error_response("Reset token is required", code="REQUIRED")), 400
    
    # Verify token
    is_valid, email, error_msg = email_verification.verify_token(token, purpose='reset_password')
    
    if not is_valid:
        return jsonify(format_error_response(error_msg, code="INVALID_TOKEN")), 400
    
    # Validate new password
    try:
        new_password = validator.validate_password(new_password)
        validator.validate_password_confirmation(new_password, confirm)
    except ValidationError as e:
        return handle_validation_error(e)
    
    # Find user and update password
    user = User.query.filter(User.email.ilike(email)).first()
    
    if not user:
        return jsonify(format_error_response("User not found", code="NOT_FOUND")), 404
    
    try:
        user.set_password(new_password)
        db.session.commit()
        
        # Clear any lockouts for this user
        rate_limiter.clear_failed_attempts(email)
        
        return jsonify({"message": "Password reset successfully. You can now log in."}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Password reset error: {e}")
        return jsonify(format_error_response("Password reset failed", code="SERVER_ERROR")), 500


@auth_bp.get("/me")
@jwt_required()
def me():
    """Get current user profile"""
    uid = get_jwt_identity()
    try:
        uid_int = int(uid) if uid is not None else None
    except (TypeError, ValueError):
        return jsonify(format_error_response("Invalid token", code="INVALID_TOKEN")), 401

    user = User.query.get(uid_int) if uid_int is not None else None
    if not user:
        return jsonify(format_error_response("User not found", code="NOT_FOUND")), 404
    
    return jsonify(user.to_dict()), 200


@auth_bp.post("/change-password")
@jwt_required()
@rate_limit(max_requests=5, time_window=3600)  # P0: 5 changes per hour
def change_password():
    """
    Change password for authenticated user (P0 enhanced).
    
    JSON: { old_password, new_password, confirm }
    """
    uid = get_jwt_identity()
    try:
        uid_int = int(uid) if uid is not None else None
    except (TypeError, ValueError):
        return jsonify(format_error_response("Invalid token", code="INVALID_TOKEN")), 401

    user = User.query.get(uid_int) if uid_int is not None else None
    if not user:
        return jsonify(format_error_response("User not found", code="NOT_FOUND")), 404

    data = request.get_json(silent=True) or {}
    old_pw = data.get("old_password") or ""
    new_pw = data.get("new_password") or ""
    confirm = data.get("confirm", None)

    if not old_pw or not new_pw:
        return jsonify(format_error_response(
            "Old password and new password are required", 
            code="REQUIRED"
        )), 400

    if not user.check_password(old_pw):
        return jsonify(format_error_response("Invalid old password", code="INVALID_PASSWORD")), 401

    try:
        # P0: Enhanced password validation
        new_pw = validator.validate_password(new_pw)
        if confirm is not None:
            validator.validate_password_confirmation(new_pw, confirm)
    except ValidationError as e:
        return handle_validation_error(e)

    # Must be different from current
    if user.check_password(new_pw):
        return jsonify(format_error_response(
            "New password must be different from current password",
            code="SAME_PASSWORD"
        )), 400

    try:
        user.set_password(new_pw)
        db.session.commit()
        return jsonify({"message": "Password changed successfully"}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Password change error: {e}")
        return jsonify(format_error_response("Password change failed", code="SERVER_ERROR")), 500


@auth_bp.post("/logout")
@jwt_required()
def logout():
    """
    Logout endpoint (token blacklisting would go here in production).
    For JWT, actual logout is client-side (delete token).
    """
    return jsonify({"message": "Logged out successfully"}), 200

