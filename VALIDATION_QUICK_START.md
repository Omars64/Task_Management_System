# Validation & Security Quick Start Guide

## TL;DR - What Changed?

1. **Passwords:** Now require 10 characters minimum (was 8)
2. **Task Titles:** Now require 3 characters minimum (was 0)
3. **Due Dates:** Must be at least 1 hour from now
4. **Login:** Locks after 5 failed attempts for 10 minutes
5. **Email Verification:** Required for new registrations (optional to enable)
6. **File Uploads:** Stricter validation (10MB max, executables blocked)

---

## For Developers

### Quick Integration

#### 1. Update Dependencies

```bash
cd workhub-backend
pip install -r requirements.txt
```

#### 2. Use Enhanced Validators (Already Active)

The enhanced `validators.py` is automatically used by existing routes:

```python
from validators import validator, ValidationError

# Will use new 10-char password policy automatically
data = validator.validate_user_payload(payload, db=db.session)
```

#### 3. Add Security Middleware to Routes

```python
from security_middleware import rate_limit, csrf_protect, limit_request_size
from schema_validation import validate_schema, TASK_CREATE_SCHEMA

@tasks_bp.post('/')
@jwt_required()
@rate_limit(max_requests=10, time_window=60)  # 10 req/min
@csrf_protect  # Requires X-CSRF-Token header
@limit_request_size()  # 10MB max
@validate_schema(TASK_CREATE_SCHEMA)  # JSON schema validation
def create_task():
    # Your code here
    pass
```

#### 4. Enable Email Verification (Optional)

Update `app.py` to use `auth_enhanced.py`:

```python
from auth_enhanced import auth_bp, init_mail
from flask_mail import Mail

mail = Mail(app)
init_mail(mail)

# Register blueprint (use enhanced version)
app.register_blueprint(auth_bp, url_prefix='/api/auth')
```

Add to `.env`:
```bash
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
FRONTEND_URL=http://localhost:3000
```

---

## For Frontend Developers

### Password Validation Updated

**Old:** 8 characters minimum
**New:** 10 characters minimum + at least 3 of: uppercase, lowercase, digit, special

```javascript
// INVALID passwords:
"Short1!"        // Too short (< 10)
"Password123"   // Too common
"Abcdef123"     // Sequential pattern

// VALID passwords:
"MyP@ssw0rd"    // 10 chars, 4 classes
"SecurePass123!" // Long enough, 4 classes
"Admin2024#"    // 10 chars, 3 classes
```

### Task Title Validation Updated

**Old:** 0-100 characters
**New:** 3-100 characters

```javascript
// INVALID:
"AB"  // Too short

// VALID:
"ABC" // Minimum 3 chars
"Fix login bug"
```

### Due Date Validation Updated

**Old:** Cannot be in the past
**New:** Must be at least 1 hour from now

```javascript
// INVALID:
new Date(Date.now() + 30 * 60 * 1000)  // 30 minutes from now

// VALID:
new Date(Date.now() + 2 * 60 * 60 * 1000)  // 2 hours from now
```

### Using Validation Utils

```javascript
import { ValidationUtils } from './utils/validation';

// Single field
const result = ValidationUtils.validatePassword(password);
if (!result.isValid) {
    console.error(result.message);
}

// Whole form
const { isValid, errors } = ValidationUtils.validateForm(formData, 'taskCreation');
```

### React Hook

```javascript
import { useFormValidation } from './utils/validation';

function MyForm() {
    const { errors, validateField, validateForm, clearErrors } = useFormValidation('userRegistration');
    
    const handleChange = (field, value) => {
        validateField(field, value, formData);
    };
    
    const handleSubmit = () => {
        if (validateForm(formData)) {
            // Submit
        }
    };
}
```

---

## For Testers

### Test Password Policy

```bash
# Test 1: Too short
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"Short1!","confirm":"Short1!","name":"Test"}'

# Expected: 400 - "Password must be at least 10 characters"

# Test 2: Common password
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"Password123","confirm":"Password123","name":"Test"}'

# Expected: 400 - "Password is too common"

# Test 3: Valid password
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"MyP@ssw0rd","confirm":"MyP@ssw0rd","name":"Test User"}'

# Expected: 201 - Success
```

### Test Rate Limiting

```bash
# Rapid login attempts
for i in {1..6}; do
    curl -X POST http://localhost:5000/api/auth/login \
         -H "Content-Type: application/json" \
         -d '{"email":"test@test.com","password":"wrong"}'
    echo ""
done

# Expected: First 5 return 401, 6th returns 429 (Rate Limited)
```

### Test Account Lockout

```bash
# 5 failed login attempts
for i in {1..6}; do
    curl -X POST http://localhost:5000/api/auth/login \
         -H "Content-Type: application/json" \
         -d '{"email":"test@test.com","password":"WrongPassword1!"}'
    echo ""
    sleep 1
done

# Expected: First 5 return 401, 6th returns 403 (Account Locked)
```

### Test Task Validation

```bash
# Test 1: Title too short
curl -X POST http://localhost:5000/api/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"title":"AB","description":"Test task description","priority":"high"}'

# Expected: 400 - "Task title must be at least 3 characters"

# Test 2: Due date too soon
curl -X POST http://localhost:5000/api/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"title":"Test","description":"Test description","due_date":"2024-01-01T12:00:00Z","priority":"high"}'

# Expected: 400 - "Due date must be at least 1 hour from now"

# Test 3: XSS attempt
curl -X POST http://localhost:5000/api/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"title":"Test","description":"<script>alert(1)</script>","priority":"high"}'

# Expected: 400 - "Description contains potentially dangerous content"
```

