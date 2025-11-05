# WorkHub CI/CD & Deployment Setup ✅

## 🎉 What's Been Implemented

All necessary files and configurations for automated deployment to Google Cloud Platform have been created and are ready to use.

---

## 📦 Files Created/Modified

### Backend Changes
- ✅ `workhub-backend/requirements.txt` - Added GCP dependencies (google-cloud-storage, google-cloud-secret-manager, gunicorn)
- ✅ `workhub-backend/config.py` - Added Cloud SQL connection support
- ✅ `workhub-backend/app.py` - Updated CORS for production domains
- ✅ `workhub-backend/storage_service.py` - NEW: Cloud Storage service for file uploads
- ✅ `workhub-backend/file_uploads.py` - Updated to use Cloud Storage
- ✅ `workhub-backend/Dockerfile` - Production-ready with health checks and gunicorn

### Frontend Changes
- ✅ `workhub-frontend/Dockerfile` - Added build args for API URL and health checks

### CI/CD Configuration
- ✅ `.github/workflows/deploy-gcp.yml` - GitHub Actions workflow for automated deployment
- ✅ `cloudbuild.yaml` - Google Cloud Build configuration (alternative to GitHub Actions)

### Deployment Scripts
- ✅ `scripts/setup-gcp.sh` - Initial GCP setup (creates all resources)
- ✅ `scripts/deploy-gcp.sh` - Manual deployment script

### Documentation
- ✅ `DEPLOYMENT_GCP.md` - Complete deployment guide (80+ pages of documentation)
- ✅ `env.production.template` - Environment variables template
- ✅ `CI_CD_README.md` - This file

---

## 🚀 Quick Start Guide

### Option 1: Automated Setup (Recommended)

```bash
# 1. Set your GCP project details
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="us-central1"

# 2. Run automated setup
bash scripts/setup-gcp.sh

# 3. Configure GitHub Secrets (see below)

# 4. Push to GitHub to trigger deployment
git push origin main
```

### Option 2: Manual Deployment

```bash
# Run manual deployment
bash scripts/deploy-gcp.sh
```

---

## 🔑 Required GitHub Secrets

Add these in: **GitHub Repo → Settings → Secrets and variables → Actions**

### Essential Secrets
```
GCP_PROJECT_ID=your-gcp-project-id
GCP_REGION=us-central1
GCP_SA_KEY=<service-account-json-key>
CLOUD_SQL_CONNECTION_NAME=project:region:instance
CLOUD_STORAGE_BUCKET=your-bucket-name
GCP_SERVICE_ACCOUNT_EMAIL=workhub-cloud-run-sa@...
DB_USER=sqlserver
```

### Application URLs (after first deployment)
```
BACKEND_URL=https://workhub-backend-xxx.a.run.app
FRONTEND_URL=https://workhub-frontend-xxx.a.run.app
ALLOWED_ORIGINS=https://your-domain.com
```

### Email Configuration
```
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_DEFAULT_SENDER=noreply@yourdomain.com
```

---

## 📋 Deployment Methods

### Method 1: GitHub Actions (Automated)
- **Trigger**: Push to `main` branch
- **Process**: Automatic build → push → deploy → verify
- **Monitoring**: GitHub Actions tab
- **Best for**: Production environments

### Method 2: Google Cloud Build
- **Trigger**: Manual or automated via Cloud Build triggers
- **Process**: Uses `cloudbuild.yaml`
- **Best for**: GCP-native deployments

### Method 3: Manual Script
- **Command**: `bash scripts/deploy-gcp.sh`
- **Best for**: Testing, debugging, one-off deployments

---

## 🏗️ Architecture

```
GitHub Push → Build Images → Artifact Registry → Cloud Run
                                                    ↓
                                          Cloud SQL + Cloud Storage
```

**Services**:
- **Cloud Run** (Backend): 2 vCPU, 2GB RAM, auto-scaling
- **Cloud Run** (Frontend): 1 vCPU, 512MB RAM
- **Cloud SQL**: SQL Server 2022, 1 vCPU, 3.75GB
- **Cloud Storage**: File uploads
- **Secret Manager**: Credentials

