# Security & Validation Implementation Guide

## Overview

This document describes the comprehensive P0 (Priority 0) and P1 (Priority 1) security and validation features implemented in the WorkHub Task Management System.

---

## P0 Security Features (Critical)

### 1. Server-Side Validation

**Status:** ✅ Implemented

**Location:** `workhub-backend/validators.py`

All user input is validated on the server side with comprehensive rules:

#### User Validation
- **Name:** 2-50 characters, letters/spaces/hyphens/apostrophes only (no digits)
- **Email:** Valid format with RFC-compliant regex, uniqueness check, normalized (lowercase)
- **Password:** 
  - Minimum 10 characters (increased from 8)
  - At least 3 of 4 character classes: uppercase, lowercase, digit, special
  - No common weak passwords
  - No sequential patterns (123, abc, etc.)

#### Task Validation
- **Title:** 3-100 characters (P1 enhancement)
- **Description:** 10-1000 characters with XSS protection
- **Due Date:** 
  - Minimum 1 hour lead time (P1)
  - Maximum 1 year in future
  - Timezone-aware (UTC storage)
- **Priority:** Must be 'low', 'medium', or 'high'
- **Tags:** Maximum 5 tags, each ≤30 characters

#### Comment & Time Log Validation
- **Comments:** ≤500 characters, profanity filter, HTML sanitization
- **Time Logs:** 0.1-24 hours, optional description ≤500 characters

### 2. XSS Protection

**Status:** ✅ Implemented

**Location:** `workhub-backend/validators.py`

All user text is sanitized before storage and rendering:

```python
# Using bleach library
- Strips dangerous HTML tags (script, iframe, embed, object)
- Detects JavaScript injection attempts
- Allows only safe formatting tags (b, i, u, em, strong, p, br)
```

**Dangerous patterns blocked:**
- `<script`, `javascript:`, `vbscript:`
- `onload=`, `onerror=`, `onclick=`, `onmouseover=`
- `<iframe`, `<embed`, `<object>`

### 3. CSRF Protection

**Status:** ✅ Implemented

**Location:** `workhub-backend/security_middleware.py`

Double-submit cookie pattern with custom header:

```python
# Usage
@csrf_protect
def my_route():
    # Route is protected
```

**How it works:**
1. Session generates CSRF token
2. Client includes token in `X-CSRF-Token` header
3. Server validates token before processing request
4. GET/HEAD/OPTIONS requests exempt (safe methods)

### 4. Authentication Hardening

#### Email Verification

**Status:** ✅ Implemented

**Location:** `workhub-backend/email_verification.py`

- 24-hour token expiry
- One-time use tokens
- Automatic token cleanup
- HTML email templates

**Flow:**
1. User registers → email_verified = false
2. System sends verification email with token
3. User clicks link → token validated
4. Account activated → email_verified = true

#### Password Policy

**Status:** ✅ Enhanced (P0)

- **Minimum:** 10 characters (was 8)
- **Complexity:** At least 3 of 4 character classes
- **Blocked:** Common passwords, sequential patterns
- **Enforced:** On registration, password change, reset

#### Rate Limiting

**Status:** ✅ Implemented

**Location:** `workhub-backend/security_middleware.py`

| Endpoint | Limit | Window |
|----------|-------|--------|
| Login | 5 requests | 5 minutes |
| Register | 3 requests | 1 hour |
| Password Reset | 3 requests | 1 hour |
| Email Verification | 10 requests | 1 hour |
| Change Password | 5 requests | 1 hour |

**Usage:**
```python
@rate_limit(max_requests=5, time_window=60)
def my_route():
    # Route is rate limited
```

#### Account Lockout

**Status:** ✅ Implemented

**Location:** `workhub-backend/security_middleware.py`

- **Threshold:** 5 failed login attempts
- **Lockout Duration:** 10 minutes
- **Scope:** Per email address
- **Auto-clear:** On successful login

**Generic Error Responses:**
All auth endpoints return generic messages to prevent account enumeration:
- ❌ "Invalid email or password" (not "Email not found")
- ❌ "If email exists, a reset link will be sent" (not "Email not found")

### 5. File Upload Validation

**Status:** ✅ Implemented

**Location:** `workhub-backend/validators.py`

