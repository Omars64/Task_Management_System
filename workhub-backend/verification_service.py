"""
Email Verification Service
Generates and sends 6-digit verification codes
"""

import random
import string
import threading
from datetime import datetime, timedelta, timezone
from flask_mail import Message
from models import User, db


class VerificationService:
    """Service for email verification with 6-digit codes"""
    
    CODE_LENGTH = 6
    CODE_EXPIRY_MINUTES = 15
    
    @staticmethod
    def generate_code():
        """Generate a random 6-digit verification code"""
        return ''.join(random.choices(string.digits, k=VerificationService.CODE_LENGTH))
    
    @staticmethod
    def create_and_send_code(user, mail):
        """
        Generate verification code, save to user, and send email
        
        Args:
            user: User model instance
            mail: Flask-Mail instance
            
        Returns:
            Dict with success status and code (for development mode)
        """
        # Generate new code
        code = VerificationService.generate_code()
        expiry = datetime.now(timezone.utc) + timedelta(minutes=VerificationService.CODE_EXPIRY_MINUTES)
        
        # Save to user
        user.verification_code = code
        user.verification_code_expires = expiry
        db.session.commit()
        
        # Check if email is configured properly
        # Priority: app.config (from env vars or SystemSettings) > SystemSettings database
        from flask import current_app
        app = current_app._get_current_object() if hasattr(current_app, '_get_current_object') else current_app
        
        # Get mail instance from app.extensions first
        if not mail:
            mail = app.extensions.get('mail')
        
        mail_username = app.config.get('MAIL_USERNAME') or app.config.get('SMTP_USERNAME', '')
        mail_password = app.config.get('MAIL_PASSWORD') or app.config.get('SMTP_PASSWORD', '')
        
        # Strip whitespace to check if actually empty
        mail_username = mail_username.strip() if mail_username else ''
        mail_password = mail_password.strip() if mail_password else ''
        
        # DEBUG: Log current state
        print(f"[DEBUG] Email config check - Username: {'SET' if mail_username else 'NOT SET'}, Password: {'SET' if mail_password else 'NOT SET'}, Mail: {'AVAILABLE' if mail else 'NOT AVAILABLE'}")
        
        # If not in app.config or empty, try loading from SystemSettings database
        if not mail_username or not mail_password:
            print("[DEBUG] Email config not in app.config, attempting to load from database...")
            try:
                from models import SystemSettings
                settings = SystemSettings.query.first()
                if settings:
                    print(f"[DEBUG] Found SystemSettings: username={'SET' if settings.smtp_username else 'NOT SET'}, password={'SET' if settings.smtp_password else 'NOT SET'}")
                    if settings.smtp_username and settings.smtp_password:
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
                        # Reinitialize mail with new config - Flask-Mail needs to be recreated
                        from flask_mail import Mail
                        new_mail = Mail(app)
                        app.extensions['mail'] = new_mail
                        mail = new_mail
                        print(f"[DEBUG] Email config loaded from database and Flask-Mail reinitialized")
                    else:
                        print(f"[DEBUG] SystemSettings found but credentials are empty")
                else:
                    print(f"[DEBUG] No SystemSettings record found in database")
            except Exception as e:
                print(f"[ERROR] Could not load email config from SystemSettings: {e}")
                import traceback
                traceback.print_exc()
        
        mail_configured = mail and mail_username and mail_password
        print(f"[DEBUG] Final check - mail_configured: {mail_configured} (mail={'YES' if mail else 'NO'}, username={'YES' if mail_username else 'NO'}, password={'YES' if mail_password else 'NO'})")
        
        # Try to send email - use a timeout to avoid blocking too long
        email_sent = False
        if mail_configured:
            try:
                # Send email with timeout - this will block briefly but ensures we know if it succeeded
                result = VerificationService.send_verification_email(user.email, user.name, code, mail)
                if result:
                    print(f"✓ Verification email sent successfully to {user.email}")
                    email_sent = True
                else:
                    print(f"✗ Failed to send verification email to {user.email} - check email configuration")
                    email_sent = False
            except Exception as e:
                print(f"✗ Error sending verification email to {user.email}: {e}")
                import traceback
                traceback.print_exc()
                email_sent = False
        else:
            print(f"⚠ Mail not configured - cannot send email to {user.email}")
            print(f"   MAIL_USERNAME: {'SET' if mail_username else 'NOT SET'}")
            print(f"   MAIL_PASSWORD: {'SET' if mail_password else 'NOT SET'}")
            print(f"   Mail instance: {'AVAILABLE' if mail else 'NOT AVAILABLE'}")
        
        # Log the code for development (when email is not configured)
        # SECURITY: Code is ONLY logged server-side, NEVER returned to client
        if not mail_configured:
            print(f"\n{'='*60}")
            print(f"DEVELOPMENT MODE: Email not configured")
            print(f"Verification code for {user.email}: {code}")
            print(f"Expires in {VerificationService.CODE_EXPIRY_MINUTES} minutes")
            print(f"{'='*60}\n")
        
        # SECURITY: Never return the verification code to the client
        return {
            'success': True,
            'email_sent': email_sent
        }
    
    @staticmethod
    def send_verification_email(email, name, code, mail):
        """
        Send verification code email
        
        Args:
            email: Recipient email address
            name: User's name
            code: 6-digit verification code
            mail: Flask-Mail instance
            
        Returns:
            True if successful, False otherwise
        """
        if not mail:
            print(f"✗ Mail instance not available - cannot send email to {email}")
            return False
        
        # Verify mail configuration
        # Priority: app.config (from env vars or SystemSettings) > SystemSettings database
        from flask import current_app
        app = current_app._get_current_object() if hasattr(current_app, '_get_current_object') else current_app
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
                    # Create a new Mail instance with updated config
                    from flask_mail import Mail
                    new_mail = Mail(app)
                    app.extensions['mail'] = new_mail
                    # Update the mail variable passed to this function
                    mail = new_mail
            except Exception as e:
                print(f"Could not load email config from SystemSettings: {e}")
        
        if not mail_username or not mail_password:
            print(f"✗ Mail credentials not configured - cannot send email to {email}")
            print(f"   MAIL_USERNAME: {'SET' if mail_username else 'NOT SET'}")
            print(f"   MAIL_PASSWORD: {'SET' if mail_password else 'NOT SET'}")
            return False
        
        msg = Message(
            subject="Verify Your Email - WorkHub",
            recipients=[email],
            html=f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
                        <h2 style="color: #4CAF50;">Welcome to WorkHub, {name}!</h2>
                        <p>Thank you for signing up. Please verify your email address using the code below:</p>
                        
                        <div style="background-color: #f5f5f5; padding: 20px; text-align: center; margin: 30px 0; border-radius: 5px;">
                            <h1 style="color: #4CAF50; font-size: 48px; letter-spacing: 10px; margin: 0;">
                                {code}
                            </h1>
                        </div>
                        
                        <p style="color: #666; font-size: 14px;">
                            This code will expire in {VerificationService.CODE_EXPIRY_MINUTES} minutes. 
                            If you didn't create an account, please ignore this email.
                        </p>
                        
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
            Welcome to WorkHub, {name}!
            
            Thank you for signing up. Please verify your email address using this code:
            
            {code}
            
            This code will expire in {VerificationService.CODE_EXPIRY_MINUTES} minutes.
            If you didn't create an account, please ignore this email.
            
            ---
            WorkHub Task Management System
            """
        )
        
        try:
            # Set a timeout for email sending to prevent long delays
            import socket
            original_timeout = socket.getdefaulttimeout()
            socket.setdefaulttimeout(10)  # 10 second timeout
            
            try:
                mail.send(msg)
                print(f"✓ Verification code email sent to {email}")
                return True
            finally:
                socket.setdefaulttimeout(original_timeout)
        except (OSError, ConnectionError) as e:
            # Network connectivity errors - provide helpful error message
            error_code = getattr(e, 'errno', None)
            error_str = str(e)
            
            # Check for network unreachable errors (errno 101 or in error message)
            if error_code == 101 or 'Network is unreachable' in error_str or '[Errno 101]' in error_str:
                mail_server = app.config.get('MAIL_SERVER', 'SMTP server')
                print(f"✗ Network connectivity error: Cloud Run cannot reach {mail_server}")
                print(f"  Error: {e}")
                print(f"  This usually means a VPC connector is blocking outbound internet access.")
                print(f"  COMPLETE FIX: Remove VPC connector to enable default outbound access:")
                print(f"  gcloud run services update workhub-backend --region=us-central1 --clear-vpc-connector --project=genai-workhub")
                print(f"  Or use the script: workhub-backend/fix_email_network_complete.sh")
            else:
                print(f"✗ Network error sending verification email to {email}: {e}")
            import traceback
            traceback.print_exc()
            return False
        except Exception as e:
            # Check if the exception message contains network error indicators
            error_str = str(e)
            if '[Errno 101]' in error_str or 'Network is unreachable' in error_str:
                mail_server = app.config.get('MAIL_SERVER', 'SMTP server')
                print(f"✗ Network connectivity error: Cloud Run cannot reach {mail_server}")
                print(f"  Error: {e}")
                print(f"  This usually means a VPC connector is blocking outbound internet access.")
                print(f"  COMPLETE FIX: Remove VPC connector to enable default outbound access:")
                print(f"  gcloud run services update workhub-backend --region=us-central1 --clear-vpc-connector --project=genai-workhub")
                print(f"  Or use the script: workhub-backend/fix_email_network_complete.sh")
            else:
                print(f"✗ Error sending verification email to {email}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    @staticmethod
    def verify_code(user, code):
        """
        Verify the code for a user
        
        Args:
            user: User model instance
            code: Code to verify
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not user.verification_code:
            return False, "No verification code found. Please request a new code."
        
        if not user.verification_code_expires:
            return False, "Verification code has expired. Please request a new code."
        
        # Check expiry - handle both timezone-aware and naive datetimes
        try:
            # Make expiry timezone-aware if it isn't
            if user.verification_code_expires.tzinfo is None:
                from datetime import timezone as tz
                expiry_aware = user.verification_code_expires.replace(tzinfo=timezone.utc)
            else:
                expiry_aware = user.verification_code_expires
            
            if datetime.now(timezone.utc) > expiry_aware:
                return False, "Verification code has expired. Please request a new code."
        except Exception as e:
            print(f"Error checking expiry: {e}")
            # If there's an error, assume expired
            return False, "Verification code has expired. Please request a new code."
        
        # Verify code
        if user.verification_code != code:
            return False, "Invalid verification code. Please try again."
        
        # Success - mark as verified and clear code
        try:
            user.email_verified = True
            user.verification_code = None
            user.verification_code_expires = None
            db.session.commit()
            print(f"✓ Email verified successfully for {user.email}")
            return True, "Email verified successfully!"
        except Exception as e:
            db.session.rollback()
            print(f"✗ Error updating user verification status: {e}")
            return False, f"Database error: {str(e)}"
    
    @staticmethod
    def send_admin_notification(user_signup, mail):
        """
        Send notification to all admins and super_admins about new signup request
        Only called AFTER email verification is complete
        
        Args:
            user_signup: User who signed up (pending approval, email verified)
            mail: Flask-Mail instance
        """
        # Get all admin and super_admin users
        admins = User.query.filter(
            User.role.in_(['admin', 'super_admin']),
            User.signup_status == 'approved'
        ).all()
        
        if not admins:
            print("No admin users found to notify")
            return
        
        admin_emails = [admin.email for admin in admins]
        
        msg = Message(
            subject="New User Signup Request - WorkHub",
            recipients=admin_emails,
            html=f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
                        <h2 style="color: #FF9800;">New User Signup Request</h2>
                        <p>A new user has signed up and is awaiting approval:</p>
                        
                        <div style="background-color: #f5f5f5; padding: 15px; margin: 20px 0; border-radius: 5px;">
                            <p style="margin: 5px 0;"><strong>Name:</strong> {user_signup.name}</p>
                            <p style="margin: 5px 0;"><strong>Email:</strong> {user_signup.email}</p>
                            <p style="margin: 5px 0;"><strong>Signup Date:</strong> {user_signup.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                        </div>
                        
                        <p>Please log in to the admin panel to review and approve or reject this request.</p>
                        
                        <p style="text-align: center; margin: 30px 0;">
                            <a href="http://localhost:3000/users" 
                               style="background-color: #4CAF50; color: white; padding: 12px 30px; 
                                      text-decoration: none; border-radius: 5px; display: inline-block;">
                                Review Pending Users
                            </a>
                        </p>
                        
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
            New User Signup Request
            
            A new user has signed up and is awaiting approval:
            
            Name: {user_signup.name}
            Email: {user_signup.email}
            Signup Date: {user_signup.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}
            
            Please log in to the admin panel to review and approve or reject this request.
            
            ---
            WorkHub Task Management System
            """
        )
        
        try:
            mail.send(msg)
            print(f"Admin notification sent to {len(admin_emails)} admins")
        except Exception as e:
            print(f"Error sending admin notification: {e}")
    
    @staticmethod
    def send_approval_email(user, mail):
        """Send email to user when their signup is approved"""
        msg = Message(
            subject="Your Account Has Been Approved - WorkHub",
            recipients=[user.email],
            html=f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
                        <h2 style="color: #4CAF50;">Account Approved!</h2>
                        <p>Hi {user.name},</p>
                        <p>Great news! Your WorkHub account has been approved by an administrator.</p>
                        <p>You can now log in and start using the task management system.</p>
                        
                        <p style="text-align: center; margin: 30px 0;">
                            <a href="http://localhost:3000/login" 
                               style="background-color: #4CAF50; color: white; padding: 12px 30px; 
                                      text-decoration: none; border-radius: 5px; display: inline-block;">
                                Log In Now
                            </a>
                        </p>
                        
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
            Account Approved!
            
            Hi {user.name},
            
            Great news! Your WorkHub account has been approved by an administrator.
            You can now log in and start using the task management system.
            
            Visit: http://localhost:3000/login
            
            ---
            WorkHub Task Management System
            """
        )
        
        try:
            mail.send(msg)
            return True
        except Exception as e:
            print(f"Error sending approval email: {e}")
            return False
    
    @staticmethod
    def send_rejection_email(user, reason, mail):
        """Send email to user when their signup is rejected"""
        if not mail:
            print("⚠ Mail instance not available - cannot send rejection email")
            return False
        
        try:
            msg = Message(
                subject="Account Signup Update - WorkHub",
                recipients=[user.email],
                html=f"""
                <html>
                    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
                            <h2 style="color: #dc2626;">Account Signup Update</h2>
                            <p>Hi {user.name},</p>
                            <p>Unfortunately, your WorkHub account signup was not approved.</p>
                            
                            {f'<div style="background-color: #fef2f2; padding: 15px; margin: 20px 0; border-left: 4px solid #dc2626;"><p style="margin: 0;"><strong>Reason:</strong> {reason}</p></div>' if reason else ''}
                            
                            <p>If you believe this was a mistake or have questions, please contact the administrator.</p>
                            
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
                Account Signup Update
                
                Hi {user.name},
                
                Unfortunately, your WorkHub account signup was not approved.
                
                {f'Reason: {reason}' if reason else ''}
                
                If you believe this was a mistake or have questions, please contact the administrator.
                
                ---
                WorkHub Task Management System
                """
            )
            
            mail.send(msg)
            print(f"✓ Rejection email sent successfully to {user.email}")
            return True
        except Exception as e:
            print(f"✗ Error sending rejection email to {user.email}: {e}")
            import traceback
            traceback.print_exc()
            return False


# Singleton instance
verification_service = VerificationService()

