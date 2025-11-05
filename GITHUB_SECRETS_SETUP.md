# GitHub Secrets Setup Guide

## 📍 How to Add Secrets to GitHub

1. Navigate to your repository on GitHub
2. Click **Settings** (top menu)
3. In the left sidebar, click **Secrets and variables** → **Actions**
4. Click **New repository secret**
5. Add each secret below

---

## 🔑 Required Secrets (12 Total)

### 1. GCP_PROJECT_ID
**Value**: Your Google Cloud Project ID  
**Example**: `workhub-production-2025`  
**How to get**:
```bash
gcloud config get-value project
```

---

### 2. GCP_REGION
**Value**: GCP region for deployment  
**Example**: `us-central1`  
**Common options**:
- `us-central1` (Iowa)
- `us-east1` (South Carolina)
- `us-west1` (Oregon)
- `europe-west1` (Belgium)
- `asia-southeast1` (Singapore)

---

### 3. GCP_SA_KEY
**Value**: Service Account JSON key (entire JSON content)  
**How to get**:
```bash
# Create key
gcloud iam service-accounts keys create key.json \
  --iam-account=workhub-cloud-run-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com

# Display key (copy entire output)
cat key.json

# Delete file after copying
rm key.json
```
**Example format**:
```json
{
  "type": "service_account",
  "project_id": "your-project",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...",
  "client_email": "workhub-cloud-run-sa@...",
  ...
}
```

---

### 4. CLOUD_SQL_CONNECTION_NAME
**Value**: Cloud SQL instance connection name  
**Format**: `PROJECT_ID:REGION:INSTANCE_NAME`  
**Example**: `workhub-prod-2025:us-central1:workhub-db`  
**How to get**:
```bash
gcloud sql instances describe workhub-db --format='value(connectionName)'
```

---

### 5. CLOUD_STORAGE_BUCKET
**Value**: Cloud Storage bucket name for file uploads  
**Example**: `workhub-uploads-prod-2025`  
**How to get**:
```bash
gsutil ls | grep workhub
```

---

### 6. GCP_SERVICE_ACCOUNT_EMAIL
**Value**: Service account email address  
**Example**: `workhub-cloud-run-sa@your-project.iam.gserviceaccount.com`  
**How to get**:
```bash
gcloud iam service-accounts list | grep workhub
```

---

### 7. DB_USER
**Value**: Database username  
**Example**: `sqlserver`  
**Note**: Set during Cloud SQL setup

---

### 8. BACKEND_URL
**Value**: Backend Cloud Run URL  
**Example**: `https://workhub-backend-abc123-uc.a.run.app`  
**How to get** (after first deployment):
```bash
gcloud run services describe workhub-backend \
  --region us-central1 \
  --format 'value(status.url)'
```
**Initial value**: Leave empty for first deployment, update after

---

### 9. FRONTEND_URL
**Value**: Frontend Cloud Run URL  
**Example**: `https://workhub-frontend-xyz789-uc.a.run.app`  
**How to get** (after first deployment):
```bash
gcloud run services describe workhub-frontend \
  --region us-central1 \
  --format 'value(status.url)'
```
**Initial value**: Leave empty for first deployment, update after

---

### 10. ALLOWED_ORIGINS
**Value**: Comma-separated list of allowed CORS origins  
**Example**: `https://workhub-frontend-xyz789-uc.a.run.app,https://app.yourdomain.com`  
**Format**: `URL1,URL2,URL3` (no spaces)  
**Initial value**: `*` (allow all - update after first deployment)

---

### 11. MAIL_SERVER
**Value**: SMTP server hostname  
**Examples**:
- Gmail: `smtp.gmail.com`
- SendGrid: `smtp.sendgrid.net`
- Mailgun: `smtp.mailgun.org`
- Office 365: `smtp.office365.com`

---

### 12. MAIL_PORT
**Value**: SMTP server port  
**Common values**:
- `587` (TLS - recommended)
- `465` (SSL)
- `25` (unencrypted - not recommended)

---

### 13. MAIL_USERNAME
**Value**: Email account username / email address  
**Example**: `notifications@yourdomain.com`  
**Note**: For Gmail, may need app-specific password

---

