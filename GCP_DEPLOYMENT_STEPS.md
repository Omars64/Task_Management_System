# 🚀 WorkHub GCP Deployment - Final Steps

## ✅ What You've Completed So Far

- ✅ All GitHub Secrets configured (10 secrets added)
- ✅ Repository ready for deployment
- ✅ CI/CD pipeline configured

---

## 📋 What's Left to Do

```
1. Create GCP Resources (Cloud SQL, Storage, etc.)
2. Re-enable GCP Deployment Workflow
3. Push to GitHub to Trigger Deployment
4. Initialize Database
5. Test Your Live Application
```

**Estimated Time:** 30-45 minutes  
**Cost:** ~$200-300/month

---

## 🔧 STEP 1: Install & Setup Google Cloud CLI

### 1.1 Install gcloud CLI (if not installed)

**Check if already installed:**
```powershell
gcloud --version
```

**If not installed:**
1. Download from: https://cloud.google.com/sdk/docs/install-sdk#windows
2. Run the installer (`GoogleCloudSDKInstaller.exe`)
3. Follow the installation wizard
4. Restart PowerShell after installation

### 1.2 Authenticate to Google Cloud

```powershell
# Login to your Google account
gcloud auth login
```
- A browser window will open
- Sign in with your Google account that has access to `genai-workhub` project
- Click "Allow" to grant permissions

### 1.3 Set Your Project

```powershell
# Set the active project
gcloud config set project genai-workhub

# Verify it's set correctly
gcloud config list
```

**Expected Output:**
```
[core]
account = your-email@gmail.com
project = genai-workhub
```

---

## 🏗️ STEP 2: Create GCP Resources

### 2.1 Enable Required APIs

```powershell
# Enable all necessary Google Cloud APIs
gcloud services enable run.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable cloudresourcemanager.googleapis.com
```

**⏱️ Takes:** 2-3 minutes

---

### 2.2 Create Artifact Registry (for Docker images)

```powershell
gcloud artifacts repositories create workhub-repo `
  --repository-format=docker `
  --location=us-central1 `
  --description="Docker repository for WorkHub"
```

**✅ Success Message:** `Created repository [workhub-repo]`

---

### 2.3 Create Cloud Storage Bucket (for file uploads)

```powershell
gcloud storage buckets create gs://workhub-uploads-genai `
  --location=us-central1 `
  --uniform-bucket-level-access
```

**✅ Success Message:** `Creating gs://workhub-uploads-genai/...`

---

### 2.4 Create Cloud SQL Instance (Database Server)

**⚠️ IMPORTANT:** This step takes 10-15 minutes!

```powershell
# Replace YOUR_SECURE_PASSWORD with a strong password
# Use the same password you added to GitHub Secret: DB_PASSWORD
gcloud sql instances create workhub-db `
  --database-version=SQLSERVER_2022_STANDARD `
  --tier=db-custom-2-7680 `
  --region=us-central1 `
  --root-password="YOUR_SECURE_PASSWORD" `
  --backup-start-time=03:00 `
  --enable-bin-log
```

**⚠️ REPLACE `YOUR_SECURE_PASSWORD`** with your actual database password!

**Example:**
```powershell
gcloud sql instances create workhub-db `
  --database-version=SQLSERVER_2022_STANDARD `
  --tier=db-custom-2-7680 `
  --region=us-central1 `
  --root-password="MySecurePass123!" `
  --backup-start-time=03:00 `
  --enable-bin-log
```

**⏱️ Wait Time:** 10-15 minutes (grab a coffee ☕)

**✅ Success Message:** `Created [https://sqladmin.googleapis.com/sql/v1beta4/projects/genai-workhub/instances/workhub-db]`

---

### 2.5 Create Database Inside SQL Instance

```powershell
gcloud sql databases create workhub --instance=workhub-db
```

**✅ Success Message:** `Created database [workhub]`

---

### 2.6 Create Service Account

