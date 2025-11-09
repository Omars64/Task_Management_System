from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime
import enum

db = SQLAlchemy()
bcrypt = Bcrypt()


class UserRole(enum.Enum):
    """User role enumeration"""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MANAGER = "manager"
    TEAM_LEAD = "team_lead"
    DEVELOPER = "developer"
    VIEWER = "viewer"


class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='viewer')  # 'super_admin', 'admin', 'manager', 'team_lead', 'developer', 'viewer'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Email verification fields
    email_verified = db.Column(db.Boolean, default=False)
    verification_code = db.Column(db.String(10))
    verification_code_expires = db.Column(db.DateTime)
    
    # Password reset fields
    reset_token = db.Column(db.String(255))
    reset_token_expires = db.Column(db.DateTime)
    force_password_change = db.Column(db.Boolean, default=False)
    
    # Signup approval fields
    signup_status = db.Column(db.String(20), default='approved')  # 'pending', 'approved', 'rejected'
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_at = db.Column(db.DateTime)
    rejection_reason = db.Column(db.Text)
    
    # Personal settings
    theme = db.Column(db.String(20), default='light')
    language = db.Column(db.String(10), default='en')
    notifications_enabled = db.Column(db.Boolean, default=True)
    
    # Relationships - Note: These use string references to avoid circular imports
    assigned_tasks = db.relationship('Task', foreign_keys='Task.assigned_to', lazy=True, viewonly=False)
    created_tasks = db.relationship('Task', foreign_keys='Task.created_by', lazy=True, viewonly=False)
    notifications = db.relationship('Notification', backref='user', lazy=True, cascade='all, delete-orphan')
    approver = db.relationship('User', remote_side=[id], backref='approved_users')
    
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def has_permission(self, permission):
        """Check if user has a specific permission"""
        from permissions import has_permission
        return has_permission(self.role, permission)
    
    def has_any_permission(self, permissions):
        """Check if user has any of the specified permissions"""
        from permissions import has_any_permission
        return has_any_permission(self.role, permissions)
    
    def has_all_permissions(self, permissions):
        """Check if user has all of the specified permissions"""
        from permissions import has_all_permissions
        return has_all_permissions(self.role, permissions)
    
    def to_dict(self, include_verification=False):
        data = {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'role': self.role,
            'theme': self.theme,
            'language': self.language,
            'notifications_enabled': self.notifications_enabled,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'email_verified': self.email_verified,
            'signup_status': self.signup_status
        }
        
        # Include verification details for admin/specific contexts
        if include_verification:
            data.update({
                'approved_by': self.approved_by,
                'approved_at': self.approved_at.isoformat() if self.approved_at else None,
                'rejection_reason': self.rejection_reason,
                'approver_name': self.approver.name if self.approver else None
            })
        
        return data


