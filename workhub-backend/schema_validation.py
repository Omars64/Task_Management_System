"""
JSON Schema validation for API endpoints (P0).
Validates request payloads against defined schemas.
"""

from functools import wraps
from flask import request, jsonify
from typing import Dict, Any, Optional


# ========== SCHEMA DEFINITIONS ==========

# User schemas
USER_REGISTRATION_SCHEMA = {
    "type": "object",
    "required": ["name", "email", "password"],
    "properties": {
        "name": {
            "type": "string",
            "minLength": 2,
            "maxLength": 50,
            "description": "User's full name"
        },
        "email": {
            "type": "string",
            "format": "email",
            "description": "User's email address"
        },
        "password": {
            "type": "string",
            "minLength": 10,
            "maxLength": 128,
            "description": "User's password (min 10 chars)"
        },
        "confirm": {
            "type": "string",
            "description": "Password confirmation"
        },
        "role": {
            "type": "string",
            "enum": ["user", "admin"],
            "description": "User role"
        }
    },
    "additionalProperties": False
}

LOGIN_SCHEMA = {
    "type": "object",
    "required": ["email", "password"],
    "properties": {
        "email": {
            "type": "string",
            "format": "email"
        },
        "password": {
            "type": "string",
            "minLength": 1
        }
    },
    "additionalProperties": False
}

PASSWORD_CHANGE_SCHEMA = {
    "type": "object",
    "required": ["old_password", "new_password"],
    "properties": {
        "old_password": {
            "type": "string",
            "minLength": 1
        },
        "new_password": {
            "type": "string",
            "minLength": 10,
            "maxLength": 128
        },
        "confirm": {
            "type": "string"
        }
    },
    "additionalProperties": False
}

# Task schemas
TASK_CREATE_SCHEMA = {
    "type": "object",
    "required": ["title", "description"],
    "properties": {
        "title": {
            "type": "string",
            "minLength": 3,
            "maxLength": 100,
            "description": "Task title (3-100 chars)"
        },
        "description": {
            "type": "string",
            "minLength": 10,
            "maxLength": 1000,
            "description": "Task description (10-1000 chars)"
        },
        "priority": {
            "type": "string",
            "enum": ["low", "medium", "high"],
            "description": "Task priority"
        },
        "status": {
            "type": "string",
            "enum": ["todo", "in_progress", "completed", "blocked"],
            "description": "Task status"
        },
        "assigned_to": {
            "type": ["integer", "null"],
            "description": "User ID of assignee"
        },
        "due_date": {
            "type": ["string", "null"],
            "format": "date-time",
            "description": "Due date (ISO 8601)"
        },
        "tags": {
            "type": "array",
            "maxItems": 5,
            "items": {
                "type": "string",
                "maxLength": 30
            },
            "description": "Task tags (max 5)"
        }
    },
    "additionalProperties": False
}

TASK_UPDATE_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {
            "type": "string",
            "minLength": 3,
            "maxLength": 100
        },
        "description": {
            "type": "string",
            "minLength": 10,
            "maxLength": 1000
        },
        "priority": {
            "type": "string",
            "enum": ["low", "medium", "high"]
        },
        "status": {
            "type": "string",
            "enum": ["todo", "in_progress", "completed", "blocked"]
        },
        "assigned_to": {
            "type": ["integer", "null"]
        },
        "due_date": {
            "type": ["string", "null"],
            "format": "date-time"
        },
        "tags": {
            "type": "array",
            "maxItems": 5,
            "items": {
                "type": "string",
                "maxLength": 30
            }
        },
        "expected_updated_at": {
            "type": "string",
            "format": "date-time",
            "description": "For optimistic locking"
        }
    },
    "additionalProperties": False
}

# Comment schema
COMMENT_CREATE_SCHEMA = {
    "type": "object",
    "required": ["content"],
    "properties": {
        "content": {
            "type": "string",
            "minLength": 1,
            "maxLength": 500,
            "description": "Comment content (max 500 chars)"
        }
    },
    "additionalProperties": False
}

# Time log schema
TIME_LOG_CREATE_SCHEMA = {
    "type": "object",
    "required": ["hours"],
    "properties": {
        "hours": {
            "type": "number",
            "minimum": 0.1,
            "maximum": 24.0,
            "description": "Hours logged (0.1-24)"
        },
        "description": {
            "type": "string",
            "maxLength": 500,
            "description": "Optional description"
        }
    },
    "additionalProperties": False
}

# Email/verification schemas
EMAIL_SCHEMA = {
    "type": "object",
    "required": ["email"],
    "properties": {
        "email": {
            "type": "string",
            "format": "email"
        }
    },
    "additionalProperties": False
}

TOKEN_SCHEMA = {
    "type": "object",
    "required": ["token"],
    "properties": {
        "token": {
            "type": "string",
            "minLength": 1
        }
    },
    "additionalProperties": False
}

PASSWORD_RESET_SCHEMA = {
    "type": "object",
    "required": ["token", "new_password"],
    "properties": {
        "token": {
            "type": "string",
            "minLength": 1
        },
        "new_password": {
            "type": "string",
            "minLength": 10,
            "maxLength": 128
        },
        "confirm": {
            "type": "string"
        }
    },
    "additionalProperties": False
}


# ========== VALIDATION FUNCTIONS ==========

