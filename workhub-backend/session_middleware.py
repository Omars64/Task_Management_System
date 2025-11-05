"""
Session timeout middleware for automatic logout after inactivity
"""
from flask import request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity, decode_token
from datetime import datetime, timedelta
import functools

# Session timeout in minutes (configurable)
SESSION_TIMEOUT_MINUTES = 30

def session_timeout_required(f):
    """
    Decorator that checks if the user's session is still valid
    Automatically logs out users after inactivity
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Get the JWT token from the request
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({'error': 'No valid token provided'}), 401
            
            token = auth_header.split(' ')[1]
            
            # Decode the token to get expiration time
            decoded_token = decode_token(token)
            exp_timestamp = decoded_token.get('exp')
            
            if exp_timestamp:
                exp_datetime = datetime.fromtimestamp(exp_timestamp)
                current_time = datetime.utcnow()
                
                # Check if token is expired
                if current_time > exp_datetime:
                    return jsonify({'error': 'Session expired. Please login again.'}), 401
                
                # Check if session is close to expiring (within 5 minutes)
                time_until_expiry = exp_datetime - current_time
                if time_until_expiry < timedelta(minutes=5):
                    # You could extend the token here if needed
                    pass
            
            return f(*args, **kwargs)
            
        except Exception as e:
            return jsonify({'error': 'Session validation failed'}), 401
    
    return decorated_function

def prevent_duplicate_submission(f):
    """
    Decorator to prevent duplicate form submissions
    Uses a simple in-memory cache (in production, use Redis or database)
    """
    submission_cache = {}
    
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Get user ID and request data to create a unique key
            user_id = get_jwt_identity()
            request_data = request.get_json() or {}
            
            # Create a unique key based on user, endpoint, and data
            cache_key = f"{user_id}_{request.endpoint}_{hash(str(sorted(request_data.items())))}"
            
            # Check if this exact submission was made recently (within 5 seconds)
            current_time = datetime.utcnow()
            if cache_key in submission_cache:
                last_submission = submission_cache[cache_key]
                if current_time - last_submission < timedelta(seconds=5):
                    return jsonify({'error': 'Duplicate submission detected. Please wait before submitting again.'}), 429
            
            # Record this submission
            submission_cache[cache_key] = current_time
            
            # Clean up old entries (simple cleanup)
            if len(submission_cache) > 1000:
                # Remove entries older than 1 minute
                cutoff_time = current_time - timedelta(minutes=1)
                submission_cache = {k: v for k, v in submission_cache.items() if v > cutoff_time}
            
            return f(*args, **kwargs)
            
        except Exception as e:
            # If there's an error in duplicate detection, allow the request to proceed
            return f(*args, **kwargs)
    
    return decorated_function

def validate_cross_field_logic(f):
    """
    Decorator for cross-field validation
    Validates business logic that spans multiple fields
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # This is a placeholder for cross-field validation
            # Specific validation logic would be implemented based on the endpoint
            
            # Example: For task updates, check if completed tasks can have future due dates
            if request.endpoint and 'task' in request.endpoint:
                data = request.get_json()
                if data and 'status' in data and 'due_date' in data:
                    if data['status'] == 'completed' and data.get('due_date'):
                        try:
                            due_date = datetime.fromisoformat(data['due_date'].replace('Z', '+00:00'))
                            if due_date > datetime.utcnow():
                                return jsonify({
                                    'error': 'Completed tasks cannot have future due dates'
                                }), 400
                        except:
                            pass  # Let other validation handle date format errors
            
            return f(*args, **kwargs)
            
        except Exception as e:
            # If cross-field validation fails, allow the request to proceed
            # Individual field validation will catch specific issues
            return f(*args, **kwargs)
    
    return decorated_function
