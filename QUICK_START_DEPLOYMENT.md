# 🚀 WorkHub - Quick Start Deployment Guide

## Your Project Configuration

- **GCP Project ID**: `genai-workhub`
- **Region**: `us-central1` (Iowa - Cost-effective with good reliability)
- **CI/CD Method**: GitHub Actions
- **Domain**: Cloud Run default URLs (no custom domain initially)

---

## ⚡ Quick Start (30 minutes)

### Step 1: Prerequisites Check (5 min)

```bash
# Verify gcloud is installed
gcloud --version

# Verify Docker is installed
docker --version

# Login to GCP
gcloud auth login

# Set project
gcloud config set project genai-workhub

# Verify project is set
gcloud config get-value project
# Should output: genai-workhub
```

---

### Step 2: Run Automated Setup (15-20 min)

```bash
# Navigate to your project directory
cd /path/to/workhub

# Run the setup script
bash scripts/setup-gcp.sh
```

**What this does**:
- ✅ Enables all required GCP APIs
- ✅ Creates Artifact Registry (`us-central1-docker.pkg.dev/genai-workhub/workhub-repo`)
- ✅ Creates Cloud Storage bucket (`genai-workhub-workhub-uploads`)
- ✅ Creates Cloud SQL instance (`genai-workhub:us-central1:workhub-db`)
- ✅ Creates database `workhub` and user `sqlserver`
- ✅ Creates service account `workhub-cloud-run-sa@genai-workhub.iam.gserviceaccount.com`
- ✅ Stores secrets in Secret Manager
- ✅ Configures IAM permissions

**Note**: Cloud SQL creation takes the longest (~15 minutes)

---

### Step 3: Create Service Account Key for GitHub (2 min)

```bash
# Create the key
gcloud iam service-accounts keys create github-actions-key.json \
  --iam-account=workhub-cloud-run-sa@genai-workhub.iam.gserviceaccount.com

# Display the key (copy this entire output)
cat github-actions-key.json

# IMPORTANT: Delete the file after copying to GitHub
rm github-actions-key.json
```

---

### Step 4: Configure GitHub Secrets (5 min)

Go to: **GitHub Repository → Settings → Secrets and variables → Actions → New repository secret**

Add these **14 secrets**:

| Secret Name | Your Value |
|------------|------------|
| `GCP_PROJECT_ID` | `genai-workhub` |
| `GCP_REGION` | `us-central1` |
| `GCP_SA_KEY` | *Paste entire JSON from above* |
| `CLOUD_SQL_CONNECTION_NAME` | `genai-workhub:us-central1:workhub-db` |
| `CLOUD_STORAGE_BUCKET` | `genai-workhub-workhub-uploads` |
| `GCP_SERVICE_ACCOUNT_EMAIL` | `workhub-cloud-run-sa@genai-workhub.iam.gserviceaccount.com` |
| `DB_USER` | `sqlserver` |
| `BACKEND_URL` | *Leave empty initially - update after first deploy* |
| `FRONTEND_URL` | *Leave empty initially - update after first deploy* |
| `ALLOWED_ORIGINS` | `*` *Update after first deploy with actual URLs* |
| `MAIL_SERVER` | `smtp.gmail.com` *(or your SMTP server)* |
| `MAIL_PORT` | `587` |
| `MAIL_USERNAME` | *Your email* |
| `MAIL_DEFAULT_SENDER` | *Your sender email* |

---

### Step 5: Deploy! (5-10 min)

```bash
# Commit all changes (if not already done)
git add .
git commit -m "Add GCP deployment configuration"

# Push to trigger GitHub Actions
git push origin main
```

**Monitor deployment**:
1. Go to GitHub → Actions tab
2. Watch the workflow run
3. Wait for green checkmarks ✅

---

### Step 6: Get Your URLs (1 min)

After successful deployment:

```bash
# Get backend URL
gcloud run services describe workhub-backend \
  --region us-central1 \
  --format 'value(status.url)'

# Get frontend URL
gcloud run services describe workhub-frontend \
  --region us-central1 \
  --format 'value(status.url)'
```

**Example URLs you'll get**:
- Backend: `https://workhub-backend-abc123xyz-uc.a.run.app`
- Frontend: `https://workhub-frontend-def456uvw-uc.a.run.app`

---

### Step 7: Update GitHub Secrets with URLs (2 min)

Now that you have the actual URLs, update these 3 secrets in GitHub:

| Secret Name | Update With |
|------------|-------------|
| `BACKEND_URL` | Your actual backend URL |
| `FRONTEND_URL` | Your actual frontend URL |
| `ALLOWED_ORIGINS` | Your actual frontend URL |

Then trigger a redeploy:
```bash
git commit --allow-empty -m "Update URLs in secrets"
git push origin main
```

---

### Step 8: Test Your Deployment (2 min)

```bash
# Test backend health
curl https://YOUR-BACKEND-URL/api/health

# Should return:
# {"status":"healthy","message":"Work Hub API is running"}

# Open frontend in browser
open https://YOUR-FRONTEND-URL
```

---

## 🎉 You're Done!

Your WorkHub application is now live on GCP!

**Your deployment includes**:
- ✅ Backend API on Cloud Run
- ✅ Frontend on Cloud Run
- ✅ SQL Server database on Cloud SQL
- ✅ File uploads to Cloud Storage
- ✅ Secrets in Secret Manager
- ✅ Automatic deployments on every push to main
- ✅ Health checks and monitoring

---

## 📊 Your Resources

