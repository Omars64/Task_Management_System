"""
Security middleware for P0 requirements:
- CSRF protection with tokens
- Rate limiting for authentication endpoints
- Account lockout after failed attempts
- Request body size limits
"""

import functools
import hashlib
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, Optional
from flask import request, jsonify, session, g
from flask_jwt_extended import get_jwt_identity


# ========== RATE LIMITING ==========

class RateLimiter:
    """
    In-memory rate limiter (P0).
    For production, use Redis or similar distributed cache.
    """
    
    def __init__(self):
        self.requests: Dict[str, list] = {}
        self.lockouts: Dict[str, datetime] = {}
        self.failed_attempts: Dict[str, list] = {}
    
    def _cleanup_old_entries(self, key: str, time_window: int):
        """Remove entries older than time_window seconds"""
        if key in self.requests:
            cutoff = time.time() - time_window
            self.requests[key] = [t for t in self.requests[key] if t > cutoff]
    
    def _cleanup_old_failures(self, key: str, time_window: int = 600):
        """Remove failed attempts older than time_window seconds (default 10 min)"""
        if key in self.failed_attempts:
            cutoff = time.time() - time_window
            self.failed_attempts[key] = [t for t in self.failed_attempts[key] if t > cutoff]
    
    def is_rate_limited(self, identifier: str, max_requests: int, time_window: int) -> bool:
        """
        Check if identifier has exceeded rate limit.
        
        Args:
            identifier: Unique identifier (IP, user ID, etc.)
            max_requests: Maximum requests allowed
            time_window: Time window in seconds
        
        Returns:
            True if rate limited, False otherwise
        """
        self._cleanup_old_entries(identifier, time_window)
        
        if identifier not in self.requests:
            self.requests[identifier] = []
        
        # Check current request count
        if len(self.requests[identifier]) >= max_requests:
            return True
        
        # Record this request
        self.requests[identifier].append(time.time())
        return False
    
    def is_locked_out(self, identifier: str) -> bool:
        """Check if identifier is currently locked out (P0)"""
        if identifier in self.lockouts:
            lockout_until = self.lockouts[identifier]
            if datetime.utcnow() < lockout_until:
                return True
            else:
                # Lockout expired, remove it
                del self.lockouts[identifier]
                if identifier in self.failed_attempts:
                    del self.failed_attempts[identifier]
        return False
    
    def record_failed_attempt(self, identifier: str, max_attempts: int = 5, 
                             lockout_minutes: int = 10) -> Optional[datetime]:
        """
        Record a failed login attempt and apply lockout if needed (P0).
        
        Args:
            identifier: Unique identifier (email, IP, etc.)
            max_attempts: Maximum failed attempts before lockout
            lockout_minutes: Lockout duration in minutes
        
        Returns:
            Lockout expiry datetime if locked out, None otherwise
        """
        self._cleanup_old_failures(identifier)
        
        if identifier not in self.failed_attempts:
            self.failed_attempts[identifier] = []
        
        self.failed_attempts[identifier].append(time.time())
        
        # Check if lockout threshold reached
        if len(self.failed_attempts[identifier]) >= max_attempts:
            lockout_until = datetime.utcnow() + timedelta(minutes=lockout_minutes)
            self.lockouts[identifier] = lockout_until
            return lockout_until
        
        return None
    
    def clear_failed_attempts(self, identifier: str):
        """Clear failed attempts after successful login"""
        if identifier in self.failed_attempts:
            del self.failed_attempts[identifier]
        if identifier in self.lockouts:
            del self.lockouts[identifier]


# Global rate limiter instance
rate_limiter = RateLimiter()


def rate_limit(max_requests: int = 5, time_window: int = 60, 
              identifier_func=None):
    """
    Rate limiting decorator (P0).
    
    Args:
        max_requests: Maximum requests allowed in time window
        time_window: Time window in seconds
        identifier_func: Function to get identifier (default: IP address)
    """
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            # Get identifier
            if identifier_func:
                identifier = identifier_func()
            else:
                # Default to IP address
                identifier = request.remote_addr or 'unknown'
            
            # Check rate limit
            if rate_limiter.is_rate_limited(identifier, max_requests, time_window):
                return jsonify({
                    'error': 'Rate limit exceeded. Please try again later.',
                    'code': 'RATE_LIMITED'
                }), 429
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def check_account_lockout(identifier: str) -> Optional[dict]:
    """
    Check if account is locked out (P0).
    Returns error response if locked out, None otherwise.
    """
    if rate_limiter.is_locked_out(identifier):
        return jsonify({
            'error': 'Account temporarily locked due to multiple failed attempts. Please try again later.',
            'code': 'ACCOUNT_LOCKED'
        }), 403
    return None


# ========== CSRF PROTECTION ==========

