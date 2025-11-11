from flask import Flask, jsonify, request, g
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required
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
    
    # Ensure JSON responses use UTF-8 encoding
    app.config['JSON_AS_ASCII'] = False  # Allow non-ASCII characters (emojis) in JSON
    
    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    JWTManager(app)
    
    # CORS configuration - support multiple origins for production
    allowed_origins = os.environ.get('ALLOWED_ORIGINS', '*')
    if allowed_origins != '*':
        allowed_origins = [origin.strip() for origin in allowed_origins.split(',')]
    CORS(app, resources={r"/*": {"origins": allowed_origins}})
    
    # Configure JWT settings for session timeout
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=30)  # 30 minute session timeout
    
    # Configure file uploads
    app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB max upload size
    
    # Configure email service (support both SMTP_* and MAIL_* envs)
    # Priority: Environment variables > SystemSettings database
    # Read from environment variables first (GCP Secret Manager or Cloud Run env vars)
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER') or os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int((os.environ.get('MAIL_PORT') or os.environ.get('SMTP_PORT') or 587))
    app.config['MAIL_USE_TLS'] = str(os.environ.get('MAIL_USE_TLS', 'True')).lower() == 'true'
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME') or os.environ.get('SMTP_USERNAME', '')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD') or os.environ.get('SMTP_PASSWORD', '')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER') or os.environ.get('SMTP_FROM_EMAIL', 'noreply@workhub.com')
    # Set timeout to prevent long delays (10 seconds)
    app.config['MAIL_TIMEOUT'] = 10
    
    # Also set SMTP_* for email_service compatibility
    app.config['SMTP_SERVER'] = app.config['MAIL_SERVER']
    app.config['SMTP_PORT'] = app.config['MAIL_PORT']
    app.config['SMTP_USERNAME'] = app.config['MAIL_USERNAME']
    app.config['SMTP_PASSWORD'] = app.config['MAIL_PASSWORD']
    app.config['SMTP_FROM_EMAIL'] = app.config['MAIL_DEFAULT_SENDER']
    app.config['SMTP_FROM_NAME'] = os.environ.get('SMTP_FROM_NAME', 'WorkHub Task Management')
    
    # Function to load email config from SystemSettings database (fallback if env vars not set)
    def load_email_config_from_db():
        """Load email configuration from SystemSettings if env vars are not set or empty"""
        try:
            from models import SystemSettings
            # Check if we have valid credentials in app.config
            current_username = app.config.get('MAIL_USERNAME') or app.config.get('SMTP_USERNAME', '')
            current_password = app.config.get('MAIL_PASSWORD') or app.config.get('SMTP_PASSWORD', '')
            
            # Strip whitespace to check if actually empty
            current_username = current_username.strip() if current_username else ''
            current_password = current_password.strip() if current_password else ''
            
            # Only load from DB if env vars are not set or are empty strings
            if not current_username or not current_password:
                settings = SystemSettings.query.first()
                if settings:
                    # Check if database has credentials (handle None values)
                    db_username = settings.smtp_username if settings.smtp_username else ''
                    db_password = settings.smtp_password if settings.smtp_password else ''
                    db_username = db_username.strip() if db_username else ''
                    db_password = db_password.strip() if db_password else ''
                    
                    if db_username and db_password:
                        # Update config from database
                        if settings.smtp_server:
                            app.config['MAIL_SERVER'] = settings.smtp_server
                            app.config['SMTP_SERVER'] = settings.smtp_server
                        if settings.smtp_port:
                            app.config['MAIL_PORT'] = settings.smtp_port
                            app.config['SMTP_PORT'] = settings.smtp_port
                        if settings.smtp_username:
                            app.config['MAIL_USERNAME'] = settings.smtp_username
                            app.config['SMTP_USERNAME'] = settings.smtp_username
                        if settings.smtp_password:
                            app.config['MAIL_PASSWORD'] = settings.smtp_password
                            app.config['SMTP_PASSWORD'] = settings.smtp_password
                        if settings.smtp_from_email:
                            app.config['MAIL_DEFAULT_SENDER'] = settings.smtp_from_email
                            app.config['SMTP_FROM_EMAIL'] = settings.smtp_from_email
                        if settings.smtp_from_name:
                            app.config['SMTP_FROM_NAME'] = settings.smtp_from_name
                        
                        # Reinitialize Flask-Mail with new config
                        if 'mail' in app.extensions:
                            app.extensions['mail'].init_app(app)
                        else:
                            mail = Mail(app)
                            app.extensions['mail'] = mail
                        
                        # Reinitialize email service
                        email_service.init_app(app)
                        
                        logging.getLogger('workhub').info("Email configuration loaded from SystemSettings database")
                        return True
                    else:
                        logging.getLogger('workhub').debug("SystemSettings found but credentials are empty or missing")
                else:
                    logging.getLogger('workhub').debug("No SystemSettings record found in database")
            else:
                logging.getLogger('workhub').debug("Email credentials already present in app.config, skipping database load")
        except Exception as e:
            logging.getLogger('workhub').warning(f"Could not load email config from database: {e}")
            import traceback
            logging.getLogger('workhub').debug(traceback.format_exc())
        return False
    
    # Store function for later use
    app.load_email_config_from_db = load_email_config_from_db
    
    # Enable emails automatically if credentials are present, unless explicitly disabled
    env_enabled = os.environ.get('EMAIL_NOTIFICATIONS_ENABLED')
    app.config['EMAIL_NOTIFICATIONS_ENABLED'] = (env_enabled.lower() == 'true') if isinstance(env_enabled, str) else bool(app.config['MAIL_USERNAME'])
    app.config['FRONTEND_URL'] = os.environ.get('FRONTEND_URL', 'http://localhost:5173')
    
    # CRITICAL: Try to load email config from database BEFORE initializing Flask-Mail
    # This ensures Flask-Mail is initialized with the correct credentials
    with app.app_context():
        try:
            # Ensure database is initialized first
            try:
                from init_cloud_sql import init_database
                init_database()
            except ImportError:
                db.create_all()
            
            # Now try to load email config from database
            config_loaded = load_email_config_from_db()
            if config_loaded:
                logging.getLogger('workhub').info("Email configuration pre-loaded from database successfully")
            else:
                logging.getLogger('workhub').info("Email configuration not found in database, will check on first request")
        except Exception as e:
            # Use print instead of logging for Unicode characters on Windows
            error_msg = str(e).encode('ascii', 'replace').decode('ascii')
            logging.getLogger('workhub').warning(f"Could not pre-load email config: {error_msg}")
            import traceback
            try:
                logging.getLogger('workhub').debug(traceback.format_exc())
            except:
                pass  # Ignore Unicode errors in traceback
            # Continue anyway - config will be loaded on first request
    
    # Initialize Flask-Mail for email verification codes (AFTER trying to load config from DB)
    # Flask-Mail reads from app.config, so if we loaded from DB, it will use those values
    mail = Mail(app)
    app.extensions['mail'] = mail
    
    # Log final email config status
    if app.config.get('MAIL_USERNAME') and app.config.get('MAIL_PASSWORD'):
        logging.getLogger('workhub').info(f"Flask-Mail initialized with username: {app.config.get('MAIL_USERNAME')}")
    else:
        logging.getLogger('workhub').warning("Flask-Mail initialized without credentials - will load from DB on first use")
    
    # Initialize email service
    email_service.init_app(app)
    
    # Initialize database schema on first request (idempotent - safe to run multiple times)
    # This ensures all tables exist when the app starts
    # Use app-level attribute to track initialization status
    app._db_initialized = False
    
    @app.before_request
    def _initialize_database():
        # Only run once per worker process
        if not getattr(app, '_db_initialized', False):
            app._db_initialized = True
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
                    
                    # After database is initialized, try to load email config from SystemSettings
                    if hasattr(app, 'load_email_config_from_db'):
                        app.load_email_config_from_db()
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
    
    # Email connectivity test endpoint (for debugging)
    @app.route('/api/health/email', methods=['GET'])
    @jwt_required()
    def email_health_check():
        """Test email connectivity - checks if SMTP server is reachable"""
        from auth import get_current_user
        from permissions import Permission
        # Only allow admins
        current_user = get_current_user()
        if not current_user or not current_user.has_permission(Permission.SETTINGS_VIEW):
            return jsonify({"error": "Access denied"}), 403

        import socket
        mail_server = app.config.get('MAIL_SERVER', 'smtp.gmail.com')
        mail_port = app.config.get('MAIL_PORT', 587)
        mail_username = app.config.get('MAIL_USERNAME') or app.config.get('SMTP_USERNAME', '')
        mail_password = app.config.get('MAIL_PASSWORD') or app.config.get('SMTP_PASSWORD', '')
        
        # Check if credentials are configured
        credentials_configured = bool(mail_username and mail_password and 
                                     mail_username.strip() and mail_password.strip())
        
        try:
            # Try to connect to SMTP server
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((mail_server, mail_port))
            sock.close()
            
            if result == 0:
                return jsonify({
                    'status': 'reachable',
                    'server': mail_server,
                    'port': mail_port,
                    'credentials_configured': credentials_configured,
                    'message': f'Successfully connected to {mail_server}:{mail_port}',
                    'note': 'Email will work if credentials are configured in Settings'
                }), 200
            else:
                return jsonify({
                    'status': 'unreachable',
                    'server': mail_server,
                    'port': mail_port,
                    'credentials_configured': credentials_configured,
                    'error': f'Cannot connect to {mail_server}:{mail_port} (error code: {result})',
                    'suggestion': 'Check VPC egress and Cloud NAT configuration'
                }), 503
        except socket.gaierror as e:
            return jsonify({
                'status': 'dns_error',
                'server': mail_server,
                'credentials_configured': credentials_configured,
                'error': f'DNS resolution failed for {mail_server}: {str(e)}'
            }), 503
        except Exception as e:
            return jsonify({
                'status': 'error',
                'server': mail_server,
                'credentials_configured': credentials_configured,
                'error': str(e)
            }), 500
    
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