"""
Email service for sending notifications
"""
import os
from flask import current_app
from flask_mail import Mail, Message
from models import SystemSettings

mail = Mail()

def init_email(app):
    """Initialize email service"""
    mail.init_app(app)

def send_notification_email(user_email, user_name, notification_title, notification_message, task_title=None):
    """Send notification email to user"""
    try:
        # Check if email notifications are enabled
        settings = SystemSettings.query.first()
        if not settings or not settings.email_notifications_enabled:
            return False
        
        # Create email message
        msg = Message(
            subject=f"Work Hub Notification: {notification_title}",
            recipients=[user_email],
            sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@workhub.com')
        )
        
        # Create email body
        body = f"""
Hello {user_name},

{notification_message}

"""
        
        if task_title:
            body += f"Task: {task_title}\n"
        
        body += f"""
You can view this notification in your Work Hub dashboard.

Best regards,
Work Hub Team
"""
        
        msg.body = body
        
        # Send email
        mail.send(msg)
        return True
        
    except Exception as e:
        current_app.logger.error(f"Failed to send email to {user_email}: {str(e)}")
        return False

def send_password_reset_email(user_email, user_name, reset_token):
    """Send password reset email"""
    try:
        reset_url = f"{current_app.config.get('FRONTEND_URL', 'http://localhost:3000')}/reset-password?token={reset_token}"
        
        msg = Message(
            subject="Work Hub - Password Reset Request",
            recipients=[user_email],
            sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@workhub.com')
        )
        
        body = f"""
Hello {user_name},

You have requested to reset your password for your Work Hub account.

Click the link below to reset your password:
{reset_url}

This link will expire in 1 hour.

If you did not request this password reset, please ignore this email.

Best regards,
Work Hub Team
"""
        
        msg.body = body
        mail.send(msg)
        return True
        
    except Exception as e:
        current_app.logger.error(f"Failed to send password reset email to {user_email}: {str(e)}")
        return False