### 14. MAIL_DEFAULT_SENDER
**Value**: Default "From" email address  
**Example**: `WorkHub Notifications <noreply@yourdomain.com>`  
**Format**: Can be just email or "Name <email>"

---

## 📝 Quick Copy-Paste Checklist

Use this checklist when adding secrets:

```
□ GCP_PROJECT_ID
□ GCP_REGION
□ GCP_SA_KEY
□ CLOUD_SQL_CONNECTION_NAME
□ CLOUD_STORAGE_BUCKET
□ GCP_SERVICE_ACCOUNT_EMAIL
□ DB_USER
□ BACKEND_URL (update after first deployment)
□ FRONTEND_URL (update after first deployment)
□ ALLOWED_ORIGINS (update after first deployment)
□ MAIL_SERVER
□ MAIL_PORT
□ MAIL_USERNAME
□ MAIL_DEFAULT_SENDER
```

---

## 🔒 Security Best Practices

1. **Never commit secrets to Git**
   - Always use GitHub Secrets
   - Don't hardcode in code
   - Don't include in documentation

2. **Rotate secrets regularly**
   - Every 90 days minimum
   - After team member departure
   - If potentially compromised

3. **Use least privilege**
   - Service account has only needed permissions
   - Separate accounts for dev/prod

4. **Monitor access**
   - Review audit logs regularly
   - Set up alerts for unauthorized access

5. **Backup secrets securely**
   - Store separately from code
   - Use password manager
   - Document recovery process

---

## 🧪 Testing Secrets

After adding all secrets:

1. **Trigger a test deployment**:
   ```bash
   git commit --allow-empty -m "Test deployment"
   git push origin main
   ```

2. **Monitor GitHub Actions**:
   - Go to **Actions** tab
   - Click on running workflow
   - Watch for any "secret not found" errors

3. **Common issues**:
   - Secret name typo
   - Missing secret
   - Incorrect secret value format
   - JSON formatting issues (for GCP_SA_KEY)

---

## 📋 Verification Commands

After deployment, verify secrets are working:

### Backend verification
```bash
# Check environment variables are set
gcloud run services describe workhub-backend \
  --region us-central1 \
  --format 'value(spec.template.spec.containers[0].env)'

# Check secrets are mounted
gcloud run services describe workhub-backend \
  --region us-central1 \
  --format 'value(spec.template.spec.containers[0].env.secretRef)'
```

### Test connectivity
```bash
# Backend health
curl https://BACKEND_URL/api/health

# Should return: {"status":"healthy","message":"Work Hub API is running"}
```

---

## 🆘 Troubleshooting

### Secret not found error
**Solution**: Verify secret name matches exactly (case-sensitive)

### JSON parsing error (GCP_SA_KEY)
**Solution**: 
1. Ensure entire JSON is copied (including braces)
2. No extra spaces or newlines
3. Use the exact output from `cat key.json`

### Permission denied
**Solution**: 
1. Verify service account has required IAM roles
2. Check GCP APIs are enabled
3. Ensure secret is set correctly

### Deployment succeeds but app doesn't work
**Solution**:
1. Check Cloud Run logs for errors
2. Verify all secrets are accessible
3. Test database connection
4. Verify storage bucket permissions

---

## 📞 Need Help?

1. **Check deployment logs**:
   - GitHub Actions → View workflow run
   - Cloud Console → Cloud Run → Logs

2. **Common commands**:
   ```bash
   # List secrets
   gcloud secrets list
   
   # View secret versions
   gcloud secrets versions list SECRET_NAME
   
   # Grant access to service account
   gcloud secrets add-iam-policy-binding SECRET_NAME \
     --member="serviceAccount:EMAIL" \
     --role="roles/secretmanager.secretAccessor"
   ```

3. **Documentation**:
   - See `DEPLOYMENT_GCP.md` for full guide
   - See `CI_CD_README.md` for quick start

---

## ✅ Final Checklist

Before first deployment:

- [ ] All 14 secrets added to GitHub
- [ ] Service account key created and added
- [ ] GCP setup script completed successfully
- [ ] Cloud SQL instance is running
- [ ] Storage bucket exists
- [ ] Artifact Registry repository created
- [ ] GitHub Actions workflow file exists
- [ ] Test push triggers workflow

**Status**: Ready to deploy when all checked ✅

---

**Last Updated**: November 2025  
**Version**: 1.0.0

