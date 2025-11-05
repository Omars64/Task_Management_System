# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Prerequisites
- Docker Desktop installed and running
- Your Gmail account for sending verification emails

---

## Step 1: Configure Email (2 minutes)

Create `.env` file in the project root:

```env
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-gmail-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
```

**Get Gmail App Password:**
1. Go to https://myaccount.google.com/security
2. Enable 2-Step Verification
3. Go to App passwords → Generate
4. Copy the 16-character password

---

## Step 2: Start Application (2 minutes)

```bash
# In project root directory
docker-compose up --build
```

Wait for:
```
✓ Database started
✓ Backend started
✓ Frontend started
```

---

## Step 3: Open Application (1 minute)

Open browser: **http://localhost:3000**

---

## Test the Flow

### 1. Sign Up New User
- Click "Sign Up" tab
- Enter name, email, password
- Click "Sign Up"

### 2. Verify Email
- Check your email inbox
- Copy the 6-digit code
- Enter code in verification page
- Click "Verify Email"
- ✅ Email verified!

### 3. Admin Approval
- Log in as admin (create first user as admin)
- Go to "Users" page
- See "Pending Users" section
- Click "Approve"
- ✅ User approved!

### 4. User Can Login
- New user receives approval email
- User can now log in
- ✅ Complete!

---

## Default Credentials

**First user created becomes admin.**

Or manually create admin in database:
```sql
UPDATE users SET role='admin', signup_status='approved' WHERE email='your-email@example.com';
```

---

## Common Commands

```bash
# View logs
docker-compose logs -f

# Stop (non-destructive)
docker-compose down

# Restart
docker-compose restart

# Rebuild
docker-compose up --build

# WARNING: Don't use `down -v` unless you want to DELETE your DB volume
# docker-compose down -v
```

---

## Troubleshooting

### Email not sending?
1. Check `.env` file exists
2. Verify Gmail App Password (not regular password)
3. Check backend logs: `docker-compose logs backend`

### Port already in use?
```bash
# Windows
netstat -ano | findstr :3000
netstat -ano | findstr :5000

# Kill process or change port in docker-compose.yml
```

### Database not starting?
```bash
# Check status
docker-compose ps

# Restart database
docker-compose restart database
```

---

## What's Running?

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000
- **Database**: localhost:1433

---

## Next Steps

1. ✅ Test signup flow
2. ✅ Test email verification
3. ✅ Test admin approval
4. ✅ Explore features:
   - Tasks management
   - Time logging
   - Comments
   - File attachments
   - Reports
   - Things to Do
   - Notifications

---

## Need Help?

See detailed docs:
- **README_DOCKER.md** - Complete Docker guide
- **FINAL_IMPLEMENTATION_SUMMARY.md** - All changes explained
- **EMAIL_CONFIGURATION_GUIDE.md** - Email setup details

---

**Ready to deploy to production? See README_DOCKER.md for production setup!**