**Estimated Cost**: $250-400/month

---

## ✨ Key Features

### Backend
✅ Production-ready with Gunicorn  
✅ Health checks and graceful shutdowns  
✅ Cloud SQL connection via Unix socket  
✅ Cloud Storage for file uploads  
✅ Secret Manager integration  
✅ Configurable CORS  
✅ Non-root user for security  

### Frontend
✅ Multi-stage Docker build  
✅ Nginx with compression  
✅ Build-time API URL configuration  
✅ Health checks  
✅ Non-root user  

### CI/CD
✅ Parallel builds (backend + frontend)  
✅ Automated deployment on push  
✅ Health verification  
✅ Rollback capability  
✅ Environment-based deployment (staging/production)  

---

## 🔧 Configuration

### Environment Variables

**Backend (Cloud Run)**:
- `CLOUD_SQL_CONNECTION_NAME` - Database connection
- `USE_CLOUD_STORAGE=true` - Enable Cloud Storage
- `CLOUD_STORAGE_BUCKET` - Bucket name
- `ALLOWED_ORIGINS` - CORS origins
- Secrets from Secret Manager

**Frontend (Build time)**:
- `VITE_API_URL` - Backend API URL

---

## 📊 Monitoring

### View Logs
```bash
# Backend logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=workhub-backend" --limit 50

# Frontend logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=workhub-frontend" --limit 50
```

### Metrics
- **Cloud Console**: Monitoring dashboard
- **Cloud Run**: Request count, latency, errors
- **Cloud SQL**: CPU, memory, connections

---

## 🐛 Troubleshooting

### Deployment fails?
1. Check GitHub Actions logs
2. Verify all secrets are set
3. Ensure GCP APIs are enabled
4. Check IAM permissions

### Can't connect to database?
1. Verify Cloud SQL instance is running
2. Check connection name is correct
3. Ensure secrets are accessible

### File uploads fail?
1. Check `USE_CLOUD_STORAGE=true` is set
2. Verify bucket exists and IAM permissions
3. Check service account has storage.objectAdmin

### CORS errors?
1. Update `ALLOWED_ORIGINS` environment variable
2. Redeploy backend service

---

## 📚 Documentation

- **Complete Guide**: See `DEPLOYMENT_GCP.md` (80+ pages)
- **Environment Template**: See `env.production.template`
- **GCP Docs**: [Cloud Run](https://cloud.google.com/run/docs)

---

## 🎯 Next Steps

1. **Run Setup Script**: `bash scripts/setup-gcp.sh`
2. **Create Service Account Key** for GitHub Actions
3. **Add GitHub Secrets** (12 required secrets)
4. **Push to GitHub** - triggers automatic deployment
5. **Get URLs** from GitHub Actions output or Cloud Console
6. **Configure Custom Domain** (optional)
7. **Set up Monitoring** and alerts

---

## ✅ Verification Checklist

After deployment:
- [ ] Backend health check: `curl https://BACKEND_URL/api/health`
- [ ] Frontend accessible: Open in browser
- [ ] Database connection works: Login to app
- [ ] File uploads work: Try uploading a file
- [ ] Email notifications work: Test signup
- [ ] Monitoring dashboard accessible
- [ ] Logs visible in Cloud Console

---

## 💡 Tips

1. **First Deployment**: May take 15-20 minutes (SQL instance provisioning)
2. **Secrets**: Never commit to Git, use Secret Manager
3. **Costs**: Monitor with Budget Alerts
4. **Scaling**: Adjust min/max instances based on traffic
5. **Security**: Enable VPC connector for production

---

## 🆘 Support

**Issues**: Check `DEPLOYMENT_GCP.md` troubleshooting section  
**Logs**: `gcloud logging read` for detailed errors  
**Status**: Check Cloud Console → Cloud Run

---

**Created**: November 2025  
**Status**: ✅ Ready for deployment  
**Next Action**: Run `bash scripts/setup-gcp.sh`