```powershell
# Create the service account
gcloud iam service-accounts create workhub-sa `
  --display-name="WorkHub Service Account" `
  --description="Service account for WorkHub Cloud Run services"
```

**✅ Success Message:** `Created service account [workhub-sa]`

---

### 2.7 Grant Permissions to Service Account

```powershell
# Grant Cloud SQL Client role
gcloud projects add-iam-policy-binding genai-workhub `
  --member="serviceAccount:workhub-sa@genai-workhub.iam.gserviceaccount.com" `
  --role="roles/cloudsql.client"

# Grant Storage Admin role
gcloud projects add-iam-policy-binding genai-workhub `
  --member="serviceAccount:workhub-sa@genai-workhub.iam.gserviceaccount.com" `
  --role="roles/storage.objectAdmin"

# Grant Secret Manager Accessor role
gcloud projects add-iam-policy-binding genai-workhub `
  --member="serviceAccount:workhub-sa@genai-workhub.iam.gserviceaccount.com" `
  --role="roles/secretmanager.secretAccessor"
```

**✅ Each command should show:** `Updated IAM policy for project [genai-workhub]`

---

### 2.8 Generate Service Account Key

```powershell
# Navigate to your project folder
cd C:\Users\Omar\Task_Management_System\Task_Management_System-1

# Generate and download the key
gcloud iam service-accounts keys create gcp-key.json `
  --iam-account=workhub-sa@genai-workhub.iam.gserviceaccount.com
```

**✅ Success Message:** `created key [...] of type [json] as [gcp-key.json]`

**⚠️ File Location:** `C:\Users\Omar\Task_Management_System\Task_Management_System-1\gcp-key.json`

---

### 2.9 Update GitHub Secret: GCP_SA_KEY

Now you need to update the `GCP_SA_KEY` secret with the actual key contents:

1. **Open the key file:**
   ```powershell
   notepad gcp-key.json
   ```

2. **Copy ALL contents** (Ctrl+A, then Ctrl+C)

3. **Update GitHub Secret:**
   - Go to: https://github.com/Omars64/Task_Management_System/settings/secrets/actions
   - Click on `GCP_SA_KEY` secret
   - Click **Update secret**
   - Paste the entire JSON contents
   - Click **Update secret**

4. **Delete the local file (security):**
   ```powershell
   Remove-Item gcp-key.json
   ```

---

### 2.10 Create Secrets in Secret Manager

```powershell
# Create secret for database password (use same as DB_PASSWORD in GitHub)
echo "YOUR_DB_PASSWORD" | gcloud secrets create workhub-db-password --data-file=-

# Create secret for Flask secret key
$SECRET_KEY = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 64 | ForEach-Object {[char]$_})
echo $SECRET_KEY | gcloud secrets create workhub-secret-key --data-file=-

# Create secret for JWT secret key
$JWT_SECRET = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 64 | ForEach-Object {[char]$_})
echo $JWT_SECRET | gcloud secrets create workhub-jwt-secret --data-file=-

# Create secret for email password (use same as MAIL_PASSWORD in GitHub)
echo "YOUR_MAIL_PASSWORD" | gcloud secrets create workhub-mail-password --data-file=-
```

**⚠️ REPLACE:**
- `YOUR_DB_PASSWORD` with your actual database password
- `YOUR_MAIL_PASSWORD` with your Gmail app password

---

## ✅ STEP 2 COMPLETE! Verify Your Resources

```powershell
# Check all resources
gcloud sql instances list
gcloud storage buckets list
gcloud artifacts repositories list --location=us-central1
gcloud iam service-accounts list
gcloud secrets list
```

**You should see:**
- ✅ Cloud SQL instance: `workhub-db`
- ✅ Storage bucket: `workhub-uploads-genai`
- ✅ Artifact Registry: `workhub-repo`
- ✅ Service Account: `workhub-sa`
- ✅ 4 Secrets in Secret Manager

---

## 🔄 STEP 3: Re-enable GCP Deployment Workflow

Now let's activate the deployment pipeline:

```powershell
# Navigate to your project
cd C:\Users\Omar\Task_Management_System\Task_Management_System-1

