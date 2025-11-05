# workhub-backend/validators.py
import re
import unicodedata
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import bleach

from models import User, Project, Sprint  # same folder: workhub-backend/models.py
from sqlalchemy.orm import Session


class ValidationError(ValueError):
    """Custom validation error with field-level details"""
    def __init__(self, message: str, field: str = None, code: str = None):
        super().__init__(message)
        self.message = message
        self.field = field
        self.code = code or "VALIDATION_ERROR"


class Validator:
    """
    Centralized validation with comprehensive security measures.
    Implements P0 & P1 validation rules.
    """

    # Users - Enhanced
    NAME_REGEX = re.compile(r"^[A-Za-z\s\-']{2,50}$")  # letters/spaces/hyphen/apostrophe; NO digits
    EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")
    
    # Enhanced password policy (P0): 10-12 chars minimum, 3 of 4 character classes
    PW_UPPER = re.compile(r"[A-Z]")
    PW_LOWER = re.compile(r"[a-z]")
    PW_DIGIT = re.compile(r"\d")
    PW_SPECIAL = re.compile(r"[^A-Za-z0-9]")  # any non-alphanumeric
    
    # Common weak passwords (P0)
    COMMON_PASSWORDS = {
        'password', 'password123', '12345678', 'qwerty123', 'abc123456',
        'welcome123', 'admin123', 'letmein123', 'monkey123', '1234567890',
        'password1', 'iloveyou', 'princess1', 'rockyou1', 'abc12345'
    }

    # Tasks - Enhanced
    PRIORITY_VALUES = {"low", "medium", "high"}
    STATUS_VALUES = {"todo", "in_progress", "completed", "blocked"}
    
    # Comments & Content
    PROFANITY_WORDS = ['damn', 'hell', 'crap', 'stupid', 'idiot', 'moron', 'fool', 'fuck', 'shit', 'ass', 'bitch']
    
    # File uploads (P0)
    ALLOWED_MIME_TYPES = {
        'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 
        'application/pdf', 'text/plain'
    }
    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.pdf', '.txt'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    BLOCKED_EXTENSIONS = {'.exe', '.bat', '.cmd', '.com', '.scr', '.pif', '.vbs', '.js', '.jar', '.dll', '.msi'}
    
    # Timing constraints (P1)
    MIN_DUE_DATE_LEAD_TIME = timedelta(hours=1)  # Tasks must be due at least 1 hour from now
    MAX_DUE_DATE_HORIZON = timedelta(days=365)  # Tasks can't be due more than 1 year ahead

    # ========== UTILITY METHODS ==========
    
    def _normalize_unicode(self, text: str) -> str:
        """Normalize Unicode to prevent homoglyph attacks (P1)"""
        if not isinstance(text, str):
            return text
        # NFC normalization: canonical composition
        normalized = unicodedata.normalize('NFC', text)
        # Remove zero-width characters
        normalized = ''.join(char for char in normalized 
                           if unicodedata.category(char) != 'Cf' or char in ['\u200c', '\u200d'])
        return normalized
    
    def _sanitize_html(self, text: str, strip_all: bool = False) -> str:
        """Sanitize HTML to prevent XSS (P0)"""
        if strip_all:
            # Strip all HTML tags
            return bleach.clean(text, tags=[], strip=True)
        else:
            # Allow only safe tags
            allowed_tags = ['b', 'i', 'u', 'em', 'strong', 'p', 'br']
            return bleach.clean(text, tags=allowed_tags, strip=True)
    
    def _trim_and_validate_not_empty(self, value: str, field_name: str) -> str:
        """Validate field is not empty or whitespace-only (P1)"""
        if not isinstance(value, str):
            raise ValidationError(f"{field_name} must be a string.", field=field_name, code="INVALID_TYPE")
        
        trimmed = value.strip()
        if not trimmed:
            raise ValidationError(f"{field_name} is required.", field=field_name, code="REQUIRED")
        
        return trimmed
    
    # ========== USER VALIDATION ==========
    
    def validate_name(self, name: str) -> str:
        """Validate user name with Unicode normalization (P1)"""
        name = self._trim_and_validate_not_empty(name, "Name")
        name = self._normalize_unicode(name)
        
        if not self.NAME_REGEX.fullmatch(name):
            raise ValidationError(
                "Name must be 2–50 characters and cannot contain numbers or symbols.",
                field="name",
                code="INVALID_FORMAT"
            )
        return name

    def validate_email(
        self,
        email: str,
        *,
        db: Optional[Session] = None,
        require_unique: bool = False,
    ) -> str:
        """Validate email with normalization (P1)"""
        email = self._trim_and_validate_not_empty(email, "Email")
        email = self._normalize_unicode(email).lower()  # Normalize and lowercase
        
        if not self.EMAIL_REGEX.fullmatch(email):
            raise ValidationError("Email format is invalid.", field="email", code="INVALID_FORMAT")
        
        if require_unique:
            if db is None:
                raise ValidationError("Internal error: DB session required for email check.")
            exists = db.query(User).filter(User.email.ilike(email)).first()
            if exists:
                # Generic message to prevent account enumeration (P0)
                raise ValidationError("Email already exists.", field="email", code="DUPLICATE")
        
        return email

    def validate_password(self, password: str) -> str:
        """
        Enhanced password policy (P0):
          - length 10–128 characters (increased from 8)
          - at least 3 of 4: upper/lower/digit/special
          - no common weak passwords
          - no sequential patterns
        """
        if not isinstance(password, str) or not password:
            raise ValidationError("Password is required.", field="password", code="REQUIRED")
        
        # Length check (P0: 10-12 chars minimum)
        if len(password) < 10:
            raise ValidationError("Password must be at least 10 characters.", field="password", code="TOO_SHORT")
        if len(password) > 128:
            raise ValidationError("Password must be less than 128 characters.", field="password", code="TOO_LONG")
        
        # Character class requirements: at least 3 of 4
        char_classes = 0
        if self.PW_UPPER.search(password):
            char_classes += 1
        if self.PW_LOWER.search(password):
            char_classes += 1
        if self.PW_DIGIT.search(password):
            char_classes += 1
        if self.PW_SPECIAL.search(password):
            char_classes += 1
        
        if char_classes < 3:
            raise ValidationError(
                "Password must include at least 3 of: uppercase, lowercase, digit, special character.",
                field="password",
                code="WEAK"
            )
        
        # Check against common passwords (P0)
        if password.lower() in self.COMMON_PASSWORDS:
            raise ValidationError("Password is too common. Please choose a stronger password.", 
                                field="password", code="COMMON")
        
        # Check for simple sequential patterns
        if re.search(r'(012|123|234|345|456|567|678|789|890|abc|bcd|cde|def)', password.lower()):
            raise ValidationError("Password contains sequential patterns. Please choose a stronger password.",
                                field="password", code="SEQUENTIAL")
        
        return password

    def validate_password_confirmation(self, password: str, confirm: Optional[str]) -> None:
        """Validate password confirmation matches"""
        if confirm is None or not confirm:
            raise ValidationError("Password confirmation is required.", 
                                field="confirm_password", code="REQUIRED")
        if password != confirm:
            raise ValidationError("Passwords do not match.", 
                                field="confirm_password", code="MISMATCH")

    def validate_user_payload(self, payload: dict, *, db: Session, check_unique_email: bool = True) -> dict:
        """Validate complete user registration/creation payload"""
        name = self.validate_name(payload.get("name", ""))
        email = self.validate_email(payload.get("email", ""), db=db, require_unique=check_unique_email)
        password = self.validate_password(payload.get("password", ""))
        
        if "confirm" in payload:  # FE sends it on create
            self.validate_password_confirmation(password, payload.get("confirm"))
        
        role = (payload.get("role") or "viewer").lower()
        valid_roles = {"super_admin", "admin", "manager", "team_lead", "developer", "viewer"}
        if role not in valid_roles:
            raise ValidationError(f"Role must be one of: {', '.join(valid_roles)}.", field="role", code="INVALID")
        
        return {"name": name, "email": email, "password": password, "role": role}

    # ========== TASK VALIDATION ==========
    
    def validate_task_title(self, title: str) -> str:
        """Validate task title (P1: 3-100 chars)"""
        title = self._trim_and_validate_not_empty(title, "Task title")
        title = self._normalize_unicode(title)
        
        # P1: Title must be 3-100 characters
        if len(title) < 3:
            raise ValidationError("Task title must be at least 3 characters.", 
                                field="title", code="TOO_SHORT")
        if len(title) > 100:
            raise ValidationError("Task title must be 100 characters or less.", 
                                field="title", code="TOO_LONG")
        
        # Sanitize HTML
        title = self._sanitize_html(title, strip_all=True)
        
        return title
    
    def validate_task_description(self, description: str) -> str:
        """Validate task description with XSS protection (P0)"""
        description = self._trim_and_validate_not_empty(description, "Description")
        description = self._normalize_unicode(description)
        
        if len(description) < 10:
            raise ValidationError("Description must be at least 10 characters.", 
                                field="description", code="TOO_SHORT")
        if len(description) > 1000:
            raise ValidationError("Description must be 1000 characters or less.", 
                                field="description", code="TOO_LONG")
        
        # Enhanced XSS protection (P0)
        dangerous_patterns = [
            r'<script', r'javascript:', r'vbscript:', r'onload\s*=', 
            r'onerror\s*=', r'onclick\s*=', r'onmouseover\s*=',
            r'<iframe', r'<embed', r'<object'
        ]
        
        description_lower = description.lower()
        for pattern in dangerous_patterns:
            if re.search(pattern, description_lower):
                raise ValidationError("Description contains potentially dangerous content.", 
                                    field="description", code="XSS_DETECTED")
        
        # Sanitize HTML but allow basic formatting
        description = self._sanitize_html(description, strip_all=False)
        
        return description
    
    def validate_priority(self, priority: Optional[str]) -> str:
        """Validate task priority"""
        if not priority:
            return "medium"  # Default
        
        priority = priority.lower().strip()
        if priority not in self.PRIORITY_VALUES:
            raise ValidationError(
                f"Priority must be one of: {', '.join(sorted(self.PRIORITY_VALUES))}.",
                field="priority",
                code="INVALID"
            )
        return priority
    
    def validate_status(self, status: Optional[str]) -> str:
        """Validate task status"""
        if not status:
            return "todo"  # Default
        
        status = status.lower().strip()
        if status not in self.STATUS_VALUES:
            raise ValidationError(
                f"Status must be one of: {', '.join(sorted(self.STATUS_VALUES))}.",
                field="status",
                code="INVALID"
            )
        return status
    
    def validate_due_date(self, due_date_str: Optional[str]) -> Optional[datetime]:
        """
        Validate due date with timezone discipline (P1):
        - Store in UTC
        - Min lead time: 1 hour
        - Max horizon: 1 year
        """
        if not due_date_str:
            return None
        
        try:
            # Parse ISO 8601 datetime
            ds = due_date_str.replace("Z", "+00:00")
            due_date_dt = datetime.fromisoformat(ds)
            
            # Ensure timezone-aware (P1: timezone discipline)
            if due_date_dt.tzinfo is None:
                due_date_dt = due_date_dt.replace(tzinfo=timezone.utc)
            
            # Convert to UTC for storage
            due_date_dt = due_date_dt.astimezone(timezone.utc)
            
            now = datetime.now(timezone.utc)
            
            # P1: Minimum lead time (1 hour)
            min_due_date = now + self.MIN_DUE_DATE_LEAD_TIME
            if due_date_dt < min_due_date:
                raise ValidationError(
                    "Due date must be at least 1 hour from now.",
                    field="due_date",
                    code="TOO_SOON"
                )
            
            # P1: Maximum horizon (1 year)
            max_due_date = now + self.MAX_DUE_DATE_HORIZON
            if due_date_dt > max_due_date:
                raise ValidationError(
                    "Due date cannot be more than 1 year in the future.",
                    field="due_date",
                    code="TOO_FAR"
                )
            
            return due_date_dt
            
        except ValueError:
            raise ValidationError(
                "Due date must be a valid ISO 8601 datetime.",
                field="due_date",
                code="INVALID_FORMAT"
            )
    
    def validate_assignee(self, assignee_id: Optional[int], db: Session) -> Optional[int]:
        """Validate assignee exists (P0: foreign key validation)"""
        if assignee_id is None:
            return None
        
        # P0: Referential integrity check
        user = db.query(User).filter_by(id=assignee_id).first()
        if not user:
            raise ValidationError("Assignee not found.", field="assigned_to", code="NOT_FOUND")
        
        return assignee_id
    
    def validate_tags(self, tags: Optional[list]) -> list:
        """Validate task tags (P1: max 5 tags, validated text)"""
        if not tags:
            return []
        
        if not isinstance(tags, list):
            raise ValidationError("Tags must be a list.", field="tags", code="INVALID_TYPE")
        
        if len(tags) > 5:
            raise ValidationError("Maximum 5 tags allowed.", field="tags", code="TOO_MANY")
        
        validated_tags = []
        for tag in tags:
            if not isinstance(tag, str):
                raise ValidationError("Each tag must be a string.", field="tags", code="INVALID_TYPE")
            
            tag = tag.strip()
            if not tag:
                continue  # Skip empty tags
            
            if len(tag) > 30:
                raise ValidationError("Each tag must be 30 characters or less.", 
                                    field="tags", code="TAG_TOO_LONG")
            
            # Sanitize tag
            tag = self._sanitize_html(tag, strip_all=True)
            validated_tags.append(tag)
        
        return validated_tags

    def validate_project_id(self, project_id: Optional[int], db: Session) -> Optional[int]:
        if project_id in (None, "", 0):
            return None
        try:
            pid = int(project_id)
        except (TypeError, ValueError):
            raise ValidationError("project_id must be an integer.", field="project_id", code="INVALID_TYPE")
        project = db.query(Project).filter_by(id=pid).first()
        if not project:
            raise ValidationError("Project not found.", field="project_id", code="NOT_FOUND")
        return pid

    def validate_sprint_id(self, sprint_id: Optional[int], db: Session, project_id: Optional[int] = None) -> Optional[int]:
        if sprint_id in (None, "", 0):
            return None
        try:
            sid = int(sprint_id)
        except (TypeError, ValueError):
            raise ValidationError("sprint_id must be an integer.", field="sprint_id", code="INVALID_TYPE")
        sprint = db.query(Sprint).filter_by(id=sid).first()
        if not sprint:
            raise ValidationError("Sprint not found.", field="sprint_id", code="NOT_FOUND")
        if project_id and sprint.project_id != project_id:
            raise ValidationError("Sprint does not belong to the specified project.", field="sprint_id", code="MISMATCH")
        return sid

    def validate_task_payload(self, payload: dict, *, db: Session, require_assigned_to: bool = True) -> dict:
        """Validate complete task creation/update payload"""
        title = self.validate_task_title(payload.get("title", ""))
        description = self.validate_task_description(payload.get("description", ""))
        priority = self.validate_priority(payload.get("priority"))
        status = self.validate_status(payload.get("status"))
        due_date = self.validate_due_date(payload.get("due_date"))
        assignee = self.validate_assignee(payload.get("assigned_to"), db)
        project_id = self.validate_project_id(payload.get("project_id"), db)
        sprint_id = self.validate_sprint_id(payload.get("sprint_id"), db, project_id)
        tags = self.validate_tags(payload.get("tags"))
        
        # If require_assigned_to is False (e.g., for subtasks), allow None assignee
        if require_assigned_to and not assignee:
            raise ValidationError("Assignee is required.", field="assigned_to", code="REQUIRED")

        return {
            "title": title,
            "description": description,
            "priority": priority,
            "status": status,
            "due_date": due_date,
            "assigned_to": assignee,
            "tags": tags,
            "project_id": project_id,
            "sprint_id": sprint_id,
        }

    # ========== PROJECT & SPRINT VALIDATION ==========

    def validate_project_payload(self, payload: dict, *, db: Session) -> dict:
        name = self._trim_and_validate_not_empty(payload.get("name", ""), "Project name")
        name = self._normalize_unicode(name)
        if len(name) < 3 or len(name) > 150:
            raise ValidationError("Project name must be 3-150 characters.", field="name", code="INVALID_LENGTH")
        description = (payload.get("description") or "").strip()
        if description:
            description = self._sanitize_html(description, strip_all=False)
        owner_id = payload.get("owner_id")
        if owner_id in (None, ""):
            owner_id_int = None
        else:
            try:
                owner_id_int = int(owner_id)
            except (TypeError, ValueError):
                raise ValidationError("owner_id must be an integer.", field="owner_id", code="INVALID_TYPE")
            if not db.query(User).filter_by(id=owner_id_int).first():
                raise ValidationError("Owner not found.", field="owner_id", code="NOT_FOUND")
        return {"name": name, "description": description, "owner_id": owner_id_int}

    def validate_sprint_payload(self, payload: dict, *, db: Session) -> dict:
        name = self._trim_and_validate_not_empty(payload.get("name", ""), "Sprint name")
        name = self._normalize_unicode(name)
        if len(name) < 3 or len(name) > 150:
            raise ValidationError("Sprint name must be 3-150 characters.", field="name", code="INVALID_LENGTH")
        goal = (payload.get("goal") or "").strip()
        if goal:
            goal = self._sanitize_html(goal, strip_all=False)
        project_id = self.validate_project_id(payload.get("project_id"), db)
        if not project_id:
            raise ValidationError("project_id is required.", field="project_id", code="REQUIRED")
        # Dates
        start_date_str = payload.get("start_date")
        end_date_str = payload.get("end_date")
        if not start_date_str or not end_date_str:
            raise ValidationError("start_date and end_date are required.", field="date_range", code="REQUIRED")
        try:
            ds = start_date_str.replace("Z", "+00:00")
            de = end_date_str.replace("Z", "+00:00")
            start_dt = datetime.fromisoformat(ds)
            end_dt = datetime.fromisoformat(de)
        except Exception:
            raise ValidationError("Dates must be ISO 8601 datetimes.", field="date_range", code="INVALID_FORMAT")
        if start_dt.tzinfo is None:
            start_dt = start_dt.replace(tzinfo=timezone.utc)
        if end_dt.tzinfo is None:
            end_dt = end_dt.replace(tzinfo=timezone.utc)
        start_dt = start_dt.astimezone(timezone.utc)
        end_dt = end_dt.astimezone(timezone.utc)
        if end_dt <= start_dt:
            raise ValidationError("end_date must be after start_date.", field="date_range", code="INVALID_RANGE")
        return {
            "project_id": project_id,
            "name": name,
            "goal": goal,
            "start_date": start_dt,
            "end_date": end_dt,
        }
    
    # ========== COMMENT VALIDATION ==========
    
    def validate_comment(self, payload: dict, allow_html: bool = True) -> dict:
        """Validate comment content - supports rich text HTML"""
        content = payload.get("content", "")
        if not isinstance(content, str):
            raise ValidationError("Comment content must be a string.", field="content", code="INVALID_TYPE")
        
        # Strip HTML tags for length check (count plain text only)
        import bleach
        plain_text = bleach.clean(content, tags=[], strip=True)
        plain_text = self._normalize_unicode(plain_text.strip())
        
        if not plain_text:
            raise ValidationError("Comment content is required.", field="content", code="REQUIRED")
        
        if len(plain_text) > 500:
            raise ValidationError("Comment must be 500 characters or less (plain text).", 
                                field="content", code="TOO_LONG")
        
        # Check for profanity in plain text (word boundary check to avoid false positives)
        content_lower = plain_text.lower()
        for word in self.PROFANITY_WORDS:
            # Use word boundaries to avoid matching substrings in legitimate words
            # e.g., "ass" shouldn't match in "Cassey", "pass", "class", "assignment", etc.
            pattern = r'\b' + re.escape(word) + r'\b'
            if re.search(pattern, content_lower):
                raise ValidationError("Comment contains inappropriate content.", 
                                    field="content", code="PROFANITY")
        
        # Sanitize HTML - allow rich text formatting tags
        if allow_html:
            # Allow safe formatting tags for rich text
            allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'b', 'i', 's', 'strike', 
                          'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'a']
            allowed_attributes = {
                'a': ['href', 'title', 'target']
            }
            content = bleach.clean(content, tags=allowed_tags, attributes=allowed_attributes, strip=True)
        else:
            # Strip all HTML for plain text comments
            content = self._sanitize_html(content, strip_all=True)
        
        return {"content": content}
    
    # ========== TIME LOG VALIDATION ==========
    
    def validate_time_log(self, payload: dict) -> dict:
        """Validate time log entry (was missing - now implemented)"""
        hours = payload.get("hours")
        
        if hours is None:
            raise ValidationError("Hours is required.", field="hours", code="REQUIRED")
        
        try:
            hours = float(hours)
        except (ValueError, TypeError):
            raise ValidationError("Hours must be a valid number.", field="hours", code="INVALID_TYPE")
        
        # Validate range: 0.1 to 24 hours
        if hours < 0.1:
            raise ValidationError("Hours must be at least 0.1.", field="hours", code="TOO_LOW")
        if hours > 24.0:
            raise ValidationError("Hours cannot exceed 24.", field="hours", code="TOO_HIGH")
        
        # Round to 2 decimal places
        hours = round(hours, 2)
        
        # Optional description
        description = payload.get("description", "")
        if description:
            description = self._normalize_unicode(description.strip())
            if len(description) > 500:
                raise ValidationError("Description must be 500 characters or less.", 
                                    field="description", code="TOO_LONG")
            description = self._sanitize_html(description, strip_all=True)
        
        return {"hours": hours, "description": description}
    
    # ========== FILE UPLOAD VALIDATION ==========
    
    def validate_file_upload(self, file_data: dict) -> dict:
        """
        Validate file upload (P0):
        - Allow-list MIME types
        - Max size check
        - Block executables
        - Sanitize filename
        """
        if not file_data:
            raise ValidationError("File is required.", field="file", code="REQUIRED")
        
        filename = file_data.get("filename", "")
        file_size = file_data.get("size", 0)
        mime_type = file_data.get("mime_type", "")
        
        # Sanitize filename (P0)
        if not filename:
            raise ValidationError("Filename is required.", field="file", code="NO_FILENAME")
        
        # Get extension
        file_ext = '.' + filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        
        # Block executables (P0)
        if file_ext in self.BLOCKED_EXTENSIONS:
            raise ValidationError("Executable files are not allowed.", field="file", code="BLOCKED_TYPE")
        
        # Allow-list extensions (P0)
        if file_ext not in self.ALLOWED_EXTENSIONS:
            raise ValidationError(
                f"File type not allowed. Allowed types: {', '.join(self.ALLOWED_EXTENSIONS)}",
                field="file",
                code="INVALID_TYPE"
            )
        
        # Allow-list MIME types (P0)
        if mime_type not in self.ALLOWED_MIME_TYPES:
            raise ValidationError(
                "File MIME type not allowed.",
                field="file",
                code="INVALID_MIME"
            )
        
        # Max size check (P0: 10MB)
        if file_size > self.MAX_FILE_SIZE:
            max_mb = self.MAX_FILE_SIZE / (1024 * 1024)
            raise ValidationError(
                f"File size must be less than {max_mb}MB.",
                field="file",
                code="TOO_LARGE"
            )
        
        # Generate safe server-side filename (P0)
        import uuid
        safe_filename = f"{uuid.uuid4().hex}{file_ext}"
        
        return {
            "original_filename": filename,
            "safe_filename": safe_filename,
            "size": file_size,
            "mime_type": mime_type,
        }


validator = Validator()
