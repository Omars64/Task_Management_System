from flask import Flask, jsonify, request, g
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from datetime import timedelta
from config import Config
from models import db, bcrypt
from auth import auth_bp
from users import users_bp
from tasks import tasks_bp
from notifications import notifications_bp
from reports import reports_bp
from projects import projects_bp
from sprints import sprints_bp
from settings import settings_bp
from file_uploads import file_uploads_bp
from reminders import reminders_bp
from meetings import meetings_bp
from chat import chat_bp
from email_service import email_service
from session_middleware import session_timeout_required, prevent_duplicate_submission, validate_cross_field_logic
import logging
import uuid
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    JWTManager(app)
    
    # CORS configuration - support multiple origins for production
    allowed_origins = os.environ.get('ALLOWED_ORIGINS', '*')
    if allowed_origins != '*':
        allowed_origins = [origin.strip() for origin in allowed_origins.split(',')]
    CORS(app, resources={r"/*": {"origins": allowed_origins}})
    
    # Initialize Flask-Mail for email verification codes
    mail = Mail(app)
    app.extensions['mail'] = mail
    
    # Configure JWT settings for session timeout
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=30)  # 30 minute session timeout
    
    # Configure file uploads
    app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB max upload size
    
    # Configure email service (support both SMTP_* and MAIL_* envs)
    app.config['SMTP_SERVER'] = os.environ.get('SMTP_SERVER') or os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    app.config['SMTP_PORT'] = int((os.environ.get('SMTP_PORT') or os.environ.get('MAIL_PORT') or 587))
    app.config['SMTP_USERNAME'] = os.environ.get('SMTP_USERNAME') or os.environ.get('MAIL_USERNAME', '')
    app.config['SMTP_PASSWORD'] = os.environ.get('SMTP_PASSWORD') or os.environ.get('MAIL_PASSWORD', '')
    app.config['SMTP_FROM_EMAIL'] = os.environ.get('SMTP_FROM_EMAIL') or os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@workhub.com')
    app.config['SMTP_FROM_NAME'] = os.environ.get('SMTP_FROM_NAME', 'WorkHub Task Management')
    # Enable emails automatically if credentials are present, unless explicitly disabled
    env_enabled = os.environ.get('EMAIL_NOTIFICATIONS_ENABLED')
    app.config['EMAIL_NOTIFICATIONS_ENABLED'] = (env_enabled.lower() == 'true') if isinstance(env_enabled, str) else bool(app.config['SMTP_USERNAME'])
    app.config['FRONTEND_URL'] = os.environ.get('FRONTEND_URL', 'http://localhost:5173')
    
    # Initialize email service
    email_service.init_app(app)
    
    # Initialize database schema on first request (idempotent - safe to run multiple times)
    # This ensures all tables exist when the app starts
    _db_init_lock = False
    
    @app.before_request
    def _initialize_database():
        global _db_init_lock
        # Only run once per worker process
        if not _db_init_lock:
            _db_init_lock = True
            try:
                with app.app_context():
                    # Try to import and use the comprehensive initialization script
                    try:
                        from init_cloud_sql import init_database
                        init_database()
                        logging.getLogger('workhub').info("Database schema initialized using init_cloud_sql.py")
                    except ImportError:
                        # Fallback: use SQLAlchemy create_all
                        db.create_all()
                        logging.getLogger('workhub').info("Database schema initialized using db.create_all()")
            except Exception as e:
                logging.getLogger('workhub').error(f"Database initialization error: {e}")
                # Don't block app if initialization fails - tables might already exist
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(tasks_bp, url_prefix='/api/tasks')
    app.register_blueprint(notifications_bp, url_prefix='/api/notifications')
    app.register_blueprint(reports_bp, url_prefix='/api/reports')
    app.register_blueprint(projects_bp, url_prefix='/api/projects')
    app.register_blueprint(sprints_bp, url_prefix='/api/sprints')
    app.register_blueprint(settings_bp, url_prefix='/api/settings')
    app.register_blueprint(file_uploads_bp, url_prefix='/api/files')
    app.register_blueprint(reminders_bp, url_prefix='/api/reminders')
    app.register_blueprint(meetings_bp, url_prefix='/api/meetings')
    app.register_blueprint(chat_bp, url_prefix='/api/chat')
    
    # Basic structured logging with request IDs
    @app.before_request
    def _attach_request_id():
        g.request_id = request.headers.get('X-Request-ID') or str(uuid.uuid4())

    @app.after_request
    def _log_request(response):
        try:
            user_id = None
            # Lazy import to avoid circulars
            from flask_jwt_extended import get_jwt_identity
            try:
                user_id = int(get_jwt_identity())
            except Exception:
                user_id = None
            log_line = {
                'request_id': getattr(g, 'request_id', None),
                'method': request.method,
                'path': request.path,
                'status': response.status_code,
                'user_id': user_id,
                'ip': request.remote_addr,
            }
            logging.getLogger('workhub').info(log_line)
            # Echo request id to clients
            response.headers['X-Request-ID'] = g.request_id
        except Exception:
            pass
        return response

    # Health check endpoint
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({'status': 'healthy', 'message': 'Work Hub API is running'}), 200
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Resource not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")
        
        # Check email configuration
        if app.config.get('MAIL_USERNAME'):
            print(f"✓ Flask-Mail configured: {app.config.get('MAIL_SERVER')}:{app.config.get('MAIL_PORT')}")
            print(f"✓ Mail sender: {app.config.get('MAIL_DEFAULT_SENDER')}")
        else:
            print("⚠ Flask-Mail not configured - verification codes will be logged to console")
    
    app.run(host='0.0.0.0', port=5000, debug=False)