class Task(db.Model):
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    priority = db.Column(db.String(20), nullable=False, default='medium')  # 'low', 'medium', 'high'
    status = db.Column(db.String(20), nullable=False, default='todo')  # 'todo', 'in_progress', 'completed'
    due_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))

    # Project and Sprint linkage (nullable for backward compatibility)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))
    sprint_id = db.Column(db.Integer, db.ForeignKey('sprints.id'))
    
    # Subtask and dependency fields
    parent_task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'))
    blocks_task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'))  # This task blocks another task
    
    # Relationships
    assignee = db.relationship('User', foreign_keys=[assigned_to], lazy=True, viewonly=False)
    creator = db.relationship('User', foreign_keys=[created_by], lazy=True, viewonly=False)
    time_logs = db.relationship('TimeLog', backref='task', lazy=True, cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='task', lazy=True, cascade='all, delete-orphan')
    subtasks = db.relationship('Task', backref=db.backref('parent_task', remote_side=[id]), foreign_keys=[parent_task_id], lazy=True)
    blocked_by_task = db.relationship('Task', backref=db.backref('blocks_task', remote_side=[id]), foreign_keys=[blocks_task_id], lazy=True)
    project = db.relationship('Project', backref=db.backref('tasks', lazy=True))
    sprint = db.relationship('Sprint', backref=db.backref('tasks', lazy=True))
    
    def to_dict(self, include_subtasks=False):
        result = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'priority': self.priority,
            'status': self.status,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'assigned_to': self.assigned_to,
            'created_by': self.created_by,
            'assignee_name': self.assignee.name if (self.assignee and hasattr(self.assignee, 'name')) else None,
            'creator_name': self.creator.name if (self.creator and hasattr(self.creator, 'name')) else None,
            'parent_task_id': self.parent_task_id,
            'blocks_task_id': self.blocks_task_id,
            'blocked_task_title': self.blocks_task.title if (self.blocks_task and hasattr(self.blocks_task, 'title')) else None,
            'project_id': self.project_id,
            'project_name': self.project.name if (getattr(self, 'project', None) and hasattr(self.project, 'name')) else None,
            'sprint_id': self.sprint_id,
            'sprint_name': self.sprint.name if (getattr(self, 'sprint', None) and hasattr(self.sprint, 'name')) else None
        }
        
        # Add blocked_by list (tasks that block this one)
        try:
            blocked_by = []
            # Find tasks where blocks_task_id equals this task's id
            if hasattr(self, 'id') and self.id is not None:
                from models import Task as TaskModel  # local import to avoid circulars
                # SQLAlchemy session from relationship context; fallback to simple query if available
                try:
                    blocked_by_tasks = TaskModel.query.filter_by(blocks_task_id=self.id).all()
                    for t in blocked_by_tasks:
                        if t and hasattr(t, 'id') and hasattr(t, 'title') and hasattr(t, 'status'):
                            blocked_by.append({'id': t.id, 'title': t.title, 'status': t.status})
                except Exception:
                    pass
            result['blocked_by'] = blocked_by
        except Exception:
            # In case of context issues during serialization, skip silently
            result['blocked_by'] = []

        if include_subtasks:
            result['subtasks'] = [st.to_dict(include_subtasks=False) for st in self.subtasks]
            result['subtask_count'] = len(self.subtasks)
            result['completed_subtask_count'] = len([st for st in self.subtasks if st.status == 'completed'])
        
        return result


class Project(db.Model):
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, unique=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    owner = db.relationship('User', backref='owned_projects', foreign_keys=[owner_id])
    sprints = db.relationship('Sprint', backref='project', lazy=True, cascade='all, delete-orphan')
    members = db.relationship('ProjectMember', backref='project', lazy=True, cascade='all, delete-orphan')

    def to_dict(self, include_sprints=False):
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'owner_id': self.owner_id,
            'owner_name': self.owner.name if self.owner else None,
        }
        if include_sprints:
            data['sprints'] = [s.to_dict() for s in self.sprints]
        return data


class Sprint(db.Model):
    __tablename__ = 'sprints'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    goal = db.Column(db.String(255))
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self, include_project=False):
        data = {
            'id': self.id,
            'project_id': self.project_id,
            'name': self.name,
            'goal': self.goal,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_project:
            data['project_name'] = self.project.name if getattr(self, 'project', None) else None
        return data


class ProjectMember(db.Model):
    __tablename__ = 'project_members'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.String(50))  # optional: project-specific role
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='project_memberships')

    __table_args__ = (
        db.UniqueConstraint('project_id', 'user_id', name='uq_project_user'),
    )


class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50))  # 'task_assigned', 'task_updated', 'deadline', 'comment', 'chat_request', 'chat_accepted', 'chat_message'
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    related_task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'))
    related_conversation_id = db.Column(db.Integer, db.ForeignKey('chat_conversations.id'))
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'message': self.message,
            'type': self.type,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'related_task_id': self.related_task_id,
            'related_conversation_id': self.related_conversation_id
        }


class TimeLog(db.Model):
    __tablename__ = 'time_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    hours = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    logged_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'user_id': self.user_id,
            'hours': self.hours,
            'description': self.description,
            'logged_at': self.logged_at.isoformat() if self.logged_at else None
        }


class Comment(db.Model):
    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.UnicodeText, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    parent_comment_id = db.Column(db.Integer, db.ForeignKey('comments.id'))
    
    user = db.relationship('User', backref='comments')
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'user_id': self.user_id,
            'user_name': self.user.name if (self.user and hasattr(self.user, 'name')) else None,
            'content': self.content,
            'created_at': self.created_at.isoformat() if (hasattr(self, 'created_at') and self.created_at) else None,
            'parent_comment_id': self.parent_comment_id
        }