# Rename the disabled workflow to enable it
Rename-Item -Path .github\workflows\deploy-gcp.yml.disabled -NewName deploy-gcp-production.yml

# Check git status
git status
```

---

## 📤 STEP 4: Commit and Push to Trigger Deployment

```powershell
# Stage the changes
git add .

# Commit
git commit -m "feat: Enable GCP production deployment

- Enabled deploy-gcp-production.yml workflow
- All GCP resources created (Cloud SQL, Storage, Artifact Registry)
- All GitHub secrets configured
- Ready for first production deployment"

# Push to trigger deployment
git push origin main
```

**🎬 This will trigger the deployment!**

---

## 👀 STEP 5: Monitor Deployment Progress

### 5.1 Watch GitHub Actions

1. Go to: https://github.com/Omars64/Task_Management_System/actions
2. Click on the latest workflow run: **"Deploy to Google Cloud Platform"**
3. Watch the progress (takes 15-20 minutes):

```
✅ Build Backend Image         (~5 minutes)
✅ Build Frontend Image        (~5 minutes)
✅ Deploy Backend to Cloud Run (~3 minutes)
✅ Deploy Frontend to Cloud Run (~2 minutes)
✅ Verify Deployment           (~1 minute)
```

### 5.2 If Deployment Fails

Check the error logs in GitHub Actions, then:

**Common Issue: Missing Secret**
- Go back to GitHub Secrets and verify all 10+ secrets are set correctly

**Common Issue: Permission Denied**
- Re-run the permission commands from Step 2.7

**Common Issue: Cloud SQL Connection**
- Verify `CLOUD_SQL_CONNECTION_NAME` is exactly: `genai-workhub:us-central1:workhub-db`

---

## 🌐 STEP 6: Get Your Application URLs

After deployment succeeds, get your URLs:

```powershell
# Get backend URL
gcloud run services describe workhub-backend --region=us-central1 --format="value(status.url)"

# Get frontend URL
gcloud run services describe workhub-frontend --region=us-central1 --format="value(status.url)"
```

**Example URLs:**
```
Backend:  https://workhub-backend-abc123-uc.a.run.app
Frontend: https://workhub-frontend-xyz789-uc.a.run.app
```

**📝 Save these URLs!** You'll need them.

---

## 🔧 STEP 7: Update GitHub Secrets with URLs

Now update these secrets with your actual URLs:

1. Go to: https://github.com/Omars64/Task_Management_System/settings/secrets/actions

2. **Update `BACKEND_URL`:**
   - Click **Update secret**
   - Paste your backend Cloud Run URL
   - Click **Update secret**

3. **Update `FRONTEND_URL`:**
   - Click **Update secret**
   - Paste your frontend Cloud Run URL
   - Click **Update secret**

4. **Update `ALLOWED_ORIGINS`:**
   - Click **Update secret**
   - Change from `*` to your frontend URL
   - Example: `https://workhub-frontend-xyz789-uc.a.run.app`
   - Click **Update secret**

---

## 🔄 STEP 8: Redeploy with Correct URLs

```powershell
# Trigger redeployment with updated secrets
git commit --allow-empty -m "chore: Redeploy with correct URLs and CORS settings"
git push origin main
```

Wait for GitHub Actions to complete again (~15 minutes).

---

## 🗄️ STEP 9: Initialize Database

Your database is empty! Let's populate it with tables and default data.

### Option A: Use Cloud Shell (Easiest)

1. Go to: https://console.cloud.google.com/sql/instances/workhub-db/overview?project=genai-workhub
2. Click **CONNECT TO THIS INSTANCE**
3. Click **OPEN CLOUD SHELL**
4. Run:
   ```bash
   gcloud sql connect workhub-db --user=sqlserver --database=workhub
   ```
5. Enter your database password
6. You're now in SQL Server console!