class CSRFProtection:
    """
    CSRF protection using double-submit cookie pattern (P0).
    For stateless APIs with JWT, we use a custom header approach.
    """
    
    @staticmethod
    def generate_csrf_token() -> str:
        """Generate a secure CSRF token"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def get_csrf_token_from_session() -> Optional[str]:
        """Get CSRF token from session"""
        return session.get('csrf_token')
    
    @staticmethod
    def set_csrf_token_in_session(token: str):
        """Store CSRF token in session"""
        session['csrf_token'] = token
    
    @staticmethod
    def validate_csrf_token(token: str) -> bool:
        """Validate CSRF token against session"""
        session_token = session.get('csrf_token')
        if not session_token:
            return False
        return secrets.compare_digest(session_token, token)


def csrf_protect(f):
    """
    CSRF protection decorator for state-changing routes (P0).
    Checks X-CSRF-Token header against session token.
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        # Skip CSRF for GET, HEAD, OPTIONS (safe methods)
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return f(*args, **kwargs)
        
        # Get CSRF token from header
        csrf_token = request.headers.get('X-CSRF-Token')
        
        if not csrf_token:
            return jsonify({
                'error': 'CSRF token missing.',
                'code': 'CSRF_MISSING'
            }), 403
        
        # Validate token
        if not CSRFProtection.validate_csrf_token(csrf_token):
            return jsonify({
                'error': 'CSRF token invalid.',
                'code': 'CSRF_INVALID'
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated_function


# ========== REQUEST SIZE LIMITING ==========

MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB (P0)


def limit_request_size(max_size: int = MAX_CONTENT_LENGTH):
    """
    Limit request body size (P0).
    Prevents DoS attacks with large payloads.
    """
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            content_length = request.content_length
            
            if content_length is not None and content_length > max_size:
                return jsonify({
                    'error': f'Request body too large. Maximum size: {max_size / (1024 * 1024)}MB',
                    'code': 'PAYLOAD_TOO_LARGE'
                }), 413
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


# ========== UNIFORM ERROR HANDLING ==========

def format_error_response(error_message: str, field: str = None, code: str = None) -> dict:
    """
    Format error response with uniform structure (P1).
    
    Returns:
        {
            "error": "Human-readable message",
            "field": "field_name" (optional),
            "code": "ERROR_CODE"
        }
    """
    response = {
        "error": error_message,
        "code": code or "ERROR"
    }
    
    if field:
        response["field"] = field
    
    return response


def handle_validation_error(validation_error):
    """
    Handle ValidationError and return uniform error response (P1).
    """
    return jsonify(format_error_response(
        str(validation_error),
        field=getattr(validation_error, 'field', None),
        code=getattr(validation_error, 'code', 'VALIDATION_ERROR')
    )), 400


# ========== IMMUTABLE FIELD PROTECTION ==========

IMMUTABLE_FIELDS = {
    'id', 'created_at', 'created_by', 'creator_id'
}


def protect_immutable_fields(payload: dict, model_name: str = "Record") -> dict:
    """
    Remove immutable fields from update payload (P0).
    Prevents modification of audit fields and primary keys.
    """
    blocked_fields = []
    cleaned_payload = {}
    
    for key, value in payload.items():
        if key in IMMUTABLE_FIELDS:
            blocked_fields.append(key)
        else:
            cleaned_payload[key] = value
    
    if blocked_fields:
        # Log attempt to modify immutable fields
        print(f"Warning: Attempt to modify immutable fields on {model_name}: {blocked_fields}")
    
    return cleaned_payload


# ========== OPTIMISTIC LOCKING ==========

def check_optimistic_lock(record, payload: dict) -> Optional[dict]:
    """
    Check optimistic lock using updated_at timestamp (P0).
    Prevents lost updates when multiple users edit the same record.
    
    Args:
        record: Database record with updated_at field
        payload: Update payload with expected_version or expected_updated_at
    
    Returns:
        Error response if lock check fails, None otherwise
    """
    expected_updated_at = payload.get('expected_updated_at')
    
    if expected_updated_at and hasattr(record, 'updated_at'):
        # Compare timestamps
        if record.updated_at:
            record_timestamp = record.updated_at.isoformat()
            if record_timestamp != expected_updated_at:
                return jsonify({
                    'error': 'Record has been modified by another user. Please refresh and try again.',
                    'code': 'OPTIMISTIC_LOCK_FAILED',
                    'current_version': record_timestamp
                }), 409
    
    return None


# ========== GENERIC ERROR RESPONSES ==========

def generic_auth_error(message: str = None):
    """
    Return generic authentication error (P0).
    Prevents account enumeration attacks.
    """
    return jsonify({
        'error': message or 'Invalid credentials.',
        'code': 'AUTH_FAILED'
    }), 401

