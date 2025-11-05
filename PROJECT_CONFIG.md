# WorkHub - GCP Project Configuration

## 🎯 Your Specific Configuration

### GCP Settings
- **Project ID**: `genai-workhub`
- **Region**: `us-central1` (Iowa)
  - **Why us-central1?**: Most cost-effective region with excellent reliability
  - Lower network costs than coastal regions
  - Good balance of performance and price
- **CI/CD**: GitHub Actions (automated on every push to main)
- **Domain**: Cloud Run default URLs (custom domain can be added later)

---

## 📦 Resources That Will Be Created

### 1. Artifact Registry
- **Repository**: `us-central1-docker.pkg.dev/genai-workhub/workhub-repo`
- **Purpose**: Store Docker images
- **Cost**: ~$0.10/GB per month

### 2. Cloud Storage
- **Bucket**: `genai-workhub-workhub-uploads`
- **Purpose**: File uploads storage
- **Location**: `us-central1`
- **Cost**: ~$0.02/GB per month

### 3. Cloud SQL
- **Instance**: `genai-workhub:us-central1:workhub-db`
- **Version**: SQL Server 2022 Standard
- **Tier**: `db-custom-1-3840` (1 vCPU, 3.75 GB RAM)
- **Database**: `workhub`
- **User**: `sqlserver`
- **Backups**: Daily at 3:00 AM, 7-day retention
- **Cost**: ~$180-250/month

### 4. Cloud Run Services

#### Backend
- **Service**: `workhub-backend`
- **URL**: `https://workhub-backend-[hash]-uc.a.run.app`
- **Config**: 
  - 2 vCPU, 2 GB RAM
  - Min instances: 1
  - Max instances: 10
  - Timeout: 300s
- **Cost**: ~$25-50/month

#### Frontend
- **Service**: `workhub-frontend`
- **URL**: `https://workhub-frontend-[hash]-uc.a.run.app`
- **Config**:
  - 1 vCPU, 512 MB RAM
  - Min instances: 1
  - Max instances: 5
  - Timeout: 60s
- **Cost**: ~$15-30/month

### 5. Service Account
- **Email**: `workhub-cloud-run-sa@genai-workhub.iam.gserviceaccount.com`
- **Roles**:
  - Cloud SQL Client
  - Storage Object Admin
  - Secret Manager Secret Accessor

### 6. Secrets (in Secret Manager)
- `workhub-db-password`
- `workhub-secret-key`
- `workhub-jwt-secret`
- `workhub-mail-password`

---

## 💰 Total Estimated Monthly Cost

| Resource | Cost Range |
|----------|-----------|
| Cloud SQL | $180-250 |
| Cloud Run (Backend) | $25-50 |
| Cloud Run (Frontend) | $15-30 |
| Cloud Storage | $2-10 |
| Artifact Registry | $1-5 |
| Networking | $5-10 |
| **Total** | **$228-355** |

**Note**: Actual costs depend on:
- Number of requests
- Data storage volume
- Egress traffic
- Instance uptime

---

## 🔑 GitHub Secrets Configuration

Add these to: **GitHub Repository → Settings → Secrets and variables → Actions**

### Core Secrets (Set Before First Deploy)
```
GCP_PROJECT_ID=genai-workhub
GCP_REGION=us-central1
GCP_SA_KEY=<paste entire JSON from service account key>
CLOUD_SQL_CONNECTION_NAME=genai-workhub:us-central1:workhub-db
CLOUD_STORAGE_BUCKET=genai-workhub-workhub-uploads
GCP_SERVICE_ACCOUNT_EMAIL=workhub-cloud-run-sa@genai-workhub.iam.gserviceaccount.com
DB_USER=sqlserver
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=<your-email>
MAIL_DEFAULT_SENDER=<your-sender-email>
```

### Update After First Deploy
```
BACKEND_URL=<actual-backend-url>
FRONTEND_URL=<actual-frontend-url>
ALLOWED_ORIGINS=<actual-frontend-url>
```

---

## 📋 Deployment Commands

### Initial Setup (Run Once)
```bash
# Set project
export GCP_PROJECT_ID="genai-workhub"
export GCP_REGION="us-central1"

# Run setup
bash scripts/setup-gcp.sh
```

### Create Service Account Key (Run Once)
```bash
gcloud iam service-accounts keys create github-actions-key.json \
  --iam-account=workhub-cloud-run-sa@genai-workhub.iam.gserviceaccount.com

cat github-actions-key.json  # Copy this to GitHub
rm github-actions-key.json   # Delete after copying
```

### Deploy (Automatic via GitHub Actions)
```bash
git push origin main  # Triggers automatic deployment
```

### Manual Deploy (If Needed)
```bash
bash scripts/deploy-gcp.sh
```

---

## 🔍 Verification Commands

### After Setup
```bash
# Verify project is active
gcloud config get-value project

# List enabled APIs
gcloud services list --enabled

# Check Cloud SQL instance
gcloud sql instances describe workhub-db

# Check storage bucket
gsutil ls gs://genai-workhub-workhub-uploads/

# Check Artifact Registry
gcloud artifacts repositories describe workhub-repo --location=us-central1
```