#### Allow-list MIME Types (P0)
```python
ALLOWED_MIME_TYPES = {
    'image/jpeg', 'image/jpg', 'image/png', 'image/gif',
    'application/pdf', 'text/plain'
}
```

#### Blocked Executables (P0)
```python
BLOCKED_EXTENSIONS = {
    '.exe', '.bat', '.cmd', '.com', '.scr', '.pif', 
    '.vbs', '.js', '.jar', '.dll', '.msi'
}
```

#### Size Limits
- **Maximum:** 10MB per file
- **Enforced:** Server-side in validator and app config

#### Filename Sanitization
- User-provided filenames are NOT used
- Server generates UUID-based filenames
- Original filename stored separately for display

### 6. Data Integrity

**Status:** ✅ Implemented

#### Foreign Key Validation (P0)

**Location:** `workhub-backend/validators.py`

All references validated before creation:
```python
# Assignee must exist
def validate_assignee(self, assignee_id, db):
    user = db.query(User).filter_by(id=assignee_id).first()
    if not user:
        raise ValidationError("Assignee not found.")
```

#### Immutable Audit Fields (P0)

**Location:** `workhub-backend/security_middleware.py`

Protected fields automatically removed from update payloads:
```python
IMMUTABLE_FIELDS = {
    'id', 'created_at', 'created_by', 'creator_id'
}
```

#### Optimistic Locking (P0)

**Location:** `workhub-backend/security_middleware.py`

Prevents lost updates when multiple users edit same record:
```python
# Client sends expected_updated_at
# Server compares with current version
# Returns 409 Conflict if version mismatch
```

### 7. API Robustness

#### Uniform Error Format (P0)

**Location:** `workhub-backend/security_middleware.py`

All errors return consistent structure:
```json
{
    "error": "Human-readable message",
    "field": "field_name",
    "code": "ERROR_CODE"
}
```

**Error codes:**
- `VALIDATION_ERROR`, `REQUIRED`, `TOO_SHORT`, `TOO_LONG`
- `INVALID_FORMAT`, `INVALID_TYPE`, `NOT_FOUND`
- `RATE_LIMITED`, `ACCOUNT_LOCKED`, `CSRF_INVALID`
- `XSS_DETECTED`, `PROFANITY`, `COMMON`, `SEQUENTIAL`

#### Request Body Size Limits (P0)

**Location:** `workhub-backend/security_middleware.py`

```python
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB

@limit_request_size(max_size=MAX_CONTENT_LENGTH)
def my_route():
    # Route has size limit
```

#### Input Validation Basics (P0)

**Location:** `workhub-backend/validators.py`

All inputs validated for:
- Empty/whitespace-only values rejected
- Unicode normalization (NFC)
- Zero-width character removal
- Homoglyph attack prevention

---

## P1 Validation & UX Features

### 1. Timezone Discipline

**Status:** ✅ Implemented

**Storage:** Always UTC
```python
due_date_dt = due_date_dt.astimezone(timezone.utc)
```

**Validation:** Timezone-aware
```python
if due_date_dt.tzinfo is None:
    due_date_dt = due_date_dt.replace(tzinfo=timezone.utc)
```

**Display:** (Frontend responsibility - add timezone conversion)

### 2. Due Date Rules

**Status:** ✅ Implemented

**Minimum Lead Time:** 1 hour from now
```python
MIN_DUE_DATE_LEAD_TIME = timedelta(hours=1)
if due_date_dt < (now + MIN_DUE_DATE_LEAD_TIME):
    raise ValidationError("Due date must be at least 1 hour from now.")
```

**Maximum Horizon:** 1 year from now
```python
MAX_DUE_DATE_HORIZON = timedelta(days=365)
if due_date_dt > (now + MAX_DUE_DATE_HORIZON):
    raise ValidationError("Due date cannot be more than 1 year in the future.")
```

### 3. Task Constraints

**Title:** 3-100 characters (was 0-100)
```python
if len(title) < 3:
    raise ValidationError("Task title must be at least 3 characters.")
```

**Tags:** Maximum 5, each ≤30 characters
```python
if len(tags) > 5:
    raise ValidationError("Maximum 5 tags allowed.")
```

### 4. Input Validation UX

**Frontend Validation:** `workhub-frontend/src/utils/validation.js`

Enhanced with:
- Real-time field validation
- Clear, specific error messages
- Consistent error format matching backend
- `useFormValidation` hook for React components

