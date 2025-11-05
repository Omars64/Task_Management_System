# ✅ WorkHub GCP Deployment Checklist

## 📊 Current Status

### GitHub Setup ✅ COMPLETE
- [x] All 10 GitHub Secrets configured
- [x] Repository ready
- [x] CI/CD workflow files in place

### GCP Setup 🔄 TODO
- [ ] Install gcloud CLI
- [ ] Authenticate to Google Cloud
- [ ] Enable GCP APIs
- [ ] Create Artifact Registry
- [ ] Create Cloud Storage Bucket
- [ ] Create Cloud SQL Instance (10-15 min wait)
- [ ] Create Database
- [ ] Create Service Account
- [ ] Grant Permissions
- [ ] Generate Service Account Key
- [ ] Update GCP_SA_KEY secret in GitHub
- [ ] Create Secrets in Secret Manager

### Deployment 🔄 TODO
- [ ] Re-enable deployment workflow
- [ ] Push to GitHub to trigger deployment
- [ ] Monitor GitHub Actions (15-20 min)
- [ ] Get Cloud Run URLs
- [ ] Update GitHub secrets with URLs
- [ ] Redeploy with correct URLs

### Post-Deployment 🔄 TODO
- [ ] Initialize database tables
- [ ] Create default admin user
- [ ] Test backend health endpoint
- [ ] Test frontend login
- [ ] Verify all features work

---

## 🎯 Quick Start Commands

### Step 1: Setup GCP (PowerShell)
```powershell
# Install gcloud CLI first from:
# https://cloud.google.com/sdk/docs/install-sdk#windows

# Then run:
gcloud auth login
gcloud config set project genai-workhub
```

### Step 2: Follow the detailed guide
Open and follow: `GCP_DEPLOYMENT_STEPS.md`

---

## ⏱️ Time Estimate

- **GCP Resource Setup:** 30 minutes (including 10-15 min Cloud SQL wait)
- **First Deployment:** 15-20 minutes
- **Database Initialization:** 10 minutes
- **Testing:** 10 minutes

**Total:** ~60-75 minutes

---

## 💰 Cost Estimate

**Monthly:** ~$200-300
- Cloud SQL (SQL Server 2022): ~$150
- Cloud Run (2 services): ~$50
- Cloud Storage: ~$10
- Other (networking, logs): ~$20

---

## 🆘 If You Get Stuck

1. Check `GCP_DEPLOYMENT_STEPS.md` for detailed instructions
2. Check GitHub Actions logs for errors
3. Check Cloud Run logs: 
   ```powershell
   gcloud run services logs read workhub-backend --region=us-central1 --limit=50
   ```

---

## 📞 Quick Links

- **GitHub Secrets:** https://github.com/Omars64/Task_Management_System/settings/secrets/actions
- **GitHub Actions:** https://github.com/Omars64/Task_Management_System/actions
- **GCP Console:** https://console.cloud.google.com/?project=genai-workhub
- **Cloud Run Services:** https://console.cloud.google.com/run?project=genai-workhub
- **Cloud SQL:** https://console.cloud.google.com/sql/instances?project=genai-workhub

---

**🚀 Ready to deploy? Open `GCP_DEPLOYMENT_STEPS.md` and start with Step 1!**