### After Deployment
```bash
# Get service URLs
gcloud run services describe workhub-backend --region us-central1 --format='value(status.url)'
gcloud run services describe workhub-frontend --region us-central1 --format='value(status.url)'

# Test backend health
curl https://workhub-backend-[hash]-uc.a.run.app/api/health

# View logs
gcloud logging read "resource.type=cloud_run_revision" --limit 50
```

---

## 🛠️ Management Commands

### View Resources
```bash
# All Cloud Run services
gcloud run services list --region us-central1

# Cloud SQL instances
gcloud sql instances list

# Storage buckets
gsutil ls

# Secrets
gcloud secrets list

# Service accounts
gcloud iam service-accounts list
```

### Monitoring
```bash
# Recent errors
gcloud logging read "severity>=ERROR" --limit 20

# Backend logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=workhub-backend" --limit 50

# Frontend logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=workhub-frontend" --limit 50
```

### Cost Analysis
```bash
# View billing info
gcloud beta billing projects describe genai-workhub

# Export billing data
gcloud beta billing budgets list --billing-account=YOUR_BILLING_ACCOUNT_ID
```

---

## 🚀 Deployment Workflow

### Automatic (GitHub Actions)
1. Developer pushes to `main` branch
2. GitHub Actions triggered automatically
3. Builds backend and frontend Docker images
4. Pushes images to Artifact Registry
5. Deploys to Cloud Run
6. Runs health checks
7. Sends notification (success/failure)

**Total time**: 5-8 minutes per deployment

---

## 🔒 Security Configuration

### IAM Roles (Service Account)
- `roles/cloudsql.client` - Database access
- `roles/storage.objectAdmin` - File uploads
- `roles/secretmanager.secretAccessor` - Read secrets

### Network Security
- All Cloud Run services use HTTPS only
- Cloud SQL accessible only via Unix socket (secure)
- Storage bucket with IAM-based access control
- Secrets stored in Secret Manager (encrypted at rest)

### Best Practices Applied
✅ Non-root users in containers  
✅ Least-privilege IAM roles  
✅ Secrets never in code  
✅ Health checks configured  
✅ Automatic backups enabled  
✅ Audit logging enabled  

---

## 📊 Monitoring & Alerts

### Recommended Alerts
Set up alerts for:
- Error rate > 5%
- P95 latency > 2 seconds
- Database CPU > 80%
- Storage usage > 80GB
- Monthly cost > $300

### Dashboards
Access monitoring at:
- https://console.cloud.google.com/monitoring/dashboards?project=genai-workhub
- https://console.cloud.google.com/run?project=genai-workhub
- https://console.cloud.google.com/sql/instances?project=genai-workhub

---

## 🔄 Update Procedures

### Update Environment Variables
```bash
gcloud run services update workhub-backend \
  --region us-central1 \
  --update-env-vars NEW_VAR=value
```

### Update Secrets
```bash
# Add new version
echo -n "new-secret-value" | gcloud secrets versions add SECRET_NAME --data-file=-

# Update Cloud Run to use latest
gcloud run services update workhub-backend \
  --region us-central1 \
  --update-secrets SECRET_NAME=SECRET_NAME:latest
```

### Scale Services
```bash
# Scale backend
gcloud run services update workhub-backend \
  --region us-central1 \
  --min-instances 2 \
  --max-instances 20 \
  --memory 4Gi \
  --cpu 4
```

---

## 🆘 Quick Troubleshooting

### Issue: Deployment Fails
```bash
# Check GitHub Actions logs
# Go to: https://github.com/your-repo/actions

# Check GCP logs
gcloud logging read "severity>=ERROR" --limit 20
```

### Issue: Can't Connect to Database
```bash
# Check instance status
gcloud sql instances describe workhub-db --format='value(state)'

# Test connection
gcloud sql connect workhub-db --user=sqlserver
```

### Issue: File Uploads Fail
```bash
# Check bucket
gsutil ls gs://genai-workhub-workhub-uploads/

# Check permissions
gsutil iam get gs://genai-workhub-workhub-uploads/
```

---

## 📞 Support Resources

- **GCP Console**: https://console.cloud.google.com/home/dashboard?project=genai-workhub
- **Cloud Run**: https://console.cloud.google.com/run?project=genai-workhub
- **Cloud SQL**: https://console.cloud.google.com/sql?project=genai-workhub
- **Monitoring**: https://console.cloud.google.com/monitoring?project=genai-workhub
- **Billing**: https://console.cloud.google.com/billing

---

## ✅ Ready to Deploy!

Your configuration is complete and ready for deployment.

**Next Steps**:
1. Review `QUICK_START_DEPLOYMENT.md` for step-by-step instructions
2. Run `bash scripts/setup-gcp.sh`
3. Add GitHub secrets
4. Push to main branch

---

**Project**: genai-workhub  
**Region**: us-central1  
**Status**: ✅ Configured and ready  
**Created**: November 2025

