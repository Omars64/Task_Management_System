# Work Hub - Project Structure

## Overview

```
workspace/
├── workhub-backend/          # Flask Backend Application
├── workhub-frontend/         # React Frontend Application
├── docker-compose.yml        # Docker orchestration
├── setup.sh                  # Quick Docker setup script
├── setup-manual.sh           # Manual installation script
├── README.md                 # Main documentation
├── DEPLOYMENT.md             # Deployment guide
└── PROJECT_STRUCTURE.md      # This file
```

## Backend Structure (workhub-backend/)

```
workhub-backend/
├── app.py                    # Main Flask application & entry point
├── config.py                 # Application configuration
├── models.py                 # SQLAlchemy database models
├── init_db.py                # Database initialization script
│
├── Routes/Blueprints:
├── auth.py                   # Authentication endpoints (login, register, password)
├── users.py                  # User management (CRUD operations)
├── tasks.py                  # Task management (CRUD, comments)
├── notifications.py          # Notification management
├── reports.py                # Report generation & CSV export
├── settings.py               # System & personal settings
│
├── Configuration:
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variables template
├── .env                      # Actual environment variables (gitignored)
├── .gitignore                # Git ignore rules
└── Dockerfile                # Docker container configuration
```

### Backend Key Files

#### app.py
- Creates Flask application
- Initializes extensions (SQLAlchemy, JWT, CORS, Bcrypt)
- Registers all blueprints
- Defines error handlers
- Health check endpoint

#### models.py
Database models:
- **User**: User accounts with authentication
- **Task**: Task management with assignments
- **Notification**: User notifications
- **TimeLog**: Task time tracking
- **Comment**: Task comments
- **SystemSettings**: Application settings

#### Routes Breakdown

**auth.py** (`/api/auth/`)
- POST `/login` - User authentication
- POST `/register` - User registration
- GET `/me` - Current user info
- POST `/reset-password` - Password reset request
- POST `/change-password` - Change password

**users.py** (`/api/users/`)
- GET `/` - List all users (Admin)
- GET `/{id}` - Get user by ID
- POST `/` - Create user (Admin)
- PUT `/{id}` - Update user
- DELETE `/{id}` - Delete user (Admin)

**tasks.py** (`/api/tasks/`)
- GET `/` - List tasks (with filters)
- GET `/{id}` - Get task details
- POST `/` - Create task (Admin)
- PUT `/{id}` - Update task
- DELETE `/{id}` - Delete task (Admin)
- POST `/{id}/comments` - Add comment

**notifications.py** (`/api/notifications/`)
- GET `/` - List notifications
- GET `/unread-count` - Get unread count
- PUT `/{id}/read` - Mark as read
- PUT `/mark-all-read` - Mark all as read
- DELETE `/{id}` - Delete notification
- DELETE `/clear-all` - Clear all notifications

**reports.py** (`/api/reports/`)
- GET `/personal/task-status` - Personal task stats
- GET `/personal/time-logs` - Personal time logs
- GET `/personal/activity` - Personal activity
- GET `/admin/overview` - Admin overview
- GET `/admin/sprint-summary` - Sprint summary
- POST `/export/csv` - Export to CSV

**settings.py** (`/api/settings/`)
- GET `/system` - Get system settings
- PUT `/system` - Update system settings (Admin)
- GET `/personal` - Get personal settings
- PUT `/personal` - Update personal settings

## Frontend Structure (workhub-frontend/)

