# Seed Production Database with Sample Data

This guide shows how to populate your production database with sample projects and tasks.

## What Will Be Created

- **5 Projects:**
  - Platform Core
  - Mobile App
  - Payments Integration
  - Analytics Dashboard
  - Customer Portal

- **25 Tasks:**
  - 5 tasks per project
  - Mix of statuses: `todo`, `in_progress`, `completed`
  - Various priorities: `low`, `medium`, `high`
  - Realistic due dates

## Option 1: Run via Cloud Shell (Recommended)

1. **Open Cloud Shell:**
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Click the Cloud Shell icon (top right)

2. **Clone and Setup:**
   ```bash
   cd ~
   git clone https://github.com/Omars64/Task_Management_System.git
   cd Task_Management_System/workhub-backend
   
   # Install dependencies
   pip3 install flask flask-sqlalchemy flask-cors flask-jwt-extended flask-bcrypt flask-mail pymssql
   ```

3. **Set Environment Variables:**
   ```bash
   export DB_DIALECT=mssql
   export DB_HOST=10.119.176.3
   export DB_PORT=1433
   export DB_NAME=workhub
   export DB_USER=sqlserver
   export DB_PASSWORD=WorkHub2024!Secure
   export SECRET_KEY=your-secret-key
   export JWT_SECRET_KEY=your-jwt-secret
   ```

4. **Run the Script:**
   ```bash
   python3 seed_production_data.py
   ```

## Option 2: Run as Cloud Run Job

Create a one-time Cloud Run job:

```bash
gcloud run jobs create seed-data-job \
  --image gcr.io/genai-workhub/workhub-backend:latest \
  --region us-central1 \
  --set-env-vars DB_HOST=10.119.176.3,DB_PORT=1433,DB_NAME=workhub,DB_USER=sqlserver,DB_DIALECT=mssql \
  --set-secrets DB_PASSWORD=workhub-db-password:latest \
  --command python \
  --args seed_production_data.py \
  --service-account your-service-account@genai-workhub.iam.gserviceaccount.com

# Execute the job
gcloud run jobs execute seed-data-job --region us-central1
```

## Option 3: Run via API Endpoint (Future)

You could add an admin-only API endpoint to trigger seeding, but this is less secure.

## Verification

After running, check your application:
- Go to Projects page - you should see 5 projects
- Go to Tasks page - you should see 25 tasks
- Tasks should be distributed across projects

## Notes

- The script is **idempotent** - safe to run multiple times
- It won't create duplicate projects or tasks
- Uses your super_admin account (`omarsolanki35@gmail.com`) as the owner
- All tasks are assigned to you by default

