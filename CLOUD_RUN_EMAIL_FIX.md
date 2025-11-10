# Cloud Run Email Network Issue - Fix Guide

## Problem
Email configuration is working correctly, but Cloud Run cannot reach external SMTP servers:
```
OSError: [Errno 101] Network is unreachable
```

## Root Cause
Cloud Run services may have restricted outbound internet access depending on VPC configuration. By default, Cloud Run has outbound access, but if a VPC connector is configured, it may need explicit egress settings.

## Solutions

### Solution 1: Update Cloud Run Service (Quick Fix)

Run this command to update your Cloud Run service:

```bash
gcloud run services update workhub-backend \
  --region=us-central1 \
  --vpc-egress=all-traffic \
  --quiet
```

**Note:** This only works if you have a VPC connector. If you don't have one, Cloud Run should have outbound access by default.

### Solution 2: Use SendGrid (Recommended for Production)

SendGrid works better with Cloud Run than Gmail SMTP:

1. **Sign up for SendGrid**: https://sendgrid.com (free tier: 100 emails/day)

2. **Get API Key**:
   - Go to Settings → API Keys
   - Create new API key with "Mail Send" permissions
   - Copy the API key

3. **Update Email Configuration**:
   - Via API: `PUT /api/settings/system`
   ```json
   {
     "smtp_server": "smtp.sendgrid.net",
     "smtp_port": 587,
     "smtp_username": "apikey",
     "smtp_password": "your-sendgrid-api-key-here",
     "smtp_from_email": "noreply@yourdomain.com",
     "smtp_from_name": "WorkHub Task Management"
   }
   ```

   - Or via Environment Variables:
   ```bash
   MAIL_SERVER=smtp.sendgrid.net
   MAIL_PORT=587
   MAIL_USERNAME=apikey
   MAIL_PASSWORD=your-sendgrid-api-key
   MAIL_DEFAULT_SENDER=noreply@yourdomain.com
   ```

### Solution 3: Create VPC Connector (If Needed)

If you need VPC connectivity for other services:

```bash
gcloud compute networks vpc-access connectors create workhub-connector \
  --region=us-central1 \
  --network=default \
  --range=10.8.0.0/28

# Then update Cloud Run service
gcloud run services update workhub-backend \
  --region=us-central1 \
  --vpc-connector=workhub-connector \
  --vpc-egress=all-traffic
```

### Solution 4: Check Firewall Rules

Ensure no firewall rules are blocking outbound SMTP (port 587):

```bash
# Check firewall rules
gcloud compute firewall-rules list --filter="direction:EGRESS"
```

## Verification

After applying a fix, test email sending:

1. Sign up a new user
2. Check server logs for:
   - `✓ Verification email sent successfully`
   - Or any error messages

## Current Status

✅ **Email Configuration**: Working (credentials loaded from database)  
❌ **Network Connectivity**: Blocked (cannot reach smtp.gmail.com)  
🔧 **Fix Required**: Update Cloud Run service or use alternative email service

## Recommended Action

**For immediate fix**: Use SendGrid (Solution 2) - it's designed for cloud environments and works reliably with Cloud Run.

**For long-term**: If you need Gmail SMTP, ensure Cloud Run has proper VPC egress configuration.

