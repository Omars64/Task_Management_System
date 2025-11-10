# workhub-backend/email_service.py
"""
Email Service for Task Management System
Handles email notifications with HTML templates and SMTP configuration
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from datetime import datetime
from typing import List, Dict, Optional
import logging
import html

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending email notifications"""
    
    def __init__(self, app=None):
        self.smtp_server = None
        self.smtp_port = None
        self.smtp_username = None
        self.smtp_password = None
        self.from_email = None
        self.from_name = None
        self.enabled = False
        self.app = None
        self.frontend_url = None
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize email service with Flask app config"""
        self.app = app  # Store app instance for later use
        self._load_config_from_app(app)
        
        if self.enabled and not self.smtp_username:
            logger.warning("Email notifications enabled but SMTP credentials not configured")
    
    def _load_config_from_app(self, app):
        """Load email configuration from app.config, with fallback to SystemSettings"""
        self.smtp_server = app.config.get('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = app.config.get('SMTP_PORT', 587)
        self.smtp_username = app.config.get('SMTP_USERNAME', '')
        self.smtp_password = app.config.get('SMTP_PASSWORD', '')
        self.from_email = app.config.get('SMTP_FROM_EMAIL', 'noreply@workhub.com')
        self.from_name = app.config.get('SMTP_FROM_NAME', 'WorkHub Task Management')
        self.enabled = app.config.get('EMAIL_NOTIFICATIONS_ENABLED', False)
        self.frontend_url = app.config.get('FRONTEND_URL', 'http://localhost:5173')
        
        # If credentials not in app.config, try loading from SystemSettings database
        if not self.smtp_username or not self.smtp_password:
            try:
                from models import SystemSettings
                with app.app_context():
                    settings = SystemSettings.query.first()
                    if settings and settings.smtp_username and settings.smtp_password:
                        self.smtp_username = settings.smtp_username
                        self.smtp_password = settings.smtp_password
                        if settings.smtp_server:
                            self.smtp_server = settings.smtp_server
                        if settings.smtp_port:
                            self.smtp_port = settings.smtp_port
                        if settings.smtp_from_email:
                            self.from_email = settings.smtp_from_email
                        if settings.smtp_from_name:
                            self.from_name = settings.smtp_from_name
                        # Update app.config for consistency
                        app.config['SMTP_USERNAME'] = self.smtp_username
                        app.config['SMTP_PASSWORD'] = self.smtp_password
                        app.config['MAIL_USERNAME'] = self.smtp_username
                        app.config['MAIL_PASSWORD'] = self.smtp_password
                        logger.info("Email configuration loaded from SystemSettings database")
            except Exception as e:
                logger.warning(f"Could not load email config from SystemSettings: {e}")
    
    def send_email(self, to_email: str, subject: str, html_content: str, plain_content: str = None) -> bool:
        """
        Send an email
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email body
            plain_content: Plain text fallback (optional)
        
        Returns:
            bool: True if sent successfully, False otherwise
        """
        # Reload config before sending (in case it was updated in SystemSettings)
        if self.app:
            self._load_config_from_app(self.app)
        
        if not self.enabled:
            logger.info(f"Email notifications disabled. Would have sent: {subject} to {to_email}")
            return False
        
        if not self.smtp_username or not self.smtp_password:
            logger.error("SMTP credentials not configured")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            msg['Date'] = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S +0000')
            
            # Add plain text version
            if plain_content:
                part1 = MIMEText(plain_content, 'plain')
                msg.attach(part1)
            
            # Add HTML version
            part2 = MIMEText(html_content, 'html')
            msg.attach(part2)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    def send_task_assigned(self, to_email: str, task_data: Dict) -> bool:
        """Send notification when a task is assigned"""
        subject = f"New Task Assigned: {task_data['title']}"
        
        html_content = self._render_task_assigned_template(task_data)
        plain_content = f"""
New Task Assigned

Task: {task_data['title']}
Priority: {task_data.get('priority', 'medium')}
Due Date: {task_data.get('due_date', 'Not set')}

Description:
{task_data.get('description', 'No description provided')}