```
workhub-frontend/
├── public/                   # Static assets
├── src/
│   ├── components/           # Reusable React components
│   │   ├── Layout.jsx        # Main layout with sidebar
│   │   └── Layout.css        # Layout styles
│   │
│   ├── pages/                # Page components
│   │   ├── Login.jsx         # Login page
│   │   ├── Login.css
│   │   ├── Dashboard.jsx     # Dashboard with stats
│   │   ├── Dashboard.css
│   │   ├── Tasks.jsx         # Task management
│   │   ├── Tasks.css
│   │   ├── Users.jsx         # User management (Admin)
│   │   ├── Notifications.jsx # Notifications center
│   │   ├── Reports.jsx       # Reports & analytics
│   │   └── Settings.jsx      # Settings management
│   │
│   ├── services/             # API services
│   │   └── api.js            # Axios configuration & API calls
│   │
│   ├── context/              # React Context
│   │   └── AuthContext.jsx  # Authentication context & state
│   │
│   ├── App.jsx               # Main app component & routing
│   ├── main.jsx              # Entry point
│   └── index.css             # Global styles
│
├── Configuration:
├── index.html                # HTML template
├── package.json              # Node dependencies
├── vite.config.js            # Vite configuration
├── .gitignore                # Git ignore rules
└── Dockerfile                # Docker container configuration
```

### Frontend Key Files

#### App.jsx
- Main application component
- Route configuration
- Private route protection
- Role-based access control

#### AuthContext.jsx
- User authentication state
- Login/logout functions
- User data management
- Role checking utilities

#### api.js
Service functions for:
- Authentication (authAPI)
- Users (usersAPI)
- Tasks (tasksAPI)
- Notifications (notificationsAPI)
- Reports (reportsAPI)
- Settings (settingsAPI)

#### Page Components

**Login.jsx**
- User authentication form
- Demo credentials display
- Error handling

**Dashboard.jsx**
- Statistics overview
- Recent tasks display
- Role-based content

**Tasks.jsx**
- Task list with filters
- Create/edit task modal
- Task detail view
- Status updates
- Comments display

**Users.jsx** (Admin only)
- User list table
- Create/edit user modal
- User deletion
- Role management

**Notifications.jsx**
- Notification list
- Mark as read functionality
- Notification deletion
- Clear all option

**Reports.jsx**
- Multiple report tabs
- Task statistics
- Activity tracking
- CSV export

**Settings.jsx**
- Personal settings (theme, language, notifications)
- System settings (Admin only)
- Tab-based interface

## Database Schema

### Tables

**users**
```sql
id (PK)
email (UNIQUE)
password_hash
name
role (admin/user)
theme
language
notifications_enabled
created_at
```

**tasks**
```sql
id (PK)
title
description
priority (low/medium/high)
status (todo/in_progress/completed)
due_date
created_at
updated_at
completed_at
assigned_to (FK -> users.id)
created_by (FK -> users.id)
```

**notifications**
```sql
id (PK)
user_id (FK -> users.id)
title
message
type
is_read
created_at
related_task_id (FK -> tasks.id)
```

**time_logs**
```sql
id (PK)
task_id (FK -> tasks.id)
user_id (FK -> users.id)
hours
description
logged_at
```

**comments**
```sql
id (PK)
task_id (FK -> tasks.id)
user_id (FK -> users.id)
content
created_at
```

**system_settings**
```sql
id (PK)
site_title
default_role
email_notifications_enabled
default_language
```

## Docker Configuration

### docker-compose.yml
Services:
- **mysql**: MySQL 8.0 database
- **backend**: Flask API server
- **frontend**: React development server

### Dockerfiles

**Backend Dockerfile**
- Python 3.11 slim base
- Install system dependencies
- Install Python packages
- Run Flask application

**Frontend Dockerfile**
- Node 18 alpine base
- Install dependencies
- Run Vite dev server

## API Flow

### Authentication Flow
```
1. User enters credentials → Login.jsx
2. POST /api/auth/login → auth.py
3. Validate credentials → models.User
4. Generate JWT token → Flask-JWT-Extended
5. Return token + user data
6. Store token in localStorage → AuthContext
7. Redirect to dashboard
```

### Task Management Flow
```
1. Admin creates task → Tasks.jsx
2. POST /api/tasks/ → tasks.py
3. Validate & save task → models.Task
4. Create notification → models.Notification
5. Return created task
6. Update task list → Tasks.jsx
7. User sees notification → Notifications.jsx
```

### Report Generation Flow
```
1. User requests report → Reports.jsx
2. GET /api/reports/personal/task-status → reports.py
3. Query database → SQLAlchemy
4. Calculate statistics
5. Return report data
6. Display charts/stats → Reports.jsx
7. Optional: Export CSV → pandas
```