def validate_type(value: Any, expected_type: str) -> tuple[bool, Optional[str]]:
    """Validate value type"""
    type_map = {
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool,
        "array": list,
        "object": dict,
        "null": type(None)
    }
    
    if expected_type not in type_map:
        return False, f"Unknown type: {expected_type}"
    
    expected = type_map[expected_type]
    
    # Handle union types (e.g., ["string", "null"])
    if isinstance(expected_type, list):
        valid = False
        for t in expected_type:
            if isinstance(value, type_map.get(t, type(None))):
                valid = True
                break
        if not valid:
            return False, f"Value must be one of types: {expected_type}"
    elif not isinstance(value, expected):
        return False, f"Value must be of type {expected_type}"
    
    return True, None


def validate_string(value: str, constraints: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """Validate string constraints"""
    if "minLength" in constraints and len(value) < constraints["minLength"]:
        return False, f"String must be at least {constraints['minLength']} characters"
    
    if "maxLength" in constraints and len(value) > constraints["maxLength"]:
        return False, f"String must be at most {constraints['maxLength']} characters"
    
    if "pattern" in constraints:
        import re
        if not re.match(constraints["pattern"], value):
            return False, f"String does not match required pattern"
    
    if "enum" in constraints and value not in constraints["enum"]:
        return False, f"Value must be one of: {', '.join(constraints['enum'])}"
    
    return True, None


def validate_number(value: (int, float), constraints: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """Validate number constraints"""
    if "minimum" in constraints and value < constraints["minimum"]:
        return False, f"Number must be at least {constraints['minimum']}"
    
    if "maximum" in constraints and value > constraints["maximum"]:
        return False, f"Number must be at most {constraints['maximum']}"
    
    return True, None


def validate_array(value: list, constraints: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """Validate array constraints"""
    if "minItems" in constraints and len(value) < constraints["minItems"]:
        return False, f"Array must have at least {constraints['minItems']} items"
    
    if "maxItems" in constraints and len(value) > constraints["maxItems"]:
        return False, f"Array must have at most {constraints['maxItems']} items"
    
    # Validate items
    if "items" in constraints:
        for i, item in enumerate(value):
            valid, error = validate_value(item, constraints["items"])
            if not valid:
                return False, f"Array item {i}: {error}"
    
    return True, None


def validate_value(value: Any, schema: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """Validate a value against a schema"""
    # Check type
    if "type" in schema:
        expected_type = schema["type"]
        
        # Handle union types
        if isinstance(expected_type, list):
            valid = False
            for t in expected_type:
                if t == "null" and value is None:
                    return True, None
                type_map = {"string": str, "integer": int, "number": (int, float), 
                           "boolean": bool, "array": list, "object": dict}
                if t in type_map and isinstance(value, type_map[t]):
                    valid = True
                    expected_type = t
                    break
            if not valid:
                return False, f"Value must be one of types: {schema['type']}"
        else:
            valid, error = validate_type(value, expected_type)
            if not valid:
                return False, error
    
    # Type-specific validation
    if isinstance(value, str) and "type" in schema and schema["type"] == "string":
        return validate_string(value, schema)
    
    if isinstance(value, (int, float)) and "type" in schema and schema["type"] in ["number", "integer"]:
        return validate_number(value, schema)
    
    if isinstance(value, list) and "type" in schema and schema["type"] == "array":
        return validate_array(value, schema)
    
    if isinstance(value, dict) and "type" in schema and schema["type"] == "object":
        return validate_object(value, schema)
    
    return True, None


def validate_object(data: Dict[str, Any], schema: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """Validate an object against a schema"""
    # Check required fields
    if "required" in schema:
        for field in schema["required"]:
            if field not in data:
                return False, f"Missing required field: {field}"
    
    # Check properties
    if "properties" in schema:
        for key, value in data.items():
            if key in schema["properties"]:
                field_schema = schema["properties"][key]
                valid, error = validate_value(value, field_schema)
                if not valid:
                    return False, f"Field '{key}': {error}"
            elif schema.get("additionalProperties") is False:
                return False, f"Additional property not allowed: {key}"
    
    return True, None


# ========== DECORATOR ==========

def validate_schema(schema: Dict[str, Any]):
    """
    Decorator to validate request JSON against a schema (P0).
    
    Usage:
        @validate_schema(TASK_CREATE_SCHEMA)
        def create_task():
            # Request data is guaranteed to match schema
            data = request.get_json()
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get JSON data
            data = request.get_json(silent=True)
            
            if data is None:
                return jsonify({
                    "error": "Request body must be JSON",
                    "code": "INVALID_JSON"
                }), 400
            
            # Validate against schema
            valid, error = validate_object(data, schema)
            
            if not valid:
                return jsonify({
                    "error": error,
                    "code": "SCHEMA_VALIDATION_FAILED"
                }), 400
            
            # Schema valid, proceed
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


# ========== HELPER FUNCTIONS ==========

def get_schema_for_endpoint(endpoint_name: str) -> Optional[Dict[str, Any]]:
    """
    Get schema for a specific endpoint.
    
    Args:
        endpoint_name: Name of endpoint (e.g., 'user_registration', 'task_create')
    
    Returns:
        Schema dict or None
    """
    schemas = {
        "user_registration": USER_REGISTRATION_SCHEMA,
        "login": LOGIN_SCHEMA,
        "password_change": PASSWORD_CHANGE_SCHEMA,
        "password_reset": PASSWORD_RESET_SCHEMA,
        "task_create": TASK_CREATE_SCHEMA,
        "task_update": TASK_UPDATE_SCHEMA,
        "comment_create": COMMENT_CREATE_SCHEMA,
        "time_log_create": TIME_LOG_CREATE_SCHEMA,
        "email": EMAIL_SCHEMA,
        "token": TOKEN_SCHEMA,
    }
    
    return schemas.get(endpoint_name)

