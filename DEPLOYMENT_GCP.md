# 🚀 WorkHub - GCP Deployment Guide

Complete guide for deploying WorkHub to Google Cloud Platform with automated CI/CD.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Initial Setup](#initial-setup)
- [Deployment Methods](#deployment-methods)
- [Configuration](#configuration)
- [Post-Deployment](#post-deployment)
- [Monitoring & Maintenance](#monitoring--maintenance)
- [Troubleshooting](#troubleshooting)
- [Cost Optimization](#cost-optimization)

---

## 🎯 Overview

WorkHub is deployed on GCP using:
- **Cloud Run** (serverless containers for frontend & backend)
- **Cloud SQL** (managed SQL Server database)
- **Cloud Storage** (file uploads storage)
- **Artifact Registry** (Docker image storage)
- **Secret Manager** (secure credential management)
- **GitHub Actions** or **Cloud Build** (CI/CD automation)

**Estimated Monthly Cost**: $250-400 USD (varies with usage)

---

## 🏗️ Architecture

```
┌─────────────────┐
│   GitHub Repo   │
└────────┬────────┘
         │
         ├───[Push to main]────►  GitHub Actions / Cloud Build
         │                              │
         ▼                              ▼
┌─────────────────────────┐    ┌──────────────────┐
│   Artifact Registry     │◄───┤  Build Images    │
│  (Docker Images)        │    └──────────────────┘
└────────┬────────────────┘
         │
         ├─────────────────────────────────┐
         │                                  │
         ▼                                  ▼
┌──────────────────┐              ┌──────────────────┐
│  Cloud Run       │              │  Cloud Run       │
│  (Backend API)   │◄────────────►│  (Frontend)      │
│  • Python/Flask  │              │  • React/Nginx   │
│  • Gunicorn      │              │  • Vite          │
│  • 2 vCPU/2GB    │              │  • 1 vCPU/512MB  │
└────────┬─────────┘              └──────────────────┘
         │
         ├─────────────┬─────────────┐
         │             │             │
         ▼             ▼             ▼
┌──────────────┐  ┌─────────┐  ┌─────────────┐
│  Cloud SQL   │  │ Secret  │  │   Cloud     │
│  (SQL Server)│  │ Manager │  │  Storage    │
│  • 1vCPU     │  │         │  │  (Uploads)  │
│  • 3.75GB    │  └─────────┘  └─────────────┘
└──────────────┘
```

---

## ✅ Prerequisites

### 1. GCP Account
- Active GCP project with billing enabled
- Project ID ready (e.g., `workhub-production-2025`)

### 2. Local Tools
```bash
# Install gcloud CLI
# https://cloud.google.com/sdk/docs/install

# Install Docker
# https://docs.docker.com/get-docker/

# Verify installations
gcloud --version
docker --version
```

### 3. GitHub Repository
- Repository with WorkHub code
- Admin access to configure secrets

### 4. Domain (Optional)
- Custom domain for production
- DNS management access

---

## 🛠️ Initial Setup

### Step 1: Run Automated Setup Script

```bash
# Clone repository
git clone https://github.com/your-org/workhub.git
cd workhub

# Set your GCP project ID and region
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="us-central1"

# Run setup script
bash scripts/setup-gcp.sh
```

The script will:
✅ Enable required GCP APIs  
✅ Create Artifact Registry repository  
✅ Create Cloud Storage bucket  
✅ Create Cloud SQL instance  
✅ Create database and user  
✅ Create service account with proper IAM roles  
✅ Generate and store secrets in Secret Manager  

**Duration**: ~15-20 minutes (Cloud SQL takes the longest)

### Step 2: Create Service Account Key for GitHub Actions

```bash
# Create service account key
gcloud iam service-accounts keys create github-actions-key.json \
  --iam-account=workhub-cloud-run-sa@${GCP_PROJECT_ID}.iam.gserviceaccount.com

# Display key (copy this)
cat github-actions-key.json
```

⚠️ **Important**: Delete this key file after copying to GitHub:
```bash
rm github-actions-key.json
```

### Step 3: Configure GitHub Secrets

Navigate to: **GitHub Repo → Settings → Secrets and variables → Actions**

Add these secrets:

| Secret Name | Value | Example |
|------------|-------|---------|
| `GCP_PROJECT_ID` | Your GCP project ID | `workhub-prod-2025` |
| `GCP_REGION` | Deployment region | `us-central1` |
| `GCP_SA_KEY` | Service account JSON key | `{...entire JSON...}` |
| `CLOUD_SQL_CONNECTION_NAME` | Cloud SQL connection | `project:region:instance` |
| `CLOUD_STORAGE_BUCKET` | Storage bucket name | `workhub-uploads-prod` |
| `GCP_SERVICE_ACCOUNT_EMAIL` | Service account email | `workhub-cloud-run-sa@...` |
| `DB_USER` | Database username | `sqlserver` |
| `BACKEND_URL` | Backend URL (after first deploy) | `https://workhub-backend-xxx.a.run.app` |
| `FRONTEND_URL` | Frontend URL (after first deploy) | `https://workhub-frontend-xxx.a.run.app` |
| `ALLOWED_ORIGINS` | Comma-separated allowed origins | `https://app.yourdomain.com` |
| `MAIL_SERVER` | SMTP server | `smtp.gmail.com` |
| `MAIL_PORT` | SMTP port | `587` |
| `MAIL_USERNAME` | Email username | `noreply@yourdomain.com` |
| `MAIL_DEFAULT_SENDER` | Default sender email | `WorkHub <noreply@yourdomain.com>` |

---

## 🚢 Deployment Methods

### Method 1: Automated CI/CD (Recommended)

**GitHub Actions** (`.github/workflows/deploy-gcp.yml`)

```bash
# Simply push to main branch
git add .
git commit -m "Deploy to production"
git push origin main

# GitHub Actions will automatically:
# 1. Build Docker images
# 2. Push to Artifact Registry
# 3. Deploy to Cloud Run
# 4. Run health checks
```

**Monitoring the deployment**:
- Go to GitHub → Actions tab
- Watch the deployment progress
- Check for any errors

### Method 2: Google Cloud Build

**Trigger from repository**:
```bash
# Submit build manually
gcloud builds submit --config cloudbuild.yaml

# Or set up automatic trigger
gcloud builds triggers create github \
  --name=workhub-deploy \
  --repo-name=workhub \
  --repo-owner=your-github-org \
  --branch-pattern="^main$" \
  --build-config=cloudbuild.yaml
```

### Method 3: Manual Deployment

```bash
# Run manual deployment script
bash scripts/deploy-gcp.sh
```

---

## ⚙️ Configuration

### Environment Variables

**Backend (Cloud Run)**:
```
CLOUD_SQL_CONNECTION_NAME=project:region:instance
DB_NAME=workhub
DB_USER=sqlserver
DB_DIALECT=mssql
USE_CLOUD_STORAGE=true
CLOUD_STORAGE_BUCKET=workhub-uploads
GCP_PROJECT=your-project-id
ALLOWED_ORIGINS=https://yourdomain.com
FRONTEND_URL=https://workhub-frontend-xxx.a.run.app
EMAIL_NOTIFICATIONS_ENABLED=true
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_DEFAULT_SENDER=noreply@yourdomain.com
```

**Secrets (Secret Manager)**:
- `workhub-db-password`
- `workhub-secret-key`
- `workhub-jwt-secret`
- `workhub-mail-password`

### Scaling Configuration

**Backend**:
- Min instances: 1
- Max instances: 10
- Memory: 2 GB
- CPU: 2
- Timeout: 300s

**Frontend**:
- Min instances: 1
- Max instances: 5
- Memory: 512 MB
- CPU: 1
- Timeout: 60s

**Modify scaling**:
```bash
gcloud run services update workhub-backend \
  --region us-central1 \
  --min-instances 2 \
  --max-instances 20
```

---

## 🔒 Security Best Practices

### 1. Secrets Management
✅ Use Secret Manager (never hardcode)  
✅ Rotate secrets every 90 days  
✅ Use least-privilege IAM roles  

### 2. Network Security
✅ Use Private IP for Cloud SQL  
✅ Enable VPC Service Controls  
✅ Use Cloud Armor for DDoS protection  

### 3. Authentication
✅ Enforce HTTPS only  
✅ Use JWT with short expiration  
✅ Implement rate limiting  

### 4. Data Protection
✅ Enable Cloud SQL automatic backups  
✅ Enable versioning on Cloud Storage  
✅ Enable audit logging  

---

## 📊 Post-Deployment

### 1. Get Service URLs

```bash
# Backend URL
gcloud run services describe workhub-backend \
  --region us-central1 \
  --format 'value(status.url)'

# Frontend URL
gcloud run services describe workhub-frontend \
  --region us-central1 \
  --format 'value(status.url)'
```

### 2. Test the Deployment

```bash
# Health check
curl https://workhub-backend-xxx.a.run.app/api/health

# Should return: {"status":"healthy","message":"Work Hub API is running"}
```

### 3. Database Migration

```bash
# Access Cloud SQL
gcloud sql connect workhub-db --user=sqlserver

# Run init_db script (first time only)
gcloud run services update workhub-backend \
  --region us-central1 \
  --command python,init_db.py
```

### 4. Create Super Admin

```bash
# SSH into a Cloud Run instance
gcloud run services exec workhub-backend \
  --region us-central1 \
  -- python scripts/promote_user.py <user_id>
```

### 5. Configure Custom Domain

```bash
# Map custom domain
gcloud run services update workhub-frontend \
  --region us-central1 \
  --domain app.yourdomain.com

# Update DNS records as instructed
# GCP will provision SSL certificate automatically
```

---

## 📈 Monitoring & Maintenance

### Monitoring Dashboard

Access: [GCP Console → Monitoring](https://console.cloud.google.com/monitoring)

**Key Metrics**:
- Request count & latency
- Error rate (4xx, 5xx)
- Instance count
- Memory & CPU usage
- Database connections

### Logging

```bash
# View backend logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=workhub-backend" \
  --limit 50 \
  --format json

# View frontend logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=workhub-frontend" \
  --limit 50 \
  --format json

# Filter by severity
gcloud logging read "resource.type=cloud_run_revision AND severity>=ERROR" \
  --limit 20
```

### Alerts

**Set up alerts for**:
- Error rate > 5%
- Latency p95 > 2 seconds
- Instance count maxed out
- Database CPU > 80%

```bash
# Create alert policy
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="WorkHub Error Rate Alert" \
  --condition-display-name="Error rate > 5%" \
  --condition-threshold-value=0.05 \
  --condition-duration=300s
```

### Backups

**Cloud SQL Backups** (automatic):
- Daily at 3:00 AM
- Retained for 7 days
- Binary logs enabled for point-in-time recovery

**Manual backup**:
```bash
gcloud sql backups create --instance=workhub-db
```

**Restore from backup**:
```bash
gcloud sql backups restore BACKUP_ID --backup-instance=workhub-db
```

---

## 🐛 Troubleshooting

### Issue: Deployment fails with "Permission Denied"

**Solution**:
```bash
# Grant necessary IAM roles
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:SERVICE_ACCOUNT_EMAIL" \
  --role="roles/run.admin"
```

### Issue: Database connection fails

**Solution**:
```bash
# Verify Cloud SQL instance is running
gcloud sql instances describe workhub-db

# Check connection name is correct
gcloud sql instances describe workhub-db \
  --format 'value(connectionName)'

# Test connectivity
gcloud sql connect workhub-db --user=sqlserver
```

### Issue: File uploads fail

**Solution**:
```bash
# Verify storage bucket exists
gsutil ls gs://BUCKET_NAME

# Check IAM permissions
gsutil iam get gs://BUCKET_NAME

# Grant storage admin role
gsutil iam ch serviceAccount:SERVICE_ACCOUNT_EMAIL:objectAdmin gs://BUCKET_NAME
```

### Issue: Frontend shows API errors

**Solution**:
```bash
# Check CORS configuration
gcloud run services describe workhub-backend --region us-central1 \
  --format 'value(spec.template.spec.containers[0].env)'

# Update ALLOWED_ORIGINS
gcloud run services update workhub-backend \
  --region us-central1 \
  --update-env-vars ALLOWED_ORIGINS=https://your-frontend-url.com
```

### Issue: High latency

**Solution**:
```bash
# Increase min instances to reduce cold starts
gcloud run services update workhub-backend \
  --region us-central1 \
  --min-instances 2

# Increase CPU/memory
gcloud run services update workhub-backend \
  --region us-central1 \
  --memory 4Gi \
  --cpu 4
```

---

## 💰 Cost Optimization

### Current Cost Breakdown

| Service | Est. Monthly Cost |
|---------|------------------|
| Cloud Run (Backend) | $25-50 |
| Cloud Run (Frontend) | $15-30 |
| Cloud SQL | $180-250 |
| Cloud Storage | $5-20 |
| Artifact Registry | $1-5 |
| **Total** | **$250-400** |

### Optimization Tips

1. **Use min instances wisely**
   - Development: 0 min instances
   - Production: 1-2 min instances
   - Peak hours: Scale up

2. **Database tier**
   - Start with `db-custom-1-3840`
   - Monitor usage and adjust
   - Consider read replicas for high traffic

3. **Storage**
   - Enable lifecycle policies
   - Delete old files periodically
   - Use nearline/coldline for backups

4. **Networking**
   - Use Cloud CDN for static assets
   - Enable compression
   - Optimize images

5. **Development Environment**
   ```bash
   # Use smaller instances for dev
   gcloud run services update workhub-backend-dev \
     --region us-central1 \
     --memory 1Gi \
     --cpu 1 \
     --min-instances 0
   ```

---

## 📚 Additional Resources

- [GCP Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud SQL Best Practices](https://cloud.google.com/sql/docs/best-practices)
- [Secret Manager Guide](https://cloud.google.com/secret-manager/docs)
- [Cloud Build Documentation](https://cloud.google.com/build/docs)
- [GitHub Actions for GCP](https://github.com/google-github-actions)

---

## 🆘 Support

**Issues**: Open an issue on GitHub  
**Email**: support@workhub.com  
**Documentation**: https://docs.workhub.com

---

**Last Updated**: November 2025  
**Version**: 1.0.0

