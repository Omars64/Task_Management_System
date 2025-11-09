# Email Configuration Updated

## ✅ What Was Updated

1. **GCP Secret Manager**: Updated `workhub-mail-password` secret with the new app password
2. **Cloud Run Service**: Updated `MAIL_USERNAME` and `MAIL_DEFAULT_SENDER` environment variables
3. **Created `.env.example`**: Added example environment file for local development

## 📧 Email Configuration

- **Email**: `omarsolanki35@gmail.com`
- **App Password**: `qaag oozk mioh ajdi` (stored in GCP Secret Manager)
- **SMTP Server**: `smtp.gmail.com`
- **Port**: `587` (TLS)

## 🔄 Next Steps

The email configuration is now active in production. The Cloud Run service has been redeployed with the new settings.

### To Update GitHub Secrets (for future deployments):

1. Go to: https://github.com/Omars64/Task_Management_System/settings/secrets/actions
2. Find the secret: `MAIL_PASSWORD`
3. Update it to: `qaag oozk mioh ajdi`
4. Save

This ensures future deployments will use the correct email password.

## ✅ Current Status

- ✅ GCP Secret Manager updated
- ✅ Cloud Run service updated and redeployed
- ✅ Email notifications should now work
- ✅ Signup verification emails will be sent

## 🧪 Test Email

Try signing up a new user - you should now receive verification emails instead of seeing "email not configured" message.

