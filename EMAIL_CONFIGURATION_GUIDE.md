# Email Configuration Guide

## Overview
The WorkHub Task Management System requires email configuration to send verification codes and notifications. Without proper email configuration, the system will work but codes will only be logged to the server console.

---

## Security Notice 🔒

**IMPORTANT**: As of the latest security update, verification codes are ONLY sent via email (out-of-band delivery). They are NEVER returned in API responses or displayed in the UI. 

- ✅ Production: Codes sent via email
- ⚠️ Development (no email): Codes logged to server console only

---

## Configuration Options

### Option 1: Gmail SMTP (Recommended for Testing)

#### Step 1: Enable App Passwords in Gmail
1. Go to your Google Account settings
2. Navigate to Security → 2-Step Verification
3. Enable 2-Step Verification if not already enabled
4. Go to Security → App passwords
5. Generate an app password for "Mail"
6. Copy the 16-character password

#### Step 2: Configure Environment Variables
Create a `.env` file in the project root:

```env
# Email Configuration (Gmail)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password-here
MAIL_DEFAULT_SENDER=your-email@gmail.com

# Optional
FRONTEND_URL=http://localhost:3000
```

---

### Option 2: Outlook/Office 365 SMTP

```env
# Email Configuration (Outlook)
MAIL_SERVER=smtp-mail.outlook.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@outlook.com
MAIL_PASSWORD=your-password
MAIL_DEFAULT_SENDER=your-email@outlook.com
```

---

### Option 3: Custom SMTP Server

```env
# Email Configuration (Custom)
MAIL_SERVER=smtp.yourdomain.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=noreply@yourdomain.com
MAIL_PASSWORD=your-password
MAIL_DEFAULT_SENDER=noreply@yourdomain.com
```

---

### Option 4: SendGrid (Production Recommended)

#### Step 1: Get SendGrid API Key
1. Sign up at https://sendgrid.com
2. Create an API key with "Mail Send" permissions
3. Verify your sender email

#### Step 2: Configure Environment
```env
# Email Configuration (SendGrid)
MAIL_SERVER=smtp.sendgrid.net
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=apikey
MAIL_PASSWORD=your-sendgrid-api-key-here
MAIL_DEFAULT_SENDER=verified@yourdomain.com
```

---

## Email Templates

The system sends the following emails:

### 1. Verification Code Email
**Subject**: "Verify Your Email - WorkHub"
- Large 6-digit code display
- 15-minute expiration notice
- Professional HTML formatting

### 2. Admin Notification Email
**Subject**: "New User Signup Request - WorkHub"
- Notifies admins of pending user signups
- Includes user details and signup date
- Link to review pending users

### 3. Approval Email
**Subject**: "Your Account Has Been Approved - WorkHub"
- Sent when admin approves a user
- Includes login link

### 4. Rejection Email
**Subject**: "Account Signup Update - WorkHub"
- Sent when admin rejects a user
- Optionally includes rejection reason

---

## Development Mode (No Email)

If email is not configured, the system works with limited functionality:

### What Happens
1. ✅ User can sign up
2. ⚠️ Verification code logged to **server console only**
3. ⚠️ UI shows: "Check server console for verification code"
4. ✅ Developer checks backend logs
5. ✅ User can enter code and verify

### Server Console Output
```
============================================================
DEVELOPMENT MODE: Email not configured
Verification code for user@example.com: 123456
Expires in 15 minutes
============================================================
```

### Security in Development Mode
- ✅ Code NEVER sent to client
- ✅ Code NEVER in API responses
- ✅ Code NEVER in browser/logs
- ✅ Code only in server console (backend terminal)

---

## Testing Email Configuration

### Test 1: Check Configuration
Start the backend and look for startup messages:
```bash
cd workhub-backend
python app.py
```

Expected output (if configured):
```
Mail server configured: smtp.gmail.com:587
```

### Test 2: Trigger Signup Email
```bash
curl -X POST http://localhost:5000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "password": "Test@123456",
    "confirm": "Test@123456"
  }'
```

Check:
1. ✅ Response does NOT include `verification_code`
2. ✅ Email arrives at test@example.com inbox
3. ✅ Email contains 6-digit code

### Test 3: Verify Response Security
```javascript
// Response should look like this:
{
  "message": "Signup successful! Please check your email for verification code.",
  "user_id": 123,
  "needs_verification": true,
  "needs_approval": true,
  "email_sent": true
}

// Should NOT include:
// "verification_code": "123456"  ❌ NEVER PRESENT
```

---

