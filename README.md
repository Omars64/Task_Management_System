# Work Hub - Task Management System

A production-ready, full-stack task management system built with React and Flask. Work Hub provides comprehensive task management features with role-based access control, real-time notifications, and advanced reporting capabilities.

## 🚀 Features

### Core Functionality
- **User Management**: Admin and user roles with different permissions
- **Task Management**: Create, assign, update, and track tasks
- **Time Logging**: Track time spent on tasks with detailed descriptions
- **Comments System**: Collaborate on tasks with threaded comments
- **Notifications**: Real-time notifications for task updates and assignments
- **Reports**: Comprehensive reporting with CSV export
- **Settings**: Personal and system-wide configuration

### Advanced Features
- **Dark/Light Theme**: User preference-based theme switching
- **Email Notifications**: SMTP integration for email alerts
- **Password Reset**: Secure password reset via email
- **Error Handling**: Comprehensive error handling with user-friendly notifications
- **Logging**: Detailed logging for security, access, and errors
- **Production Ready**: Docker containerization with production configurations

## 🛠️ Tech Stack

### Frontend
- **React 18** - Modern UI framework
- **Vite** - Fast build tool and dev server
- **React Router** - Client-side routing
- **Axios** - HTTP client
- **React Icons** - Icon library
- **CSS Variables** - Theme system

### Backend
- **Flask** - Python web framework
- **SQLAlchemy** - ORM for database operations
- **JWT** - Authentication and authorization
- **Flask-Mail** - Email functionality
- **Bcrypt** - Password hashing
- **MySQL** - Database

### Infrastructure
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration
- **Nginx** - Reverse proxy and static file serving
- **MySQL 8.0** - Database server

## 📋 Requirements

### Functional Requirements
- **FR-1**: Email and password authentication
- **FR-2**: Password reset functionality
- **FR-3**: Role-based access control
- **FR-4**: Task creation and assignment (Admin)
- **FR-5**: Task viewing and status updates (Users)
- **FR-6**: Task filtering and search
- **FR-7**: Real-time notifications
- **FR-8**: Personal and system-wide reports
- **FR-9**: CSV export functionality
- **FR-10**: System and personal settings

### Non-Functional Requirements
- **NFR-1**: Support for 500+ concurrent users
- **NFR-2**: Secure password storage (bcrypt)
- **NFR-3**: 99% uptime availability
- **NFR-4**: Responsive design across devices
- **NFR-5**: Scalable database design

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Git

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd workhub
   ```

2. **Start the development environment**
   ```bash
   docker-compose up --build
   ```

3. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:5000/api
   - Health Check: http://localhost:5000/api/health

4. **Default Credentials**
   - Admin: admin@workhub.com / admin123
   - User: john@workhub.com / user123
   - User: jane@workhub.com / user123

### Production Deployment

See [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md) for detailed production deployment instructions.

## 📁 Project Structure

```
workhub/
├── workhub-backend/          # Flask backend
│   ├── app.py               # Main application
│   ├── models.py            # Database models
│   ├── auth.py              # Authentication routes
│   ├── tasks.py             # Task management routes
│   ├── users.py             # User management routes
│   ├── notifications.py     # Notification routes
│   ├── reports.py           # Reporting routes
│   ├── settings.py          # Settings routes
│   ├── email_service.py     # Email functionality
│   ├── logging_config.py    # Logging configuration
│   ├── config.py            # Configuration
│   ├── init_db.py           # Database initialization
│   └── requirements.txt     # Python dependencies
├── workhub-frontend/         # React frontend
│   ├── src/
│   │   ├── components/      # Reusable components
│   │   ├── pages/           # Page components
│   │   ├── context/         # React contexts
│   │   ├── hooks/           # Custom hooks
│   │   ├── services/        # API services
│   │   └── styles/          # CSS files
│   ├── package.json         # Node dependencies
│   └── vite.config.js       # Vite configuration
├── nginx/                    # Nginx configuration
├── docker-compose.yml        # Development setup
├── docker-compose.prod.yml   # Production setup
└── deploy.sh                 # Production deployment script
```

## 🔧 Configuration

### Environment Variables

Create `.env` file for development or `.env.prod` for production:

```bash
# Database
DB_HOST=localhost
DB_PORT=3306
DB_NAME=workhub
DB_USER=root
DB_PASSWORD=password

# Application
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret

# Email (Optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com

# URLs
FRONTEND_URL=http://localhost:3000
```

## 🎨 UI/UX Features

### Theme System
- Light and dark theme support
- User preference persistence
- System-wide theme switching

### Responsive Design
- Mobile-first approach
- Tablet and desktop optimized
- Touch-friendly interface

### Accessibility
- Keyboard navigation support
- Screen reader compatibility
- High contrast support

## 🔒 Security Features

### Authentication
- JWT-based authentication
- Secure password hashing (bcrypt)
- Password reset via email
- Session management

### Authorization
- Role-based access control
- Route protection
- API endpoint security

### Data Protection
- Input validation and sanitization
- SQL injection prevention
- XSS protection
- CSRF protection

## 📊 Monitoring and Logging

### Logging Levels
- **Access Logs**: API requests and responses
- **Security Logs**: Authentication and authorization events
- **Error Logs**: Application errors and exceptions
- **General Logs**: Application flow and debugging

### Health Checks
- Database connectivity
- Service availability
- API endpoint health

## 🧪 Testing

### Backend Testing
```bash
cd workhub-backend
python -m pytest tests/
```

### Frontend Testing
```bash
cd workhub-frontend
npm test
```

### Integration Testing
```bash
docker-compose -f docker-compose.test.yml up --build
```

## 📈 Performance

### Optimization Features
- Database query optimization
- Frontend code splitting
- Image optimization
- Gzip compression
- Caching strategies

### Scalability
- Horizontal scaling support
- Database connection pooling
- Load balancer ready
- Microservices architecture

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### Development Guidelines
- Follow PEP 8 for Python code
- Use ESLint for JavaScript/React code
- Write comprehensive tests
- Update documentation

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Documentation
- [API Documentation](docs/API.md)
- [Deployment Guide](PRODUCTION_DEPLOYMENT.md)
- [Development Guide](docs/DEVELOPMENT.md)

### Issues
- [GitHub Issues](https://github.com/your-repo/issues)
- [Bug Reports](https://github.com/your-repo/issues/new?template=bug_report.md)
- [Feature Requests](https://github.com/your-repo/issues/new?template=feature_request.md)

### Contact
- Email: support@workhub.com
- Documentation: [docs.workhub.com](https://docs.workhub.com)

## 🙏 Acknowledgments

- React team for the amazing framework
- Flask team for the lightweight web framework
- All contributors and testers
- Open source community

---

**Work Hub** - Streamline your team's productivity with powerful task management.