View task: {task_data.get('task_url', '#')}
"""
        
        return self.send_email(to_email, subject, html_content, plain_content)
    
    def send_task_updated(self, to_email: str, task_data: Dict, changes: Dict) -> bool:
        """Send notification when a task is updated"""
        subject = f"Task Updated: {task_data['title']}"
        
        html_content = self._render_task_updated_template(task_data, changes)
        plain_content = f"""
Task Updated

Task: {task_data['title']}

Changes:
{self._format_changes_plain(changes)}

View task: {task_data.get('task_url', '#')}
"""
        
        return self.send_email(to_email, subject, html_content, plain_content)
    
    def send_comment_notification(self, to_email: str, task_data: Dict, comment_data: Dict) -> bool:
        """Send notification when someone comments on a task"""
        subject = f"New Comment on: {task_data['title']}"
        
        html_content = self._render_comment_template(task_data, comment_data)
        plain_content = f"""
New Comment

Task: {task_data['title']}

{comment_data['author_name']} commented:
{comment_data['content']}

View task: {task_data.get('task_url', '#')}
"""
        
        return self.send_email(to_email, subject, html_content, plain_content)
    
    def send_task_due_soon(self, to_email: str, task_data: Dict) -> bool:
        """Send notification when a task is due soon"""
        subject = f"⏰ Task Due Soon: {task_data['title']}"
        
        html_content = self._render_task_due_soon_template(task_data)
        plain_content = f"""
Task Due Soon!

Task: {task_data['title']}
Due Date: {task_data.get('due_date', 'Not set')}
Priority: {task_data.get('priority', 'medium')}

View task: {task_data.get('task_url', '#')}
"""
        
        return self.send_email(to_email, subject, html_content, plain_content)
    
    def send_generic_notification(self, to_email: str, subject: str, message: str) -> bool:
        """Send a generic notification email"""
        if not self.enabled:
            return False
        
        try:
            # Use stored frontend_url or fallback to default
            frontend_url = self.frontend_url or 'http://localhost:5173'
            
            html_content = f"""
            <div class="container">
                <div class="header">
                    <h1>{subject}</h1>
                </div>
                <div class="content">
                    <p>{message}</p>
                    <a href="{frontend_url}/calendar" class="button">View Calendar</a>
                </div>
                <div class="footer">
                    <p>WorkHub Task Management System</p>
                </div>
            </div>
            """
            
            plain_content = f"{subject}\n\n{message}\n\nView Calendar: {frontend_url}/calendar"
            
            return self.send_email(to_email, subject, html_content, plain_content)
        except Exception as e:
            logger.error(f"Error sending generic notification email: {str(e)}")
            return False
    
    def send_task_overdue(self, to_email: str, task_data: Dict) -> bool:
        """Send notification when a task is overdue"""
        subject = f"🚨 Task Overdue: {task_data['title']}"
        
        html_content = self._render_task_overdue_template(task_data)
        plain_content = f"""
Task Overdue!

Task: {task_data['title']}
Due Date: {task_data.get('due_date', 'Not set')}
Priority: {task_data.get('priority', 'medium')}

Please update the task status or due date.