class SystemSettings(db.Model):
    __tablename__ = 'system_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    site_title = db.Column(db.String(100), default='Work Hub')
    default_role = db.Column(db.String(20), default='developer')
    email_notifications_enabled = db.Column(db.Boolean, default=True)
    default_language = db.Column(db.String(10), default='en')
    
    # SMTP Configuration
    smtp_server = db.Column(db.String(255), default='smtp.gmail.com')
    smtp_port = db.Column(db.Integer, default=587)
    smtp_username = db.Column(db.String(255))
    smtp_password = db.Column(db.String(255))
    smtp_from_email = db.Column(db.String(255), default='noreply@workhub.com')
    smtp_from_name = db.Column(db.String(255), default='WorkHub Task Management')
    
    def to_dict(self):
        return {
            'id': self.id,
            'site_title': self.site_title,
            'default_role': self.default_role,
            'email_notifications_enabled': self.email_notifications_enabled,
            'default_language': self.default_language,
            'smtp_server': self.smtp_server,
            'smtp_port': self.smtp_port,
            'smtp_username': self.smtp_username,
            # Don't expose password
            'smtp_from_email': self.smtp_from_email,
            'smtp_from_name': self.smtp_from_name
        }


class NotificationPreference(db.Model):
    __tablename__ = 'notification_preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # Email notification preferences
    email_task_assigned = db.Column(db.Boolean, default=True)
    email_task_updated = db.Column(db.Boolean, default=True)
    email_task_commented = db.Column(db.Boolean, default=True)
    email_task_due_soon = db.Column(db.Boolean, default=True)
    email_task_overdue = db.Column(db.Boolean, default=True)
    
    # In-app notification preferences
    inapp_task_assigned = db.Column(db.Boolean, default=True)
    inapp_task_updated = db.Column(db.Boolean, default=True)
    inapp_task_commented = db.Column(db.Boolean, default=True)
    inapp_task_due_soon = db.Column(db.Boolean, default=True)
    inapp_task_overdue = db.Column(db.Boolean, default=True)
    
    # Digest settings
    daily_digest = db.Column(db.Boolean, default=False)
    weekly_digest = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref='notification_preference')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'email_task_assigned': self.email_task_assigned,
            'email_task_updated': self.email_task_updated,
            'email_task_commented': self.email_task_commented,
            'email_task_due_soon': self.email_task_due_soon,
            'email_task_overdue': self.email_task_overdue,
            'inapp_task_assigned': self.inapp_task_assigned,
            'inapp_task_updated': self.inapp_task_updated,
            'inapp_task_commented': self.inapp_task_commented,
            'inapp_task_due_soon': self.inapp_task_due_soon,
            'inapp_task_overdue': self.inapp_task_overdue,
            'daily_digest': self.daily_digest,
            'weekly_digest': self.weekly_digest
        }


class FileAttachment(db.Model):
    __tablename__ = 'file_attachments'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)  # Size in bytes
    file_type = db.Column(db.String(100))  # MIME type
    file_path = db.Column(db.String(500), nullable=False)  # Path to file on server
    
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='uploaded_files')
    task = db.relationship('Task', backref='attachments')
    
    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else None,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'file_type': self.file_type,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None
        }


class Reminder(db.Model):
    __tablename__ = 'reminders'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    reminder_date = db.Column(db.DateTime, nullable=False)
    reminder_type = db.Column(db.String(50), default='custom')  # 'task_deadline', 'days_before', 'time_based', 'custom'
    days_before = db.Column(db.Integer, nullable=True)  # For days_before type
    time_based = db.Column(db.DateTime, nullable=True)  # For time_based type
    is_sent = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='reminders')
    task = db.relationship('Task', backref='reminders')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'task_id': self.task_id,
            'title': self.title,
            'description': self.description,
            'reminder_date': self.reminder_date.isoformat() if self.reminder_date else None,
            'reminder_type': self.reminder_type,
            'days_before': self.days_before,
            'time_based': self.time_based.isoformat() if self.time_based else None,
            'is_sent': self.is_sent,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'task_title': self.task.title if self.task else None
        }


class Meeting(db.Model):
    __tablename__ = 'meetings'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(255))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_meetings')
    project = db.relationship('Project', backref='meetings')
    invitations = db.relationship('MeetingInvitation', backref='meeting', cascade='all, delete-orphan', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'location': self.location,
            'created_by': self.created_by,
            'creator_name': self.creator.name if self.creator else None,
            'project_id': self.project_id,
            'project_name': self.project.name if self.project else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'invitations': [inv.to_dict() for inv in self.invitations] if self.invitations else []
        }