### Cloud Run Services
```bash
# List all services
gcloud run services list --region us-central1

# View backend logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=workhub-backend" --limit 50

# View frontend logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=workhub-frontend" --limit 50
```

### Cloud SQL
```bash
# Connect to database
gcloud sql connect workhub-db --user=sqlserver

# View instance info
gcloud sql instances describe workhub-db
```

### Cloud Storage
```bash
# List bucket contents
gsutil ls gs://genai-workhub-workhub-uploads/

# View bucket info
gsutil du -sh gs://genai-workhub-workhub-uploads/
```

---

## 💰 Cost Management

### Current Configuration Costs (Estimated Monthly)

| Resource | Configuration | Est. Cost |
|----------|--------------|-----------|
| Cloud Run (Backend) | 2 vCPU, 2GB, 1-10 instances | $25-50 |
| Cloud Run (Frontend) | 1 vCPU, 512MB, 1-5 instances | $15-30 |
| Cloud SQL | db-custom-1-3840 | $180-250 |
| Cloud Storage | 100GB | $2-5 |
| Other | Networking, Registry | $5-10 |
| **Total** | | **$227-345/month** |

### Set Up Budget Alerts

```bash
# Create budget alert at $300/month
gcloud billing budgets create \
  --billing-account=YOUR_BILLING_ACCOUNT_ID \
  --display-name="WorkHub Budget" \
  --budget-amount=300 \
  --threshold-rule=percent=50 \
  --threshold-rule=percent=90 \
  --threshold-rule=percent=100
```

---

## 🔄 Continuous Deployment

Every time you push to `main` branch:
1. GitHub Actions automatically builds new Docker images
2. Pushes images to Artifact Registry
3. Deploys to Cloud Run
4. Runs health checks
5. Notifies you of success/failure

**No manual deployment needed!**

---

## 🛠️ Common Operations

### Scale up/down

```bash
# Scale backend
gcloud run services update workhub-backend \
  --region us-central1 \
  --min-instances 2 \
  --max-instances 20

# Scale frontend
gcloud run services update workhub-frontend \
  --region us-central1 \
  --min-instances 2 \
  --max-instances 10
```

### Update environment variables

```bash
# Update backend
gcloud run services update workhub-backend \
  --region us-central1 \
  --update-env-vars KEY=VALUE

# Update frontend
gcloud run services update workhub-frontend \
  --region us-central1 \
  --update-env-vars KEY=VALUE
```

### Manual rollback

```bash
# List revisions
gcloud run revisions list --service workhub-backend --region us-central1

# Rollback to previous revision
gcloud run services update-traffic workhub-backend \
  --region us-central1 \
  --to-revisions REVISION_NAME=100
```

---

## 🐛 Troubleshooting

### Deployment fails?
```bash
# Check GitHub Actions logs
# Go to: GitHub → Actions → Failed workflow

# Check GCP logs
gcloud logging read "severity>=ERROR" --limit 20
```

### Can't connect to database?
```bash
# Verify instance is running
gcloud sql instances describe workhub-db --format='value(state)'
# Should output: RUNNABLE

# Test connection
gcloud sql connect workhub-db --user=sqlserver
```

### File uploads fail?
```bash
# Check bucket exists
gsutil ls gs://genai-workhub-workhub-uploads/

# Check permissions
gsutil iam get gs://genai-workhub-workhub-uploads/
```

---

## 📚 Additional Resources

- **Complete Guide**: `DEPLOYMENT_GCP.md`
- **GitHub Secrets**: `GITHUB_SECRETS_SETUP.md`
- **Implementation Details**: `DEPLOYMENT_SUMMARY.md`
- **GCP Console**: https://console.cloud.google.com/run?project=genai-workhub

---

## 🆘 Support Commands

```bash
# View all resources in your project
gcloud projects describe genai-workhub

# Check billing status
gcloud beta billing projects describe genai-workhub

# List all Cloud Run services
gcloud run services list --region us-central1

# Get service URLs
gcloud run services describe workhub-backend --region us-central1 --format='value(status.url)'
gcloud run services describe workhub-frontend --region us-central1 --format='value(status.url)'

# View recent logs
gcloud logging read "resource.type=cloud_run_revision" --limit 50 --format json

# Check Cloud SQL status
gcloud sql instances list

# List storage buckets
gsutil ls

# Check Secret Manager secrets
gcloud secrets list
```

---

## ✅ Post-Deployment Checklist

- [ ] Backend health check passes
- [ ] Frontend accessible in browser
- [ ] Can login to application
- [ ] Can create a test task
- [ ] Can upload a file
- [ ] Email notifications work
- [ ] GitHub Actions workflow is green
- [ ] Budget alerts configured
- [ ] Monitoring dashboard set up

---

## 🎯 Next Steps (Optional)

1. **Custom Domain** (if you get one later):
   ```bash
   gcloud run services update workhub-frontend \
     --region us-central1 \
     --domain your-domain.com
   ```

2. **Staging Environment**:
   - Create separate Cloud Run services with `-staging` suffix
   - Use separate database instance
   - Deploy from `develop` branch

3. **Enhanced Monitoring**:
   - Set up Cloud Monitoring dashboards
   - Configure alert policies
   - Enable Cloud Trace

4. **Performance Optimization**:
   - Enable Cloud CDN for static assets
   - Implement caching strategies
   - Optimize database queries

---

**Last Updated**: November 2025  
**Project**: genai-workhub  
**Region**: us-central1  
**Status**: ✅ Ready to deploy

