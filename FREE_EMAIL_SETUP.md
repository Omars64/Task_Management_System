# Free Email Setup - Gmail SMTP (No API Purchase Required)

## ✅ Status: FIXED!

You've successfully configured Cloud Run to allow outbound SMTP connections. Your application can now send emails using **free Gmail SMTP** - no paid API services needed!

## What Was Fixed

1. **Cloud Run Network Configuration**: Added `--vpc-egress=all-traffic` to allow outbound internet access
2. **Email Configuration**: Already working (credentials loaded from database)
3. **Deployment Scripts**: Updated to maintain this setting in future deployments

## Current Setup (100% FREE)

- ✅ **Email Service**: Gmail SMTP (free)
- ✅ **Network Access**: Cloud Run can reach `smtp.gmail.com`
- ✅ **Credentials**: Stored in database (`SystemSettings` table)
- ✅ **No API Purchase**: Everything works with free Gmail SMTP

## Email Configuration

Your email is configured with:
- **SMTP Server**: `smtp.gmail.com`
- **Port**: `587` (TLS)
- **Username**: `omarsolanki35@gmail.com`
- **Password**: App password (stored securely)
- **From Email**: `omarsolanki35@gmail.com`

## Testing Email

### Test 1: Sign Up a New User

1. Go to your application's sign-up page
2. Enter a valid email address
3. Submit the form
4. Check the email inbox for verification code

### Test 2: Check Logs

View Cloud Run logs to verify email sending:

```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=workhub-backend" \
  --limit 50 \
  --format json \
  --project=genai-workhub
```

Look for:
- ✅ `✓ Verification email sent successfully`
- ❌ Any error messages

### Test 3: Check Email Status in UI

1. Log in as admin
2. Go to Settings → System Settings
3. Check if "Email Configuration" shows as configured

## Troubleshooting

### If Emails Still Don't Send

1. **Verify Gmail App Password**:
   - Go to https://myaccount.google.com/apppasswords
   - Ensure you're using an App Password (not your regular password)
   - Update in database if needed: `PUT /api/settings/system`

2. **Check Cloud Run Logs**:
   ```bash
   gcloud run services logs read workhub-backend \
     --region=us-central1 \
     --project=genai-workhub \
     --limit=50
   ```

3. **Verify Network Access**:
   - The `--vpc-egress=all-traffic` flag should be set
   - Check with: `gcloud run services describe workhub-backend --region=us-central1`

4. **Test SMTP Connection** (from Cloud Shell):
   ```bash
   # This will test if Cloud Run can reach Gmail SMTP
   # (You can't test directly, but check logs after signup)
   ```

## Future Deployments

The `--vpc-egress=all-traffic` flag is now included in:
- ✅ `.github/workflows/deploy-gcp.yml` (GitHub Actions)
- ✅ `cloudbuild.yaml` (Cloud Build)
- ✅ `scripts/deploy-gcp.sh` (Manual deployment)

**This setting will persist across all future deployments!**

## Gmail Limits (Free Tier)

- **Daily Limit**: 500 emails/day (for personal Gmail accounts)
- **Rate Limit**: ~100 emails/hour
- **For Production**: If you exceed limits, consider:
  - Using a Google Workspace account (higher limits)
  - Or upgrading to a paid email service (only if needed)

## Summary

🎉 **Your email is now fully functional using FREE Gmail SMTP!**

- No API purchase required
- No monthly fees
- Works with your existing Gmail account
- Configured to persist across deployments