---

## Usage Examples

### Backend Validation

```python
from validators import validator, ValidationError

# Validate user
try:
    data = validator.validate_user_payload(payload, db=db.session, check_unique_email=True)
except ValidationError as e:
    return handle_validation_error(e)

# Validate task
try:
    data = validator.validate_task_payload(payload, db=db.session)
except ValidationError as e:
    return handle_validation_error(e)

# Validate comment
try:
    data = validator.validate_comment(payload)
except ValidationError as e:
    return handle_validation_error(e)
```

### Frontend Validation

```javascript
import { ValidationUtils } from './utils/validation';

// Validate field
const result = ValidationUtils.validateEmail(email);
if (!result.isValid) {
    console.error(result.message);
}

// Validate form
const { isValid, errors } = ValidationUtils.validateForm(formData, 'userRegistration');
if (!isValid) {
    console.error(errors);
}

// Use hook
const { errors, validateField, validateForm } = useFormValidation('taskCreation');
```

### Security Middleware

```python
from security_middleware import rate_limit, csrf_protect, limit_request_size

@rate_limit(max_requests=5, time_window=60)
@csrf_protect
@limit_request_size(max_size=5*1024*1024)  # 5MB
def my_route():
    # Fully protected route
    pass
```

---

## Testing Security Features

### 1. Test Rate Limiting
```bash
# Rapid requests should trigger rate limit
for i in {1..10}; do
    curl -X POST http://localhost:5000/api/auth/login \
         -H "Content-Type: application/json" \
         -d '{"email":"test@test.com","password":"wrong"}'
done
# Should see 429 Too Many Requests
```

### 2. Test Account Lockout
```bash
# 5 failed logins should lock account
for i in {1..6}; do
    curl -X POST http://localhost:5000/api/auth/login \
         -H "Content-Type: application/json" \
         -d '{"email":"test@test.com","password":"WrongPass123!"}'
done
# 6th request should return 403 Account Locked
```

### 3. Test Password Policy
```bash
# Too short (< 10 chars)
curl -X POST http://localhost:5000/api/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email":"test@test.com","password":"Short1!","confirm":"Short1!","name":"Test"}'
# Should return 400 with error: "Password must be at least 10 characters"

# Common password
curl -X POST http://localhost:5000/api/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email":"test@test.com","password":"Password123","confirm":"Password123","name":"Test"}'
# Should return 400 with error: "Password is too common"
```

### 4. Test XSS Protection
```bash
curl -X POST http://localhost:5000/api/tasks \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -d '{"title":"Test","description":"<script>alert(1)</script>","priority":"high"}'
# Should return 400 with error: "Description contains potentially dangerous content"
```

---

## Migration Notes

### For Existing Installations

1. **Update Dependencies:**
   ```bash
   cd workhub-backend
   pip install -r requirements.txt
   ```

2. **Add Email Verified Column (optional):**
   ```sql
   ALTER TABLE users ADD COLUMN email_verified BIT DEFAULT 0;
   ```

3. **Update Environment Variables:**
   ```bash
   # .env
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USE_TLS=True
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-app-password
   MAIL_DEFAULT_SENDER=noreply@workhub.com
   FRONTEND_URL=http://localhost:3000
   ```

4. **Update Existing Users:**
   ```python
   # Reset existing passwords to meet new policy
   # Send password reset emails to all users
   ```

---

## Future Enhancements

### Recommended for Production

1. **MFA/TOTP for Admins**
   - Implement 2FA using pyotp library
   - QR code generation for authenticator apps

2. **JWT Token Blacklisting**
   - Redis-based token blacklist for logout
   - Automatic cleanup of expired tokens

3. **Distributed Rate Limiting**
   - Replace in-memory rate limiter with Redis
   - Ensures rate limiting across multiple servers

4. **Security Headers**
   - Add helmet.js equivalent for Flask
   - CSP, X-Frame-Options, HSTS, etc.

5. **Audit Logging**
   - Log all authentication events
   - Track failed login attempts
   - Monitor suspicious activity

---

## Support & Questions

For questions or issues, please refer to:
- Main README: `../README.md`
- API Documentation: `../API_DOCUMENTATION.md`
- Implementation Summary: `../IMPLEMENTATION_SUMMARY.md`

## License

See main project LICENSE file.

