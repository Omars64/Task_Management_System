# Email Configuration Setup Guide

## Overview
The WorkHub application now supports email configuration through two methods:
1. **Environment Variables** (recommended for production/Cloud Run)
2. **SystemSettings Database** (fallback or for easy configuration via API)

## Configuration Methods

### Method 1: Environment Variables (Production)

Set these environment variables in your deployment (Cloud Run, Docker, etc.):

```bash
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
```

**For Gmail:**
- Use an **App Password** (not your regular password)
- Generate at: https://myaccount.google.com/apppasswords
- Enable 2-Step Verification first

### Method 2: SystemSettings Database (Via API or Script)

#### Option A: Using the Configuration Script

Run the interactive script:

```bash
cd workhub-backend
python configure_email.py
```

The script will:
- Check for existing environment variables
- Prompt for missing values
- Save configuration to the database

#### Option B: Using the API Endpoint

Send a PUT request to `/api/settings/system`:

```json
{
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 587,
  "smtp_username": "your-email@gmail.com",
  "smtp_password": "your-app-password",
  "smtp_from_email": "your-email@gmail.com",
  "smtp_from_name": "WorkHub Task Management",
  "email_notifications_enabled": true
}
```

**Note:** Requires authentication and SETTINGS_VIEW permission.

## How It Works

1. **Priority Order:**
   - First: Environment variables are checked
   - Second: If env vars are not set, SystemSettings database is checked
   - The application automatically loads from database on startup

2. **Dynamic Loading:**
   - Email services check both sources dynamically
   - Settings can be updated via API without restarting the app
   - Changes take effect immediately for new email sends

## Testing Email Configuration

1. **Check Configuration:**
   - Look for log messages: "Email configuration loaded from SystemSettings database"
   - Check server logs for email sending status

2. **Test Signup:**
   - Create a new user account
   - Check if verification email is received
   - If not received, check server logs for errors

3. **Common Issues:**
   - **Gmail "Less secure app" error:** Use App Password instead
   - **Connection timeout:** Check firewall/network settings
   - **Authentication failed:** Verify username and password are correct

## Troubleshooting

### Email Not Sending

1. Check server logs for error messages
2. Verify SMTP credentials are correct
3. Test SMTP connection manually:
   ```python
   import smtplib
   server = smtplib.SMTP('smtp.gmail.com', 587)
   server.starttls()
   server.login('your-email@gmail.com', 'your-app-password')
   server.quit()
   ```

### Configuration Not Loading

1. Check database connection
2. Verify SystemSettings table exists
3. Check that settings are saved correctly:
   ```sql
   SELECT smtp_username, smtp_server, smtp_port FROM system_settings;
   ```

## Security Notes

- **Never commit passwords to git**
- Use environment variables in production (Cloud Run secrets)
- App passwords are safer than regular passwords
- Database passwords are encrypted at rest (database-level encryption)

## Support

If you encounter issues:
1. Check this guide
2. Review server logs
3. Verify SMTP settings with your email provider
4. Test with a simple SMTP connection script

