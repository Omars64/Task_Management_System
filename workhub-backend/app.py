from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from models import db, bcrypt
from auth import auth_bp
from users import users_bp
from tasks import tasks_bp
from notifications import notifications_bp
from reports import reports_bp
from settings import settings_bp
from email_service import init_email
from logging_config import setup_logging, log_api_access, log_security_event
import time

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    JWTManager(app)
    CORS(app, resources={r"/*": {"origins": "*"}})
    init_email(app)
    
    # Setup logging
    setup_logging(app)
    
    # Request logging middleware
    @app.before_request
    def log_request_info():
        request.start_time = time.time()
    
    @app.after_request
    def log_response_info(response):
        if hasattr(request, 'start_time'):
            response_time = (time.time() - request.start_time) * 1000  # Convert to milliseconds
            
            # Get user ID if authenticated
            user_id = None
            try:
                from flask_jwt_extended import get_jwt_identity
                user_id = get_jwt_identity()
            except:
                pass
            
            # Log API access
            log_api_access(
                method=request.method,
                endpoint=request.endpoint or request.path,
                user_id=user_id,
                ip_address=request.remote_addr,
                status_code=response.status_code,
                response_time=response_time
            )
        
        return response
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(tasks_bp, url_prefix='/api/tasks')
    app.register_blueprint(notifications_bp, url_prefix='/api/notifications')
    app.register_blueprint(reports_bp, url_prefix='/api/reports')
    app.register_blueprint(settings_bp, url_prefix='/api/settings')
    
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
    
    app.run(host='0.0.0.0', port=5000, debug=False)