## Troubleshooting

### Error: "Connection refused" or "Timeout"
**Cause**: SMTP server unreachable
**Solutions**:
- Check firewall settings
- Verify SMTP server address and port
- Try alternative port (465 for SSL, 587 for TLS)

### Error: "Authentication failed"
**Cause**: Invalid credentials
**Solutions**:
- Verify username and password
- For Gmail: Use App Password, not account password
- Check if 2FA is enabled (required for Gmail)

### Error: "SSL/TLS error"
**Cause**: Certificate or encryption issues
**Solutions**:
- Set `MAIL_USE_TLS=True` for port 587
- Set `MAIL_USE_SSL=True` for port 465
- Check SMTP server requirements

### Emails Not Arriving
**Causes & Solutions**:
1. Check spam/junk folder
2. Verify sender email is verified with provider
3. Check email service logs/console output
4. Ensure recipient email is valid
5. Check rate limits (SendGrid, etc.)

### Development: Can't See Code
**Solution**: Check the **backend terminal/console**, not browser console. The code is logged server-side only.

---

## Production Deployment

### Best Practices
1. ✅ Use dedicated email service (SendGrid, AWS SES, Mailgun)
2. ✅ Use environment variables (never hardcode credentials)
3. ✅ Verify sender domain (SPF, DKIM, DMARC)
4. ✅ Monitor email delivery rates
5. ✅ Set up email bounce handling
6. ✅ Use HTTPS for frontend URL in emails

### Recommended Services
- **SendGrid**: Up to 100 emails/day free, good API
- **AWS SES**: Low cost, high volume, requires setup
- **Mailgun**: Developer-friendly, good free tier
- **Postmark**: Excellent deliverability, transactional emails

### Environment Variables for Production
```env
# Production Email (SendGrid example)
MAIL_SERVER=smtp.sendgrid.net
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=apikey
MAIL_PASSWORD=${SENDGRID_API_KEY}
MAIL_DEFAULT_SENDER=noreply@yourdomain.com

# Production URLs
FRONTEND_URL=https://workhub.yourdomain.com
SECRET_KEY=${RANDOM_SECRET_KEY}
JWT_SECRET_KEY=${RANDOM_JWT_SECRET}
```

---

## Security Checklist

- ✅ Email credentials in environment variables (not code)
- ✅ Verification codes ONLY sent via email
- ✅ No verification codes in API responses
- ✅ No verification codes in client UI
- ✅ Use TLS/SSL for SMTP connection
- ✅ Sender email verified with provider
- ✅ Rate limiting enabled
- ✅ Email templates don't expose sensitive data
- ✅ HTTPS used for links in emails (production)

---

## Email Flow Diagram

```
┌──────────────┐
│ User Signup  │
└──────┬───────┘
       │
       ▼
┌──────────────────────┐
│ Generate 6-Digit Code│
│ (Server-side only)   │
└──────┬───────────────┘
       │
       ├─────────────────────────┐
       │                         │
       ▼                         ▼
┌─────────────┐         ┌───────────────┐
│ Send Email  │         │ Log to Console│
│ (Production)│         │ (Development) │
└──────┬──────┘         └───────────────┘
       │
       ▼
┌─────────────────┐
│ User Receives   │
│ Email with Code │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ User Enters Code│
│ in Web Form     │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Server Validates│
│ & Marks Verified│
└─────────────────┘
```

---

## Quick Start

### Minimum Configuration (Gmail)
1. Create `.env` file in project root
2. Add these lines:
```env
MAIL_USERNAME=your.email@gmail.com
MAIL_PASSWORD=your-16-char-app-password
MAIL_DEFAULT_SENDER=your.email@gmail.com
```
3. Restart backend
4. Test signup flow

### Verification
- ✅ Check email inbox for code
- ✅ Code should be 6 digits
- ✅ Code expires in 15 minutes
- ✅ Code can be used once

---

## Related Files

- `workhub-backend/config.py` - Email configuration loading
- `workhub-backend/verification_service.py` - Email sending logic
- `workhub-backend/auth.py` - Signup and verification endpoints
- `SECURITY_FIX_VERIFICATION_CODE.md` - Security implementation details

---

## Support

If you encounter issues:
1. Check this guide's troubleshooting section
2. Verify environment variables are loaded
3. Check backend console for error messages
4. Review `SECURITY_FIX_VERIFICATION_CODE.md` for security details
5. Test with a different email provider

---

**Last Updated**: 2025-10-27  
**Security Compliance**: ✅ Out-of-band delivery verified