## State Management

### Frontend State
- **AuthContext**: User authentication state
- **Local State**: Component-specific state (useState)
- **API Calls**: Direct API calls with Axios
- **localStorage**: JWT token persistence

### Backend State
- **Database**: Persistent data (MySQL)
- **Session**: JWT-based stateless authentication
- **No server-side sessions**: Fully stateless API

## Security Implementation

### Authentication
- Password hashing: bcrypt
- Token-based auth: JWT
- Token expiry: 24 hours
- Protected routes: @jwt_required()

### Authorization
- Role-based access: admin_required()
- Route-level protection
- Frontend route guards

### Data Protection
- SQL injection: SQLAlchemy ORM
- XSS: React auto-escaping
- CORS: Flask-CORS configuration
- Input validation: Server-side validation

## Key Technologies

### Backend Stack
- **Framework**: Flask 3.0
- **Database**: MySQL 8.0
- **ORM**: SQLAlchemy
- **Authentication**: Flask-JWT-Extended
- **Password Hashing**: Flask-Bcrypt
- **CORS**: Flask-CORS
- **Data Export**: Pandas
- **Email**: Flask-Mail

### Frontend Stack
- **Framework**: React 18
- **Build Tool**: Vite
- **Routing**: React Router v6
- **HTTP Client**: Axios
- **Icons**: React Icons
- **Date Handling**: date-fns
- **Styling**: CSS3 (Custom)

### Development Tools
- **Containerization**: Docker & Docker Compose
- **Version Control**: Git
- **API Testing**: Built-in health checks

## Development Workflow

### Adding a New Feature

1. **Backend**
   ```python
   # 1. Update models.py if needed
   # 2. Create/update route in appropriate blueprint
   # 3. Add validation and error handling
   # 4. Test with curl or Postman
   ```

2. **Frontend**
   ```javascript
   // 1. Add API function in api.js
   // 2. Create/update component
   // 3. Add routing if needed
   // 4. Test in browser
   ```

3. **Database**
   ```python
   # 1. Update models.py
   # 2. Drop and recreate tables (dev)
   # 3. Or create migration script (prod)
   ```

### Code Organization Principles

- **Separation of Concerns**: Models, routes, and business logic separated
- **DRY**: Reusable components and functions
- **RESTful API**: Standard HTTP methods and status codes
- **Component-Based**: React components for UI
- **Modular**: Blueprints for backend, components for frontend

## Performance Considerations

### Backend
- Database indexing on foreign keys
- Efficient queries with SQLAlchemy
- Connection pooling
- Pagination for large datasets (can be added)

### Frontend
- Code splitting (React.lazy can be added)
- Lazy loading for large lists
- Optimized re-renders
- Efficient state management

## Testing Strategy

### Backend Testing
```python
# Unit tests for models
# Integration tests for routes
# Test authentication & authorization
# Test database operations
```

### Frontend Testing
```javascript
// Component tests
// Integration tests
// E2E tests (Cypress/Playwright)
// Accessibility tests
```

## Monitoring & Logging

### Application Logs
- Flask logging
- Console logs in development
- File logs in production

### Error Handling
- Try-catch blocks
- HTTP error responses
- User-friendly error messages
- Database rollback on errors

## Future Enhancements

### Backend
- [ ] Database migrations (Alembic)
- [ ] Caching (Redis)
- [ ] Background tasks (Celery)
- [ ] Rate limiting
- [ ] API versioning
- [ ] WebSocket support

### Frontend
- [ ] Progressive Web App (PWA)
- [ ] Offline support
- [ ] Dark mode implementation
- [ ] Internationalization (i18n)
- [ ] Advanced filtering
- [ ] Drag-and-drop task management

### Features
- [ ] File attachments
- [ ] Subtasks
- [ ] Project grouping
- [ ] Team collaboration
- [ ] Calendar view
- [ ] Gantt charts
- [ ] Time tracking automation
- [ ] Mobile apps

---

This structure provides a solid foundation for a production-ready task management system with room for future enhancements.