View task: {task_data.get('task_url', '#')}
"""
        
        return self.send_email(to_email, subject, html_content, plain_content)
    
    def _format_changes_plain(self, changes: Dict) -> str:
        """Format changes for plain text email"""
        lines = []
        for field, change in changes.items():
            lines.append(f"- {field}: {change.get('old', 'N/A')} → {change.get('new', 'N/A')}")
        return '\n'.join(lines)
    
    def _get_base_template(self) -> str:
        """Base HTML template for all emails"""
        return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
            margin: 0;
            padding: 0;
        }
        .container {
            max-width: 600px;
            margin: 20px auto;
            background-color: #ffffff;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .header {
            background: #68939d;
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 24px;
            font-weight: 600;
        }
        .content {
            padding: 30px;
        }
        .task-title {
            font-size: 20px;
            font-weight: 600;
            color: #1a202c;
            margin-bottom: 15px;
        }
        .task-detail {
            background-color: #f7fafc;
            border-left: 4px solid #68939d;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }
        .detail-row {
            display: flex;
            margin-bottom: 8px;
        }
        .detail-label {
            font-weight: 600;
            color: #4a5568;
            min-width: 100px;
        }
        .detail-value {
            color: #2d3748;
        }
        .priority-high {
            color: #e53e3e;
            font-weight: 600;
        }
        .priority-medium {
            color: #ed8936;
            font-weight: 600;
        }
        .priority-low {
            color: #48bb78;
            font-weight: 600;
        }
        .button {
            display: inline-block;
            padding: 12px 30px;
            background: #68939d;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 600;
            margin-top: 20px;
        }
        .footer {
            background-color: #f7fafc;
            padding: 20px;
            text-align: center;
            color: #718096;
            font-size: 14px;
        }
        .changes-list {
            background-color: #fff5f5;
            border-left: 4px solid #fc8181;
            padding: 15px;
            margin: 15px 0;
        }
        .change-item {
            margin-bottom: 8px;
        }
        .comment-box {
            background-color: #f7fafc;
            border-radius: 6px;
            padding: 15px;
            margin: 15px 0;
        }
        .comment-author {
            font-weight: 600;
            color: #68939d;
            margin-bottom: 8px;
        }
        .alert-warning {
            background-color: #fffaf0;
            border-left: 4px solid #ed8936;
            padding: 15px;
            margin: 15px 0;
            border-radius: 4px;
        }
        .alert-danger {
            background-color: #fff5f5;
            border-left: 4px solid #e53e3e;
            padding: 15px;
            margin: 15px 0;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    {{CONTENT}}
</body>
</html>
"""
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters to prevent injection"""
        if text is None:
            return ''
        return html.escape(str(text))
    
    def _render_task_assigned_template(self, task_data: Dict) -> str:
        """Render HTML template for task assignment"""
        # Escape all user-supplied data
        title = self._escape_html(task_data.get('title', ''))
        description = self._escape_html(task_data.get('description', 'No description provided'))
        priority = self._escape_html(task_data.get('priority', 'medium'))
        due_date = self._escape_html(task_data.get('due_date', 'Not set'))
        status = self._escape_html(task_data.get('status', 'pending'))
        task_url = self._escape_html(task_data.get('task_url', '#'))
        
        priority_class = f"priority-{priority.lower()}"
        
        content = f"""
    <div class="container">
        <div class="header">
            <h1>📋 New Task Assigned</h1>
        </div>
        <div class="content">
            <div class="task-title">{title}</div>
            
            <div class="task-detail">
                <div class="detail-row">
                    <span class="detail-label">Priority:</span>
                    <span class="detail-value {priority_class}">{priority.upper()}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Due Date:</span>
                    <span class="detail-value">{due_date}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Status:</span>
                    <span class="detail-value">{status}</span>
                </div>
            </div>
            
            <p><strong>Description:</strong></p>
            <p>{description}</p>
            
            <a href="{task_url}" class="button">View Task</a>
        </div>
        <div class="footer">
            <p>WorkHub Task Management System</p>
            <p>You are receiving this email because you are assigned to this task.</p>
        </div>
    </div>
"""
        
        return self._get_base_template().replace('{{CONTENT}}', content)
    
    def _render_task_updated_template(self, task_data: Dict, changes: Dict) -> str:
        """Render HTML template for task update"""
        # Escape all user-supplied data
        title = self._escape_html(task_data.get('title', ''))
        task_url = self._escape_html(task_data.get('task_url', '#'))
        
        changes_html = ""
        for field, change in changes.items():
            escaped_field = self._escape_html(field)
            old_val = self._escape_html(change.get('old', 'N/A'))
            new_val = self._escape_html(change.get('new', 'N/A'))
            changes_html += f'<div class="change-item"><strong>{escaped_field}:</strong> {old_val} → {new_val}</div>'
        
        content = f"""
    <div class="container">
        <div class="header">
            <h1>🔄 Task Updated</h1>
        </div>
        <div class="content">
            <div class="task-title">{title}</div>
            
            <p><strong>The following changes were made:</strong></p>
            
            <div class="changes-list">
                {changes_html}
            </div>
            
            <a href="{task_url}" class="button">View Task</a>
        </div>
        <div class="footer">
            <p>WorkHub Task Management System</p>
            <p>You are receiving this email because you are involved in this task.</p>
        </div>
    </div>
