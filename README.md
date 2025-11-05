# WorkHub - Enterprise Task Management System

## Requirements Specification Document (RSD)
**Version:** 2.0  
**Last Updated:** November 2025  
**Status:** Production Ready  
**Document Type:** Functional & Non-Functional Requirements Specification

---

## Table of Contents
1. [Executive Summary](#1-executive-summary)
2. [System Overview](#2-system-overview)
3. [Functional Requirements](#3-functional-requirements)
4. [Non-Functional Requirements](#4-non-functional-requirements)
5. [API Specifications (API-First Approach)](#5-api-specifications)
6. [Validation Rules & Business Logic](#6-validation-rules--business-logic)
7. [Security Requirements](#7-security-requirements)
8. [Architecture & Technology Stack](#8-architecture--technology-stack)
9. [Database Schema](#9-database-schema)
10. [Deployment & Installation](#10-deployment--installation)

---

## 1. Executive Summary

### 1.1 Purpose
WorkHub is an enterprise-grade, full-stack task management platform designed to streamline project collaboration, resource allocation, and workflow automation for teams of 5-500 users.

### 1.2 Scope
This document defines the complete functional and non-functional requirements for the WorkHub Task Management System, including API specifications, validation rules, security protocols, and deployment procedures.

### 1.3 System Capabilities
- **User Management:** 6-tier role-based access control (Super Admin, Admin, Manager, Team Lead, Developer, Viewer)
- **Task Management:** Comprehensive CRUD operations with dependencies, subtasks, and bulk operations
- **Project & Sprint Management:** Agile workflow support with sprint planning and tracking
- **Real-Time Communication:** Built-in chat with file attachments, emoji reactions, and typing indicators
- **Calendar & Scheduling:** Meeting management, reminders, and calendar integration
- **Reporting & Analytics:** Advanced reports with CSV export and data visualization
- **File Management:** Secure file uploads with role-based access and cloud storage support

---

## 2. System Overview

### 2.1 System Architecture
```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   React SPA     │◄────►│   Flask API     │◄────►│  SQL Server DB  │
│   (Frontend)    │ HTTP │   (Backend)     │ SQL  │  (Database)     │
└─────────────────┘      └─────────────────┘      └─────────────────┘
         │                        │                         │
         │                        ▼                         │
         │               ┌─────────────────┐              │
         └──────────────►│  Cloud Storage  │◄─────────────┘
                         │   (GCS/Local)   │
                         └─────────────────┘
```

### 2.2 Technology Stack
- **Frontend:** React 18, Vite, React Router v6, Axios
- **Backend:** Python 3.11, Flask 3.0, SQLAlchemy, Flask-JWT-Extended
- **Database:** SQL Server 2022 (Production), MSSQL with pymssql driver
- **Infrastructure:** Docker, Docker Compose, Google Cloud Platform (GCP)
- **CI/CD:** GitHub Actions, Google Cloud Build
- **Storage:** Google Cloud Storage (Production), Local filesystem (Development)

### 2.3 Deployment Targets
- **Development:** Local Docker containers
- **Production:** Google Cloud Run + Cloud SQL + Cloud Storage

---

## 3. Functional Requirements

### 3.1 User Management (FR-UM)

#### FR-UM-001: User Registration & Email Verification
- **Description:** Users must register with email verification before admin approval
- **Business Rule:** 
  - Email must be unique, valid format, non-disposable
  - 6-digit verification code sent via email (24-hour expiry)
  - User account status: `pending` → `approved` or `rejected`
- **Validation:**
  - Email format validation with regex
  - MX record verification
  - Disposable email domain blocking
  - Password strength: min 8 chars, uppercase, lowercase, number, special char
- **API Endpoint:** `POST /api/auth/register`, `POST /api/auth/verify-email`

#### FR-UM-002: Role-Based Access Control (RBAC)
- **Roles & Hierarchy:**
  1. **Super Admin:** Full system access, user promotion, system settings
  2. **Admin:** User management, project management, all reports
  3. **Manager:** Project creation, team management, task assignment
  4. **Team Lead:** Sprint management, task creation for team members
  5. **Developer:** Task updates, comments, time logging
  6. **Viewer:** Read-only access to assigned projects

- **Permission Matrix:**
  | Permission | Super Admin | Admin | Manager | Team Lead | Developer | Viewer |
  |------------|-------------|-------|---------|-----------|-----------|--------|
  | USERS_CREATE | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
  | USERS_DELETE | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
  | TASKS_CREATE | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
  | TASKS_DELETE | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
  | PROJECTS_CREATE | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
  | REPORTS_ADMIN | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
  | SETTINGS_MANAGE | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |

#### FR-UM-003: User Authentication
- **Requirement:** Secure JWT-based authentication with token refresh
- **Business Rules:**
  - Access token expiry: 1 hour
  - Refresh token expiry: 7 days
  - Maximum 5 failed login attempts before 15-minute lockout
  - Password reset via email with time-limited token (1 hour)
- **API Endpoints:** `POST /api/auth/login`, `POST /api/auth/refresh`, `POST /api/auth/forgot-password`

### 3.2 Task Management (FR-TM)

#### FR-TM-001: Task CRUD Operations
- **Create Task:**
  - **Required Fields:** title (3-100 chars), project_id, status
  - **Optional Fields:** description (max 500 chars), priority, due_date, assigned_to, sprint_id, blocks_task_id
  - **Business Rules:**
    - Only Manager, Team Lead, Admin, Super Admin can create tasks
    - Due date must be in future or same-day (min 1 hour ahead)
    - Assignee must be project member
  - **API:** `POST /api/tasks/`

- **Update Task:**
  - **Authorization:** Creator, Assignee, Manager+
  - **Business Rules:**
    - Status change to `completed` requires all blocking tasks to be completed
    - Status change validation applies to both single and bulk updates
  - **API:** `PUT /api/tasks/{id}`, `POST /api/tasks/bulk-update`

- **Delete Task:**
  - **Authorization:** Admin, Super Admin, Task Creator
  - **Business Rule:** Cascade delete comments, attachments, and time logs
  - **API:** `DELETE /api/tasks/{id}`

#### FR-TM-002: Task Dependencies
- **Requirement:** Tasks can block other tasks (predecessor-successor relationship)
- **Business Rules:**
  - A task cannot be marked `completed` if it blocks an incomplete task
  - Dependency validation enforced in both single and bulk updates
  - Circular dependencies are prevented
- **Validation:** Backend enforcement with clear error messages

#### FR-TM-003: Task Comments & Mentions
- **Requirement:** Users can comment on tasks with @mentions
- **Business Rules:**
  - Comments support rich text (markdown)
  - @mentions trigger email notifications
  - Only project members can comment
  - Comment length: max 1000 chars
- **API:** `POST /api/tasks/{id}/comments`, `GET /api/tasks/{id}/comments`

#### FR-TM-004: File Attachments
- **Requirement:** Tasks support multiple file attachments
- **Validation Rules:**
  - Max file size: 50 MB (single file), 100 MB (total per task)
  - Allowed types: PDF, DOC, DOCX, XLS, XLSX, PNG, JPG, MP4, ZIP
  - File name sanitization to prevent injection
- **Business Rules:**
  - Only project members can upload/view attachments
  - Admin/Super Admin can delete any attachment
  - Files stored in Cloud Storage (production) or local filesystem (dev)
- **API:** `POST /api/tasks/{id}/attachments`, `GET /api/tasks/attachments/{id}/download`

### 3.3 Project & Sprint Management (FR-PM)

#### FR-PM-001: Project Management
- **Create Project:**
  - **Required:** name (3-100 chars), owner_id (admin/super_admin only)
  - **Optional:** description (max 500 chars), start_date, end_date
  - **Business Rules:**
    - Only Manager, Admin, Super Admin can create projects
    - Project owner must be admin or super_admin
    - Team members are explicitly assigned
- **API:** `POST /api/projects/`, `PUT /api/projects/{id}`, `DELETE /api/projects/{id}`

#### FR-PM-002: Project Visibility
- **Business Rules:**
  - Viewer, Developer, Team Lead, Manager: See only assigned projects
  - Admin, Super Admin: See all projects + edit permissions
- **API:** `GET /api/projects/`, `GET /api/projects/mine`

#### FR-PM-003: Sprint Management
- **Requirement:** Agile sprint support with time-boxed iterations
- **Business Rules:**
  - Sprint duration: 1-4 weeks
  - Sprints belong to projects
  - Tasks can be assigned to sprints
  - Sprint status: `planned`, `active`, `completed`
- **API:** `POST /api/sprints/`, `GET /api/sprints/`, `PUT /api/sprints/{id}`

### 3.4 Communication (FR-COMM)

#### FR-COMM-001: Real-Time Chat
- **Requirement:** User-to-user chat with file sharing
- **Features:**
  - 1-on-1 messaging
  - File attachments (audio, photo, video, docs up to 100MB)
  - Emoji reactions on messages
  - Message edit (30-minute window)
  - Message delete (soft delete, 30-minute window)
  - Typing indicators
  - Read receipts
- **Validation:**
  - Message length: 1-2000 chars
  - Profanity filter with word boundary detection
  - Emoji support via Unicode (db.UnicodeText)
- **API:** `POST /api/chat/send`, `GET /api/chat/messages`, `POST /api/chat/reactions`

#### FR-COMM-002: Notifications
- **Types:**
  - Task assignment, task update, task comment, task due soon, task overdue
  - User approval/rejection, password reset
- **Channels:**
  - In-app notifications (bell icon with badge count)
  - Email notifications (HTML templates, user-configurable)
- **Business Rules:**
  - Users can configure notification preferences per type
  - Notifications marked read/unread
  - Auto-clear after 30 days
- **API:** `GET /api/notifications/`, `PUT /api/notifications/{id}/read`

### 3.5 Calendar & Reminders (FR-CAL)

#### FR-CAL-001: Meeting Management
- **Create Meeting:**
  - **Required:** title, start_time, end_time
  - **Validation:**
    - End time after start time
    - Max duration: 8 hours
    - No past scheduling
    - Warning if outside business hours (7 AM - 6 PM)
    - Max 1 year ahead
- **API:** `POST /api/meetings/`, `GET /api/meetings/`, `DELETE /api/meetings/{id}`

#### FR-CAL-002: Reminders
- **Create Reminder:**
  - **Required:** title, reminder_date, days_before
  - **Validation:**
    - Reminder date: No past dates, max 1 year ahead
    - Days before: Positive integer, 1-365 range
    - Title: 3-100 chars
    - Description: max 500 chars
- **API:** `POST /api/reminders/`, `GET /api/reminders/`, `DELETE /api/reminders/{id}`

### 3.6 Reporting & Analytics (FR-REP)

#### FR-REP-001: Personal Reports
- **Available to:** All authenticated users
- **Reports:**
  - Task status distribution (pie chart)
  - Activity timeline (last 30 days)
  - Assigned vs completed tasks
- **API:** `GET /api/reports/personal/task-status`, `GET /api/reports/personal/activity`

#### FR-REP-002: Admin Reports
- **Available to:** Admin, Super Admin
- **Reports:**
  - System overview (users, tasks, projects)
  - Sprint summary with burndown
  - User productivity metrics
  - Task completion trends
- **Export:** CSV format
- **API:** `GET /api/reports/admin/overview`, `POST /api/reports/export/csv`

---

## 4. Non-Functional Requirements

### 4.1 Performance (NFR-PERF)
- **NFR-PERF-001:** System must support 500+ concurrent users
- **NFR-PERF-002:** API response time < 200ms for 95% of requests
- **NFR-PERF-003:** Page load time < 2 seconds on 4G connection
- **NFR-PERF-004:** Database queries optimized with indexes on foreign keys

### 4.2 Scalability (NFR-SCALE)
- **NFR-SCALE-001:** Horizontal scaling via Cloud Run (auto-scaling)
- **NFR-SCALE-002:** Database connection pooling (max 20 connections per instance)
- **NFR-SCALE-003:** File storage decoupled via Cloud Storage
- **NFR-SCALE-004:** Stateless backend for load balancing

### 4.3 Availability (NFR-AVAIL)
- **NFR-AVAIL-001:** 99% uptime SLA
- **NFR-AVAIL-002:** Health check endpoints for all services
- **NFR-AVAIL-003:** Database automated backups (daily, 30-day retention)
- **NFR-AVAIL-004:** Graceful degradation if email service is unavailable

### 4.4 Security (NFR-SEC)
- **NFR-SEC-001:** All passwords hashed with bcrypt (cost factor 12)
- **NFR-SEC-002:** JWT tokens with short expiry (1 hour)
- **NFR-SEC-003:** HTTPS only in production
- **NFR-SEC-004:** SQL injection prevention via ORM (SQLAlchemy)
- **NFR-SEC-005:** XSS prevention via HTML escaping in email templates
- **NFR-SEC-006:** CSRF protection via JWT in Authorization header
- **NFR-SEC-007:** Rate limiting: 100 requests/minute per IP
- **NFR-SEC-008:** Account lockout after 5 failed login attempts

### 4.5 Usability (NFR-USE)
- **NFR-USE-001:** Responsive design (mobile, tablet, desktop)
- **NFR-USE-002:** Toast notifications for user actions (non-blocking)
- **NFR-USE-003:** Form validation with real-time feedback
- **NFR-USE-004:** Character counters for text inputs
- **NFR-USE-005:** Dark mode support (user preference)

### 4.6 Maintainability (NFR-MAINT)
- **NFR-MAINT-001:** Modular codebase with separation of concerns
- **NFR-MAINT-002:** RESTful API design
- **NFR-MAINT-003:** Comprehensive error logging
- **NFR-MAINT-004:** Database migrations via SQLAlchemy
- **NFR-MAINT-005:** Docker containerization for consistent environments

---

## 5. API Specifications

### 5.1 API Design Principles
- **RESTful:** Resource-based URLs, HTTP verbs for actions
- **Versioning:** `/api/v1/` prefix (future-proof)
- **Authentication:** JWT in `Authorization: Bearer <token>` header
- **Response Format:** JSON with consistent structure
- **Error Handling:** Standardized error codes and messages
- **CORS:** Configurable origins for security

### 5.2 Standard Response Structure

#### Success Response (200 OK)
```json
{
  "data": { ... },
  "message": "Success message",
  "timestamp": "2025-11-05T12:00:00Z"
}
```

#### Error Response (4xx, 5xx)
```json
{
  "error": "Error message",
  "code": "ERROR_CODE",
  "details": { ... },
  "timestamp": "2025-11-05T12:00:00Z"
}
```

### 5.3 Authentication Endpoints

#### POST /api/auth/register
**Description:** Register new user with email verification  
**Authorization:** Public  
**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "name": "John Doe",
  "role": "developer"
}
```
**Response:** `201 Created`
```json
{
  "message": "User registered. Verification code sent to email.",
  "user_id": 123
}
```
**Validation:**
- Email: Valid format, unique, non-disposable
- Password: Min 8 chars, uppercase, lowercase, number, special
- Name: 2-100 chars
- Role: Must be valid enum

#### POST /api/auth/verify-email
**Description:** Verify email with 6-digit code  
**Authorization:** Public  
**Request Body:**
```json
{
  "email": "user@example.com",
  "code": "123456"
}
```
**Response:** `200 OK`
```json
{
  "message": "Email verified. Awaiting admin approval."
}
```

#### POST /api/auth/login
**Description:** Authenticate user and receive JWT  
**Authorization:** Public  
**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```
**Response:** `200 OK`
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 123,
    "email": "user@example.com",
    "name": "John Doe",
    "role": "developer"
  }
}
```
**Error Codes:**
- `401`: Invalid credentials
- `403`: Account not approved or locked

#### GET /api/auth/me
**Description:** Get current user profile  
**Authorization:** Required (JWT)  
**Response:** `200 OK`
```json
{
  "id": 123,
  "email": "user@example.com",
  "name": "John Doe",
  "role": "developer",
  "status": "approved"
}
```

### 5.4 Task Management Endpoints

#### GET /api/tasks/
**Description:** List tasks with filters and pagination  
**Authorization:** Required (see project members)  
**Query Parameters:**
- `status`: Filter by status (todo, in_progress, completed)
- `priority`: Filter by priority (low, medium, high)
- `assigned_to`: Filter by user ID
- `project_id`: Filter by project
- `sprint_id`: Filter by sprint
- `search`: Full-text search in title/description
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 20, max: 100)

**Response:** `200 OK`
```json
{
  "tasks": [
    {
      "id": 1,
      "title": "Implement login API",
      "description": "Create JWT-based authentication",
      "priority": "high",
      "status": "in_progress",
      "due_date": "2025-11-10T23:59:59Z",
      "assigned_to": {
        "id": 123,
        "name": "John Doe",
        "email": "john@example.com"
      },
      "project": {
        "id": 5,
        "name": "Backend Development"
      },
      "sprint": {
        "id": 2,
        "name": "Sprint 3"
      },
      "created_by": {
        "id": 1,
        "name": "Admin User"
      },
      "created_at": "2025-11-01T10:00:00Z",
      "updated_at": "2025-11-05T15:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 45,
    "pages": 3
  }
}
```

#### POST /api/tasks/
**Description:** Create new task  
**Authorization:** Required (Manager, Team Lead, Admin, Super Admin)  
**Request Body:**
```json
{
  "title": "Implement login API",
  "description": "Create JWT-based authentication endpoint",
  "priority": "high",
  "status": "todo",
  "due_date": "2025-11-10T23:59:59Z",
  "assigned_to": 123,
  "project_id": 5,
  "sprint_id": 2,
  "blocks_task_id": null
}
```
**Response:** `201 Created`
```json
{
  "message": "Task created successfully",
  "task_id": 456
}
```
**Validation:**
- title: Required, 3-100 chars
- description: Max 500 chars
- priority: Enum (low, medium, high)
- status: Enum (todo, in_progress, completed)
- due_date: ISO 8601 format, future date or same-day (min 1h ahead)
- assigned_to: Must be project member
- project_id: Required, must exist

#### PUT /api/tasks/{id}
**Description:** Update existing task  
**Authorization:** Required (Assignee, Creator, Manager+)  
**Request Body:** (Partial update supported)
```json
{
  "status": "completed",
  "priority": "medium"
}
```
**Response:** `200 OK`
```json
{
  "message": "Task updated successfully"
}
```
**Business Rules:**
- Status → `completed`: All blocking tasks must be completed
- If task blocks others, cannot mark as completed until dependents are complete

**Error Codes:**
- `400`: Task blocked by incomplete task
- `403`: Unauthorized to update task
- `404`: Task not found

#### POST /api/tasks/bulk-update
**Description:** Bulk update multiple tasks  
**Authorization:** Required (Manager, Team Lead, Admin, Super Admin)  
**Request Body:**
```json
{
  "task_ids": [1, 2, 3, 4],
  "updates": {
    "status": "completed",
    "priority": "high"
  }
}
```
**Response:** `200 OK`
```json
{
  "message": "4 tasks updated successfully"
}
```
**Validation:**
- Same dependency checks as single update
- Atomic operation (all succeed or all fail)
- Maximum 100 tasks per bulk update

#### DELETE /api/tasks/{id}
**Description:** Delete task  
**Authorization:** Required (Admin, Super Admin, Task Creator)  
**Response:** `200 OK`
```json
{
  "message": "Task deleted successfully"
}
```
**Business Rules:**
- Cascade delete: comments, attachments, time logs
- Cannot delete if blocking other tasks (must resolve dependencies first)

### 5.5 File Management Endpoints

#### POST /api/tasks/{task_id}/attachments
**Description:** Upload file attachment  
**Authorization:** Required (Project members)  
**Content-Type:** `multipart/form-data`  
**Request:**
```
file: <binary data>
```
**Response:** `201 Created`
```json
{
  "message": "File uploaded successfully",
  "attachment": {
    "id": 789,
    "filename": "design_mockup.pdf",
    "file_size": 2457600,
    "uploaded_by": "John Doe",
    "uploaded_at": "2025-11-05T14:30:00Z"
  }
}
```
**Validation:**
- Max file size: 50 MB
- Allowed extensions: pdf, doc, docx, xls, xlsx, png, jpg, jpeg, gif, mp4, zip
- Filename sanitization

#### GET /api/tasks/attachments/{id}/download
**Description:** Download file attachment  
**Authorization:** Required (Project members)  
**Response:** `302 Redirect` (to signed URL for GCS) or `200 OK` (binary data for local)

### 5.6 Additional API Endpoints

For complete API documentation, see:
- **User Management:** `/api/users/*` (CRUD, role assignment)
- **Projects:** `/api/projects/*` (CRUD, member management)
- **Sprints:** `/api/sprints/*` (CRUD, sprint planning)
- **Chat:** `/api/chat/*` (messages, reactions, attachments)
- **Meetings:** `/api/meetings/*` (CRUD, calendar integration)
- **Reminders:** `/api/reminders/*` (CRUD, notifications)
- **Reports:** `/api/reports/*` (personal, admin, export)
- **Notifications:** `/api/notifications/*` (list, read, clear)
- **Settings:** `/api/settings/*` (system, personal)

---

## 6. Validation Rules & Business Logic

### 6.1 Input Validation Standards

#### String Fields
| Field | Min Length | Max Length | Pattern | Required |
|-------|-----------|-----------|---------|----------|
| Email | - | 255 | RFC 5322 | Yes |
| Password | 8 | 128 | 1 upper, 1 lower, 1 digit, 1 special | Yes |
| Name | 2 | 100 | Alphanumeric + spaces | Yes |
| Task Title | 3 | 100 | Any | Yes |
| Task Description | 0 | 500 | Any | No |
| Comment Content | 1 | 1000 | Any | Yes |
| Chat Message | 1 | 2000 | Any | Yes |

#### Date/Time Fields
- **Format:** ISO 8601 (`YYYY-MM-DDTHH:MM:SSZ`)
- **Timezone:** UTC for storage, local for display
- **Validation:**
  - Due dates: Future or same-day (min 1 hour ahead)
  - Meeting times: End after start, max 8-hour duration
  - Reminders: No past dates, max 1 year ahead

#### Numeric Fields
- **Task Priority:** Enum (low=1, medium=2, high=3)
- **Days Before Reminder:** Integer, 1-365 range
- **File Size:** Max 50 MB per file, 100 MB total per task
- **Pagination:** page ≥ 1, per_page ≤ 100

### 6.2 Business Rules

#### BR-001: Task Dependency Enforcement
- **Rule:** A task cannot be marked `completed` if it blocks an incomplete task
- **Enforcement:** Backend validation in both `PUT /api/tasks/{id}` and `POST /api/tasks/bulk-update`
- **Error Message:** "Cannot complete task: Task '{title}' is blocked by '{blocking_task_title}'. Complete it first."

#### BR-002: Project Visibility
- **Rule:** Non-admin users see only projects they are assigned to
- **Enforcement:** SQL query filter on project_members join
- **Exception:** Admin and Super Admin see all projects

#### BR-003: Email Verification
- **Rule:** Users cannot log in until email is verified AND admin approves
- **Enforcement:** User status must be `approved` for login
- **Flow:** pending → (verify email) → verified → (admin approval) → approved

#### BR-004: Password Reset Token Expiry
- **Rule:** Password reset tokens expire after 1 hour
- **Enforcement:** Token timestamp checked on `/api/auth/reset-password` endpoint
- **Security:** Token hashed in database, one-time use

#### BR-005: File Upload Security
- **Rule:** Only project members can upload/view task attachments
- **Enforcement:** Authorization check via project membership query
- **Sanitization:** Filename sanitized to prevent path traversal

#### BR-006: Profanity Filter
- **Rule:** Chat messages filtered for inappropriate content
- **Enforcement:** Word boundary detection (regex `\b{word}\b`) to prevent false positives
- **Action:** Message rejected with error if profanity detected

### 6.3 Validation Error Responses

All validation errors return `400 Bad Request` with structured error details:

```json
{
  "error": "Validation failed",
  "code": "VALIDATION_ERROR",
  "details": {
    "title": ["Title must be between 3 and 100 characters"],
    "due_date": ["Due date must be in the future"],
    "assigned_to": ["User is not a member of this project"]
  },
  "timestamp": "2025-11-05T12:00:00Z"
}
```

---

## 7. Security Requirements

### 7.1 Authentication & Authorization

#### Password Security
- **Hashing Algorithm:** bcrypt with cost factor 12
- **Strength Requirements:**
  - Minimum 8 characters
  - At least 1 uppercase letter
  - At least 1 lowercase letter
  - At least 1 digit
  - At least 1 special character (`!@#$%^&*()_+-=[]{}|;:,.<>?`)
- **Storage:** Never stored in plain text, only bcrypt hash

#### JWT Tokens
- **Access Token:**
  - Expiry: 1 hour
  - Payload: user_id, email, role
  - Algorithm: HS256
- **Refresh Token:**
  - Expiry: 7 days
  - Stored in secure HTTP-only cookie (production)
  - Used to obtain new access token
- **Secret Keys:** Environment variables, never committed to version control

#### Session Management
- **Failed Login Attempts:** Max 5 attempts
- **Lockout Duration:** 15 minutes
- **Lockout Reset:** Automatic after duration or admin override

### 7.2 Data Protection

#### HTML Injection Prevention
- **Risk:** User-supplied data in email templates
- **Mitigation:** HTML escaping via `html.escape()` in all email template methods
- **Scope:** Task titles, descriptions, comments, user names in email notifications

#### SQL Injection Prevention
- **Mitigation:** SQLAlchemy ORM with parameterized queries
- **Policy:** No raw SQL queries with user input

#### XSS Prevention
- **Frontend:** React escapes output by default
- **Backend:** HTML escaping in server-rendered content (emails)
- **CSP:** Content Security Policy headers in production

#### CSRF Prevention
- **Mechanism:** JWT in Authorization header (not cookies)
- **State-changing operations:** Require valid JWT

### 7.3 Rate Limiting

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/api/auth/login` | 5 requests | 15 minutes |
| `/api/auth/register` | 3 requests | 1 hour |
| `/api/auth/forgot-password` | 3 requests | 1 hour |
| All other endpoints | 100 requests | 1 minute |

### 7.4 File Upload Security

- **File Type Validation:** Whitelist of allowed extensions
- **File Size Limits:** 50 MB per file, 100 MB total
- **Filename Sanitization:** Remove special characters, prevent path traversal
- **Virus Scanning:** Recommended for production (not implemented in MVP)
- **Access Control:** Only project members can access task attachments

### 7.5 Secrets Management

- **Development:** `.env` file (git-ignored)
- **Production:** Google Cloud Secret Manager
- **Secrets:**
  - Database credentials
  - JWT secret keys
  - Email SMTP credentials
  - Cloud Storage service account keys

---

## 8. Architecture & Technology Stack

### 8.1 System Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                          │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │  Browser   │  │   Mobile   │  │  Desktop   │            │
│  │  (React)   │  │   (PWA)    │  │   (Elect.) │            │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘            │
└────────┼────────────────┼────────────────┼───────────────────┘
         │                │                │
         └────────────────┴────────────────┘
                         │ HTTPS
         ┌───────────────▼───────────────┐
         │      LOAD BALANCER (GCP)      │
         │     Cloud Load Balancing      │
         └───────────────┬───────────────┘
                         │
         ┌───────────────▼───────────────────────────┐
         │          APPLICATION LAYER                 │
         │  ┌─────────────────────────────────────┐  │
         │  │  Flask API (Cloud Run)              │  │
         │  │  - Auth, Users, Tasks, Projects     │  │
         │  │  - Chat, Meetings, Reports          │  │
         │  │  - Notifications, File Uploads      │  │
         │  └────┬──────────────────────┬─────────┘  │
         └───────┼──────────────────────┼────────────┘
                 │                      │
     ┌───────────▼────────┐   ┌────────▼──────────┐
     │  DATABASE LAYER    │   │  STORAGE LAYER    │
     │  Cloud SQL         │   │  Cloud Storage    │
     │  (SQL Server)      │   │  (Files, Backups) │
     └────────────────────┘   └───────────────────┘
```

### 8.2 Technology Stack Details

#### Frontend Stack
```
React 18.2.0
├── react-router-dom 6.x      # Client-side routing
├── axios 1.x                  # HTTP client
├── moment 2.x                 # Date/time manipulation
├── react-big-calendar 1.x     # Calendar component
├── react-icons 4.x            # Icon library
└── vite 4.x                   # Build tool & dev server
```

#### Backend Stack
```
Python 3.11
├── Flask 3.0.0                # Web framework
├── Flask-SQLAlchemy 3.x       # ORM
├── Flask-JWT-Extended 4.x     # JWT authentication
├── Flask-CORS 4.x             # CORS handling
├── Flask-Mail 0.9.x           # Email notifications
├── bcrypt 4.x                 # Password hashing
├── pymssql 2.x                # SQL Server driver
├── gunicorn 21.x              # Production WSGI server
└── google-cloud-storage 2.x   # Cloud file storage
```

#### Database
- **Engine:** Microsoft SQL Server 2022
- **Driver:** pymssql (FreeTDS)
- **ORM:** SQLAlchemy 2.x
- **Migrations:** Manual SQL scripts + Python migration tools

#### Infrastructure
- **Containerization:** Docker 24.x, Docker Compose 2.x
- **Cloud Platform:** Google Cloud Platform (GCP)
  - Cloud Run (serverless containers)
  - Cloud SQL (managed SQL Server)
  - Cloud Storage (object storage)
  - Secret Manager (secrets)
  - Artifact Registry (container images)
  - Cloud Build (CI/CD)
- **CI/CD:** GitHub Actions + Google Cloud Build
- **Monitoring:** Google Cloud Logging, Cloud Monitoring

### 8.3 Design Patterns

#### Backend Patterns
- **Blueprint Pattern:** Modular route organization (auth, users, tasks, etc.)
- **Repository Pattern:** Data access abstraction via SQLAlchemy models
- **Decorator Pattern:** Authorization via `@jwt_required`, `@admin_required`
- **Factory Pattern:** Database connection and app initialization
- **Service Layer:** Business logic separation (email_service, storage_service)

#### Frontend Patterns
- **Component Composition:** Reusable UI components
- **Custom Hooks:** useAuth, useModal, useToast, useFormValidation
- **Context API:** Global state (AuthContext, ToastContext)
- **Higher-Order Components:** Layout wrapper for authenticated routes

---

## 9. Database Schema

### 9.1 Entity Relationship Diagram (ERD)

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│    Users    │───┬───│    Tasks    │───────│   Projects  │
│             │   │   │             │       │             │
│ id (PK)     │   │   │ id (PK)     │       │ id (PK)     │
│ email       │   │   │ title       │       │ name        │
│ password    │   │   │ description │       │ description │
│ name        │   │   │ priority    │       │ owner_id    │
│ role        │   │   │ status      │       │ start_date  │
│ status      │   │   │ due_date    │       │ end_date    │
│ ...         │   │   │ assigned_to ├───┐   │ created_at  │
└─────────────┘   │   │ project_id  ├───┤   └─────────────┘
                  │   │ sprint_id   │   │
                  │   │ created_by  ├───┘
                  │   │ blocks_task │
                  │   └─────────────┘
                  │
                  ├───┌─────────────┐
                  │   │   Comments  │
                  │   │             │
                  │   │ id (PK)     │
                  │   │ task_id     │
                  │   │ user_id     │
                  │   │ content     │
                  │   │ created_at  │
                  │   └─────────────┘
                  │
                  └───┌──────────────┐
                      │Notifications │
                      │              │
                      │ id (PK)      │
                      │ user_id      │
                      │ title        │
                      │ message      │
                      │ type         │
                      │ is_read      │
                      │ related_task │
                      └──────────────┘
```

### 9.2 Core Tables

#### Users
```sql
CREATE TABLE users (
    id INT IDENTITY(1,1) PRIMARY KEY,
    email NVARCHAR(255) NOT NULL UNIQUE,
    password_hash NVARCHAR(255) NOT NULL,
    name NVARCHAR(100) NOT NULL,
    role NVARCHAR(50) NOT NULL DEFAULT 'viewer',
    status NVARCHAR(50) NOT NULL DEFAULT 'pending',
    theme NVARCHAR(20) DEFAULT 'light',
    language NVARCHAR(10) DEFAULT 'en',
    notifications_enabled BIT DEFAULT 1,
    reset_token NVARCHAR(255),
    reset_token_expires DATETIME2,
    force_password_change BIT DEFAULT 0,
    verification_code NVARCHAR(10),
    verification_code_expires DATETIME2,
    failed_login_attempts INT DEFAULT 0,
    locked_until DATETIME2,
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    INDEX idx_email (email),
    INDEX idx_role (role),
    INDEX idx_status (status)
);
```

#### Tasks
```sql
CREATE TABLE tasks (
    id INT IDENTITY(1,1) PRIMARY KEY,
    title NVARCHAR(100) NOT NULL,
    description NVARCHAR(500),
    priority NVARCHAR(20) DEFAULT 'medium',
    status NVARCHAR(20) DEFAULT 'todo',
    due_date DATETIME2,
    assigned_to INT,
    project_id INT NOT NULL,
    sprint_id INT,
    created_by INT NOT NULL,
    blocks_task_id INT,
    completed_at DATETIME2,
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    updated_at DATETIME2 DEFAULT GETUTCDATE(),
    FOREIGN KEY (assigned_to) REFERENCES users(id),
    FOREIGN KEY (created_by) REFERENCES users(id),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (sprint_id) REFERENCES sprints(id),
    FOREIGN KEY (blocks_task_id) REFERENCES tasks(id),
    INDEX idx_status (status),
    INDEX idx_priority (priority),
    INDEX idx_assigned_to (assigned_to),
    INDEX idx_project_id (project_id),
    INDEX idx_due_date (due_date)
);
```

#### Projects
```sql
CREATE TABLE projects (
    id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(100) NOT NULL,
    description NVARCHAR(500),
    owner_id INT NOT NULL,
    start_date DATETIME2,
    end_date DATETIME2,
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    updated_at DATETIME2 DEFAULT GETUTCDATE(),
    FOREIGN KEY (owner_id) REFERENCES users(id),
    INDEX idx_owner_id (owner_id)
);
```

#### ChatMessages
```sql
CREATE TABLE chat_messages (
    id INT IDENTITY(1,1) PRIMARY KEY,
    sender_id INT NOT NULL,
    recipient_id INT NOT NULL,
    content NVARCHAR(MAX) NOT NULL,  -- Unicode support for emojis
    is_read BIT DEFAULT 0,
    is_edited BIT DEFAULT 0,
    is_deleted BIT DEFAULT 0,
    deleted_for_sender BIT DEFAULT 0,
    deleted_for_recipient BIT DEFAULT 0,
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    updated_at DATETIME2 DEFAULT GETUTCDATE(),
    FOREIGN KEY (sender_id) REFERENCES users(id),
    FOREIGN KEY (recipient_id) REFERENCES users(id),
    INDEX idx_sender_recipient (sender_id, recipient_id),
    INDEX idx_created_at (created_at)
);
```

#### FileAttachments
```sql
CREATE TABLE file_attachments (
    id INT IDENTITY(1,1) PRIMARY KEY,
    task_id INT NOT NULL,
    filename NVARCHAR(255) NOT NULL,
    original_filename NVARCHAR(255) NOT NULL,
    file_path NVARCHAR(500) NOT NULL,  -- Local path or GCS URI
    file_size BIGINT NOT NULL,
    mime_type NVARCHAR(100),
    uploaded_by INT NOT NULL,
    uploaded_at DATETIME2 DEFAULT GETUTCDATE(),
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (uploaded_by) REFERENCES users(id),
    INDEX idx_task_id (task_id)
);
```

### 9.3 Additional Tables

- **Sprints:** Sprint management (id, name, project_id, start_date, end_date, status)
- **Comments:** Task comments (id, task_id, user_id, content, created_at)
- **Notifications:** User notifications (id, user_id, title, message, type, is_read)
- **NotificationPreferences:** User notification settings (user_id, type, email_enabled, app_enabled)
- **SystemSettings:** Global config (id, site_title, default_role, email_enabled)
- **ProjectMembers:** Many-to-many user-project relationship (project_id, user_id)
- **Meetings:** Calendar events (id, user_id, title, start_time, end_time)
- **Reminders:** User reminders (id, user_id, title, description, reminder_date, days_before)
- **MessageReactions:** Chat emoji reactions (id, message_id, user_id, emoji)

---

## 10. Deployment & Installation

### 10.1 Quick Start (Docker - Development)

#### Prerequisites
- Docker 24+ and Docker Compose 2+
- Git

#### Steps
```bash
# 1. Clone repository
git clone https://github.com/Omars64/Task_Management_System.git
cd Task_Management_System

# 2. Create environment file
cp .env.example .env
# Edit .env with your configuration (database password, email, etc.)

# 3. Start all services
docker-compose up -d

# 4. Wait for services to be healthy
docker-compose ps

# 5. Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:5000/api
# Database: localhost:1433

# 6. Login with default credentials
# Super Admin: admin@workhub.com / admin123
```

### 10.2 Production Deployment (Google Cloud Platform)

#### Prerequisites
- GCP Project ID: `genai-workhub`
- gcloud CLI installed and authenticated
- GitHub repository configured

#### Automated Setup
```bash
# 1. Run GCP resource setup script
chmod +x scripts/setup-gcp.sh
./scripts/setup-gcp.sh

# 2. Configure GitHub Secrets (see GITHUB_SECRETS_SETUP.md)
# Required secrets:
# - GCP_PROJECT_ID
# - GCP_SERVICE_ACCOUNT_KEY
# - CLOUD_SQL_CONNECTION_NAME
# - DB_PASSWORD
# - JWT_SECRET_KEY
# - MAIL_USERNAME
# - MAIL_PASSWORD

# 3. Push to main branch to trigger deployment
git push origin main

# 4. Monitor deployment in GitHub Actions
# URL: https://github.com/Omars64/Task_Management_System/actions
```

#### Manual Deployment
```bash
# 1. Build and push Docker images
./scripts/deploy-gcp.sh

# 2. Deploy to Cloud Run
gcloud run deploy workhub-backend \
  --image gcr.io/genai-workhub/workhub-backend \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated

gcloud run deploy workhub-frontend \
  --image gcr.io/genai-workhub/workhub-frontend \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated

# 3. Get service URLs
gcloud run services list --region us-central1
```

### 10.3 Environment Variables

#### Backend (.env)
```bash
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=<random-64-char-string>
JWT_SECRET_KEY=<random-64-char-string>

# Database Configuration
DB_HOST=localhost                          # Dev: localhost, Prod: /cloudsql/...
DB_PORT=1433
DB_NAME=workhub
DB_USER=sa
DB_PASSWORD=<strong-password>
CLOUD_SQL_CONNECTION_NAME=genai-workhub:us-central1:workhub-db  # GCP only

# Email Configuration (Gmail example)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=<app-specific-password>
MAIL_DEFAULT_SENDER=noreply@workhub.com

# Storage Configuration
USE_CLOUD_STORAGE=false                    # Dev: false, Prod: true
CLOUD_STORAGE_BUCKET=workhub-uploads       # GCP only

# CORS Configuration
ALLOWED_ORIGINS=http://localhost:3000,https://workhub.example.com

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=100
```

#### Frontend (.env)
```bash
VITE_API_URL=http://localhost:5000  # Dev: localhost, Prod: Cloud Run URL
```

### 10.4 Database Migration

#### Initial Setup
```bash
# Development (Docker)
docker-compose exec backend python init_db.py

# Production (Cloud SQL)
gcloud sql connect workhub-db --user=sqlserver
# Run migration SQL scripts in migrations/ folder
```

#### Backup & Restore
```bash
# Backup (Windows PowerShell)
.\scripts\backup-db.ps1

# Restore (Windows PowerShell)
.\scripts\restore-db.ps1 -BackupFile "backup_20251105_120000.bak"

# Backup (Linux/Mac)
./scripts/backup-db.sh

# Restore (Linux/Mac)
./scripts/restore-db.sh backup_20251105_120000.bak
```

### 10.5 Health Checks

#### Backend Health Check
```bash
curl http://localhost:5000/api/health
# Response: {"status": "healthy", "database": "connected"}
```

#### Frontend Health Check
```bash
curl http://localhost:3000
# Response: 200 OK (HTML content)
```

#### Database Health Check
```bash
# Docker
docker-compose exec backend python -c "from app import db; print(db.engine.execute('SELECT 1').scalar())"

# SQL Server Management Studio
SELECT 1  -- Should return 1 if connected
```

---

## 11. Testing & Quality Assurance

### 11.1 Test Credentials

| Role | Email | Password | Access Level |
|------|-------|----------|--------------|
| Super Admin | admin@workhub.com | admin123 | Full system access |
| Admin | admin2@workhub.com | admin123 | User & project management |
| Manager | manager@workhub.com | manager123 | Project & task creation |
| Team Lead | teamlead@workhub.com | lead123 | Sprint & task management |
| Developer | dev@workhub.com | dev123 | Task updates only |
| Viewer | viewer@workhub.com | viewer123 | Read-only access |

### 11.2 Test Scenarios

#### Authentication Flow
1. Register new user → Receive verification email → Enter 6-digit code
2. Admin approves user → User can log in
3. Failed login attempts (5 times) → Account locked for 15 minutes
4. Password reset → Receive email → Reset token valid for 1 hour

#### Task Management Flow
1. Manager creates task → Assigns to Developer → Developer receives notification
2. Developer updates status to `in_progress` → Task creator notified
3. Developer marks task as `completed` → Dependent tasks unblocked
4. Admin bulk updates 10 tasks to `completed` → All dependencies validated

#### Project Visibility
1. Developer logs in → Sees only assigned projects
2. Admin logs in → Sees all projects → Can edit any project
3. Manager creates new project → Assigns team members → Members see project

#### File Upload
1. User uploads 45 MB PDF → Success
2. User uploads 60 MB video → Error (exceeds limit)
3. User uploads `.exe` file → Error (invalid file type)
4. Non-project-member tries to access attachment → Error (403 Forbidden)

### 11.3 API Testing (curl examples)

```bash
# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@workhub.com","password":"admin123"}'

# Create Task (with JWT token)
curl -X POST http://localhost:5000/api/tasks/ \
  -H "Authorization: Bearer <your-jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title":"New API Task",
    "description":"Created via API",
    "priority":"high",
    "status":"todo",
    "project_id":1,
    "assigned_to":2
  }'

# Get User Tasks
curl -X GET "http://localhost:5000/api/tasks/?assigned_to=2&status=in_progress" \
  -H "Authorization: Bearer <your-jwt-token>"

# Upload File
curl -X POST http://localhost:5000/api/tasks/1/attachments \
  -H "Authorization: Bearer <your-jwt-token>" \
  -F "file=@/path/to/document.pdf"
```

### 11.4 Performance Testing

#### Load Testing (Recommended Tools)
- **Apache JMeter:** Simulate 100-500 concurrent users
- **Locust:** Python-based load testing
- **Artillery:** Node.js load testing

#### Performance Benchmarks
- API response time (p95): < 200ms
- Page load time: < 2 seconds
- Database query time: < 50ms (with indexes)
- File upload time: < 5 seconds for 10 MB file

---

## 12. Documentation & Support

### 12.1 Additional Documentation

- **API Documentation:** See `/api/docs` endpoint (Swagger UI - future)
- **Deployment Guide:** `DEPLOYMENT_GCP.md`
- **CI/CD Setup:** `CI_CD_README.md`
- **GitHub Secrets:** `GITHUB_SECRETS_SETUP.md`
- **Quick Start:** `QUICK_START.md`
- **Docker Guide:** `README_DOCKER.md`
- **User Roles:** `USER_ROLES_AND_PERMISSIONS.md`
- **Security Guide:** `workhub-backend/SECURITY_VALIDATION_GUIDE.md`

### 12.2 Troubleshooting

#### Database Connection Issues
```bash
# Check SQL Server is running
docker-compose ps

# Test connection from backend
docker-compose exec backend python -c "from app import app, db; app.app_context().push(); print(db.engine.execute('SELECT @@VERSION').scalar())"

# Check logs
docker-compose logs db
```

#### Frontend Not Loading
```bash
# Check if backend is accessible
curl http://localhost:5000/api/health

# Check CORS configuration
# Backend: ALLOWED_ORIGINS in .env
# Frontend: VITE_API_URL in .env

# Clear browser cache
# Chrome: Ctrl+Shift+R
```

#### Email Not Sending
```bash
# Check email configuration in .env
# For Gmail: Use App-Specific Password (not regular password)
# Enable "Less secure app access" or use OAuth2

# Test email configuration
docker-compose exec backend python -c "
from flask_mail import Mail, Message
from app import app, mail
with app.app_context():
    msg = Message('Test', sender=app.config['MAIL_DEFAULT_SENDER'], recipients=['test@example.com'])
    msg.body = 'Test email'
    mail.send(msg)
"
```

### 12.3 Support Channels

- **GitHub Issues:** https://github.com/Omars64/Task_Management_System/issues
- **Documentation:** https://github.com/Omars64/Task_Management_System/tree/main/docs
- **Email:** support@workhub.com (if configured)

---

## 13. License & Legal

### 13.1 License
This project is released under the MIT License. See `LICENSE` file for details.

### 13.2 Third-Party Dependencies
All third-party libraries are used under their respective licenses:
- React: MIT License
- Flask: BSD-3-Clause License
- SQLAlchemy: MIT License
- See `package.json` and `requirements.txt` for full list

### 13.3 Data Privacy
- All user passwords are hashed using bcrypt (irreversible)
- Email verification codes are time-limited and single-use
- JWT tokens expire after 1 hour
- File uploads are scoped to project members only
- GDPR compliance: Users can request data export/deletion (admin feature)

---

## 14. Changelog

### Version 2.0 (November 2025)
- ✅ Added 6-tier RBAC (Super Admin, Admin, Manager, Team Lead, Developer, Viewer)
- ✅ Implemented project & sprint management
- ✅ Added real-time chat with file attachments and emoji reactions
- ✅ Calendar integration with meetings & reminders
- ✅ Advanced form validation with real-time feedback
- ✅ Email verification with 6-digit code
- ✅ Admin approval workflow for new users
- ✅ Task dependencies with blocking relationships
- ✅ Bulk task operations with dependency validation
- ✅ File upload system with cloud storage support
- ✅ HTML injection prevention in email templates
- ✅ GCP deployment with CI/CD pipeline
- ✅ Docker containerization for development & production

### Version 1.0 (October 2025)
- ✅ Initial release with basic task management
- ✅ User authentication with JWT
- ✅ Admin and User roles
- ✅ Task CRUD operations
- ✅ Basic reporting
- ✅ Email notifications

---

## 15. Roadmap (Future Enhancements)

### Phase 1 (Q1 2026)
- [ ] Swagger/OpenAPI documentation
- [ ] Automated API testing (Postman/Newman)
- [ ] Mobile apps (React Native)
- [ ] Push notifications (Firebase Cloud Messaging)

### Phase 2 (Q2 2026)
- [ ] Advanced analytics dashboard with charts
- [ ] Time tracking with timesheets
- [ ] Invoice generation for projects
- [ ] Gantt chart view for project timelines

### Phase 3 (Q3 2026)
- [ ] Third-party integrations (Slack, Jira, GitHub)
- [ ] Webhook support for external systems
- [ ] Custom workflows and automation rules
- [ ] White-label branding for enterprises

### Phase 4 (Q4 2026)
- [ ] AI-powered task prioritization
- [ ] Natural language task creation
- [ ] Predictive analytics for project completion
- [ ] Sentiment analysis for team communication

---

## 16. Contributing

### 16.1 Development Setup
```bash
# Fork the repository
git clone https://github.com/YOUR_USERNAME/Task_Management_System.git
cd Task_Management_System

# Create a feature branch
git checkout -b feature/your-feature-name

# Make changes, commit, and push
git add .
git commit -m "feat: Add your feature description"
git push origin feature/your-feature-name

# Create a Pull Request on GitHub
```

### 16.2 Code Standards
- **Python:** Follow PEP 8 style guide
- **JavaScript:** Follow Airbnb style guide
- **Commits:** Use conventional commits (feat, fix, docs, refactor, test, chore)
- **Testing:** Write unit tests for new features
- **Documentation:** Update README and API docs for new endpoints

---

## 17. Contact & Acknowledgments

### 17.1 Project Team
- **Lead Developer:** Omar
- **Repository:** https://github.com/Omars64/Task_Management_System
- **Project ID:** genai-workhub (GCP)

### 17.2 Acknowledgments
- React Team for the excellent frontend framework
- Flask Team for the lightweight Python web framework
- Google Cloud Platform for reliable infrastructure
- All open-source contributors whose libraries power this project

---

**Document Version:** 2.0  
**Last Updated:** November 5, 2025  
**Next Review:** December 2025

---

Built with ❤️ using React, Flask, and SQL Server
