"""Password Reset Service - Handles secure password reset flow"""

import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from flask import current_app
from flask_mail import Message
from models import db, User

class PasswordResetService:
    """Service for handling password resets"""
    
    @staticmethod
    def generate_reset_token():
        """Generate a secure random token for password reset"""
        # Generate a cryptographically secure random token
        token = secrets.token_urlsafe(32)
        # Hash it before storing (additional security layer)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        return token, token_hash
    
    @staticmethod
    def create_reset_link(token):
        """Create the full password reset link"""
        frontend_url = current_app.config.get('FRONTEND_URL', 'http://localhost:3000')
        return f"{frontend_url}/reset-password?token={token}"
    
    @staticmethod
    def send_reset_email(user_email, reset_token, mail):
        """Send password reset email with link"""
        from flask import current_app
        app = current_app._get_current_object() if hasattr(current_app, '_get_current_object') else current_app
        
        if not mail:
            print(f"✗ Mail instance not available - cannot send password reset email to {user_email}")
            return False
        
        # Verify mail configuration (re-load if necessary)
        mail_username = app.config.get('MAIL_USERNAME') or app.config.get('SMTP_USERNAME', '')
        mail_password = app.config.get('MAIL_PASSWORD') or app.config.get('SMTP_PASSWORD', '')
        
        # If not in app.config, try loading from SystemSettings database
        if not mail_username or not mail_password:
            try:
                from models import SystemSettings
                settings = SystemSettings.query.first()
                if settings and settings.smtp_username and settings.smtp_password:
                    mail_username = settings.smtp_username
                    mail_password = settings.smtp_password
                    # Update app.config for future use
                    app.config['MAIL_USERNAME'] = mail_username
                    app.config['MAIL_PASSWORD'] = mail_password
                    app.config['SMTP_USERNAME'] = mail_username
                    app.config['SMTP_PASSWORD'] = mail_password
                    if settings.smtp_server:
                        app.config['MAIL_SERVER'] = settings.smtp_server
                        app.config['SMTP_SERVER'] = settings.smtp_server
                    if settings.smtp_port:
                        app.config['MAIL_PORT'] = settings.smtp_port
                        app.config['SMTP_PORT'] = settings.smtp_port
                    if settings.smtp_from_email:
                        app.config['MAIL_DEFAULT_SENDER'] = settings.smtp_from_email
                        app.config['SMTP_FROM_EMAIL'] = settings.smtp_from_email
                    # Reinitialize mail with new config
                    from flask_mail import Mail
                    new_mail = Mail(app)
                    app.extensions['mail'] = new_mail
                    mail = new_mail
            except Exception as e:
                print(f"Could not load email config from SystemSettings: {e}")
        
        if not mail_username or not mail_password:
            print(f"✗ Mail credentials not configured - cannot send password reset email to {user_email}")
            return False
        
        try:
            user = User.query.filter_by(email=user_email).first()
            if not user:
                print(f"✗ User not found: {user_email}")
                return False
            
            reset_link = PasswordResetService.create_reset_link(reset_token)
            frontend_url = app.config.get('FRONTEND_URL', 'http://localhost:3000')
            
            msg = Message(
                subject='Reset Your WorkHub Password',
                recipients=[user_email],
                html=f"""
                <html>
                    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
                            <h2 style="color: #4a90e2;">Password Reset Request</h2>
                            
                            <p>Hello {user.name},</p>
                            
                            <p>We received a request to reset your password for your WorkHub account. 
                            Click the button below to reset your password:</p>
                            
                            <div style="text-align: center; margin: 30px 0;">
                                <a href="{reset_link}" style="background-color: #4a90e2; color: white; 
                                   padding: 12px 30px; text-decoration: none; border-radius: 5px; 
                                   display: inline-block; font-weight: bold;">
                                    Reset My Password
                                </a>
                            </div>
                            
                            <p>Or copy and paste this link into your browser:</p>
                            <p style="background-color: #f4f4f4; padding: 10px; border-radius: 5px; 
                                      word-break: break-all; font-size: 12px;">
                                {reset_link}
                            </p>
                            
                            <p><strong>This link will expire in 15 minutes.</strong></p>
                            
                            <p>If you didn't request a password reset, please ignore this email. 
                            Your password will remain unchanged.</p>
                            
                            <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                            <p style="color: #999; font-size: 12px; text-align: center;">
                                WorkHub Task Management System<br>
                                This is an automated email, please do not reply.
                            </p>
                        </div>
                    </body>
                </html>
                """,
                body=f"""
                Password Reset Request
                
                Hello {user.name},
                
                We received a request to reset your password for your WorkHub account.
                
                Click this link to reset your password:
                {reset_link}
                
                This link will expire in 15 minutes.
                
                If you didn't request a password reset, please ignore this email.
                Your password will remain unchanged.
                
                ---
                WorkHub Task Management System
                """
            )
            
            # Set a timeout for email sending to prevent long delays
            import socket
            original_timeout = socket.getdefaulttimeout()
            socket.setdefaulttimeout(10)  # 10 second timeout
            
            try:
                mail.send(msg)
                print(f"✓ Password reset email sent to {user_email}")
                return True
            finally:
                socket.setdefaulttimeout(original_timeout)
            
        except (OSError, ConnectionError) as e:
            error_code = getattr(e, 'errno', None)
            error_str = str(e)
            if error_code == 101 or 'Network is unreachable' in error_str or '[Errno 101]' in error_str:
                mail_server = app.config.get('MAIL_SERVER', 'SMTP server')
                print(f"✗ Network connectivity error: Cloud Run cannot reach {mail_server}")
                print(f"  Error: {e}")
            else:
                print(f"✗ Network error sending password reset email to {user_email}: {e}")
            import traceback
            traceback.print_exc()
            return False
        except Exception as e:
            error_str = str(e)
            if '[Errno 101]' in error_str or 'Network is unreachable' in error_str:
                mail_server = app.config.get('MAIL_SERVER', 'SMTP server')
                print(f"✗ Network connectivity error: Cloud Run cannot reach {mail_server}")
                print(f"  Error: {e}")
            else:
                print(f"✗ Error sending password reset email to {user_email}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    @staticmethod
    def request_password_reset(email, mail):
        """Initiate password reset flow"""
        try:
            user = User.query.filter_by(email=email).first()
            
            if not user:
                # Don't reveal if email exists (security best practice)
                print(f"⚠ Password reset requested for non-existent email: {email}")
                return {
                    'success': True,
                    'message': 'If an account exists with that email, a password reset link has been sent.'
                }
            
            # Generate reset token
            token, token_hash = PasswordResetService.generate_reset_token()
            
            # Set expiry to 15 minutes from now
            expiry = datetime.now(timezone.utc) + timedelta(minutes=15)
            
            # Update user record
            user.reset_token = token_hash
            user.reset_token_expires = expiry
            user.force_password_change = False  # Will be set to True after successful reset
            db.session.commit()
            
            print(f"✓ Reset token generated for {email}, expires at {expiry}")
            
            # Send email
            email_sent = PasswordResetService.send_reset_email(email, token, mail)
            
            return {
                'success': True,
                'message': 'If an account exists with that email, a password reset link has been sent.',
                'email_sent': email_sent
            }
            
        except Exception as e:
            db.session.rollback()
            print(f"✗ Error in password reset request: {e}")
            return {
                'success': False,
                'message': 'An error occurred. Please try again later.'
            }
    
    @staticmethod
    def verify_reset_token(token):
        """Verify if a reset token is valid"""
        try:
            import traceback
            print(f"DEBUG: Received token: {token[:20]}...")
            
            # Hash the token to match what's stored
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            print(f"DEBUG: Token hash: {token_hash[:20]}...")
            
            # Find user with this token
            user = User.query.filter_by(reset_token=token_hash).first()
            
            if not user:
                print("DEBUG: No user found with this token hash")
                # Let's check what tokens exist in the database
                users_with_tokens = User.query.filter(User.reset_token.isnot(None)).all()
                print(f"DEBUG: Found {len(users_with_tokens)} users with reset tokens")
                for u in users_with_tokens:
                    print(f"  - User: {u.email}, Token: {u.reset_token[:20]}...")
                return False, None, "Invalid or expired reset token."
            
            print(f"DEBUG: Found user: {user.email}")
            
            # Check if token has expired
            now = datetime.now(timezone.utc)
            # Ensure both are timezone-aware for comparison
            if user.reset_token_expires.tzinfo is None:
                # If stored datetime is naive, assume it's UTC
                token_expiry = user.reset_token_expires.replace(tzinfo=timezone.utc)
            else:
                token_expiry = user.reset_token_expires
            print(f"DEBUG: Current time: {now}, Token expires: {token_expiry}")
            if now > token_expiry:
                # Clear expired token
                print("DEBUG: Token has expired")
                user.reset_token = None
                user.reset_token_expires = None
                db.session.commit()
                return False, None, "Reset token has expired. Please request a new one."
            
            print("DEBUG: Token verified successfully!")
            return True, user, "Token verified successfully."
            
        except Exception as e:
            print(f"✗ Error verifying reset token: {e}")
            import traceback
            traceback.print_exc()
            return False, None, "An error occurred while verifying the token."
    
    @staticmethod
    def reset_password(token, new_password):
        """Reset password using valid token"""
        try:
            # Verify token
            valid, user, message = PasswordResetService.verify_reset_token(token)
            
            if not valid:
                return False, message
            
            # Set new password
            user.set_password(new_password)
            
            # Clear reset token (one-time use)
            user.reset_token = None
            user.reset_token_expires = None
            
            # Force password change on next login
            user.force_password_change = True
            
            db.session.commit()
            
            print(f"✓ Password reset successful for {user.email}")
            return True, "Password reset successful! Please log in with your new password."
            
        except Exception as e:
            db.session.rollback()
            print(f"✗ Error resetting password: {e}")
            return False, "An error occurred while resetting the password. Please try again."

