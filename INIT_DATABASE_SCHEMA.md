# Initialize Database Schema on Cloud SQL

The database tables are missing, which is why you're getting "Invalid object name" errors. Follow these steps to create all required tables.

## Option 1: Run from Cloud Shell (Recommended)

### Step 1: Open Cloud Shell
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Click the **Cloud Shell** icon (terminal icon) in the top right
3. Wait for Cloud Shell to open

### Step 2: Clone Your Repository
```bash
cd ~
git clone https://github.com/Omars64/Task_Management_System.git
cd Task_Management_System/workhub-backend
```

### Step 3: Install Python Dependencies
```bash
# Install Python 3.10+ if needed
python3 --version

# Install required packages
pip3 install flask flask-sqlalchemy flask-cors flask-jwt-extended flask-bcrypt flask-mail pymssql
```

### Step 4: Set Environment Variables
```bash
# Get your database connection details from Secret Manager or Cloud SQL
export DB_DIALECT=mssql
export DB_HOST=10.119.176.3  # Your Cloud SQL Private IP
export DB_PORT=1433
export DB_NAME=workhub
export DB_USER=sqlserver
export DB_PASSWORD=WorkHub2024!Secure  # Your database password

# Optional: Set other required env vars
export SECRET_KEY=your-secret-key-here
export JWT_SECRET_KEY=your-jwt-secret-key-here
export ALLOWED_ORIGINS=https://workhub-frontend-kf6vth5ica-uc.a.run.app
export FRONTEND_URL=https://workhub-frontend-kf6vth5ica-uc.a.run.app
```

### Step 5: Run the Initialization Script
```bash
python3 init_cloud_sql.py
```

You should see output like:
```
============================================================
Initializing Cloud SQL Database Schema
============================================================

Existing tables: ['users', ...]

Creating tables using SQLAlchemy models...
✓ SQLAlchemy create_all() completed

Ensuring all required tables exist...
✓ projects table created
✓ sprints table created
...
✓ All required tables exist!

============================================================
Database initialization complete!
============================================================
```

## Option 2: Run from Local Machine

If you prefer to run from your local machine:

### Step 1: Install Cloud SQL Proxy
Download and install Cloud SQL Proxy from: https://cloud.google.com/sql/docs/sqlserver/connect-admin-proxy

### Step 2: Start Cloud SQL Proxy
```bash
# In a separate terminal
./cloud-sql-proxy genai-workhub:us-central1:workhub-db --port 1433
```

### Step 3: Set Environment Variables
```bash
export DB_DIALECT=mssql
export DB_HOST=127.0.0.1  # Local proxy
export DB_PORT=1433
export DB_NAME=workhub
export DB_USER=sqlserver
export DB_PASSWORD=WorkHub2024!Secure
```

### Step 4: Run the Script
```bash
cd workhub-backend
python3 init_cloud_sql.py
```

## Option 3: Run via Cloud Run Job (Advanced)

If you want to run it as a one-time Cloud Run job:

1. Create a Cloud Run job that runs `init_cloud_sql.py`
2. Configure it with the same environment variables as your backend service
3. Execute the job once

## Verification

After running the script, verify the tables were created:

### Using Cloud SQL Studio:
1. Go to Cloud SQL → workhub-db → **Databases** → **workhub** → **Tables**
2. You should see tables like: `users`, `tasks`, `projects`, `sprints`, `meetings`, `reminders`, etc.

### Using SQL Query:
```sql
SELECT TABLE_NAME 
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_TYPE = 'BASE TABLE'
ORDER BY TABLE_NAME;
```

## Troubleshooting

### Error: "Login failed for user"
- Verify `DB_USER` and `DB_PASSWORD` are correct
- Check that the user has permissions on the `workhub` database

### Error: "Cannot connect to database"
- Verify `DB_HOST` is the Private IP (10.119.176.3)
- Ensure you're running from Cloud Shell (which has VPC access) or using Cloud SQL Proxy

### Error: "Module not found"
- Install all required Python packages: `pip3 install -r requirements.txt`

## Next Steps

After initialization:
1. ✅ Tables will be created
2. ✅ You can create projects, tasks, meetings, etc.
3. ✅ The application should work normally

The script is **idempotent** - it's safe to run multiple times. It will only create tables that don't exist.

