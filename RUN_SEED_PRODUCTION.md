# Quick Guide: Seed Production Data

## Run via Cloud Shell (Easiest Method)

1. **Open Cloud Shell** in Google Cloud Console

2. **Run these commands:**

```bash
# Clone the repo
cd ~
git clone https://github.com/Omars64/Task_Management_System.git
cd Task_Management_System/workhub-backend

# Install Python dependencies
pip3 install flask flask-sqlalchemy flask-cors flask-jwt-extended flask-bcrypt flask-mail pymssql

# Set environment variables
export DB_DIALECT=mssql
export DB_HOST=10.119.176.3
export DB_PORT=1433
export DB_NAME=workhub
export DB_USER=sqlserver
export DB_PASSWORD='WorkHub2024!Secure'
export SECRET_KEY='temp-secret-for-seeding'
export JWT_SECRET_KEY='temp-jwt-secret'

# Run the seeding script
python3 seed_production_data.py
```

3. **You should see output like:**
```
============================================================
Seeding Production Database with Sample Data
============================================================

✓ Using owner: Omar Solanki (omarsolanki35@gmail.com)

Creating projects...
✓ Created project: Platform Core
✓ Created project: Mobile App
...

✅ Seeding Complete!
   Projects: 5
   Tasks: 25
============================================================
```

## What Gets Created

- **5 Projects** with descriptions
- **25 Tasks** (5 per project)
- Tasks assigned to you (super_admin)
- Mix of statuses: todo, in_progress, completed
- Realistic due dates

## Verify in Application

After running, refresh your application:
- **Projects page**: Should show 5 projects
- **Tasks page**: Should show 25 tasks
- Tasks are linked to their respective projects