"""
        
        return self._get_base_template().replace('{{CONTENT}}', content)
    
    def _render_comment_template(self, task_data: Dict, comment_data: Dict) -> str:
        """Render HTML template for comment notification"""
        # Escape all user-supplied data
        title = self._escape_html(task_data.get('title', ''))
        task_url = self._escape_html(task_data.get('task_url', '#'))
        author_name = self._escape_html(comment_data.get('author_name', 'Unknown'))
        comment_content = self._escape_html(comment_data.get('content', ''))
        
        content = f"""
    <div class="container">
        <div class="header">
            <h1>💬 New Comment</h1>
        </div>
        <div class="content">
            <div class="task-title">{title}</div>
            
            <div class="comment-box">
                <div class="comment-author">{author_name} commented:</div>
                <div>{comment_content}</div>
            </div>
            
            <a href="{task_url}" class="button">View Task & Reply</a>
        </div>
        <div class="footer">
            <p>WorkHub Task Management System</p>
            <p>You are receiving this email because you are involved in this task.</p>
        </div>
    </div>
"""
        
        return self._get_base_template().replace('{{CONTENT}}', content)
    
    def _render_task_due_soon_template(self, task_data: Dict) -> str:
        """Render HTML template for task due soon"""
        # Escape all user-supplied data
        title = self._escape_html(task_data.get('title', ''))
        due_date = self._escape_html(task_data.get('due_date', 'Not set'))
        priority = self._escape_html(task_data.get('priority', 'medium'))
        status = self._escape_html(task_data.get('status', 'pending'))
        task_url = self._escape_html(task_data.get('task_url', '#'))
        
        priority_class = f"priority-{priority.lower()}"
        
        content = f"""
    <div class="container">
        <div class="header">
            <h1>⏰ Task Due Soon</h1>
        </div>
        <div class="content">
            <div class="alert-warning">
                <strong>Reminder:</strong> This task is due within 24 hours!
            </div>
            
            <div class="task-title">{title}</div>
            
            <div class="task-detail">
                <div class="detail-row">
                    <span class="detail-label">Due Date:</span>
                    <span class="detail-value">{due_date}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Priority:</span>
                    <span class="detail-value {priority_class}">{priority.upper()}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Status:</span>
                    <span class="detail-value">{status}</span>
                </div>
            </div>
            
            <a href="{task_url}" class="button">Update Task</a>
        </div>
        <div class="footer">
            <p>WorkHub Task Management System</p>
        </div>
    </div>
"""
        
        return self._get_base_template().replace('{{CONTENT}}', content)
    
    def _render_task_overdue_template(self, task_data: Dict) -> str:
        """Render HTML template for task overdue"""
        # Escape all user-supplied data
        title = self._escape_html(task_data.get('title', ''))
        due_date = self._escape_html(task_data.get('due_date', 'Not set'))
        priority = self._escape_html(task_data.get('priority', 'medium'))
        status = self._escape_html(task_data.get('status', 'pending'))
        task_url = self._escape_html(task_data.get('task_url', '#'))
        
        priority_class = f"priority-{priority.lower()}"
        
        content = f"""
    <div class="container">
        <div class="header">
            <h1>🚨 Task Overdue</h1>
        </div>
        <div class="content">
            <div class="alert-danger">
                <strong>Alert:</strong> This task is overdue and requires immediate attention!
            </div>
            
            <div class="task-title">{title}</div>
            
            <div class="task-detail">
                <div class="detail-row">
                    <span class="detail-label">Due Date:</span>
                    <span class="detail-value">{due_date}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Priority:</span>
                    <span class="detail-value {priority_class}">{priority.upper()}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Status:</span>
                    <span class="detail-value">{status}</span>
                </div>
            </div>
            
            <p>Please update the task status or adjust the due date.</p>
            
            <a href="{task_url}" class="button">Update Task</a>
        </div>
        <div class="footer">
            <p>WorkHub Task Management System</p>
        </div>
    </div>
"""
        
        return self._get_base_template().replace('{{CONTENT}}', content)


# Global email service instance
email_service = EmailService()