class MeetingInvitation(db.Model):
    __tablename__ = 'meeting_invitations'
    
    id = db.Column(db.Integer, primary_key=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meetings.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'confirmed', 'rejected'
    rejection_reason = db.Column(db.Text, nullable=True)
    responded_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='meeting_invitations')
    
    def to_dict(self):
        return {
            'id': self.id,
            'meeting_id': self.meeting_id,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else None,
            'user_email': self.user.email if self.user else None,
            'status': self.status,
            'rejection_reason': self.rejection_reason,
            'responded_at': self.responded_at.isoformat() if self.responded_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class ChatConversation(db.Model):
    """1-on-1 chat conversation between two users"""
    __tablename__ = 'chat_conversations'
    
    id = db.Column(db.Integer, primary_key=True)
    user1_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user2_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'accepted', 'rejected'
    requested_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    accepted_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user1 = db.relationship('User', foreign_keys=[user1_id], backref='chat_conversations_as_user1')
    user2 = db.relationship('User', foreign_keys=[user2_id], backref='chat_conversations_as_user2')
    requester = db.relationship('User', foreign_keys=[requested_by], backref='chat_requests_sent')
    messages = db.relationship('ChatMessage', backref='conversation', lazy=True, cascade='all, delete-orphan', order_by='ChatMessage.created_at')
    
    __table_args__ = (
        db.UniqueConstraint('user1_id', 'user2_id', name='uq_chat_users'),
    )
    
    def to_dict(self, current_user_id=None):
        """Convert to dictionary, showing other user info"""
        other_user = self.user1 if current_user_id == self.user2_id else self.user2
        return {
            'id': self.id,
            'other_user': {
                'id': other_user.id,
                'name': other_user.name,
                'email': other_user.email
            } if other_user else None,
            'status': self.status,
            'requested_by': self.requested_by,
            'requested_at': self.requested_at.isoformat() if self.requested_at else None,
            'accepted_at': self.accepted_at.isoformat() if self.accepted_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'unread_count': len([m for m in self.messages if m.recipient_id == current_user_id and not m.is_read]) if current_user_id else 0
        }


class ChatMessage(db.Model):
    """Individual message in a chat conversation"""
    __tablename__ = 'chat_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('chat_conversations.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # Use UnicodeText to preserve emojis and non-ASCII characters reliably across DB backends
    content = db.Column(db.UnicodeText, nullable=False)
    delivery_status = db.Column(db.String(20), default='sent')  # 'sent', 'delivered', 'read'
    is_read = db.Column(db.Boolean, default=False)
    read_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime)  # For tracking edits
    is_edited = db.Column(db.Boolean, default=False)
    is_deleted = db.Column(db.Boolean, default=False)  # Soft delete for everyone
    deleted_for_sender = db.Column(db.Boolean, default=False)  # Hide for sender only
    deleted_for_recipient = db.Column(db.Boolean, default=False)  # Hide for recipient only
    
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    recipient = db.relationship('User', foreign_keys=[recipient_id], backref='received_messages')
    reactions = db.relationship('MessageReaction', backref='message', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'sender_id': self.sender_id,
            'sender_name': self.sender.name if self.sender else None,
            'recipient_id': self.recipient_id,
            'content': self.content,
            'delivery_status': self.delivery_status,
            'is_read': self.is_read,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_edited': self.is_edited,
            'is_deleted': self.is_deleted,
            'reactions': [r.to_dict() for r in self.reactions] if hasattr(self, 'reactions') else []
        }


class MessageReaction(db.Model):
    """Emoji reactions to chat messages"""
    __tablename__ = 'message_reactions'
    
    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey('chat_messages.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    emoji = db.Column(db.String(10), nullable=False)  # Unicode emoji
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='message_reactions')
    
    __table_args__ = (
        db.UniqueConstraint('message_id', 'user_id', 'emoji', name='uq_message_user_emoji'),
    )
    
    def to_dict(self):
        # Ensure emoji is properly encoded as UTF-8 string
        emoji_value = self.emoji
        if emoji_value:
            # If emoji is bytes, decode it; if it's already a string, ensure it's valid UTF-8
            if isinstance(emoji_value, bytes):
                try:
                    emoji_value = emoji_value.decode('utf-8')
                except (UnicodeDecodeError, AttributeError):
                    emoji_value = str(emoji_value)
            # Ensure it's a valid string and not corrupted
            if not isinstance(emoji_value, str):
                emoji_value = str(emoji_value)
            # Remove any null bytes or invalid characters
            emoji_value = emoji_value.replace('\0', '').strip()
        
        return {
            'id': self.id,
            'message_id': self.message_id,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else None,
            'emoji': emoji_value,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }