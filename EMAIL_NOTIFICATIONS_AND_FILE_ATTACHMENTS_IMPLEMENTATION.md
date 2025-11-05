# 📧 Email Notifications & 📎 File Attachments Implementation

## Overview
This document describes the implementation of two major features for the WorkHub Task Management System:
1. **Email Notification System** - Send email notifications for task events
2. **File Attachments** - Upload, download, and manage files attached to tasks

---

## 🚀 Feature 1: Email Notification System

### Backend Implementation

#### 1. Email Service (`email_service.py`)
A comprehensive email service with HTML templates for various notification types:

**Features:**
- ✅ SMTP configuration support (Gmail, custom servers)
- ✅ HTML email templates with responsive design
- ✅ Multiple notification types:
  - Task assigned
  - Task updated
  - New comments
  - Task due soon (24 hours)
  - Task overdue
- ✅ Plain text fallback for email clients
- ✅ Clickable links to tasks in frontend
- ✅ Beautiful gradient design matching WorkHub branding

**Configuration (Environment Variables):**
```bash
EMAIL_NOTIFICATIONS_ENABLED=true
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@workhub.com
SMTP_FROM_NAME=WorkHub Task Management
FRONTEND_URL=http://localhost:5173
```

**Gmail Setup:**
1. Enable 2-Factor Authentication on your Google Account
2. Generate an "App Password":
   - Go to Google Account Settings → Security → App Passwords
   - Select "Mail" and your device
   - Copy the generated 16-character password
3. Use this app password as `SMTP_PASSWORD`

#### 2. Notification Preferences Model (`models.py`)
New database model to store user notification preferences:

```python
class NotificationPreference(db.Model):
    # Email notifications
    email_task_assigned = db.Column(db.Boolean, default=True)
    email_task_updated = db.Column(db.Boolean, default=True)
    email_task_commented = db.Column(db.Boolean, default=True)
    email_task_due_soon = db.Column(db.Boolean, default=True)
    email_task_overdue = db.Column(db.Boolean, default=True)
    
    # In-app notifications
    inapp_task_assigned = db.Column(db.Boolean, default=True)
    inapp_task_updated = db.Column(db.Boolean, default=True)
    inapp_task_commented = db.Column(db.Boolean, default=True)
    inapp_task_due_soon = db.Column(db.Boolean, default=True)
    inapp_task_overdue = db.Column(db.Boolean, default=True)
    
    # Digest settings
    daily_digest = db.Column(db.Boolean, default=False)
    weekly_digest = db.Column(db.Boolean, default=False)
```

#### 3. Enhanced Notifications Module (`notifications.py`)
Added `create_notification_with_email()` helper function that:
- Creates in-app notification
- Checks user preferences
- Sends email if user has opted in
- Respects per-notification-type preferences

**API Endpoints:**
- `GET /api/notifications/preferences` - Get user's notification preferences
- `PUT /api/notifications/preferences` - Update notification preferences

#### 4. SMTP Configuration in SystemSettings
Extended `SystemSettings` model to store SMTP configuration in database:
```python
smtp_server = db.Column(db.String(255), default='smtp.gmail.com')
smtp_port = db.Column(db.Integer, default=587)
smtp_username = db.Column(db.String(255))
smtp_password = db.Column(db.String(255))
smtp_from_email = db.Column(db.String(255))
smtp_from_name = db.Column(db.String(255))
```

### Frontend Implementation

#### 1. Notification Preferences UI (`Settings.jsx`)
New "Notification Preferences" tab with three sections:

**Email Notifications:**
- Task Assigned
- Task Updated
- New Comment
- Task Due Soon
- Task Overdue

**In-App Notifications:**
- Same types as email notifications

**Digest Settings:**
- Daily Digest (9:00 AM)
- Weekly Digest (Mondays at 9:00 AM)

#### 2. API Integration (`api.js`)
```javascript
notificationsAPI: {
  getPreferences: () => api.get('/notifications/preferences'),
  updatePreferences: (data) => api.put('/notifications/preferences', data)
}
```

### How to Use

#### For Administrators:
1. Configure SMTP settings via environment variables (or future admin UI)
2. Enable email notifications: `EMAIL_NOTIFICATIONS_ENABLED=true`
3. Restart the application

#### For Users:
1. Navigate to Settings → Notification Preferences
2. Toggle email notifications for each event type
3. Optionally enable daily/weekly digest
4. Save preferences

#### Testing Email Notifications:
1. Assign a task to a user
2. Check the user's email inbox
3. Verify the email has proper formatting and clickable links

**Note:** If email notifications are disabled or SMTP is not configured, the system will only create in-app notifications.

---

## 📎 Feature 2: File Attachments

### Backend Implementation

#### 1. File Uploads Service (`file_uploads.py`)
Comprehensive file upload system with validation and security:

**Features:**
- ✅ File upload with validation (size, type)
- ✅ Maximum file size: 50 MB
- ✅ Allowed file types:
  - Documents: txt, pdf, doc, docx, xls, xlsx, ppt, pptx, md, log
  - Images: png, jpg, jpeg, gif
  - Archives: zip, rar, 7z
  - Media: mp4, avi, mov, mp3, wav
  - Data: csv, json, xml
- ✅ Unique filename generation (prevents collisions)
- ✅ Secure file storage in `uploads/` directory
- ✅ Role-based access control:
  - Admins can add attachments to any task
  - Users can add attachments to tasks they're assigned or created
  - Only admins and the uploader can delete attachments
  - All involved users can download attachments

**API Endpoints:**
- `POST /api/files/task/<task_id>/upload` - Upload file to task
- `GET /api/files/task/<task_id>/attachments` - Get all attachments for a task
- `GET /api/files/attachment/<attachment_id>/download` - Download file
- `DELETE /api/files/attachment/<attachment_id>` - Delete attachment
- `GET /api/files/stats` - Get upload statistics (admin only)

#### 2. FileAttachment Model (`models.py`)
```python
class FileAttachment(db.Model):
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    filename = db.Column(db.String(255))  # Unique filename on server
    original_filename = db.Column(db.String(255))  # Original user filename
    file_size = db.Column(db.Integer)  # Size in bytes
    file_type = db.Column(db.String(100))  # MIME type
    file_path = db.Column(db.String(500))  # Path on server
    uploaded_at = db.Column(db.DateTime)
```

#### 3. App Configuration (`app.py`)
```python
app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB
app.register_blueprint(file_uploads_bp, url_prefix='/api/files')
```

### Frontend Implementation

#### 1. FileUpload Component (`FileUpload.jsx`)
Beautiful drag-and-drop file upload component:

**Features:**
- ✅ Drag and drop support
- ✅ Click to browse files
- ✅ Real-time upload progress
- ✅ Client-side file validation
- ✅ Visual feedback for drag state
- ✅ Error handling with dismissible alerts
- ✅ Maximum file size display

#### 2. AttachmentsList Component (`FileUpload.jsx`)
Display and manage attachments:

**Features:**
- ✅ File type icons (🖼️ images, 📄 PDF, 📦 archives, etc.)
- ✅ File size display (human-readable: KB, MB, GB)
- ✅ Uploader name and timestamp
- ✅ Download button
- ✅ Delete button (with confirmation)
- ✅ Responsive layout
- ✅ Empty state message

#### 3. Integration in Tasks Page (`Tasks.jsx`)
Added "Attachments" section to task detail modal:

**Workflow:**
1. View task details
2. Scroll to "Attachments" section
3. Drag and drop files or click to browse
4. Files upload automatically
5. Attachments list updates in real-time
6. Download or delete attachments as needed

#### 4. API Integration (`api.js`)
```javascript
filesAPI: {
  uploadToTask: (taskId, file) => { /* FormData upload */ },
  getTaskAttachments: (taskId) => api.get(`/files/task/${taskId}/attachments`),
  downloadAttachment: (attachmentId) => api.get(`/files/attachment/${attachmentId}/download`, { responseType: 'blob' }),
  deleteAttachment: (attachmentId) => api.delete(`/files/attachment/${attachmentId}`),
  getUploadStats: () => api.get('/files/stats')
}
```

### How to Use

#### Upload Files:
1. Open a task detail modal (click on task title)
2. Scroll to the "Attachments" section
3. Either:
   - Drag and drop files into the upload area
   - Click the upload area to browse files
4. Wait for upload to complete
5. File appears in attachments list

#### Download Files:
1. Open task detail modal
2. Find the attachment in the list
3. Click the download button (⬇️)
4. File downloads to your browser's download folder

#### Delete Files:
1. Open task detail modal
2. Find the attachment in the list
3. Click the delete button (🗑️)
4. Confirm deletion
5. File is removed from server and database

### Security Considerations

**Backend:**
- ✅ File type whitelist (prevents malicious file uploads)
- ✅ File size limit (prevents DoS via large uploads)
- ✅ Unique filename generation (prevents path traversal attacks)
- ✅ Role-based access control (prevents unauthorized access)
- ✅ Secure file serving (no directory listing)

**Frontend:**
- ✅ Client-side validation (immediate feedback)
- ✅ Confirmation dialogs for deletion (prevents accidents)
- ✅ Proper MIME type handling for downloads

---

## 🗄️ Database Migration

To add the new models to your database, run:

```bash
# Option 1: Using Flask shell
python -c "from app import create_app; from models import db; app = create_app(); app.app_context().push(); db.create_all(); print('Database updated!')"

# Option 2: Using init_db.py (if you have it)
python init_db.py

# Option 3: Manual migration (recommended for production)
# 1. Backup your database
# 2. Generate migration with Flask-Migrate
flask db migrate -m "Add notification preferences and file attachments"
flask db upgrade
```

**New Tables:**
- `notification_preferences` - Stores user notification preferences
- `file_attachments` - Stores file metadata

**Modified Tables:**
- `system_settings` - Added SMTP configuration fields

---

## 📊 File Upload Statistics (Admin Only)

Admins can view upload statistics:

```javascript
GET /api/files/stats

Response:
{
  "total_files": 42,
  "total_size_mb": 128.5,
  "top_uploaders": [
    { "name": "John Doe", "file_count": 15 },
    { "name": "Jane Smith", "file_count": 12 }
  ]
}
```

---

## 🎨 UI/UX Highlights

### Email Templates:
- Modern gradient header (purple to violet)
- Responsive design (works on mobile and desktop)
- Color-coded priority badges (High: Red, Medium: Orange, Low: Green)
- Clickable "View Task" buttons
- Professional footer with branding

### File Upload:
- Intuitive drag-and-drop interface
- Visual feedback on drag hover (border color change)
- Progress indicator during upload
- Beautiful file type icons (emoji-based for universal support)
- Human-readable file sizes
- Clean, card-based attachment list

---

## 🐛 Troubleshooting

### Email Notifications Not Sending:

**Check 1:** Is email enabled?
```bash
# In environment variables or config
EMAIL_NOTIFICATIONS_ENABLED=true
```

**Check 2:** Are SMTP credentials correct?
```bash
# Test SMTP connection
python -c "
from email_service import EmailService
import smtplib
try:
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login('your-email', 'your-app-password')
    print('✅ SMTP connection successful!')
except Exception as e:
    print(f'❌ SMTP error: {e}')
"
```

**Check 3:** Check application logs
```bash
# Look for email service logs
tail -f app.log | grep "Email"
```

**Common Issues:**
- Gmail blocking sign-in: Enable "Less secure app access" or use App Password
- Firewall blocking port 587: Check network settings
- Wrong SMTP server/port: Verify with your email provider

### File Upload Errors:

**Error:** "File is too large"
- **Solution:** File exceeds 50 MB limit. Compress or split the file.

**Error:** "File type not allowed"
- **Solution:** File extension not in whitelist. Convert to supported format.

**Error:** "Failed to upload file"
- **Solution:** Check server permissions on `uploads/` directory:
  ```bash
  mkdir -p uploads
  chmod 755 uploads
  ```

**Error:** "You do not have permission"
- **Solution:** Only admins and task participants can upload. Check task assignment.

---

## 🔮 Future Enhancements

### Email Notifications:
- [ ] Scheduled digest emails (daily/weekly summaries)
- [ ] Email templates customization in admin UI
- [ ] Support for multiple email providers (SendGrid, AWS SES, Mailgun)
- [ ] Unsubscribe links in emails
- [ ] Email tracking (open rates, click rates)
- [ ] Rich text formatting in email bodies
- [ ] Inline images in email templates
- [ ] Mention notifications (@user in comments)

### File Attachments:
- [ ] File preview (images, PDFs) in browser
- [ ] Multiple file upload at once
- [ ] File versioning (upload new version of same file)
- [ ] File comments/annotations
- [ ] Virus scanning integration (ClamAV)
- [ ] Cloud storage integration (AWS S3, Google Drive, Dropbox)
- [ ] Thumbnail generation for images
- [ ] File search and filtering
- [ ] Bulk download (zip multiple files)
- [ ] Storage quotas per user/project
- [ ] File sharing links (public/private)
- [ ] File expiration dates

---

## 📚 Related Documentation

- `ENHANCED_FEATURES_ROADMAP.md` - Full feature roadmap
- `VALIDATION_IMPLEMENTATION_SUMMARY.md` - UI validation features
- `REAL_TIME_EMAIL_VALIDATION_IMPLEMENTATION.md` - Email format validation
- `PROJECT_STRUCTURE.md` - Project organization
- `QUICKSTART.md` - Setup and installation guide

---

## ✅ Testing Checklist

### Email Notifications:
- [ ] Configure SMTP credentials
- [ ] Enable email notifications
- [ ] Create/assign a task
- [ ] Verify email received
- [ ] Check email formatting
- [ ] Test all notification types
- [ ] Verify preference controls work
- [ ] Test digest mode (if implemented)

### File Attachments:
- [ ] Upload a file via drag-and-drop
- [ ] Upload a file via click-to-browse
- [ ] Upload various file types
- [ ] Try uploading too-large file (should fail)
- [ ] Try uploading disallowed file type (should fail)
- [ ] Download an attachment
- [ ] Delete an attachment
- [ ] Test permissions (admin vs user)
- [ ] Upload multiple files to one task
- [ ] Check file statistics (admin)

---

## 🎉 Implementation Complete!

Both Email Notifications and File Attachments are now fully integrated into the WorkHub Task Management System. Users can receive timely email updates about their tasks and attach important files for collaboration.

**Next Steps:**
1. Configure SMTP credentials
2. Run database migrations
3. Test email notifications
4. Test file uploads
5. Train users on new features
6. Monitor for issues

For questions or issues, please refer to the troubleshooting section or contact the development team.