---

## Common Validation Errors & Solutions

### Error: "Password must be at least 10 characters"

**Solution:** Use a password with 10+ characters

```
❌ MyPass1!
✅ MyPassw0rd!
```

### Error: "Password is too common"

**Solution:** Avoid common patterns like "Password123", "Admin123"

```
❌ Password123
✅ MyP@ssw0rd
```

### Error: "Password contains sequential patterns"

**Solution:** Avoid sequences like "123", "abc"

```
❌ Abc123def!
✅ MyP@ssw0rd
```

### Error: "Task title must be at least 3 characters"

**Solution:** Use 3+ character titles

```
❌ "AB"
✅ "ABC"
✅ "Fix login bug"
```

### Error: "Due date must be at least 1 hour from now"

**Solution:** Set due date to 1+ hours in the future

```javascript
❌ new Date(Date.now() + 30 * 60 * 1000)  // 30 min
✅ new Date(Date.now() + 2 * 60 * 60 * 1000)  // 2 hours
```

### Error: "Account locked due to multiple failed attempts"

**Solution:** Wait 10 minutes or contact admin to unlock

### Error: "Rate limit exceeded"

**Solution:** Wait before retrying. Limits vary by endpoint:
- Login: 5 attempts per 5 minutes
- Registration: 3 attempts per hour
- Password reset: 3 attempts per hour

### Error: "Description contains potentially dangerous content"

**Solution:** Remove HTML/JavaScript from description

```
❌ "<script>alert(1)</script>"
❌ "Click <a href='javascript:void(0)'>here</a>"
✅ "Regular text description"
```

---

## Quick Validation Reference

### User Fields

| Field | Min | Max | Rules |
|-------|-----|-----|-------|
| Name | 2 | 50 | Letters, spaces, hyphens, apostrophes only |
| Email | - | - | Valid email format, unique |
| Password | 10 | 128 | 3 of 4: upper/lower/digit/special |

### Task Fields

| Field | Min | Max | Rules |
|-------|-----|-----|-------|
| Title | 3 | 100 | Required, no symbols-only |
| Description | 10 | 1000 | Required, XSS protected |
| Priority | - | - | low/medium/high |
| Tags | 0 | 5 | Each tag ≤30 chars |
| Due Date | +1h | +1y | ISO 8601, UTC |

### Comment/Time Log

| Field | Min | Max | Rules |
|-------|-----|-----|-------|
| Comment | 1 | 500 | Profanity filter, XSS protected |
| Hours | 0.1 | 24 | Numeric, 2 decimal places |

### File Upload

| Constraint | Value |
|------------|-------|
| Max Size | 10MB |
| Allowed Types | jpg, jpeg, png, gif, pdf, txt |
| Blocked Types | exe, bat, cmd, com, scr, vbs, js, jar, dll |

---

## Rate Limits Reference

| Endpoint | Limit | Window |
|----------|-------|--------|
| POST /auth/login | 5 | 5 minutes |
| POST /auth/register | 3 | 1 hour |
| POST /auth/forgot-password | 3 | 1 hour |
| POST /auth/reset-password | 5 | 1 hour |
| POST /auth/verify-email | 10 | 1 hour |
| POST /auth/change-password | 5 | 1 hour |
| POST /tasks | 10 | 1 minute |

---

## Example Valid Payloads

### Register User

```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "SecureP@ss123",
  "confirm": "SecureP@ss123",
  "role": "user"
}
```

### Login

```json
{
  "email": "john@example.com",
  "password": "SecureP@ss123"
}
```

### Create Task

```json
{
  "title": "Implement user authentication",
  "description": "Add JWT-based authentication to the API endpoints",
  "priority": "high",
  "status": "todo",
  "due_date": "2024-12-31T23:59:59Z",
  "tags": ["auth", "security", "backend"]
}
```

### Add Comment

```json
{
  "content": "I've started working on this task"
}
```

### Log Time

```json
{
  "hours": 2.5,
  "description": "Implemented login endpoint"
}
```

---

## Need More Help?

- **Full Documentation:** `SECURITY_VALIDATION_GUIDE.md`
- **Implementation Details:** `VALIDATION_IMPLEMENTATION_SUMMARY.md`
- **Code Examples:** Check the `/examples` in each file

---

## Breaking Changes

⚠️ **Important:** These changes may break existing functionality:

1. **Passwords < 10 chars:** Users with 8-9 char passwords need to reset
2. **Task titles < 3 chars:** Existing short titles need updating
3. **Due dates < 1 hour:** Need to be adjusted to 1+ hour lead time
4. **Email verification:** If enabled, new users must verify email before login

### Migration Script

To update existing data:

```python
# Update short task titles
from models import db, Task
tasks = Task.query.filter(db.func.length(Task.title) < 3).all()
for task in tasks:
    task.title = f"TSK-{task.title}"  # Prefix to make it 3+ chars
db.session.commit()

# Force password reset for weak passwords
from models import User
users = User.query.all()
for user in users:
    # Send password reset email
    send_password_reset_email(user.email)
```

---

## License

See main project LICENSE file.