### Option B: Use Your Local Machine

```powershell
# Download Cloud SQL Proxy
Invoke-WebRequest -Uri "https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.2/cloud-sql-proxy.x64.exe" -OutFile "cloud-sql-proxy.exe"

# Run the proxy (keep this running in one window)
.\cloud-sql-proxy.exe genai-workhub:us-central1:workhub-db
```

Then connect using SQL Server Management Studio (SSMS) or Azure Data Studio:
- Server: `localhost,1433`
- Authentication: SQL Server Authentication
- Login: `sqlserver`
- Password: (your DB_PASSWORD)

### Initialize Tables

Run the SQL from your `init_db.py` to create all tables and insert default users.

**Or use the API to initialize:**
```powershell
# Call the initialization endpoint (if you created one)
curl -X POST "https://YOUR-BACKEND-URL/api/init-db"
```

---

## ✅ STEP 10: Test Your Live Application!

### 10.1 Test Backend Health

```powershell
# Replace with your actual backend URL
curl https://workhub-backend-abc123-uc.a.run.app/api/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "database": "connected"
}
```

### 10.2 Open Frontend in Browser

Open your frontend URL in Chrome/Edge:
```
https://workhub-frontend-xyz789-uc.a.run.app
```

**You should see:** WorkHub login page! 🎉

### 10.3 Login

Use default credentials:
- **Email:** `admin@workhub.com`
- **Password:** `admin123`

(You'll need to create this user in the database first)

---

## 🎯 Post-Deployment Checklist

- [ ] Backend health check passes
- [ ] Frontend loads correctly
- [ ] Login works
- [ ] Can create tasks
- [ ] Can upload files
- [ ] Email notifications work
- [ ] All features accessible

---

## 🐛 Troubleshooting

### Issue: "Cloud SQL connection failed"

**Check:**
```powershell
gcloud sql instances describe workhub-db --format="value(connectionName)"
```
Should return: `genai-workhub:us-central1:workhub-db`

**Fix:** Update `CLOUD_SQL_CONNECTION_NAME` secret in GitHub

---

### Issue: "Permission denied" errors

**Fix:** Re-run permission commands:
```powershell
gcloud projects add-iam-policy-binding genai-workhub `
  --member="serviceAccount:workhub-sa@genai-workhub.iam.gserviceaccount.com" `
  --role="roles/cloudsql.client"
```

---

### Issue: "Backend returns 500 errors"

**Check logs:**
```powershell
gcloud run services logs read workhub-backend --region=us-central1 --limit=50
```

---

### Issue: "Frontend can't connect to backend"

**Fix:** Verify `ALLOWED_ORIGINS` includes your frontend URL

---

## 💰 Cost Monitoring

Monitor your GCP costs:

1. Go to: https://console.cloud.google.com/billing?project=genai-workhub
2. Check "Cost breakdown"

**Expected Monthly Cost:** ~$200-300
- Cloud SQL: ~$150
- Cloud Run: ~$50
- Cloud Storage: ~$10
- Other: ~$20

---

## 🎉 SUCCESS!

Once you see your application running, you're done! 

**Your WorkHub app is now live on:**
- Frontend: `https://workhub-frontend-xyz789-uc.a.run.app`
- Backend: `https://workhub-backend-abc123-uc.a.run.app`

**Share the frontend URL with your team!**

---

## 📚 Additional Resources

- **View Services:** https://console.cloud.google.com/run?project=genai-workhub
- **View Database:** https://console.cloud.google.com/sql/instances?project=genai-workhub
- **View Storage:** https://console.cloud.google.com/storage/browser?project=genai-workhub
- **View Logs:** https://console.cloud.google.com/logs?project=genai-workhub

---

## 🆘 Need Help?

If you get stuck:
1. Check the error message in GitHub Actions
2. Check Cloud Run logs
3. Verify all secrets are correct
4. Share the error with me!

---

**🚀 Good luck with your deployment!**

