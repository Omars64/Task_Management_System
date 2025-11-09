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
        
        # Check if email is configured
        from flask import current_app
        app = current_app._get_current_object() if hasattr(current_app, '_get_current_object') else current_app
        mail_configured = mail and app.config.get('MAIL_USERNAME') and app.config.get('MAIL_PASSWORD')
        
        # Try to send email in background thread to avoid blocking
        email_sent = False
        if mail_configured:
            # Send email in background thread to avoid blocking the API response
            def send_email_async():
                try:
                    result = VerificationService.send_verification_email(user.email, user.name, code, mail)
                    if result:
                        print(f"✓ Verification email sent successfully to {user.email}")
                    else:
                        print(f"✗ Failed to send verification email to {user.email}")
                except Exception as e:
                    print(f"✗ Error sending verification email to {user.email}: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Start email sending in background thread
            thread = threading.Thread(target=send_email_async, daemon=True)
            thread.start()
            
            # Assume email will be sent (optimistic) - actual result handled in background
            # This prevents blocking the API response
            email_sent = True
        else:
            print(f"⚠ Mail not configured - cannot send email to {user.email}")
        
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
        except Exception as e:
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

